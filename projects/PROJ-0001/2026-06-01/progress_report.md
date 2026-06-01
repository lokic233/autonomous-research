# PROJ-0001 — Beginning-of-Day Progress Report (2026-06-01 UTC)

**Project:** GPU CUDA-VMM as the wrong abstraction for agentic KV branching
**Orchestrator:** orchestrator-r3-001 · **Rescan:** full claims+verdicts+cemetery, project_id-filtered (no cross-project leak)
**Headline:** PROJECT DONE / CLOSED. 5 promoted GREEN claims, camera-ready paper. Frontier exhausted; new-claim hunt confirms exhaustion (8th disjoint lane, r3).

## Proved / Promoted (6/6 GREEN committee)
| Claim | Verdict | One-liner |
|---|---|---|
| CLAIM-0001 | VERDICT-0001 green | HW VMM CoW is DOMINATED for agent KV (0/12 win-region; 1.06–2.20× slower than SW prefix-sharing). |
| CLAIM-0002 | VERDICT-0002 green | NVIDIA ~520K CUDA-VMM per-device mapping ceiling = vendor-specific portability cliff (reproduced; AMD MI350X no wall). |
| CLAIM-0003 | VERDICT-0003 green | Ceiling+CoW+slowdown COMPOUND into E2E throughput collapse (HW wins 0/8 fanout regimes). |
| CLAIM-0004 | VERDICT-0005 green | The Mapping-Budget Wall: conserved per-device VMM mapping budget governs branch fanout (root-caused). |
| CLAIM-0007 | VERDICT-0008 green | Attention-Visible GPU-MMU Write-After-Share: a forked branch's CoW edit is bit-identical/attention-visible. |

## Killed / Closed-negative
| Claim | Verdict | Disposition |
|---|---|---|
| CLAIM-0005 | VERDICT-0006, VERDICT-0019 yellow | CLOSED negative: super-quadratic injection pathology DEAD; measured k~1.3 (sub-quadratic). Not a discovery. |

## Cemetery (10 dead ends, project-filtered)
DEAD-0001..0008 (2026-05-30), DEAD-0009..0010 (2026-05-31). Covers bit-exact-determinism, AMD-HW-CoW-win-region (DEAD-0003), isolation-primitive, handle-attestation, slope-1 accounting identities, etc.

## In-progress (r3 lanes — both CONFIRM closure, no open work)
- **gapmine-r3** (DONE): mined MAP-0001 as 8th disjoint early-kill lane; 6 fresh candidate angles (G1–G6) ALL killed to the same three closed forces (accounting-identity / occupied-by-published / forbidden-probe). EXHAUSTION-CONFIRMED. NO seed. Deliverable: prior_art/PROJ-0001/GAPMINE_r3_2026-06-01.md.
  - Probe-free by-product: CLAIM-0001's 0/12 SW-win region analytically TRANSFERS to AMD without a probe (AMD 4KB granule → 512× worse per-op fork tax; per-op cost dominates per CLAIM-0001). Retires the DEAD-0003 AMD-revival door as predicted-no-anomaly. → map-delta to apply.
- **freshseed-r3** (DONE): publication hardening + cross-project leverage scan. Deliverable: prior_art/PROJ-0001/PUB_HARDENING_r3_2026-06-01.md.

## Status: DONE. No further claims to seed. Maintain at floor for monitoring; redirect spare effort to PROJ-0003 (live committee work).
