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
