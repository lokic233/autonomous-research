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
  boilerplate tokens.
- Each tool = bag of tokens: ONE distinctive token d_t + a random subset of shared tokens.
- Each tool's SCHEMA (stage-2 observable) = {d_t} U its shared tokens.
- Each server's EDITORIAL AGGREGATE description (stage-1 observable) = union over its member
  tools of: distinctive token d_t included with probability c (coverage rate; with prob (1-c)
  the distinctive token is ABSENT — the coverage gap) PLUS all shared/boilerplate tokens
  (boilerplate always present — that's what "editorial/aggregate" descriptions look like).
- Query for a target tool t = {d_t} (+ optionally a few of t's shared tokens). GT = t (which
  tool the query was generated to target). GT is harness-held, NEVER exposed to retrieval.

## RETRIEVERS (read ONLY observable scores; never see GT)
- Score = cosine over token count vectors (TF) by default; stronger arm upgrades this.
- stage-1: score(query, server-description) over the S server descriptions.
- stage-2: score(query, tool-schema) over tools within retrieved servers.

## FOUR CONDITIONS
(i)  FLAT: score(query, tool-schema) over ALL N tools; take top-k. No routing. No-ceiling baseline.
(ii) TWO-STAGE: top-m servers by stage-1, then top-k tools (by stage-2) within them. Sweep
     top-m in {1,2,3,5,...,S}.
(iii)TWO-STAGE + RERANK: same routing, but stage-2 is a STRONGER within-server reranker
     (idf-weighted / exact-distinctive-match boost — the ToolRerank mitigation). Tests whether a
     better stage-2 lifts reachable-recall (it cannot route to an unrouted server).
(iv) * TWO-STAGE + STRONGER STAGE-1 (killer #4 boundary): give stage-1 a richer/stronger server
     representation — query expansion + idf weighting + an ORACLE-ish strong matcher (even
     allowed to use the FULL boilerplate + any token actually in the description, best-possible
     lexical+semantic match). The server description STILL only contains what coverage c put in.
     If d_t was dropped (coverage gap), even a perfect matcher on the description has no signal.

## METRIC
reachable-recall@k = fraction of queries whose GT tool appears in the FINAL candidate set
(after both stages, within top-k). Within-server we keep top-k tools per routed server; final
set = union, capped at k where applicable. We report reachable-recall@k for k = T (full
within-server set, isolating the routing ceiling) and also k small.

## SWEEPS
- coverage c in {0.5, 0.7, 0.9, 1.0}
- registry size S in {5, 10, 20, 40} (T fixed, e.g. T=8)
- top-m in {1, 2, 3, 5, S}
- seeds: >=20 seeds per cell; report mean +/- 95% CI (normal approx).

## DECISION RULES (pre-committed)
Let G(c,S,m) = reachable-recall_FLAT - reachable-recall_TWOSTAGE at given cell.
- HELD (SUPPORT): For c<1 and m<S, G>0 with CI excluding 0 AND
  (a) RERANK does NOT close G (stage-2 strengthening leaves G ~ unchanged), AND
  (b) * STRONGER STAGE-1 does NOT close G (the #4 discriminator — gap persists), AND
  (c) G grows with (1-c) and with S (monotone trend).
  Mechanism check: misses must coincide with coverage-gap events (d_t absent from GT-server desc).
- KILL/WEAKEN: STRONGER STAGE-1 representation CLOSES G (G -> ~0 under arm iv) -> recoverable
  vocab-mismatch (killer #4 wins). Report honestly. KILL if it fully closes; WEAKEN if partial.
- HONEST-NEGATIVE: at realistic c=0.7-0.9 G is negligible, OR top-m=2-3 closes G, OR no S-scaling
  -> raise-m/rerank sufficient, contradicts production complaint.

## EXPECTED MECHANISM (a-priori, falsifiable)
When d_t is absent from server(t)'s description, the query {d_t} matches server(t) ONLY via
shared/boilerplate tokens — which ALL servers also share. So server(t) is NOT distinguished;
under top-m < (#servers tied on boilerplate) it is NOT routed; its tool t is unreachable. A
stronger stage-1 cannot manufacture the absent signal. FLAT bypasses routing -> finds t directly.
