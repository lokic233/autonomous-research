# DESIGN: Structural Anti-Sprawl — Single Multi-Lane Poller (replaces N self-spawning sub-monitors)

Author: monitor successor (bugbash #4), 2026-06-02. STATUS: PROPOSAL — needs dengcchi approval before
any loop is re-enabled. The system is currently FROZEN (all prompt-loops disabled) and must stay frozen
until this (or an approved variant) is built and signed off.

## THE PROBLEM (what dengcchi diagnosed)
18h of "productive idleness": 363 commits, ZERO new science. Root cause = AGENT SPRAWL. Each sub-monitor,
orchestrator, and GPU coordinator was an INDEPENDENT TOP-LEVEL Navi session with its OWN recurring
schedule job. At ~35% context each self-retired and spawned a SUCCESSOR session via
spawn_agent(new_session). With ~4-15 such loops running every 5-10 min, the fleet spent ALL its tokens on
self-maintenance: heartbeating, re-reading bloated buglogs, retire/respawn handoffs, false-DEAD rescues
(BUG-60), and the recurring "retired-no-successor" false-flag (BUG-41). sub-monitor-0015 churned r8->r36
(28 generations). 191 agents registered, 52 stuck status:running. The loops were a perpetual-motion
machine that produced commits but no evidence deltas.

WHY IT HAPPENED STRUCTURALLY: there is NO engine spawn primitive. Spawning is 100% prompt-driven via the
Navi spawn_agent tool. So "coverage" == "a prompt-loop is heartbeating", and the only way an agent could
persist past its context window was to spawn a fresh top-level session. N projects -> N+ independent
self-perpetuating sessions. Nothing bounded the generation count or the agent count.

## THE FIX: ONE poller session, MANY lanes (no per-lane sessions)
Replace the N self-spawning sub-monitor sessions with a SINGLE long-lived POLLER session (one schedule
job) that iterates ALL active project lanes each cycle. The orchestrator is the only other long-lived
session. That's 2 standing sessions total (poller + orchestrator) + ephemeral researcher procs — instead
of 4-15 self-replicating ones.

Concretely:
- A lane = one active project's monitoring duty (what a sub-monitor used to do): watch its researcher(s),
  forward committee-ready evidence to the queue, hold below floor when no open work. PURELY OBSERVE +
  FORWARD — never judge/verdict/seed/dispatch (those stay orchestrator authority; unchanged).
- The POLLER runs `ros lanes` once per cycle. The engine computes, for every active (non-converged)
  project, that lane's state + the SINGLE next action (if any). The poller executes only ACTIONABLE
  lanes; idle lanes are a no-op (no make-work, no commit churn). One heartbeat for the poller, not N.
- No lane ever spawns a session. Researchers are still spawned (ephemeral claude -p procs that EXIT when
  done — and now correctly auto-complete via BUG-60), but a LANE is just a loop iteration, not a session.
- When the poller itself approaches its context limit, IT does ONE handoff to a successor poller (like
  the orchestrator does today). That's ONE generational handoff for the whole fleet per ~context-window,
  not N independent ones. Generation growth is bounded to O(time), not O(time x projects).

## ENGINE SUPPORT BUILT THIS SESSION (the `ros lanes` command)
`ros lanes` (read-only by default) emits the per-lane work plan for the single poller:
  - enumerates active (non-converged) projects;
  - for each: the live researcher state (alive/completed/none), open committee-queue submissions, claim
    lifecycle (from `ros resume`), and the ONE next action keyword: HOLD | FORWARD | AWAIT | RESEED?.
  - HOLD   = below floor, no open work -> no-op (correct, not a gap).
  - FORWARD= a researcher finished candidate-grade evidence -> poller should `ros queue submit`.
  - AWAIT  = researcher running / committee pending -> just heartbeat.
  - RESEED?= researcher dead/gone WITH open work -> flag for orchestrator (NOT auto-respawn by the lane;
    the orchestrator owns reseed, via the existing reaper AGENT_DOWN/RESEED_NEEDED notification).
This collapses N `ros submonitors`/per-lane prompts into ONE deterministic plan the poller acts on.

## ANTI-SPRAWL INVARIANTS (enforced/owned)
1. EXACTLY 2 standing sessions: poller + orchestrator. (GPU coordinators can also fold into the poller as
   gpu-lanes, or stay 1 coord — TBD with dengcchi; either way bounded, not self-replicating.)
2. AUTO-OPEN A TASK ON SPAWN: whenever a researcher is spawned, the spawner opens a TASK (ros task open
   --assignee <researcher> --parent <poller-lane>) so every spawn is tracked + visible in `ros tree`.
   On EXP-terminal the researcher auto-completes (BUG-60) AND its task auto-closes (BUG-60b). No lingering
   researcher, no lingering task.
3. ORCHESTRATOR OWNS the incrementing task-id + the notification mechanism (already true: ros task ledger
   is atomic O_EXCL, reaper drops AGENT_DOWN/TASK_ORPHANED/RESEED_NEEDED into the orchestrator inbox).
4. NO SELF-SPAWNING TOP-LEVEL SESSIONS. A lane is a loop iteration. Only the poller and orchestrator ever
   hand off, one generation at a time, and ONLY at their own context limit.
5. The poller HOLDS idle lanes silently (no commit per idle cycle) -> kills the 363-commits/no-science
   churn. Commit only on a real durable change (evidence forwarded, task opened/closed, verdict written).

## MIGRATION (when dengcchi approves — NOT YET)
1. Build `ros lanes` (this session: implemented + tested in isolation).
2. Write ONE poller schedule job (single session, every ~10m) whose prompt = "run ros lanes; act only on
   FORWARD/RESEED? lanes; heartbeat; commit ONLY on durable change; self-handoff to one successor at
   >=35% ctx." Remove ALL the per-sub-monitor loop jobs (they're already disabled).
3. Keep the orchestrator loop as-is (it already self-checks at a bounded cadence).
4. Reap the historical sprawl roster once (`ros reap --apply`) so `ros tree`/liveness show only the live
   poller + orchestrator + any live researcher.
5. Watch ONE metric: real evidence-delta rate (verdicts/exps with new data), NOT commit count.

## OPEN QUESTIONS FOR DENGCCHI
- Fold GPU coordinators into the poller as gpu-lanes, or keep 1 coordinator session? (Either is bounded.)
- Poller cadence (10m felt right for sub-monitors; the single poller can afford 10-15m since it's 1 session).
- Floor policy per lane unchanged (work-gated; HOLD below floor is correct) — confirm.
