# PRE-REGISTRATION — EXP-0034 (CLAIM-0037)

**Researcher:** researcher-0034 | L0 CHEAP follow-up | CPU-only, stdlib-only, SERIAL, ≤15 min
**Parent:** EXP-0033 (sibling dir) found online monitor beats generic-difficulty (+0.095 AUC,
CI excludes 0) but TIES/LOSES to agent self-confidence (−0.006, CI below 0) at the SINGLE
hardcoded value sigma_conf=0.35. Committee#1 (VERDICT-0034, yellow) demanded two cheap blockers
before any GPU L1. This experiment runs both. COMMITTED BEFORE RUNNING.

## BLOCKER 1 — sigma_conf FLIP-POINT SWEEP (load-bearing)

In the EXP-0033 model, agent self-confidence is a noisy readout of latent health:
`confidence_score_t = -(latent_h_t + N(0, sigma_conf))`. EXP-0033 fixed sigma_conf=0.35.
The monitor reconstructs health from indirect noisy observables (tool-error/loop/info-gain EWMA);
it never sees latent health. Intuition: as sigma_conf grows (worse calibration), the direct
readout degrades until the indirect reconstruction wins.

### Design
- REUSE EXP-0033's `gen_trajectory`, `monitor_scores`, `confidence_scores`, `difficulty_score`,
  `oracle_score`, `auc`, `early_window_score`, `bootstrap_ci` UNCHANGED (import the module).
- SWEEP sigma_conf over a realistic-to-extreme grid:
  `[0.10, 0.20, 0.35 (EXP-0033 ref), 0.50, 0.70, 0.90, 1.20, 1.60, 2.00]`.
- For each sigma_conf: run the SAME 12-cell (frac×sigma×rho) × 8-seed pooled design as EXP-0033,
  400 trajectories/cell. Compute, pooled across all 96 rows per sigma_conf:
  - mean AUC(monitor), mean AUC(confidence), mean AUC(difficulty)
  - delta = AUC(monitor) − AUC(confidence), with 95% bootstrap CI (B=2000) over the 96 per-row deltas.
- The monitor's AUC does NOT depend on sigma_conf (monitor never reads confidence); only the
  confidence baseline degrades. So we hold the monitor fixed and re-score confidence per sigma_conf.

### Flip-point definition (PRE-REGISTERED, no post-hoc)
- **EQUAL point:** smallest sigma_conf where the delta 95% CI INCLUDES 0 (no longer a robust loss).
- **BEAT point:** smallest sigma_conf where delta 95% CI is ENTIRELY ABOVE 0 (robust monitor win).
- Report delta(sigma_conf) curve with CIs to results/sweep_sigma_conf.csv.

### Realistic-miscalibration anchoring (PRE-REGISTERED interpretation)
The model's "calibration" maps to sigma_conf via the noise on the agent's latent-health readout.
We translate sigma_conf to an interpretable miscalibration scale: latent_h has process SD ~0.25/step
and ranges roughly [-1.5, +1]; sigma_conf is the readout noise SD relative to that signal. We will
compute the signal-to-noise / a proxy "confidence-AUC degradation" and compare the BEAT-point's
implied confidence-AUC to PUBLISHED LLM self-confidence failure-detection AUC / ECE ranges. We are
EXPLICIT that this is a coarse mapping (an L0 sim, not real LLM logprobs) — the real magnitude is an
L1 question — but a directional verdict is possible: does the monitor only win when the confidence
baseline is driven BELOW realistically-reported LLM confidence discrimination (AUC ~0.5-0.65 for
verbalized confidence on hard multi-step tasks)?

## BLOCKER 2 — LIVE ≥2-SOURCE PRIOR-ART CHECK

Question: does any PUBLISHED system already do ONLINE, LEAD-TIME-measured agent-trajectory scoring
of impending failure (distinct from difficulty)? Check specifically:
1. Process Reward Models / step-level PRMs (Lightman et al. 2023, Let's Verify Step by Step).
2. AgentBoard progress-rate (Ma et al., NeurIPS 2024).
3. Online LLM-as-Judge / stepwise self-evaluation early-stopping (Zheng et al. 2023 and successors).
For each: is it ONLINE (causal, step ≤ t only)? Does it MEASURE LEAD TIME before failure? Is it
DISTINCT from difficulty? Verdict on whether each RELABELS the surviving weak-form novelty
("an EARLY ONLINE causal failure signature with measured LEAD TIME, distinct from difficulty").

## DECISION RULE (PRE-REGISTERED)

> IF the monitor-beats-confidence flip-point (robust BEAT point) is WITHIN realistic published LLM
> self-confidence miscalibration ranges (i.e., the monitor wins at a calibration level real agents
> actually exhibit) AND no published system does online lead-time trajectory failure scoring
> -> claim is L1-WORTHY (recommend yellow-advance to L1).
> ELSE (monitor only wins at absurd/unrealistic miscalibration, OR a published system already does
> online lead-time progression scoring) -> CONVERGE (recommend red/weaken: relabeling or
> unrealistic-regime).

## ANTI-CIRCULARITY / HONESTY
- Monitor reads ONLY noisy observables; never latent health/difficulty/label (inherited from EXP-0033).
- A "claim is relabeling / not L1-worthy" finding is a WIN, reported honestly.
- multiprocessing BLOCKED -> SERIAL. Trust on-disk CSVs, not stdout.
