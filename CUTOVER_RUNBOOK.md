# research-os v3 — CUTOVER RUNBOOK (requires dengcchi's explicit approval)

STATUS: v3 BUILT + standby-validated. Live v2 (/Users/dengcchi/autonomous-research) is FROZEN and
UNTOUCHED. Do NOT cut over without dengcchi's explicit go.

## WHAT v3 IS (one screen)
Only 3 LLM agent kinds: orchestrator (lean debugger), researchers (claim seeders, 2/project), committee
(6 reviewers). EVERYTHING else is a deterministic script/cron. Ever-run agents (no self-kill at ctx%);
hard 350k token ceiling -> distill -> ONE successor. Two-tier learning (roles/<fam>.md warm-start +
<fam>/DATE.md daily). Escalation: main navi (troubleshooter) <- orchestrator <- crons.

## THE 4 CRONS (engine/crons/, all deterministic, wrap hardened v2 primitives)
| cron             | freq | wraps                              | notifies            |
| monitor.sh       | 5m   | ros cron-health(#1) + ros progress(#4) + ros reap | troubleshooter (sys-health) / orchestrator (work-not-landing) |
| coordinator.sh   | 2m   | ros gpu-pending + ros exp dispatch | orchestrator (dispatch/fault); silent if no GPU work |
| committee_health.sh | 1m | run_committee.sh gate artifacts   | orchestrator (READY/INCOMPLETE); silent if none |
| proj_monitor.sh  | 5m   | ros lanes (BUG-61)                 | orchestrator (FORWARD/RESEED?/ADVANCE?); silent on HOLD/AWAIT |
Each drops runtime/cron/<job>.alive ONLY on success. cron-health flags stale > alive_stale_x x interval.
The MAIN NAVI session watches the monitor's own .alive ("who watches the watchers").

## STANDBY VALIDATION (safe, anytime — no scheduler, no v2 contact)
  export ROS_INSTANCE=/Users/dengcchi/autonomous-research-v3
  bash /Users/dengcchi/research-os/engine/crons/drive.sh once
Expect: all 4 crons exit 0, cron-health all FRESH. (Done 2026-06-02, clean.)

## CUTOVER STEPS (only on dengcchi's go)
1. Confirm v2 is fully frozen (no enabled loop jobs; only PSL Sync biweekly, unrelated).
2. Seed v3's first real work: `ros seed new` the starting claim(s) / project(s) into the v3 instance.
3. Spawn the 3 agent kinds as Navi sessions pointed at ROS_INSTANCE=v3:
   - ONE orchestrator (ever-run, warm-start `ros learn warm --role orchestrator`).
   - researchers per active project (warm-start `ros learn warm --role researcher`).
   - committee convened on demand by the orchestrator via run_committee.sh.
4. Install the crons (deterministic, NOT Navi sessions):
   `ROS_INSTANCE=/Users/dengcchi/autonomous-research-v3 bash engine/crons/drive.sh crontab | crontab -`
   (or `drive.sh launchd` for macOS launchd plists).
5. Watch ONE metric: real evidence-delta rate (verdicts/exps with NEW data), NOT commit count.
6. ROLLBACK: `crontab -r` (or unload launchd) stops all v3 crons instantly; v2 remains frozen, untouched.

## SAFETY INVARIANTS (never violate)
real 6/6 by ROLE for green/promote (BUG-56/57); COMMITTEE_INCOMPLETE never counts; host_mem_floor on
MI350X never waived; never force-demote a promoted claim; no human decision points; agents distill+hand
to ONE successor at 350k. v3 instance has its OWN local runtime_dir + NO git remote (can't pollute live).
