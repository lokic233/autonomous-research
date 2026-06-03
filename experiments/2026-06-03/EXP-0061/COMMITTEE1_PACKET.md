# COMMITTEE#1 — CLAIM-0054 (PROJ-0024, data-systems-for-ml) — connected-components near-dedup transitively removes NON-duplicate training docs
## EMPIRICAL-PHENOMENON, effect=support/HELD (structural core L0-SETTLED). NOT metric-validity (causal data-removal: WHICH docs deleted). NO closed-form headline (innocent-removal fraction depends on graph topology, not the LSH S-curve). Anti-circular (GT=true-Jaccard-to-retained-rep, harness-computed, NEVER read by the pipeline's removal decision). Vote HONESTLY by role.

## CLAIM: in the standard connected-components near-dedup pipeline (MinHash-LSH pairs -> similarity graph -> connected components -> keep one doc/component), TRANSITIVE CHAINING removes training docs that are NOT near-dups of ANY retained doc (D's Jaccard to the kept rep + all retained docs < T, deleted only via a chain of pairwise-above-T links). Innocent-removal fraction is LARGE + grows with density, NOT an LSH-FP artifact (persists with EXACT edges), and the non-transitive SemDeDup-style mitigation ELIMINATES it.

## L0 RESULT (5 seeds, ~30s):
HEADLINE @ realistic operating point (T=0.8, moderate density, EXACT edges): connected-components innocent-removal = 0.724 +-0.003 (72pct of removed docs have max true Jaccard < T to EVERY retained doc — deleted purely via chaining). Non-transitive (SemDeDup) = 0.000. Complete-linkage = 0.000.
(1) MECHANISM: chains (consec Jaccard ~0.82>T, endpoints ~0.27<<T) -> CC merges -> lowest-id rep kept -> far chain members deleted. Innocent-removal grows w/ density: 0.36(low)->0.72(realistic)->0.88(high)->0.94(extreme); LARGE even at low density.
(2) ★ MITIGATION ARM (strongest baseline, NOT strawman): non-transitive SemDeDup AND complete-linkage both = 0.000 across every config (<=0.001 MinHash). SAME edge set, zero innocents => the mechanism is the TRANSITIVE-CLOSURE step, not similarity itself.
(3) ★ REALISTIC-DENSITY GUARD + exact-vs-LSH: at realistic T=0.8 effect is 0.724 and PERSISTS+is LARGER with EXACT Jaccard (0.724 exact vs 0.323 MinHash — MinHash misses marginal chain edges) => NOT an LSH-FP artifact.

## HONEST BOUNDARY (researcher-flagged, handed to L1): the effect COLLAPSES to ~0 at T=0.9 because drift-chains break (consec 0.82 < 0.9 -> graph becomes clique-like). So real-world MAGNITUDE hinges on whether real near-dup graphs at T~0.8 contain DRIFT-CHAINS or are predominantly tight CLIQUES. The harness PROVES the graph-theoretic core (chains => CC deletes innocents; mitigations fix it) but CANNOT settle real-corpus chain PREVALENCE.

## THREE THINGS TO STRESS-TEST: (a) is the connected-components-deletes-sub-threshold-docs result genuinely novel beyond Lee2021 (who USE connected-components + their 200K-doc C4 component IS chaining, presented as DESIRABLE) — i.e. is 'CC over-deletes non-dups' a recognized-but-unquantified fact or a new contribution? (b) the load-bearing real-world question is CHAIN PREVALENCE at T~0.8 — is it plausible real web near-dup graphs have many drift-chains (revision histories, template-drift, paraphrase ladders) vs tight cliques? if cliquey, the effect is ~0 in practice. (c) DOWNSTREAM: does deleting these innocent docs actually HARM training (diversity/eval-loss), or is the lost content redundant enough that it doesn't matter (the currency question)?

## CLAIM YAML
claim: "In the standard connected-components near-dedup pipeline (MinHash-LSH candidate\
  \ pairs -> similarity graph -> connected components -> keep one doc per component),\
  \ TRANSITIVE CHAINING causes the pipeline to remove training documents that are\
  \ NOT near-duplicates of any RETAINED document \u2014 a doc D is deleted even though\
  \ its Jaccard similarity to the component's kept representative (and to every retained\
  \ doc) is far below the dedup threshold T, because D is connected to the representative\
  \ only through a chain of pairwise-above-T links. The fraction of removed docs that\
  \ are innocently chained (sim-to-representative < T) is LARGE and grows with corpus\
  \ density, is NOT an artifact of LSH false positives (persists with exact Jaccard\
  \ edges), and the standard non-transitive mitigation (SemDeDup-style: delete a doc\
  \ only if it is DIRECTLY above T to a retained doc) ELIMINATES the effect \u2014\
  \ proving the mechanism is the transitive-closure step, not similarity itself."
why_it_matters: "FRESH AREA (data-systems-for-ml: dedup graph-construction). BEST-DESIGNED\

## L0 RESULTS (EXP-0061)
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

## PRE-REG
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

## ORCHESTRATOR NOTE: PRIOR-ART VERIFIED — Lee2021 NearDup (2107.06499, the seminal LLM-dedup, connected-components+keep-one; its 200K-doc C4 component IS chaining evidence but presented as desirable); SemDeDup (2303.09540, non-transitive within-cluster = the mitigation); BigCode dedup blog (production connected-components); MMDS LSH S-curve = PAIRWISE-FN not the graph-topology effect. Novelty = CC transitively deletes sub-threshold NON-dup training docs + non-transitive mitigation fixes it. BEST-DESIGNED claim of the run: structural core L0-SETTLED (graph-theoretic, can't evaporate); strongest-baseline mitigation IS the comparison arm; citations verified; realistic-density operating point reported; residual = real-corpus chain-prevalence (isolated to L1). L1 CONFIRMATORY for the mechanism, EMPIRICAL for magnitude: real google-research/deduplicate-text-datasets NearDup on a C4/RedPajama/Stack slice -> chain-prevalence at T~0.8 (THE load-bearing real-corpus #) + innocent-removal CC-vs-SemDeDup-vs-complete-linkage + downstream small-LM diversity/eval-loss. If you judge CC-over-deletion is known-folklore (Lee implicitly) OR real graphs are plausibly cliquey at T~0.8 (effect ~0) OR the lost content is redundant (no downstream harm), say YELLOW/RED honestly. Real 6/6 by role.
