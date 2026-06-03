# PRE_REGISTRATION — EXP-0047 (CLAIM-0045 committee#1 L0 REMEDIATION)

**Researcher:** researcher-0045 | **Level:** L0 (CPU-only, stdlib, SERIAL, <=12 min)
**Project:** PROJ-0015 | **Predecessor:** EXP-0044 (HELD/YELLOW by committee#1; VERDICT-0043)
**Committed BEFORE any run.** Honest pipeline; a negative is a WIN. Trust on-disk CSVs, not stdout.
Reuses EXP-0044's EXACT verified BM25 + Zipf corpus + grid (imports EXP-0043 boilerplate_bm25.py).
Anti-circularity INHERITED from EXP-0044: GT = planted-answer doc-id (generative); BM25 reads only
token stats; outcome mapping (is-this-the-answer) used ONLY at evaluation time.

## PURPOSE
Committee#1 required FOUR cheap remediations BEFORE any L1. This is a ONE-SHOT decisive experiment
(not a seeder loop). Goal: a clear scoping verdict on whether the EXP-0044 inverted-U is a robust
phenomenon (HELD-STRONG, fast-track L1) or a BM25-default-(b>0)-specific over-penalization artifact
(HELD-NARROW, scoped honestly). Both outcomes are valid L0 results.

## REMEDIATION 1 — b-SWEEP (decisive mechanistic test)
On the STRONGEST cell only (frac=1.0, T_qterms=2), re-run the full L-sweep with BM25 length-norm
parameter **b in {0, 0.25, 0.5, 0.75, 1.0}, k1=1.2 FIXED**. L in {0,4,8,16,32,64,128,256,512}, >=20 seeds.
- STATED MECHANISM: the recovery arm (large-L rank returning to #1) is LENGTH-NORM-dominated.
- PREDICTION: **b=0 (NO length normalization) MUST ABOLISH the recovery arm** — with b=0 the long
  templated distractors are NOT length-penalized, so once their score is raised by the injected
  query terms it should STAY raised; rank should NOT recover (expected monotone-worsen or plateau,
  no interior inverted-U).
- DECISION:
  - b=0 KILLS recovery (no significant inverted-U at b=0) -> CONFIRMS length-norm is the necessary
    cause of the recovery arm. Honest scoping. As b increases from 0 -> 0.75, the inverted-U should
    progressively APPEAR/deepen.
  - b=0 does NOT kill recovery -> genuine SURPRISE that ELEVATES novelty (something other than the
    BM25 length penalty drives recovery). Report and flag for L1.
- Report the pre-registered inverted-U test outcome PER b value (same test as EXP-0044, below).

## REMEDIATION 2 — BM25L variant (Lv & Zhai, CIKM 2011, delta=0.5)
Implement BM25L, the known fix that LOWER-BOUNDS the TF normalization to prevent over-penalization
of long documents — i.e. exactly the length penalty that may drive the recovery arm.
**FORMULA (Lv & Zhai 2011):**
  Let c(t,D) = raw term freq; |D| = doc len; avgdl = mean doc len.
  ctd' = c(t,D) / (1 - b + b*|D|/avgdl)        # the standard length-normalized tf (b=0.75)
  score_BM25L = sum_t IDF_L(t) * ( (k1+1) * (ctd' + delta) ) / ( k1 + ctd' + delta )
  where delta = 0.5, k1 = 1.2, b = 0.75, and
  IDF_L(t) = ln( (N + 1) / (df + 0.5) )         # Lv&Zhai's IDF (long-doc-robust variant)
The +delta shift on the *normalized* tf lower-bounds the contribution of a term in a long doc,
preventing BM25's over-penalization of long docs. VERIFY against an independent hand-check
(logged to results/sanity_bm25l.txt) before the sweep.
- Run BM25L on the SAME grid as EXP-0044 (L x frac{0.5,1.0} x T_qterms{1,2}, >=20 seeds).
- DECISION (HELD-STRONG vs HELD-NARROW):
  - inverted-U PERSISTS under BM25L (>=1 cell HELD by the pre-registered CI test) -> phenomenon is
    ROBUST to the known length-penalty fix -> recommend **HELD-STRONG (fast-track L1)**.
  - inverted-U VANISHES under BM25L (no cell HELD) -> phenomenon is a BM25-default(b>0)-specific
    over-penalization artifact -> recommend **HELD-NARROW** (scope honestly as a
    "BM25-default-specific corpus-hygiene diagnostic"; reduced novelty; still a valid L0 result).

## REMEDIATION 3 — SCORE-MARGIN metric
Alongside rank, report SCORE MARGIN(L) = (clean-answer BM25 score) - (top-distractor score) as a
function of L for the STRONGEST cell (frac=1.0, T_qterms=2), default BM25 (b=0.75).
- margin > 0 => answer is #1; margin < 0 => answer displaced. |margin| at the displacement peak
  measures whether the displacement is SUBSTANTIAL (large negative margin, hard for a reranker to
  recover) or MARGINAL (near-zero crossing, trivially reranker-recoverable). Report mean +/- 95% CI.

## REMEDIATION 4 — CITATION FIX + CLAIM REWRITE
Delivered in RESULTS.md (orchestrator updates the YAML). (a) Remove WRONG cites 2504.21015
("Don't Retrieve, Generate" — synthetic training data, NOT doc-expansion) and 2604.05087
(unverifiable/future-dated). Correct prior-art frame: Singhal-Buckley-Mitra SIGIR 1996 (pivoted
length normalization — the EXACT mechanism behind the recovery arm), Robertson & Walker SIGIR 1994
(BM25 / 2-Poisson length norm), Lv & Zhai CIKM 2011 (BM25L), Zhong et al. EMNLP 2023 (corpus
poisoning — same family, must distinguish), Gospodinov et al. 2023 (Doc2Query--, over-expansion
hurts on the TARGET doc). (b) DROP the dual-mechanism framing: recovery along L is
LENGTH-NORM-DOMINATED; IDF-collapse acts ONLY via the SPREAD (frac) axis, NOT via L (the old text
"at large L the query-terms' df spreads so their IDF collapses" is CONTRADICTED by the flat
qterm_idf table — qterm_idf ~4.05 flat across all L>0).

## PRE-REGISTERED INVERTED-U TEST (identical to EXP-0044; df=19, t*=2.093 for 20 seeds)
Per (cell, b/variant): r(L)=mean rank, h(L)=95% CI half-width.
INVERTED-U HELD iff EXISTS interior L* with:
   r(L*) - h(L*) > r(0) + h(0)   AND   r(L*) - h(L*) > r(Lmax) + h(Lmax)
(interior peak's CI excludes BOTH endpoint means). Also report per-seed support fraction.
MONOTONE / FLAT otherwise (= recovery abolished, for the b-sweep purpose).

## SEEDS / BUDGET
>=20 seeds (SEEDS = range(20)). b-sweep: 5 b x 9 L x 20 seeds = 900 ranks (1 cell). BM25L: 9 L x
2 frac x 2 T_qterms x 20 seeds = 720 ranks. Margin: reuse b=0.75 strongest-cell rows. SERIAL,
stdlib, CPU. Expected <~60s (EXP-0044 did 720 in ~10s); <=12 min budget.

## DECISION RULE SUMMARY
- effect=`support` if inverted-U SURVIVES BM25L (HELD-STRONG).
- effect=`keep-exploring` if it NARROWS to BM25-default-specific (vanishes under BM25L; HELD-NARROW).
- effect=`kill` ONLY if the b-sweep reveals the whole EXP-0044 effect was a bug/artifact
  (e.g. inverted-U present even at b=0 in a way that implicates a harness error, not length-norm).

## OUTPUTS
- results/bsweep_raw.csv, results/bsweep_summary.csv
- results/bm25l_raw.csv, results/bm25l_summary.csv
- results/margin_strongest.csv
- results/sanity_bm25l.txt (BM25L hand-check, PASS)
- RESULTS.md
