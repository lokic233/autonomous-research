# PROJ-0001 — GPU CUDA-VMM as wrong abstraction for agentic KV branching

**Stage:** candidate  ·  **Target venue:** ATC/EuroSys/OSDI/MLSys  ·  **Updated:** 2026-05-31T12:14:42Z

## Claims under this project
| Claim | Status | Stage | One-liner |
|---|---|---|---|
| CLAIM-0001 | promoted | paper-track | HW VMM CoW is dominated for agent KV (0/12 win-region; 1.06-2.20x slower than software pre |
| CLAIM-0002 | promoted | paper-track | The NVIDIA ~520K CUDA-VMM per-context mapping ceiling is a vendor-specific portability cli |
| CLAIM-0003 | promoted | paper-track | Ceiling + CoW + slowdown COMPOUND into end-to-end throughput collapse: HW wins 0/8 fanout  |
| CLAIM-0004 | promoted | candidate | The Mapping-Budget Wall: a conserved per-context VMM mapping budget governs branch fanout  |
| CLAIM-0005 | weakened | exploration | Tool-call mid-prompt injection is a SUPER-quadratic recompute pathology. |

## Promotion gate (candidate -> next)
Entry criteria for current stage: initial evidence + baseline matrix + prior-work stub + evidence brief
Promoted (6/6 GREEN) claims: CLAIM-0001, CLAIM-0002, CLAIM-0003, CLAIM-0004

## Evidence
Experiments: see experiments/2026-05-30/ (archived) + registry/experiments/ (live), linked from each claim's supporting_evidence.
Prior art: prior_art/ (per-claim notes + PROJ packet).
Dead ends: registry/cemetery/ (do not re-propose).

## Paper story (draft)
The unifying thesis: GPU CUDA-VMM is the wrong abstraction for agentic KV branching — characterized (mapping-ceiling cliff), shown dominated (CoW 0/12 win-region), proven to collapse end-to-end (throughput). Plus the one real HW capability delta: attention-visible bit-identical write-after-share.
