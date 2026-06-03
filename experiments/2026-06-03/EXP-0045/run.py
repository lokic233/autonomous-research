#!/usr/bin/env python3
"""EXP-0045 / CLAIM-0046 — in-degree -> per-item FN rate, controlled vs density.
Pure stdlib, serial, L0 CPU. See PREREGISTRATION.md."""
import math, random, heapq, time, json, os

T0 = time.time()
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
os.makedirs(RES, exist_ok=True)

# ---- locked params ----
N = 4000; D = 12; K_CLUST = 8; Q = 500; K = 10
M = 16; EF_C = 32; EF_S = 10  # AMENDMENT 1: ef_search=k (minimal honest width)
SIGMAS = [0.3, 0.5, 0.8, 1.2, 1.8, 2.5, 3.5, 5.0]
DATA_SEED = 12345; QUERY_SEED = 999
BUILD_SEEDS = [7, 11, 13, 17, 19]   # [0]=main

# ---- corpus generator ----
def gen_centers(seed):
    r = random.Random(seed)
    return [[r.uniform(-10,10) for _ in range(D)] for _ in range(K_CLUST)]

def gen_points(n, centers, seed):
    r = random.Random(seed)
    pts = []
    for i in range(n):
        c = i % K_CLUST
        sig = SIGMAS[c]
        ctr = centers[c]
        pts.append([ctr[j] + r.gauss(0, sig) for j in range(D)])
    return pts

def gen_queries(q, centers, seed):
    r = random.Random(seed)
    pts = []
    for i in range(q):
        c = r.randrange(K_CLUST)
        sig = SIGMAS[c]
        ctr = centers[c]
        pts.append([ctr[j] + r.gauss(0, sig) for j in range(D)])
    return pts

def sqdist(a, b):
    s = 0.0
    for i in range(D):
        d = a[i]-b[i]; s += d*d
    return s

# ---- exact GT oracle (graph-blind) ----
def exact_topk(query, pts, k):
    # returns list of (idx) of k nearest
    dists = [(sqdist(query, pts[i]), i) for i in range(len(pts))]
    dists.sort()
    return [idx for _,idx in dists[:k]]

# ---- density: dist to own kth true neighbor ----
def compute_density(pts, k):
    n = len(pts)
    dens = [0.0]*n
    for i in range(n):
        p = pts[i]
        ds = []
        for j in range(n):
            if j==i: continue
            ds.append(sqdist(p, pts[j]))
        ds.sort()
        dens[i] = math.sqrt(ds[k-1])  # dist to kth nbr
    return dens

# ---- NSW/HNSW-style graph build (single flat layer) ----
def greedy_search_build(pts, graph, entry, query_pt, ef):
    # returns candidate set as list of (dist, idx), size up to ef, for construction
    visited = set([entry])
    d0 = sqdist(pts[entry], query_pt)
    cand = [(d0, entry)]          # min-heap by dist (to expand nearest)
    res = [(-d0, entry)]          # max-heap of best ef (store neg dist)
    while cand:
        d, c = heapq.heappop(cand)
        worst = -res[0][0]
        if d > worst and len(res) >= ef:
            break
        for nb in graph[c]:
            if nb in visited: continue
            visited.add(nb)
            dn = sqdist(pts[nb], query_pt)
            worst = -res[0][0]
            if dn < worst or len(res) < ef:
                heapq.heappush(cand, (dn, nb))
                heapq.heappush(res, (-dn, nb))
                if len(res) > ef:
                    heapq.heappop(res)
    return [(-nd, idx) for nd, idx in res]  # (dist, idx)

def heuristic_prune(pts, base_pt, cand_list, m):
    # cand_list: list of (dist, idx). Malkov RNG heuristic. nearest-first.
    cand_list = sorted(cand_list)
    kept = []
    for d, c in cand_list:
        if len(kept) >= m: break
        good = True
        for _, k_idx in kept:
            # keep c only if c closer to base than to any kept neighbor
            if sqdist(pts[c], pts[k_idx]) < d:
                good = False; break
        if good:
            kept.append((d, c))
    return [idx for _, idx in kept]

def build_graph(pts, seed):
    n = len(pts)
    graph = [[] for _ in range(n)]
    order = list(range(n))
    random.Random(seed).shuffle(order)
    entry = order[0]
    for pos, node in enumerate(order):
        if pos == 0:
            continue
        cands = greedy_search_build(pts, graph, entry, pts[node], EF_C)
        # remove self if present
        cands = [(d,i) for d,i in cands if i != node]
        nbrs = heuristic_prune(pts, pts[node], cands, M)
        graph[node] = list(nbrs)
        # add reverse edges with re-prune
        for nb in nbrs:
            if node in graph[nb]: continue
            graph[nb].append(node)
            if len(graph[nb]) > M:
                # re-prune nb's neighbor list
                cl = [(sqdist(pts[nb], pts[x]), x) for x in graph[nb]]
                graph[nb] = heuristic_prune(pts, pts[nb], cl, M)
    return graph, entry

# ---- greedy search (tested system) ----
def greedy_search(pts, graph, entry, query_pt, ef, k):
    visited = set([entry])
    d0 = sqdist(pts[entry], query_pt)
    cand = [(d0, entry)]
    res = [(-d0, entry)]
    while cand:
        d, c = heapq.heappop(cand)
        worst = -res[0][0]
        if d > worst and len(res) >= ef:
            break
        for nb in graph[c]:
            if nb in visited: continue
            visited.add(nb)
            dn = sqdist(pts[nb], query_pt)
            worst = -res[0][0]
            if dn < worst or len(res) < ef:
                heapq.heappush(cand, (dn, nb))
                heapq.heappush(res, (-dn, nb))
                if len(res) > ef:
                    heapq.heappop(res)
    out = sorted([(-nd, idx) for nd, idx in res])[:k]
    return [idx for _, idx in out]

# ---- in-degree ----
def in_degrees(graph):
    n = len(graph)
    ind = [0]*n
    for j in range(n):
        for t in graph[j]:
            ind[t] += 1
    return ind

# ---- stats: Spearman ----
def rankdata(x):
    n = len(x)
    order = sorted(range(n), key=lambda i: x[i])
    ranks = [0.0]*n
    i = 0
    while i < n:
        j = i
        while j+1 < n and x[order[j+1]] == x[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for t in range(i, j+1):
            ranks[order[t]] = avg
        i = j+1
    return ranks

def pearson(a, b):
    n = len(a)
    ma = sum(a)/n; mb = sum(b)/n
    num = sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    da = math.sqrt(sum((a[i]-ma)**2 for i in range(n)))
    db = math.sqrt(sum((b[i]-mb)**2 for i in range(n)))
    if da==0 or db==0: return 0.0
    return num/(da*db)

def spearman(a, b):
    return pearson(rankdata(a), rankdata(b))

def ols_residuals(y, x):
    # residuals of y ~ 1 + x
    n = len(x)
    mx = sum(x)/n; my = sum(y)/n
    sxx = sum((x[i]-mx)**2 for i in range(n))
    sxy = sum((x[i]-mx)*(y[i]-my) for i in range(n))
    b = sxy/sxx if sxx else 0.0
    a = my - b*mx
    return [y[i] - (a + b*x[i]) for i in range(n)]

def partial_spearman(v1, v2, ctrl):
    # partial corr of v1,v2 controlling ctrl, on ranks (rank-residual)
    r1 = rankdata(v1); r2 = rankdata(v2); rc = rankdata(ctrl)
    res1 = ols_residuals(r1, rc)
    res2 = ols_residuals(r2, rc)
    return pearson(res1, res2)

def zscore(x):
    n = len(x); m = sum(x)/n
    sd = math.sqrt(sum((v-m)**2 for v in x)/n)
    if sd==0: return [0.0]*n
    return [(v-m)/sd for v in x]

def multiple_regression(y, X):
    # X: list of feature columns (already z-scored), add intercept. Normal equations.
    n = len(y); p = len(X)
    # design with intercept
    cols = [[1.0]*n] + X
    pp = len(cols)
    # XtX
    XtX = [[sum(cols[a][i]*cols[b][i] for i in range(n)) for b in range(pp)] for a in range(pp)]
    Xty = [sum(cols[a][i]*y[i] for i in range(n)) for a in range(pp)]
    # solve via Gaussian elimination
    A = [row[:] + [Xty[r]] for r, row in enumerate(XtX)]
    for col in range(pp):
        piv = max(range(col, pp), key=lambda r: abs(A[r][col]))
        A[col], A[piv] = A[piv], A[col]
        pv = A[col][col]
        if abs(pv) < 1e-12: continue
        for c in range(col, pp+1):
            A[col][c] /= pv
        for r in range(pp):
            if r==col: continue
            f = A[r][col]
            for c in range(col, pp+1):
                A[r][c] -= f*A[col][c]
    return [A[r][pp] for r in range(pp)]  # [b0, b1, b2,...]

print(f"[{time.time()-T0:.1f}s] params set", flush=True)

# ============ MAIN RUN ============
centers = gen_centers(1)  # fixed center seed
pts = gen_points(N, centers, DATA_SEED)
queries = gen_queries(Q, centers, QUERY_SEED)
print(f"[{time.time()-T0:.1f}s] corpus generated N={N} Q={Q}", flush=True)

# GT oracle
gt = [exact_topk(queries[qi], pts, K) for qi in range(Q)]
print(f"[{time.time()-T0:.1f}s] GT oracle done", flush=True)

# density
density = compute_density(pts, K)
print(f"[{time.time()-T0:.1f}s] density done", flush=True)

def per_item_miss(graph, entry):
    # denom[i], num[i]
    denom = [0]*N; num = [0]*N
    for qi in range(Q):
        truth = set(gt[qi])
        got = set(greedy_search(pts, graph, entry, queries[qi], EF_S, K))
        for i in truth:
            denom[i] += 1
            if i not in got:
                num[i] += 1
    return denom, num

# build main graph (seed 7) + stability builds
all_miss_rank = {}   # seed -> per-item miss list (over items with denom>=2 universe)
main_data = None
for si, seed in enumerate(BUILD_SEEDS):
    graph, entry = build_graph(pts, seed)
    denom, num = per_item_miss(graph, entry)
    ind = in_degrees(graph)
    print(f"[{time.time()-T0:.1f}s] build seed={seed} done", flush=True)
    if si == 0:
        main_data = (graph, entry, denom, num, ind)
    # store miss rate per item (use -1 for items with denom<2 -> handled in stability)
    miss = [ (num[i]/denom[i]) if denom[i]>=1 else None for i in range(N) ]
    all_miss_rank[seed] = (denom, miss)

graph, entry, denom, num, ind = main_data

# analysis universe: denom>=2
idx = [i for i in range(N) if denom[i] >= 2]
miss = [num[i]/denom[i] for i in idx]
indeg = [float(ind[i]) for i in idx]
dens = [density[i] for i in idx]
nA = len(idx)
print(f"[{time.time()-T0:.1f}s] analysis universe (denom>=2): {nA} items", flush=True)

# (a)(b)
sp_indeg_miss = spearman(indeg, miss)
sp_dens_miss = spearman(dens, miss)
sp_indeg_dens = spearman(indeg, dens)

# (c) within density strata (quartiles)
order_d = sorted(range(nA), key=lambda i: dens[i])
strata = []
qs = nA // 4
for b in range(4):
    lo = b*qs; hi = (b+1)*qs if b<3 else nA
    members = order_d[lo:hi]
    sm = [miss[i] for i in members]; si_ = [indeg[i] for i in members]
    sp = spearman(si_, sm)
    strata.append({"bin": b, "n": len(members), "spearman_indeg_miss": sp,
                   "dens_lo": dens[members[0]], "dens_hi": dens[members[-1]],
                   "mean_miss": sum(sm)/len(sm), "mean_indeg": sum(si_)/len(si_)})

# (d) partial spearman in-degree vs miss controlling density
pc = partial_spearman(indeg, miss, dens)

# (e) multiple regression miss ~ z(indeg) + z(dens)
zi = zscore(indeg); zd = zscore(dens)
coefs = multiple_regression(miss, [zi, zd])  # [b0, b_indeg, b_dens]

# bootstrap CIs for pc and coefs
rng = random.Random(2024)
B = 1000
pc_bs = []; bi_bs = []; bd_bs = []; spim_bs = []
for _ in range(B):
    samp = [rng.randrange(nA) for _ in range(nA)]
    mi = [miss[s] for s in samp]; ii = [indeg[s] for s in samp]; dd = [dens[s] for s in samp]
    pc_bs.append(partial_spearman(ii, mi, dd))
    spim_bs.append(spearman(ii, mi))
    c = multiple_regression(mi, [zscore(ii), zscore(dd)])
    bi_bs.append(c[1]); bd_bs.append(c[2])

def ci(v):
    v = sorted(v)
    return (v[int(0.025*len(v))], v[int(0.975*len(v))])

pc_ci = ci(pc_bs); bi_ci = ci(bi_bs); bd_ci = ci(bd_bs); spim_ci = ci(spim_bs)
print(f"[{time.time()-T0:.1f}s] bootstrap done", flush=True)

# stability: pairwise spearman of per-item miss across seeds (items with denom>=2 in BOTH=universe shared)
# use the union universe: items with denom>=2 in main; miss across seeds (denom>=1 used) -> require denom>=2 in each seed for inclusion in that pair
pairs = []
seeds = BUILD_SEEDS
for a in range(len(seeds)):
    for b in range(a+1, len(seeds)):
        da, ma = all_miss_rank[seeds[a]]
        db, mb = all_miss_rank[seeds[b]]
        common = [i for i in range(N) if da[i]>=2 and db[i]>=2]
        xa = [ma[i] for i in common]; xb = [mb[i] for i in common]
        sp = spearman(xa, xb)
        pairs.append({"seed_a": seeds[a], "seed_b": seeds[b], "n": len(common), "spearman": sp})
mean_stab = sum(p["spearman"] for p in pairs)/len(pairs)
print(f"[{time.time()-T0:.1f}s] stability done mean={mean_stab:.3f}", flush=True)

# in-degree distribution sanity (confound active)
import statistics
ind_all = [float(x) for x in ind]
indeg_stats = {"min": min(ind_all), "max": max(ind_all), "mean": sum(ind_all)/N,
               "stdev": statistics.pstdev(ind_all),
               "n_zero_indeg": sum(1 for x in ind if x==0)}
dens_stats = {"min": min(density), "max": max(density), "mean": sum(density)/N,
              "stdev": statistics.pstdev(density)}
overall_recall = 1 - sum(num)/sum(denom)

# ---- outcome decision ----
pc_neg_sig = (pc_ci[1] < 0)            # partial corr negative & CI excludes 0
bi_neg_sig = (bi_ci[1] < 0)            # regression coef negative & sig
strata_neg_sig = sum(1 for s in strata if s["spearman_indeg_miss"] < -0.05)
stable = mean_stab > 0.3

if pc_neg_sig and bi_neg_sig and strata_neg_sig >= 2 and stable:
    outcome = "POSITIVE"
elif (pc_ci[0] <= 0 <= pc_ci[1]):
    outcome = "HONEST-NEGATIVE"
else:
    outcome = "MIXED"

result = {
  "nA_items": nA, "overall_recall": overall_recall,
  "spearman_indeg_miss_raw": sp_indeg_miss, "spearman_indeg_miss_ci": spim_ci,
  "spearman_dens_miss_raw": sp_dens_miss,
  "spearman_indeg_dens": sp_indeg_dens,
  "partial_spearman_indeg_miss_ctrl_dens": pc, "partial_ci": pc_ci,
  "regression": {"b0": coefs[0], "b_indeg_z": coefs[1], "b_dens_z": coefs[2],
                 "b_indeg_ci": bi_ci, "b_dens_ci": bd_ci},
  "strata": strata,
  "stability_pairs": pairs, "stability_mean_spearman": mean_stab,
  "indeg_stats": indeg_stats, "dens_stats": dens_stats,
  "outcome": outcome,
  "wall_seconds": time.time()-T0,
}
with open(os.path.join(RES, "result.json"), "w") as f:
    json.dump(result, f, indent=2)

# CSV of per-item data (main build)
with open(os.path.join(RES, "per_item.csv"), "w") as f:
    f.write("item,in_degree,density_kth,denom,num_miss,miss_rate\n")
    for i in idx:
        f.write(f"{i},{ind[i]},{density[i]:.6f},{denom[i]},{num[i]},{num[i]/denom[i]:.6f}\n")

print("==== RESULT ====")
print(json.dumps({k:v for k,v in result.items() if k not in ('strata','stability_pairs')}, indent=2))
print("STRATA:")
for s in strata: print(s)
print("STABILITY PAIRS mean=", mean_stab)
print("OUTCOME:", outcome)
print(f"WALL {time.time()-T0:.1f}s")
