# PROJ-0006 — Agent-Event-Phase Desynchronization Tax in Batch Speculative Decoding

**Created:** 2026-06-01 by orchestrator-r6-001 (design committee proj0607_design, 5/5 yellow RESEED-WITH-FIXES; charter Candidate A).
**Layer:** decode-time batch-SD verification goodput (distinct from PROJ-0004 single-sequence acceptance penalty).
**First claim:** CLAIM-0016.

## THESIS
In batch speculative decoding, co-batched sequences accept different numbers of draft tokens per round (the
"ragged tensor" problem); the round is bottlenecked to the MINIMUM accepted length. On real agentic trajectories
this ragged variance is driven by AGENT-EVENT PHASE (mid-tool-result-injection low-acceptance transition vs
formulaic high-acceptance resumption vs free-form reasoning), and a phase-aligned BATCH-COMPOSITION policy
(group sessions of similar predicted acceptance-phase into the same SD micro-batch) reduces the min-bound ragged
tax at ZERO accuracy change (SD exact). CONTRIBUTION RESTS ON COMPOSITION (leg a) + RECOVERY (leg c) — the phase
predictor is the GROUPING MECHANISM, NOT a standalone dAUC novelty claim.

## NON-COLLISION
- vs PROJ-0004 (DEAD-0011/0012): single-SEQUENCE position/format acceptance penalty. PROJ-0006 is CROSS-sequence
  batch-COMPOSITION. The SAME agent-phase-over-{running-mean-acceptance+entropy+position} dAUC discriminator was
  FALSIFIED TWICE on the SAME EXP-0046 proxy (DEAD-0011; DEAD-0012 dAUC -0.090 CC / -0.322 Codex sig-neg). LEG (b)
  is restructured to NOT re-run that dead standalone discriminator; the predictor only forms batch groups.
- vs TETRIS/ACL2025 (in-batch token SELECTION), ECHO 2604.09603 (per-request concurrency gate), Batch-SD-Done-Right
  2510.22876 (ragged-tensor CORRECTNESS). Composition lever is the unoccupied delta. (Body-verify TETRIS arXiv id +
  Semi-Clairvoyant 2505.17074 / BASS-class before any PROMOTION — owed, NOT a seeding blocker.)

## L0 GATING EXP (CPU-only, Monte-Carlo batch-round model on EXP-0046 acceptance proxy + parsed CC/Codex corpora)
Pre-register ALL of these RE gates BEFORE the run (locked timestamp), decision rules exact:
- RE-A1 LOAD-BEARING: phase-aligned batch composition raises mean accepted-length-per-round (recovers ragged tax)
  OVER the STATIC-TASK-TYPE GROUPING SCHEDULER baseline (co-batch by historical per-task-type mean acceptance, no
  dynamic phase) — 95% LB>0 on goodput delta. (evaluation_prosecutor killer experiment.)
- RE-A2 SHAM-CLUSTER CONTROL: cluster on running-mean-acceptance feature ALONE (no phase label) — phase must beat
  this to isolate phase-attributable variance from generic difficulty-clustering Jensen gains.
- RE-A3 leg (a) PRE-REGISTERED MINIMUM TAX MAGNITUDE: the min<max ragged tax must clear an operational floor
  (>=5% mean-round-throughput penalty) at the tested B — else leg (a) is a foregone conclusion (min<max trivially).
- RE-A4 WITHIN-SESSION WITHIN-POSITION-BUCKET permutation null (absorb position x phase autocorrelation).
- RE-A5 MULTIPLICITY CORRECTION across (B values x draft lengths x corpora x tokenizers) (Holm/BH).
- RE-A6 SCHEDULER OVERHEAD: phase-tracking + grouping compute must be < the ragged tax it saves (net goodput >0).
- RE-A7 CITE DEAD-0011 + DEAD-0012 in prior_art (the same-discriminator same-proxy prior kills).
KILL if RE-A1 (composition over static-task grouping) fails CI>0 OR RE-A3 tax floor not met.
INSTRUMENTS: EXP-0046 acceptance_proxy.json + parsed CC/Codex/Gemini traces; Mac CPU stdlib-only. NO GPU for L0.
L1 (optional, later, orchestrator-dispatched): real vLLM/TGI/SGLang batch-SD accepted-length telemetry on H100.

## HONEST KILL PATHWAY
If phase-aligned composition shows no goodput over static-task clustering (RE-A1 fail) -> clean publishable negative:
"agent-event phase adds nothing over per-task difficulty clustering for batch-SD composition; use difficulty models,
not phase." Actionable either way.
