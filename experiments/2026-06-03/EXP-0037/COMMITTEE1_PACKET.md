# COMMITTEE#1 — CLAIM-0040 (PROJ-0011), evidence EXP-0037 (L0)
## SYSTEMS/latency study, effect=keep-exploring / HELD-PARTIAL. This is the FIRST fresh-axis claim in a long run that did NOT die at L0 — scrutinize it HARD (it's a candidate). Screened against all 3 anti-patterns (not tuned-knob, not KV-reuse, not predictor-vs-logprob); it's a structural-overlap claim with a correctness-safety break-even. Vote honestly. novelty_killer: the latency-OVERLAP is known practice (streaming-LLM, incremental parsing); the CLAIMED novelty is the correctness-safety BREAK-EVEN MAP for SEMANTIC early-commit (p* vs detectability vs rho vs W) + the proven necessity of partial-stream detectability — NOT 'overlap exists'. Distinct from speculative decoding (token-level, lossless, no semantic redo) and from dead CLAIM-0003/EXP-0004 (which prefetched the CALL and needed implausible accuracy where payoff was high — this commits on the partial RESULT and the break-even is FAVORABLE where it matters). Live >=2-source check: does any published work give a correctness-safety break-even for committing on a partial/streaming tool RESULT?

## L0 FINDINGS:
(B) THE HEADLINE — the INVERSE of EXP-0004's trap: break-even p* = W*T_step/((1-d)*T_stream + W*T_step) is LOW (0.07-0.39 at W<=1) EXACTLY in the lucrative regime (rho=T_stream/T_step >= 2, long streamed results); the high-p* cells (rho<=0.5, p* 0.7-0.94) are where there's almost nothing to gain anyway. A mediocre detector (acc~0.75) clears p* in EVERY rho>=2 cell (W<=2). 1064/1260 cells robust-win (all 7 seeds); realistic region (acc 0.7-0.8, f_fl 0.3-0.5): mean +12.1%, high-rho up to +48%. Even acc=0.5 net-positive on average. W=2 + weak detector (acc<=0.7) shrinks to +2.9% but does NOT flip negative. The two MODEL-INTERNAL negative triggers (wrong-commit dominance; implausible-accuracy break-even) did NOT fire.
(A) Detectability is LOAD-BEARING: a BLIND detector (fires at fixed position, no partial-stream signal) wins only 242/540 cells and LOSES to -57% on tail-heavy/low-f_fl. A detector that can't tell front from tail on the partial stream is frequently net-NEGATIVE.

## WHY ONLY PARTIAL (not promotion): the two EMPIRICAL load-bearing unknowns are UNMEASURABLE CPU-only and ARE the L1: (1) the REAL front-loading rate of real tool-result corpora (API/JSON, search/RAG lists, code-exec/test output, DB results, log tails — actual fractional position of actionable content); (2) the REAL partial-stream detector P(correct|fire) + fire-position vs the (low) p*. Plus real rho (win lives at rho>=1), real redo cost W + REVERSIBILITY (side-effecting steps -> W>1/irreversible -> gate early-commit to side-effect-free steps).

## CLAIM
claim: "For agent tool-result re-ingestion, EARLY-COMMITTING the next reasoning step\
  \ on the STREAMING PREFIX of a long tool result (once the front-loaded actionable\
  \ content has arrived, before the full result streams in) reduces end-to-end agent-step\
  \ latency vs serialize-then-read, with a NET win whenever the fraction of results\
  \ that are genuinely front-loaded times the latency saved exceeds the wrong-early-commit\
  \ cost (re-doing the step when the tail actually mattered) \u2014 because real tool\
  \ results are often front-loaded (answer first, boilerplate/pagination after) and\
  \ that structure is detectable from the partial stream."
why_it_matters: "FRESH axis (tool-result streaming early-commit \u2014 untouched by\

## L0 RESULTS (EXP-0037)
# RESULTS — EXP-0037 / CLAIM-0040
**Streaming-prefix early-commit for agent tool-result re-ingestion.**
L0 (CPU-only, stdlib-only, SERIAL, analytic + Monte-Carlo trace sim). 7 seeds, N=2500/cell.
Honest pipeline; negatives are wins. Verdict read from on-disk CSVs (results/).

## VERDICT: PARTIAL / HELD (mechanism positive in a realistic regime; gated on two empirical unknowns L0 cannot settle)

The latency-overlap mechanism is real and **nets out POSITIVE across a broad, realistic region** —
critically, **the break-even does NOT replay the EXP-0004 trap.** But the claim's two falsifiable
parts (A: real front-loading rate; B: real detectability + redo cost) are *empirical* and cannot be
settled CPU-only. So: HELD, with a sharp, falsifiable L1 spec. Not a clean negative, not a promotion.

---

## (A) Front-loading + detectability

We do NOT have a real corpus at L0, so we **assumed** three position regimes (front Beta(1.5,6)≈0.20;
uniform; tail Beta(6,1.5)≈0.80) and swept the front-load fraction f_fl ∈ {0.1..0.9}. We CANNOT
claim a real front-loading rate — that is the #1 thing L1 must measure. What L0 *can* say:

- **Front-load fraction monotonically drives the win** (realistic detector acc≥0.8):
  f_fl=0.1→+9.9%, 0.3→+16.5%, 0.5→+23.0%, 0.7→+29.5%, 0.9→+36.0% step-latency reduction.
- **Detectability is necessary.** BLIND detector ablation (fires at fixed position, no signal from the
  partial stream): only **242/540 cells net-win**, and it LOSES badly on tail-heavy/low-f_fl
  (down to −1.76 absolute, ≈ −57% in the worst smart-equivalent). A detector that cannot distinguish
  front-loaded from tail-heavy on the partial stream is a coin-flip and frequently net-NEGATIVE.
  → **Detectability on the partial stream is the load-bearing assumption.** L1 must measure it directly.

## (B) Net-win break-even — and why it is NOT the EXP-0004 trap

Per-fire break-even (committed in PRE_REG): **p\* = W·T_step / ((1−d)·T_stream + W·T_step)**, where the
detector must achieve P(correct|fire) ≥ p\* to net-win. The decisive finding (results/breakeven.csv):

| regime | p\* (W=1, d=0.2) | gain available |
|---|---|---|
| ρ=T_stream/T_step = 0.25 (stream cheap) | **0.83** (implausible) | tiny (only 0.20·T_step saveable) |
| ρ = 1 | 0.56 | moderate |
| ρ = 2 | 0.39 | large |
| ρ = 4 | **0.24** | large |
| ρ = 8 (long streamed result) | **0.135** | huge |

**This is the OPPOSITE of EXP-0004's failure.** In EXP-0004 (spec tool-CALL prefetch) the break-even
demanded *implausible* accuracy *exactly in the lucrative regime*. Here, p\* is LOW precisely where the
payoff is HIGH (long streamed results, ρ≥2): a mediocre detector (acc≈0.75) clears p\* in **every** ρ≥2
cell we checked (W≤2). The high-p\* cells (ρ≤0.5) are where there's almost nothing to gain anyway —
so a wrong commit there costs little in absolute terms and you'd simply not arm the detector.
Why the difference: early-commit on a long *streamed result* overlaps with a large remaining stream
(gain scales with ρ), whereas prefetching a *call* gambled the whole step on a guess of the call itself.

## Sweep summary (results/sweep_smart.csv, 1260 cells × 7 seeds)

- **Overall:** 1094/1260 cells mean-win; **1064/1260 robust (all 7 seeds win)**.
- **Detector accuracy** (avg over all f_fl,ρ,W,mix): acc 0.5→+3.8%, 0.7→+13.1%, 0.8→+17.8%, 0.9→+22.4%,
  1.0→+27.1%. Win-fraction climbs 0.67→0.90→1.0. **Even acc=0.5 is net-positive on average** because the
  high-ρ cells dominate the gain and the low-ρ losses are bounded.
- **Latency ratio ρ** (acc≥0.8, f_fl≥0.5): ρ=0.25→+8.9%, 1→+25.9%, 4→+42.8%, 8→+47.9%. **Gain scales
  with ρ** — the make-or-break variable alongside f_fl.
- **Wrong-commit penalty W** (low-acc regime acc≤0.7, the stress test): W=0.5→+12.9% (win 0.87),
  W=1→+9.6% (0.74), W=2→+2.9% (0.61). A heavy redo penalty (W=2) erodes most of the edge for a weak
  detector but does **not flip the average negative** — it just shrinks the win region toward high ρ / high f_fl.
- **Where it loses:** f_fl=0.1, tail-heavy, acc=0.5, low ρ, W=2 → −57%. I.e. a blind detector on a
  tail-heavy corpus with expensive redos. Exactly the honest-negative quadrant.
- **Realistic region** (acc∈{0.7,0.8}, f_fl∈{0.3,0.5}, all W/ρ/mix): **121/144 mean-win,
  115 robust, mean +12.1%.**

## Honest-negative branch — which triggers fired?
Of the four pre-registered negative triggers:
1. *Front-loading rare* → **CANNOT confirm/deny at L0** (we assumed it). HELD pending real corpus.
2. *Tails matter too often → wrong-commit dominates* → **did NOT fire** as a blanket negative; only
   in the low-ρ / low-f_fl / W=2 corner, which is also the low-payoff corner.
3. *Break-even needs implausible accuracy in the lucrative regime* → **did NOT fire** (the headline:
   p\* is LOW where payoff is high — the inverse of EXP-0004).
4. *Detector can't tell front from tail on partial stream* → **CANNOT confirm/deny at L0**; the BLIND
   ablation proves detectability is *necessary* (blind ⇒ frequent net-loss), but whether a real
   detector achieves the (easily-clearable) p\* on real partial streams is an L1 measurement.

→ **Two of four triggers are empirical (A's corpus + detectability) and unresolved CPU-only.** The two
*model-internal* triggers (wrong-commit dominance, implausible-accuracy break-even) did NOT fire. Hence
HELD, not negative: the math is favorable; the empirics are unmeasured.

## What a real L1 must measure (the binding constraints)
1. **Real front-loading rate (A).** Mine real tool-result corpora — API/JSON responses, search/RAG
   result lists, code-exec/test output, DB query results, log tails — and measure the *actual* fractional
   position of the actionable content the agent's next step depends on. Is f_fl realistically ≥0.3?
2. **Real detectability (B).** Train/probe a cheap detector on partial streams; measure its true
   P(correct|fire) and where it fires (d). Compare against the (low) p\* this experiment computed.
3. **Real ρ = T_stream/T_step.** Measure streamed-tool-result wall time vs next-step generation latency
   for actual agent loops. The win lives at ρ≥1; if real tool results stream fast (ρ≪1), the addressable
   gain shrinks regardless of detector quality.
4. **Real redo cost W.** A wrong early step may have *side effects* (tool calls, edits) → W>1 and possibly
   irreversible. Measure W empirically and whether wrong commits are safely *reversible* (if not, gate
   early-commit to side-effect-free steps only).

## Prior-art caveat (committed in PRE_REG)
- **Speculative decoding** (token-level, lossless verify): different — lossless, no *semantic* redo;
  here a wrong commit is a real semantic redo with a penalty.
- **Dead CLAIM-0003 / EXP-0004** (speculative tool-CALL prefetch): same break-even *structure*, opposite
  outcome — that one prefetched the *call* and the break-even demanded implausible accuracy in the
  lucrative regime; THIS commits on the partial *result* and the break-even is favorable where it matters.
- **Streaming-LLM / incremental parsing:** the latency *overlap* mechanism overlaps with known practice;
  our contribution is the **correctness-safety break-even for SEMANTIC early-commit** (p\* vs detectability
  vs ρ vs W), not the overlap itself. Be honest: the novelty is the break-even map + the detectability
  necessity, not "overlap exists".

## Reproducibility
- `sim_early_commit.py` (stdlib only) → results/sweep_smart.csv, sweep_blind.csv, breakeven.csv
- `analyze.py` → logs/analysis.log. Seeds {0..6}. Run serial, <1 min wall.

## PRE-REG
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

## ORCHESTRATOR NOTE: if candidate-grade, the L1 ask = real tool-result corpora front-loading measurement + a real partial-stream detector's P(correct|fire) + real rho/W/reversibility. Consider whether a CHEAP follow-up (front-loading measurement on a real corpus, no GPU) gates the full L1 (the cost-aware-gating lesson).
