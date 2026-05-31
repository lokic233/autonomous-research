# EXP-0015 Result — WIN-REGION MAP with bootstrap CIs + workload-prior sensitivity (CPU)

**Claim:** CLAIM-0006 · **Level:** 1 · **Device:** CPU-only (/usr/bin/python3, stdlib only — NO numpy/scipy, NO GPU/torch/CUDA) · **Date:** 2026-05-31
**Agent:** researcher-0002-laneA · reporting to orchestrator 22bd6bef
**Impl:** `impl/exp0015_winregion_map.py` (deterministic, MASTER_SEED=20260531, ~50s wall, <100MB)
**Data:** `experiment_result/results.json`, `experiment_result/results.csv`

## What this sharpens (lane mandate)
The surviving CLAIM-0006 contribution (per VERDICT-0023) is the **workload-conditioned WIN-REGION of CDC
repair on its accounting line** — slope~1 is a CDC-specific accounting identity, not a cross-engine law.
EXP-0005 located the win-region but gave **point estimates only** (single seed) with **no CIs** and **3
hand-picked sensitivities**. This experiment adds the statistics that gate-A's stats-rigor pass demands:
- **Nonparametric cluster bootstrap 95% CIs** (resample whole TASKS, the correct correlated unit) on
  the win-region fractions, **count-weighted AND token-weighted**.
- The **joint win-region** per the lane spec: `inj/seq <= 1% AND S >= 50k` (CDC's large-reused-context home).
- A **systematic 4×4 workload-prior sweep** (heavy-tail dump probability × base-context scale), with a CI
  at every grid cell — replacing the 3 ad-hoc variants — so we can state robustness *across* the prior.

Same evidence-grounded workload model as EXP-0005 (`input_data/sources.md`); same cost regimes from
EXP-0002 (recompute%≈inj/seq) and EXP-0006 (CDC-vs-fair-PIC edge only ~1.1–1.7× median, tie at inj/seq≥5%).
**PROXY caveat:** token counts proxy KV recompute work, not GPU wall-clock (gate-B, GPU, untouched here).

## Baseline prior (tail=1, ctx=1) — point + bootstrap 95% CI (291,454 injections, 20k tasks, B=600)

| Win-region metric | Point | Bootstrap mean | **95% CI** |
|---|---|---|---|
| **Count-fraction**, marginal inj/seq≤1% | 0.2461 | 0.2460 | **[0.2426, 0.2495]** |
| **Token-weighted fraction**, inj/seq≤1% | 0.0370 | 0.0369 | **[0.0361, 0.0379]** |
| Count-fraction, **joint** (≤1% AND S≥50k) | 0.1825 | 0.1824 | [0.1781, 0.1863] |
| Token-fraction, **joint** (≤1% AND S≥50k) | 0.0343 | 0.0343 | [0.0334, 0.0352] |
| Large-ctx share (S≥50k), count | 0.3991 | 0.3989 | [0.3917, 0.4053] |
| Large-ctx share (S≥50k), token | 0.4007 | 0.4005 | [0.3942, 0.4074] |
| **Count-frac win1 GIVEN S≥50k** (CDC home turf) | 0.4573 | 0.4572 | **[0.4531, 0.4613]** |
| Token-frac win1 GIVEN S≥50k | 0.0857 | 0.0857 | [0.0842, 0.0873] |

Reproduces EXP-0005's point estimates exactly and tightens them with CIs. The CIs are narrow (the
20k-task Monte-Carlo is well-resolved), so the *uncertainty* in these fractions is small — what matters
is their *magnitude* and *prior-sensitivity*, below.

## Workload-prior sweep (4 tail-scales × 4 ctx-scales = 16 cells; full table in results.csv)

| metric | range across all 16 priors | median | takeaway |
|---|---|---|---|
| count-frac win1 (inj/seq≤1%) | **0.175 – 0.408** | 0.313 | a sizable minority of *injections*, prior-dependent |
| **token-frac win1 (inj/seq≤1%)** | **0.027 – 0.081** | **0.037** | **small under EVERY prior — never exceeds ~8%** |
| count-frac win1 GIVEN S≥50k | **0.411 – 0.520** | 0.477 | **remarkably prior-STABLE ~½** |
| large-ctx share (count) | 0.251 – 0.764 | — | grows with ctx-scale (long-horizon agents) |

CI half-widths at every cell are ≤0.004 (see CSV `_lo`/`_hi` columns), so the ranges above are driven by
the *prior*, not sampling noise. Two robust structural facts emerge:

1. **The token-weighted win-region is a negligible slice under EVERY prior tested (2.7%–8.1%, median 3.7%).**
   Even when we triple the dump probability AND quadruple context size, ≥92% of injected *tokens* fall
   outside CDC's ≤1% win-region. Large tool dumps (file reads, code stdout, RAG bundles, JSON datasets)
   dominate token volume and live in the MID/DEGRADE regimes where CDC ties a fair PIC baseline.
2. **Conditioned on large reused context (S≥50k), CDC wins on ~½ of injections, robustly (41–52%, median 48%),
   independent of the prior.** This is CDC's genuine, stable home regime — the one SWE-ContextBench's
   >97%-cache-read finding says dominates real long-horizon SWE token *usage*. As ctx-scale rises (modeling
   200k–1M long-horizon agents), the *share* of traffic that is large-context grows to 60–76%, so this
   conditional region covers a growing fraction of real traffic.

## Honest verdict: **WEAKEN** (qualified — the conditional characterization survives, the unconditional one does not)

The honest question was: meaningful slice or negligible corner? **Both, on different axes — and the net is WEAKEN.**

- **By injected TOKENS (the work that actually matters for cost/latency): the win-region is a negligible
  corner.** It is 3.7% at the base prior and never exceeds ~8% across the entire prior grid. ~81% of tokens
  sit in the >5% degrade regime (EXP-0005), where CDC ties a fair PIC baseline (EXP-0006). A characterization
  pitched as "CDC saves recompute on agentic traffic" is **not supported in token-weighted terms** — the
  bulk of recompute work is in regimes CDC does not win.
- **By injection COUNT, conditioned on large reused context: it is a meaningful and prior-robust slice
  (~48% of S≥50k injections, stable across all 16 priors).** So the *conditional* CLAIM-0006 framing — "for
  long-lived, heavily-reused contexts (S≥50k), small tool-result injections (inj/seq≤1%) are common (~½ of
  injections) and CDC wins there" — **survives and is the defensible characterization**. But it must be
  stated conditionally, and with the honest caveat that these win-region injections carry only ~8.6% of the
  tokens *even within* the large-context regime (token-frac-given-large = 0.086 [0.084,0.087]).

**Net effect on CLAIM-0006: WEAKEN the unconditional/typical-case and any token-weighted framing; the
contribution is honest only as a CONDITIONAL count-level win-region map (S≥50k ∧ inj/seq≤1%), which is
real, prior-robust, and a meaningful minority of injections but a small minority of tokens.** This is
consistent with (and quantifies, with CIs) the committee's standing "useful narrow characterization, not a
broad law" position; it does not rescue a broad claim, and it does not weaken further than VERDICT-0023
already states — it puts CIs and prior-robustness on the win-region that VERDICT-0023 called the surviving leg.

## Limits / caveats (do not overclaim)
- **PROXY**, not GPU wall-clock; inherits EXP-0002/0005/0006 scope. Token-count → recompute-fraction mapping
  is the CDC accounting identity (EXP-0013); kernel/scatter wall-clock is gate-B (GPU, untouched).
- Win-region thresholds (inj/seq≤1%, S≥50k) are the literature-/EXP-derived operating points; the qualitative
  conclusions (token-frac tiny under every prior; count-frac-given-large ~½ and prior-stable) are robust to
  the ±10pp distribution-shift EXP-0005 already flagged, because they hold across the explicit 16-cell sweep.
- Distribution is modeled from cited anchors, not sampled from a live production trace corpus.
- Bootstrap is a cluster bootstrap over the *modeled* tasks: it quantifies Monte-Carlo/sampling uncertainty,
  NOT model-specification uncertainty (the latter is what the prior sweep addresses).

## Reproduce
`cd experiments/2026-05-31/EXP-0015 && /usr/bin/python3 impl/exp0015_winregion_map.py`
→ writes `results.json` + `results.csv` (copied into `experiment_result/`). Deterministic seed 20260531.
