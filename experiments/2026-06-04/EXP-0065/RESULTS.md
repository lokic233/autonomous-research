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
1. The prereg's PRIMARY prediction (stream-p99 >=1.2x for k=8 across realistic T) is NOT cleanly HELD:
   stream-p99 is material only at LARGE T, which is the OPPOSITE regime from where realistic
   Qwen2-VL images live AND from where the worst-case single-request stall bites. The honest verdict
   is REGIME-BOUNDED, and the choice of "which regime is bad" is metric-dependent.
2. killer #10 (genuine null exit): there IS a real null region — T>>B on worst-iter, and small-T on
   stream-p99. We report both honestly; neither metric shows the effect uniformly.
3. killer #9 (vLLM PR#8425 already said multimodal+chunked-prefill "doesn't work well"): our
   contribution is the QUANTIFIED, image-count-driven, token-budget-INVISIBLE axis (the fixed
   per-image ViT term scaling with k) that survives the encoder-cache RECOMPUTE fix. This is a
   different axis from the recompute bug PR#8425 fixed — but it remains a SIMULATION-LEVEL claim;
   the magnitude is entirely a function of the (anchored, plausible-but-unmeasured) r and of B. L1
   on real hardware is required to confirm the r and B that production actually runs at.

## WHAT L1 SHOULD MEASURE
Real vLLM-V1 chunked-prefill + per-image encoder-cache ON, H100 devgpu014, serving Qwen2-VL-7B.
Mixed trace: steady decode background (N~64) + inject ONE multimodal prefill at FIXED total
image-tokens T, varying image COUNT k in {1,2,4,8} (1 large image vs k small summing to T).
Measure real decode-stream ITL p99 AND p999/worst-iter, plus SLO-violation count, ATTRIBUTABLE to
image count at fixed T. Sweep T across realistic Qwen2-VL sizes (256-1280) AND large (4k-16k) to map
the material-vs-null regimes empirically. Measure the REAL r (per_image_fixed via single-image ViT
microbench at varying token counts -> intercept/slope) and the REAL chunk size B -> place production
on the crossover map. KEY L1 question: at production (T, B, r), does worst-iteration decode ITL /
SLO-violation depend on image count -> is the Sarathi-Serve stall-free guarantee silently broken for
multimodal by an image-count-driven, token-budget-invisible amount?

## ARTIFACTS
- sim.py — discrete-event Sarathi-Serve chunked-prefill scheduler (unchunked atomic ViT burst)
- results/itl_sweep.csv — 96 rows: (r,T,k) -> p99, p999, pmax, spike_vs_k1
