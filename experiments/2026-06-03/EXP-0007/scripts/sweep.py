#!/usr/bin/env python3
"""EXP-0007 serial sweep: 3-way (greedy / vtc / bounded-W) Pareto on (p99_wait, recomp_tokens).
Multiprocessing BLOCKED on this sandbox -> SERIAL. Trust on-disk CSV, not stdout.
Writes results/sweep_all.csv (one row per policy-point per cell, all seeds aggregated).
"""
import csv, statistics, random, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sim import simulate, BLOCKS_PER_FAMILY

SEEDS = list(range(24))                 # >=20 per committee
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS, exist_ok=True)
M = 400
W_LIST = [1, 2, 4, 8, 16, 32]

# cache capacity expressed as MULTIPLE of B families: must hold the running set (B fams pinned)
# plus reuse headroom. capfam in {B+1, B+2, 2B-ish} -> genuine eviction pressure.
def cells():
    out = []
    for K in [8, 16]:
        for skew in [1.5, 2.0]:
            for B in [4, 16]:
                if B >= K:    # need K > B so cache pressure is meaningful (can't hold all fams)
                    continue
                for load in [0.7, 1.0, 1.4]:
                    for capfam in [B + 1, B + 2, min(2 * B, K - 1)]:
                        out.append((K, skew, B, load, capfam))
    # dedup capfam
    seen = set(); ded = []
    for c in out:
        key = c
        if key in seen: continue
        seen.add(key); ded.append(c)
    return ded

def mean(xs): return statistics.mean(xs)
def pstd(xs): return statistics.pstdev(xs) if len(xs) > 1 else 0.0

def run_policy(pol, W, K, skew, lam, B, cap, M):
    runs = [simulate(pol, W, K, skew, lam, B, cap, M, s) for s in SEEDS]
    return runs

def main():
    t0 = time.time()
    rows = []
    cs = cells()
    for ci, (K, skew, B, load, capfam) in enumerate(cs):
        lam = load * B / 1.0
        cap = int(BLOCKS_PER_FAMILY * capfam)
        # baselines
        greedy = run_policy("greedy", 0, K, skew, lam, B, cap, M)
        vtc    = run_policy("vtc", 0, K, skew, lam, B, cap, M)
        policy_points = [("greedy", 0, greedy), ("vtc", 0, vtc)]
        for W in W_LIST:
            policy_points.append(("bounded", W, run_policy("bounded", W, K, skew, lam, B, cap, M)))
        for pol, W, runs in policy_points:
            p99 = [r["p99_wait"] for r in runs]
            rc = [r["recomp_tokens"] for r in runs]
            hit = [r["hit_rate"] for r in runs]
            rows.append({
                "K": K, "skew": skew, "B": B, "load": load, "capfam": capfam,
                "lam": lam, "cap_blocks": cap, "policy": pol, "W": W,
                "p99_mean": mean(p99), "p99_std": pstd(p99),
                "recomp_mean": mean(rc), "recomp_std": pstd(rc),
                "hit_mean": mean(hit),
                "p99_seeds": ";".join(f"{x:.4f}" for x in p99),
                "recomp_seeds": ";".join(str(x) for x in rc),
            })
        if ci % 4 == 0:
            print(f"cell {ci}/{len(cs)} t={time.time()-t0:.0f}s", flush=True)
    keys = list(rows[0].keys())
    with open(os.path.join(RESULTS, "sweep_all.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    print(f"DONE cells={len(cs)} rows={len(rows)} t={time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
