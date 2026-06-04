# PROJ-0036 — Data-systems/storage-format x downstream statistics CROSS-AREA: fp16 storage-dtype silently makes a column's summary stat DEPEND ON THE REDUCTION TOOL (NEW NON-OBVIOUS COUPLING)

9th cross-area coupling claim, FIRST-GREEN (CLAIM-0059) shape, GENUINELY ORTHOGONAL to every dead vein this run.
Screened to clear BOTH hard gates (incremental-composition + verify-the-composition) with real pre-verification.

## THE SEAM (two independently-owned subsystems)
- A = DATA/STORAGE team: casts a numeric feature column to float16 for storage/transport cost. fp16 SURVIVES a pyarrow
  Parquet round-trip unchanged (seam traversed — consumer receives fp16). Mental model: "fp16 represents my magnitude-100
  VALUES fine (range to 65504)" — TRUE about every stored element.
- B = ML/ANALYTICS team: computes a summary stat (mean/std for normalization) with whatever reduction tool is idiomatic.
- DIVERGENT DEFAULTS (verified in source, pandas 3.0.3 / numpy 2.4.6): numpy fp16 reduction UPCASTS the accumulator to
  fp32 (finite, quantized result). pandas nanops.nanmean keeps dtype_sum=dtype_count=fp16 for float kinds (NO upcast) ->
  the sum overflows fp16 (max 65504) -> inf, or count overflows at N>65504 -> nan. sklearn StandardScaler uses incremental
  fp64 -> correct. SAME column, THREE tools, THREE answers, no error/warning.

## PRIMARY THESIS (public-measurable)
On an fp16 column: pandas Series.mean() = inf/nan; numpy ndarray.mean() = quantized-but-finite; sklearn .mean_ = correct.
Divergence onsets at N~656 (magnitude-100 feature) / N~65504 (unit-scale, count overflow). The quantization-vs-overflow
tool DIVERGENCE itself holds at ALL N>=~1k regardless of magnitude. NULL EXIT: fp32/fp64 storage -> all agree ~1e-5.

## ★★ WHY IT CLEARS INCREMENTAL-COMPOSITION (load-bearing)
NEITHER endpoint predicts the outcome from its OWN side. A: "fp16 fits my magnitude-100 values" — correct about every
stored ELEMENT, predicts NOTHING about an ACCUMULATOR over N (A never sees N x value). B: "mean of a ~100 column is ~100,
finite" — correct ARITHMETICALLY, predicts NOTHING about pandas's fp16-accumulator returning inf (invisible at the API:
no dtype, no error, no warning). The surprise lives ONLY in fp16-storage(A) x fp16-accumulator-policy(pandas nanmean, B);
drop either -> vanishes. = CLAIM-0059 structure (numpy-fp32-acc vs pandas-fp16-acc is the NFKC-vs-NFC analog).

## ★ COMPOSITION-VERIFICATION (CLAIM-0065 kill lesson — verified ACTUAL wiring, not assumed)
Scout traced the real pandas nanops.nanmean source (dtype_sum=dtype for float kind, NOT upcast); empirically confirmed
numpy's opposite fp32-upcast (np.float16 sum -> inf but .mean() -> finite); verified fp16 survives the Parquet round-trip
(seam traversed); confirmed sklearn does NOT inherit it (fp64) = clean three-tools-three-answers contrast.

## NULL EXIT / COULD-IT-FAIL
fp32/fp64 storage -> all three tools agree to ~1e-5 (isolates fp16 storage-dtype as the cause). Honest boundary: the most
dramatic inf/nan needs magnitude>=100 OR N>65504; below that it degrades to quantization-vs-finite divergence (still
tool-divergent, less spectacular). The DIVERGENCE core holds at all N>=~1k.

## KILLER SCREEN (cleared — see CLAIM-0066)
#1 not metric-validity (a value-corruption + cross-tool divergence). #2 nearest lit (bf16/fp16 FMA-accum precision
1904.06376, Kahan/pairwise summation) is about SUMMATION ERROR not a storage-dtype x tool-choice SEAM. #3 the composition
divergence is novel; individual facts (fp16 range, accumulator policy) are not the claim. #4 currency = the reported stat
value (inf/nan/quantized vs true). #5 real: pandas/numpy/sklearn/pyarrow run as-shipped, verified in source. #6 the "fix"
(upcast before reduce / store fp32) is exactly what pandas's default does NOT do. #7 baseline = the fp64 ground-truth
mean. #8 L0 CAN fail (fp32/fp64 control agrees). #9 prod-framework prior-art: no framework documents the cross-tool
divergence; no active cluster. #10 public-measurable (synthetic + any fp16-castable public feature column). #11
version-current (pandas 3.0.3/numpy 2.4.6/pyarrow 24.0.0; root cause is intentional documented pandas code, stable).

## HONEST RISK
Magnitude-frequency objection (most dramatic inf needs magnitude>=100 or N>65504) -> defense: HEADLINE the cross-tool
DIVERGENCE (numpy quantizes / pandas inf / sklearn correct on the identical col, robust at all N>=~1k); any unnormalized
count/price/duration feature is magnitude>>1; even unit-scale breaks pandas at N>65504 (tiny for a feature store). Scout-N
GREEN-eligible, pre-verified end-to-end on cli:devvm14382.

## POSTURE
EXPAND/LIGHTWEIGHT: ONE sharp claim (CLAIM-0066), normal pipeline. L0 = CPU (N x magnitude x tool sweep on a real public
fp16-cast feature column to harden the magnitude-frequency objection). Owner: orchestrator-r8-001.
