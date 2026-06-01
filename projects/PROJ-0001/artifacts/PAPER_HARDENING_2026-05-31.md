# PROJ-0001 Paper-Track Hardening — Audit-Item Resolutions

**Date:** 2026-05-31 · **Agent:** researcher-0001-paper (paper-track hardening lane, CPU-only) ·
**Orchestrator session:** 22bd6bef-b84b-4827-a371-87443ea8602f
**Scope:** READ-ONLY against existing result files. NO claim/verdict/map edits. NO GPU / model CLIs /
mapping re-probes (FORBIDDEN per MI350X postmortem). Recommendations only — for the orchestrator
to fold into the promoted claims / writeup.

**Worklist source:** `prior_art/PROJ-0001/PAPER_SYNTHESIS_laneE.md` (CONSISTENCY-2/-3/-4).
**Note:** laneE's HIGH finding (per-context -> per-device, CONSISTENCY-1) is ALREADY DONE by the
orchestrator (see `registry/claims/PROJ-0001/2026-05-31/CLAIM-0002.yaml` `evidence_corrections`
block dated 2026-05-31). Not re-touched here.

---

## ITEM 1 [MED] — RESOLVED: K=519,936 vs 523,404 are the SAME quantity, two measurement methods

**Verdict: NOT a discrepancy. The two numbers are reconcilable and a primary-source reconciliation
ALREADY EXISTS — it simply never propagated out of `sessions/` into the experiment-dir docs or
prior_art. laneE flagged it as "unreconciled in any doc" because laneE only searched prior_art/;
the reconciliation lives in the committee traces.**

### The two numbers, with exact provenance
| Number | What it is | Source file + line |
|---|---|---|
| **523,404** | The clean single-reservation alias **ceiling** = the per-device access-descriptor budget, charged at `cuMemSetAccess`. Deterministic to 0.000% variance across 3 converging paths (R1, control, E3d n=1). | `experiments/2026-05-30/EXP-A007/experiment_result/r1.json:3` (`mappings_before_fail: 523404, va_reserves: 1, oom_call: cuMemSetAccess`); `EXP-A004/experiment_result/e3d_results.jsonl:1` (`n_contexts=1 -> 523404`); `EXP-A002/experiment.yaml:8` (headline "523,404 +/-0.6%"); `EXP-A003/impl/bench_ET_tax_throughput.py:64` (`K_CEILING = 523404`) |
| **519,936** | A **MEDIAN of B*P** (branches x prefix-pages) across prefix sizes in the older "Metric 4b" envelope sweep. Used ONLY as the input constant `K` to the e3c relevance/deployment-envelope **model** (max_branches = K // prefix_pages). | `experiments/2026-05-30/EXP-A004/impl/e3c_relevance.py:8` (`K = 519936  # measured median K on H100 (Metric 4b), driver 580.82`); `EXP-A004/experiment_result/e3c_result.json:3` (`"K": 519936`) |

### Why 519,936 < 523,404 (the reconciliation, primary-sourced)
523,404 is the **pure** ceiling: one VA reservation, alias one physical page into N VA slots, only
`cuMemSetAccess` draws from the budget. 519,936 is a **median of realized B*P** from multi-branch
runs that ALSO spend VA reservations; reserves draw from the SAME per-device budget at a different
weight (the R2 effect: a reserve+map pair ~= 1.745 budget units vs 1.0 for a bare map — see
`EXP-A007/.../r2`/`E3D_CORRECTION.md`), so realized B*P lands slightly BELOW the pure ceiling. The
Metric-4b sweep spans **522,752 @ 1 GiB prefix -> 516,096 @ 12 GiB prefix** (median 519,936); the
whole spread brackets 523,404 from below, exactly as the reservation-overhead model predicts.

This is documented verbatim in:
- `sessions/5_30_2026/048fcb0d-abd5-4c19-bb73-a0a7ca4ff0ec/committee_traces/E3D_CORRECTION.md:24-28`
  ("Reconciliation of the two K numbers (CC4.8 point 1)").
- `sessions/.../048fcb0d.../votes/cc48_final.txt:9` (area-chair CC48 final, point (1) marked
  **"reconciles. Two methodologies, not two truths."** — the 519,936 spread @1GiB->12GiB cited).
- `sessions/.../048fcb0d.../proposals/revote_nt1_cc48.md:7-8` (same reconciliation).
The original GREEN-blocker (`votes/d_CC48.txt:9` point (2)) was raised AND discharged in the same
committee round; the 6/6 GREEN was cast AFTER the reconciliation.

### One-paragraph reconciliation for the orchestrator to fold into CLAIM-0002 / the writeup
> The mapping ceiling is reported as two numbers that are the same underlying per-device
> access-descriptor budget measured two ways. **523,404** is the pure single-reservation alias
> ceiling — the budget charged at `cuMemSetAccess`, deterministic to 0.000% variance across three
> independent paths (one-reservation alias R1, clean-GPU control, and the n=1 context sweep), and is
> the value the paper headlines (523,404 +/-0.6%). **519,936** is the median realized B*P (branches x
> prefix-pages) over the older Metric-4b prefix-size sweep (522,752 @ 1 GiB down to 516,096 @ 12 GiB),
> used solely as the input constant to the e3c deployment-envelope *model*; it sits a fraction below
> the pure ceiling because multi-branch runs also spend VA reservations, which draw from the same
> per-device budget. The two numbers therefore bracket the ceiling consistently (a ~0.66% spread from
> the reservation-overhead model), not a genuine inconsistency.

### Recommendation
1. Standardize the **headline** on **523,404 +/-0.6%** (the measured ceiling); already the case in
   CLAIM-0002 + EXP-A002.
2. Add the one-paragraph reconciliation above wherever the constant is headlined, and label the e3c
   K=519,936 explicitly as a **model input (median B*P from Metric 4b)**, NOT the ceiling — consistent
   with how `EVIDENCE_BRIEF.md:20` already labels e3c "a MODEL (K=519936 median), not a measurement".
3. Optional hygiene: add a one-line note in `EXP-A004/impl/e3c_relevance.py:8` / `e3c_result.json`
   pointing to the 523,404 ceiling, so the reconciliation lives next to the data (NOT a claim edit).

---

## ITEM 2 [MED] — CONFIRMED: FlashInfer 41-152x is ANALYTIC; SW-domination 1.06-2.20x is MEASURED

**Source:** `experiments/2026-05-30/EXP-A001/experiment_result/ec_rollback_e2e.csv` (44 data rows,
13 cols; `notes` column = the ANALYTIC/measured tag). 12 cells = prefix{long4096,short512} x
N{4,16} x R{0,4,16}; each cell has 4 arms.

### Per-arm tagging (verified across ALL rows of the CSV `notes` column)
| Arm | Tag in every row | Status |
|---|---|---|
| `hw_vmm_cow` | `measured (SDPA contig decode over CoW KV + real driver CoW)` | MEASURED |
| `hw_vmm_cow_fullfwd` | `measured (full real-model forward per token)` | MEASURED |
| `sw_prefix` | `measured (SDPA contig decode + sw block-table bookkeeping)` | MEASURED |
| `flashinfer` | `ANALYTIC: 48 paged-steps@~0.03ms(batch) + measured sw bookkeeping` | **ANALYTIC** (projection, NOT a real FlashInfer run) |

The FlashInfer median_latency_ms is an analytic construction: (paged-step latency x 48 steps) + a
measured SW-bookkeeping term. There is NO measured FlashInfer kernel run in this CSV.

### Headline ratios recomputed from the CSV (median_latency_ms)
- **SW domination (MEASURED / MEASURED): `hw_vmm_cow / sw_prefix` = 1.056 - 2.195** across the 12
  cells. This EXACTLY matches the claim's "1.06-2.20x slower than software prefix-sharing" and is
  fully self-healing: BOTH numerator and denominator are measured arms. The "HW VMM CoW is
  dominated" headline stands on measured data alone.
  (min 1.056 @ long/N4/R0; max 2.195 @ short/N16/R16.)
- **FlashInfer multiple (MEASURED hw / ANALYTIC fi): `hw_vmm_cow / flashinfer` = 41.3 - 151.5**
  across the 12 cells. This matches the claim's "41-152x slower than FlashInfer" — BUT the
  denominator (FlashInfer) is the ANALYTIC projection in every cell.
  (min 41.3 @ long/N4/R0; max 151.5 @ short/N16/R16.)

### Recommendation
- In CLAIM-0001 and the writeup, label the FlashInfer multiple as **"41-152x slower than FlashInfer
  (analytic paged-step projection; not a measured FlashInfer run)"**. The measured 1.06-2.20x SW
  domination already carries the "dominated" thesis; FlashInfer is a bonus widening multiplier and
  must be marked analytic to survive systems review.
- A real FlashInfer cell is OPTIONAL and GPU-SAFE (this is a kernel-latency bench, NOT a mapping
  probe — no MI350X-postmortem risk). It is NOT required for the thesis; labeling suffices.
- (Documentation only — do NOT edit CLAIM-0001 YAML; this is a writeup-label recommendation.)

---

## ITEM 3 [LOW] — CONFIRMED: B>=128 ceiling crashes are cleanly separable from the B=16 transient

**Source:** `experiments/2026-05-30/EXP-A003/experiment_result/et_tax_throughput.csv` (8 hw rows + 8
sw rows; cols include `crashed`, `crash_call`, `notes`). Fanout B grid: {4, 16, 64, 128, 256, 511,
919, 1124}.

### HW arm — exact crash classification (verified row-by-row)
| B | crashed | crash_call | Class |
|---|---|---|---|
| 4 | False | none | clean |
| **16** | True | **`transient_cublas(1of3reps;NOT_ceiling)`** | **TRANSIENT** (rep1 cublas_status_execution_failed; 2/3 reps OK — explicitly NOT the ceiling) |
| 64 | False | none | clean |
| **128** | True | `cuMemSetAccess@B~63` | **CEILING** |
| **256** | True | `cuMemSetAccess@B~210` | **CEILING** |
| **511** | True | `cuMemSetAccess@B~360` | **CEILING** |
| **919** | True | `cuMemSetAccess_ceiling(illegal_access)@B~171` | **CEILING** |
| **1124** | True | `cuMemSetAccess@B~357` | **CEILING** |

- The ceiling crash (`cuMemSetAccess...`) first appears at **B=128** and occurs at **every B>=128**
  (128/256/511/919/1124) — **CONSISTENT with the claim "crashes for all B>=128".**
- The only sub-128 crash is **B=16**, and it is explicitly tagged a transient cuBLAS failure (1 of 3
  reps; "NOT_ceiling", 2/3 reps OK) — a DIFFERENT failure mode, NOT the mapping ceiling. B=64 is
  clean, confirming the B>=128 boundary is sharp.

### SW arm — no crashes, scales as claimed
All 8 sw rows: `crashed=False, crash_call=none`. Throughput 280.5 (B=4) -> peaks 799.79 (B=919),
matching the claim's "software scales 280->800 tok/s". (Min 280.5 @ B=4; max 799.79 @ B=919.)

### Recommendation
- In any paper table, split the `crashed` boolean into two columns: **`ceiling_crash`** (True only
  for B>=128, `cuMemSetAccess`) vs **`transient`** (True only for B=16, cuBLAS). This makes the
  B>=128 ceiling boundary read cleanly and prevents a skimming reviewer from misreading the B=16
  `crashed=True` as a fuzzy boundary. Purely cosmetic — the underlying data already distinguishes
  them in `crash_call`/`notes`. No claim/data change needed.

---

## Summary for orchestrator
| Item | laneE sev | Resolution | Action for orchestrator |
|---|---|---|---|
| 1. K=519,936 vs 523,404 | MED | **RESOLVED — same quantity, not a discrepancy.** Reconciliation already exists in `committee_traces/E3D_CORRECTION.md` + `votes/cc48_final.txt`; never propagated to prior_art (why laneE saw it as unreconciled). | Fold the one-paragraph reconciliation (Item 1) into CLAIM-0002 / writeup; label e3c K as model-input median. Headline = 523,404. |
| 2. FlashInfer 41-152x | MED | **CONFIRMED.** All `flashinfer` rows ANALYTIC; SW-domination 1.06-2.20x (recomputed 1.056-2.195) is measured/measured (self-healing). FlashInfer multiple recomputed 41.3-151.5 with ANALYTIC denominator. | Label CLAIM-0001 FlashInfer multiple "(analytic paged-step projection)". Optional GPU-safe real FlashInfer cell (not required). |
| 3. B>=128 crash | LOW | **CONFIRMED.** B>=128 (128/256/511/919/1124) all `cuMemSetAccess` ceiling crashes; B=16 is a tagged transient cuBLAS (NOT_ceiling); B=64 clean. SW 280->800 (max 799.79) no crashes. | Cosmetic: split `crashed` -> `ceiling_crash` vs `transient` in paper tables. |

**Constraints honored:** wrote ONLY this file under `prior_art/PROJ-0001/`. No claim/verdict/map
edits. No GPU / model CLIs / mapping re-probes. All findings verified against EXISTING result files
with exact paths + line refs above.
