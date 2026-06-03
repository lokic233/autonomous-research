# COMMITTEE#2 (FINAL) — CLAIM-0045 (PROJ-0015) — two-pass complete, L0+GPU-L1 in hand
## This is the FINAL verdict (green/yellow/red). The L1 ecological-validity test is the load-bearing new fact. Vote HONESTLY by role. Do NOT green a claim whose general reading FAILED at L1.

## TWO-PASS TRAIL:
L0 (EXP-0044) -> committee#1 YELLOW (VERDICT-0043) with a cheap mandatory gate (b-sweep + BM25L) -> remediation EXP-0047 returned HELD-STRONG -> GPU L1 EXP-0048 (committee#1's own decision rule fast-tracked it) -> THIS committee#2.

## L0 RESULT (HELD-STRONG, EXP-0044 + remediation EXP-0047):
Under BM25 (b>0), a query-term-bearing topical template on DISTRACTOR docs (clean canonical answer stays CLEAN) makes the clean answer's rank trace an INVERTED-U in template length L (worsens to interior peak, recovers to #1). REMEDIATION CONFIRMED: b=0 ABOLISHES the recovery arm (monotone, 0/20) => length-normalization is the necessary cause; BM25L (Lv-Zhai 2011, delta=0.5) PERSISTS the inverted-U (3/4 cells, 20/20 strongest) => robust to the known length-penalty fix, NOT a default-b artifact; score-margin -4.22 at the danger zone (substantial). Mechanism: query-term injection lifts distractors above the clean answer at small L; length-norm crushes the bloated distractors back below it at large L.

## GPU L1 RESULT (EXP-0048, H100, dense bge-base-en-v1.5 + e5-base-v2, 20-seed grid + 15-seed stress probe) — THE LOAD-BEARING NEW FACT:
REALISTIC query-bearing templates: the inverted-U does NOT TRANSFER. Clean answer holds rank 1.00 (CI +-0.00) at EVERY L for BOTH models = FLAT. Interior-peak test NOT triggered. Score-margin dips slightly (bge +0.234->+0.138@L16->+0.226; e5 +0.098->+0.065@L16->+0.101) then recovers, NEVER negative.
Only an ADVERSARIAL verbatim-query injection into every distractor (an ATTACK, not corpus-hygiene drift) displaces the clean answer, and then MODEL-DEPENDENTLY: bge -> MONOTONE-WORSE (rank 1->101 @ndist=100, no recovery — confirms the L0 'more vulnerable, no recovery' prediction); e5 -> PARTIAL INVERTED-U (1->13.5@L64->1.00 — recovery EXISTS in a dense model, via a DIFFERENT mechanism: 512-token truncation / mean-pool dilution, NOT BM25 length-norm).
BOTTOM LINE (researcher's honest synthesis): CLAIM-0045 is a BM25-SPECIFIC LEXICAL ARTIFACT that does NOT threaten dense RAG under normal corpus hygiene. The general reading (a corpus-hygiene risk for retrieval broadly) FAILED ecological validity. The surviving result is BM25-only.

## THE VERDICT QUESTION (decide by role): is the SCOPED finding green-worthy, yellow, or red?
- GREEN would require: a genuinely novel, robust, ecologically-valid contribution. The general claim FAILED at L1 (dense=flat under realistic templates). The surviving BM25-only inverted-U is real + mechanistically clean (b-sweep + BM25L) but NARROW and the recovery arm is essentially pivoted-length-normalization (Singhal-Buckley-Mitra 1996) made visible via competitor templating.
- YELLOW: real, mechanistically-sound, honestly-scoped BM25-specific phenomenon + the L1 dense-divergence (bge monotone vs e5 inverted-U) is itself interesting, but it's an ATTACK finding not hygiene, and the hygiene-relevant realistic result is FLAT.
- RED: the interesting general claim died at L1; the BM25-only survivor restates pivoted-length-norm + the displacement requires query-term-stuffing (adversarial), so the corpus-hygiene framing is unsupported.
Judge novelty vs: Singhal-Buckley-Mitra 1996 (pivoted length norm = the recovery mechanism), Robertson-Walker 1994, Lv-Zhai 2011 (BM25L), Zhong 2023 corpus-poisoning (the adversarial-injection regime IS their family — distinguish honestly), Gospodinov 2023 Doc2Query--.

## CLAIM (current corrected text)
claim: 'Under BM25 with length normalization (b>0), when DISTRACTOR documents carry
  a shared topical template containing some of the query''s terms while the genuine
  canonical answer doc stays CLEAN, the clean answer''s rank degrades NON-MONOTONICALLY
  (inverted-U) as template length L grows: an intermediate L maximally displaces the
  answer, after which further growth RECOVERS its rank toward #1. The recovery along
  the L axis is LENGTH-NORMALIZATION-DOMINATED (at small L the template injects query
  terms into distractors raising their scores above the clean answer; at large L BM25
  length normalization progressively crushes the bloated distractors'' scores back
  below the clean answer; recovery REQUIRES b>0 and is abolished at b=0 where rank
  worsens monotonically). The IDF/spread effect acts ONLY via the SPREAD (frac) axis
  (widening the fraction of templated distractors lowers the curve baseline, qterm_idf
  4.65->4.05) and NOT via L (qterm_idf is FLAT ~4.05 across all L>0 because a distractor''s
  df for a query term is fixed once present, regardless of repetition). The phenomenon
  PERSISTS under the BM25L long-doc over-penalization fix, so it is a property of
  length-normalized lexical retrieval, NOT a default-b over-penalization artifact.
  Corpus-statistics-dependent crossover; no closed-form predictor.'
why_it_matters: 'DISTINCT successor to killed CLAIM-0044/DEAD-0011 in the revival-condition

## L0 RESULTS (EXP-0044)
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

## L0 REMEDIATION (EXP-0047 — b-sweep + BM25L)
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

## NOTE: L1 RESULTS.md lives on devgpu014 ~/ros-EXP-0048/RESULTS.md (no Mac mount). Key numbers are summarized above + in the queue submission. raw_results.csv = 1280 rows on devgpu014.

## ORCHESTRATOR POSTURE: I am NOT pushing for a green. The L1 negative is honest and important. If the committee judges the scoped BM25-only finding is a legitimate publishable negative-ish/scoped result -> YELLOW (accept + converge, it's a real finding). If the surviving result is too narrow / restates pivoted-length-norm / the hygiene framing is unsupported -> RED. GREEN only if a reviewer genuinely defends a novel robust contribution. Lightweight: either way PROJ-0015 converges after this (CLAIM-0044 dead, CLAIM-0045 terminal). Real 6/6 by role.
