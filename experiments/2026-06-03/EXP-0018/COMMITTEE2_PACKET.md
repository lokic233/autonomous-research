# COMMITTEE#2 — CLAIM-0013 (PROJ-0001), WITH real-data L1 (EXP-0017 L0 + EXP-0018 L1)
## SECOND pass (post-L1). committee#1 (VERDICT-0016) voted unanimous YELLOW and required an L1 with: real traces, a REAL embedding, the SEMANTIC-QUERY-CACHE baseline (the load-bearing comparator — random-skip was only a sanity check), real LLM-in-loop task accuracy, and a live prior-art sweep vs SKR/GPTCache. The L1 is now in. Cast FINAL votes. Engine enforces real 6/6; GREEN only if truly unanimous green by role — NEVER fabricate. This L1 is a clean pre-registered REFUTED — vote honestly (a well-evidenced negative that resolves the question is the correct outcome; the researcher's honesty is commendable, keep out of punitive RED-for-RED's-sake but the claim concept IS dead).

## L1 KEY FINDINGS (real CoQA 4764 turns; MiniLM embedding; Qwen2.5-1.5B-Instruct via vLLM, 5604 gens; on H100):
1. Real redundancy M1 = 0.532 (>20% confirmed on real data — Part A holds).
2. LOAD-BEARING (the committee#1 ask): in-context gate vs SEMANTIC QUERY CACHE @ matched ~29% skip (1868 paired turns) -> real LLM token-F1: always 0.476 / gate 0.4505 / cache 0.4501. gate-cache F1 = +0.0004, bootstrap 95% CI [-0.0045,+0.0053] = ZERO measurable difference. A query cache captures the same redundant retrievals at equal Pareto efficiency. The 'live window vs past query' distinction is operationally MEANINGLESS on real data. (pre-registered N1 fires.)
3. Cheap signal is near-chance on real data: AUC vs in-context GT = 0.570 (embedding) / 0.554 (lexical) / oracle 1.0 -> gap ~0.43. The L0's AUC 0.84-1.00 was a TAUTOLOGY of its generator (text seeded from item-id). Real embedding beats lexical by only +0.016.
4. Real LLM task accuracy: gate~=cache~=(always - 2.6 F1). Wrong skips only PARTIALLY recoverable (wrong-skip F1 0.17 vs correct-skip 0.52). No gate-vs-cache gap anywhere.
5. NOVELTY KILL (pre-registered N4 fires): A-RAG (arXiv 2602.03442) 'Context Tracker' ALREADY records which chunks have been read to prevent redundant retrieval — that IS the live-window residency gate the claim called its narrow novelty. Plus 'To Retrieve or To Think?' (2601.08747) gates on evolving context; semantic query caching is a deployed standard (GPTCache, GPT Semantic Cache 2411.05276).
Both pre-registered kill-branches (N1 cache-matches AND N4 prior-art) fired. The L0 'win' was an artifact of the constructed generator; on real data the live-window gate = a semantic query cache, and a published system already does it.

## WHAT SURVIVES: only the MEASUREMENT METHODOLOGY (anti-circular item-id GT + matched-skip-rate-vs-cache control) + the clean negative itself. The gate CONCEPT is operationally dead.

## CLAIM
claim: "In long-horizon agents with external memory/RAG, a non-trivial fraction (>20%)\
  \ of retrieval calls are REDUNDANT \u2014 they return content already present in\
  \ the live context window \u2014 AND a cheap pre-retrieval check (lexical/embedding\
  \ overlap of the query against in-context spans, NO extra model call) can identify\
  \ a meaningful share of these BEFORE issuing the retrieval, skipping them to cut\
  \ retrieval latency + injected-token cost WITHOUT harming task accuracy (the skipped\
  \ content was already available to the model)."
why_it_matters: "Fresh axis (agent memory/RAG retrieval-cost \u2014 untouched by the\

## FULL L1 RESULTS (EXP-0018)
# RESULTS — EXP-0018 (L1, CLAIM-0013, PROJ-0001)
researcher-0018 | nodes: cli:devgpu014 (H100, REAL egress via fwdproxy) for data/embedding/LLM; cli:dengcchi-mac (engine+artifacts).
Pre-registered & committed BEFORE running (commit 51b9eb7). Honest pipeline. A negative / operational-falsification = WIN.
Reused ros-EXP-0003 venv (torch 2.11+cu13, vLLM 0.22, transformers 5.9) + uv (PyPI via fwdproxy; system pip wrapper-blocked).

## TL;DR VERDICT: **REFUTED / OPERATIONALLY DEAD** (two independent pre-registered kill-branches fire: N1 ∧ N4).
The L0's load-bearing edge does NOT survive real data. On REAL multi-turn conversational-QA traces with a REAL
sentence embedding and a REAL LLM in the loop, the IN-CONTEXT (live-window) redundancy gate is **statistically
indistinguishable from a semantic QUERY CACHE** at matched skip-rate (the deployment baseline committee#1 demanded),
AND a published system (**A-RAG, arXiv 2602.03442, "Context Tracker"**) already gates retrieval on live-window
residency. The "live window" contribution is operationally falsified and the narrow novelty is pre-existing.

---

## (1) DID WE GET REAL TRACES + REAL EMBEDDING + REAL LLM? — YES to all three.
- **REAL TRACES**: HuggingFace `stanfordnlp/coqa` (CoQA), validation split, 300 dialogs → **4,764 real multi-turn
  conversational-QA turns**. Each dialog = a story + a sequence of Qs whose answers reference earlier turns. We frame
  it as agent+RAG (the pre-registered HONEST SUBSTITUTE — real corpus + real retrieval, labels from ACTUAL
  retrieved-vs-in-context overlap; NOT the L0 synthetic generator): story → sentence chunks = retrieval corpus;
  each turn retrieves top-1 chunk by embedding sim; the gold supporting chunk is located via CoQA's real
  `answer_start` rationale offsets. **GT_INCONTEXT(t)** := the gold supporting chunk for turn t was already SHOWN
  (retrieved or was a prior answer's support) within the live window (W=6 turns). Structural, from real annotations.
- **REAL EMBEDDING**: `sentence-transformers/all-MiniLM-L6-v2`, on H100, replacing the L0 stdlib hashed surrogate.
- **REAL LLM**: `Qwen/Qwen2.5-1.5B-Instruct` via vLLM 0.22 (5,604 generations), answers each turn with/without the
  skipped retrieval; token-F1 + EM vs CoQA gold.

**M1 real redundancy fraction = 0.532** (2,535/4,764 turns in-context-redundant). >20% confirmed on real data
(consistent with L0's moderate-reuse band). Real retrieval top-1==gold rate = 0.434 (single-hop QA is hard; honest).

## (2) *** THE LOAD-BEARING ANSWER: does the in-context gate beat a SEMANTIC QUERY CACHE @ matched skip-rate? NO. ***
Semantic query cache = GPTCache/RAGCache style: cosine(query_t, PAST QUERIES); skip on hit. In-context gate =
cosine(query_t, LIVE WINDOW content: prior Q/A + retrieved chunk text); skip on hit. Same embedding. Matched skip-rate.

PRECISION (frac of skipped retrievals that were truly redundant; redundant BASE RATE = 0.532 = random-skip precision):
| matched skip | GATE prec | CACHE prec | RANDOM prec | Δ(gate−cache) [boot 95% CI] | gate−random |
|---|---|---|---|---|---|
| 0.10 | 0.583 | 0.526 | 0.532 | **+0.057 [+0.022,+0.090]** | +0.051 |
| 0.20 | 0.549 | 0.525 | 0.532 | +0.024 [−0.001,+0.046] | +0.017 |
| 0.30 | 0.557 | 0.544 | 0.532 | +0.013 [−0.005,+0.031] | +0.025 |
| 0.40 | 0.572 | 0.562 | 0.532 | +0.011 [−0.005,+0.024] | +0.040 |
| 0.50 | 0.574 | 0.568 | 0.532 | +0.006 [−0.006,+0.017] | +0.042 |
The gate beats the cache only at the lowest 10% skip (CI>0, +5.7pts) and is **statistically indistinguishable from
the query cache at every deployment-relevant skip-rate ≥20% (all CIs straddle 0).** Both sit barely above the
random-skip floor (0.532). **PRE-REGISTERED N1 FIRES.** Contrast the L0's +9 to +19pt edge over random — that edge
evaporated on real data because the cheap signal is near-useless here (see #3).

**End-to-end (the real test) — REAL LLM task accuracy @ matched ~29% skip (Qwen2.5-1.5B, 1,868 paired turns):**
| policy | F1 | EM | skip-rate |
|---|---|---|---|
| always-retrieve | 0.4765 | 0.3448 | 0.000 |
| in-context GATE | 0.4505 | 0.3276 | 0.296 |
| semantic CACHE  | 0.4501 | 0.3276 | 0.288 |
**gate − cache F1 = +0.0004, bootstrap 95% CI [−0.0045, +0.0053] → ZERO measurable difference.** The live-window
gate buys NOTHING over a query cache in real task accuracy. (always−gate = +0.026 [+0.018,+0.034]: skipping does
cost ~2.6 F1 pts — modest but CI-significant; wrong skips are only PARTIALLY recoverable: wrong-skip F1=0.17 vs
correct-skip F1=0.52, so the LLM does NOT fully re-ask its way out of a bad skip).

## (3) REAL-EMBEDDING AUC vs LEXICAL + ORACLE GAP (M2)
AUC of each cheap signal vs GT_INCONTEXT (oracle AUC = 1.0 by definition):
| signal | AUC | gap-to-oracle |
|---|---|---|
| gate, real embedding (MiniLM) | 0.570 | 0.430 |
| gate, lexical Jaccard | 0.554 | 0.446 |
| cache, real embedding | 0.554 | 0.446 |
| cache, lexical Jaccard | 0.543 | 0.457 |
**Real embedding beats lexical by only +0.016 AUC** (0.570 vs 0.554) — a trivial closure of the oracle gap. The L0
hoped a real embedding would "close much of the paraphrase gap"; on real data BOTH are ~0.55, i.e. **near chance.**
The L0's AUC 0.84–1.00 was a tautology of its generator (text seeded from the item-id). On real CoQA the cheap
query-vs-window overlap signal barely predicts in-context residency at all — redundancy here is driven by topical
continuity over a small story, not by query/span lexical-semantic similarity. **Pre-registered N2 effectively also
fires** (the embedding upgrade does not rescue the signal). NOTE (lexical-Jaccard precision is actually slightly
HIGHER than the embedding gate at low skip — 0.644 vs 0.583 at s=0.1 — so the expensive embedding is not even
clearly the right cheap check). The whole gate family is weak on real data.

## (4) REAL LLM-IN-LOOP TASK ACCURACY @ matched skip-rate — see table in (2).
gate ≈ cache ≈ (always − 2.6 F1). Wrong skips partially but not fully recoverable. No policy gap between gate and cache.

## (5) PRIOR-ART (M5, live ≥2-source sweep — full detail in PRIOR_ART.md). NOVELTY KILL.
- **A-RAG (arXiv 2602.03442) "Context Tracker"**: "we maintain a context tracker that records which chunks have
  been READ during the retrieval process [to] prevent redundant information retrieval and unnecessary token
  consumption." This IS the live-window/in-context-residency gate the claim called its narrow novelty. DIRECT
  collision on the core mechanism. **Pre-registered N4 FIRES.**
- "To Retrieve or To Think?" (2601.08747): gates retrieval on evolving context state — same family.
- Semantic query cache is a deployed standard: GPTCache/Zilliz, GPT Semantic Cache (2411.05276), Privacy-Aware
  Semantic Cache (2403.02694); HF forum (172433) already combines "query rewriting + semantic caching" for multi-turn RAG.
- Parametric "do-I-need-knowledge" gating (DISTINCT axis, also published): SKR (2310.05002), SeaKR (2406.19215),
  Self-RAG, FLARE, Adaptive-RAG, Self-Routing RAG (2504.01018). These gate on parametric self-knowledge, not in-context.
**Answer: YES — published work (A-RAG) already gates retrieval on in-context (live-window) residency.**

## (6) COMMITTEE#2-READY VERDICT: **REFUTED (operationally dead).**
Two independent pre-registered kill-branches fire on real data:
- **N1**: the in-context gate does NOT beat a semantic query cache at matched skip-rate (precision Δ CI straddles 0
  for skip≥20%; real-LLM F1 Δ = +0.0004 [−0.0045,+0.0053]). The "live window vs past-query" distinction is
  OPERATIONALLY MEANINGLESS here — a query cache captures the same redundant retrievals at equal Pareto efficiency.
- **N4**: A-RAG's Context Tracker already implements live-window-residency retrieval gating → the narrow novelty is
  pre-existing.
- N2 also effectively fires (real embedding ≈ lexical ≈ chance; AUC ~0.55). The L0's strong AUC was generator-tautological.
What SURVIVES (and only this): the **MEASUREMENT METHODOLOGY** — the anti-circular GT, the matched-skip-rate-vs-cache
control, and the honest finding that *the live-window signal adds nothing over a query cache on real data*. That is a
clean, publishable NEGATIVE about a plausible optimization, not a positive contribution. The gate CONCEPT is dead.
Recommended map delta: CLAIM-0013 → weaken→refuted; retain only "matched-baseline measurement methodology + the
negative result that live-window gating ≈ query caching on real conversational RAG."

## HONEST LIMITATIONS (do not over-read)
- CoQA-as-RAG is an honest SUBSTITUTE, not native agent+RAG logs with human in-context-presence labels; single-hop,
  small-story setting where retrieval top-1==gold is only 0.434. A larger multi-doc agent corpus could differ — but
  the DIRECTION (gate≈cache; A-RAG prior art) is robust to that. The negative is conservative: if the cheap signal
  were stronger elsewhere, the cache benefits equally (both use the same embedding family). The N4 prior-art kill is
  dataset-independent.
- Qwen2.5-1.5B is a small model; a larger model might recover better from wrong skips, narrowing always−gate further
  (making skipping even safer) — which does NOT help the gate-vs-cache distinction (the load-bearing one).

## FILES (on cli:dengcchi-mac under experiments/2026-06-03/EXP-0018/)
- PRE_REGISTRATION.md (committed pre-run, 51b9eb7), PRIOR_ART.md, RESULTS.md
- results/analysis.json (AUC + M3 matched-skip precision/recall), results/ci_precision.json (bootstrap CI gate−cache),
  results/llm_inloop.json (real-LLM F1/EM + bootstrap CI)
- On cli:devgpu014 /home/dengcchi/ros-EXP-0018/: build_traces.py, analyze.py, ci.py, score_llm.py, llm_ci.py,
  traces.pkl, results/{rows.csv (4764 turns × signals), llm_detail.csv (5604 generations)}, run_llm.sh, load_test.sh

## L1 PRIOR-ART
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

## committee#1 reference: VERDICT-0016 yellow (required this exact L1: semantic-cache baseline + real data + prior-art).
