#!/usr/bin/env python3
# EXP-0059 L0 sim: decontam length-bias. stdlib-only, SERIAL.
# Harness OWNS GT (d_i,p_i). Filter reads ONLY token overlap (modeled via per-k-gram match prob q).
import random, math, statistics, csv, os, time

ART = os.path.dirname(os.path.abspath(__file__))
M = 4000
N_SEEDS = 8
ALPHAS = [0.0, 0.3, 0.6, 0.9]
C_MAP = {"low": 0.002, "med": 0.01, "high": 0.05}   # per-k-gram match prob q
KS = [8, 13, 25]
Lmin, Lmax = 12, 400

def sigmoid(x): return 1.0/(1.0+math.exp(-x))

def gen_lengths(rng):
    Ls=[]
    for _ in range(M):
        L = round(math.exp(rng.normalvariate(3.0, 0.6)))
        L = max(Lmin, min(Lmax, L))
        Ls.append(L)
    return Ls

def standardize(xs):
    m = statistics.fmean(xs); sd = statistics.pstdev(xs) or 1.0
    return [(x-m)/sd for x in xs]

def run_cell(alpha, q, k, seed):
    rng = random.Random(seed*7919 + k*101 + int(q*100000) + int(alpha*1000))
    Ls = gen_lengths(rng)
    glog = standardize([math.log(L) for L in Ls])   # length contribution g(L)
    # difficulty + true prob (GT, harness-owned). eps independent of length.
    p=[]; d=[]
    for i in range(M):
        eps = rng.normalvariate(0,1)
        di = alpha*glog[i] + (1-alpha)*eps
        d.append(di); p.append(sigmoid(-di))
    # FILTER: remove iff ANY k-gram matches. n_kgrams = max(0, L-k+1). per-kgram match prob q.
    # FILTER NEVER sees d/p. operates only on length (token-overlap surrogate).
    survive_mask=[]
    for i in range(M):
        ng = max(0, Ls[i]-k+1)
        # P(remove) = 1-(1-q)^ng ; draw per-kgram bernoulli (any match => remove)
        removed = False
        # efficient: draw whether removed via the closed-form prob (exactly equiv to ANY of ng bernoullis)
        p_remove = 1.0 - (1.0-q)**ng
        removed = (rng.random() < p_remove)
        survive_mask.append(not removed)
    surv_idx=[i for i in range(M) if survive_mask[i]]
    n_surv=len(surv_idx)
    acc_full = statistics.fmean(p)
    acc_surv = statistics.fmean([p[i] for i in surv_idx]) if n_surv>0 else float('nan')
    delta = acc_surv - acc_full
    mean_L_full = statistics.fmean(Ls)
    mean_L_surv = statistics.fmean([Ls[i] for i in surv_idx]) if n_surv>0 else float('nan')
    removal_rate = 1 - n_surv/M
    # structural anchor: removal rate by length bin (monotone check) + union-bound check
    return dict(delta=delta, acc_full=acc_full, acc_surv=acc_surv,
                mean_L_full=mean_L_full, mean_L_surv=mean_L_surv,
                removal_rate=removal_rate, n_surv=n_surv,
                Ls=Ls, mask=survive_mask)

def ci95(xs):
    if len(xs)<2: return (xs[0],xs[0],0.0)
    m=statistics.fmean(xs); sd=statistics.stdev(xs); h=1.96*sd/math.sqrt(len(xs))
    return (m, h, sd)

def main():
    t0=time.time()
    rows=[]
    anchor_rows=[]
    for alpha in ALPHAS:
        for cname,q in C_MAP.items():
            for k in KS:
                deltas=[]; rr=[]; mlf=[]; mls=[]; accf=[]; accs=[]
                agg_len_remove={}  # length -> [removed,total] across seeds (for monotonicity)
                for s in range(N_SEEDS):
                    r=run_cell(alpha,q,k,s)
                    deltas.append(r['delta']); rr.append(r['removal_rate'])
                    mlf.append(r['mean_L_full']); mls.append(r['mean_L_surv'])
                    accf.append(r['acc_full']); accs.append(r['acc_surv'])
                    # accumulate removal-by-length for anchor (only need one alpha-c-k since filter is length-only;
                    # but do for all to be safe)
                    if alpha==0.0:  # filter is identical across alpha (length-only); record once per (c,k)
                        for i,L in enumerate(r['Ls']):
                            e=agg_len_remove.setdefault(L,[0,0])
                            e[0]+= 0 if r['mask'][i] else 1
                            e[1]+= 1
                dm,dh,dsd=ci95(deltas)
                rrm,rrh,_=ci95(rr)
                rows.append(dict(alpha=alpha,c=cname,q=q,k=k,
                    delta_mean=dm,delta_ci=dh,
                    acc_full=statistics.fmean(accf),acc_surv=statistics.fmean(accs),
                    removal_rate=rrm,removal_ci=rrh,
                    mean_L_full=statistics.fmean(mlf),mean_L_surv=statistics.fmean(mls),
                    ci_covers_0 = (abs(dm)<=dh)))
                if alpha==0.0:
                    # build length-binned removal curve + union-bound prediction
                    bins=sorted(agg_len_remove.keys())
                    # coarse bins
                    binedges=[12,16,20,26,34,45,60,80,110,150,200,400]
                    binagg={}
                    for L in bins:
                        for bi in range(len(binedges)-1):
                            if binedges[bi]<=L<binedges[bi+1]:
                                e=binagg.setdefault(bi,[0,0,0.0]); 
                                e[0]+=agg_len_remove[L][0]; e[1]+=agg_len_remove[L][1]
                                break
                    for bi in sorted(binagg.keys()):
                        rem,tot,_=binagg[bi]
                        Lmid=(binedges[bi]+binedges[bi+1])/2
                        ng=max(0,Lmid-k+1)
                        pred=1-(1-q)**ng
                        anchor_rows.append(dict(c=cname,q=q,k=k,
                            L_lo=binedges[bi],L_hi=binedges[bi+1],L_mid=Lmid,
                            removal_emp=rem/tot if tot else float('nan'),
                            removal_pred_unionbound=pred,n=tot))
    # write CSVs
    with open(os.path.join(ART,'results','delta_table.csv'),'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with open(os.path.join(ART,'results','anchor_table.csv'),'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(anchor_rows[0].keys())); w.writeheader(); w.writerows(anchor_rows)
    print("elapsed %.1fs  rows=%d anchor=%d"%(time.time()-t0,len(rows),len(anchor_rows)))
    return rows, anchor_rows

if __name__=='__main__':
    os.makedirs(os.path.join(ART,'results'),exist_ok=True)
    main()
