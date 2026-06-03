import time, csv, statistics, math
from harness import run_cell, ci95

t0 = time.time()
Ks = [3,5,10,20,50]
temps = [0.05, 0.15, 0.40]   # >=3 temps (anti-tuned-knob)
sigmas = [0.10, 0.30]        # >=2 noise levels
SEEDS = list(range(8))       # >=8 seeds
N = 500                      # requests per trial

# Escape prior: a FIXED flat affinity for 'other'. Set so escape competes with concrete distractors.
# The nearest-in-enum logit on oos ~ -gap_to_nearest/temp. A flat esc_prior means escape wins when the
# nearest concrete distractor is far (logit very negative) and loses when it's close (logit near 0).
# Pick esc_prior per temp so it sits in the operative range: esc_prior = -0.18/temp (a "0.18 effective dist").
def esc_prior_for(temp):
    return -0.18/temp

# ---- K-curve robustness across temp x sigma (GUARD 1) ----
rows = []
for temp in temps:
    for sigma in sigmas:
        for K in Ks:
            mvals, gvals, monvals = [], [], []
            for s in SEEDS:
                r = run_cell(K, temp, sigma, seed=1000+s, n_requests=N)
                mvals.append(r['misroute_rate']); gvals.append(r['gad_recovery']); monvals.append(r['monitor_recall'])
            mm, mci = ci95(mvals)
            gm, gci = ci95(gvals)
            rows.append(dict(temp=temp, sigma=sigma, K=K,
                             misroute_mean=round(mm,4), misroute_ci=round(mci,4),
                             gad_recovery_mean=round(gm,5), gad_recovery_ci=round(gci,5),
                             monitor_recall=round(statistics.mean(monvals),5)))
            print(f"temp={temp} sigma={sigma} K={K:2d}  misroute={mm:.3f}±{mci:.3f}  gad_rec={gm:.4f}  mon_recall={statistics.mean(monvals):.3f}")

with open('results/misroute_vs_K_robustness.csv','w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

print("\n--- escape-recall vs proximity (gap bins), K=10, multiple temps ---")
# escape recall by gap bin, aggregated over seeds, at a fixed K
esc_rows = []
gap_labels = ["<=0.10","<=0.20","<=0.30","<=0.45",">0.45"]
for temp in temps:
    for sigma in sigmas:
        agg = [[] for _ in gap_labels]
        for s in SEEDS:
            r = run_cell(10, temp, sigma, seed=2000+s, n_requests=N, esc_prior=esc_prior_for(temp))
            for k,v in enumerate(r['esc_recall_by_bin']):
                if v is not None: agg[k].append(v)
        means = [round(statistics.mean(a),3) if a else None for a in agg]
        esc_rows.append(dict(temp=temp, sigma=sigma, **{gap_labels[k]:means[k] for k in range(len(gap_labels))}))
        print(f"temp={temp} sigma={sigma}  esc_recall by gap (near->far): {means}")

with open('results/escape_recall_vs_proximity.csv','w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(esc_rows[0].keys())); w.writeheader(); w.writerows(esc_rows)

print(f"\nelapsed {time.time()-t0:.1f}s")
