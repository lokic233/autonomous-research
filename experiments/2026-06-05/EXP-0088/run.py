# EXP-0088 reproducer (CLAIM-0073). DuckDB 1.5.3, pandas 3.0.3, Python 3.12.
# Run on a venv with `pip install duckdb pandas`. Deterministically regenerates all test CSVs.
import duckdb, pandas as pd, sys, io, contextlib, csv, json
OUT = "."
N = 40000; SAMPLE = 20480  # DuckDB default sample_size
def make_csv(path, frac_positions, frac_value="3.14", nonnum_positions=None, inrow5=None):
    nonnum_positions = nonnum_positions or {}
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["val"])
        for r in range(1, N+1):
            if inrow5 is not None and r == 5: w.writerow([inrow5])
            elif r in nonnum_positions: w.writerow([nonnum_positions[r]])
            elif r in frac_positions: w.writerow([frac_value])
            else: w.writerow([r])
def kw_str(kw):
    if not kw: return ""
    return "".join((f", {k}='{v}'" if isinstance(v,str) else f", {k}={v}") for k,v in kw.items())
def val_at(path, datarow, **kw):
    con = duckdb.connect()
    q = f"SELECT val FROM (SELECT row_number() OVER () rn, val FROM read_csv('{path}'{kw_str(kw)})) WHERE rn={datarow}"
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rel = con.sql(f"SELECT * FROM read_csv('{path}'{kw_str(kw)})"); dt = str(rel.types[0])
        res = con.sql(q).fetchall()
    return (res[0][0] if res else None), dt, err.getvalue()
# [1] DEFAULT, [2] LOUD, [3] IN-SAMPLE, [4] FULL-SCAN, [5] PANDAS, [6] SWEEP — see RESULTS.md
