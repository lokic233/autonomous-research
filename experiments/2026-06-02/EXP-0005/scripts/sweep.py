#!/usr/bin/env python3
import csv, statistics, random, time, itertools, json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sim import simulate, BLOCKS_PER_FAMILY

SEEDS = list(range(8))
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS, exist_ok=True)

def mean_std(xs):
    return statistics.mean(xs), (statistics.pstdev(xs) if len(xs)>1 else 0.0)

def paired_bootstrap_ci(deltas, n=2000, seed=12345):
    rng = random.Random(seed)
    m = len(deltas); boots=[]
    for _ in range(n):
        s = sum(deltas[rng.randrange(m)] for _ in range(m))/m
        boots.append(s)
    boots.sort()
    return boots[int(0.025*n)], boots[int(0.975*n)]

# capacity regimes relative to K
def cap_for(regime, K):
    if regime=="one":  return BLOCKS_PER_FAMILY*1
    if regime=="few":  return BLOCKS_PER_FAMILY*max(2, K//2)
    if regime=="all":  return BLOCKS_PER_FAMILY*K
M = 400
W_CANDIDATES = [0,1,2,4,8,16,32,10**9]  # 0=FCFS, inf=unbounded

# load relative to capacity B/BASE_SERVICE=B throughput; lam multiples
def run_cell(K, skew, lam, B, regime):
    cap = cap_for(regime, K)
    # FCFS baseline per seed
    fcfs = [simulate("fcfs",0,K,skew,lam,B,cap,M,s) for s in SEEDS]
    fcfs_p99 = mean_std([r["p99_wait"] for r in fcfs])[0]
    fcfs_recomp = [r["recomp_tokens"] for r in fcfs]
    # PFA at each W; find matched-fairness W = largest W with p99 within 10% of FCFS
    rows=[]
    matched=None
    for W in W_CANDIDATES:
        if W==0: continue
        pfa = [simulate("pfa",W,K,skew,lam,B,cap,M,s) for s in SEEDS]
        pfa_p99 = mean_std([r["p99_wait"] for r in pfa])[0]
        deltas = [p["recomp_tokens"]-f for p,f in zip(pfa,fcfs_recomp)]  # negative = PFA saves
        ci = paired_bootstrap_ci(deltas)
        fair_ratio = pfa_p99/fcfs_p99 if fcfs_p99>0 else 1.0
        rec = {
            "K":K,"skew":skew,"lam":lam,"B":B,"regime":regime,"cap_blocks":cap,"W":W,
            "fcfs_recomp_mean":mean_std(fcfs_recomp)[0],"fcfs_recomp_std":mean_std(fcfs_recomp)[1],
            "pfa_recomp_mean":mean_std([r["recomp_tokens"] for r in pfa])[0],
            "pfa_recomp_std":mean_std([r["recomp_tokens"] for r in pfa])[1],
            "delta_mean":statistics.mean(deltas),"ci_lo":ci[0],"ci_hi":ci[1],
            "fcfs_hit":mean_std([r["hit_rate"] for r in fcfs])[0],
            "pfa_hit":mean_std([r["hit_rate"] for r in pfa])[0],
            "fcfs_p99":fcfs_p99,"pfa_p99":pfa_p99,"fair_ratio":fair_ratio,
            "fcfs_mean_wait":mean_std([r["mean_wait"] for r in fcfs])[0],
            "pfa_mean_wait":mean_std([r["mean_wait"] for r in pfa])[0],
        }
        rows.append(rec)
        if fair_ratio <= 1.10:
            if matched is None or W>matched["W"]:
                matched=rec
    return rows, matched

def main():
    t0=time.time()
    Ks=[2,4,8,16]; skews=[0.0,1.0]; lams_mult=[("light",0.6),("mod",1.0),("heavy",1.6)]
    Bs=[4,16]; regimes=["one","few","all"]
    allrows=[]; matched_rows=[]
    for K in Ks:
        for skew in skews:
            for (lname,lm) in lams_mult:
                for B in Bs:
                    lam = lm * B / 1.0  # offered load relative to B throughput
                    for regime in regimes:
                        rows, matched = run_cell(K,skew,lam,B,regime)
                        for r in rows: r["lname"]=lname
                        allrows.extend(rows)
                        if matched: matched["lname"]=lname; matched_rows.append(matched)
    # write all
    keys=list(allrows[0].keys())
    with open(os.path.join(RESULTS,"sweep_all.csv"),"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(allrows)
    with open(os.path.join(RESULTS,"matched_fairness.csv"),"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(matched_rows)
    print(f"cells={len(allrows)} matched_cells={len(matched_rows)} elapsed={time.time()-t0:.1f}s")
    # quick verdict scan over matched-fairness rows
    wins=[r for r in matched_rows if r["ci_hi"]<0]   # CI fully below 0 => PFA saves tokens
    print(f"matched-fairness cells where PFA wins (CI<0): {len(wins)}/{len(matched_rows)}")
if __name__=="__main__":
    main()
