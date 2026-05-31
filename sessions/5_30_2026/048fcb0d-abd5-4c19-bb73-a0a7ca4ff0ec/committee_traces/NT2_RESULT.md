# NT2 RESULT — Prefix-Cache Invalidation Law + the REAL repair (H100, pure-CPU, SAFE)
Date: 2026-05-30. Node: <GPU-NODE-A>.

## Honest null first (v1): de-chained "segmented hash" does NOT help (1.0x everywhere)
NT2 originally proposed segmented/position-independent hashing as the repair. MEASURED: 1.0x
reduction at every injection point (nt2_result.json). FALSIFIED. Why: a mid-prompt tool
insertion SHIFTS all downstream tokens into different FIXED 16-token block boundaries, so every
later block's CONTENT changes — not just its parent-hash chain. The cascade is a block-BOUNDARY
ALIGNMENT problem, not a hash-chaining problem. (Used vLLM's real hash_block_tokens logic,
verbatim, to confirm.)

## The correct repair (v2): Content-Defined Chunking (CDC). MEASURED on H100:
Rolling-hash block boundaries (avg ~16 tok) instead of fixed positions, so downstream chunks
re-sync to original content after an insertion:
| inject @ | fixed-block (vLLM) recompute | CDC recompute | reduction |
|---|---|---|---|
| 10% | 90.1% | 2.4% | **45.4x** |
| 25% | 75.4% | 2.4% | **31.7x** |
| 50% | 50.4% | 2.4% | **21.2x** |
| 75% | 25.8% | 2.0% | **13.0x** |
| 90% | 10.7% | 2.0% | **5.4x** |

## NT2 reframed (stronger, evidence-backed)
"The mid-prompt-injection prefix-cache cascade (EDMM's measured 8.21x TTFT penalty) is caused by
FIXED-SIZE block boundaries, not hash chaining (de-chaining gives 0x improvement — measured).
Content-defined chunking re-syncs downstream KV blocks after an insertion, cutting recompute
from up-to-90% to ~2% (5-45x fewer blocks), independent of injection position."
Honest scope: this is a block-reuse/recompute-count model on token streams (the cache-hit
quantity that drives TTFT); a full vLLM CDC integration + wall-clock TTFT is the 30-day step.
Differentiates from Continuum (2511.02230, scheduling) — this is a cache-DATA-STRUCTURE fix.
Artifacts: nt2_segmented_hash.py (null), nt2_cdc.py (repair), nt2_result.json, nt2v2_result.json.
