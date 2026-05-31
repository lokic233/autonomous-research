# Related Work — PROJ-0001 (GPU CUDA-VMM for agentic KV branching)

| Work | Venue/Year | Core idea | Diff from our claims | Collision risk |
|---|---|---|---|---|
| vAttention | arXiv 2405.04437 2024 | CUDA VMM for KV cache, contiguous VA, unmodified attention kernel | read-only sharing; no fork/CoW branching | medium |
| vLLM PagedAttention | SOSP'23 2023 | paged KV cache + prefix caching (APC) | per-request lifecycle, software refcount; no branch CoW | medium |
| SGLang RadixAttention | NeurIPS'24 2024 | radix-tree prefix sharing, software refcount | software, not HW MMU CoW; captures token-prefix=KV sharing (=> DEAD-0006) | high |
| FlashInfer | github.com/flashinfer-ai 2024 | production paged-attention kernels | kernel lib; the dominant perf baseline (41-152x faster than HW CoW) | low |
| Continuum | arXiv 2511.02230 2025 | KV-cache TTL retention across pauses | retains existing KV; no speculative prefill of predicted continuation | medium |
| Speculative Tool Calls | arXiv 2512.15834 2025 | speculatively issue tool calls to fill idle gaps | speculates WHICH tool; not engine-side continuation prefill | medium |

## Collision summary
GPU CUDA-VMM for KV is occupied (vAttention/PagedAttention). Our contribution is the NEGATIVE/characterization angle (CoW dominated, vendor ceiling cliff, compounding collapse) + the attention-visible write-after-share capability delta — outside the read-only-sharing prior art.
