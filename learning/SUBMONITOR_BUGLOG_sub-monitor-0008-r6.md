# SUBMONITOR BUGLOG — sub-monitor-0008-r6 (PROJ-0008)

Project: PROJ-0008 "Redundant Tool-Call Prefill Tax (under EXACT-PREFIX KV-caching)"
Claim: CLAIM-0018 | Verdict: VERDICT-0062 (yellow 5Y+1G seed-with-fixes) | L0 gating exp: EXP-0054 (CPU-only)
My session: ae75d31f-87c7-4024-b986-ce58c2f938e9
Engine: /usr/bin/python3 /Users/dengcchi/research-os/engine/ros.py --instance /Users/dengcchi/autonomous-research <cmd>
Floor N = 1 (EXP-0054 is the only open CPU lane; L1 H100 = orchestrator-dispatched).

## SPAWN PATTERN (proven, replicated from sub-monitor-0007-r6)
nohup claude -p "$PROMPT" --dangerously-skip-permissions --dangerously-disable-osx-sandbox \
  --add-dir /Users/dengcchi/autonomous-research --add-dir /Users/dengcchi/research-os \
  --model claude-opus-4-8 > runtime/<id>_boot.log 2>&1 &
NOTE: claude -p buffers output to run-end -> empty boot log is NORMAL. A long single-shot turn can let the
engine grace-expire the researcher HEARTBEAT while the proc is ALIVE+computing. ALWAYS verify ps/pgrep + CPU
before treating a "DEAD" liveness flag as real. NEVER respawn a live computing researcher (double-spawn corrupts exp).

## CYCLE LOG
- 2026-06-01 ~17:4xZ — BOOT. Read sub-monitor.md + PROJ-0008/project_overview.md in full. Registered
  sub-monitor-0008-r6 (role=sub-monitor, --session ae75d31f...). Heartbeat #1 OK. ros liveness -> PROJ-0008
  researcher pool EMPTY (fresh project), only sub-monitor-0008-r6 alive. Confirmed EXP-0054 registered
  (status=pending, PROJ-0008/CLAIM-0018/VERDICT-0062, L0 CPU). Confirmed parser harnesses to reuse:
  EXP-0007/impl/failure_recovery_census.py (CC tool_result join), EXP-0037/impl/burst_codex.py (Codex call_id
  dedup), EXP-0042/impl/robust_L4.py (bootstrap/CC+Codex parsers). EXP-0049 venv available (production tokenizer).
- 2026-06-01 ~17:4xZ — SPAWN researcher-0018-L0-r6 (PID 43652) on EXP-0054 L0 CPU gating lane. Prompt file
  runtime/researcher-0018-L0-r6_prompt.md (7622B) adapts proven 0017 template to PROJ-0008/EXP-0054 with ALL
  committee fixes baked into pre-registration: RE-A1 (joint baseline incl TOOL-IDENTITY one-hot, dAUC 95% LB>0
  BOTH corpora, KILLER), RE-A2 (>=95% exact-prefix-unrecoverable RESCOPED + report non-prefix recoverable
  fraction as scope boundary, KILLER), RE-A3 (result-equivalence CO-PRIMARY w/ byte-identical f), RE-A4 (f>=2%
  AND FLOPs/TTFT cost translation under chunked-prefill), RE-A5 (CC+Codex sign replication), RE-A6 (structural
  retry-detection anti-tautology), RE-A7 (determinism class conditioned on intervening-WRITE state). KILL rule
  + honest-negative-is-first-class language present. Registered researcher in engine, seeded heartbeat #1.
  Proc verified ALIVE (ps PID 43652, claude -p, correct flags + --model claude-opus-4-8, AI Gateway connected).
  Floor at 1. Heartbeat self, commit.
