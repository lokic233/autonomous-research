import os, numpy as np
from datasets import load_dataset, interleave_datasets
BASE=os.path.dirname(os.path.abspath(__file__)); DATA=os.path.join(BASE,"data")
def files(d): return [os.path.join(DATA,d,f) for f in sorted(os.listdir(os.path.join(DATA,d))) if f.endswith(".parquet")]
for bc in [1,64]:
    dsA=load_dataset("parquet",data_files=files("A_64"),split="train",streaming=True)
    dsB=load_dataset("parquet",data_files=files(f"B_{bc}"),split="train",streaming=True)
    # RAW interleave, NO shuffle -> look at B example positions & B idx ordering in first 5000 outputs
    inter=interleave_datasets([dsA,dsB],probabilities=[0.9,0.1],seed=0,stopping_strategy="all_exhausted")
    it=iter(inter); pos=[]; bidx=[]
    for i in range(5000):
        ex=next(it)
        if ex["source"]=="B": pos.append(i); bidx.append(ex["idx"])
    pos=np.array(pos)
    gaps=np.diff(pos)
    print(f"B-shards={bc}: nB_in_5000={len(pos)} Bfrac={len(pos)/5000:.3f} "
          f"meanGap={gaps.mean():.2f} maxGap={gaps.max()} | first B idx seq: {bidx[:8]} ... B idx range[{min(bidx)},{max(bidx)}]")
