import warnings, pandas as pd, pyarrow as pq_mod, pyarrow.parquet as pq, duckdb, polars as pl, numpy as np, json, csv

DOMAIN=["trace","debug","info","warn","error","fatal"]
np.random.seed(7)
N=100_000; NG=2000
g=np.random.randint(0,NG,N)
sev_vals=np.random.choice(DOMAIN,N)

# ----- ORDERED CATEGORICAL FILE -----
df=pd.DataFrame({"g":g,"sev":pd.Categorical(sev_vals,categories=DOMAIN,ordered=True)})
df.to_parquet("scale_ordered.parquet",engine="pyarrow")
print("schema sev ordered:",pq.read_schema("scale_ordered.parquet").field("sev").type.ordered)

# pandas groupby max (domain-aware)
pdf=pd.read_parquet("scale_ordered.parquet",engine="pyarrow")
pmax=pdf.groupby("g",observed=True)["sev"].max().astype(str)

# duckdb groupby max (lexical) on identical file
con=duckdb.connect()
with warnings.catch_warnings(record=True) as wl:
    warnings.simplefilter("always")
    dmax_df=con.execute("SELECT g, max(sev) mx FROM read_parquet('scale_ordered.parquet') GROUP BY g").df()
    duck_warns=[str(w.message) for w in wl]
dmax=dmax_df.set_index("g")["mx"].astype(str)

# align
joined=pd.DataFrame({"pandas":pmax,"duckdb":dmax}).dropna()
disagree=(joined["pandas"]!=joined["duckdb"]).sum()
total=len(joined)
print(f"\nORDERED CATEGORICAL groupby-max: {disagree}/{total} groups DISAGREE = {100*disagree/total:.2f}%")
print("duckdb warnings during groupby:",duck_warns)
joined.reset_index().to_csv("groupby_ordered.csv",index=False)

# ----- PLAIN STRING CONTROL (same logical data) -----
df_str=pd.DataFrame({"g":g,"sev":pd.Series(sev_vals,dtype="object")})
df_str.to_parquet("scale_string.parquet",engine="pyarrow")
print("\nstring file sev type:",pq.read_schema("scale_string.parquet").field("sev").type)
pdf_s=pd.read_parquet("scale_string.parquet",engine="pyarrow")
pmax_s=pdf_s.groupby("g",observed=True)["sev"].max().astype(str)  # lexical for object
dmax_s=con.execute("SELECT g,max(sev) mx FROM read_parquet('scale_string.parquet') GROUP BY g").df().set_index("g")["mx"].astype(str)
plf_s=pl.read_parquet("scale_string.parquet")
plmax_s=plf_s.group_by("g").agg(pl.col("sev").max()).to_pandas().set_index("g")["sev"].astype(str)
j2=pd.DataFrame({"pandas":pmax_s,"duckdb":dmax_s,"polars":plmax_s}).dropna()
dis_pd=(j2["pandas"]!=j2["duckdb"]).sum()
dis_pl=(j2["pandas"]!=j2["polars"]).sum()
print(f"PLAIN STRING control pandas-vs-duckdb: {dis_pd}/{len(j2)} disagree = {100*dis_pd/len(j2):.2f}%")
print(f"PLAIN STRING control pandas-vs-polars: {dis_pl}/{len(j2)} disagree = {100*dis_pl/len(j2):.2f}%")
j2.reset_index().to_csv("groupby_string.csv",index=False)

out={"ordered_disagree":int(disagree),"ordered_total":int(total),
     "ordered_disagree_pct":round(100*disagree/total,2),"duckdb_groupby_warnings":duck_warns,
     "string_pd_duck_disagree":int(dis_pd),"string_pd_pl_disagree":int(dis_pl),
     "string_total":int(len(j2)),
     "string_pd_duck_agree_pct":round(100*(1-dis_pd/len(j2)),2),
     "string_pd_pl_agree_pct":round(100*(1-dis_pl/len(j2)),2)}
json.dump(out,open("part_c.json","w"),indent=2)
print("\n",json.dumps(out,indent=2))
