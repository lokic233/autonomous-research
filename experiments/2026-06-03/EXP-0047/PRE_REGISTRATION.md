# PRE_REGISTRATION — EXP-0047 (CLAIM-0045) — Committee#1 L0 REMEDIATION

**Researcher:** researcher-0045 | **Level:** L0 (CPU-only, stdlib, SERIAL, <=12 min)
**Project:** PROJ-0015 | **Task:** TASK-0037 | **Committed BEFORE any run.**
Honest pipeline; a negative is a WIN. Trust on-disk CSVs, not stdout.

## CONTEXT
CLAIM-0045 (clean answer-doc BM25 rank traces an INVERTED-U as a query-term-bearing template
on the DISTRACTORS grows in length L) was voted HELD/YELLOW by committee#1. This is a TARGETED
one-shot remediation running FOUR committee-required cheap checks BEFORE any L1. We REUSE the
EXACT sim/corpus/grid from EXP-0044 (imports EXP-0043's verified BM25 + EXP-0044's corpus build),
so this is a clean controlled extension. Anti-circularity inherited: GT = planted-answer doc-id
(generative); BM25 reads token stats only, never reads GT.

## REUSED HARNESS (frozen)
- Corpus: EXP-0044's build_corpus(seed) — N=2000 short Zipf docs; ONE clean answer doc with ALL 5
  query terms; ~30 distractors with random SUBSETS; template = T_qterms query terms repeated to
  length L, prepended to a `frac` fraction of DISTRACTORS ONLY (answer never templated).
- Standard BM25 verified in EXP-0043 (k1=1.2, b=0.75; IDF=ln((N-df+0.5)/(df+0.5)+1)); hand-check <1e-9.
- >=20 seeds (seeds 0..19), same as EXP-0044.

## REMEDIATION 1 — b-SWEEP (decisive mechanistic test)
On the STRONGEST cell (frac=1.0, T_qterms=2), re-run the full L-sweep
L in {0,4,8,16,32,64,128,256,512} for BM25 b in {0, 0.25, 0.5, 0.75, 1.0}, k1=1.2 FIXED.
Mechanism claim: the recovery arm is LENGTH-NORM-dominated. With b=0 there is NO length
normalization (denom = f + k1), so the length-norm crushing of bloated distractors is ABOLISHED.
PREDICTION: b=0 MUST kill the recovery arm — rank should stay displaced / monotone-worsen, NOT
recover to #1. 
- If b=0 ABOLISHES recovery -> confirms length-norm is the necessary cause (honest scoping).
- If b=0 does NOT abolish recovery -> genuine surprise that ELEVATES novelty (length-norm is NOT
  the mechanism; something else drives recovery).
Report the pre-registered inverted-U test outcome PER b value, 20 seeds.

## REMEDIATION 2 — BM25L variant (Lv & Zhai, CIKM 2011, delta=0.5)
Implement BM25L. FORMULA USED (Lv & Zhai 2011, "When Documents Are Very Long, BM25 Fails!"):
  Let len-norm B(D) = (1 - b + b*|D|/avgdl), k1=1.2, b=0.75 (BM25 defaults), delta=0.5.
  c(t,D) = f(t,D) / B(D)                      # length-normalized tf (Lv-Zhai notation)
  score += IDF(t) * (k1+1)*(c + delta) / (k1 + c + delta)
  where IDF = ln((N - df + 0.5)/(df + 0.5))  [Lv-Zhai use the classic RSJ idf; we use the SAME
  non-negative add-1 idf as our BM25 baseline for a controlled comparison: ln((N-df+0.5)/(df+0.5)+1)].
The +delta term LOWER-BOUNDS the normalized tf so long docs are not over-penalized — the known fix
for exactly the length-penalty that may drive the recovery arm. We VERIFY against a hand-check
(delta=0 must reduce BM25L back toward standard BM25's tf-saturation shape on the sanity corpus;
and a long-doc case must show BM25L >= BM25 for a matching term). Hand-check transcript -> sanity.txt.
Run BM25L on the SAME grid as EXP-0044 (L x frac{0.5,1.0} x T_qterms{1,2}, 20 seeds).
DECISION RULE:
- If the inverted-U PERSISTS under BM25L (>=1 cell HELD by the pre-registered CI test) ->
  phenomenon is ROBUST to the known length-penalty fix -> recommend HELD-STRONG (fast-track L1).
- If it VANISHES under BM25L (no cell HELD; recovery flattened/monotone) -> phenomenon is a
  BM25-default(b>0)-specific over-penalization artifact -> recommend HELD-NARROW
  ("BM25-default-specific diagnostic", reduced novelty, still a valid L0 result).

## REMEDIATION 3 — SCORE-MARGIN metric
Alongside rank, for the STRONGEST cell (frac=1.0, T_qterms=2), report
  score_margin(L) = (clean answer BM25 score) - (top distractor score)
as a function of L (mean over seeds, with CI). Negative margin => answer displaced. Assesses
whether the rank displacement is LARGE (reranker-recoverable danger zone) or MARGINAL. Reported
for the standard BM25 (b=0.75) strongest cell.

## REMEDIATION 4 — CITATION FIX + CLAIM REWRITE (no run; in RESULTS.md)
(a) Correct the prior-art: REMOVE 2504.21015 (it is "Don't Retrieve, Generate" —
synthetic-training-data, NOT doc-expansion) and 2604.05087 (unverifiable/future-dated). Correct
frame: Singhal-Buckley-Mitra 1996 (pivoted length normalization — the exact mechanism behind the
recovery arm); Robertson & Walker SIGIR 1994 (BM25 length norm); Lv & Zhai CIKM 2011 (BM25L);
Zhong et al. EMNLP 2023 (corpus poisoning — same family, must distinguish); Doc2Query--
(Gospodinov et al. 2023, over-expansion-hurts on the TARGET doc).
(b) REWRITE the claim to DROP the dual-mechanism-via-L framing: recovery along L is
LENGTH-NORM-DOMINATED; IDF-collapse acts ONLY via the SPREAD (frac) axis, NOT via L (the old
"at large L the query-terms' df spreads so their IDF collapses" is CONTRADICTED by the flat
qterm_idf table — qterm_idf is flat ~4.05 across L>0). Corrected claim text -> RESULTS.md.

## PRE-REGISTERED INVERTED-U TEST (identical to EXP-0044)
Per (variant, cell): r(L)=mean rank, h(L)=95% CI half-width (t, df=19, t*=2.093).
INVERTED-U HELD iff EXISTS interior L* with:
  r(L*) - h(L*) > r(0) + h(0)   AND   r(L*) - h(L*) > r(Lmax) + h(Lmax)
Also report per-seed support (fraction of seeds with an interior rank worse than both ends).
MONOTONE / FLAT otherwise.

## OVERALL DECISION
- b-sweep tells us WHETHER length-norm is the necessary cause of recovery.
- BM25L tells us HELD-STRONG (inverted-U survives the known fix) vs HELD-NARROW
  (BM25-default-specific artifact).
- effect = `support` if inverted-U survives BM25L; `keep-exploring` if it narrows to
  BM25-default-specific; `kill` only if the b-sweep shows the whole effect was a bug.

## OUTPUTS
- results/bsweep.csv         (per seed x L x b: rank, scores, lennorm)  [strongest cell]
- results/bm25l_raw.csv      (per seed x L x frac x T_qterms: rank, scores)
- results/margin.csv         (per L: score_margin mean/CI)  [strongest cell, std BM25]
- results/sanity.txt         (BM25 + BM25L unit/hand checks)
- RESULTS.md
