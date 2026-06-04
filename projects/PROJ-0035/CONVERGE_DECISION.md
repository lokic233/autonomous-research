# PROJ-0035 / CLAIM-0065 — ORCHESTRATOR CONVERGE DECISION (r8-001, 2026-06-04)

OUTCOME: CLEAN L0 KILL (researcher-0065, EXP-0078, result_effect=kill -> DEAD-0013). status: killed. NO committee, NO
fake verdict (verdict_history empty) — the ideal cheap self-falsification. researcher self-converged (.converged set).

DECISION: RATIFY the honest kill. The decisive shard-count-monotonicity control returned the pre-registered NULL EXACTLY.

WHAT HAPPENED: CLAIM-0065 was the run's strongest green-track candidate — the FIRST claim screened to clear the
SHARPENED incremental-composition ceiling (scout-K argued convincingly neither endpoint predicts the bimodal rare-source
starvation). But the make-or-break could-fail risk MATERIALIZED at L0: researcher-0065 verified IN THE INSTALLED datasets
4.8.5 SOURCE that interleave_datasets samples a source PER-EXAMPLE via Categorical(p) UPSTREAM of the shuffle buffer
(RandomlyCyclingMultiSourcesExamplesIterable._get_indices_iterator), so shard cardinality is fully absorbed inside each
source's concatenated sub-stream and NEVER surfaces as a burst. Divergence-vs-shard-count is FLAT at the Bernoulli null
across {1,4,16,64} shards (byte-identical to 5 sig figs); raw-interleave probe shows B's positions identical regardless
of sharding (mean gap 10.28 examples, max 75 = 0.29 batches — far too short to starve). The hypothesized A(shard-card) x
B(buffer-fill) coupling DOES NOT EXIST on the interleave_datasets->.shuffle path.

WHY THIS IS THE SYSTEM AT ITS BEST: a GREEN-ELIGIBLE candidate that CLEARED the screening ceiling STILL died honestly at
the cheapest tier (L0) because the REAL MECHANISM (read from source) contradicted the premise. The screening got the
ALTITUDE right (it was a genuinely non-obvious coupling IF the mechanism held); the L0 caught that the mechanism didn't
hold. Zero false greens intact. No fake verdict, clean kill, $0 committee cost.

★ DISTILL-WORTHY LESSON (for orchestrator.md + scout briefings) — INTERLEAVE-VS-CONCATENATE / VERIFY-THE-COMPOSITION:
the claim conflated two streaming primitives. The seam (rare-source few-shards -> contiguous buffer burst -> starvation)
IS REAL for concatenate_datasets / a single multi-shard dataset read in shard order (the known shard-sensitive reservoir
limitation). It is FALSE for interleave_datasets(probabilities=p), whose per-example Categorical cycling sits UPSTREAM of
the buffer and de-correlates the rare source's arrival regardless of sharding. GENERAL LESSON: when a cross-area coupling
claim depends on the COMPOSITION ORDER of two library primitives (here cycler-then-buffer), the screening scout MUST
VERIFY THE ACTUAL COMPOSITION IN THE INSTALLED SOURCE at design time — not assume the intuitive data-flow. A
"non-obvious coupling" that clears the incremental-composition test can still be PREMISE-FALSE if the real library wiring
decouples the two endpoints. The could-it-fail control (does interleave already spread the rare source?) caught it cheaply
at L0 — pre-register that exact control for any "primitive-A-composed-with-primitive-B" claim. (Revival route, NOT pursued:
the concatenate/single-dataset-no-interleave path WOULD show the effect — but that's the known reservoir limitation, not a
new coupling -> would YELLOW on mechanism-known anyway.)

NEXT: now 0/2 investing (CLAIM-0065 was the only live project). See HOLD/RESCOUT decision in the next orchestrator note.
