# PRE_REGISTRATION — EXP-0060 (CLAIM-0052) — L1 DENSE-ENCODER (killer #4 resolution)

researcher-0058 | PROJ-0022 | TASK-0050 | L1 GPU H100 (devgpu014) | one-shot
Committed BEFORE running. Honest pipeline — a null/recovery is a WIN. Never fabricate.

## WHY THIS L1 EXISTS (the load-bearing gap)
L0 (EXP-0058) HELD on a LEXICAL stronger-stage-1 arm (idf + query-expansion over token-bags).
committee#1 (VERDICT-0050): unanimous YELLOW, no RED — clean, but GREEN BLOCKED by ONE gap
flagged by all 5 reviewers: the L0 stronger-stage-1 arm is a STRAWMAN. A lexical matcher failing
to recover a literally-ABSENT token is ALGEBRAICALLY FORCED, not evidence about representational
power. Xiao et al. 2018 (1806.10869) showed NEURAL/dense reps recover recall lexical indices miss
by exploiting SEMANTIC NEIGHBORS. So the claim's differentiator ("the coverage gap is NOT closed
by a stronger stage-1 representation") is ASSERTED, not EARNED, until a DENSE encoder is tested
and STILL fails. THIS L1 settles it.

## DECISION (pre-committed)
- SUPPORT (structural ceiling EARNED, green-track): a DENSE embedding stage-1 router ALSO fails to
  close the coverage gap (because when the distinctive capability is genuinely ABSENT from the
  editorial description, even semantic similarity has nothing to match on) AND pooled-member-schema
  routing does NOT trivially drive effective coverage -> 1.
- KILL/WEAKEN (recoverable vocab-mismatch, killer #4 WINS): the dense encoder RECOVERS the gap
  (semantic neighbors of the absent capability in the editorial description surface the server
  anyway). KILL if it fully closes; WEAKEN if it substantially (but not fully) closes.
- ECOLOGICAL-KILL: pooled-member-schema (ReDDE "big-document") server representation drives
  effective coverage -> ~1 (gap vanishes) -> real systems that pool member schemas don't have the
  ceiling -> the claim's ceiling is not ecologically load-bearing.

## ENCODERS (real dense neural, NOT token-bags)
- PRIMARY: BAAI/bge-base-en-v1.5 (768d, instruction-tuned retrieval SOTA-class).
- SECONDARY (robustness): intfloat/e5-base-v2 (768d). e5 "query:"/"passage:" prefixes; bge uses
  its retrieval instruction. Both cached on devgpu014, HF_HUB_OFFLINE for the run.
- Encoding on H100 (GPU 3), cosine over L2-normalized embeddings. GPU mem capped; os._exit.
- ALSO report the L0-style LEXICAL token-bag stage-1 (TF cosine) on the SAME registry as the
  reference arm, so the #4 discriminator is DENSE-vs-LEXICAL on identical data.

## REGISTRY (realistic NL descriptions so dense semantics are MEANINGFUL)
Real MCP catalog harvested LIVE from the Glama registry API (398 real, as-written editorial server
descriptions in real_mcp_descs.json). The Glama endpoints do NOT expose per-tool schemas (tools[]
empty), so per-tool capability ground truth is not directly available. We therefore build a
CONTROLLED registry whose descriptions are REAL-NL-STYLE and whose coverage knob c is harness-owned
(required to RESOLVE #4 — we must control whether the distinctive capability is present/absent in
the editorial blurb):
- S servers x T tools. Each server is assigned a real-world DOMAIN (web scraping, SQL database,
  git/code search, calendar, image generation, k8s ops, ...) from a curated bank of realistic MCP
  capability phrases grounded in the 398 real descriptions.
- Each tool = a DISTINCTIVE CAPABILITY as a natural-language phrase (e.g. "convert a web page URL
  into clean LLM-ready markdown") + the server's shared domain boilerplate sentence. Tool SCHEMA
  (stage-2 observable) = NL string: distinctive capability + boilerplate.
- Server EDITORIAL AGGREGATE description (stage-1 observable) = a natural-language paragraph: the
  domain boilerplate sentence + for each member tool, its distinctive capability phrase INCLUDED
  w.p. c (coverage), else OMITTED (the coverage gap). Mirrors real editorial blurbs that describe
  the server theme + a SUBSET of its tools.
- Query for target tool t = a natural-language PARAPHRASE of t's distinctive capability (NOT the
  verbatim schema string), so dense semantics — not string match — are what matters. GT = t,
  harness-held, NEVER exposed to retrieval. Retrieval reads ONLY embeddings of (query, server-desc,
  tool-schema).

## RETRIEVERS (read ONLY embeddings; never see GT)
- Score = cosine(query_emb, target_emb).
- FLAT: cosine(query, tool-schema) over ALL N tools; top-k. No routing => no-ceiling baseline.
- TWO-STAGE dense (#4 arm): cosine(query, server-EDITORIAL-desc) -> top-m servers ->
  cosine(query, tool-schema) within -> top-k. Sweep m.
- POOLED-MEMBER-SCHEMA (ReDDE big-doc, ecological baseline): server rep = concatenation of all
  member tool SCHEMAS (not the editorial blurb). If pooling drives effective coverage->1, real
  systems don't have the ceiling.
- LEXICAL TWO-STAGE (L0 reference): TF token-bag cosine on the editorial desc, same routing.

## CONDITIONS (4 + lexical reference)
(i)   FLAT dense (no-ceiling baseline)
(ii)  TWO-STAGE dense over EDITORIAL desc (sweep top-m) — the #4 test
(iii) the #4 discriminator = dense editorial stage-1 vs L0 lexical at COVERAGE-GAP items
(iv)  POOLED-MEMBER-SCHEMA stage-1 (ecological audit)
(ref) LEXICAL TWO-STAGE over editorial desc (TF cosine) — L0-style reference on identical data

## METRIC
reachable-recall@k = fraction of queries whose GT tool is in the FINAL candidate set after both
stages within top-k. PRIMARY k = T (full within-server set — isolates the ROUTING ceiling). Also
report reachable-recall at COVERAGE-GAP ITEMS ONLY (queries whose GT tool's distinctive capability
is ABSENT from its server's editorial desc) — the #4 discriminator number.

## SWEEPS
- coverage c in {0.5, 0.7, 0.9, 1.0}
- registry size S in {10, 20, 40} (T fixed = 8)
- top-m in {1, 2, 3, S}
- seeds: >= 12 seeds/cell; mean +/- 95% CI (normal approx).

## TOST / EQUIVALENCE (pre-committed)
For any "dense doesn't help" NULL we report an EQUIVALENCE test, NOT just failure-to-reject.
Quantity: delta = reachable-recall(dense TWO-STAGE at coverage-gap items) -
reachable-recall(lexical TWO-STAGE at coverage-gap items), per matched cell. TOST equivalence
bound = +/- 0.05 (5 recall points) on this paired delta. If the 90% CI of the mean paired delta
lies within +/-0.05 -> statistically EQUIVALENT (dense does NOT recover the gap) -> SUPPORT-side.
If dense delta CI is meaningfully > +0.05 -> dense RECOVERS -> KILL/WEAKEN.

## ANTI-CIRCULAR / MECHANISM CHECK
GT is harness-held and never embedded into any retrieval score. For every two-stage miss we log
whether it is a coverage-gap event (distinctive capability absent from GT server's editorial desc).
SUPPORT requires misses to coincide with coverage-gap events; recovery would show dense routing the
GT server DESPITE the absence (semantic-neighbor recovery — the Xiao2018 mechanism).

## EXPECTED MECHANISM (a-priori, falsifiable)
When the distinctive capability is ABSENT, the editorial desc's remaining content is shared domain
boilerplate — which all same-domain servers share and which is SEMANTICALLY GENERIC w.r.t. the
specific query. A dense encoder exploits semantic neighbors ONLY IF the absent capability leaves a
semantic trace. If boilerplate is generic and the capability genuinely distinctive, dense
similarity has near-zero signal to surface that server at top-m < #same-domain-servers -> ceiling
EARNED, distinct from Xiao2018. If realistic boilerplate carries enough semantic overlap that dense
recovers -> KILL (honest).
