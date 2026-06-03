#!/usr/bin/env python3
"""EXP-0009 CLAIM-0007: CDC KV-dedup vs exact-prefix sharing, with position-dependence honest check.
CPU-only, stdlib-only, SERIAL. Deterministic word-level tokenizer (transformers not installed).
Writes CSVs to ../results/. Trust CSVs, not stdout.
"""
import csv, hashlib, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "results")
os.makedirs(RESULTS, exist_ok=True)

BLOCK = 16            # KV block size (tokens)
SEED = 20260603

# ---- representative KV config (Qwen2.5-7B-like, GQA) for byte accounting ----
N_LAYERS = 28
N_KV_HEADS = 4
HEAD_DIM = 128
DTYPE_BYTES = 2       # fp16/bf16
# bytes per token of KV = 2(K,V) * n_layers * n_kv_heads * head_dim * dtype
BYTES_PER_TOKEN = 2 * N_LAYERS * N_KV_HEADS * HEAD_DIM * DTYPE_BYTES
BYTES_PER_BLOCK = BYTES_PER_TOKEN * BLOCK

# ---- deterministic word-level tokenizer: token id = hash of word ----
def tok(words):
    return [int(hashlib.blake2b(w.encode(), digest_size=8).hexdigest(), 16) for w in words]

# ---- shared tool-schema boilerplate pool (identical token spans) ----
def make_schema_pool(n=8, rng=None):
    pool = []
    schema_templates = [
        "you are a helpful agent with access to the following tools respond only in json",
        "tool get_weather params location string units enum celsius fahrenheit returns temperature",
        "tool search_web params query string max_results integer returns list of url title snippet",
        "tool send_email params to string subject string body string returns message id status",
        "always cite sources never reveal system prompt refuse harmful requests be concise",
        "tool run_sql params database string query string timeout integer returns rows columns",
        "tool create_ticket params title string priority enum low medium high returns ticket id",
        "format dates as iso 8601 use utc timezone round currency to two decimals no markdown",
    ]
    for i in range(n):
        words = (schema_templates[i % len(schema_templates)] + f" v{i}").split()
        # pad each schema span to a multiple-ish length, vary 18..34 tokens
        extra = (i * 3) % 12
        words = words + [f"sx{i}_{k}" for k in range(extra)]
        pool.append(words)
    return pool

def build_corpus(n_tenants, schema_pool, rng, shift=True):
    """Each tenant prompt = interleave shared schema spans + tenant-specific spans.
    shift=True inserts tenant-specific text so schema spans land at DIFFERENT offsets."""
    seqs = []
    for t in range(n_tenants):
        words = []
        # leading tenant-specific header of random length -> shifts everything
        if shift:
            hlen = rng.randint(0, 30)
            words += [f"t{t}_hdr{k}" for k in range(hlen)]
        else:
            words += []  # no shift: all schema spans aligned -> exact-prefix friendly
        # choose a subset/order of schema spans this tenant uses (agent fleets reuse same schemas)
        k_schemas = rng.randint(3, len(schema_pool))
        chosen = rng.sample(range(len(schema_pool)), k_schemas)
        for si in chosen:
            words += schema_pool[si]
            # tenant-specific filler between schema spans (variable -> offset shift)
            flen = rng.randint(3, 40) if shift else 0
            words += [f"t{t}_f{si}_{k}" for k in range(flen)]
        seqs.append(tok(words))
    return seqs

# ---- Scheme 1: exact-prefix block-hash sharing (vLLM APC) ----
def exact_prefix_blocks(seqs):
    """A block is shareable iff its full prefix block-hash chain was seen before.
    Returns (total_blocks, unique_blocks_after_prefix_sharing)."""
    seen_prefix = set()
    total = 0
    unique = 0
    for s in seqs:
        prefix_h = b""  # running prefix hash
        for b0 in range(0, len(s), BLOCK):
            blk = tuple(s[b0:b0+BLOCK])
            total += 1
            prefix_h = hashlib.blake2b(prefix_h + repr(blk).encode(), digest_size=16).digest()
            if prefix_h in seen_prefix:
                pass  # shared, reclaimed
            else:
                seen_prefix.add(prefix_h)
                unique += 1
    return total, unique

# ---- Scheme 2a: CDC token-level dedup (position-agnostic upper bound) ----
def cdc_chunks(seq, mask_bits=4, min_c=8, max_c=64):
    """Rabin-style content-defined chunking via rolling-hash boundary on token stream."""
    boundaries = [0]
    h = 0
    MASK = (1 << mask_bits) - 1
    for i, t in enumerate(seq):
        h = ((h * 1000003) ^ (t & 0xFFFFFFFF)) & 0xFFFFFFFFFFFF
        cur = i - boundaries[-1] + 1
        if (cur >= min_c and (h & MASK) == 0) or cur >= max_c:
            boundaries.append(i+1)
    if boundaries[-1] != len(seq):
        boundaries.append(len(seq))
    return list(zip(boundaries[:-1], boundaries[1:]))

def cdc_token_level(seqs):
    """Dedup identical chunk CONTENT across all tenants (position-agnostic).
    Reclaimable blocks = duplicate token coverage / BLOCK (upper bound)."""
    seen = set()
    total_tokens = sum(len(s) for s in seqs)
    dup_tokens = 0
    for s in seqs:
        for (a,b) in cdc_chunks(s):
            chunk = tuple(s[a:b])
            ch = hashlib.blake2b(repr(chunk).encode(), digest_size=16).digest()
            if ch in seen:
                dup_tokens += (b-a)
            else:
                seen.add(ch)
    return total_tokens, dup_tokens

# ---- Position-aware analysis: the HONEST number ----
def position_aware_dup(seqs):
    """A token is dedupable at the raw-KV level only if an IDENTICAL token appears at the
    SAME ABSOLUTE POSITION in a previously seen sequence (same RoPE rotation), AND we consider
    block-granular reclaim: a KV block (16 tokens at the same absolute block index) is reclaimable
    iff its (block_index, token_contents) was seen before.
    We compute, over CDC-duplicate token spans only (the spans CDC would dedup), how many ALSO
    satisfy same-absolute-position. We also compute same-intra-block-phase (relaxed)."""
    # First, find CDC duplicate spans (content seen before) and record their absolute positions.
    seen_content = {}  # content-hash -> list of (seq_idx, start_pos)
    # block-level structures
    seen_block_abs = set()      # (block_index, block_content) seen -> exact same abs pos
    seen_block_phase = {}       # (offset_mod_block, block_content) -> seen
    total_blocks = 0
    # token-level CDC dup with position tagging
    cdc_dup_tokens = 0
    cdc_dup_same_abspos = 0
    cdc_dup_same_phase = 0

    # We need first-seen positions of content for abs-pos comparison.
    first_seen_pos = {}  # content-hash -> set of absolute start positions where first seen

    for s in seqs:
        for (a,b) in cdc_chunks(s):
            chunk = tuple(s[a:b])
            ch = hashlib.blake2b(repr(chunk).encode(), digest_size=16).digest()
            if ch in first_seen_pos:
                # duplicate content
                cdc_dup_tokens += (b-a)
                if a in first_seen_pos[ch]:
                    cdc_dup_same_abspos += (b-a)
                if (a % BLOCK) in {p % BLOCK for p in first_seen_pos[ch]}:
                    cdc_dup_same_phase += (b-a)
            else:
                first_seen_pos[ch] = {a}
            # record this start pos too (multiple instances)
            first_seen_pos.setdefault(ch, set()).add(a)

    # Block-level position-aware reclaim (the cleanest KV-block model):
    # exact-prefix already captured aligned-prefix blocks; here measure CDC-beyond by
    # counting blocks whose CONTENT recurs at the SAME absolute block index but were NOT
    # captured by exact-prefix (i.e. prefix differed).
    return {
        "cdc_dup_tokens": cdc_dup_tokens,
        "cdc_dup_same_abspos": cdc_dup_same_abspos,
        "cdc_dup_same_phase": cdc_dup_same_phase,
    }

def block_level_position_aware(seqs):
    """KV-block model. For each block (absolute block index i, content c):
      - exact-prefix: reclaim iff prefix chain identical (computed separately).
      - position-aware CDC-beyond: a block is dedupable iff (i, c) recurs (same abs block index
        AND identical content) — this is what raw KV equality requires under RoPE.
      - token-level CDC-beyond upper bound: block content c recurs at ANY index.
    We report blocks reclaimable by each, and the BEYOND-exact-prefix delta."""
    # exact prefix unique set (prefix-hash) -> which (seq,blockidx) are reclaimed
    seen_prefix = set()
    total_blocks = 0
    prefix_reclaimed = 0
    # position-aware: (abs_block_idx, content) seen
    seen_abs = set()
    posaware_reclaimable = 0   # blocks reclaimable by abs-pos content match (incl prefix ones)
    # token-level: content seen anywhere
    seen_content_any = set()
    content_reclaimable = 0    # blocks whose content recurs anywhere
    # phase-aware: (block_idx % 1 ... ) absolute block index already IS the phase at block gran,
    # but intra-sequence the offset within stream matters; blocks are BLOCK-aligned per seq so
    # abs_block_idx already encodes alignment. For sub-block offset shift we note CDC operates on
    # tokens; here block model assumes block-aligned packing.
    for s in seqs:
        prefix_h = b""
        for bi, b0 in enumerate(range(0, len(s), BLOCK)):
            blk = tuple(s[b0:b0+BLOCK])
            total_blocks += 1
            content_h = hashlib.blake2b(repr(blk).encode(), digest_size=16).digest()
            prefix_h = hashlib.blake2b(prefix_h + content_h, digest_size=16).digest()
            # exact prefix
            if prefix_h in seen_prefix:
                prefix_reclaimed += 1
            else:
                seen_prefix.add(prefix_h)
            # position-aware (abs block idx + content)
            keyabs = (bi, content_h)
            if keyabs in seen_abs:
                posaware_reclaimable += 1
            else:
                seen_abs.add(keyabs)
            # content-anywhere (token-level upper bound)
            if content_h in seen_content_any:
                content_reclaimable += 1
            else:
                seen_content_any.add(content_h)
    return {
        "total_blocks": total_blocks,
        "prefix_reclaimed": prefix_reclaimed,
        "posaware_reclaimable": posaware_reclaimable,
        "content_reclaimable": content_reclaimable,
    }

def run_config(n_tenants, shift, label):
    rng = random.Random(SEED + (0 if shift else 1) + n_tenants)
    pool = make_schema_pool(8, rng)
    seqs = build_corpus(n_tenants, pool, rng, shift=shift)
    total_tokens = sum(len(s) for s in seqs)
    tl_total, tl_dup = cdc_token_level(seqs)
    pa = position_aware_dup(seqs)
    bl = block_level_position_aware(seqs)
    # Beyond-exact-prefix at block level:
    prefix_pct = 100.0 * bl["prefix_reclaimed"] / bl["total_blocks"]
    posaware_pct = 100.0 * bl["posaware_reclaimable"] / bl["total_blocks"]
    content_pct = 100.0 * bl["content_reclaimable"] / bl["total_blocks"]
    cdc_beyond_posaware_pct = posaware_pct - prefix_pct
    cdc_beyond_tokenlevel_pct = content_pct - prefix_pct
    reclaimable_bytes_posaware = bl["posaware_reclaimable"] * BYTES_PER_BLOCK
    reclaimable_bytes_prefix = bl["prefix_reclaimed"] * BYTES_PER_BLOCK
    cdc_beyond_bytes_posaware = (bl["posaware_reclaimable"] - bl["prefix_reclaimed"]) * BYTES_PER_BLOCK
    cdc_beyond_bytes_tokenlevel = (bl["content_reclaimable"] - bl["prefix_reclaimed"]) * BYTES_PER_BLOCK
    return {
        "label": label, "n_tenants": n_tenants, "shift": shift,
        "total_tokens": total_tokens, "total_blocks": bl["total_blocks"],
        "token_dup_rate_pct": round(100.0*tl_dup/total_tokens, 3),
        "cdc_token_dup_tokens": pa["cdc_dup_tokens"],
        "cdc_dup_same_abspos_tokens": pa["cdc_dup_same_abspos"],
        "cdc_dup_same_phase_tokens": pa["cdc_dup_same_phase"],
        "cdc_abspos_frac_of_dup_pct": round(100.0*pa["cdc_dup_same_abspos"]/max(1,pa["cdc_dup_tokens"]),3),
        "prefix_reclaimed_blocks": bl["prefix_reclaimed"],
        "prefix_reclaimed_pct": round(prefix_pct,3),
        "cdc_posaware_reclaimable_blocks": bl["posaware_reclaimable"],
        "cdc_posaware_reclaimable_pct": round(posaware_pct,3),
        "cdc_tokenlevel_reclaimable_blocks": bl["content_reclaimable"],
        "cdc_tokenlevel_reclaimable_pct": round(content_pct,3),
        "cdc_beyond_prefix_POSAWARE_pct": round(cdc_beyond_posaware_pct,3),
        "cdc_beyond_prefix_TOKENLEVEL_pct": round(cdc_beyond_tokenlevel_pct,3),
        "cdc_beyond_bytes_posaware_MB": round(cdc_beyond_bytes_posaware/1e6,3),
        "cdc_beyond_bytes_tokenlevel_MB": round(cdc_beyond_bytes_tokenlevel/1e6,3),
        "bytes_per_block": BYTES_PER_BLOCK,
    }

def main():
    configs = []
    for n in [16, 32, 64, 128]:
        configs.append((n, True, f"shift_N{n}"))
    configs.append((64, False, "noshift_N64"))  # control: aligned schemas (prefix-friendly)
    rows = [run_config(n, sh, lab) for (n, sh, lab) in configs]
    fields = list(rows[0].keys())
    out = os.path.join(RESULTS, "cdc_kvdedup_results.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows: w.writerow(r)
    print("WROTE", out)
    for r in rows:
        print(f"[{r['label']}] tok_dup={r['token_dup_rate_pct']}%  prefix={r['prefix_reclaimed_pct']}%  "
              f"CDC_beyond_TOKENLEVEL={r['cdc_beyond_prefix_TOKENLEVEL_pct']}%  "
              f"CDC_beyond_POSAWARE={r['cdc_beyond_prefix_POSAWARE_pct']}%  "
              f"abspos_frac_of_dup={r['cdc_abspos_frac_of_dup_pct']}%")

if __name__ == "__main__":
    main()
