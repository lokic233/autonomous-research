# Prior-art sweep — EXP-0013 (real abstracts fetched via arxiv export + web search, 2026-06-03)

## Required baselines (VERDICT-0011)
- **H2O (2306.14048)**: heavy-hitter = accumulated attention. The exact eviction signal we call "P-H2O".
- **SnapKV (2404.14469)**: per-head attention features from an observation window at end of prompt; pooling/clustering of important KV positions. Prompt-window based, not long-horizon callback.
- **Scissorhands (2305.17118)**: "persistence of importance" hypothesis — pivotal tokens stay pivotal. CLAIM-0010's cold-then-hot is the COUNTEREXAMPLE to this hypothesis (importance NOT persistent: cold at commit, hot later).
- **A2SF (2407.20485)**: *** COLLISION RISK ***. Diagnoses that accumulated attention score is biased by token order/masking; adds a Forgetting Factor. Same "accumulated-attention is a biased importance signal" critique as ours. Differs: A2SF still works in attention space (a decay correction), does NOT use lexical/handle recurrence and does NOT operate on tool-result spans.
- **InfiniGen (2406.19707)**: speculates next-layer important tokens via minimal rehearsal + partial query/key; prefetches essential KV from offload. Predicts FUTURE-layer importance from a cheap proxy — same *class* (cheap proxy → future KV importance) but attention-space speculation, not lexical handles, and within-step not cross-turn callback.
- **Quest (2406.10774)**: query-aware page criticality from min/max key per page. Query-dependent (recovers cold-then-hot IF the later query attends), page-granularity. Same *class*. No lexical handle signal, no tool-result-span notion.
- **ArkVale (NeurIPS24)**: *** STRONGEST COLLISION ***. "Recallable KV eviction" — evicts pages but can RECALL evicted ones for later queries. This DIRECTLY addresses cold-then-hot: a span evicted while cold can be recalled when it becomes hot. If ArkVale recall works on tool-result handles, H2O's "0.000 on delayed callbacks" weakness is ALREADY SOLVED by a published method — and the recall is query-driven, not requiring our lexical proxy.
- **ACON (2510.00615)**: agent context compression for long-horizon LLM agents; LLM-optimized compression guidelines from paired success/fail trajectories. Same DOMAIN (long-horizon agents, tool obs+history). Differs: NL-space compression, not KV eviction; learns what to keep from failure analysis.

## Additional collision works found (web search)
- **"Learning to Evict from KV Cache" (Apple, 2602.10238)**: explicitly frames the problem as "recency/past-attention heuristics serve only as INDIRECT PROXIES for a token's FUTURE value" — *identical framing to CLAIM-0010's thesis*, and learns the future value directly. Threatens the core "predict future reference, not past attention" novelty.
- **ForesightKV (2602.03203)** "Learning Long-Term Contribution"; **OBCache (2510.07651)**; **ClusterKV (2412.03213)** recallable; **NACL (2408.03675)**.

## VERDICT on novelty (honest)
The residual novelty CLAIM-0010 banked on after VERDICT-0011 = {tool-result-span granularity + LEXICAL handle/n-gram recurrence as the predictor signal}.
- The "past-attention is a biased/indirect proxy for FUTURE value" diagnosis is NOT novel: A2SF, InfiniGen, Quest, "Learning to Evict" (Apple), ForesightKV all share it.
- The cold-then-hot recovery mechanism is NOT novel as a system capability: ArkVale (recallable eviction) and Quest (query-aware recall) already recover spans that go cold-then-hot, WITHOUT needing a lexical handle signal — they use query-key geometry.
- The ONLY surviving differentiator is the LEXICAL handle/n-gram-recurrence signal on tool-result spans specifically. None of the surveyed works use lexical surface recurrence of tool-result identifiers. That is a narrow, real-but-thin slice — AND it is only valuable if (a) real traces have cold-then-hot AND (b) the geometry-based recallers (ArkVale/Quest) DON'T already catch those spans. If H2O's own real attention catches handle tokens at commit, even the thin slice is moot.
