#!/usr/bin/env python3
"""EXP-0035 / CLAIM-0038 — pre-call schema-geometry as wrong-tool-selection predictor.
L0: CPU-only, stdlib-only, SERIAL. Anti-circular, anti-relabeling.
See PRE_REGISTRATION.md. y generated from LATENT confusability c + difficulty d, never schema tokens.
Schema-overlap predictor reads ONLY noisy lexical schema overlap (proxy of c). Oracle reads c."""
import random, math, csv, os, time

ART = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ART, "results"); os.makedirs(RES, exist_ok=True)
LOG = os.path.join(ART, "logs"); os.makedirs(LOG, exist_ok=True)

# ---------- helpers ----------
def sigmoid(x):
    if x < -60: return 0.0
    if x > 60: return 1.0
    return 1.0/(1.0+math.exp(-x))

VOCAB = 200  # synthetic schema vocabulary size

def make_tool_schema(rng, topic, spread):
    """A tool schema = bag of token ids drawn around a latent topic center.
    'topic' is a float in [0,1] mapped to a vocab center; spread controls width.
    Higher topic-closeness between two tools => higher lexical overlap (noisy proxy of confusability)."""
    center = int(topic * (VOCAB-1))
    n = rng.randint(8, 14)
    toks = set()
    for _ in range(n):
        # gaussian-ish around center, wrapped, with 'spread' tokens of noise
        off = int(rng.gauss(0, spread))
        toks.add((center + off) % VOCAB)
    # add a few pure-noise tokens (generic-language tokens common to all tools)
    for _ in range(rng.randint(1,3)):
        toks.add(rng.randint(0, VOCAB-1))
    return toks

def jaccard(a, b):
    u = len(a | b)
    return (len(a & b)/u) if u else 0.0

def cos_bag(a, b):
    # bag cosine for sets (binary) == |a&b|/sqrt(|a||b|)
    if not a or not b: return 0.0
    return len(a & b)/math.sqrt(len(a)*len(b))

# ---------- AUC (Mann-Whitney) ----------
def auc(scores, labels):
    pos = [s for s,l in zip(scores,labels) if l==1]
    neg = [s for s,l in zip(scores,labels) if l==0]
    if not pos or not neg: return 0.5
    # rank-based
    paired = sorted(zip(scores,labels), key=lambda x:x[0])
    # assign average ranks
    ranks=[0.0]*len(paired); i=0
    while i < len(paired):
        j=i
        while j+1 < len(paired) and paired[j+1][0]==paired[i][0]: j+=1
        r=(i+j)/2.0+1
        for k in range(i,j+1): ranks[k]=r
        i=j+1
    sum_pos=sum(rk for rk,(s,l) in zip(ranks,paired) if l==1)
    n_pos=len(pos); n_neg=len(neg)
    return (sum_pos - n_pos*(n_pos+1)/2.0)/(n_pos*n_neg)

def standardize(xs):
    m=sum(xs)/len(xs)
    v=sum((x-m)**2 for x in xs)/len(xs)
    sd=math.sqrt(v) if v>0 else 1.0
    return [(x-m)/sd for x in xs]

# ---------- one cell ----------
def run_cell(seed, K, rho, sigma_lp, N=4000):
    rng = random.Random(seed*1000 + K*17 + int(rho*100) + int(sigma_lp*100))
    # store per-call features + label
    rows=[]
    # model coefficients (fixed): error driven by confusability c and difficulty d
    b0, bc, bd = -1.2, 2.6, 1.8
    for i in range(N):
        # latent difficulty d ~ U(0,1)
        d = rng.random()
        # latent confusability c: correlated with d by rho, else independent
        base = rng.random()
        c = max(0.0, min(1.0, rho*d + (1-rho)*base))
        # ---- build toolset of K tools with topics; correct tool topic = t0 ----
        t0 = rng.random()
        # nearest distractor placed close to t0 by amount governed by c (high c => closer topic)
        # topic gap shrinks with c => more lexical overlap (noisy proxy)
        gap = (1.0 - c) * 0.5 + rng.uniform(-0.03,0.03)
        sign = 1 if rng.random()<0.5 else -1
        t_dist = max(0.0, min(1.0, t0 + sign*gap))
        topics=[t0, t_dist]
        for _ in range(K-2):
            topics.append(rng.random())
        spread = 6.0  # lexical readout noise (proxy noise) — moderate, fixed
        schemas=[make_tool_schema(rng, tp, spread) for tp in topics]
        # ---- schema-overlap features (OBSERVABLE, schema-only, pre-call) ----
        sims=[]
        for a in range(K):
            for b in range(a+1,K):
                sims.append(cos_bag(schemas[a], schemas[b]))
        max_sim=max(sims); mean_sim=sum(sims)/len(sims)
        # ---- selection-error label from LATENT c,d (NEVER from schema tokens) ----
        p_err = sigmoid(b0 + bc*(c-0.5) + bd*(d-0.5))
        y = 1 if rng.random() < p_err else 0
        # ---- agent self-logprob: noisy readout of BOTH c and d (its own felt confidence) ----
        # high c or high d -> lower confidence (more negative logprob).
        true_conf = -(0.9*c + 0.7*d)  # latent log-confidence of its choice
        lp = true_conf + rng.gauss(0, sigma_lp)   # observed self-logprob (miscalibratable via sigma)
        # ---- generic prompt-difficulty predictor: noisy readout of d ONLY ----
        diff_pred = d + rng.gauss(0, 0.25)
        rows.append((y, max_sim, mean_sim, lp, diff_pred, c, d, p_err))
    return rows

# ---------- bootstrap CI on a statistic of paired arrays ----------
def bootstrap_delta(rows, statfn, B=1000, seed=0):
    rng=random.Random(seed)
    n=len(rows)
    vals=[]
    idx=list(range(n))
    for _ in range(B):
        samp=[rows[rng.randrange(n)] for _ in range(n)]
        vals.append(statfn(samp))
    vals.sort()
    lo=vals[int(0.025*B)]; hi=vals[int(0.975*B)]
    return lo, hi

def main():
    t0=time.time()
    Ks=[3,6,12]; rhos=[0.0,0.5]; sigmas=[0.5,1.5]; seeds=[1,2,3,4,5]
    cell_csv=open(os.path.join(RES,"cells.csv"),"w",newline="")
    cw=csv.writer(cell_csv)
    cw.writerow(["K","rho","sigma_lp","seed","N","pos_rate",
                 "auc_random","auc_diff","auc_logprob","auc_schema_max","auc_schema_mean","auc_oracle",
                 "auc_logprob_only","auc_combo","delta_auc_combo_minus_logprob",
                 "delta_schema_minus_diff"])
    # aggregate rows for pooled bootstrap by cell-key
    agg={}
    for K in Ks:
        for rho in rhos:
            for sig in sigmas:
                for sd in seeds:
                    rows=run_cell(sd,K,rho,sig)
                    y=[r[0] for r in rows]
                    pos_rate=sum(y)/len(y)
                    maxs=[r[1] for r in rows]; means=[r[2] for r in rows]
                    lp=[r[3] for r in rows]; diffp=[r[4] for r in rows]
                    c=[r[5] for r in rows]
                    rng2=random.Random(sd)
                    rand_scores=[rng2.random() for _ in rows]
                    a_rand=auc(rand_scores,y)
                    a_diff=auc(diffp,y)
                    a_lp=auc([-x for x in lp],y)        # low confidence -> high risk
                    a_smax=auc(maxs,y)
                    a_smean=auc(means,y)
                    a_orac=auc(c,y)
                    # combo: standardized(-lp)+standardized(max_sim)
                    z_neglp=standardize([-x for x in lp]); z_smax=standardize(maxs)
                    combo=[a+b for a,b in zip(z_neglp,z_smax)]
                    a_lponly=a_lp
                    a_combo=auc(combo,y)
                    delta=a_combo-a_lponly
                    delta_sd=a_smax-a_diff
                    cw.writerow([K,rho,sig,sd,len(rows),f"{pos_rate:.4f}",
                        f"{a_rand:.4f}",f"{a_diff:.4f}",f"{a_lp:.4f}",f"{a_smax:.4f}",f"{a_smean:.4f}",f"{a_orac:.4f}",
                        f"{a_lponly:.4f}",f"{a_combo:.4f}",f"{delta:.4f}",f"{delta_sd:.4f}"])
                    key=(K,rho,sig)
                    agg.setdefault(key,[]).extend(rows)
    cell_csv.close()
    # ---- pooled bootstrap CIs per (K,rho,sigma) on the two key deltas ----
    boot_csv=open(os.path.join(RES,"bootstrap.csv"),"w",newline="")
    bw=csv.writer(boot_csv)
    bw.writerow(["K","rho","sigma_lp","N","auc_schema_max","auc_diff","auc_logprob","auc_combo",
                 "delta_combo_minus_logprob","ci_lo","ci_hi",
                 "delta_schema_minus_diff","ci_lo2","ci_hi2","auc_oracle"])
    def stat_delta_combo(samp):
        y=[r[0] for r in samp]; lp=[r[3] for r in samp]; maxs=[r[1] for r in samp]
        z_neglp=standardize([-x for x in lp]); z_smax=standardize(maxs)
        combo=[a+b for a,b in zip(z_neglp,z_smax)]
        return auc(combo,y)-auc([-x for x in lp],y)
    def stat_delta_sd(samp):
        y=[r[0] for r in samp]; maxs=[r[1] for r in samp]; diffp=[r[4] for r in samp]
        return auc(maxs,y)-auc(diffp,y)
    for key in sorted(agg.keys()):
        rows=agg[key]; K,rho,sig=key
        y=[r[0] for r in rows]; lp=[r[3] for r in rows]; maxs=[r[1] for r in rows]
        diffp=[r[4] for r in rows]; c=[r[5] for r in rows]
        a_smax=auc(maxs,y); a_diff=auc(diffp,y); a_lp=auc([-x for x in lp],y)
        z_neglp=standardize([-x for x in lp]); z_smax=standardize(maxs)
        combo=[a+b for a,b in zip(z_neglp,z_smax)]; a_combo=auc(combo,y)
        a_orac=auc(c,y)
        d_combo=a_combo-a_lp; d_sd=a_smax-a_diff
        lo,hi=bootstrap_delta(rows,stat_delta_combo,B=400,seed=key[0]+int(rho*10))
        lo2,hi2=bootstrap_delta(rows,stat_delta_sd,B=400,seed=key[0]+99)
        bw.writerow([K,rho,sig,len(rows),f"{a_smax:.4f}",f"{a_diff:.4f}",f"{a_lp:.4f}",f"{a_combo:.4f}",
            f"{d_combo:.4f}",f"{lo:.4f}",f"{hi:.4f}",f"{d_sd:.4f}",f"{lo2:.4f}",f"{hi2:.4f}",f"{a_orac:.4f}"])
    boot_csv.close()
    print(f"DONE in {time.time()-t0:.1f}s -> {RES}/cells.csv , bootstrap.csv")

if __name__=="__main__":
    main()
