# PRE-REGISTRATION — EXP-0081 (CLAIM-0068)

**Researcher:** researcher-0068  **Parent:** orchestrator-r8-001  **Project:** PROJ-0038
**Date:** 2026-06-04  **Level:** 0 (CPU, multi-runtime)
**Status:** committed BEFORE running.

## THE CLAIM (CLAIM-0068)
A float column with IEEE-754 NaN written to Parquet by pandas (`DataFrame.to_parquet(engine="pyarrow")`)
silently stores NaN as NULL (statistics.null_count>0, NaN values gone). Any Arrow-native writer
(polars/Rust arrow-rs, DuckDB C++, pyarrow-direct) stores NaN-as-VALUE (null_count=0). So the SAME
reader + SAME query gives different correctness depending ONLY on which runtime WROTE the file:
count(distinct k) 2<->3, self-join using(k) 5<->9 rows, sum(v) finite<->NaN.

## NOVELTY FRAMING (what this is NOT)
NOT "pandas treats NaN as NA" (folklore, in-memory). The NEW coupling: file PROVENANCE (which runtime
wrote the parquet) silently flips a FOREIGN-runtime reader's JOIN/GROUP-BY/aggregate correctness — a
consequence documented in neither runtime's docs nor either issue tracker.

## PINNED VERSIONS (cli:devvm14382, venv ~/pq_venv)
- python 3.12.13+meta
- pandas 3.0.3
- pyarrow 24.0.0
- polars 1.41.2
- duckdb 1.5.3
- numpy 2.4.6

## PRE-REGISTERED NULL HYPOTHESIS
H0: Delta = 0 for all files — the writer runtime is irrelevant; null_count and all aggregates are identical
regardless of which runtime wrote the parquet.

## IT-MATTERS THRESHOLD (what would SUPPORT the claim)
1. Composition verified BOTH directions: pandas-written float-NaN col -> null_count=2 (NaN->NULL);
   polars-written AND duckdb-written IDENTICAL col -> null_count=0 (NaN-as-value).
2. SAME reader (DuckDB AND polars), SAME query, files differ ONLY by writer -> aggregates DIFFER:
   count(distinct k) = 2 (pandas) vs 3 (Arrow-native); self-join using(k) = 5 vs 9 rows;
   sum(v) over single-NaN col = finite (3.0) vs NaN.
3. PREVALENCE non-trivial: a non-negligible FRACTION of real public parquet float columns carry
   actual NaN values (not already-true-null). If prevalence ~0 -> real-but-rare -> WEAKEN.

## DISPOSITIONS
- SUPPORT: composition verified (null_count 2<->0) + aggregate-flip on both readers + prevalence non-trivial
  (NaN-bearing float cols are NOT vanishingly rare) -> submit to committee.
- WEAKEN (real-but-rare): mechanism verified but NaN-bearing float columns are vanishingly rare in real
  public parquet (prevalence ~0).
- KILL: pandas does NOT collapse NaN->null on pinned versions, OR readers coerce NaN->null on read
  (erasing the divergence), OR composition does not reproduce.

## EXPERIMENT PLAN
### (A) COMPOSITION RE-VERIFICATION (re-confirm scout-S, both directions)
Input float col k=[1.0, NaN, 2.0, NaN, 1.0] + a v column.
- (a) pandas DataFrame.to_parquet(engine="pyarrow") -> read parquet file metadata via pyarrow -> assert
  column k statistics.null_count == 2.
- (b) write IDENTICAL logical col via polars write_parquet AND via DuckDB COPY TO -> assert null_count == 0.
- (c) read BOTH files with SAME reader (DuckDB AND polars): count(distinct k), self-join using(k), sum(v).
  Assert pandas-file: distinct=2, self-join=5, sum=3.0; arrow-file: distinct=3, self-join=9, sum=NaN.
Record byte-level null_count from parquet footer.

### (B) READER-DEFAULT CHECK (control on coercion)
Confirm reader default does NOT coerce NaN->null on read on pinned versions. Read the Arrow-native
(null_count=0, NaN-bearing) file and confirm the reader still SEES NaN (polars: is_nan count; DuckDB:
isnan count) rather than silently nulling it. If a reader coerces, the seam narrows — report honestly.

### (C) PREVALENCE MEASUREMENT (load-bearing)
Scan a corpus of REAL public parquet datasets (HuggingFace datasets that ship parquet; public data lakes
e.g. NYC-taxi). For each FLOAT column:
- read parquet metadata null_count, and SCAN the data for actual NaN values (count NaN).
- Classify each float column: (i) carries NaN values (seam LIVE), (ii) only true-null no NaN (seam moot),
  (iii) writer-provenance fingerprint (a pandas-written float col should show ZERO stored NaN; an
  Arrow-native writer can show stored NaN).
- Report: FRACTION of real public float columns carrying NaN; can we fingerprint pandas-vs-Arrow writers?

### (D) AGGREGATE-FLIP on REAL data
Take real public parquet float columns. For NaN-bearing columns (or, if none found at meaningful rate,
INJECT NaN into a real column's structure to demonstrate the MECHANISM — clearly labeled as injection,
NOT used to inflate prevalence): round-trip read->pandas-to_parquet vs read->polars-write_parquet, recompute
count(distinct)/sum/self-join under DuckDB -> show Delta!=0.

### (E) NO-NaN CONTROL (effect must be NaN-specific)
Float column with finite values + true nulls (NO NaN). Round-trip pandas vs polars -> Delta MUST be 0.
Confirms the divergence is NaN-specific, not a generic round-trip artifact.

## HONEST BRANCHES
- If pandas does NOT collapse NaN->null on pinned versions -> KILL.
- If readers coerce NaN->null on read (erase divergence) -> seam narrows / KILL.
- If real public float cols essentially never carry NaN (prevalence ~0) -> WEAKEN (real-but-rare).
- Do NOT inject NaN at unrealistic rates to inflate prevalence. Measure REAL rate first; injection only
  to demonstrate mechanism on real column structure, clearly labeled.

## DELIVERABLES
PREREG.md (this), RESULTS.md, CSVs (composition, prevalence-per-column, aggregate-flip, control).
