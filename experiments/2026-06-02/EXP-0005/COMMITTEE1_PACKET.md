# COMMITTEE#1 REVIEW PACKET — CLAIM-0004 (PROJ-0003), evidence EXP-0005 (L0)

## PASS: committee#1 (post-L0, pre-GPU). Two-pass model. This L0 is effect=support / PARTIAL-conditional-HELD with the MATCHED-FAIRNESS control intact. If candidate-grade, state SPECIFIC required_evidence for a GPU pass (researcher recommends real vLLM/SGLang scheduler + automatic prefix caching, real p99 TTFT under bursty agentic loops). An honest YELLOW with concrete required_evidence is valid; do NOT rubber-stamp to green.
## novelty_killer: live >=2-source prior-art sweep OWED (no egress at L0). STRONG overlap risk with SGLang cache-aware/RadixAttention scheduling + vLLM scheduler+APC (cache-hit-aware admission is a KNOWN idea). The researcher's stated narrow contribution is the MATCHED-FAIRNESS control (bounded reorder window with explicit p99 cap) + the explicit separation of greedy-but-unfair (+17% @ 1.3x p99) vs fair-and-still-wins — NOT cache-aware admission itself. The novelty hinges on whether the fairness-bounded framing is published.

## THE CLAIM (CLAIM-0004)
claim: For agentic LLM serving, a prefix-family-aware batch admission policy that
  co-schedules queued requests sharing a long system+tool-schema prefix into the same
  running batch achieves strictly lower aggregate prefill cost (recomputed prefill
  tokens) and higher prefix-cache hit rate than FCFS/priority admission at matched
  fairness, because co-residency of a prefix family maximizes cache reuse before eviction.
why_it_matters: 'Continuous-batching admission ignores prefix sharing; co-scheduling

## L0 EVIDENCE — EXP-0005 RESULTS (effect: support; PARTIAL/conditional-HELD)
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

## PRE-REGISTRATION (committed PRE-run, git 0697cce)
# PRE-REGISTRATION — EXP-0005 (L0, CPU-only)

**Claim CLAIM-0004:** For agentic LLM serving, a prefix-family-aware batch admission
policy that co-schedules queued requests sharing a long system+tool-schema prefix into
the same running batch achieves strictly lower aggregate prefill cost (recomputed prefill
tokens) and higher prefix-cache hit rate than FCFS/priority admission AT MATCHED FAIRNESS,
because co-residency of a prefix family maximizes cache reuse before eviction.

**Pre-registered BEFORE any runs.** Honest pipeline: negative/conditional results are wins.

## 1. Arrival model
- M requests arrive over a horizon via a Poisson process (exponential inter-arrival,
  rate λ req/s). Sweep λ.
- Each request belongs to one of K prefix FAMILIES. Family assignment drawn from a
  (possibly skewed) categorical distribution (Zipf skew parameter s; s=0 => uniform).
- Each request: prefix_len tokens (shared by its family, the system+tool-schema prefix,
  fixed = PREFIX_LEN) + scratch_len tokens (per-request, ~ small, drawn from a range).

## 2. Block prefix cache model (SHARED, the crux)
- Prefix tokens are stored in fixed-size BLOCKS (block_size tokens). A family's prefix
  occupies ceil(PREFIX_LEN/block_size) blocks. Block identity = (family_id, block_index)
  — i.e. blocks are content-addressed and SHARED across all requests of a family
  (radix/prefix-cache sharing).
- Cache capacity = CACHE_BLOCKS total blocks, LRU eviction at block granularity.
- A request's family-prefix blocks that are RESIDENT at admission time are FREE
  (cache hit). Missing blocks are RECOMPUTED (counted as recomputed prefill tokens) and
  inserted into the cache (may evict LRU). Scratch tokens are always computed but are NOT
  the object of study (we count prefix recompute as the primary metric; scratch is a
  fixed cost identical across policies).
- On admission, the request's family blocks are touched (LRU bump) and pinned while the
  request occupies a batch slot (cannot be evicted while in-flight); freed for eviction
  when the request completes (but remain resident until LRU-evicted).
- Capacity regimes swept so cache holds: ~1 family / a few families / all K families.

## 3. Continuous-batching server
- B concurrent slots. A request occupies a slot for a service time proportional to its
  total work; for L0 simplicity service_time = base_service (constant per request, so the
  queueing dynamics are clean and policy differences isolate to ADMISSION ORDER, not
  service-time variance). Sweep B.
- When a slot frees, the admission policy picks the next queued request to admit.

## 4. Admission policies
- (a) **FCFS**: admit the earliest-arrived queued request.
- (b) **Prefix-family-aware (PFA)**: when a slot frees, prefer admitting a queued request
  whose family is ALREADY resident in cache OR already running in the batch (co-residency),
  to maximize reuse before eviction. BOUNDED REORDERING: a request may be skipped over at
  most W times (reorder window / starvation bound) — once a request has been passed W
  times, it MUST be admitted next (head-of-line protection). W is the fairness knob.
  W=0 reduces to FCFS.

## 5. Metrics
- **PRIMARY:** aggregate recomputed prefill tokens (sum over all requests of missed
  prefix blocks * block_size). Lower is better.
- **SECONDARY:** prefix-cache hit rate = (free prefix blocks served) / (total prefix
  blocks requested).
- **FAIRNESS:** queueing wait = admission_time - arrival_time. Report mean wait and
  p99 wait. PFA must be compared to FCFS AT MATCHED FAIRNESS — i.e. with W tuned so PFA's
  p99 wait is within X% (X=10%) of FCFS p99 wait. Also report max wait.

## 6. Sweeps
- CACHE_BLOCKS: sized to hold {1, few(~K/2), all K} family prefixes.
- K (#families): {2, 4, 8, 16}.
- skew s (Zipf): {0.0 uniform, 1.0 moderate}.
- λ (arrival rate): {light, moderate, heavy} relative to B/base_service.
- B (batch slots): {4, 16}.
- W (reorder window): swept {0,1,2,4,8,16,32,inf} per config to find matched-fairness W.
- SEEDS: >= 5 (use 8). Report mean +/- std. Paired bootstrap 95% CI on the
  PFA-minus-FCFS prefill-token delta (paired by seed).

## 7. Hypotheses & decision rule
- H1 (primary): At MATCHED FAIRNESS (PFA p99 wait <= 1.10x FCFS p99), PFA aggregate
  recomputed prefill tokens < FCFS, with paired bootstrap 95% CI excluding 0.
- H2 (hit rate): PFA hit rate > FCFS at matched fairness.
- Expected win region: cache too small to hold all K families (CACHE_BLOCKS < all),
  moderate-heavy load (queue depth > 1 so reordering has options), K>=4.

## 8. HONEST-NEGATIVE branch (pre-committed)
We will report a NEGATIVE / PARTIAL verdict if ANY of:
- (N1) PFA only wins on prefill by SACRIFICING fairness — i.e. at matched p99 wait
  (W capped so p99 within 10% of FCFS) the prefill-token CI includes 0 or favors FCFS.
- (N2) The win VANISHES when the cache is large enough to hold all K families
  (no eviction pressure => no co-residency benefit).
- (N3) The win is negligible (< a few % of FCFS prefill) even when statistically present.
Verdict taxonomy: HELD (win at matched fairness in expected region, CI excludes 0),
PARTIAL (win only unbounded/unfair, or only in narrow regime, or small effect),
NEGATIVE (no win at matched fairness anywhere, or win requires unfairness).

## 9. Reproducibility
- Pure stdlib Python3, no GPU/network. Fixed seeds. Script: sim.py. Raw CSV in results/.
- Deterministic given (seed, config).

## ORCHESTRATOR NOTES
- THE CRUX is the matched-fairness control: bounded-W PFA wins (up to 76% prefill-token reduction, 15/92 cells clean CI<0, never harmful) at ~1.02x p99 wait. Unbounded-greedy W=inf gets +17% mean BUT at 1.29-1.34x p99 — reported SEPARATELY and NOT counted as a matched-fairness win. The 'win only by sacrificing fairness' failure mode is real and was explicitly excluded.
- Honest-negative branch fired: cache holds all K families -> 0/32 wins, exactly 0.0% savings (mechanism null without eviction). As pre-registered.
- Win region: cache cannot hold all families AND under load (queue depth>1); strongest at small batch B=4, larger K.
- evaluation_prosecutor: the L0 uses constant-service-time + token-count proxy, not wall-clock. A GPU pass on real vLLM/SGLang APC measuring real TTFT/throughput + p99 under bursty agentic loops is the natural ask.
- systems_reviewer: is fairness-bounded prefix-family admission expressible in / already done by SGLang cache-aware scheduling or vLLM scheduler+APC? That adjudication is load-bearing for novelty.
