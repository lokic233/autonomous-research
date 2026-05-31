# EXP-0006 Result — CDC vs a FAIR PIC-family baseline (recompute-fraction, CPU)

**Claim:** CLAIM-0006 · **Device:** CPU-only · **Date:** 2026-05-31 · **Agent:** researcher (EXP-0006)
**Methodology:** identical to EXP-0003 (token-count recompute-fraction proxy, single mid-prefix
insertion of R tokens into a reused prefix of length S, suffix preserved). Adds a PIC-family arm.
**Impl:** `impl/cdc_vs_pic_microbench.py` (main surface) + `impl/pic_window_sensitivity.py` (honesty check).
**Data:** `experiment_result/results.json`, `results.csv`.

## What this experiment answers
VERDICT-0012 (6/6 YELLOW) named the #1 GREEN-blocker: the 3 EXP-0003 baselines (vLLM-APC,
SGLang-RadixAttention, FlashInfer) are all **contiguous shared-prefix** engines — on a mid-prefix
insertion they recompute the **whole suffix** (~(1−f)·seq). So CDC's reported **8x–465x** advantage is
a *structural* gap (CDC does position-independent recovery; they cannot), **not** a competitive benchmark.
The committee demanded a **PIC-family** baseline that CAN do position-independent recovery, head-to-head
on recompute fraction. This experiment builds it.

## The fair PIC baseline (non-strawman)
Modeled on EPIC (arXiv:2410.15332), CacheBlend (arXiv:2405.16444, EuroSys'25), MEPIC (2512.16822),
and Irminsul (2605.05696) — all in `prior_art/PROJ-0002/CLAIM-0006/`. On a mid-prefix insertion of R
tokens, PIC recomputes ONLY:
  (a) the **R new tokens** (unavoidable; CDC pays this too),
  (b) a **boundary repair window W** around the insertion seam (attention-sink / LegoLink / CacheBlend
      local recompute), and
  (c) a **selective fraction p** of reused tokens to repair cross-attention drift (CacheBlend HKVD
      top-p%; EPIC/MEPIC block-level partial recompute).
PIC is **position-independent by construction** (that is the point of PIC) — and so is CDC. We sweep
p ∈ {1%, 5%, 10%, 15%} (CacheBlend's published operating range) and W ∈ {0, 32, 64, 256}.

> Note: per prior-art LaneA, **CDC is itself a PIC-family mechanism** (Irminsul = CDC-over-radix). So
> this is NOT a novelty test — it is an **intra-family recompute-fraction comparison**: does CDC's
> boundary-localized re-sync recompute fewer tokens than PIC's window+selective repair?

## Headline finding — CDC's advantage LARGELY COLLAPSES against a fair PIC baseline

| comparison | EXP-0003 (vs contiguous baselines) | EXP-0006 (vs fair PIC) |
|---|---|---|
| median advantage | ~27x | **1.69x** (PIC p=1%, W=256) |
| min / max | 8.3x / 465x | **1.02x / 11.84x** |
| with PIC tuned lean (p=1%, W=0) | — | **median 1.1x, range 1.0–5.5x** |

CDC still wins **15/15 cells** vs PIC(p=1%,W=256) — but the win is driven almost entirely by PIC's
**fixed costs** (boundary window W + the selective floor), not by any structural superiority of the CDC
mechanism. The 8x–465x story does **not** survive a fair baseline.

### Where CDC wins, and where it's a tie (surface, vs PIC p=1%, W=256)
- **inj/seq = 0.1%** (tiny injection): CDC 0.2–0.63% vs PIC 1.9–7.5% → **8.1x–11.8x**. CDC's only real
  win-region. Driven by PIC's fixed W=256 dominating a small seq; CDC localizes to ~1 chunk.
- **inj/seq = 1%:** **2.5x–5.5x**.
- **inj/seq = 5%:** **1.3x–2.2x** (marginal).
- **inj/seq = 25%:** **1.07x–1.27x** (≈ tie).
- **inj/seq = 100%:** **1.02x–1.07x** (tie — both recompute ~half the doubled sequence).

### Honesty check — most of even the residual win is PIC's *free* boundary-window parameter
`pic_window_sensitivity.py` sweeps W. The boundary window W is a tunable PIC knob, not a fundamental
cost. With PIC set to its leanest honest configuration (**W=0, p=1%**, pure selective recompute):

| inj/seq | CDC advantage vs PIC(p=1%, W=0) |
|---|---|
| 0.1%    | 1.74x–5.49x |
| 1%      | 1.30x–1.77x |
| 5%      | 1.08x–1.17x |
| 25%     | 1.02x–1.03x |
| 100%    | 1.00x–1.01x |

**Median CDC advantage vs lean PIC = 1.1x** (range 1.0x–5.5x). The only durable CDC edge is at the
extreme small-injection corner (inj/seq ≈ 0.1%), where CDC's chunk-localization (~0.2%) beats PIC's
~1% selective floor. Everywhere else it is a **statistical tie within parameter-tuning noise**.

## Honest verdict (for the orchestrator — I do NOT write claims/verdicts)
1. **CDC's 8x–465x advantage is an artifact of the EXP-0003 baselines' structural inability to do
   position-independent recovery.** Against a fair PIC baseline that CAN, the advantage drops to a
   **median ~1.1–1.7x**, and to a **tie (~1.0–1.2x) for any injection ≥5% of the sequence**.
2. **CDC has a real but narrow win-region:** very small injections (inj/seq ≲ 1%) on small-to-mid
   contexts, where CDC's chunk-grain localization (~1 chunk ≈ 0.2–1.5%) beats PIC's boundary-window +
   selective-recompute *floor*. The residual delta there is **~2–6x**, not orders of magnitude.
3. **This is a partially NEGATIVE result and should be reported as such.** Any CLAIM-0006 writeup must
   NOT cite the 8x–465x number as a competitive result. The defensible framing is the one prior-art
   LaneA already recommended: a **characterization / cost-map** paper (recompute ~ inj/seq, position is
   NOT the driver), explicitly stating that against PIC-family repair the recompute-fraction gap is
   small except in the low-injection regime — and that CDC's *mechanism* is itself PIC-family
   (Irminsul/EPIC), so no mechanism-novelty is claimed.
4. **Caveat (faithful to scope):** this is a **token-count proxy**, not wall-clock. CDC's chunk-grain
   re-sync and PIC's scattered selective recompute have *different kernel/scatter costs* per recomputed
   token; a recompute-fraction tie does not guarantee a wall-clock tie (PIC's HKVD scatter may be more
   expensive per token than CDC's contiguous chunk recompute, or vice-versa). The fair wall-clock
   head-to-head is GPU work (orchestrator territory) and is the real remaining GREEN-blocker.

## Prior-art / map deltas surfaced
- No NEW prior art hit beyond what's already in `prior_art/PROJ-0002/` (Irminsul, EPIC, MEPIC,
  CacheBlend, Cache-Craft all already logged). No cemetery collision.
- **Map-relevant finding to record:** the head-to-head recompute-fraction advantage of CDC over the
  PIC family is **~1.1–1.7x median (CPU token-count proxy), collapsing to a tie at inj/seq ≥ 5%** — i.e.
  the surviving CLAIM-0006 contribution (the cost-map) holds, but the *competitive margin* vs PIC is
  small and regime-dependent, NOT the headline 8x–465x.
