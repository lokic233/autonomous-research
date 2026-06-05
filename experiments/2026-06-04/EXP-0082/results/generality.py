import warnings, pandas as pd, pyarrow.parquet as pq, duckdb, polars as pl, json
scales={
 "severity":["trace","debug","info","warn","error","fatal"],
 "tshirt":["XS","S","M","L","XL","XXL"],
 "education":["primary","secondary","bachelor","master","phd"],
 "alphabetical_control":["alpha","bravo","charlie","delta","echo"],  # domain==lexical -> NO flip expected
}
out={}
con=duckdb.connect()
for name,dom in scales.items():
    df=pd.DataFrame({"sev":pd.Categorical(dom*2,categories=dom,ordered=True)})
    fn=f"g_{name}.parquet"; df.to_parquet(fn,engine="pyarrow")
    ordered=pq.read_schema(fn).field("sev").type.ordered
    pmin,pmax=str(df["sev"].min()),str(df["sev"].max())
    with warnings.catch_warnings(record=True) as wl:
        warnings.simplefilter("always")
        r=con.execute(f"SELECT min(sev),max(sev) FROM read_parquet('{fn}')").fetchone()
        dwarn=[str(w.message) for w in wl]
    dmin,dmax=str(r[0]),str(r[1])
    lex_min,lex_max=sorted(dom)[0],sorted(dom)[-1]
    out[name]={"ordered_flag":bool(ordered),"domain":dom,
               "pandas_min":pmin,"pandas_max":pmax,
               "duckdb_min":dmin,"duckdb_max":dmax,
               "expected_lexical_min":lex_min,"expected_lexical_max":lex_max,
               "duckdb_is_lexical":(dmin==lex_min and dmax==lex_max),
               "max_flipped":(pmax!=dmax),"duckdb_warnings":dwarn}
# unordered categorical: pandas should refuse .min()
dfu=pd.DataFrame({"sev":pd.Categorical(scales["severity"]*2,categories=scales["severity"],ordered=False)})
try:
    _=dfu["sev"].min(); refused=False
except TypeError as e:
    refused=True
out["unordered_pandas_refuses_min"]=refused
print(json.dumps(out,indent=2))
json.dump(out,open("generality.json","w"),indent=2)
