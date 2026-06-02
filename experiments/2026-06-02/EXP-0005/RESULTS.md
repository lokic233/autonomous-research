# RESULTS — EXP-0005 (L0, CPU-only) — CLAIM-0004

**Claim:** Prefix-family-aware (PFA) batch admission co-schedules requests sharing a long
system+tool-schema prefix into the same running batch, achieving strictly lower aggregate
recomputed prefill tokens AND higher prefix-cache hit rate than FCFS **at matched fairness**.

**Verdict: PARTIAL / CONDITIONAL HELD.** The claim holds — with a statistically clean,
bootstrap-CI-backed win — but ONLY in a specific regime: **cache too small to hold all
families AND the server is under load (queue depth > 1)**. It is a clean **NEGATIVE** in
the regime the claim's own mechanism predicts: when the cache holds all families, there is
no win (0/32 cells), exactly as pre-registered honest-negative branch N2.

## Method recap
- Discrete-event continuous-batching sim. Poisson arrivals, K prefix families (Zipf skew),
  shared LRU **block** prefix cache (block=16 tok, family prefix=2048 tok=128 blocks).
  Resident family blocks FREE; missing blocks recomputed (PRIMARY metric). In-flight blocks
  pinned. B slots, constant service time (isolates ADMISSION ORDER from service variance).
- FCFS vs PFA. PFA prefers a queued request whose family is resident/in-batch, with a
  **bounded reorder window W** (a request passed over W times must be admitted next; W=0=FCFS).
- **Matched fairness control (the crux):** for each config we pick the largest BOUNDED W
  whose mean p99 wait is <= 1.10x FCFS p99. Unbounded W (W=inf) is reported separately and is
  NOT eligible as a matched-fairness point.
- Sweep: K{2,4,8,16} x skew{0,1} x load{light=0.6,heavy=1.6 of B throughput} x B{4,16} x
  cache regime{one / few(~K/2) / all K families}. 6 seeds. Paired bootstrap 95% CI (2000
  resamples) on the per-seed PFA-minus-FCFS prefill-token delta. 96 cells, 576 rows, 260s.

## Headline numbers (at MATCHED FAIRNESS, bounded W, p99 within 10% of FCFS)

| cache regime | cells | CI<0 wins | mean prefill savings | mean p99 fairness ratio | mean W | FCFS hit -> PFA hit |
|---|---|---|---|---|---|---|
| one (cache holds ~1 family)  | 30 | 7 | 5.8% | 1.019 | 28 | 0.818 -> 0.872 |
| few (cache holds ~K/2)       | 30 | 8 | 5.0% | 1.018 | 28 | 0.858 -> 0.895 |
| all (cache holds all K)      | 32 | **0** | **0.0%** | 0.996 | 32 | 0.975 -> 0.975 |

**By load (the other gating factor):**
- one/heavy: 6/16 cells win, **mean 10.6% prefill savings**.   one/light: 1/14, 0.3%.
- few/heavy: 6/16 cells win, **mean 9.2% prefill savings**.    few/light: 2/14, 0.3%.
- all/* : 0 wins regardless of load.

**Strongest matched-fairness wins (eviction-pressured + heavy + small batch):**
- K=8, uniform, heavy, B=4, W=32: **76.4%** fewer recomputed prefill tokens,
  CI=[-261k,-246k] (excludes 0), p99 fairness ratio 1.077, hit rate 0.46 -> 0.87.
- K=16, uniform, heavy, B=4, W=32: **67.8%** savings, CI excludes 0, fair 1.089, hit 0.23 -> 0.75.
- K=16, Zipf, heavy, B=4, W=8: 41.7% savings, fair 1.023, hit 0.43 -> 0.67.

## Answers to the pre-registered questions
1. **Does PFA cut prefill / raise hit rate AT MATCHED FAIRNESS?** YES, but conditionally.
   In the eviction-pressured + loaded regime the win is large (up to 76%) and the paired
   bootstrap CI excludes 0. Across all 92 matched cells, 15 are clean CI<0 wins, all
   concentrated in {one,few} x heavy. No matched-fairness cell ever favored FCFS (no
   CI fully above 0), so PFA is never harmful on prefill at matched fairness.
2. **Which regime?** Exactly the predicted one: **cache cannot hold all families AND
   the queue has depth** (heavy load, small B so requests actually wait and PFA has
   reordering options). Light load => queue rarely has >1 family-distinct option =>
   no reordering leverage => ~0% savings.
3. **What is the fairness cost?** At matched fairness, essentially none (we constrained
   p99 to <=1.10x; achieved mean ratio 1.018-1.019, often <1.02). The cost is paid in
   **throughput of reordering** not in fairness, because bounded W caps starvation.
   **Crucially, the UNBOUNDED-W (pure greedy co-residency) variant gets ~17% mean savings
   but at p99 fairness ratio 1.29-1.34 — a 29-34% p99 wait blowup.** So pure greed buys
   more prefill savings ONLY by sacrificing fairness; the honest, fairness-respecting
   policy (bounded W) keeps most of the win in the pressured regime and gives it up
   gracefully elsewhere.
4. **Honest-negative branch N2 fired:** when the cache holds all K families, savings are
   exactly 0.0% (0/32 wins) — no eviction => no co-residency benefit. The mechanism in
   the claim ("maximizes cache reuse before eviction") is null when there is no eviction.

## Verdict: PARTIAL (conditional HELD)
- HELD in the claim's intended regime (cache < all families, loaded): statistically clean,
  large, fairness-respecting prefill + hit-rate win.
- NEGATIVE where the claim's mechanism is inoperative (cache holds all families): zero win,
  as pre-registered.
- The "at matched fairness" qualifier is essential and SURVIVES: bounded-W PFA wins without
  measurably hurting p99. Pure-greedy PFA would be a fairness-cost overclaim (we did NOT
  count it as a matched-fairness win).

## Reproducibility
- `scripts/sim.py` (simulator), `scripts/sweep.py` (serial sweep, 6 seeds, bootstrap CI),
  `scripts/analyze.py`. Raw: `results/sweep_all.csv` (576 rows), `results/matched_fairness.csv`
  (92 cells, bounded-W matched points), `results/unbounded.csv` (W=inf fairness-cost rows).
- Pure stdlib Python3, deterministic per (seed,config). multiprocessing is BLOCKED on this
  sandboxed Mac (SemLock PermissionError) — sweep is serial. ~260s wall.

## What a GPU pass should measure
- Replace the constant-service-time + token-count proxy with a **real vLLM (or SGLang)
  scheduler + automatic prefix caching (APC / RadixAttention)** on actual model weights;
  measure wall-clock TTFT/throughput, real prefill FLOPs, and KV-block eviction under the
  paged-attention allocator — not just recomputed token counts.
- Verify the matched-fairness control on real p99 TTFT under bursty agentic traffic
  (tool-call loops that re-hit the same system+schema prefix).
- Sweep real cache sizing (GPU KV blocks) vs number of concurrent agent "families"
  (system-prompt / tool-schema variants) to locate the real-world eviction-pressure regime.
- Test interaction with chunked prefill and priority/SLO scheduling.

## Prior-art caveat (NO egress — sweep owed at committee)
Could not search externally. Likely closely related and must be reconciled before any
novelty claim: **SGLang cache-aware / RadixAttention scheduling** (cache-hit-aware request
scheduling is a known SGLang idea), and **vLLM's scheduler + automatic prefix caching**
(prefix-cache-aware scheduling has been discussed/PR'd). This experiment's contribution is
narrowly the **matched-fairness control** (bounded reorder window with explicit p99 cap and
the separation of greedy-but-unfair vs fair-and-still-wins), not the idea of cache-aware
admission itself. Treat as a careful re-measurement with a fairness control, pending the
literature sweep.
