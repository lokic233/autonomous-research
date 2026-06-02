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
