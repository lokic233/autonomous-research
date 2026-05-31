# EXP-0013 Result — STATISTICAL-RIGOR PASS for CLAIM-0006 headline numbers (CPU)

**Claim:** CLAIM-0006 · **Device:** CPU-only (/usr/bin/python3, stdlib only — NO numpy/scipy, NO GPU) · **Date:** 2026-05-31
**Agent:** researcher-0006-priorart-stats · reporting to orchestrator 22bd6bef
**Addresses:** VERDICT-0022 required_evidence #3 (theory_skeptic): headline numbers are point estimates without
CIs/n/variance, AND "slope~1" could be an ENGINE-AVERAGING ARTIFACT across engines with different block sizes.
**Method:** re-ran the EXACT recompute-fraction token-count models from EXP-0003 (per-engine contiguous baselines:
vLLM-APC fixed-16-block, SGLang-RadixAttention token-granularity, FlashInfer==host-engine), the CDC arm
(EXP-0002/0003), and the lean fair-PIC arm (EXP-0006), now sweeping **inj/seq as the independent variable**
(9 ratios 0.1%→100%) × 3 seq-lens (4k/8k/32k) × 3 insert positions (f=0.1/0.5/0.9) × 5 seeds = 405 cells/engine.
Slope, 95% CI (Student-t, exact via stdlib inverse-CDF), R², Wilson CIs, and bootstrap median CIs all implemented
in pure stdlib. Impl: `impl/stats_pass.py` + `impl/stats_pass2.py`. Data: `experiment_result/results.{json,csv}`.

## HEADLINE: slope~1 does NOT survive per-engine decomposition as a CROSS-ENGINE law — it is CDC/PIC-mechanism-specific.

### (1) Per-engine slope of recompute% vs inj/seq% — LOW regime (inj/seq ≤ 5%, where the "slope~1" claim lives)
| engine | slope | 95% CI | R² | n | interpretation |
|---|---|---|---|---|---|
| **CDC** | **0.958** | **[0.937, 0.980]** | **0.972** | 225 | slope~1, TIGHT — recompute% ≈ inj/seq. Accounting identity (Pope/CacheBlend §4). |
| PIC (lean) | 0.907 | [0.738, 1.076] | 0.333 | 225 | ~1 but noisier (fixed W=256 floor dominates at small seq). |
| vLLM-APC | 0.476 | [−1.94, 2.89] | **0.0007** | 225 | **NO inj/seq relationship** — cost is position-driven, not injection-driven. |
| SGLang-Radix | 0.475 | [−1.94, 2.88] | **0.0007** | 225 | **NO inj/seq relationship** (same). |
| FlashInfer | 0.475 | [−1.94, 2.88] | **0.0007** | 225 | == host engine (Radix); **NO inj/seq relationship**. |

Per-engine × per-seq-len (low regime): CDC slope is stable across seq (4k:0.989, 8k:0.930, 32k:0.956; R²→0.999),
confirming the CDC slope~1 is NOT an averaging artifact across block sizes — it holds per seq-length. The three
contiguous engines have R²=0.0007 at EVERY seq-length (slope CI spans [−3.8, 4.7] — statistically indistinguishable
from zero relationship to inj/seq).

### (2) WHY the contiguous engines have no inj/seq slope — they are POSITION-driven (the decisive decomposition)
Position test (slope vs inj/seq at FIXED insert position f, contiguous engines):
- Radix/vLLM-APC: f=0.1 → slope 0.05; f=0.5 → 0.26; f=0.9 → 0.46. The "slope" is just (1−f) showing through;
  recompute% = (1−f)·100 + tiny inj term. Their cost is governed by WHERE you inject, not HOW MUCH.
- **Position spread** (range of recompute% across f at fixed seq,inj), mean over all cells:
  - vLLM-APC **69.3 pp** (median 76.2, max 80.0) · Radix/FlashInfer **69.3 pp** · **CDC 0.13 pp** (max 0.52) · PIC 0.00 pp.
- So: the contiguous baselines are ~entirely position-determined (~70 pp swing); CDC/PIC are position-independent
  (≤0.5 pp swing) and inj/seq-determined. These are TWO DIFFERENT COST LAWS.

### (3) The engine-averaging artifact — CONFIRMED, but precisely characterized
Averaging the 3 contiguous engines and fitting vs inj/seq gives slope 0.258, R² 0.075 (full range) — a meaningless
fit (the contiguous engines don't track inj/seq). **theory_skeptic is correct that "slope~1" must NOT be pitched as
an engine-averaged or cross-engine law.** The slope~1 is a property of the **CDC/PIC re-sync mechanism's token
accounting** (recompute = R + boundary-window; fraction = (R+W)/(S+R) ≈ inj/seq for W≪R), NOT a property the
vLLM-APC/SGLang-Radix/FlashInfer baseline engines share. Mixing them manufactures an intermediate, ill-fit slope.

### EFFECT = WEAKEN (with a surviving narrow claim)
- WEAKENS: any framing that "recompute% ~ inj/seq with slope~1" is an *engine-internal* law spanning
  vLLM-APC/SGLang-Radix/FlashInfer. It is NOT — those engines have R²≈0 vs inj/seq (position-driven, ~70 pp swing).
- SUPPORTS (narrowly): for the **CDC mechanism specifically**, recompute% ≈ inj/seq with slope **0.958 [0.937,0.980],
  R²=0.972**, stable per-seq-length, and position-independent (0.13 pp spread). But this is the **mechanism-derived
  accounting identity already demoted by the committee** (VERDICT-0017, CacheBlend §4 r%↔overhead), now CI-quantified.
- NET: the defensible CLAIM-0006 contribution is the **workload-conditioned win-region locating where real agentic
  traffic sits on the CDC accounting line**, NOT a cross-engine slope law. The slope~1 is CDC's identity, not a discovery.

## HEADLINE NUMBER CIs (n, variance) — addressing the "point estimates without error bars" objection

### CDC-vs-lean-PIC competitive margin (the "1.1–1.7x")
| regime | n | mean margin (95% CI) | median (bootstrap 95% CI) |
|---|---|---|---|
| ALL cells | 405 | 3.90× [3.36, 4.44] (sd 5.54) | **1.77× [1.56, 1.87]** |
| inj/seq ≤ 1% (win-region) | 135 | 8.63× | **6.20× [5.15, 6.86]** |
| inj/seq ≥ 5% (the "tie") | 225 | **1.29× [1.25, 1.33]** | — |
The "1.1–1.7x median" survives as a **median 1.77× [1.56,1.87]** over all cells; the **tie at inj/seq≥5% is
confirmed with a tight CI: 1.29× [1.25,1.33]** (NOT a true 1.0 tie — CDC keeps a small but statistically real
~1.3× edge even at large injections, driven by PIC's selective floor). The big means (3.9×, 8.6×) are right-skewed
by the small-injection corner — the median is the honest summary.

### Win-region fraction (Wilson 95% CI), "win" = CDC ≥5% cheaper than lean-PIC (beyond proxy noise)
| regime | wins/n | fraction | Wilson 95% CI |
|---|---|---|---|
| ALL | 360/405 | 0.889 | [0.855, 0.916] |
| inj/seq ≤ 1% | 135/135 | **1.000** | [0.972, 1.000] |
| inj/seq ≥ 5% | 180/225 | 0.800 | [0.743, 0.847] |
CDC's durable win-region (inj/seq ≤ 1%) is **100% of cells [Wilson 0.972, 1.0]** — clean. At inj/seq≥5% it still
"wins" 80% by the ≥5%-cheaper criterion but the *magnitude* is only ~1.3× (the practical tie).

### Attention-sink / sequence-start carve-out — first-chunk recompute fraction PER ENGINE (f=0 prepend)
| engine | sink (first-chunk) fraction of seq | note |
|---|---|---|
| CDC | **0.119%** | first content-defined chunk (~avg-chunk ≈ 19 tok / S) — the genuinely position-dependent corner. |
| vLLM-APC | 0.217% | first fixed 16-tok block (16/S). |
| SGLang-Radix / FlashInfer | 0.014% | LCP=0 at prepend ⇒ whole-seq recompute; "sink" = first token only (1/S). |
| PIC (lean) | 3.467% | boundary window W=256 at the seam (256/S) — PIC's structural sink-repair carve-out. |
This quantifies CLAIM-0006's required caveat: "position-independent EXCEPT the sequence-start sink chunk." For CDC
the sink carve-out is the first chunk ≈ 0.12% of the sequence — small but non-zero and genuinely position-dependent
(Irminsul's W vs S analysis). PIC's sink cost is larger (its fixed window), which is exactly why CDC wins the
small-injection corner.

## Caveats (faithful to scope)
1. **Token-count proxy, not GPU wall-clock** (same caveat as EXP-0002/0003/0006). Slopes/CIs are over recompute
   FRACTION; CDC's contiguous-chunk recompute vs PIC's scattered HKVD scatter have different per-token kernel cost.
   The fair wall-clock head-to-head (gate-B) is GPU work and remains the long pole [human-go].
2. **The CDC slope~1 is an accounting identity** (recompute=(R+W)/(S+R)), now CI-quantified — NOT promoted back to
   an emergent law. Committee demotion (VERDICT-0017) stands; this pass adds the error bars it asked for.
3. Seeds vary the random token streams (5 reps); within a (engine,seq,inj,f) cell the proxy is near-deterministic,
   so most variance is across the inj/seq grid (captured by the slope CIs) and across position (captured by spread).
