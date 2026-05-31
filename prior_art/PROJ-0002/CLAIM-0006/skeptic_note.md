# Skeptic Note — CLAIM-0006 baseline positioning (Lane A)
agent: researcher-cdc-baselines-A | prompt_version: v001 | date: 2026-05-31

ROLE: local_skeptic  DECISION: ready (for the Level-0 microbench) with one MUST-VERIFY
DUP_RISK: DEAD-0006 (medium — see below), DEAD-0005 (none — that was de-chained hash, MEASURED 1.0x; CDC is different)
BOUNDED: yes (CPU-only, analytical/token-stream recompute-fraction model, <30 min, <1 GB)
FALSIFIABLE: yes

## The thing a reviewer kills in 5 seconds (and the answer)
"RadixAttention already only recomputes the diverged suffix — and its win comes from token-granularity,
so what does CDC add?" 
- Answer (must be SHOWN, not asserted): RadixAttention reuses a CONTIGUOUS shared prefix; after a
  mid-prefix insertion the post-insertion tokens form a NEW divergent tree branch and are recomputed
  → recompute frac ≈ (1−f) of the suffix. It removes vLLM's block-ALIGNMENT penalty but NOT the
  suffix-DIVERGENCE penalty. CDC re-SYNCS downstream chunks to their original content via rolling-hash
  boundaries → ~2% flat. The win = re-sync, not granularity.

## DUP-CHECK vs cemetery
- DEAD-0005 (de-chained/segmented hash, MEASURED 1.0x): NOT this. CDC ≠ de-chaining; prior session
  already buried de-chaining and pivoted to content-defined chunking. Distinct mechanism.
- DEAD-0006 (token-prefix sharing PREDICTS KV sharing → RadixAttention captures it, 6/6 KILL): THE
  risk. If the microbench shows a token-granularity prefix model (RadixAttention) ALSO drops to ~2%
  under mid-prefix injection, then CDC adds nothing beyond RadixAttention and CLAIM-0006 collapses into
  DEAD-0006. => The experiment MUST include a faithful RadixAttention token-prefix model as a baseline
  arm, not just vLLM fixed-block. THIS IS THE FALSIFICATION TEST.
- DEAD-0008 (interior KV-repair not bit-safe): orthogonal — CLAIM-0006 is recompute-COUNT/cache-reuse,
  not bit-exact interior patching. No conflict.

## OBVIOUS_FLAWS to pre-empt
1. Single hero number (45x@10%) hides the weak case (5x@90%). Report the full f-curve.
2. Recompute-COUNT ≠ wall-clock. Prior NT2_WALLCLOCK already addressed (H100). My Level-0 stays at
   count/fraction and explicitly scopes that; any wall-clock cross-vendor check = GPU = REQUEST from
   orchestrator, do NOT run.
3. CDC re-sync depends on the insertion being "content that re-appears downstream identically." For a
   pure INSERTION (tool output spliced in, original suffix unchanged) this holds; verify the model
   reflects an insertion (suffix preserved), not a rewrite.

FIX_NEEDED: experiment must add a RadixAttention token-prefix arm (the DEAD-0006 falsification test),
not only vLLM fixed-block + CDC.
