# RESULTS — EXP-0033 (CLAIM-0037)

**Researcher:** researcher-0033 | **L0** CPU-only, stdlib-only, SERIAL | wall-clock ~2.6s (budget 15min)
**Design:** pre-registered in PRE_REGISTRATION.md (committed BEFORE running). Sim/trace L0 modeling study.
**Sweep:** 12 cells (frac_foreshadowed × sigma × rho) × 8 seeds = 96 rows; 400 trajectories/row.
Raw: `results/raw_results.csv` · per-cell: `results/agg_by_cell.csv` · global: `results/global_summary.csv`

## VERDICT: PARTIAL → effectively NEGATIVE on the load-bearing test

The online causal monitor passes **2 of 3** required gates but FAILS the one that matters most for the
claim as written (it must beat BOTH baselines).

| Gate | Result | Pass? |
|---|---|---|
| (A) Lead time exists (>=1 step before agent termination) | median lead **+2.32 steps**; but only **42%** of failures flagged >=1 step early at 30% flag-rate (pre-reg bar was >0.5) | PARTIAL |
| (B1) Beats GENERIC DIFFICULTY (anti-relabeling, the CLAIM-0015 death) | AUC(mon)-AUC(diff) = **+0.095**, 95% CI **[+0.087, +0.103]** (excludes 0); 96/96 rows positive | **YES** |
| (B2) Beats AGENT SELF-CONFIDENCE | AUC(mon)-AUC(conf) = **-0.006**, 95% CI **[-0.011, -0.001]** (below 0) | **NO** |
| Anti-circularity: monitor < latent-health ORACLE | mon 0.743 < oracle 0.858 (gap 0.115) | YES |

**Bottom line:** The progression signature is REAL and is NOT merely a relabeling of intrinsic
difficulty — it decisively beats a generic difficulty predictor with tight CIs, and it carries genuine
lead time (~2.3 steps median). BUT it does NOT beat the agent's own self-confidence. In this model the
agent's confidence is a (noisy) readout of the same latent health the failure is generated from, so it is
structurally privileged: an online observer reconstructing health from indirect noisy proxies cannot do
better than a direct (noisy) readout of that health. The claim requires beating BOTH (a) and (b); it
beats (b) but ties/loses to (a). **Per the pre-registered honest-negative branch, this is reported as a
(partial) NEGATIVE.**

## (A) LEAD-TIME DISTRIBUTION
- Online monitor median lead = **+2.32 steps** before the agent's own termination (pooled across cells).
- It is even slightly EARLIER than self-confidence's first-fire (~1.6 steps) at matched 30% flag-rate.
- HOWEVER, coverage is the catch: only **42.4%** of failed trajectories are flagged >=1 step early
  (the rest are flagged late or never within budget) — below the pre-registered >0.5 bar.
- Trend with foreshadowing: as frac_foreshadowed rises 0.2 -> 0.8, frac-early climbs 0.37 -> 0.48 and
  AUC climbs 0.69 -> 0.80, confirming the signature tracks foreshadowed (not abrupt) failure. When abrupt
  failures dominate (frac=0.2) the monitor's edge shrinks toward the noise floor, exactly as pre-registered.

## (B) HEAD-TO-HEAD AT MATCHED FLAG-RATE (the anti-relabeling test)
- vs generic difficulty: **WIN, robust.** d=+0.095, CI [+0.087,+0.103], all 96 rows positive. The online
  progression signal contains information the static difficulty predictor does not. This is the test
  CLAIM-0015 failed; here the monitor clears it cleanly.
- vs self-confidence: **LOSS/TIE, robust.** d=-0.006, CI [-0.011,-0.001]. Small but consistently negative.
  Self-confidence (direct noisy health readout) >= reconstructed-from-observables monitor.

## ORACLE GAP (anti-circularity, the CLAIM-0008/0013 lesson)
Monitor AUC 0.743 sits well below the latent-health oracle 0.858 (gap 0.115). The monitor is NOT secretly
reading the label — it operates on emitted noisy observables only and pays the reconstruction penalty.
Confidence (0.749) also sits below the oracle. Anti-circularity holds.

## HONEST INTERPRETATION
The model is built so the agent's OWN confidence is a privileged direct (noisy) view of latent health,
while the monitor must reconstruct health from indirect proxies (tool-error/loop/info-gain). Under that
(arguably realistic) assumption, the online monitor cannot beat self-confidence — it can only beat the
difficulty baseline. The claim's strong form ("beats BOTH") is therefore FALSIFIED in this regime.
A weaker, still-interesting form survives: **the online progression signature beats a generic difficulty
baseline and has real lead time** — i.e., impending failure has a structural progression signature
distinct from intrinsic difficulty (the anti-relabeling claim holds). But it is dominated by the agent's
own self-report, which undercuts the practical "cheap external monitor beats the agent" pitch.

This conclusion is sensitive to ONE modeling assumption: how good is real-agent self-confidence? Published
work suggests LLM self-confidence/verbalized-uncertainty is often POORLY calibrated and weakly predictive
of failure — if real self-confidence is noisier than modeled here (larger sigma_conf, or biased), the
monitor could flip to beating it. That is the key L1 question, not resolvable at L0.

## WHAT A REAL L1 SHOULD MEASURE
- Real agent FAILURE trajectories: tau-bench, AppWorld, SWE-agent rollouts (success + failure).
- Real online features: actual tool-error/retry events, action n-gram self-similarity (true looping),
  new-entity/new-token info-gain per step, step index — extracted causally (no peeking past step t).
- Real lead time vs the agent's ACTUAL termination/error step (not a simulated death threshold).
- Real self-confidence baseline: the agent's verbalized confidence / logprob-derived uncertainty,
  with its TRUE (mis)calibration — this is the load-bearing comparison and the one L0 cannot settle.
- Real difficulty baseline: a per-task difficulty predictor trained on task features only (no trajectory).
- Then re-run (B): does the online monitor beat self-confidence AND difficulty at matched flag-rate with
  real lead time? L0 says it beats difficulty but not (modeled) confidence.

## PRIOR-ART CAVEAT
Agent-failure attribution, LLM-as-judge post-hoc trajectory analysis, AgentBoard, and trajectory-eval are
PUBLISHED — but they are POST-HOC (analyze a finished trajectory). The novelty would be the EARLY ONLINE
CAUSAL signature with MEASURED lead time beating self-confidence AND difficulty. L0 supports the
"distinct-from-difficulty + has lead time" half but NOT the "beats the agent's own signal" half. Failure
analysis itself is well-trodden; honest framing required.
