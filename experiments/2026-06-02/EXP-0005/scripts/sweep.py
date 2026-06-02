#!/usr/bin/env python3
"""Serial sweep (multiprocessing blocked by sandbox sem perms). Budget-safe."""
import csv, statistics, random, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sim import simulate, BLOCKS_PER_FAMILY

SEEDS = list(range(6))
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS, exist_ok=True)
M = 300
W_CANDIDATES = [1,2,4,8,32,10**9]   # last = unbounded (NOT eligible for matched fairness)

def mean_std(xs):
    return statistics.mean(xs), (statistics.pstdev(xs) if len(xs)>1 else 0.0)

def paired_bootstrap_ci(deltas, n=2000, seed=12345):
    rng=random.Random(seed); m=len(deltas); boots=[]
    for _ in range(n):
        boots.append(sum(deltas[rng.randrange(m)] for _ in range(m))/m)
    boots.sort()
    return boots[int(0.025*n)], boots[int(0.975*n)]

def cap_for(regime,K):
    return BLOCKS_PER_FAMILY*{"one":1,"few":max(2,K//2),"all":K}[regime]

def run_cell(K,skew,lname,lm,B,regime):
    lam=lm*B/1.0; cap=cap_for(regime,K)
    fcfs=[simulate("fcfs",0,K,skew,lam,B,cap,M,s) for s in SEEDS]
    fcfs_p99=mean_std([r["p99_wait"] for r in fcfs])[0]
    fcfs_recomp=[r["recomp_tokens"] for r in fcfs]
    rows=[]; matched=None; unbounded=None
    for W in W_CANDIDATES:
        pfa=[simulate("pfa",W,K,skew,lam,B,cap,M,s) for s in SEEDS]
        pfa_p99=mean_std([r["p99_wait"] for r in pfa])[0]
        deltas=[p["recomp_tokens"]-f for p,f in zip(pfa,fcfs_recomp)]
        ci=paired_bootstrap_ci(deltas)
        fair=pfa_p99/fcfs_p99 if fcfs_p99>0 else 1.0
        rec={"K":K,"skew":skew,"lname":lname,"lam":lam,"B":B,"regime":regime,"cap_blocks":cap,"W":W,
             "fcfs_recomp_mean":mean_std(fcfs_recomp)[0],"fcfs_recomp_std":mean_std(fcfs_recomp)[1],
             "pfa_recomp_mean":mean_std([r["recomp_tokens"] for r in pfa])[0],
             "pfa_recomp_std":mean_std([r["recomp_tokens"] for r in pfa])[1],
             "delta_mean":statistics.mean(deltas),"ci_lo":ci[0],"ci_hi":ci[1],
             "fcfs_hit":mean_std([r["hit_rate"] for r in fcfs])[0],
             "pfa_hit":mean_std([r["hit_rate"] for r in pfa])[0],
             "fcfs_p99":fcfs_p99,"pfa_p99":pfa_p99,"fair_ratio":fair,
             "fcfs_mean_wait":mean_std([r["mean_wait"] for r in fcfs])[0],
             "pfa_mean_wait":mean_std([r["mean_wait"] for r in pfa])[0]}
        rows.append(rec)
        if W==10**9: unbounded=rec
        elif fair<=1.10 and (matched is None or W>matched["W"]):
            matched=rec
    return rows,matched,unbounded

def main():
    t0=time.time()
    allrows=[]; matched_rows=[]; unbounded_rows=[]
    cells=[(K,skew,ln,lm,B,rg)
        for K in [2,4,8,16] for skew in [0.0,1.0]
        for (ln,lm) in [("light",0.6),("heavy",1.6)]
        for B in [4,16] for rg in ["one","few","all"]]
    for i,c in enumerate(cells):
        rows,matched,unb=run_cell(*c)
        allrows.extend(rows)
        if matched: matched_rows.append(matched)
        if unb: unbounded_rows.append(unb)
        if i%16==0:
            print(f"cell {i}/{len(cells)} t={time.time()-t0:.0f}s",flush=True)
    keys=list(allrows[0].keys())
    for name,data in [("sweep_all",allrows),("matched_fairness",matched_rows),("unbounded",unbounded_rows)]:
        with open(os.path.join(RESULTS,name+".csv"),"w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(data)
    wins=[r for r in matched_rows if r["ci_hi"]<0]
    print(f"DONE cells={len(cells)} rows={len(allrows)} matched={len(matched_rows)} wins_CI<0={len(wins)} t={time.time()-t0:.0f}s",flush=True)
if __name__=="__main__":
    main()
