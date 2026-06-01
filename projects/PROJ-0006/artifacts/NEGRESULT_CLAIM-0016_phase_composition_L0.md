# NEGATIVE RESULT — Agent-Event Phase Does Not Help Batch-SD Composition (CLAIM-0016, L0)
# PROJ-0006 | EXP-0052 | researcher-0016-L0-r6 | 2026-06-01 | prompt v001
# Status: CLEAN KILL at L0 (both corpora). Pre-registration LOCKED 2026-06-01T16:07:18Z.

## Claim tested
In batch speculative decoding the round is bottlenecked to the MIN accepted-length across co-batched
sequences (ragged-tensor tax). CLAIM-0016: a phase-aligned BATCH-COMPOSITION policy (co-batch sessions of
similar predicted AGENT-EVENT PHASE: mid-tool-injection TRANSITION / formulaic RESUMPTION / FREE-FORM
reasoning) recovers this min-bound tax over a static per-task difficulty grouping baseline, at zero accuracy
change (SD exact). Phase = grouping mechanism only (NOT a standalone discriminator; cf. DEAD-0011/0012).

## Result: FALSIFIED (both corpora, pre-registered killer RE-A1)
CPU Monte-Carlo batch-round min-bound model on the EXP-0046 top-1-agreement proxy (CC 99,434 rounds / Codex
29,495 rounds @ gamma=8; cluster-bootstrap by session B=2000):
- **RE-A1 delta1(phase - static-task-difficulty) = +0.00032 CC (95% CI [-0.00062,+0.00060]) / +0.00081 Codex
  (CI [-0.00173,+0.00158]); LB <= 0 both -> KILL.**
- RE-A2 (vs sham running-mean cluster): CI includes 0 both. RE-A4 permutation null NOT survived (p=0.15/1.0).
- RE-A5: 0/16 grid cells Holm-significant. RE-A3 ragged tax ~100% but DEGENERATE (min-bound floor collapse).
- RE-A6 overhead negligible (7.4e-8 s/round) but moot. RE-A7: DEAD-0011/0012 cited.
- EXPLORATORY resolvable-regime sweep (alpha 0.5->0.9, real magnitudes): phase ~0 over static in CC at every
  level; one fragile Codex cell (alpha=0.7) only -> kill is ROBUST, not a proxy-floor artifact.

## WHY (two structural, predictor-independent reasons)
1. **~97.5% of decoded tokens on real agentic trajectories are FREE-FORM reasoning** (TRANSITION+RESUMPTION
   < 3% combined) -> phase grouping puts nearly everything in one bucket; almost no grouping leverage.
2. **Between-session difficulty variance >> within-trajectory phase variance** (session-mean-acc std
   0.104 CC / 0.088 Codex vs per-phase deviation -0.07..+0.14) -> a static per-task difficulty model already
   captures the recoverable ragged-min-bound variance; phase adds nothing on top.

## Actionable takeaway for serving teams
For batch-SD composition, group by per-task/per-session DIFFICULTY (or current length, cf. Batch-SD-Done-Right
EXSpec 2510.22876), NOT by agent-event phase. Dynamic agent-event-phase tracking is not worth its complexity.

## Revival condition
A real neural SD draft/target pair (L1: vLLM/TGI/SGLang accepted-length telemetry on H100) showing
phase-composition goodput over a static per-task-difficulty grouping baseline with 95% LB > 0 AND a
non-degenerate ragged tax — i.e. cross-sequence phase signal the trigram proxy structurally cannot detect AND
that is not already captured by difficulty/length grouping. Absent that, the phase-composition lever stays dead.

## Provenance
experiments/2026-06-01/EXP-0052/impl/{preregistration.md, batch_round_model.py};
results/{batch_round_model.json, exp_regime_sweep.json, analysis.md}; prior_art/PROJ-0006/.
