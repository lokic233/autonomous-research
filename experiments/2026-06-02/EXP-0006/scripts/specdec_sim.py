#!/usr/bin/env python3
"""EXP-0006 / CLAIM-0005 — region-adaptive vs best-tuned-fixed speculative-decoding
draft window. L0 CPU-only analytic model + Monte-Carlo cross-check. stdlib only."""
import json, math, os, random, csv, statistics

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(OUT, exist_ok=True)
K_MAX = 32

# ---- analytic speculative-decoding throughput proxy ----
def expected_accept(p, k):
    # E[a] = sum_{i=1..k} p^i  (leftmost acceptance, i.i.d. Bernoulli(p))
    if p >= 1.0:
        return float(k)
    return p * (1 - p**k) / (1 - p)

def tps_region(p, k, r):
    # tokens emitted per target-equivalent time for a single region
    # emitted per step = E[a]+1 ; cost per step = k*r + 1
    return (expected_accept(p, k) + 1.0) / (k * r + 1.0)

def best_k_for_region(p, r):
    best, bk = -1.0, 1
    for k in range(1, K_MAX + 1):
        t = tps_region(p, k, r)
        if t > best:
            best, bk = t, k
    return bk, best

def trace_tps(f, kc, kp, pc, pp, r):
    # token-weighted harmonic mean: total time additive, tokens additive
    tc = tps_region(pc, kc, r)
    tp = tps_region(pp, kp, r)
    return 1.0 / (f / tc + (1 - f) / tp)

def best_fixed(f, pc, pp, r):
    best, bk = -1.0, 1
    for k in range(1, K_MAX + 1):
        t = trace_tps(f, k, k, pc, pp, r)  # SAME k both regions
        if t > best:
            best, bk = t, k
    return bk, best

def adaptive(f, pc, pp, r):
    kc, _ = best_k_for_region(pc, r)
    kp, _ = best_k_for_region(pp, r)
    return kc, kp, trace_tps(f, kc, kp, pc, pp, r)

# ---- sweeps ----
P_C = [0.85, 0.90, 0.94, 0.97]
P_P = [0.55, 0.65, 0.75]
F   = [0.05, 0.10, 0.20, 0.35, 0.50, 0.60]
R   = [0.05, 0.10, 0.20, 0.35]

rows = []
for pc in P_C:
    for pp in P_P:
        if pp >= pc:  # constrained must be >= prose
            continue
        for f in F:
            for r in R:
                bk, tf = best_fixed(f, pc, pp, r)
                kc, kp, ta = adaptive(f, pc, pp, r)
                gain = ta / tf - 1.0
                rows.append(dict(p_constrained=pc, p_prose=pp, gap=round(pc-pp,3),
                    f=f, r=r, best_fixed_k=bk, tps_best_fixed=round(tf,5),
                    adapt_kc=kc, adapt_kp=kp, tps_adaptive=round(ta,5),
                    gain_pct=round(100*gain,3),
                    spd_fixed_vs_nospec=round(tf,4), spd_adapt_vs_nospec=round(ta,4)))

with open(os.path.join(OUT, "sweep.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

# ---- Monte-Carlo cross-check of analytic E[a] / tps ----
def mc_region_tps(p, k, r, n_tokens, rng):
    emitted = 0; steps = 0
    while emitted < n_tokens:
        a = 0
        for _ in range(k):
            if rng.random() < p:
                a += 1
            else:
                break
        emitted += a + 1
        steps += 1
    total_cost = steps * (k * r + 1.0)
    return emitted / total_cost

mc_checks = []
mc_points = [(0.94, 8, 0.1), (0.65, 4, 0.1), (0.90, 16, 0.2), (0.55, 2, 0.35)]
for (p, k, r) in mc_points:
    analytic = tps_region(p, k, r)
    sims = []
    for seed in range(5):
        rng = random.Random(1000 + seed)
        sims.append(mc_region_tps(p, k, r, 200_000, rng))
    m = statistics.mean(sims)
    rel = abs(m - analytic) / analytic
    mc_checks.append(dict(p=p, k=k, r=r, analytic=round(analytic,5),
        mc_mean=round(m,5), mc_std=round(statistics.pstdev(sims),6),
        rel_err=round(rel,5), pass_2pct=bool(rel < 0.02)))

# ---- summary stats ----
realistic = [x for x in rows if x["f"] <= 0.35]
def med(key, subset): return round(statistics.median([x[key] for x in subset]),3)
def mx(key, subset):  return max(subset, key=lambda x: x[key])

gains_real = [x["gain_pct"] for x in realistic]
gains_all  = [x["gain_pct"] for x in rows]
low_f = [x for x in rows if x["f"] in (0.10, 0.20)]

summary = dict(
    n_grid_points=len(rows),
    median_gain_pct_all=round(statistics.median(gains_all),3),
    median_gain_pct_realistic_f_le_0p35=round(statistics.median(gains_real),3),
    mean_gain_pct_realistic=round(statistics.mean(gains_real),3),
    median_gain_pct_low_f_0p1_0p2=round(statistics.median([x["gain_pct"] for x in low_f]),3),
    max_gain_pct=round(max(gains_all),3),
    max_gain_point=mx("gain_pct", rows),
    min_gain_pct=round(min(gains_all),3),
    frac_points_gain_ge_5pct=round(sum(1 for g in gains_all if g>=5)/len(gains_all),3),
    frac_points_gain_ge_3pct=round(sum(1 for g in gains_all if g>=3)/len(gains_all),3),
    frac_realistic_gain_ge_5pct=round(sum(1 for x in realistic if x["gain_pct"]>=5)/len(realistic),3),
    mc_cross_check=mc_checks,
    mc_all_pass=all(c["pass_2pct"] for c in mc_checks),
)
with open(os.path.join(OUT, "summary.json"), "w") as fh:
    json.dump(summary, fh, indent=2)

print(json.dumps(summary, indent=2))
