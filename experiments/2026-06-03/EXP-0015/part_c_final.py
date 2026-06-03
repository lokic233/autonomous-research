"""Part C final: reclaim vs latency at MATCHED FAIRNESS, in the PREDICTABLE regime (sharpness=16,
observable AUC ~0.71) so the predictor is actually useful. Honest accounting of two reclaim levers:
 LEVER-1 (scheduling): deprioritize flagged turns under CONTENTION -> completed turns get slots sooner.
 LEVER-2 (early-term-on-confirm): once a flagged turn ACTUALLY abandons (reaches abandon_step), we stop
   scheduling it. Baseline ALSO stops an abandoned turn at abandon_step (it self-terminates). So token
   reclaim from pure deferral = 0; the honest reclaim is SLOT reclaim under contention: fewer batch
   cycles spent on doomed turns BEFORE they self-terminate, because they advance slower (1/(1+W)).
MATCHED FAIRNESS: cap W so completed-turn p99 stays within +5%. Report the full W frontier so the
fairness/reclaim tradeoff is explicit. CPU/stdlib/serial. 8 seeds via TEST split."""
import sys,os,random,statistics,csv
sys.path.insert(0,".")
import harness as H, sharpen as S
OUT=H.OUT
SHARP=16; SIGMA=0.10; P=0.30

def sim(turns,flagged,W,B,admit_rate):
    n=len(turns); need=[t["decoded"] for t in turns]; ab=[t["abandoned"] for t in turns]
    prog=[0]*n; at=[None]*n; active=[]; nxt=0; tick=0
    comp=[]; fp=[]; abslot=0
    MAX=sum(need)+n*(W+3)+300
    while True:
        adm=0
        while len(active)<B and nxt<n and adm<admit_rate:
            at[nxt]=tick; active.append(nxt); nxt+=1; adm+=1
        if not active and nxt>=n: break
        still=[]
        for i in active:
            dep=flagged[i]; adv=(not dep) or (W==0) or (tick%(1+W)==0)
            if adv:
                prog[i]+=1
                if ab[i]: abslot+=1
            if prog[i]>=need[i]:
                lat=tick-at[i]+1
                if not ab[i]:
                    comp.append(lat)
                    if flagged[i]: fp.append(lat)
            else: still.append(i)
        active=still; tick+=1
        if tick>MAX: break
    return comp,fp,abslot

def pct(xs,q):
    if not xs: return float('nan')
    xs=sorted(xs); return xs[min(len(xs)-1,int(q*len(xs)))]

def run(W_grid=(1,2,4,8), B=8, admit_rate=3):
    trf=[];trl=[]
    for s in H.TRAIN_SEEDS:
        rng=random.Random(7777+s); F,L,M=S.P.feats_labels(rng,S.gen_ep(s,P,"mixed",SHARP),SIGMA); trf+=F;trl+=L
    w,mu,sd=H.fit_weights(trf,trl); trs=H.score(trf,w,mu,sd); thr=sorted(trs)[int(0.80*len(trs))]
    test=[]
    for s in H.TEST_SEEDS:
        rng=random.Random(9999+s); F,L,M=S.P.feats_labels(rng,S.gen_ep(s,P,"mixed",SHARP),SIGMA); sc=H.score(F,w,mu,sd)
        test.append((S.gen_ep(s,P,"mixed",SHARP),[si>thr for si in sc]))
    # baseline: no deprioritization
    bc=[];bab=0
    for turns,flg in test:
        c,f,ab=sim(turns,[False]*len(turns),0,B,admit_rate); bc+=c; bab+=ab
    bp50=pct(bc,0.50); bp99=pct(bc,0.99)
    rows=[{"W":"baseline","B":B,"admit_rate":admit_rate,"obs_auc_regime":0.708,
           "completed_p50":round(bp50,1),"completed_p99":round(bp99,1),"fp_turn_p99":"nan",
           "abandoned_slot_occupancy":bab,"reclaimed_slots":0,"reclaim_pct":0.0,
           "completed_p99_delta_pct":0.0,"within_5pct_fairness":True,"n_completed":len(bc)}]
    for W in W_grid:
        c=[];f=[];ab=0
        for turns,flg in test:
            cc,ff,a=sim(turns,flg,W,B,admit_rate); c+=cc; f+=ff; ab+=a
        p99=pct(c,0.99); p50=pct(c,0.50); rec=bab-ab
        delta=100*(p99-bp99)/bp99 if bp99 else 0.0
        rows.append({"W":W,"B":B,"admit_rate":admit_rate,"obs_auc_regime":0.708,
            "completed_p50":round(p50,1),"completed_p99":round(p99,1),
            "fp_turn_p99":round(pct(f,0.99),1) if f else "nan",
            "abandoned_slot_occupancy":ab,"reclaimed_slots":rec,
            "reclaim_pct":round(100*rec/bab,2) if bab else 0.0,
            "completed_p99_delta_pct":round(delta,2),
            "within_5pct_fairness":bool(delta<=5.0),"n_completed":len(c)})
    with open(os.path.join(OUT,"C_reclaim_latency.csv"),"w",newline="") as fh:
        wr=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
    return rows
for r in run(): print(r)
