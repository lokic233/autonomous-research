#!/usr/bin/env python3
"""FINAL decisive run: exact-Jaccard deduper (sharp LSH limit) + real banded MinHash-LSH.
PRIMARY: FN(normalizer, arm) at production threshold + alias control + mitigation.
S-curve isolation: FN-vs-frac vs Jaccard-crossing-knee."""
import sys, json, time, statistics as st, importlib, random
sys.path.insert(0,'/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0068')
import harness; importlib.reload(harness); import harness as H
t0=time.time()
SEEDS=[1,2,3,4,5,6,7]
NORMS=['raw','NFC','NFKC','NFKC+casefold']
FRACS=[0.05,0.1,0.2,0.3,0.4,0.5,0.6,0.8]
N=300; BASE_LEN=60
def ci95(xs):
    xs=[x for x in xs if x==x]
    if len(xs)<2: return (st.mean(xs) if xs else float('nan'),0.0)
    return st.mean(xs),1.96*st.pstdev(xs)/(len(xs)**0.5)

def eval_cell(arm,nm,frac,T,seed):
    """For NORMALIZABLE arm: FN over model-identical dups (J<T => missed).
    For TYPO arm: pairs are NOT model-identical -> measure deduper FLAG-rate (J>=T) — sensitivity to nm.
    Also collect mean Jaccard + fraction with J>=T (S-curve crossing)."""
    rng=random.Random(seed*97+hash(nm)%89+hash(arm)%53+int(frac*1000))
    dn=H.NORMALIZERS[nm]; ngt=0;miss=0; flagged=0;ntot=0; Js=[]
    for _ in range(N):
        d1=H.make_base_doc(rng,BASE_LEN); npos=H.normalizable_positions(d1)
        if not npos: continue
        rng.shuffle(npos); ch=npos[:max(1,round(frac*len(npos)))]
        d2,ap=(H.apply_normalizable_at(d1,ch) if arm=='normalizable' else H.apply_typo(d1,rng,ch))
        if ap==0: continue
        ntot+=1
        gt=(H.model_normalize(d1)==H.model_normalize(d2))
        J=H.true_jaccard(H.shingles(dn(d1)),H.shingles(dn(d2))); Js.append(J)
        flag=(J>=T)
        if flag: flagged+=1
        if gt:
            ngt+=1
            if not flag: miss+=1
    return {'fn':(miss/ngt if ngt else float('nan')),'flag':(flagged/ntot if ntot else float('nan')),
            'ngt':ngt,'meanJ':(sum(Js)/len(Js) if Js else float('nan')),
            'frac_Jge_T':(sum(1 for j in Js if j>=T)/len(Js) if Js else float('nan'))}

T=0.8  # production threshold
agg=[]
for arm in ['normalizable','typo']:
    for nm in NORMS:
        for frac in FRACS:
            runs=[eval_cell(arm,nm,frac,T,s) for s in SEEDS]
            fn_m,fn_c=ci95([r['fn'] for r in runs]); fl_m,fl_c=ci95([r['flag'] for r in runs])
            jm,_=ci95([r['meanJ'] for r in runs]); cm,_=ci95([r['frac_Jge_T'] for r in runs])
            agg.append({'arm':arm,'norm':nm,'frac':frac,'T':T,'fn':fn_m,'fn_ci':fn_c,
                        'flag':fl_m,'flag_ci':fl_c,'meanJ':jm,'frac_Jge_T':cm,
                        'ngt':sum(r['ngt'] for r in runs)})
    print(f"arm={arm} done t={time.time()-t0:.0f}s",flush=True)

# THRESHOLD sweep (normalizable arm only, frac=0.3) for primary robustness
thr_sweep=[]
for nm in NORMS:
    for Tt in [0.5,0.6,0.7,0.8,0.9]:
        runs=[eval_cell('normalizable',nm,0.3,Tt,s) for s in SEEDS]
        fn_m,fn_c=ci95([r['fn'] for r in runs])
        thr_sweep.append({'norm':nm,'T':Tt,'frac':0.3,'fn':fn_m,'fn_ci':fn_c})
print(f"threshold sweep done t={time.time()-t0:.0f}s",flush=True)

json.dump({'agg':agg,'thr_sweep':thr_sweep,'T':T,'N':N,'seeds':len(SEEDS)},
          open('results/final.json','w'),indent=1)

print(f"\n=== FINAL  exact-Jaccard deduper, production T={T}, N={N}/seed, {len(SEEDS)} seeds ===\n")
for arm in ['normalizable','typo']:
    print(f"##### ARM={arm}  ({'FN over model-identical dups' if arm=='normalizable' else 'flag-rate; NOT model-identical (difficulty control)'}) #####")
    metric='fn' if arm=='normalizable' else 'flag'
    print(f"{'frac':<6}"+''.join(f"{nm[:7]:>11}" for nm in NORMS)+"   meanJ(raw)  fracJ>=T(raw)")
    for frac in FRACS:
        row=f"{frac:<6}"
        for nm in NORMS:
            a=[x for x in agg if x['arm']==arm and x['norm']==nm and x['frac']==frac][0]
            row+=f"{a[metric]:>7.2f}±{a[metric+'_ci']:>.2f}"
        ar=[x for x in agg if x['arm']==arm and x['norm']=='raw' and x['frac']==frac][0]
        row+=f"   {ar['meanJ']:>6.3f}      {ar['frac_Jge_T']:>5.3f}"
        print(row)
    print()
print("=== THRESHOLD SWEEP (normalizable arm, frac=0.3) — primary robustness ===")
print(f"{'T':<6}"+''.join(f"{nm[:7]:>11}" for nm in NORMS))
for Tt in [0.5,0.6,0.7,0.8,0.9]:
    row=f"{Tt:<6}"
    for nm in NORMS:
        a=[x for x in thr_sweep if x['norm']==nm and x['T']==Tt][0]
        row+=f"{a['fn']:>10.2f} "
    print(row)
print(f"\nelapsed {time.time()-t0:.0f}s")
