# PROJ-0001 Adjacent-Claim Mining + Saturation Re-test — researcher-0001-laneD

**Date:** 2026-05-31 · **Agent:** researcher-0001-laneD (CPU-only mining lane) ·
**Orchestrator session:** 22bd6bef-b84b-4827-a371-87443ea8602f
**Scope:** READ-ONLY adjacent-claim hunt. NO claims/verdicts/map edits. NO GPU/model/memory probes
(MI350X_CRASH_POSTMORTEM honored). NO binding to any promoted claim (BUG-25 lesson honored).
**Method:** independent re-derivation of the territory, then HEAVY early-kill of every adjacent
idea against the 5 promoted claims (0001/0002/0003/0004/0007), the weakened CLAIM-0005, the 10
DEAD ideas (0001-0010), MAP-0001 red_zones/open_gaps, and the crash forbidden-zone.

## TL;DR
**PROJ-0001 is SATURATED. CONFIRMED — laneD independently reaches laneB's conclusion via a
DISJOINT set of candidate gaps.** I generated 9 adjacent ideas (the 3 assigned directions + 6
fresh ones laneB did not enumerate). Every one is KILLED: occupied by a promoted claim, buried as
a DEAD idea, fenced by a red_zone, FORBIDDEN (GPU mapping probe), or a derivable accounting
identity (the recurring DEAD-0009/DEAD-0010 failure mode). **No genuinely-open, not-occupied,
not-dead adjacent claim exists in the MAP-0001 / PROJ-0001 territory.** No experiment registered,
no claim seeded. Recommend orchestrator keep PROJ-0001 mature/closed.

## Territory map (what the 5 promoted claims already own)
- CLAIM-0001: HW VMM CoW DOMINATED for agent KV (0/12 win-region; 1.06-2.20x slower than SW
  prefix-share, 41-152x slower than FlashInfer). The "is CoW ever worth it" question = CLOSED.
- CLAIM-0002: NVIDIA ~520K per-context VMM mapping ceiling (523,404 +/-0.6%) is a VENDOR
  portability cliff; AMD no wall at 80M (153x). The cross-vendor ceiling question = CLOSED.
- CLAIM-0003: ceiling+CoW+slowdown COMPOUND into end-to-end throughput collapse (HW 0/8 fanout
  regimes, crashes B>=128, SW 280->800 tok/s). The end-to-end throughput story = CLOSED.
- CLAIM-0004: Mapping-Budget Wall — conserved per-context VMM mapping budget governs branch
  fanout, root-caused cross-vendor. The predictive resource model = CLOSED.
- CLAIM-0007: Attention-visible GPU-MMU write-after-share is bit-identical, kernel-transparent =
  the ONE real HW-CoW capability delta. The "what CAN HW do that SW can't" question = CLOSED.
- CLAIM-0005 (weakened) + DEAD-0009: the injection-recompute exponent k~1.3 is a regime-local
  accounting-derivable crossover slope, not a law. The recompute-scaling-law question = CLOSED.

## Per-idea kill ledger (HEAVY early-kill)

### Assigned direction 1 — "cross-vendor portability cost models beyond the 520K ceiling"
| Idea | Verdict | Collision evidence |
|---|---|---|
| 1a. Measure AMD's TRUE mapping ceiling (push past 80M) | **KILL — FORBIDDEN + gold-plate** | DUPLICATE of laneB's first kill. CLAIM-0002 already GREEN at 153x divergence; a precise K_amd is decision-irrelevant (CROSSVENDOR_RESULT: "claim is >=4M no wall, not a measured K_amd"). FORBIDDEN by MI350X_CRASH_POSTMORTEM: unbounded mapping probes (alloc AND teardown) crashed the node 3x incl a 4-5h HW repair. Revival = NEVER via this method. |
| 1b. A quantitative cross-vendor PORTABILITY COST MODEL (predict NVIDIA fanout ceiling from AMD-measured params, or $/branch portability tax) | **KILL — occupied + identity** | The predictive resource model IS CLAIM-0004 (Mapping-Budget Wall: conserved per-context budget governs fanout, root-caused cross-vendor). A "cost model" layered on it is K=branches x prefix_pages (already the stated ceiling formula in CROSSVENDOR_RESULT) divided by granule (2MiB NVIDIA / 4KB AMD) — i.e. a deterministic arithmetic restatement of CLAIM-0002+0004, not a discovery. Same DEAD-0009/-0010 accounting-identity failure mode (no non-derivable anomaly). |
| 1c. Third-vendor ceiling (Intel/Habana/Trainium VMM) | **KILL — measure-zero + no HW** | DUPLICATE of laneB. Same logic as DEAD-0003: a vendor WITH a CoW win-region would CONTRADICT CLAIM-0001; a vendor WITHOUT a wall just re-confirms "NVIDIA-specific." Either way revival-only, not an open gap. Also CPU-only: no such HW reachable, and any VMM probe is forbidden. |

### Assigned direction 2 — "the COMPOUND throughput-collapse story's untested corners"
| Idea | Verdict | Collision evidence |
|---|---|---|
| 2a. Throughput collapse under DIFFERENT batch/fanout regimes than the measured 8 | **KILL — occupied, monotone** | CLAIM-0003 already spans 0/8 fanout regimes AND "crashes for all B>=128." The collapse is monotone in fanout+batch (more branches -> more mappings -> hit the CLAIM-0004 budget -> CLAIM-0003 crash). Untested cells are interpolations/extrapolations of an already-monotone GREEN result; no new regime can invert the sign (CLAIM-0001 0/12 win-region forbids a HW-win cell). Gold-plating a GREEN claim, not a new gap. |
| 2b. Collapse under MULTI-CONTEXT / multi-tenant concurrency (does it super-scale?) | **KILL — DEAD-0004 red_zone** | Directly fenced: "super-linear multi-ctx VMM degradation = per-worker memory ARTIFACT, RETRACTED (DEAD-0004); revive only with a clean isolated >linear measurement." Reviving requires isolated GPU multi-worker VMM measurement = forbidden probe class + retracted-artifact territory. KILL. |
| 2c. Collapse vs a DIFFERENT software baseline (LMCache/TGI/DeepSpeed) | **KILL — adds no decision value** | CLAIM-0001/0003 already measure vs the dominant baselines (vLLM APC, RadixAttention, FlashInfer @ 41-152x). A weaker SW baseline only widens the HW deficit; a stronger one widens it more. No baseline can produce a HW win-region (CLAIM-0001). Restates a GREEN negative result. |

### Assigned direction 3 — "agentic-KV allocation patterns not covered by CoW/ceiling/throughput theses"
| Idea | Verdict | Collision evidence |
|---|---|---|
| 3a. A KV-sharing regime that token-prefix sharing does NOT capture (new allocation pattern) | **KILL — DEAD-0006** | Exactly DEAD-0006's revival condition ("only if a KV-sharing regime exists that token-prefix sharing does NOT capture"). DEAD-0006 was 6/6 KILL: token-prefix sharing PREDICTS KV sharing -> RadixAttention already captures it. No such regime found; this is the open revival door, not a new gap. |
| 3b. Layer/position-stratified reuse as an allocation pattern | **KILL — DEAD-0007 red_zone** | Fenced: "layer-stratified positional KV reuse capped at 1.5% real incidence (DEAD-0007); revive only if real-trace incidence > 2%." Below kill bar; revival needs a real-trace incidence measurement, not available CPU-only and already attempted. |
| 3c. Interior / mid-sequence edit allocation (repair-in-place branching) | **KILL — DEAD-0008** | Fenced: interior KV-repair is NOT bit-safe (max|dK| 4.04 at every layer>=1); reframed into CLAIM-0006 (PROJ-0002). Terminal/prepend edits already captured by CLAIM-0006. KILL. |

### Fresh angles laneB did NOT explicitly enumerate (my own generation)
| Idea | Verdict | Collision evidence |
|---|---|---|
| F1. Granularity as the design lever: would a SMALLER NVIDIA VMM granule (if config'd <2MiB) lift the 520K ceiling? | **KILL — identity, no knob, forbidden** | CROSSVENDOR_RESULT already attributes the ceiling to per-context mapping-METADATA, NOT granule alone (NVIDIA 2MiB granule -> 520K; AMD 4KB -> no wall). But the ceiling is "independent of vm.max_map_count (392 VMAs vs 67M)" — it is a driver-internal metadata cap, not a user-tunable granule. No exposed knob to test. Any test = forbidden GPU mapping probe. The relationship is a deterministic restatement of CLAIM-0002/0004 (budget = metadata slots). KILL. |
| F2. Does the 520K ceiling shift with a DRIVER UPDATE (temporal portability)? | **KILL — out of lane + forbidden** | This is exactly needs_attention.md #2 ("a driver update could change the number — re-probe before paper-track"). It is a paper-track RE-VERIFICATION chore for CLAIM-0002, owned by the claim/orchestrator, NOT a new adjacent claim. And re-probing = forbidden GPU probe. Not a discovery; a maintenance recheck. KILL as new-gap; flag to orchestrator as the existing known recheck. |
| F3. HW-CoW write-after-share (CLAIM-0007 delta) used for a NON-perf purpose: deterministic replay / debugging / provenance of branch edits | **KILL — DEAD-0001/0002** | Any "the capability is useful for X" angle for X in {isolation, attestation, provenance} is buried: DEAD-0001 (isolation: SW matches bit-identically + 240x faster at fork), DEAD-0002 (attestation: handle is a userspace int, forgeable). Provenance/replay reduces to the same SW-refcount-suffices argument (SW can snapshot the same bytes). No HW-rooted necessity. KILL. |
| F4. CoW edit LATENCY / atomicity as a characterizable contribution (not capacity, the time axis) | **KILL — laneB-killed + dominated** | DUPLICATE of laneB's "write-after-share beyond bit-identity" kill. CLAIM-0001/0003 already establish CoW is dominated/collapses; characterizing the latency of a dominated mechanism is not a contribution (no win-region to defend). KILL. |
| F5. Speculative / predictive allocation to PRE-WARM branch mappings under idle windows | **KILL — DEAD-0010 + open_gap fenced** | Directly the DEAD-0010 red_zone (idle-window speculative prefill: break-even h*f>=alpha/(1+alpha) is a generic accounting identity; occupied by arXiv:2511.20048 + 2605.06472). Pre-warming MAPPINGS specifically also runs into CLAIM-0004 (the budget is the bottleneck, not warm-up latency) and forbidden probes. KILL. |
| F6. A "when-to-use VMM-CoW" DECISION PROCEDURE / unified design-guidance paper | **KILL — DEAD-0003** | Exactly DEAD-0003: "TRUE-branch is measure-zero (C* 0/12 win-region) -> 'use VMM CoW' fires never -> A*+C* stapled, not a discovery. Superseded by T-TAX (=CLAIM-0003)." KILL. |

## Cross-cutting observation (why the area is structurally saturated)
Three of my fresh kills (1b, F1, the cost-model family) and three of the prior deaths (DEAD-0009,
DEAD-0010, and the slope~1 red_zone for CLAIM-0006) die the SAME way: the candidate "discovery"
reduces to a deterministic accounting identity already implied by CLAIM-0002/0004 (mapping budget =
metadata slots = branches x prefix_pages / granule) or by textbook FLOP accounting. The territory's
two load-bearing quantities (the mapping budget and the prefill FLOP curve) are BOTH already
characterized AND shown to be derivable, so any adjacent "law/cost-model" angle is pre-killed by the
identity test. This is the signature of a saturated negative-result area: the remaining moves are all
either (a) restatements of the conserved quantity, (b) revivals that would CONTRADICT a GREEN claim,
or (c) forbidden GPU probes. There is no fourth category left.

## Disjointness from laneB (independent confirmation)
laneB killed 6 candidates; I share only 2 by construction (1a AMD-true-ceiling; F4 write-after-share
latency) and reached the SAME verdict on both. My other 7 (1b cost-model, 1c third-vendor, 2a-2c
collapse corners, 3a-3c allocation patterns, F1-F3/F5-F6) are largely NEW framings and ALL die to
the existing fence. Two researchers, disjoint candidate sets, identical conclusion = strong saturation
signal.

## Conclusion
NO genuinely-open, not-occupied, not-dead adjacent claim exists. PROJ-0001 remains a saturated,
mature negative-result project. The only residual work is paper-track writing of the 5 promoted
claims + the already-logged needs_attention rechecks (F2 driver-update re-probe is a CLAIM-0002
maintenance item, NOT a new claim — and is forbidden to run here). Recommend orchestrator keep
PROJ-0001 mature/closed.

(No claims seeded. No verdicts. No map edits. No experiments registered. CPU-only, no GPU/memory/model probes. No binding to any promoted claim.)
