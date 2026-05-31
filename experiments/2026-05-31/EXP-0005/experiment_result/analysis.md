# EXP-0005 — Workload Realism: empirical distribution of inj/seq for agentic tool-use

**Agent:** researcher-cdc-workload-B · **Project:** PROJ-0002 · **Claim:** CLAIM-0006 · **Level:** 0
**Method:** CPU-only Monte-Carlo, **token-count PROXY** for KV-cache blocks. NO GPU/torch/CUDA.
Deterministic (seed 20260531), ~1.5s wall, <50MB. **prompt_version:** researcher_v001
**Hardware:** CPU-only (dengcchi-mac).

## The crux this attacks
EXP-0002 established the CDC cost law: **recompute% ≈ injection_tokens / sequence_length (slope ~1)**,
NOT edit position. The ~2% headline holds ONLY where **inj/seq ≤ ~1%**. The committee's open attack:
*is inj/seq ≤ 1% the COMMON case in real agentic workloads, or a cherry-picked corner?* This experiment
answers it with an evidence-grounded distribution. It is a PROXY (token counts, not wall-clock KV cost),
explicitly so — but EXP-0002 already validated the proxy maps onto recompute fraction.

## Model (trajectory-aware, honest)
Agentic loops **accumulate context**: each tool result of size R_t is injected into a context of current
length S_t; the decision quantity is `inj/seq = R_t / S_t` at injection time. We Monte-Carlo 20,000 tasks
(291,454 injections) over evidence-grounded distributions (see `input_data/sources.md`, all cited):
- **Base context** (system prompt + tool schemas + task): light ~2k / typical ~8k / heavy MCP ~23k
  (dev.to MCP audit = 22,945 tok) / very heavy ~40k.
- **Tool-result sizes** by type, with heavy right tails for dumps: web_search 150–1800; rag_retrieve
  k(3–5)×chunk(128–1024); file_read mostly 120–2000 w/ 18% tail to 30k; code_exec mostly 40–1500 w/
  15% tail to 40k; api_json mostly 80–2500 w/ 20% tail to 60k (OpenBB MCP worst case = 210,004 tok);
  small_status 5–60.
- **Trajectory length** 1–60 tool calls; 1M-token context cap with compaction.

Regimes (from EXP-0002 law): **CDC_WINS** inj/seq≤1% (recompute<~2.4%) · **MID** 1–5% · **CDC_DEGRADES** >5%.

## Results (main run, count fractions over all injections)

| Regime | Count fraction | Token-weighted fraction |
|---|---|---|
| CDC_WINS (≤1%) | **24.6%** | 3.7% |
| MID (1–5%) | 38.9% | 15.6% |
| CDC_DEGRADES (>5%) | **36.5%** | **80.7%** |

inj/seq percentiles: p10=0.0037, p25=0.0102, **p50=0.0282**, p75=0.092, p90=0.293, p95=0.617, p99=2.87.

By tool type (count-fraction in CDC_WINS): small_status 96.8% · code_exec 27.4% · web_search 23.7% ·
file_read 17.9% · api_json 14.9% · rag_retrieve 14.7%.

### Sensitivity
- **No context accumulation** (each result vs base only — adversarial early-trajectory worst case):
  CDC_WINS **6.3%**, DEGRADES 76.7%.
- **Heavy tails ×2** (double dump probability — "tool dumps are large" stress test):
  CDC_WINS 30.8%, DEGRADES 36.5% (roughly stable — accumulation offsets bigger dumps).
- **FAIR-TO-CDC — condition on large context (S≥50k, ~39% of injections in long-running agents,
  the regime SWE-ContextBench shows dominates real SWE work at >97% cache-read):**
  CDC_WINS **45.7%**, MID 43.9%, DEGRADES only **10.4%**.

## Honest verdict: **WEAKEN** (with an important conditional caveat)

Across a realistic, evidence-grounded agentic mix, **the median injection is inj/seq ≈ 2.8% — ABOVE the
1% "CDC-wins-big" threshold.** Only **~25% of injections** land in the ≤1% regime; **~37% land in the
>5% degrade regime**; and **~81% of injected TOKENS** are in the degrade regime because large tool
dumps (file reads, code stdout, RAG bundles, JSON datasets) dominate volume. The committee's worry is
**substantially correct**: the unconditional/typical agentic injection is NOT in the regime where CDC's
~2% win holds. The headline "~2% recompute" is a **best-case contour, not the common case** when measured
over realistic tool-result sizes.

**BUT — and this is decision-relevant for the claim's reframe, not a rescue:** CDC's advantage is real and
common *in its proper regime*. Conditioned on **large, long-lived context (≥50k tokens)** — which is
exactly the prefix-cache reuse regime CLAIM-0006 targets, and which SWE-ContextBench shows dominates real
long-horizon agent token usage (>97% cache-read) — **CDC wins (≤1%) on 46% of injections and degrades on
only 10%.** So the right framing is conditional on BOTH (a) growing/large context AND (b) bounded tool-result
size; small status/tool-result injections into a large reused context are the genuine common win, while
large dumps into modest context are the genuine common loss.

**Net effect on CLAIM-0006:** WEAKEN the unconditional/typical-case framing (the ≤1% regime is a minority,
~25%, of all agentic injections; median is ~2.8%). The conditional claim survives only when explicitly
gated on large reused context + bounded injection — and even there ~1 in 10 injections degrades. The
committee crux ("cherry-picked corner?") is **largely vindicated for the general case** and only partially
rebutted for the large-context sub-regime.

## Caveats / limits (do not overclaim)
- **PROXY:** token counts, not measured KV wall-clock. EXP-0002 validated proxy→recompute mapping; this
  inherits that scope (count model, single confound chain).
- **Distribution is modeled, not sampled from a live agent trace corpus.** Sizes are cited point/range
  anchors fitted into plausible mixtures; the true production mix could shift fractions ±10pp. The
  qualitative conclusion (median > 1%, dumps dominate token volume, large-ctx is CDC's real regime) is
  robust across all three sensitivities.
- Tool-type mix weights are an estimate; small_status share (6%) materially affects the win fraction.
- Compaction modeled as a hard halving at 1M; real compaction is gradual.

## Reproduce
`/usr/bin/python3 impl/exp0005_workload_realism.py` → `/tmp/exp0005_workload.json`
(copied to `experiment_result/results.json`). Deterministic seed 20260531.
