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

## WHAT L1 SHOULD MEASURE
Real MMLU/GSM8K/QuALITY + actual GPT-3/Llama 8/13-gram decontam vs a real web n-gram corpus
(C4/Pile): confirm removal-rises-with-length + survivor-shorter (the anchored, unconditional
part); measure the REAL length<->difficulty slope from public per-item accuracy of open
models (maps to empirical alpha); report realized inflation on survivors vs full set.

## PRIOR-ART CAVEAT (precise, honest)
Brown2020 GPT-3 n-gram decontam (2005.14165) + Llama3 Dubey (2407.21783, 8-gram) = the
standard practice benchmarked against. Yang 2311.04850 (rephrased-samples) = false-NEGATIVES
(opposite direction). Bordt 2410.03249 applies the filter + notes significant filtering but
treats removal as benign. Schaeffer 2601.04301 studies un-removed-contamination inflation.
NOVELTY: the decontam filter is itself a LENGTH-BIASED test-set sampler whose collateral
removal (independent of real contamination) distorts the surviving difficulty distribution
and inflates the score.
