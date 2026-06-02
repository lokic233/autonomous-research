# HANDOFF -> v3 IMPLEMENTATION SESSION #2 (fresh Navi session)

From: v3-impl session #1 (handed off at dengcchi's request, context). You are session #2.
Your job is UNCHANGED: BUILD research-os v3, lean + first-principles, FULL STANDBY, ZERO
interference with the live FROZEN v2 instance. Cut over only on dengcchi's explicit approval.

## ★ READ FIRST (in order, on cli:dengcchi-mac)
1. /Users/dengcchi/autonomous-research/learning/HANDOFF_v3_implementation.md  — the ORIGINAL handoff
   (build plan, method-that-worked, safety rules, open items). Still authoritative.
2. /Users/dengcchi/autonomous-research/learning/DESIGN_v3_lean_architecture.md  — THE SPEC. Build to this.
3. /Users/dengcchi/autonomous-research/learning/DESIGN_anti-sprawl_single-poller.md  — earlier context.
4. tail of /Users/dengcchi/autonomous-research/learning/ENGINE_BUGLOG_orchestrator-r2-001.md — 61 v2 bugs
   fixed; v3 REUSES these hardened primitives, do NOT regress them.
5. /vercel/sandbox/workspace/memory/2026-06-02.md (workspace node) — full session narrative.

## GROUND TRUTH VERIFIED BY SESSION #1 (2026-06-02 ~18:30 UTC)
- Engine /Users/dengcchi/research-os HEAD 39a80cd — CLEAN, pushed.
- Instance /Users/dengcchi/autonomous-research HEAD d5bba2b — CLEAN (one harmless pre-freeze runtime
  buglog append on sub-monitor-0003-r4, ignore).
- Engine CLI: /usr/bin/python3 /Users/dengcchi/research-os/engine/ros.py --instance <ROOT> <cmd>. HTTPS-only.
- 49 commands today; `ros lanes` already emits FORWARD|AWAIT|RESEED?|ADVANCE?|HOLD (BUG-61).
- runtime_dir resolver = engine/ros.py:404 runtime_dir(root): reads config runtime.runtime_dir, ABSOLUTE.
  Live config /Users/dengcchi/autonomous-research/research-os.config.yaml line 9 runtime_dir is ABSOLUTE
  -> ALWAYS sed it to a LOCAL /tmp path in any test instance or test agents LEAK into live runtime.
- SCHEDULER = CLEAN SLATE: only "PSL Sync Reminder (biweekly)" (965a0d10), DISABLED, Weave-unrelated. Leave it.
- v2 live instance FROZEN (no loops). Do NOT touch its running state.

## OPEN DECISION FOR DENGCCHI (asked, not yet answered)
- PHASE 0 cleanup: the validate-instance leftover orchestrator-navi (session ead51fa6, last hb 16:21,
  dormant ~2h) + 4 researcher records (researcher-A/A2/B/B2) still registered in
  /Users/dengcchi/autonomous-research-validate/runtime/agents/. Its self-check job is ALREADY gone from
  the scheduler. The validate instance has its OWN local runtime_dir (line 9 =
  /Users/dengcchi/autonomous-research-validate/runtime) so it NEVER leaked into live.
  QUESTION ASKED: `ros reap --apply` it (keep dir+history) OR `rm -rf` the whole validate instance
  (it was v2-topology validation, not v3)? Session #1 leaned rm (v3 starts fresh) but it's destructive
  so asked first. GET DENGCCHI'S ANSWER before acting.

## PROPOSED v3 BUILD ORDER (session #1's plan, dengcchi hasn't objected)
Phase 0 — cleanup validate leftover (per decision above); stand up v3 instance dir w/ LOCAL runtime_dir.
Phase 1 — two net-new READ-ONLY engine commands (the monitor's eyes; lowest risk):
   1. `ros cron-health`  — reads runtime/cron/<job>.alive stamps; stale > 3x interval = dead (monitor #1).
   2. `ros progress`     — time-since-last-real-landing per claim: last-commit / last-verdict /
      last-GPU-result; flag > 20m (GPU > 30m) (monitor #4, the important one).
Phase 2 — learning tiers: learning/roles/<role>.md (curated warm-start) + learning/<role>/YYYY-MM-DD.md
   (daily) + retire@350k distill step.
Phase 3 — ever-run agent loop contract (350k ceiling, ONE successor, warm-start from Tier-1, researcher
   stays alive between experiments).
Phase 4 — the 4 crons as DETERMINISTIC SCRIPTS (monitor 5m / coordinator 2m / committee-health 1m /
   proj-monitor 5m), each drops runtime/cron/<job>.alive on success, each notifies per the cron table
   (monitor->main navi/troubleshooter for system-health; others->orchestrator). These WRAP the hardened
   primitives (ros lanes, ros exp dispatch/complete, run_committee.sh, the verdict 6/6 gate) — do NOT
   reimplement or weaken BUG-31..61.
Phase 5 — wire-up + standby validation in v3 instance -> ESCALATE to dengcchi for the CUTOVER decision.

## HOW TO BUILD SAFELY (the method that worked all session)
- ALWAYS isolated instance w/ LOCAL runtime_dir (sed config runtime_dir -> /tmp/...). Clean any leaked
  test agents (*t1*/*9001*/test) from live if you slip.
- AST-validate after every edit: python3 -c "import ast; ast.parse(open('engine/ros.py').read())".
- Capture stderr (backgrounded failures hide NameErrors — nearly slipped a fatal once).
- Commit to BOTH repos + log each change. Engine: cd /Users/dengcchi/research-os && git add -A && commit
  && push (HTTPS). Instance: `ros commit`.

## SAFETY (never violate)
never fabricate votes/verdicts; real 6/6 (every configured member BY ROLE) for green/promote — engine
BUG-56/57 gate enforces it, don't weaken it; COMMITTEE_INCOMPLETE never counts; host_mem_floor on MI350X
NEVER waived; never force-demote; NO human decision points ("awaiting dengcchi" for a resolved item = bug).
v3 = full standby; cut over only on dengcchi's explicit approval.

## ESCALATE to dengcchi for: cutover approval, the Phase-0 reap-vs-rm decision, anything ambiguous.
Otherwise build autonomously + lean. Check in at milestones (Phase 1 = both read-only cmds tested green).
