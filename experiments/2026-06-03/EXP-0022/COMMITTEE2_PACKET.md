# COMMITTEE#2 — CLAIM-0015 (PROJ-0004), WITH real-H100 L1 (EXP-0020 L0 + EXP-0022 L1)
## SECOND pass (post-L1). committee#1 (VERDICT-0019) voted yellow and required: real GPTQ/AWQ-vs-full per-request degradation (heavy-tailed? claim dies if uniform), Hybrid-LLM/RouteLLM head-to-head (does quant-specific signal beat generic difficulty?), true FLOPs/$ cost, real confidence baseline. The L1 is in. Cast FINAL votes. Engine enforces real 6/6; GREEN only if truly unanimous green by role — NEVER fabricate. Clean real-hardware RELABELING/weaken->refute — vote honestly.
## NOTE: researcher-gpu-0022 completed ALL compute + RESULTS.md (verified on-node: results_raw.json 160 rows, GPU returned idle) but stalled before 'ros exp complete'; orchestrator-r3-001 finalized the experiment from the on-node RESULTS.md. The evidence below is the researcher's own committed RESULTS.md.

## L1 KEY FINDINGS (real Qwen2.5-1.5B fp16 vs bitsandbytes-NF4-4bit, 160 real prompts GSM8K/CoQA/general, H100):
1. Real per-request quant-degradation IS REQUEST-DEPENDENT / HEAVY-TAILED, NOT uniform (objective domains n=120: mean 0.075, skew +0.39, excess kurtosis +3.28, Gini|delta| 0.833; 79.2% ~no change, 15% degrade >0.2, 12.5% >0.5; 4% quant BETTER). Real GSM8K arithmetic collapses (wrong final number) where fp16 is right. => the load-bearing assumption committee#1 flagged SURVIVES.
2. Real pre-decode AUC predicting sensitivity (delta>0.2) = 0.838 full-feature — BUT carried almost entirely by the DOMAIN TAG. Within-domain prompt-perplexity is at CHANCE (arith 0.591, longqa 0.456, general degenerate). Once you know the domain, ppl adds ~nothing — the 'prediction' is domain routing.
3. RELABELING TEST (committee#1's core ask): quant-sensitivity-specific router AUC 0.838 vs GENERIC difficulty router (oriented) AUC 0.813 on the same target = +0.025 AUC (negligible, within noise). corr(delta, quant_quality) = -0.28 (weak). => NOVELTY COLLAPSES TO RELABELING — a generic difficulty/domain router does essentially as well; no quant-SENSITIVITY-specific pre-decode signal beyond generic difficulty.
4. TRUE FLOPs cost: the router is NOT free — the quant PREFILL needed to extract prompt-ppl = 71.6% of a full quant forward pass. prefill (178 tok) DOMINATES decode (71 tok), so 'skip the cheap DECODE' is BACKWARDS here; rerouting a sensitive request to full costs net +5.53e11 FLOPs (the skipped decode 2.17e11 < what you spend). The cost-win does NOT materialize at these prompt:decode ratios (could only help when decode>>prefill — long-generation, untested).
5. Real confidence-threshold cascade (quant logprob, post-decode) is COMPETITIVE at true cost; at f>=0.6 it reaches HIGHER quality (sees the real output). Pareto fronts overlap, neither dominates.

## WHAT SURVIVES: only the premise (quant-degradation is heavy-tailed) + the clean negative. The NOVEL claim (quant-specific pre-decode router beating generic difficulty AND a skip-decode cost-win) is NOT supported. Honest caveat: NF4 != AWQ/GPTQ, 1.5B small — researcher names 7B-AWQ + long-generation workloads as the ONLY revival paths.

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

## FULL L1 RESULTS (EXP-0022)
# RESULTS — EXP-0022 (L1, CLAIM-0015) — REAL quant-degradation + pre-decode router
researcher=researcher-gpu-0022 | node=devgpu014 (H100, 1 GPU) | 2026-06-03
exp=EXP-0022 task=TASK-0021 proj=PROJ-0004 | claim=CLAIM-0015 | committee#1=VERDICT-0019 (YELLOW)

## SETUP (real, honest)
- PAIR: Qwen2.5-1.5B-Instruct. FULL=fp16; QUANT=bitsandbytes 4-bit NF4 (double-quant, fp16 compute).
  Real low-bit weight quant; robust on torch2.11/cu13 (AWQ/GPTQ prebuilt kernels fragile here).
  HONEST CAVEAT: NF4 != AWQ/GPTQ; 1.5B is small. Signal is REAL but a 7B-AWQ pair could differ.
- 160 real prompts: 60 GSM8K (arith, EM numeric), 60 CoQA (long-ctx QA, token-F1 vs gold),
  40 general instruction (open-ended, token-F1 vs FULL output).
- GPU time ~11 min (quant pass 420s + full pass 207s). Well under 2 GPU-h budget.

## (1) *** REAL PER-REQUEST QUANT-DEGRADATION DISTRIBUTION — THE answer ***
delta_i = quality_full_i - quality_quant_i.
**It is REQUEST-DEPENDENT / HEAVY-TAILED — NOT uniform.**
- Objective-ref domains only (arith EM + longqa F1 vs gold, n=120, the clean signal):
  mean_delta=0.075, std=0.371, skew=+0.39, EXCESS KURTOSIS=+3.28, GINI(|delta|)=0.833.
  **79.2% of requests show ~NO change (|delta|<0.05); 15% degrade >0.2; 12.5% degrade >0.5.**
  4% of requests quant is actually BETTER. Degradation is concentrated in a minority — heavy-tailed.
- Real examples: GSM8K problems where quant produced a wrong final number (180 vs 540; 126 vs 366)
  while fp16 got it right — genuine arithmetic-reasoning collapse, not a scoring artifact.
- CAVEAT/CONFOUND found: the 'general' open-ended domain shows huge delta (0.39 mean) but that is
  quant-vs-full DIVERGENCE (both outputs fine, reworded) NOT quality loss — excluded from headline.
=> **The load-bearing assumption SURVIVES: real quant degradation IS request-dependent & heavy-tailed.**

## (2) REAL PRE-DECODE FEATURE AUC + oracle gap
Features: prompt log-perplexity (from QUANT prefill), prompt length, arith-marker count, domain tag, long-ctx flag.
- Predicting sensitivity (delta>0.2): full-feature 5-fold CV-AUC = **0.838** (thr0.15: 0.844; thr0.3: 0.780).
- BUT the AUC is carried ALMOST ENTIRELY by the DOMAIN TAG, not by prompt-perplexity:
  single-feat log_ppl AUC=0.824 — *however* this is because perplexity is itself a domain proxy
  (arith prompts have systematically different ppl). The decisive test is WITHIN domain:
  - **arith ppl-only AUC = 0.591, longqa = 0.456 (chance), general = degenerate (95% positive).**
  => Once you know the domain, prompt-perplexity adds ~NOTHING. The "prediction" is domain routing.

## (3) *** QUANT-SENSITIVITY vs GENERIC DIFFICULTY ROUTER — RELABELING TEST ***
Same features, sensitivity-target (delta large) vs generic-difficulty-target (quant quality low):
- sensitivity router AUC=0.838; **generic difficulty router (oriented) AUC on sensitivity=0.813.**
- **Sensitivity-specific ADVANTAGE = +0.025 AUC (negligible, within noise).**
- corr(delta, quant_quality) = -0.28 (weak). The signal both routers exploit is DOMAIN + difficulty.
=> **NOVELTY COLLAPSES TO RELABELING.** A generic difficulty/domain router does essentially as well.
   There is no quant-SENSITIVITY-specific pre-decode signal beyond generic difficulty here.

## (4) TRUE FLOPs / COST ACCOUNTING (skip-cheap-decode)
Per request (2*P*tok, P=1.54e9): avg prompt=178 tok, decode~71 tok.
- prefill FLOPs=5.47e11; quant-decode=2.17e11; full-decode=2.23e11.
- **The router is NOT free: the quant PREFILL needed to extract prompt-ppl = 5.47e11 = 71.6% of a
  full quant forward pass.** The "skip the cheap DECODE" framing is BACKWARDS for this model: prefill
  (178 tok) DOMINATES decode (71 tok), so skipping decode saves little.
- Worse, when you reroute a quant-sensitive request to FULL, you pay full prefill+decode (7.70e11)
  having ALSO already paid quant prefill — net +5.53e11 FLOPs per rerouted req. The decode you skipped
  (2.17e11) is SMALLER than what you spend. **The "skip cheap decode" cost-win does not materialize
  at these prompt:decode ratios.** (It could only help when decode >> prefill, i.e. long-generation
  workloads — not measured here, and pre-declared as the only place the cost story could survive.)

## (5) REAL CONFIDENCE-THRESHOLD CASCADE at TRUE cost
Quant mean-token-logprob as post-decode confidence; escalate low-confidence to full.
- At matched escalation fraction the PRE-DECODE router has LOWER cost (skips quant decode) and
  comparable quality at low f — BUT confidence AUC predicting sensitivity = 0.695, and at f>=0.6 the
  cascade reaches HIGHER quality (it sees the real output). At true cost the two Pareto fronts overlap;
  neither dominates. Confidence-cascade is competitive and uses a strictly more-informed signal.

## VERDICT (committee#2-ready): **RELABELING / WEAKEN (effective refute of the NOVEL claim)**
- SURVIVES: real quant degradation is heavy-tailed & request-dependent (the assumption committee#1
  flagged is TRUE — good news for the premise).
- DIES: (a) the predictive signal is DOMAIN/generic-difficulty, NOT a quant-sensitivity-specific
  signal — within-domain perplexity is at chance; (b) a generic difficulty router matches it
  (+0.025 AUC); (c) the "skip cheap decode" cost-win is negative at measured prompt:decode ratios
  (prefill dominates); (d) a real confidence cascade is competitive at true cost.
- The novel contribution (a QUANT-SPECIFIC pre-decode router beating generic difficulty routing AND
  a cost-win from skipping decode) is NOT supported. It collapses to generic difficulty/domain routing.

## HONEST RESIDUAL (where the claim could still live, NOT shown here)
- Long-generation workloads (decode >> prefill) could revive the cost story — untested.
- A larger/stronger quant (7B AWQ/GPTQ) MIGHT expose a quant-specific signal distinct from difficulty.
  Recommend that as the ONLY revival path; otherwise converge.

## PATHS
- devgpu014: /home/dengcchi/ros-EXP-0022/ (PRE_REGISTRATION.md, run_eval.py, analyze.py,
  results_raw.json, summary_stats.json, run_eval2.log, RESULTS.md)
- Mac: /Users/dengcchi/autonomous-research-v3/experiments/2026-06-03/EXP-0022/

## committee#1 reference: VERDICT-0019 yellow (required this exact real degradation + head-to-head + true cost).
