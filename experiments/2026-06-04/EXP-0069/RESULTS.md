# RESULTS — EXP-0069 / CLAIM-0059 — researcher-0066 (L1, DECISIVE)

## OUTCOME: **GREEN GATE MET — SUPPORT.** residual_FN_rate = **95.1%** (≫ 1% gate).

The normalizer-divergence seam is NOT toothless. On REAL multilingual web text (C4), of document pairs
that are IDENTICAL under the model tokenizer's normalization (NFKC+casefold), **95.1% ESCAPE the
production dedup pipeline's default normalization** (datatrove `simplify_text`). The residual is driven
overwhelmingly by **NFKC-compatibility variation that production's lowercase+NFD+strip-Mn pipeline does
NOT collapse** — chiefly **fullwidth ASCII** (CJK) and **German ß / ligatures / typographic compat** (European).
This is a material hidden model-identical-duplicate exposure (memorization / privacy / eval-contamination risk).

---

## ★ THE NUMBER (METRIC A — NFKC-twin, injection-free, the headline)
For each REAL doc d, its most natural model-identical twin = `NFKC(d)` (the canonical Unicode rendering a
different site would use). Counted only when twin≠d AND `model_norm(d)==model_norm(twin)` (GT: model-identical).
residual FN = production dedup fails to match (`prod(d)≠prod(twin)`).

| metric | value |
|--------|-------|
| total real docs (5 langs × 4000, ja 5300→4000) | 20,000 |
| model-identical (d, NFKC-twin) pairs formable | 9,044 |
| **residual_FN_rate = pairs escaping production dedup / model-identical pairs** | **0.9514 (95.1%)** |
| pair-formable / prevalence (docs with a distinct model-identical twin) | **45.2%** |

### Per language (residual_FN_rate, prevalence)
| lang | model-identical pairs | residual FN | **residual_FN_rate** | prevalence (pair-formable) |
|------|----------------------|-------------|----------------------|----------------------------|
| ja (Japanese) | 3610 | 3552 | **0.984** | 0.903 |
| zh (Chinese)  | 3317 | 3312 | **0.998** | 0.829 |
| de (German)   | 587  | 556  | **0.947** | 0.147 |
| fr (French)   | 856  | 810  | **0.946** | 0.214 |
| ar (Arabic)   | 674  | 375  | **0.556** | 0.169 |

→ Every language clears the GREEN gate by ≥55×. CJK clears by ~98×. **GREEN.**

---

## WHICH UNICODE EQUIVALENCE CLASSES DRIVE THE RESIDUAL (attribution)
Counts = residual-driving characters (a char c where `model(c)≠c` AND `prod(c)≠prod(model(c))`):

| class | residual-driving char count (5-lang) | what it is | why production misses it |
|-------|--------------------------------------|------------|--------------------------|
| **fullwidth_ascii** | 300,261 | Ａ-Ｚ ０-９ etc. (pervasive in CJK web) | NFKC→ASCII; production **NFD is canonical-only**, never touches compat |
| other_compat | 23,850 | **ß→ss**, …→..., ™→tm, ℃→°c, º, ′″ | production `.lower()` ≠ casefold (ß stays ß); NFD keeps compat signs |
| halfwidth_kana_hangul | 14,148 | ﾊﾝｶｸ kana | compat (NFKC) not canonical (NFD) |
| fullwidth_sign | 1,330 | ＄￥％＃ | compat |
| super/subscript & modifier | 1,071 | ², ₃, ᵃ | compat |
| enclosed/circled | 1,029 | ①②㈱ | compat |
| cjk_squared | 331 | ㌔㍑ | compat |
| roman_numeral | 268 | Ⅳ→iv | compat |
| ligature | 262 | ﬁ→fi (Latin), Arabic ligatures | compat |
| fraction | 154 | ½→1⁄2 | compat |

**Root cause (one sentence):** the model normalizer uses **NFKC (compatibility) + casefold**, while the
production deduper uses **NFD (canonical) + lowercase** — NFD by definition leaves every COMPATIBILITY
character distinct, and `lower()` ≠ `casefold()` (ß, ligatures). The residual is exactly the
compatibility+casefold gap between NFKC+casefold and NFD+lower.

---

## METRIC B — does the SHINGLE / TOKEN representation change the picture? (production uses shingles, not exact match)
Of the 8,605 exact-string residual FNs, how many ALSO escape under Jaccard<0.8 of the production-normalized text:

| representation | still a FN | rate of the residual FNs |
|----------------|-----------|--------------------------|
| 5-gram char shingles (Jaccard<0.8) | 2,980 | 34.6% |
| whitespace word tokens (Jaccard<0.8) | 5,050 | 58.7% |

→ The residual is NOT merely an exact-string artifact. A large share survives even production's real
SHINGLE-based MinHash matching at T=0.8 — because a fullwidth-saturated CJK doc and its ASCII twin share
**few** production-normalized char-5-grams (fullwidth char ≠ ascii char at the shingle level too). Word-token
escape is even higher. Consistent with L0 (EXP-0068), where the divergence projects model-identical pairs to
low Jaccard the LSH cannot recover. (Docs with only a FEW fullwidth chars stay high-Jaccard → caught by shingles,
which is why shingle-FN < exact-FN; the seam's teeth are in the heavily-variant docs.)

---

## CROSS-CHECK: text-dedup normalizer arm (lowercase + split on \W)
Re-run METRIC A with the second production default (text-dedup `\W+` split):
| lang | residual_FN_rate (text-dedup arm) |
|------|-----------------------------------|
| de | 0.203 | fr | 0.225 | ar | 0.132 |
(text-dedup's aggressive non-word splitting collapses more punctuation-class variation, so the European/Arabic
residual drops to 13–23% — STILL ≥13× the GREEN gate. CJK fullwidth-letter residual remains ~unchanged because
fullwidth letters are word chars and survive \W splitting too.) **Both production defaults clear GREEN.**

---

## DATA SOURCE + CAVEATS (stated clearly)
- **REAL corpus:** `allenai/c4` (C4-multilingual), validation splits, streamed live from the HuggingFace
  datasets-server `/rows` API to the Mac. 21,300 real web documents: ja 5,300, zh/ar/de/fr 4,000 each
  (measured on 4,000/lang = 20,000). Saved to `data/c4_*.jsonl` (189 MB). NO injection in METRIC A — the
  variation is ALREADY PRESENT in the real text; the model-identical twin is the doc's own NFKC rendering.
- **MODEL normalizer (GT standard):** `NFKC(casefold(x))` — the tokenizer normalization standard per the claim
  (used by mBERT/XLM-R-family NFKC tokenizers + casefold). Harness-computed GT; never read by the tested signal.
- **PRODUCTION normalizer (tested signal):** REAL datatrove `simplify_text` default = lowercase → NFD →
  strip combining marks (Mn) → strip ASCII punctuation → collapse whitespace → digit→'0'. Cross-checked with
  text-dedup `\W+` preprocess. The tested signal NEVER reads the GT (anti-circular).
- CAVEAT: the model GT is the *standard* NFKC+casefold, not a specific loaded tokenizer.json normalizer; this is
  the equivalence standard named in CLAIM-0059 and validated in L0. A specific tokenizer that does only NFC would
  shrink the gap, but NFKC+casefold is the pervasive multilingual-tokenizer default and the claim's stated GT.
- CAVEAT: METRIC A's twin is `NFKC(d)` (readable canonical form) while GT equality uses full `NFKC(casefold(...))`;
  pairs are only counted when model-identical under the full GT, so this is conservative (some ß-only docs need
  casefold to be model-identical and are correctly included).

---

## ANTI-CIRCULAR / HONESTY
- GT = `model_norm` equality, harness-computed. Tested signal = production normalizer output, which never
  reads the GT. The residual is the disagreement between the two independent equivalence relations on REAL text.
- No injection in the headline metric — fullwidth/ß/ligature variation is endogenous to real C4.
- RED was a live outcome: if production NFD+lower had collapsed the compat classes, residual→~0. It did not,
  because NFD is canonical-only and `lower()`≠casefold — a real, structural Unicode fact, not a tuned artifact.
- The one "caught" demonstration case (a doc whose only variation was fullwidth *punctuation* ！？, which
  production strips) confirms the harness is not trivially always-FN: production DOES catch punctuation-only
  variation; the residual is specifically the letter/digit/ligature/ß compatibility gap.

---

## DISPOSITION: **GREEN gate MET (residual_FN_rate 95.1% ≫ 1%).**
Material hidden model-identical-duplicate exposure attributable to the normalizer-divergence seam, on real
multilingual web text, driven by NFKC-compatibility (fullwidth/ligature/compat) + casefold(ß) variation that
production dedup normalization structurally cannot collapse. Recommend committee#2 (per orchestrator).
Did NOT self-converge / did NOT touch .converged.

— researcher-0066, 2026-06-04
