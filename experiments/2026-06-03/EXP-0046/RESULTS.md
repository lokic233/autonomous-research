# RESULTS — EXP-0046 (CLAIM-0047) — INCONCLUSIVE / sim tripped its OWN pre-registered bug-check

**Outcome: keep-exploring (INCONCLUSIVE — corrected re-run required).** Researcher-0044 completed the
Monte-Carlo compute (results.csv, 23 rows, 1063s) but went stale before synthesis. Orchestrator (r4-001)
recorded this honest finding directly from the committed CSV — NOT fabricated, NOT rubber-stamped.

## THE PRE-REGISTERED BUG-CHECK FAILED (this gates everything)
The PRE_REGISTRATION.md states verbatim: "At alpha=0 (memoryless) the claim predicts ZERO penalty. If
alpha=0 shows a big penalty (|penalty| > 5%), the sim or policy is BUGGY -> fix before trusting alpha>0."

**Measured alpha=0 penalty = -0.459 (-46%)** (alpha_B1 row) and **-0.275 (-28%)** (alpha_B2 row).
|penalty| = 46% and 28% — BOTH >> the 5% bug-check threshold. By the experiment's OWN locked rule,
the sim/policy comparison is mis-specified and the alpha>0 results CANNOT be trusted as evidence.

## WHY (diagnosis): policy A "does-not-complete" artifact
At realistic alpha (0.005-0.02) the huge headline penalties (+3700% to +4500%) co-occur with
**dnc_A = 0.57-0.62** — policy A (restart-from-last-checkpoint) FAILS TO COMPLETE 57-62% of rollouts,
while dnc_B ~0.01-0.02. The +4000% is therefore largely an artifact of policy A never terminating
(re-failing forever inside the elevated-hazard region with no bounded-attempt accounting), NOT a fair
expected-wasted-token comparison. The negative alpha=0 penalty shows the dual flaw: policy B's
overshoot OVER-rolls-back when there is no rising hazard, wasting ~46% there.

## DISPOSITION: NOT a HELD. NOT a clean kill either — the DIRECTION may survive a corrected sim.
Required fix before any committee: (1) bound policy A's re-attempts + account wasted tokens fairly on
non-completion (cap horizon, count tokens-to-give-up, not infinite); (2) make policy B NOT overshoot
when no deviation is inferred so alpha=0 calibrates to ~0 (|penalty|<5%) AS PRE-REGISTERED; (3) THEN
re-measure penalty(alpha). Only if alpha=0 calibrates ~0 AND alpha>0 shows >=25% monotone is it HELD.

## Honest reusable signal (directional, NOT evidence): under a rising hazard, restart-from-last-ckpt
does appear to re-fail more than deviation-aware rollback — but the magnitude is uninterpretable until
the alpha=0 calibration passes and the dnc accounting is fair. Committed CSV: results/results.csv.
