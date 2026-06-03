#!/usr/bin/env python3
"""EXP-0027 CLAIM-0026: spec-decode session-phase-adaptive vs BEST-TUNED-FIXED draft policy.
L0 CPU-only, stdlib-only, SERIAL, analytic core + stochastic detection sim. See PRE_REGISTRATION.md."""
import csv, os, random, statistics, json

ART = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ART, "results")
os.makedirs(RES, exist_ok=True)

# ---- THROUGHPUT MODEL (pre-registered) ----
def E_accepted(a, k):
    # sum_{i=1..k} a^i ; geometric-prefix accept with constant per-token accept a
    if a <= 0: return 0.0
    if a >= 1: return float(k)
    return a * (1 - a**k) / (1 - a)

def nettps(a, k, r):
    # (E[accepted]+1) / (k*c_draft + c_target), c_target=1, c_draft=r
    return (E_accepted(a, k) + 1.0) / (k * r + 1.0)

K_RANGE = list(range(1, 33))

def best_k_for_phase(a, r):
    return max(K_RANGE, key=lambda k: nettps(a, k, r))

def best_tuned_fixed(phase_accs, fracs, r):
    # single k maximizing session-weighted net tok/s
    def sess(k):
        return sum(f * nettps(a, k, r) for a, f in zip(phase_accs, fracs))
    kstar = max(K_RANGE, key=sess)
    return kstar, sess(kstar)

def adaptive_ideal(phase_accs, fracs, r):
    # per-phase optimal k, no overhead (upper bound)
    tot = 0.0; kmap = []
    for a, f in zip(phase_accs, fracs):
        kp = best_k_for_phase(a, r); kmap.append(kp)
        tot += f * nettps(a, kp, r)
    return tot, kmap

def adaptive_realistic(phase_accs, fracs, r, p_err, s, rng):
    # detection: with prob p_err, misclassify -> use a DIFFERENT phase's optimal k (wrong k applied
    # to the true phase's acceptance). Then apply switching tax (1-s).
    kmap = [best_k_for_phase(a, r) for a in phase_accs]
    n_phases = len(phase_accs)
    tot = 0.0
    for i, (a, f) in enumerate(zip(phase_accs, fracs)):
        if rng.random() < p_err and n_phases > 1:
            # pick a wrong phase's k
            wrong = rng.choice([j for j in range(n_phases) if j != i])
            k_used = kmap[wrong]
        else:
            k_used = kmap[i]
        tot += f * nettps(a, k_used, r)
    return tot * (1.0 - s)

# ---- PHASE MODEL ----
PHASE_MIXES = {
    "realistic_deep": (0.25, 0.55, 0.20),   # prose, tool, mixed
    "balanced":       (0.50, 0.30, 0.20),
    "tool_heavy":     (0.10, 0.70, 0.20),
}
A_PROSE = [0.55, 0.65, 0.75, 0.85]
GAP = [-0.30, -0.20, -0.10, 0.0, 0.10, 0.20, 0.30]
R_RATIO = [0.05, 0.10, 0.20, 0.40]
P_ERR = [0.0, 0.05, 0.15]
S_TAX = [0.0, 0.02, 0.05]
SEEDS = [0, 1, 2, 3, 4]

def clamp(x): return max(0.02, min(0.98, x))

rows = []
for mixname, (fp, ft, fm) in PHASE_MIXES.items():
    fracs = (fp, ft, fm)
    for a_prose in A_PROSE:
        for gap in GAP:
            a_tool = clamp(a_prose + gap)
            a_mixed = clamp((a_prose + a_tool) / 2.0)
            phase_accs = (a_prose, a_tool, a_mixed)
            drift = abs(a_tool - a_prose)
            sess_spread = max(phase_accs) - min(phase_accs)
            for r in R_RATIO:
                kstar, ntps_fixed = best_tuned_fixed(phase_accs, fracs, r)
                ntps_adapt_ideal, kmap = adaptive_ideal(phase_accs, fracs, r)
                ntps_k1 = sum(f * nettps(a, 1, r) for a, f in zip(phase_accs, fracs))
                # fraction of total (over-k1) improvement captured by single tuned k
                denom = ntps_adapt_ideal - ntps_k1
                fixed_captured_frac = ((ntps_fixed - ntps_k1) / denom) if denom > 1e-12 else 1.0
                ideal_gain_pct = 100.0 * (ntps_adapt_ideal - ntps_fixed) / ntps_fixed
                for p_err in P_ERR:
                    for s in S_TAX:
                        vals = []
                        for seed in SEEDS:
                            rng = random.Random((seed*131 + int(a_prose*100)*17 + int((gap+1)*100)*7
                                                 + int(r*100)*3 + int(p_err*100)*5 + int(s*100)) & 0x7fffffff)
                            vals.append(adaptive_realistic(phase_accs, fracs, r, p_err, s, rng))
                        ntps_adapt = statistics.mean(vals)
                        ntps_adapt_std = statistics.pstdev(vals) if len(vals) > 1 else 0.0
                        gain_pct = 100.0 * (ntps_adapt - ntps_fixed) / ntps_fixed
                        rows.append(dict(
                            mix=mixname, a_prose=round(a_prose,3), gap=round(gap,3),
                            a_tool=round(a_tool,3), a_mixed=round(a_mixed,3),
                            drift=round(drift,3), sess_spread=round(sess_spread,3),
                            r=r, k_star_fixed=kstar, k_map=";".join(map(str,kmap)),
                            ntps_fixed=round(ntps_fixed,4), ntps_adapt_ideal=round(ntps_adapt_ideal,4),
                            ntps_adapt=round(ntps_adapt,4), ntps_adapt_std=round(ntps_adapt_std,4),
                            ntps_k1=round(ntps_k1,4),
                            fixed_captured_frac=round(fixed_captured_frac,4),
                            ideal_gain_pct=round(ideal_gain_pct,3),
                            gain_pct=round(gain_pct,3),
                            p_err=p_err, s=s,
                        ))

csvpath = os.path.join(RES, "exp0027_sweep.csv")
with open(csvpath, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print("WROTE", csvpath, "rows=", len(rows))

# ---- ANALYSIS / verdict-relevant aggregates ----
def summarize(subset, label):
    if not subset: return None
    gains = [x["gain_pct"] for x in subset]
    ideal_gains = [x["ideal_gain_pct"] for x in subset]
    captured = [x["fixed_captured_frac"] for x in subset]
    return dict(label=label, n=len(subset),
                gain_mean=round(statistics.mean(gains),3),
                gain_med=round(statistics.median(gains),3),
                gain_p90=round(sorted(gains)[int(0.9*len(gains))-1],3),
                ideal_gain_mean=round(statistics.mean(ideal_gains),3),
                ideal_gain_med=round(statistics.median(ideal_gains),3),
                captured_mean=round(statistics.mean(captured),3),
                captured_med=round(statistics.median(captured),3),
                frac_gain_gt3=round(sum(1 for g in gains if g>3.0)/len(gains),3),
                frac_captured_ge80=round(sum(1 for c in captured if c>=0.80)/len(captured),3))

summ = []
summ.append(summarize(rows, "ALL"))
# realistic operating point: realistic_deep mix, with detection error + switching tax present
real = [x for x in rows if x["mix"]=="realistic_deep" and x["p_err"]>0 and x["s"]>0]
summ.append(summarize(real, "realistic_deep w/ p_err>0 & s>0 (realistic op point)"))
# realistic mix, ideal (no overhead) — to show the theoretical ceiling
real_ideal = [x for x in rows if x["mix"]=="realistic_deep" and x["p_err"]==0 and x["s"]==0]
summ.append(summarize(real_ideal, "realistic_deep IDEAL (no overhead)"))
# drift breakdown
for d_lo, d_hi, lbl in [(0.0,0.05,"drift~0"),(0.05,0.15,"small drift"),(0.15,0.5,"large drift")]:
    sub = [x for x in rows if d_lo <= x["drift"] < d_hi and x["mix"]=="realistic_deep" and x["p_err"]>0 and x["s"]>0]
    summ.append(summarize(sub, f"realistic_deep {lbl} ({d_lo}-{d_hi}) w/ overhead"))

with open(os.path.join(RES, "exp0027_summary.json"), "w") as f:
    json.dump([s for s in summ if s], f, indent=2)

print("\n=== SUMMARY ===")
for s in summ:
    if s: print(json.dumps(s))
