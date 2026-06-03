import time, json, os, sys, math
exec(open('/Users/dengcchi/autonomous-research-v3/experiments/2026-06-03/EXP-0057/harness.py').read())

OUT = '/Users/dengcchi/autonomous-research-v3/experiments/2026-06-03/EXP-0057/results/'
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
b = B_BATCH   # 32

def infl_ci(vals):
    m = sum(vals)/len(vals)
    if len(vals)>1:
        sd = math.sqrt(sum((x-m)**2 for x in vals)/(len(vals)-1)); ci = 1.96*sd/math.sqrt(len(vals))
    else: sd=0.0; ci=0.0
    return m, ci, sd

# ---- core cell: interleaved stream (C), buffer shuffle, full-shuffle + per-shard baselines ----
def cell_interleave(B, L, C, seed, sig=SIGMA_SIG, noise=SIGMA_NOISE):
    N = choose_N(L)
    grads, labels = gen_stream_interleave(seed, L, N, C, sig, noise)
    n = len(grads)
    rng_buf = random.Random(seed*7919 + B*31 + L*131 + C*97 + 1)
    bo = buffer_shuffle_order(n, B, rng_buf)
    V_buf, nb = batch_mean_var(grads, bo, b)
    rho_buf = rho_same_source(labels, bo, b)
    rng_full = random.Random(seed*104729 + 3)
    fo = list(range(n)); rng_full.shuffle(fo)
    V_full, _ = batch_mean_var(grads, fo, b)
    # per-shard baseline (within contiguous same-label run)
    rng_ps = random.Random(seed*1299709 + 5)
    pso = per_shard_shuffle_order(labels, rng_ps)
    V_ps, _ = batch_mean_var(grads, pso, b)
    infl_full = V_buf/V_full if V_full>0 else float('nan')
    infl_ps   = V_buf/V_ps   if V_ps>0   else float('nan')
    return dict(B=B,L=L,C=C,seed=seed,N=n,nbatches=nb,V_buf=V_buf,V_full=V_full,V_ps=V_ps,
                inflation=infl_full, inflation_vs_pershard=infl_ps, rho_buf=rho_buf)

raw=[]; agg_rows=[]
# ============ BLOCKER 1: interleaving sweep ============
print("=== BLOCKER 1: INTERLEAVING (cycle_length C) ===", flush=True)
pts = [(10*b,640),(10*b,6400),(2*b,640),(50*b,6400)]   # (B,L): realistic, large-L, +2 axis
Cgrid=[1,2,4,8,16]
interleave_grid={}
for (B,L) in pts:
    for C in Cgrid:
        cells=[cell_interleave(B,L,C,s) for s in SEEDS]
        raw+=cells
        m,ci,sd=infl_ci([c['inflation'] for c in cells])
        mp,cip,_=infl_ci([c['inflation_vs_pershard'] for c in cells])
        rb=sum(c['rho_buf'] for c in cells)/len(cells)
        interleave_grid[(B,L,C)]=dict(B=B,L=L,C=C,L_eff=L/C,inflation=m,ci=ci,
                                      inflation_vs_pershard=mp,ci_ps=cip,rho_buf=rb,nbatches=cells[0]['nbatches'])
        print(f"  B={B:5d} L={L:5d} C={C:2d} L_eff={L/C:7.1f}  infl_vsFull={m:7.3f}+/-{ci:.3f}  infl_vsPerShard={mp:6.3f}  rho={rb:.4f}  t={time.time()-T0:.1f}s",flush=True)

# ============ L_eff = L/C hypothesis: build L0-style single-stream reference inflation(B, L') ============
print("=== L_eff REFERENCE: sequential inflation(B, L') for L'=L/C values ===", flush=True)
def cell_seq(B, Lp, seed):
    Lp=max(1,int(round(Lp)))
    N=choose_N(Lp)
    grads,labels=gen_stream_param(seed,Lp,N)
    n=len(grads)
    rng_buf=random.Random(seed*7919+B*31+Lp*131+1)
    bo=buffer_shuffle_order(n,B,rng_buf)
    V_buf,nb=batch_mean_var(grads,bo,b)
    rng_full=random.Random(seed*104729+3); fo=list(range(n)); rng_full.shuffle(fo)
    V_full,_=batch_mean_var(grads,fo,b)
    return (V_buf/V_full) if V_full>0 else float('nan')
leff_check=[]
for (B,L) in pts:
    for C in Cgrid:
        Lp=L/C
        ref_vals=[cell_seq(B,Lp,s) for s in SEEDS]
        ref_m,_,_=infl_ci(ref_vals)
        obs=interleave_grid[(B,L,C)]['inflation']
        rel=abs(obs-ref_m)/ref_m if ref_m>0 else float('nan')
        leff_check.append(dict(B=B,L=L,C=C,L_eff=Lp,obs_interleave=obs,ref_seq_Leff=ref_m,rel_err=rel))
        print(f"  B={B:5d} L={L:5d} C={C:2d} L_eff={Lp:7.1f}  obs(interleave)={obs:7.3f}  ref seq(L_eff)={ref_m:7.3f}  rel_err={rel*100:5.1f}%  t={time.time()-T0:.1f}s",flush=True)

# ============ BLOCKER 2: rho_within sweep at realistic point ============
print("=== BLOCKER 2: RHO_WITHIN sweep at realistic (B=320,L=640,C=1) ===", flush=True)
rho_rows=[]
B_r, L_r = 10*b, 640
for r in [0.2,0.5,0.8]:
    noise = SIGMA_SIG*math.sqrt((1-r)/r)
    cells=[]; achieved=[]
    for s in SEEDS:
        N=choose_N(L_r)
        grads,labels=gen_stream_param(s,L_r,N,SIGMA_SIG,noise)
        n=len(grads)
        rng_buf=random.Random(s*7919+B_r*31+L_r*131+1)
        bo=buffer_shuffle_order(n,B_r,rng_buf)
        V_buf,nb=batch_mean_var(grads,bo,b)
        rng_full=random.Random(s*104729+3); fo=list(range(n)); rng_full.shuffle(fo)
        V_full,_=batch_mean_var(grads,fo,b)
        rng_ps=random.Random(s*1299709+5); pso=per_shard_shuffle_order(labels,rng_ps)
        V_ps,_=batch_mean_var(grads,pso,b)
        cells.append((V_buf/V_full, V_buf/V_ps))
        if s==SEEDS[0]:
            achieved.append(measure_within_corr(grads,labels))
    m,ci,_=infl_ci([c[0] for c in cells]); mp,_,_=infl_ci([c[1] for c in cells])
    rho_rows.append(dict(rho_target=r,rho_achieved=achieved[0],sigma_noise=noise,
                         inflation=m,ci=ci,inflation_vs_pershard=mp))
    print(f"  rho_target={r:.2f} achieved={achieved[0]:.3f} noise={noise:.3f}  infl_vsFull={m:7.3f}+/-{ci:.3f}  infl_vsPerShard={mp:6.3f}  t={time.time()-T0:.1f}s",flush=True)

elapsed=time.time()-T0
print(f"=== DONE {elapsed:.1f}s ===",flush=True)
out=dict(config=dict(D=D,b=b,seeds=SEEDS,sig=SIGMA_SIG,Cgrid=Cgrid,pts=pts,
                     realistic_point=dict(B=B_r,L=L_r)),
         interleave=[dict(**v) for v in interleave_grid.values()],
         leff_check=leff_check, rho_within=rho_rows, raw=raw, elapsed_s=elapsed)
json.dump(out,open(OUT+'results.json','w'),indent=2)
with open(OUT+'interleave.csv','w') as f:
    f.write("B,L,C,L_eff,inflation_vsFull,ci,inflation_vsPerShard,rho_buf,nbatches\n")
    for v in sorted(interleave_grid.values(),key=lambda x:(x['B'],x['L'],x['C'])):
        f.write(f"{v['B']},{v['L']},{v['C']},{v['L_eff']:.1f},{v['inflation']:.4f},{v['ci']:.4f},{v['inflation_vs_pershard']:.4f},{v['rho_buf']:.4f},{v['nbatches']}\n")
with open(OUT+'leff_check.csv','w') as f:
    f.write("B,L,C,L_eff,obs_interleave,ref_seq_Leff,rel_err\n")
    for r in leff_check:
        f.write(f"{r['B']},{r['L']},{r['C']},{r['L_eff']:.1f},{r['obs_interleave']:.4f},{r['ref_seq_Leff']:.4f},{r['rel_err']:.4f}\n")
with open(OUT+'rho_within.csv','w') as f:
    f.write("rho_target,rho_achieved,sigma_noise,inflation_vsFull,ci,inflation_vsPerShard\n")
    for r in rho_rows:
        f.write(f"{r['rho_target']},{r['rho_achieved']:.4f},{r['sigma_noise']:.4f},{r['inflation']:.4f},{r['ci']:.4f},{r['inflation_vs_pershard']:.4f}\n")
print("wrote results.json + interleave.csv + leff_check.csv + rho_within.csv",flush=True)
