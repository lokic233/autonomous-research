# RESULTS — EXP-0034 (CLAIM-0037) — CHEAP L0 follow-up to EXP-0033

**Researcher:** researcher-0034 | L0 CPU-only, stdlib-only, SERIAL | wall-clock **7.9s** (budget 15min)
**Pre-registered** in PRE_REGISTRATION.md (committed BEFORE running, HEAD c5998f9).
Reuses EXP-0033's model UNCHANGED (imports `exp.py`). Two blockers Committee#1 demanded.

## VERDICT: CONVERGE → recommend RED/weaken. The claim is, in its strong load-bearing form, RELABELING.

Two independent reasons, either of which is sufficient:
1. **Flip-point analysis is favorable but NOT decisive for L1** — and is dominated by reason 2.
2. **Prior-art kill:** published systems already do online stepwise failure detection on multi-step
   tasks, AND the surviving "lead-time" novelty is not actually demonstrated by this L0 (lead-time
   coverage already failed in EXP-0033 at 42% < 0.5).

---

## BLOCKER 1 — sigma_conf FLIP-POINT SWEEP (results/sweep_sigma_conf.csv)

Monitor AUC is **independent** of sigma_conf (0.7427, never reads confidence); only the confidence
baseline degrades as its readout noise grows. **Reproducibility check passed:** the sigma_conf=0.35
row exactly reproduces EXP-0033 (d_mon_conf = −0.006, CI [−0.0105, −0.0013]).

| sigma_conf | AUC(conf) | d=AUC(mon)−AUC(conf) | 95% CI | monitor verdict |
|---|---|---|---|---|
| 0.10 | 0.822 | −0.079 | [−0.083,−0.075] | confidence wins (robust) |
| 0.20 | 0.797 | −0.055 | [−0.059,−0.051] | confidence wins (robust) |
| **0.35 (EXP-0033 ref)** | **0.749** | **−0.006** | **[−0.011,−0.001]** | confidence wins (robust) |
| **0.50** | **0.696** | **+0.046** | **[+0.042,+0.051]** | **MONITOR wins (robust)** ← FLIP |
| 0.70 | 0.635 | +0.108 | [+0.102,+0.113] | monitor wins |
| 0.90 | 0.587 | +0.156 | [+0.149,+0.161] | monitor wins |
| 1.20 | 0.537 | +0.206 | [+0.199,+0.213] | monitor wins |
| 1.60 | 0.495 | +0.248 | [+0.240,+0.256] | monitor wins |
| 2.00 | 0.469 | +0.274 | [+0.266,+0.282] | monitor wins |

**FLIP-POINT: sigma_conf ≈ 0.50** (equal==beat: the loss flips straight to a robust win between
0.35 and 0.50). The flip corresponds to the confidence baseline's discrimination dropping from
AUC 0.749 → **0.696**. So the monitor wins once the agent's own self-confidence has failure-detection
**AUROC below ~0.72**.

### Is that flip-point within realistic published LLM self-confidence miscalibration? → YES (directionally).
Verbalized/self-reported LLM confidence on hard multi-step/agentic tasks is repeatedly reported with
WEAK failure discrimination, frequently in the AUROC ~0.5–0.70 band:
- **Agentic Uncertainty Reveals Agentic Overconfidence** (arXiv 2602.06948): agents that succeed 22%
  of the time predict 77% — severe overconfidence, weak success/failure discrimination.
- **Benchmarking LLM Confidence in Clinical Questions** (PubMed 40378406): "even the most accurate
  models show **minimal variation in confidence between right and wrong answers**" → AUROC ≈ 0.5.
- **The Confidence Dichotomy** (arXiv 2601.07264): tool-use agents show **severe verbalized
  overconfidence**, esp. with evidence/search tools.
- **Mind the Confidence Gap** (arXiv 2502.11028): large overconfidence / high ECE documented broadly.
So a confidence-AUC of ~0.70 (the level at which the monitor begins to win) is well within — even
optimistic relative to — commonly reported *verbalized* confidence discrimination. **On this axis the
claim looks L1-worthy.** BUT this is a coarse sim mapping (sigma_conf is a stand-in for readout noise,
not measured LLM logprobs), and it is OVERTURNED by the prior-art finding below — and by a competing
strong-confidence regime: when confidence is taken from *step-by-step self-evaluation / logprob
probes* rather than naive verbalized scores, reported AUC is **0.9+** (see Blocker 2), i.e.
sigma_conf well below the flip-point, where the monitor LOSES.

---

## BLOCKER 2 — LIVE ≥2-SOURCE PRIOR-ART CHECK (egress available; arxiv reachable, verified live)

The surviving weak-form novelty was: *"an EARLY ONLINE causal failure signature with measured
LEAD TIME, distinct from difficulty."* Live check of the three named systems + adjacent 2025–26 work:

1. **Step-level PRMs / Let's Verify Step by Step** (Lightman et al. 2023, arXiv 2305.20050) — VERIFIED.
   Step-level scoring IS online/causal (scores step ≤ t). It does NOT measure lead-time-before-failure
   and is trained on reasoning correctness, not agent-trajectory failure. Partial overlap (online
   step scoring) but not lead-time framing. NOT a full relabel by itself.

2. **AgentBoard progress-rate** (Ma et al., NeurIPS 2024, OpenReview 09Y7J22N9c) — VERIFIED.
   "Progress rate" = max fraction of annotated subgoals achieved along a trajectory. It is an
   **analytical EVALUATION metric requiring ground-truth subgoal annotations**, reported over
   completed/truncated rollouts (post-hoc), NOT an online causal failure predictor on live unseen
   trajectories and NOT lead-time-measured. So AgentBoard alone does NOT fully relabel the online
   lead-time claim — but it occupies the "online progression score" conceptual territory.

3. **Online LLM-as-Judge / stepwise self-evaluation** — VERIFIED, and this is the KILL:
   - **Self-Evaluating LLMs for Multi-Step Tasks: Stepwise Confidence Estimation for Failure
     Detection** (Mavi et al., arXiv 2511.07364, Nov 2025). Does **step-by-step (online-capable)
     confidence scoring for FAILURE DETECTION on multi-step tasks**, AUC-ROC up to ~0.9, stepwise
     beats holistic by up to +15% rel. This is precisely "online stepwise scoring of impending
     failure on multi-step agent trajectories." It IS the self-confidence baseline done online and
     done well (AUC ~0.9, i.e. sigma_conf far below our flip-point → monitor would LOSE).
   - **Accurate Failure Prediction in Agents...** (Vasudev et al., arXiv 2602.03338, Feb 2026):
     a binary LLM **critic** with offline **AUROC 0.94** predicting agent failure — and shows the
     deeper problem that accurate prediction does not imply effective prevention.

### Prior-art verdict
The conceptual space — **online/stepwise scoring of impending failure on multi-step LLM-agent
trajectories** — is OCCUPIED (2511.07364 directly; PRMs and AgentBoard adjacent). The ONLY sliver
left for CLAIM-0037 is the *specific framing* "an EXTERNAL causal-observable signature (tool-error +
looping − info-gain) with MEASURED LEAD TIME that beats BOTH self-confidence AND difficulty." But:
- EXP-0033 already showed it **does not beat self-confidence** at realistic-strong calibration, and
  the published online self-evaluators hit AUC ~0.9 (strong calibration → our model says monitor loses).
- The **lead-time** half was already weak in EXP-0033 (only 42% of failures flagged ≥1 step early,
  below the pre-registered 0.5 bar). The novelty hinges on a property the L0 itself failed.
- "Distinct from difficulty" (the one robust win, +0.095) is real but is the **weakest, least novel**
  half — process-vs-difficulty separation is implicit in any step-level PRM / progress-rate work.

The claim's distinctive contribution is therefore **relabeling** of online stepwise failure
detection, dressed in a lead-time framing the L0 cannot support.

---

## DECISION RULE (PRE-REGISTERED) → outcome
> IF flip-point within realistic miscalibration AND no published online lead-time scorer -> L1-worthy.
> ELSE -> converge.

- Flip-point within realistic *verbalized*-confidence range? **YES.**
- No published online lead-time trajectory failure scorer? **FALSE** — 2511.07364 does online stepwise
  failure detection (AUC ~0.9); PRMs/AgentBoard occupy the progression-score territory.

Because the AND fails on the prior-art conjunct, the pre-registered rule fires the ELSE branch:
**CONVERGE.** Additionally, even the flip-point favorability is fragile: the published online
self-evaluators achieve AUC ~0.9 (sigma_conf ≪ flip), the regime where our own model says the monitor
LOSES. The monitor only wins against *naive verbalized* confidence, not against the *online stepwise
self-evaluation* that the prior art already deploys.

## RECOMMENDATION: RED / weaken-to-relabeling.
Do NOT spend a GPU L1. The strong claim ("cheap external online monitor beats the agent's own signal
AND difficulty, with lead time") is (a) dominated by published online stepwise self-evaluation
(AUC ~0.9), and (b) its surviving lead-time novelty is unsupported even at L0 (42% coverage). The only
robust positive — "progression signal is distinct from static difficulty" — is real but is the
least-novel half and is implicit in existing PRM/progress-rate work. This cheap L0 did its job:
it AVOIDED a wasted GPU L1.

## ARTIFACTS
- PRE_REGISTRATION.md (committed before run, HEAD c5998f9)
- sweep.py (imports EXP-0033/exp.py unchanged)
- results/sweep_sigma_conf.csv, results/flip_summary.csv
- logs/sweep.log
