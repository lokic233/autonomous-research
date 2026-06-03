# RESULTS — EXP-0061 (CLAIM-0054) — researcher-0059
L0 | CPU-only | stdlib-only | SERIAL | wall ~30s | 5 seeds + 95% CI | honest pipeline

## VERDICT: HELD (structural core), with explicit realistic-density caveat handed to L1.

The transitive-closure (connected-components keep-one) step deletes a LARGE fraction of training
docs that are NOT near-duplicates of any retained doc, and the non-transitive (SemDeDup-style) +
complete-linkage mitigations ELIMINATE it. The effect PERSISTS with EXACT-Jaccard edges (it is
not an LSH false-positive artifact). The one honest caveat the orchestrator demanded — realistic
density — is satisfied IF drift-chains exist at the operating T; whether such chains are prevalent
in real corpora at T~0.8 is the load-bearing empirical question for L1.

## HEADLINE — REALISTIC OPERATING POINT (T=0.8, moderate density, EXACT edges)
| arm                         | innocent-removal fraction |
|-----------------------------|---------------------------|
| connected-components (CC)   | **0.724 ± 0.003**         |
| non-transitive (SemDeDup)   | **0.000**                 |
| complete-linkage            | **0.000**                 |

72% of docs removed by the standard CC pipeline have max TRUE Jaccard < T to EVERY retained doc —
they are deleted purely via transitive chaining. Both mitigations drive this to exactly 0.

## (a) MECHANISM — innocent-removal grows with density (T=0.8, EXACT edges, arm=CC)
| density   | n_chains×len | innocent-removal | mean removed |
|-----------|--------------|------------------|--------------|
| low       | 3×6          | 0.361 ± 0.017    | 28           |
| moderate  | 8×10 (realistic) | **0.724 ± 0.003** | 83       |
| high      | 20×15        | 0.878 ± 0.000    | 286          |
| extreme   | 35×25        | 0.940 ± 0.000    | 839          |
Large even at LOW density (0.36) — not only an extreme-density artifact.

## (b) ★ MITIGATION ARM (the strongest-baseline test) — DROPS TO ~0
Across EVERY config, non-transitive (SemDeDup) and complete-linkage give innocent-removal = 0.000
(exact edges; ≤0.001 with MinHash). This PROVES the effect is the transitive-closure step, not
similarity itself: deleting D only when it is DIRECTLY >T to a RETAINED doc removes zero innocents.

## (c) ★ ROBUSTNESS — persists with EXACT edges (NOT an LSH-FP artifact)
| operating point      | EXACT (CC) | MinHash (CC) |
|----------------------|-----------|--------------|
| realistic T=0.8      | 0.724     | 0.323        |
| high density T=0.8   | 0.878     | 0.472        |
| extreme density T=0.8| 0.940     | 0.471        |
Exact edges give a LARGER effect than MinHash (k=128). MinHash *misses* some true-but-marginal
chain edges (consec Jaccard ~0.82 near T), breaking some chains and REDUCING innocent-removal.
=> the phenomenon is graph topology, not LSH false positives. Confirmed.

## (d) ★ REALISTIC-DENSITY / T SWEEP — the honest boundary
T sweep (moderate density, EXACT, arm=CC):
| T   | innocent-removal | removed | note |
|-----|------------------|---------|------|
| 0.7 | 0.731            | 87      | chains form (consec ~0.82 > 0.7) |
| 0.8 | 0.724            | 83      | **realistic LLM-dedup point — chains form (0.82 > 0.8)** |
| 0.9 | 0.000            | 8       | chains BREAK (consec 0.82 < 0.9) → graph clique-like → ~0 |

Drift robustness (T=0.8, EXACT): innocent-removal = 0.70–0.74 across drift 0.06–0.10
(consec Jaccard 0.82–0.89), and exactly 0.000 at drift 0.12 (consec 0.786 < T → no chain edges).

THE HONEST CAVEAT: the effect is large at the realistic T=0.8 *whenever drift-chains with
consecutive Jaccard > T actually exist*. At T=0.9 those chains break and the graph is clique-like
(innocent-removal → 0). So the magnitude in a REAL corpus hinges on whether near-dup graphs at
T~0.8 contain such drift-chains or are predominantly tight cliques. This harness PROVES the
structural/graph-theoretic core (chains ⇒ CC deletes innocents; mitigations fix it) but cannot
settle real-corpus chain PREVALENCE — that is the L1 question.

## ANTI-CIRCULARITY (honored)
- Harness owns GT geometry (chains/cliques/singletons via shingle drift).
- Pipeline reads ONLY shingle sets → thresholded similarity graph → union-find → keep lowest-id rep.
- GT label (max true-Jaccard of a removed doc to ANY retained doc) computed AFTER the pipeline runs;
  the removal decision never uses it.

## KILLER SCREEN
- LSH-FP artifact? NO — persists & is larger with EXACT Jaccard edges.
- Strawman baseline? NO — tested SemDeDup non-transitive AND complete-linkage (both → 0).
- Similarity-itself (not chaining)? NO — non-transitive rule keeps identical edge set yet → 0 innocents.
- Extreme-density-only? NO — 0.36 at low density, 0.72 at moderate/realistic.
- Drift artifact? NO — stable across drift 0.06–0.10; collapses only when consec drops below T (=no chain).

## FILES
- PRE_REGISTRATION.md (committed before running)
- harness.py (corpus/GT + pipeline + 3 arms + metric)
- run.py (sweep, 5 seeds)
- results/sweep.csv (42 rows: edge_type × config × arm)

## WHAT L1 SHOULD MEASURE
Run real google-research/deduplicate-text-datasets NearDup (5-grams, Lee2021 b/r bands) on a
C4 / RedPajama / Stack slice. (1) MEASURE CHAIN PREVALENCE at T~0.8 in the real near-dup graph:
fraction of connected components that are NON-clique (have a >T-thresholded edge between two docs
whose true Jaccard pair is <T via a path) — this is the real-corpus version of the load-bearing
question. (2) innocent-removal fraction: connected-components vs SemDeDup vs complete-linkage.
(3) downstream small-LM diversity / eval-loss on equal-token-budget corpora deduped by CC vs
non-transitive. PRIOR ART (verified): Lee2021 NearDup (2107.06499) connected-components keep-one
(its 200K-doc C4 component IS chaining evidence, presented as desirable); SemDeDup (2303.09540) =
non-transitive within-cluster pruning = the mitigation; BigCode dedup blog = production CC;
MMDS LSH S-curve = PAIRWISE-FN, not this graph-topology effect. NOVELTY = CC transitively deletes
sub-threshold (non-dup) training docs + the non-transitive mitigation fixes it.
