#!/usr/bin/env python3
"""EXP-0007 analysis: 3-way Pareto + joint-dominance test with paired bootstrap + Bonferroni FWER.
Reads results/sweep_all.csv. Writes results/pareto_points.csv, results/dominance.csv, and prints verdict.

Joint dominance (THE test): for a given cell, does there exist a bounded-W point that is
statistically <= BOTH greedy AND vtc on BOTH axes (p99_wait, recomp_tokens), with at least one
strict, surviving Bonferroni correction across all candidate (cell x baseline x axis) comparisons?
"""
import csv, os, statistics, random, math

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")

def load():
    rows = []
    with open(os.path.join(RESULTS, "sweep_all.csv")) as f:
        for r in csv.DictReader(f):
            r["p99_seedv"] = [float(x) for x in r["p99_seeds"].split(";")]
            r["recomp_seedv"] = [float(x) for x in r["recomp_seeds"].split(";")]
            for k in ("p99_mean","p99_std","recomp_mean","recomp_std","hit_mean","load","skew","lam"):
                r[k] = float(r[k])
            for k in ("K","B","capfam","W","cap_blocks"):
                r[k] = int(r[k])
            rows.append(r)
    return rows

def cellkey(r): return (r["K"], r["skew"], r["B"], r["load"], r["capfam"])

def paired_bootstrap_ci(deltas, n=5000, seed=12345, alpha=0.05):
    rng = random.Random(seed); m = len(deltas); boots = []
    for _ in range(n):
        boots.append(sum(deltas[rng.randrange(m)] for _ in range(m)) / m)
    boots.sort()
    lo = boots[int((alpha/2)*n)]; hi = boots[int((1-alpha/2)*n)]
    return lo, hi

def main():
    rows = load()
    cells = {}
    for r in rows:
        cells.setdefault(cellkey(r), {})[(r["policy"], r["W"])] = r

    # Pareto points export (per cell, all policy points)
    with open(os.path.join(RESULTS, "pareto_points.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["K","skew","B","load","capfam","policy","W","p99_mean","p99_std","recomp_mean","recomp_std","hit_mean"])
        for ck, pts in sorted(cells.items()):
            for (pol, W), r in sorted(pts.items()):
                w.writerow([*ck, pol, W, f"{r['p99_mean']:.3f}", f"{r['p99_std']:.3f}",
                            f"{r['recomp_mean']:.0f}", f"{r['recomp_std']:.0f}", f"{r['hit_mean']:.4f}"])

    # Candidate joint-dominance comparisons: for each cell, each bounded-W, vs greedy & vtc, on 2 axes.
    # First collect ALL candidate comparisons (for Bonferroni m).
    dom_rows = []
    candidates = []  # (ck, W, baseline, axis, deltas, mean_delta)
    for ck, pts in cells.items():
        greedy = pts.get(("greedy", 0)); vtc = pts.get(("vtc", 0))
        if not greedy or not vtc: continue
        for W in [1,2,4,8,16,32]:
            b = pts.get(("bounded", W))
            if not b: continue
            for bl_name, bl in [("greedy", greedy), ("vtc", vtc)]:
                # delta = bounded - baseline ; want < 0 (bounded lower = better) on BOTH axes
                d_p99 = [bp - sp for bp, sp in zip(b["p99_seedv"], bl["p99_seedv"])]
                d_rc  = [br - sr for br, sr in zip(b["recomp_seedv"], bl["recomp_seedv"])]
                candidates.append((ck, W, bl_name, "p99", d_p99))
                candidates.append((ck, W, bl_name, "recomp", d_rc))
    m_comparisons = len(candidates)
    # Bonferroni: per-comparison alpha = 0.05 / m
    alpha_bonf = 0.05 / max(1, m_comparisons)
    ci_cache = {}
    def ci_for(deltas, alpha):
        key = (tuple(round(x,6) for x in deltas), round(alpha,10))
        if key not in ci_cache:
            ci_cache[key] = paired_bootstrap_ci(deltas, alpha=alpha)
        return ci_cache[key]

    # Now evaluate joint dominance per (cell, W): need bounded statistically <= BOTH baselines on
    # BOTH axes, with >=1 strict, under Bonferroni.
    joint_wins = []
    detail = []
    for ck, pts in cells.items():
        greedy = pts.get(("greedy", 0)); vtc = pts.get(("vtc", 0))
        if not greedy or not vtc: continue
        for W in [1,2,4,8,16,32]:
            b = pts.get(("bounded", W))
            if not b: continue
            res = {}
            strict_any = False
            ok = True
            for bl_name, bl in [("greedy", greedy), ("vtc", vtc)]:
                d_p99 = [bp - sp for bp, sp in zip(b["p99_seedv"], bl["p99_seedv"])]
                d_rc  = [br - sr for br, sr in zip(b["recomp_seedv"], bl["recomp_seedv"])]
                lo_p, hi_p = ci_for(d_p99, alpha_bonf)
                lo_r, hi_r = ci_for(d_rc, alpha_bonf)
                # <= baseline (not worse): require hi <= 0 means strictly better; for "not worse"
                # we require the CI not to show it's WORSE: lo < 0 boundary. We use a strict
                # dominance definition: better-or-equal on both, strictly better on >=1.
                # better (strict) on axis = hi < 0. not-worse = lo <= 0 (CI doesn't exclude 0 above).
                better_p = hi_p < 0; notworse_p = lo_p <= 0
                better_r = hi_r < 0; notworse_r = lo_r <= 0
                res[bl_name] = dict(d_p99=statistics.mean(d_p99), d_rc=statistics.mean(d_rc),
                                    ci_p99=(lo_p,hi_p), ci_rc=(lo_r,hi_r),
                                    better_p=better_p, notworse_p=notworse_p,
                                    better_r=better_r, notworse_r=notworse_r)
                # dominance vs this baseline: not-worse on both AND strictly better on >=1
                dom_bl = (notworse_p and notworse_r) and (better_p or better_r)
                if not dom_bl: ok = False
                if better_p or better_r: strict_any = True
            detail.append((ck, W, res, ok))
            if ok and strict_any:
                joint_wins.append((ck, W, res))

    with open(os.path.join(RESULTS, "dominance.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["K","skew","B","load","capfam","W",
                    "vs_greedy_dp99","vs_greedy_drc","vs_greedy_ci_p99","vs_greedy_ci_rc",
                    "vs_vtc_dp99","vs_vtc_drc","vs_vtc_ci_p99","vs_vtc_ci_rc","joint_dominates"])
        for ck, W, res, ok in sorted(detail):
            g = res["greedy"]; v = res["vtc"]
            w.writerow([*ck, W,
                f"{g['d_p99']:.2f}", f"{g['d_rc']:.0f}", f"[{g['ci_p99'][0]:.2f},{g['ci_p99'][1]:.2f}]", f"[{g['ci_rc'][0]:.0f},{g['ci_rc'][1]:.0f}]",
                f"{v['d_p99']:.2f}", f"{v['d_rc']:.0f}", f"[{v['ci_p99'][0]:.2f},{v['ci_p99'][1]:.2f}]", f"[{v['ci_rc'][0]:.0f},{v['ci_rc'][1]:.0f}]",
                ok])

    print(f"# Bonferroni m={m_comparisons} comparisons, per-comp alpha={alpha_bonf:.2e}")
    print(f"# JOINT-DOMINANCE win cells (bounded-W beats BOTH greedy AND vtc, both axes, FWER): {len(joint_wins)}")
    for ck, W, res in joint_wins:
        print(f"  WIN cell K={ck[0]} skew={ck[1]} B={ck[2]} load={ck[3]} capfam={ck[4]} W={W}")
        for bl in ("greedy","vtc"):
            r = res[bl]
            print(f"     vs {bl}: dp99={r['d_p99']:.2f} ci={r['ci_p99']}  drc={r['d_rc']:.0f} ci={r['ci_rc']}")
    # also report: in how many cells does greedy dominate vtc (context), and best bounded behavior
    return joint_wins

if __name__ == "__main__":
    main()
