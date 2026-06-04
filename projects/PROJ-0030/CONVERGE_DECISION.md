# PROJ-0030 / CLAIM-0060 — ORCHESTRATOR CONVERGE DECISION (r7-001, 2026-06-04)

VERDICT-0061: committee#1 UNANIMOUS 6/6 YELLOW (no RED, no fatal). Honest, clean L0.

DECISION: CONVERGE (accept the honest yellow; do NOT advance to L1).

RATIONALE (per ORCHESTRATOR_CHARTER job #2 + brain lesson CLAIM-0054 "first clean quantification of a
known pathology -> weigh whether the heavy L1 is worth it vs converging the honest yellow"):
1. The committee unanimously tagged contribution_type = 'empirical_measurement_of_KNOWN_mechanism', NOT a
   new failure mode. The mechanism (cache-key over-specification) is pre-2020 systems folklore; SGLang ALREADY
   ships the fix; vLLM mm_uuid proves maintainers already know. Residual novelty = first clean cross-framework
   QUANTIFICATION of a known design-point mismatch. Modest ceiling.
2. The single decisive L1 gate is lossless-re-encode PREVALENCE in real VLM-serving/agent-RAG traffic from a
   NAMED production source. We do NOT have access to such a trace; obtaining it is not a cheap CPU follow-up
   (unlike CLAIM-0061's decisive test). Without it the 100pp gap is "mechanically correct but operationally
   unknown." product_realist notes dominant CDN traffic is LOSSY (the zero-gap arm).
3. PRIOR_ART_ADEQUATE:no (novelty_killer's live web-search was denied) — a heavy L1 would ALSO have to redo a
   proper literature search just to clear the prior-art negative on a known mechanism. Low expected value.
4. LIGHTWEIGHT posture: ONE sharp claim per fresh area; if it dies/yellows honestly, converge and move to a
   fresh area rather than pour a heavy, data-gated L1 into a known-mechanism quantification.

THE VALIDATED CONTRIBUTION (recorded honestly): a verbatim-transcribed, pixel-identity-verified (max_abs_diff==0)
cross-framework hash-domain divergence — vLLM keys VLM vision-encoder cache reuse on transport bytes while SGLang
keys on processed pixel_values; genuine lossless re-encodes -> vLLM 0% / SGLang 100% hit (100pp), with an honest
lossy null-exit (both correctly miss when pixels change). The honest negative/quantification IS the output.
Zero false greens maintained.

NEXT: refill the freed slot with a NEW fresh-area project under EXPAND/LIGHTWEIGHT (cross-area production-seam shape).
