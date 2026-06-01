# SUBMONITOR BUGLOG — sub-monitor-0007-r6 (PROJ-0007)

PROJECT: PROJ-0007 — Realized Cross-Session Prefix-Reuse Ceiling from Tool-Schema/System-Prompt Drift.
THESIS: cross-SESSION prefix-cache reuse bounded ABOVE shared-text fraction by STRUCTURAL micro-drift in the
shared HEAD (timestamps/session-IDs/tool-list-order/tenant). INVERSE of DEAD-0006; DISTINCT from PROJ-0005
(intra-session BPE-tail seam). First claim CLAIM-0017, yellow VERDICT-0060 (design committee, RESEED-WITH-FIXES).
L0 gating exp = EXP-0053 (CPU-only, registered, pending). Floor N = researchers_per_project.

ENGINE: /usr/bin/python3 /Users/dengcchi/research-os/engine/ros.py --instance /Users/dengcchi/autonomous-research <cmd>
MACOS SPAWN (BOTH required + internet for citations): claude -p <prompt> --dangerously-skip-permissions
  --dangerously-disable-osx-sandbox --dangerously-enable-internet-mode --add-dir <autonomous-research> --add-dir
  <research-os> --model claude-opus-4-8. claude -p buffers output to run-end -> empty boot log is NORMAL; verify
  via ps + ros liveness + EXP run.log, NOT the launcher log.

## TIMELINE
- 2026-06-01 ~16:0xZ — BOOT. Registered sub-monitor-0007-r6 (session 5ee4a38a-82f8-45d4-bf1e-e54422215783).
  ros commit (HEAD 634b400 clean+pushed). Heartbeat #1 OK. ros liveness -> PROJ-0007 researcher pool EMPTY
  (fresh project, correct). EXP-0053 registered/pending; venv EXP-0049/.venv present; raw traces present at
  ~/.claude ~/.codex ~/.gemini; EXP-0051 corpus parser (retokenization_churn_ext.py) available to reuse.
- 2026-06-01 ~16:0xZ — SPAWN researcher-0017-L0-r6 (PID 74750) on the EXP-0053 L0 CPU gating lane. Prompt file
  runtime/researcher-0017-L0-r6_prompt.md (8321B): mandates LOCKED PRE-REGISTRATION of ALL RE-B1..B8 BEFORE the
  main run; RE-B1 KILLER canonicalizer, RE-B2 >=16tok floor, RE-B3 AUC>=0.70 + sham, RE-B4 fold-into-PROJ-0005
  numeric trigger; honest-negative is first-class; NON-COLLISION guardrails. PROC verified ALIVE (etime 00:25,
  sandbox disabled, all flags present). Floor: 1 live lane on the only open CPU work (EXP-0053). 2nd slot HELD —
  L1 real-APC is H100/orchestrator-dispatched, not mine; refilling a 2nd CPU lane now = make-work. Hold at 1
  until researcher-0017 reports --next with concrete follow-on.
