# RESULTS — EXP-0068 / CLAIM-0059 — researcher-0065 (L0)

## OUTCOME: **HELD (PRIMARY)** — divergence-drives-FN. Secondary step: PRIMARY-ONLY (no step beyond saturation).

The MODEL tokenizer's normalizer (NFKC+casefold) sets the near-dedup recall **ceiling**: when the
deduper normalizes more weakly than the model (raw / NFC-only), every document pair that is
IDENTICAL under the model's normalization escapes the deduper (FN = 1.00). Aligning the deduper's
normalizer to the model's (NFKC+casefold) collapses FN to baseline (0.00). The cause is normalizer
DIVERGENCE, not surface edit distance — proven by the matched-edit-distance typo control.

---

## SETUP (pure-Python stdlib: unicodedata, hashlib, random; CPU-only; SERIAL)
- **Corpus (harness-owned GT):** synthetic docs, ascii + accented/multilingual vocab. For each pair,
  doc2 = doc1 with a controlled difference of TYPE, at matched positions/count (matched raw edit distance).
- **GT (never read by deduper):** pair is a TRUE DUPLICATE iff `NFKC(casefold(doc1)) == NFKC(casefold(doc2))`.
- **Two arms (matched edit distance):**
  - NORMALIZABLE: each changed char → compat/case/combining-EQUIVALENT codepoint
    (fullwidth↔halfwidth, ligature↔expansion, precomposed↔combining, upper↔lower). Stays model-identical.
  - TYPO: each changed char → random NON-normalizable substitution. Same count/positions. Difficulty control.
- **Deduper (tested signal; reads only its own shingles):** from-scratch MinHash + banded LSH, k=5 char
  shingles, internal-normalizer PARAM ∈ {raw, NFC, NFKC, NFKC+casefold}. FN computed by harness.
- Verified with BOTH an exact-Jaccard deduper (sharp LSH limit, production threshold T=0.8) AND a REAL
  64-perm banded MinHash-LSH (b=4,r=16, knee≈0.92).

---

## PRIMARY RESULT — FN(deduper-normalizer, arm), production T=0.8, N=300/seed × 7 seeds

### NORMALIZABLE arm — FN = missed model-identical dups / model-identical dups
| frac | raw | NFC | NFKC | NFKC+casefold | meanJ(raw) | frac J≥0.8 (raw) |
|------|-----|-----|------|---------------|-----------|------------------|
| 0.05 | **1.00** | **1.00** | 0.00 | 0.00 | 0.667 | 0.000 |
| 0.10 | **1.00** | **1.00** | 0.00 | 0.00 | 0.472 | 0.000 |
| 0.20 | **1.00** | **1.00** | 0.00 | 0.00 | 0.251 | 0.000 |
| 0.30 | **1.00** | **1.00** | 0.00 | 0.00 | 0.132 | 0.000 |
| 0.50 | **1.00** | **1.00** | 0.00 | 0.00 | 0.030 | 0.000 |
| 0.80 | **1.00** | **1.00** | 0.00 | 0.00 | 0.001 | 0.000 |
(all ±0.00 over 7 seeds)

→ Deduper WEAKER than model (raw/NFC): **FN = 1.00 (total miss)**. Deduper ALIGNED (NFKC / NFKC+casefold):
**FN = 0.00 (perfect recall)**. The mitigation arm (align normalizers) collapses FN to baseline. **Coupling = divergence.**

### Threshold robustness (normalizable arm, frac=0.3): FN is flat in T
| T | raw | NFC | NFKC | NFKC+cf |
|---|-----|-----|------|---------|
| 0.5 | 1.00 | 1.00 | 0.00 | 0.00 |
| 0.6 | 1.00 | 1.00 | 0.00 | 0.00 |
| 0.7 | 1.00 | 1.00 | 0.00 | 0.00 |
| 0.8 | 1.00 | 1.00 | 0.00 | 0.00 |
| 0.9 | 1.00 | 1.00 | 0.00 | 0.00 |

→ FN is invariant to the Jaccard threshold: the raw/NFC deduper projects model-identical pairs to
Jaccard ≈ 0 (table above), so NO threshold and NO LSH knee recovers them. Not a threshold artifact.

### REAL banded MinHash-LSH confirmation (b=4,r=16, 64 perms, knee≈0.92, unique docs), normalizable arm FN
| frac | raw | NFC | NFKC | NFKC+cf |
|------|-----|-----|------|---------|
| 0.1 | 1.00 | 1.00 | 0.00 | 0.00 |
| 0.2 | 1.00 | 1.00 | 0.01 | 0.00 |
| 0.3 | 1.00 | 1.00 | 0.01 | 0.00 |
| 0.5 | 1.00 | 1.00 | 0.02 | 0.00 |

→ Identical conclusion in the real banded-LSH pipeline. (Tiny NFKC-only residual at high frac = precomposed
accents that NFKC keeps distinct but casefold collapses — a small extra divergence between NFKC and NFKC+casefold.)

---

## ALIAS CONTROL (the decisive test: divergence vs difficulty)
Both arms apply the SAME number of raw-codepoint changes at the SAME positions → **matched raw edit
distance**. Evidence the Jaccard trajectories are identical across arms (raw normalizer):

| frac | meanJ normalizable(raw) | meanJ typo(raw) |
|------|------------------------|-----------------|
| 0.05 | 0.667 | 0.665 |
| 0.10 | 0.472 | 0.470 |
| 0.30 | 0.132 | 0.132 |
| 0.50 | 0.030 | 0.030 |

- **Normalizable arm:** FN swings 1.00 (raw/NFC) ↔ 0.00 (NFKC+cf) — normalizer choice is decisive.
- **Typo arm:** the deduper's behavior is **FLAT across all four normalizers** (Jaccard identical to 3 d.p.;
  no model-identity to recover — these are genuinely different docs). Normalizer has zero leverage on
  non-normalizable noise.

→ At MATCHED edit distance, FN moves ONLY in the normalizable arm and ONLY with normalizer choice.
**The mover is normalizer DIVERGENCE, not difficulty.** Null exit N2 (moves equally in typo arm) did NOT fire.
Null exit N1 (NFC already collapses the classes) did NOT fire — NFC is as blind as raw to NFKC/casefold equivalence.

---

## SECONDARY (S-curve-guarded step): PRIMARY-ONLY
The claim's flagged secondary step ("FN jumps in steps vs normalizable-fraction") is **NOT supported as a
distinct effect**, and we report that honestly. Under the weaker normalizers FN is **saturated at 1.00 for
every fraction ≥ 0.05** — there is no step to attribute, because even one normalizable swap that the model
folds away is enough to (eventually) push raw Jaccard below threshold as fraction grows, and `frac J≥0.8 = 0`
everywhere for raw. The textbook LSH S-curve is irrelevant here: the divergence acts *upstream* of the LSH —
it changes the Jaccard the LSH sees, not the LSH's collision probability at a given Jaccard. So no genuine
equivalence-class STEP beyond the trivial saturation; SECONDARY downgraded to **PRIMARY-ONLY**. (Null exit N3
on the step is effectively "the step is not real / is just saturation," reported honestly.)

---

## NULL EXITS — none fired against the primary
- N1 (FN flat across normalizers even in normalizable arm — NFC already collapses classes): **did NOT fire.**
  NFC preserves compatibility/case/ligature distinctions, so NFC ≈ raw (FN 1.00). Divergence is real.
- N2 (moves equally in typo arm — difficulty not divergence): **did NOT fire.** Typo arm flat across normalizers.
- N3 (secondary step is just the LSH S-curve): the step itself isn't a real effect (saturation) → SECONDARY dropped, PRIMARY intact.

---

## INTERPRETATION / NOVELTY
A different subsystem's vocab decision — the **model tokenizer's normalizer** — silently sets the near-dedup
recall ceiling. Prior art (Lee2022, Kandpal2022, BigCode, Noise-Robust-Dedup ICLR23) frames dedup recall as a
shingle/threshold/hash + surface-noise problem and NEVER as a function of an EXTERNAL model-side normalizer;
Unicode/UAX#15 + tokenizer-normalization-for-fertility (Arnett2025) sit on the model side and never touch dedup
recall. The seam (model-normalizer ⟶ dedup-recall) has zero direct hits. Novel cross-area coupling.
**Risk:** model-identical duplicates survive production dedup purely from normalizer divergence → hidden
duplicate exposure → memorization / privacy / eval-contamination risk that is invisible to the dedup metrics.

## ARTIFACTS
- PRE_REGISTRATION.md (committed before running)
- harness.py (corpus + GT + from-scratch MinHash/LSH + arms)
- run_frac.py / run_final.py / run_lshcheck.py
- results/frac_sweep.json, results/final.json, results/lshcheck.json (+ .log)

## WHAT L1 SHOULD MEASURE
Real multilingual C4/OSCAR shard × a real HF tokenizer normalizer config (model side, e.g. NFKC+lowercase
in a BERT-family or a fertility-tuned tokenizer) × datatrove or text-dedup MinHash (data side, with its default
NFC/raw normalizer). Measure: rate of model-identical duplicate pairs SURVIVING production near-dedup due to
normalizer divergence, and recovery when the deduper's normalizer is aligned to the tokenizer's. Quantify the
resulting hidden-duplicate exposure / memorization-privacy / eval-contamination surface.
