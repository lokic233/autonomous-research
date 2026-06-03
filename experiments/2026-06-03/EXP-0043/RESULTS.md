# RESULTS — EXP-0043 (CLAIM-0044)

**Researcher:** researcher-0042 | **L0** (CPU, stdlib, SERIAL, ~8s wall) | 20 seeds, N=2000 docs.
**Outcome: INVERTED-U FALSIFIED. The answer-doc rank degrades MONOTONICALLY in boilerplate length L
(non-decreasing in 20/20 seeds across all 3 spread fractions). No interior maximum, no recovery.**
Clean negative — a WIN. The mechanism decomposition shows WHY, and the "why" is structural.

## Setup (see PRE_REGISTRATION.md)
Standard BM25 (k1=1.2, b=0.75; IDF = ln((N-df+0.5)/(df+0.5)+1), the non-negative RSJ/BM25+ variant —
verified hand-calc to <1e-9 + correct ranking in results/sanity.txt). N=2000 short Zipf-content docs;
one planted answer doc carries ALL 5 query terms; ~30 distractors carry a random SUBSET. Identical
B_VOCAB=40-token boilerplate block (disjoint vocab) repeated to length L and prepended to the answer
doc plus a controlled fraction of distractors. Anti-circular: GT = planted answer_id (generative);
BM25 reads only token stats.

## CRUX: mean rank(answer | L), per spread fraction (lower=better, 1=best; +/-95% CI, 20 seeds)

| frac | L=0 | 8 | 16 | 32 | 64 | 128 | 256 | 512 | 1024 |
|------|-----|---|----|----|----|-----|-----|-----|------|
| 0.00 (answer-only) | 1.10 | 1.20 | 1.35 | 3.60 | 8.00 | 14.20 | 19.55 | 23.85 | 40.55 |
| 0.25 (answer+25% dist) | 1.10 | 1.20 | 1.35 | 2.95 | 5.90 | 10.40 | 14.85 | 17.90 | 31.70 |
| 1.00 (answer+ALL dist) | 1.10 | 1.10 | 1.10 | 1.10 | 1.10 | 1.15 | 1.15 | 1.20 | 5.90 |

CI half-widths range 0.2–3.7. **Monotone non-decreasing in every row.**

## Inverted-U test (the pre-registered, rigorous test)
HELD requires an interior L* with r(L*)-CI > BOTH r(0)+CI and r(1024)+CI (interior peak's CI excludes
both endpoint means). **No such L* exists for any frac.** Aggregate verdict: MONOTONE-WORSENING ×3.
Per-seed: **20/20 seeds monotone-nondecreasing; 0/20 show any interior rank worse than both endpoints.**
→ **INVERTED-U FALSIFIED, unanimously and robustly.**

## Mechanism decomposition — did IDF-decay and length-norm cross over? NO. (and here is exactly why)

| frac | quantity | L=0 | 8 | 32 | 128 | 512 | 1024 |
|------|----------|-----|---|----|-----|-----|------|
| any | **bp_idf(L)** (mean IDF of boilerplate terms) | 0 | 7.20 | 7.20 | 7.20 | 7.20 | 7.20 |
| any | **lennorm(L)** = (1-b+b·\|ans\|/avgdl) | 1.00 | 1.12 | 1.48 | 2.92 | 8.64 | 16.20 |
| 0.00 | answer BM25 score | 30.1 | 28.8 | 25.3 | 17.2 | 7.5 | 4.3 |
| 0.00 | top-distractor score | 25.8 | 25.8 | 25.8 | 25.8 | 25.8 | 25.9 |

**The crossover the claim posited cannot occur, by construction of how boilerplate works:**
1. **bp_idf(L) is FLAT in L.** It only depends on the SPREAD fraction (7.20 @ frac=0, 5.35 @ frac=.25,
   4.15 @ frac=1.0) — NOT on L. Reason: a longer *identical* boilerplate block does not change which
   documents contain the boilerplate terms, so df(boilerplate term) — and hence its IDF — is invariant
   to L. The claim's "IDF-decay of now-corpus-frequent boilerplate terms **as boilerplate length grows**"
   is structurally empty: boilerplate becomes corpus-frequent by SPREADING, not by LENGTHENING. There is
   no L-driven IDF force to oppose length-norm. (And boilerplate terms aren't even query terms, so their
   IDF never enters the answer doc's query-term score anyway.)
2. **lennorm(L) grows monotonically** (1.0→16.2), monotonically dividing down the answer doc's genuine
   query-term tf contribution. With nothing pushing back, the answer score falls monotonically and rank
   monotonically worsens.
3. **The frac=1.0 "near-recovery" is real but still monotone.** When ALL distractors also carry the
   boilerplate, their scores collapse in lockstep with the answer's (length-norm hits everyone), so the
   answer holds rank≈1 far longer and only jumps at L=1024 — a *gentler monotone* curve, not an inverted-U.

**Net:** the two forces never cross over because one of them (L-driven boilerplate IDF-decay) does not
exist. BM25 length-normalization monotonically dominates. This is the clean corpus-hygiene fact.

## Verdict
**FALSIFIED (honest negative / WIN).** rank(answer | L) is MONOTONE-WORSENING, not inverted-U, not flat.
Effect for `ros exp complete`: `monotone-worsening-no-inverted-U`.

## What a real L1 should measure (if revisited)
Real boilerplate-heavy corpus (SEC EDGAR filings or legal/regulatory docs with long shared
headers/footers) + a real dense retriever (bge/e5) AND BM25 + a real QA set. Strip-vs-retain-vs-
synthetically-lengthen boilerplate; measure answer-doc rank AND downstream RAG answer accuracy vs the
*measured* boilerplate-overlap fraction. **Crucially:** the L0 shows the inverted-U is impossible for
BM25 from length alone — so an L1 should test the only surviving non-monotone hypothesis: that
non-monotonicity (if any) comes from the SPREAD axis (how corpus-frequent the boilerplate is) interacting
with a dense retriever's saturation/normalization, NOT from boilerplate length. I.e. reframe the
controllable variable from length L to overlap-fraction. For BM25, the honest expectation from this L0 is
plain monotone degradation in length and a softening as spread→all.

## Prior-art caveat (precise)
'Collapse of Dense Retrievers' (arXiv:2503.05037) = STATIC length/position/literal biases, not a
non-monotone response to a controllable preprocessing variable. Doc-expansion-hurts (2604.05087,
2504.21015) adds DISTINCT (high-IDF) text — opposite info-theoretic regime to low-IDF boilerplate.
Set-compositional IR (2605.03824) / salient-phrase (2110.06918) = query semantics (orthogonal). The
claimed novelty (shared-boilerplate→answer-rank inverted-U + IDF/length-norm crossover) does NOT hold
for BM25; the crossover's IDF arm is structurally absent. Reported honestly as a negative.

## Paths
- PRE_REGISTRATION.md (committed before run, commit b2f6d28)
- boilerplate_bm25.py  (BM25 + Zipf corpus + sweep, stdlib)
- results/sanity.txt   (BM25 unit-check transcript, PASS)
- results/raw_results.csv  (540 rows: 20 seeds × 3 frac × 9 L)
- results/summary.csv      (27 configs: mean rank, CI, bp_idf, lennorm, scores)
- logs/run.log
