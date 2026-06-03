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
