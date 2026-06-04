# PROJ-0037 — Data-systems/storage-encoding-semantics x feature-contract CROSS-AREA: per-shard category-cast silently sets an unstable .cat.codes integer feature across shards (NEW NON-OBVIOUS COUPLING)

10th cross-area coupling claim, FIRST-GREEN (CLAIM-0059) shape, GENUINELY ORTHOGONAL to every dead vein + to PROJ-0036's
fp16-dtype-x-stats angle (this is encoding-SEMANTICS x feature-contract, NO statistic involved). Clears BOTH hard gates
(incremental-composition + verify-the-composition) with real pre-verification.

## THE SEAM (two independently-owned subsystems)
- A = INGESTION/STORAGE: per-shard df[col].astype("category") for compression (smaller parquet, dict encoding). Mental
  model: "category is lossless; the string VALUES round-trip" — TRUE. A never produces an integer.
- B = FEATURE/ML: reads a shard, calls series.cat.codes for a cheap integer feature (no sklearn object to manage). Mental
  model: ".cat.codes is a stable integer encoding" — TRUE WITHIN ONE FILE.
- DIVERGENT DEFAULTS (verified, pandas 2.3.3 / pyarrow 21.0.0): astype("category") SORTS categories lexicographically
  over the OBSERVED values ONLY -> a shard observing c0..c39 vs one observing c10..c49 shifts every common code by the
  count of absent low categories (30/30 = 100% common categories differ). pyarrow.dictionary_encode() uses FIRST-SEEN
  (arrival) order (also unstable) and round-trips into pandas .cat.codes -> independent 2nd divergence source.

## PRIMARY THESIS (public-measurable)
Per-shard .cat.codes is UNSTABLE across shards with differing observed-category subsets -> a tree model's R^2 on
overlapping categories collapses 0.957 (fixed global map) -> -0.583 (per-shard .cat.codes), delta~1.54 (worse than the
mean predictor on trained categories), ZERO error raised. NULL EXIT: every shard observes the FULL alphabet -> codes
stable -> delta R^2 -> 0 (conditional on partial observation = the common case in time/geo-partitioned ingestion;
single-file pipelines immune).

## ★★ WHY IT CLEARS INCREMENTAL-COMPOSITION (load-bearing)
NEITHER endpoint predicts the outcome from its OWN side. A: "values round-trip" — correct + complete from A's view; A
never produced an INTEGER so never set an integer contract. B: ".cat.codes is standard label encoding" — correct WITHIN
one file; B never FITS an encoder, so fit-on-train/transform-on-serve discipline NEVER FIRES (no encoder to misuse) — the
integer contract was set INVISIBLY by A's storage cast, stable within any single file so B can't see the cross-shard
instability. The damage lives ONLY in A-per-shard-sorting x B-per-shard-.cat.codes x partial-observation. No single owner
sees all three. = CLAIM-0059 structure.

## ★ COMPOSITION-VERIFICATION (CLAIM-0065 kill lesson — verified wiring; first intuition was WRONG)
Scout's first hypothesis (arrival-order instability) was FALSIFIED by probe: astype("category") SORTS -> equal-alphabet
shards give identical codes. The REAL mechanism (partial-observation-per-shard shifts the sort) was verified end-to-end
through parquet write->read on a 50-cat partitioned dataset (100% co-occurring codes differ). pyarrow-dict-encode
first-seen path verified as a 2nd arm.

## KILLER SCREEN (cleared — see CLAIM-0067)
#1 not metric-validity (a semantic-contract correctness skew). #2 no seminal incumbent for the cross-shard storage-cast
seam. #3 the composition (storage-cast x cross-shard partial-obs) is novel; NOT standard fit-transform leakage. #4
currency = downstream model R^2 on overlapping categories. #5 real: pandas/pyarrow as-shipped, verified through parquet.
#6 the standard mitigation (fit a LabelEncoder/global map) is exactly what .cat.codes BYPASSES (no fit step fires). #7
baseline = fixed global string->int map. #8 L0 CAN fail (full-alphabet shards -> stable -> delta 0). #9 prod-framework
prior-art: sklearn encoders teach fit-on-train but target ENCODER OBJECTS; .cat.codes is a dtype property set by storage;
active leakage lit (Kapoor-Narayanan 2023) is within-dataset train/test contamination, NOT cross-shard storage-x-feature
skew with no fitted estimator -> orthogonal, no active cluster. #10 public-measurable (Criteo/NYC-taxi/partitioned-parquet
categorical). #11 version-current (pandas 2.3.3/pyarrow 21.0.0, documented-default sorting = stable).

## HONEST RISK
Requires shards with differing observed subsets (common in time/geo partitioning + streaming days; single-file immune) ->
the claim MUST state this condition or it overclaims. Reviewer "just fit an encoder" -> rebuttal = .cat.codes BYPASSES the
fit step; the storage cast made it LOOK like a free stable encoding so the discipline is never invoked = the undocumented
trap. Possible niche blog on .cat.codes instability -> targeted L1 prior-art search before committee. Scout-O GREEN-eligible.

## POSTURE
EXPAND/LIGHTWEIGHT: ONE sharp claim (CLAIM-0067), normal pipeline. L0 = CPU (partial-observation-fraction sweep showing
delta R^2 monotone in missing-alphabet-fraction + the pyarrow-dict-encode 2nd arm). Owner: orchestrator-r8-001.
