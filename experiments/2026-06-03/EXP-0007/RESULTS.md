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
