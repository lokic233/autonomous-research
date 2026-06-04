# PROJ-0038 — CROSS-RUNTIME data-systems seam: pandas-written Parquet stores NaN as NULL while every Arrow-native writer stores NaN-as-value -> file PROVENANCE silently flips a foreign-runtime reader's JOIN/GROUP-BY/aggregate correctness (NEW NON-OBVIOUS COUPLING)

11th cross-area coupling claim, textbook FIRST-GREEN (CLAIM-0059) structure, the CONVERGENT PIVOT both scout-Q + scout-R
recommended (within-language frontier saturated) and scout-S validated end-to-end across 3 real runtimes. The FIRST claim
this run to clear ALL FOUR gates with empirical write-A/read-B verification.

## THE SEAM (FOUR independently-owned orgs, across the LANGUAGE/RUNTIME boundary)
- WRITER A = pandas 3.0.3 + pyarrow 24.0.0 (Python/C++): DataFrame.to_parquet(engine=pyarrow). pyarrow from_pandas
  applies pandas missing-value semantics -> float NaN treated as NULL. VERIFIED: written file statistics.null_count=2 for
  a 2-NaN column (NaN values GONE, replaced by Parquet definition-level NULLs).
- WRITER B = polars 1.41.2 (Rust/arrow-rs) write_parquet + DuckDB 1.5.3 (C++) COPY TO: write the IDENTICAL logical NaNs
  as NaN VALUES -> null_count=0. VERIFIED directly.
- WHY INDEPENDENT: pandas-dev / pola-rs / duckdb / apache-arrow-rs = 4 separate orgs/repos/cadences. pandas UNIQUELY
  conflates NaN==missing (NumPy legacy); every Arrow-native writer keeps NaN!=null (Arrow's validity bitmap is distinct
  from the NaN bit pattern). The canonical lakehouse seam: a Python pipeline emits Parquet; a Rust/DuckDB service reads it.

## PRIMARY THESIS (public-measurable, falsifiable, integer-valued)
Same reader + same SQL, opposite correctness, SOLELY from writer runtime (verified, 2 independent readers DuckDB+polars):
count(distinct k) = 2 (pandas-written) vs 3 (polars/duckdb); self-join using(k) = 5 vs 9 rows; sum(v) single-NaN col =
3.0 (finite) vs NaN. NULL EXIT: float cols with NO NaN (finite + true nulls) -> Delta=0 (NaN-specific).

## ★★ WHY IT CLEARS INCREMENTAL-COMPOSITION (false-by-documentation gate PASSED both sides)
pandas side documents only its OWN in-memory "NaN means NA"; to_parquet docs do NOT say the FILE gets NULLs where you
wrote NaN, nor that another writer differs. Reader side (polars Missing-data guide, DuckDB) documents only its OWN
in-memory NaN-vs-null model; polars nan_to_null is the in-memory from_pandas path, NOT the parquet writer/reader. NEITHER
endpoint predicts the divergence from its own side; the cross-writer file-provenance -> foreign-reader-aggregate-flip is
in NOBODY's docs. = CLAIM-0059 structure (NFKC vs NFC each correct on its own side; the coupling consequence emergent).

## ★★ FRAMEWORK-ISSUE-TRACKER CHECK — BOTH runtimes (the CLAIM-0066 gate)
Searched apache/arrow + pandas-dev (pandas->parquet NaN->null cross-writer) + pola-rs/polars + duckdb (pandas-written
parquet NaN read as null / count / sum inconsistency). ALL hits are the opposite/known direction (nullable-int Hive
errors, fastparquet NaN->int, to_pandas Int64->float64). NO issue/PR reports the cross-writer NaN-vs-null Parquet
correctness seam. (This is the gate that RED'd CLAIM-0066 — here it PASSES on both trackers.)

## ★ COMPOSITION-VERIFICATION (ran it, both directions, 2 readers — not assumed)
Live on cli:devvm14382: input k=[1.0,NaN,2.0,NaN,1.0]. pandas-written null_count=2 -> DuckDB count(distinct)=2, self-join
5 rows, sum=3.0, polars GROUP BY -> null group. polars/duckdb-written null_count=0 -> count(distinct)=3, self-join 9 rows,
sum=NaN, GROUP BY -> NaN group. Verified on TWO independent readers (DuckDB C++, polars Rust) -> not a single-reader quirk.

## NOT-FOLKLORE
pandas in-memory NaN=NA is famous. The file-provenance -> foreign-runtime-reader categorically-different-aggregate
consequence (JOIN cardinality 5<->9, distinct 2<->3 under an IDENTICAL reader) is in no doc/README/blog/tracker found.
Folklore = the in-memory model; the SEAM = on-disk bytes + a foreign reader.

## KILLER SCREEN (cleared — see CLAIM-0068)
#1 not metric-validity (a correctness divergence). #2 no seminal incumbent for the cross-writer seam. #3 the cross-runtime
composition (pandas-NaN->null x Arrow-native-NaN-value) is novel; the individual NaN-vs-null models are not the claim.
#4 currency = downstream aggregate/JOIN correctness (integer-valued). #5 real: pandas/polars/duckdb as-shipped, verified.
#6 the "fix" (write NaN-as-value / coerce on read) is exactly what pandas's default does NOT do + neither side wires.
#7 baseline = the SAME reader+SQL, only writer differs (strongest). #8 L0 CAN fail (no-NaN control Delta=0; low prevalence
shrinks blast radius). #9 prod-framework prior-art on BOTH trackers clean. #10 public-measurable (null_count+NaN-presence
fingerprints the writer; corpus scan quantifies at-risk files). #11 version-stable (from_pandas default persists 1.x->3.x;
polars 1.41 read stabilized toward NaN-preservation, sharpening it).

## HONEST RISK
PREVALENCE (how often real float cols carry NaN vs already-null) = the main risk -> the L0 MEASURES it (corpus scan), turning
it into a number not an assumption. Secondary: "NaN-as-NA is famous" -> rebuttal = the file-provenance->foreign-reader
aggregate flip is the novel undocumented measurable consequence. Scout-S self-rating GREEN 8/10.

## POSTURE
EXPAND/LIGHTWEIGHT: ONE sharp claim (CLAIM-0068), normal pipeline. L0 = corpus scan (prevalence) + the verified
write-A/read-B aggregate-flip on real public parquet. Owner: orchestrator-r8-001.
