#!/usr/bin/env python3
"""E-B analysis (rigorous). Two distinct exponent tests:

  (A) PENALTY-RATIO scaling:   penalty(L) = TTFT_cont/TTFT_hit ~ L^kappa  (per engine, P=50)
      This is the headline "is the workload pathology superlinear" number, but it is a
      RATIO of two L-dependent quantities, so its exponent is NOT directly comparable to
      the quadratic-attention prediction.

  (B) THE PROPER QUADRATIC TEST: fit the ABSOLUTE recompute cost
          TTFT_cont(N) ~ N^k        where N = recomputed token count = (L - P_tokens)
      Naive masked-attention prefill over N tokens with full preceding context costs
      ~ O(N * L) FLOPs; in the P=50 slice L=2N so cost ~ O(N^2) -> k_pred = 2.0.
      MLP/projection cost is O(N*d) -> linear. So a compute-bound prefill predicts
      1.0 <= k <= 2.0, approaching 2.0 only when attention dominates.
      VERDICT RULE on the ABSOLUTE recompute exponent k:
        k CI upper < 1.85  -> SUB-quadratic (bandwidth/kernel/launch-bound; below naive attn)
        1.85..2.15         -> consistent with quadratic attention (known algebra)
        k CI lower > 2.15  -> SUPER-quadratic = system amplifier (the discovery)
"""
import csv, math
CSV = "/home/dengcchi/committee_naviC/data/eb_injection_scaling.csv"

def fit(xs, ys):
    lx=[math.log(x) for x in xs]; ly=[math.log(y) for y in ys]; n=len(lx)
    mx=sum(lx)/n; my=sum(ly)/n
    sxx=sum((x-mx)**2 for x in lx); sxy=sum((lx[i]-mx)*(ly[i]-my) for i in range(n))
    k=sxy/sxx; b=my-k*mx
    yhat=[k*lx[i]+b for i in range(n)]
    ss_res=sum((ly[i]-yhat[i])**2 for i in range(n)); ss_tot=sum((y-my)**2 for y in ly)
    r2=1-ss_res/ss_tot if ss_tot>0 else float("nan")
    se=math.sqrt(ss_res/(n-2)/sxx) if n>2 else float("nan")
    return k, math.exp(b), r2, se

def main():
    rows=list(csv.DictReader(open(CSV)))
    for r in rows:
        r["context_len"]=int(r["context_len"]); r["inject_pos_pct"]=int(r["inject_pos_pct"])
        for f in ("ttft_cachehit_ms","ttft_contaminated_ms","penalty_ratio"):
            r[f]=float(r[f])
        r["post_tokens"]=int(r["post_tokens"]); r["pre_tokens"]=int(r["pre_tokens"])
    engines=sorted(set(r["engine"] for r in rows))
    print("="*80); print("E-B ANALYSIS — tool-injection prefix-cache recompute scaling"); print("="*80)

    print("\n[A] Penalty-RATIO scaling  penalty(L)=TTFT_cont/TTFT_hit ~ L^kappa  (P=50%)")
    print(f"  {'engine':22}{'kappa':>8}{'SE':>7}{'R2':>8}")
    kap={}
    for e in engines:
        pts=sorted([(r["context_len"],r["penalty_ratio"]) for r in rows if r["engine"]==e and r["inject_pos_pct"]==50])
        if len(pts)<3: continue
        k,a,r2,se=fit([p[0] for p in pts],[p[1] for p in pts]); kap[e]=(k,se,r2)
        print(f"  {e:22}{k:8.3f}{se:7.3f}{r2:8.4f}")

    print("\n[B] PROPER QUADRATIC TEST — absolute recompute cost  TTFT_cont(N) ~ N^k")
    print("    N = recomputed tokens = post_tokens + tool + suffix (tokens after inject pt).")
    print(f"  {'engine':22}{'pos':>5}{'k':>8}{'SE':>7}{'R2':>8}   verdict")
    absk={}
    for e in engines:
        for P in (25,50,75):
            pts=sorted([(r["post_tokens"], r["ttft_contaminated_ms"]) for r in rows
                        if r["engine"]==e and r["inject_pos_pct"]==P and r["post_tokens"]>0])
            if len(pts)<3: continue
            k,a,r2,se=fit([p[0] for p in pts],[p[1] for p in pts])
            lo,hi=k-1.96*se,k+1.96*se
            if hi<1.85: v="SUB-quadratic (kernel/bw-bound)"
            elif lo>2.15: v="SUPER-quadratic = SYSTEM AMPLIFIER"
            else: v="~quadratic (known algebra)"
            if P==50: absk[e]=(k,se,r2)
            print(f"  {e:22}{P:5}{k:8.3f}{se:7.3f}{r2:8.4f}   {v}")

    print("\n[C] Cross-engine agreement of the ABSOLUTE recompute exponent k (P=50%)")
    if len(absk)>=2:
        kv=[v[0] for v in absk.values()]; kmean=sum(kv)/len(kv); spread=(max(kv)-min(kv))/kmean*100
        print("    "+", ".join(f"{e.split('-')[0]}={absk[e][0]:.3f}" for e in absk))
        print(f"    mean k={kmean:.3f}, spread={spread:.1f}% -> {'AGREE (<=15%, workload property)' if spread<=15 else 'DISAGREE (>15%, engine artifact)'}")

    print("\n[D] Position dependence (penalty at fixed L)")
    for e in engines:
        print(f"  {e}:")
        for L in sorted(set(r['context_len'] for r in rows if r['engine']==e)):
            ps=sorted([(r['inject_pos_pct'],r['penalty_ratio']) for r in rows if r['engine']==e and r['context_len']==L])
            print(f"    L={L:6}: "+"  ".join(f"P{p}%={v:.2f}x" for p,v in ps))
    print("="*80)

if __name__=="__main__": main()
