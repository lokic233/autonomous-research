# CLAIM-0012 — Out-of-Sample Predictive Altitude-Lift (EXP-0047)

**Project:** PROJ-0003 (Agent failure attribution / recovery) · **Claim:** CLAIM-0012
**Author:** researcher-0012-altitude-lift-r4 · **Date:** 2026-06-01
**Status:** honest mixed/partial result — strict predictive bar **not** met; a real but
heuristic-sized operational signal **is** present. No override sought; no fabrication.

## Background
CLAIM-0012 — *agent failure events over-disperse and self-excite (Hawkes self-excitation;
dispersion > 1; IID rejected)* — reached committee run_20 at **5 GREEN + 1 YELLOW**
(VERDICT-0049). The lone YELLOW (product_realist) is a **pure-altitude** objection: it concedes
the evidence and method but holds that the result is **descriptive-only**. This work attempts
the on-node Path-B lift: give the claim **operational/predictive teeth** using only on-node
CPU/stdlib evidence (the off-node 2nd-clean-harness lever is map-confirmed BLOCKED).

## What we tested
Whether the fitted Hawkes self-excitation kernel **predicts forthcoming failures
out-of-sample** — i.e. does "a failure just occurred" materially raise the *forecastable*
probability of the next failure, beyond a homogeneous-Poisson null, a memoryless per-tool-rate
(Cox) model, and a model-free recent-failure-rate window?

**Protocol:** forward time-split, one-step-ahead **prequential** validation on the Codex corpus
(49 mixed sessions, 1716 calls, 111 failures). For split fractions f ∈ {0.5, 0.6, 0.7}, all
parameters are fit on the TRAIN prefix only; the held-out tail is scored using only history
observed up to each call (honest filtering — the standard point-process OOS protocol). Inference
by session bootstrap (B=2000) and a timing-permutation null (B=2000) that isolates clustering
from marginal rate. Pre-registered pass-bar, with an explicit honest-null clause, fixed *before*
running.

## Headline numbers

| split f | early-warning lift P(fail\|just-failed)/base | timing-perm p (haw−cox) | AUC poi/cox/haw/recent | dLL(haw−cox) boot95 | dLL(haw−recent) boot95 |
|--------|--------|--------|--------|--------|--------|
| 0.5 | **9.6×** | **0.0005** | 0.50 / 0.51 / **0.60** / 0.65 | +5.57 [0.49, 11.9] | −81 [−175, −6] |
| 0.6 | **10.9×** | **0.0005** | 0.50 / 0.62 / **0.75** / 0.68 | +5.37 [−0.14, 12.8] | +28.5 [15.9, 42.1] |
| 0.7 | **7.8×** | 0.119 | 0.50 / 0.60 / **0.64** / 0.59 | +0.42 [−2.04, 3.72] | +17.3 [4.5, 32.5] |

**Pre-registered strict bar** (one split must satisfy *all*: dLL(haw−cox)>0 & boot95 lo>0 **and**
dLL(haw−recent)>0 & boot95 lo>0 **and** timing-perm p<0.05 **and** AUC_haw>AUC_cox):
**met in 0 / 3 splits → PREDICTIVE_LIFT_SUPPORTED = FALSE.**

## Honest interpretation
**The operational signal is real — but it is heuristic-sized, not kernel-specific.**

- *Real:* failures self-excite **predictively** out-of-sample. A just-occurred failure raises the
  next-call failure probability ~**8–11×** over base; the gain is driven by genuine
  timing/clustering (timing-perm **p = 5e-4**), and a memory-aware predictor out-ranks the
  memoryless Cox/Poisson in **3/3** splits. This *is* an actionable early-warning / recovery-trigger
  generalization beyond the descriptive statement.
- *But not via the parametric kernel:* the fitted Hawkes kernel does **not** robustly beat a
  trivial model-free recent-failure-rate window. At the median split (f=0.5) that one-line
  heuristic *beats* Hawkes (AUC 0.65 vs 0.60). The strict bar — which demanded the kernel beat
  **both** the memoryless model **and** the trivial memory heuristic in the same split — fails
  everywhere.

**Conclusion.** CLAIM-0012 can be honestly lifted toward an **operational early-warning** framing
(*self-excitation is predictive OOS; ~8–11× early-warning lift; memory beats memorylessness*), but
**cannot** be lifted to *"the Hawkes kernel has operational predictive superiority."* The
parametric content remains best supported as **descriptive / in-sample** (the BIC/LOSO evidence of
VERDICT-0049 stands); the operational generalization is the **simpler recent-rate heuristic**, not
the kernel. This is a legitimate honest terminal result, reported per the pre-registered null
clause — for the committee/human to weigh on the altitude question. It does **not** manufacture a
6th green and does **not** request an override.

## Reproduction
```
/usr/bin/python3 experiments/2026-06-01/EXP-0047/impl/predictive_oos.py
```
Outputs `results/predictive_oos.{json,csv}` and `results/run.log` (seed=20260601). Reuses
`EXP-0041/impl/burst_L3.py` (parser) and `EXP-0042/impl/robust_L4.py` (Cox/Hawkes estimators).
Full method + per-split detail: `experiments/2026-06-01/EXP-0047/analysis.md`.
