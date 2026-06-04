# PRE_REGISTRATION — EXP-0068 / CLAIM-0059 / researcher-0065 (L0)

## CLAIM (CROSS-AREA: tokenization/preprocessing × data-systems)
In a standard MinHash+LSH near-dedup pipeline, the document-pair FALSE-NEGATIVE rate
(missed true duplicates, where 'true duplicate' = IDENTICAL under the MODEL tokenizer's
normalization = NFKC+casefold) is driven by the Unicode-equivalence DIVERGENCE between the
deduper's normalizer and the model tokenizer's — NOT by surface edit distance. When the model
normalizes more strongly than the deduper (model NFKC+casefold, deduper raw/NFC), a class of
pairs identical from the model's view escapes the deduper; aligning the deduper's normalizer
collapses the FN to baseline.

## PRIMARY vs SECONDARY split
- PRIMARY (robust): DIVERGENCE-DRIVES-FN. Decided by the CAUSAL-ALIAS CONTROL.
- SECONDARY (flagged, S-curve-guarded): is there a genuine STEP in FN-vs-normalizable-fraction
  beyond the textbook LSH S-curve? If the step is just the S-curve -> downgrade to PRIMARY-ONLY.

## MODEL (harness-owned GT normalizer, NEVER read by deduper)
model_normalize(s) = casefold(NFKC(s))  [strong: compatibility folding + case folding]
GT: a true-dup pair (doc1,doc2) is a GROUND-TRUTH DUPLICATE iff
    model_normalize(doc1) == model_normalize(doc2).
By construction every generated pair satisfies this (see arms). FN computed by harness only.

## CORPUS (harness owns construction & GT)
- N base docs ~ 6000. Vocab: ascii words + multilingual/accented/punctuation tokens so
  compatibility/case/combining variation is meaningful.
- Each doc has length ~ 40-120 tokens.
- For a controlled fraction P (corpus-composition sweep), make a TRUE-DUPLICATE pair:
  doc2 = doc1 with exactly M positions changed (M = matched edit-budget, default 6).
  ARM determines the KIND of change:
    (i) NORMALIZABLE arm: each of the M chosen chars replaced by a COMPATIBILITY/CASE/COMBINING
        EQUIVALENT codepoint (fullwidth<->halfwidth, ligature ﬁ<->'fi', precomposed é<->e+combining,
        upper<->lower) such that model_normalize(doc1)==model_normalize(doc2) STILL holds (true dup).
    (ii) TYPO arm: each of the M chosen chars replaced by a RANDOM real char substitution that does
        NOT normalize away (model_normalize differs char-for-char). To keep these as GT-DUPLICATES
        for the FN measurement under the SAME definition, the TYPO arm is the EDIT-DISTANCE-MATCHED
        CONTROL: same M changes, same positions distribution. NOTE: typo pairs are NOT model-identical;
        they are the difficulty control. We measure the deduper's flag-rate on typo pairs at matched M
        and compare its SENSITIVITY to normalizer choice. KEY: if FN(flag-miss) on typo pairs is FLAT
        across deduper-normalizers while normalizable-arm FN moves, the mover is divergence not difficulty.
- MATCHED EDIT DISTANCE: both arms apply exactly M raw-codepoint changes at the same positions, so
  raw Levenshtein/Hamming budget is held FIXED across arms.

## DEDUPER (tested signal; reads ONLY its own shingles/hashes; NEVER GT)
From-scratch MinHash + banded LSH.
- internal_normalizer = PARAM in {raw, NFC, NFKC, NFKC+casefold}.
- shingles: k=5 char shingles over internally-normalized text (production default).
- num_perms = 128. Banded LSH: b=32 bands x r=4 rows (production-ish; threshold≈(1/b)^(1/r)≈0.42
  collision knee; we ALSO sweep band/row to place knee near Jaccard 0.8).
- Production baseline config: k=5 char, 128 perms, NFC internal normalizer (realistic default),
  banded LSH with knee tuned ~0.8.
- Emits candidate duplicate pairs (any LSH band collision). A true-dup pair is a FALSE NEGATIVE
  if the deduper does NOT emit it.

## ANTI-CIRCULAR
GT = model_normalize-identity (harness). Deduper sees only its own shingles/hashes under its
normalizer. FN = (model-identical true-dup pairs NOT flagged by deduper) / (total model-identical
true-dup pairs). Deduper never sees GT label.

## ARMS + SWEEPS
- deduper-normalizer ∈ {raw, NFC, NFKC, NFKC+casefold}
- arm ∈ {normalizable, typo}
- Jaccard-threshold / LSH band-row sweep (place knee at several points)
- corpus-composition: fraction normalizable P ∈ {0.1,...} for the step analysis
- seeds: >=5; report mean + bootstrap/normal CI.

## DECISIVE RESULTS
- PRIMARY: in NORMALIZABLE arm with deduper weaker than model (raw/NFC) -> FN LARGE.
  In TYPO arm at matched M -> deduper flag-behavior FLAT across normalizers (alias control).
  deduper=NFKC+casefold (aligned) -> FN COLLAPSE to baseline (mitigation null arm).
- SECONDARY (S-curve-guarded): genuine step in FN-vs-P beyond LSH S-curve? Isolate by holding
  band/row FIXED and showing the FN step is/ isn't explained by Jaccard crossing the S-curve knee.
  Report Jaccard distribution per arm + whether FN step coincides with knee.

## THREE NULL EXITS (honest)
N1. FN FLAT across deduper-normalizers EVEN in normalizable arm (deduper's NFC already collapses
    the classes) -> coupling absent -> claim FALSE / NULL.
N2. FN moves EQUALLY in the typo arm as in normalizable arm at matched M -> it's difficulty not
    divergence -> NULL.
N3. (secondary) the FN step in FN-vs-P is fully explained by the LSH S-curve (Jaccard crossing knee)
    -> downgrade to PRIMARY-ONLY (PARTIAL), do not headline the step.

## OUTCOMES
- HELD: normalizable-arm FN large under weaker deduper-normalizer + typo-arm FLAT at matched M +
  aligning normalizers collapses FN to baseline.
- PARTIAL: primary holds but step is just LSH S-curve -> primary-only.
- NULL: N1 or N2 fires.

## PRIOR-ART (verified)
side-A: Unicode UAX#15; tokenizer-normalization-for-fertility (Arnett2025).
side-C: Lee2022 dedup; Kandpal2022; BigCode near-dedup; Noise-Robust-Dedup ICLR23 — all frame dedup
recall as shingle/threshold/hash + surface-noise, NEVER an external MODEL-normalizer. Seam: zero direct
hits. Novelty = the MODEL's normalizer (a different subsystem's vocab decision) sets the dedup recall
ceiling via normalizer DIVERGENCE.

## RUNTIME: L0, CPU-only, pure-Python stdlib (unicodedata, hashlib), SERIAL, <=15 min.
