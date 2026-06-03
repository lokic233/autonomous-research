#!/usr/bin/env python3
"""EXP-0061 sweep runner. SERIAL. Writes results CSVs."""
import csv, time, statistics, math
import harness as H

SEEDS = [11,22,33,44,55]
SHINGLES = 50
VOCAB = 2000
NUM_PERM = 128

def ci95(vals):
    if len(vals) < 2: return (vals[0] if vals else 0.0, 0.0)
    m = statistics.mean(vals); sd = statistics.stdev(vals)
    half = 1.96 * sd / math.sqrt(len(vals))
    return m, half

# drift calibrated so consecutive Jaccard > T, endpoints << T (drift 0.10 => consec ~0.82)
def run_config(T, n_chains, chain_len, drift, n_cliques, clique_size, n_singletons, edge_type):
    """Returns dict of per-arm innocent-removal fractions averaged over seeds."""
    arms = {"cc": [], "nontrans": [], "complete": []}
    nremoved = {"cc": [], "nontrans": [], "complete": []}
    for seed in SEEDS:
        docs = H.gen_corpus(seed, n_chains, chain_len, drift, n_cliques, clique_size,
                            n_singletons, SHINGLES, VOCAB, T)
        n = len(docs)
        if edge_type == "exact":
            edges = H.build_edges_exact(docs, T)
        else:
            mh = H.MinHasher(NUM_PERM, seed=seed+1000)
            edges = H.build_edges_minhash(docs, T, mh)
        # arm 1: connected-components keep-one
        kept, removed = H.cc_keep_one(n, edges)
        f, nr = H.innocent_removal_frac(docs, kept, removed, T)
        arms["cc"].append(f); nremoved["cc"].append(nr)
        # arm 2: non-transitive
        kept2, removed2 = H.nontransitive_keep(n, edges)
        f2, nr2 = H.innocent_removal_frac(docs, kept2, removed2, T)
        arms["nontrans"].append(f2); nremoved["nontrans"].append(nr2)
        # arm 3: complete-linkage
        kept3, removed3 = H.complete_linkage_keep(n, edges, None)
        f3, nr3 = H.innocent_removal_frac(docs, kept3, removed3, T)
        arms["complete"].append(f3); nremoved["complete"].append(nr3)
    out = {}
    for a in arms:
        m, h = ci95(arms[a])
        out[a] = (m, h, statistics.mean(nremoved[a]))
    return out

def main():
    t0 = time.time()
    rows = []
    # ---- Realistic operating point + T sweep + density sweep ----
    # density controlled by chain prevalence (#chains) + chain_len; cliques are genuine dups.
    # Realistic LLM-dedup operating point: T=0.8, moderate density.
    configs = []
    # T sweep at a fixed MODERATE (realistic) density
    for T in [0.7, 0.8, 0.9]:
        configs.append(dict(label=f"realistic_T{T}", T=T, n_chains=8, chain_len=10, drift=0.10,
                            n_cliques=5, clique_size=4, n_singletons=40))
    # density sweep at T=0.8: low -> extreme (more/longer chains)
    for nc, cl, dens in [(3,6,"low"),(8,10,"moderate"),(20,15,"high"),(35,25,"extreme")]:
        configs.append(dict(label=f"dens_{dens}_T0.8", T=0.8, n_chains=nc, chain_len=cl, drift=0.10,
                            n_cliques=5, clique_size=4, n_singletons=40))
    for edge_type in ["exact", "minhash"]:
        for cfg in configs:
            res = run_config(cfg["T"], cfg["n_chains"], cfg["chain_len"], cfg["drift"],
                             cfg["n_cliques"], cfg["clique_size"], cfg["n_singletons"], edge_type)
            for arm in ["cc", "nontrans", "complete"]:
                m, h, nr = res[arm]
                rows.append(dict(label=cfg["label"], edge_type=edge_type, arm=arm, T=cfg["T"],
                                 n_chains=cfg["n_chains"], chain_len=cfg["chain_len"],
                                 innocent_frac=round(m,4), ci95_half=round(h,4),
                                 mean_removed=round(nr,1)))
            print(f"[{time.time()-t0:5.1f}s] {edge_type:7s} {cfg['label']:18s} "
                  f"cc={res['cc'][0]:.3f}±{res['cc'][1]:.3f} "
                  f"nontrans={res['nontrans'][0]:.3f} complete={res['complete'][0]:.3f} "
                  f"(rm cc={res['cc'][2]:.0f})")
    with open("results/sweep.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nTotal {time.time()-t0:.1f}s, {len(rows)} rows -> results/sweep.csv")

if __name__ == "__main__":
    main()
