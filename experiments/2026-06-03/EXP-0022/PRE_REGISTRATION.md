# PRE_REGISTRATION — EXP-0022 (L1)
claim=CLAIM-0015 | exp=EXP-0022 | task=TASK-0021 | proj=PROJ-0004
researcher=researcher-gpu-0022 | node=devgpu014 (8xH100) | date=2026-06-03

## CLAIM UNDER TEST
A cheap PRE-decode router predicts per-request whether low-bit quantization will
materially degrade THIS request's output (from prompt perplexity / domain / arith /
long-ctx markers) and routes only quant-sensitive requests to the full-precision model
— beating all-quant / all-full AND a confidence-threshold cascade at matched budget.

L0 (synthetic, VERDICT-0019, YELLOW): ties confidence-cascade at low noise (CI∋0);
the real win is claimed to be COST not quality. Committee#1: the load-bearing assumption
(real quant degradation is request-dependent & predictable) is ASSUMED, not measured.
Novelty may collapse to relabeling generic difficulty-routing.

## REAL SETUP (honest, bounded)
- Model PAIR: Qwen2.5-1.5B-Instruct (cached). FULL = fp16. QUANT = bitsandbytes 4-bit NF4
  (double-quant). This is a REAL low-bit weight quantization (production-grade, robust on
  torch2.11/cu13 where AWQ/GPTQ prebuilt kernels are fragile). Same weights, same prompts.
  If time/budget allows, also try Qwen2.5-7B pair for a stronger degradation signal.
  HONEST CAVEAT pre-declared: NF4 is the quant we can run reliably in-budget; AWQ/GPTQ may
  differ. We report the method used.
- Eval prompts (real, span domains): GSM8K (arithmetic), CoQA / long-context QA (cached),
  general instruction prompts. Target ~300-450 prompts total across domains.
- Metric: per-request quality delta full-vs-quant. GSM8K=exact-match numeric answer;
  QA=token-F1 vs reference; general=token-F1 / ROUGE-L overlap vs full-precision output
  (full as reference for open-ended). Degradation delta_i = quality_full_i - quality_quant_i.

## MEASUREMENTS (the 5 required-evidence items)
1. *** REAL per-request quant-degradation distribution *** delta_i across all requests.
   Report: mean, std, skew, kurtosis, fraction with delta>threshold, Gini, tail mass.
2. PRE-decode feature AUC: features = prompt perplexity (from QUANT model prefill),
   domain tag, arith-marker count, prompt length / long-ctx flag. Predict label
   (delta_i materially-degraded). Real ROC-AUC + oracle gap (vs perfect routing Pareto).
3. HEAD-TO-HEAD vs GENERIC difficulty router: train a generic difficulty predictor
   (predict P(quant gets it WRONG) i.e. quant-quality-low, RouteLLM/Hybrid-LLM style) on
   SAME features, vs quant-SENSITIVITY predictor (predict delta_i large). Does sensitivity
   add AUC / Pareto beyond generic difficulty? If not -> RELABELING.
4. FLOPs/$ cost accounting: price the QUANT-model PREFILL needed to extract prompt-ppl
   (router is NOT free). Core reframed contribution = "skip the cheap DECODE". Quantify in
   real FLOPs: prefill_flops vs decode_flops vs full-precision rerun cost.
5. Real post-decode confidence baseline: quant-model output logprob/entropy (mean token
   logprob) as confidence-threshold cascade. Compare Pareto at TRUE matched cost (prefill+
   partial-decode for confidence vs prefill-only for pre-decode router).

## HONEST-NEGATIVE BRANCHES (pre-committed)
- If real quant-degradation is ~UNIFORM (low skew/kurtosis, no heavy tail, ~all requests
  degrade similarly OR ~none do) -> **CLAIM DIES**. Routing has nothing to exploit.
- If pre-decode features don't predict real degradation at useful AUC (~<0.65) -> **DIES**.
- If a GENERIC difficulty router matches the quant-specific router (ΔAUC ~0, overlapping
  Pareto) -> **NOVELTY COLLAPSES TO RELABELING**.
- If a real confidence-threshold cascade matches/beats pre-decode routing at true cost ->
  the COST-win is the only survivor; quantify it or converge.
- Only HELD/STRENGTHEN if: degradation heavy-tailed AND pre-decode AUC useful AND
  quant-specific beats generic AND beats confidence-cascade at true cost.

## BUDGET: <=120min wall, <=2 GPU-h. Single GPU. Clean up procs at end.
