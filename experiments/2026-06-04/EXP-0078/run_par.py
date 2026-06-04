#!/usr/bin/env python3
"""EXP-0078 parallel runner. One config per process. Reduced to 800 batches early-training window."""
import os, sys, json, time, math
import numpy as np, pyarrow as pa
import datasets
from datasets import load_dataset, interleave_datasets

BASE=os.path.dirname(os.path.abspath(__file__)); DATA=os.path.join(BASE,"data"); RES=os.path.join(BASE,"results")
BATCH=256; N_STEPS=800; SEED=0
A_SHARDS=64

def files(d): return [os.path.join(DATA,d,f) for f in sorted(os.listdir(os.path.join(DATA,d))) if f.endswith(".parquet")]

def run(bc, buf):
    a=files("A_64"); b=files(f"B_{bc}")
    dsA=load_dataset("parquet",data_files=a,split="train",streaming=True)
    dsB=load_dataset("parquet",data_files=b,split="train",streaming=True)
    inter=interleave_datasets([dsA,dsB],probabilities=[0.9,0.1],seed=SEED,stopping_strategy="all_exhausted")
    shuf=inter.shuffle(seed=SEED,buffer_size=buf)
    it=iter(shuf); counts=[]
    for step in range(N_STEPS):
        cb=0;n=0
        try:
            for _ in range(BATCH):
                ex=next(it)
                if ex["source"]=="B": cb+=1
                n+=1
        except StopIteration:
            if n==0: break
        if n==0: break
        counts.append(cb)
    counts=np.array(counts,dtype=int); fr=counts/BATCH
    mzr=cur=0
    for c in counts:
        if c==0: cur+=1; mzr=max(mzr,cur)
        else: cur=0
    win=50
    if len(fr)>=win:
        sw=np.convolve(fr,np.ones(win)/win,mode="valid"); swmin,swmax=float(sw.min()),float(sw.max())
    else: swmin=swmax=float("nan")
    bern=math.sqrt(256*0.1*0.9)/256
    r={"b_shard_count":bc,"buffer_size":buf,"n_batches":len(counts),"max_zero_B_run":int(mzr),
       "frac_batches_zero_B":float((counts==0).mean()) if len(counts) else float("nan"),
       "mean_b_fraction":float(fr.mean()) if len(fr) else float("nan"),
       "std_b_fraction":float(fr.std()) if len(fr) else float("nan"),
       "sliding50_min":swmin,"sliding50_max":swmax,"bernoulli_sd":bern}
    r["std_over_bernoulli"]=r["std_b_fraction"]/bern
    # write per-config CSV + json
    with open(os.path.join(RES,f"series_B{bc}_N{buf}.csv"),"w") as f:
        f.write("step,b_count,b_fraction\n")
        for i,c in enumerate(counts): f.write(f"{i},{c},{c/BATCH}\n")
    with open(os.path.join(RES,f"cfg_B{bc}_N{buf}.json"),"w") as f: json.dump(r,f,indent=2)
    return r

if __name__=="__main__":
    bc=int(sys.argv[1]); buf=int(sys.argv[2])
    t0=time.time(); r=run(bc,buf)
    print(f"B{bc}_N{buf}: batches={r['n_batches']} maxZeroBrun={r['max_zero_B_run']} "
          f"fracZero={r['frac_batches_zero_B']:.3f} mean={r['mean_b_fraction']:.4f} "
          f"std={r['std_b_fraction']:.5f} ({r['std_over_bernoulli']:.2f}x) "
          f"sw50=[{r['sliding50_min']:.3f},{r['sliding50_max']:.3f}] {time.time()-t0:.0f}s",flush=True)
