# RESULTS — EXP-0035 / CLAIM-0038
researcher-0035 | L0 CPU-only stdlib-only SERIAL | honest pipeline. Verdict: **NEGATIVE (relabeling collapse).**

## TL;DR
The pre-call schema-overlap signal is a WEAK predictor of wrong-tool-selection (AUC ~0.48–0.56,
barely above chance), it is DOMINATED by a generic prompt-difficulty predictor, and it ADDS NOTHING
beyond the agent's own self-logprob — in most cells it HURTS. **The claim COLLAPSES to relabeling**:
the schema-geometry "confusability" signal is just a noisier, weaker re-expression of information the
generic difficulty predictor and the agent's own confidence already carry better. This is exactly the
CLAIM-0015/0037 failure mode the claim was designed to avoid — and it failed the bar. Reported honestly.

## What was measured (anti-circular by construction)
Label y (wrong-tool-selection) generated from LATENT confusability c + intrinsic difficulty d, NEVER
from schema tokens. The schema predictor reads ONLY observable lexical schema overlap (bag-cosine of
name+desc+param tokens) — a NOISY proxy of c. Generic-difficulty predictor reads a noisy readout of d
only. Agent self-logprob is a separate noisy readout of BOTH c and d (its felt confidence) + noise.
Oracle reads true latent c (ceiling). Sweep: K∈{3,6,12}, coupling rho∈{0,0.5}, logprob-noise
σ∈{0.5,1.5}, 5 seeds/cell, N=4000/seed, bootstrap B=400 on the two key deltas.
ENV CAVEAT: no numpy/transformers on this Mac → schema overlap is LEXICAL/HASHED, not a neural
embedding. L1 must redo with real schema embeddings. (Stated, per pre-reg.)

## (A) Schema-predictability answer
- **AUC(schema_max) ≈ 0.48–0.56** across all cells (cells.csv). On the cleanest cells (rho=0, low σ):
  K=3 ≈0.55, K=6 ≈0.50, K=12 ≈0.50. At K≥6 it is at or BELOW chance.
- **Oracle AUC(true c) ≈ 0.68–0.73.** So there IS latent confusability signal — but the lexical schema
  proxy recovers almost none of it. **Oracle gap is huge (~0.18–0.23 AUC):** the pre-call lexical
  schema geometry is a very lossy readout of true confusability.
- Decision-rule threshold (AUC_schema_max > 0.55 on rho=0 cells) is met ONLY at K=3, FAILS at K=6/12.
  => Even part (A) is, at best, marginal-and-fragile, and fails for realistic toolset sizes.

## (B) Beats random + difficulty? Adds beyond self-logprob? (bootstrap.csv, 95% CIs)
- **vs RANDOM:** schema ~0.50–0.56 vs random ~0.50. Marginal at best; not at K≥6.
- **vs GENERIC DIFFICULTY: FAILS in EVERY cell.** delta(schema − difficulty) is NEGATIVE everywhere,
  CI entirely below 0 (e.g. K=6,rho=0.5,σ=1.5: −0.202 [−0.230,−0.174]; K=3,rho=0,σ=0.5: −0.052
  [−0.083,−0.023]). A generic difficulty predictor beats schema-overlap decisively, always.
- **ADDS BEYOND SELF-LOGPROB: NO.** delta-AUC (combo[−logprob+schema] − logprob-only) is ≤0 in 11/12
  pooled cells; CI upper bound < 0 (schema strictly HURTS) in 7/12 cells (e.g. K=12,rho=0.5,σ=0.5:
  −0.043 [−0.059,−0.028]; K=6,rho=0,σ=0.5: −0.040 [−0.057,−0.024]). The ONLY cells where the CI
  even touches 0 are the high-logprob-noise (σ=1.5, rho=0) cells where the agent's own confidence is
  artificially degraded — and even there the point estimate is ~+0.01 with CI straddling 0. Under any
  realistic (calibrated) self-logprob, schema-overlap adds NOTHING.

## Verdict (pre-committed rule) → NEGATIVE
ALL three HELD conditions fail: schema AUC only marginal/sub-chance at K≥6; it does NOT beat generic
difficulty (CI<0 everywhere); it does NOT add beyond self-logprob (CI≤0, often strictly <0).
This is **relabeling**: the cheap schema-geometry signal is dominated by both a generic difficulty
predictor and the agent's own logprob. The load-bearing anti-relabeling bar (CLAIM-0015/0037 lesson)
is FAILED. NEGATIVE is the honest finding — and a WIN for the pipeline.

## Why (mechanism, not just numbers)
Lexical schema overlap is a lossy readout of latent confusability (oracle gap ~0.2 AUC), AND
confusability is only one of two error drivers; intrinsic difficulty d drives error at least as
strongly (bd=1.8 vs bc=2.6 but d is recovered cleanly by the difficulty predictor while c is recovered
poorly by lexical overlap). The agent's self-logprob already integrates BOTH c and d, so it strictly
dominates the noisy single-factor schema proxy. Even with a real embedding (L1), the agent's own
logprob would still see confusability the schema sees — the bar is whether schema sees it the agent
CANNOT, which this analytic model says it does not under realistic calibration.

## What a real L1 should measure
Real tool-calling benchmark — BFCL-multiple / ToolBench / Gorilla-API: (1) real schema embeddings
(sentence-transformers / model embeddings of name+desc+params), (2) real wrong-tool-selection labels
from ground-truth tool, (3) the agent's REAL tool-choice logprob/confidence. Then the exact same three
tests: AUC(schema_max) vs random vs generic-difficulty-predictor (e.g. prompt-length/perplexity), AND
delta-AUC of schema added to a logprob model. The L0 prediction is that schema-overlap will NOT add
beyond the agent's own logprob on calibrated models — L1 should try to falsify that.

## Prior-art caveat
Tool RETRIEVAL (ToolLLM, Gorilla, ToolBench) retrieves relevant tools; confusable-tool /
tool-disambiguation work and LLM-as-judge exist; tool-selection-error is published. The intended
novelty was the PRE-CALL SCHEMA-GEOMETRY confusability signal as a selection-ERROR predictor that adds
beyond self-logprob. The L0 result is that this incremental-over-logprob novelty does NOT hold
(relabeling). Tool selection itself is not novel and we never claimed it.

## Artifacts
- PRE_REGISTRATION.md (committed before run)
- run_exp.py (generative model + per-cell AUCs)   -> results/cells.csv (60 rows: 12 cells x 5 seeds)
- boot.py (pooled bootstrap CIs)                   -> results/bootstrap.csv (12 cells)
- logs/run.log, logs/boot.log
