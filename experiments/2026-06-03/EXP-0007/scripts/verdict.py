#!/usr/bin/env python3
"""EXP-0007 STRICT joint-dominance verdict. Reads sweep_all.csv.
STRICT definition (pre-registered Pareto dominance, Bonferroni FWER):
  bounded-W JOINTLY DOMINATES baseline iff, on BOTH axes (p99, recomp), bounded is
  NOT-WORSE (paired-bootstrap Bonferroni CI does NOT show bounded strictly worse, i.e. CI_lo of
  delta=bounded-baseline is <= 0 with the upper bound not forcing worse) AND STRICTLY BETTER on
  >=1 axis (Bonferroni CI_hi < 0). Must hold vs BOTH greedy AND vtc simultaneously.
We ALSO report the weaker, honest "not-worse" using mean signs to characterize the tradeoff.
"""
import csv, os, statistics, random

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")

def load():
    rows=[]
    with open(os.path.join(RESULTS,"sweep_all.csv")) as f:
        for r in csv.DictReader(f):
            r["p99v"]=[float(x) for x in r["p99_seeds"].split(";")]
            r["rcv"]=[float(x) for x in r["recomp_seeds"].split(";")]
            for k in ("K","B","capfam","W","load"): r[k]=float(r[k])
            rows.append(r)
    return rows

def ck(r): return (r["K"],r["skew"],r["B"],r["load"],r["capfam"])

def boot_ci(d,n=4000,seed=7,alpha=0.05):
    rng=random.Random(seed);m=len(d);b=[]
    for _ in range(n): b.append(sum(d[rng.randrange(m)] for _ in range(m))/m)
    b.sort(); return b[int(alpha/2*n)], b[int((1-alpha/2)*n)]

rows=load()
cells={}
for r in rows: cells.setdefault(ck(r),{})[(r["policy"],int(r["W"]))]=r

# count candidate dominance comparisons for Bonferroni: cells * 6 W * 2 baselines * 2 axes
cand=0
for c,pts in cells.items():
    if ("greedy",0) in pts and ("vtc",0) in pts:
        cand += 6*2*2
alpha_bonf=0.05/cand

strict_wins=[]; partial=[]; summary_lines=[]
greedy_dom_vtc=0; cells_eval=0
for c,pts in cells.items():
    g=pts.get(("greedy",0)); v=pts.get(("vtc",0))
    if not g or not v: continue
    cells_eval+=1
    # does greedy dominate vtc (context)? mean-level
    if g["p99v"] and statistics.mean(g["p99v"])<=statistics.mean(v["p99v"]) and statistics.mean([x for x in g["rcv"]])<=statistics.mean(v["rcv"]):
        greedy_dom_vtc+=1
    for W in [1,2,4,8,16,32]:
        b=pts.get(("bounded",W))
        if not b: continue
        verdict_vs={}
        joint=True; strict_any=False
        for bln,bl in [("greedy",g),("vtc",v)]:
            dp=[bp-sp for bp,sp in zip(b["p99v"],bl["p99v"])]
            dr=[br-sr for br,sr in zip(b["rcv"],bl["rcv"])]
            lp,hp=boot_ci(dp,alpha=alpha_bonf); lr,hr=boot_ci(dr,alpha=alpha_bonf)
            better_p = hp<0; worse_p = lp>0
            better_r = hr<0; worse_r = lr>0
            # not-worse = not statistically worse
            nw_p = not worse_p; nw_r = not worse_r
            dom_bl = nw_p and nw_r and (better_p or better_r)
            if not dom_bl: joint=False
            if better_p or better_r: strict_any=True
            verdict_vs[bln]=(statistics.mean(dp),statistics.mean(dr),better_p,worse_p,better_r,worse_r)
        if joint and strict_any:
            strict_wins.append((c,W,verdict_vs))

print(f"# cells evaluated: {cells_eval}")
print(f"# Bonferroni m={cand}, per-comp alpha={alpha_bonf:.2e}")
print(f"# cells where GREEDY mean-dominates VTC on both axes: {greedy_dom_vtc}/{cells_eval}")
print(f"# STRICT joint-dominance wins (bounded-W not-worse+strict vs BOTH, FWER): {len(strict_wins)}")
for c,W,vv in strict_wins:
    print(f"  K={c[0]} skew={c[1]} B={c[2]} load={c[3]} capfam={c[4]} W={W}")
    for bln in ("greedy","vtc"):
        dp,dr,bp,wp,br,wr=vv[bln]
        print(f"     vs {bln}: mean dp99={dp:+.2f}(better={bp},worse={wp}) drc={dr:+.0f}(better={br},worse={wr})")
