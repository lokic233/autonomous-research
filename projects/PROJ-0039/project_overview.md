# PROJ-0039 — CROSS-RUNTIME data-systems seam: pandas-written ORDERED Categorical (Arrow ordered=1) silently loses its domain ordering in DuckDB/Polars -> MAX/MIN/ORDER BY flips to a WRONG category, no warning (NEW NON-OBVIOUS COUPLING)

12th cross-area coupling claim, textbook FIRST-GREEN (CLAIM-0059) structure, the 2nd cross-runtime green-candidate
(scout-T) — structural TWIN of PROJ-0038/CLAIM-0068 (scout-S) but DISTINCT: value-of-aggregate divergence (WHICH
category is max), not null-counting. The cross-runtime vein is NOT saturated (scout-Q/R proved within-language saturated;
scout-S/T both found greens sitting in the open).

## THE SEAM (independently-owned orgs across the LANGUAGE/RUNTIME boundary)
- WRITER/native-reader A = pandas 3.0.3 (via pyarrow 24.0.0): df.to_parquet of an ordered=True Categorical -> Arrow
  dictionary<values=string, indices=int8, ordered=1> (confirmed in schema). pandas reads back cat.ordered=True, computes
  MIN=trace/MAX=fatal (DOMAIN order). (For an UNORDERED categorical pandas REFUSES .min() — it treats ordering as undefined.)
- FOREIGN READER B = DuckDB 1.5.3 (primary, cleanest endpoint) + Polars 1.41.2 (secondary): read the SAME parquet and
  return MIN=debug/MAX=warn (LEXICOGRAPHIC), NO error/warning. Even pyarrow itself has no min_max kernel for an ordered
  dictionary (ArrowNotImplementedError) -> the ordering is honored by LITERALLY ONLY the pandas layer.
- WHY INDEPENDENT: pandas-dev (Python/Cython) writes; duckdb (C++ SQL) + pola-rs (Rust) consume — separate projects.
  Divergent defaults: A DEFINES + SERIALIZES a domain ordering; B DEFINES comparison as lexicographic for dictionary/
  categorical types + never reads the ordered bit.

## PRIMARY THESIS (public-measurable, falsifiable)
On a 6-level domain scale trace<debug<info<warn<error<fatal (lexical order differs), reading the IDENTICAL pandas-written
parquet: GROUPBY g MAX(sev) pandas-vs-DuckDB = 100.0% of 2000 groups DISAGREE; global MAX pandas=fatal vs DuckDB=warn;
global MIN pandas=trace vs DuckDB=debug; both readers ZERO warnings. NULL EXIT: plain-string column -> both lexical ->
100% AGREEMENT (isolates the ordered=1 flag).

## ★★ WHY IT CLEARS INCREMENTAL-COMPOSITION (false-by-doc gate PASSED both sides)
Neither endpoint predicts from its own side: pandas docs say ordered=True imposes an ordering but NOTHING about other
engines dropping it; DuckDB ENUM docs ("behaves exactly like VARCHAR") describe DuckDB's OWN lexical comparison, never
mention an incoming ordered=1 it ignores. NOWHERE does either side document the cross-runtime CONSEQUENCE (MAX returns a
different category by reader). = CLAIM-0059 structure.

## ★★ FRAMEWORK-ISSUE-TRACKER CHECK — BOTH runtimes (the CLAIM-0066 gate)
Searched apache/arrow + pandas-dev + duckdb + pola-rs issues/PRs. Closest = polars PR#23016 (Polars intentionally lexical)
= Polars' OWN internal design note, does NOT report reading a pandas ordered=1 parquet + flipping aggregates. NO issue/PR
on any of the 4 repos reports THIS seam. (Lead with DuckDB — no such design note, cleanest gate.)

## ★ COMPOSITION-VERIFICATION (ran it on real runtimes — not assumed)
Wrote ordered Categorical (ordered=1 confirmed in schema); read same file: pandas MIN/MAX=low/high; DuckDB=high/med;
Polars=high/med. Scaled to 100k rows / 6-level scale -> 100% of 2000 groups disagree on GROUPBY-MAX; both readers silent.
Control: plain-string -> 100% agreement.

## KILLER SCREEN (cleared — see CLAIM-0069)
#1 not metric-validity (value-of-aggregate correctness flip). #2 no seminal incumbent. #3 cross-runtime ordered-flag-drop
composition is novel. #4 currency = which-category-is-MAX (aggregate correctness). #5 real runtimes, verified. #6 the
"fix" (read the ordered bit / pass an explicit ENUM ordering) is exactly what DuckDB/Polars default does NOT do. #7
baseline = SAME reader+SQL, only writer-asserted ordering differs (strongest). #8 L0 CAN fail (plain-string control 100%
agree; alphabetical-domain -> no flip). #9 prod-framework prior-art on all 4 trackers clean. #10 public-measurable
(any domain-ordered category where lexical!=domain). #11 version-stable (ordered bit in Arrow/Parquet spec; DuckDB lexical
core SQL stable 1.x; Polars committed to lexical).

## HONEST RISK
Lead with DuckDB (Polars PR#23016 makes Polars partly-documented; DuckDB has no design note + no warning = cleanest).
Skeptic "ordering undefined for categoricals in SQL" -> rebuttal = the writer EXPLICITLY serialized non-default ordered=1
to assert a domain order, pandas honors it, the reader silently OVERRIDES with zero warning = genuine cross-runtime
correctness divergence (file metadata says one thing, reader does another). Distinct from PROJ-0038 (aggregate-value not
null-count). Scout-T self-rating GREEN.

## POSTURE
EXPAND/LIGHTWEIGHT: ONE sharp claim (CLAIM-0069), normal pipeline. L0 = the verified write-pandas/read-DuckDB MAX-flip on
real public domain-ordered categories + plain-string control + prevalence (how common are pandas-written ordered
categoricals in real parquet). Owner: orchestrator-r8-001.
