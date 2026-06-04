# PROJ-0037 / CLAIM-0067 — ORCHESTRATOR CONVERGE DECISION (r8-001, 2026-06-04)

VERDICT-0066: committee#1 UNANIMOUS 6/6 YELLOW (no RED). ★ Framework-issue-tracker gate CLEARED (5 independent reviewer
searches, no collision -> definitively NOT a CLAIM-0066 repeat; the new gate worked). Exceptionally clean L0.

DECISION: CONVERGE (accept the strong honest yellow; do NOT advance to the L1).

RATIONALE (ORCHESTRATOR_CHARTER job #2 + mechanism-known-ceiling + CLAIM-0054 weigh-the-L1-cost):
1. ALTITUDE = framing-composition-over-DOCUMENTED-mechanism. The sort-over-observed-values mechanism is documented
   (Categorical.codes API); the non-portability is community folklore (SO Q54731396). The delta is the CONSEQUENCE
   framing (unstable cross-shard ML feature IDs) — real + unfound pre-existing, but a documentation-coverage gap, not a
   mechanism discovery. Same ceiling family as CLAIM-0061/0064 (documented/known mechanism -> caps at yellow).
2. ★ THE GREEN PATH'S BEST CASE IS REDUCED-ALTITUDE OR RED: the area_chair predicts the Global-CategoricalDtype baseline
   will ZERO deltaR2 (expected -> "missing-practice issue, not framework defect" -> GREEN at a REDUCED altitude at best);
   AND the load-bearing sociotechnical assumption (real consumers read raw .cat.codes cross-shard as ML features) is
   ASSERTED not measured -> if no real pipeline does this, the multi-shard pipeline is a STRAWMAN -> RED. So the L1's
   modal outcomes are (a) reduced-altitude "missing-practice awareness" green or (b) strawman RED — low expected value
   for a heavy 5-evidence-item + 3-baseline L1.
3. The strawman risk is the killer: a green REQUIRES proving a real-world consumer anti-pattern exists (raw .cat.codes
   used cross-shard as features) — hard to establish convincingly, and the evaluation_prosecutor's unrebutted point is
   that any competent multi-file practitioner applies Global CategoricalDtype / OrdinalEncoder, which trivially prevents it.
4. LIGHTWEIGHT posture: ONE sharp claim per fresh area; converge the honest yellow + move on.

VALIDATED CONTRIBUTION (recorded honestly): per-shard astype("category") + raw .cat.codes yields UNSTABLE integer ML
feature IDs across separately-cast shards under partial category observation (verified CURRENT pandas 3.0.3; exact f=0
null boundary; strict monotonic deltaR2 0->1.415 over f=0->0.4; seam R2 NEGATIVE with zero error; RF cross-check; pyarrow
dict-encode 2nd arm unconditionally unstable). A real, clean, well-controlled cross-shard feature-contract instability —
honestly bounded to "conditional on partial observation + a consumer who reads raw .cat.codes cross-shard without global
schema management." The honest yellow IS the contribution. Zero false greens maintained.

NOTE (the issue-tracker gate PAID OFF): CLAIM-0066 died RED on a pandas-issue-tracker collision the scout missed;
CLAIM-0067 (sibling data-systems claim) was screened WITH the new gate + the committee independently CONFIRMED no
collision -> the gate correctly distinguished a documented-but-unreported-framing claim (yellow) from a
reported-and-patched bug (red). The gate is a durable asset.

NEXT: now 0/2 (PROJ-0037 was the last live project; PROJ-0036 died RED last cycle). See run-state assessment.
