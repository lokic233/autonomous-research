import numpy as np, pandas as pd, pyarrow.parquet as pq
from sklearn.preprocessing import StandardScaler
import tempfile, os, csv, warnings, sys, platform
warnings.simplefilter("ignore")  # we record finiteness ourselves; numpy overflow warnings expected

OUT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(OUT, "results")
os.makedirs(RES, exist_ok=True)

VERS = dict(python=platform.python_version(), pandas=pd.__version__, numpy=np.__version__,
            pyarrow=pq.pa.__version__, sklearn=__import__("sklearn").__version__)
print("VERSIONS:", VERS)

def roundtrip_parquet(arr, dtype):
    """cast arr to dtype, write parquet, read back. return (reloaded_series, survived_bool, schema_str)"""
    a = arr.astype(dtype)
    df = pd.DataFrame({"feat": a})
    fn = tempfile.mktemp(suffix=".parquet")
    df.to_parquet(fn, engine="pyarrow")
    t = pq.read_table(fn)
    schema = str(t.schema.field("feat").type)
    df2 = pd.read_parquet(fn, engine="pyarrow")
    os.remove(fn)
    survived = (df2["feat"].dtype == np.dtype(dtype))
    return df2["feat"], survived, schema

def fin(x):
    try:
        return "finite" if np.isfinite(float(x)) else ("inf" if np.isinf(float(x)) else "nan")
    except Exception:
        return "err"

def relerr(val, gt):
    try:
        v=float(val)
        if not np.isfinite(v): return ""
        if gt==0: return abs(v)
        return abs(v-gt)/abs(gt)
    except Exception:
        return ""

def measure(series, gt):
    """return dict of the three tools' mean + std results"""
    sv = series.values  # numpy array of the stored dtype
    out = {}
    # pandas
    pm = series.mean()
    out["pandas_mean"]=float(pm); out["pandas_mean_state"]=fin(pm); out["pandas_mean_relerr"]=relerr(pm,gt)
    # numpy
    nm = sv.mean()
    out["numpy_mean"]=float(nm); out["numpy_mean_state"]=fin(nm); out["numpy_mean_relerr"]=relerr(nm,gt)
    # sklearn
    sc = StandardScaler().fit(sv.reshape(-1,1))
    skm = sc.mean_[0]
    out["sklearn_mean"]=float(skm); out["sklearn_mean_state"]=fin(skm); out["sklearn_mean_relerr"]=relerr(skm,gt)
    out["gt_mean"]=gt
    # distinct-answer count (round finite to compare; treat non-finite as distinct categories)
    def canon(v,st):
        if st!="finite": return st
        return round(float(v),3)
    answers = {canon(out["pandas_mean"],out["pandas_mean_state"]),
               canon(out["numpy_mean"],out["numpy_mean_state"]),
               canon(out["sklearn_mean"],out["sklearn_mean_state"])}
    out["distinct_mean_answers"]=len(answers)
    # std arm (bonus)
    pstd = series.std()  # pandas ddof=1
    nstd = sv.std()      # numpy ddof=0
    skstd = np.sqrt(sc.var_[0])  # sklearn ddof=0 variance
    out["pandas_std"]=float(pstd); out["pandas_std_state"]=fin(pstd)
    out["numpy_std"]=float(nstd); out["numpy_std_state"]=fin(nstd)
    out["sklearn_std"]=float(skstd); out["sklearn_std_state"]=fin(skstd)
    return out

# ============ SWEEP (synthetic) ============
Ns = [100, 656, 1000, 10000, 65504, 100000, 1_000_000]
mags = [1.0, 100.0, 1000.0]
rows=[]
for storage in ["float16","float32","float64"]:
    for N in Ns:
        for mag in mags:
            base = np.full(N, mag, dtype=np.float64)  # constant -> exact gt mean = mag
            gt = mag
            series, survived, schema = roundtrip_parquet(base, storage)
            m = measure(series, gt)
            r = dict(storage=storage, N=N, magnitude=mag, parquet_survived=survived, parquet_schema=schema, **m)
            rows.append(r)
            tag = f"[{storage} N={N} mag={mag}]"
            print(f"{tag} pandas={m['pandas_mean_state']}({m['pandas_mean']:.4g}) "
                  f"numpy={m['numpy_mean_state']}({m['numpy_mean']:.4g}) "
                  f"sklearn={m['sklearn_mean_state']}({m['sklearn_mean']:.6g}) distinct={m['distinct_mean_answers']}")

fields = list(rows[0].keys())
with open(os.path.join(RES,"sweep_synthetic.csv"),"w",newline="") as f:
    w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
print("\nwrote sweep_synthetic.csv:", len(rows), "rows")

# ============ REAL PUBLIC DATASET ARM ============
from sklearn.datasets import fetch_california_housing
ds = fetch_california_housing(as_frame=True)
dfreal = ds.frame
print("\n=== REAL: California housing feature magnitudes ===")
realrows=[]
feats = list(ds.feature_names) + [("MedInc_x100","derived")]
for feat in ds.feature_names:
    col = dfreal[feat].values.astype(np.float64)
    gt = col.mean()
    realrows.append((feat, col, gt))
# derived magnitude-100 feature on REAL distribution
col = (dfreal["MedInc"].values.astype(np.float64))*100.0
realrows.append(("MedInc_x100", col, col.mean()))

real_out=[]
for name, col, gt in realrows:
    N=len(col)
    series, survived, schema = roundtrip_parquet(col, "float16")
    m = measure(series, gt)
    mn, mx = float(col.min()), float(col.max())
    r=dict(feature=name, N=N, data_min=mn, data_max=mx, gt_mean=gt,
           is_mag_ge_100=(abs(gt)>=100 or mx>=100),
           parquet_survived=survived, **{k:v for k,v in m.items() if k!="gt_mean"})
    real_out.append(r)
    print(f"[{name}] N={N} range=[{mn:.3g},{mx:.3g}] gt_mean={gt:.4g} -> "
          f"pandas={m['pandas_mean_state']}({m['pandas_mean']:.4g}) "
          f"numpy={m['numpy_mean_state']}({m['numpy_mean']:.4g}) "
          f"sklearn={m['sklearn_mean']:.6g} distinct={m['distinct_mean_answers']}")

with open(os.path.join(RES,"real_california.csv"),"w",newline="") as f:
    fields2=list(real_out[0].keys())
    w=csv.DictWriter(f, fieldnames=fields2); w.writeheader(); w.writerows(real_out)
print("wrote real_california.csv:", len(real_out), "rows")

import json
with open(os.path.join(RES,"versions.json"),"w") as f: json.dump(VERS,f,indent=2)
print("DONE")
