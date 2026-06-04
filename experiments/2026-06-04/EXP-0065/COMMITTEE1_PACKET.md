# COMMITTEE#1 — CLAIM-0057 (PROJ-0027, multimodal-serving) — chunked-prefill stall-free guarantee broken for multimodal (image-count-driven ITL)
## EMPIRICAL-PHENOMENON, effect=keep-exploring/REGIME-BOUNDED. NOT metric-validity (decode ITL = Sarathi-Serve's native SLO). NO closed-form headline. Anti-circular (r=0 -> spike EXACTLY 1.000, effect not baked in). Vote HONESTLY by role.

## CLAIM: with chunked prefill ON (vLLM-V1/SGLang default post-encoder-cache), the per-iter ViT burst is scheduled ATOMICALLY + NOT governed by the prefill TOKEN budget -> decode ITL p99 tail inflation from an interleaved image request is driven by image COUNT + per-image fixed ViT overhead, NOT the image-token-count the chunk budget prices. 1 large image vs k small (same total tokens T) -> materially different decode ITL spikes. Stall-free guarantee silently broken for multimodal by an amount the token budget can't see.

## L0 RESULT (CPU discrete-event Sarathi scheduler; ViT cost = k*per_image_fixed + per_token_marginal*T; ratio r EXTERNALLY ANCHORED from Qwen2-VL/Nsight + SWEPT):
MECHANISM CONFIRMED + ANTI-CIRCULAR PASSES: at fixed T, ITL spikes grow with image count k (the fixed term is budget-invisible, scales with k). r=0 -> k-spike EXACTLY 1.000 for all k, all T, BOTH metrics -> NOT baked in; emerges only from (swept r) x (unchunked-atomic-ViT mechanic).
KILLER-#10 NULL EXIT IS REAL + PARTIALLY HIT — the material regime FLIPS by tail metric: WORST-ITER ITL (single-request stall, the SLO tail) material at SMALL T<=B (k ViT bursts COALESCE into one super-inflated chunk-iter, up to 7.3x@r=4096; washes out at large T); STREAM-P99 (the prereg's PRIMARY metric) material at LARGE T>>B (bursts spread across chunk-iters, up to 6.8x; invisible at small T). So the prereg's PRIMARY prediction (uniform stream-p99) did NOT cleanly hold -> REGIME-BOUNDED, NOT HELD.
CROSSOVER (smallest r for >=1.2x worst-iter, k=8 vs k=1): T=256->r=16; T=1024->r=64; T>=4096->NONE in range (genuine NULL region — per_token_marginal*T dominates, token budget IS the right unit there).
PUBLISHED ANCHORING r=per_image_fixed/per_token_marginal: Qwen2-VL ViT ~200 CUDA kernels x 5-25us launch (Nsight) ~1-5ms fixed/image; ~4us/token marginal -> realistic r~64-1024. Realistic Qwen2-VL image T~256-1280 -> worst-iter spike MATERIAL 1.25-5.9x in the realistic band.

## THE LIVE RISKS TO ADJUDICATE (orchestrator flags these UPFRONT — they're the exact recent-yellow failure modes):
(#9 ACKNOWLEDGMENT) vLLM PR#8425 ALREADY says 'multimodal+chunked-prefill doesn't work well' + encoder-cache PRs fixed a version. The claim's defense: the residual image-COUNT-driven LATENCY axis (k*per-image-fixed-ViT, budget-invisible) survives the encoder-cache RECOMPUTE fix = a DIFFERENT axis. Is that a genuine unacknowledged contribution, or 'quantifying a known interaction the maintainers already flagged'? (the CLAIM-0054/0056 modest-ceiling pattern.)
(REGIME) the effect is material only on the WORST-ITER (single-stall) metric at SMALL realistic T; the prereg's PRIMARY stream-p99 is material in the OPPOSITE (large-T) regime. Is 'worst-iteration single-request stall at realistic Qwen2-VL image sizes' a candidate-grade SLO finding, or too regime-narrow (p99 invisible)?
(SIM-LEVEL) magnitude = f(anchored-but-UNMEASURED r, chunk size B). The mechanism is clean but the real magnitude needs the L1 microbench of real r + B. Is the L0 sufficient to establish the MECHANISM (the anti-circular control + the genuine null-exit make it non-tautological) pending the L1?

## CLAIM YAML
claim: "In production multimodal LLM serving with chunked prefill enabled (the vLLM-V1/SGLang\
  \ default after the encoder-cache work), the per-iteration vision-encoder (ViT)\
  \ compute burst is scheduled ATOMICALLY and is NOT governed by the prefill token\
  \ budget \u2014 so decode-side inter-token-latency (ITL) p99 tail inflation from\
  \ an interleaved image request is governed by ViT encoder cost (driven by image\
  \ COUNT and per-image fixed overheads), NOT by the image-token count the chunk-prefill\
  \ token budget accounts for. For two multimodal requests with IDENTICAL total image-token\
  \ counts but different image COUNTS (one large image vs many small summing to the\
  \ same token count), Sarathi-style chunked prefill produces materially different\
  \ decode ITL p99 spikes, because the token-budget scheduler prices both identically\
  \ while the ViT forward (run unchunked, per-image) does not \u2014 so the stall-free\
  \ guarantee chunked prefill provides for text is silently broken for multimodal\
  \ by an amount the token budget cannot see."
why_it_matters: "FRESH AREA (multimodal-serving: chunked-prefill x vision-encoder).\

## L0 RESULTS (EXP-0065)
# RESULTS — EXP-0065 / CLAIM-0057
researcher-0063 | PROJ-0027 | TASK-0055 | L0 CPU-only stdlib SERIAL
Run AFTER committed PRE_REGISTRATION.md. Honest pipeline — null exit was genuinely possible.

## VERDICT: REGIME-BOUNDED (mechanism CONFIRMED; materiality is metric- and T-dependent)
Effect = **keep-exploring** (support of the mechanism, but the headline materiality is regime-bounded,
NOT the uniform-across-T HELD the prereg's primary p99 prediction expected).

## HEADLINE (the honest, two-metric result)
The claim's CORE MECHANISM is confirmed and the anti-circular control passes: at fixed total
image-token-count T, decode ITL spikes grow with image COUNT k — an inflation the token budget
prices identically (same T) but the unchunked per-image ViT forward does not. BUT which T-regime is
"material" FLIPS depending on which tail metric the SLO targets, and the prereg's primary metric
(stream p99) and the SLO-relevant metric (worst-iteration ITL) tell OPPOSITE regime stories:

| metric                              | material regime         | null regime        |
|-------------------------------------|-------------------------|--------------------|
| worst-iteration ITL (single stall)  | SMALL T (T <= B)        | LARGE T (T >> B)   |
| stream p99 over 400-iter window     | LARGE T (many chunks)   | SMALL T (1 fat iter)|

This is the real finding: it's the same mechanism viewed two ways. At small T (T<=B=512) all k
images' tokens schedule in ONE chunk-iteration, so all k unchunked ViT bursts COALESCE into a single
super-inflated iteration (worst-case ITL up to 7.3x at r=4096) — devastating for the unlucky request's
ITL but a single point that hides below stream-p99 in a busy decode pool. At large T (T>>B) the prefill
spans many chunk-iterations, the k bursts SPREAD across them, each iteration carries ~one extra fixed
burst -> visible in stream p99 (up to 1.36x at the realistic band), but no single catastrophic stall.

## ANTI-CIRCULAR CONTROL (passed)
With per_image_fixed = 0 (r=0): k-spike is EXACTLY 1.000 for all k, all T, on BOTH metrics.
The image-count dependence is NOT baked into the scheduler — it emerges only from
(external swept r) x (unchunked-atomic-ViT mechanic). PASS.

## ViT COST RATIO — ANCHORED + SWEPT (anti-tuned-knob)
r = per_image_fixed / per_token_marginal, in image-token-equivalents. Swept r in {0,16,64,256,1024,4096}.
Published anchoring (stated in prereg): Qwen2-VL ViT ~28 layers x ~7 kernels + patch-embed conv +
merger/projector ~= 200 CUDA kernels; launch overhead ~5-25 us each (NVIDIA Nsight) -> fixed launch
chain + alloc/padding/Python dispatch ~1-5 ms per image. per_token_marginal ~ few us/token-equiv on H100.
=> REALISTIC BAND r ~ 64-1024 token-equivalents (fixed=1-5ms / marginal=0.004ms/tok). Qwen2-VL images
are typically 256-1280 tokens -> small/mid-T regime, exactly where worst-iter ITL is material.

## CROSSOVER (smallest r for >=1.2x worst-iteration ITL, k=8 vs k=1)
| T (img-tokens) | crossover r        | at realistic r~64-1024 |
|----------------|--------------------|------------------------|
| 256            | r=16  (very low)   | MATERIAL (1.9x-5.9x)   |
| 1024           | r=64               | MATERIAL (1.25x-2.8x)  |
| 4096           | >4096 (none)       | NULL (worst-iter ~1.0) |
| 16384          | >4096 (none)       | NULL (worst-iter ~1.0) |

So: for realistic Qwen2-VL image sizes (T<=~1280) AND realistic ViT overhead (r~64-1024), the
worst-iteration decode stall is MATERIALLY image-count-driven (1.25x-5.9x) — token-budget-invisible.
For large total-image-token requests (T>>B) the worst-iter effect WASHES OUT (genuine null region:
per_token_marginal*T dominates, the token budget IS the right accounting unit there).

## STREAM p99 (prereg primary metric) — k=8/k=1 spike
| r \ T | 256  | 1024 | 4096   | 16384  |
|-------|------|------|--------|--------|
| 0     |1.000 |1.000 | 1.000  | 1.000  |  <- control
| 64    |1.000 |1.000 | 1.091  | 1.091  |
| 256   |1.000 |1.000 | 1.364* | 1.364* |
| 1024  |1.000 |1.000 | 2.454* | 2.454* |
| 4096  |1.000 |1.000 | 6.818* | 6.818* |
(* >=1.2x). Stream-p99 materiality is the MIRROR of worst-iter: needs LARGE T (many chunk-iters to
register in p99) — exactly the regime where worst-iter washes out.

## HONEST FLAGS (to committee)

## PRE-REG
# PRE_REGISTRATION — EXP-0065 / CLAIM-0057
researcher-0063 | PROJ-0027 | TASK-0055 | L0 CPU-only stdlib SERIAL <=15min
Committed BEFORE running. Honest pipeline — negatives are wins. This claim has a GENUINE NULL EXIT (killer #10).

## THE CLAIM (CLAIM-0057)
With chunked prefill enabled (vLLM-V1/SGLang default, post-encoder-cache), the per-iteration ViT
(vision-encoder) compute burst is scheduled ATOMICALLY and is NOT governed by the prefill TOKEN budget.
Therefore decode-side ITL p99 tail inflation from an interleaved multimodal request is driven by image
COUNT + per-image fixed ViT overhead, NOT by the image-token count the chunk budget prices. Two multimodal
requests with IDENTICAL total image-token counts T but different image COUNTS (1 large vs k small summing
to T) produce materially different decode ITL p99 spikes — the token-budget scheduler prices both
identically; the unchunked per-image ViT forward does not.

## RISKY PREDICTION
Decode ITL p99 spike DEPENDS ON image COUNT k at FIXED total image-token-count T:
  ITL_p99(k=8, T) >= 1.2 * ITL_p99(k=1, T) at realistic anchored ViT overhead ratios.

## THE GENUINE NULL EXIT (killer #10 — the whole point)
NULL: ITL spike is INVARIANT to k at fixed T (per-image fixed ViT cost negligible vs per_token_marginal*T
at realistic T). -> the token budget IS the right accounting unit -> CLAIM FALSE -> clean honest negative
(informative: the encoder-cache fix restored the stall-free guarantee; multimodal chunked-prefill is
stall-fair). If invariant, we report NULL honestly.

## SCHEDULER (discrete-event, Sarathi-Serve chunked-prefill iteration-level)
- Fixed token budget B per iteration.

## ORCHESTRATOR NOTE: PRIOR-ART VERIFIED — Sarathi-Serve (2403.02310 OSDI24, token-work/iter bound, IS the baseline); vLLM PR#8425 (disabled multimodal-chunked-prefill hotfix); SGLang PR#5456/vLLM-V1 (encoder cache = production baseline, modeled). Novelty = the quantified image-count-driven token-budget-invisible LATENCY axis surviving the recompute fix. The L0 CLEARED killer-#10 (genuine null exit, real null region at T>>B + anti-circular control passes) + had the built-in causal-alias control (fix T vary k). If candidate-grade, L1: real vLLM-V1 chunked-prefill+encoder-cache ON, H100 devgpu014, Qwen2-VL-7B; inject multimodal at fixed T vary image-count -> real decode ITL p99 AND worst-iter + measure the REAL r (microbench intercept/slope) + real B -> place production on the crossover map. If you judge it's too regime-narrow (worst-iter-only) / too-close-to-the-acknowledged-PR-issue / the sim-level magnitude is unanchored -> YELLOW/RED honestly. If the mechanism + the realistic-band worst-iter-stall is a genuine SLO contribution -> approve toward the real-vLLM L1. Real 6/6 by role.
