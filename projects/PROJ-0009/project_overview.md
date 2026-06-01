# PROJ-0009 — Prefill-Cost Heavy-Tail Pre-Execution Prediction (Chunked-Prefill Admission)

Seeded: 2026-06-01 by orchestrator-r7-001 (design committee proj0910_design, 6/6 ALL_COMMITTEE_DONE).
Verdict: YELLOW / seed-with-mandatory-fixes (FINAL_VERDICT A=yellow). First claim: CLAIM-0020.

## THESIS
Tool-result prefill cost in agent serving is extreme heavy-tail (live CC: top 10% of calls carry 78.9% of
all result-prefill tokens, top 1% carry 39.4%). Structural cause: result length is set by execution/
filesystem state, not by call position/cadence, so a FIFO chunked-prefill scheduler (vLLM chunked prefill /
Sarathi-Serve / SGLang) suffers head-of-line blocking from a predictable minority. NON-TRIVIAL claim is
WITHIN-tool: can a cheap PRE-EXECUTION feature of the arguments predict which call OF A GIVEN TOOL will be a
prefill whale — enabling a fast/slow-path admission split BEFORE the tool runs.

## FIRST CLAIM (CLAIM-0020)
Within >=1 high-volume tool class, a static pre-execution arg-structure feature set predicts top-decile
result length OVER AND ABOVE the joint baseline (RE-1-over-joint-baseline pattern). Clean publishable
negative if it fails: within-tool prefill cost is NOT pre-predictable; schedulers can only bucket by tool name.

## PRE-REGISTERED RE GATES (with committee MANDATORY FIXES baked in)
- RE-A0 (magnitude floor): top-decile result-prefill share >=50% (live 78.9%). Floor gate, NOT load-bearing.
- RE-A1 (LOAD-BEARING KILLER, over JOINT baseline): label = result in top decile of token length.
  B0 = {log1p(gap), log1p(freq), TOOL one-hot, **ARG-TEMPLATE feature** (first word/AST token of args_str
  one-hot OR arg-template hash) [FIX-1, UPGRADE GATE]}. B1 = B0 + arg-structure features. PASS iff
  dAUC_LB95 > 0 AND **dAUC_point >= 0.03** [stat fix]. If B1 dAUC<=0 vs the arg-template-tightened B0 ->
  thesis falsified as sub-tool identity recovery -> clean negative.
- RE-A2 (no-leakage): features from args_str ONLY (pre-execution); result text never in X. By construction.
- RE-A3 (cross-instrument, HARD GATE): Codex replication — sign agreement REQUIRED for PASS [FIX].
- RE-A4 (heavy-tail mass gate) [FIX-2]: secondary gate — Spearman rank corr (predicted score vs result-token
  count, session-clustered bootstrap) OR Lorenz/Gini lift (fraction of total prefill MASS captured in top-k
  predictions vs B0). AUC on a thresholded label discards the heavy-tail structure the thesis depends on.
- RE-A5 (within-session permutation control) [FIX-3]: permute glob-breadth/path-depth features within session
  to rule out session-level project-size confound that 5-fold session-clustered CV does not address.
- STAT DISCIPLINE: report fold-to-fold dAUC std across 5 folds, require ALL 5 folds positive (sign-stability);
  report Herfindahl index of positive-class mass — if >0.2, flag AUC dominated by 2-3 sessions.
- PRE-REG: add OSS prior-art section citing specific vLLM/SGLang mechanisms + stated non-overlap; live
  arXiv-ID re-verification (S3 / TetriInfer / SSJF lineage) before pre-registration claims authority.

## NOVELTY / NON-COLLISION (committee-checked)
Predicting external tool-RESULT length from pre-execution ARGUMENT structure is mechanistically distinct from
the output-length-prediction lineage (S3/TetriInfer/SSJF predict MODEL-generated length from prompts) —
novelty_killer GREEN, unchallenged. vLLM chunked prefill / Sarathi chunk AFTER tokens exist; no shipping
mechanism predicts result-prefill whales from args before execution. Not DEAD-0010 (idle speculative prefill),
not DEAD-0016/PROJ-0008 (byte-identical interior repeats — A is novel-result LENGTH), not PROJ-0005 (BPE seam),
not PROJ-0002 (edit->recompute). No decode-time SD.

## L0 GATING EXPERIMENT
EXP (CPU, Mac stdlib, reuse EXP-0054 parse+JOIN + auc/logistic_fit/session-clustered-CV/2000x bootstrap).
~2300 rows logistic, <10s. YELLOW->GREEN upgrade contingent on ALL fixes incorporated into pre-registration
BEFORE L0 entry (the fixes change B0 composition + gate criteria).
