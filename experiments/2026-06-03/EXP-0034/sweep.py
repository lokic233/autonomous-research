#!/usr/bin/env python3
# EXP-0034 / CLAIM-0037 -- sigma_conf flip-point sweep.
# REUSES EXP-0033's model UNCHANGED (imports exp.py). CPU, stdlib, SERIAL.
# Only change vs EXP-0033: confidence baseline re-scored across a sigma_conf grid;
# monitor & difficulty are independent of sigma_conf and held fixed.
import random, math, csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
E33 = os.path.join(os.path.dirname(HERE), "EXP-0033")
sys.path.insert(0, E33)
import exp as m  # reuse gen_trajectory, monitor_scores, confidence_scores, difficulty_score,
                 # oracle_score, auc, early_window_score, bootstrap_ci, percentile, N_TRAJ, SEEDS

OUT = os.path.join(HERE, "results"); os.makedirs(OUT, exist_ok=True)

SIGMA_CONF_GRID = [0.10, 0.20, 0.35, 0.50, 0.70, 0.90, 1.20, 1.60, 2.00]
CELLS = [(f,s,r) for f in (0.2,0.5,0.8) for s in (0.3,0.8) for r in (0.0,0.6)]

def run_cell_seed_multi(frac, sigma, rho, seed):
    """Identical trajectory generation to EXP-0033.run_cell_seed, but returns per-sigma_conf
    confidence AUCs (monitor/difficulty computed once)."""
    rng = random.Random(seed*7919 + int(frac*100)*31 + int(sigma*100)*13 + int(rho*100))
    trajs = []
    for _ in range(m.N_TRAJ):
        d = rng.random()
        trajs.append(m.gen_trajectory(rng, d, frac, sigma, rho))
    labels = [t["failed"] for t in trajs]
    mon_steps = [m.monitor_scores(t["obs"]) for t in trajs]
    diff_static = [m.difficulty_score(t, random.Random(seed*977+i), 0.30) for i,t in enumerate(trajs)]
    orc = [m.oracle_score(t) for t in trajs]
    mon_early = [m.early_window_score(ms, t["term_step"]) for ms,t in zip(mon_steps, trajs)]
    auc_mon = m.auc(mon_early, labels)
    auc_diff = m.auc(diff_static, labels)
    auc_orc = m.auc(orc, labels)
    out = {}
    for sc in SIGMA_CONF_GRID:
        # SAME RNG seeding pattern as EXP-0033 (seed*131+i) so sigma_conf=0.35 reproduces EXP-0033.
        conf_steps = [m.confidence_scores(t, random.Random(seed*131+i), sc) for i,t in enumerate(trajs)]
        conf_early = [m.early_window_score(cs, t["term_step"]) for cs,t in zip(conf_steps, trajs)]
        auc_conf = m.auc(conf_early, labels)
        out[sc] = dict(auc_conf=auc_conf, d_mon_conf=auc_mon-auc_conf)
    return dict(frac=frac, sigma=sigma, rho=rho, seed=seed,
                auc_mon=auc_mon, auc_diff=auc_diff, auc_oracle=auc_orc, per_sc=out)

def main():
    rows = []
    for (f,s,r) in CELLS:
        for seed in m.SEEDS:
            rows.append(run_cell_seed_multi(f,s,r,seed))
    # per-row raw for sigma_conf=0.35 sanity (must match EXP-0033)
    auc_mon_mean = sum(x["auc_mon"] for x in rows)/len(rows)
    auc_diff_mean = sum(x["auc_diff"] for x in rows)/len(rows)
    auc_orc_mean = sum(x["auc_oracle"] for x in rows)/len(rows)

    sweep_path = os.path.join(OUT, "sweep_sigma_conf.csv")
    flip = {"equal": None, "beat": None}
    with open(sweep_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sigma_conf","mean_auc_mon","mean_auc_conf","mean_d_mon_conf",
                    "ci_lo","ci_hi","ci_excludes_zero_above","ci_includes_zero","n_rows"])
        for sc in SIGMA_CONF_GRID:
            deltas = [x["per_sc"][sc]["d_mon_conf"] for x in rows]
            confs  = [x["per_sc"][sc]["auc_conf"] for x in rows]
            mean_d = sum(deltas)/len(deltas)
            mean_conf = sum(confs)/len(confs)
            lo, hi = m.bootstrap_ci(deltas, B=2000, seed=12345)
            includes_zero = (lo <= 0.0 <= hi)
            above_zero = (lo > 0.0)
            if flip["equal"] is None and (includes_zero or above_zero):
                flip["equal"] = sc
            if flip["beat"] is None and above_zero:
                flip["beat"] = sc
            w.writerow([sc, round(auc_mon_mean,4), round(mean_conf,4), round(mean_d,4),
                        round(lo,4), round(hi,4), above_zero, includes_zero, len(deltas)])

    # summary
    summ = os.path.join(OUT, "flip_summary.csv")
    with open(summ, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["metric","value"])
        w.writerow(["mean_auc_mon", round(auc_mon_mean,4)])
        w.writerow(["mean_auc_diff", round(auc_diff_mean,4)])
        w.writerow(["mean_auc_oracle", round(auc_orc_mean,4)])
        w.writerow(["equal_point_sigma_conf", flip["equal"]])
        w.writerow(["beat_point_sigma_conf", flip["beat"]])
        w.writerow(["exp33_ref_sigma_conf", 0.35])
        w.writerow(["n_rows_per_sigma", len(rows)])
    print("DONE rows=", len(rows), "equal=", flip["equal"], "beat=", flip["beat"])
    print("auc_mon=", round(auc_mon_mean,4))
    print("wrote", sweep_path, summ)

if __name__ == "__main__":
    main()
