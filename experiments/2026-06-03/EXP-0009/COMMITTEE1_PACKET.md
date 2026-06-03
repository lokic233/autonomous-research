# COMMITTEE#1 — CLAIM-0007 (PROJ-0001), evidence EXP-0009 (L0)
## Honest NEGATIVE: position-dependence (RoPE) kills the cross-tenant KV-dedup mechanism. Token-level CDC finds 4-7% offset-shifted schema dup beyond exact-prefix, but RoPE bakes abs position into K so raw-KV dedup only works at the SAME absolute offset -> position-aware gain collapses to 0.35-1.46% (below the pre-registered threshold). Vote honestly. Revival path the researcher identified: a cheap re-rope/position-shift transform R(delta) on cached K-blocks (CacheBlend-adjacent) — if cheaper than recompute, token-level 4-7% becomes the ceiling and it could revive to PARTIAL. novelty_killer: prior-art sweep owed (LMCache, KVQuant, CacheBlend prefix-independent KV reuse — directly targets this RoPE re-anchoring).

## CLAIM
claim: In multi-tenant agentic LLM serving, content-defined chunking (CDC) of KV-cache
  blocks enables cross-request KV DEDUPLICATION that reclaims significantly more KV
  memory than exact-prefix sharing alone, because agent fleets run near-identical
  tool-schema/boilerplate spans embedded at DIFFERENT offsets across different system
  prompts (which exact-prefix block-hashing misses), and the reclaimed memory translates
  to higher effective batch size / fewer preemptions.
why_it_matters: "Exact-prefix caching (vLLM APC, RadixAttention) only shares from\

## L0 RESULTS (EXP-0009, effect=weaken)
# RESULTS — EXP-0009 (CLAIM-0007): CDC KV-dedup vs exact-prefix sharing

**Verdict: NEGATIVE (position-dependence is the crux and it kills the gain).**
L0, CPU-only, stdlib-only, SERIAL, deterministic word-level tokenizer (transformers NOT installed
on this Mac — stated honestly; 1 word ≈ 1 token). Block size = 16. Seed = 20260603. Wall < 0.1 s.
Numbers below are read from `results/cdc_kvdedup_results.csv` (trust CSV, not stdout).

## Setup
- Synthetic multi-tenant agent corpus: N tenants, each system prompt = interleave of 8 SHARED
  tool-schema boilerplate spans (identical token sequences) + variable-length TENANT-SPECIFIC
  filler inserted between them, plus a random-length tenant header. The filler/header DELIBERATELY
  shift identical schema spans to DIFFERENT absolute offsets across tenants (the exact condition
  the claim needs to beat exact-prefix).
- KV byte model (Qwen2.5-7B-like GQA): 28 layers × 4 KV-heads × 128 head_dim × 2(K,V) × 2 B(fp16)
  × 16 tokens/block = **917,504 B/block (0.875 MiB)**.
- Schemes: (1) exact-prefix block-hash sharing (vLLM APC); (2) CDC/Rabin content-defined-chunk dedup.
- Two dedup levels reported for CDC, per pre-registration:
  - **TOKEN-LEVEL** (upper bound): block/chunk content recurs ANYWHERE (pretends position is free).
  - **POSITION-AWARE** (honest): a KV block is dedupable only if identical content recurs at the
    SAME ABSOLUTE block index (same RoPE rotation) — raw-KV equality requires this.

## Headline numbers (realistic offset-shifted regime, `shift=True`)

| Config | tok dup % | exact-prefix reclaim % | CDC beyond-prefix **TOKEN-LEVEL** % | CDC beyond-prefix **POSITION-AWARE** % | abspos frac of CDC dup-tokens |
|---|---|---|---|---|---|
| N=16  | 0.43 | 0.00 | **4.18** | **0.35** | 0.0% |
| N=32  | 1.16 | 0.00 | **4.47** | **0.64** | 0.0% |
| N=64  | 2.46 | 0.00 | **6.12** | **0.75** | 4.7% |
| N=128 | 2.37 | 0.11 | **6.70** | **1.46** | 7.1% |

Control `noshift_N64` (schemas aligned, no offset shift): tok dup 25.3%, exact-prefix reclaims
20.2%, CDC token-level beyond +24.3%, **CDC position-aware beyond +6.0%**, abspos frac 59.2%.

## Interpretation — the position-dependence verdict (the make-or-break)
1. **The offset-shifted-duplicate opportunity is real but modest at the token level.** When schema
   spans are shifted across tenants, exact-prefix sharing captures ~0% (every tenant's prefix
   differs immediately), while CDC's token-level dedup finds 4–7% of blocks worth of recurring
   content that exact-prefix misses. This is the number a naive reading of the claim would cite.
2. **Position-dependence destroys ~80–95% of that gain.** Because RoPE/absolute position bakes
   position into K, a recurring span is only raw-KV-dedupable if it lands at the SAME absolute
   position. In the shifted regime, only **0.0–7.1%** of CDC-duplicate tokens occur at the same
   absolute offset (`abspos_frac_of_dup`). So CDC-beyond-exact-prefix collapses from 4–7%
   (token-level) to **0.35–1.46%** (position-aware) — below the pre-registered "few %" threshold.
3. **The control proves the mechanism, not the claim.** With schemas ALIGNED (`noshift`), 59% of
   dup tokens share absolute position — but in that aligned case exact-prefix ALREADY reclaims
   20.2%, and CDC-beyond-prefix position-aware is +6.0%. Crucially, alignment is exactly the
   regime where exact-prefix works; the claim's whole premise is the SHIFTED regime, where the
   position-aware CDC gain is ~1%.
4. **CDC chunk boundaries vs 16-token KV-block granularity:** CDC produces variable-length chunks
   that do not align to 16-token block boundaries, so even token-level dup must be re-quantized to
   blocks; the block-level position-aware number already folds this in and it is ~1%.

## Verdict against pre-registered decision rule
- HELD requires position-aware CDC-beyond-prefix > ~10% robustly → **not met** (≤1.5% in the
  shifted regime).
- The honest-negative branch fires on TWO of three conditions: (a) CDC reclaims < a few % beyond
  exact-prefix at the position-aware level (0.35–1.46%); and the realistically-dedupable rate is
  negligible because (the position-dependence of KV) offset-shifted spans almost never share
  absolute position.
- **VERDICT: NEGATIVE.** At the raw-KV level, CDC dedup does NOT meaningfully beat exact-prefix
  sharing for offset-shifted agent boilerplate, because position-dependence (RoPE) means
  offset-shifted identical token spans are NOT identical KV tensors. The claim's core mechanism
  ("dedup the same schema at different offsets") is largely impossible without a re-rotation
  transform.

## What a GPU/real-model pass should measure
1. **Real KV-tensor equality across offset-shifted spans** — confirm at fp16 that K tensors for an
   identical token span at offset Δ differ (RoPE), quantify cosine/MSE vs Δ, and whether any
   tolerance band makes approximate dedup viable.
2. **Re-rope / position-shift transform**: does applying the RoPE rotation delta R(Δ) to a cached
   K-block recover the value needed at a new offset cheaply enough to beat recompute? If a cheap
   re-rotation makes shifted-span dedup correct, the token-level 4–7% becomes the real ceiling and
   the claim could revive to PARTIAL. This is the single most important follow-up.
3. **Real tokenizer (Qwen) on real agent system prompts / tool schemas** to replace the
   word≈token proxy and get true dup rates and chunk-boundary alignment.
4. **End-to-end batch-size/preemption impact** only if (1)+(2) show a positive reclaimable %.

## Prior-art caveat (sweep owed — no network egress on this L0)
KV dedup / cache compression is an emerging area: LMCache (cross-request KV reuse), KVQuant
(KV quantization), and "cache-dedup" lines of work. Position-dependence (RoPE re-anchoring for
reusing KV at new positions, e.g. CacheBlend / prefix-independent KV reuse) is precisely the known
hard problem; some works re-compute or partially re-attend to fix cross-position reuse. A literature
sweep is owed before any HELD/PARTIAL claim — this L0 only establishes the position-dependence
ceiling, not novelty.

## Artifacts
- `PRE_REGISTRATION.md` (committed before runs)
- `scripts/cdc_kvdedup.py`
- `results/cdc_kvdedup_results.csv`
- `logs/run.log`

## PRE-REG (committed pre-run 8c4c339-lineage)
# PRE_REGISTRATION — EXP-0009 (CLAIM-0007)

**Committed BEFORE running.** Researcher researcher-0008, L0 (CPU-only, stdlib, SERIAL, ≤15 min).

## Claim under test (CLAIM-0007)
In multi-tenant agentic LLM serving, content-defined chunking (CDC) of KV-cache blocks enables
cross-request KV DEDUPLICATION that reclaims significantly more KV memory than exact-prefix sharing
alone, because agent fleets run near-identical tool-schema/boilerplate spans embedded at DIFFERENT
offsets across different system prompts (which exact-prefix block-hashing misses), and reclaimed
memory → higher effective batch size / fewer preemptions.

## Hypothesis (H1) and honest-negative branch
- **H1:** CDC/content-defined-chunk dedup of token spans reclaims meaningfully MORE KV blocks than
  exact-prefix block-hash sharing, AND that gain survives the position-dependence reality check.
- **H0 / NEGATIVE branch (report negative if ANY holds):**
  (a) CDC reclaims < ~a few % beyond exact-prefix at the *position-aware* level; OR
  (b) the offset-shifted-duplicate rate is negligible in realistic agent prompts; OR
  (c) CDC chunk boundaries don't align to KV-block (16-token) granularity well enough to dedup.

## THE position-dependence reality check (the crux)
KV blocks are POSITION-DEPENDENT (RoPE / absolute position bakes position into K). Identical token
spans at DIFFERENT byte/token offsets do NOT produce identical KV tensors without re-rotation.
Therefore we report TWO numbers for every dedup measurement:
  - **(a) TOKEN-LEVEL dedupable** — upper bound, pretends position doesn't matter.
  - **(b) POSITION-AWARE dedupable** — the honest number: a duplicate span is only dedupable if the
    duplicate KV blocks land at the SAME intra-sequence position (same absolute token offset, hence
    same RoPE rotation) as a previously-seen instance. We additionally report the relaxed
    "same intra-block phase" variant (offset ≡ mod block_size) as a sensitivity, but the strict
    same-absolute-position number is the headline honest one, since RoPE depends on absolute pos.

## Metrics
- **PRIMARY:** % of KV blocks reclaimable by CDC-dedup BEYOND exact-prefix sharing.
  Reported token-level (upper bound) AND position-aware (honest).
- **SECONDARY:** total reclaimable bytes (KV bytes = blocks × block_size × 2(K,V) × n_layers ×
  n_kv_heads × head_dim × dtype_bytes; we use a representative Qwen2.5-7B-like config, stated below).

## Prompt model (synthetic multi-tenant agent corpus)
- N tenants. Each tenant system prompt = interleave of:
  - SHARED tool-schema boilerplate spans drawn from a fixed pool (identical token sequences,
    e.g. JSON tool definitions, formatting rules, safety preamble);
  - TENANT-SPECIFIC text spans (unique, variable length) inserted BETWEEN shared spans so the
    shared spans land at DIFFERENT absolute offsets across tenants (the offset-shift the claim needs).
- Deterministic word-level tokenizer (transformers NOT installed on this Mac — stated honestly).
  1 word ≈ 1 token. Block size = 16 tokens.
- Params (pre-registered): N_TENANTS=64, shared pool=8 schema spans, tenant-specific spans random
  length 3..40 tokens, seed=20260603. We also run a sensitivity over N and shifting.

## Schemes compared
1. **Exact-prefix block-hash sharing** (vLLM-style automatic prefix caching): a block is shared
   only if its entire prefix (all preceding blocks) is identical → block hash chains from seq start.
   Captures only the COMMON PREFIX across tenants.
2. **CDC / Rabin-style content-defined-chunk dedup:** content-defined boundaries (rolling hash mod
   mask) cut the token stream into variable chunks robust to offset shift; dedup identical chunk
   content across all tenants. Token-level then position-aware filtered.

## Decision rule
- HELD: position-aware CDC-beyond-exact-prefix gain is large (e.g. >10% of blocks) AND robust.
- PARTIAL: token-level gain is large but position-aware gain is small-but-nonzero.
- NEGATIVE: position-aware gain ~0 (position-dependence kills it) OR offset-dup rate negligible.

## Honesty / hygiene
- SERIAL only (multiprocessing blocked on this sandbox). Trust on-disk CSVs, not stdout.
- No GPU, no model, no network. Synthetic corpus; tokenizer limitation stated.
