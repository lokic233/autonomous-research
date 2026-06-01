# PROJ-0004 — Tool-Boundary Acceptance Cliff in Speculative Decoding for Agent Trajectories

**Created:** 2026-06-01 (orchestrator-r4-001, capacity handoff from converged PROJ-0001)
**Charter source:** projects/PROJ-0004/CANDIDATE_CHARTERS.md (Candidate A), selected by honest 6-member
design committee (runtime/committee_run_proj4_design, ALL_COMMITTEE_DONE, 6/6 real votes, .err clean of
EMPTY_OUTPUT). Committee verdict: YELLOW / SEED-A-WITH-FIXES (novelty_killer GREEN, product_realist GREEN,
3 YELLOW, 0 RED on A; Candidate B -> RED [EpiCache/Continuum-occupied + length-identity risk = DEAD-0009/0010
pattern]; Candidate C -> RED-as-first-seed [AMD ROCm public guidance already states the prefill/decode HBM-BW
asymmetry; demote to possible companion claim after A resolves]).
**Topic bias satisfied:** inference-optimization / agentic-systems / LLM-serving (config new_project_topic_bias).
**Status:** L0-DESIGN (investing). occupied_territory = within-trajectory position-indexed draft-acceptance at
tool-result resumption boundaries (decode-time; NOT per-op fork-cost [PROJ-0001]; NOT invalidation cost-map
[PROJ-0002]; NOT failure attribution [PROJ-0003]).

## THESIS
On real agentic tool-calling trajectories, a speculative-decoding draft model's token-acceptance rate drops a
measurable, position-localized amount in the K decode steps immediately following each tool-result injection
(the resumption boundary), and this boundary penalty — not task cognitive domain, not generic content-type, not
local target-entropy — is a distinct within-trajectory driver of accepted-length variance.

## FIRST CLAIM (CLAIM-0013) — amended per committee fixes
Across >=2 agent-trace corpora and >=2 (target, draft) pairs, mean draft acceptance in the first K=8 decode
positions after a tool-result injection is below the trajectory baseline by a margin whose 95% CI excludes 0
AND which SURVIVES the committee's required controls:
  PASS requires the boundary penalty to remain CI>0 after:
  (1) content-type-matched null (splice identical tool-result text at NON-boundary positions; if acceptance
      drops equivalently -> content-type effect, not position -> FALSIFIED);
  (2) exceeding the generic non-tool context-shift penalty (user-turn / system-prompt / document boundary) with
      CI>0 on the difference;
  (3) conditioning on local target-model entropy/perplexity at the K=8 boundary tokens (must survive — else it's
      just "harder text is harder to speculate");
  (4) pre-registered K and minimum boundary-vs-domain superiority margin + multiple-comparison correction over
      positions 1..K (NO post-hoc window selection).
  FAIL = CI includes 0, OR boundary effect <= content-type/context-shift/entropy explanation, OR <= task-domain
  spread (2510.02128).

## COMMITTEE-MANDATED EVIDENCE / BASELINES (the 7 fixes; bake into the claim BEFORE L0 interpretation)
1. Content-type-matched null (HIGHEST PRIORITY cheap killer).
2. Non-tool context-shift baseline.
3. Target-model entropy reporting + conditioning.
4. Pre-register K + superiority margin + multiple-comparison correction.
5. SGLang EMA-adaptive SD baseline — show the cliff is NOT already absorbed by workload-adaptive step count
   (else "existing adaptive SD already handles this" -> kill).
6. EAGLE/EAGLE-2/Medusa acceptance baselines + task-domain partialling (2510.02128 as named null); boundary
   effect must survive after partialling out draft-model family AND task domain.
7. L1: real vLLM SD accepted-length telemetry (not only top-1 proxy), stratified by tool-result length/format/pair.

## PRIOR-ART (verified by novelty_killer against 4 sources)
- 2510.02128 "Disparate Impacts of SD" — task-axis divergence (NOT position/boundary). The named task-domain null.
- 2405.19715 SpecDec++ — whole-dataset OOD (not recurring intra-sequence spike).
- 2509.17396 EpiCache — occupies Candidate B's eviction axis (why B was RED).
- 2503.08311 "Mind the Memory Gap" — settles Candidate C's decode-bandwidth premise.
- UNVERIFIED (arxiv 429/503 at design time; MUST be fetched+verified before L0 results are interpreted, do NOT
  treat as confirmed non-collisions): 2601.11580, 2604.14682, 2604.13519, 2602.10238, 2604.25975, 2605.04178.
- Body-level must-cite: EAGLE / EAGLE-2 / Medusa / REST acceptance baselines.

## GATING EXPERIMENT (L0, CPU, cheap kill)
Teacher-forcing acceptance proxy (token "accepted" iff draft top-1 == target top-1) on the already-parsed
CC/Codex/Gemini agent-trace corpora; position-indexed acceptance vs distance-from-tool-boundary; bootstrap CI;
the 4 controls (content-type-matched null, non-tool context-shift, entropy conditioning, pre-registered K). Hours,
no GPU. KILL: a flat curve (or one that vanishes under any control) kills the thesis cheaply — and is itself
publishable (tells serving teams boundary-aware SD scheduling is NOT worth building; corroborates 2510.02128).
L1 (only after L0 passes fixes 1-4): H100 devgpu014 vLLM ngram/EAGLE SD real accepted-length telemetry, bounded
+ watchdogged (H100 safe; MI350X NOT required).

## WHY IT MATTERS (Meta)
Agentic serving (coding agents, tool-calling assistants) is where SD is deployed and where decode dominates cost.
A real boundary cliff -> a boundary-aware speculation policy (suppress/re-warm speculation for K steps post-
injection) recovers wasted verification FLOPs. A flat curve -> saves teams from building it. Serving-cost result
on a real Meta-shaped workload either way.
