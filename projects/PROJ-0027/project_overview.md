# PROJ-0027 — Multimodal-serving: chunked-prefill stall-free guarantee SILENTLY BROKEN for multimodal — ITL tail driven by image COUNT not image-token-count (EMPIRICAL PHENOMENON)
Fresh area: multimodal-serving (chunked-prefill x vision-encoder interaction). EMPIRICAL-phenomenon. Survivor of scout-L
(retrieval+agentic candidates failed Lesson-A synthesis). CLEARS killer #10 (genuine null exit) + Lessons B (built-in
causal-alias control) + C (production baseline = chunked-prefill+encoder-cache, NOT naive-off). THESIS: with chunked
prefill enabled (vLLM-V1/SGLang default post-encoder-cache), the per-iteration ViT compute burst is scheduled
ATOMICALLY + is NOT governed by the prefill TOKEN budget — so decode-side ITL p99 tail inflation from an interleaved
image request is governed by ViT cost (image COUNT + per-image fixed overhead), NOT the image-TOKEN-count the chunk
budget prices. Concretely: two multimodal requests with IDENTICAL total image-token counts but different image COUNTS
(1 large image vs many small summing to the same tokens) produce MATERIALLY DIFFERENT decode ITL p99 spikes — Sarathi
chunked prefill prices both identically but the ViT forward (unchunked, per-image) does not. The stall-free guarantee
is silently broken for multimodal by an amount the token budget cannot see. ★ ORCHESTRATOR FLAGS (scout-honest, the
LIVE risks = exactly the recent-yellow failure modes — adjudicate UPFRONT): (#9 acknowledgment) vLLM PR#8425 ALREADY
says 'multimodal+chunked-prefill doesn't work well' + encoder-cache PRs fixed a version -> the claim's defense is that
the residual LATENCY breakage (mis-accounted by the token budget) is a DIFFERENT unacknowledged axis from the
recompute/correctness bug they fixed — PLAUSIBLE BUT THIN, committee may judge it 'quantifying a known interaction'
(modest ceiling, CLAIM-0054/0056 pattern). (Lesson A synthesis) the non-obvious lift ('token budget is the wrong unit,
image-count is the driver') is real but adjacent to obvious-once-stated — the killer-#10 GENUINE NULL EXIT (ITL could
be image-count-INVARIANT at fixed tokens -> claim false) is the strongest defense vs synthesis. Passes the rest: NOT
metric-validity (ITL p99 = Sarathi's native SLO); NOT closed-form (image-count<->ITL depends on empirical ViT batching/
padding/kernel-launch); foundational incumbent Sarathi-Serve (2403.02310 OSDI24) named+benchmarked+IS the baseline; NOT
known-mechanism-costume + STRONGEST baseline (chunked-prefill+encoder-cache, not off); NOT wrong-currency (decode ITL);
NOT trivially-small (per-image ViT fixed cost = real multi-ms bursts inside 10-30ms decode iters -> visible p99);
anchored structurally (per-image fixed overhead real); standard mitigation (encoder cache PR#5456) MODELED IN as
baseline + claim survives (cache removes RECOMPUTE not first-touch BURST placement); citations read (Sarathi bound =
token-work/iter; Qwen2-VL ViT-tokens+FLOPs both scale w/ pixels -> resolution doesn't cleanly decouple -> decouple on
image COUNT at fixed tokens where per-image fixed cost diverges); no IID. L0 (CPU, no GPU): discrete-event Sarathi
chunked-prefill scheduler (token budget B/iter, decode piggyback, ITL=iter walltime); ViT cost = per_image_fixed +
per_token_marginal*tokens, the ratio EXTERNALLY ANCHORED from published Qwen2-VL/ViT microbench (swept across the
plausible range, NOT tuned). ALIAS-BREAK: fix total image-tokens T, vary image count (1xT vs kx(T/k)); measure decode
ITL p99. RISKY headline: spike(k-small) > spike(1-large), grows with k at fixed T. NULL EXIT (genuine): if ITL
invariant to k at fixed T (per_image_fixed negligible vs per_token_marginal*T at realistic T) -> token budget IS the
right unit -> claim FALSE -> honest negative (informative: encoder-cache fix restored stall-fairness). Anti-circular:
outcome depends on the measured ViT cost ratio (external input), not a tuned knob. L1: real vLLM-V1 (chunked-prefill+
encoder-cache ON) on H100 devgpu014 serving Qwen2-VL-7B, mixed trace steady-decode + injected multimodal at fixed
total-image-tokens varying image count -> real decode ITL p99/p999 + SLO-violation attributable to image-count.
