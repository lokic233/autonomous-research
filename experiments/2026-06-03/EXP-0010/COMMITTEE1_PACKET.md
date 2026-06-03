# COMMITTEE#1 — CLAIM-0008 (PROJ-0002), evidence EXP-0010 (L0)
## This is the first HELD L0 (effect=support). The make-or-break control (oracle vs causal predictor) came back FOR the claim: causal predictor MATCHES the oracle in the sparse+predictable regime (gap CI [0,0]), beats recency-truncation in 633/648 cells (CI [+0.275,+0.307] excludes 0), honest-negative N3 ('needs oracle') REFUTED. Vote HONESTLY and HOSTILELY — this is a green-candidate, so scrutinize hard. If candidate-grade, name SPECIFIC GPU/real-model required_evidence (researcher: real attention/citation signal as the causal predictor + real task accuracy on a tool-agent benchmark + verify sparsity/predictability hold on REAL tool outputs). novelty_killer: context/KV compression is CROWDED (LLMLingua, H2O, SnapKV, StreamingLLM=the RT arm) — live >=2-source sweep OWED; the ONLY distinct angle claimed is (a) tool-result-specific + (b) retention-as-causal-future-reference-prediction with the oracle gap quantified. Isolate our contribution vs the compression mechanism itself.

## CLAIM
claim: In long-horizon tool-calling agents, extractively COMPRESSING committed tool-result
  segments in the running transcript (retaining only the spans that later turns actually
  reference, detected by attention/citation signal) reduces prompt token growth with
  BOUNDED task-accuracy loss, achieving a strictly better context-length / task-success
  Pareto than (a) no compression and (b) naive recency-truncation, because tool outputs
  are verbose but later-referenced content is sparse and predictable.
why_it_matters: "Agent transcripts blow up by appending verbose tool outputs; most\

## L0 RESULTS (EXP-0010, effect=support, HELD-in-sim)
# RESULTS — EXP-0010 (L0, CPU-only, stdlib-only, SERIAL) — CLAIM-0008

**Claim:** In long-horizon tool-calling agents, extractively COMPRESSING committed
tool-result segments (retaining only spans later turns reference, detected by
attention/citation signal) reduces prompt-token growth with BOUNDED task-accuracy loss,
beating both no-compression and naive recency-truncation on the (context-length,
task-success) Pareto, because tool outputs are verbose but later-referenced content is
sparse and predictable.

**Verdict: HELD (in simulation), with one honest scope caveat.** A *realizable CAUSAL*
extractive predictor (using only past reference/salience/recency signal — no future
knowledge) strictly dominates naive recency-truncation on the (tokens, success) Pareto
across the ENTIRE sweep (633/648 paired cells; bootstrap CI excludes 0), and the
**oracle-vs-causal gap is small overall (+0.027 success) and exactly ZERO in the
claim-favorable regime (sparse + predictable references)**. The make-or-break negative
(N3 — "needs oracle knowledge to win") is REFUTED. This is an L0 trace simulation: a real
attention/citation predictor on a real tool-agent benchmark is OWED (see below).

## Method recap
- Synthetic long-horizon trace: T=60 turns, each appends a verbose TOOL-RESULT (verbosity
  swept), partitioned into SPAN_LEN=32-token spans (the atomic compression unit). Later
  turns reference a SPARSE subset of prior spans; reference probability mixes recency,
  an OBSERVABLE salience score (proxy for attention/citation signal), and repeat-reference.
  Reference SPARSITY (`ref_density`) and PREDICTABILITY (low/med/high — how much reference
  mass is explained by the observable signal) are swept.
- **task-success = fraction of (turn, referenced-span) demands satisfied** = referenced
  span still PRESENT in the (possibly compressed) context at the demanding turn. Cleanest
  L0 proxy for "the agent can still see the content it needs."
- 4 arms, all replay the SAME trace at a per-trace token `budget` (fraction of the
  no-compression peak): **NC** (no compression, ceiling), **RT** (recency-truncation, drop
  oldest), **EC** (extractive-causal: keep top spans by salience + times-referenced-so-far
  + recency — PAST signal only), **EO** (extractive-oracle: keep exactly future-referenced
  spans — upper bound, unrealizable).
- Sweep: verbosity{64,256,1024} × ref_density{0.02,0.08,0.25} × predictability{low,med,high}
  × budget_frac{0.25,0.5,0.75} × 8 seeds = 2592 rows. SERIAL, stdlib-only, **~10s compute**.

## Headline numbers

### The Pareto (success at each context-budget fraction, mean over all configs/seeds)
| budget (frac of NC peak) | NC | RT | **EC (causal)** | EO (oracle) | EC−RT | oracle gap EO−EC |
|---|---|---|---|---|---|---|
| 0.25 | 1.000 | 0.424 | **0.938** | 1.000 | **+0.514** | +0.062 |
| 0.50 | 1.000 | 0.711 | **0.985** | 1.000 | **+0.274** | +0.015 |
| 0.75 | 1.000 | 0.914 | **0.997** | 1.000 | **+0.083** | +0.003 |

EC dominates RT at every budget; the gap is largest where compression bites hardest (tight
budget). At budget 0.25 EC retains 93.8% task-success vs RT's 42.4% — a realizable causal
policy recovers ~92% of the ORACLE's headroom over truncation at the tightest budget.

### Primary metric — context tokens saved at a fixed success-loss budget (success ≥ 0.95·NC)
- **EC needs a LOWER token budget than RT in 201/216 (93.1%) config-seeds; RT beats EC in 0.**
- **EC reaches the 95%-of-NC success bar within budget≤0.75 in 100% of cells; RT in only 23.1%.**
  RT essentially cannot hit a bounded-accuracy-loss target by dropping oldest content,
  because early tool-result spans keep getting referenced.
- Mean min-budget achieving the bar: **EC=0.37, EO=0.25** (oracle gap = 0.12 budget); RT
  fails to reach it in 77% of cells (sentinel).

### THE oracle-vs-causal gap (the make-or-break question)
| | EC−RT (causal beats truncation?) | EO−EC (oracle−causal gap) |
|---|---|---|
| **Overall (648 cells)** | **+0.290**, CI [+0.275,+0.307], wins 633/648 | +0.027, CI [+0.022,+0.032] |
| FAVORABLE (sparse 0.02 + high-pred) | **+0.363**, CI [+0.311,+0.418] | **+0.000**, CI [0,0] |
| HOSTILE (dense 0.25 + low-pred) | +0.135, CI [+0.104,+0.167] | +0.119, CI [+0.091,+0.148] |

**Answer: a realizable causal predictor DOES still beat truncation — decisively — and in
the regime the claim's mechanism predicts (sparse+predictable references) it matches the
oracle EXACTLY (gap = 0).** The oracle-causal gap only opens up in the HOSTILE regime
(dense, low-predictability references), where the references are nearly random and no
observable signal can predict them — and even there EC still beats RT (+0.135). This is the
cleanest possible result for the claim: the headroom the oracle exposes is *fully
capturable causally* precisely when the claim's premise holds.

## Answers to the pre-registered questions
1. **Is referenced-span content sparse & predictable, and does that let extractive beat
   truncation?** Yes. Realized distinct-referenced fraction ≈ ref_density (sparse by
   construction); the sparser and more predictable, the larger EC's win and the smaller the
   oracle gap.
2. **Does the CAUSAL predictor (no future knowledge) beat naive truncation on the Pareto?**
   YES — 633/648 cells, CI excludes 0, at every budget, in every predictability×density bin
   (EC-wins% ranges 91.7–100%).
3. **Does the predictor need ORACLE knowledge to win (negative N3)?** NO — refuted. Oracle
   gap is +0.027 overall and 0.000 in the favorable regime. The causal proxy (salience +
   repeat-reference + recency) captures essentially all the oracle headroom where it matters.
4. **Where does it NOT fully win?** Hostile regime (dense + low-predictability): EC still
   beats RT but leaves a +0.119 oracle gap on the table — the partial-negative boundary,
   exactly as pre-registered. References that are genuinely unpredictable from past signal
   cannot be retained better than oracle by any causal policy.

## Honest caveats & what a GPU / real-model pass should measure
- **This is a TRACE SIMULATION, not a model run.** "task-success" = referenced-span
  availability, a proxy; the salience score is a SYNTHETIC stand-in for real
  attention/citation signal. The realizability question is bracketed, not closed.
- A GPU/real pass should: (1) use **real attention or citation signal** (e.g. H2O/SnapKV-style
  attention mass, or explicit later-turn citations) as the causal reference predictor and
  measure its TRUE predictive AUC for future references; (2) measure **real task accuracy**
  on a tool-agent benchmark (e.g. multi-tool ReAct/SWE/τ-bench traces) under each compression
  policy at matched token budgets; (3) verify the sparsity+predictability assumptions hold on
  REAL tool outputs (this L0 assumes them); (4) re-run the full verbosity×density×budget sweep.
- **PRIOR-ART CAVEAT (crowded field — sweep is OWED):** context/KV compression is dense with
  prior work — **LLMLingua** (prompt compression), **H2O** & **SnapKV** (attention-based
  KV-cache eviction), **StreamingLLM** (recency + attention-sink truncation, ≈ our RT arm).
  This L0's *only* distinct angle is (a) the **TOOL-RESULT-specific** structure (verbose
  outputs, sparse later reference) and (b) framing the retention policy as **causal
  future-reference PREDICTION** with an explicit oracle-vs-causal gap quantified. We do NOT
  claim novelty over the compression mechanism itself; the contribution-vs-prior-art
  isolation is flagged as owed before any L1+ promotion.

## Reproducibility
- `scripts/sim.py` (trace model + policies), `scripts/sweep.py` (serial driver),
  `scripts/analyze.py` (Pareto + primary metric + oracle gap + bootstrap CI).
- `results/sweep_all.csv` (2592 rows). Re-run: `python3 scripts/sweep.py && python3 scripts/analyze.py`.
- stdlib-only, deterministic per seed (seeds 0–7), ~10s wall, SERIAL (no multiprocessing).

## PRE-REG (committed pre-run c1f1a13)
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

## ORCHESTRATOR CAVEAT TO WEIGH: this is a TRACE SIM with a SYNTHETIC salience proxy for attention/citation, and success is an AVAILABILITY proxy (not real task accuracy). Realizability on real attention is BRACKETED, not closed. The sparse+predictable premise is assumed by construction. These are exactly what a GPU/real-model pass must close before any green.
