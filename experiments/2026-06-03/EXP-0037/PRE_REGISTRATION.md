# PRE_REGISTRATION — EXP-0037 / CLAIM-0040
**Researcher:** researcher-0037 | **Task:** TASK-0029 | **Project:** PROJ-0011
**Level:** L0 (CPU-only, stdlib-only, SERIAL, analytic + trace-sim). Budget ≤15 min.
**Committed BEFORE any results are computed.**

## THE CLAIM (CLAIM-0040)
For agent tool-result re-ingestion, EARLY-COMMITTING the next reasoning step on the
STREAMING PREFIX of a long tool result (once front-loaded actionable content has arrived,
before the full result streams in) reduces end-to-end agent-step latency vs serialize-then-read,
with a NET win whenever (fraction of front-loaded results) × (latency saved) exceeds the
wrong-early-commit cost (re-doing the step when the tail actually mattered).

## TWO FALSIFIABLE PARTS
- **(A)** Are real tool results actually FRONT-LOADED (actionable content in the prefix,
  boilerplate/pagination in the tail) at a meaningful rate? And is front-loaded distinguishable
  from tail-heavy on the PARTIAL stream (detectability)?
- **(B)** Is early-commit a NET latency win once the wrong-early-commit cost (redo when the
  tail mattered) is charged?

## FAILURE-MODE SCREEN (committed)
- NOT a Jensen-floor tuned-knob (no convexity-of-an-average artifact; we model discrete
  commit/no-commit outcomes with explicit penalty).
- NOT a RoPE-wall KV-reuse claim (no positional reuse; this is latency overlap).
- NOT a predictor-vs-own-logprob relabeling (the detector reads the partial STREAM bytes/tokens,
  not the model's own confidence relabeled as truth).
- It IS a systems/latency-overlap claim with a correctness-safety break-even.
- PRIOR ART confronted head-on (EXP-0004 lesson, speculative tool-call prefetch): the break-even
  p* = penalty/(gain+penalty) often demands implausible correctness in the lucrative regime.
  We compute p* explicitly and ask whether the required detector accuracy is plausible.

## MODEL (committed)

### Tool-result content model
- Result length L (tokens). Streams at rate r tok/s → full stream time T_stream = L/r.
- "Actionable content" sits at fractional position q ∈ [0,1] in the result; absolute pos = q·L.
  The reasoning step needs ALL content up to and including q to be correct.
- Three position regimes (we sweep mixtures):
  - FRONT-LOADED: q ~ Beta(a=1.5, b=6)  (mean ≈ 0.20) — answer early, tail is boilerplate/pagination.
  - UNIFORM: q ~ Uniform(0,1).
  - TAIL-HEAVY: q ~ Beta(a=6, b=1.5) (mean ≈ 0.80) — answer late (e.g. final summary / last row).
- A result is "effectively front-loaded" if q ≤ q_fl_thresh (default 0.4): enough of the answer is
  in the prefix that committing on the prefix CAN be correct.
- Mixture parameter f_fl = fraction of results drawn from FRONT-LOADED regime (the rest split
  between uniform and tail-heavy per a mix vector). Swept.

### Latency model (per agent step)
- T_step = reasoning/generation latency of the next step (model forward), independent of stream.
- Baseline (serialize-then-read): wait for full stream THEN run step.
    L_base = T_stream + T_step.
- Early-commit: a detector watches the partial stream. It FIRES at fractional position d ∈ [0,1]
  (detector's belief that actionable content has arrived). On fire, step starts immediately,
  overlapping with the remaining stream.
  - The step's WALL time is still T_step, started at d·T_stream.
  - CORRECT early-commit (d ≥ q, i.e. the actual answer position was already streamed when we fired):
    L_early = max(d·T_stream + T_step, T_stream)
      (step overlaps the tail; finish when both step done AND stream done — but on a correct
       commit we don't need the tail, so completion = d·T_stream + T_step, EXCEPT we still must
       have received up to q; since d≥q that's satisfied by d·T_stream. We DO NOT wait for full
       stream on a correct commit because the tail is boilerplate.)
    → L_early_correct = d·T_stream + T_step.   (latency SAVED = (1-d)·T_stream vs baseline.)
  - WRONG early-commit (d < q: we fired before the answer arrived; the tail mattered):
    the step ran on incomplete content → it is WRONG → must REDO after full stream.
    L_early_wrong = d·T_stream            (wasted partial step, but we detect wrongness only
                    + W·T_step            after full stream arrives; W = wasted-work weight ≥0)
                    + T_stream            (we still finish streaming)
                    + T_step.             (redo the step on full result)
    Simplify (since d·T_stream < T_stream): the redo dominates.
    → L_early_wrong = T_stream + T_step + W·T_step  = L_base + W·T_step.
       i.e. wrong-commit costs an EXTRA W·T_step over baseline (the wasted speculative step).
       W = wrong-commit penalty weight (swept; W=1 means the wasted step fully duplicated cost;
       W can be >1 if a wrong step has side effects / extra recovery, or <1 if partially salvageable).

### Detector model
- Detector fires at position d. Detection has error. Model the detector as: it estimates q̂ from
  the partial stream and fires when its running estimate says "answer arrived", with accuracy:
  - With probability that depends on a detector skill parameter, it fires CORRECTLY (d ≥ q) on
    front-loaded results and HOLDS (waits for full stream = baseline) on tail-heavy results.
  - We parameterize by detector accuracy `acc` ∈ [0.5,1.0]: P(detector classifies a given result's
    prefix correctly as "answer present" vs "not yet"). On a front-loaded result, a correct
    classification → fire at d ≈ q+ε (just after answer) and WIN; a wrong classification →
    fire too early (d<q) → WRONG-commit, OR fail to fire → fall back to baseline (no win, no loss).
  - DETECTABILITY ablation: can the detector even distinguish front-loaded from tail-heavy on the
    partial stream? We model a "blind" detector (acc=0.5, fires at fixed d regardless) vs an
    "oracle" (acc=1.0) and sweep between.

### Early-commit POLICY (committed)
- Conservative detector: only fire when running-estimate confidence ≥ threshold τ. Higher τ →
  fires later (larger d, less savings) but fewer wrong-commits. We treat the operating point as
  (d_fire, acc) pairs and sweep.

### Per-result expected latency under early-commit (decision tree)
For a result with true position q and detector outcome:
- detector FIRES (prob p_fire) at d:
    - if d ≥ q: WIN, latency = d·T_stream + T_step
    - if d < q: WRONG, latency = L_base + W·T_step
- detector HOLDS (prob 1-p_fire): baseline, latency = L_base.
Aggregate over the result mixture and detector accuracy.

### Net win metric
ΔL = L_base − E[L_early]  (positive = early-commit wins). Also report % step-latency reduction.

### Break-even (THE crux, EXP-0004 lesson)
Per-fire decision: gain on correct = G = (1−d)·T_stream (saved tail stream time).
Penalty on wrong = P = W·T_step (extra wasted step).
For firing to be worthwhile in expectation, need:
   P(correct | fired) · G  >  P(wrong | fired) · P
Break-even correctness among fires:
   p* = P / (G + P) = W·T_step / ((1−d)·T_stream + W·T_step).
We compute p* across the latency ratio ρ = T_stream/T_step and W, then ask: is the achievable
detector P(correct|fire) ≥ p* in the lucrative (high-ρ, front-loaded) regime? (EXP-0004's exact
trap: p* may demand implausible accuracy.)

## SWEEPS (committed)
- f_fl (front-load fraction): {0.1, 0.3, 0.5, 0.7, 0.9}
- mix of the non-front-loaded remainder: {uniform-heavy, tail-heavy} (2 mixes)
- detector acc: {0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0}
- d_fire (where detector fires on a positive): tied to q (q+ε) for "smart", or fixed {0.2,0.3,0.5} for "blind"
- latency ratio ρ = T_stream/T_step: {0.25, 0.5, 1, 2, 4, 8}  (stream vs step cost)
- W (wrong-commit penalty weight): {0.5, 1.0, 2.0}
- SEEDS: 7 (≥5 required): {0,1,2,3,4,5,6}
- N results per cell: 4000

## HONEST-NEGATIVE BRANCH (committed BEFORE running)
Report a NEGATIVE if ANY of:
1. Front-loading is RARE in realistic tool-result mixes (if realistic f_fl is low, the addressable
   market is small).
2. Tails matter too often → wrong-commit cost dominates (ΔL ≤ 0 across the realistic region).
3. The break-even front-load-fraction × detectability is implausibly high (required detector
   P(correct|fire) ≥ p* demands accuracy not plausibly achievable from a partial byte stream).
4. A detector CANNOT tell front-loaded from tail-heavy on the partial stream (detectability ablation
   shows acc collapses to ~0.5 → no usable signal → no net win).
PASS only if there is a realistic region (plausible f_fl, plausible detector acc) with ΔL>0
robustly across seeds.

## DELIVERABLES
- results/*.csv (raw sweep, per-cell ΔL + breakeven), logs/, RESULTS.md.
- ros exp complete --claim CLAIM-0040 --exp EXP-0037 --effect <honest>.

## PRIOR-ART CAVEAT (committed)
- Speculative decoding (token-level, LOSSLESS verify) — different: lossless, no semantic redo.
- Dead CLAIM-0003 / EXP-0004 (speculative tool-CALL prefetch): prefetched the CALL; THIS commits
  on the partial RESULT. Same break-even-trap structure applies.
- Streaming-LLM / incremental parsing: overlap exists in practice; our contribution is the
  correctness-safety break-even for SEMANTIC early-commit, not lossless parsing. Be honest about overlap.
