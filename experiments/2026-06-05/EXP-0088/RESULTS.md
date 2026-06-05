# RESULTS — EXP-0088 (CLAIM-0073, PROJ-0043)
**Agent:** researcher-0073  **Date:** 2026-06-05  **Disposition: SUPPORT** ✅

## Pinned environment
| | |
|---|---|
| DuckDB | **v1.5.3** (`14eca11bd9`, "Variegata"), pip, venv `/tmp/ddbenv` |
| pandas | 3.0.3 |
| Python | 3.12.13 |
| Node | cli:devvm14382 |
| Test data | N=40000-row single-column (`val`) CSV; rows 1..20480 integer, fractional `3.14` planted at known post-sample rows |

## NOVELTY (lead result) — the LOUD-vs-SILENT ASYMMETRY
For the **exact same column** locked to BIGINT by the default 20480-row sniff, DuckDB
treats two out-of-vocabulary post-sample values in **opposite** ways:

| post-sample value at row 30000 | DuckDB 1.5.3 behavior |
|---|---|
| `"hello"` (non-numeric) | **LOUD**: `ConversionException` — stops, throws, even prints the fix (`sample_size=-1`) |
| `3.14` (fractional) | **SILENT**: returns `3`, dtype BIGINT, `null_count=0`, **zero** stderr/warning/NULL |

This is NOT folklore ("sampling picks the wrong type"). The contribution is the
**asymmetry by value type** (non-numeric → loud error; fractional → silent integer
truncation) composed with the **no-widen-after-sample** design and a **documented-promise
violation**: the sniffer authors promise "if any structural errors are encountered, the
scanner will immediately stop and throw the error" — yet a fractional value past the
sample is silently rounded, no error. The loud-error message itself proves DuckDB *can*
diagnose a bad post-sample value — it just chooses not to for floats.

## Measurement table

| # | Test | Sniffed dtype | Loaded value (CSV had `3.14`) | Diagnostic |
|---|------|--------------|------------------------------|-----------|
| 1 | **DEFAULT** `read_csv`, 3.14 @ row 30000 | `BIGINT` | **`3`** | none (stderr empty, null_count=0) |
| 2 | **LOUD** `"hello"` @ row 30000 | `BIGINT` | — (errors) | **`ConversionException` on line 30001** |
| 3 | **IN-SAMPLE CONTROL** 3.14 @ row 5 | `DOUBLE` | `3.14` ✓ | n/a (preserved) |
| 4 | **FULL-SCAN FIX** `sample_size=-1` | `DOUBLE` | `3.14` ✓ | n/a (preserved) |
| 5 | **LINEAGE CONTROL** `pandas.read_csv` | `float64` | `3.14` ✓ | n/a (preserved) |

## Sweep — position independence (DEFAULT read_csv)

| first fractional row | dtype | loaded | no diagnostic | silently truncated |
|---|---|---|---|---|
| 20481 | BIGINT | 3 | ✓ | ✓ |
| 25000 | BIGINT | 3 | ✓ | ✓ |
| 30000 | BIGINT | 3 | ✓ | ✓ |
| 39000 | BIGINT | 3 | ✓ | ✓ |

**4/4 = 100%** of post-sample fractional values silently truncated. The truncation is a
function of being *past the sample boundary*, not a specific row.

## Causation chain (proves the sample boundary is the knob)
- **In-sample (row 5) → DOUBLE, preserves 3.14.** Same value, inside window → correct.
- **Post-sample (rows 20481–39000) → BIGINT, truncates to 3.** Same value, outside window → silent loss.
- **`sample_size=-1` (full scan) → DOUBLE, preserves 3.14.** Flipping the single default knob fixes it.
- The ONLY variable is the position relative to `sample_size=20480`. ⇒ the default `sample_size` silently sets a data-fidelity correctness property.

## Lineage control (proves DuckDB-specific novelty)
`pandas.read_csv` reads the whole file → infers `float64` → preserves `3.14`. The mature
lineage does NOT exhibit this. DuckDB's bounded-sample + non-widening + silent integer-cast
composition is genuinely its own behavior, not inherited.

## Route confirmation
Identical silent truncation through **`read_csv`**, **`read_csv_auto`**, and
**`CREATE TABLE AS SELECT ... read_csv`** — it is the default ingest path, not an artifact
of the relational API.

## Pre-registered NULL — REJECTED
NULL was "DuckDB errors or preserves fractional values (like pandas)." Reality: it
**silently truncates** (3.14→3, dtype BIGINT, no error/NULL/warning) for every tested
post-sample position. None of the COULD-IT-FAIL falsifiers fired (no auto-widen, no error,
no NULL; in-sample control preserved as expected).

## IT-MATTERS threshold — MET
Silent truncation with zero diagnostic for ≥1 (in fact 4/4) post-sample fractional values,
under the default `read_csv`. Trigger is a generic file shape (integer-valued early rows,
fractional later — IDs/counts then measurements/prices; sorted/append-only logs; sparse decimals).

## Disposition: **SUPPORT** — committee-ready
All five pillars hold: silent-truncate-default + loud-non-numeric + in-sample-preserves +
full-scan-preserves + pandas-preserves. Rigorously reproduced on pinned DuckDB 1.5.3.

## Artifacts
- `PREREG.md` (this dir) — pre-registered before any run.
- `summary.json` — machine-readable results.
- `verify_output.txt` — full loud-error text + CREATE TABLE / read_csv_auto route confirmation + version banner.
- `run.py` — deterministic reproducer (regenerates all test CSVs).
- Raw CSVs + scripts on cli:devvm14382: `/tmp/exp0088/{m1_default.csv, m2_loud.csv, m3_insample.csv, sweep_*.csv, run.py, verify.py, summary.json, exp0088_artifacts.tar.gz}`.
