# PROJ-0022 — Agentic-systems: two-stage tool-routing has an EDITORIAL-COVERAGE reachability ceiling that survives the standard mitigations (top-m + rerank) (EMPIRICAL PHENOMENON)
Fresh area: agentic-systems (tool routing / MCP-scale tool retrieval). EMPIRICAL-phenomenon, NO closed form
(the miss depends on coverage x server-composition x top-m x rerank interaction, must be simulated). Survivor of
scout-G's 8-vein search (7 died). Anchored: editorial under-coverage is a STRUCTURAL quantity the harness controls
(not an assumed real-world shape -> beats killer #6). Models BOTH standard mitigations (top-m budget + within-server
rerank) and shows them insufficient (beats killer #7). HONEST RESIDUAL RISK = killer #4 (coverage-gap vs ordinary
vocabulary-mismatch Xiao2018) — NOT fully retired at design; the L0 is built to TEST THE #4 BOUNDARY as its PRIMARY
falsification. THESIS: in two-stage (route-to-server-then-select-tool) agentic tool retrieval, a correct tool is
structurally UNREACHABLE whenever its server's editorial AGGREGATE description fails to cover the tool's distinctive
capability tokens; this coverage-gap miss is independent of embedding/lexical score GEOMETRY, so NOT removed by
raising the server-probe budget top-m below full scan NOR by within-server reranking; flat (per-tool) retrieval over
the same registry has NO such ceiling; the reachable-recall gap grows with under-coverage rate (1-c) and registry
size S. THE #4-BOUNDARY TEST (load-bearing, primary): does a STRONGER stage-1 REPRESENTATION close the gap? If yes
-> recoverable vocab-mismatch (KILL/weaken); if no (server structurally never retrieved at m<#shadowing-servers
REGARDLESS of representation power) -> novel topological ceiling (HELD). Anti-circular: GT = which tool the query
targets (harness-held, never exposed to retrieval); signal reads only lexical/embedding scores over query<->server-
desc (stage1) + query<->tool-schema (stage2). Honest-negative (informative): if at realistic c=0.7-0.9 the gap is
negligible, OR modest top-m=2-3 closes it, OR it doesn't scale with S, OR a stronger stage-1 representation closes it
-> reduces to recoverable vocab-mismatch (killer #4 wins) -> weaken/kill. PRIOR-ART: Tool-to-Agent (2511.01854),
ToolRerank (2403.06551), RAG-MCP/MCP-Zero (2506.01056) treat failures as GEOMETRY/ranking; FOUNDATIONAL collection-
selection (Kulkarni&Callan, Salton cluster hypothesis), IVF/nprobe (FAISS), vocab-mismatch (Xiao 1806.10869) model
cluster score as MEMBER GEOMETRY (raising nprobe/top-m recovers recall). Delta = the load-bearing quantity is the
EDITORIAL AGGREGATE description (NOT the member centroid) -> coverage-determined not geometry-determined -> persists
at any top-m<#servers + invisible to rerank + m-threshold UNBOUNDED in registry size.
