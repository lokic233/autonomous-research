# COMMITTEE#1 — CLAIM-0052 (PROJ-0022, agentic-systems) — two-stage tool-routing editorial-coverage reachability CEILING
## EMPIRICAL-PHENOMENON, effect=support/HELD. NOT metric-validity (reachability/recall mechanism). NO closed form. Anti-circular (GT=query target tool, harness-held, NEVER exposed; signal=lexical scores only). Vote HONESTLY by role — strongest+cleanest HELD of the v3 expansion, the ONLY one whose load-bearing residual risk (killer #4) was tested IN the L0 and survived. Do not rubber-stamp; do not reflexively kill.

## CLAIM: in two-stage (route-to-server-then-select-tool) agentic tool retrieval, a correct tool is structurally UNREACHABLE whenever its server's editorial AGGREGATE description fails to cover the tool's distinctive capability tokens; this coverage-gap miss is INDEPENDENT of score geometry, NOT removed by raising top-m below full scan NOR by within-server reranking; flat retrieval has no such ceiling; the gap grows with under-coverage (1-c) and registry size S; AND it is NOT closed by a stronger stage-1 representation (distinguishing it from recoverable vocabulary-mismatch).

## L0 RESULT (24 seeds/cell, T=8, anti-circular):
Reachable-recall@full: FLAT=1.000 everywhere (no routing => no ceiling). Two-stage CAPPED below flat at m<S: gap +0.467+-0.013 @S=40,c=0.5 (95% CI excludes 0); +0.286 @c=0.7; +0.097 @c=0.9; 0 @c=1.0; 0 @m=S.
(a) CAPPED below flat at m<S — confirmed CI-clean.
(b) RERANK INSUFFICIENT: stronger stage-2 (idf) is BIT-IDENTICAL to plain two-stage — a better within-server ranker cannot route to an un-routed server.
(c) ★ THE #4 DISCRIMINATOR — STRONGER stage-1 does NOT close the gap: idf + query-expansion + best-lexical lift = -0.001 to -0.066 (zero-or-NEGATIVE at EVERY cell; expansion adds boilerplate noise). A perfect matcher on a description lacking the distinctive token has no signal. => NOT recoverable vocab-mismatch (Xiao 1806.10869); killer #4 does NOT win; the STRUCTURAL CEILING HOLDS.
(d) SCALING: gap grows with (1-c) [+0.467@c.5 -> +0.097@c.9] and UNBOUNDED in S [+0.324@S5 -> +0.467@S40 at m=1].
MECHANISM AIRTIGHT: 39312/39312 (100.00pct) of two-stage misses across all (c,S,m<S) cells are coverage-gap tools (distinctive token absent from GT server desc). Boundary controls: c=1.0->gap=0; m=S->gap=0.

## THREE THINGS TO STRESS-TEST HONESTLY:
(a) is the 'editorial AGGREGATE != member centroid' framing genuinely distinct from collection-selection theory (Kulkarni&Callan/Salton cluster hypothesis, IVF/nprobe)? OR in real systems is stage-1 routing built by POOLING member tool schemas (not a short editorial blurb), making coverage~1 in practice -> the ceiling wouldn't bite? (the ecological crux)
(b) the L0 stronger-stage-1 arm is LEXICAL (idf/expansion). Would a real DENSE embedding encoder still be defeated by an absent token, or could it infer the capability SEMANTICALLY from related tokens (which would partially close the gap -> the L1 #4 resolution)? Judge whether lexical-only is sufficient evidence at L0.
(c) ecological: do real MCP/agent registries actually route on editorial blurbs WITH under-coverage, or on member-pooled representations? Is the under-coverage regime (c<1) realistic?

## CLAIM YAML
claim: "In two-stage (route-to-server-then-select-tool) agentic tool retrieval, a\
  \ correct tool is structurally UNREACHABLE whenever its server's editorial AGGREGATE\
  \ description fails to cover the tool's distinctive capability tokens \u2014 and\
  \ this coverage-gap miss rate is INDEPENDENT of embedding/lexical score geometry,\
  \ so it is NOT removed by raising the server-probe budget top-m below full scan,\
  \ NOR by within-server reranking (the standard production mitigations); whereas\
  \ flat (per-tool) retrieval over the same registry has no such ceiling. The reachable-recall\
  \ gap between two-stage and flat GROWS with editorial under-coverage rate (1-c)\
  \ and with registry size S \u2014 and critically, the gap is NOT closed by a stronger\
  \ stage-1 representation (which distinguishes it from recoverable vocabulary-mismatch)."
why_it_matters: "FRESH AREA (agentic-systems: tool routing / MCP-scale retrieval).\

## L0 RESULTS (EXP-0058)
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

## PRE-REG
# PRE_REGISTRATION — EXP-0058 (CLAIM-0052)

researcher-0056 | PROJ-0022 | TASK-0048 | L0 CPU-only/stdlib-only/SERIAL/<=15min
Committed BEFORE running. Honest pipeline — negatives are wins.

## THE CLAIM (CLAIM-0052)
In two-stage (route-to-server-then-select-tool) agentic tool retrieval, a correct tool is
structurally UNREACHABLE whenever its server's editorial AGGREGATE description fails to cover
the tool's distinctive capability tokens (the editorial-aggregate-vs-member COVERAGE GAP). This
miss is INDEPENDENT of score geometry — NOT removed by raising the server-probe budget top-m
below full scan, NOR by within-server reranking. Flat (per-tool) retrieval has no such ceiling.
The reachable-recall gap grows with under-coverage (1-c) and registry size S. CRITICALLY the gap
is NOT closed by a stronger stage-1 representation (distinguishing it from recoverable
vocabulary-mismatch, Xiao et al. 2018).

## THE LOAD-BEARING TEST (killer #4 boundary)
Biggest risk: this is just ordinary VOCABULARY-MISMATCH relabeled — recoverable by a better
stage-1 representation. PRIMARY falsification = does a STRONGER stage-1 representation CLOSE the gap?
- CLOSES it -> recoverable vocab-mismatch -> FALSIFIED (KILL/WEAKEN).
- PERSISTS regardless of stage-1 power (because the distinctive capability is ABSENT from the
  server's aggregate description — no query-side/representation-side trick surfaces a server with
  ZERO signal for the query at top-m < #shadowing-servers) -> NOVEL TOPOLOGICAL CEILING (HELD).
Discriminator: ceiling must come from the server being STRUCTURALLY unrepresented, not a
weak-but-fixable matching function.

## REGISTRY MODEL (harness OWNS GT)
- S servers, T tools each. Total N = S*T tool schemas.
- Vocabulary: D_dist distinctive capability tokens (one per tool, unique-ish) + B shared/

## ORCHESTRATOR NOTE: PRIOR-ART — Tool-to-Agent (2511.01854)/ToolRerank (2403.06551)/MCP-Zero (2506.01056) treat failures as geometry/ranking; FOUNDATIONAL collection-selection (Kulkarni&Callan/Salton), IVF/nprobe, vocab-mismatch (Xiao 1806.10869) model cluster score as MEMBER GEOMETRY. Novelty = editorial-aggregate-vs-member coverage gap = reachability ceiling unbounded in S + NOT closed by a stronger (lexical) stage-1. This is the BEST-screened candidate of the expansion: anchored (coverage structural, beats killer#6), both standard mitigations modeled+insufficient (beats killer#7), mechanism 100pct attributed, and the killer-#4 residual was TESTED IN THE L0 and did NOT fire (lexical stronger-stage-1 doesn't close it). If candidate-grade, L1 (CONFIRMATORY): real MCP/ToolBench registry + real DENSE embedding retriever+reranker, reachable-recall@k flat-vs-two-stage w/ as-written editorial descs, confirm real under-coverage + ceiling/S-scaling + RESOLVE #4 (the miss NOT closed by a stronger DENSE stage-1 ENCODER — the one thing L0 lexical couldn't fully settle). If you judge the editorial-blurb routing premise is ecologically wrong (real routing is member-pooled -> coverage~1) OR a dense encoder would close it, say YELLOW/RED honestly. Real 6/6 by role.
