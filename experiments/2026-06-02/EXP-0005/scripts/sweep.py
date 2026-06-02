#!/usr/bin/env python3
import csv, statistics, random, time, json, sys, os
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(__file__))
from sim import simulate, BLOCKS_PER_FAMILY

SEEDS = list(range(8))
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS, exist_ok=True)
M = 400
W_CANDIDATES = [1,2,4,8,16,32,10**9]

def mean_std(xs):
    return statistics.mean(xs), (statistics.pstdev(xs) if len(xs)>1 else 0.0)

def paired_bootstrap_ci(deltas, n=2000, seed=12345):
    rng = random.Random(seed); m=len(deltas); boots=[]
    for _ in range(n):
        boots.append(sum(deltas[rng.randrange(m)] for _ in range(m))/m)
    boots.sort()
    return boots[int(0.025*n)], boots[int(0.975*n)]

def cap_for(regime, K):
    if regime=="one": return BLOCKS_PER_FAMILY*1
    if regime=="few": return BLOCKS_PER_FAMILY*max(2, K//2)
    if regime=="all": return BLOCKS_PER_FAMILY*K

def run_cell(args):
    K, skew, lname, lm, B, regime = args
    lam = lm * B / 1.0
    cap = cap_for(regime, K)
    fcfs = [simulate("fcfs",0,K,skew,lam,B,cap,M,s) for s in SEEDS]
    fcfs_p99 = mean_std([r["p99_wait"] for r in fcfs])[0]
    fcfs_recomp = [r["recomp_tokens"] for r in fcfs]
    rows=[]; matched=None
    for W in W_CANDIDATES:
        pfa = [simulate("pfa",W,K,skew,lam,B,cap,M,s) for s in SEEDS]
        pfa_p99 = mean_std([r["p99_wait"] for r in pfa])[0]
        deltas = [p["recomp_tokens"]-f for p,f in zip(pfa,fcfs_recomp)]
        ci = paired_bootstrap_ci(deltas)
        fair = pfa_p99/fcfs_p99 if fcfs_p99>0 else 1.0
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
        if fair<=1.10 and (matched is None or W>matched["W"]):
            if W<10**9: matched=rec   # matched-fairness must use a BOUNDED window
    return rows, matched

def main():
    t0=time.time()
    cells=[]
    for K in [2,4,8,16]:
        for skew in [0.0,1.0]:
            for (lname,lm) in [("light",0.6),("mod",1.0),("heavy",1.6)]:
                for B in [4,16]:
                    for regime in ["one","few","all"]:
                        cells.append((K,skew,lname,lm,B,regime))
    with Pool(10) as p:
        out = p.map(run_cell, cells)
    allrows=[]; matched_rows=[]
    for rows,matched in out:
        allrows.extend(rows)
        if matched: matched_rows.append(matched)
    keys=list(allrows[0].keys())
    with open(os.path.join(RESULTS,"sweep_all.csv"),"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(allrows)
    with open(os.path.join(RESULTS,"matched_fairness.csv"),"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(matched_rows)
    wins=[r for r in matched_rows if r["ci_hi"]<0]
    print(f"cells={len(cells)} rows={len(allrows)} matched_cells={len(matched_rows)} wins_CI<0={len(wins)} elapsed={time.time()-t0:.1f}s")
if __name__=="__main__":
    main()
