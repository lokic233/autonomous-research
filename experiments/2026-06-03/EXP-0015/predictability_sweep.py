#!/usr/bin/env python3
"""Honest predictability frontier: abandonment is partly latent-determined (hazard_strength) and
partly irreducible noise. We sweep hazard_strength to show WHEN a cheap pre-completion predictor can
reach AUC bands {0.6,0.7,0.8}, and report the oracle ceiling alongside. This makes the conditionality
explicit: predictability is a property of the WORKLOAD, not just the predictor. CPU/stdlib/serial."""
import sys,os,random,statistics,csv,math
sys.path.insert(0,"/Users/dengcchi/autonomous-research-v3/experiments/2026-06-03/EXP-0015")
import harness as H
OUT=H.OUT

def gen_turn(rng, p_abandon, timing, hazard_strength):
    d=rng.random(); f=rng.random(); bv=rng.random()
    L=max(8,int(math.exp(rng.gauss(math.log(120),0.6))))
    hz=0.45*d+0.35*f+0.20*(1-bv)              # in [0,1], mean ~0.5
    # abandonment prob: blend irreducible base p_abandon with hazard-driven component.
    # hazard_strength in [0,1]: 0 -> pure coin flip (unpredictable); 1 -> strongly latent-driven.
    pa = (1-hazard_strength)*p_abandon + hazard_strength*(p_abandon*2*hz)
    pa=min(0.98,max(0.0,pa))
    ab = rng.random()<pa
    astep=None
    if ab:
        if timing=="early": frac=rng.betavariate(1.5,5)
        elif timing=="mid": frac=rng.betavariate(3,3)
        elif timing=="late": frac=rng.betavariate(5,1.5)
        else: frac=rng.random()
        astep=max(1,int(frac*L))
    decoded=L if not ab else astep
    return {"L_plan":L,"abandoned":ab,"abandon_step":astep,"decoded":decoded,
            "latent_difficulty":d,"latent_tool_fragility":f,"latent_branch_value":bv,
            "retry_count":(1 if (f>0.6 and rng.random()<0.5) else 0)}

def gen_ep(seed,p,timing,hs):
    rng=random.Random(seed*1000003 + (hash((p,timing,hs))%100000))
    return [gen_turn(rng,p,timing,hs) for _ in range(H.N_TURNS_PER_EPISODE)]

def obs(rng,t,step,sigma):
    d=t["latent_difficulty"];f=t["latent_tool_fragility"];bv=t["latent_branch_value"]
    return [0.45*d+0.0008*step+rng.gauss(0,sigma),
            0.35*f+rng.gauss(0,sigma),
            0.20*(1-bv)+rng.gauss(0,sigma),
            t["retry_count"]*0.15+rng.gauss(0,sigma*0.5)]

def feats_labels(rng,turns,sigma):
    F=[];L=[];M=[];run=[]
    for t in turns:
        Lp=t["L_plan"];tm=max(2,int(H.PREFIX_FRAC*Lp));ot=tm
        if t["abandoned"] and t["abandon_step"]<tm: ot=t["abandon_step"]
        o=obs(rng,t,ot,sigma); run.append(Lp); o.append(ot/(statistics.mean(run)+1e-9))
        F.append(o);L.append(1 if t["abandoned"] else 0)
        M.append({"ot":ot,"as":t["abandon_step"],"ab":t["abandoned"]})
    return F,L,M

def run():
    rows=[]
    sigma=0.10  # low obs noise so we isolate WORKLOAD predictability
    p=0.30
    for hs in [0.0,0.25,0.5,0.75,1.0]:
        # oracle ceiling
        osc=[];olb=[]
        for s in H.SEEDS:
            for t in gen_ep(s,p,"mixed",hs):
                hz=0.45*t["latent_difficulty"]+0.35*t["latent_tool_fragility"]+0.20*(1-t["latent_branch_value"])
                osc.append(hz);olb.append(1 if t["abandoned"] else 0)
        oracle=H.auc(osc,olb)
        # observable predictor, held-out
        trf=[];trl=[]
        for s in H.TRAIN_SEEDS:
            rng=random.Random(7777+s); F,L,M=feats_labels(rng,gen_ep(s,p,"mixed",hs),sigma); trf+=F;trl+=L
        w,mu,sd=H.fit_weights(trf,trl); trs=H.score(trf,w,mu,sd); thr=sorted(trs)[int(0.80*len(trs))]
        tes=[];tel=[];leads=[]
        for s in H.TEST_SEEDS:
            rng=random.Random(8888+s); F,L,M=feats_labels(rng,gen_ep(s,p,"mixed",hs),sigma); sc=H.score(F,w,mu,sd)
            tes+=sc;tel+=L
            for si,mi in zip(sc,M):
                if mi["ab"] and si>thr: leads.append(mi["as"]-mi["ot"])
        a=H.auc(tes,tel)
        flg=[(sc,l) for sc,l in zip(tes,tel) if sc>thr]
        prec=sum(l for _,l in flg)/len(flg) if flg else float('nan')
        rec=sum(l for _,l in flg)/sum(tel) if sum(tel) else float('nan')
        rows.append({"hazard_strength":hs,"p_abandon":p,"obs_noise":sigma,
            "oracle_auc":round(oracle,4),"observable_auc":round(a,4),
            "flag_precision":round(prec,4),"flag_recall":round(rec,4),
            "median_lead_tokens":round(statistics.median(leads),1) if leads else "nan",
            "frac_positive_lead":round(sum(1 for x in leads if x>0)/len(leads),3) if leads else "nan"})
    with open(os.path.join(OUT,"B2_predictability_frontier.csv"),"w",newline="") as fh:
        wr=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
    return rows

if __name__=="__main__":
    for r in run(): print(r)
