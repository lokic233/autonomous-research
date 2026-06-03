# PROJ-0016 — Retrieval-and-memory: graph-ANN per-item false-negative rate predicted by reverse-kNN in-degree (EMPIRICAL PHENOMENON)
Fresh area: retrieval-and-memory (graph vector-index recall STRUCTURE). EMPIRICAL-phenomenon archetype (NO
closed form — greedy-graph reachability under RNG pruning has no analytic predictor). Screened vs 3 anti-patterns
+ NOT the dead metric-validity shape (headline = a causal PREDICTOR of where misses concentrate, not 'metric
over/under-counts'). Thesis: in a greedy-traversal graph ANN index (NSW/HNSW-style, RNG-pruned out-edges), a
STABLE subset of DB vectors suffer elevated per-item false-negative rate (true top-k for some legit query yet
greedy search never returns them), and this per-item miss rate is monotonically predicted by the item's
reverse-kNN IN-DEGREE in the built graph, with signal that SURVIVES after partialling out local density (dist
to own kth true neighbor). Both confounds ACTIVE (density real via varied-density GMM; in-degree variance real
via RNG hub/orphan spread). Anti-circular: GT = exact brute-force top-k (graph-blind); tested = greedy result;
predictor = in-degree (independent of query+oracle). Honest-negative (informative): if in-degree carries ~no
residual signal after density, FALSIFIED -> 'blind spots are a density artifact not topological' (redirects
index-repair to density). PRIOR-ART: 2510.22316 (per-QUERY reachability, OOD) / 2405.17813 (AGGREGATE recall vs
order/dim) / 2412.01940 (HIGH-in-degree HUBS for speed) / Aumuller fairness (EXACT search). Delta = PER-ITEM miss
as fn of reverse-kNN in-degree, controlled vs density, framed as item topological role. Stability sub-check:
high-miss item IDENTITY correlated across insertion-order seeds (Spearman > chance).
