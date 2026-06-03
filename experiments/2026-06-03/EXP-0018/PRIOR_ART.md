# PRIOR-ART SWEEP — EXP-0018 (M5). Live web sweep on 2026-06-03 (devgpu014 egress + web_search). >=2 sources per claim.

## THE NOVELTY-KILL: A published work ALREADY gates retrieval on IN-CONTEXT (live-window) RESIDENCY.
### A-RAG — "Scaling Agentic Retrieval-Augmented Generation via Hierarchical Retrieval Interfaces" (arXiv 2602.03442)
VERBATIM (arxiv.org/html/2602.03442, §3 "Context Tracker"):
  "To prevent redundant information retrieval and unnecessary token consumption, we maintain a CONTEXT TRACKER
   that records which chunks have been READ during the retrieval process. Specifically, we track a set
   C^read = {c_{i1}, c_{i2}, ..., c_{ik}} ..."
=> This is EXACTLY the in-context-residency gate the claim asserts as its narrow novelty: track what is already
   resident in the live context (read so far) and skip retrieving it again to cut token/latency cost. A-RAG
   gates on the LIVE CONTEXT (read-set), NOT on past queries (cache) and NOT on parametric self-knowledge (SKR).
   This is a DIRECT collision on the core mechanism (the "live-window" contribution). NOVELTY KILL.

### "To Retrieve or To Think? An Agentic Approach for Context Evolution" (arXiv 2601.08747)
  Critiques "rigid brute-force retrieval at every step"; gates retrieval on the EVOLVING CONTEXT state — same
  family (skip retrieval when the current context already suffices), reinforcing that live-context-conditioned
  retrieval gating is established prior art, not novel.

## SEMANTIC QUERY CACHE (the load-bearing baseline) IS a deployed standard.
- GPTCache / Zilliz (zilliz.com "Yet another cache but for ChatGPT"): embed query context, vector-search the
  cache of past queries, skip the LLM/retrieval call on a similarity hit. THE comparator we implemented.
- "GPT Semantic Cache" (arXiv 2411.05276): semantic embedding caching of (query,result), cosine thr ~0.8.
- "Privacy-Aware Semantic Cache" (arXiv 2403.02694), "Semantic Caching for Low-Cost LLM Serving" (2508.07675),
  Redis "prompt vs semantic caching": all store past query->answer and reuse on semantic similarity.
- HF forum thread (discuss.huggingface.co/t/172433): multi-turn RAG explicitly COMBINES "context-aware query
  rewriting + SEMANTIC CACHING + scope-aware caching" — the gate+cache combination is already practitioner-standard.

## "DO I NEED EXTERNAL KNOWLEDGE" gating (parametric self-knowledge) — distinct axis, also published.
- SKR (arXiv 2310.05002, "Self-Knowledge Guided Retrieval Augmentation"): elicit the model's self-knowledge of
  whether it already KNOWS the answer (PARAMETRIC), retrieve only when it doesn't. NOT in-context residency.
- SeaKR (ACL 2025 / arXiv 2406.19215): retrieve on internal-state self-aware UNCERTAINTY. Parametric, not in-context.
- Self-RAG, FLARE, Adaptive-RAG, Self-Routing RAG (2504.01018), RetrievalQA/TA-ARE (2402.16457): all gate on
  "is external retrieval needed/useful", NOT "is this content already in my live window".
- "Learning When to Retrieve, What to Rewrite... in Conversational QA" (arXiv 2409.15515): conversational
  when-to-retrieve gating using dialog context — closest conversational analogue; gates on contextual search
  INTENT, overlaps the spirit of the claim.

## VERDICT ON NOVELTY (M5)
The claim's NARROW novelty was "gate retrieval specifically on IN-CONTEXT (live-window) residency, distinct from
(a) parametric self-knowledge [SKR/SeaKR] and (b) past-query caching [GPTCache]." Finding: A-RAG's Context Tracker
(2602.03442) ALREADY gates on live-window residency (read-set of chunks) to prevent redundant retrieval. The
specific contribution is therefore PRE-EXISTING. NOVELTY KILL (pre-registered branch N4 fires).
