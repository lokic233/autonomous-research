# PROJ-0002 — DESCRIPTIVE-PIVOT CANDIDATE (for orchestrator) → recommend DO-NOT-SEED (near-miss)

**Agent:** researcher-0002-descseed · 2026-05-31 · CPU-only · document-only (NO claim/verdict/map edits, NO seeding).
**Probe:** EXP-0040 (level 1, --claim none per BUG-25, ~2.3s). **Recommendation: KILL / DO-NOT-SEED.**

## The angle (the CLAIM-0012 pivot, applied to PROJ-0002's INJECTION stream)
Every prior PROJ-0002 lane asked a PREDICTIVE/cost question (recompute%~inj/seq, win-region, eviction
economics, k~1.3, idle-window, compaction) or characterized the inj/seq MAGNITUDE distribution (EXP-0005,
an order-blind marginal). This lane tried the SAME descriptive pivot that found CLAIM-0012 in PROJ-0003 —
but on the **prefix-cache INVALIDATION / injection event stream** rather than the failure stream:

> *Are LARGE prefix-cache invalidation events temporally OVER-DISPERSED (bursty) within a real agent session,
> vs a permutation null that fixes the result-size multiset and shuffles only ORDER?*

## Why it does NOT seed (the collision check did its job)
Two variants, with a built-in collision control:
- **V1 (inj/seq>5% "costly invalidation"): COLLIDES with EXP-0005.** Big runs-Z (CC −10.3 / Codex −13.3) is
  an S-growth artifact — events front-load (CC mean-pos 0.34, 27/40 sessions), and the permutation null that
  fixes the inj/seq multiset collapses the signal (CC perm_p median 0.12). This is exactly the EXP-0005
  accumulation axis / the EXP-0036 CONTROL-A reduction ("accumulation re-parametrizes the inj/seq prior").
- **V2 (raw top-1/3 result SIZE; S-growth removed): genuinely-NEW, distinct from EXP-0005 (which assumes
  i.i.d. size draws), EXP-0036, the 10 neighbors, and CLAIM-0012 — BUT under the correct permutation null it
  replicates on only 1 of 2 harnesses.** Codex significant (perm_p median 0.076, 27/62 sessions p<0.05);
  Claude NOT (perm_p median 0.30, 4/39). Gemini has no tool-call data, so a 2nd confirming harness is
  unavailable. 1/2 < the domain's cross-harness bar (CLAIM-0012 itself was cautioned at 2/2 + missing Gemini).

## Collision verdict (explicit, as mandated)
| vs | V1 | V2 |
|---|---|---|
| EXP-0005/0015 magnitude distribution | **COLLIDE** (accumulation axis) | DISTINCT (temporal correlation of sizes; EXP-0005 is i.i.d./order-blind) |
| EXP-0036 CONTROL-A (routing→prior) | **COLLIDE** (accumulation re-param) | DISTINCT (no routing/modality; within-session order stat) |
| 10 neighbors + red_zones | DISTINCT (descriptive, not cost-law) | DISTINCT |
| CLAIM-0012 failure-burstiness | DISTINCT stream | DISTINCT stream (injection ≠ failure); sibling method |

## Recommendation → DO-NOT-SEED
The descriptive pivot was worth one shot (it found CLAIM-0012). Result: the only NON-colliding variant (V2,
raw-result-size arrival burstiness) does not clear cross-harness replication under the conservative
permutation test (Codex yes, Claude no, Gemini n/a). V1 is a clean collision with EXP-0005. PROJ-0002's
saturation is reinforced, now also against the descriptive-arrival angle. Revive ONLY if a 2nd harness
(beyond Codex) shows permutation-significant raw-result-size clustering.

## Files
- This doc · experiment_result: experiments/2026-05-31/EXP-0040/experiment_result.md
- impl: experiments/2026-05-31/EXP-0040/impl/exp0040_injection_arrival.py · results/results.json
