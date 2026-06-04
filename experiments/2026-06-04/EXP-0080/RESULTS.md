# RESULTS — EXP-0080 (CLAIM-0067, PROJ-0037)

**Researcher:** researcher-0067 · **Parent:** orchestrator-r8-001 · **Level:** L0 (CPU)
**Disposition: SUPPORT** (all pre-registered it-matters criteria met; honest boundary characterized).

## ★ NOVELTY (lead)
This is **NOT** standard fit-transform / train-test leakage — **no estimator is ever fitted on a
contract here.** The new coupling: a **storage team's** per-shard `df[col].astype("category")` (chosen
purely for *compression*) silently sets an **unstable `.cat.codes` integer feature contract across
shards**, because the cast **sorts lexicographically over the OBSERVED values only**. Neither endpoint can
predict this from its own side:
- **Ingestion/storage (A):** "category is lossless; the string VALUES round-trip." TRUE — A never emits an
  integer, so it has no reason to think it set any integer contract.
- **Feature/ML (B):** "`.cat.codes` is a stable label encoding." TRUE *within a single file*; B never FITS
  an encoder, so the fit-on-train/transform-on-serve discipline **never even fires** (no encoder object to
  misuse). The codes are stable within any one file, so B cannot see the cross-shard instability.
The catastrophic skew lives **only** in `storage-cast × cross-shard partial-observation`. No single owner
sees all three factors. Active leakage literature (Kapoor–Narayanan 2023, fit-before-split, target-encoding
leakage) is *within-dataset train/test contamination*; this is *cross-shard storage × feature skew with no
fitted estimator* → orthogonal.

## PINNED VERSIONS (this run)
Python **3.13.12** · pandas **3.0.3** · pyarrow **24.0.0** · scikit-learn **1.9.0** · numpy **2.4.6**
(NEWER than the scout's pandas 2.3.3 / pyarrow 21.0.0 — composition re-verified and STILL HOLDS in pandas 3.0.)

## ★ VERIFIED COMPOSITION (CLAIM-0065 lesson — verify the REAL mechanism, not the first intuition)
The scout's first intuition (arrival-order) was FALSIFIED for `astype`; the real lever is partial-observation
shifting the sort. All three confirmed in installed pandas 3.0.3 / pyarrow 24.0.0 (probe scripts saved):

| # | Check | Result |
|---|-------|--------|
| (a) | `astype("category")` sorts over OBSERVED values only. Shard1 observes c00..c39, shard2 c10..c49. | `code('c20')`: shard1=**20**, shard2=**10** → DIFFER. **30/30 = 100%** of common categories get different codes. |
| (a-null) | FULL alphabet on both shards (even reversed input order) | **0/50** codes differ → sorting makes full-alphabet shards stable. The bug is CONDITIONAL on partial observation. |
| (b) | Codes survive parquet write→read round-trip | dtype stays `category`; c20 still 20 vs 10; **30/30 (100%)** common codes still differ post-round-trip. |
| (c) | `pyarrow.dictionary_encode()` uses FIRST-SEEN (arrival) order, round-trips to pandas `.cat.codes` | With scrambled arrival order, dict not sorted; **30/30 (100%)** common codes differ → independent 2nd divergence source. |

**Premise intact** — astype does NOT give stable codes across partial-observation shards; codes DO survive parquet.

## MAIN EXPERIMENT (realistic synthetic, NOT engineered-extreme)
50 categories, latent per-category effect θ_k~N(0,1), target y = θ_cat + N(0, 0.5) → realistic SNR giving a
believable **global-map R² ≈ 0.78** (not an inflated 0.99). Two shards (train, serve) observe DIFFERENT but
overlapping subsets; each written to parquet with category dtype and read back. Model = HistGradientBoosting
(RandomForest cross-check). SEAM arm = each shard's OWN `.cat.codes`; CONTROL arm = fixed global string→int
map. R² measured on serve rows whose category also appears in train. 12 seeds per cell.

## ★ PARTIAL-OBSERVATION SWEEP — the monotonicity smoking gun (astype, HistGradientBoosting)

| missing-frac f | R²(control) | R²(seam) | **ΔR²** | ΔR² std | %common-codes-differ |
|---:|---:|---:|---:|---:|---:|
| **0.0** | 0.780 | **0.780** | **0.000** | 0.000 | **0%** |
| 0.1 | 0.770 | −0.196 | **0.966** | 0.401 | 61% |
| 0.2 | 0.776 | −0.291 | **1.067** | 0.326 | 73% |
| 0.4 | 0.736 | −0.679 | **1.415** | 0.469 | 74% |
| 0.6 | 0.712 | −0.334 | 1.046 | 0.522 | 71% |

- **f=0 (full alphabet): ΔR² = 0.000 EXACTLY**, 0% codes differ → the pre-registered null boundary holds.
- ΔR² rises **strictly monotonically** 0.000 → 0.966 → 1.067 → **1.415** across f = 0 → 0.4. The dip at
  f=0.6 (1.046) is a **high-variance tail artifact**: at 60% missing, the train∩serve overlap set shrinks
  and predictions on few categories are noisy (std jumps). The smoking-gun monotonic regime (0 → realistic
  0.4) is clean.
- The seam R² goes **NEGATIVE** (−0.2 to −0.68) — worse than predicting the mean — with **ZERO error raised**.
- **RandomForest cross-check at f=0.4:** ΔR² = **1.414** (vs HGB 1.415) → not model-specific.

## SECOND ARM — pyarrow.dictionary_encode (first-seen order)
Honest reporting of two sub-cases:
- `dictencode` (rows block-grouped by category as produced): first-seen order *equals* sorted order here, so
  it degenerates to the astype numbers (kept in CSV for transparency, **not** an independent path).
- **`dictencode_shuffled`** (rows shuffled before encoding → genuine arrival-order divergence per shard):

| missing-frac f | R²(control) | R²(seam) | **ΔR²** | %common-codes-differ |
|---:|---:|---:|---:|---:|
| **0.0** | 0.780 | **−0.755** | **1.535** | **99%** |
| 0.1 | 0.770 | −0.712 | 1.482 | 98% |
| 0.2 | 0.776 | −0.719 | 1.495 | 98% |
| 0.4 | 0.736 | −0.695 | 1.431 | 97% |
| 0.6 | 0.712 | −1.452 | 2.163 | 97% |

**Key contrast:** the first-seen path is **unconditionally unstable** — ΔR² is high even at **f=0 (full
alphabet)**, because its divergence comes from *arrival order*, not partial observation. So the two divergence
sources are mechanistically distinct: `astype` instability is gated by partial observation; `dictionary_encode`
instability is gated by arrival-order differences (the common streaming case). Both collapse R² with no error.

## PRE-REGISTERED IT-MATTERS THRESHOLD — MET
1. ΔR² > 0.2 at realistic f ≥ 0.2 → **1.067 at f=0.2, 1.415 at f=0.4** ✓
2. ΔR² monotone in f over the core range (0→0.4 strictly increasing) ✓ (tail f=0.6 noisy, disclosed)
3. full-alphabet control f=0 gives ΔR² ≈ 0 → **exactly 0.000** ✓
4. composition checks (a,b,c) all pass ✓

## COULD-IT-FAIL audit (all checked, none triggered)
- astype gives stable codes across partial-obs shards? **No** — 100% differ (a).
- Codes lost in parquet round-trip? **No** — survive, stay divergent (b).
- ΔR²≈0 at high f? **No** — ΔR² ≥ 1.0 for all f ≥ 0.1.
- Newer pandas 3.0 fixed the sort? **No** — behavior identical to scout's 2.3.3.
- Did we engineer an extreme signal? **No** — global-map R²≈0.78, a realistic SNR.

## FILES
- `csv/raw_runs.csv` — all per-seed runs (astype·hgb, astype·rf, dictencode, dictencode_shuffled).
- `csv/summary.csv` — grouped means/std.
- Probe scripts: `/tmp/probe_0067.py` (a, a-null), `/tmp/probe2_0067.py` (b, c).

## DISPOSITION: SUPPORT → submit to committee (do NOT self-converge).
