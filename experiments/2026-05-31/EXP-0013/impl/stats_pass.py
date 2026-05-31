"""
EXP-0013 (CLAIM-0006) — STATISTICAL-RIGOR PASS (CPU-only, stdlib only; NO numpy/scipy, NO GPU).
Addresses theory_skeptic's VERDICT-0022 objection: headline characterization numbers
(median inj/seq, win-region fractions, 1.1-1.7x margin, slope~1) are point estimates without
error bars, AND slope~1 could be an ENGINE-AVERAGING ARTIFACT across engines with different block sizes.

Re-runs the EXACT recompute-fraction models from EXP-0003 (per-engine contiguous baselines:
vLLM-APC fixed-16-block, SGLang-Radix token-granularity, FlashInfer==host-engine), the CDC arm
(EXP-0002/0003), and the fair-PIC arm (EXP-0006), but now sweeps inj/seq as the INDEPENDENT
VARIABLE with multiple seeds and fits recompute% ~ inj/seq PER ENGINE (not averaged), reporting
slope + 95% CI + R^2. Also CIs on the margin + attention-sink chunk fraction per engine.
All stats (OLS, t-CI, R^2, bootstrap, t inverse-CDF) implemented in pure stdlib.
"""
import json, hashlib, random, math, statistics, csv, pickle

def hfn(b): return hashlib.blake2b(repr(b).encode(), digest_size=16).digest()
def fixed_blocks(tokens, B=16):
    return [tuple(tokens[i:i+B]) for i in range(0, len(tokens)-B+1, B)]
def cdc_blocks(tokens, tgt=16, mask=0xF):
    blocks=[]; cur=[]
    for t in tokens:
        cur.append(t)
        if (int.from_bytes(hashlib.blake2b(str(t).encode(),digest_size=2).digest(),"little") & mask)==0 or len(cur)>=2*tgt:
            blocks.append(tuple(cur)); cur=[]
    if cur: blocks.append(tuple(cur))
    return blocks
def vllm_apc_recompute_pct(base, contam, B=16):
    fb_base=fixed_blocks(base,B); fb_con=fixed_blocks(contam,B)
    cached=set(hfn(b) for b in fb_base)
    first=next((i for i in range(min(len(fb_base),len(fb_con))) if hfn(fb_con[i]) not in cached), len(fb_con))
    rec_blocks=len(fb_con)-first
    return 100.0*(rec_blocks*B)/max(1,(len(fb_con)*B))
def radix_recompute_pct(base, contam):
    n=min(len(base),len(contam)); lcp=0
    while lcp<n and base[lcp]==contam[lcp]: lcp+=1
    return 100.0*(len(contam)-lcp)/max(1,len(contam))
def flashinfer_recompute_pct(base, contam):
    return radix_recompute_pct(base, contam)
def cdc_recompute_pct(base, contam):
    cb_base=cdc_blocks(base); cb_con=cdc_blocks(contam)
    cached=set(hfn(b) for b in cb_base)
    rec_tokens=sum(len(b) for b in cb_con if hfn(b) not in cached)
    return 100.0*rec_tokens/max(1,sum(len(b) for b in cb_con))
def pic_recompute_pct(S, R, p_frac, W):
    rec = R + min(S, min(W,S) + math.ceil(p_frac*S))
    return 100.0*rec/(S+R)

def mean(xs): return sum(xs)/len(xs)
def ols(xs, ys):
    n=len(xs); mx=mean(xs); my=mean(ys)
    sxx=sum((x-mx)**2 for x in xs); sxy=sum((x-mx)*(y-my) for x,y in zip(xs,ys)); syy=sum((y-my)**2 for y in ys)
    slope=sxy/sxx; intercept=my-slope*mx
    ss_res=sum((y-(slope*x+intercept))**2 for x,y in zip(xs,ys))
    r2= 1 - ss_res/syy if syy>0 else float('nan')
    df=n-2
    slope_se=math.sqrt((ss_res/df)/sxx) if (df>0 and sxx>0) else float('nan')
    return slope, intercept, r2, n, slope_se, df
def _tcdf(t,df):
    def betacf(a,b,x):
        FPMIN=1e-300; qab=a+b; qap=a+1; qam=a-1; c=1.0; d=1-qab*x/qap
        if abs(d)<FPMIN: d=FPMIN
        d=1/d; h=d
        for m in range(1,201):
            m2=2*m
            aa=m*(b-m)*x/((qam+m2)*(a+m2)); d=1+aa*d
            if abs(d)<FPMIN: d=FPMIN
            c=1+aa/c
            if abs(c)<FPMIN: c=FPMIN
            d=1/d; h*=d*c
            aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2)); d=1+aa*d
            if abs(d)<FPMIN: d=FPMIN
            c=1+aa/c
            if abs(c)<FPMIN: c=FPMIN
            d=1/d; de=d*c; h*=de
            if abs(de-1)<3e-12: break
        return h
    def betai(a,b,x):
        if x<=0: return 0.0
        if x>=1: return 1.0
        bt=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log(1-x))
        return bt*betacf(a,b,x)/a if x<(a+1)/(a+b+2) else 1-bt*betacf(b,a,1-x)/b
    x=df/(df+t*t); ib=betai(df/2,0.5,x)
    return 1-0.5*ib if t>0 else 0.5*ib
def t_ppf(p, df):
    lo,hi=-100.0,100.0
    for _ in range(200):
        mid=(lo+hi)/2
        if _tcdf(mid,df)<p: lo=mid
        else: hi=mid
    return (lo+hi)/2
def slope_ci(slope, slope_se, df, level=0.95):
    if df<=0 or math.isnan(slope_se): return (float('nan'),float('nan'))
    tc=t_ppf(1-(1-level)/2, df); return (slope-tc*slope_se, slope+tc*slope_se)
def mean_ci(xs, level=0.95):
    n=len(xs)
    if n<2: return (mean(xs) if xs else float('nan'), float('nan'), float('nan'), 0.0)
    m=mean(xs); sd=statistics.stdev(xs); se=sd/math.sqrt(n); tc=t_ppf(1-(1-level)/2, n-1)
    return (m, m-tc*se, m+tc*se, sd)
def bootstrap_median_ci(xs, level=0.95, B=5000, seed=42):
    rnd=random.Random(seed); n=len(xs); meds=[]
    for _ in range(B):
        meds.append(statistics.median([xs[rnd.randrange(n)] for _ in range(n)]))
    meds.sort(); return statistics.median(xs), meds[int((1-level)/2*B)], meds[int((1-(1-level)/2)*B)-1]
def wilson_ci(k, n, level=0.95):
    if n==0: return (float('nan'),float('nan'),float('nan'))
    z=t_ppf(1-(1-level)/2, 10**6); p=k/n; den=1+z*z/n
    centre=(p+z*z/(2*n))/den; half=(z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)))/den
    return (p, centre-half, centre+half)

SEQ_LENS=[4000,8000,32000]
INJ_SEQ=[0.001,0.005,0.01,0.02,0.05,0.10,0.25,0.50,1.00]
F_POS=[0.1,0.5,0.9]
SEEDS=[0,1,2,3,4]
PIC_P=0.01; PIC_W=256
ENGINES=["vllm_apc","radix","flashinfer","cdc","pic_lean"]

rows=[]
for S in SEQ_LENS:
    for ratio in INJ_SEQ:
        Rtok=max(1,int(round(ratio*S)))
        for f in F_POS:
            for sd in SEEDS:
                rnd=random.Random(10_000_000*sd + 1000*S + Rtok + int(f*100))
                base=[rnd.randint(10,50000) for _ in range(S)]
                tool=[rnd.randint(10,50000) for _ in range(Rtok)]
                p=int(S*f); contam=base[:p]+tool+base[p:]
                vals={"vllm_apc":vllm_apc_recompute_pct(base,contam),
                      "radix":radix_recompute_pct(base,contam),
                      "flashinfer":flashinfer_recompute_pct(base,contam),
                      "cdc":cdc_recompute_pct(base,contam),
                      "pic_lean":pic_recompute_pct(S,Rtok,PIC_P,PIC_W)}
                for eng,v in vals.items():
                    rows.append({"engine":eng,"seq_len":S,"inj_seq":ratio,"inj_tokens":Rtok,"f":f,"seed":sd,"recompute_pct":v})

per_engine_slope={}
for eng in ENGINES:
    xs=[r["inj_seq"]*100 for r in rows if r["engine"]==eng]
    ys=[r["recompute_pct"] for r in rows if r["engine"]==eng]
    slope,inter,r2,n,se,df=ols(xs,ys)
    per_engine_slope[eng]={"slope":slope,"slope_ci":slope_ci(slope,se,df),"intercept":inter,"r2":r2,"n":n,"slope_se":se}

avg_rows={}
for r in rows:
    if r["engine"] in ("vllm_apc","radix","flashinfer"):
        avg_rows.setdefault((r["seq_len"],r["inj_seq"],r["f"],r["seed"]),[]).append(r["recompute_pct"])
xs_avg=[k[1]*100 for k in avg_rows]; ys_avg=[mean(v) for v in avg_rows.values()]
slope,inter,r2,n,se,df=ols(xs_avg,ys_avg)
engine_averaged_slope={"slope":slope,"slope_ci":slope_ci(slope,se,df),"intercept":inter,"r2":r2,"n":n}

mr={}
for r in rows: mr[(r["engine"],r["seq_len"],r["inj_seq"],r["f"],r["seed"])]=r["recompute_pct"]
def collect_margin(pred):
    out=[]
    for S in SEQ_LENS:
        for ratio in INJ_SEQ:
            if not pred(ratio): continue
            for f in F_POS:
                for sd in SEEDS:
                    c=mr[("cdc",S,ratio,f,sd)]; p=mr[("pic_lean",S,ratio,f,sd)]
                    if c>0: out.append(p/c)
    return out
margins=collect_margin(lambda r:True)
margins_win=collect_margin(lambda r:r<=0.01)
margins_tie=collect_margin(lambda r:r>=0.05)
margin_all_ci=mean_ci(margins); margin_all_med=bootstrap_median_ci(margins)
margin_win_med=bootstrap_median_ci(margins_win); margin_win_ci=mean_ci(margins_win)
margin_tie_ci=mean_ci(margins_tie)

print("=== PER-ENGINE SLOPE (recompute% vs inj/seq%, all positions+seq) ===")
for eng in ENGINES:
    d=per_engine_slope[eng]
    print(f"  {eng:11s} slope={d['slope']:.4f} 95%CI[{d['slope_ci'][0]:.4f},{d['slope_ci'][1]:.4f}] R2={d['r2']:.4f} n={d['n']}")
d=engine_averaged_slope
print(f"=== ENGINE-AVERAGED(3 contiguous): slope={d['slope']:.4f} 95%CI[{d['slope_ci'][0]:.4f},{d['slope_ci'][1]:.4f}] R2={d['r2']:.4f} n={d['n']}")
print("=== CDC vs lean-PIC margin ===")
print(f"  ALL: mean={margin_all_ci[0]:.3f} 95%CI[{margin_all_ci[1]:.3f},{margin_all_ci[2]:.3f}] sd={margin_all_ci[3]:.3f} n={len(margins)} median={margin_all_med[0]:.3f} boot95%CI[{margin_all_med[1]:.3f},{margin_all_med[2]:.3f}]")
print(f"  win(<=1%): median={margin_win_med[0]:.3f} boot95%CI[{margin_win_med[1]:.3f},{margin_win_med[2]:.3f}] mean={margin_win_ci[0]:.3f} n={len(margins_win)}")
print(f"  tie(>=5%): mean={margin_tie_ci[0]:.3f} 95%CI[{margin_tie_ci[1]:.3f},{margin_tie_ci[2]:.3f}] n={len(margins_tie)}")

pickle.dump({"rows":rows,"per_engine_slope":per_engine_slope,"engine_averaged_slope":engine_averaged_slope,
             "margin_all_ci":margin_all_ci,"margin_all_med":margin_all_med,"margin_win_med":margin_win_med,
             "margin_win_ci":margin_win_ci,"margin_tie_ci":margin_tie_ci,"margins":margins,
             "INJ_SEQ":INJ_SEQ,"SEQ_LENS":SEQ_LENS,"F_POS":F_POS,"SEEDS":SEEDS},
            open("/tmp/exp0013_stash.pkl","wb"))
print("stashed.")
