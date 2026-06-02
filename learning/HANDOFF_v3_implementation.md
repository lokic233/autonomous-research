# HANDOFF -> v3 IMPLEMENTATION SESSION (fresh Navi session)

From: monitor successor (retiring at context limit, 2026-06-02). You are the fresh session that will
IMPLEMENT research-os v3. dengcchi designed it; your job is to BUILD it (lean, first-principles), in
FULL STANDBY, with ZERO interference to the live frozen v2.

## ★ READ FIRST (in order)
1. /Users/dengcchi/autonomous-research/learning/DESIGN_v3_lean_architecture.md  — THE SPEC (dengcchi's
   confirmed design: component classification, ever-run agents @350k, 2-tier learning, cron table,
   monitor's 5 jobs, 2-pass committee, escalation chain, reuse-vs-add changeset). Build to THIS.
2. /Users/dengcchi/autonomous-research/learning/DESIGN_anti-sprawl_single-poller.md — earlier design
   context (the `ros lanes` poller idea that v3 builds on).
3. /Users/dengcchi/autonomous-research/learning/ENGINE_BUGLOG_orchestrator-r2-001.md (tail) — all 61
   engine bugs fixed in v2 (BUG-31..61). v3 REUSES these hardened primitives; do NOT regress them.
4. /vercel/sandbox/workspace/memory/2026-06-02.md (workspace node) — the full session narrative.

## CURRENT STATE (clean handoff point)
- Engine repo /Users/dengcchi/research-os HEAD 39a80cd (CLEAN, pushed). Instance
  /Users/dengcchi/autonomous-research HEAD 03292cc (CLEAN, pushed, has the v3 design docs).
- Engine CLI: /usr/bin/python3 /Users/dengcchi/research-os/engine/ros.py --instance <ROOT> <cmd>  (cli:dengcchi-mac, HTTPS-only).
- ALL v2 self-spawn loop jobs REMOVED from the scheduler (done this session). ONLY remaining job =
  "PSL Sync Reminder (biweekly)" = Weave, UNRELATED, leave it. Scheduler is a clean slate.
- v2 live instance is FROZEN (no loops). DO NOT touch /Users/dengcchi/autonomous-research's running
  state for v3 work — v3 gets its OWN instance dir.
- LEFTOVER to clean up: the orchestrator-navi VALIDATION session (ead51fa6-...) + its researcher
  sub-agents are still registered in /Users/dengcchi/autonomous-research-validate/runtime/agents/. That
  was a v2-topology validation; you can `ros reap --apply` it or just rm the validate instance — it is
  NOT v3. (v3 starts fresh.)

## v3 BUILD PLAN (lean — from the design doc's reuse/add/cleanup sections)
REUSE AS-IS (already deterministic + concurrency-safe): Channels (BUG-59 locks), ros lanes (BUG-61
RESEED?/ADVANCE?), ros reap/tree/task/retire/handoff (supervise.py), ros exp dispatch/complete (GPU
lease+fault, host_mem_floor), ros verdict write (real-6/6 member-role gate BUG-56/57), run_committee.sh.
ADD (net-new):
  1. `ros cron-health` — checks runtime/cron/<job>.alive stamps (stale > 3x interval = dead). Each cron
     drops its .alive on success. (monitor job #1)
  2. `ros progress` (read-only) — time-since-last-real-landing per claim: last-commit / last-verdict /
     last-GPU-result; flag > 20min (GPU > 30min). (monitor job #4 — "work isn't landing")
  3. Learning tiers: learning/roles/<role>.md (curated warm-start) + learning/<role>/YYYY-MM-DD.md
     (segregated daily) + a retire@350k distill step.
  4. Ever-run agent loop contract: 350k ceiling, ONE successor, warm-start from Tier-1 role brain,
     researcher stays alive between experiments.
  5. The cron wiring as SCRIPTS (monitor 5m / coordinator 2m / committee-health 1m / proj-monitor 5m),
     NOT Navi sessions. Each notifies per the cron table (monitor->troubleshooter; others->orchestrator).
CLEAN UP: the runtime/ graveyard (months of launch_run*/poll_run*/researcher-*_prompt). v3 starts clean.

## HOW TO BUILD SAFELY (the method that worked all session)
- ALWAYS build/test in an ISOLATED instance with a LOCAL runtime_dir: mkdir /tmp/v3test; cp config; sed
  runtime_dir -> /tmp/v3test/runtime (config default is ABSOLUTE -> test agents LEAK into the live
  runtime if you skip this — happened repeatedly; clean any leaked *t1*/*9001*/test agents).
- AST-validate after every edit: python3 -c "import ast; ast.parse(open('engine/ros.py').read())".
- Capture stderr (backgrounded failures hide NameErrors — that's how a fatal bug nearly slipped).
- Commit to BOTH repos + log each change. Engine: cd /Users/dengcchi/research-os && git add -A &&
  commit && push. Instance: `ros commit`.

## SAFETY (never violate — same as v2)
never fabricate votes/verdicts; real 6/6 (every configured member by role) for green/promote — the
engine BUG-56/57 gate enforces this, don't weaken it; COMMITTEE_INCOMPLETE never counts; host_mem_floor
on fragile MI350X NEVER waived; never force-demote; no human decision points ("awaiting dengcchi" for a
resolved item = bug). v3 = full standby; cut over only on dengcchi's explicit approval.

## OPEN ITEMS dengcchi flagged for you
- standing ever-run orchestrator agent (he leaned YES — keep it standing as the lean debugger).
- GPU coordinator stays a deterministic cron (confirmed, not folded judgment).
- exact `ros progress` / `ros cron-health` command shapes (your call, keep lean).
- the experiment date path (cmd_exp_register line ~241) uses its OWN date calc, not obj_dir/_valid_date —
  unify it through _valid_date for consistency (minor, noticed but not yet done).

## ESCALATE to dengcchi for: cutover approval, anything ambiguous. Otherwise build autonomously + lean.
