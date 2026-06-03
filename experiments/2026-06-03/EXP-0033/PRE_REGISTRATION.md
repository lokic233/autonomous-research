# PRE-REGISTRATION — EXP-0033 (CLAIM-0037)

**Researcher:** researcher-0033 | **Level:** L0 (CPU-only, stdlib-only, SERIAL, ≤15 min, trace/sim)
**Claim:** CLAIM-0037 | **Project:** PROJ-0008 | **Task:** TASK-0025
**Committed BEFORE running any experiment code.**

## THE CLAIM
In multi-step LLM-agent trajectories that ultimately FAIL, the failure is foreshadowed by a CAUSAL
online-observable signature (rising tool-error/retry rate, looping = repeated near-identical actions,
declining new-information-per-step) that a cheap monitor detects to flag the trajectory doomed STRICTLY
EARLIER (>=N steps before) than the agent's own termination/error — AND this beats BOTH (a) the agent's
own self-reported confidence and (b) a generic per-trajectory difficulty predictor, because impending
failure has a structural progression signature distinct from intrinsic task difficulty.

## TWO FALSIFIABLE PARTS
- **(A) LEAD TIME:** Does the online monitor flag doomed trajectories STRICTLY EARLIER (>= N>=1 steps)
  than the agent's own error/termination step? (If it only fires at/after the agent already knows → NEGATIVE.)
- **(B) ANTI-RELABELING / RIGHT-BASELINE:** At matched flag-rate, does the online causal monitor (c) beat
  BOTH (a) agent self-confidence AND (b) a generic difficulty predictor at predicting eventual failure
  (AUC) — with bootstrap CIs on (c-a) and (c-b) deltas excluding 0? (If generic-difficulty matches it →
  it's a relabeling of difficulty = the CLAIM-0015 death = NEGATIVE.)

## METRICS (pre-committed)
1. **Lead-time distribution** of monitor's first-fire on FAILED trajectories, measured in steps BEFORE
   the agent's own termination step (positive = earlier = good). Report median + IQR + frac>=1 step early.
2. **Early-warning AUC** for predicting eventual failure, computed from each predictor's score evaluated
   at a fixed EARLY observation window (first half of the trajectory only — online, no peeking).
3. **Head-to-head at matched flag-rate:** set each predictor's threshold to the SAME global flag-rate;
   compare AUC and lead-time. Primary deltas: AUC(c)-AUC(a) and AUC(c)-AUC(b), bootstrap 95% CI over seeds.
4. **Oracle gap:** an oracle that reads the LATENT health directly — monitor AUC must sit strictly BELOW it.

## AGENT-TRAJECTORY MODEL (latent, monitor does NOT read it)
Each trajectory has TWO independent latent scalars drawn per-trajectory:
- `difficulty d ~ U(0,1)`: intrinsic task hardness. Affects baseline failure probability AND step-0
  observable noise floor — but is STATIC (no progression).
- `health h_t`: a latent trajectory-health random walk starting at h0 (h0 anti-correlated with d via a
  tunable coupling `rho`). Failing trajectories' health DEGRADES over steps via one of 3 mechanisms
  (tool-error cascade, looping, info-starvation); each mechanism is a drift on h_t.
Ground-truth failure label = (h_T crosses a death threshold) OR (an abrupt unforeseeable hit with prob
`p_abrupt` independent of health — these have NO foreshadowing, the honest hard case).
`frac_foreshadowed` = fraction of failures that come from health-degradation (vs abrupt).

## MONITOR ONLINE OBSERVABLES (per step — the ONLY thing the online monitor reads)
Emitted as a noisy function of latent h_t (monitor never sees h_t, d, or label):
- `tool_error_flag_t` (Bernoulli, rate rises as health falls)
- `action_similarity_t` (looping signal, rises as health falls)
- `info_gain_t` = new-entities-per-step (falls as health falls)
- `step_index_t`
Online monitor score = EWMA of (tool_error_rate + looping − info_gain), causal (only past+present steps).

## THREE PREDICTORS (matched flag-rate)
- (a) **agent self-confidence**: noisy readout of CURRENT latent health (the agent's own signal) — sees
  health but with readout noise `sigma_conf`; available online.
- (b) **generic difficulty predictor**: per-trajectory STATIC difficulty features (step-0 observables +
  a noisy readout of d), NO online progression. Trained-free: monotone in estimated d.
- (c) **online causal monitor**: the progression EWMA above. Online, causal.

## SWEEP (>=5 seeds each cell)
- frac_foreshadowed ∈ {0.2, 0.5, 0.8}
- observable noise sigma ∈ {low, high}
- difficulty-health coupling rho ∈ {0.0, 0.6} (0 = independent; 0.6 = hard tasks tend to be unhealthy)
- seeds: 8 per cell. Bootstrap 2000x over seeds for CI on deltas.

## HONEST-NEGATIVE BRANCH (pre-committed — these are WINS to report)
Report NEGATIVE if ANY of:
- **No lead time:** monitor's median lead <= 0 (fires at/after agent's own termination), OR frac of
  failures flagged >=1 step early is not clearly > 0.5.
- **Relabeling of difficulty:** AUC(c)-AUC(b) CI includes or is below 0 (generic difficulty matches the
  online monitor) — the CLAIM-0015 death.
- **Loses to self-confidence:** AUC(c)-AUC(a) CI includes or is below 0.
- **Oracle-dependent / circular:** monitor AUC is not strictly below the latent-health oracle (would mean
  it's secretly reading the label).
- When abrupt/unforeseeable failures dominate (frac_foreshadowed low), expect lead time to collapse —
  report it as the honest ceiling on the method.

## ANTI-CIRCULARITY GUARANTEE
The failure LABEL is generated from latent (h_T, p_abrupt) which the monitor NEVER reads. The monitor sees
only emitted noisy observables. We include a latent-health oracle as an upper bound; the real monitor must
sit below it. No predictor reads d, h_t, or the label directly (confidence reads h_t through noise only —
it is the agent's own signal by construction, still not the label).

## PRIOR-ART CAVEAT
Agent-failure attribution / LLM-as-judge post-hoc trajectory analysis, AgentBoard, trajectory-eval are
PUBLISHED but POST-HOC. Novelty here = EARLY ONLINE CAUSAL signature with MEASURED lead time that beats
self-confidence AND a generic difficulty baseline. This L0 is a modeling/feasibility check only.
