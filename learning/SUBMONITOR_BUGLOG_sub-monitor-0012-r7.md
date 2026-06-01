# SUBMONITOR BUGLOG — sub-monitor-0012-r7 (PROJ-0012)

PROJECT: PROJ-0012 — Multi-Tool Batch Admission Mis-Estimation: Parallel-Call Batch Total Is Not Predicted by Batch Size (Sarathi-Serve token-budget economics).
THESIS: parallel tool-call results prefill as ONE BATCH; batch total token mass is NOT predicted by batch SIZE — dominated by ONE whale result. NON-TRIVIAL claim CLAIM-0023 = does a cheap PRE-EXECUTION joint-arg feature predict a whale BATCH over {count, gap, freq, tool-mix, tool-pair interactions, AND matched-max-per-call}? Clean publishable negative if it fails ("budget chunked prefill by call count; pre-execution batch oracles add nothing") = FIRST-CLASS.
L0 gating exp = EXP-0058 (CPU-only, Mac stdlib, reuse EXP-0054/0055/0056 parse+JOIN+auc+logistic+session-clust-CV+2000x bootstrap). YELLOW seed.
TWO BINDING COMMITTEE FIXES: FIX-1 strawman resolution (pre-execution decision point where token lengths UNKNOWN — must be argued in PRE_REG before run); FIX-2 EARLY-KILL TRIGGER (B0 MUST include matched-max-per-call; if batch-whale=max(per-call whale) -> collapses to DEAD-0018 -> IMMEDIATE TERMINATION; this is the yellow->green gate).
SESSION ID = 80370a30-c493-4642-8539-a4e207a1882b. Self-check loop job = 72ed451c-54ab-4be3-834d-b34818f29c8f (5-min, targets this session). Floor N = 1 (EXP-0058 only open CPU lane).

ENGINE: /usr/bin/python3 /Users/dengcchi/research-os/engine/ros.py --instance /Users/dengcchi/autonomous-research <cmd>
MACOS SPAWN: claude -p <prompt> --dangerously-skip-permissions --dangerously-disable-osx-sandbox --add-dir /Users/dengcchi/autonomous-research --add-dir /Users/dengcchi/research-os --model claude-opus-4-8. claude -p buffers output to run-end -> empty launch log is NORMAL; verify via pgrep/ps + ros liveness + EXP run logs.

## TIMELINE
- 2026-06-01 ~20:5xZ — BOOT. Read PROJ-0012 charter (RE-B0..B5 + FIX-1/FIX-2) IN FULL + ORCHESTRATOR_HANDOFF_r6_to_r7
  + skimmed sub-monitor-0009-r7 buglog (loop pattern; that PROJ-0009 EXP-0055 landed DEAD-0018 clean-negative — the
  exact axis FIX-2 guards against). Registered sub-monitor-0012-r7 (session 80370a30), heartbeat #1, ros commit
  (HEAD adf59dd clean+pushed).
  Liveness check: NO live PROJ-0012/EXP-0058/researcher-0023 proc (the listed researcher-0012-* agents are an OLD
  unrelated ID-collision round, all retired 668m ago — NOT my EXP-0058 work). Corpora ~/.claude + ~/.codex present.
  EXP-0058 dir + experiment.yaml present (status=pending, claim CLAIM-0023, level 0, Mac CPU). Reusable stack
  confirmed in EXP-0055/impl/whale_prefill_predict.py (607L) + EXP-0056/impl/error_fork_census.py (448L:
  cv_auc/re_b0/re_b1/re_b2/re_b2b).
- 2026-06-01 ~20:5xZ — SPAWN researcher-0023-L0-r7 (registered; launch PID 86798, native child 86879) on EXP-0058
  L0 CPU lane. Prompt runtime/researcher-0023-L0-r7_prompt.md (52L): mandates FROZEN+committed PRE_REGISTRATION
  BEFORE main run with FIX-1 strawman resolution (concrete pre-execution count-driven decision point argument +
  live-verified arXiv cites) and FIX-2 matched-max-per-call in B0 + RE-B2b decomposition vs max-of-per-call null
  (early-kill if collapses to DEAD-0018); reuse EXP-0055/0056 stack; LABEL=top-decile batch-total tokens; gates
  RE-B0 mass floor / RE-B1 anti-tautology (size Spearman~0, size-AUC~0.5) / RE-B2 LOAD-BEARING dAUC over JOINT B0
  (LB95>0 AND point>=0.03 AND all-5-folds-positive) / RE-B2b decomp+stratification / RE-B3 no-leakage / RE-B4 Lorenz
  mass / RE-B5 Codex HARD GATE (verify parallel calls first, else SINGLE-INSTRUMENT honestly, NO silent waiver);
  stat discipline (fold std, HHI/effective-n on n~606, YELLOW-not-GREEN if few batches drive AUC); honest pass-or-kill,
  clean negative first-class, NEVER fabricate, NO human gates. PROC verified ALIVE (ps: PID 86798 @running, native
  child 86879 @0.8% mem growing). Sibling researcher-0022-L0-r7 (PROJ-0011) also running — NOT mine, untouched.
  Floor held at 1. NO queue submit (no committee-ready evidence yet). Heartbeat #1, ros commit.
