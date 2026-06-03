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
