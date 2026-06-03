#!/usr/bin/env python3
"""Part C v2 — honest reclaim model with online-confirmed-abandonment.
Imports trace+predictor machinery from harness.py.
Mechanism: the predictor FLAGS a turn early (lead time). Flagging does NOT kill (no ground truth);
it DEPRIORITIZES (bounded-W slowdown). The REAL reclaim arises because an abandoned turn naturally
*ends* at abandon_step (in its own wall-clock); when it ends, its remaining planned tokens are never
decoded. Deprioritization helps completed turns get scheduled sooner relative to abandoned ones, AND
the early flag lets us STOP decoding a flagged-abandoned turn as soon as its abandonment is observed
(at abandon_step) instead of continuing — but baseline ALSO stops at abandon_step (a turn that abandons
stops emitting). So the genuine reclaim lever is: deprioritized abandoned turns consume FEWER decode
SLOTS before they self-terminate -> those freed slots serve completed turns -> completed-turn latency
can IMPROVE or stay flat while abandoned turns' slot-occupancy drops.

We measure: completed-turn p50/p99 (treatment vs baseline), FP-turn p99, and RECLAIMED DECODE SLOTS =
(baseline abandoned-turn slot-occupancy) - (treatment abandoned-turn slot-occupancy). Reclaim>0 means
the batch spent fewer decode cycles on doomed turns under treatment.
"""
import sys, os, random, statistics, csv
sys.path.insert(0,"/Users/dengcchi/autonomous-research-v3/experiments/2026-06-03/EXP-0015")
import harness as H

OUT=H.OUT

def sim(turns, flagged, W):
    """Round-robin token-time sim. Each active turn emits 1 token/tick unless deprioritized
    (then 1 token every (1+W) ticks). A turn 'self-terminates' after it has emitted `need` tokens
    where need = decoded (abandon_step if abandoned, else L_plan). Returns metrics."""
    n=len(turns); B=16
    need=[t["decoded"] for t in turns]
    is_ab=[t["abandoned"] for t in turns]
    progressed=[0]*n; admit_t=[None]*n; finished=[False]*n
    active=[]; next_admit=0; tick=0
    comp_lat=[]; fp_lat=[]; ab_slot=0  # decode slots spent on abandoned turns
    MAX=sum(need)+n*(W+2)+50
    while True:
        while len(active)<B and next_admit<n:
            admit_t[next_admit]=tick; active.append(next_admit); next_admit+=1
        if not active and next_admit>=n: break
        still=[]
        for i in active:
            dep=flagged[i]
            advance=(not dep) or (W==0) or (tick%(1+W)==0)
            if advance:
                progressed[i]+=1
                if is_ab[i]: ab_slot+=1
            if progressed[i]>=need[i]:
                lat=tick-admit_t[i]+1
                if not is_ab[i]:
                    comp_lat.append(lat)
                    if flagged[i]: fp_lat.append(lat)
                finished[i]=True
            else:
                still.append(i)
        active=still; tick+=1
        if tick>MAX: break
    return comp_lat, fp_lat, ab_slot, tick

def pct(xs,q):
    if not xs: return float('nan')
    xs=sorted(xs); k=min(len(xs)-1,int(q*len(xs))); return xs[k]

def run(p=0.35, sigma=0.70, W_grid=(0,1,2,4)):
    # train predictor
    tr_feats=[]; tr_labels=[]
    for s in H.TRAIN_SEEDS:
        rng=random.Random(7777+s); turns=H.gen_episode(s,p,"mixed")
        f,l,m=H.featurize(rng,turns,sigma); tr_feats+=f; tr_labels+=l
    w,mu,sd=H.fit_weights(tr_feats,tr_labels)
    tr_scores=H.score(tr_feats,w,mu,sd)
    thr=sorted(tr_scores)[int(0.80*len(tr_scores))]
    # baseline (W=0, no deprioritization at all -> flagged all False)
    base_comp=[]; base_fp=[]; base_abslot=0
    test_sets=[]
    for s in H.TEST_SEEDS:
        rng=random.Random(9999+s); turns=H.gen_episode(s,p,"mixed")
        f,l,m=H.featurize(rng,turns,sigma); sc=H.score(f,w,mu,sd)
        flagged=[si>thr for si in sc]
        test_sets.append((turns,flagged))
    # true baseline: NO flags
    for turns,flagged in test_sets:
        cl,fl,ab,_=sim(turns,[False]*len(turns),0)
        base_comp+=cl; base_fp+=fl; base_abslot+=ab
    base_p50=pct(base_comp,0.50); base_p99=pct(base_comp,0.99)
    rows=[]
    rows.append({"W":"baseline","completed_p50":round(base_p50,1),"completed_p99":round(base_p99,1),
                 "fp_turn_p99":"nan","abandoned_slot_occupancy":base_abslot,
                 "reclaimed_slots_vs_baseline":0,"reclaim_pct":0.0,
                 "completed_p99_delta_pct":0.0,"n_completed":len(base_comp)})
    for W in W_grid:
        comp=[]; fp=[]; abslot=0
        for turns,flagged in test_sets:
            cl,fl,ab,_=sim(turns,flagged,W); comp+=cl; fp+=fl; abslot+=ab
        p99=pct(comp,0.99); p50=pct(comp,0.50)
        reclaim=base_abslot-abslot
        rows.append({
            "W":W,"completed_p50":round(p50,1),"completed_p99":round(p99,1),
            "fp_turn_p99":round(pct(fp,0.99),1) if fp else "nan",
            "abandoned_slot_occupancy":abslot,
            "reclaimed_slots_vs_baseline":reclaim,
            "reclaim_pct":round(100*reclaim/base_abslot,2) if base_abslot else 0.0,
            "completed_p99_delta_pct":round(100*(p99-base_p99)/base_p99,2) if base_p99 else 0.0,
            "n_completed":len(comp),
        })
    with open(os.path.join(OUT,"C_reclaim_latency.csv"),"w",newline="") as fh:
        wr=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
    return rows

if __name__=="__main__":
    import time; t0=time.time()
    r=run(); 
    for x in r: print(x)
    print("C done", round(time.time()-t0,1),"s")
