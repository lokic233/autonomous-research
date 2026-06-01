# ADJACENT-CLAIM VET r3 — PROJ-0002 (researcher-0006-adjacent-r3, 2026-06-01)

**Role:** researcher · **Node:** cli:dengcchi-mac · CPU/read-only · NO claim/verdict/map edits, NO seeding, NO GPU, READ-ONLY external.
**Mandate:** Vet the BEST next-adjacent claim for PROJ-0002 that is (a) NOT env-blocked, (b) genuinely novel vs MAP-0001,
(c) not a cemetery re-tread, (d) not an accounting identity. Start by honestly evaluating the existing
injection_arrival_EXP-0040 candidate: is it seedable?

## TL;DR — RECOMMENDATION: **KILL / DO-NOT-SEED. Adjacent territory is EXHAUSTED.**
The existing injection_arrival candidate is correctly a DO-NOT-SEED (verified below — the analysis is honest and
its kill stands). After re-deriving the occupancy map from MAP-0001 + 5 independent prior lanes + a fresh web
novelty sweep, **no CPU-doable, genuinely-novel, non-identity, non-cemetery adjacent claim exists.** The
CLAIM-0006 1-degree neighborhood is saturated to the point of over-determination (laneB + laneE + laneD +
adjacent2 + descseed all independently land EARLY-KILL). Keep resources on CLAIM-0006's single binding
GREEN-gate (vLLM>=0.7 V1-KVConnector async-E2E under concurrent load — env-upgrade-gated, human-go) and on
CLAIM-0007 (already PROMOTED).

---
## 1. Verdict on the existing injection_arrival_EXP-0040 candidate: NOT seedable (kill is sound)
I re-read EXP-0040's actual `experiment_result.md` (numbers below) against its candidate note. The kill is HONEST
and CORRECT, not pessimism:

- **V1 (inj/seq>5% "costly invalidation" burstiness): COLLIDES with EXP-0005.** Runs-Z is large (CC -10.3, Codex
  -13.3) but events are front-loaded (CC mean-pos 0.341, 27/40 sessions); the conservative within-session
  permutation null that fixes the inj/seq multiset and shuffles ONLY order collapses the signal (CC perm_p
  median 0.12). This IS the EXP-0005 accumulation axis / the EXP-0036 CONTROL-A reduction ("accumulation
  re-parametrizes the inj/seq prior"). Clean collision. **DEAD.**
- **V2 (raw top-1/3 result SIZE, S-growth removed): genuinely-new framing, confound correctly removed
  (mean-pos ~0.51/0.58, NOT front-loaded), distinct from EXP-0005's i.i.d. size assumption — BUT replicates on
  only 1 of 2 harnesses under the correct permutation null.** Codex significant (perm_p median 0.076, 27/62
  sessions p<0.05); Claude NOT (perm_p median 0.30, 4/39); Gemini has zero tool-call data (same gap CLAIM-0012
  hit). The Stouffer -4.2 on Claude is carried by the size gradient the permutation test correctly removes.
  **1/2 < the domain's cross-harness bar** (CLAIM-0012 itself was cautioned at 2/2 + missing Gemini). A
  single-harness, permutation-marginal arrival-clustering statistic is not a seedable claim.

**My independent assessment:** the descseed agent's statistics are sound and the kill is the right call. The
permutation null is the correct test (it controls the size multiset and isolates order); riding the Stouffer
combine would have been the over-claim, and the note correctly refuses it. This is a textbook early-kill, not a
near-miss worth reviving on current evidence. Revive condition (already in MAP-0001 red_zones) is exactly right:
ONLY if a 2nd harness beyond Codex shows permutation-significant raw-result-size arrival clustering. **No new data
is reachable on CPU here** (Gemini has no tool-call data; only Claude+Codex corpora exist locally), so the revive
condition cannot be met by me. → **DO-NOT-SEED stands.**

## 2. Why there is no next-best alternative — the occupancy map (re-derived, not inherited)
Every 1-degree adjacency of CLAIM-0006 is in the claim itself, a MAP-0001 red_zone, a body-verified neighbor, or
collapses to an accounting identity. Cross-checked against MAP-0001 (full key_prior_work + red_zones) + 5 lanes:

| Adjacent angle | Status | Killing reason |
|---|---|---|
| inj/seq recompute cost-map + win-region | **CLAIM-0006 (occupied)** | The claim itself; surviving leg. |
| CDC-over-radix repair MECHANISM | **DEAD (red_zone)** | Irminsul 2605.05696 twin, 2x-indexed; PIC genus. |
| slope~1 as cross-engine law | **DEAD** | Accounting identity (EXP-0013, contiguous R2=0.0007). |
| injection exponent k~1.3 | **DEAD-0009** | Regime-local crossover, Pope/Kwon FLOP-derivable. |
| idle-window speculative prefill | **DEAD-0010** | Generic speculate-or-skip identity; 2511.20048 + 2605.06472 occupy. |
| compaction-as-prefix-invalidation | **DEAD (EXP-0028)** | == R/S identity at R:=summary; footprint=eviction/TTL (occupied). |
| layer-stratified positional KV reuse | **DEAD-0007** | <1.5% real incidence; revive only >2%. |
| eviction-vs-recompute economics | **KILL (laneB-A)** | Continuum/KVFlow + 9 2026 eviction works; crowded. |
| cumulative-trajectory recompute | **KILL (laneB-B)** | Trivial integral of cost-map over EXP-0005. |
| tool-result DEPENDENCY (semantic staleness) invalidation | **KILL (laneB-C)** | ToolCacheAgent (ICLR'26, openreview 05f7fe08...) + hierarchical-caching dep-graph occupy. |
| count-vs-volume static-policy regret | **KILL (laneB-D)** | Regret==0; CDC pointwise-dominates (analytic); no crossover. |
| spec-decode x invalidation | **KILL (laneE-1)** | DEAD-0010 twin + generic SD bookkeeping. |
| multi-agent shared-context compounding | **KILL (laneE-2)** | Densely occupied (KVFlow/Tokencake/KVCOMM/2601.08343 "when reuse fails"...). |
| harness-routing -> endogenous inj/seq | **DEAD (EXP-0036)** | CONTROL-A: reduces to trajectory-length (EXP-0005) ∘ result-size prior (EXP-0015). |
| repair DISPATCHER (route CDC vs PIC on inj/seq) | **HOLD (laneD)** | Min-selection identity risk; provenance-blocked on the un-measured crossover; routing-axis prior-art (EPIC/KVFlow/CacheClip) NOT body-cleared. |
| descriptive invalidation-arrival burstiness | **DO-NOT-SEED (EXP-0040)** | V1 collides EXP-0005; V2 1/2-harness under permutation null. |

## 3. Fresh novelty sweep (2026-06-01, web) — no new open lane opened, no new collision threat
Checked whether the V2 "large tool results arrive in temporal bursts" angle has either (a) become publishable or
(b) been scooped. Neither changes the verdict:
- **2604.05404** "Beyond Accuracy: Unveiling Inefficiency Patterns in Tool-Integrated Reasoning" — characterizes
  TIR inefficiency patterns (adjacent descriptive territory; reinforces the area is being mined descriptively).
- **2506.02006** workload-aware serving under "dynamic and bursty workloads" — request-level burstiness, the
  serving-systems framing the arrival angle would land inside.
- **2511.20048 / 2512.15834** speculative-tool-call output-length asymmetry — the result-size-distribution
  neighborhood (already a red_zone twin for the speculation angle).
- **2605.00737** "To Call or Not to Call" + **2601.08343** "When KV Cache Reuse Fails in Multi-Agent Systems" —
  tool-necessity / reuse-failure, the dependency+multi-agent neighbors laneB-C/laneE-2 already killed.
None publishes a within-session result-size arrival-clustering statistic — so V2's framing is still not directly
occupied — but V2 dies on EMPIRICS (1/2 harness), not novelty, so this is moot. No web result reopens a killed
lane or threatens CLAIM-0006/0007.

## 4. Honest conclusion
The descriptive-pivot was the last genuinely-distinct angle (it found CLAIM-0012 in PROJ-0003), and it was worth
one shot. It returned a single-harness, permutation-marginal result that does not clear the bar. With:
- every PREDICTIVE/cost angle dead or an accounting identity,
- every descriptive-arrival operationalization either colliding (V1) or 1/2-harness (V2),
- the cross-project angle reducing to EXP-0005/0015 (EXP-0036 CONTROL-A),
- the dispatcher angle provenance-blocked AND min-selection-identity-risky,
- and no CPU-reachable data to satisfy any revive condition,

**PROJ-0002's adjacent territory is exhausted.** I decline to manufacture a fresh claim id — seeding now would
either re-tread a red_zone, collide with a body-verified neighbor, or rest on an accounting identity, all of which
the mandate explicitly forbids. The intellectually honest output is a KILL.

**Recommendation to orchestrator: KILL the adjacent-claim hunt. Do NOT seed. Concentrate remaining resources on
CLAIM-0006's single binding GREEN-gate (vLLM>=0.7 V1-KVConnector async-E2E under concurrent load, env-upgrade /
human-go) and on the already-promoted CLAIM-0007.** Saturation is now confirmed by SIX independent lanes
(laneB + laneE + laneD + adjacent2 + descseed + this r3 vet).

## Files
- This doc (prior_art/PROJ-0002/ADJACENT_CLAIM_r3_2026-06-01.md)
- Re-read: EXP-0040 experiment_result.md; MAP-0001; laneB/laneE/laneD/adjacent2 gap analyses; novelty_boundary;
  related_work; NEW_CLAIM_CANDIDATE_injection_arrival_EXP-0040.md; needs_attention.md
- No experiment run (vet was a read+novelty-sweep; no new probe was warranted — EXP-0040 already probed the only
  live angle and the kill is sound).
