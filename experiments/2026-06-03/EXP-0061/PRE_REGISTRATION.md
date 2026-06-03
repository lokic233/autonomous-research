# PRE_REGISTRATION — EXP-0061 (CLAIM-0054)
researcher-0059 | PROJ-0024 | L0 (CPU-only, stdlib-only, SERIAL, <=15min)

## CLAIM
In the standard connected-components near-dedup pipeline (MinHash-LSH candidate pairs ->
similarity graph -> connected components -> keep one doc/component), TRANSITIVE CHAINING
removes training docs that are NOT near-duplicates of any RETAINED doc. Doc D is deleted
though its Jaccard to the kept representative (and every retained doc) is far below threshold
T, because D connects to the rep only via a chain of pairwise-above-T links. The
innocently-chained-removal fraction is LARGE + grows with density, is NOT an LSH false-positive
artifact (persists with EXACT Jaccard edges), and the NON-TRANSITIVE SemDeDup-style mitigation
(delete D only if DIRECTLY above T to a retained doc) ELIMINATES it.

## CORPUS / GRAPH MODEL (harness OWNS ground truth)
- N docs = shingle sets (sets of int token-ids, ~5-gram-like). Vocab V.
- Geometry the harness controls:
  (a) CHAINS: sequences doc_0..doc_L where consecutive docs share >= T*|shingles| but DRIFT
      (each step swaps out a fraction of shingles) so endpoints share < (T - delta). Vary
      chain length L + drift-per-step.
  (b) CLIQUES: clusters where all pairs Jaccard > T (genuine dup clusters).
  (c) SINGLETONS: unrelated docs.
- Vary chain prevalence + edge density.

## PIPELINE UNDER TEST (reads ONLY shingle sets, NEVER the GT label)
1. Compute pairwise similarity (EXACT Jaccard OR MinHash estimate) for candidate pairs.
2. Edge iff sim > T.
3. Connected components via union-find.
4. Keep one representative per component = lowest doc id (mirrors Lee2021 NearDup).
5. All other docs in component => REMOVED.

## MITIGATION ARMS
- NON-TRANSITIVE (SemDeDup-style): a doc D is REMOVED only if it is DIRECTLY sim > T to a doc
  that is RETAINED (no transitive closure). Implemented as greedy: process by id; keep D unless
  D has a >T edge to an already-kept doc.
- COMPLETE-LINKAGE components: only merge into a cluster if the doc is >T to ALL current cluster
  members (agglomerative complete-linkage); keep one rep per cluster.

## ANTI-CIRCULARITY
GT label = "is removed doc D a true near-dup (true Jaccard > T) of the doc the pipeline retains
as D's component representative" — and the stronger metric: max true-Jaccard of D to ANY retained
doc. Harness computes this AFTER the pipeline runs. The pipeline never sees this label.

## METRICS
(a) MECHANISM: innocent-removal fraction = of REMOVED docs, fraction whose max true-Jaccard to
    ANY retained doc < T.
(b) MITIGATION: same metric under non-transitive + complete-linkage (expect ~0).
(c) ROBUSTNESS: run with EXACT-Jaccard edges AND MinHash-LSH edges; effect must PERSIST with
    exact edges (=> not an LSH-FP artifact).
(d) REALISTIC DENSITY: sweep T in {0.7,0.8,0.9} x chain prevalence/density; REPORT innocent-removal
    AT a realistic operating point (T~0.8, realistic density), not just the max.
- Multiple seeds (>=5) + 95% CIs (normal approx on the mean across seeds).

## DECISION RULES (pre-committed)
- HELD: innocent-removal LARGE (>~0.10) at a REALISTIC operating point (T=0.8, moderate density)
  AND persists with EXACT edges (within CI of MinHash) AND drops to ~0 (<~0.02) under
  non-transitive mitigation.
- HONEST-NEGATIVE: innocent-removal ~0 at realistic density (graphs clique-like), OR the
  non-transitive mitigation does NOT change it (=> mechanism isn't transitive closure).
- WEAKEN: innocent-removal LARGE only at EXTREME density and ~0 at realistic T=0.8.

## EXECUTION
Pure Python3 stdlib, single process, no multiprocessing (SemLock blocked). RESULTS.md + CSVs.
