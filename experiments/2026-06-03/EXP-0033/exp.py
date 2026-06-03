#!/usr/bin/env python3
# EXP-0033 / CLAIM-0037 -- online failure-foreshadow signature vs self-confidence + generic-difficulty.
# L0: CPU-only, stdlib-only, SERIAL. Anti-circular: monitor reads ONLY noisy observables,
# never latent health/difficulty/label. See PRE_REGISTRATION.md.
import random, math, csv, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)

T_STEPS = 20
DEATH_THR = -1.0
N_TRAJ = 400
EARLY_FRAC = 0.5
SEEDS = list(range(8))
TARGET_FLAG = 0.30

def gen_trajectory(rng, difficulty, frac_foreshadowed, sigma, rho, p_abrupt_base=0.5):
    h0 = rng.gauss(0.6 - rho*difficulty, 0.25)
    will_degrade = rng.random() < (0.15 + 0.55*difficulty)
    mech = rng.choice(["toolerr","loop","starve"])
    h = h0
    obs = []; latent_h = []; term_step = T_STEPS-1; failed = None; abrupt_step = None
    p_abrupt = p_abrupt_base*(1.0-frac_foreshadowed) + 0.01
    if rng.random() < p_abrupt:
        abrupt_step = rng.randint(2, T_STEPS-1)
    for t in range(T_STEPS):
        drift = -(0.06+0.10*difficulty) if will_degrade else 0.02
        h = h + drift + rng.gauss(0,0.08)
        latent_h.append(h)
        hp = max(0.0, min(1.0, 0.5+0.4*h))
        te_rate = (1-hp)*0.6 + (0.2 if mech=="toolerr" and will_degrade else 0.0)
        te = 1 if rng.random() < min(0.95, te_rate + rng.gauss(0,sigma)*0.1) else 0
        loop = max(0.0,min(1.0,(1-hp)*0.7 + (0.2 if mech=="loop" and will_degrade else 0.0) + rng.gauss(0,sigma)*0.15))
        info = max(0.0,min(1.0, hp*0.8 - (0.2 if mech=="starve" and will_degrade else 0.0) + rng.gauss(0,sigma)*0.15))
        obs.append((te,loop,info,t))
        if abrupt_step is not None and t == abrupt_step:
            failed=True; term_step=t; break
        if h < DEATH_THR:
            failed=True; term_step=t; break
    if failed is None:
        failed = (h < -0.3) or (rng.random() < 0.05*difficulty)
        term_step = T_STEPS-1
    return dict(obs=obs, latent_h=latent_h, failed=failed, term_step=term_step,
                difficulty=difficulty,
                abrupt=(abrupt_step is not None and failed and term_step==abrupt_step),
                will_degrade=will_degrade)

def monitor_scores(obs):
    alpha=0.4; s=0.0; out=[]; init=False
    for (te,loop,info,t) in obs:
        inst = te*0.5 + loop*0.5 - info*0.5
        if not init: s=inst; init=True
        else: s = alpha*inst + (1-alpha)*s
        out.append(s)
    return out

def confidence_scores(traj, rng, sigma_conf):
    return [-(h + rng.gauss(0,sigma_conf)) for h in traj["latent_h"]]

def difficulty_score(traj, rng, sigma_diff):
    d_est = traj["difficulty"] + rng.gauss(0,sigma_diff)
    te0,loop0,info0,_ = traj["obs"][0]
    return d_est*1.0 + te0*0.3 + loop0*0.3 - info0*0.3

def oracle_score(traj):
    return -min(traj["latent_h"])

def auc(scores, labels):
    pos=[s for s,l in zip(scores,labels) if l]; neg=[s for s,l in zip(scores,labels) if not l]
    if not pos or not neg: return 0.5
    wins=0.0; n=0
    for p in pos:
        for q in neg:
            n+=1
            if p>q: wins+=1
            elif p==q: wins+=0.5
    return wins/n

def early_window_score(per_step, term_step):
    k=max(1,int(math.ceil((term_step+1)*EARLY_FRAC)))
    return max(per_step[:k])

def first_fire_step(per_step, thr):
    for t,s in enumerate(per_step):
        if s>=thr: return t
    return None

def percentile(vals,p):
    if not vals: return float('nan')
    v=sorted(vals); k=(len(v)-1)*p; f=math.floor(k); c=math.ceil(k)
    if f==c: return v[int(k)]
    return v[f]*(c-k)+v[c]*(k-f)

def run_cell_seed(frac, sigma, rho, seed):
    rng=random.Random(seed*7919 + int(frac*100)*31 + int(sigma*100)*13 + int(rho*100))
    trajs=[]
    for _ in range(N_TRAJ):
        d=rng.random()
        trajs.append(gen_trajectory(rng,d,frac,sigma,rho))
    labels=[t["failed"] for t in trajs]
    mon_steps=[monitor_scores(t["obs"]) for t in trajs]
    conf_steps=[confidence_scores(t, random.Random(seed*131+i), 0.35) for i,t in enumerate(trajs)]
    diff_static=[difficulty_score(t, random.Random(seed*977+i), 0.30) for i,t in enumerate(trajs)]
    orc=[oracle_score(t) for t in trajs]
    mon_early=[early_window_score(ms,t["term_step"]) for ms,t in zip(mon_steps,trajs)]
    conf_early=[early_window_score(cs,t["term_step"]) for cs,t in zip(conf_steps,trajs)]
    auc_mon=auc(mon_early,labels); auc_conf=auc(conf_early,labels)
    auc_diff=auc(diff_static,labels); auc_orc=auc(orc,labels)
    thr_mon=percentile([max(ms) for ms in mon_steps], 1-TARGET_FLAG)
    thr_conf=percentile([max(cs) for cs in conf_steps], 1-TARGET_FLAG)
    leads_mon=[]; leads_conf=[]; n_fail=0; n_mon_early=0
    for ms,cs,t in zip(mon_steps,conf_steps,trajs):
        if not t["failed"]: continue
        n_fail+=1
        ff=first_fire_step(ms,thr_mon)
        if ff is not None:
            leads_mon.append(t["term_step"]-ff)
            if t["term_step"]-ff>=1: n_mon_early+=1
        cf=first_fire_step(cs,thr_conf)
        if cf is not None: leads_conf.append(t["term_step"]-cf)
    return dict(frac=frac,sigma=sigma,rho=rho,seed=seed,
        fail_rate=sum(labels)/len(labels),
        auc_mon=auc_mon,auc_conf=auc_conf,auc_diff=auc_diff,auc_oracle=auc_orc,
        d_mon_conf=auc_mon-auc_conf, d_mon_diff=auc_mon-auc_diff,
        med_lead_mon=(percentile(leads_mon,0.5) if leads_mon else float('nan')),
        med_lead_conf=(percentile(leads_conf,0.5) if leads_conf else float('nan')),
        frac_mon_early=(n_mon_early/n_fail) if n_fail else float('nan'),
        n_fail=n_fail)

def bootstrap_ci(vals, B=2000, seed=12345):
    rng=random.Random(seed); n=len(vals)
    if n==0: return (float('nan'),float('nan'))
    means=[]
    for _ in range(B):
        s=[vals[rng.randrange(n)] for _ in range(n)]
        means.append(sum(s)/n)
    means.sort()
    return (means[int(0.025*B)], means[int(0.975*B)])

def main():
    cells=[(f,s,r) for f in (0.2,0.5,0.8) for s in (0.3,0.8) for r in (0.0,0.6)]
    rows=[]
    for (f,s,r) in cells:
        for seed in SEEDS:
            rows.append(run_cell_seed(f,s,r,seed))
    raw=os.path.join(OUT,"raw_results.csv")
    with open(raw,"w",newline="") as fh:
        w=csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader()
        for row in rows: w.writerow(row)
    # per-cell aggregate + global
    agg=os.path.join(OUT,"agg_by_cell.csv")
    with open(agg,"w",newline="") as fh:
        cols=["frac","sigma","rho","n_seed","fail_rate","auc_mon","auc_conf","auc_diff","auc_oracle",
              "d_mon_conf","ci_lo_mc","ci_hi_mc","d_mon_diff","ci_lo_md","ci_hi_md",
              "med_lead_mon","med_lead_conf","frac_mon_early"]
        w=csv.DictWriter(fh,fieldnames=cols); w.writeheader()
        for (f,s,r) in cells:
            grp=[x for x in rows if x["frac"]==f and x["sigma"]==s and x["rho"]==r]
            def m(k): return sum(x[k] for x in grp)/len(grp)
            mc=[x["d_mon_conf"] for x in grp]; md=[x["d_mon_diff"] for x in grp]
            lo_mc,hi_mc=bootstrap_ci(mc); lo_md,hi_md=bootstrap_ci(md)
            w.writerow(dict(frac=f,sigma=s,rho=r,n_seed=len(grp),
                fail_rate=round(m("fail_rate"),3),
                auc_mon=round(m("auc_mon"),3),auc_conf=round(m("auc_conf"),3),
                auc_diff=round(m("auc_diff"),3),auc_oracle=round(m("auc_oracle"),3),
                d_mon_conf=round(m("d_mon_conf"),3),ci_lo_mc=round(lo_mc,3),ci_hi_mc=round(hi_mc,3),
                d_mon_diff=round(m("d_mon_diff"),3),ci_lo_md=round(lo_md,3),ci_hi_md=round(hi_md,3),
                med_lead_mon=round(m("med_lead_mon"),2),med_lead_conf=round(m("med_lead_conf"),2),
                frac_mon_early=round(m("frac_mon_early"),3)))
    # global pooled CI on deltas (across all rows)
    allmc=[x["d_mon_conf"] for x in rows]; allmd=[x["d_mon_diff"] for x in rows]
    g_lo_mc,g_hi_mc=bootstrap_ci(allmc); g_lo_md,g_hi_md=bootstrap_ci(allmd)
    glob=os.path.join(OUT,"global_summary.csv")
    with open(glob,"w",newline="") as fh:
        w=csv.writer(fh)
        w.writerow(["metric","value"])
        w.writerow(["n_rows",len(rows)])
        w.writerow(["mean_auc_mon",round(sum(x["auc_mon"] for x in rows)/len(rows),4)])
        w.writerow(["mean_auc_conf",round(sum(x["auc_conf"] for x in rows)/len(rows),4)])
        w.writerow(["mean_auc_diff",round(sum(x["auc_diff"] for x in rows)/len(rows),4)])
        w.writerow(["mean_auc_oracle",round(sum(x["auc_oracle"] for x in rows)/len(rows),4)])
        w.writerow(["mean_d_mon_conf",round(sum(allmc)/len(allmc),4)])
        w.writerow(["ci_d_mon_conf_lo",round(g_lo_mc,4)])
        w.writerow(["ci_d_mon_conf_hi",round(g_hi_mc,4)])
        w.writerow(["mean_d_mon_diff",round(sum(allmd)/len(allmd),4)])
        w.writerow(["ci_d_mon_diff_lo",round(g_lo_md,4)])
        w.writerow(["ci_d_mon_diff_hi",round(g_hi_md,4)])
        w.writerow(["mean_med_lead_mon",round(sum(x["med_lead_mon"] for x in rows if x["med_lead_mon"]==x["med_lead_mon"])/len(rows),3)])
        w.writerow(["mean_frac_mon_early",round(sum(x["frac_mon_early"] for x in rows)/len(rows),4)])
    print("DONE rows=",len(rows))
    print("wrote",raw,agg,glob)

if __name__=="__main__":
    main()
