# RESULTS — EXP-0047 (CLAIM-0045) — Committee#1 L0 REMEDIATION

**Researcher:** researcher-0045 | **L0** (CPU, stdlib, SERIAL, ~23s wall) | 20 seeds, N=2000 docs.
Reuses EXP-0043's verified BM25 (hand-check <1e-9) + EXP-0044's exact corpus/template. Anti-circular
inherited: GT = planted-answer doc-id; scorers read token stats only. Sanity (incl. BM25L hand-check)
PASS — results/sanity.txt.

**HEADLINE: HELD-STRONG.** (1) The b-sweep PROVES the recovery arm is length-normalization-driven:
b=0 (no length norm) ABOLISHES recovery (monotone worsening 1.10->14.30, 0/20 seeds). (2) The
inverted-U PERSISTS under BM25L (Lv & Zhai 2011, the known length-penalty fix): strongest cell
20/20 seeds, 3 of 4 cells HELD — same as default BM25. => robust to the standard fix, not a
default-b artifact. (3) Displacement is SUBSTANTIAL (margin swings +4.4 -> -4.2 -> +7.1).

## REMEDIATION 1 — b-SWEEP (decisive mechanistic test; strongest cell f=1.0, T_qterms=2, k1=1.2)
mean rank(clean answer) over 20 seeds (lower=better; 1=best):

| b | L=0 | 4 | 8 | 16 | 32 | 64 | 128 | 256 | 512 | inverted-U | per-seed |
|---|-----|---|---|----|----|----|-----|-----|-----|-----------|----------|
| **0.00** | 1.10 | 4.05 | 5.45 | 7.65 | 10.60 | 11.50 | 13.00 | 13.80 | **14.30** | **NOT held (MONOTONE)** | 0/20 |
| 0.25 | 1.10 | 3.95 | 5.10 | 6.90 | 7.45 | 7.05 | 6.65 | 4.10 | 1.85 | HELD L*=32 | 20/20 |
| 0.50 | 1.10 | 3.90 | 4.80 | 6.25 | 6.65 | 5.25 | 3.05 | 1.70 | 1.10 | HELD L*=32 | 20/20 |
| 0.75 | 1.10 | 3.90 | 4.70 | 5.20 | 4.95 | 4.10 | 1.85 | 1.20 | 1.00 | HELD L*=16 | 20/20 |
| 1.00 | 1.10 | 3.70 | 4.10 | 4.70 | 4.10 | 2.90 | 1.30 | 1.00 | 1.00 | HELD L*=16 | 20/20 |

**Did b=0 abolish recovery? YES — DECISIVELY.** With b=0 the BM25 denominator is `f + k1`
(no `|D|/avgdl` term), so bloating the distractors adds no length penalty: their injected query-term
score never gets crushed and the clean answer NEVER recovers — rank climbs monotonically to 14.30 at
L=512 (0/20 inverted-U). The instant b>0 (b=0.25) the recovery arm reappears and 20/20 seeds show the
inverted-U; recovery sharpens monotonically with b (peak displacement shrinks 7.45@b.25 -> 4.70@b1.0,
recovery to L=512 deepens 1.85 -> 1.00). **=> length normalization is the NECESSARY cause of the
recovery arm — the stated mechanism is confirmed (honest scoping, not a surprise).**

## REMEDIATION 2 — BM25L (Lv & Zhai, CIKM 2011, delta=0.5) on the EXP-0044 grid
**Formula used (verified by hand, sanity.txt):** with B(D)=(1-b+b|D|/avgdl), k1=1.2, b=0.75, delta=0.5,
c = f/B(D); `score += IDF(t) * (k1+1)*(c+delta)/(k1 + c + delta)`. IDF = same non-negative add-1
RSJ idf as baseline (ln((N-df+0.5)/(df+0.5)+1)) for a controlled comparison. The +delta term
lower-bounds normalized tf so long docs are not over-penalized. Hand-check: BM25L(delta=0.5) on a
len-200 f=1 doc = 0.0891 >= BM25 = 0.0053 (PASS — BM25L does NOT over-penalize the long doc).

mean rank(clean answer), 20 seeds:

| frac | T_q | L=0 | 4 | 8 | 16 | 32 | 64 | 128 | 256 | 512 | inverted-U | per-seed |
|------|-----|-----|---|---|----|----|----|-----|-----|-----|-----------|----------|
| 0.5 | 1 | 1.10 | 1.80 | 1.80 | 1.80 | 1.30 | 1.20 | 1.05 | 1.05 | 1.00 | NOT held (weak) | 9/20 |
| 0.5 | 2 | 1.10 | 2.50 | 3.05 | 3.05 | 3.10 | 3.05 | 2.05 | 1.60 | 1.25 | HELD L*=32 | 18/20 |
| 1.0 | 1 | 1.10 | 2.20 | 2.30 | 2.20 | 1.50 | 1.25 | 1.10 | 1.00 | 1.00 | HELD L*=8 | 13/20 |
| 1.0 | 2 | 1.10 | 3.85 | 4.70 | 4.75 | 4.75 | 4.45 | 2.90 | 1.45 | 1.25 | **HELD L*=16** | **20/20** |

**Inverted-U PERSISTS under BM25L** — 3 of 4 cells HELD by the pre-registered CI test, strongest cell
20/20 seeds, same pattern as default BM25 in EXP-0044 (the lone non-held cell f=0.5,T=1 is the identical
weakest cell that was also non-held under default BM25). BM25L softens the recovery slightly (peak L=512
rank 1.25 vs 1.00 under default — the +delta floor partly protects long distractors) but does NOT
flatten the inverted-U. **=> the phenomenon is ROBUST to the known length-penalty fix (BM25L).**
**DECISION: HELD-STRONG (fast-track L1).** It is NOT a BM25-default(b=0.75)-specific over-penalization
artifact — it survives the variant specifically designed to fix long-doc over-penalization.

## REMEDIATION 3 — SCORE-MARGIN(L) = answer_score - top_distractor_score (b=0.75 strongest cell)

| L | 0 | 4 | 8 | 16 | 32 | 64 | 128 | 256 | 512 |
|---|---|---|---|----|----|----|-----|-----|-----|
| margin | +4.36 | -2.25 | -3.63 | **-4.22** | -3.74 | -2.08 | +0.63 | +3.89 | +7.08 |
| ±95%CI | 0.96 | 0.83 | 0.84 | 0.85 | 0.85 | 0.85 | 0.85 | 0.85 | 0.85 |

The displacement is **SUBSTANTIAL, not marginal**: the margin swings from +4.36 (answer dominant,
L=0) to **-4.22** at the L=16 peak (answer clearly behind the top distractor, CI excludes 0 by ~5
half-widths) and recovers to +7.08 at L=512. A -4.2 BM25-score deficit at the danger zone is a
genuine (not knife-edge) displacement — the answer is robustly crowded below competitors at
intermediate L, so the rank loss is real and would propagate to a downstream reranker's candidate
set, not a tie that any reranker trivially fixes.

## REMEDIATION 4 — CITATION FIX + CLAIM REWRITE

### Corrected prior-art (replaces the prior claim's citations)
- **REMOVE** 2504.21015 — it is "Don't Retrieve, Generate" (synthetic training-data generation),
  NOT document-expansion. Mis-cited.
- **REMOVE** 2604.05087 — unverifiable / future-dated. Dropped.
- **Singhal, Buckley & Mitra, SIGIR 1996 — "Pivoted Document Length Normalization."** The EXACT
  mechanism behind the recovery arm: as competitor docs grow long, length normalization pivots
  their scores down. Our b-sweep is a direct instantiation (b is the pivot slope; b=0 => no pivot
  => no recovery).
- **Robertson & Walker, SIGIR 1994 — Okapi BM25 length normalization.** Origin of the (1-b+b|D|/avgdl)
  term whose b>0 is shown here to be necessary and sufficient for the recovery arm.
- **Lv & Zhai, CIKM 2011 — BM25L.** The known long-doc over-penalization fix; we show the inverted-U
  SURVIVES it (Remediation 2) => not a length-over-penalization artifact.
- **Zhong et al., EMNLP 2023 — corpus poisoning for dense retrieval.** Same FAMILY (adversarial
  manipulation of competitor docs), MUST DISTINGUISH: they inject crafted passages to be retrieved
  for a query; we use benign topical templates on competitors and the signature is a NON-MONOTONE
  displacement of a CLEAN canonical answer governed by a controllable preprocessing length L.
- **Gospodinov et al., 2023 — Doc2Query-- (over-expansion hurts).** Over-expansion degrades the
  TARGET doc; here expansion is on COMPETITORS and the effect on the clean answer is non-monotone.

### Corrected claim text (drops the dual-mechanism-via-L framing)
> Under BM25 with length normalization (b>0), when DISTRACTOR documents carry a shared topical
> template containing some of the query's terms while the genuine canonical answer doc stays CLEAN,
> the clean answer's rank degrades NON-MONOTONICALLY (inverted-U) as template length L grows: an
> intermediate L maximally displaces the answer, after which further growth RECOVERS its rank toward
> #1. The recovery along the L axis is **LENGTH-NORMALIZATION-DOMINATED** — at small L the template
> injects query terms into distractors (raising their scores above the clean answer), and at large L
> BM25 length normalization progressively crushes the bloated distractors' scores back below the
> clean answer. The recovery arm REQUIRES b>0 (with b=0 it is abolished and rank worsens monotonically).
> The IDF/spread effect acts ONLY via the SPREAD (frac) axis — widening the fraction of templated
> distractors lowers the whole curve's baseline (qterm_idf 4.65->4.05) — and NOT via L: qterm_idf is
> FLAT (~4.05) across all L>0 because a distractor's df for a query term is fixed once it contains the
> term, regardless of repetition count. The phenomenon is robust to the BM25L long-doc over-penalization
> fix (inverted-U persists), so it is a property of length-normalized lexical retrieval, not a
> default-b over-penalization artifact. Corpus-statistics-dependent crossover; no closed-form predictor.

(Correction vs old text: the old "at large L the query-terms' df spreads so their IDF collapses" is
CONTRADICTED by the flat qterm_idf table — IDF-collapse is a SPREAD-axis effect, not an L-axis effect.
Recovery along L is purely length-norm.)

## VERDICT
**HELD-STRONG.** Effect: `support`. The clean-answer inverted-U is (i) mechanistically pinned to
length normalization (b=0 abolishes it; recovery sharpens monotonically with b), (ii) robust to the
known length-penalty fix BM25L (persists, 20/20 strongest cell), and (iii) a substantial (not
marginal) displacement (peak margin -4.2). Recommend fast-track to L1.

## What L1 should now measure (given the scoping result)
Because the mechanism is confirmed length-norm and robust to BM25L, L1 should test EXTERNAL/ECOLOGICAL
validity, not re-litigate the mechanism:
1. Real corpus where DISTRACTOR docs share topical templates mentioning query terms (SEO/template-spam
   pages; SEC EDGAR boilerplate quoting the topic; Wikipedia navboxes) + a real QA answer set.
   Strip-vs-retain-vs-lengthen the COMPETITOR templates; measure the CLEAN canonical answer's rank and
   downstream RAG accuracy vs measured template length L and spread fraction. Confirm the danger zone.
2. **Critical dense-retriever test:** dense models (bge/e5) lack BM25's explicit length penalty (they
   use cosine/softmax norm). PREDICTION from this L0: the recovery ARM should be DAMPENED or ABSENT
   under dense retrieval (no b>0 length crush) -> displacement would stay monotone-worse, a sharper
   corpus-hygiene risk for dense RAG. This is the highest-value L1 measurement.
3. Quantify the operational implication: boilerplate-stripping aggressiveness on COMPETITOR docs has a
   non-monotone payoff under BM25, with a measurable intermediate-L danger zone where the canonical
   answer is maximally crowded out — and (per #2) possibly a MONOTONE risk under dense retrieval.

## Paths
- PRE_REGISTRATION.md (committed before run, commit 8dd906e)
- remediation.py  (imports EXP-0043's verified BM25 + EXP-0044's corpus/template; parameterized b + BM25L)
- results/sanity.txt   (BM25 unit-check + b-param + b=0 len-independence + BM25L hand-check, all PASS)
- results/bsweep.csv   (900 rows: 20 seeds x 5 b x 9 L; strongest cell)
- results/bm25l_raw.csv (720 rows: 20 seeds x 2 frac x 2 T_qterms x 9 L)
- logs/run.log
