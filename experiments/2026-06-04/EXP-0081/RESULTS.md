# RESULTS — EXP-0081 (CLAIM-0068)

**Researcher:** researcher-0068  **Parent:** orchestrator-r8-001  **Project:** PROJ-0038
**Date:** 2026-06-04  **Level:** 0 (CPU, multi-runtime)  **Compute:** cli:devvm14382 (venv ~/pq_venv)

## DISPOSITION: **WEAKEN (real-but-rare)**
The mechanism is **rock-solid and reproduces exactly** (composition verified both directions, both readers).
But the **load-bearing prevalence measurement says the seam is essentially never live in real public
parquet**: **0 of 244 float columns across 13 real public parquet files carry stored NaN.** Real-world
float missingness is stored as true-NULL, not NaN-in-parquet. The divergence requires an in-memory NaN to
reach an Arrow-native writer AS A VALUE — which does happen mechanically, but is absent from the public
corpus scanned. Honest call: **the bug is real; the blast radius is small.**

---

## ★ NOVELTY FRAMING (lead)
This is NOT "pandas treats NaN as NA" (folklore, in-memory). The candidate-new coupling: file PROVENANCE
(which runtime wrote the parquet) silently flips a FOREIGN-runtime reader's JOIN/GROUP-BY/SUM correctness —
a consequence in neither runtime's docs nor either issue tracker. We CONFIRMED the mechanism end-to-end.
The reason this lands as a WEAKEN (not GREEN) is empirical, not conceptual: the trigger condition
(NaN-stored-in-parquet) does not occur in the real public corpus we scanned.

---

## PINNED VERSIONS (exact)
- python 3.12.13+meta
- pandas 3.0.3
- pyarrow 24.0.0
- polars 1.41.2
- duckdb 1.5.3
- numpy 2.4.6

All match scout-S.

---

## (A) COMPOSITION RE-VERIFICATION — ✅ CONFIRMED both directions, both readers
Input float col `k = [1.0, NaN, 2.0, NaN, 1.0]`. (CSV: `composition.csv`)

### (a)(b) byte-level null_count of column k from the parquet footer
| writer | created_by string         | null_count(k) | meaning           |
|--------|---------------------------|---------------|-------------------|
| pandas | parquet-cpp-arrow v24.0.0 | **2**         | NaN → NULL        |
| polars | Polars                    | **0**         | NaN-as-value      |
| duckdb | DuckDB v1.5.3             | **0**         | NaN-as-value      |

### (c) SAME reader, SAME query, files differ ONLY by writer
| reader | writer | null_count | count(distinct k) | self-join using(k) | reader sees NaN | reader sees NULL |
|--------|--------|-----------:|------------------:|-------------------:|----------------:|-----------------:|
| DuckDB | pandas | 2 | **2** | **5** | 0 | 2 |
| DuckDB | polars | 0 | **3** | **9** | 2 | 0 |
| DuckDB | duckdb | 0 | **3** | **9** | 2 | 0 |
| polars | pandas | 2 | 3* | **5** | 0 | 2 |
| polars | polars | 0 | 3 | **9** | 2 | 0 |
| polars | duckdb | 0 | 3 | **9** | 2 | 0 |

- **self-join 5↔9 flips on BOTH readers** ✅ (NaN=NaN does not join in SQL; NULL=NULL does not join either,
  but the 2 collapsed NULLs vs 2 NaN values change the join cardinality: 1+1+1 finite-dup pattern → 5 vs
  the NaN-self-equality + finite dups → 9).
- **count(distinct k) 2↔3 flips on DuckDB** ✅. *On polars, `n_unique()` counts NULL as one distinct value,
  so the pandas file yields 3 (2 reals + 1 null) = same integer as the 3-real arrow file — the distinct-flip
  is **reader-dependent**, honestly noted. The self-join flip is reader-robust.*

### Sum-flip (separate single-NaN column `v = [1.0, 2.0, NaN]`)
| writer | null_count(v) | DuckDB sum(v) | polars sum(v) |
|--------|--------------:|--------------:|--------------:|
| pandas | 1 | **3.0** (finite) | **3.0** (finite) |
| polars | 0 | **NaN** | **NaN** |

**sum flips 3.0 (finite) ↔ NaN on BOTH readers** ✅ — the cleanest divergence.

**Verdict (A): composition fully reproduced.** null_count 2↔0; self-join 5↔9 (both readers); sum 3.0↔NaN
(both readers); count(distinct) 2↔3 (DuckDB; reader-dependent on polars).

---

## (B) READER-DEFAULT CHECK — ✅ NO coercion on read (seam stays open)
On the pinned versions, reading the Arrow-native (null_count=0, NaN-bearing) file, BOTH readers still SEE
the NaN as a value: DuckDB `isnan(k)` count = 2, polars `is_nan().sum()` = 2 (table above, "reader sees NaN").
Neither reader silently coerces NaN→null on read. The divergence is preserved at read time. ✅
(Matches scout-S's polars-1.41-preserves-NaN observation.)

---

## (C) ★★ PREVALENCE MEASUREMENT — the load-bearing result
Corpus: 13 real public parquet files, **39.9M rows total**, 244 float columns. (CSVs:
`corpus_manifest.csv`, `prevalence_columns.csv`)

Sources: NYC-TLC taxi (yellow 2023-01 = 3.07M rows, yellow 2019-01 = 7.70M, green 2023-01, **fhvhv 2023-01
= 18.5M rows**), and HuggingFace tabular datasets (credit-card, diabetes-readmission 151 cols, electricity,
heart-failure, house-sales, iris, compas, native-uploaded titanic + a 500k-row tabular set).

### Result
| metric | count | fraction |
|--------|------:|---------:|
| float columns scanned | 244 | 100% |
| **carry actual stored NaN values** | **0** | **0.0%** |
| have ≥1 true NULL | 13 | 5.3% |

**Zero of 244 real public float columns carry stored NaN.** Float missingness in the wild IS present and
sometimes large (e.g. NYC yellow-2019 `congestion_surcharge` = 4,884,887 nulls; titanic `Age` = 177 nulls),
but it is ALWAYS stored as **true-NULL**, never as NaN-in-parquet. The at-risk seam (NaN-stored-in-parquet)
is **not live** anywhere in this corpus.

### Writer-fingerprint finding (negative / important nuance)
Every file in the corpus was written by `parquet-cpp-arrow` (versions 7.0.0–15.0.2) — including the HF
auto-converted files (HF datasets-server uses pyarrow) AND native author uploads (the `datasets` library
wraps pyarrow). **We found NO genuinely pandas-`to_parquet`-direct public file with a distinct fingerprint.**

Critically, **`created_by` does NOT fingerprint pandas vs Arrow-direct**: BOTH `pandas.to_parquet(engine=
"pyarrow")` AND `pyarrow.write_table` emit the identical `created_by = "parquet-cpp-arrow version 24.0.0"`,
yet they behave OPPOSITELY on NaN (pandas→NULL, pyarrow-direct→NaN-value; verified). Only polars
(`created_by="Polars"`) and DuckDB (`"DuckDB version ..."`) are string-distinguishable. **You cannot reliably
fingerprint the pandas-vs-Arrow NaN behavior from the parquet footer string** — only NaN-vs-null CONTENT
discriminates, and even that is ambiguous (an Arrow pipeline that genuinely had nulls is byte-identical to
pandas-that-collapsed-NaN). This weakens the "fingerprint writers in the wild" sub-claim.

---

## (D) AGGREGATE-FLIP on REAL data — Δ=0 as-is; Δ≠0 only under labeled NaN-injection
Real Titanic `Age` column (177 true-null missing). (CSV: `real_roundtrip.csv`)

| case | null_count pandas/polars | Δ distinct | Δ self-join | sum pandas → polars |
|------|--------------------------|-----------:|------------:|----------------------|
| Age (as-is, real true-NULL) | 177 / 177 | **0** | **0** | 21205.17 → 21205.17 |
| Fare (no missing) | 0 / 0 | **0** | **0** | 28693.95 → 28693.95 |
| **Age (NaN INJECTED — mechanism demo, labeled)** | 177 / **0** | **+1** | **+31329** | 21205.17 → **NaN** |

- On the REAL column as-stored (true-NULL), pandas↔polars round-trip is **identical** (Δ=0). The seam does
  not fire because there is no NaN to collapse.
- Only when we **inject** the missing-as-NaN into the real column structure (clearly labeled, NOT used to
  inflate prevalence) does the divergence appear — and it is severe: self-join cardinality explodes
  11,192 → 42,521 (NaN-self-equality under polars/DuckDB join semantics differs from SQL NaN handling),
  distinct 88→89, sum → NaN. **Mechanism confirmed on real column structure; trigger absent in real data.**

---

## (E) NO-NaN CONTROL — ✅ Δ=0 (effect is NaN-specific)
(CSV: `control.csv`)
| case (in-memory pandas col) | null_count p/q | Δ distinct | Δ self-join | sum p→q |
|-----------------------------|----------------|-----------:|------------:|---------|
| finite + None (true null, NO NaN) | 2 / 2 | 0 | 0 | 4.0 → 4.0 |
| finite only | 0 / 0 | 0 | 0 | 9.0 → 9.0 |
| with NaN, **via `pl.from_pandas`** | 2 / 2 | 0 | 0 | 4.0 → 4.0 |

- No-NaN control passes: Δ=0. The effect is **NaN-specific**, not a generic round-trip artifact. ✅
- **Boundary condition discovered:** `pl.from_pandas(df)` defaults `nan_to_null=True`, so a NaN routed
  through pandas→polars-via-from_pandas COLLAPSES to null and matches pandas (Δ=0). The divergence ONLY
  fires when the NaN reaches the Arrow-native writer **as a genuine float value** (e.g. raw Python list,
  native polars/DuckDB computation like 0.0/0.0, or ingestion from a NaN-carrying source) — NOT when
  laundered through `from_pandas`. This further narrows the realistic trigger surface.

---

## SYNTHESIS — why WEAKEN, not GREEN
1. **Mechanism: confirmed.** null_count 2↔0; self-join 5↔9 (both readers); sum 3.0↔NaN (both readers).
   Readers do not coerce on read. No-NaN control Δ=0. The composition is exactly as the claim describes.
2. **Prevalence: ~0.** 0/244 real public float columns carry stored NaN. Real missingness is true-NULL.
   The PREREG it-matters threshold required "prevalence non-trivial"; measured prevalence is 0.0%.
3. **Trigger surface is narrow:** the divergence needs NaN-as-value reaching an Arrow-native writer; the
   common pandas↔polars path (`from_pandas`) collapses it; HF/`datasets`/Arrow pipelines store true-NULL.
4. **Writer-fingerprint sub-claim weakened:** `created_by` cannot distinguish pandas-via-pyarrow from
   pyarrow-direct (identical string, opposite NaN behavior).

Per PREREG honest-branch: "If real public float cols essentially never carry NaN (prevalence ~0) → WEAKEN
(real-but-rare)." That branch fired. **Disposition: WEAKEN.** Revival condition: if a corpus of genuinely
pandas-`to_parquet`-direct public files (or NaN-computing polars/Spark pipelines) shows non-trivial stored-NaN
prevalence, the seam becomes live and the claim could revive toward GREEN.

## ARTIFACTS
- PREREG.md (committed pre-run)
- composition.csv, control.csv, corpus_manifest.csv, prevalence_columns.csv, real_roundtrip.csv
- scripts on cli:devvm14382: ~/parquet_exp/exp_{A,A2,C,D,E}_*.py ; corpus in ~/parquet_exp/corpus/
