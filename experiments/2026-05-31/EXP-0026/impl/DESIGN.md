# EXP (CLAIM-0006 gate-B FINAL): real vLLM PagedAttention E2E serving cell — the load-bearing measurement
Node: devgpu014 H100, ~/.conda/envs/py312conda/bin/python (vLLM 0.6.6.post1, PagedAttention non-contiguous KV).
VERDICT-0029's load-bearing requirement: does CDC's contiguous-recompute advantage SURVIVE the dominant
production serving stack (PagedAttention's NON-CONTIGUOUS paged KV layout), measured (not analytic)?

## METHOD (measured, real vLLM)
- Model: a HF model that fits 1 H100 fp16 (Qwen2.5-7B-Instruct or Llama-3-8B if cached; else smallest available).
- Serve via vLLM LLM() engine with PagedAttention (default). Reused prefix of length S, then a mid-prefix
  injection of R tokens (inj/seq = R/S) forcing KV repair of the affected region.
- TWO recompute strategies measured END-TO-END through vLLM:
  * CDC-contiguous: recompute the contiguous affected block (one prefill over a contiguous token range).
  * PIC-scattered (CacheBlend-style, implemented against vLLM PagedAttention since lmcache absent): recompute
    R new + a selective scattered fraction p of reused tokens (HKVD top-p), gathered from NON-CONTIGUOUS
    paged KV blocks — this is exactly where PagedAttention's layout could change the cost vs the kernel proxy.
- Metrics: E2E TTFT (ms, median+p95 over reps) AND batched throughput (tok/s) at batch {1,8,32}.
- Surface: inj/seq {1,5,25%} x seq {8k,32k}, INCLUDING inj/seq>=5% (the regime committee flagged PIC may win).
- Report CDC/PIC ratio per cell for BOTH TTFT and throughput; HONESTLY surface any cell where PIC wins.

## DECISION VALUE (R0)
This is THE load-bearing cell for unanimous GREEN (VERDICT-0029). It settles whether the advantage SIGN
survives PagedAttention non-contiguous layout — which the kernel proxy + analytic bridge structurally could not.
A measured negative (PIC wins under real serving) is publishable and equally decision-relevant.

## SAFETY (MI350X_CRASH_POSTMORTEM)
H100 (non-fragile) ONLY. Bounded: one vLLM engine + KV cache (gpu_memory_utilization<=0.6, ~60GB of 98GB).
NOT a mapping probe. host-mem-floor 300 watchdog; os._exit(0) teardown (vLLM holds CUDA graphs/NCCL — _exit
avoids slow destructor paths). Single GPU (tensor_parallel=1). Cap reps; do not chase large numbers.
