#!/usr/bin/env python3
"""Two FWER-corrected sub-questions:
 A) Does bounded-W STRICTLY DOMINATE VTC (not-worse both axes, strictly better >=1) -> the defensible win?
 B) Does bounded-W strictly BEAT greedy on p99 (fairness) -> partial win (with prefill cost)?
"""
import csv,os,statistics,random
RESULTS=os.path.join(os.path.dirname(__file__),"..","results")
def load():
    rows=[]
    for r in csv.DictReader(open(os.path.join(RESULTS,"sweep_all.csv"))):
        r["p99v"]=[float(x) for x in r["p99_seeds"].split(";")]
        r["rcv"]=[float(x) for x in r["recomp_seeds"].split(";")]
        rows.append(r)
    return rows
def ck(r): return (r["K"],r["skew"],r["B"],r["load"],r["capfam"])
def boot(d,n=4000,seed=7,a=0.05):
    rng=random.Random(seed);m=len(d);b=[sum(d[rng.randrange(m)] for _ in range(m))/m for _ in range(n)];b.sort()
    return b[int(a/2*n)],b[int((1-a/2)*n)]
rows=load();cells={}
for r in rows: cells.setdefault(ck(r),{})[(r["policy"],int(r["W"]))]=r
# A) bounded dominates vtc: m = cells*6W*2axes
mA=sum(6*2 for c,p in cells.items() if ("vtc",0) in p); aA=0.05/mA
domvtc=[]
for c,pts in cells.items():
    v=pts.get(("vtc",0))
    if not v: continue
    for W in [1,2,4,8,16,32]:
        b=pts.get(("bounded",W))
        if not b: continue
        dp=[x-y for x,y in zip(b["p99v"],v["p99v"])]; dr=[x-y for x,y in zip(b["rcv"],v["rcv"])]
        lp,hp=boot(dp,a=aA); lr,hr=boot(dr,a=aA)
        nw_p=not(lp>0); nw_r=not(lr>0); strict=(hp<0)or(hr<0)
        if nw_p and nw_r and strict: domvtc.append((c,W,statistics.mean(dp),statistics.mean(dr),hp<0,hr<0))
# B) bounded beats greedy on p99 (one-sided strict): m = cells*6
mB=sum(6 for c,p in cells.items() if ("greedy",0) in p); aB=0.05/mB
beatp99=[]
for c,pts in cells.items():
    g=pts.get(("greedy",0))
    if not g: continue
    for W in [1,2,4,8,16,32]:
        b=pts.get(("bounded",W))
        if not b: continue
        dp=[x-y for x,y in zip(b["p99v"],g["p99v"])]
        lp,hp=boot(dp,a=aB)
        if hp<0:  # bounded strictly lower p99 than greedy
            dr=statistics.mean([x-y for x,y in zip(b["rcv"],g["rcv"])])
            beatp99.append((c,W,statistics.mean(dp),dr))
print(f"A) bounded-W STRICTLY DOMINATES VTC (FWER m={mA}, a={aA:.2e}): {len(domvtc)} (cell,W) points")
# show distinct cells
cA=set(x[0] for x in domvtc)
print(f"   distinct cells with >=1 such W: {len(cA)}/{sum(1 for c,p in cells.items() if ('vtc',0) in p)}")
for c,W,dp,dr,sp,sr in sorted(domvtc)[:12]:
    print(f"     K={c[0]} sk={c[1]} B={c[2]} ld={c[3]} cap={c[4]} W={W}: dp99={dp:+.2f} drc={dr:+.0f} (strict p99={sp},rc={sr})")
print(f"\nB) bounded-W strictly LOWER p99 than greedy (FWER m={mB}, a={aB:.2e}): {len(beatp99)} (cell,W) points")
cB=set(x[0] for x in beatp99)
print(f"   distinct cells: {len(cB)}/{sum(1 for c,p in cells.items() if ('greedy',0) in p)}; ALL come with prefill COST (drc>0):")
costs=[dr for _,_,_,dr in beatp99]
print(f"   prefill delta vs greedy on these points: min={min(costs):+.0f} max={max(costs):+.0f} mean={statistics.mean(costs):+.0f}")
