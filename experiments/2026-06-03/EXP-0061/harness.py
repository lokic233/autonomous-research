#!/usr/bin/env python3
"""EXP-0061 L0: transitive-chaining innocent-removal in connected-components near-dedup.
Pure stdlib, serial. Harness owns GT geometry. Pipeline reads ONLY shingle sets."""
import random, csv, math, statistics, time
from itertools import combinations

# ---------- similarity ----------
def jaccard(a, b):
    if not a and not b: return 1.0
    inter = len(a & b); uni = len(a | b)
    return inter / uni if uni else 0.0

# ---------- MinHash ----------
class MinHasher:
    def __init__(self, num_perm, seed):
        rnd = random.Random(seed)
        self.P = (1 << 61) - 1
        self.coeffs = [(rnd.randrange(1, self.P), rnd.randrange(0, self.P)) for _ in range(num_perm)]
        self.num_perm = num_perm
    def sig(self, shingles):
        P = self.P
        s = [float('inf')] * self.num_perm
        for x in shingles:
            for i, (a, b) in enumerate(self.coeffs):
                h = (a * x + b) % P
                if h < s[i]: s[i] = h
        return s
def minhash_est(s1, s2):
    eq = sum(1 for a, b in zip(s1, s2) if a == b)
    return eq / len(s1)

# ---------- corpus generation (GT geometry) ----------
def gen_corpus(seed, n_chains, chain_len, drift, n_cliques, clique_size,
               n_singletons, shingles_per_doc, vocab, T):
    """Returns list of (doc_id -> shingle set). Chains drift so endpoints diverge.
    drift = fraction of shingles swapped per chain step."""
    rnd = random.Random(seed)
    docs = []
    def fresh(): return set(rnd.randrange(vocab) for _ in range(shingles_per_doc))
    # CHAINS
    for _ in range(n_chains):
        base = fresh()
        docs.append(set(base))
        cur = set(base)
        n_swap = max(1, int(drift * shingles_per_doc))
        for _ in range(chain_len - 1):
            cur = set(cur)
            cur_list = list(cur)
            rnd.shuffle(cur_list)
            for k in range(min(n_swap, len(cur_list))):
                cur.discard(cur_list[k])
            while len(cur) < shingles_per_doc:
                cur.add(rnd.randrange(vocab))
            docs.append(set(cur))
    # CLIQUES (tight dup clusters: small perturbation of a base, all pairs > T)
    for _ in range(n_cliques):
        base = fresh()
        for _ in range(clique_size):
            d = set(base)
            # perturb tiny amount so all pairs stay > T
            n_swap = max(0, int(0.03 * shingles_per_doc))
            dl = list(d); rnd.shuffle(dl)
            for k in range(min(n_swap, len(dl))): d.discard(dl[k])
            while len(d) < shingles_per_doc: d.add(rnd.randrange(vocab))
            docs.append(d)
    # SINGLETONS
    for _ in range(n_singletons):
        docs.append(fresh())
    return docs

# ---------- pipeline: build edges ----------
def build_edges_exact(docs, T):
    n = len(docs); edges = []
    for i, j in combinations(range(n), 2):
        if jaccard(docs[i], docs[j]) > T:
            edges.append((i, j))
    return edges

def build_edges_minhash(docs, T, mh):
    sigs = [mh.sig(d) for d in docs]
    n = len(docs); edges = []
    for i, j in combinations(range(n), 2):
        if minhash_est(sigs[i], sigs[j]) > T:
            edges.append((i, j))
    return edges

# ---------- union-find connected components ----------
def connected_components(n, edges):
    par = list(range(n))
    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for i, j in edges:
        ri, rj = find(i), find(j)
        if ri != rj: par[ri] = rj
    comps = {}
    for x in range(n):
        comps.setdefault(find(x), []).append(x)
    return list(comps.values())

# keep one rep per component (lowest id) -> removed set
def cc_keep_one(n, edges):
    comps = connected_components(n, edges)
    removed, kept = set(), set()
    for c in comps:
        c_sorted = sorted(c)
        kept.add(c_sorted[0])
        for x in c_sorted[1:]: removed.add(x)
    return kept, removed

# ---------- non-transitive (SemDeDup-style) ----------
# A doc removed only if DIRECTLY >T to an already-KEPT doc. Greedy by id.
def nontransitive_keep(n, edges):
    adj = {i: set() for i in range(n)}
    for i, j in edges:
        adj[i].add(j); adj[j].add(i)
    kept, removed = set(), set()
    for x in range(n):
        if any(nb in kept for nb in adj[x]):
            removed.add(x)
        else:
            kept.add(x)
    return kept, removed

# ---------- complete-linkage agglomerative ----------
# merge doc into a cluster only if >T to ALL current members; keep one rep (lowest id)
def complete_linkage_keep(n, edges, simfn):
    adj = {i: set() for i in range(n)}
    for i, j in edges:
        adj[i].add(j); adj[j].add(i)
    clusters = []  # list of member-lists
    for x in range(n):
        placed = False
        for cl in clusters:
            if all(x in adj[m] for m in cl):  # >T to all members
                cl.append(x); placed = True; break
        if not placed:
            clusters.append([x])
    kept, removed = set(), set()
    for cl in clusters:
        cl_sorted = sorted(cl)
        kept.add(cl_sorted[0])
        for m in cl_sorted[1:]: removed.add(m)
    return kept, removed

# ---------- innocent-removal metric ----------
def innocent_removal_frac(docs, kept, removed, T):
    """Of removed docs, fraction whose max TRUE-Jaccard to ANY retained doc < T."""
    if not removed: return 0.0, 0
    kept_list = list(kept)
    innocent = 0
    for r in removed:
        mx = 0.0
        for k in kept_list:
            jv = jaccard(docs[r], docs[k])
            if jv > mx: mx = jv
            if mx >= T: break
        if mx < T: innocent += 1
    return innocent / len(removed), len(removed)
