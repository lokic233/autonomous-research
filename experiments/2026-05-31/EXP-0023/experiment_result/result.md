# EXP-0023 RESULT — CLAIM-0006 gate-B: ANALYTIC SERVING-OVERHEAD BRIDGE (CPU)

**Claim:** CLAIM-0006 · **Level:** 1 · **Device:** CPU-only (/usr/bin/python3, stdlib only; NO GPU/torch/CUDA, NO model CLIs, NO memory probes) · **Date:** 2026-05-31
**Agent:** researcher-0002-laneC · reporting to orchestrator 22bd6bef
**Impl:** `impl/exp0023_analytic_bridge.py` (deterministic, no RNG; <1s wall; <50MB)
**Data:** `experiment_result/e2e_sensitivity.csv`, `experiment_result/summary.json`

## What this is (and is NOT)
The committee (VERDICT-0025/0028, 4/5 reviewers) requires an **end-to-end serving anchor** (real
vLLM+CacheBlend) to confirm that CDC's **kernel-level** wall-clock advantage (EXP-0014/0021: CDC contiguous
faster than PIC scattered-HKVD, PIC/CDC = 1.13–2.63x, ALL 8 CI95 exclude 1.0) **survives the serving stack**.
That cell could NOT be run (vLLM/lmcache not installable on devgpu014; prod paths block pip — see EXP-0021 req#2).

This experiment **BOUNDS what we can say without that cell**: it builds the strongest honest **analytic bridge**
from the kernel-proxy to an end-to-end TTFT estimate by adding the serving overheads the proxy omits, using
**published overhead figures** (cited), and produces a **best/worst-case end-to-end CDC/PIC sensitivity band**.
It is a **MODEL, not a measurement** — it does not replace the serving cell; it tells the committee **how
load-bearing the missing cell is**. The theory_skeptic's concern is the explicit target: *can the kernel win
INVERT under serving?*

## Model (transparent)
`TTFT_arm = kernel_ms(arm) + per_call_sched + PIC_extra_launches·us_per_launch − overlap·g_attr·(PIC kernel penalty)`
- **kernel_ms** reconstructed to ABSOLUTE scale from EXP-0014's whole-suffix anchor (32k/0.1% CDC ≈ 0.71 ms),
  using a contiguous attention-work proxy R·S; PIC_ms = (EXP-0021 ratio)·CDC_ms.
- **per_call_sched** (vLLM scheduler/sampling/prepare-inputs): applied EQUALLY to both arms → SHRINKS the
  ratio toward 1.0 (this is the skeptic's "fixed serving tax dilutes the kernel win" mechanism).
- **PIC_extra_launches × us_per_launch**: scattered selective recompute issues MORE distinct kernels
  (gather/index_select + per-chunk attn) than one contiguous block; per-launch overhead is "microsecond
  scale" [NV], amortized to ~0 by CUDA graphs.
- **overlap·g_attr·penalty**: a TUNED serving stack OVERLAPS the scattered KV gather/HBM-load with compute
  [CacheBlend], HIDING part of the kernel-proxy's PIC penalty (the proxy measured gather NOT overlapped).
  This is the **dominant erosion** of CDC's advantage. `g_attr` = fraction of PIC's kernel penalty that is
  *overlappable gather* (vs *irreducible selective recompute*, which overlap cannot remove).

## Cited overhead sources (real; not invented)
- **[K]** EXP-0021 (this project): H100 SDPA kernel-proxy, 30 reps, bootstrap CI95 PIC/CDC; all 8 cells exclude 1.0.
- **[W]** EXP-0014 (this project): whole-suffix anchor 32k/0.1% CDC ≈ 0.71 ms (absolute-scale calibration).
- **[CB]** CacheBlend, **arXiv:2405.16444** (Yao et al.): selective recompute of ~15% HKVD tokens; 2.2–3.3×
  TTFT reduction vs full prefill; **scattered KV gather/HBM-load is overlapped with compute** (pipelined).
- **[NV]** NVIDIA *Getting Started with CUDA Graphs* + PyTorch *Accelerating PyTorch with CUDA Graphs*:
  per-kernel CPU launch overhead is "microsecond scale" (≈5–10 µs/launch), amortized ~0 by CUDA graphs.
- **[SCH]** vLLM continuous-batching: fixed per-step Python scheduling/sampling/prepare-inputs CPU cost
  (tens–hundreds of µs at prefill), modeled as a symmetric per-call tax.

## RESULT — end-to-end PIC/CDC sensitivity band (>1 = CDC faster end-to-end)
| scenario | band over all 8 cells | cells that INVERT (PIC faster) |
|---|---|---|
| best-for-CDC (no overlap, big launch tax on PIC) | **[1.18, 7.59]** | 0/8 |
| **nominal** (45% gather overlap, 6µs/launch, 0.20ms sched) | **[1.10, 2.03]** | 0/8 |
| **worst-for-CDC** (85% overlap, CUDA-graph launches, 0.60ms sched, CI-LOW kernel ratios) | **[1.00, 1.28]** | **0/8** |

**Win-region (32k, inj≤1%) worst-case end-to-end PIC/CDC: 1.04–1.28×** — CDC stays faster even under the
most adverse plausible serving assumptions. The tightest (most fragile) cells are **4k/0.1% (worst 1.002,
a near-tie)** and **32k/1% (worst 1.038)** — small-context or moderate-injection corners where the absolute
kernel gap is sub-millisecond and the symmetric sched tax dominates.

## Break-even analysis (the load-bearing result)
Solving for the gather-overlap that makes PIC tie CDC (launches≈0, symmetric sched): **break-even overlap =
1/g_attr**. Since `g_attr ≤ 1` by construction (overlap can only hide the *overlappable gather* fraction,
never the *irreducible selective recompute*), the break-even overlap is **≥ 1.0 — i.e. ≥100%**, which is
**physically impossible**. Conclusion: **gather/HBM overlap ALONE cannot invert CDC's advantage.** The only
path to a flip is a large per-call scheduling/launch asymmetry that *favors PIC* — but PIC issues MORE
kernels and MORE scattered traffic, so realistic asymmetry runs the OTHER way. **Flip risk is LOW.**

## HONEST VERDICT: **support** (the kernel advantage plausibly SURVIVES serving) — with one caveat the cell still owes
- Across the **entire plausible overhead range**, CDC's end-to-end TTFT advantage **does NOT invert** in any
  of the 8 decision cells. Worst-case it compresses to a **near-tie (1.00–1.04×) at the small-context /
  moderate-injection corners** and holds at **1.04–1.28×** in CLAIM-0006's actual win-region (32k, inj≤1%).
- The theory_skeptic's "kernel wins flip under serving" concern is **NOT supported by any plausible
  overhead assignment**: the dominant erosion (gather overlap) is mathematically bounded below a tie.
- **Therefore the missing serving cell is MODERATELY — not critically — load-bearing.** It is needed to
  *confirm* the magnitude (best→1.1×, the band is wide) and to rule out second-order effects this model does
  NOT capture (below), but it is **unlikely to REVERSE the sign**. CLAIM-0006's win-region survives this
  analytic bridge pending real confirmation.

## Limits / what this model does NOT capture (do not overclaim)
- **TTFT only, single request.** Does NOT model **batched throughput**: under high concurrency the *total
  recompute FLOPs* (where EXP-0006 showed CDC ties a fair PIC at inj/seq≥5%, since CDC recomputes the whole
  contiguous chunk while PIC recomputes a *smaller* selective set) could favor PIC for *aggregate throughput*
  even where per-request TTFT favors CDC. **This is the one regime where the real serving cell could still
  bite** — and it lives at inj/seq≥5%, OUTSIDE the 32k/inj≤1% win-region. Flagged honestly.
- Absolute kernel times are **reconstructed** from a single anchor + a work proxy, not independently measured
  (full EXP-0014 source archived). Ratios are firm (EXP-0021 CI); absolute ms are approximate.
- Overhead magnitudes are **plausible literature ranges**, not measured on this stack. PagedAttention's
  block-paged (non-contiguous) KV layout is NOT modeled — vLLM's native KV is itself paged, which could
  narrow CDC's "contiguous" assumption; the real cell is needed to settle this (VERDICT-0025 baseline #1).
- This BOUNDS, does not REPLACE, the owed vLLM+CacheBlend serving cell.

## Reproduce
`cd experiments/2026-05-31/EXP-0023 && /usr/bin/python3 impl/exp0023_analytic_bridge.py`
→ writes `e2e_sensitivity.csv` + `summary.json`. Deterministic (no RNG).
