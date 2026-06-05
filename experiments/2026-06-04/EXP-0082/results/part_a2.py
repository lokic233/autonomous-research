import warnings, pandas as pd, pyarrow as pa, pyarrow.parquet as pq, polars as pl, duckdb, json
import pyarrow.compute as pc

DOMAIN = ["trace","debug","info","warn","error","fatal"]
# Ensure ALL levels present so extremes are unambiguous
df = pd.DataFrame({"sev": pd.Categorical(DOMAIN*3, categories=DOMAIN, ordered=True)})
df.to_parquet("ordered_full.parquet", engine="pyarrow")
sch = pq.read_schema("ordered_full.parquet")
print("sev type:", sch.field("sev").type, "| ordered=", sch.field("sev").type.ordered)
print("lexical sort:", sorted(DOMAIN))
print("domain order:", DOMAIN)
print("EXPECT pandas MIN/MAX (domain): trace / fatal")
print("EXPECT duckdb MIN/MAX (lexical): debug / warn\n")

res={}
pdf = pd.read_parquet("ordered_full.parquet", engine="pyarrow")
res["pandas_min"]=str(pdf["sev"].min()); res["pandas_max"]=str(pdf["sev"].max())
res["pandas_ordered"]=bool(pdf["sev"].cat.ordered)

with warnings.catch_warnings(record=True) as wl:
    warnings.simplefilter("always")
    con=duckdb.connect()
    r=con.execute("SELECT min(sev) mn,max(sev) mx FROM read_parquet('ordered_full.parquet')").fetchone()
    res["duckdb_min"],res["duckdb_max"]=str(r[0]),str(r[1])
    # also ORDER BY DESC LIMIT 1 to cross-check max semantics
    r2=con.execute("SELECT sev FROM read_parquet('ordered_full.parquet') ORDER BY sev DESC LIMIT 1").fetchone()
    res["duckdb_orderby_desc_top"]=str(r2[0])
    res["duckdb_warnings"]=[str(w.message) for w in wl]

with warnings.catch_warnings(record=True) as wl:
    warnings.simplefilter("always")
    plf=pl.read_parquet("ordered_full.parquet")
    res["polars_dtype"]=str(plf["sev"].dtype)
    res["polars_min"]=str(plf["sev"].min()); res["polars_max"]=str(plf["sev"].max())
    res["polars_warnings"]=[str(w.message) for w in wl]

tbl=pq.read_table("ordered_full.parquet")
try:
    res["pyarrow_minmax"]=str(pc.min_max(tbl["sev"]))
except Exception as e:
    res["pyarrow_minmax_error"]=f"{type(e).__name__}: {e}"

print(json.dumps(res,indent=2))
json.dump(res,open("part_a.json","w"),indent=2)
