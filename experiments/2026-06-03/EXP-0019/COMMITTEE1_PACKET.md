# COMMITTEE#1 — CLAIM-0014 (PROJ-0003), evidence EXP-0019 (L0)
## MEASUREMENT/MODELING study, effect=keep-exploring / PARTIAL-lean-positive. The researcher MODELED the make-or-break (finite fair-share PCIe bandwidth under concurrency) rather than assuming infinite BW — and it materialized exactly as the pre-registered risk: the policy wins broadly but LOSES in a bounded PCIe-contention corner. The researcher REFUSES to promote 'strictly better Pareto' as universal — it must be SCOPED to the win-region. Vote honestly. novelty_killer: KV offload is NOT novel (vLLM CPU-swap reactive, LMCache cross-instance, FlexGen, InfiniGen, layer-wise offload) — the researcher concedes this; the NARROW claimed novelty is AGENT-INTER-TURN-GAP-timed PROACTIVE demote+prefetch (scheduling the full host round-trip against the KNOWN conversational idle gap). Run a live >=2-source sweep: does any published offload work specifically time proactive demote+prefetch to the agent inter-turn gap (vs reactive-on-preemption or speculative-token prefetch)? If candidate-grade, the L1 ask: real concurrent PCIe/NVLink-C2C BW under D2H+H2D+decode traffic; real vLLM/LMCache offload resume-TTFT vs recompute; real agent inter-turn-gap distribution (sub-second mass + tail decide the kill-corner); real re-reference prob on resume.

## CLAIM
claim: For agentic LLM serving with bursty per-session KV pressure, a tiered KV-offload
  policy that proactively demotes a session's COLD prefix blocks to CPU/host memory
  (and prefetches them back on the session's next turn, overlapping fetch with the
  inter-turn idle gap) achieves a strictly better effective-batch-size / TTFT Pareto
  than evict-and-recompute, because agent inter-turn gaps are long enough to hide
  PCIe fetch latency AND the demoted blocks are re-referenced with high probability
  on resume.
why_it_matters: "NEW axis (KV-offload tiering across the agent inter-turn gap \u2014\

## L0 RESULTS (EXP-0019)
# RESULTS — EXP-0019 (CLAIM-0014) — PARTIAL (win-region characterized; PCIe-contention boundary is the kill-switch)

**L0 analytic + Monte-Carlo trace sim. CPU-only, stdlib-only, SERIAL. NO GPU/model/network.**
Honest pipeline. Numbers below are read from on-disk CSVs (results/sweep_*.csv), not stdout.

## Verdict: PARTIAL (lean POSITIVE in the realistic region, with a sharp, predictable kill-corner)
The two falsifiable parts both survive in the realistic agentic regime, but the claim's
"strictly better Pareto" is **NOT universal** — it has a clean PCIe-bandwidth-under-concurrency
boundary that is exactly the load-bearing risk the pre-registration flagged. The claim should be
**scoped**, not promoted as stated.

## Models used (cited in PRE_REGISTRATION.md)
- KV size: Qwen2.5-7B-like GQA fp16 -> 57,344 B/token, **0.875 MiB per 16-tok block** (2*28 layers*4 kv-heads*128 head_dim*2B).
- Inter-turn gap: LogNormal(median, sigma=0.8); median swept 0.2-30 s (tool-call + downstream).
- Fetch latency w/ CONTENTION: shared PCIe link B_total split fair-share across C concurrent prefetchers;
  fetch = prefix_bytes / (B_total / C). Wasted (1-p_rr) prefetches inflate effective C to C/p_rr.
- Evict-recompute TTFT = prefix_tokens / prefill_tps (FLOP/GPU-bound; tps swept 30k/60k/120k tok/s).

## PART A — Is the inter-turn gap long enough to hide host<->GPU KV fetch? **MOSTLY YES.**
(results/sweep_gap_vs_fetch.csv, 630 cells, MC=2000 per cell)
- **89.7%** of cells hide the fetch >=90% of the time; only **3.8%** hide <50%.
- Fetch latency is genuinely small vs agentic gaps in the common case: e.g. a 256-block (224 MiB)
  prefix over 16 GB/s with C=8 fetches in ~0.11 s — trivially hidden by a 1-2 s tool-call gap.
- **The exception (A fails) is a tight corner:** 512 blocks (448 MiB) + 8 GB/s + C=16-32 + gap<=1 s
  -> fetch 0.94-1.88 s, hide prob drops to 0.21-0.54. Big prefix + slow link + high concurrency +
  short gap = fetch no longer hides. This is the PCIe-contention regime, not a gap-length problem per se.

## PART B — Does demote+prefetch beat evict-and-recompute on the (B_eff, TTFT) Pareto? **YES in-region; NO in the kill-corner.**
(results/sweep_pareto.csv, 7560 cells)
- **Prefetch wins (lower TTFT-on-resume) in 93.5%** of cells.
- **Prefetch loses in 6.5%**, and **70% of those losses are PCIe-BW-BOUND** (aggregate prefetch
  demand C/p_rr * prefix_bytes exceeds B_total * gap). The mechanism that kills it is exactly the
  pre-registered risk: contention, not gap length.
- **Loss-region fingerprint** (n=488 losses): short gap (<=0.5 s = 75%), high concurrency
  (C>=16 = 90%), large prefix (>=256 blocks = 73%), low BW (8 GB/s = 63%), low re-reference
  (p_rr<=0.7 = 64%), and fast prefill (120k tps = 45%, because cheap recompute is a strong baseline).
- **Sane-deployment box** (BW>=16 GB/s, C<=8, prefix<=256 blocks): **1 loss out of 7560 cells.**
  Inside it, prefetch is essentially always on the better Pareto frontier.

### Representative Pareto (BW=16 GB/s, C=8, p_rr=0.9, gap=2 s, prefill=60k tok/s)
| prefix | KV size | TTFT evict-recompute | TTFT demote+prefetch | speedup |
|--------|---------|----------------------|----------------------|---------|
| 512 tok  | 28 MiB  | 8.5 ms   | ~0 (fully hidden) | — |
| 1024 tok | 56 MiB  | 17.1 ms  | ~0 (fully hidden) | — |
| 2048 tok | 112 MiB | 34.1 ms  | ~0 (fully hidden) | — |
| 4096 tok | 224 MiB | 68.3 ms  | 0.02 ms | 3413x |
| 8192 tok | 448 MiB | 136.5 ms | 0.28 ms | 488x |
The longer the prefix, the BIGGER the prefetch win — because recompute scales linearly with prefix
length while a hidden fetch costs ~0 on the critical path. This is the strongest case for the policy.

## THE CRUX (pre-registered make-or-break): does aggregate prefetch demand exceed PCIe BW?
Yes, and the model captures it. The win flips exactly when **C/p_rr * prefix_bytes > B_total * gap**.
Worst observed loss: 512-block prefix, 8 GB/s, C=32, p_rr=0.5, gap=0.2 s -> effective fetch 3.48 s
vs evict-recompute 0.07-0.27 s: prefetch is **~13-50x WORSE** there. So the policy is NOT free; under
heavy concurrent demote/prefetch on a constrained link it is strictly dominated by evict-recompute.

## Win-region (honest)
demote+prefetch is the right policy when ALL roughly hold:
  prefix KV per session moderate (<= ~224 MiB / 256 blocks),
  effective PCIe BW >= 16 GB/s,
  concurrent prefetchers C <= ~8 (or B_total provisioned so C/p_rr*bytes < B_total*gap),
  agentic inter-turn gap median >= ~1 s,
  re-reference prob >= ~0.7.
Outside it (very long prefixes, slow/oversubscribed PCIe, bursty high-concurrency resumes, sub-second
gaps, low re-reference) evict-and-recompute is better or comparable — recompute is bounded and uses
zero PCIe, so it degrades gracefully under load while prefetch collapses on the contended link.

## What a real GPU L1 should measure (this L0 cannot)
1. REAL effective PCIe/NVLink-C2C BW under concurrent cudaMemcpyAsync D2H/H2D (not nameplate; measure
   8/16/32 GB/s reality + queueing on a shared link), and overlap with active decode traffic.
2. REAL vLLM/LMCache CPU-offload + block-swap path TTFT-on-resume vs prefill recompute, same model.
3. REAL agent inter-turn gap DISTRIBUTION from a live agent trace (tool latency + downstream) — the
   LogNormal here is a placeholder; the tail and sub-second mass decide the kill-corner.
4. REAL re-reference probability on resume from agent session logs (does the demoted prefix actually
   get reused, or does the agent rewrite context?).
5. Contention WITH concurrent decode/prefill PCIe traffic (this sim isolates the prefetch link).

## Prior-art caveat (MUST distinguish — KV offload is NOT novel)
- **vLLM CPU swap space**: block swap on preemption — REACTIVE, triggered by scheduler eviction, not
  scheduled against a known idle gap.
- **LMCache**: cross-request / cross-instance KV reuse + CPU/disk offload — about REUSE/sharing, not
  per-session gap-timed round-trips.
- **FlexGen**: offload weights+KV for throughput-oriented single-large-batch inference (latency-insensitive).
- **InfiniGen**: dynamic KV management / speculative prefetch of *important tokens* within generation.
- **Layer-wise KV offload**: pipeline offload across layers.
**Claimed novelty = AGENT-INTER-TURN-GAP-timed PROACTIVE demote+prefetch** (scheduling the full
host round-trip against the *known* conversational idle gap of an agentic session), vs reactive-on-
preemption or cross-request reuse. This L0 does NOT claim the mechanism is novel — the DMA paths exist.
It tests whether the GAP-TIMING premise (A) and the Pareto win (B) hold under honest PCIe-contention
modeling. They hold in a bounded region and fail predictably in the contention corner.

## Files
- experiments/2026-06-03/EXP-0019/PRE_REGISTRATION.md
- experiments/2026-06-03/EXP-0019/sim.py
- experiments/2026-06-03/EXP-0019/results/sweep_gap_vs_fetch.csv (630 rows)
- experiments/2026-06-03/EXP-0019/results/sweep_pareto.csv (7560 rows)

## PRE-REG (committed pre-run c5f675b)
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

## ORCHESTRATOR CAVEAT: analytic+MC model, NOT real hardware — LogNormal gap is a placeholder; effective concurrent PCIe BW is modeled fair-share (nameplate-derived, not measured under contention); re-reference prob is a swept parameter not a measured agent statistic. These are exactly what the L1 must close — and the kill-corner is sensitive to the real gap distribution's sub-second mass.
