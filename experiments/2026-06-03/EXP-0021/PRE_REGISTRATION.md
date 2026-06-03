# PRE-REGISTRATION — EXP-0021 (L1, CLAIM-0014, PROJ-0003, TASK-0020)
researcher-gpu-0021 | committed BEFORE running results. Honest pipeline. Negatives / prior-art-dominated = WINS.
Nodes: cli:devgpu014 (8xH100, devgpu014.eag3.facebook.com, NOT fragile, real egress via fwdproxy, reuse
ros-EXP-0003 .venv: torch 2.11+cu130, vllm 0.22.0, flashinfer 0.6.11, transformers 5.9). cli:dengcchi-mac = engine + artifact dir.
Budget: <=120 min wall, <=2 GPU-hours, 1 GPU sufficient.

## CONTEXT — L1 of a YELLOW L0 (VERDICT-0018)
The L0 (analytic + Monte-Carlo, modeled FAIR-SHARE PCIe) tested a tiered KV-offload policy that proactively
DEMOTES a session's cold prefix KV to host memory during the agent inter-turn idle gap and PREFETCHES it back
on resume (overlapping fetch with the gap), claiming it beats evict-and-recompute on the effective-batch / TTFT
Pareto. L0 found it wins in 93.5% of cells but loses in a PCIe-contention corner.
Committee#1 verdict: (a) mechanism is LARGELY PRIOR ART — AttentionStore/CachedAttention (Gao, USENIX ATC
2024), Pensieve, SGLang HiCache, vLLM-v1 KV offload all do turn-gap-timed proactive demote+prefetch; the only
candidate novelty is the PCIe-contention KILL-CORNER characterization. (b) L0 baselines were a strawman
(full O(N) recompute) and did not isolate gap-timing.

## THE CLAIM UNDER TEST (CLAIM-0014)
Tiered KV-offload (proactive demote-during-gap + prefetch-on-resume, overlapping fetch with idle gap) beats
evict-and-recompute on effective-batch/TTFT Pareto for agentic multi-turn serving.

## REQUIRED EVIDENCE (from VERDICT-0018)
E1. *** REAL concurrent PCIe / NVLink-C2C bandwidth *** under simultaneous D2H + H2D + active-decode traffic
    on the H100. Measure cudaMemcpyAsync D2H+H2D effective GB/s WHILE a decode-like GEMM kernel runs; report
    contended GB/s vs nameplate (PCIe Gen5 x16 ~= 64 GB/s/dir; SXM H100 has no C2C, uses PCIe to host).
    Load-bearing: L0 assumed fair-share; real arbitration likely WIDENS the kill-corner.
E2. Add omitted baselines: (a) REACTIVE fetch-on-demand (prefetch ON RESUME — pays latency, wastes ZERO BW on
    p_rr<1 misses); (b) PREFIX-CACHED recompute (recompute only UNIQUE suffix, a la RadixAttention/vLLM APC).
    Compare demote+prefetch vs BOTH on resume-TTFT + wasted-PCIe-BW + P99.
E3. Real KV sizes + real transfer: move realistic 7B-class GQA prefix KV host<->GPU, measure real fetch latency
    vs gap. vLLM/LMCache CPU-offload if standable; else real-transfer microbench + analytic prefill (labeled).
E4. Live >=2-source prior-art sweep vs AttentionStore/CachedAttention (ATC24) + Pensieve + SGLang HiCache:
    MECHANISM-DELTA TABLE. If mechanistically identical, contribution collapses to kill-corner; report so.
E5. Real agent inter-turn gap distribution if obtainable, else state unavailable (LogNormal + sensitivity).

## METHODS COMPARED (resume-TTFT, wasted-PCIe-BW, P99)
- DEMOTE+PREFETCH (claim): proactive D2H demote during gap, H2D prefetch overlapping gap, recompute on miss.
- REACTIVE fetch-on-demand: no proactive work; on resume H2D fetch prefix (full latency, 0 wasted BW).
- PREFIX-CACHED RECOMPUTE: recompute only unique suffix (shared sysprompt prefix cached); cost = suffix prefill.
- FULL-RECOMPUTE: L0 strawman reference.

## MEASUREMENT PLAN
1. Real GPU microbench: realistic prefix-KV tensors; pure H2D, pure D2H, CONCURRENT D2H+H2D, each idle and with
   a concurrent decode-proxy GEMM stream saturating SMs. GB/s + p50/p99 per-transfer latency; sweep KV sizes.
2. Plug REAL contended BW into L0-style cost model; re-run demote+prefetch vs reactive vs prefix-cached across
   (gap, prefix_len, p_rr, concurrency). Report how kill-corner moves vs L0 fair-share.
3. Real KV transfer latency vs gap distribution (E5 if available).
4. Prior-art mechanism-delta table (E4).

## HONEST-NEGATIVE BRANCH (pre-committed)
Report NEGATIVE / prior-art-dominated if ANY of: real concurrent PCIe BW << nameplate (widening kill-corner to
dominate realistic traffic); OR reactive-fetch comparable (no gap-timing advantage); OR prefix-cached-recompute
makes recompute cheap enough that prefetch's win shrinks materially; OR AttentionStore/Pensieve/HiCache
mechanistically identical (no novelty -> contribution = kill-corner only). A clean "mechanism = prior art,
kill-corner is the only contribution" is a WIN.

## SAFETY
Cap GPU mem (<= ~40 GB), NO unbounded VMM probes, watch host RAM for pinned buffers, clean up GPU procs at end
via nvidia-smi. <=2 GPU-hours / 120 min wall.
