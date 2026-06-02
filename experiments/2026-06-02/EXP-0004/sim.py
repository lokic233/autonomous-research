#!/usr/bin/env python3
"""EXP-0004 L0: analytic + Monte-Carlo model of speculative tool-call prefetch.
CLAIM-0003. Stdlib only. CPU only. See PRE_REGISTRATION.md for the model."""
import json, math, random, statistics, os, csv

ART = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ART, "results")
os.makedirs(RES, exist_ok=True)

# Fixed normalization
T_ARGS = 1.0
T_NAME = 0.1
COMMIT_FRAC = 0.05  # c_commit = COMMIT_FRAC * t_args

# Sweep grids
P_GRID    = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
R_GRID    = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0]   # t_tool/t_args
LEAD_GRID = [0.3, 0.5, 0.7]
W_GRID    = [0.5, 1.0]
SEEDS     = [11, 22, 33, 44, 55]
SIGMA     = 0.15   # lognormal multiplicative jitter
N_TRIALS_PER_SEED = 4000

def analytic(p, r, lead, w):
    t_args, t_name, t_tool = T_ARGS, T_NAME, r * T_ARGS
    c = COMMIT_FRAC * t_args
    rem = (1 - lead) * t_args
    T_base = t_name + t_args + t_tool
    T_correct = t_name + lead*t_args + max(rem, t_tool) + c
    T_wrong   = t_name + t_args + t_tool + w*t_tool
    E_spec = p*T_correct + (1-p)*T_wrong
    S = T_base - T_correct           # gain when correct
    P = T_wrong - T_base             # penalty when wrong (= w*t_tool)
    # break-even p* where E_spec == T_base  ->  -p*S + (1-p)*P = 0 -> p* = P/(S+P)
    pstar = P / (S + P) if (S + P) > 0 else float('inf')
    return dict(T_base=T_base, T_correct=T_correct, T_wrong=T_wrong,
                E_spec=E_spec, S=S, P=P, pstar=pstar,
                wins=(E_spec < T_base), speedup=(T_base/E_spec))

def lognorm(rng, mean, sigma):
    # multiplicative lognormal noise with E~=mean (mu shift to keep mean ~ mean)
    mu = math.log(max(mean,1e-9)) - 0.5*sigma*sigma
    return math.exp(rng.gauss(mu, sigma))

def monte_carlo(p, r, lead, w, seed):
    rng = random.Random(seed)
    base_tot = 0.0; spec_tot = 0.0
    for _ in range(N_TRIALS_PER_SEED):
        t_args = lognorm(rng, T_ARGS, SIGMA)
        t_name = lognorm(rng, T_NAME, SIGMA)
        t_tool = lognorm(rng, r*T_ARGS, SIGMA)
        c = COMMIT_FRAC * t_args
        rem = (1-lead)*t_args
        T_base = t_name + t_args + t_tool
        correct = rng.random() < p
        if correct:
            T_spec = t_name + lead*t_args + max(rem, t_tool) + c
        else:
            T_spec = t_name + t_args + t_tool + w*t_tool
        base_tot += T_base; spec_tot += T_spec
    return base_tot/N_TRIALS_PER_SEED, spec_tot/N_TRIALS_PER_SEED

rows = []
for r in R_GRID:
    for lead in LEAD_GRID:
        for w in W_GRID:
            for p in P_GRID:
                a = analytic(p, r, lead, w)
                mc_base = []; mc_spec = []
                for s in SEEDS:
                    b, sp = monte_carlo(p, r, lead, w, s)
                    mc_base.append(b); mc_spec.append(sp)
                mb = statistics.mean(mc_base); sb = statistics.pstdev(mc_base)
                ms = statistics.mean(mc_spec); ss = statistics.pstdev(mc_spec)
                rows.append(dict(
                    r=r, lead=lead, w=w, p=p,
                    T_base=round(a['T_base'],4),
                    E_spec_analytic=round(a['E_spec'],4),
                    mc_base_mean=round(mb,4), mc_base_std=round(sb,4),
                    mc_spec_mean=round(ms,4), mc_spec_std=round(ss,4),
                    pstar=round(a['pstar'],4),
                    wins=a['wins'],
                    speedup=round(a['speedup'],4),
                    S=round(a['S'],4), P=round(a['P'],4),
                ))

# Write raw CSV
csv_path = os.path.join(RES, "sweep.csv")
with open(csv_path, "w", newline="") as f:
    wri = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    wri.writeheader(); wri.writerows(rows)

# Break-even curve: pstar as function of (r, lead, w) — independent of p
becurve = []
for r in R_GRID:
    for lead in LEAD_GRID:
        for w in W_GRID:
            a = analytic(0.0, r, lead, w)  # pstar independent of p
            becurve.append(dict(r=r, lead=lead, w=w, pstar=round(a['pstar'],4),
                                S=round(a['S'],4), P=round(a['P'],4),
                                feasible=(a['pstar'] <= 1.0 and a['S'] > 0)))
be_path = os.path.join(RES, "breakeven.csv")
with open(be_path, "w", newline="") as f:
    wri = csv.DictWriter(f, fieldnames=list(becurve[0].keys()))
    wri.writeheader(); wri.writerows(becurve)

# Summary stats
total = len(rows)
wins = sum(1 for x in rows if x['wins'])
# realistic regime: tool latency comparable-or-bigger than arg decode (r>=1)
real = [x for x in rows if x['r'] >= 1.0]
real_wins = sum(1 for x in real if x['wins'])
# break-even feasibility
be_feasible = sum(1 for x in becurve if x['feasible'])
# what p* is needed in the realistic regime
real_pstars = sorted(set(x['pstar'] for x in becurve if x['r'] >= 1.0))

summary = dict(
    total_configs=total, wins=wins, win_frac=round(wins/total,3),
    realistic_configs=len(real), realistic_wins=real_wins,
    realistic_win_frac=round(real_wins/len(real),3),
    breakeven_feasible=be_feasible, breakeven_total=len(becurve),
    realistic_pstar_min=min(x['pstar'] for x in becurve if x['r']>=1.0),
    realistic_pstar_max=max(x['pstar'] for x in becurve if x['r']>=1.0),
    realistic_pstars=real_pstars,
)
with open(os.path.join(RES, "summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

print(json.dumps(summary, indent=2))
print("\n# MC vs analytic max abs diff (validation):")
mxd = max(abs(x['E_spec_analytic']-x['mc_spec_mean']) for x in rows)
print("  max |analytic - MC| spec =", round(mxd,4))
