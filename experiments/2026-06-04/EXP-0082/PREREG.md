# PRE-REGISTRATION — EXP-0082 (CLAIM-0069)
researcher-0069 / PROJ-0039 / level 0 / CPU multi-runtime
Committed BEFORE running. Compute: cli:devvm14382 (venv). ROS state: cli:dengcchi-mac.

## PINNED VERSIONS (installed, confirmed)
- pandas 3.0.3
- pyarrow 24.0.0
- polars 1.41.2
- duckdb 1.5.3
- Python 3.12.13+meta

## THE CLAIM
A pandas-written ORDERED Categorical -> Parquet Arrow dictionary<ordered=1>. pandas honors the
domain order for MIN/MAX/sort; DuckDB (primary) + Polars (secondary) SILENTLY drop the ordered flag
-> lexicographic comparison -> MAX/MIN/GROUPBY-MAX flips to a WRONG category, NO warning.
LEAD WITH DUCKDB (cleanest — Polars PR#23016 makes Polars partly-documented).

## COMPOSITION RE-VERIFICATION (re-confirm scout-T)
(a) Write pd.Categorical categories=[trace,debug,info,warn,error,fatal], ordered=True, to_parquet(engine=pyarrow).
    Confirm Arrow schema shows dictionary<...ordered=1> via pq.read_schema.
(b) Read SAME file:
    - pandas MIN/MAX -> EXPECT domain: trace / fatal
    - DuckDB MIN/MAX -> EXPECT lexicographic: debug / warn, with ZERO warning (warnings.catch_warnings)
    - Polars MIN/MAX -> record
(c) Scale ~100k rows, GROUPBY g, MAX(sev) pandas vs DuckDB on identical file -> measure % groups disagree.

## PLAIN-STRING CONTROL (load-bearing — isolates the ordered=1 flag)
Same logical data as a PLAIN STRING column (not categorical) -> pandas, DuckDB, Polars MAX ALL lexicographic
-> 100% AGREEMENT. MUST hold. If it does NOT hold, the divergence is not caused by ordered=1 -> weaken/kill.

## PREVALENCE SCAN (blast-radius — load-bearing)
Scan real public parquet (HuggingFace datasets / public data lakes). For each dictionary/categorical column:
read Arrow schema, check ordered=1, and whether domain order != lexical order.
Report: fraction of real public categorical-parquet columns carrying ordered=1 with a non-alphabetical domain.
HONEST: may be ~0 (most parquet categoricals are unordered/alphabetical). Report the REAL number.

## PRE-REGISTERED NULL
If DuckDB honored ordered=1 -> MAX agreement = 100% (no divergence).

## IT-MATTERS THRESHOLD
(1) On a non-alphabetical domain scale, GROUPBY-MAX pandas-vs-DuckDB disagreement > 0% (scout-T saw 100%); AND
(2) prevalence of ordered=1 non-alphabetical categoricals in real parquet is non-trivial.

## COULD-IT-FAIL (honest branches)
- DuckDB/Polars on pinned versions DO honor ordered=1 -> report honestly (null met).
- A reader WARNS -> weakens silent-flip framing.
- Real public parquet essentially never has ordered=1 non-alphabetical categoricals (prevalence ~0)
  -> real-but-rare -> WEAKEN.
- Do NOT use only adversarial hand-built scale to claim prevalence — measure the REAL rate.

## DISPOSITION RULE
SUPPORT iff: schema ordered=1 confirmed AND DuckDB MAX flips with zero warning AND groupby disagreement>0%
AND plain-string control 100% agreement AND prevalence non-trivial.
If prevalence ~0 OR any verification breaks -> honest WEAKEN/KILL.
