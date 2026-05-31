# PROJ-0001 — Camera-Ready Polish Delta

**Date:** 2026-05-31 · **Agent:** researcher-0001-polish2 (final camera-ready lane, CPU-only) ·
**Orchestrator session:** 22bd6bef-b84b-4827-a371-87443ea8602f
**Scope:** READ-ONLY on claims/verdicts/maps/experiments. Document/draft-edit only.
NO claim/verdict/map edits, NO experiments, NO GPU/model CLIs/mapping re-probes (FORBIDDEN per MI350X postmortem).
**Base document (unchanged):** `prior_art/PROJ-0001/PAPER_DRAFT.md` (30,002 bytes, RED-TEAM-GO / submission-ready).
**This doc:** a polish-delta + tightened abstract + figure/table manifest + final consistency pass.
PAPER_DRAFT.md remains the authoritative base; apply these deltas at camera-ready typesetting.

---

## 0. Summary

The red-team verdict (`PAPER_REVIEW_REDTEAM.md`) is **GO / submission-ready, punch-list empty except 2
optional polish items**. This camera-ready pass:

1. **Confirms both red-team optional polish items are already satisfied** (no edit needed — see §1).
2. **Provides a tightened ≤250-word abstract** (246 words) with the 3-pillar thesis + "build SW
   prefix-sharing" landing in the first 3 sentences (§2).
3. **Provides a clean FIGURES/TABLES manifest** mapping each table/figure to its source EXP CSV/result
   file with verified paths (§3).
4. **Reports a final consistency pass**: every headline number in the abstract + intro was re-derived
   directly from the source CSVs/JSON this pass and **matches byte-for-byte. Zero inconsistencies** (§4).

**No blocking defect found. No promoted claim YAML touched. The paper is camera-ready.**

---

## 1. Red-team optional polish items — both already satisfied (verified this pass)

### 1a. FlashInfer-analytic label clarity (GPU-optional → kept analytic, no GPU run)
**STATUS: ALREADY SATISFIED in the draft. No edit needed.** The FlashInfer 41-152x multiple is labeled
**analytic** (not a measured FlashInfer run) in **8 distinct places** in `PAPER_DRAFT.md`, verified by grep:

- Abstract (line 32): "on an **analytic** paged-step projection ~41-152x slower than FlashInfer"
- §4.1 (lines 233-234): "`flashinfer` — *analytic* (48 paged-steps at ~0.03 ms/batch + measured SW
  bookkeeping; **not** a real FlashInfer run)"
- §4.3 heading (line 244): "The FlashInfer multiple is **analytic** (and a bonus)"
- §4.3 body (lines 246-251): "we label this explicitly as an **analytic paged-step projection, not a
  measured FlashInfer run** … with no real FlashInfer kernel invocation in the dataset … a *bonus widening
  multiplier* on top of the already-proven measured SW domination, not as a load-bearing measurement."
- §7 (lines 356-357): "the 41-152x-faster **analytic** reference of Section 4"
- Appendix A (line 408): "41-152x (**analytic**)"
- Appendix B (line 421): "41-152x … **ANALYTIC** denominator … `flashinfer` rows tagged **ANALYTIC**"

The prose is unambiguous: the **measured** 1.06-2.20x SW domination carries the thesis alone (self-healing,
both arms measured); the FlashInfer multiple is a demoted bonus. **No GPU run is required or recommended**
(an optional real FlashInfer kernel-latency bench would only widen an already-proven gap; per
PUBLICATION_READINESS.md §2b, deferrable). This camera-ready pass keeps it analytic.

### 1b. needs_attention re-probe wording — corrected, and does NOT leak into the draft (verified)
**STATUS: ALREADY SATISFIED. No edit needed.** Two independent checks:

- **`needs_attention.md` item 2** now reads as a driver-version-scoped threat-to-validity:
  "This is a DRIVER-VERSION-SCOPED characterization — future NVIDIA driver versions are a scoped
  limitation / threat-to-validity to STATE IN THE PAPER, **NOT a re-probe instruction** (re-probing the
  mapping ceiling is FORBIDDEN per learning/MI350X_CRASH_POSTMORTEM.md)." The stale "re-probe before
  paper-track" wording is gone.
- **The draft does not leak any re-probe instruction.** `grep -ni "re-probe|reprobe|re-run before|before
  paper-track" PAPER_DRAFT.md` → **zero matches** in any instruction sense. The only adjacent hit is §3.4,
  which explicitly states the driver-version scoping is "a stated threat-to-validity, **not** a re-run
  instruction" — correct hygiene, consistent with the MI350X-postmortem FORBIDDEN-re-probe constraint.

**Both optional polish items are closed. The draft needed no change for either.**

---

## 2. Tightened abstract (camera-ready replacement — 246 words, ≤250)

Replace the abstract + bullet block + standalone Thesis paragraph of `PAPER_DRAFT.md` with the following
single tightened paragraph. The 3-pillar thesis and the "build software prefix-sharing, not HW VMM CoW"
engineering conclusion both land in the **first three sentences** (sentence 1: the CoW/VMM intuition;
sentence 2: we built both arms + measured + the conclusion; sentence 3: the three-pillar + concession
structure). The detailed per-pillar bullets and the standalone **Thesis** block from the original draft can
be retained immediately below as an optional expanded restatement, or dropped at camera-ready for length.

> **Abstract.** Agentic LLM workloads fork conversation state into many speculative branches sharing a long
> common prefix — the textbook case for copy-on-write (CoW) over the KV cache, and seemingly the ideal
> target for hardware acceleration via NVIDIA's CUDA Virtual Memory Management (VMM): alias the prefix once,
> then let the GPU MMU diverge branches lazily on first write. We built both the HW VMM-CoW mechanism and a
> software prefix-sharing baseline (radix/refcount, in the vLLM-APC / RadixAttention lineage), measured them
> head-to-head on production GPUs (NVIDIA H100, AMD MI350X), and reach a single engineering conclusion:
> build software prefix-sharing, not HW VMM CoW. The indictment has three compounding pillars plus one
> honest concession. (I) Capacity: a conserved per-device CUDA-VMM access-descriptor budget — 523,404
> mappings (+/-0.6%), deterministic to 0.000% variance, charged at cuMemSetAccess — hard-caps branch
> mappings and splits across contexts (n=2: ~260K each), while AMD MI350X shows no wall to 80,000,000
> mappings (153x), making this a vendor portability cliff, not a GPU law. (II) Per-op cost: even below the
> ceiling HW CoW never wins — 0/12 across a prefix x fanout x rollback grid, 1.06-2.20x slower than software
> (both arms measured), and ~41-152x slower than FlashInfer (analytic projection). (III) Compound: capacity
> and per-op cost multiply into end-to-end throughput collapse — HW wins 0/8 fanout regimes and crashes at
> the ceiling for every B>=128, while software scales 280->800 tok/s. The sole HW advantage — a
> bit-identical, kernel-transparent write-after-share (max_abs_diff = 0.0) — is orthogonal to performance
> and does not redeem the abstraction.

**Word count: 246 (≤250).** Every number is identical to the source-verified values in §4. The original
draft's expanded bullet list (Pillars I-III + Concession) and standalone Thesis paragraph are preserved in
`PAPER_DRAFT.md` and may be kept as an optional expanded abstract or moved into §1 at typesetting.

---

## 3. FIGURES / TABLES manifest (camera-ready reproducible artifacts)

Each table/figure the paper needs, mapped to its source EXP result file (all paths verified to exist this
pass). All sources are CPU-readable artifacts already committed under `experiments/`. **No new artifact
generation or GPU run is required** — every figure is a plot/table over an existing CSV/JSON.

| # | Artifact | Pillar / §  | Type | Source file (verified path) | Key values to render |
|---|----------|-------------|------|------------------------------|----------------------|
| **T1** | Per-device conservation table | I / §3.2 | Table (3 rows) | `experiments/2026-05-30/EXP-A004/experiment_result/e3d_results.jsonl` | n=1: 523,404 \| n=2: 260,281+263,003=523,284 \| n=3: 171,633+174,206+177,325=523,164; total conserved ~523,300 (±0.05%), splits ~K/n |
| **T2** | 0/12 per-op cost grid (the 12-cell domination table) | II / §4.2 | Table or heatmap (12 cells × arms) | `experiments/2026-05-30/EXP-A001/experiment_result/ec_rollback_e2e.csv` | prefix{long4096,short512} × N{4,16} × R{0,4,16}; arms hw_vmm_cow / hw_vmm_cow_fullfwd / sw_prefix / flashinfer(ANALYTIC); hw/sw 1.056-2.196 (0/12 win); hw/flashinfer 41.31-151.48 (analytic) |
| **T3** | B-grid ceiling-crash table | III / §5.1 | Table (8 rows, 2 crash classes) | `experiments/2026-05-30/EXP-A003/experiment_result/et_tax_throughput.csv` (hw arm) | B=4 clean / B=16 transient_cublas(NOT_ceiling) / B=64 clean / B=128,256,511,919,1124 cuMemSetAccess **ceiling** crash; HW wins 0/8; B>=128 boundary sharp |
| **T4** | Cross-vendor 153x table | I / §3.4 | Table (NVIDIA vs AMD) | `prior_art/PROJ-0001/511ce2e2__CROSSVENDOR_RESULT.md` (corroborates EXP-A002/A004/A007 NVIDIA side) | NVIDIA 523,404 hard wall (2 MiB granule, CUDA 12.8/580.82.07) vs AMD MI350X no wall to 80,000,000 (4 KiB granule = 512× finer, ROCm 7.0.2.1 gfx950); 153× headroom; 3 AMD runs (4M/50M/80M) |
| **F1** | SW-scales-vs-HW-collapses throughput plot (keystone figure) | III / §5.2 | Line/bar chart (8 B values × 2 arms) | `experiments/2026-05-30/EXP-A003/experiment_result/et_tax_throughput.csv` (both arms) | SW 280.5→799.79 tok/s (0 crashes, rises with fanout) vs HW collapse at ceiling for B>=128; the visual keystone of the MLSys story |

### Supporting source files (cited inline, not standalone figures)
| Number | Source file (verified) | Used in |
|--------|------------------------|---------|
| 523,404 ceiling, `va_reserves:1`, `oom_call:cuMemSetAccess` | `EXP-A007/experiment_result/r1.json` | §3.1 ceiling provenance |
| "523,404 +/-0.6%" result summary | `EXP-A002/experiment.yaml` | §3.1, §3.3 headline |
| `K_CEILING = 523404` | `EXP-A003/impl/bench_ET_tax_throughput.py` | §3.1 throughput-experiment input constant |
| 519,936 median realized B×P (model input, NOT ceiling) | `EXP-A004/experiment_result/e3c_result.json`; `EXP-A004/impl/e3c_relevance.py` | §3.3 reconciliation (model input, not a measurement) |
| max_abs_diff_vs_clone = 0.0, bit-identical, `kernel_modified:false`, cow_fired | `EXP-A007/experiment_result/e1b_result.json` | §6 concession |

**Manifest note (T2/F1 arm hygiene):** when rendering T2 and F1, label the `flashinfer` column/series
**ANALYTIC** to preserve the §4.3 boundary (the measured SW-domination ratio carries the thesis; the
FlashInfer multiple is a bonus). When rendering T3, keep the two crash classes visually distinct
(`ceiling` vs `transient`) so the B>=128 boundary reads as sharp, per §5.1.

---

## 4. Final consistency pass — every abstract + intro number re-derived from source (this pass)

I re-derived each headline number directly from the source CSV/JSON this pass (not just from Appendix B),
to confirm the tightened abstract and §1 intro match the body and the source files. **All match. Zero
inconsistencies found.**

| Number (abstract + intro) | Re-derived from source this pass | Match |
|---|---|---|
| 523,404 (+/-0.6%) per-device ceiling at cuMemSetAccess | `r1.json` → mappings_before_fail=523404, va_reserves=1, oom_call=cuMemSetAccess; `EXP-A002/experiment.yaml` "523,404 +/-0.6%" | EXACT |
| 0.000% variance / deterministic | three independent paths (r1, clean control, e3d n=1=523,404) | EXACT |
| per-device split n=2 ~260K each | `e3d_results.jsonl` n=2: 260,281+263,003=523,284 (avg 261,642) | EXACT |
| AMD no wall to 80,000,000 = 153x; 4 KiB = 512× finer granule; 3 runs | `511ce2e2__CROSSVENDOR_RESULT.md`: "80,000,000 … = 153×", "4096 bytes … 512× finer", runs 4M/50M/80M | EXACT |
| 0/12 win; 1.06-2.20x slower than SW (both measured) | `ec_rollback_e2e.csv` recomputed: hw/sw min 1.0560 max 2.1955; HW wins 0/12 | EXACT |
| 41-152x slower than FlashInfer (analytic) | `ec_rollback_e2e.csv` recomputed: hw/flashinfer min 41.31 max 151.48 | EXACT |
| HW 0/8 fanout; crashes at ceiling every B>=128 | `et_tax_throughput.csv` hw arm: B=128/256/511/919/1124 all cuMemSetAccess ceiling crash; B=4,64 clean; B=16 transient_cublas(NOT_ceiling); HW wins 0/8 | EXACT |
| SW scales 280->800 tok/s, 0 crashes | `et_tax_throughput.csv` sw arm: min 280.50 (B=4), max 799.79 (B=919), 0/8 crashed | EXACT |
| max_abs_diff = 0.0, bit-identical, kernel-transparent | `e1b_result.json`: max_abs_diff_vs_clone=0.0, sdpa_output_bit_identical_to_full_clone=true, kernel_modified=false | EXACT |
| 519,936 model input (NOT a ceiling) | `e3c_result.json` → 519936; correctly framed as model input in §3.3 | EXACT |

**Cross-check (stale-number leak scan):** MEMORY.md's older "96x" AMD figure does **NOT** appear in the
draft or the tightened abstract (both correctly headline 153× = the largest clean watchdog-safe 80M run).
No stale number leaked. The per-context→per-device correction is fully landed in §3.2 (no per-context leak
in abstract or intro). The FlashInfer multiple is labeled analytic everywhere it appears.

**INCONSISTENCIES FOUND: NONE.**

---

## 5. Camera-ready apply checklist (typesetting)

1. Replace the abstract block in `PAPER_DRAFT.md` with the §2 tightened 246-word paragraph (optionally
   retain the original per-pillar bullets/Thesis paragraph as an expanded restatement under §1).
2. Render T1–T4 + F1 from the §3 manifest sources; label the `flashinfer` series ANALYTIC (T2/F1) and keep
   crash classes distinct (T3).
3. Keep §3.4 driver-version threat-to-validity wording as-is (no re-probe instruction).
4. No promoted claim YAML, verdict, map, or experiment was modified by this pass.

---

## Constraints honored
Wrote ONLY this file under `prior_art/PROJ-0001/`. No claim/verdict/map edits. No experiments. No
GPU/model CLIs/mapping re-probes (FORBIDDEN per MI350X postmortem). CPU-only. PAPER_DRAFT.md left
unchanged as the base. All figure-manifest paths and all consistency-pass numbers verified against the
existing source files (exact paths above). Did NOT seed new claims or re-mine adjacent/frontier space
(confirmed exhausted).
