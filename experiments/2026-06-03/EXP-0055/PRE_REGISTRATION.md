# PRE_REGISTRATION — EXP-0055 (CLAIM-0050) — L1, cost-aware staged 4-gate
**Researcher:** researcher-0053 | **Claim:** CLAIM-0050 (YELLOW-CONDITIONAL, committee#1 VERDICT-0048)
**Committed BEFORE any run.** Honest pipeline; null/negative is a WIN.

## CLAIM under test
In continuous-batching VLM serving, input-length-SJF scheduling is WORSE than FCFS below a
proxy-correlation crossover tau*, and realistic VLM mixes live BELOW tau* (so harm is large at
realistic params). L0 (EXP-0054, M/G/1 sim) SUPPORTED the mechanism: at the ASSUMED realistic tau
band, SJF p99 is 1.4-5.8x worse than FCFS; controls C1 (oracle SJF beats FCFS) + C2 (FCFS
tau-invariant) isolated the proxy. The load-bearing premise — that REAL VLM
Kendall-tau(input_tokens, decode_length) is below tau* — was ASSUMED, not measured.

## tau* from L0 (EXP-0054): crossover tau* in [+0.43 (rho=0.7) .. +0.8 (rho=0.95)].
L0 ASSUMED realistic VLM tau ~ 0.0 to -0.2 (central 0.0). GATE-1 MEASURES the real number.

## == GATE-1 (LOAD-BEARING, do FIRST; decisive ecological test) ==
**Option A (PREFERRED, feasible):** Qwen3-VL-4B-Instruct (CACHED on devgpu014 H100, ros-vllm07
env, vLLM 0.22.0) on a perception+reasoning IMAGE+TEXT mix designed to span the two regimes the
claim depends on:
  - PERCEPTION/OCR/caption: LARGE image, SHORT expected answer (read this text / describe briefly)
  - VISUAL-REASONING: SMALL/simple image, LONG expected chain-of-thought answer (count/compare/
    explain step by step)
  Mix ~ a few hundred examples (target >=200, budget-permitting), balanced across the two regimes
  plus intermediate cases so input-token range and decode-length range both vary.
  For EACH request record: input_token_count (image placeholder tokens + text prompt tokens, from
  the actual processed prompt) and REALIZED decode/output length (vLLM completion token count).
  Image source: programmatically SYNTHESIZED with PIL (offline) — OCR text cards (varying size →
  big image, short answer) + geometric/count scenes (small image, long CoT). Ecological limitation
  STATED: synthetic images, single 4B VLM, greedy decode; this is a real VLM forward pass on a real
  perception+reasoning mix, NOT a production trace. Reported as Option A with that caveat.
**Decode realism:** allow up to max_tokens=512, temperature=0 (deterministic), so realized decode
length reflects the model's natural stopping (EOS) per request — the genuine decode cost.

### GATE-1 measurement & DECISION RULE (committed)
Compute Kendall-tau_b(input_token_count, realized_decode_length) across the full mix, WITH a 95%
bootstrap CI (B=2000 resamples). Compare to L0 tau* band [+0.43, +0.8]:
  - **GATE-1 PASSES** iff measured real tau is clearly BELOW tau* (CI upper bound < +0.43, i.e.
    real mixes sit in the harmful region). Proceed to GATE-2.
  - **GATE-1 FAILS** iff real tau is NOT below tau* (CI overlaps or exceeds +0.43; or tau is
    strongly POSITIVE meaning input length predicts decode length well). -> ecological claim
    COLLAPSES -> HONEST NEGATIVE -> STOP (no GPU on GATE-2).
We report the measured tau + CI as THE load-bearing number regardless of direction.

**Option B (FALLBACK if VLM env fails):** text-LLM proxy (Qwen2.5-7B cached) on a mix of
short-answer QA + long-CoT reasoning prompts; measure tau(input_len, output_len). State ecological
limitation (text-only, no image tokens). Do NOT skip GATE-1.

## == GATE-2 (ONLY if GATE-1 passes) — continuous-batching realism ==
Continuous-batching simulator (stdlib): iteration-level scheduler, each step advances ALL active
requests by one decode token (processor-sharing round-robin), admission by policy (FCFS arrival
order vs input-length-SJF), bounded batch (max concurrent), preemption allowed. Couple the proxy to
true decode cost at the REAL tau measured in GATE-1 (Gaussian copula calibrated to measured tau).
Decode lengths drawn from the EMPIRICAL realized-decode distribution measured in GATE-1.
**Decision:** SJF-worse-than-FCFS p99 regression SURVIVES iff SJF_p99/FCFS_p99 >= 1.2x (with CI
lower bound > 1.0) under continuous batching at realistic load; COLLAPSES otherwise.

## == GATE-3 (cheap, alongside) ==
Bootstrap CIs (B>=2000) on ALL headline p99 ratios; batch-means CI on tau* localization.
Report tau* with CI from the L0 sweep data (p99 is high-variance).

## == GATE-4 (cheap, alongside) ==
sigma_d (decode-length tail) sensitivity sweep in GATE-2 model: is the 1.2x+ regression conditional
on heavy tail (sigma_d=1.0)? Re-run at sigma_d in {0.25,0.5,0.75,1.0}. Report whether effect
vanishes at sigma_d<=0.5. State regime-dependence honestly.

## ANTI-CIRCULAR (preserved from L0)
Scheduler reads ONLY the proxy (input_token_count / arrival order). Ground-truth decode cost
realizes ONLY at service to advance the clock. No leakage of true decode length into ordering.

## CITATIONS / POSITIONING
- Purohit, Svitkina, Kumar (NeurIPS 2018) + Lykouris, Vassilvitskii (ICML 2018): consistency/
  robustness theory — "a bad predictor can be worse than the baseline" is a KNOWN qualitative
  regime. This work positions its contribution as the QUANTITATIVE magnitude + the VLM-ECOLOGY
  question (does the harmful regime actually occur on real VLM mixes?), NOT as regime discovery.
- Fu 2408.15792, S3 2306.06000: input-length already known to be an inadequate decode-length proxy.
GATE-1 is precisely the test of whether CLAIM-0050 has a real ecological foothold or is a known
robustness regime exhibited only in a toy model.

## FINAL DISPOSITION RULE (committed)
- **support** iff GATE-1 PASSES (real tau clearly < tau*) AND GATE-2 regression survives (>=1.2x,
  CI lower bound >1.0) under continuous batching.
- **keep-exploring** iff GATE-1 passes but GATE-2 ambiguous (CI straddles 1.2x).
- **weaken/kill** iff GATE-1 FAILS (real tau NOT below tau* -> no ecological foothold) OR GATE-2
  collapses the magnitude (<1.2x at realistic sigma_d).
Do NOT self-converge; orchestrator runs committee#2 if warranted.
