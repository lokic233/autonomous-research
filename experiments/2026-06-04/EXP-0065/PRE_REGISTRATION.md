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
- N concurrent decode requests piggyback EVERY iteration; each decode contributes base_decode_cost/iter.
- A decode request's ITL = wall-clock duration of the iteration it sits in.
- Iteration duration = base_decode_work(N decodes) + prefill_token_work(this iter, capped at B)
                       + ViT_burst landing this iter (UNCHUNKED — whole ViT forward for a touched image
                         runs ATOMICALLY in ONE iteration, NOT spread across the token budget).
- Encoder-cache: removes RECOMPUTE on cache hit; but FIRST-TOUCH burst per distinct image still lands
  unchunked. We model FIRST-TOUCH (cold) — each distinct image's ViT forward fires once, atomically.
- Mechanism under test: the unchunked-ViT-burst-inside-a-decode-iteration. NOT baked to force the answer.

## ViT COST MODEL + ANCHORED/SWEPT RATIO (anti-tuned-knob)
vit_cost(image) = per_image_fixed + per_token_marginal * tokens_in_image
- per_token_marginal: the patch-matmul / attention work, scales with image tokens (the part the token
  budget CAN see).
- per_image_fixed: per-image kernel-launch chain + encoder-batch padding + projector setup + Python
  dispatch — the part the token budget CANNOT see, INVARIANT to image size, paid ONCE PER IMAGE.

ANCHORING (published basis, stated):
- CUDA kernel-launch overhead ~5-25 us each (NVIDIA Nsight Systems blog, developer.nvidia.com). A ViT
  forward dispatches O(10s-100s) of kernels (patch-embed conv, N transformer blocks x {qkv, attn, proj,
  mlp x2, 2x norm}, merger/projector). At ~28 layers (Qwen2-VL ViT) x ~7 kernels + embed + projector
  ~= 200 kernels -> fixed launch chain alone ~1-5 ms on top of memory-alloc/padding/Python dispatch.
- per_token_marginal: a 1280-d ViT block over T tokens is bandwidth/compute bound; on H100 a few-hundred-
  token image's marginal patch work is ~tens of us per token-equivalent at small T, dropping as kernels
  saturate. Realistic ViT-forward microbench: a single small image (~256 img-tokens) ~3-10 ms total;
  a large image (~4096 img-tokens) ~15-40 ms. This implies fixed is a NON-TRIVIAL fraction at small per-
  image token counts and amortizes at large counts.
- We express the knob as RATIO r = per_image_fixed / per_token_marginal (units: tokens-equivalent).
  Plausible published range swept: r in {16, 64, 256, 1024, 4096} token-equivalents.
  (r=256 means the fixed per-image overhead equals the marginal cost of 256 image-tokens — i.e. for
   images smaller than 256 tokens, fixed dominates; larger, marginal dominates.)
- We SWEEP r across this whole range and REPORT THE CROSSOVER r at which image-count-dependence becomes
  material (>=1.2x). The result depends on the swept external ratio, NOT a hand-tuned value.

## ALIAS-BREAK CONTROL (causal isolation)
Hold TOTAL image-token-count T FIXED; vary image COUNT k in {1,2,4,8}.
  (a) k=1: one image of T tokens.
  (b) k>1: k images of T/k tokens each (sum = T).
Token budget's view: same T in both -> prices identically -> same prefill_token_work.
ViT-cost view: total ViT = k*per_image_fixed + per_token_marginal*T  -> fixed term scales with k.
Any ITL difference between (a) and (b) at fixed T is attributable to image COUNT, not token-count.

## T SWEEP (regime mapping)
T in {256, 1024, 4096, 16384} image-tokens. Small T -> per-image fixed more dominant (HELD region);
large T -> per_token_marginal*T dominates -> the NULL EXIT region.

## METRICS
Decode-stream ITL distribution -> p99 (and p999) per condition (k, T, r). GT = harness-set true per-request
ViT cost from the cost model. ITL read from iteration wall-times. Headline = ITL_p99(k) at fixed T,r.

## DECISION RULE
- HELD/support: ITL p99 grows materially with k at fixed T (>=1.2x for k=8 vs k=1) across a realistic
  chunk of the anchored ratio range (r in plausible published band) at realistic T.
- REGIME-BOUNDED/keep-exploring: material only at small T and/or high r -> report the regime + crossover.
- NULL/weaken-or-kill: ITL p99 ~invariant to k at fixed T across the realistic ratio range (token budget
  is the right unit) -> claim FALSE, honest negative. Also kill if material only at implausible r.

## ANTI-CIRCULAR STATEMENT
The scheduler does not bake in image-count-dependence. With per_image_fixed=0 the model MUST return NULL
(pure token accounting). The effect, if any, emerges only from (external swept r) x (unchunked atomic ViT
mechanic). We will verify the per_image_fixed=0 sanity null as a control.
