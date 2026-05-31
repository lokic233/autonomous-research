# Prior-Art Note — CLAIM-0006 baseline positioning (Lane A)
agent: researcher-cdc-baselines-A | role: researcher | prompt_version: v001
date: 2026-05-31 | scope: how the 3 mandatory baselines handle a MID-prefix injection.

## The claim under test
CLAIM-0006: mid-prompt tool injection breaks the prefix-cache hash chain; chained-decode-cache
(CDC = content-defined chunking) repair achieves ~2% recompute vs full-suffix recompute. Prior
evidence (sess 048fcb0d): on a token-stream block-reuse model using vLLM's REAL hash_block_tokens
logic, fixed-block recompute is up-to-90% (position-dependent), CDC is ~2.0-2.4% (position-
INDEPENDENT) → 5.4x–45.4x fewer recomputed blocks; H100 wall-clock confirms 11.6x@8k, 119.6x@32k.

## Mechanism of each mandatory baseline under a mid-prefix insertion

### 1. vLLM Automatic Prefix Caching (APC) — PagedAttention, SOSP'23
- Source: docs.vllm.ai .../design/automatic_prefix_caching.html (primary).
- KV partitioned into **fixed-size KV blocks** (default block_size=16 tokens). Each block keyed by
  `hash(prefix tokens + block tokens)` — a one-to-one map block-hash <-> physical KV block, in a
  global hash table (no tree; blocks independent; LRU eviction with longest-prefix tiebreak).
- Behaviour under mid-prefix INSERTION at position p: inserting tokens (a) changes the *prefix* of
  every downstream block, AND (b) **shifts token→block alignment** (the fixed 16-tok grid re-aligns),
  so every block after p has different *content*. The reuse rule is a CONTIGUOUS longest-prefix match
  → first miss at the block containing p → **all blocks after p are recomputed** (full-suffix recompute).
- Partial repair for an interior insertion: **NONE**. APC has no mechanism to re-sync downstream blocks.
  (This is the EDMM 8.21x TTFT cascade.)

### 2. SGLang RadixAttention — NeurIPS'24 (arXiv 2312.07104)
- Source: arxiv.org/html/2312.07104v2 (primary, §RadixAttention + App. A).
- Radix tree mapping **token sequences → KV tensors**; pages are **token-granularity (page size = 1
  token)**, not 16-tok blocks. Runtime does prefix matching + reuse; LRU evicts leaves first.
- STRONGEST baseline because token-granularity avoids vLLM's block-ALIGNMENT shift: there is no fixed
  16-tok grid to re-align. BUT a radix tree still only reuses a **shared (contiguous) prefix**. A
  mid-prefix insertion creates a NEW divergent path at the insertion token; everything after the
  insertion is a different token sequence → a new tree branch → **recomputed**. No re-sync/repair of
  the post-insertion suffix back to the cached original.
- So RadixAttention removes the *alignment* component of the cascade but NOT the *suffix-divergence*
  component: recompute fraction under an insertion at position p ≈ (N−p)/N of the suffix tokens.

### 3. FlashInfer — attention kernel library (Cascade Inference, flashinfer.ai 2024-02-02)
- Source: flashinfer.ai/2024/02/02/cascade-inference.html (primary).
- FlashInfer is a **kernel library** (efficient prefill/decode attention, shared-prefix "cascade"
  batch decode, paged KV layout). It does NOT own a cache-eviction / prefix-invalidation policy — it
  consumes the page table / block layout the serving engine (vLLM/SGLang) hands it.
- Under mid-prefix injection: FlashInfer simply computes attention over whatever span the engine marks
  dirty. It has **no partial-repair of its own**; its recompute fraction == the host engine's. Its only
  relevant edge (cascade inference) is for *batch* shared-prefix decode, orthogonal to single-sequence
  mid-prefix repair.

## Head-to-head summary (recompute fraction under insertion at fractional position f = p/N)
| baseline | block grain | match type | partial re-sync? | recompute frac @ inject f |
|---|---|---|---|---|
| vLLM APC | fixed 16-tok | hash(prefix+block), contiguous | NO | ~(1−f) of blocks (+alignment) |
| SGLang RadixAttention | 1-tok page | radix-tree shared prefix | NO | ~(1−f) of suffix tokens |
| FlashInfer | (engine's) | none (kernel only) | NO | == host engine |
| **CDC (CLAIM-0006)** | content-defined (avg~16) | rolling-hash re-sync | **YES** | **~2% (position-independent)** |

## Baseline implications for the experiment
1. The fair, falsifiable head-to-head is RECOMPUTE FRACTION under a single mid-prefix insertion at
   varying f. CDC's claim is position-INDEPENDENCE (~2% flat); every baseline is position-DEPENDENT
   (~(1−f)). The win is largest for EARLY injection (small f), smallest for late injection (f→1).
2. RadixAttention is the binding baseline. At f→0.9 a baseline recomputes only ~10%, so CDC's ~2%
   is only ~5x there — must report the WHERE-IT-WINS curve, not a single hero number. (Matches prior
   5.4x@90% vs 45.4x@10%.)
3. DEAD-0006 caution: token-prefix sharing PREDICTS KV sharing → RadixAttention captures it. CDC is
   NOT claiming a new KV-sharing regime; it claims re-SYNC AFTER a divergence, which radix-prefix
   matching does NOT do. This is the line that keeps CLAIM-0006 out of DEAD-0006's grave — must verify
   in the microbench that RadixAttention (token-granularity prefix) really does recompute the full
   diverged suffix and does not "accidentally" re-sync.

## Collision risk
- vLLM APC / RadixAttention / FlashInfer: **low** collision — none implements post-insertion re-sync;
  they are baselines, not the same idea.
- ContiguousKV (arXiv 2601.13631) "granularity-aligned KV" and "When to Commit? variable-size blocks"
  (arXiv 2604.23994, diffusion) — MEDIUM: variable/content-aware block ideas exist adjacently; verify
  none does mid-prefix re-sync for autoregressive prefix cache. (Flag for committee, not fatal.)
