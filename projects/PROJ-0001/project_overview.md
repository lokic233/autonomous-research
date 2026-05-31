# PROJ-0001 — GPU CUDA-VMM as wrong abstraction for agentic KV branching

**Stage:** candidate  ·  **Target venue:** ATC/EuroSys/OSDI/MLSys
**Prior art:** ../../prior_art/PROJ-0001/  ·  **Experiments:** ../../experiments/<date>/  ·  **Dead ends:** ../../registry/cemetery/PROJ-0001/

## Thesis
GPU CUDA-VMM is the wrong abstraction for agentic KV branching: characterized (mapping-ceiling cliff), shown dominated (CoW 0/12 win-region), proven to collapse end-to-end. One real HW capability delta: attention-visible bit-identical write-after-share.

## Claim roster
| Claim | Status | Stage | One-liner |
|---|---|---|---|
| CLAIM-0001 | promoted | paper-track | HW VMM CoW is dominated for agent KV (0/12 win-region; 1.06-2.20x slower than so |
| CLAIM-0002 | promoted | paper-track | The NVIDIA ~520K CUDA-VMM per-context mapping ceiling is a vendor-specific porta |
| CLAIM-0003 | promoted | paper-track | Ceiling + CoW + slowdown COMPOUND into end-to-end throughput collapse: HW wins 0 |
| CLAIM-0004 | promoted | candidate | The Mapping-Budget Wall: a conserved per-context VMM mapping budget governs bran |
| CLAIM-0005 | weakened | exploration | Tool-call mid-prompt injection is a SUPER-quadratic recompute pathology. |

## Promotion gate
Stage `candidate` → next requires the standard research-os gate (see engine rules).
