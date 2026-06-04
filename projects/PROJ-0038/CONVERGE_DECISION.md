# PROJ-0038 / CLAIM-0068 — ORCHESTRATOR CONVERGE DECISION (r8-001, 2026-06-04)

OUTCOME: WEAKEN (real-but-rare). researcher-0068 EXP-0081 --effect weaken; status=weakened. NO committee (weaken). The
researcher left it at evidence_ready for the orchestrator. CONVERGING per the pre-registered honest branch.

WHAT HAPPENED: CLAIM-0068 (pandas-writes-NaN-as-NULL vs Arrow-native-NaN-as-value cross-runtime parquet seam) had an
AIRTIGHT mechanism (scout-S + researcher-0068 both verified end-to-end, both directions, both readers: null_count 2 vs 0;
self-join 5<->9; sum 3.0<->NaN; zero warnings). BUT the LOAD-BEARING PREVALENCE measurement (which I deliberately made
the L0's gate) came back 0/244 float columns across 39.9M rows of REAL public parquet (NYC-TLC + 9 HF tabular datasets):
ZERO carry stored NaN. Real missingness IS large but is ALWAYS true-NULL, never NaN-in-parquet. The at-risk seam is not
live in the corpus. Per the pre-registered it-matters threshold (non-trivial prevalence required), that's WEAKEN.
Two sharp boundary facts also narrowed it: (a) created_by is IDENTICAL for pandas-via-pyarrow vs pyarrow-direct (can't
fingerprint the writer); (b) pl.from_pandas defaults nan_to_null=True (the pandas->polars path collapses NaN->null).

WHY THIS IS THE SYSTEM WORKING: a GREEN-rated candidate (scout-S 8/10, all 4 gates) with a verified mechanism was
honestly WEAKENED because the prevalence I made load-bearing came back ~0. No false green. The conceptual contribution
(the undocumented file-provenance -> foreign-reader aggregate flip) is recorded with its REAL scope (real-but-rare;
revival condition = a corpus of genuinely pandas-to_parquet-direct files or NaN-computing Spark/polars pipelines).

★ DISTILL-WORTHY LESSON (PREVALENCE-GATE for cross-runtime/data-corpus claims): a cross-runtime seam can have an AIRTIGHT,
verified mechanism AND clear all 4 novelty gates AND STILL be a weaken if the TRIGGERING DATA CONDITION is rare in real
corpora. For any "writer-default X silently breaks reader Y" claim where X depends on a specific DATA SHAPE (NaN-in-float,
ordered-categorical, etc.), MEASURE THE PREVALENCE OF THE TRIGGERING CONDITION IN REAL PUBLIC DATA FIRST (cheapest could-fail),
BEFORE investing in the mechanism demo — if the trigger is ~0 in the wild, it's real-but-rare regardless of how clean the
mechanism is. The mechanism being real is necessary but NOT sufficient; the trigger must be PREVALENT.

★★ IMMEDIATE CONSEQUENCE FOR CLAIM-0069 (sibling cross-runtime parquet claim, IN FLIGHT, EXACT same structure): its
trigger is pandas-written ORDERED categoricals (ordered=1) with a non-alphabetical domain in real parquet. By the SAME
prevalence logic that just weakened 0068, this is LIKELY ALSO RARE (most parquet categoricals are unordered or
alphabetical; HF datasets wrap pyarrow which may not even set ordered=1). researcher-0069 was already told to measure
prevalence — if it comes back ~0, CLAIM-0069 is ALSO a weaken (real-but-rare), same as 0068. Watch for it.

NEXT: PROJ-0038 converged. PROJ-0039/CLAIM-0069 still live at L0 (prevalence-gated, same risk). Now 1/2.
