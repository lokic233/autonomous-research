# EXP-0018 — Idle-window speculative prefill: break-even surface (CPU proxy)

**Agent:** researcher-0001-laneA · **Claim:** CLAIM-0002-adjacent open_gap (MAP-0001:
"idle-window speculative prefill") · **Level 1, CPU-only, ~12 min** · **2026-05-31**
**Effect: REFUTE (EARLY-KILL).** The lane collides with published prior art AND the
"discovery" reduces to a textbook expected-value accounting identity (the DEAD-0009 pattern).

---

## What the lane asked
Engine-side *speculative continuation prefill* during idle windows (turn gaps, think-time,
tool-latency bubbles): prefill a predicted continuation of P tokens so a matching real
continuation gets TTFT savings. Wanted: CPU break-even surface (wasted-compute vs
latency-saved) as a function of idle-window-length distribution and hit-rate.

## What I built (impl/breakeven.py, pure stdlib, no GPU/probes)
Token-count proxy. Per turn: HIT (prob h) reuses a matched prefix of m≤P speculated tokens;
MISS wastes all P. With α = wasted-token weight (0=idle compute free, 1=fully contended):

```
NET(tokens) = h·m·(1+α) − α·P
BREAK-EVEN:  NET ≥ 0  ⇔  h · f ≥ α/(1+α)      where f = m/P  (reuse-fraction, dimensionless)
```

Reuse-fraction modeled by per-token path-survival q: m = q(1−q^P)/(1−q), f = m/P.
Swept idle-window distribution (0.2–30s, heavy-tailed), R_prefill, P∈{16,64,256,1024},
q∈{0.8,0.9,0.95,0.99}, α∈{0,0.1,0.25,0.5,1}, h∈{0.1…0.9}. CSVs: breakeven_surface.csv (2000
rows), collapse_check.csv (72 rows).

## Findings (the surface is real and clean)
- **Break-even is a single dimensionless inequality** `h·f ≥ α/(1+α)`. Window length W and
  prefill throughput R cancel — they only set the *achievable* P (and via P, f). 
- **Feasible win-region is narrow:** short speculation (P≤16–64) + very high quality (q≥0.95)
  + low/free waste (α≤0.25). E.g. P=16,q=0.95,α=0.25 → h_min=0.30 (feasible). 
- **It collapses fast:** P=256,q=0.95,α=0.25 → h_min=2.69 (need h>1, impossible). P=1024 → h_min≥10.
  Filling the whole idle window (P=W·R, e.g. 720K tokens) is strictly dominated (f→0).
- So the honest answer to "when does it pay off": only when you speculate a SHORT, HIGH-
  CONFIDENCE continuation and idle compute is nearly free. Otherwise it's pure waste.

## WHY THIS IS A KILL (two independent kill legs)

### Leg 1 — Prior-art collision (occupied territory)
The "engine-side continuation prefill in idle windows + cost model to bound wasted compute"
is already published:
- **arXiv:2511.20048** (Nov 2025) "Reducing Latency of LLM Search Agent via Speculation-based
  Algorithm-System Co-Design" — speculates during agent tool-latency/idle gaps; carries an
  explicit overhead model T = t·[1−(1−p)]·(2N_m+N_a) and a request-scheduler that *controls
  speculative inference overhead* (the exact wasted-vs-saved tradeoff this lane proposed). DIRECT TWIN.
- **arXiv:2605.06472** "Prediction-based KV-Cache Management for Dynamic Agent Workflows" (2026) —
  predicts/prefills agent continuations. 
- **arXiv:2504.06319** Asynchronous KV-Cache Prefetching; **arXiv:2502.02789** Speculative Prefill
  (TTFT); **arXiv:2410.00428** LayerKV (computes T_allow_prefill idle slack). 
- Registry prior_art already flagged: Continuum 2511.02230 (KV-TTL), Speculative Tool Calls
  2512.15834 (which-tool). The "engine-side continuation" gap the registry believed was open
  is in fact occupied by 2511.20048 + 2605.06472 (NOT previously indexed in MAP-0001).

### Leg 2 — The characterization is an accounting identity (DEAD-0009 pattern)
`h·f ≥ α/(1+α)` is the textbook expected-value break-even of any speculate-or-skip decision
(E[saved]≥α·E[wasted]). Nothing about KV, attention, or VMM enters — W and R cancel entirely.
This is the SAME retirement basis as DEAD-0009 (k~1.3 "fully derivable from prefill FLOP
accounting") and the slope~1 demotion: a derivable identity is not a discovery. No emergent,
non-derivable, system-specific anomaly was found.

## Cemetery / red-zone check
- Does NOT touch HW VMM CoW / HW isolation / handle attestation / CDC-over-radix / mapping-
  ceiling red-zones. (Good — it's a scheduling/speculation idea, orthogonal to the dead HW legs.)
- Adjacent to DEAD-0007 (prefill-FLOP saving <2% bar) in spirit: the realized saving here is
  also gated to a tiny operating envelope (short P, q≥0.95, free compute).
- REVIVAL CONDITION (narrow): only if someone measures a speculative-prefill operating point
  that (a) is NOT covered by 2511.20048 / 2605.06472 at body level, AND (b) shows a benefit
  NOT predicted by the h·f ≥ α/(1+α) identity (a genuine system anomaly, e.g. attention-sink
  reuse that breaks the linear-token currency). Absent that, dead.

## Verdict
**REFUTE / EARLY-KILL.** Occupied by published agent-speculation work (2511.20048 twin) and the
surviving "characterization" is a derivable accounting identity. No CPU-measurable result here
advances the YELLOW gap to GREEN without colliding. Recommend cemetery entry + adding
2511.20048 / 2605.06472 to MAP-0001 occupied_territory (orchestrator action — I do not edit map).
