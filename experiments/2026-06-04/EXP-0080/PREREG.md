# PRE-REGISTRATION — EXP-0080 (CLAIM-0067, PROJ-0037)

**Researcher:** researcher-0067  **Parent:** orchestrator-r8-001  **Level:** L0 (CPU)
**Date:** 2026-06-04  **Written BEFORE main experiment + sweep runs.**

## PINNED VERSIONS (installed, this run)
- Python 3.13.12  (venv ~/ros_venv_0067 on cli:dengcchi-mac)
- pandas 3.0.3   (scout used 2.3.3 — NEWER here; re-verify composition holds)
- pyarrow 24.0.0 (scout used 21.0.0)
- scikit-learn 1.9.0
- numpy 2.4.6

## CLAIM UNDER TEST
A storage team's per-shard `df[col].astype("category")` (compression) silently sets the integer
mapping a feature team consumes via `.cat.codes`. Because the cast SORTS lexicographically over the
OBSERVED values per shard, categories co-occurring across shards with DIFFERENT observed subsets get
DIFFERENT codes — collapsing a tree model's R² on overlapping categories vs a fixed-global-map control,
with NO error raised. CONDITIONAL on partial observation (full-alphabet shards → stable → no bug).

## COMPOSITION-VERIFICATION PLAN (do FIRST; CLAIM-0065 lesson)
- (a) astype("category") sorts over OBSERVED values only → shard observing c00..c39 vs c10..c49 gives
  different `.cat.codes` for common category c20. Full-alphabet both shards → identical codes.
- (b) codes SURVIVE parquet write→read round-trip and remain divergent.
- (c) pyarrow.dictionary_encode() uses FIRST-SEEN order (not sorted), round-trips into pandas
  `.cat.codes` as an independent 2nd divergence source.
- IF astype gives stable codes across partial-obs shards (newer pandas fix) → premise breaks → honest report.

## MAIN EXPERIMENT
- Synthetic: K=50 categories; per-category latent effect θ_k ~ N(0, σ²); target y = θ_{cat} + noise.
  REALISTIC signal (not engineered extreme): pick σ/noise so global-map R² is a believable ~0.8-0.95.
- TWO shards (train, serve) observing different but OVERLAPPING category subsets (drop a fraction of the
  alphabet per shard, disjoint missing sets → realistic time/geo partitioning).
- Write each shard to parquet with category dtype; read back.
- SEAM arm: TRAIN tree (HistGradientBoosting + RandomForest) on train shard's `.cat.codes`; PREDICT on
  serve-shard rows whose category ALSO appears in train, using serve shard's OWN `.cat.codes`. Measure R².
- CONTROL arm: same pipeline but FIXED GLOBAL string→int map for both shards. Measure R².
- ΔR² = R²(control) − R²(seam) on the SAME overlapping serve rows.

## PARTIAL-OBSERVATION SWEEP (core: it-matters + could-fail)
- Sweep missing-fraction f ∈ {0, 0.1, 0.2, 0.4, 0.6} (fraction of alphabet absent per shard).
- Multiple seeds (≥10) per f; report mean ± std ΔR².
- PREDICTION: ΔR² ≈ 0 at f=0 (full alphabet → stable codes), and grows MONOTONICALLY with f.

## SECOND ARM
- Repeat seam arm with pyarrow.dictionary_encode() (first-seen order) instead of astype → show it ALSO
  produces cross-shard instability / R² collapse.

## PRE-REGISTERED NULL
Per-shard `.cat.codes` is stable across shards → ΔR² ≈ 0 independent of missing-fraction.

## IT-MATTERS THRESHOLD (decision rule, set BEFORE running)
SUPPORT iff ALL of:
1. ΔR² > 0.2 at a realistic missing-fraction (f ≥ 0.2), AND
2. ΔR² monotone non-decreasing in f (across the sweep means), AND
3. full-alphabet control f=0 gives ΔR² ≈ 0 (|ΔR²| < 0.02), AND
4. composition checks (a,b,c) all pass.
WEAKEN/KILL iff: astype gives stable codes across partial-obs shards, OR ΔR²≈0 at high f, OR codes don't
survive parquet round-trip, OR non-monotone. Report honestly either way. Do NOT engineer an extreme
category/target relationship to inflate the collapse.

## NOVELTY FRAMING
NOT standard fit-transform leakage (no fitted estimator). The NEW coupling: storage cast's per-shard
sorting silently sets an UNSTABLE `.cat.codes` feature contract across shards — invisible to ingestion
(only string values, which round-trip) and to ML (codes stable within one file, no encoder fit to misuse).
