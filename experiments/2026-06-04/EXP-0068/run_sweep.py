#!/usr/bin/env python3
import sys, json, time, statistics as st
sys.path.insert(0,'/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0068')
import harness as H

t0=time.time()
SEEDS=[1,2,3,4,5]
NORMS=['raw','NFC','NFKC','NFKC+casefold']
ARMS=['normalizable','typo']
NUM_PERMS=128
N_PAIRS=400
BASE_LEN=80
M=6
# Production LSH: b*r=128. knee≈(1/b)^(1/r). Use b=16,r=8 -> knee≈0.69; also b=32,r=4 ->0.42; b=8,r=16->0.84
LSH_CONFIGS=[(16,8),(32,4),(8,16)]

results=[]
def ci95(xs):
    xs=[x for x in xs if x==x]
    if len(xs)<2: return (st.mean(xs) if xs else float('nan'), 0.0)
    m=st.mean(xs); sd=st.pstdev(xs); se=sd/(len(xs)**0.5)
    return m, 1.96*se

# MAIN sweep: arm x norm x LSH config x seeds, M fixed
agg=[]
for (b,r) in LSH_CONFIGS:
    for arm in ARMS:
        for nm in NORMS:
            runs=[H.run_pair_eval(arm,nm,M,NUM_PERMS,b,r,N_PAIRS,BASE_LEN,s) for s in SEEDS]
            results.extend(runs)
            fn_m,fn_ci=ci95([x['fn_rate'] for x in runs])
            fl_m,fl_ci=ci95([x['flag_rate'] for x in runs])
            jac_m,_=ci95([x['mean_jaccard'] for x in runs])
            ngt=sum(x['n_gt_dup'] for x in runs)
            agg.append({'b':b,'r':r,'arm':arm,'norm':nm,'fn_mean':fn_m,'fn_ci':fn_ci,
                        'flag_mean':fl_m,'flag_ci':fl_ci,'jac_mean':jac_m,'n_gt':ngt})

with open('results/main_sweep.json','w') as f: json.dump({'agg':agg,'raw':results},f,indent=1)

print(f"=== MAIN SWEEP (M={M}, perms={NUM_PERMS}, pairs/seed={N_PAIRS}, seeds={len(SEEDS)}) ===")
for (b,r) in LSH_CONFIGS:
    knee=(1.0/b)**(1.0/r)
    print(f"\n--- LSH b={b} r={r} (knee≈{knee:.2f}) ---")
    print(f"{'arm':<13}{'norm':<15}{'FN_rate':<18}{'flag_rate':<18}{'mean_J':<8}{'n_gt'}")
    for a in agg:
        if a['b']==b and a['r']==r:
            fn = f"{a['fn_mean']:.3f}±{a['fn_ci']:.3f}" if a['fn_mean']==a['fn_mean'] else "n/a(typo)"
            fl = f"{a['flag_mean']:.3f}±{a['flag_ci']:.3f}"
            print(f"{a['arm']:<13}{a['norm']:<15}{fn:<18}{fl:<18}{a['jac_mean']:.3f}   {a['n_gt']}")
print(f"\nelapsed {time.time()-t0:.1f}s")
