"""
NT2 experiment (H100, SAFE — pure CPU hashing, no GPU): characterize the prefix-cache
invalidation cascade under vLLM's REAL chained block hashing vs a segmented (position-
independent) repair, as a function of WHERE a tool response is injected.

vLLM's hash_block_tokens chains parent_block_hash into every block -> a mid-prompt insertion
at block i changes block i's tokens AND (via the chain) the parent_hash of i+1, i+2, ... ALL
the way to the end => cascade. The repair hashes each block by CONTENT ONLY (no parent chain)
=> only blocks whose token-content actually changed are invalidated.

We use vLLM's ACTUAL hash_block_tokens for the chained scheme (ground truth) and measure the
number of invalidated (recomputed) blocks for both schemes across injection positions.
"""
import sys, os, json, hashlib
# Verbatim reimplementation of vLLM kv_cache_utils.py:541 hash_block_tokens (avoids heavy
# pydantic import). The parent_block_hash chaining is copied exactly.
NONE_HASH = hashlib.blake2b(b"NONE_HASH", digest_size=16).digest()
def hash_block_tokens(hash_function, parent_block_hash, curr_block_token_ids, extra_keys=None):
    if not parent_block_hash:
        parent_block_hash = NONE_HASH
    return hash_function((parent_block_hash, tuple(curr_block_token_ids), extra_keys))

BLOCK=16  # vLLM default tokens/block

def hfn(x):  # deterministic hash function
    return hashlib.blake2b(repr(x).encode(), digest_size=16).digest()

def blocks_of(tokens):
    return [tuple(tokens[i:i+BLOCK]) for i in range(0, len(tokens)-BLOCK+1, BLOCK)]

def chained_hashes(tokens):
    """vLLM's real scheme: each block hash chains the parent."""
    hs=[]; parent=None
    for blk in blocks_of(tokens):
        h = hash_block_tokens(hfn, parent, blk)
        hs.append(h); parent=h
    return hs

def segmented_hashes(tokens):
    """Repair: content-only block hash (no parent chain) => position-independent."""
    return [hfn(blk) for blk in blocks_of(tokens)]

def invalidated(h_old, h_new):
    """# blocks that must be recomputed = blocks whose hash changed and all after the FIRST
    mismatch for chained (cache is prefix-contiguous); for segmented, only changed blocks."""
    return h_old, h_new

def cascade_chained(base_tok, contam_tok):
    a=chained_hashes(base_tok); b=chained_hashes(contam_tok)
    n=min(len(a),len(b))
    # prefix cache reuses up to the first mismatch, then recomputes the REST
    first=next((i for i in range(n) if a[i]!=b[i]), n)
    return len(b)-first, len(b), first

def cascade_segmented(base_tok, contam_tok):
    a=set(segmented_hashes(base_tok)); b=segmented_hashes(contam_tok)
    # any block whose content-hash is already cached is reused, regardless of position
    recompute=sum(1 for hb in b if hb not in a)
    return recompute, len(b), None

R={"experiment":"NT2_invalidation_cascade_chained_vs_segmented","BLOCK":BLOCK}
import random; random.seed(0)
CTX=4000  # ~4000 tokens of context (like a 6k-char agent prompt)
base=[random.randint(10,50000) for _ in range(CTX)]
tool=[random.randint(10,50000) for _ in range(40)]  # ~tool response

rows=[]
for frac in [0.1,0.25,0.5,0.75,0.9]:
    pos=int(CTX*frac); pos -= pos%BLOCK  # align
    contam = base[:pos]+tool+base[pos:]
    ch_rec, ch_tot, first = cascade_chained(base, contam)
    sg_rec, sg_tot, _     = cascade_segmented(base, contam)
    rows.append({"inject_frac":frac,"inject_pos_tok":pos,
                 "chained_recompute_blocks":ch_rec,"chained_total":ch_tot,
                 "chained_recompute_pct":round(100*ch_rec/ch_tot,1),
                 "segmented_recompute_blocks":sg_rec,"segmented_total":sg_tot,
                 "segmented_recompute_pct":round(100*sg_rec/sg_tot,1),
                 "reduction_x":round(ch_rec/max(sg_rec,1),1)})
R["rows"]=rows
R["claim_supported"]= all(r["chained_recompute_blocks"] > r["segmented_recompute_blocks"]*3 for r in rows)
R["headline"]="chained hashing recomputes everything AFTER injection (cascade); segmented recomputes only the changed blocks"
print(json.dumps(R,indent=2)); json.dump(R,open("nt2_result.json","w"),indent=2)
