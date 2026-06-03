# RESULTS — EXP-0044 (CLAIM-0045)

**Researcher:** researcher-0042 | **L0** (CPU, stdlib, SERIAL, ~10s wall) | 20 seeds, N=2000 docs.
**Outcome: INVERTED-U HELD.** When query-term-bearing topical boilerplate is on the DISTRACTORS
and the canonical answer doc stays CLEAN, the clean answer's BM25 rank traces a clear inverted-U
in template length L: worsens to an interior maximum displacement, then RECOVERS to #1. HELD in
3 of 4 (frac,T_qterms) cells by the pre-registered CI test; 20/20 seeds in the strongest cell.
This is the regime DEAD-0011 (killed CLAIM-0044) lacked — the predicted crossover is PRESENT here.

## Setup (see PRE_REGISTRATION.md)
Reuses EXP-0043's verified standard BM25 (k1=1.2, b=0.75; IDF=ln((N-df+0.5)/(df+0.5)+1); hand-calc
<1e-9 + correct ranking re-logged in results/sanity.txt) and Zipf corpus builder. N=2000 short docs;
ONE clean answer doc carries ALL 5 query terms; ~30 distractors carry a random SUBSET. A shared
TEMPLATE = a block of T_qterms query terms repeated to length L, prepended to a fraction `frac` of
DISTRACTORS ONLY (answer never templated). Anti-circular: GT=clean-answer doc-id (generative); BM25
reads only token stats.

## CRUX: mean rank(clean answer) per cell across L (lower=better, 1=best; 20 seeds)

| frac | T_q | L=0 | 4 | 8 | 16 | 32 | 64 | 128 | 256 | 512 |
|------|-----|-----|---|---|----|----|----|-----|-----|-----|
| 0.5 | 1 | 1.10 | 1.80 | 1.80 | 1.80 | 1.30 | 1.05 | 1.05 | 1.00 | 1.00 |
| 0.5 | 2 | 1.10 | 2.50 | 3.15 | **3.70** | 3.70 | 2.55 | 1.70 | 1.25 | 1.00 |
| 1.0 | 1 | 1.10 | **2.30** | 2.30 | 2.20 | 1.50 | 1.10 | 1.00 | 1.00 | 1.00 |
| 1.0 | 2 | 1.10 | 3.90 | 4.70 | **5.20** | 4.95 | 4.10 | 1.85 | 1.20 | 1.00 |

(bold = interior peak). CI half-widths 0.0–1.2.

## Inverted-U test (pre-registered, rigorous)
HELD requires interior L* with r(L*)-CI > BOTH r(0)+CI and r(512)+CI.
- **f=0.5,T=2: HELD** (L*=16, r=3.70±1.02 > both ends).  18/20 seeds within-seed inverted-U.
- **f=1.0,T=1: HELD** (L*=4,  r=2.30±0.83 > both ends).  13/20 seeds.
- **f=1.0,T=2: HELD** (L*=16, r=5.20±1.21 > both ends).  **20/20 seeds.**
- f=0.5,T=1: non-monotone but interior peak NOT significant vs both ends (weakest condition: half-spread, one query term — only 9/20 seeds). Reported honestly; does not falsify the overall claim.

**→ INVERTED-U HELD** (>=1 cell with statistically clear recovery; 3 of 4 cells, monotone in
template strength: more query terms and/or wider spread => deeper, clearer inverted-U).

## Mechanism decomposition — DID the two forces cross over? YES.
Worked example f=1.0,T=2 (strongest cell):

| quantity | L=0 | 4 | 16 | 64 | 256 | 512 |
|----------|-----|---|----|----|-----|-----|
| **top-distractor score** | 25.8 | 30.9 | **32.9** | 30.9 | 25.4 | 22.8 |
| clean-answer score | 30.1 | 28.7 | 28.7 | 28.8 | 29.3 | 29.9 |
| **dist_lennorm** (templated distractors) | 1.00 | 1.06 | 1.24 | 1.93 | 4.51 | 7.56 |
| qterm_idf (mean IDF of template query terms) | 4.65 | 4.05 | 4.05 | 4.05 | 4.05 | 4.05 |

**The crossover is explicit:**
1. **Small L (rising arm):** the template injects query terms into distractors -> top-distractor
   score JUMPS 25.8 -> 32.9, OVERTAKING the (flat ~29) clean-answer score -> rank worsens.
2. **Large L (falling/recovery arm):** the template makes distractors LONG -> BM25
   length-normalization (dist_lennorm 1.0 -> 7.6) progressively CRUSHES the bloated distractors'
   scores back down (32.9 -> 22.8), dropping them BELOW the clean answer -> rank recovers to #1.
3. The two opposing forces (query-term injection raising distractor scores vs. length-norm
   crushing them) genuinely CROSS OVER at an interior L -> the inverted-U. This is exactly the
   crossover CLAIM-0044/DEAD-0011 posited but could not produce (there the boilerplate was on the
   ANSWER, was non-query / low-IDF, and only length-norm acted -> monotone).

**Honest mechanism nuance:** qterm_idf is flat ACROSS L>0 (once a distractor contains the query
term, its df is fixed regardless of how many times the template repeats it) — the same structural
fact EXP-0043 found. So within a fixed spread, the L-driven RECOVERY is carried by **length-norm
crushing the bloated distractors**, while the IDF-collapse arm acts via the SPREAD axis (qterm_idf
4.65->4.05 as frac 0.5->1.0 lowers the whole curve's baseline). Both forces are real and opposing;
the inverted-U is their net signature. The honest refinement vs the literal claim text: the
recovery's L-dependence is length-norm-dominated; IDF-collapse modulates depth via spread.

## Verdict
**HELD (inverted-U confirmed).** Effect: `support`. The shared-boilerplate -> clean-answer-rank
inverted-U + its (length-norm vs query-term-injection) crossover is a real, replicated,
non-closed-form BM25 corpus-hygiene phenomenon. Distinct from and complementary to DEAD-0011
(which established the monotone regime when boilerplate is non-query text on the answer doc).

## What a real L1 should measure
Real boilerplate-heavy corpus where DISTRACTOR docs share topical templates that mention query
terms (SEO/template-spam pages; SEC EDGAR boilerplate sections that quote the topic; Wikipedia
navboxes) + a real dense retriever (bge/e5) AND BM25 + a real QA set. Strip-vs-retain-vs-lengthen
the distractor templates; measure the CLEAN canonical answer doc's rank AND downstream RAG accuracy
vs measured template length and template-spread fraction. CONFIRM the inverted-U (and test whether a
dense retriever's softmax/cosine normalization reproduces or dampens the length-norm recovery arm,
since dense models lack BM25's explicit length penalty) -> implication: boilerplate-stripping
aggressiveness on COMPETITOR docs has a non-monotone payoff, and there is a measurable "danger zone"
of intermediate template length where the canonical answer is maximally crowded out.

## Prior-art caveat (precise)
'Collapse of Dense Retrievers' (2503.05037) = STATIC biases, not a non-monotone response to a
controllable preprocessing var. Doc-expansion-hurts (2604.05087, 2504.21015) adds DISTINCT text to
the TARGET doc; here the template is on COMPETITORS, is query-term-bearing, and the signature is a
non-monotone crossover. Set-compositional (2605.03824)/salient-phrase (2110.06918) = query semantics
(orthogonal). Novelty = the clean-answer-rank inverted-U under a query-term-bearing distractor
template + its length-norm/query-injection crossover.

## Paths
- PRE_REGISTRATION.md (committed before run, commit 0284080)
- clean_answer_invertedU.py  (imports EXP-0043's verified BM25 + corpus)
- results/sanity.txt   (BM25 unit-check, PASS)
- results/raw_results.csv  (720 rows: 20 seeds x 2 frac x 2 T_qterms x 9 L)
- results/summary.csv      (36 configs: mean rank, CI, qterm_idf, dist_lennorm, scores)
- logs/run.log
