# PRE-REGISTRATION — EXP-0069 / CLAIM-0059 (L1, DECISIVE) — researcher-0066

**Registered BEFORE running the measurement.** One-shot L1. Honest pipeline: a RED is a WIN (it is the truth).

## QUESTION (the one number that gates GREEN)
Of document pairs that are IDENTICAL under the MODEL tokenizer's normalization (NFKC + casefold),
what fraction SURVIVES (is NOT collapsed by) the PRODUCTION dedup pipeline's default normalization?
That surviving fraction = `residual_FN_rate` = the hidden model-identical-dup exposure attributable
to the normalizer-divergence seam, AFTER production normalization already does lowercase + diacritic-strip.

## DATA (real multilingual corpus)
- **allenai/c4** (C4-multilingual), validation splits, streamed via HuggingFace datasets-server
  `/rows` and/or parquet files (refs/convert/parquet). REAL web text.
- Languages chosen for pervasive Unicode-compatibility variation:
  - **ja** (Japanese) + **zh** (Chinese): fullwidth↔halfwidth latin/digits/punct, CJK compat ideographs.
  - **ar** (Arabic): combining marks / presentation forms / tatweel.
  - **de**, **fr** (European): precomposed↔combining accents, ligatures (ﬁ→fi), ß/casefold.
- Target sample: >= 30k documents total across languages (CPU-only sufficient).
- If download blocked at runtime: FALLBACK to /rows streaming; LAST RESORT proxy corpus (flagged).
  Whatever is used will be STATED CLEARLY in RESULTS.

## THE TWO NORMALIZERS
- **MODEL (GT equivalence standard):** `NFKC(casefold(doc))`. Two docs are *model-identical* iff
  `NFKC(casefold(d1)) == NFKC(casefold(d2))`. (Harness-computed GT; never read by the tested signal.)
- **PRODUCTION DEDUP DEFAULT (tested signal):** the REAL datatrove `simplify_text` logic:
  lowercase -> NFD -> strip combining marks (Mn) -> strip punctuation -> collapse whitespace ->
  normalize digits (each digit -> '0'). Implemented from the published datatrove default.
  (Cross-check arm: text-dedup preprocess = lowercase + split on non-word chars.)
  The tested signal NEVER reads the GT.

## MEASUREMENT (anti-circular)
For each pair (d1,d2) that is model-identical (`NFKC(casefold(d1))==NFKC(casefold(d2))`, GT):
- Apply production normalizer P. If `P(d1)==P(d2)` -> deduper WOULD catch the pair (no FN).
- If `P(d1)!=P(d2)` -> pair escapes the deduper DESPITE being model-identical -> a **residual FN**.
- `residual_FN_rate = (model-identical pairs with P(d1)!=P(d2)) / (total model-identical pairs)`.

Because exhaustive O(N^2) pairing on a real corpus where most docs are unique would be dominated by
trivially-distinct pairs (uninformative), the model-identical pair POPULATION is constructed honestly by:
generating, for each REAL doc, its set of model-equivalent variants drawn ONLY from REAL Unicode
equivalence classes (fullwidth/halfwidth, NFKC compat, casefold, ligature expansion, combining sequences)
that actually OCCUR in that doc's characters. Each (doc, model-equivalent-variant) is a model-identical
pair BY CONSTRUCTION (verified by the GT comparator). We then ask whether production P collapses it.
This isolates exactly the seam: model says "same", does production also say "same"?
The variant generator uses ONLY transformations that leave NFKC+casefold invariant (verified per-pair);
it never reads P's output. Prevalence is reported as: fraction of real docs that even CONTAIN a character
whose NFKC+casefold class has a representative that production-P does NOT collapse.

## GATES (pre-committed)
- **GREEN** iff `residual_FN_rate >= 1%` of model-identical near-dup pairs in multilingual slices
  (material hidden-dup exposure from the normalizer seam).
- **RED** iff `residual_FN_rate < 0.1%` (seam open but TOOTHLESS: production normalization already
  collapses nearly all the model-equivalence variation).
- 0.1%–1% = ambiguous YELLOW band; report the number honestly and let orchestrator decide.

## ALSO REPORTED
(a) PREVALENCE of relevant residual Unicode variation in the real corpus.
(b) WHICH Unicode equivalence classes drive the residual (fullwidth? ligatures? combining marks
    production's NFD+strip-Mn does NOT remove? compat ideographs?).
(c) whether word-shingle vs BPE-token-shingle representation changes the picture.

## NULL/HONESTY EXITS
- If production P collapses ~all model-equivalent variants -> RED (toothless). Reported as a WIN.
- If the residual is driven by a single artifact class only, that is stated (scoped, not overclaimed).

— researcher-0066, pre-registered 2026-06-04
