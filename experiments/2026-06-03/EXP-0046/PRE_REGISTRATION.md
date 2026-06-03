# PRE_REGISTRATION — EXP-0046 (CLAIM-0047)

**Researcher:** researcher-0044 | **Level:** L0 (CPU-only, pure-stdlib, SERIAL, <=15 min)
**Project:** PROJ-0017 (agentic-systems: recovery & failure-process policy)
**Committed BEFORE any run.** Honest pipeline; negatives are WINS. Trust on-disk CSVs, not stdout.

## THE CLAIM (CLAIM-0047)
In long-horizon agentic rollouts whose per-step failure hazard is path-dependent and RISING after a
deviation (an agent that drifts off the canonical path becomes monotonically more failure-prone the
longer it stays off-path), the token-cost-optimal recovery policy is to roll back PAST the last
checkpoint to before the inferred deviation onset. A Young/Daly-style "restart from the most recent
checkpoint" policy (optimal under memoryless failures) incurs >=25% more expected wasted tokens
because restarting inside a still-elevated-hazard region re-fails at a high rate; the penalty grows
monotonically with hazard-rise steepness alpha and is ZERO when memoryless (alpha=0).

## ARCHETYPE / SCREEN
EMPIRICAL-phenomenon / policy-cost (NOT metric-validity — no scalar metric indicted; headline =
wasted-token cost of a recovery DECISION). NO closed form in the non-memoryless regime (optimal
rollback DEPTH depends jointly on the realized deviation-onset distribution + hazard-rise shape +
checkpoint spacing; the policy must INFER an unobserved latent onset). Screened vs 3 anti-patterns:
NOT tuned-knob (both policies are FIXED rules given the failure process); NOT KV-reuse; NOT
relabeling-vs-logprob. NOT a forces-crossover (single dominant mechanism: elevated post-restart
hazard wastes re-execution).

## THE FALSIFIABLE QUESTION (three-way, all reportable)
Under a rising post-deviation hazard, does deviation-aware "rollback PAST the last checkpoint" save
>=25% expected wasted tokens vs memoryless-optimal "restart from last checkpoint", AND does that
penalty grow monotonically with hazard-rise steepness alpha, AND is it ZERO at alpha=0 (memoryless
control)?
  - HELD: alpha=0 penalty ~0 (MUST hold) AND realistic alpha>0 penalty >=25% AND monotone increasing in alpha.
  - HONEST-NEGATIVE: alpha=0 ~0 but alpha>0 penalty <25% OR non-monotone -> "HPC-inherited restart
    already near-optimal for agent token-economics."
  - DETECTOR-BOUNDED: B only wins (>=25%) with an unrealistically accurate detector.

## CALIBRATION CONTROL (load-bearing)
At alpha=0 (memoryless) the claim predicts ZERO penalty (Young/Daly IS optimal there). If alpha=0
shows a big penalty (say |penalty| > 5%), the sim or policy is BUGGY -> fix before trusting alpha>0.

## ROLLOUT STOCHASTIC PROCESS (faithful generative process, NOT a closed-form object)
A rollout = sequence of steps toward target length N_target (default 200 steps to "complete").
Latent state: on_path in {True, False}, plus t_since_dev (steps since deviation onset; undefined
while on-path). Per executed step:
  - If on-path: with prob h0_dev (default 0.01) the agent DEVIATES (flip on_path->False; set
    t_since_dev=0, record true onset step). Independently, with small base fail prob h0_fail
    (default 0.002) a failure occurs.
  - If off-path: per-step FAILURE hazard RISES with time since deviation:
      LINEAR variant: h(t) = min(h_cap, h0_fail + alpha * t_since_dev)
      WEIBULL variant: h(t) = min(h_cap, h0_fail + base_w * (t_since_dev ** (k-1)))  with k>1 (k=2.0)
    (h_cap = 0.6 to keep hazards valid probabilities.)  t_since_dev increments each off-path step.
  - A failure triggers RECOVERY (see policies). Steps are 1 token each.
Checkpoints saved every c steps (default c=20); each checkpoint-save costs S tokens (default S=2).
NOTE: deviation does NOT auto-resolve on its own; only a rollback that lands BEFORE the true onset
returns the agent to on-path. A rollback that lands AFTER the onset stays off-path with
t_since_dev reset to (restart_pos - onset).  (This is the crux: restarting inside the elevated
region re-enters rising hazard.)

## TWO RECOVERY POLICIES (neither sees on_path or true onset)
(A) MEMORYLESS-OPTIMAL (Young/Daly): on failure, restart from the MOST RECENT checkpoint
    (largest checkpoint position <= failure step). Re-executes from there.
(B) DEVIATION-AWARE: on failure, INFER the deviation onset from OBSERVABLES and roll back PAST the
    last checkpoint to before the inferred onset, snapping to the nearest checkpoint <= inferred
    onset (you cannot resume from a non-checkpoint; rolling back lands on the checkpoint at-or-before
    the inferred onset). Two detector implementations, both reported:
      (B1) NOISY DETECTOR: emits an estimated onset step = true onset + Gaussian-ish integer noise,
           gated by FPR/FNR: with prob FNR the detector MISSES (falls back to last-checkpoint,
           i.e. behaves like A); with prob FPR on a non-deviation-driven failure it fabricates a
           spurious early onset (over-rolls-back, wasting tokens). Default FPR=0.1, FNR=0.1, noise
           sd=3 steps.
      (B2) FIXED-OVERSHOOT HEURISTIC: roll back D_overshoot checkpoints beyond the last one
           (default D_overshoot=1, i.e. one checkpoint earlier than A), no inference.
    The policy operates ONLY on observables: step-level failure events + checkpoint positions +
    the detector's output. It NEVER reads on_path or the true onset.

## ANTI-CIRCULARITY (structural separation)
GROUND TRUTH = the true latent deviation-onset step + true hazard process (simulator-known,
policy-HIDDEN). TESTED SIGNAL = the policy's OBSERVABLES only (failure events, checkpoint
positions, detector output). The simulator advances the true latent state and SCORES wasted tokens
against ground truth; the policy chooses rollback depth from observables alone.

## WASTED-TOKEN METRIC
Per COMPLETED rollout (run until N_target successful steps accumulate): total wasted tokens =
(sum of all re-executed steps after every failure, i.e. steps that had to be redone) +
(checkpoint-save overhead actually incurred). Productive tokens = N_target. Monte-Carlo over R
rollouts (R=2e4 primary; bump to 5e4 if time permits and serial budget allows). Report mean waste
with bootstrap 95% CIs.
PRIMARY RESULT: relative wasted-token PENALTY of policy A vs B = (waste_A - waste_B) / waste_B.
(Positive penalty => A wastes more => B wins.)

## SWEEPS
- alpha in {0.0, 0.005, 0.01, 0.02, 0.04, 0.08} (LINEAR). alpha=0 is the memoryless control.
- ALSO Weibull k=2.0 variant at a matched set of base_w producing comparable mean off-path hazard.
- checkpoint spacing c in {10, 20, 40}.
- detector FPR/FNR sweep: (FPR,FNR) in {(0,0),(0.1,0.1),(0.25,0.25),(0.5,0.5)} at a fixed realistic
  alpha — to find the noise boundary where B's advantage vanishes.
"Realistic alpha" for the headline >=25% check is pre-declared = alpha=0.02 (LINEAR, c=20,
B1 detector at FPR=FNR=0.1). (Chosen before running as a mid-sweep, non-extreme value.)

## SEEDS / MC / DETERMINISM
Pure-stdlib `random`. Master seed 20260603. Each (config) cell uses a deterministic per-cell seed
derived from the master + a hash of the config; each of R rollouts uses seed = cell_seed + rollout_idx.
Same RNG stream reused across BOTH policies within a rollout (common random numbers: the SAME
deviation onset + SAME base failure draws feed A and B, so the penalty is a paired contrast and
not RNG-variance noise). This is critical for a clean paired estimate.

## OUTCOME DEFINITIONS (pre-declared)
- CALIBRATION (alpha=0): |penalty| <= 5% with CI overlapping 0. MUST pass or sim is buggy.
- HELD: calibration passes AND penalty(alpha=0.02, realistic detector) >= 25% (CI lower bound > 25%)
  AND penalty(alpha) monotone non-decreasing across the alpha sweep (each step's CI consistent).
- HONEST-NEGATIVE: calibration passes but realistic-alpha penalty < 25% OR non-monotone.
- DETECTOR-BOUNDED: B1 only achieves >=25% at FPR=FNR=0 (or <=0.1) and collapses below 25% (or goes
  negative) by FPR=FNR=0.25 — report the crossing FPR/FNR.

## DELIVERABLES
sim_recovery.py (the generative sim + both policies + sweeps, writes CSVs), results/*.csv,
RESULTS.md (penalty(alpha) curve incl alpha=0 calibration PASS/FAIL, monotonicity test, >=25%
threshold check at realistic alpha, detector-FPR/FNR boundary, which outcome), sanity.txt
(hand-checked invariants: hazards in [0,1], alpha=0 paired waste_A==waste_B within CI, common-RNG
verified).
