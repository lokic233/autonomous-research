#!/usr/bin/env python3
"""Fix B (make noise the binding AUC knob; tune feature->latent coupling so AUC spans 0.6/0.7/0.8)
and C (model the REAL reclaim lever honestly: early-flag enables EARLY TERMINATION of confirmed-doomed
turns once abandonment is observed AT abandon_step, instead of letting the system continue scheduling
the turn's slot up to abandon_step regardless. The reclaim = decode slots saved by terminating a
*flagged* abandoned turn at the moment of confirmation vs a non-flag baseline that only learns at
abandon_step too — so the genuine, honest reclaim is the SCHEDULING reclaim: a deprioritized abandoned
turn yields batch slots to completed turns BEFORE it self-terminates, shrinking completed-turn latency.

Honest reframing for C: with no online kill, total decoded-doomed-tokens is FIXED (=abandon_step). The
only lever is WHICH turns occupy scarce batch slots WHEN. So the right C metric is: does deprioritizing
flagged turns (bounded-W) IMPROVE completed-turn p99 (because completed turns get slots sooner) WITHOUT
harming FP turns beyond budget? If batch isn't the bottleneck (B>=offered load) there's nothing to
reclaim -> honest negative-by-non-bottleneck. We test under a CONTENDED batch (small B, bursty admit)."""
import sys, os, random, statistics, csv, math
sys.path.insert(0,"/Users/dengcchi/autonomous-research-v3/experiments/2026-06-03/EXP-0015")
import harness as H
OUT=H.OUT

# ---- B fix: stronger latent->observable coupling so NOISE is the binding constraint ----
def observables_v2(rng, turn, t, sigma):
    d=turn["latent_difficulty"]; f=turn["latent_tool_fragility"]; bv=turn["latent_branch_value"]
    # the hazard the LABEL uses: 0.45 d + 0.35 f + 0.20 (1-bv). Make observables noisy reads of the
    # SAME latents (NOT the label, NOT the hazard variable, NOT abandon_step) so AUC can be high at low
    # noise and degrade with sigma. This is causal: observables are downstream of latents, label is too,
    # but predictor never reads label/hazard/abandon_step.
    o1=0.45*d + 0.0008*t + rng.gauss(0,sigma)          # entropy ~ difficulty
    o2=0.35*f + rng.gauss(0,sigma)                      # malformation ~ fragility
    o3=0.20*(1-bv) + rng.gauss(0,sigma)                 # prune-risk ~ low branch value
    o4=turn["retry_count"]*0.15 + rng.gauss(0,sigma*0.5)
    return o1,o2,o3,o4

def featurize_v2(rng, turns, sigma):
    feats=[]; labels=[]; meta=[]; running=[]
    for tn in turns:
        L=tn["L_plan"]; t_meas=max(2,int(H.PREFIX_FRAC*L))
        obs_t=t_meas
        if tn["abandoned"] and tn["abandon_step"]<t_meas: obs_t=tn["abandon_step"]
        o1,o2,o3,o4=observables_v2(rng,tn,obs_t,sigma)
        running.append(L); base=statistics.mean(running)
        o5=obs_t/(base+1e-9)
        feats.append([o1,o2,o3,o4,o5]); labels.append(1 if tn["abandoned"] else 0)
        meta.append({"obs_t":obs_t,"abandon_step":tn["abandon_step"],"L":L,"abandoned":tn["abandoned"]})
    return feats,labels,meta

def part_B_v2(noise_grid=(0.05,0.20,0.60)):
    rows=[]
    for sigma in noise_grid:
        for p in H.P_ABANDON_GRID:
            tr_f=[]; tr_l=[]
            for s in H.TRAIN_SEEDS:
                rng=random.Random(7777+s); turns=H.gen_episode(s,p,"mixed")
                f,l,m=featurize_v2(rng,turns,sigma); tr_f+=f; tr_l+=l
            w,mu,sd=H.fit_weights(tr_f,tr_l)
            tr_s=H.score(tr_f,w,mu,sd); thr=sorted(tr_s)[int(0.80*len(tr_s))]
            te_s=[]; te_l=[]; leads=[]
            for s in H.TEST_SEEDS:
                rng=random.Random(8888+s); turns=H.gen_episode(s,p,"mixed")
                f,l,m=featurize_v2(rng,turns,sigma); sc=H.score(f,w,mu,sd)
                te_s+=sc; te_l+=l
                for si,mi in zip(sc,m):
                    if mi["abandoned"] and si>thr: leads.append(mi["abandon_step"]-mi["obs_t"])
            a=H.auc(te_s,te_l)
            flagged=[(sc,l) for sc,l in zip(te_s,te_l) if sc>thr]
            prec=(sum(l for _,l in flagged)/len(flagged)) if flagged else float('nan')
            rec=(sum(l for _,l in flagged)/sum(te_l)) if sum(te_l) else float('nan')
            rows.append({"noise_sigma":sigma,"p_abandon":p,"test_auc":round(a,4),
                "flag_precision":round(prec,4),"flag_recall":round(rec,4),
                "median_lead_tokens":round(statistics.median(leads),1) if leads else "nan",
                "frac_positive_lead":round(sum(1 for x in leads if x>0)/len(leads),3) if leads else "nan",
                "n_flagged_abandoned":len(leads)})
    with open(os.path.join(OUT,"B_predictor_auc_leadtime.csv"),"w",newline="") as fh:
        wr=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
    return rows

# ---- C fix: CONTENDED batch + EARLY-TERMINATION reclaim ----
# Two reclaim levers, both honest:
#  (1) SCHEDULING: deprioritize flagged turns under contention -> completed turns finish sooner.
#  (2) EARLY-TERM: a flagged turn, once it actually self-terminates (reaches abandon_step), we STOP;
#      baseline ALSO stops at abandon_step (an abandoned turn emits abandon_step tokens then stops).
#      So early-term gives NO token reclaim with pure deferral. The ONLY honest reclaim is scheduling
#      reclaim measured as completed-turn p99 improvement under contention. We report it straight.
def sim(turns, flagged, W, B, admit_rate):
    n=len(turns)
    need=[t["decoded"] for t in turns]; is_ab=[t["abandoned"] for t in turns]
    prog=[0]*n; admit_t=[None]*n; active=[]; nxt=0; tick=0
    comp=[]; fp=[]; abslot=0
    MAX=int(sum(need)/min(B,1 if B==0 else B))+n*(W+3)+200
    while True:
        # bursty admit: admit_rate turns per tick (contention if > B drain)
        adm=0
        while len(active)<B and nxt<n and adm<admit_rate:
            admit_t[nxt]=tick; active.append(nxt); nxt+=1; adm+=1
        if not active and nxt>=n: break
        still=[]
        for i in active:
            dep=flagged[i]
            advance=(not dep) or (W==0) or (tick%(1+W)==0)
            if advance:
                prog[i]+=1
                if is_ab[i]: abslot+=1
            if prog[i]>=need[i]:
                lat=tick-admit_t[i]+1
                if not is_ab[i]:
                    comp.append(lat)
                    if flagged[i]: fp.append(lat)
            else: still.append(i)
        active=still; tick+=1
        if tick>MAX: break
    return comp,fp,abslot

def pct(xs,q):
    if not xs: return float('nan')
    xs=sorted(xs); k=min(len(xs)-1,int(q*len(xs))); return xs[k]

def part_C_v2(p=0.35, sigma=0.20, W_grid=(1,2,4), B=8, admit_rate=3):
    # train predictor (sigma=0.20 ~ AUC 0.7 band from B_v2)
    tr_f=[]; tr_l=[]
    for s in H.TRAIN_SEEDS:
        rng=random.Random(7777+s); turns=H.gen_episode(s,p,"mixed")
        f,l,m=featurize_v2(rng,turns,sigma); tr_f+=f; tr_l+=l
    w,mu,sd=H.fit_weights(tr_f,tr_l); tr_s=H.score(tr_f,w,mu,sd)
    thr=sorted(tr_s)[int(0.80*len(tr_s))]
    test=[]
    for s in H.TEST_SEEDS:
        rng=random.Random(9999+s); turns=H.gen_episode(s,p,"mixed")
        f,l,m=featurize_v2(rng,turns,sigma); sc=H.score(f,w,mu,sd)
        test.append((turns,[si>thr for si in sc]))
    # baseline: no deprioritization
    bc=[]; bf=[]; bab=0
    for turns,flagged in test:
        c,f2,ab=sim(turns,[False]*len(turns),0,B,admit_rate); bc+=c; bab+=ab
    bp50=pct(bc,0.50); bp99=pct(bc,0.99)
    rows=[{"W":"baseline","B":B,"admit_rate":admit_rate,"completed_p50":round(bp50,1),
           "completed_p99":round(bp99,1),"fp_turn_p99":"nan","completed_p99_delta_pct":0.0,
           "n_completed":len(bc)}]
    for W in W_grid:
        c=[]; f2=[]
        for turns,flagged in test:
            cc,ff,ab=sim(turns,flagged,W,B,admit_rate); c+=cc; f2+=ff
        p99=pct(c,0.99); p50=pct(c,0.50)
        rows.append({"W":W,"B":B,"admit_rate":admit_rate,"completed_p50":round(p50,1),
            "completed_p99":round(p99,1),"fp_turn_p99":round(pct(f2,0.99),1) if f2 else "nan",
            "completed_p99_delta_pct":round(100*(p99-bp99)/bp99,2) if bp99 else 0.0,
            "n_completed":len(c)})
    with open(os.path.join(OUT,"C_reclaim_latency.csv"),"w",newline="") as fh:
        wr=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
    return rows

if __name__=="__main__":
    import time; t0=time.time()
    B=part_B_v2(); print("B_v2 done",round(time.time()-t0,1),"s")
    C=part_C_v2(); print("C_v2 done",round(time.time()-t0,1),"s")
    for r in C: print(r)
