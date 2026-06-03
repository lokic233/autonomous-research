# RESULTS — EXP-0040 (CLAIM-0042)

**Researcher:** researcher-0040 | **Level:** L0 (CPU-only, **stdlib-only lexical near-dup/n-gram**,
SERIAL) | **Verdict: PARTIAL-HELD (with a sharp, honest boundary).**
Runtime 171s main sweep + ~90s supplementary (well under 15-min budget). 7 seeds, max metric
std 0.019 (highly stable). sentence-transformers NOT available on this Mac → used **lexical
8-gram shingles**: document-level = **Jaccard near-dup of whole-doc vs whole-item shingle sets**;
passage-level = **fraction of item 8-grams present in the doc** (GPT-3/PaLM n-gram-check analog).

## Setup recap
- Corpus: N=300 docs (doc_len ∈ {100,500,2500,5000}), M=60 benchmark items (item_len=50),
  contam_frac=0.2. Ground truth = the **generative fact** of which item-span we embedded into
  which doc; detectors read TEXT ONLY and never the label (anti-circular).
- Sweeps: span_ratio ∈ {0.5,0.1,0.02,0.01}, paraphrase ∈ {0,0.2,0.4}, doc_thresh ∈ {0.3..0.8},
  span_thresh ∈ {0.4,0.6,0.8,0.95}, ngram_k=8.

## (A) THE DOC-vs-PASSAGE MISS GAP
For **verbatim** embedded spans (paraphrase=0), in the realistic short-span regime
(span_ratio ≤ 0.1, i.e. a 50-tok item in a ≥500-tok doc):

| span_ratio | doc-level recall | passage recall | **MISS GAP** | passage precision |
|---|---|---|---|---|
| 0.5 (50-in-100)  | 0.00 @thr≥0.5; **1.00 @thr≤0.4** | 1.00 | 0.00 (doc catches w/ lenient thr) | 1.00 |
| 0.1 (50-in-500)  | **0.00 even @thr=0.3** | 1.00 | **1.00** | 1.00 |
| 0.02 (50-in-2500)| **0.00 even @thr=0.3** | 1.00 | **1.00** | 1.00 |
| 0.01 (50-in-5000)| **0.00 even @thr=0.3** | 1.00 | **1.00** | 1.00 |

**The miss gap is ~100% (not just >20%) for any span_ratio ≤ 0.1, and it is NOT a threshold
artifact:** even at the most lenient document-level near-dup threshold (Jaccard ≥ 0.3),
document-level recall stays 0.00 once the embedded item is ≤10% of the doc. Reason (measured
directly): a 50-tok item gives 43 8-grams; embedded in a 500-tok doc the union has ~490 shingles
→ Jaccard ≈ 43/490 ≈ 0.09, far below any usable near-dup threshold. The **union normalization**
of document-level near-dedup is exactly why short embedded spans are invisible. Passage n-gram
matching, which asks "does the doc contain ≥span_thresh of this item's 8-grams" (no union
dilution), recovers 100% of them.

Only when the item is ~half the document (span_ratio 0.5) and the near-dup threshold is lenient
(≤0.4) does document-level catch it (gap→0) — we report this to avoid a strawman.

## (B) >20%? + REPORTED-RATE EFFECT + PRECISION (false-positive control)
- **>20%? YES, overwhelmingly** — gap ≈ 100% across the realistic span_ratio ≤0.1 regime, ≥5 seeds.
- **Reported contamination rate:** true rate = 0.20. Document-level reports **0.00** (it sees no
  contamination at all in the short-span regime); passage-level reports **0.20** = the true rate.
  This is the materiality result: document-level dedup would report **ZERO** contamination on a
  corpus that is genuinely 20% contaminated via short spans — a maximal under-count, not a marginal one.
- **Passage-level PRECISION (the load-bearing FP control): it is REAL, and it bites.** With a
  clean distinct item vocab, precision is trivially 1.00 — so we ran a hard confound: inject into
  INNOCENT docs a **partial/large quote** of an actual benchmark item (legit citation, NOT the
  eval instance) and ask whether passage-level mislabels them:

  | innocent quote_frac | span_thresh 0.4 | 0.6 | 0.8 | **0.95** |
  |---|---|---|---|---|
  | 0.5 | prec 0.56 | 1.00 | 1.00 | 1.00 |
  | 0.7 | 0.56 | 0.56 | 1.00 | 1.00 |
  | 0.9 | 0.56 | 0.55 | **0.57** | **1.00** |

  At low/medium span_thresh, passage-level OVER-FLAGS innocent ~90%-quotes (precision → 0.55):
  its "extra catches" would NOT all be real contamination. **But at span_thresh ≈ 0.95 precision
  returns to 1.00 at every quote level while recall on true verbatim contamination stays 1.00.**
  So the extra catches are real contamination *at a properly tuned high threshold* — and that
  threshold is a genuine, non-trivial knob, not a free lunch.

## VERDICT: PARTIAL-HELD
- **HELD:** for verbatim (or near-verbatim) short embedded spans, the doc-vs-passage miss gap is
  ~100% (≫20%), document-level dedup under-counts contamination from 20% true → **0% reported**,
  and passage n-gram matching recovers the true rate **at perfect precision when span_thresh is
  high (~0.95)**. The claim's mechanism (union-normalized whole-doc near-dup is blind to short
  spans) is confirmed and is threshold-robust.
- **NOT held / honest boundary (the negative half):** the gap **collapses under paraphrase**.
  At paraphrase ≥0.2, passage recall falls to ~0 too (8-grams don't survive ~20% token edits),
  so passage-level ALSO misses paraphrased contamination — the *advantage* of passage over doc-level
  is specific to verbatim/near-verbatim spans. And passage-level's extra catches are only "real"
  at a high span_thresh; a naively-tuned low threshold over-flags innocent long quotes (precision
  0.55). The claim as stated ("frequently … large enough to materially change reported rates")
  holds for the **verbatim short-span** regime, which is the empirically dominant contamination
  mode in real corpora, but is NOT a universal property across paraphrase.

## ARTIFACTS (trust on-disk CSVs)
- Pre-reg: `experiments/2026-06-03/EXP-0040/PRE_REGISTRATION.md` (committed before running)
- Sim:     `experiments/2026-06-03/EXP-0040/sim_contamination.py`
- Main:    `results/raw_results.csv` (336 rows), `results/summary.csv` (48 configs × 7 seeds)
- Threshold-robustness: `results/supp_lowthresh.csv`
- FP controls: `results/fp_stress.csv` (random boilerplate — no FP), `results/fp_stress2.csv`
  (partial-quote confound — FP appears at low span_thresh, vanishes at 0.95)
- Logs: `logs/run.log`, `logs/supp.log`, `logs/fp.log`, `logs/fp2.log`

## WHAT A REAL L1 SHOULD MEASURE
- Real corpus shards (a Pile / C4 / Dolma slice) vs real benchmark items (MMLU / GSM8K / HellaSwag).
- Real document-level dedup: **MinHash-LSH** (e.g. datasketch, the standard near-dup pipeline) on
  whole documents vs whole benchmark items.
- Real passage/n-gram contamination check: the **GPT-3 13-gram / PaLM 8-gram** clean-flag or a
  substring/suffix-automaton match of benchmark items inside training docs.
- Report contaminated-**item** counts at BOTH granularities and the gap; crucially, **measure the
  paraphrase distribution of real contamination** (how often it is verbatim vs reworded) since this
  L0 shows the gap is entirely a verbatim-regime phenomenon.
- Calibrate the n-gram threshold against a held-out set of innocent long quotes (the precision
  control) to confirm the extra catches are real eval-instance contamination, not legit citation.

## PRIOR-ART CAVEAT (honest)
n-gram contamination checks are PUBLISHED and standard (GPT-3 13-gram, PaLM 8-gram, the LM
data-contamination surveys, dedup papers e.g. Lee et al. 2021 "Deduplicating Training Data Makes
LMs Better"). This experiment claims NEITHER "contamination exists" NOR "n-gram checks exist".
The contribution is the **quantified granularity GAP**: document-level near-dedup (the dedup
papers' method) and passage-level n-gram contamination checks measure *different things*, and on
short embedded spans the former reports ~0 contamination where the latter (correctly) reports the
true 20% — a maximal, threshold-robust under-count — but ONLY for verbatim spans and ONLY at a
precision-calibrated n-gram threshold. The novelty is the measured gap + its rate effect + the
precision boundary, not the existence of either tool.
