#!/usr/bin/env python3
import sys, json, time, statistics as st, importlib
sys.path.insert(0,'/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0068')
import harness; importlib.reload(harness); import harness as H

t0=time.time()
SEEDS=[1,2,3,4,5]
NORMS=['raw','NFC','NFKC','NFKC+casefold']
ARMS=['normalizable','typo']
NUM_PERMS=64
N_PAIRS=150
BASE_LEN=60
B,R=16,8   # production LSH, knee≈0.71
FRACS=[0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.8,1.0]

def ci95(xs):
    xs=[x for x in xs if x==x]
    if len(xs)<2: return (st.mean(xs) if xs else float('nan'),0.0)
    m=st.mean(xs); se=st.pstdev(xs)/(len(xs)**0.5); return m,1.96*se

agg=[]
for frac in FRACS:
    for arm in ARMS:
        for nm in NORMS:
            f=max(frac,0.02) if frac==0.0 else frac  # frac>0 so at least 1 change
            runs=[H.run_pair_eval(arm,nm,None,NUM_PERMS,B,R,N_PAIRS,BASE_LEN,s,frac=f) for s in SEEDS]
            fn_m,fn_ci=ci95([x['fn_rate'] for x in runs])
            fl_m,fl_ci=ci95([x['flag_rate'] for x in runs])
            jac_m,_=ci95([x['mean_jaccard'] for x in runs])
            jmin,_=ci95([x['min_jaccard'] for x in runs])
            ngt=sum(x['n_gt_dup'] for x in runs)
            agg.append({'frac':frac,'arm':arm,'norm':nm,'fn_mean':fn_m,'fn_ci':fn_ci,
                'flag_mean':fl_m,'flag_ci':fl_ci,'jac_mean':jac_m,'jac_min':jmin,'n_gt':ngt})
    print(f"frac={frac} done t={time.time()-t0:.0f}s",flush=True)

with open('results/frac_sweep.json','w') as f: json.dump({'agg':agg,'B':B,'R':R,'knee':(1.0/B)**(1.0/R)},f,indent=1)

print(f"\n=== FRACTION SWEEP  LSH b={B} r={R} knee≈{(1.0/B)**(1.0/R):.2f}  (perms={NUM_PERMS},pairs={N_PAIRS},seeds={len(SEEDS)}) ===")
print("FN_rate = missed model-identical dups / model-identical dups (NORMALIZABLE arm only; typo not model-identical)")
print("flag_rate = deduper emitted the pair (both arms)\n")
for arm in ARMS:
    print(f"\n##### ARM = {arm} #####")
    hdr=f"{'frac':<6}"+''.join(f"{nm[:6]:>9}" for nm in NORMS)
    print("FN_rate     "+hdr)
    for frac in FRACS:
        row=f"{frac:<6}"
        for nm in NORMS:
            a=[x for x in agg if x['frac']==frac and x['arm']==arm and x['norm']==nm][0]
            row+= (f"{a['fn_mean']:>9.3f}" if a['fn_mean']==a['fn_mean'] else f"{'n/a':>9}")
        print("           "+row)
    print("mean_Jacc  ")
    for frac in FRACS:
        row=f"{frac:<6}"
        for nm in NORMS:
            a=[x for x in agg if x['frac']==frac and x['arm']==arm and x['norm']==nm][0]
            row+=f"{a['jac_mean']:>9.3f}"
        print("           "+row)
print(f"\nelapsed {time.time()-t0:.0f}s")
