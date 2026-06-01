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

- 2026-06-01 ~16:1xZ — CYCLE (heartbeat #3). researcher-0017-L0-r6 ALIVE (PID 74750, etime 08:40, running,
  last=7.4m). HEALTHY + ON-TRACK, NOT a stall. Progress verified:
    * Boot report: parsed 3 distinct template families — CC=248, Codex=109, Gemini=84 trace files
      (RE-B6 >=2-family gate satisfiable; Gemini flagged as degenerate/low-drift control, not counted).
    * PRE_REGISTRATION.md (11279B) WRITTEN + LOCKED + COMMITTED BEFORE the main run (commit b83fb0c,
      locked-ts 2026-06-01T16:09:03Z) — exactly the pre-registration discipline VERDICT-0060 demands.
    * Gates frozen & verified: RE-B1 KILLER (PASS iff shortfall_after mean>=16tok AND CI_lo>=16tok; KILL if
      collapses to quantization floor), RE-B2 (>=16tok drift-attributable, CI_lo>=16), RE-B3 (AUC>=0.70 AND
      real>sham), RE-B4 fold-trigger X=50% (majority BPE-seam -> fold into PROJ-0005). Overall kill rule +
      honest-negative-is-first-class language present. Design grounded in observed truth (Codex
      base_instructions byte-identical /109; available_skills 109 distinct hashes = dynamic-list drift).
    * No results/ yet (main run not started) — expected; harness build is next per --next.
  DECISION: NO action needed — researcher on-task, gates correct. NO queue submit yet (no committee-ready
  evidence: main run not run, RE-B1/B2/B3 not yet resolved). Floor held at 1 (EXP-0053 only open CPU lane;
  L1 real-APC = H100/orchestrator). Refill only on concrete --next follow-on. Heartbeat #3, commit.

- 2026-06-01 ~16:1xZ — CYCLE (heartbeat #4). researcher-0017-L0-r6 ALIVE (PID 74750, etime 13:23, running,
  last=4.4m). HEALTHY + ON-TRACK. Progress since last cycle (report #2 @16:11:39Z):
    * Harness BUILT: impl/xsession_prefix_ceiling.py (22180B) — head reconstruction (Codex/CC/Gemini) ->
      block-LCP -> canonicalizer -> drift-free control -> drift-class predictor+sham -> bootstrap. stdlib.
    * Ground-truth crux NAMED correctly: "is skill-list drift REORDER (canonicalizer fixes -> KILL) or
      MEMBERSHIP (survives canon -> PASS)" = exactly the RE-B1 KILLER decision. CC envelope drift catalogued
      (19 cwd / 7 ver / 2 branch).
    * --next: "Run EXP-0053 main; gather RE-B7/B8 prior art." Main run imminent.
    * results/ still empty (main not yet run) — expected.
  DECISION: NO action — on-task, gates already locked (b83fb0c), harness built. NO queue submit (RE-B1/B2/B3
  not yet resolved; no committee-ready evidence). Floor held at 1. Heartbeat #4, commit.
