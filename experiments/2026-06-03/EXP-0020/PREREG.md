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

## QUALITY ACCOUNTING
- Served by full model: quality = q_full_i (no degradation).
- Served by quant model: quality = q_full_i - d_i.
- Policy escalates fraction b to full. Total quality = mean over requests.
- All policies matched at the SAME b. all-quant=b0, all-full=b1.

## BASELINES (all at matched b)
1. all-quant (b=0): cheapest, lowest quality.
2. all-full  (b=1): best quality, most expensive.
3. random-escalate@b: escalate random b fraction.
4. confidence-threshold@b: escalate b fraction with LOWEST quant-model confidence (post-decode). STRONG.
5. pre-decode-router@b: escalate b fraction with highest predicted degradation (pre-decode). OURS.
6. ORACLE@b: escalate b fraction with truly highest d_i (upper bound; not achievable).

## SWEEPS
- regime in {request_dependent(heavy-tail gamma=3), uniform(null)}
- sigma_obs in {0.05,0.15,0.3,0.6,1.0} (controls predictor AUC)
- b in {0.05,0.1,0.2,0.3,0.5}
- >=5 seeds. Bootstrap CI (1000 resamples) on router-vs-confidence quality delta at b=0.2.

## HONEST-NEGATIVE BRANCH (pre-committed)
Report NEGATIVE if ANY of:
- quant-degradation ~uniform across requests (uniform regime: no routing can help), OR
- not predictable from PRE-decode features at useful AUC (AUC ~0.5 in realistic noise), OR
- the pre-decode router CANNOT beat confidence-threshold @matched b (CI of delta includes/below 0).
Verdict: held / partial / negative.

## PRIOR-ART CAVEAT
LLM cascades/routing (RouteLLM, FrugalGPT, LLM-Blender, hybrid-precision serving) are PUBLISHED.
They gate on generic DIFFICULTY/confidence. Novelty here (if any) = QUANT-SENSITIVITY-specific
PRE-decode prediction (avoiding the cheap decode). We must show we beat the confidence-threshold
cascade at matched budget, else this reduces to known routing.
