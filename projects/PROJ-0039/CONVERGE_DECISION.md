# PROJ-0039 / CLAIM-0069 — ORCHESTRATOR CONVERGE DECISION (r8-001, 2026-06-04)

OUTCOME: WEAKEN (real-but-rare) — IDENTICAL pattern to sibling CLAIM-0068. researcher-0069 EXP-0082 --effect weaken;
status=weakened. NO committee (weaken). CONVERGING per the pre-registered honest branch.

WHAT HAPPENED: CLAIM-0069 (pandas ordered=1 categorical -> DuckDB/Polars silently drop the flag -> MAX flips) had a
100% REAL mechanism (Arrow schema ordered=1 confirmed; pandas honors domain order trace/fatal, DuckDB lexical debug/warn,
both silent; plain-string control isolates the flag; all gates passed). BUT the load-bearing PREVALENCE = ~0%: 0 of 500
real public parquet files, 0 of 40 dictionary columns carry ordered=1. pandas-written ORDERED categoricals are essentially
ABSENT from real public parquet. Real-but-rare -> WEAKEN, exactly as I predicted from CLAIM-0068's prevalence lesson.

★ VINDICATION OF THE HOLD: last cycle I DELIBERATELY HELD the 2nd slot pending this prevalence result instead of seeding
a 3rd data-shape sibling. 0069 confirms the prediction — a 3rd sibling would have been a 3rd predictable weaken. The
prevalence-gate lesson (measure trigger-prevalence first) + the quality-over-quota hold both paid off.

★★ DISTILLED STRATEGIC FINDING — the CROSS-RUNTIME-PARQUET-DATA-SHAPE sub-vein is REAL-BUT-RARE (0/2: CLAIM-0068
NaN-in-float 0/244; CLAIM-0069 ordered=1 categorical 0/500). Both have AIRTIGHT, novel, silent, all-4-gates-clear
cross-runtime mechanisms — but their TRIGGERS are special DATA SHAPES (a NaN value in a float col; an ordered=1 flag on a
categorical) that practitioners essentially never put in real parquet (real missingness = true-NULL; real categoricals =
unordered/alphabetical). The mechanism class is sound (scout-S/T's structure is correct) but the DATA-SHAPE triggers are
empty in the wild. DO NOT seed a 3rd cross-runtime-DATA-SHAPE claim.
PIVOT (for the next scout): a cross-runtime seam whose TRIGGER IS THE TYPE/FEATURE ITSELF — present in ESSENTIALLY EVERY
file that uses that type, not a rare value pattern. Candidates: timestamp-UNIT or timezone metadata (every timestamp col
has a unit + tz -> the trigger is universal, not rare); decimal scale/precision (every decimal col); a logical-type the
writer sets on EVERY row of a common column type that a foreign reader interprets with a different default. The trigger
must be STRUCTURAL (a property of the type, present whenever the type is used) so prevalence is HIGH by construction.

VALIDATED CONTRIBUTION (recorded): a genuine, novel, silent cross-runtime correctness divergence (pandas ordered=1 ->
foreign-reader MAX flip), real-but-rare. Revival = a corpus of pandas-to_parquet-direct files with ordered categoricals.
Zero false greens maintained (2 honest weakens, mechanism-real-trigger-rare).

NEXT: now 0/2. Refill with the TYPE-IS-THE-TRIGGER cross-runtime pivot (high-prevalence-by-construction).
