# EDITORIAL_REVISION — EXP-0070 / CLAIM-0059 — researcher-0067

**Purpose.** Editorial revision of EXP-0069 (which met the GREEN gate, residual_FN_rate = 95.1% on real
C4-multilingual). NO new experiments. This document addresses the **5 framing/completeness conditions** the
committee#2 (VERDICT-0058) identified as the path from YELLOW → unanimous GREEN, plus the **chair-mandated
driver-concentration baseline**. All numbers are re-derived deterministically from EXP-0069's real corpus
(21,300 C4 docs) and verified to reproduce EXP-0069's point estimates exactly before bootstrapping.

---

## CONDITION 1 — REFRAME ALTITUDE (this is a measurement, not a new mechanism)

> **Framing (use as the abstract's altitude-setting sentences):**
> The normalization / equivalence-class mismatch we measure is **not a newly discovered mechanism** — it is the
> classic information-retrieval phenomenon described in Manning, Raghavan & Schütze, *Introduction to
> Information Retrieval* (IIR) **§2.2 ("Determining the vocabulary of terms" → token normalization &
> equivalence classing)**: two independent text-processing stages that adopt **different equivalence relations**
> over surface forms will disagree on which strings are "the same," and the disagreement is exactly the
> symmetric difference of their equivalence classes. **Our contribution is empirical, not conceptual:** we
> *measure the magnitude* of that known mismatch at a specific, previously-unquantified seam — the
> **near-dedup normalizer × model-tokenizer normalizer** seam — on real multilingual web text, and we show it
> has a **demonstrated-material safety/privacy/contamination consequence** (model-identical duplicates that the
> production deduper structurally cannot collapse → memorization / eval-contamination exposure). We claim the
> *measurement and its consequence*, not the existence of the mechanism.

IIR §2.2 is cited explicitly. The mechanism (equivalence-class mismatch between two normalizers) is textbook;
the **45.2% prevalence on real C4** and the **34.6% survival through production MinHash** are the new facts.

---

## CONDITION 2 — LEAD METRIC (operationally-grounded, not the construction rate)

`theory_skeptic` is correct that the **95.1% twin-construction/escape rate is structurally predicted by
UAX#15 once the experiment design is fixed** (NFD-canonical can never collapse a compatibility character, and
`.lower()` ≠ `casefold()`, so a model-identical-by-NFKC twin is *almost tautologically* not prod-identical —
the only question is how often the design is *applicable*). We therefore **demote 95.1% from the headline** and
**lead with the two operationally-grounded numbers** that demonstrate real-world impact:

> **HEADLINE (rewritten):**
> **45.2%** of real multilingual web documents (C4: ja/zh/ar/de/fr) have a **model-identical NFKC-twin** — a
> different-but-tokenizer-equivalent rendering that a production near-dedup pipeline treats as a *distinct*
> document. Of those model-identical pairs, **34.6%** survive **real MinHash near-dedup at threshold T=0.8**
> (5-gram char shingles over production-normalized text) — i.e. they are *not* caught even by shingle-based
> approximate matching, the actual production mechanism. These are hidden, tokenizer-identical duplicates that
> reach the model.

The 95.1% exact-string escape rate is retained as a **supporting / explanatory** figure (it explains *why* the
operational numbers are nonzero), not as the lead claim.

| role | metric | value [95% CI] |
|------|--------|----------------|
| **LEAD** | prevalence: real docs with a model-identical NFKC-twin | **45.2%** (9,044 / 20,000) |
| **LEAD** | of those pairs, survive real MinHash @ T=0.8 | **34.6%** [33.6%, 35.6%] |
| support | exact-string residual_FN_rate (structurally predicted) | 95.1% [94.7%, 95.6%] |
| support | word-token Jaccard<0.8 survival | 58.7% |

---

## CONDITION 3 — TOKENIZER-FAMILY SCOPE NOTE (honest bound on the claim)

> **Scope.** This finding holds **specifically for models whose tokenizer normalizer is NFKC + casefold** — the
> SentencePiece/T5 `nfkc_cf` normalizer family, which is the **pervasive multilingual default** (T5/mT5,
> ByT5-adjacent SP configs, many XLM/multilingual SP tokenizers, and any tokenizer.json declaring an
> `Nmt`/`NFKC`+`Lowercase`/casefold normalizer). For this family, the model's notion of "identical" is
> NFKC+casefold, which is **strictly coarser** than the production deduper's NFD+lowercase — hence the gap.
>
> The relationship **does not hold uniformly across tokenizer families**, and we state the boundaries:
> - **Raw-bytes BPE (GPT-2 / Llama / most GPT-family):** the tokenizer applies **no Unicode normalization** —
>   its "identical" is **byte/string-identical**. A production deduper that *does* normalize is then *more*
>   aggressive than the model, so there is **no model-identical-but-prod-distinct gap in this direction** (the
>   relationship inverts: the model is the stricter equivalence). The seam's teeth require model-coarser-than-prod.
> - **BERT-multilingual-style (NFD/NFC + lowercase + strip-accents):** the tokenizer's normalization is
>   **≈ the production deduper's** (both are canonical-decomposition + lowercase). The two equivalence relations
>   nearly coincide, so **the gap collapses toward zero**.
>
> The claim is therefore: *for the NFKC+casefold tokenizer family (the dominant multilingual default), the
> dedup×tokenizer seam leaks model-identical duplicates at the measured rates.* Outside that family the
> magnitude is bounded by how far the tokenizer's normalizer sits from NFKC+casefold.

---

## CONDITION 4 — BOOTSTRAP CONFIDENCE INTERVALS

**Method.** Re-derived the **per-pair residual-FN indicator** (1 if `prod(d) ≠ prod(twin)` for a GT
model-identical pair, else 0) directly from EXP-0069's real C4 jsonl using the identical `measure_final`
logic (`normalizers.model_norm` / `prod_norm`). Verified the per-language and pooled point estimates reproduce
EXP-0069 *exactly*. Nonparametric percentile bootstrap, **B = 10,000**, seed = 20260604, resampling the
per-pair indicator with replacement (for a 0/1 sample, the resample-mean distribution is exactly
Binomial(N, p̂)/N — generated via an exact Bernoulli-geometric sampler; no numpy dependency, no parametric
approximation). 95% CI = [2.5th, 97.5th] percentile of resample means.

### residual_FN_rate — per language + pooled (95% bootstrap CI)
| lang | n model-identical pairs | residual_FN_rate | 95% CI |
|------|------------------------|------------------|--------|
| ja (Japanese) | 3,610 | 0.9839 | **[0.9795, 0.9878]** |
| zh (Chinese)  | 3,317 | 0.9985 | **[0.9970, 0.9997]** |
| de (German)   | 587   | 0.9472 | **[0.9284, 0.9642]** |
| fr (French)   | 856   | 0.9463 | **[0.9311, 0.9603]** |
| ar (Arabic)   | 674   | 0.5564 | **[0.5193, 0.5935]** |
| **POOLED**    | 9,044 | **0.9515** | **[0.9469, 0.9558]** |

**Every language's lower CI bound clears the 1% GREEN gate by ≥51× (Arabic, the weakest) to ≥997× (Chinese).**
The pooled lower bound is 94.7%. The gate is not within an order of magnitude of any interval.

### MinHash-survival sub-rate (the LEAD operational number), 95% bootstrap CI
| metric | n (fn pairs) | rate | 95% CI |
|--------|--------------|------|--------|
| survive real MinHash near-dedup @ T=0.8 (char 5-gram Jaccard<0.8) | 8,605 | **0.3463** | **[0.3361, 0.3562]** |

The headline operational claim (34.6% survive production MinHash) has a tight ±1% CI well clear of any
"could-be-an-artifact" regime.

---

## CONDITION 5 — text-dedup NORMALIZER VERIFICATION (≥2 production codebases misalign with NFKC+casefold)

**Source inspected:** `ChenghaoMou/text-dedup` (GitHub), the widely-used MinHash/SimHash dedup toolkit used in
several open LLM data pipelines.

**What its near-dedup preprocessing actually does** (its `NON_ALPHA` tokenization path, used by the
MinHash/MinHashLSH deduplicators):
- It splits text on a **non-alphanumeric regex** — `NON_ALPHA = re.compile(r"\W+", re.UNICODE)` (equivalently
  `[^A-Za-z0-9_]+` under the Unicode flag) — to produce the tokens that are then n-gram-shingled and hashed.
- There is **NO `unicodedata.normalize("NFKC", ...)`** and **NO `casefold()`** in this path. Case handling, when
  present, is plain ASCII `.lower()`; the dominant transform is the `\W+` split + whitespace rejoin.

**Conclusion (substantiates ≥2 production codebases off NFKC+casefold):**
1. **datatrove** (`simplify_text`): lowercase → **NFD (canonical-only)** → strip combining marks → strip ASCII
   punctuation → digit→0 → collapse whitespace. **NFD ≠ NFKC; `.lower()` ≠ `casefold()`.** → misaligned.
2. **text-dedup** (`NON_ALPHA` `\W+` split + `.lower()`): **no NFKC, no casefold, no canonical decomposition at
   all** — purely a lowercase + non-word-character split. → misaligned.

Neither production deduper applies the model tokenizer's NFKC+casefold equivalence. The seam is **not a
single-library quirk** — it is present across the two most common open-source dedup defaults. (EXP-0069's
cross-check arm confirms the *consequence*: under the text-dedup `\W+` arm the European/Arabic residual drops to
13–23% — because aggressive non-word splitting collapses more punctuation-class variation — but **still ≥13×
the GREEN gate**, and the CJK fullwidth-letter residual is ~unchanged because fullwidth letters are `\w` word
characters and survive the split.)

---

## CHAIR BASELINE — DRIVER CONCENTRATION (Gini / top-class share): is it a single-mode artifact?

**Question:** is the residual driven by a single Unicode class (which would make the result a narrow
fullwidth-ASCII artifact), or is it genuinely multi-modal? Computed two concentration views.

### (a) Per-pair dominant-class assignment (each FN pair → its top residual-driving class)
| class | dominant in # FN pairs | share |
|-------|------------------------|-------|
| fullwidth_ascii | 6,663 | **77.4%** |
| other_compat (ß→ss, ™, ℃, …, ′″, º, etc.) | 1,634 | **19.0%** |
| super/subscript & modifier | 140 | 1.6% |
| halfwidth_kana_hangul | 66 | 0.8% |
| fraction | 30 | 0.3% |
| ligature (ﬁ→fi, Arabic) | 27 | 0.3% |
| + 5 more classes (fullwidth_sign, enclosed_circled, cjk_squared, roman_numeral, presentation_form) | ≤14 each | <0.2% each |

- **Gini (per-pair dominant class) = 0.852**; **top-1 share = 77.4%**; **top-10 share = 99.98%**.
- **Classes holding ≥1% of dominant-pair mass = 3** (fullwidth_ascii, other_compat, super_subscript_modifier).

### (b) Char-level residual-driving counts (every residual-causing character)
| | value |
|--|--|
| total residual-driving chars | 342,738 |
| top-1 class share (fullwidth_ascii) | 87.6% |
| top-10 class share | 99.99% |
| **Gini** | **0.870** |

**Interpretation (the chair's question, answered):** the residual is **dominant-but-not-monolithic**.
Fullwidth-ASCII is the clear primary mode (77–88% depending on view), exactly as predicted — **but it is NOT
the only class**. A substantial, independent **second mode (`other_compat`: German ß→ss, typographic compat
℃/™/…/′″/º) drives ~19% of FN pairs**, and a non-trivial third mode (super/subscript). The European languages
(de/fr at 94.6–94.7% residual) clear the gate **without any fullwidth-ASCII at all**, proving the seam has
teeth from at least two structurally distinct Unicode sources (CJK fullwidth + Latin/typographic casefold-compat).
The high Gini reflects a **heavy-but-not-degenerate** distribution: ≥3 classes each carry ≥1% of the signal, so
the result is **not a single-mode artifact**. (If fullwidth-ASCII were the *only* driver, de/fr would sit at the
gate floor, not at 94%+.)

---

## SUMMARY: all 6 conditions addressed
1. ✅ Altitude reframed — empirical measurement of IIR §2.2 normalization/equivalence-class mismatch at the
   dedup×tokenizer seam, with demonstrated material privacy/contamination consequence. Mechanism not claimed novel.
2. ✅ Lead metric rewritten — leads with **45.2% prevalence** + **34.6% MinHash survival**; 95.1% demoted to support.
3. ✅ Tokenizer-family scope note — bounded to NFKC+casefold family; raw-bytes BPE inverts, BERT-NFD collapses.
4. ✅ Bootstrap 95% CIs — per-language + pooled (B=10k); every lower bound ≥51× the gate; MinHash-survival CI ±1%.
5. ✅ text-dedup normalizer verified — `\W+` split + lower, **no NFKC/casefold**; ≥2 production codebases misalign.
6. ✅ Chair baseline — Gini 0.85 (per-pair) / 0.87 (char); top-1 77–88% but ≥3 classes ≥1% → multi-modal, not artifact.

**Disposition:** GREEN gate remains met (this revision does not move the gate; it reframes, bounds, and
quantifies uncertainty). Effect = **SUPPORT**. Ready for committee#3 re-run toward unanimous GREEN.
Artifacts: `results/bootstrap_gini.json` (CIs + concentration), `PRE_REGISTRATION.md`. Did NOT touch .converged.

— researcher-0067, 2026-06-04
