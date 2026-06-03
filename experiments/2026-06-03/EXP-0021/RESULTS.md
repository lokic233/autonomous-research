# RESULTS — EXP-0021 (L1, CLAIM-0014, PROJ-0003, TASK-0020)
researcher-gpu-0021 | cli:devgpu014 (1x H100 SXM5, PCIe Gen5 x16 to host) | honest pipeline.
Pre-reg committed BEFORE results (e279314). venv: torch 2.11+cu130, transformers 5.9.
VERDICT: **PARTIAL / PRIOR-ART-DOMINATED — claim WEAKENED. Mechanism is prior art; the kill-corner moved
AGAINST the claim (reactive fetch-on-demand strictly dominates whenever p_rr<1); and even the kill-corner
CHARACTERIZATION (the L0's last-resort novelty) is itself prior art (Meng/Lee/Wang kappa_crit, arXiv 2601.19910).**

================================================================================
## E1 — REAL CONCURRENT PCIe BANDWIDTH UNDER CONTENTION (the load-bearing number)
Measured on H100 SXM5, pinned host memory, bf16, cudaMemcpyAsync via torch copy on dedicated streams.

  Direction / regime              effective GB/s (p50)    vs nameplate (Gen5 x16 ~64 GB/s/dir)
  ------------------------------  --------------------    ------------------------------------
  H2D unidirectional              57.0  (p99 57.5)        89% of nameplate
  D2H unidirectional              53.5  (p99 53.6)        84% of nameplate
  BIDIRECTIONAL D2H+H2D (agg)     80-98 (size-dep)        NOT 110 (=57+53); ~75-90% of ideal sum
  BIDI + heavy decode (HBM-bound) 93.3  (p99 93.6)        only -4.7% vs bidi-idle (97.9)
  decode-proxy verified HBM load                          2135 GB/s (64% of 3.35 TB/s HBM3 nameplate)

  *** KEY FINDING (contradicts L0's pessimism in one axis, confirms it in another) ***
  - Concurrent ACTIVE DECODE barely touches PCIe BW (-4.7%). On H100 the copy engines (DMA) are
    INDEPENDENT of SM/HBM traffic. The L0's "fair-share PCIe under active decode" assumption was
    PESSIMISTIC for the compute-vs-copy case — real arbitration is BETTER than fair-share there.
  - The REAL bandwidth tax is BIDIRECTIONAL self-contention: simultaneous D2H (demote of session A) +
    H2D (prefetch of session B) yields ~80-98 GB/s aggregate, i.e. each direction collapses to
    ~40-46 GB/s (vs 53-57 solo) — a ~20-25% per-direction penalty. This is exactly the regime a tiered
    demote+prefetch policy CREATES (it demotes and prefetches at once), so it pays its own tax.

================================================================================
## E2/E3 — DEMOTE+PREFETCH vs REACTIVE FETCH-ON-DEMAND vs PREFIX-CACHED RECOMPUTE
Real GQA KV bytes (Llama-3-8B GQA8, bf16): 2k=262MB, 8k=1049MB, 16k=2097MB, 32k=4194MB.
Real measured single-H100 prefill throughput (SDPA, 32 layers): 2k=40k tok/s, 8k=36k tok/s, 16k=31k tok/s.
(Prefill is FAR cheaper than the L0's strawman assumed — this alone shrinks prefetch's win.)

### Resume-TTFT (ms), prefix=8000, real measured BW + prefill:
  gap   p_rr | demote+prefetch | reactive-fetch | prefix-cached-recompute | full-recompute(L0 strawman)
  200   1.0  |       0.0       |     18.4       |        80.0             |        222
  800   0.7  |       0.0       |     12.9       |        56.0             |        155
  3000  0.4  |       0.0       |      7.4       |        32.0             |         89
  -> Prefetch "wins" resume-TTFT only by hiding an ~18ms fetch in the gap. 18ms is NEGLIGIBLE vs typical
     multi-second agent gaps. Reactive pays ~5-37ms on resume; prefix-cached ~30-80ms. All sub-100ms.

### THE KILL-CORNER, RE-MEASURED — effective serving capacity (max resume-cycles/sec on the PCIe channel,
### the metric that actually decides effective batch). Higher = better.
  prefix  p_rr  KV_MB | demote+prefetch | reactive | prefix-cache(compute-bound)
   2000   1.0    262  |     171.7       |  171.7   |    50.0
   2000   0.7    262  |     171.7       |  202.0   |    50.0
   2000   0.4    262  |     171.7       |  245.2   |    50.0
   8000   1.0   1049  |      42.9       |   42.9   |    11.3
   8000   0.7   1049  |      42.9       |   50.5   |    11.3
   8000   0.4   1049  |      42.9       |   61.3   |    11.3
  16000   1.0   2097  |      21.5       |   21.5   |     4.8
  16000   0.7   2097  |      21.5       |   25.2   |     4.8
  16000   0.4   2097  |      21.5       |   30.7   |     4.8

  *** KILL-CORNER VERDICT ***
  - At p_rr=1.0 (every idle session resumes): demote+prefetch == reactive (identical PCIe demand).
    Prefetch's ONLY edge is hiding ~18ms — negligible. NO throughput advantage.
  - At p_rr<1 (REALISTIC agentic traffic — many idle sessions abandoned/timed-out): reactive STRICTLY
    DOMINATES, serving 1.18x (p_rr=0.7) to 1.43x (p_rr=0.4) MORE resume-cycles/sec, because it wastes
    ZERO speculative H2D BW. Proactive prefetch burns 1x KV of H2D on every non-resuming session.
  - With REAL (high) PCIe BW, the kill-corner did NOT shrink to a corner — it BROADENED to dominate the
    entire p_rr<1 region. The proactive-prefetch advantage requires p_rr~=1 AND a gap long enough to
    hide a fetch that is already only ~5-90ms. That intersection is small; the loss region is large.
  - Prefix-cached recompute is PCIe-free (recompute unique suffix on GPU); it's compute-bound and here
    sustains fewer resumes/s than the PCIe policies at these sizes, but it is the right tier exactly when
    PCIe is saturated and suffixes are short — i.e. it removes the recompute baseline's strawman status.

================================================================================
## E4 — PRIOR-ART MECHANISM-DELTA TABLE (live >=2-source sweep)
  System (venue)                        | gap-timed proactive demote? | prefetch-on-resume overlap? | Delta vs CLAIM-0014
  AttentionStore/CachedAttention        | YES async save when session | YES scheduler-aware layerwise| NONE. Identical mechanism,
   (Gao, USENIX ATC 2024, 2403.19708)   | goes idle between turns      | preload overlaps GPU compute | more mature
  Pensieve (Yu&Li NYU, 2312.05516)      | YES stateful multi-turn      | YES pin/recall across tiers  | NONE on mechanism
  SGLang HiCache / RadixAttention       | YES hierarchical host/disk   | YES prefix-tree reuse+fetch  | NONE; adds prefix sharing
  vLLM v1 KV offload + APC               | YES CPU offload + block-swap | YES automatic prefix cache   | NONE
  Continuum (Berkeley/Stanford 2511.02230)| YES explicit AGENT multi-turn| KV-TTL idle-gap scheduling   | SUPERSEDES agent-gap framing
  Meng/Lee/Wang (UPenn/Intel 2601.19910)| analytical kappa_crit =      | PCIe-bound offload vs        | *** PRE-EMPTS the L0's
                                         | critical cached/prefill ratio| recompute crossover          | last-resort kill-corner ***

  *** E4 VERDICT: demote-during-gap + prefetch-on-resume is mechanistically IDENTICAL to AttentionStore/
  CachedAttention (ATC24), Pensieve, SGLang HiCache, vLLM-v1. NO mechanism-level novelty. The "agent
  inter-turn gap" framing is subsumed by Continuum. Worse: the PCIe-contention kill-corner (committee#1's
  identified last-resort contribution) is ITSELF prior art (Meng et al. kappa_crit, Dec 2025). The
  contribution collapses to a HARDWARE-SPECIFIC RE-MEASUREMENT of a known crossover on H100, plus the
  minor (possibly-novel) observation that the binding constraint is BIDIRECTIONAL self-contention, not
  compute-vs-copy fair-share. ***

================================================================================
## E5 — REAL AGENT INTER-TURN GAP DISTRIBUTION
  UNAVAILABLE. No wall-clock-timestamped agent multi-turn trace reachable on node (CoQA present but has NO
  turn timing). Reported honestly per pre-reg. Sensitivity substitute:
  - Real measured fetch times: 8k KV=18-23ms, 32k KV=74-91ms.
  - LogNormal gap (sigma=1): P(gap < fetch, prefetch can't fully hide):
      median 0.2s: 8k=1.5%, 32k=21.7%   median 0.5s: 8k=0.1%, 32k=4.3%
      median 1.0s: 8k=0.0%, 32k=0.8%    median 3.0s: 8k=0.0%, 32k=0.0%
  - Implication: for median gap >=0.5s, real PCIe is fast enough that BOTH prefetch AND reactive (nearly)
    fully hide the fetch. Gap-timing gives no material TTFT edge.

================================================================================
## SAFETY / BUDGET
  1 GPU, peak <40GB alloc, no VMM probes, GPU returned to 106MB idle / 0% util at end. Wall < 60 min,
  GPU-time well under 2 GPU-hours. Host pinned buffers freed.

## COMMITTEE#2-READY VERDICT: **WEAKEN (toward REFUTE on the core claim; MEASUREMENT-ONLY on what survives)**
  1. Mechanism = PRIOR ART (AttentionStore/Pensieve/HiCache/vLLM/Continuum). No novelty.
  2. With REAL PCIe BW + REAL prefill cost + the two omitted baselines, the claim's win region SHRINKS and
     the loss region BROADENS: reactive fetch-on-demand strictly dominates demote+prefetch for all p_rr<1
     (1.18-1.43x more effective serving capacity), and ties at p_rr=1 (where prefetch saves only ~18ms).
  3. Even the kill-corner characterization is pre-empted by Meng et al. kappa_crit (2601.19910).
  4. ONE mildly-novel measurement: binding PCIe constraint for tiered offload is BIDIRECTIONAL demote+
     prefetch self-contention (-20-25%/dir), NOT compute-vs-copy fair-share (~free on H100). Narrow,
     honest, measurement-only — not a systems contribution.

## ARTIFACT PATHS
  GPU node cli:devgpu014: /home/dengcchi/ros-EXP-0021/ (bench_pcie.py, bench_pcie2.py, real_prefill.py,
    kv_model.py, compare.py, killcorner.py, gap_sensitivity.py, *.json, *.csv, RESULTS.md)
  Mac instance: /Users/dengcchi/autonomous-research-v3/experiments/2026-06-03/EXP-0021/
    (PRE_REGISTRATION.md, RESULTS.md, pcie_bw.csv, killcorner.csv, ttft_compare.csv)
