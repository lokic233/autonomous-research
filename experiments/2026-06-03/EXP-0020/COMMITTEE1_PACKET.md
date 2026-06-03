# COMMITTEE#1 — CLAIM-0015 (PROJ-0004), evidence EXP-0020 (L0)
## MEASUREMENT study, effect=weaken / PARTIAL. Anti-circular (GT degradation from a LATENT s_i the predictor NEVER reads — heeds the CLAIM-0008 lesson). The STRONG baseline (confidence-threshold cascade @ matched escalation budget) was used, NOT a strawman: the router only TIES it at low noise (bootstrap CI includes 0) and wins modestly (<=2.4% quality) only when post-decode confidence is >= as noisy as pre-decode features; NEVER loses. The researcher reframes the real win as COST (route before any decode -> avoid the cheap decode), not quality. Vote honestly. novelty_killer: routing/cascades ARE published (RouteLLM, FrugalGPT, LLM-Blender, Tabi, hybrid-precision serving) — gate on generic difficulty/confidence; the NARROW claimed novelty is QUANT-SENSITIVITY-specific PRE-decode prediction (route on predicted quantization degradation specifically, before any decode). Live >=2-source sweep: does any published router gate specifically on predicted quantization-sensitivity pre-decode? If candidate-grade, the L1 ask: REAL 4-bit (GPTQ/AWQ) vs full model on the SAME real prompts -> real per-request degradation (is it heavy-tailed? claim dies if uniform); real pre-decode-feature AUC; real quant-model confidence as the post-decode baseline; real FLOPs/$ cost accounting.

## CLAIM
claim: "In a mixed-precision serving fleet (a cheap low-bit-quantized model + an expensive\
  \ full-precision model), a cheap PRE-GENERATION router that predicts per-request\
  \ whether low-bit quantization will materially degrade THIS request's output (from\
  \ features available before decode: prompt perplexity, domain/topic, presence of\
  \ exact-arithmetic or long-context-reasoning markers) can route only the quant-sensitive\
  \ requests to the expensive model \u2014 achieving a strictly better cost/quality\
  \ Pareto than (a) all-quant, (b) all-full, and (c) random/confidence-threshold routing\
  \ at matched escalation budget, because quantization error is request-dependent\
  \ and predictable from cheap pre-decode signals."
why_it_matters: "NEW axis (quantization-error-aware request ROUTING \u2014 untouched\

## L0 RESULTS (EXP-0020)
# RESULTS — EXP-0020 / CLAIM-0015
## Quant-sensitivity PRE-decode router (L0 analytic/trace sim; CPU-only, stdlib, SERIAL)

VERDICT: **PARTIAL** (conditionally held; strong-baseline edge is modest & noise-dependent).

L0 caveat: this is a SIMULATION with a synthetic latent quant-sensitivity model, NOT real
quant-vs-full model outputs. It tests the LOGIC of the claim (predictability + Pareto-vs-baselines),
not its real-world magnitude. See "What a real L1 must measure".

---

## (A) Is per-request quant-degradation predictable from cheap PRE-decode features?

Anti-circularity (the lesson that RED'd CLAIM-0008): ground-truth degradation d_i is generated
from a LATENT scalar s_i. The predictor (logistic regression) reads ONLY noisy PRE-decode
correlates of s_i (prompt perplexity, domain tag, arith/long-ctx markers) — NEVER s_i or d_i.

Predictor AUC for "materially degraded" label (top-30% degradation), 5 seeds, N=2000
(results/predictability.csv):

| regime              | sigma_obs | AUC mean | AUC range       |
|---------------------|-----------|----------|-----------------|
| request_dependent   | 0.05      | 0.994    | 0.993–0.994     |
| request_dependent   | 0.15      | 0.955    | 0.951–0.962     |
| request_dependent   | 0.30      | 0.886    | 0.874–0.901     |
| request_dependent   | 0.60      | 0.810    | 0.793–0.834     |
| request_dependent   | 1.00      | 0.769    | 0.755–0.794     |
| uniform (null)      | 0.05–1.0  | ~0.52    | 0.51–0.53       |

ANSWER: YES — predictable from PRE-decode features WHEN degradation is request-dependent
(heavy-tailed in the latent), with realistic-noise AUC 0.77–0.89. In the UNIFORM null regime
(degradation independent of request) AUC collapses to chance (~0.52) as pre-committed —
nothing to predict, nothing to route. Anti-circular: predictor never reads the generative cause.

ORACLE GAP (results/pareto.csv, request_dependent sigma=0.3, quality at b):
 b=0.2: router 0.852 vs oracle 0.885 (gap 0.033); b=0.5: router 0.953 vs oracle 0.976 (gap 0.023).
The achievable router captures most of the oracle's routing value but leaves a real gap that
WIDENS with observation noise.

---

## (B) Cost/quality Pareto vs ALL baselines (matched escalation budget b)

Endpoints (request_dependent, sigma=0.3): all-quant=0.733 (b=0, cheapest),
all-full=0.999 (b=1, most expensive). Quality at matched b, mean over 5 seeds:

request_dependent, sigma=0.3:
| b    | router | conf-thresh | random | oracle | router−conf | router−random |
|------|--------|-------------|--------|--------|-------------|---------------|
| 0.05 | 0.7670 | 0.7661      | 0.7464 | 0.7802 | +0.0009     | +0.0206       |
| 0.10 | 0.7984 | 0.7957      | 0.7590 | 0.8210 | +0.0027     | +0.0394       |
| 0.20 | 0.8518 | 0.8444      | 0.7857 | 0.8846 | +0.0075     | +0.0662       |
| 0.30 | 0.8939 | 0.8843      | 0.8125 | 0.9283 | +0.0096     | +0.0813       |
| 0.50 | 0.9529 | 0.9438      | 0.8640 | 0.9756 | +0.0092     | +0.0889       |

request_dependent, sigma=0.6 (noisier observables): router−conf grows to +0.016 .. +0.024.

uniform (null): all policies collapse onto each other (router−conf ≈ 0.000–0.001); only
random/oracle bracket trivially. As pre-committed, NO routing helps when degradation is uniform.

- vs all-quant / all-full: router DOMINATES both endpoints (strictly Pareto-better) ✅ in
  request_dependent regime — it lifts quality above all-quant at any b < 1 and reaches all-full
  faster (per unit escalation) than random.
- vs random@matched-b: router beats it decisively (+0.02 to +0.09 quality) ✅.
- vs CONFIDENCE-THRESHOLD@matched-b (the STRONG baseline): router wins, but the margin is
  MODEST and noise-dependent. Bootstrap CI on per-request quality delta @ b=0.2
  (1000 resamples, results/bootstrap_router_vs_conf.csv):

  | sigma | mean Δ(router−conf) | 95% CI            | beats conf? |
  |-------|---------------------|-------------------|-------------|
  | 0.15  | +0.0011             | [−0.0031, +0.0055]| NO (CI∋0)   |
  | 0.30  | +0.0075             | [+0.0027, +0.0127]| YES         |
  | 0.60  | +0.0165             | [+0.0115, +0.0217]| YES         |

ANSWER: The pre-decode router beats confidence-threshold at matched budget ONLY when the
post-decode confidence signal is at least as noisy as the pre-decode features (sigma>=0.3 here).
At low noise (sigma=0.15) confidence-threshold TIES it (CI includes 0). The router NEVER loses,
but its edge over the strong baseline is small and conditional.

---

## Verdict: PARTIAL

- (A) Predictability: HELD in request-dependent regime (AUC up to 0.89 at realistic noise),
  NULL in uniform regime — exactly as pre-registered. Anti-circular, real oracle gap.
- (B) Pareto: HELD vs all-quant/all-full/random (dominates). vs confidence-threshold: held only
  conditionally (sigma>=0.3); ties at low noise. The claim's strongest form — "strictly better
  than confidence-threshold at matched budget" — is NOT robustly supported; it depends on the
  relative noise of pre- vs post-decode signals.

The defensible, honest claim: a quant-sensitivity-specific PRE-decode router is Pareto-competitive
with a confidence-threshold cascade and avoids the cheap decode entirely — but its QUALITY edge
over a tuned confidence cascade is small and only appears when post-decode confidence is noisy.
Its real selling point is COST (skipping the cheap decode), NOT a large quality win.

---

## What a real L1 must measure (this L0 cannot)
1. REAL per-request degradation: run a real low-bit-quant model (e.g. GPTQ/AWQ 4-bit) AND the
   full-precision model on the SAME real prompts; measure per-request quality delta (task metric
   / judge / exact-match for arithmetic). Is it actually heavy-tailed/request-dependent? (The
   claim DIES if real degradation is ~uniform.)
2. REAL pre-decode predictiveness: do real prompt-perplexity, domain, arithmetic/long-context
   markers actually predict that real per-request degradation? Measure real AUC + oracle gap.
3. REAL confidence baseline: the quant model's actual output confidence (logprob/entropy) as a
   POST-decode escalation signal — is it MORE predictive than pre-decode features? If yes, the
   pre-decode router only wins on cost (skipped decode), not quality.
4. REAL cost accounting: cheap-decode cost vs full-decode cost vs router-inference cost, to put
   the x-axis (cost) in true FLOPs/$ rather than escalation-rate.

## Prior-art caveat (MUST distinguish — routing is PUBLISHED)
LLM cascades/routing are well-established: FrugalGPT, RouteLLM, LLM-Blender, Tabi, and
hybrid/mixed-precision serving all gate cheap->expensive on generic DIFFICULTY or CONFIDENCE.
This work's ONLY potential novelty is QUANT-SENSITIVITY-SPECIFIC, PRE-decode prediction (route
before any decode, on the basis of predicted *quantization* degradation specifically, not generic
difficulty). The L0 result tempers even that: against a confidence-threshold cascade at matched
budget the quality edge is modest/conditional. Honest framing: the contribution (if it survives
L1) is "predicting quant-sensitivity pre-decode is feasible and saves the cheap decode," NOT
"a new dominant routing paradigm." Routing itself is not novel.

## Artifacts
- experiments/2026-06-03/EXP-0020/PREREG.md  (committed before run, commit 1a6652b)
- experiments/2026-06-03/EXP-0020/sim.py
- results/predictability.csv  (AUC vs noise, 2 regimes)
- results/pareto.csv          (5 policies x 5 budgets x 5 seeds x 5 sigmas x 2 regimes)
- results/bootstrap_router_vs_conf.csv  (router-vs-confidence delta CI @ b=0.2)

## PRE-REG (committed pre-run 1a6652b)
# PRE-REGISTRATION — EXP-0020 / CLAIM-0015
# Committed BEFORE running. Quant-sensitivity PRE-decode router.

## CLAIM
A cheap PRE-GENERATION router predicting per-request whether low-bit quantization will
materially degrade THIS request's output (from PRE-decode features: prompt perplexity,
domain, arithmetic/long-context markers) routes only quant-sensitive requests to the
expensive full-precision model — achieving a strictly better cost/quality Pareto than
(a) all-quant, (b) all-full, (c) random escalation @matched budget, AND (d) a
CONFIDENCE-THRESHOLD escalation baseline @matched budget.

## TWO FALSIFIABLE PARTS
A. Is per-request quant-degradation predictable from cheap PRE-decode features (real AUC)?
B. Does the pre-decode router beat all-quant/all-full AND confidence-threshold @matched
   escalation budget b on the cost/quality Pareto?

## METRICS
- M1 (predictability): ROC-AUC of pre-decode predictor for "high quant-degradation" label,
  vs oracle (latent property) gap. Sweep observation noise.
- M2 (Pareto): quality(b) at matched escalation rate b for each policy; x=cost(=b), y=quality.
  Primary delta: router_quality(b) - confidence_threshold_quality(b), with bootstrap CI.

## REQUEST / QUANT-ERROR MODEL (anti-circular; the lesson that RED'd CLAIM-0008)
- Each request i has a LATENT scalar s_i in [0,1] = "true quant-sensitivity" (the generative
  cause). The PREDICTOR NEVER reads s_i.
- Quant degradation d_i (quality drop if served by quant model) is a function of s_i:
    * REQUEST-DEPENDENT (heavy-tailed) regime: d_i = base * s_i^gamma  (gamma>1 -> heavy tail),
      so a minority of requests carry most of the degradation. Claim NEEDS this.
    * UNIFORM regime (null): d_i ~ constant + small iid noise, independent of s_i.
- PRE-decode observables (what predictor sees), each a NOISY correlate of s_i:
    * prompt_perplexity = s_i + N(0, sigma_obs)   (higher ppl ~ harder ~ more sensitive)
    * domain_tag: noisy categorical; high-sensitivity domains (math/code/long-ctx) drawn
      with prob increasing in s_i, but flips with prob p_flip.
    * arith_marker, longctx_marker: Bernoulli with P=logistic(s_i) but corrupted by noise.
  Predictor = logistic regression on these PRE-decode features ONLY. AUC swept by sigma_obs.
- CONFIDENCE-THRESHOLD baseline: uses the QUANT MODEL's output confidence c_i = g(s_i)+noise.
  This is a POST-decode signal (requires running the cheap decode first) — modeled honestly
  as a separate, also-noisy correlate of s_i. The pre-decode router's selling point is
  avoiding even the cheap decode; but on QUALITY at matched b, confidence-threshold is the
  STRONG baseline to beat. We give it a FAIR (comparable-noise) confidence signal.
