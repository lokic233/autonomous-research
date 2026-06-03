# COMMITTEE#1 — CLAIM-0046 (PROJ-0016, retrieval-and-memory — graph-ANN per-item false-negative law)
## EMPIRICAL-PHENOMENON study, effect=keep-exploring / MIXED. NOT metric-validity (a causal structural predictor, not 'metric over/under-counts'). NO closed form (greedy-graph reachability under RNG pruning). Screened vs 3 anti-patterns (ef/M fixed, not tuned). Anti-circular held. Vote HONESTLY.

## THE RESULT IS TWO-HALVED — judge each:
CONFIRMED HALF (strong): reverse-kNN IN-DEGREE predicts per-item false-negative rate, DENSITY-INDEPENDENT. Partial Spearman(in-degree,miss|density)=-0.152 CI[-0.203,-0.097] (unchanged from raw -0.149, excludes 0); NEGATIVE+significant in ALL 4 density quartiles; density near-orthogonal to in-degree (-0.032) so NOT the confound; density's own effect is WEAK and NEGATIVE (-0.079, opposite the naive sparse=missed intuition). Regression b_indeg=-0.0495 CI[-0.065,-0.033] sig.
NEGATIVE HALF (why MIXED): the claim's 'a STABLE SUBSET of vectors' FAILS — per-item miss-rank Spearman across 5 insertion-order seeds = mean 0.134 (BELOW the pre-registered 0.30 threshold; denom>=5 diagnostic 0.079, lower -> not rate-noise). The in-degree->miss LAW holds in every build's population, but WHICH items are blind spots RESHUFFLES with insertion order -> blind-spot membership is a property of the BUILD, not the item.

## THE LOAD-BEARING QUESTION FOR YOU: given the stable-subset half FAILED, is the surviving contribution (a density-independent in-degree->per-item-FN LAW about POPULATIONS) novel + publishable ON ITS OWN? OR does the order-dependence of blind-spot IDENTITY gut the practical payoff (you cannot 'repair' items whose blind-spot-ness reshuffles each build) -> making it a non-actionable curiosity? Distinguish: a LAW about populations (useful for understanding/aggregate repair) vs an actionable per-item diagnostic (which the instability undercuts). Judge novelty honestly vs the prior art.

## SETUP (anti-circular, all pre-registered): N=4000 d=12, 8-cluster GMM varied sigma (density ACTIVE 0.63-24.2); pure-Python NSW M=16 efc=32 Malkov RNG-prune+bidir re-prune (in-degree 1-29, no orphans = variance ACTIVE); tested ef_search=k=10 (Amendment-1 pre-committed: ef=32 was degenerate ~100% recall/zero FN variance; ef=k = minimal honest width, NOT tuned); recall 0.822; n=1303 items denom>=2; 21s. GT=exact brute-force top-10 (graph-blind); predictor=reverse-kNN in-degree (query/oracle-independent); control=dist-to-own-10th-true-neighbor. Stability=5 insertion-order seeds.

## CLAIM
claim: "In a greedy-traversal graph ANN index (NSW/HNSW-style with RNG-pruned out-edges),\
  \ a stable subset of database vectors suffer a systematically elevated per-item\
  \ false-negative rate (they are the true top-k for some legitimate query yet greedy\
  \ search never returns them), and this per-item miss rate is monotonically predicted\
  \ by the item's reverse-kNN IN-DEGREE in the built graph, with predictive signal\
  \ that SURVIVES after controlling for the item's local density (distance to its\
  \ own kth true neighbor) \u2014 i.e. low-in-degree items are retrieval blind spots\
  \ whose misses are a property of the indexed item's graph role, not of the query."
why_it_matters: "FRESH AREA (retrieval-and-memory: graph vector-index recall structure).\

## L0 RESULTS (EXP-0045)
# RESULTS — EXP-0045 / CLAIM-0046
researcher-0043 | PROJ-0016 | L0 CPU-only, stdlib-only, SERIAL | wall = 21s

## Setup (as pre-registered + Amendment 1)
- Corpus: N=4000, d=12, 8-cluster Gaussian mixture, per-cluster sigma in {0.3..5.0}
  (varied densities -> density confound ACTIVE: dens range 0.63..24.2, sd 4.82).
- Graph: pure-Python NSW build, M=16, ef_construction=32, Malkov RNG/heuristic prune,
  bidirectional edges + re-prune. In-degree range 1..29 (sd 4.40, no orphans) -> in-degree
  variance ACTIVE.
- Search (tested system): greedy best-first, ef_search = k = 10 (minimal honest width;
  see Amendment 1 — ef=32 was degenerate at 100% recall). Overall recall = 0.822.
- GT oracle: exact brute-force top-10 (graph-blind). Predictor: reverse-kNN in-degree
  (query- & oracle-independent). Control: dist to own 10th true neighbor (graph-blind).
- Analysis universe: 1303 items with denom>=2 (in true top-k of >=2 queries).

## The three correlations
| relationship                        | Spearman | 95% bootstrap CI       |
|-------------------------------------|----------|------------------------|
| (a) in-degree <-> miss (raw)        | -0.149   | [-0.200, -0.094]       |
| (b) density   <-> miss (raw)        | -0.079   | (weak, NEGATIVE)       |
| in-degree <-> density (coupling)    | -0.032   | (near-orthogonal)      |

## The crux: does in-degree survive density control? YES.
- (d) PARTIAL Spearman(in-degree, miss | density) = **-0.152**, CI [-0.203, -0.097]
  -> CI excludes 0, NEGATIVE. The in-degree effect does NOT shrink when density is
  partialled out (it is essentially unchanged from raw -0.149) because in-degree and
  density are nearly orthogonal here. Density is NOT the confound the claim feared.
- (e) Multiple regression  miss ~ z(in-degree) + z(density):
    b_in-degree = **-0.0495**, CI [-0.0645, -0.0333]  (significant, NEGATIVE)
    b_density   = -0.0371, CI [-0.0507, -0.0242]      (significant, but WEAK & also NEGATIVE)
  Both predictors independently significant; in-degree the stronger.
- (c) Within density quartiles, Spearman(in-degree, miss):
    bin0 -0.208 | bin1 -0.102 | bin2 -0.174 | bin3 -0.162  -> NEGATIVE in ALL 4 strata.

=> The topological signal (low in-degree -> higher per-item FN) is REAL and SURVIVES
   density control. NOT a density artifact. (Indeed density's own sign is NEGATIVE/weak,
   opposite the claim's assumption that sparse-region items miss more.)

## Stability sub-check: WEAK (this is what makes the outcome MIXED)
- Per-item miss-rank Spearman across 5 insertion-order seeds {7,11,13,17,19}, 10 pairs:
  mean = **0.134** (pairwise range -0.03 .. 0.36). Above chance (>0) but BELOW the
  pre-registered POSITIVE threshold of 0.30.
- Diagnostic at higher exposure (denom>=5): mean 0.079 -> even lower, so it is NOT merely
  rate-estimate noise. The IDENTITY of blind-spot items genuinely reshuffles with insertion
  order: the in-degree->miss LAW holds in every build's population, but WHICH items end up
  low-in-degree depends on insertion order, so the specific blind spots move.

## OUTCOME: **MIXED** (by pre-registered definition)
- Partial in-degree signal: significant, negative, survives density, present in all strata. PASS.
- Stability of blind-spot IDENTITY across builds: 0.134 < 0.30 threshold. FAIL.
=> The PREDICTOR (in-degree -> per-item FN, density-independent) is confirmed as a population
   law; the STABLE-SUBSET part of the claim ("a stable subset of vectors") is only weakly
   supported — blind-spot membership is build-dependent, not an immutable property of the item.

## Honest reading
- CONFIRMED: in-degree is a genuine, density-independent predictor of per-item false-negative
  rate in a greedy RNG-pruned graph index. Misses concentrate on low-in-degree items as a
  graph-role property; density does NOT explain it away (and density's own effect is weak and
  of the opposite sign to the naive "sparse = missed" intuition).
- NOT CONFIRMED: that the blind-spot set is STABLE. Insertion order reshuffles which items are
  low-in-degree, so the *identity* of blind spots is a property of the BUILD, not of the item.
- Effect sizes are modest (|rho|~0.15) but robustly significant at n=1303 with tight bootstrap CIs.

## Anti-circularity (held)
GT = exact brute-force membership (distance-only). Tested = greedy traversal (graph-dependent).
Predictor = reverse-kNN in-degree (graph structure, query- & oracle-independent). Control =
dist-to-kth-true-neighbor (distance-only). No quantity on both sides.

## What a real L1 should measure
1. REAL embeddings (SIFT1M and a sentence-embedding corpus, high intrinsic dim where hubness
   intensifies) + PRODUCTION faiss-HNSW / hnswlib (multi-layer, real ef). Test whether the
   density-independent in-degree->per-item-FN law strengthens (hubness theory predicts it
   should) — and crucially whether blind-spot IDENTITY becomes MORE stable at scale / with
   deep embeddings (our L0 weak stability may be a small-N / single-flat-layer artifact).
2. ACTIONABLE PAYOFF: cheap in-degree-based blind-spot REPAIR — add a few reverse edges TO the
   lowest-in-degree items (boost their reachability) and measure per-item recall lift at FIXED
   ef (no widening search). If per-item recall rises without raising ef, the predictor is not
   just diagnostic but a free repair lever.
3. Decompose stability: is blind-spot reshuffling driven by entry-point routing, insertion
   order, or layer assignment? (multi-seed x multi-layer ablation).

## Prior-art delta (precise, honest)
- 2510.22316 = per-QUERY reachability (query-side, OOD) — we are per-ITEM, query-independent.
- 2405.17813 = AGGREGATE recall vs insertion order / intrinsic dim — we are per-item FN, and we
  find the per-item LAW stable but per-item IDENTITY order-dependent (refines their aggregate view).
- 2412.01940 "H in HNSW = Hubs" = HIGH-in-degree hubs for search SPEED — we are the LOW-in-degree
  retrievability DEFICIT (the mirror image, an FN/recall property not a latency property).
- Aumuller SIGMOD fairness = EXACT search FNs, not graph-traversal FNs.
Novelty stands: per-item FN rate as a density-controlled function of reverse-kNN in-degree.
Our honest contribution includes the NEGATIVE half: the blind-spot SET is not stable across builds.

## PRE-REG + Amendment-1 (committed pre-run)
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

## ORCHESTRATOR NOTE: prior-art delta (researcher, honest): 2510.22316 per-QUERY reachability (query-side, OOD) vs our per-ITEM query-independent; 2405.17813 AGGREGATE recall vs order/intrinsic-dim (we refine: per-item LAW stable, per-item IDENTITY order-dependent); 2412.01940 'H=Hubs' HIGH-in-degree for SPEED vs our LOW-in-degree recall deficit (mirror image, recall not latency); Aumuller SIGMOD exact-search FNs not graph-traversal. If candidate-grade, L1 = real embeddings SIFT1M/sentence-corpus + faiss-HNSW (does the density-independent law STRENGTHEN at high intrinsic dim/hubness + does blind-spot IDENTITY STABILIZE at scale/depth — the weak stability may be a small-N single-flat-layer artifact) + actionable repair (add reverse edges to lowest-in-degree items, per-item recall lift at FIXED ef). If you judge the population-law is occupied OR the instability makes it non-actionable + not novel enough, say RED/YELLOW honestly. If the density-independent law is a genuine novel contribution even with the honest stability caveat, approve toward L1 (which can test if identity stabilizes at scale). Lightweight: if killed, converge PROJ-0016.
