# PRE-REGISTRATION — EXP-0054 (CLAIM-0050)

**Researcher:** researcher-0052 | **Project:** PROJ-0020 | **Task:** TASK-0044
**Level:** L0 (CPU-only, stdlib-only, SERIAL, <=15 min) | **Date:** 2026-06-03

## THE CLAIM (CLAIM-0050)
In continuous-batching multimodal (VLM) serving where the scheduler uses INPUT/prefill-token
count as the SJF priority proxy (cheapest observable, image-token-dominated), there is a
rank-correlation sign-flip threshold tau* in the proxy-vs-true-decode-cost Kendall-tau such that
for tau < tau* input-length-SJF yields STRICTLY WORSE p99 request latency than plain FCFS — and
realistic VLM mixes sit at/below tau* (image-token count near-zero/negatively correlated with
output length: big OCR/caption images -> short answers; small-image reasoning -> long CoT), so the
harm is LARGE at realistic parameters, NOT only at adversarial extremes (anti-pattern #6 defense).

EMPIRICAL phenomenon (no closed form). This is NOT metric-validity: a scheduling POLICY causes a
real p99 latency regression in the SAME currency (request latency) it nominally optimizes.

## QUEUE MODEL
Discrete-event single-server (SERIAL) M/G/1-style queue. N requests, Poisson(lambda) arrivals.
Single server processes one request at a time, NON-PREEMPTIVE. (Continuous-batching VLM serving
serializes the decode bottleneck onto the accelerator; M/G/1 captures the head-of-line dynamics
that scheduling order controls. We keep it single-server + non-preemptive for L0 clarity; the
ordering effect — which job goes next — is exactly what FCFS vs SJF differ on.)

## GROUND TRUTH (GT) — true_service_time (harness-controlled, NEVER visible to scheduler)
For each request i:
  decode_length_i ~ heavy-tailed LOG-NORMAL (mu_d, sigma_d) with sigma_d=1.0 (heavy tail,
    CV>1) so that a few long-decode jobs dominate the queue — the regime where scheduling order
    matters most.
  true_service_time_i = c_decode * decode_length_i + c_prefill * prefill_tokens_i
    with c_decode dominating (decode is the serial bottleneck in VLM serving). We set
    c_prefill small (prefill is parallel/cheap per-token vs autoregressive decode).
GT is realized ONLY during "service" to advance the simulation clock. No policy reads it.

## OBSERVABLE PROXY — input_token_count (the ONLY thing SJF reads)
input_token_count_i = image_tokens_i + text_tokens_i, dominated by image_tokens (VLM: a single
image is hundreds-to-thousands of vision tokens). We generate input_token_count JOINTLY with
decode_length via a GAUSSIAN-COPULA rank-coupling knob:
  - Draw two correlated standard normals (Z_proxy, Z_true) with Pearson rho_g (the copula knob).
  - Map Z_true -> decode_length via lognormal inverse-CDF (the GT driver).
  - Map Z_proxy -> input_token_count via a lognormal inverse-CDF (proxy marginal; mu_p, sigma_p
    chosen to look like VLM input-token counts, heavy on image tokens).
  - The Kendall-tau between input_token_count and true_service_time is a MONOTONE function of
    rho_g (Kendall tau = (2/pi) arcsin(rho_g) for the Gaussian copula, modulo the small prefill
    term). We sweep rho_g to hit target Kendall-tau values and MEASURE the realized empirical
    Kendall-tau on each generated workload (report measured tau, not nominal).

## RANK-COUPLING KNOB & tau SWEEP
Copula knob rho_g swept so realized Kendall-tau(proxy, true_service_time) ranges over:
  tau in approximately {+0.8, +0.6, +0.4, +0.3, +0.2, +0.1, 0.0, -0.1, -0.2, -0.3, -0.4, -0.5}
(well-aligned through anti-correlated). Measured per workload, reported.

## LOAD (rho) SWEEP
rho in {0.70, 0.80, 0.90, 0.95}. lambda set from rho = lambda * E[true_service_time].

## POLICIES
- FCFS: dequeue in arrival order. Reads ONLY arrival timestamp. tau-INVARIANT by construction.
- input-length-SJF: among queued requests, dequeue the one with SMALLEST input_token_count.
  Reads ONLY input_token_count (observable proxy). Non-preemptive.
Neither policy touches GT. GT realizes only at service to advance the clock (anti-circularity).

## MEASUREMENT
For each (rho, tau): N=4000 requests/run, K=12 seeds. Compute per-request latency
(completion - arrival). Report MEAN and p99 latency under FCFS and SJF, with 95% bootstrap/normal
CIs across seeds. Warmup: drop first 200 completions to remove cold-start bias.

## HEADLINE TEST
The crossover tau* = the tau at which SJF p99 crosses ABOVE FCFS p99 (SJF becomes worse).
Found by locating the sign change of (p99_SJF - p99_FCFS) along the tau axis at each rho.

## REALISTIC-tau ESTIMATE (load-bearing, anti-pattern #6)
Empirically-plausible VLM Kendall-tau(input-token-count, decode-length): we argue it sits in
[-0.2, +0.3], centered NEAR ZERO or slightly NEGATIVE. Justification:
  - VLM input tokens are image-token-dominated (one high-res image = 1000s of vision tokens).
  - Big/high-res images are frequently OCR/caption/detection tasks -> SHORT answers
    (a label, a transcript span) -> small decode_length.
  - Small-image or text-heavy reasoning prompts (charts, "explain", multi-step) -> long CoT
    decode -> large decode_length.
  - Net: image-token count anti-correlates (or is ~uncorrelated) with decode length, while it
    DOMINATES the input-token proxy. So input-length is a near-blind / wrong-by-class proxy for
    decode cost. Plausible tau ~ 0.0 to -0.2.
We REPORT the SJF-vs-FCFS p99 gap AT realistic tau (we use tau_realistic = 0.0 as the central
estimate, and the [-0.2,+0.3] band), not only at extremes.

## CONTROLS
(C1) tau -> +1 (well-aligned, tau~+0.8): SJF must STRICTLY BEAT FCFS on p99 (correct proxy helps).
(C2) FCFS p99 must be tau-INVARIANT across the sweep (FCFS ignores the proxy) -> confirms the
     effect is the PROXY, not the workload. We report FCFS p99 variation across tau (should be
     within seed CI).

## DECISION BRANCHES (committed BEFORE running)
- SUPPORTED iff ALL: (a) a crossover tau* exists at realistic rho (>=0.8); AND (b) tau* > the
  realistic VLM tau (realistic mixes fall in the harmful region, tau* >= ~0.0); AND (c) at
  realistic tau (0.0) SJF p99 >= 1.2x FCFS p99 at some realistic load; AND (d) both controls pass.
- HONEST-NEGATIVE iff SJF p99 <= FCFS p99 across the realistic tau range [-0.2,+0.3] at ALL loads
  -> input-length-SJF is SAFE on multimodal mixes (a useful negative).
- WEAKEN iff crossover exists ONLY at adversarial tau < -0.4 (anti-pattern #6 bites: the harmful
  regime is not realistic).

## NOVELTY / PRIOR-ART CAVEAT (precise)
Mitzenmacher "Scheduling with Predictions" (ITCS2020, 1902.00732), Dell'Amico inexact job sizes
(1907.04824), SOAP/Gittins (1712.00790) ALL assume unbiased / zero-mean per-job size error;
LLM length-pred scheduling (Fu 2408.15792) treats predictor error as noise to REDUCE. Novelty =
the proxy-CLASS-ANTICORRELATION regime + the tau* crossover where SJF is ACTIVELY HARMFUL vs FCFS
+ realistic-VLM-mixes-live-below-tau*. This is NOT textbook SJF-starvation (there the ranking is
correct; here it is wrong-BY-CLASS).
