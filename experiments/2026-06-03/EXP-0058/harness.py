#!/usr/bin/env python3
"""EXP-0058: editorial-aggregate-vs-member coverage gap as a topological reachability
ceiling in two-stage agentic tool retrieval. CPU-only, stdlib-only, SERIAL.

Honest pipeline. GT held by harness, NEVER seen by retrievers. Retrievers read only
observable scores. The #4-boundary STRONGER-STAGE-1 arm is the load-bearing test."""
import math, random, statistics, json, sys, time

# ---------------- registry model ----------------
def build_registry(S, T, rng, c, n_shared_per_tool=4, n_boiler=6, shared_pool=40):
    """Returns servers[list of dict], tools[list], queries[list], gt[list].
    Each tool has one distinctive token 'd{idx}'. Server editorial description includes
    each member's distinctive token w.p. c (else COVERAGE GAP) + all boilerplate + all
    shared tokens of members. Boilerplate is shared across ALL servers (editorial flavor)."""
    boiler = [f"b{i}" for i in range(n_boiler)]          # global boilerplate, every server has all
    shared = [f"s{i}" for i in range(shared_pool)]       # shared capability tokens
    tools = []   # each: dict(idx, server, dist, shared_set, schema_set)
    servers = [] # each: dict(idx, member_idxs, desc_set)
    tidx = 0
    for sv in range(S):
        members = []
        desc = set(boiler)  # editorial aggregate always carries boilerplate
        for _ in range(T):
            dist = f"d{tidx}"
            sh = set(rng.sample(shared, n_shared_per_tool))
            schema = {dist} | sh
            tools.append(dict(idx=tidx, server=sv, dist=dist, shared=sh, schema=schema))
            members.append(tidx)
            desc |= sh                          # shared tokens roll up to description
            if rng.random() < c:                # COVERAGE: include distinctive w.p. c
                desc.add(dist)
            # else: COVERAGE GAP — distinctive token absent from server description
            tidx += 1
        servers.append(dict(idx=sv, members=members, desc=desc))
    # queries: one per tool, query = {dist} (+ maybe 1 shared token of that tool)
    queries, gt = [], []
    for t in tools:
        q = {t["dist"]}
        if rng.random() < 0.5 and t["shared"]:
            q |= set(rng.sample(sorted(t["shared"]), 1))
        queries.append(q); gt.append(t["idx"])
    return servers, tools, queries, gt, boiler, shared

# ---------------- scoring ----------------
def cos(qset, dset, idf=None):
    """TF cosine over token sets. If idf given, weight by idf (stronger representation)."""
    if not qset or not dset: return 0.0
    inter = qset & dset
    if not inter: return 0.0
    if idf is None:
        num = len(inter); 
        return num / (math.sqrt(len(qset)) * math.sqrt(len(dset)))
    num = sum(idf.get(tok, 1.0)**2 for tok in inter)
    qn = math.sqrt(sum(idf.get(tok,1.0)**2 for tok in qset))
    dn = math.sqrt(sum(idf.get(tok,1.0)**2 for tok in dset))
    if qn==0 or dn==0: return 0.0
    return num/(qn*dn)

def build_idf(docs):
    """idf over a collection of token-sets."""
    N = len(docs); df = {}
    for d in docs:
        for tok in d: df[tok] = df.get(tok,0)+1
    return {tok: math.log((N+1)/(c+0.5)) for tok,c in df.items()}

# ---------------- conditions ----------------
def flat(query, tools, k):
    scored = sorted(((cos(query, t["schema"]), t["idx"]) for t in tools), reverse=True)
    return [idx for _,idx in scored[:k]]

def stage1_rank(query, servers, idf=None):
    return sorted(((cos(query, sv["desc"], idf), sv["idx"]) for sv in servers), reverse=True)

def two_stage(query, servers, tools, m, k, s1_idf=None, s2_idf=None, expand=None):
    q1 = query | (expand(query) if expand else set())
    s1 = stage1_rank(q1, servers, s1_idf)
    routed = [idx for _,idx in s1[:m]]
    cand = []
    rs = set(routed)
    for t in tools:
        if t["server"] in rs:
            cand.append((cos(query, t["schema"], s2_idf), t["idx"]))
    cand.sort(reverse=True)
    return [idx for _,idx in cand[:k]]

def reachable_recall(retrieved_fn, queries, gt, k):
    hit = 0
    for q, g in zip(queries, gt):
        if g in retrieved_fn(q)[:k]:
            hit += 1
    return hit/len(queries)

# ---------------- experiment ----------------
def ci95(vals):
    if len(vals)<2: return (statistics.mean(vals),0.0)
    m = statistics.mean(vals); sd = statistics.stdev(vals)
    return m, 1.96*sd/math.sqrt(len(vals))

def run():
    t0=time.time()
    T = 8
    Ss = [5,10,20,40]
    cs = [0.5,0.7,0.9,1.0]
    seeds = list(range(24))
    K_full = T            # full within-server set (isolates routing ceiling) — k>=T per server
    results = {}          # (cond, c, S, m) -> list over seeds
    misses_coverage_gap = []  # mechanism: of two-stage misses, fraction that are coverage-gap

    for S in Ss:
        for c in cs:
            for seed in seeds:
                rng = random.Random(1000*S + 100*int(c*10) + seed)
                servers, tools, queries, gt, boiler, shared = build_registry(S,T,rng,c)
                # idf collections
                server_docs = [sv["desc"] for sv in servers]
                tool_docs = [t["schema"] for t in tools]
                s1_idf = build_idf(server_docs)        # stronger stage-1: idf over server descs
                s2_idf = build_idf(tool_docs)          # stronger stage-2: idf over tool schemas
                # query expansion for stronger stage-1: add shared tokens co-occurring (oracle-ish:
                # expand query distinctive into ALL shared tokens of ANY tool sharing it — but
                # since query already targets one tool, expand to that tool's shareds via schema.
                # We give it the strongest realistic boost: expand to neighbors in shared space.
                def make_expand():
                    # map shared token -> other shared tokens seen together (cooccurrence)
                    cooc = {}
                    for t in tools:
                        toks = list(t["shared"])
                        for a in toks:
                            cooc.setdefault(a,set()).update(toks)
                    def exp(q):
                        add=set()
                        for tok in q:
                            if tok in cooc: add |= cooc[tok]
                        return add
                    return exp
                expand = make_expand()

                # GT-coverage-gap map: is dist token of GT tool absent from its server desc?
                gap = {}
                for t in tools:
                    gap[t["idx"]] = (t["dist"] not in servers[t["server"]]["desc"])

                ms = sorted(set([1,2,3,5,S]))
                # FLAT (baseline) — m-independent
                fr = reachable_recall(lambda q: flat(q,tools,K_full*S), queries, gt, K_full*S)
                results.setdefault(("flat",c,S,0),[]).append(fr)

                for m in ms:
                    # (ii) two-stage TF
                    fn2 = lambda q,m=m: two_stage(q,servers,tools,m,K_full*m)
                    r2 = reachable_recall(fn2, queries, gt, K_full*m)
                    results.setdefault(("twostage",c,S,m),[]).append(r2)
                    # (iii) two-stage + RERANK (stronger stage-2 idf)
                    fn3 = lambda q,m=m: two_stage(q,servers,tools,m,K_full*m,s2_idf=s2_idf)
                    r3 = reachable_recall(fn3, queries, gt, K_full*m)
                    results.setdefault(("rerank",c,S,m),[]).append(r3)
                    # (iv) two-stage + STRONGER STAGE-1 (idf + query expansion) — #4 boundary
                    fn4 = lambda q,m=m: two_stage(q,servers,tools,m,K_full*m,
                                                  s1_idf=s1_idf,s2_idf=s2_idf,expand=expand)
                    r4 = reachable_recall(fn4, queries, gt, K_full*m)
                    results.setdefault(("strong_s1",c,S,m),[]).append(r4)

                    # mechanism: for two-stage misses at m, fraction that are coverage-gap tools
                    if m < S:
                        for q,g in zip(queries,gt):
                            got = fn2(q)
                            if g not in got:
                                misses_coverage_gap.append((c,S,m,gap[g]))
    elapsed = time.time()-t0
    return results, misses_coverage_gap, dict(T=T,Ss=Ss,cs=cs,nseeds=len(seeds),elapsed=elapsed)

if __name__=="__main__":
    results, misses, meta = run()
    out = {"meta":meta, "cells":[]}
    for key, vals in results.items():
        cond,c,S,m = key
        m_,ci = ci95(vals)
        out["cells"].append(dict(cond=cond,c=c,S=S,m=m,mean=m_,ci=ci,n=len(vals)))
    # mechanism summary
    from collections import defaultdict
    mg = defaultdict(lambda:[0,0])  # (c,S,m) -> [gap_misses, total_misses]
    for c,S,m,isgap in misses:
        mg[(c,S,m)][1]+=1
        if isgap: mg[(c,S,m)][0]+=1
    out["mechanism"]=[dict(c=c,S=S,m=m,gap_misses=g,total_misses=tot,
                           frac_gap=(g/tot if tot else None))
                      for (c,S,m),(g,tot) in sorted(mg.items())]
    with open(sys.argv[1] if len(sys.argv)>1 else "results.json","w") as f:
        json.dump(out,f,indent=2)
    print(f"DONE in {meta['elapsed']:.1f}s, {len(out['cells'])} cells, {len(misses)} miss-records")
