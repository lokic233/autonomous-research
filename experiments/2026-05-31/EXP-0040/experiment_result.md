# EXP-0040 Result — DESCRIPTIVE arrival-process probe of prefix-cache INVALIDATION events

**Agent:** researcher-0002-descseed · **Project:** PROJ-0002 · **Claim:** none (new-idea probe per BUG-25)
**Level 1 · CPU-only · deterministic (seed 20260531) · ~2.3s · <50MB.** NO GPU/torch/CUDA/model CLIs/memory probes.
Corpora: ~/.claude/projects (40 usable sessions ≥8 tool-results), ~/.codex (62 usable). ~/.gemini = NO tool-call
data (only user/gemini text, 0 sessions ≥8 — same gap CLAIM-0012 hit).

## The descriptive pivot (the CLAIM-0012 move, applied to the INJECTION stream)
All prior PROJ-0002 lanes asked PREDICTIVE/cost questions (recompute%~inj/seq, win-region, eviction economics,
k~1.3, idle-window speculation, compaction) + the workload MAGNITUDE distribution (EXP-0005, an order-blind
marginal of inj/seq). NONE measured the **temporal ARRIVAL PROCESS** of prefix-cache invalidation events.
This probe asks ONE purely-descriptive question (no prediction, no cost-law):

> *Within a real agent session, are LARGE prefix-cache invalidation events temporally OVER-DISPERSED (bursty)
> vs a within-session permutation null that fixes the result-size multiset but shuffles ORDER?*

This is distinct from CLAIM-0012 (which measured the FAILURE stream); here the stream is the
INJECTION/invalidation stream (tool RESULTS appended to the prefix).

## Two operationalizations + the built-in collision control
- **V1 = inj/seq>5% events** — the "costly invalidation" indicator. *Pre-flagged collision risk:* inj/seq is
  small/large mostly because of accumulated context S (small early → big inj/seq early). Front-loading would
  make V1 reduce to the EXP-0005 **accumulation axis** (its "no-accumulation→6.3%" sensitivity input).
- **V2 = raw top-1/3 result SIZE (R tokens)** — S-growth REMOVED. Asks whether LARGE TOOL RESULTS arrive in
  bursts. EXP-0005 models R as **i.i.d. size draws** (no temporal correlation), so this is NOT an EXP-0005 fact.

Test: per-session Wald–Wolfowitz runs-Z (Stouffer-combined) AND a conservative **per-session permutation null**
(shuffle the big-indicator order, p = P(perm runs ≤ observed)). The permutation null is the correct test
because it controls for the size *multiset* and isolates ORDER.

## Results
| harness | metric | runs Stouffer Z | mean big-pos (0.5=unif) | front-loaded sess | perm_p median | sess perm_p<0.05 |
|---|---|---|---|---|---|---|
| Claude | V1 inj/seq>5% | **−10.27** | **0.341** | **27/40** | 0.123 | 16/40 |
| Claude | V2 raw-size  | −4.20 | 0.507 | 7/39 | **0.303** | **4/39** |
| Codex  | V1 inj/seq>5% | −13.33 | 0.467 | 20/62 | 0.110 | 25/62 |
| Codex  | V2 raw-size  | −13.58 | 0.577 | 7/62 | **0.076** | **27/62** |

## Interpretation (honest)
**V1 (inj/seq>5%) COLLIDES with EXP-0005 → KILL.** The big runs-Z is an artifact of S-growth: events are
front-loaded (Claude mean-pos 0.341, 27/40 sessions front-loaded), and once the permutation null fixes the
inj/seq *multiset* and shuffles only ORDER, significance largely collapses (Claude perm_p median 0.12,
16/40 sig). The order-blind "early injections look big because S is small" is exactly the EXP-0005
accumulation axis (and the EXP-0036 CONTROL-A reduction: trajectory/accumulation re-parametrizes the inj/seq
prior). **V1 reduces to EXP-0005/0015 territory.**

**V2 (raw result-size) is the only genuinely-NEW statistic, but it REPLICATES on only 1 of 2 harnesses
under the correct (permutation) test:**
- Confound removed ✓ (V2 mean-pos ≈ 0.51/0.58, NOT front-loaded; only 7 front-loaded each).
- Codex: real order-clustering of large results (perm_p median 0.076, 27/62 sessions p<0.05). LARGE TOOL
  RESULTS arrive in bursts within Codex sessions, independent of context growth.
- Claude: **NOT significant** under the permutation null (perm_p median 0.30, only 4/39 sessions p<0.05).
  The Stouffer −4.2 is carried by the size-gradient the permutation test correctly removes.

## Collision verdict
- **vs EXP-0005/0015 (workload-magnitude distribution):** V1 = COLLISION (S-growth/accumulation axis). V2 =
  DISTINCT (EXP-0005 assumes i.i.d. size draws; V2 measures temporal correlation of result sizes — an
  arrival-process fact EXP-0005 cannot express). ✓ distinct only for V2.
- **vs EXP-0036 CONTROL-A (routing→endogenous inj/seq):** V1 collapses to the same "accumulation/trajectory
  re-parametrizes the prior" reduction. V2 is orthogonal (no routing/modality claim; a within-session marginal
  order-statistic). ✓ distinct for V2.
- **vs the 10 body-verified neighbors + red_zones (MAP-0001):** all neighbors are cost-map / PIC / mechanism
  / accounting-identity claims; red_zones are all PREDICTIVE/cost laws (slope~1, k~1.3, idle-window,
  compaction, routing). V2 is a DESCRIPTIVE arrival-process statistic — none of these. ✓ distinct.
- **vs CLAIM-0012 (failure burstiness):** DIFFERENT STREAM (invalidation/injection vs failure). The estimand
  is the arrival over-dispersion of LARGE TOOL RESULTS, not failures. ✓ distinct — but methodologically a
  sibling (same runs/permutation machinery).

## Verdict: KILL (lean), with a thin V2 caveat the orchestrator may weigh
- **V1 is a clean KILL** — collides with EXP-0005 (the inj/seq magnitude distribution IS already characterized;
  its temporal structure is the accumulation gradient, an EXP-0005 input).
- **V2 is genuinely-new and distinct from EXP-0005/0036/neighbors/CLAIM-0012, BUT under the correct
  permutation null it replicates on only 1 of 2 harnesses (Codex yes, Claude no).** The domain's standing bar
  is cross-harness replication (CLAIM-0012 itself was cautioned on 2/2 + a missing Gemini leg). V2 is 1/2,
  Gemini is unavailable (no tool data), so V2 cannot clear the replication bar with the data on hand.
- Net recommendation to orchestrator: **DO NOT SEED.** The descriptive pivot was given its one genuine shot;
  the only non-colliding variant (V2 raw-result-size arrival burstiness) does not replicate cross-harness
  under the conservative test. Document as a near-miss; revive only if a 2nd harness (beyond Codex) shows
  permutation-significant raw-size clustering.

## Files
- impl: experiments/2026-05-31/EXP-0040/impl/exp0040_injection_arrival.py
- results: experiments/2026-05-31/EXP-0040/results/results.json
- candidate doc: prior_art/PROJ-0002/NEW_CLAIM_CANDIDATE_injection_arrival_EXP-0040.md
