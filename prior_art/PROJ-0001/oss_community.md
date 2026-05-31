# OSS / Community Landscape — PROJ-0001

Implementations + community signal relevant to GPU KV-cache memory mechanisms. Refresh per freshness rules
(fast-moving: ~14 days).

| Project | What it ships | Relevance to our claims |
|---|---|---|
| vLLM (`vllm-project/vllm`) | PagedAttention + APC (automatic prefix caching) | The strong software baseline our negative results are measured against (CLAIM-0001/0003). |
| SGLang (`sgl-project/sglang`) | RadixAttention (radix-tree prefix sharing) | Captures token-prefix=KV sharing → killed our DEAD-0006. Baseline for CLAIM-0006. |
| FlashInfer (`flashinfer-ai/flashinfer`) | production paged-attention kernels | The dominant perf baseline (41–152× faster than HW VMM CoW). |
| LMCache | KV offload/retention | Adjacent to prefix-cache retention (Continuum-style). |
| TensorRT-LLM, DeepSpeed, TGI | inference engines | Third-engine cross-checks for workload claims (CLAIM-0005). |

## Watch (GitHub issues/PRs that could move the boundary)
- vLLM speculative/chunked-prefill scheduler work (vLLM #39060 = sparse-prefill TTFT, distinct concept).
- Any vendor VMM API change that lifts/alters the ~520K NVIDIA mapping ceiling (would affect CLAIM-0002/0004).
