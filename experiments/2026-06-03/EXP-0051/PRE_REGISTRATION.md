# PRE_REGISTRATION — EXP-0051 (L1, REAL DATA) / CLAIM-0048
**Researcher:** researcher-0049. **Committed BEFORE running.** Honest pipeline; a negative is a WIN.
**Node:** cli:dengcchi-mac (Stage A, CPU). Stage B only if gated: cli:devgpu014 (H100; NEVER devgpu499/MI350X).

## CLAIM under test (committee#1 VERDICT-0046, HELD/YELLOW)
Raising an answer-equivalence canonicalizer's RECALL has a SIGN-FLIPPING effect on maj@k
self-consistency accuracy, governed by the correct-vs-incorrect FRAGMENTATION ASYMMETRY phi.
Committee diagnosis: mechanism real but = classical SPOILER/Duverger vote-splitting applied to
eval-canonicalization (novel domain-application). Requires REAL-DATA L1 for ECOLOGICAL plausibility.

## ANTI-CIRCULARITY / GROUND TRUTH
GT = true answer-equivalence, GOLD-ANCHORED: two answer strings are TRULY-equivalent iff both
parse to the gold value (or, for wrong answers, to the same numeric value). The canonicalizer
reads ONLY answer strings, NEVER the gold or GT class. q (precision) measured against this GT.

## DATA SOURCE (real, prefer real)
- PRIMARY: GSM8K test (1319 problems), real, downloaded from openai/grade-school-math test.jsonl.
  Gold final answers parsed from "#### N". Free-form numeric answers => real surface-form variety.
- Wrong-answer surface distributions: where real model samples are unavailable in Stage A, we
  construct REALISTIC distractor surface forms from gold by applying the SAME real-world
  surface transforms GSM8K answers exhibit ($, commas, "X dollars", trailing .0, spacing) plus
  realistic arithmetic-error magnitudes. This is the only proxy element and is FLAGGED. Stage B
  (if gated) replaces it with REAL model samples.
- Optional secondary: Hendrycks MATH algebra (fractions/\frac/decimals) if fetch succeeds.

## REAL CANONICALIZER PAIR (differing recall)
- (i) EXACT-MATCH (low recall): byte-equal after trivial strip.
- (ii) NUMERIC/Minerva-style normalizer (HIGH recall): strip $/commas/units/whitespace, parse
  ints, decimals, fractions a/b, \frac{a}{b}, percentages; canonicalize via sympy.Rational /
  sympy.simplify to an exact numeric key. Two strings merge iff same numeric key.
- (iii) optional intermediate: lexical (lowercase+strip punctuation+strip units) — mid recall.

## MEASUREMENTS (the two load-bearing real quantities the committee demanded)
(a) EMPIRICAL PHI distribution: per problem, build the correct-equivalence-class surface set and
    the dominant-incorrect class surface set; measure surface-form entropy of each (H_C, H_W);
    phi = H_C - H_W. Report the DISTRIBUTION across problems. Question: is the asymmetry real, or
    do correct & incorrect fragment SYMMETRICALLY (phi ~ 0) in practice?
(b) EMPIRICAL PRECISION q of the HIGH-recall numeric normalizer: of all answer-string PAIRS it
    MERGES, fraction that are TRULY GT-equivalent (gold-anchored). Make-or-break: L0 shows the
    effect DIES at q<=0.6.

## STAGE-A GATE THRESHOLD (pre-committed)
PROCEED to Stage B iff BOTH:
  - phi-asymmetry is REAL in the data: median/mean phi is materially != 0 in the direction that
    makes recall matter (errors more fragmented than correct, i.e. phi<0, OR vice versa), i.e.
    |mean phi| reliably bounded away from 0 with a clear nonzero fraction of asymmetric problems
    (pre-committed: at least 25% of problems show |phi|>0.2 AND mean phi sign is consistent), AND
  - high-recall q > 0.6 with margin (pre-committed: q >= 0.80).
If gate FAILS (real q<=0.6 OR phi symmetric): STOP. Report HONEST NEGATIVE — the L0 sign-flip has
NO ecological foothold. This is a clean valuable L1 result; do NOT waste GPU on Stage B.

## STAGE B (only if gated) — real model-pair maj@k inversion
2-3 small open models on devgpu014 H100 (reuse EXP-0003 venv/proxy; cap mem; os._exit), temperature
sampling k=8..64 on a GSM8K slice. For two FIXED models+samples compute maj@k under exact-match vs
numeric grader; test pairwise ranking INVERSION purely from grader swap. Report inversion OR null.
If not runnable in budget: Stage A is the L1 deliverable + spec what L2 needs.

## DOM_FRAC SENSITIVITY
Re-measure phi distribution + slope direction under varying dominant-incorrect mass assumptions.

## CITATIONS
- Spoiler effect / Duverger's Law (vote-splitting) — the mechanism analogue.
- Bulian et al. 2022 "Tomayto Tomahto" (BEM, answer-equivalence beyond exact match).
- Kuhn et al. 2023 / Farquhar et al. 2024 — semantic entropy (clustering answer meanings).
- Biderman et al. 2024 (arXiv:2405.14782) — eval reproducibility / scoring sensitivity.

## FLAGS
- The L0 ranking-INVERSION construction (EXP-0050 §3) is EXPLORATORY (post-hoc retune of model p_C).
- Stage-A wrong-answer surface proxy is FLAGGED; Stage B replaces with real samples if gated.
