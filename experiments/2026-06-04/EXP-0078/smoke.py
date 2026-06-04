import os, numpy as np, pyarrow as pa, pyarrow.parquet as pq, shutil
from datasets import load_dataset, interleave_datasets
BASE=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(BASE,"smoke_data")
def w(out,n,ns,lab):
    if os.path.isdir(out): shutil.rmtree(out)
    os.makedirs(out)
    b=np.linspace(0,n,ns+1).astype(int); fs=[]
    for s in range(ns):
        idx=np.arange(b[s],b[s+1],dtype=np.int64)
        pq.write_table(pa.table({"source":[lab]*len(idx),"idx":idx}),os.path.join(out,f"s{s:03d}.parquet")); fs.append(os.path.join(out,f"s{s:03d}.parquet"))
    return fs
a=w(os.path.join(D,"A"),9000,8,"A")
for bc in [1,16]:
    b=w(os.path.join(D,f"B{bc}"),1000,bc,"B")
    dsA=load_dataset("parquet",data_files=a,split="train",streaming=True)
    dsB=load_dataset("parquet",data_files=b,split="train",streaming=True)
    inter=interleave_datasets([dsA,dsB],probabilities=[0.9,0.1],seed=0,stopping_strategy="all_exhausted")
    shuf=inter.shuffle(seed=0,buffer_size=500)
    seq=[]; it=iter(shuf)
    for _ in range(2000):
        try: seq.append(next(it)["source"])
        except StopIteration: break
    seq=np.array([1 if s=="B" else 0 for s in seq])
    # max zero-B run + overall frac
    mr=cur=0
    for x in seq:
        if x==0: cur+=1; mr=max(mr,cur)
        else: cur=0
    print(f"B-shards={bc}: n={len(seq)} Bfrac={seq.mean():.3f} maxZeroBrun(examples)={mr}")
