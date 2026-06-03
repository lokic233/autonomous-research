#!/usr/bin/env python3
"""
EXP-0011 / CLAIM-0009 — L0 analytic model (VECTORIZED/ANALYTIC, stdlib-only, SERIAL).
Structure-aware per-class early-exit threshold vs BEST-TUNED global threshold.
CPU-only, no real model. Honest pipeline. Metric: FLOPs saved at MATCHED token-error-rate.

KEY CONTROL (EXP-0006 lesson): GLOBAL tau is SWEPT to per-workload optimum (best-tuned).
Jensen guarantees per-class >= global trivially -> we report the MAGNITUDE of the gap.

Performance: instead of looping over N tokens, we model each class's behavior as a
per-class (FLOP, err) function of tau, evaluated over a Monte-Carlo noise sample of the
confidence curve. We precompute, for each class and each tau, the expected exit-layer FLOP
fraction and expected error by averaging over a fixed noise sample (NS draws). Then global
and per-class optimization just combine these per-class curves with class mix f. This is
mathematically identical to the token-loop model (LLN) but ~ (#tau) instead of (#tau x N).
"""
import math, csv, random, os

L_TOTAL = 32
BASE_ERR = 0.5
D_BOILER = 0.25
TAU_GRID = [i/200.0 for i in range(1, 200)]   # global sweep: 199 pts
TAU_GRID_2D = [i/100.0 for i in range(1, 100)] # per-class sweep: 99 pts each
NS = 2000           # noise samples per class (LLN for expectation)
SEEDS = list(range(5))
NOISE_SD = 0.03

def sigmoid(x):
    if x < -60: return 0.0
    if x > 60: return 1.0
    return 1.0/(1.0+math.exp(-x))

def conf(L, d, slope):
    return sigmoid(slope*(L/float(L_TOTAL) - d))

def class_curve(d, slope, seed):
    """For a class with saturation depth d, return per-tau arrays:
       flop[tau], err[tau] = expected FLOP-fraction and expected error over noise.
    Computed by sampling NS noise draws and, for each, finding exit layer per tau.
    Returns dict tau-> (flop,err) but we align to TAU_GRID and TAU_GRID_2D separately."""
    rng = random.Random(seed*104729 + int(d*1000) + int(slope*10))
    # precompute confidence at each layer (no noise), then add per-sample noise
    base_c = [conf(L, d, slope) for L in range(1, L_TOTAL+1)]  # idx 0 -> layer1
    err_layer = [max(0.0, BASE_ERR*(1.0-c)) for c in base_c]
    flop_layer = [(L+1)/float(L_TOTAL) for L in range(L_TOTAL)]  # layer L+1
    noises = [rng.gauss(0, NOISE_SD) for _ in range(NS)]
    def curve(taus):
        flop_out=[]; err_out=[]
        for tau in taus:
            tf=0.0; te=0.0
            for nz in noises:
                # shallowest layer where base_c[i]+nz >= tau
                Lidx=L_TOTAL-1
                for i in range(L_TOTAL):
                    if base_c[i]+nz >= tau:
                        Lidx=i; break
                tf+=flop_layer[Lidx]; te+=err_layer[Lidx]
            flop_out.append(tf/NS); err_out.append(te/NS)
        return flop_out, err_out
    return curve

def best_global(fb_curve, fv_curve, f, budget, taus):
    """Single tau for all tokens. Mix: f boiler + (1-f) value. Min FLOP s.t. err<=budget."""
    bf, be = fb_curve; vf, ve = fv_curve
    best=None
    for i,tau in enumerate(taus):
        flop = f*bf[i] + (1-f)*vf[i]
        err  = f*be[i] + (1-f)*ve[i]
        if err<=budget and (best is None or flop<best[0]):
            best=(flop,err,tau)
    if best is None:
        # full compute fallback
        best=(1.0, f*be[-1]+(1-f)*ve[-1] if False else 0.0, None)
        # recompute err at max tau (~full): last grid point is highest tau
        best=(f*bf[-1]+(1-f)*vf[-1], f*be[-1]+(1-f)*ve[-1], taus[-1])
    return best

def best_perclass(fb_curve, fv_curve, f, budget, taus):
    """Independent tau per class. Min total FLOP s.t. total err<=budget.
    NOTE: this couples classes through the shared error budget, so it is NOT
    a trivial per-class independent optimization — both taus traded jointly."""
    bf, be = fb_curve; vf, ve = fv_curve
    n=len(taus)
    best=None
    for ib in range(n):
        fb_=f*bf[ib]; eb_=f*be[ib]
        for iv in range(n):
            flop = fb_ + (1-f)*vf[iv]
            err  = eb_ + (1-f)*ve[iv]
            if err<=budget and (best is None or flop<best[0]):
                best=(flop,err,taus[ib],taus[iv])
    if best is None:
        best=(f*bf[-1]+(1-f)*vf[-1], f*be[-1]+(1-f)*ve[-1], taus[-1], taus[-1])
    return best

def main():
    out_dir=os.path.dirname(os.path.abspath(__file__))
    F_GRID=[0.1,0.2,0.3,0.4,0.5]
    DGAP_GRID=[0.2,0.35,0.5]
    E_GRID=[0.01,0.02,0.05]
    SLOPE_GRID=[6.0,10.0]
    rows=[]
    # cache class curves per (d,slope,seed) for both tau grids
    cache={}
    def get_curves(d,slope,seed):
        k=(d,slope,seed)
        if k not in cache:
            c=class_curve(d,slope,seed)
            cache[k]=(c(TAU_GRID), c(TAU_GRID_2D))
        return cache[k]
    for slope in SLOPE_GRID:
        for gap in DGAP_GRID:
            d_value=round(D_BOILER+gap,3)
            for f in F_GRID:
                for E in E_GRID:
                    gflops=[];sflops=[];gerrs=[];serrs=[]
                    for seed in SEEDS:
                        b1,b2=get_curves(D_BOILER,slope,seed)
                        v1,v2=get_curves(d_value,slope,seed)
                        gf,ge,_=best_global(b1,v1,f,E,TAU_GRID)
                        sf,se,_,_=best_perclass(b2,v2,f,E,TAU_GRID_2D)
                        gflops.append(gf);sflops.append(sf);gerrs.append(ge);serrs.append(se)
                    def m(x):return sum(x)/len(x)
                    def sd(x):
                        mu=m(x);return (sum((v-mu)**2 for v in x)/len(x))**0.5
                    gf_m=m(gflops);sf_m=m(sflops)
                    rows.append(dict(slope=slope,f=f,depth_gap=gap,d_value=d_value,E=E,
                        global_flop=round(gf_m,4),global_flop_sd=round(sd(gflops),4),
                        struct_flop=round(sf_m,4),struct_flop_sd=round(sd(sflops),4),
                        global_err=round(m(gerrs),4),struct_err=round(m(serrs),4),
                        delta_flop=round(gf_m-sf_m,4),delta_pp=round((gf_m-sf_m)*100,2),
                        global_savings_pp=round((1-gf_m)*100,2),
                        struct_savings_pp=round((1-sf_m)*100,2)))
    keys=list(rows[0].keys())
    with open(os.path.join(out_dir,"results","sweep.csv"),"w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=keys);w.writeheader()
        for r in rows:w.writerow(r)
    # agentic vs reasoning: reasoning = f=0 (all deep), best-tuned-global savings
    comp=[]
    for slope in SLOPE_GRID:
        for gap in DGAP_GRID:
            d_value=round(D_BOILER+gap,3)
            for E in E_GRID:
                rfl=[]
                for seed in SEEDS:
                    v1,_=get_curves(d_value,slope,seed)
                    b1,_=get_curves(D_BOILER,slope,seed)
                    rf,_,_=best_global(b1,v1,0.0,E,TAU_GRID); rfl.append(rf)
                reason=sum(rfl)/len(rfl)
                for f in F_GRID:
                    afl=[];sfl=[]
                    for seed in SEEDS:
                        b1,b2=get_curves(D_BOILER,slope,seed)
                        v1,v2=get_curves(d_value,slope,seed)
                        af,_,_=best_global(b1,v1,f,E,TAU_GRID);afl.append(af)
                        sf,_,_,_=best_perclass(b2,v2,f,E,TAU_GRID_2D);sfl.append(sf)
                    a=sum(afl)/len(afl);s=sum(sfl)/len(sfl)
                    comp.append(dict(slope=slope,E=E,depth_gap=gap,f=f,
                        reason_global_flop=round(reason,4),agentic_global_flop=round(a,4),
                        agentic_struct_flop=round(s,4),
                        agentic_global_savings_pp=round((1-a)*100,2),
                        reason_global_savings_pp=round((1-reason)*100,2),
                        agentic_minus_reason_savings_pp=round((reason-a)*100,2),
                        struct_extra_savings_pp=round((a-s)*100,2)))
    ck=list(comp[0].keys())
    with open(os.path.join(out_dir,"results","agentic_vs_reasoning.csv"),"w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=ck);w.writeheader()
        for r in comp:w.writerow(r)
    print("DONE rows=",len(rows),"comp=",len(comp))

if __name__=="__main__":
    main()
