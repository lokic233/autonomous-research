import sys,os,random,statistics,csv,math
sys.path.insert(0,".")
import harness as H, predictability_sweep as P
OUT=H.OUT

def gen_turn(rng,p_abandon,timing,sharp):
    d=rng.random();f=rng.random();bv=rng.random()
    L=max(8,int(math.exp(rng.gauss(math.log(120),0.6))))
    hz=0.45*d+0.35*f+0.20*(1-bv)            # mean ~0.5
    # logistic with tunable steepness 'sharp'; center so marginal rate ~ p_abandon
    z=sharp*(hz-0.5)
    pa=p_abandon* (2.0/(1+math.exp(-z)))    # ranges 0..2*p_abandon as hz sweeps
    pa=min(0.98,max(0.0,pa)); ab=rng.random()<pa
    astep=None
    if ab:
        if timing=="early":frac=rng.betavariate(1.5,5)
        elif timing=="mid":frac=rng.betavariate(3,3)
        elif timing=="late":frac=rng.betavariate(5,1.5)
        else:frac=rng.random()
        astep=max(1,int(frac*L))
    return {"L_plan":L,"abandoned":ab,"abandon_step":astep,"decoded":L if not ab else astep,
            "latent_difficulty":d,"latent_tool_fragility":f,"latent_branch_value":bv,
            "retry_count":(1 if (f>0.6 and rng.random()<0.5) else 0)}

def gen_ep(seed,p,timing,sharp):
    rng=random.Random(seed*1000003+(hash((p,timing,round(sharp,3)))%100000))
    return [gen_turn(rng,p,timing,sharp) for _ in range(H.N_TURNS_PER_EPISODE)]

def run():
    rows=[]; sigma=0.10; p=0.30
    for sharp in [0,3,6,10,16]:
        osc=[];olb=[]
        for s in H.SEEDS:
            for t in gen_ep(s,p,"mixed",sharp):
                hz=0.45*t["latent_difficulty"]+0.35*t["latent_tool_fragility"]+0.20*(1-t["latent_branch_value"])
                osc.append(hz);olb.append(1 if t["abandoned"] else 0)
        oracle=H.auc(osc,olb)
        trf=[];trl=[]
        for s in H.TRAIN_SEEDS:
            rng=random.Random(7777+s);F,L,M=P.feats_labels(rng,gen_ep(s,p,"mixed",sharp),sigma);trf+=F;trl+=L
        w,mu,sd=H.fit_weights(trf,trl);trs=H.score(trf,w,mu,sd);thr=sorted(trs)[int(0.80*len(trs))]
        tes=[];tel=[];leads=[]
        for s in H.TEST_SEEDS:
            rng=random.Random(8888+s);F,L,M=P.feats_labels(rng,gen_ep(s,p,"mixed",sharp),sigma);sc=H.score(F,w,mu,sd)
            tes+=sc;tel+=L
            for si,mi in zip(sc,M):
                if mi["ab"] and si>thr: leads.append(mi["as"]-mi["ot"])
        a=H.auc(tes,tel)
        flg=[(sc,l) for sc,l in zip(tes,tel) if sc>thr]
        prec=sum(l for _,l in flg)/len(flg) if flg else float('nan')
        rec=sum(l for _,l in flg)/sum(tel) if sum(tel) else float('nan')
        rows.append({"hazard_sharpness":sharp,"p_abandon":p,"obs_noise":sigma,
            "oracle_auc":round(oracle,4),"observable_auc":round(a,4),
            "flag_precision":round(prec,4),"flag_recall":round(rec,4),
            "median_lead_tokens":round(statistics.median(leads),1) if leads else "nan",
            "frac_positive_lead":round(sum(1 for x in leads if x>0)/len(leads),3) if leads else "nan"})
    with open(os.path.join(OUT,"B2_predictability_frontier.csv"),"w",newline="") as fh:
        wr=csv.DictWriter(fh,fieldnames=list(rows[0].keys()));wr.writeheader();wr.writerows(rows)
    return rows
for r in run(): print(r)
