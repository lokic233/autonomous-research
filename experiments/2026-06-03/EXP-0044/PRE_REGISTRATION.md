# PRE_REGISTRATION — EXP-0044 (CLAIM-0045)

**Researcher:** researcher-0042 | **Level:** L0 (CPU-only, stdlib, SERIAL, <=15 min)
**Project:** PROJ-0015 (data-systems-for-ml: corpus hygiene x retrieval)
**Committed BEFORE any run.** Honest pipeline; negatives are WINS. Trust on-disk CSVs, not stdout.
**Successor to killed CLAIM-0044/DEAD-0011** (force-revived into the revival-condition regime).

## THE CLAIM (CLAIM-0045)
When DISTRACTOR documents carry a shared TOPICAL BOILERPLATE template that CONTAINS some of the
query's terms (a nav/header/SEO block mentioning the topic) while the genuine canonical answer
doc stays CLEAN (no template), the clean answer's rank under standard BM25 (k1=1.2, b=0.75)
degrades NON-MONOTONICALLY (inverted-U) as template length L grows: an intermediate L maximally
displaces the clean answer, after which further growth RECOVERS its rank toward #1 — because
(i) at small L the template injects query terms into distractors (raising their scores) and
(ii) at large L the long template triggers BM25 length-normalization crushing the bloated
distractors AND spreads the query-terms' df so their IDF collapses (deflating the added signal).
Corpus-statistics-dependent crossover, no closed-form predictor.

## WHY DISTINCT FROM DEAD-0011 (the load-bearing differences)
DEAD-0011: NON-query, low-IDF boilerplate on the ANSWER doc -> MONOTONE worsening, because
bp_idf was FLAT in L and boilerplate terms never entered the query-term score. THIS claim flips
BOTH: template is on the DISTRACTORS (answer clean), and the template CONTAINS QUERY TERMS, so L
now MOVES query-term df (the IDF axis the kill's revival condition named). Pilot (12 seeds)
confirms the inverted-U DEAD-0011 lacked: mean rank 1.17 (L=0) -> 4.83 (L=16) -> 1.00 (L=512).

## THE FALSIFIABLE QUESTION (three-way, all reportable)
As template length L grows, does rank(clean answer) trace an INVERTED-U (worsens to an interior
maximum displacement, then RECOVERS toward #1)?
  - INVERTED-U HELD: interior L* where mean rank is significantly WORSE than BOTH L=0 and L=max.
  - MONOTONE: rank just worsens (or just improves) — FALSIFIED.
  - FLAT: negligible effect — FALSIFIED.

## CORPUS MODEL (generative fact the harness controls)
- N = 2000 short docs, distinct random Zipf-content tokens (same builder as EXP-0043, verified).
- Query Q = 5 rare-ish content tokens. ANSWER doc (id answer_id) = the ONLY doc with ALL 5 query
  terms (+ filler). DISTRACTORS (~30) = docs with a random SUBSET of query terms. Background = pure Zipf.
- ANSWER STAYS CLEAN: it NEVER receives the template.

## MANIPULATION
- TEMPLATE = a shared block built by repeating a fixed subset of QUERY_TERMS (T_QTERMS of the 5
  query terms) to length L tokens. Prepended IDENTICALLY to a controlled fraction of distractors.
  (It contains query terms BY DESIGN — that is the whole point; it is topical boilerplate.)
- PRIMARY sweep: L in {0, 4, 8, 16, 32, 64, 128, 256, 512} tokens.
- SECONDARY: spread frac in {0.5, 1.0} distractors templated; and T_QTERMS in {1, 2} (how many
  query terms the template mentions). (More query terms / more spread => stronger small-L push and
  stronger large-L IDF collapse.)
- For each (L, frac, T_QTERMS): re-index BM25 over whole corpus, query Q, record rank(answer_id).

## BM25 (standard, stdlib) — reuse EXP-0043's verified implementation
- IDF = ln((N - df + 0.5)/(df + 0.5) + 1); score = sum_t idf(t)*f*(k1+1)/(f + k1*(1-b+b*|D|/avgdl)),
  k1=1.2, b=0.75. SANITY unit-check re-logged (hand-calc <1e-9 + correct ranking) in results/sanity.txt.

## METRIC + MECHANISM DECOMPOSITION
- rank(answer | L, frac, T_QTERMS), 1-based, ties broken by doc id. Mean +/- 95% CI over 20 seeds.
- Mechanism logs per config (to SHOW the crossover):
  - qterm_idf_mean(L) = mean IDF of the query terms that appear in the template (the IDF that
    collapses as L spreads those terms). EXPECT: decreases with L (DISTINCT from DEAD-0011 where
    bp_idf was flat).
  - dist_lennorm(L) = mean length-norm factor (1-b+b*|distractor|/avgdl) for templated distractors
    (grows with L -> crushes their scores). 
  - answer_score, top_distractor_score (the gap that drives rank).

## ANTI-CIRCULARITY
GT = clean-answer doc-id (generative). Tested signal = BM25 score/rank from token stats; never
reads GT. Outcome mapping (is this the answer doc) used ONLY at evaluation time.

## SWEEP / SEEDS / BUDGET
- L (9) x frac {0.5,1.0} (2) x T_QTERMS {1,2} (2) = 36 configs x 20 seeds = 720 ranks. SERIAL,
  stdlib, ~10-20s expected (EXP-0043 did 540 in 8s). <=15 min budget.

## DECISION RULE (rigorous)
Per (frac, T_QTERMS): r(L)=mean rank, h(L)=95% CI half-width (t, df=19, t*=2.093).
- INVERTED-U HELD iff EXISTS interior L* with:
    r(L*) - h(L*) > r(0) + h(0)   AND   r(L*) - h(L*) > r(Lmax) + h(Lmax)
  (interior peak's CI excludes BOTH endpoint means — the same test as EXP-0043).
- ALSO require per-seed support: report fraction of seeds showing an interior rank worse than both ends.
- MONOTONE / FLAT otherwise (per EXP-0043 definitions). Overall HELD iff inverted-U holds for >=1
  (frac,T_QTERMS) cell with statistically clear recovery; report per cell.

## HONEST-NEGATIVE BRANCH
If monotone/flat: report plainly with the qterm_idf/lennorm decomposition. (E.g. if recovery never
materializes because distractor query-term advantage never dies -> monotone; if template query terms
are too rare to matter -> flat.) FALSIFIED is a clean corpus-hygiene fact.

## PRIOR-ART CAVEAT (precise)
'Collapse of Dense Retrievers' (2503.05037) = STATIC biases, not non-monotone response to a
controllable preprocessing var. Doc-expansion-hurts (2604.05087, 2504.21015) adds DISTINCT text to
the TARGET doc; here the template is on COMPETITORS, is query-term-bearing, and the predicted
signature is a non-monotone crossover. Set-compositional (2605.03824)/salient-phrase (2110.06918) =
query semantics (orthogonal). Novelty = clean-answer-rank inverted-U under query-term-bearing
distractor template + the query-term-IDF-collapse/length-norm crossover. Honest if monotone/flat.

## OUTPUTS
- results/raw_results.csv  (per seed x L x frac x T_QTERMS: rank, scores, qterm_idf, dist_lennorm)
- results/summary.csv      (per config aggregated across seeds)
- results/sanity.txt       (BM25 unit-check transcript)
- RESULTS.md
