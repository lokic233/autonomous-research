#!/usr/bin/env python3
# EXP-0062 v2: substantive metrics.
#  - STREAM silent-misroute rate = P(out-of-set AND emitted valid-wrong, undetected) over ALL requests.
#    This RISES as K falls because P(out-of-set) rises as the enum covers less of intent space.
#  - NEAR-MISS DANGER: misroute "confidence" = softmax prob mass on the emitted (wrong) action,
#    measured by neighbor-gap bin. Near-miss => emitted distractor is very close => HIGH confidence
#    => MORE dangerous (looks right). We report mean confidence of misroute by gap bin.
#  - GAD gap-recovery (~0), validity-monitor recall (=0), escape-recall vs proximity.
import math, random, statistics

G = 12
CELLS = [(i/(G-1), j/(G-1)) for i in range(G) for j in range(G)]
NCELLS = len(CELLS)
def dist(a,b): return math.hypot(a[0]-b[0], a[1]-b[1])
def nearest_cell(r):
    best,bi=1e9,-1
    for i,c in enumerate(CELLS):
        d=dist(r,c)
        if d<best: best,bi=d,i
    return bi

def run_cell(K, temp, sigma, seed, n_requests=500, esc_prior=None):
    rng = random.Random(seed)
    n_oos=0; stream_misroute=0; gad_recover=0; monitor_hits=0
    gap_edges=[0.10,0.20,0.30,0.45,99]
    bin_oos=[0]*len(gap_edges); bin_esc=[0]*len(gap_edges)
    bin_conf_sum=[0.0]*len(gap_edges)  # confidence of the misroute (softmax mass on emitted)
    for _ in range(n_requests):
        enum = rng.sample(range(NCELLS), K); enum_set=set(enum)
        r=(rng.random(),rng.random()); tstar=nearest_cell(r); in_set=tstar in enum_set
        logits=[(-dist(r,c)/temp + rng.gauss(0,sigma)) for c in CELLS]
        # masked argmax over enum (arm A == arm B argmax)
        best,emit=-1e18,-1
        for i in enum:
            if logits[i]>best: best,emit=logits[i],i
        if not in_set:
            n_oos+=1
            gap=min(dist(CELLS[tstar],CELLS[e]) for e in enum)
            bi=next(k for k,ub in enumerate(gap_edges) if gap<=ub)
            bin_oos[bi]+=1
            # STREAM misroute: out-of-set + emitted valid-wrong + undetected (always, on oos)
            stream_misroute+=1
            # confidence = renormalized softmax mass on emitted, over enum support (GAD-faithful dist)
            mx=max(logits[i] for i in enum)
            Z=sum(math.exp(logits[i]-mx) for i in enum)
            conf=math.exp(logits[emit]-mx)/Z
            bin_conf_sum[bi]+=conf
            if emit==tstar: gad_recover+=1   # impossible on oos -> 0
            # escape hatch
            if esc_prior is not None:
                esc_logit=esc_prior+rng.gauss(0,sigma)
                if esc_logit>logits[emit]: bin_esc[bi]+=1
    stream_rate=stream_misroute/n_requests
    oos_frac=n_oos/n_requests
    gad_rec=gad_recover/n_oos if n_oos else 0.0
    mon_recall=monitor_hits/stream_misroute if stream_misroute else 0.0
    conf_by_bin=[(bin_conf_sum[k]/bin_oos[k] if bin_oos[k] else None) for k in range(len(gap_edges))]
    esc_by_bin=[(bin_esc[k]/bin_oos[k] if bin_oos[k] else None) for k in range(len(gap_edges))]
    return dict(K=K,temp=temp,sigma=sigma,seed=seed,oos_frac=oos_frac,stream_rate=stream_rate,
                gad_rec=gad_rec,mon_recall=mon_recall,conf_by_bin=conf_by_bin,esc_by_bin=esc_by_bin,
                bin_oos=bin_oos,gap_edges=gap_edges)

def ci95(v):
    if len(v)<2: return (statistics.mean(v),0.0)
    m=statistics.mean(v); s=statistics.stdev(v); return (m,1.96*s/math.sqrt(len(v)))
print("harness2 loaded")
