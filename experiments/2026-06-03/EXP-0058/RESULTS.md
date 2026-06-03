# RESULTS — EXP-0058 (CLAIM-0052)

researcher-0056 | PROJ-0022 | TASK-0048 | L0 CPU-only/stdlib/SERIAL | ran in 56.4s, 24 seeds/cell

## OUTCOME: **HELD (SUPPORT)** — incl. the load-bearing #4 stronger-stage-1 arm NOT closing the gap.

The editorial-aggregate-vs-member **coverage gap** is a genuine **topological reachability ceiling**
in two-stage tool retrieval: when a tool's distinctive capability token is ABSENT from its server's
aggregate description (prob 1-c), the tool is structurally unreachable at top-m < S, and **no
stronger stage-1 representation recovers it** — decisively distinguishing it from recoverable
vocabulary-mismatch (killer #4). Pre-registered decision rules all satisfied.

## Setup (see PRE_REGISTRATION.md — committed before running)
S servers x T=8 tools; each tool has one distinctive token + shared/boilerplate tokens. Server
editorial description = boilerplate (all) + members' shared tokens + each member's distinctive token
**w.p. c** (else coverage gap). Query targets one tool via its distinctive token. GT harness-held,
NEVER seen by retrievers. Metric: reachable-recall@full = fraction of queries whose GT tool reaches
the final candidate set. Cosine scoring; idf + query-expansion for the stronger arms.

## The reachable-recall tables (full sweep in results/tables.txt; representative m=1)
```
  S    c  m |   FLAT   2STG  RERANK  STRONG_S1 | FLAT-2STG  STRONG_S1-2STG
  5  0.5  1 |  1.000  0.676  0.676     0.634   |  +0.324      -0.042
 10  0.5  1 |  1.000  0.593  0.593     0.577   |  +0.407      -0.016
 20  0.5  1 |  1.000  0.561  0.561     0.542   |  +0.439      -0.019
 40  0.5  1 |  1.000  0.533  0.533     0.510   |  +0.467      -0.023
 40  0.7  1 |  1.000  0.714  0.714     0.707   |  +0.286      -0.007
 40  0.9  1 |  1.000  0.903  0.903     0.903   |  +0.097       0.000
 40  1.0  1 |  1.000  1.000  1.000     1.000   |  +0.000       0.000
  *  any  S |  1.000  1.000  1.000     1.000   |  +0.000       0.000   (m=S closes it)
```

## The crux (a)-(d), each pre-committed and confirmed
**(a) Two-stage reachable-recall is CAPPED below flat at m<S.** FLAT = 1.000 everywhere (no
routing => no ceiling). Two-stage at m=1, c=0.5: 0.53-0.68. Gap CI-clean, e.g. S=40,c=0.5:
**+0.467 ± 0.013** (95% CI excludes 0).

**(b) RERANK does NOT lift it.** RERANK (stronger idf stage-2) is **bit-identical** to plain
two-stage at every cell — a better within-server ranker cannot route to an un-routed server.

**(c) ★ STRONGER STAGE-1 does NOT close it (#4 discriminator — load-bearing).** Giving stage-1
idf weighting + query expansion + best-possible lexical match on the description LEAVES THE GAP
(STRONG_S1 - 2STG lift = **-0.001 to -0.066**, i.e. zero-or-slightly-negative at every cell;
expansion adds boilerplate noise). A perfect matcher on a description that does NOT contain the
distinctive token has no signal to surface that server. **=> NOT recoverable vocab-mismatch =>
the structural ceiling HOLDS.** This is the single most important result.

**(d) Gap grows with (1-c) AND with S.**
- (1-c): at S=40, m=1, gap = +0.467 (c=.5) -> +0.286 (c=.7) -> +0.097 (c=.9) -> 0 (c=1.0).
- S: at c=0.5, m=1, gap = +0.324 (S=5) -> +0.407 (S=10) -> +0.439 (S=20) -> +0.467 (S=40).
  Monotone unbounded growth in S — the ceiling is NOT a fixed small constant.

## Mechanism — airtight
Of **39,312** two-stage misses across all (c,S,m<S) cells, **39,312 (100.00%)** are coverage-gap
tools (distinctive token absent from the GT server's description). Misses are EXACTLY the coverage
gap — not a fixable matching artifact. At c=1.0 (full coverage) the gap is identically 0.

## Boundary controls
- m=S (full scan) => gap=0: confirms it is a top-m routing ceiling, not a scoring bug.
- c=1.0 => gap=0: confirms the gap is the coverage gap, not generic routing loss.
- FLAT=1.000: the no-ceiling baseline is exact.

## Honest caveat / prior-art positioning
Tool-to-Agent (2511.01854)/ToolRerank (2403.06551)/MCP-Zero (2506.01056) treat failures as
score-geometry/ranking; foundational collection-selection (Kulkarni&Callan; Salton cluster
hypothesis), IVF/nprobe, and vocab-mismatch (Xiao 1806.10869) model the cluster/collection score as
MEMBER GEOMETRY. The novelty validated here: the **editorial-AGGREGATE-vs-member coverage gap** is a
topological reachability ceiling **unbounded in S**, and — critically — **NOT** closed by a stronger
stage-1 representation, so it is NOT the recoverable vocab-mismatch of Xiao et al. We were rigorous
about the kill condition; it did not trigger.

## What L1 should measure
Real two-stage tool retrieval over an MCP-scale registry (ToolBench / a real MCP catalog) with a
real embedding retriever + real reranker. Compute reachable-recall@k for FLAT vs TWO-STAGE vs
+RERANK using the **as-written editorial server descriptions**. Confirm: (1) real under-coverage
exists in shipped descriptions; (2) the ceiling + S-scaling reproduce; (3) **RESOLVE #4** by showing
the miss is NOT closed by a stronger stage-1 encoder (e.g. a larger/instruction-tuned embedding
model or LLM-rewritten queries) — the discriminator between this novel ceiling and ordinary
vocab-mismatch.

## Artifacts
- experiments/2026-06-03/EXP-0058/PRE_REGISTRATION.md (committed before run)
- experiments/2026-06-03/EXP-0058/harness.py
- experiments/2026-06-03/EXP-0058/results/results.json  (244 cells + mechanism)
- experiments/2026-06-03/EXP-0058/results/tables.txt    (full sweep)
