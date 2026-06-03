#!/usr/bin/env python3
"""EXP-0052 / CLAIM-0049 — retention-policy quality skew under identical cluster removal.
L0 CPU-only, pure stdlib, SERIAL. Harness owns GT (latent q). Detector blind to q.
Policies blind to q. Skew measured after the fact."""
import random, hashlib, math, statistics, csv, time, os, sys

ARTDIR = os.path.dirname(os.path.abspath(__file__))
RESDIR = os.path.join(ARTDIR, "results")
os.makedirs(RESDIR, exist_ok=True)

# ---------------- config ----------------
N = 15000
V = 20000               # vocab size
F_CLUST = 0.30          # fraction of docs in near-dup clusters
NUM_PERM = 64
BANDS, ROWS = 16, 4     # 16*4=64 ; LSH ~ threshold (1/b)^(1/r) = (1/16)^.25 ~ 0.5
BASE_LEN = 60           # base token-set size
BETA = 0.35             # completeness-quality coupling (size *= 1+beta*q)
JACCARD_TARGET = 0.82   # within-cluster near-dup level
NSEEDS = 22
RHO_SWEEP = [-0.6,-0.4,-0.2,0.0,0.1,0.2,0.3,0.4,0.6,0.8,1.0]
REALISTIC_RHO = 0.2
SIGMA_WITHIN_DEFAULT = 1.0
SIGMA_SWEEP = [0.0,0.5,1.0,1.5]

# MinHash via universal hashing: h_i(x) = (a_i*x + b_i) mod P, on integer token ids.
# This is a REAL MinHash (k independent permutations of the universe), pure stdlib, fast.
# Permutation params seeded from sha1 so they are fixed/reproducible (hashlib-derived).
_P = (1 << 61) - 1  # Mersenne prime
def _perm_params(nperm):
    rng = random.Random(int.from_bytes(hashlib.sha1(b"minhash-perms").digest()[:8],'big'))
    return [(rng.randrange(1,_P), rng.randrange(0,_P)) for _ in range(nperm)]
PERMS = _perm_params(NUM_PERM)

def minhash(token_set):
    if not token_set:
        return tuple([0]*NUM_PERM)
    sig = []
    for a,b in PERMS:
        m = min(((a*t + b) % _P) for t in token_set)
        sig.append(m)
    return tuple(sig)

# ---------------- generative world ----------------
def gen_docs(seed, sigma_within=SIGMA_WITHIN_DEFAULT):
    """Generate docs with latent q and token-sets. NO positions yet (rho-independent).
    Detection depends only on token-sets, so this is computed ONCE per (seed,sigma)."""
    rng = random.Random(seed)
    docs = []
    did = 0
    n_clustered = int(N * F_CLUST)
    n_singleton = N - n_clustered
    for _ in range(n_singleton):
        q = rng.gauss(0,1)
        size = max(5, int(round(BASE_LEN * (1 + BETA*q))))
        toks = set(rng.randrange(V) for _ in range(size))
        docs.append({"id": did, "q": q, "tokens": toks, "cluster": None})
        did += 1
    cid = 0
    placed = 0
    while placed < n_clustered:
        k = rng.choice([2,3,4,5])
        if placed + k > n_clustered:
            k = n_clustered - placed
            if k < 2: k = 2
        q_cluster = rng.gauss(0,1)
        base_size = max(8, int(round(BASE_LEN)))
        base = set(rng.randrange(V) for _ in range(base_size))
        base_list = list(base)
        for _m in range(k):
            qm = q_cluster + rng.gauss(0, sigma_within)
            size = max(5, int(round(base_size * (1 + BETA*qm*0.5))))
            nkeep = max(3, int(round(len(base_list)*JACCARD_TARGET)))
            kept = set(rng.sample(base_list, min(nkeep, len(base_list))))
            toks = set(kept)
            while len(toks) < size:
                toks.add(rng.randrange(V))
            docs.append({"id": did, "q": qm, "tokens": toks, "cluster": cid})
            did += 1
            placed += 1
        cid += 1
    return docs, cid

def assign_positions(docs, seed, rho):
    """Assign stream positions with order-quality correlation rho (Gaussian copula on q).
    Returns a new pos array indexed by doc index; does not mutate token-sets."""
    rng = random.Random(seed*104729 + 7)
    scored = []
    for i,d in enumerate(docs):
        noise = rng.gauss(0,1)
        pscore = rho*d["q"] + math.sqrt(max(0,1-rho*rho))*noise
        scored.append((pscore, i))
    scored.sort()
    pos = [0]*len(docs)
    for p,(ps,i) in enumerate(scored):
        pos[i] = p
    return pos

# ---------------- detector: real MinHash + LSH ----------------
def detect_clusters(docs):
    """Returns: parent[] union-find over doc indices for detected near-dup components.
    Blind to q. Uses MinHash sigs + LSH banding."""
    sigs = [minhash(d["tokens"]) for d in docs]
    # union-find
    parent = list(range(len(docs)))
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return x
    def union(a,b):
        ra,rb=find(a),find(b)
        if ra!=rb: parent[ra]=rb
    # LSH banding
    for band in range(BANDS):
        buckets = {}
        for i,sig in enumerate(sigs):
            key = (band,) + sig[band*ROWS:(band+1)*ROWS]
            buckets.setdefault(key, []).append(i)
        for key, members in buckets.items():
            if len(members) > 1:
                first = members[0]
                for m in members[1:]:
                    union(first, m)
    # build components
    comp = {}
    for i in range(len(docs)):
        r = find(i)
        comp.setdefault(r, []).append(i)
    detected = [m for m in comp.values() if len(m) > 1]
    return detected, sigs

# ---------------- retention policies ----------------
def apply_policies(docs, detected, pos, seed):
    rng = random.Random(seed*7919 + 13)
    removed_first=set(); removed_last=set(); removed_rand=set()
    for comp in detected:
        kf = min(comp, key=lambda i: pos[i])
        kl = max(comp, key=lambda i: pos[i])
        kr = rng.choice(comp)
        for i in comp:
            if i!=kf: removed_first.add(i)
            if i!=kl: removed_last.add(i)
            if i!=kr: removed_rand.add(i)
    return removed_first, removed_last, removed_rand

def mean_q(docs, removed):
    qs = [docs[i]["q"] for i in range(len(docs)) if i not in removed]
    return statistics.fmean(qs)

# ---------------- detection cache + measurement ----------------
def measure(docs, detected, nclust, pos, seed):
    rf, rl, rr = apply_policies(docs, detected, pos, seed)
    corpus_sd = statistics.pstdev([d["q"] for d in docs])
    mr = mean_q(docs, rr); mf = mean_q(docs, rf); ml = mean_q(docs, rl)
    df = (mf - mr)/corpus_sd
    dl = (ml - mr)/corpus_sd
    # keep-random absolute bias vs full-corpus mean (should be ~0)
    full_mean = statistics.fmean([d["q"] for d in docs])
    dr_abs = (mr - full_mean)/corpus_sd
    audit_same_count = (len(rf)==len(rl)==len(rr))
    # FP: detected component spanning a singleton (None) or >1 true cluster id
    fp_docs = 0
    for comp in detected:
        cids = set(docs[i]["cluster"] for i in comp)
        if None in cids or len(cids)>1:
            fp_docs += len(comp)
    return {"df":df,"dl":dl,"dr_abs":dr_abs,"removed_first":len(rf),"removed_last":len(rl),
            "removed_rand":len(rr),"audit_same_count":audit_same_count,
            "removal_rate":len(rf)/len(docs),"fp_docs":fp_docs,
            "n_detected":len(detected),"corpus_sd":corpus_sd}

def ci95(vals):
    if len(vals)<2: return (statistics.fmean(vals),0.0)
    m=statistics.fmean(vals); s=statistics.stdev(vals)
    return (m, 1.96*s/math.sqrt(len(vals)))

if __name__=="__main__":
    t0=time.time()
    print("EXP-0052 start N=%d seeds=%d nperm=%d bands=%dx%d"%(N,NSEEDS,NUM_PERM,BANDS,ROWS),flush=True)
    # ===== MAIN: rho sweep (sigma_within default) =====
    # detect ONCE per seed (rho-independent), reuse across all rhos
    per_seed = []  # list of (docs, detected, nclust)
    for s in range(NSEEDS):
        docs, nclust = gen_docs(12345+s)
        detected, _ = detect_clusters(docs)
        per_seed.append((docs, detected, nclust))
        if s==0:
            print("  seed0: ndocs=%d nclust=%d detected=%d [%.0fs]"%(len(docs),nclust,len(detected),time.time()-t0),flush=True)
    print("  detection done for %d seeds [%.0fs]"%(NSEEDS,time.time()-t0),flush=True)

    rho_rows=[]
    for rho in RHO_SWEEP:
        dfs=[];dls=[];drs=[];same=[];fps=[];rates=[];ndet=[]
        for s in range(NSEEDS):
            docs,detected,nclust = per_seed[s]
            pos = assign_positions(docs, 12345+s, rho)
            m = measure(docs, detected, nclust, pos, 12345+s)
            dfs.append(m["df"]);dls.append(m["dl"]);drs.append(m["dr_abs"])
            same.append(m["audit_same_count"]);fps.append(m["fp_docs"])
            rates.append(m["removal_rate"]);ndet.append(m["n_detected"])
        mdf,cdf=ci95(dfs);mdl,cdl=ci95(dls);mdr,cdr=ci95(drs)
        rho_rows.append({"rho":rho,"delta_first":mdf,"ci_first":cdf,"delta_last":mdl,"ci_last":cdl,
                         "delta_rand_abs":mdr,"ci_rand":cdr,"all_audit_same_count":all(same),
                         "mean_fp_docs":statistics.fmean(fps),"mean_removal_rate":statistics.fmean(rates),
                         "mean_n_detected":statistics.fmean(ndet),"nseeds":NSEEDS})
        print("rho=%+.2f Df=%+.4f±%.4f Dl=%+.4f±%.4f Dr=%+.4f±%.4f same=%s rate=%.4f fp=%.0f [%.0fs]"%(
            rho,mdf,cdf,mdl,cdl,mdr,cdr,all(same),statistics.fmean(rates),statistics.fmean(fps),time.time()-t0),flush=True)
    with open(os.path.join(RESDIR,"rho_sweep.csv"),"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rho_rows[0].keys()));w.writeheader();w.writerows(rho_rows)

    # ===== within-cluster variance sweep (at realistic rho) =====
    sig_rows=[]
    SIG_SEEDS=10
    for sw in SIGMA_SWEEP:
        dfs=[];dls=[]
        for s in range(SIG_SEEDS):
            docs,nclust = gen_docs(12345+s, sigma_within=sw)
            detected,_ = detect_clusters(docs)
            pos = assign_positions(docs, 12345+s, REALISTIC_RHO)
            m = measure(docs, detected, nclust, pos, 12345+s)
            dfs.append(m["df"]);dls.append(m["dl"])
        mdf,cdf=ci95(dfs);mdl,cdl=ci95(dls)
        sig_rows.append({"sigma_within":sw,"rho":REALISTIC_RHO,"delta_first":mdf,"ci_first":cdf,
                         "delta_last":mdl,"ci_last":cdl,"nseeds":SIG_SEEDS})
        print("sigma_within=%.1f (rho=%.1f) Df=%+.4f±%.4f Dl=%+.4f±%.4f [%.0fs]"%(
            sw,REALISTIC_RHO,mdf,cdf,mdl,cdl,time.time()-t0),flush=True)
    with open(os.path.join(RESDIR,"sigma_sweep.csv"),"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(sig_rows[0].keys()));w.writeheader();w.writerows(sig_rows)

    # ===== GUARD B: byte-identical removed cluster set check (one representative seed) =====
    docs,nclust = gen_docs(12345)
    detected,_ = detect_clusters(docs)
    pos0 = assign_positions(docs,12345,REALISTIC_RHO)
    rf,rl,rr = apply_policies(docs,detected,pos0,12345)
    # the CLUSTER set each policy operates on is `detected` (identical by construction).
    # removed docs differ (different representative kept) but #removed identical & clusters identical.
    clusters_identical = True  # all three iterate the SAME `detected` list
    same_count = (len(rf)==len(rl)==len(rr))
    with open(os.path.join(RESDIR,"guardB_audit.csv"),"w",newline="") as f:
        w=csv.writer(f);w.writerow(["check","value"])
        w.writerow(["n_detected_clusters",len(detected)])
        w.writerow(["clusters_identical_across_policies",clusters_identical])
        w.writerow(["removed_first",len(rf)]);w.writerow(["removed_last",len(rl)]);w.writerow(["removed_rand",len(rr)])
        w.writerow(["removed_count_identical",same_count])
        w.writerow(["removal_rate",len(rf)/len(docs)])
    print("GUARD B: clusters_identical=%s removed F/L/R=%d/%d/%d count_identical=%s"%(
        clusters_identical,len(rf),len(rl),len(rr),same_count),flush=True)
    print("DONE total %.0fs"%(time.time()-t0),flush=True)
