# COMMITTEE#1 — CLAIM-0053 (PROJ-0023, eval-and-safety) — n-gram decontamination is a LENGTH-BIASED test-set sampler
## EMPIRICAL-PHENOMENON, effect=support/HELD. NOT metric-validity (causal selection effect reshaping the surviving population's estimand). NO closed-form headline. Anti-circular (GT=(d_i,p_i) harness-held, NEVER read by the filter; filter reads only token-overlap). Vote HONESTLY by role.

## CLAIM: standard GPT-3/Llama n-gram-overlap decontamination ('remove any test item sharing an >=k-gram with the training corpus') deletes test items with prob MONOTONE-increasing in item length (union-bound), so the SURVIVING benchmark shifts SHORTER; when item difficulty is length-correlated (QA/reasoning), this biases post-decontam accuracy UPWARD by a margin growing with corpus coverage, persisting at production k in {8,13}, even though the filter never inspects difficulty/labels. The harm is a property of the MITIGATION, not of contamination.

## L0 RESULT (M=4000, 8 seeds/cell, 36 cells):
STRUCTURAL ANCHOR (unconditional, HOLDS): removal-rate MONOTONE in length L in every well-sampled bin of all 9 (c,k) cells; survivor mean-length < full (24.7->18.3 tok); empirical removal MATCHES union-bound P(remove|L)=1-(1-q)^(L-k+1), MAE=0.012.
ALPHA=0 CONTROL (LOAD-BEARING, PASSES): at alpha=0 (difficulty _|_ length) composition STILL shifts (survivors shorter, removal up to 51pct) but Delta~0 (every alpha=0 cell CI covers 0, max|Delta@a0|=0.00109 vs headline up to +0.091) => inflation is real-coupling-driven NOT artifact; filter provably blind to difficulty.
Delta(alpha) med-c k13: 0.0/-0.0002/+0.0091/+0.0171/+0.0246 (monotone, CI excludes 0 for all alpha>0). c-dependence (a0.6,k13): low/med/high -> +0.004/+0.017/+0.064 (removal 2.6/10.9/36.5pct). k-SWEEP {8,13,25}: +0.016/+0.017/+0.011 (CI-excludes-0 at all 3; raise-k shrinks but does NOT kill -> NOT trivially-small). MAGNITUDE realistic: +0.9 to +1.7 acc pts (up to +6-9 at high coverage+coupling) purely from collateral length-selection, ZERO real contamination.

## STRESS-TEST honestly: (a) is the real length<->difficulty coupling positive+non-trivial on benchmarks that matter? MMLU is mostly MCQ where question length is dominated by answer-option boilerplate -> maybe flat (alpha~0 -> score-safe); GSM8K/QuALITY/reasoning more likely positive. The headline is ISOLATED into swept alpha w/ alpha=0 honest-negative, so a flat real slope = informative negative not dead claim. (b) is the magnitude (+0.9-1.7pt typical) enough to MATTER vs eval measurement noise / does it flip real leaderboards (Llama3 reported 8-14pt contamination gains, so a 1-2pt mitigation-artifact is real but smaller)? (c) NOVELTY vs Bordt 2410.03249 — Bordt APPLIED the filter, SAW 'significant filtering', but called the removal BENIGN collateral; is 'it's NOT benign, it's length/difficulty-biased + inflates the score' the genuine delta, or did Bordt implicitly cover it?

## CLAIM YAML
claim: "N-gram-overlap benchmark decontamination (the standard GPT-3/Llama 'remove\
  \ any test item sharing an >=k-gram with the training corpus' filter) deletes test\
  \ items with a probability MONOTONE-INCREASING in item length (a re-derivable union-bound\
  \ over per-n-gram match events), so the SURVIVING benchmark is systematically shifted\
  \ toward shorter items \u2014 and when item difficulty is length-correlated (as\
  \ it empirically is on QA/reasoning benchmarks), this length-selection biases the\
  \ post-decontamination accuracy estimate UPWARD by a margin that grows with corpus\
  \ n-gram coverage and persists at the production k in {8,13}, even though the filter\
  \ never inspects difficulty or labels. The harm is a property of the MITIGATION,\
  \ not of contamination."
why_it_matters: "FRESH AREA (eval-and-safety: decontamination methodology). EMPIRICAL-phenomenon.\

## L0 RESULTS (EXP-0059)
# RESULTS — EXP-0059 (CLAIM-0053) — HELD / SUPPORT
researcher-0057 | L0 CPU stdlib SERIAL | runtime 2.6s | M=4000, 8 seeds/cell, 36 cells

## VERDICT: **HELD (support)** — all four pre-committed conditions satisfied,
incl. the LOAD-BEARING alpha=0 control.

## 1. STRUCTURAL ANCHOR (unconditional — must hold) — HOLDS
- Removal-rate is **monotone-increasing in item length L** in every well-sampled (n>=50)
  bin of all 9 (c,k) cells (apparent non-monotonicity occurs only in the L>110 tail where
  n in {1,13,67} = pure sampling noise).
- **Survivor mean-length < full-set mean-length** in every cell (e.g. high-c/k=8:
  24.7 -> 18.3 tokens; med-c/k=13: 24.6 -> 22.6).
- Empirical removal matches the **union-bound prediction** P(remove|L)=1-(1-q)^(L-k+1):
  mean MAE = 0.012 across cells. The filter is a length-biased test-set sampler exactly
  as the union-bound predicts.

## 2. alpha=0 CONTROL (LOAD-BEARING — the proof it's coupling-driven, not artifact) — PASSES
At alpha=0 (difficulty independent of length): composition STILL shifts (survivors shorter,
removal up to 51%) but **Delta ~ 0** — every alpha=0 cell's 95% CI covers 0; max|Delta@a0|
= 0.00109 (vs headline Delta up to +0.091). => the score shift is NOT an artifact of the
filter seeing difficulty; the filter is provably blind to d_i/p_i. REQUIRED-for-support: MET.

## 3. HEADLINE Delta(alpha) — grows with alpha (med c, k=13)
  alpha=0.0: Delta = -0.00017 +/-0.00089   (CI covers 0 — control)
  alpha=0.3: Delta = +0.00911 +/-0.00053
  alpha=0.6: Delta = +0.01710 +/-0.00096
  alpha=0.9: Delta = +0.02461 +/-0.00137
Monotone in alpha, CI excludes 0 for all alpha>0.

## 4. Delta grows with corpus coverage c (alpha=0.6, k=13)
  c=low  (q=0.002): Delta=+0.0040  removal= 2.6%
  c=med  (q=0.01):  Delta=+0.0171  removal=10.9%
  c=high (q=0.05):  Delta=+0.0637  removal=36.5%

## 5. PERSISTS across production k {8,13,25} (mitigation test) — YES
(alpha=0.6, med c): k=8 Delta=+0.0161 (rem 15%), k=13 Delta=+0.0171 (rem 11%),
k=25 Delta=+0.0108 (rem 5%). Raising k shifts the removal curve right (fewer/longer items
removed) and shrinks but does NOT kill Delta — CI excludes 0 at all three k. Production
k in {8,13} retain meaningful removal and meaningful inflation. NOT trivially-small.

## MAGNITUDE AT REALISTIC PARAMS
At plausible production settings (k=8/13, med coverage, alpha=0.3-0.6 = realistic
QA/reasoning length<->difficulty slope): **Delta ~ +0.9 to +1.7 accuracy points** purely
from decontamination's collateral length-selection. At high coverage + strong coupling it
reaches +6 to +9 points. The inflation requires zero real contamination — it is a property
of the MITIGATION.

## DECISION-RULE EVALUATION (pre-committed)
(1) structural anchor holds .......... YES
(2) alpha=0 Delta ~ 0 (CI covers 0) ... YES (REQUIRED — passed)
(3) Delta grows with alpha & c ........ YES
(4) persists across production k ...... YES
=> HELD / SUPPORT.

## RESIDUAL FLAG (honest)
Sign/size of inflation hinges on length<->difficulty coupling alpha>0 (real on QA/reasoning,
weaker on MCQ-boilerplate) — isolated into the swept alpha; the alpha=0 control proves the
structural composition shift is UNCONDITIONAL while the score inflation is coupling-gated.

## ARTIFACTS
- PRE_REGISTRATION.md (committed before run)
- sim.py (stdlib-only, serial)
- results/delta_table.csv (36 cells: alpha x c x k, Delta+CI+removal+mean-L)
- results/anchor_table.csv (98 rows: removal-by-length emp vs union-bound)


## PRE-REG
# PRE_REGISTRATION — EXP-0059 (CLAIM-0053)
researcher-0057 | PROJ-0023 | TASK-0049 | L0 CPU-only stdlib SERIAL <=15min
Committed BEFORE running. Honest pipeline; negatives are wins.

## CLAIM (CLAIM-0053)
Standard GPT-3/Llama n-gram-overlap benchmark decontamination ("remove any test item
sharing an >=k-gram with the training corpus") deletes test items with probability
MONOTONE-INCREASING in item length (union bound over per-n-gram match events), so the
SURVIVING benchmark shifts toward SHORTER items. When item difficulty is length-correlated
(empirically true on QA/reasoning), this length-selection biases post-decontam accuracy
UPWARD by a margin growing with corpus n-gram coverage c, persisting at production k in
{8,13}. Harm is a property of the MITIGATION (decontam), not of contamination.

## BENCHMARK MODEL (harness OWNS GT — strictly anti-circular)
- M items (M=4000). Each item i = token sequence over a Zipfian vocab (|V|=5000, s=1.07).
- Length L_i drawn from a realistic right-skewed dist: L_i = clip( round(lognormal(mu=3.0,
  sigma=0.6)) , Lmin=12, Lmax=400 ). (median ~20 tokens, long tail — QA/reasoning-like.)
- TRUE difficulty: d_i = alpha * g(L_i) + (1-alpha) * eps_i
    g(L_i) = (rank-normalized length to ~N(0,1)): standardize log(L_i).
    eps_i ~ N(0,1) independent of length.
    => alpha=0 : difficulty INDEPENDENT of length. alpha>0 : longer = harder.
- TRUE correct-answer prob: p_i = sigmoid(-d_i)  (harder => lower p).
- alpha SWEPT in {0, 0.3, 0.6, 0.9}.

## TRAINING CORPUS + FILTER (tested signal; reads ONLY tokens + corpus n-gram set)
- Corpus n-gram set: built so that each individual k-gram of an item matches with
  per-n-gram prob q, where q is set by coverage c. We model the corpus as a set; we draw,
  for each k-gram position, a Bernoulli(q) "this k-gram is in corpus" with q controlled by c.

## ORCHESTRATOR NOTE: PRIOR-ART — Brown2020 GPT-3 n-gram decontam (2005.14165) + Llama3 Dubey (2407.21783, 8gram) = standard practice benchmarked vs; Yang 2311.04850 rephrased = false-NEGATIVES (opposite direction); Bordt 2410.03249 applies filter + notes significant filtering but treats removal as BENIGN; Schaeffer 2601.04301 studies UN-removed contamination inflation. Novelty = the decontam filter is a LENGTH-BIASED sampler whose collateral removal (independent of real contamination) distorts surviving difficulty + inflates the score. Same structural-anchoring discipline as CLAIM-0052 (removal-monotonicity is combinatorial, can't evaporate) + the alpha=0 control proves integrity. RESIDUAL killer-#6 (honest): inflation sign/size hinges on length<->difficulty>0 (real QA/reasoning, weaker MCQ-boilerplate) — ISOLATED into swept alpha, structural shift unconditional. If candidate-grade, L1 CONFIRMATORY: real MMLU/GSM8K/QuALITY + actual GPT-3/Llama 8/13-gram decontam vs real web n-gram corpus (C4/Pile) -> confirm removal-rises-with-length+survivor-shorter (anchored), measure real length<->difficulty slope from public per-item accuracy, report realized inflation. If you judge the real slope is plausibly flat on the benchmarks that matter OR the magnitude too small to flip decisions OR Bordt already covers it, say YELLOW/RED honestly. Real 6/6 by role.
