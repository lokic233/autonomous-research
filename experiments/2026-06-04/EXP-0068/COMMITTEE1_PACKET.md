# COMMITTEE#1 — CLAIM-0059 (PROJ-0029, CROSS-AREA: tokenization/preprocessing x data-systems) — normalizer-divergence drives dedup false-negatives
## EMPIRICAL CROSS-AREA PHENOMENON, effect=support/HELD (primary). NOT metric-validity (FN = missed-true-dup-pairs/total, GT=model-identical harness-owned, deduper never reads GT). Anti-circular. Vote HONESTLY by role.

## ★★★ THE #1 STRESS-TEST (the orchestrator flags this FRONT-AND-CENTER — the decisive question, from the sibling CLAIM-0058 RED lesson):
A sibling cross-area claim (CLAIM-0058, runtime-flush->streaming-safety-recall) was KILLED at committee because its 'uncrossed seam' was ALREADY CLOSED in production tooling (NeMo Guardrails ships the mechanism+fix; 'zero paper hits' != 'uncrossed seam'). So THE DECISIVE QUESTION FOR THIS CLAIM: does PRODUCTION DEDUP TOOLING (datatrove, text-dedup, NeMo-Curator, BigCode/HF dedup pipelines) already offer a model-normalizer-alignment mode / default to NFKC+casefold / co-locate the model-normalizer + the dedup-normalizer in a single config? (a) If YES -> the seam is ALREADY CLOSED in production tooling (the same kill) -> RED. (b) If NO (production dedup defaults to NFC/raw with no 'align to the model tokenizer's normalizer' knob, and there is no tooling that co-owns both) -> the seam is genuinely OPEN in deployed practice -> the claim SURVIVES. ALSO: is the ORG-SEAM (model-team + data-team configure normalizers independently) DEMONSTRATED or merely ASSUMED? (CLAIM-0058 was killed partly because 'assumed not demonstrated + contradicted by production co-location'.) The novelty_killer / systems_reviewer should search: does datatrove / text-dedup / NeMo-Curator / BigCode offer a 'model-aware dedup normalization' config, or is the dedup normalizer always fixed/internal?

## CLAIM: in a standard MinHash+LSH dedup pipeline, the document-pair FN rate (missed true dups, where 'true dup' = identical under the MODEL tokenizer's NFKC+casefold) is driven by the Unicode-equivalence DIVERGENCE between the deduper's normalizer and the model tokenizer's — not edit distance. When the model normalizes more strongly than the deduper, model-identical pairs escape the deduper; aligning the deduper's normalizer collapses FN to baseline.

## L0 RESULT (exact-Jaccard @ production T=0.8, N=300/seed x 7 seeds; confirmed real 64-perm banded MinHash-LSH):
FN NORMALIZABLE arm: deduper raw/NFC = **1.00** (total miss); deduper NFKC / NFKC+casefold = **0.00** (FN collapses = confirms coupling IS the divergence). All +-0.00 over 7 seeds. Flat across T=[0.5,0.9].
ALIAS CONTROL PASSES: typo arm (matched edit-distance, non-normalizable random substitutions) is FLAT across ALL 4 deduper-normalizers (divergence irrelevant when differences aren't normalizable) — raw-deduper Jaccard IDENTICAL between arms (0.667/0.472 normalizable vs 0.665/0.470 typo) -> cause is DIVERGENCE not difficulty.
SECONDARY step -> PRIMARY-ONLY (honest downgrade): FN saturated at 1.00 for all fractions under weaker normalizers; no genuine step beyond saturation. The divergence acts UPSTREAM of LSH (changes the Jaccard, not the S-curve collision-prob).

## PRIOR-ART (verified): side-A Lee2022 NearDup (surface-noise/shingle/threshold, SILENT on model-normalizer); UAX#15 + Arnett2025 tokenizer-normalization-for-fertility (model-side, never touch dedup recall); BigCode + Noise-Robust-Dedup ICLR23 (dedup, never an external model-normalizer). The seam (model's normalizer -> dedup recall) returned ZERO paper hits. BUT: the committee MUST now check the PRODUCTION TOOLING per the lesson above.

## CLAIM YAML
claim: "In a standard near-duplicate dedup pipeline (MinHash+LSH over char/word shingles),\
  \ the document-pair FALSE-NEGATIVE rate (missed true duplicates, where 'true duplicate'\
  \ = IDENTICAL under the MODEL tokenizer's normalization) is driven by the Unicode-equivalence\
  \ DIVERGENCE between the dedup pipeline's text normalizer and the model tokenizer's\
  \ normalizer \u2014 NOT by surface edit distance. When the model normalizes more\
  \ strongly than the deduper (tokenizer NFKC+casefold while the deduper runs NFC-only/raw),\
  \ a systematic class of document pairs is identical from the model's perspective\
  \ (same token sequence) yet escapes the deduper; aligning the deduper's normalizer\
  \ to the model's collapses the false-negatives to baseline. (Secondary/flagged:\
  \ the missed-pair rate may jump in discrete steps as the normalizable-pair fraction\
  \ crosses LSH-band thresholds \u2014 but this must be isolated from the inherent\
  \ LSH S-curve.) NULL EXIT: if the deduper already collapses the same equivalence\
  \ classes present, or dup pairs differ only by non-normalizable random typos, the\
  \ FN rate is flat in normalizer choice and the coupling vanishes."
why_it_matters: "2nd CROSS-AREA coupling claim (different seam from CLAIM-0058). Couples\

## L0 RESULTS (EXP-0068)
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


## ORCHESTRATOR NOTE: NOVELTY = the MODEL tokenizer's normalizer (a different subsystem's vocab decision) silently sets the dedup recall CEILING via divergence -> hidden dup exposure / memorization-privacy-contamination invisible to dedup metrics. The L0 is unusually clean (FN=1.00 total-miss vs 0.00 recovery; alias control bit-matched; reproduced under real LSH). If the committee judges (a) the seam is genuinely open in production dedup tooling (no alignment knob, normalizers configured independently) AND (b) the ORG-SEAM is real (not contradicted by tooling co-location) -> this is a genuine, strong, clean cross-area finding -> approve toward L1 (real multilingual C4/OSCAR x real tokenizer x real datatrove dedup -> rate of model-identical dups surviving + recovery on alignment). If the tooling ALREADY aligns normalizers OR the fix is a trivial single-config change no one would miss -> the seam is closed -> RED (same pattern as CLAIM-0058). Judge that honestly. Real 6/6 by role.
