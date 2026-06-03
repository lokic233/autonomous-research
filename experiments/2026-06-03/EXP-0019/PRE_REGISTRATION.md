# PRE_REGISTRATION — EXP-0019 (CLAIM-0014)
**Committed BEFORE running. L0: CPU-only, stdlib-only, SERIAL, analytic + trace sim. NO GPU/model/network.**

## Claim under test
For agentic LLM serving with bursty per-session KV pressure, a tiered KV-offload policy that
proactively DEMOTES a session's COLD prefix blocks to CPU/host memory (and PREFETCHES them back on
the session's next turn, overlapping fetch with the inter-turn idle gap) achieves a strictly better
effective-batch-size / TTFT Pareto than EVICT-AND-RECOMPUTE — because (i) agent inter-turn gaps are
long enough to hide PCIe fetch latency AND (ii) demoted blocks are re-referenced w/ high prob on resume.

## Two FALSIFIABLE parts
- **(A) Gap-vs-fetch:** Is the inter-turn idle gap >= host<->GPU KV fetch latency for realistic KV sizes
  AND under realistic CONCURRENCY (aggregate prefetch demand vs PCIe BW)?
- **(B) Pareto:** Does proactive demote+prefetch dominate evict-and-recompute on the
  (effective-batch-size, TTFT-on-resume) Pareto across the sweeps?

## Metrics (the two)
1. **Effective batch size B_eff** = number of *active/resumable* sessions servable given a fixed GPU-KV
   capacity. Offload frees GPU KV for cold sessions -> both policies raise B_eff vs no-offload, but the
   policies differ in *resume cost*. We report B_eff achievable at a target resume-TTFT budget.
2. **TTFT-on-resume** = time from "session resumes" to "first output token ready" = time to make the
   session's prefix KV resident again, on the critical path.
   - evict-recompute: TTFT_resume = prefill_recompute_time(prefix_len)  (FLOP-bound, GPU compute)
   - demote+prefetch: TTFT_resume = max(0, fetch_time - gap_overlap)  (PCIe-bound; if fetch hid in
     gap, ~0 extra; if BW-saturated or gap too short, residual stall). PLUS wasted-BW cost if the
     session does NOT resume (re-reference prob < 1).

## Models (all parameters cited / justified inline)
### KV size model (GQA, decode KV cache)
KV bytes per token = 2 (K,V) * n_layers * n_kv_heads * head_dim * bytes_per_elem.
Qwen2.5-7B-like: n_layers=28, n_kv_heads=4 (GQA, 28 q-heads/4 kv groups), head_dim=128, fp16 (2B).
  per-token = 2*28*4*128*2 = 57,344 B ~= 56 KiB/token.
  per 16-tok block = 16*57,344 = 917,504 B ~= **0.875 MiB/block** (matches the ~0.9MB/16-tok figure cited).
Prefix length sweep: N_blocks in {32,64,128,256,512} -> prefix tokens {512..8192}.
  prefix_KV_bytes = N_blocks * 0.875 MiB.  (e.g. 256 blocks=4096 tok -> 224 MiB)

### Inter-turn gap model
Agent inter-turn gap = wall time between a session's consecutive turns = tool-call latency +
downstream processing + (human/agent think). Realistic agentic distribution is heavy-tailed.
Model: gap ~ LogNormal parameterized by median. Sweep MEDIAN gap in {0.2, 0.5, 1, 2, 5, 10, 30} s.
  (0.2s = trivial local tool; 1-2s = typical API/tool call; 5-30s = web/retrieval/multi-step.)
sigma (log) = 0.8 fixed (moderate tail). We report results vs the MEDIAN as the primary x-axis and
also the P10 (pessimistic short-gap) since the SHORT gaps are what break prefetch.

### Fetch-latency model (PCIe, with CONTENTION — load-bearing)
fetch_time_ideal = prefix_KV_bytes / PCIe_BW_per_session.
PCIe effective BW sweep: {8, 16, 32} GB/s (PCIe4 x16 ~26 GB/s theo ~ 16-24 effective; PCIe5 ~ up to 32).
CONTENTION: a shared PCIe link of total BW B_total. If C sessions prefetch concurrently, each gets
B_total/C (fair share) -> fetch_time_contended = prefix_KV_bytes / (B_total / C_concurrent).
C_concurrent modeled from arrival: sessions resuming within a fetch window. Concurrency sweep
C in {1,2,4,8,16,32}. THIS is the make-or-break: aggregate demand C*prefix_bytes vs B_total*gap.

### Re-reference probability on resume
p_rr = P(a demoted session resumes AND reuses its demoted prefix). Sweep {0.5, 0.7, 0.9, 0.99}.
Demote+prefetch pays transfer cost for ALL prefetched sessions; only p_rr fraction is useful ->
wasted BW = (1-p_rr) of prefetch traffic competes for the same PCIe link (we charge it into contention).

### Recompute cost model (evict-recompute baseline)
prefill recompute is FLOP-bound. prefill FLOPs ~= 2 * P_params * prefix_tokens (fwd pass).
Qwen2.5-7B P=7.6e9. A100-class realistic prefill throughput ~ 1e11-2e11 tok/s effective? NO — use
TOKEN throughput: realistic prefill ~ 5e4-1e5 tokens/s/GPU for a 7B at batch (we cite a conservative
band: prefill 50k tok/s sustained). recompute_time = prefix_tokens / prefill_tok_per_s.
Sweep prefill_tok_per_s in {30k, 60k, 120k} to bound it. (Higher = harder for prefetch to win.)

## Policies (matched GPU-KV capacity)
- **P_evict (evict-and-recompute):** on demote, drop KV (free GPU + no host traffic). On resume,
  recompute prefill. Cost = recompute_time on critical path. No PCIe use. B_eff gated by recompute TTFT.
- **P_prefetch (demote+prefetch):** on demote, DMA KV to host (frees GPU). On resume, DMA back,
  overlapped with the inter-turn gap. Cost = max(0, fetch_contended - gap). Wastes BW when no resume.

## Sweeps (full grid, SERIAL)
N_blocks x gap_median x PCIe_BW x C_concurrent x p_rr x prefill_tps. Grid sized to finish < 15 min.
Monte Carlo over gap distribution: 2000 samples per cell for the gap-vs-fetch hide probability.

## HONEST-NEGATIVE branch (pre-committed)
Report the NEGATIVE if ANY of:
- inter-turn gaps are SHORTER than fetch latency for realistic KV sizes (A fails), OR
- the policy is PCIe-BANDWIDTH-BOUND under concurrency (aggregate demand > B_total over the gap), OR
- re-reference prob on resume is LOW enough that wasted transfer dominates, OR
- demote+prefetch LOSES to evict-recompute on the (B_eff, TTFT) Pareto in the realistic region.
A partial/win-region result (wins only for large prefix + long gap + low concurrency + high BW) is
reported as PARTIAL with the explicit win-region boundary. Negatives are WINS for this committee.

## Outputs
- results/sweep_gap_vs_fetch.csv  (A: hide-probability per cell)
- results/sweep_pareto.csv        (B: B_eff + TTFT_resume per policy per cell)
- RESULTS.md                       (Pareto, win-region, held/partial/negative)
Trust on-disk CSVs, not stdout.

## Prior-art caveat (MUST distinguish)
KV offload/swapping is NOT new: vLLM CPU swap-space (block swap on preemption, REACTIVE), LMCache
(cross-instance/cross-request KV reuse + offload to CPU/disk), FlexGen (offload weights+KV for
throughput-oriented single-batch), InfiniGen (dynamic KV cache mgmt / speculative prefetch of
important tokens), layer-wise KV offload. NOVELTY here = AGENT-INTER-TURN-GAP-timed PROACTIVE
demote+prefetch (scheduling the round-trip against the known idle gap of a *conversational/agentic*
session), vs reactive-on-preemption (vLLM) or cross-request reuse (LMCache). This L0 does NOT claim
the mechanism is novel — it tests whether the GAP-TIMING premise (A) and the Pareto win (B) hold
under honest PCIe-contention modeling. Mechanism overlap is acknowledged.
