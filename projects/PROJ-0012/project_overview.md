# PROJ-0012 — Multi-Tool Batch Admission Mis-Estimation: Parallel-Call Batch Total Is Not Predicted by Batch Size

Seeded: 2026-06-01 by orchestrator-r7-001 (design committee proj0011_design, 6/6 ALL_COMMITTEE_DONE).
Verdict: YELLOW / seed-with-mandatory-fixes (FINAL_VERDICT B=yellow; 1 green + 3 yellow + 1 red). First claim: CLAIM-0023.
Strongest NOVELTY signal of the 3 candidates (novelty_killer GREEN, uncrowded), BUT carries a BINDING DESIGN-PHASE GATE
(strawman resolution, systems_reviewer RED) + a DEAD-0018-re-skin EARLY-KILL TRIGGER (theory_skeptic) — see fixes 1+2.

## THESIS
Modern agents (Claude, Codex) emit multiple tool calls in a single assistant turn (parallel tool use); their results
arrive together and must be prefilled as one BATCH hitting a chunked-prefill scheduler simultaneously. On the live CC
corpus 50% of tool-call bursts are multi-call (mean 2.94, max 26), and the batch token-total is NOT predicted by batch
SIZE — median batch-total is ~flat across sizes 2-7 (278/177/162/170/203 tok) with within-size CV 3.3-3.9, size-total
Spearman ~0, size-only whale-AUC ~0.5, and the top-10% of batches carry 75.7% of all batched-prefill mass. The
structural cause: batch total is dominated by ONE whale result among the parallel calls, not by call count. NON-TRIVIAL
claim: does a cheap PRE-EXECUTION feature of the batch's joint ARGUMENT structure predict a whale BATCH over and above
{count, gap, freq, tool-mix, AND matched-max-per-call} — i.e. beyond both the count confound and the DEAD-0018
per-call-whale carry-over.

## FIRST CLAIM (CLAIM-0023)
Within multi-tool batches, a static pre-execution joint-argument feature set predicts batch-total prefill whales over
and above {count, gap, freq, tool-mix, matched-max-per-call} — so a batch-admission decision should pre-size by
predicted token mass, not call count, AT A DECISION POINT WHERE TOKEN LENGTHS ARE NOT YET KNOWN. Clean publishable
negative if it fails: batch total is execution-state noise given count+mix+max-per-call -> budget by count -> "do not
build pre-execution batch-cost oracles." EARLY-KILL: if batch-whale = max(independent per-call whales), the claim
collapses to DEAD-0018 (killed) and is terminated immediately.

## BINDING DESIGN-PHASE GATES (must pass BEFORE L0 execution begins)
- MANDATORY FIX 1 — STRAWMAN RESOLUTION (systems_reviewer RED, unrebutted): shipping vLLM exposes max_num_batched_tokens
  (token-level budget) and Sarathi-Serve chunks by tokens AFTER payloads exist. Before L0, produce EVIDENCE (scheduler
  code trace or doc) that a real admission/dispatch decision uses call COUNT (not known token lengths) at a
  PRE-EXECUTION decision point (before tool results return). If the only such point is orchestrator-side batch DISPATCH
  sizing, REFRAME the mechanism to that explicitly. If no count-driven pre-execution decision point exists, the project
  is REFRAMED-OR-KILLED at design — do NOT proceed to L0 on a strawman.
- MANDATORY FIX 4 — VERIFY CODEX PARALLEL CALLS BEFORE SEEDING-PROCEED (not WAIVED-WITH-FLAG): the cross-instrument
  HARD GATE requires a real Codex replication set. Confirm Codex emits parallel calls (call_id/message co-occurrence);
  if it does not, declare the project SINGLE-INSTRUMENT by design honestly — the WAIVED-WITH-FLAG escape is unacceptable.

## PRE-REGISTERED RE GATES (committee MANDATORY FIXES baked in)
- RE-B0 (magnitude floor): multi-call bursts >=25% AND top-decile batches carry >=50% of batched-prefill mass (live 50%
  / 75.7%). If batches small/uniform -> clean kill.
- RE-B1 (count-insufficiency anti-tautology): batch SIZE alone has Spearman with batch-total below threshold (live ~0)
  AND size-only whale-AUC ~0.5+eps. Establishes budget-by-count genuinely fails.
- RE-B2 (LOAD-BEARING KILLER, over JOINT baseline): unit = each multi-call batch. Label = batch total in top decile of
  batch-total tokens. B0 = {log1p(batch-size), log1p(mean-gap), log1p(mean-freq), tool-mix one-hot, **tool-pair/triple
  interaction terms** [FIX-3], **matched-max-per-call** [FIX-2]}. B1 = B0 + joint pre-execution arg-structure (max/sum
  over the batch's calls of: has-numeric-limit, glob/wildcard count, path-depth, Bash head/tail/redirect flags,
  arg-token-count). PASS iff dAUC_LB95>0 AND dAUC_point>=0.03 AND all-5-folds-positive. If <=0 -> batch total
  unpredictable from args given count+mix+max-per-call -> clean negative.
- RE-B2b (matched-COUNT + DECOMPOSITION control, UPGRADE GATE + EARLY-KILL) [FIX-2]: (a) within each batch-size stratum
  arg-structure still separates whale vs non-whale (per-stratum AUC); AND (b) pre-registered DECOMPOSITION TEST — the
  joint-arg features must BEAT the null "batch whale = max of independently-distributed per-call whales". If batch-whale
  reduces to max(per-call whale) -> collapses to DEAD-0018 -> IMMEDIATE TERMINATION. THE yellow->green gate + early-kill.
- RE-B3 (no-leakage): all features from args_str ONLY (pre-execution); no result text in X. By construction.
- RE-B4 (heavy-tail mass gate): Lorenz/Gini lift — fraction of total batched-prefill MASS captured in top-k predicted
  batches vs B0.
- RE-B5 (cross-instrument, HARD GATE): Codex replication — dAUC sign agreement REQUIRED (see FIX 4; no silent waiver).
- STAT DISCIPLINE [FIX-5]: fold-to-fold dAUC std, ALL 5 folds positive, **Herfindahl/effective-n** after
  session-clustering AND size-stratification on n~606 batches (the binding sample-size risk) — flag YELLOW not GREEN if
  a handful of batches drive the AUC.

## NOVELTY / NON-COLLISION (committee-checked; novelty_killer GREEN — uncrowded)
Relevance-ranked arXiv sweep returned NO prior art on count-vs-total batch-admission mis-estimation for parallel tool
calls. MANDATORY FIX 6 — cite + disclaim overlap axis: DynaServe 2504.09285 (general length heterogeneity, not the
count!=total claim), Sutradhara 2601.12967 (tool-exec/prefill overlap axis), plus the output/input-length-prediction-
for-scheduling line (S3/TetriInfer/SSJF — MODEL-generated length, not tool-result batch mass). Sarathi-Serve 2403.02310
/ vLLM chunked prefill chunk AFTER tokens exist. DISTINCT FROM PROJ-0009/DEAD-0018 (that was a per-call WITHIN-TOOL
whale, no count confound; B is a BATCH-level whale across a MULTI-tool co-issued turn with batch-SIZE as explicit B0
confound + matched-max-per-call decomposition guard). NOT the LLMCompiler 2312.04511 / Parrot 2405.19888 / Teola /
Autellix dependency-graph parallelism axis (makes NO parallelization/dataflow claim — budget mis-prediction of an
ALREADY-co-issued batch). Cemetery: not DEAD-0010 (idle prefill — B schedules REAL batched prefill), not DEAD-0016
(byte-identical repeats). No decode-SD.

## L0 GATING EXPERIMENT (EXP-0058)
CPU, Mac stdlib, reuse EXP-0054 parse+JOIN + auc/logistic_fit/session-clustered-CV/2000x bootstrap. Detect parallel-
call batches via stream-offset adjacency (gap<5 tok) for CC and call_id/message co-occurrence for Codex (FIX 4 verify
first). Per batch emit (size, mean_gap, mean_freq, tool_mix, tool_pair_interactions, max_per_call, joint_arg_features,
batch_total_tok, whale_label); fit B0 vs B1 session-clustered CV; bootstrap dAUC; matched-count + decomposition control;
Lorenz mass lift. ~606 CC batch rows + Codex, <10s. YELLOW->GREEN contingent on (i) FIX-1 strawman resolved at design,
(ii) ALL fixes in pre-registration BEFORE L0, (iii) RE-B2b decomposition NOT collapsing to DEAD-0018.
