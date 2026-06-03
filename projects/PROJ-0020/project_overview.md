# PROJ-0020 — Multimodal-serving: input-length-SJF scheduling is WORSE than FCFS below a proxy-correlation crossover tau*, and realistic VLM mixes live there (EMPIRICAL PHENOMENON)
Fresh area: multimodal-serving (VLM inference scheduling under continuous batching). EMPIRICAL-phenomenon, NO
closed form (tau* is an emergent queueing crossover under a specific arrival process + heavy-tailed decode dist +
batching; incumbent theory gives bounds only for UNBIASED error, not the sign-flip location under class-structured
anti-correlation). Passes all 6 anti-patterns (scout-verified) incl #6 INVERTED: the effect is LARGEST at REALISTIC
params (image-token count near-zero/NEGATIVELY correlated w/ output length — big OCR/caption images -> short answers,
small-image reasoning -> long CoT), the ADVERSARIAL extreme (proxy perfectly correlated) is the BENIGN end. THESIS:
in continuous-batching VLM serving, when the scheduler uses input/prefill-token count as the SJF priority proxy
(cheapest observable, image-token-dominated), there's a rank-correlation sign-flip threshold tau* in the proxy<->
true-decode-cost Kendall-tau such that for tau<tau* input-length-SJF yields STRICTLY WORSE p99 latency than plain
FCFS — and realistic VLM mixes sit at/below tau*, so the harm is large at realistic params. Anti-circular: GT =
generative true_service_time (=f(decode_length), harness-controlled, NEVER visible to scheduler); SJF reads ONLY
input_token_count (observable), FCFS reads only arrival order; GT realizes only during service to advance the clock.
Honest-negative (informative): if SJF p99 <= FCFS p99 across the realistic tau range [-0.2,+0.3] at all loads ->
input-length-SJF is SAFE to deploy on multimodal mixes (useful negative); graded: if crossover only at tau<-0.4
(adversarial) -> weaken (anti-pattern #6). Controls: tau->+1 SJF beats FCFS (sanity); FCFS curve tau-invariant
(confirms effect is the PROXY not workload). PRIOR-ART: FOUNDATIONAL Mitzenmacher 'Scheduling with Predictions'
(ITCS2020, 1902.00732) + Dell'Amico inexact-job-sizes (1907.04824) + SOAP/Gittins (1712.00790) — ALL assume
unbiased/zero-mean per-job size error; LLM length-pred scheduling (Fu 2408.15792 etc.) treats predictor error as
noise to REDUCE. Delta = the proxy-CLASS-ANTICORRELATION regime they exclude + the tau* crossover where SJF becomes
ACTIVELY HARMFUL vs FCFS + realistic-VLM-mixes-live-below-tau*. NOT textbook SJF-starvation (there ranking is
CORRECT; here ranking is WRONG-by-class, promoting long jobs).
