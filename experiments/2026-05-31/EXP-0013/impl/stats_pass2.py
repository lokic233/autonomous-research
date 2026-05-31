"""EXP-0013 part 2: regime-resolved slope fits + sink-fraction + win-region. Loads stash from part1."""
import pickle, math, statistics, random, json, csv
S=pickle.load(open("/tmp/exp0013_stash.pkl","rb"))
rows=S["rows"]; INJ_SEQ=S["INJ_SEQ"]; SEQ_LENS=S["SEQ_LENS"]; F_POS=S["F_POS"]; SEEDS=S["SEEDS"]

def mean(xs): return sum(xs)/len(xs)
def ols(xs, ys):
    n=len(xs); mx=mean(xs); my=mean(ys)
    sxx=sum((x-mx)**2 for x in xs); sxy=sum((x-mx)*(y-my) for x,y in zip(xs,ys)); syy=sum((y-my)**2 for y in ys)
    if sxx==0: return float('nan'),float('nan'),float('nan'),n,float('nan'),n-2
    slope=sxy/sxx; intercept=my-slope*mx
    ss_res=sum((y-(slope*x+intercept))**2 for x,y in zip(xs,ys))
    r2= 1 - ss_res/syy if syy>0 else float('nan'); df=n-2
    slope_se=math.sqrt((ss_res/df)/sxx) if (df>0) else float('nan')
    return slope, intercept, r2, n, slope_se, df
def _tcdf(t,df):
    def betacf(a,b,x):
        FPMIN=1e-300; qab=a+b; qap=a+1; qam=a-1; c=1.0; d=1-qab*x/qap
        if abs(d)<FPMIN: d=FPMIN
        d=1/d; h=d
        for m in range(1,201):
            m2=2*m
            for (num,den) in [ (m*(b-m)*x,(qam+m2)*(a+m2)), (-(a+m)*(qab+m)*x,(a+m2)*(qap+m2)) ]:
                aa=num/den; d=1+aa*d
                if abs(d)<FPMIN: d=FPMIN
                c=1+aa/c
                if abs(c)<FPMIN: c=FPMIN
                d=1/d; h*=d*c
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
    for _ in range(120):
        mid=(lo+hi)/2
        if _tcdf(mid,df)<p: lo=mid
        else: hi=mid
    return (lo+hi)/2
def slope_ci(slope, se, df, level=0.95):
    if df<=0 or se!=se: return (float('nan'),float('nan'))
    tc=t_ppf(1-(1-level)/2, df); return (slope-tc*se, slope+tc*se)
def wilson(k,n,level=0.95):
    if n==0: return (float('nan'),)*3
    z=1.959963985; p=k/n; den=1+z*z/n
    c=(p+z*z/(2*n))/den; h=(z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/den
    return (p,c-h,c+h)

ENGINES=["vllm_apc","radix","flashinfer","cdc","pic_lean"]

def fit(engine, ratio_pred=None, seq=None, fpos=None):
    xs=[];ys=[]
    for r in rows:
        if r["engine"]!=engine: continue
        if ratio_pred and not ratio_pred(r["inj_seq"]): continue
        if seq and r["seq_len"]!=seq: continue
        if fpos is not None and r["f"]!=fpos: continue
        xs.append(r["inj_seq"]*100); ys.append(r["recompute_pct"])
    if len(xs)<3: return None
    sl,inter,r2,n,se,df=ols(xs,ys)
    return {"slope":sl,"ci":slope_ci(sl,se,df),"r2":r2,"n":n,"intercept":inter}

OUT={"experiment":"EXP-0013","claim":"CLAIM-0006","device":"CPU","method":"stdlib OLS/t-CI/bootstrap on recompute-fraction proxy (re-run of EXP-0003/0006 models) swept over inj/seq with 5 seeds"}

# --- (1) per-engine slope in the ANCHOR low-injection regime inj/seq<=5% (where the 'slope~1' claim lives) ---
print("### PER-ENGINE slope of recompute% vs inj/seq%, LOW regime (inj/seq<=5%) ###")
low={}
for e in ENGINES:
    d=fit(e, lambda r:r<=0.05)
    low[e]=d
    print(f"  {e:11s} slope={d['slope']:.4f} 95%CI[{d['ci'][0]:.4f},{d['ci'][1]:.4f}] R2={d['r2']:.4f} n={d['n']}")
OUT["per_engine_slope_low_regime_inj_le_5pct"]=low

# --- (2) full-range (already in part1, recomputed for completeness) ---
print("### PER-ENGINE slope, FULL range (inj/seq 0.1%-100%) — saturating, expect <1 ###")
full={}
for e in ENGINES:
    d=fit(e, lambda r:True); full[e]=d
    print(f"  {e:11s} slope={d['slope']:.4f} 95%CI[{d['ci'][0]:.4f},{d['ci'][1]:.4f}] R2={d['r2']:.4f} n={d['n']}")
OUT["per_engine_slope_full_range"]=full

# --- (3) per-engine x per-seq-len slope in low regime (block-size sensitivity) ---
print("### PER-ENGINE x PER-SEQ slope (low regime inj/seq<=5%) ###")
for e in ENGINES:
    for S_ in SEQ_LENS:
        d=fit(e, lambda r:r<=0.05, seq=S_)
        if d:
            print(f"  {e:11s} seq={S_:6d} slope={d['slope']:.4f} 95%CI[{d['ci'][0]:.4f},{d['ci'][1]:.4f}] R2={d['r2']:.4f} n={d['n']}")
            OUT.setdefault("per_engine_per_seq_slope_low",{}).setdefault(e,{})[str(S_)]=d

# --- (4) position-dependence: slope vs inj/seq at fixed f, and recompute spread across f at fixed inj ---
print("### POSITION test: does recompute% depend on inj/seq or on f? (contiguous engines) ###")
for e in ["radix","vllm_apc","cdc"]:
    for f in F_POS:
        d=fit(e, lambda r:True, fpos=f)
        print(f"  {e:11s} f={f} slope={d['slope']:.4f} R2={d['r2']:.4f}")
# recompute% spread across position at fixed (seq, inj) — quantify position sensitivity per engine
print("### POSITION SPREAD: mean |range across f| per engine (pp), at each inj/seq ###")
pos_spread={}
for e in ENGINES:
    spreads=[]
    for S_ in SEQ_LENS:
        for ratio in INJ_SEQ:
            vals_by_f=[]
            for f in F_POS:
                vv=[r["recompute_pct"] for r in rows if r["engine"]==e and r["seq_len"]==S_ and r["inj_seq"]==ratio and r["f"]==f]
                if vv: vals_by_f.append(mean(vv))
            if len(vals_by_f)>=2: spreads.append(max(vals_by_f)-min(vals_by_f))
    pos_spread[e]={"mean_pp":mean(spreads),"median_pp":statistics.median(spreads),"max_pp":max(spreads),"n_cells":len(spreads)}
    print(f"  {e:11s} mean_spread={pos_spread[e]['mean_pp']:.3f}pp median={pos_spread[e]['median_pp']:.3f}pp max={pos_spread[e]['max_pp']:.3f}pp")
OUT["position_spread_pp"]=pos_spread

# --- (5) attention-sink chunk fraction per engine (sequence-start carve-out) ---
# For an injection AT THE SEQUENCE START (f=0, prepend), what fraction of recompute is the first-chunk/sink?
# Model: CDC -> first chunk (~16 tok / S). vLLM-APC -> first fixed block (16/S). Radix -> LCP=0 so 100% (no prefix reuse).
print("### ATTENTION-SINK chunk fraction per engine (f=0 prepend, small inj) ###")
import hashlib
def cdc_blocks(tokens, tgt=16, mask=0xF):
    blocks=[]; cur=[]
    for t in tokens:
        cur.append(t)
        if (int.from_bytes(hashlib.blake2b(str(t).encode(),digest_size=2).digest(),"little") & mask)==0 or len(cur)>=2*tgt:
            blocks.append(tuple(cur)); cur=[]
    if cur: blocks.append(tuple(cur))
    return blocks
sink={}
for e in ENGINES:
    fracs=[]
    for S_ in SEQ_LENS:
        for sd in SEEDS:
            rnd=random.Random(777+sd+S_)
            base=[rnd.randint(10,50000) for _ in range(S_)]
            if e=="cdc":
                cb=cdc_blocks(base); first_chunk=len(cb[0]); fracs.append(first_chunk/S_)
            elif e=="vllm_apc":
                fracs.append(16.0/S_)
            elif e in ("radix","flashinfer"):
                # prepend at f=0 -> LCP=0 -> whole sequence recomputed; "sink" = first token only
                fracs.append(1.0/S_)
            elif e=="pic_lean":
                # PIC boundary window W=256 around seam; at seq start that window IS the sink carve-out
                fracs.append(min(256,S_)/S_)
    sink[e]={"mean_first_chunk_frac":mean(fracs),"as_pct":100*mean(fracs)}
    print(f"  {e:11s} sink/first-chunk fraction = {100*mean(fracs):.4f}% of seq (mean over seq_lens,seeds)")
OUT["attention_sink_first_chunk_fraction_pct"]={k:v["as_pct"] for k,v in sink.items()}

# --- (6) win-region fraction with Wilson CI: among ALL cells, fraction where CDC beats lean-PIC ---
mr={}
for r in rows: mr[(r["engine"],r["seq_len"],r["inj_seq"],r["f"],r["seed"])]=r["recompute_pct"]
def winfrac(ratio_pred):
    wins=0;tot=0
    for S_ in SEQ_LENS:
        for ratio in INJ_SEQ:
            if not ratio_pred(ratio): continue
            for f in F_POS:
                for sd in SEEDS:
                    c=mr[("cdc",S_,ratio,f,sd)]; p=mr[("pic_lean",S_,ratio,f,sd)]
                    tot+=1
                    if c < p*0.95: wins+=1   # "win" = CDC at least 5% cheaper (beyond noise)
    return wins,tot
w,t=winfrac(lambda r:True); print(f"### WIN-REGION (CDC>=5% cheaper than lean-PIC): {w}/{t} = {wilson(w,t)}")
OUT["win_region_all"]={"k":w,"n":t,"wilson_ci":wilson(w,t)}
w1,t1=winfrac(lambda r:r<=0.01); print(f"###   inj/seq<=1%: {w1}/{t1} = {wilson(w1,t1)}")
OUT["win_region_inj_le_1pct"]={"k":w1,"n":t1,"wilson_ci":wilson(w1,t1)}
w5,t5=winfrac(lambda r:r>=0.05); print(f"###   inj/seq>=5%: {w5}/{t5} = {wilson(w5,t5)}")
OUT["win_region_inj_ge_5pct"]={"k":w5,"n":t5,"wilson_ci":wilson(w5,t5)}

# carry margin stats from part1
OUT["margin_cdc_vs_lean_pic"]={
  "all_mean_ci":S["margin_all_ci"],"all_median_bootci":S["margin_all_med"],
  "win_le1pct_median_bootci":S["margin_win_med"],"win_le1pct_mean_ci":S["margin_win_ci"],
  "tie_ge5pct_mean_ci":S["margin_tie_ci"]}
OUT["engine_averaged_slope_full_range"]=S["engine_averaged_slope"]
OUT["per_engine_slope_full_range_part1"]=S["per_engine_slope"]

json.dump(OUT, open("/Users/dengcchi/autonomous-research/experiments/2026-05-31/EXP-0013/experiment_result/results.json","w"), indent=2, default=str)
# CSV of raw rows
with open("/Users/dengcchi/autonomous-research/experiments/2026-05-31/EXP-0013/experiment_result/results.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["engine","seq_len","inj_seq","inj_tokens","f","seed","recompute_pct"])
    for r in rows: w.writerow([r["engine"],r["seq_len"],r["inj_seq"],r["inj_tokens"],r["f"],r["seed"],round(r["recompute_pct"],4)])
print("WROTE results.json + results.csv")
