# PRE-REGISTRATION — EXP-0053 (L2, GPU H100)

- **Claim:** CLAIM-0048 — canonicalizer RECALL has a SIGN-FLIPPING effect on maj@k self-consistency
  accuracy governed by fragmentation asymmetry phi; higher recall can INVERT two models' maj@k
  ranking purely by swapping the grader, in the phi<<0 regime.
- **Researcher:** researcher-0051. **Hardware:** devgpu014 (NVIDIA H100). **Env:** conda ros-vllm07 (vllm 0.22.0).
- **Gate:** committee#2 VERDICT-0047 = YELLOW, gated on this L2 in the RIGHT regime (symbolic MATH),
  retiring 3 concerns: (1) headline inversion only seen in L0 sim; (2) MATH phi<<0 may be near-tautological;
  (3) recall-problem vs plain-plurality-problem.

## Models (FIXED before run)
- M1: Qwen/Qwen2.5-0.5B-Instruct (cached)
- M2: Qwen/Qwen2.5-7B-Instruct (cached)
- M3 (3rd model, different answer-surface concentration, if it loads in budget):
  Qwen/Qwen2.5-Math-1.5B-Instruct (math-tuned -> expected MORE concentrated answer surface),
  else fall back to meta-llama/Meta-Llama-3-8B-Instruct (cached, general).

## Data (FIXED)
- HuggingFaceH4/MATH-500, test split, boxed-answer problems. N >= 300 (use all 500 if budget allows).
- GT = boxed gold `answer` field (a real fact). Anti-circular: graders read only answer STRINGS;
  phi & accuracy scored vs gold.

## Sampling (FIXED)
- k = 32 samples/problem, temperature 0.8, top_p 0.95, max_tokens 1024.
- Multiple seeds folded into the k draws (single vLLM n=32 call per problem, seed=0; bootstrap over problems for CIs).
- Answer extraction: robust `\boxed{...}` extractor (balanced-brace), handles \frac, \dfrac, \sqrt, integers, pi, fractions a/b.

## Graders (reuse exp0051/canon.py) — 3 recall levels
- EXACT  = canon_exact (string strip) — LOW recall
- LEXICAL= canon_lexical (lowercase, strip units/$/commas/trailing .0) — MID recall
- NUMERIC= canon_numeric (sympy simplify of \frac/\sqrt/pi/fractions/decimals) — HIGH recall, q~1.0

## DELIVERABLE A — real-model-sample phi on MATH (retires Concern 2)
- For each problem & model: among the k samples, partition by NUMERIC-correct (== gold) vs wrong.
- H_C = Shannon entropy of EXACT surface forms among the TRULY-correct samples.
- H_W = Shannon entropy of EXACT surface forms among the DOMINANT wrong-answer cluster
  (the most-frequent wrong NUMERIC bucket).
- phi = H_C - H_W, measured PER PROBLEM from ACTUAL model-output frequencies (NOT a proxy generator).
- Report phi distribution (median, IQR, %phi<0) per model. Load-bearing: is real-model phi really <<0?

## DELIVERABLE B — 3-recall maj@k + the headline inversion (retires Concern 1)
- maj@k accuracy per model under EXACT, LEXICAL, NUMERIC (model+samples FIXED; only grader changes).
- (i) slope: is maj@k monotone non-increasing... NO — predicted DIRECTION: in phi<<0, higher recall
  should help the LEADER less / hurt relative standing; we report the slope sign honestly.
- (ii) HEADLINE: does ANY model pair's maj@k RANKING INVERT between EXACT and NUMERIC graders?
  Report with 1000x bootstrap-over-problems 95% CIs on the per-grader accuracy GAP. Inversion counts
  as DEMONSTRATED only if the gap CI excludes 0 on BOTH ends with opposite sign, or honestly NULL.

## DELIVERABLE C — spoiler-immune baseline (retires Concern 3)
- Re-aggregate the SAME samples per problem under Borda count over NUMERIC answer buckets
  (each sample ranks its bucket; Borda = bucket frequency weighting -> equivalently we use
  Borda over distinct buckets ranked by vote share). Also report a plurality-vs-Borda agreement.
- Does recall-sensitivity / inversion PERSIST under Borda? If it VANISHES, effect = plurality artifact,
  not canonicalizer-recall (honest scoping, weakens claim).

## DELIVERABLE D — semantic-entropy distinction (Kuhn2023 / Farquhar2024)
- Written 3-4 sentences reasoning from mechanism (prior-art search may be limited).

## DECISION RULE (pre-committed)
- HELD / green-worthy: real-model phi << 0 CONFIRMED (median phi clearly <0, majority of problems)
  AND a real model-pair maj@k inversion DEMONSTRATED on MATH between EXACT and NUMERIC with CIs
  AND it PERSISTS (or is honestly scoped) under Borda.
- KEEP-EXPLORING / still-YELLOW: phi<<0 confirmed + monotone recall slope, but NO clean inversion (null).
- WEAKEN / KILL: real-model phi ~0 or symmetric (near-tautology confirmed, no foothold) OR the
  effect is purely a plurality artifact that Borda removes.

## Budget & safety
- 60 min wall / 1.5 GPU-h. Single H100 (cap gpu_memory_utilization<=0.55), enforce_eager, os._exit(0) on done.
- devgpu014 H100 ONLY. NEVER devgpu499 (MI350X, fragile).
