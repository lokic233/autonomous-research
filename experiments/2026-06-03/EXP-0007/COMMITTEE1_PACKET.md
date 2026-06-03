# COMMITTEE#1 — CLAIM-0006 (PROJ-0003), evidence EXP-0007 (L0)
## This claim IS the committee's own reframe of RED'd CLAIM-0004 (VERDICT-0006). It tested vs the RIGHT baselines (SGLang-greedy + VTC, NOT FCFS), 24 seeds, Bonferroni FWER, service-time feedback. Result: NEGATIVE on joint-dominance (0/36). Honest negative. Vote honestly — do NOT inflate; a clean negative that closes a reframe is a legitimate outcome. If you think a GPU pass is warranted, name the SPECIFIC required_evidence (researcher's pivot: multi-SLO/priority classes where metric -> SLO-attainment-at-fixed-prefill). novelty_killer: prior-art sweep owed (SGLang RadixAttention NeurIPS24, VTC OSDI24, Preble).

## CLAIM
claim: "For agentic LLM serving where cache-aware admission (SGLang RadixAttention\
  \ / vLLM APC) is ALREADY the production default, a fairness-bounded variant that\
  \ caps queue reordering by an explicit p99-wait budget (bounded-W) achieves a strictly\
  \ better fairness/prefill Pareto frontier than BOTH unbounded-greedy cache-aware\
  \ scheduling (SGLang-style, which maximizes reuse at unbounded p99 cost) AND VTC-style\
  \ fairness scheduling (which ignores prefix reuse) \u2014 i.e. there exists a reorder-budget\
  \ regime where bounded-W dominates both on the (p99-wait, recomputed-prefill) plane."
why_it_matters: "VERDICT-0006 RED'd the FCFS-baseline framing (SGLang/vLLM APC already\

## L0 RESULTS (EXP-0007, effect=weaken)
# RESULTS — EXP-0007 (L0, CPU-only) — CLAIM-0006

**Claim:** A fairness-bounded cache-aware admission variant (bounded-W) that caps queue reordering
by an explicit p99-wait budget achieves a strictly better fairness/prefill Pareto frontier than
BOTH (a) SGLang-style unbounded-greedy cache-aware AND (b) VTC-style fairness — i.e. there exists a
reorder-budget regime where bounded-W JOINTLY DOMINATES both on the (p99-wait, recomputed-prefill) plane.

## VERDICT: **NEGATIVE on joint-dominance** (claim as literally stated does NOT hold).
## Silver lining (PARTIAL): bounded-W cleanly dominates VTC everywhere, and tames greedy's tail.

---

## Headline 3-way Pareto numbers (representative high-pressure cell: K=8, skew=2.0, B=4, load=1.4, cap=7 families)
mean ± pstdev over 24 seeds; x = p99 wait (fairness, lower better), y = recomputed prefill tokens (lower better)

| policy        | p99 wait        | recomp prefill tok |
|---------------|-----------------|--------------------|
| greedy (SGLang) | 12.75 ± 9.12  | **20992 ± 2789** (prefill FLOOR) |
| vtc (fairness)  | 7.07 ± 2.52   | 23723 ± 3782 |
| bounded W=16    | 5.94 ± 1.73   | 23296 ± 3823 |
| bounded W=4     | **4.95 ± 1.79** (p99 FLOOR) | 24064 ± 4512 |

Here bounded-W beats BOTH baselines on p99 and beats VTC on prefill — but loses to greedy on prefill
(+2304 tok). That is a fairness/prefill TRADE, not joint dominance.

## THE joint-dominance answer (the question)
Strict pre-registered Pareto dominance (paired bootstrap 95% CI, **Bonferroni FWER m=864**,
per-comparison alpha=5.79e-05; bounded must be statistically not-worse on BOTH axes AND strictly
better on >=1, vs BOTH greedy AND vtc simultaneously):

**Joint-dominance win cells = 0 / 36.**  No reorder-budget regime jointly dominates both baselines.

Why (structural, not a tuning miss):
- **Greedy is the recomputed-prefill FLOOR in 32/36 cells** (by construction it maximizes reuse).
  Bounded-W beats greedy on prefill (mean) in only 3/36 cells, none FWER-significant. You cannot
  beat the reuse-maximizer on reuse with a fairness cap that *forces* cache-suboptimal admissions.
- **Bounded-W beats greedy on p99 (fairness) in 13/36 cells under FWER** — but EVERY such p99 win
  comes with a strictly POSITIVE prefill cost (delta vs greedy: min +1109, max +38229, mean +16093
  tokens). The budget buys fairness by paying prefill. No free lunch.
- Net: bounded-W lives on the Pareto interior segment BETWEEN greedy (prefill corner) and a
  fairness-capped point; it is a tunable knob ALONG the frontier, not a point that pushes the
  frontier inward past both corners.

## The defensible PARTIAL win: bounded-W vs VTC
- **bounded-W STRICTLY DOMINATES VTC in 36/36 cells** (>=1 W per cell; 215 (cell,W) points total)
  under the SAME Bonferroni FWER (m=432, alpha=1.16e-04): lower p99 AND (usually) lower prefill.
- Interpretation: VTC's fairness counter ignores prefix reuse, so under Zipf-skewed family load it
  pays prefill for fairness it doesn't need — a cache-aware bounded reorder is strictly better than
  pure fairness scheduling. This is real, but it is dominance over the WEAKER baseline only.
- **Greedy itself mean-dominates VTC on both axes in 31/36 cells** — under heavy skew, serving the
  hot (reuse-rich) families first is *also* roughly fair because they arrive most. VTC is the easy
  baseline to beat; greedy is the hard one.

## Held / partial / negative
- **HELD:** NO — no joint-dominance regime over BOTH baselines (0/36, FWER).
- **PARTIAL:** YES — bounded-W strictly dominates VTC everywhere and strictly lowers greedy's p99 tail
  in 13/36 cells (at a prefill cost). It is a useful tunable fairness-vs-prefill knob, NOT a free lunch.
- **NEGATIVE (the honest headline):** the *specific* claim that a budget regime JOINTLY dominates BOTH
  the SGLang-greedy and VTC extremes is FALSE in this CPU queueing/cache simulation. Greedy is the
  prefill floor; you can only move along the frontier toward fairness, never strictly inside it past greedy.

## Sweeps & stats (as pre-registered)
- K in {8,16}, skew in {1.5,2.0}, B in {4,16} (kept K>B for cache pressure), load_mult in {0.7,1.0,1.4},
  cache cap in {B+1,B+2,2B} families. M=400 req. **24 seeds** (>=20 per committee).
- Service-time FEEDBACK active: svc = 0.5 + 0.0015*recomputed_prefix_tok + 0.0008*scratch (cache
  misses lengthen slot occupancy -> couples p99 and prefill; constant-service would sever the loop).
- Paired bootstrap CI (4000-5000 resamples), Bonferroni FWER on all dominance comparisons.
- 36 cells, 288 policy-points, 167s serial wall. Artifacts: results/sweep_all.csv (raw seeds),
  results/pareto_points.csv (frontier), results/dominance.csv (per-cell joint-dom CIs).

## What a GPU pass should measure (L1+)
- Replace the abstraction with the REAL schedulers: SGLang RadixAttention greedy admission vs the
  real VTC implementation on vLLM/APC, on a real H100/MI350X, measuring **real p99 TTFT** (not
  simulated wait) and **real recomputed prefill FLOPs/tokens** under a Zipf-skewed multi-tenant
  prefix-family trace. The simulator's prefill-floor structural result predicts the negative will
  hold on hardware, but real prefill cost is non-linear (chunked prefill, paged KV) and real fairness
  has SLO classes — the bounded-W-beats-VTC partial may strengthen, while joint-dominance over greedy
  almost certainly stays out of reach.
- Add multi-SLO / priority classes (greedy has no notion of per-tenant SLO; bounded-W's p99 cap maps
  naturally to an SLO) — that is the regime where bounded-W could earn a real production case, but it
  changes the metric from raw Pareto to SLO-attainment-at-fixed-prefill.

## Prior-art caveat (sweep owed — no egress in this L0)
Likely-related and NOT independently sweep-verified here:
- **SGLang RadixAttention** (Zheng et al., NeurIPS 2024) — the greedy cache-aware extreme (baseline a).
- **VTC / Virtual Token Counter** fair scheduling (Sheng et al., OSDI 2024) — fairness extreme (baseline b).
- **Preble** — prefix-aware distributed scheduling.
This L0 is a queueing+cache SIMULATION, not the real systems. The negative result is about the
*abstract* Pareto structure (greedy is the reuse floor); a literature/code sweep against the real
schedulers is owed before any external claim.

## PRE-REG (committed pre-run 6d100f0)
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
