# PROJ-0024 — Data-systems-for-ml: connected-components near-dedup TRANSITIVELY removes non-duplicate training docs; non-transitive mitigation fixes it (EMPIRICAL PHENOMENON)
Fresh area: data-systems-for-ml (corpus dedup graph-construction step). BEST-DESIGNED survivor of the run — internalizes
ALL recent yellow lessons. EMPIRICAL-phenomenon; the STRUCTURAL CORE is L0-SETTLED (transitive closure deleting
sub-threshold docs + the non-transitive mitigation fixing it is a graph-theoretic fact the harness controls, can't
evaporate); only the real-world MAGNITUDE escalates to L1. THESIS: in the standard connected-components near-dedup
pipeline (MinHash-LSH candidate pairs -> similarity graph -> connected components -> keep one doc/component), TRANSITIVE
CHAINING removes training docs that are NOT near-duplicates of any RETAINED doc — D is deleted though its Jaccard to the
component's kept representative (and every retained doc) is far below threshold T, because D connects to the rep only via
a chain of pairwise-above-T links. The innocently-chained fraction (sim-to-rep < T) is LARGE + grows with corpus
density, NOT an LSH-false-positive artifact (persists with EXACT Jaccard edges), and the non-transitive SemDeDup-style
mitigation (delete D only if DIRECTLY above T to a retained doc) ELIMINATES it (proving the mechanism is the transitive-
closure step + supplying the honest-negative). Passes all 8 killers: NOT metric-validity (causal data-removal: WHICH
docs get deleted); NOT closed-form (innocent-removal fraction depends on real graph topology/chain-length/density, not
the LSH S-curve; union-find must run); foundational incumbent VERIFIED+addressed (Lee2021 NearDup 2107.06499 = the
seminal LLM-dedup, builds graph+connected-components+keep-one; its 200K-doc C4 component IS prima facie chaining
evidence but presented as desirable; MMDS LSH S-curve is PAIRWISE-FN not the graph-topology effect); NOT known-mechanism-
costume + STRONGEST-BASELINE used (single-linkage chaining is textbook BUT the consequence for which TRAINING docs
survive dedup is new; the L0 tests vs the STRONGEST standard mitigation SemDeDup non-transitive, NOT a strawman, and the
effect must VANISH there); NOT wrong-currency (count/fraction of unique-content docs wrongly deleted); NOT trivially-
small/assumed-shape (structurally anchored: chaining forced-possible by transitive closure on a thresholded graph;
magnitude measured; real burstiness STRENGTHENS chaining); NOT omitted-mitigation (the non-transitive mitigation IS the
comparison arm); citations VERIFIED (Lee2021=connected-components, SemDeDup 2303.09540=non-transitive within-cluster,
BigCode blog=production connected-components), NO IID assumption. DISTINCT from OCCUPIED dedup-representative-selection
(that=which doc to keep IN a true cluster; this=the cluster itself is spuriously inflated by chaining so genuinely-
distinct docs are deleted). Anti-circular: GT = is doc D a true near-dup (Jaccard>T) of the retained representative
(harness-known); pipeline reads only shingle sets, never the GT label. ORCHESTRATOR GUARD: the L0 MUST report the
REALISTIC-DENSITY operating point (not just nonzero at extreme density) so the magnitude is grounded; residual killer-#6
(real graphs may be clique-like at T~0.8 -> small innocent-removal) flagged MODERATE, isolated to L1. L1: real google-
research/deduplicate-text-datasets NearDup on a C4/RedPajama/Stack slice -> innocent-removal fraction (exact-Jaccard of
removed vs retained reps) connected-components vs SemDeDup vs complete-linkage + downstream small-LM diversity/eval-loss.
