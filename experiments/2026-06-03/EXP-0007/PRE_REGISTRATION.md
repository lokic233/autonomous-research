# PRE-REGISTRATION — EXP-0007 (L0, CPU-only, serial, stdlib)

**Claim CLAIM-0006 / Project PROJ-0003 / Task TASK-0007.**
Pre-registered and committed BEFORE any runs. Honest pipeline: negative/conditional results are WINS.

## 0. Why this claim exists (context)
A predecessor claim (CLAIM-0004, EXP-0005) compared prefix-family-aware admission only against
naive FCFS. Committee#1 (VERDICT-0006) RED'd it as a strawman: SGLang RadixAttention and vLLM APC
ALREADY ship cache-aware admission. The committee's constructive reframe is THIS claim. The open
question is NOT "does cache-awareness beat FCFS" (settled, yes) but: **does a p99-BOUNDED reorder
budget beat BOTH of the RIGHT baselines on the fairness/prefill Pareto plane?**

## 1. THE CLAIM (verbatim, CLAIM-0006)
A fairness-bounded cache-aware admission variant that caps queue reordering by an explicit
p99-wait budget (**bounded-W**) achieves a strictly better fairness/prefill Pareto frontier than
BOTH:
  (a) **unbounded-greedy cache-aware** scheduling (SGLang-style: maximize prefix reuse, ignore fairness), AND
  (b) **VTC-style fairness** scheduling (ignore prefix reuse).
I.e. there exists a reorder-budget regime where bounded-W **dominates BOTH** on the
(p99-wait, recomputed-prefill) plane.

## 2. The THREE policies (the crux — RIGHT baselines, NOT FCFS)
All three share the SAME server model (continuous batching, B slots, Poisson arrivals, K prefix
families with Zipf skew s>=1.5, shared LRU block prefix cache) so the only difference is the
admission ordering rule.

  (a) **greedy** (SGLang-style greedy cache-aware): at each admission, pick the queued request whose
      prefix-family is MOST-resident (most resident blocks / in-batch), UNBOUNDED reordering. No
      fairness cap. Maximizes reuse; can starve cold families. Tunable knob: none intrinsic — it is
      the prefill-optimal extreme. (We sweep load to trace its frontier.)
  (b) **vtc** (VTC-style fairness, Sheng et al. OSDI24): admit by a virtual-time / weighted-service
      fairness counter. Each family accumulates virtual service = cumulative admitted requests
      (weighted). Always admit the queued request from the family with the LEAST accrued virtual
      service (ties -> earliest arrival). Prefix reuse is IGNORED. This is the fairness-optimal
      extreme.
  (c) **bounded** (bounded-W): cache-aware admission (prefer most-resident family, like greedy) BUT
      reordering is bounded by an explicit per-request skip budget W: a queued request that has been
      passed over >= W times MUST be admitted (head-of-line starvation cap). Sweep W in
      {1,2,4,8,16,32}. W=0 collapses to FCFS-order (no reorder); W=inf collapses to greedy. The
      claim is that some intermediate W yields a Pareto point dominating BOTH (a) and (b).

## 3. Server model & SERVICE-TIME FEEDBACK (committee-required)
- Poisson arrivals rate lambda = load_mult * B / mean_service.
- K families, Zipf skew s. Per committee: **s >= 1.5** (we sweep s in {1.5, 2.0}).
- Shared LRU block prefix cache, block granularity, pinned-while-inflight (reuse EXP-0005 BlockCache).
- **SERVICE-TIME FEEDBACK (the loop the committee required):** a request's service (slot-occupancy)
  time is NOT constant. It = BASE_SERVICE + PREFILL_COEF * (recomputed_prefill_tokens) +
  DECODE * scratch. Recomputed (cache-miss) prefix tokens cost prefill compute, which lengthens slot
  occupancy, which feeds back into queue wait. So poor cache decisions -> longer service -> more
  queueing -> the p99/prefill tradeoff is genuinely coupled (constant service-time would sever the
  loop and trivialize the result; committee flagged this).

## 4. Pareto metric (THE plane)
- **x = p99 wait** (admission_time - arrival_time, 99th pctile) -> FAIRNESS / tail latency axis.
- **y = recomputed prefill tokens** (total, lower = better cache reuse) -> PREFILL / efficiency axis.
- Lower-left is better on both axes. A policy point P **dominates** Q iff P.x <= Q.x AND P.y <= Q.y
  with at least one strict. The **frontier** of a policy = its Pareto-nondominated points over its
  knob sweep + load sweep.

## 5. Sweeps
- K in {8, 16}; skew s in {1.5, 2.0}; B in {4, 16}; load_mult in {0.7, 1.0, 1.4} (under/near/over-load).
- greedy: 1 knob value (it IS the greedy extreme) traced across the load sweep.
- vtc: 1 knob value (fairness extreme) traced across the load sweep.
- bounded: W in {1,2,4,8,16,32} traced across the load sweep.
- M = 400 requests per run (horizon). >= 20 seeds.

## 6. Seeds & statistics
- **SEEDS = 24** (committee flagged n=6 as too few; we use 24 >= 20).
- Report mean +/- pstdev for p99_wait and recomp_tokens per policy/knob/cell.
- **Dominance test:** for each (cell) where bounded-W appears to jointly dominate, compute PAIRED
  bootstrap 95% CI (same seeds across policies) on BOTH deltas:
    delta_p99 = bounded.p99 - baseline.p99   (want CI_hi < 0, i.e. bounded strictly lower p99)
    delta_recomp = bounded.recomp - baseline.recomp (want CI_hi < 0, strictly lower prefill)
  A JOINT-DOMINANCE win cell requires bounded to be statistically <= both baselines on BOTH axes
  with at least one strict, vs BOTH greedy AND vtc.
- **FWER correction:** Bonferroni across all candidate dominance cells (n_cells * 2 baselines * 2
  axes comparisons). A win survives only if its Bonferroni-adjusted CI excludes 0 in the winning
  direction. (BH as a secondary, less-conservative report.)

## 7. HONEST-NEGATIVE branch (pre-committed)
If bounded-W does NOT jointly dominate BOTH baselines on the Pareto plane — i.e. it is dominated by
greedy on prefill OR by VTC on fairness with NO joint-better regime surviving FWER — we report the
NEGATIVE. Specifically:
  - HELD: >=1 cell where bounded jointly dominates BOTH baselines (Bonferroni-significant on both axes).
  - PARTIAL: bounded dominates one baseline but not both jointly anywhere, OR wins only pre-correction.
  - NEGATIVE: bounded is Pareto-dominated by greedy (prefill) and/or vtc (fairness); no joint regime.
We pre-commit to reporting whichever obtains. A clean PARTIAL/NEGATIVE is a publishable result
(it tells the field the bounded-budget knob does not buy a free lunch over the two production extremes).

## 8. Prior-art caveat
Likely-related (sweep owed if egress available; this L0 has no network):
  - SGLang RadixAttention (Zheng et al., NeurIPS 2024) — the greedy cache-aware extreme.
  - VTC / Virtual Token Counter fair scheduling (Sheng et al., OSDI 2024) — the fairness extreme.
  - Preble (prefix-aware distributed scheduling).
This L0 is a queueing/cache SIMULATION abstraction, not the real schedulers. A GPU pass should
re-run against the real SGLang scheduler + real VTC on vLLM/APC with real p99 TTFT (see RESULTS.md).

## 9. Scope / constraints
CPU-only, pure stdlib, SERIAL (multiprocessing blocked — SemLock PermissionError on this sandbox),
<= 15 min wall clock. Trust on-disk CSVs, not stdout (stale leftover processes may contaminate logs).
