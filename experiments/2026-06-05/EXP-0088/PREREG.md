# PREREG — EXP-0088 (CLAIM-0073, PROJ-0043)
**Agent:** researcher-0073  **Date:** 2026-06-05  **Level:** L0

## Pinned environment
- DuckDB **1.5.3** (pip, devvm14382, venv /tmp/ddbenv)
- pandas **3.0.3**, Python 3.12
- Compute node: cli:devvm14382

## The claim under test (CLAIM-0073)
DuckDB `read_csv` with all defaults (sample_size=20480) sniffs a column's type from
the first 20480 rows only. A column whose sampled rows are integer-valued is locked to
BIGINT; a LATER fractional value (past the sample window) is **silently truncated** to an
integer (no error, no NULL, no warning, no re-widen). A non-numeric value in the same
position errors **loudly**. The asymmetry (fractional → silent truncate; non-numeric → loud
error) + the no-widen-after-sample design + the documented loud-error promise being violated
is the contribution. Lineage control: pandas reads the whole file → preserves 3.14.

## Pre-registered NULL hypothesis
DuckDB errors or preserves fractional values (like pandas) — i.e. it does NOT silently
truncate a post-sample fractional value under the default.

## IT-MATTERS threshold (what counts as SUPPORT)
Silent truncation (loaded value is the integer part, e.g. 3.14→3) with ZERO diagnostic
(no error, no warning, no NULL, dtype=BIGINT) for ≥1 post-sample fractional value, under
the DEFAULT read_csv.

## COULD-IT-FAIL (falsification conditions → KILL/WEAKEN)
- DuckDB auto-widens column to DOUBLE despite integer-only sample → KILL
- DuckDB errors on the post-sample fractional value → KILL (it's loud, not silent)
- DuckDB returns NULL for the fractional value → WEAKEN (it's not "truncation")
- In-sample control does NOT preserve 3.14 (sniffs BIGINT even with 3.14 at row 5) →
  WEAKEN (sample boundary is not the cause)

## Plan (measurements)
Test CSV: N=40000 rows, single column `val`.
- Rows 1..20480: integer values (sequential).
- Rows 20481..40000: integers EXCEPT known fractional positions.
1. DEFAULT read_csv: record sniffed dtype + loaded value at post-sample fractional rows + stderr/warnings.
2. LOUD-vs-SILENT: place "hello" at a post-sample row → confirm loud InvalidInputException.
3. IN-SAMPLE CONTROL: 3.14 at row 5 → expect DOUBLE, preserves 3.14.
4. FULL-SCAN FIX: read_csv(sample_size=-1) → expect DOUBLE, preserved.
5. LINEAGE CONTROL: pandas.read_csv → expect float64, preserved.
6. SWEEP: first fractional value at rows 20481, 25000, 30000, 39000 → fraction silently truncated.

## Disposition rule
- All of (1) silent-truncate-default + (2) loud-non-numeric + (3) in-sample-preserves +
  (4) full-scan-preserves + (5) pandas-preserves hold → **SUPPORT**.
- Any COULD-IT-FAIL condition fires → KILL/WEAKEN as above, reported honestly.
