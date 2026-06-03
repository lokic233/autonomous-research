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
