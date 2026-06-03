# PRE-REGISTRATION — EXP-0045 / CLAIM-0046
# researcher-0043 | PROJ-0016 | L0 CPU-only, stdlib-only, SERIAL, <=15min
# COMMITTED BEFORE RUNNING. No edits to design after this point.

## CLAIM (restated)
In a greedy-traversal graph ANN index (NSW/HNSW-style, RNG-pruned out-edges), a stable
subset of DB vectors have an elevated per-item false-negative rate (true top-k for some
legit query, yet greedy search never returns them). This per-item miss rate is
monotonically predicted by the item's reverse-kNN IN-DEGREE in the built graph, and that
predictive signal SURVIVES after controlling for the item's local density (distance to its
own kth true neighbor). Low-in-degree items = retrieval blind spots (a graph-role property,
not a query property).

## THE FALSIFIABLE QUESTION
Does reverse-kNN in-degree predict per-item FN rate AFTER partialling out local density?

## OUTCOME DEFINITIONS (locked)
- POSITIVE: partial correlation of in-degree vs miss (controlling density) is significant
  (95% bootstrap CI excludes 0) AND NEGATIVE (higher in-degree -> lower miss) AND the
  within-stratum in-degree->miss slope is negative & significant in >=2 of the density bins,
  AND stability Spearman of per-item miss-rank across build seeds is > 0.3 (well above chance).
- HONEST-NEGATIVE: after controlling density, in-degree partial-correlation CI includes 0
  (or flips sign) -> blind spots are a DENSITY ARTIFACT, not topological. (Informative WIN.)
- MIXED: partial signal present but unstable across seeds (stability Spearman <=0.3), OR
  significant in raw but vanishes in only some strata.

## CORPUS (vector generator) — locked
- N = 4000 DB vectors, d = 12.
- Gaussian mixture, K = 8 clusters with VARIED densities (confound active):
  cluster centers ~ Uniform[-10,10]^d (fixed seed); cluster sigma per-cluster from
  {0.3, 0.5, 0.8, 1.2, 1.8, 2.5, 3.5, 5.0} (round-robin -> dense AND sparse clusters).
  Mixture weights uniform.
- Pure stdlib: random.Random + math. Exact Euclidean (squared) distances.
- DATA seed = 12345 (fixed for main run).

## QUERY SET (held-out) — locked
- Q = 500 queries drawn from the SAME mixture (same centers/sigmas), query seed = 999.
  Queries NOT in DB. k = 10.

## GROUND-TRUTH ORACLE (graph-blind) — locked
- For each query, exact brute-force top-k over all N. GT membership = distance-only.
  Independent of any graph.

## GRAPH BUILD (NSW/HNSW-style, single-layer flat NSW) — locked
- Pure-Python incremental insertion. M = 16 out-neighbors target. ef_construction = 32.
- For each new node: greedy-search current graph from fixed entry (node 0) collecting
  ef_construction candidates; Malkov RNG/heuristic prune to <=M: keep candidate c
  (nearest-first) only if c closer to new node than to any already-kept neighbor. Add
  bidirectional edges; re-prune neighbor list if it exceeds M.
- ef/M FIXED. NO tuning. BUILD seed (main) = 7.

## TESTED SYSTEM (greedy search) — locked
- ef_search = 32, return top-k=10. Greedy best-first from entry 0, visited set + candidate
  heap (standard HNSW search-layer). FIXED ef.

## PER-ITEM FALSE-NEGATIVE RATE — locked
- item i: denom = #queries where i in exact top-k (GT). num = #those where greedy FAILED to
  return i. miss_i = num/denom. Analysis restricted to denom >= 2.

## PREDICTOR (query- AND oracle-independent) — locked
- reverse-kNN IN-DEGREE of i = # nodes j whose out-edge list (post-prune) contains i.
  Purely graph structure.

## CONTROL VARIABLE (density) — locked
- density_i = distance to i's own k-th (k=10) TRUE nearest neighbor (exact). Larger=sparser.

## THE CRUX TEST — locked
(a) raw Spearman in-degree <-> miss.
(b) Spearman density <-> miss.
(c) WITHIN density strata: 4 quartiles by density; per bin Spearman(in-degree, miss) + n.
(d) PARTIAL Spearman (in-degree, miss) controlling density, rank-residual method; bootstrap
    1000x for 95% CI.
(e) MULTIPLE REGRESSION on z-scored predictors: miss ~ b0 + b_indeg*z(indeg)+b_dens*z(dens);
    both coeffs + bootstrap 95% CIs.

## STABILITY SUB-CHECK — locked
- Rebuild with 5 insertion seeds {7,11,13,17,19} (data/query/oracle FIXED). Pairwise Spearman
  of per-item miss across C(5,2)=10 pairs; report mean. Want >0, ideally >0.3.

## ANTI-CIRCULARITY (verified)
- GT exact brute-force (graph-blind). Tested = greedy traversal (graph-dependent).
- Predictor = reverse-kNN in-degree (query/oracle independent). Control = dist-to-kth-true-nbr.
- No quantity on both sides.

## SIGNIFICANCE
- Bootstrap 1000 resamples over items; 95% percentile CIs. Significant = CI excludes 0.
