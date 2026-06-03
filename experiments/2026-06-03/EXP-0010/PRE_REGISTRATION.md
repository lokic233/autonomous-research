# PRE-REGISTRATION — EXP-0010 (L0, CPU-only, stdlib-only, SERIAL)

**Claim CLAIM-0008:** In long-horizon tool-calling agents, extractively COMPRESSING
committed tool-result segments in the running transcript (retaining only spans that later
turns actually reference, detected by attention/citation signal) reduces prompt token
growth with BOUNDED task-accuracy loss, achieving a strictly better context-length /
task-success Pareto than (a) no compression and (b) naive recency-truncation, because tool
outputs are verbose but later-referenced content is sparse and predictable.

**Pre-registered BEFORE any runs.** Honest pipeline: negative/partial results are WINS.

## 0. THE CRUX (make-or-break, pre-committed)
"Retain only spans later turns reference" requires KNOWING future references. We model BOTH:
- **ORACLE compressor** — knows exactly which prior spans future turns will cite. Upper
  bound on achievable Pareto. NOT a realizable policy.
- **CAUSAL predictor** — predicts which spans WILL be referenced using ONLY past signal
  (which spans have been referenced so far, recency, span salience). The realistic policy.

**The claim HOLDS only if the CAUSAL predictor beats naive recency-truncation on the
(context-length, task-success) Pareto.** The oracle merely bounds the headroom. We quantify
the oracle-vs-causal gap explicitly. If the causal predictor needs oracle future-reference
knowledge to win → NEGATIVE.

## 1. Trace model (synthetic long-horizon agent)
- A trace has T turns. Turn t appends a TOOL-RESULT segment of `verbosity` tokens
  (parameterize VERBOSITY ∈ {64,256,1024} mean tokens, geometric jitter).
- Each tool-result is partitioned into SPANS of `span_len` tokens (span = the atomic unit
  of extractive compression; e.g. a paragraph/line/JSON field). A turn's result has
  ceil(verbosity/span_len) spans.
- LATER-REFERENCE process (the sparsity+predictability crux): at each turn t>warmup, the
  turn "references" a SPARSE subset of spans from PRIOR turns' tool-results. Number of
  referenced spans ~ Poisson(ref_rate). WHICH spans get referenced is governed by:
    - REFERENCE SPARSITY `ref_density` ∈ {0.02, 0.08, 0.25} = fraction of all prior spans
      that ever get referenced over the whole trace (low = sparse = claim-favorable).
    - PREDICTABILITY/LOCALITY: a referenced span is drawn with probability mixing
      (i) RECENCY bias (geometric over turn-distance, weight `w_rec`),
      (ii) SALIENCE: each span has a latent salience score; high-salience spans are more
           likely to be referenced (weight `w_sal`), AND salience is OBSERVABLE to the
           causal predictor (proxy for attention/keyword/citation signal),
      (iii) REPEAT-REFERENCE: a span referenced once is more likely to be referenced again
            (weight `w_rep`) — this is the signal the causal predictor exploits.
    - PREDICTABILITY knob `predictability` ∈ {low,med,high} sets how much of the reference
      mass is explained by observable salience+repeat vs unpredictable uniform noise.
      low → references are ~random (claim-hostile); high → references concentrate on
      observable-salient/repeated spans (claim-favorable).

## 2. Context budget & policies (4 arms)
At each turn, BEFORE generating, the running context = system + all retained spans so far +
new tool-result. A `budget` (max context tokens) is enforced (sweep budget as fraction of
the no-compression peak). Policies decide which prior spans to RETAIN when over budget:
- **A. no-compression (NC):** retain everything. Context grows unbounded (the baseline that
  always has every referenced span present → task-success ceiling, token cost ceiling).
  When NC exceeds budget it simply OVERFLOWS (we report its token growth; for Pareto it sits
  at max-tokens, success=1.0 minus any hard-context-limit failures — for L0 NC never drops).
- **B. recency-truncation (RT):** drop OLDEST spans first to fit budget (StreamingLLM-style).
  Loses early referenced spans.
- **C. extractive-causal (EC):** score every retained span by the CAUSAL predictor
  (observable salience + times-referenced-so-far + recency) and keep the top-scoring spans
  that fit the budget. Realistic policy.
- **D. extractive-oracle (EO):** keep exactly the spans that SOME future turn will reference
  (within budget; if referenced spans exceed budget, keep the soonest-referenced). Upper bound.

## 3. Task-success metric
- **task-success = fraction of (turn, referenced-span) demands that are SATISFIED**, i.e.
  the referenced span is still PRESENT in the context at the turn that references it.
  A reference to an evicted span = a miss (the agent can't see the content it needs).
  This operationalizes "task accuracy" as referenced-content availability — the cleanest
  L0 proxy. Reported per trace, averaged over seeds.
- **context-tokens** = mean (or peak) running context size in tokens over the trace.

## 4. Sweep
- VERBOSITY ∈ {64,256,1024}
- ref_density ∈ {0.02, 0.08, 0.25}   (sparsity)
- predictability ∈ {low, med, high}
- budget_frac ∈ {0.25, 0.5, 0.75} of NC peak tokens (the context-length axis)
- T = 60 turns, span_len = 32 tok, warmup = 5, ref_rate = 3
- seeds: 8 (>=5 required)
- Total cells: 3*3*3*3 = 81 configs * 8 seeds = 648 traces * 4 policies. SERIAL, stdlib only.

## 5. Primary analysis
- **(context-tokens, task-success) Pareto** for all 4 policies, per regime.
- **Primary metric:** context-tokens SAVED vs NC at a FIXED task-success-loss budget
  (e.g. success >= 0.95 of NC's success). For each policy find the min context-tokens
  achieving the success-loss budget; compare EC vs RT vs EO.
- **THE oracle-vs-causal gap:** at matched budget, EO.success - EC.success and the
  token-savings gap. Does EC (causal) still dominate RT (truncation)?
- Paired-by-seed: report mean delta + a bootstrap-style spread (stdlib random resampling).

## 6. Honest verdicts (pre-committed)
- **HELD:** EC (causal) strictly dominates RT on the (tokens, success) Pareto across the
  claim-favorable regime (sparse + predictable references), with the dominance robust
  across seeds; oracle gap finite (causal captures a real fraction of oracle headroom).
- **PARTIAL/CONDITIONAL:** EC beats RT only in some regime (e.g. only high-predictability
  or only low-density) — report exactly which, and that the win is regime-gated.
- **NEGATIVE (a WIN to report):** ANY of:
    (N1) referenced-span content is NOT sparse/predictable in the regime that matters →
         no extractive policy can beat RT;
    (N2) EC (causal) does NOT beat RT on the Pareto (truncation is already near-Pareto);
    (N3) the predictor needs ORACLE future-reference knowledge to win — i.e. EO beats RT
         but EC ≈ RT (the causal-oracle gap is the whole effect). This is the most
         important negative: the mechanism is real but UNREALIZABLE causally.

## 7. Scope / prior-art caveat (pre-committed)
Context compression is a CROWDED field: LLMLingua (prompt compression), H2O / SnapKV
(KV-cache eviction by attention), StreamingLLM (recency+sink truncation). This L0 isolates
the TOOL-RESULT-specific + CAUSAL-reference-prediction angle in a trace SIMULATION; it does
NOT run a real model or measure real task accuracy. A GPU/real-model pass is OWED (see
RESULTS.md "what a GPU pass should measure"). The salience signal here is a synthetic proxy
for real attention/citation signal; the realizability of the causal predictor on REAL
attention is the open question this L0 only brackets.
