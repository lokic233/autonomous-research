# PRE_REGISTRATION — EXP-0040 (CLAIM-0042)

**Researcher:** researcher-0040 | **Level:** L0 (CPU-only, stdlib, serial, <=15 min)
**Project:** PROJ-0013 | **Task:** TASK-0032
**Committed BEFORE any run.** Honest pipeline; negatives are WINS.

## THE CLAIM (CLAIM-0042)
Document-level near-dedup of training corpora systematically UNDER-COUNTS eval-benchmark
contamination, because benchmark items frequently appear as SHORT embedded spans inside
training documents that are NOT document-level near-duplicates of the benchmark — so a
non-trivial fraction (>20%) of true passage-level benchmark contamination is INVISIBLE to
document-level dedup but caught by passage/n-gram-level span matching, AND this gap is large
enough to materially change reported contamination rates.

## FALSIFIABLE PARTS
- (A) What fraction of TRUE passage-level benchmark contamination is INVISIBLE to
  document-level near-dedup but caught by passage/n-gram span matching? (the MISS GAP)
- (B) Is that gap >20% AND large enough to materially change reported contamination rates,
  AT ACCEPTABLE passage-level PRECISION (extra catches are REAL contamination, not innocent
  n-gram overlap false positives)?

## CORPUS MODEL (a generative fact we control)
- N training documents, each a long doc of doc_len tokens drawn from a shared vocabulary
  (Zipf-ish), with COMMON PHRASES injected at a controlled rate to create realistic innocent
  n-gram overlap between unrelated docs (so passage-level FP is real, not zero by construction).
- A benchmark of M items, each item_len tokens (question/answer/passage), drawn from a
  DISTINCT vocabulary slice so an item is not naturally similar to a doc.
- CONTAMINATION (ground truth): for a fraction contam_frac of docs, we EMBED one benchmark
  item as a SHORT contiguous span inside the doc (optionally paraphrased: replace a fraction
  paraphrase of the span tokens with synonyms/reorderings). The ground-truth label
  (doc d is contaminated with item i) == we actually embedded item i's span into d.
  This label is NEVER read by detectors.

## DETECTORS (read TEXT only)
- (a) DOCUMENT-LEVEL near-dedup: MinHash/Jaccard similarity of the WHOLE doc's n-gram shingle
  set vs the WHOLE benchmark item's shingle set. Flags (d,i) contaminated iff
  Jaccard(shingles(d), shingles(i)) >= doc_thresh. Standard near-dup that only fires when
  the doc AS A WHOLE resembles the item.
- (b) PASSAGE-LEVEL span match: slide a window over doc d; flag (d,i) iff there exists a
  doc-window whose k-gram overlap with item i exceeds span_thresh (fraction of item i's
  k-grams found within a doc window). I.e. a benchmark span match (GPT-3/PaLM n-gram analog).

## METRICS
- Per detector: RECALL = (true-contaminated (d,i) pairs flagged) / (all true-contaminated pairs).
- Per detector: PRECISION = (flagged pairs that are truly contaminated) / (all flagged pairs).
  Passage-level PRECISION is the LOAD-BEARING false-positive control.
- MISS GAP = fraction of TRUE-contaminated pairs caught by passage-level but MISSED by
  document-level = |caught_passage AND missed_doc AND true| / |true|.
- REPORTED-RATE effect: reported contamination rate = (#docs flagged) / N per detector.
  Compare doc-level vs passage-level vs TRUE rate. "Materially changes" = passage-level
  reported rate substantially closer to true AND >1.25x doc-level reported rate.

## SWEEPS
- span_ratio = item_len/doc_len in {0.5, 0.1, 0.02, 0.01}
- paraphrase in {0.0, 0.2, 0.4}
- doc_len in {500, 2500, 5000}
- doc_thresh in {0.5, 0.8} ; span_thresh in {0.6, 0.8}
- ngram_k = 8 (PaLM 8-gram analog; conservative for L0 short items)
- contam_frac = 0.2 ; N docs = 300 ; M items = 60 ; 7 SEEDS (0..6)

## DECISION RULE
- HELD: in realistic long-doc regime (span_ratio <= 0.02), MISS GAP > 20% AND passage-level
  precision >= 0.8 AND passage-level reported rate >1.25x doc-level (closer to true).
- PARTIAL: gap >20% some regimes but precision degrades, or rate change not material.
- NEGATIVE (a WIN): doc-level already catches most (gap <20% everywhere), OR passage over-flags
  (low precision — extra catches are innocent overlap), OR gap does not change reported rates.

## ANTI-CIRCULARITY
Ground truth = generative embedding fact (we control whether item i span went into doc d).
Both detectors read ONLY text, NEVER the label. Doc-level = whole-vs-whole; passage = span
window n-gram. Innocent common-phrase overlap injected so passage FP is genuinely possible.

## PRIOR-ART CAVEAT
n-gram contamination checks are PUBLISHED (GPT-3 13-gram, PaLM 8-gram, contamination surveys,
dedup e.g. Lee et al. 2021). Novelty = the MEASURED doc-vs-passage granularity GAP and its
effect on REPORTED rates under a precision control — NOT "contamination exists" / "n-gram checks exist".

## OUTPUTS
- results/raw_results.csv  (per seed x config)
- results/summary.csv      (aggregated across seeds)
- RESULTS.md
