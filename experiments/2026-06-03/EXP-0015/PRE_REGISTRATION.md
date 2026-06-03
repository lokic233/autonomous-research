# PRE-REGISTRATION — EXP-0015 (L0, CLAIM-0012, PROJ-0003)
researcher-0015 | node dengcchi-mac (CPU-only, stdlib-only, SERIAL — multiprocessing BLOCKED) | TASK-0014
Pre-registered BEFORE running. Honest pipeline — a NEGATIVE result is a WIN. Committed before any run.

## THE CLAIM (CLAIM-0012)
"In agentic LLM serving, a non-trivial fraction (>15%) of generated decode tokens are WASTED on agent
turns subsequently abandoned (tool errors, early-stop, branch pruning, retries), AND a cheap online
abandonment-risk signal (available BEFORE the turn completes) can identify a meaningful share early
enough to deprioritize them in the batch — reclaiming served compute WITHOUT harming completed-turn
latency at matched fairness."

This is a MEASUREMENT/CHARACTERIZATION study on a CONSTRUCTED trace model. NOT a claim of a universal
real-world number. We report the wasted-decode fraction AS A FUNCTION of two knobs (abandonment rate,
abandonment timing) and state workload-conditionality explicitly. L0 cannot prove the real-world value;
L0's job: (a) characterize the mechanism, (b) build a NON-CIRCULAR predictor and measure real AUC + lead
time, (c) build a reclaim model and check the latency/fairness constraint — and honestly report a
negative on any of the three falsifiable sub-parts.

## THREE FALSIFIABLE SUB-PARTS
- (A) WASTED-DECODE FRACTION: fraction of generated decode tokens spent on turns abandoned before their
  output was used. Falsifiable: if <~15% across realistic regimes -> NEGATIVE on part 1.
- (B) CAUSAL (NON-ORACLE) PREDICTOR: uses ONLY features observable BEFORE turn completion, NOT the latent
  abandonment cause. Falsifiable: if it cannot reach realistic AUC (sweep {0.6,0.7,0.8}) with USABLE lead
  time -> NEGATIVE on part 2.
- (C) RECLAIM WITHOUT HARM AT MATCHED FAIRNESS: bounded, fairness-matched deprioritization reclaims
  compute > 0 AND keeps completed-turn p99 within budget AND does not harm FP (would-complete) turns.
  Falsifiable: if reclaim <= 0 OR p99 blows budget OR FP turns harmed -> NEGATIVE on part 3.

## ANTI-CIRCULARITY (load-bearing design constraint)
A prior claim died because the predictor's features WERE the generative cause. We avoid this by design:
1. TRUE abandonment of each turn drawn from a LATENT process with latents {latent_difficulty,
   latent_tool_fragility, latent_branch_value} + a latent abandonment hazard the predictor NEVER reads.
2. Predictor reads ONLY noisy partial-decode OBSERVABLES available before completion:
     o1 = output_entropy_so_far        [noisy fn of latent difficulty]
     o2 = repetition_ratio_so_far      [noisy fn of latent difficulty]
     o3 = tool_call_malformation_prob  [noisy fn of latent tool fragility]
     o4 = turn_len_so_far / running_quantile_of_abandoned_lens [structural, no leakage]
     o5 = branch_retry_count           [observable history]
   Each observable is a LATENT-dependent signal corrupted by gaussian noise (swept knob). Predictor does
   NOT see latent hazard, abandonment label, abandon_step, or any post-completion info. Scores at decode
   prefix step t < turn_end.
3. AUC computed on HELD-OUT split (train predictor weights on train seeds, score on test seeds), ranking
   turns by predicted risk vs TRUE eventual abandonment label.
4. LEAD TIME = (abandon_step - fire_step) in decode tokens; fire_step = first prefix step crossing the
   operating threshold. Positive lead = fired before abandonment; report distribution.

## TRACE MODEL (constructed — conditionality stated)
- Serving episode = N agent turns. Each turn: planned length L_plan (lognormal via stdlib) + LATENT
  abandonment draw.
- ABANDONMENT TYPES: tool-error->retry, early-stop/branch-prune, user-interrupt; each w/ characteristic
  abandon-timing distribution.
- RATE knob p_abandon in {0.10,0.20,0.35,0.50}. TIMING knob in {early,mid,late,mixed}.
- WASTED tokens for an abandoned turn = abandon_step (tokens decoded before output discarded). Completed
  turns waste 0. WASTED-DECODE FRACTION = sum(wasted)/sum(all decoded). Reported as a SURFACE over
  (p_abandon x timing), NOT one universal number.

## RECLAIM MODEL (bounded-fairness)
- Baseline: round-robin batch decode, no deprioritization; measure completed-turn p50/p99 (token-time).
- Treatment: on predictor flag at fire_step, deprioritize the turn by BOUNDED W (max delay budget —
  analogous to a prior bounded-W). NOT killed (no online ground truth); only slowed.
- RECLAIMED COMPUTE per true-positive ~ tokens of the abandoned turn that are deferred past its
  abandonment (slot yielded to a turn that WILL complete). Net reclaim = baseline_wasted - treatment_wasted.
- MATCHED FAIRNESS: cap W so completed-turn p99 increase <= 5% budget. FALSE POSITIVES (would-complete
  turns deprioritized) must not be harmed beyond same budget — measured separately.
- WIN on C: net reclaim > 0 AND completed p99 within +5% AND FP-turn p99 within +5%.

## NOISE SWEEP / SEEDS
- Predictor observation-noise sigma swept to target AUC bands {~0.6,~0.7,~0.8}; report ACHIEVED AUC.
- 8 seeds per cell; report mean +/- std and seed-spread CI.

## HONEST-NEGATIVE BRANCH (pre-committed — report any AS the answer)
(N-A) wasted fraction <~15% across realistic regimes -> part 1 workload-conditional; if small everywhere
      realistic -> NEGATIVE part 1.
(N-B) no cheap early observable at AUC >= ~0.65 with positive median lead -> NEGATIVE part 2.
(N-C) bounded-W reclaim <= 0 OR blows p99 budget OR harms FP turns -> NEGATIVE part 3.
(N-D) PRIOR-ART caveat: speculative-decode early-exit, request preemption / SLO scheduling (FastServe,
      Llumnix), KV-aware preemption already do generic preemption/migration. NOVEL angle =
      AGENT-ABANDONMENT-SPECIFIC waste characterization + early abandonment predictor exploiting agent-loop
      structure (retries, tool malformation, branch pruning). If it reduces to generic preemption with no
      agent-specific signal advantage -> novelty-kill.

## PRIMARY OUTCOME
Honest joint verdict: HELD only if (A>=15% realistic regime) AND (B AUC>=0.65 w/ usable lead) AND
(C reclaim>0 within fairness budget). PARTIAL if some hold. NEGATIVE if core fails. We accept any; goal
is honest anti-circular measurement, not a positive result.

## BUDGET / SAFETY
<=15 min wall, CPU-only, stdlib-only (no numpy/network/GPU), SERIAL. Trust on-disk CSVs over stdout.
Fixed seeds for reproducibility.
