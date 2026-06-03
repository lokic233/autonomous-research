# PRE-REGISTRATION — EXP-0018 (L1, CLAIM-0013, PROJ-0001)
researcher-0018 | committed BEFORE running results. Honest pipeline. Negatives / operationally-falsified = WINS.
Nodes: cli:devgpu014 (H100, real egress via fwdproxy, reuse ros-EXP-0003 venv + uv) for real embedding/LLM/datasets;
cli:dengcchi-mac (engine + artifact dir).

## CONTEXT
L0 (EXP-0017) = unanimous-YELLOW (VERDICT-0016). Committee#1: random-skip is a SANITY CHECK not a deployment
baseline. The LOAD-BEARING required baseline is a SEMANTIC QUERY CACHE (GPTCache/RAGCache). Contribution
currently narrowed to MEASUREMENT METHODOLOGY; gate-concept novelty UNRESOLVED vs SKR + semantic caching.

## THE CLAIM UNDER TEST
In long-horizon agents w/ external memory/RAG, a cheap pre-retrieval check (embedding/lexical overlap of the
query vs IN-CONTEXT spans — the LIVE CONTEXT WINDOW, NO extra LLM call) can SKIP retrievals whose answer is
ALREADY in the window, cutting cost without harming task accuracy. The NARROW novelty = gating on IN-CONTEXT
(live-window) residency, distinct from (a) "do I need external knowledge" (SKR/Self-RAG) and (b) "have I seen
this QUERY before" (semantic query cache / GPTCache).

## DATASETS WE WILL ATTEMPT (real, in priority order; egress on devgpu014)
1. A real multi-turn conversational-QA / conversational-RAG dataset where answers to later turns appear in
   PRIOR turns of the SAME conversation (=> in-context-presence label derivable from structure). Candidates:
   - HF `coqa` / `quac` (conversational QA over a passage; later questions reference earlier answers).
   - HF `topiocqa` or `mrqa`-style multi-turn if reachable.
   - If none reachable: BFCL multi_turn (already on devgpu014) repurposed — successive turns whose answer
     (a created entity / earlier tool result) is already resident.
   We will STATE EXACTLY what loaded. In-context-presence GT label per turn t:
     GT_INCONTEXT(t) := the gold answer string (or its supporting span) for turn t is already present in the
     concatenated text of turns < t that are inside the live window W. This is STRUCTURAL, derived from the
     dataset's own answer annotations — NOT a synthetic generator, NOT the L0 item-id sim.
   If NO real dataset is reachable offline => HONEST SUBSTITUTE: a small REAL corpus + REAL retrieval, labels
   from actual retrieved-vs-in-context overlap. Clearly labeled. NOT the L0 generator.

## METHODS / SYSTEMS COMPARED
- ALWAYS-RETRIEVE (upper-bound accuracy, zero savings).
- ORACLE-SKIP (skips iff GT_INCONTEXT — upper bound for any gate).
- RANDOM-SKIP @ matched skip-rate (sanity floor; carried from L0).
- *** IN-CONTEXT GATE *** : skip retrieval at turn t if max similarity(query_t, span) over spans in the LIVE
  WINDOW >= tau. Similarity in 2 variants: (i) lexical Jaccard (token sets), (ii) REAL sentence embedding
  cosine (all-MiniLM-L6-v2 or similar via sentence-transformers).
- *** SEMANTIC QUERY CACHE (LOAD-BEARING) *** : GPTCache/RAGCache-style. Maintain a cache of PAST (query,
  result) pairs seen so far in the conversation. Skip retrieval at turn t if max cosine(query_t, past_query_j)
  >= tau_cache; on hit, reuse cached result. Same embedding model. Key difference: cache keys on PAST QUERIES,
  gate keys on the LIVE CONTEXT WINDOW (which includes retrieved RESULTS / tool outputs / prior answers, not
  just queries).

## METRICS
- M1 real redundancy fraction (frac of turns with GT_INCONTEXT=1) on the real data.
- M2 AUC of each cheap signal (lexical Jaccard, real-embedding cosine) vs GT_INCONTEXT; ORACLE AUC=1. Report
  AUC-gap closure: real-embedding AUC − lexical AUC, and (1 − each) = gap to oracle.
- M3 *** HEAD-TO-HEAD @ MATCHED SKIP-RATE *** : sweep tau for the in-context gate; for each achieved skip-rate
  s, set the query-cache threshold to also skip s of retrievals; compare (a) which redundant retrievals each
  catches (precision/recall vs GT_INCONTEXT), (b) end-to-end task accuracy. Pareto curve savings vs accuracy.
- M4 REAL LLM-in-loop task accuracy at matched skip-rate: Qwen2.5-1.5B-Instruct answers each turn with the
  context it would have under each policy (with vs without the skipped retrieval). Score vs gold (EM/F1/judge).
  in-context-gate vs semantic-cache vs always-retrieve, at matched skip-rate.
- M5 prior-art: >=2 live sources. SKR(2310.05002), GPTCache, Self-RAG, FLARE, Adaptive-RAG, conversational
  query-rewriting/history-aware retrieval. Does ANY published work gate retrieval on IN-CONTEXT (live-window)
  RESIDENCY specifically (vs parametric "do I need external knowledge" or "have I seen this query")?

## PRE-REGISTERED HONEST-NEGATIVE BRANCHES (any one => report the negative; that is a WIN)
N1. In-context gate does NOT beat the semantic query cache at matched skip-rate (cache catches the same or
    more redundant retrievals at >= Pareto efficiency) => "live window" contribution OPERATIONALLY FALSIFIED.
N2. Real-embedding gate does NOT beat lexical Jaccard (AUC gap not closed) => embedding upgrade unjustified.
N3. Skipping TANKS real LLM task accuracy at matched skip-rate (model does NOT recover) => gate unsafe.
N4. A published work ALREADY gates on the live-window (in-context residency) => NOVELTY KILL.
N5. No real trace/LLM reachable offline => "methodology-only, key baselines unmeasured" — converge, NO fabrication.

## VERDICT MAPPING
- held: gate beats query-cache at matched skip-rate AND real-embedding helps AND LLM accuracy preserved AND no prior-art collision on live-window gate.
- partial/weaken: some but not all.
- refuted/operationally-dead: N1 or N4 fires (query cache does it just as well, OR a paper already does the live-window gate).
- methodology-only: N5.
