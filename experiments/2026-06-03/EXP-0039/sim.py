#!/usr/bin/env python3
"""EXP-0039 / CLAIM-0041 — write-amplification + pre-write dedup vs size-cap eviction.
L0: CPU-only, stdlib-only, SERIAL, deterministic. Lexical token-set Jaccard near-dup signal.
Anti-circular: latent fact_id is ground truth; gate reads ONLY surface text.
Optimized: inverted-index candidate pruning for the dedup max-Jaccard query."""
import random, csv, os, statistics, time

ART = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ART, "results"); os.makedirs(RES, exist_ok=True)
t0 = time.time()

VOCAB = ["alpha","bravo","charlie","delta","echo","foxtrot","golf","hotel","india","juliet",
         "kilo","lima","mike","november","oscar","papa","quebec","romeo","sierra","tango",
         "uniform","victor","whiskey","xray","yankee","zulu","north","south","east","west",
         "red","green","blue","gold","silver","iron","copper","stone","river","mountain"]
FILLER = ["the","a","is","at","on","near","with","and","of","by","for","to","in"]

def make_fact_text(fact_id):
    r = random.Random(fact_id*7919+13); k = r.randint(4,6)
    return frozenset(r.sample(VOCAB, k))

def paraphrase(rng, content):
    toks = list(content)
    keep = [t for t in toks if rng.random() > 0.34] or [toks[0]]
    out = [(rng.choice(VOCAB) if rng.random()<0.34 else t) for t in keep]
    for _ in range(rng.randint(1,3)): out.append(rng.choice(FILLER))
    return frozenset(out)

def jaccard(a,b):
    if not a and not b: return 1.0
    return len(a&b)/len(a|b)

def gen_stream(seed,n_facts,T,restore_rate,paraphrase_rate):
    rng=random.Random(seed); seen=[]; writes=[]; canonical={}
    for t in range(T):
        if seen and rng.random()<restore_rate:
            fid=rng.choice(seen); base=canonical[fid]
            toks = paraphrase(rng,base) if rng.random()<paraphrase_rate else \
                   (base | {rng.choice(FILLER)} if rng.random()<0.5 else base)
        else:
            fid=len(canonical)
            if fid>=n_facts:
                fid=rng.choice(seen) if seen else 0; toks=canonical[fid]
            else:
                toks=make_fact_text(fid); canonical[fid]=toks; seen.append(fid)
        writes.append((fid,toks))
    return writes,canonical

def run_policy(writes,policy,cap,thr):
    store=[]              # list of (fact_id, frozenset tokens)
    inv={}               # token -> list of store-indices (for candidate pruning)
    present_count={}     # fact_id -> count in store
    skipped_true=skipped_false=true_dup_writes=caught_true=0
    def add(fid,toks,idx):
        for tk in toks: inv.setdefault(tk,[]).append(idx)
        present_count[fid]=present_count.get(fid,0)+1
    for fid,toks in writes:
        is_true_dup = present_count.get(fid,0)>0
        if is_true_dup: true_dup_writes+=1
        if policy=='dedup':
            # candidate store entries: those sharing >=1 token
            cand=set()
            for tk in toks: cand.update(inv.get(tk,()))
            mx=0.0
            for ci in cand:
                if ci < len(store) and store[ci] is not None:
                    j=jaccard(toks,store[ci][1])
                    if j>mx: mx=j
            if mx>=thr:
                if is_true_dup: skipped_true+=1; caught_true+=1
                else: skipped_false+=1
                continue
        elif policy=='oracle':
            if is_true_dup: skipped_true+=1; caught_true+=1; continue
        idx=len(store); store.append((fid,toks)); add(fid,toks,idx)
        if policy!='nodedup_uncapped' and (len(store)-store.count(None))>cap:
            # evict oldest non-None
            for ei in range(len(store)):
                if store[ei] is not None:
                    efid,etoks=store[ei]
                    present_count[efid]-=1
                    if present_count[efid]==0: del present_count[efid]
                    store[ei]=None
                    break
    eff=[s for s in store if s is not None]
    skt=skipped_true+skipped_false
    gp=(skipped_true/skt) if skt else float('nan')
    gr=(caught_true/true_dup_writes) if true_dup_writes else float('nan')
    return eff,dict(gate_prec=gp,gate_rec=gr,skipped_false=skipped_false,skipped_true=skipped_true)

def task_recall(eff,queries):
    present=set(f for f,_ in eff)
    return sum(1 for q in queries if q in present)/len(queries) if queries else float('nan')

def gen_queries(seed,canonical,horizon,n_q=200):
    rng=random.Random(seed*31+5); created=sorted(canonical.keys())
    if not created: return []
    n=len(created); qs=[]
    for _ in range(n_q):
        if horizon=='long': idx=rng.randint(0,max(0,int(n*0.4)-1))
        else: idx=rng.randint(int(n*0.6),n-1)
        qs.append(created[idx])
    return qs

def bootstrap_ci(d,B=2000,seed=12345):
    if not d: return (float('nan'),)*3
    rng=random.Random(seed); n=len(d); m=[]
    for _ in range(B):
        m.append(sum(d[rng.randrange(n)] for _ in range(n))/n)
    m.sort(); return (statistics.mean(d), m[int(0.025*B)], m[int(0.975*B)])

# ---- grid ----
N_FACTS=250; T=1000; SEEDS=list(range(5))
RESTORE_RATES=[0.2,0.4,0.6]; PARAPHRASE_RATES=[0.0,0.3,0.6]
HORIZONS=['long','short']; CAPS=[120,200]; THRESHOLDS=[0.3,0.5,0.7]

rows=[]; amp_rows=[]
for seed in SEEDS:
    for rr in RESTORE_RATES:
        for pr in PARAPHRASE_RATES:
            writes,canonical=gen_stream(seed,N_FACTS,T,rr,pr)
            distinct=len(canonical)
            seen_so_far=set(); td=0
            for fid,_ in writes:
                if fid in seen_so_far: td+=1
                seen_so_far.add(fid)
            amp=td/len(writes)
            amp_rows.append(dict(seed=seed,restore_rate=rr,paraphrase_rate=pr,T=T,
                distinct_facts=distinct,true_dup_writes=td,amplification_rate=round(amp,4)))
            for hz in HORIZONS:
                q=gen_queries(seed,canonical,hz)
                for cap in CAPS:
                    s_nu,_=run_policy(writes,'nodedup_uncapped',cap,0); r_nu=task_recall(s_nu,q)
                    s_sc,_=run_policy(writes,'sizecap',cap,0); r_sc=task_recall(s_sc,q)
                    s_or,_=run_policy(writes,'oracle',cap,0); r_or=task_recall(s_or,q)
                    for thr in THRESHOLDS:
                        s_dd,st=run_policy(writes,'dedup',cap,thr); r_dd=task_recall(s_dd,q)
                        rows.append(dict(seed=seed,restore_rate=rr,paraphrase_rate=pr,horizon=hz,
                            cap=cap,thr=thr,amplification_rate=round(amp,4),
                            growth_nodedup_uncapped=len(s_nu),recall_nodedup_uncapped=round(r_nu,4),
                            size_sizecap=len(s_sc),recall_sizecap=round(r_sc,4),
                            size_dedup=len(s_dd),recall_dedup=round(r_dd,4),
                            size_oracle=len(s_or),recall_oracle=round(r_or,4),
                            dedup_minus_sizecap_recall=round(r_dd-r_sc,4),
                            oracle_minus_dedup_recall=round(r_or-r_dd,4),
                            gate_prec=(round(st['gate_prec'],4) if st['gate_prec']==st['gate_prec'] else ''),
                            gate_rec=(round(st['gate_rec'],4) if st['gate_rec']==st['gate_rec'] else ''),
                            skipped_false=st['skipped_false'],skipped_true=st['skipped_true']))
    print(f"seed {seed} done @ {time.time()-t0:.1f}s", flush=True)

with open(os.path.join(RES,"amplification.csv"),"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(amp_rows[0].keys())); w.writeheader(); w.writerows(amp_rows)
with open(os.path.join(RES,"policies.csv"),"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f"WROTE {len(amp_rows)} amp rows, {len(rows)} policy rows @ {time.time()-t0:.1f}s")
print("DONE_SIM")
