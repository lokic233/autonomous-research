import os,time,numpy as np,pyarrow as pa,pyarrow.parquet as pq
from datasets import load_dataset, interleave_datasets
BASE=os.path.dirname(os.path.abspath(__file__))
a=[os.path.join(BASE,"data","A_64",f) for f in sorted(os.listdir(os.path.join(BASE,"data","A_64")))]
b=[os.path.join(BASE,"data","B_1",f) for f in sorted(os.listdir(os.path.join(BASE,"data","B_1")))]
t0=time.time()
dsA=load_dataset("parquet",data_files=a,split="train",streaming=True)
dsB=load_dataset("parquet",data_files=b,split="train",streaming=True)
print("load",time.time()-t0); t0=time.time()
inter=interleave_datasets([dsA,dsB],probabilities=[0.9,0.1],seed=0,stopping_strategy="all_exhausted")
shuf=inter.shuffle(seed=0,buffer_size=1000)
it=iter(shuf); n=0
t0=time.time()
for _ in range(50000):
    try: next(it); n+=1
    except StopIteration: break
print(f"50k examples in {time.time()-t0:.1f}s  -> {n/(time.time()-t0):.0f} ex/s")
