# PRE_REGISTRATION — EXP-0049 (CLAIM-0047) — CORRECTED RE-RUN of EXP-0046

**Researcher:** researcher-0047 | **Level:** L0 (CPU-only, pure-stdlib, SERIAL, <=12 min)
**Project:** PROJ-0017 | **Claim:** CLAIM-0047 | **Supersedes:** EXP-0046 (INCONCLUSIVE, tripped its own bug-check)
**COMMITTED BEFORE ANY RUN.** Honest pipeline; a negative is a WIN. Trust on-disk CSVs, not stdout.

## THE CLAIM (CLAIM-0047)
In long-horizon agentic rollouts whose per-step failure hazard is path-dependent and RISING after a
deviation, the token-cost-optimal recovery is to roll back PAST the last checkpoint to before the
inferred deviation onset; a Young/Daly-style "restart from the most recent checkpoint" policy
(optimal under memoryless failures) incurs >=25% more expected wasted tokens; the penalty grows
monotonically with hazard-rise steepness alpha and is ZERO when memoryless (alpha=0).

## WHY THIS IS A RE-RUN (the two diagnosed bugs in EXP-0046)
EXP-0046 produced +3700%..+4500% penalties BUT tripped its OWN pre-registered bug-check:
  - alpha=0 penalty measured -46% (B1) / -28% (B2): policy B WORSE than A at alpha=0, |penalty| >> 5%.
  - the +4000% penalties co-occur with dnc_A = 0.57-0.62 (policy A never completes 57-62% of rollouts),
    so the headline is a "policy A never terminates / hit the 50000-token CAP" artifact, NOT a fair
    expected-wasted-token comparison.
We reuse EXP-0046's hazard model (linear h(t)=min(h_cap,h0+alpha*t_since_dev) AND weibull variant) and
checkpoint structure, but apply THREE FIXES + the calibration gate below, locked BEFORE running.

## ROLLOUT GENERATIVE PROCESS (unchanged from EXP-0046, faithful, latent state policy-HIDDEN)
N_TARGET=200 productive steps to complete. Latent: on_path in {T,F}, t_since_dev. Per executed step:
  - on-path: deviate with prob H0_DEV=0.01 (set onset=progress, t=0); base fail hazard h0_fail=0.002.
  - off-path: fail hazard RISES with t_since_dev:
      LINEAR:  h(t)=min(H_CAP, h0_fail + alpha*t)
      WEIBULL: h(t)=min(H_CAP, h0_fail + base_w*(t**(k-1))), k=2.0
    H_CAP=0.6. t_since_dev increments each off-path step.
  - On failure -> RECOVERY (policy). 1 token / step. Checkpoint every c steps (default 20), save cost S=2.
  - Deviation does NOT self-resolve; only a rollback landing BEFORE the true onset returns to on-path
    (rollback landing AFTER onset stays off-path with t reset to restart_pos-onset). This is the crux.

## THREE FIXES (locked before running)

### FIX #1 — FAIR finite non-completion accounting (same rule for BOTH policies)
Replace the EXP-0046 "wasted>50000-token CAP" (which over-counts A as ~50000 deadweight) with a
shared, agent-realistic GIVE-UP rule applied IDENTICALLY to A and B:
  - MAX_ATTEMPTS = 50 recovery attempts (failures) per rollout. After the 50th failed recovery the
    rollout is abandoned (DNC). Both A and B face the same MAX_ATTEMPTS.
  - On DNC, wasted tokens = the ACTUAL tokens spent up to give-up (finite, exactly accumulated), NOT
    the cap, NOT infinity, NOT a degenerate penalty. This is the real token cost an agent burned.
  - Report dnc_A AND dnc_B as first-class outcomes for EVERY cell. The penalty is only trustable when
    dnc rates are reported and comparable.
This makes the wasted-token metric finite and the A-vs-B contrast fair under common random numbers.

### FIX #2 — policy B must NOT overshoot when NO deviation is inferred (evidence-gated detector)
EXP-0046's B1 fired its overshoot whenever onset!=None (i.e. on essentially any post-deviation failure),
even at alpha=0 where there is NO rising hazard to escape -> B paid deadweight overshoot -> -46% penalty.
FIX: B's rollback-PAST behavior is GATED on an actual INFERRED deviation, defined ONLY from observables:
  - DEVIATION EVIDENCE = repeated failures in a short window: the detector fires "rising-hazard inferred"
    only if the agent has seen >= K_EVID failures since its last successful checkpoint advance
    (K_EVID=2, i.e. at least one re-fail after a restart). A single isolated failure -> NO inference ->
    behave like A (restart from last checkpoint).
  - At alpha=0 (flat hazard) re-fails after restart are rare (hazard does not rise), so the K_EVID>=2
    window rarely triggers -> B behaves ~like A -> alpha=0 penalty must calibrate to ~0 (|penalty|<5%).
  - When evidence DOES fire (alpha>0, repeated re-fails), B infers onset via the noisy detector (B1) or
    fixed overshoot (B2) and rolls back past the last checkpoint. Overshoot is NEVER unconditional.
This is the load-bearing fix: it ties B's overshoot to observable evidence of a rising hazard, so the
memoryless control (alpha=0) is honest.

### FIX #3 — VERIFY THE CALIBRATION GATE BEFORE TRUSTING ANYTHING
Run alpha=0 FIRST. If |penalty| >= 5% at alpha=0, the sim is STILL buggy -> debug B until alpha=0
calibrates to within +-5% with CI overlapping 0. ONLY AFTER alpha=0 passes do we sweep alpha and report.
If alpha=0 will not calibrate after honest debugging -> outcome = STILL-BUGGY (report the blocker, do
NOT fabricate). The gate is the precondition for any alpha>0 claim.

## TWO RECOVERY POLICIES (neither sees on_path or true onset)
(A) MEMORYLESS-OPTIMAL (Young/Daly): on failure, restart from MOST RECENT checkpoint (largest ckpt<=fp).
(B) DEVIATION-AWARE (evidence-gated, FIX #2): on failure, IF deviation evidence fires (>=K_EVID fails
    since last checkpoint advance), infer onset and roll back to nearest checkpoint <= inferred onset:
      (B1) NOISY DETECTOR: est_onset = true_onset + round(gauss(0,sd=3)); FNR=miss->behave like A;
           FPR=fabricate spurious early onset (over-rollback). Default FPR=FNR=0.1.
      (B2) FIXED-OVERSHOOT: roll back ov=1 checkpoint beyond the last (only when evidence fires).
    ELSE (no evidence): behave EXACTLY like A. Policy reads ONLY observables (failure events, checkpoint
    positions, failure-since-advance counter, detector output). NEVER reads on_path or true onset.

## ANTI-CIRCULARITY (inherited, structural separation)
GROUND TRUTH = true latent deviation-onset + true hazard process (simulator-known, policy-HIDDEN).
TESTED SIGNAL = policy's OBSERVABLES only (failure events, checkpoint positions, fails-since-advance,
detector output). Simulator advances true latent state and SCORES wasted tokens vs ground truth; policy
chooses rollback depth from observables alone. The noisy detector's access to true onset is mediated by
FPR/FNR/noise (it never reads onset directly in the no-noise sense — onset+noise is the observable proxy).

## WASTED-TOKEN METRIC
Per rollout (run to 200 productive steps OR give-up at MAX_ATTEMPTS=50 failed recoveries): wasted =
(sum of re-executed steps after every failure) + (checkpoint-save overhead incurred). On DNC, wasted =
actual tokens spent to give-up (finite). Monte-Carlo over R rollouts, COMMON RANDOM NUMBERS: A and B
share the SAME onset + SAME failure draws per rollout (paired contrast). Report mean waste + bootstrap
95% CI. PRIMARY PENALTY = (waste_A - waste_B)/waste_B. Positive => A wastes more => B wins.
Also report completion-conditional waste (rollouts that completed) as a secondary, and dnc_A, dnc_B.

## SWEEPS (after alpha=0 gate passes)
- alpha in {0, 0.002, 0.005, 0.01, 0.02, 0.04} (LINEAR). alpha=0 = memoryless control (the gate).
- Weibull k=2.0 variant at matched base_w.
- checkpoint spacing c in {10, 20, 40} at a fixed realistic alpha.
- detector FPR/FNR in {(0,0),(0.1,0.1),(0.25,0.25),(0.5,0.5)} at fixed realistic alpha.
"Realistic alpha" for the headline >=25% check is pre-declared = alpha=0.02 (LINEAR, c=20, B1 FPR=FNR=0.1).

## SEEDS / MC / DETERMINISM
Pure-stdlib random. MASTER=20260603. Per-cell seed = MASTER + hash(config); rollout seed = cell_seed+idx.
Same RNG stream feeds A and B within a rollout (common random numbers). R=4000 primary (bump if budget).

## OUTCOME DEFINITIONS (pre-declared, locked)
- CALIBRATION (alpha=0): |penalty| < 5% with CI overlapping 0. MUST PASS or outcome = STILL-BUGGY.
- HELD: calibration passes AND penalty(alpha=0.02, realistic detector) >= 25% (CI lower bound > 25%)
  AND penalty(alpha) monotone non-decreasing across the alpha sweep, AND dnc_A, dnc_B reported &
  comparable (penalty not driven by an A-only non-completion blowup).
- HONEST-NEGATIVE: calibration passes but realistic-alpha penalty < 25% OR non-monotone ->
  "HPC-inherited restart-from-last-checkpoint is near-optimal for agent token-economics."
- STILL-BUGGY: alpha=0 won't calibrate to ~0 after honest debugging -> report the blocker, NO fake result.

## DELIVERABLES
sim_recovery_corrected.py (generative sim + evidence-gated B + MAX_ATTEMPTS give-up + sweeps, writes CSV),
results/results_corrected.csv, RESULTS.md (alpha=0 gate PASS/FAIL, penalty(alpha) curve with CIs + BOTH
dnc rates, monotonicity test, >=25% check at alpha=0.02, detector & ckpt sweeps, which outcome), sanity
checks (hazards in [0,1], alpha=0 paired waste comparable, common-RNG verified).
