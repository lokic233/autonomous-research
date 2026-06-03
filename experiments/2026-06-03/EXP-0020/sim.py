#!/usr/bin/env python3
# EXP-0020 / CLAIM-0015 — quant-sensitivity PRE-decode router. stdlib-only, SERIAL.
# Anti-circular: predictor NEVER reads latent s_i; only noisy PRE-decode correlates.
import math, random, csv, os
random.seed(0)
OUT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(OUT, "results"); os.makedirs(RES, exist_ok=True)

def logistic(x): return 1.0/(1.0+math.exp(-x))

def gen_requests(n, regime, sigma_obs, seed):
    rng = random.Random(seed)
    reqs = []
    for i in range(n):
        s = rng.random()                      # LATENT true quant-sensitivity (NEVER seen by predictor)
        qfull = 1.0 + 0.1*rng.gauss(0,1)      # base quality if full-precision (request-specific)
        # ground-truth quant degradation d_i (quality drop if served by quant model)
        if regime == "request_dependent":
            d = 1.0 * (s**3.0) + 0.02*abs(rng.gauss(0,1))   # heavy-tailed in s: gamma=3
        else:  # uniform null: degradation independent of s
            d = 0.35 + 0.05*rng.gauss(0,1)
            d = max(0.0, d)
        # PRE-decode observables: noisy correlates of s
        ppl = s + sigma_obs*rng.gauss(0,1)
        p_hi_dom = logistic(4*(s-0.5))
        domain_hi = 1 if rng.random() < (p_hi_dom*(1-0.15) + (1-p_hi_dom)*0.15) else 0  # 15% flip
        arith = 1 if rng.random() < logistic(3*(s-0.5)) and rng.random()>sigma_obs*0.3 else 0
        longctx = 1 if rng.random() < logistic(3*(s-0.4)) and rng.random()>sigma_obs*0.3 else 0
        # POST-decode quant-model confidence (strong baseline signal): also noisy correlate of s
        # lower confidence <-> higher sensitivity. Give it comparable noise to be FAIR.
        conf = (1.0 - s) + sigma_obs*rng.gauss(0,1)
        reqs.append(dict(s=s, d=d, qfull=qfull, ppl=ppl, dom=domain_hi,
                         arith=arith, longctx=longctx, conf=conf))
    return reqs

# ---- logistic regression (stdlib GD) on PRE-decode features only ----
def train_logreg(rows, feat_keys, label_key, iters=250, lr=0.4):
    w = {k:0.0 for k in feat_keys}; b=0.0
    # standardize
    means={k:sum(r[k] for r in rows)/len(rows) for k in feat_keys}
    sds={k:(sum((r[k]-means[k])**2 for r in rows)/len(rows))**0.5 or 1.0 for k in feat_keys}
    def feat(r,k): return (r[k]-means[k])/sds[k]
    for _ in range(iters):
        gw={k:0.0 for k in feat_keys}; gb=0.0
        for r in rows:
            z=b+sum(w[k]*feat(r,k) for k in feat_keys)
            p=logistic(z); err=p-r[label_key]
            for k in feat_keys: gw[k]+=err*feat(r,k)
            gb+=err
        n=len(rows)
        for k in feat_keys: w[k]-=lr*gw[k]/n
        b-=lr*gb/n
    def score(r): return logistic(b+sum(w[k]*feat(r,k) for k in feat_keys))
    return score

def auc(scores, labels):
    # Mann-Whitney via tie-aware ranking, O(n log n)
    n=len(scores); npos=sum(labels); nneg=n-npos
    if npos==0 or nneg==0: return 0.5
    order=sorted(range(n), key=lambda i:scores[i])
    ranks=[0.0]*n; i=0
    while i<n:
        j=i
        while j<n and scores[order[j]]==scores[order[i]]: j+=1
        avg=(i+1+j)/2.0  # average rank (1-based)
        for k in range(i,j): ranks[order[k]]=avg
        i=j
    sum_pos=sum(ranks[i] for i in range(n) if labels[i]==1)
    return (sum_pos - npos*(npos+1)/2.0)/(npos*nneg)

def quality_policy(reqs, escalate_set):
    # escalate_set: set of indices served by full model
    tot=0.0
    for i,r in enumerate(reqs):
        if i in escalate_set: tot += r["qfull"]
        else: tot += r["qfull"] - r["d"]
    return tot/len(reqs)

def topk_idx(values, b):
    k=int(round(b*len(values)))
    order=sorted(range(len(values)), key=lambda i:-values[i])
    return set(order[:k]), k

N=2000
SEEDS=[1,2,3,4,5]
SIGMAS=[0.05,0.15,0.3,0.6,1.0]
BUDGETS=[0.05,0.1,0.2,0.3,0.5]
REGIMES=["request_dependent","uniform"]
FEATS=["ppl","dom","arith","longctx"]

pred_rows=[]    # predictability table
pareto_rows=[]  # policy quality at each b

for regime in REGIMES:
    for sigma in SIGMAS:
        aucs=[]
        for seed in SEEDS:
            reqs=gen_requests(N, regime, sigma, seed*100+hash(regime)%97)
            # label: top-30% degradation = "quant-sensitive" (materially degraded)
            ds=sorted(r["d"] for r in reqs)
            thr=ds[int(0.7*len(ds))]
            for r in reqs: r["label"]=1 if r["d"]>=thr else 0
            score=train_logreg(reqs, FEATS, "label")
            sc=[score(r) for r in reqs]; lb=[r["label"] for r in reqs]
            a=auc(sc,lb); aucs.append(a)
            # also oracle "predictor" auc = perfect (uses d) -> sanity ~1.0 (not reported as achievable)
            # Pareto policies at each b
            for b in BUDGETS:
                rng=random.Random(seed*7+int(b*100))
                # pre-decode router uses predicted degradation prob sc
                router_set,_=topk_idx(sc,b)
                # confidence-threshold: escalate lowest conf -> highest (-conf)
                conf_neg=[-r["conf"] for r in reqs]
                conf_set,_=topk_idx(conf_neg,b)
                # random
                k=int(round(b*len(reqs))); rand_set=set(rng.sample(range(len(reqs)),k))
                # oracle
                oracle_set,_=topk_idx([r["d"] for r in reqs],b)
                q_router=quality_policy(reqs,router_set)
                q_conf=quality_policy(reqs,conf_set)
                q_rand=quality_policy(reqs,rand_set)
                q_oracle=quality_policy(reqs,oracle_set)
                q_allq=quality_policy(reqs,set())
                q_allf=quality_policy(reqs,set(range(len(reqs))))
                pareto_rows.append(dict(regime=regime,sigma=sigma,seed=seed,b=b,
                    q_router=q_router,q_conf=q_conf,q_rand=q_rand,q_oracle=q_oracle,
                    q_allquant=q_allq,q_allfull=q_allf,auc=a))
        pred_rows.append(dict(regime=regime,sigma=sigma,
            auc_mean=sum(aucs)/len(aucs),
            auc_min=min(aucs),auc_max=max(aucs)))

with open(os.path.join(RES,"predictability.csv"),"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["regime","sigma","auc_mean","auc_min","auc_max"]); w.writeheader()
    for r in pred_rows: w.writerow(r)
with open(os.path.join(RES,"pareto.csv"),"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["regime","sigma","seed","b","q_router","q_conf","q_rand","q_oracle","q_allquant","q_allfull","auc"]); w.writeheader()
    for r in pareto_rows: w.writerow(r)
# ---- bootstrap CI: router-vs-confidence quality delta @ b=0.2, request_dependent, sigma=0.3 ----
boot_rows=[]
for sigma in [0.15,0.3,0.6]:
    b=0.2
    deltas=[]  # per-seed mean delta on held requests
    # collect per-request served-quality difference (router served full vs quant etc.)
    all_diffs=[]
    for seed in SEEDS:
        reqs=gen_requests(N,"request_dependent",sigma,seed*100+hash("request_dependent")%97)
        ds=sorted(r["d"] for r in reqs); thr=ds[int(0.7*len(ds))]
        for r in reqs: r["label"]=1 if r["d"]>=thr else 0
        score=train_logreg(reqs,FEATS,"label")
        sc=[score(r) for r in reqs]
        router_set,_=topk_idx(sc,b)
        conf_set,_=topk_idx([-r["conf"] for r in reqs],b)
        # per-request quality contribution diff (router - conf)
        for i,r in enumerate(reqs):
            qr = r["qfull"] if i in router_set else r["qfull"]-r["d"]
            qc = r["qfull"] if i in conf_set  else r["qfull"]-r["d"]
            all_diffs.append(qr-qc)
    # bootstrap over per-request diffs
    rng=random.Random(999)
    boots=[]
    M=len(all_diffs)
    for _ in range(1000):
        s=sum(all_diffs[rng.randrange(M)] for _ in range(M))/M
        boots.append(s)
    boots.sort()
    mean_delta=sum(all_diffs)/M
    lo=boots[int(0.025*len(boots))]; hi=boots[int(0.975*len(boots))]
    boot_rows.append(dict(sigma=sigma,b=b,mean_delta=mean_delta,ci_lo=lo,ci_hi=hi))

with open(os.path.join(RES,"bootstrap_router_vs_conf.csv"),"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["sigma","b","mean_delta","ci_lo","ci_hi"]); w.writeheader()
    for r in boot_rows: w.writerow(r)
print("DONE pred_rows=",len(pred_rows)," pareto_rows=",len(pareto_rows)," boot=",len(boot_rows))
