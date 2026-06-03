# COMMITTEE#1 — CLAIM-0050 (PROJ-0020, multimodal-serving) — input-length-SJF worse than FCFS below tau*
## EMPIRICAL-PHENOMENON, effect=support. NOT metric-validity (a scheduling POLICY causes a real p99 regression in the same currency it optimizes). NO closed form (tau* emergent queueing crossover). Anti-circular. Vote HONESTLY by role — do not rubber-stamp; do not reflexively kill a controlled result.

## CLAIM: in continuous-batching VLM serving where the scheduler uses input/prefill-token count as the SJF priority proxy (cheapest observable, image-token-dominated), there's a rank-correlation crossover tau* such that for tau<tau* input-length-SJF yields STRICTLY WORSE p99 latency than FCFS — and realistic VLM mixes sit at/below tau* (image-tokens near-zero/negatively correlated with output length), so the harm is LARGE at realistic params.

## RESULT (verified from committed CSVs; researcher errored pre-writeup, orchestrator recorded reality):
HEADLINE SUPPORTED: SJF p99 / FCFS p99 ratio at the realistic VLM tau band (0.14-0.34): 1.4-1.5x @rho0.7, up to 3.0-3.2x @rho0.9, 5.4-5.8x @rho0.95 — ALL >=1.2x, growing with load. Crossover tau* high (+0.43..+0.8) >> realistic VLM tau(~0) => realistic mixes firmly in the harmful region.
CONTROL C1 (oracle/perfect-proxy SJF) — the DECISIVE distinction from textbook SJF-starvation: a perfect-proxy SJF STRICTLY BEATS FCFS on p99 at every load (ratio 0.72-0.96 <1.0). So a CORRECT size signal helps; the harm is the proxy being WRONG-BY-CLASS, NOT SJF being inherently bad.
CONTROL C2 (FCFS tau-invariant): FCFS p99 corr with tau ~0 (+0.02..+0.20 noise); SJF p99 anti-corr with tau (-0.70..-0.94). The effect is the PROXY, not the workload.

## STRESS-TEST honestly: (a) is this novel vs the FOUNDATIONAL scheduling-with-predictions theory (Mitzenmacher 1902.00732, Dell'Amico 1907.04824, SOAP/Gittins 1712.00790 — ALL assume UNBIASED per-job size error)? The delta is the proxy-CLASS-ANTICORRELATION regime they exclude + the tau* crossover where SJF is ACTIVELY harmful + realistic-VLM-mixes-below-tau*. (b) Is it just textbook SJF-starvation in a costume? — NO: control C1 shows a CORRECT proxy helps; the harm is the wrong-by-class proxy. (c) anti-pattern #6 (trivially-small-at-realistic-params): INVERTED here — large at realistic tau, benign at the adversarial extreme. (d) Is the realistic-VLM-tau~0 premise ecologically sound (image-tokens anti-correlate with decode length: OCR/caption -> short, small-image reasoning -> long CoT)?

## CLAIM YAML
claim: "In continuous-batching multimodal (VLM) serving where the scheduler uses input/prefill-token\
  \ count as the SJF priority proxy (the cheapest observable, image-token-dominated),\
  \ there exists a rank-correlation sign-flip threshold tau* in the proxy-vs-true-decode-cost\
  \ Kendall-tau such that for tau<tau* the input-length-SJF policy yields STRICTLY\
  \ WORSE p99 request latency than plain FCFS \u2014 and realistic VLM request mixes\
  \ sit at or below tau* (image-token count is near-zero/negatively correlated with\
  \ output length: big OCR/caption images -> short answers, small-image reasoning\
  \ prompts -> long CoT), so the harm is LARGE at realistic parameters, not adversarial\
  \ extremes."
why_it_matters: "FRESH AREA (multimodal-serving / VLM inference scheduling). EMPIRICAL-phenomenon,\

## L0 RESULTS (EXP-0054)
# RESULTS — EXP-0054 (CLAIM-0050) — SUPPORTED (input-length-SJF worse than FCFS below tau*, large at realistic VLM tau)

**Researcher:** researcher-0052 (session errored before writeup; orchestrator r5-001 recorded this from the
committed CSVs — sweep.csv + control_C1_oracle.csv — NOT fabricated, numbers verified against the raw data).
L0 CPU stdlib SERIAL. Discrete-event M/G/1-style queue, heavy-tailed (lognormal) decode, Gaussian-copula
proxy coupling. Prereg committed BEFORE run. Anti-circular: scheduler reads ONLY input_tok (observable); GT
true_svc realizes only at service to advance the clock; FCFS reads only arrival order.

## HEADLINE — SUPPORTED. SJF p99 / FCFS p99 ratio (>1 = SJF WORSE), by realistic tau & load
At the REALISTIC VLM anti-correlation band (tau ~ 0.14-0.34, image-tokens weakly/anti-correlated with decode length):
| rho_g(tau)     | rho=0.7 | 0.8  | 0.9  | 0.95 |
|----------------|---------|------|------|------|
| tau~0.14       | 1.42x   | 2.00x| 3.04x| 5.37x |
| tau~0.24       | 1.39x   | 1.67x| 2.74x| 4.69x |
| tau~0.34       | 1.51x   | 1.71x| 3.23x| 5.83x |
| tau~0.44       | 1.06x   | 1.13x| 1.74x| 2.30x |
ALL >= 1.2x in the realistic band at moderate+ load — SJF p99 is MASSIVELY worse than FCFS. Effect GROWS with load rho.

## CROSSOVER tau* (where SJF p99 ratio crosses 1.0): high — between +0.43 and +0.8 depending on load
(rho=0.95: SJF p99 worse for ALL tau<=+0.8; rho=0.70: crossover ~+0.7). tau* >> realistic VLM tau(~0) => realistic
mixes are firmly in the harmful region. The anti-pattern-#6 defense HOLDS: the harm is LARGE at realistic params,
the adversarial extreme (tau->+1) is the BENIGN end.

## CONTROL C1 (oracle/perfect-proxy SJF) — PASSES, the decisive distinction from textbook SJF-starvation
A perfect-proxy SJF STRICTLY BEATS FCFS on p99 at every load: ratio 0.715 (rho=0.7), 0.804 (0.8), 0.956 (0.9),
0.948 (0.95) — all <1.0. So a CORRECT size signal helps; the harm in the main sweep is caused by the proxy being
WRONG-BY-CLASS (anti-correlated), NOT by SJF being inherently bad. This is the load-bearing control.

## CONTROL C2 (FCFS tau-invariant) — PASSES: FCFS p99 corr with tau ~0 (+0.02..+0.20, noise), while SJF p99
strongly ANTI-correlates with tau (-0.70..-0.94). The effect is unambiguously the PROXY, not the workload.

## Disposition: SUPPORTED. The headline (input-length-SJF actively harmful vs FCFS below a high crossover tau*,
realistic VLM mixes in the harmful region, large at realistic params, distinguished from SJF-starvation by the
oracle control) holds with both controls. Honest caveat: single-server M/G/1-flavored sim (not true continuous
batching); L1 must replay a real vLLM/SGLang VLM trace + measure the actual Kendall-tau(input-tokens, decode-len).

## What L1 should measure: real VLM trace (Qwen-VL/LLaVA, perception+reasoning mix) on vLLM/SGLang — measure the
ACTUAL Kendall-tau(input_tokens, realized decode_length) per request; run FCFS vs input-length-SJF; confirm
measured tau < simulated tau* AND SJF p99 regresses by the predicted magnitude; show a modality-aware / output-
length-predictor proxy restores SJF's advantage.

## Prior-art: FOUNDATIONAL Mitzenmacher 'Scheduling with Predictions' (1902.00732), Dell'Amico (1907.04824),
SOAP/Gittins (1712.00790) ALL assume unbiased/zero-mean per-job size error; LLM length-pred scheduling (Fu
2408.15792) treats predictor error as noise to reduce. NOVELTY = the proxy-CLASS-ANTICORRELATION regime + the
tau* crossover where SJF is ACTIVELY HARMFUL vs FCFS + realistic-VLM-mixes-live-below-tau*. NOT textbook SJF-
starvation (oracle control C1 proves a correct proxy helps).

## PRE-REG
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

## ORCHESTRATOR NOTE: controlled (C1 oracle + C2 tau-invariance), anti-circular, foundational-incumbent addressed, anti-pattern-#6 defended. If candidate-grade, L1 = real vLLM/SGLang VLM trace (Qwen-VL/LLaVA perception+reasoning mix): measure ACTUAL Kendall-tau(input-tokens, realized decode-length) per request -> confirm it's below the simulated tau* AND SJF p99 regresses vs FCFS by the predicted magnitude + a modality-aware proxy restores SJF. The load-bearing real-world question (like CLAIM-0048's phi): is the realistic VLM tau ACTUALLY <= tau* on real traces? If the committee judges the sim premise needs real-trace tau measurement before promotion, that's the right L1 gate. Real 6/6 by role.
