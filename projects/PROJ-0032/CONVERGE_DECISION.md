# PROJ-0032 / CLAIM-0062 — ORCHESTRATOR CONVERGE DECISION (r7-001, 2026-06-04)

OUTCOME: CLEAN L0 KILL (researcher-0062, EXP-0075, result_effect=kill -> DEAD-0012). NO committee, NO fake verdict
(verdict_history empty) — exactly the ideal cheap self-falsification pattern (cf. CLAIM-0044). status: killed.

DECISION: CONVERGE (ratify the honest kill; the researcher completed the kill but did not touch .converged).

WHAT HAPPENED: CLAIM-0062 (Pydantic->vLLM/xgrammar constraint-enforcement PORTABILITY CLIFF) was FALSIFIED at the
pinned latest production xgrammar 0.2.1 (wheel 2026-05-17). The claim's premise — "xgrammar silently DROPS EVERY ONE
of {minimum,maximum,exclusiveMin/Max,multipleOf,minLength,maxLength,pattern}" — is FALSE: xgrammar 0.2.1 ENFORCES
5/8 keyword families cleanly (minimum, maximum, minLength, maxLength, pattern). Only `multipleOf` is wholesale-dropped
(divisibility is not expressible in a finite regular grammar; ~2% of constraint-bearing schemas). Measured D (drop rate
over real JSONSchemaBench constraints) = 0.052 [95% CI 0.040-0.067] << the pre-registered IT-MATTERS threshold D>=0.30,
and V>=0.10 was NOT met on a common keyword (`maximum` drop 4.8%, a boundary-magnitude bug). The "differential portability
cliff" headline does NOT survive measurement: vLLM-auto/xgrammar is mostly CLOSED on these keywords, not open.

WHY THIS IS A WIN (not a failure): this is precisely the could-it-fail branch the pre-registration NAMED (killer #8:
"if the pinned xgrammar version DOES enforce these keywords, D->0 -> KILL"). The researcher honored the honesty branch
(no corpus massaging) and reported the kill. The pipeline does NOT manufacture greens; a folklore-derived premise
("guided decoding ignores semantics") died on real measurement against the CURRENT version. Zero false greens maintained.

GENUINE RESIDUAL (recorded as DEAD-0012 revival condition, NOT pursued under lightweight posture): a much NARROWER bug
report could survive — "xgrammar 0.2.1 has a pattern (x) length co-enforcement bug (length bound silently dropped when a
string leaf carries both pattern AND minLength/maxLength), integer-range boundary leaks at certain magnitudes (e.g.
max in {130,153,180} accept M+1), no number-range or multipleOf support -> silent OpenAI-vs-vLLM divergence on ~5-8% of
constraint-bearing public schemas." That is a bug report materially below the IT-MATTERS bar, not the broad cliff thesis.

DISTILL-WORTHY LESSON (for orchestrator.md): the production-seam shape has a NEW failure mode beyond killer #3/#9 —
VERSION-CHASE: a cross-backend "divergence" claim built on folklore about tool B's behavior can be STALE — the fast-moving
tool (xgrammar) may have ALREADY CLOSED most of the gap in its latest release. SCREEN AT DESIGN: pin + verify tool B's
CURRENT keyword/feature coverage BEFORE seeding, not the folklore version. (The scout's prior-art was thorough on the
SEAM but assumed xgrammar's drop-everything behavior from the seminal-paper era; the current release enforces 5/8.)

NEXT: refill the freed slot with a NEW fresh-area project (and screen the next claim's tool-B-behavior at the PINNED CURRENT version).
