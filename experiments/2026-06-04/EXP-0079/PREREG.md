# PREREG — EXP-0079 (CLAIM-0066, PROJ-0036)

**Researcher:** researcher-0066 | **Parent:** orchestrator-r8-001 | **Level:** 0 (CPU) | **Date:** 2026-06-04
**Committed BEFORE running the sweep / real-dataset arm.** (Composition-verification a-d already empirically confirmed; logged below as a gating precondition — the premise holds, so we proceed.)

## CLAIM (CLAIM-0066)
A numeric feature column stored as float16 silently makes the SAME column's mean DEPEND ON WHICH REDUCTION TOOL computes it:
pandas `Series.mean()` -> inf/nan (fp16 accumulator overflow); numpy `ndarray.mean()` -> quantized-but-finite (fp32 accumulator upcast);
sklearn `StandardScaler.mean_` -> correct (fp64 incremental). Three tools, three answers, NO error/warning. fp16 survives a pyarrow
Parquet round-trip (seam traversed).

## PINNED VERSIONS (installed, this machine cli:dengcchi-mac, venv python3.13)
- python 3.13 | pandas 3.0.3 | numpy 2.4.6 | pyarrow 24.0.0 | scikit-learn 1.9.0
- (These match the claim's target versions exactly: pandas 3.0.3 / numpy 2.4.6 / pyarrow 24.0.0.)

## COMPOSITION VERIFICATION (a-d) — the load-bearing wiring (CLAIM-0065 lesson)
GATING PRECONDITION: if ANY of (a)-(d) is FALSE on installed versions -> premise breaks -> honest report, no overclaim.
- (a) pandas `nanops.nanmean` source (site-packages/pandas/core/nanops.py L697-712): for `dtype.kind == "f"` ->
  `dtype_sum = dtype` AND `dtype_count = dtype` (NO upcast). So fp16 column -> fp16 sum accumulator (overflows at 65504)
  AND fp16 count (overflows -> inf/nan at N>65504). [READ IN INSTALLED SOURCE — CONFIRMED]
- (b) numpy `np.float16([100.]*2000).sum()` = inf (overflow) BUT `.mean()` = 100.0 finite (fp32 accumulator in mean reduce). [CONFIRMED]
- (c) sklearn `StandardScaler().fit(x).mean_` -> fp64, correct. [CONFIRMED]
- (d) fp16 -> to_parquet -> read_parquet keeps dtype float16 (pyarrow `halffloat`), values identical. [CONFIRMED]

## THE SWEEP (synthetic)
Build feature column (constant value = magnitude, so ground-truth mean == magnitude exactly), cast fp16, write+read parquet.
- N (rows) in {100, 656, 1000, 10000, 65504, 100000, 1_000_000}
- magnitude in {1, 100, 1000}
- For each (N, magnitude) compute mean via: (1) pandas Series.mean(), (2) numpy ndarray.mean(), (3) sklearn StandardScaler().fit().mean_, (4) fp64 ground truth.
- Record all four values + finite/inf/nan flag for each tool + relative error vs ground truth (when finite).
- BONUS ARM: also sweep std()/var() across the three tools (do they diverge too?).

## REAL PUBLIC DATASET ARM (harden the magnitude-frequency objection)
- sklearn California housing: feature `MedInc` (median income, ~scale 1-15) and `Population` (naturally magnitude ~100-35000),
  `AveOccup`, `HouseAge`. Cast each to fp16, write+read parquet, compute mean via all 3 tools + fp64 GT.
- Report which real features are naturally magnitude>=100 (i.e. how common unnormalized magnitude>=100 features are).
- Also: a derived magnitude-100 feature (MedInc*100) to mirror the "income x100" example, on REAL data distribution (not constant).

## CONTROL (isolates fp16 as cause)
- Identical pipeline with fp32 and fp64 storage dtype -> expect all three tools agree to ~1e-5 (no divergence, no inf/nan).

## PRE-REGISTERED NULL
fp16 storage causes <= ~1e-3 relative error in the downstream mean, IDENTICAL across all three tools (no divergence, no non-finite).

## IT-MATTERS THRESHOLD (what counts as SUPPORT)
1. pandas returns non-finite (inf/nan) at the predicted N x magnitude regimes (sum overflow when N*magnitude > 65504; count overflow -> nan when N > 65504), AND
2. the three tools DIVERGE (>= 2 distinct finite-or-not answers) at ALL N >= ~1k regardless of magnitude (numpy quantizes / pandas overflows-or-quantizes / sklearn correct), AND
3. the fp32/fp64 CONTROL shows all three tools agree to ~1e-5 (isolates fp16).

## COULD-IT-FAIL (honest kill branches)
- If fp32/fp64 control ALSO diverges -> data-scale artifact, not fp16 -> KILL/weaken.
- If pandas does NOT overflow at predicted N (e.g. newer pandas upcasts) -> premise broke -> KILL.
- If fp16 does NOT survive parquet round-trip -> seam not traversed -> KILL.
- Do NOT rig magnitudes; the real-dataset arm is the honesty check (use whatever magnitudes the data naturally has).

## DISPOSITION RULE
SUPPORT iff (1) AND (2) AND (3) all hold. Otherwise weaken/kill with honest write-up.
