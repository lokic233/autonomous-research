# SUBMONITOR BUGLOG — sub-monitor-0009-r7 (PROJ-0009)

PROJECT: PROJ-0009 — Prefill-Cost Heavy-Tail Pre-Execution Prediction (Chunked-Prefill Admission).
THESIS: tool-RESULT prefill cost is extreme heavy-tail; NON-TRIVIAL claim = WITHIN a high-volume tool class, a
cheap PRE-EXECUTION arg-structure feature predicts result-prefill whales OVER the arg-template-tightened joint
baseline (RE-1-over-joint-baseline). Clean publishable negative if it fails. First claim CLAIM-0020, yellow seed.
L0 gating exp = EXP-0055 (CPU-only, Mac stdlib, reuse EXP-0054 parse+JOIN+auc+logistic+session-clust-CV+2000x bootstrap).
SESSION ID = 124ec26e-8bd1-4e56-b94c-686406c93850. Self-check job = 3b3ee10c. Floor N = 1 (EXP-0055 only open CPU lane).

ENGINE: /usr/bin/python3 /Users/dengcchi/research-os/engine/ros.py --instance /Users/dengcchi/autonomous-research <cmd>
MACOS SPAWN: claude -p <prompt> --dangerously-skip-permissions --dangerously-disable-osx-sandbox
  --add-dir /Users/dengcchi/autonomous-research --add-dir /Users/dengcchi/research-os --model claude-opus-4-8.
  claude -p buffers output to run-end -> empty launch log is NORMAL; verify via pgrep + ros liveness + EXP run logs.

## TIMELINE
- 2026-06-01 ~19:1xZ — BOOT. Read PROJ-0009 charter (RE-A0..A5 gates) + ORCHESTRATOR_HANDOFF_r6_to_r7 + skimmed
  sub-monitor-0007-r6 buglog (loop pattern). Registered sub-monitor-0009-r7 (session 124ec26e), heartbeat #1,
  ros commit (HEAD b3679b6 clean+pushed). Confirmed via handoff this IS the session r7 spawned (job 3b3ee10c).
  Liveness: PROJ-0009 researcher pool EMPTY (correct, fresh); sibling researcher-0021-L0-r7 (PROJ-0010) running;
  sub-monitor-0010-r7 alive. EXP-0055 dir + experiment.yaml present (status pending). EXP-0054 reusable stack
  verified: parse_cc/codex JOIN (args_str carried), auc, logistic_fit, cv_scores (session-clust 5-fold,
  det_hash%5), re_a1 (dAUC + 2000x session-clust bootstrap), det_hash. Raw corpora ~/.claude + ~/.codex present.
- 2026-06-01 ~19:1xZ — SPAWN researcher-0020-L0-r7 (PID 6575) on EXP-0055 L0 CPU lane. Prompt file
  runtime/researcher-0020-L0-r7_prompt.md (8082B): mandates FROZEN PRE_REGISTRATION before main run; reuse
  EXP-0054 stack; LABEL=top-decile result token length; B0=arg-template-tightened JOINT (FIX-1 upgrade gate);
  B1=B0+arg-structure; gates RE-A0 mass floor / RE-A1 LOAD-BEARING dAUC_LB95>0 AND dAUC_point>=0.03 over
  arg-template B0 / RE-A2 no-leakage / RE-A3 Codex sign-agreement HARD / RE-A4 Spearman-or-Gini mass / RE-A5
  within-session permutation; ALL-5-folds-positive + HHI flag; honest pass-or-kill, clean negative first-class,
  NEVER fabricate. PROC verified ALIVE (pgrep, all flags present). Floor held at 1 (L1+ = orchestrator-dispatched).
  NO queue submit yet (no committee-ready evidence). Heartbeat #1, ros commit.
