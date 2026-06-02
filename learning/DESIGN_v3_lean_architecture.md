# research-os v3 — LEAN ARCHITECTURE (dengcchi's design)

Authored 2026-06-02 from dengcchi's first-principles design session. STATUS: DESIGN — to be
implemented by a FRESH Navi session (this one is at context limit). v3 runs in FULL STANDBY alongside
v2; it must NOT interfere with the live frozen v2 instance.

## FIRST PRINCIPLE
An LLM agent is justified ONLY where there is open-ended judgment that cannot be written as a rule.
Everything else is deterministic plumbing = a script (ros.py / cron). v2's fatal flaw: proj-monitors
and coordinators were Navi SESSIONS by historical accident — that accident WAS the sprawl (N
self-spawning top-level sessions, 18h productive-idleness).

## COMPONENT CLASSIFICATION (dengcchi-confirmed)
AGENTS (LLM — only 3 kinds):
  - orchestrator        (the LEAN debugger; research judgment: design new claim, advance-vs-converge a
                         yellow, TALLY the 6 committee votes -> ros verdict write)
  - claim seeders       (researchers; real experiments/analysis/design; 2 per proj-monitor)
  - committee group     (6 honest reviewers)

DETERMINISTIC (script / cron / data — everything else):
  - H100, MI350                         (hardware)
  - GPU task queue, verdict queue, committee queue   (data stores = Channels)
  - monitor                             (top-level driver/reaper cron — system health watchdog)
  - coordinator                         (GPU dispatch cron)
  - committee health monitor            (the ALL_COMMITTEE_DONE gate cron)
  - proj-monitor 1/2/3                  (per-project lane cron = `ros lanes` per project)

## AGENT LIFECYCLE — EVER-RUN (not self-kill)
Agents LIVE long; they do NOT self-kill at 35%. This eliminates the v2 init-churn (constant
re-initialization was a big chunk of the busy-work). Bounded by:
  - HARD retire ceiling = 350k tokens. At 350k: distill MOST VALUABLE learnings -> role .md, then hand
    to exactly ONE successor (NOT generational churn every few cycles).
  - A researcher that finishes EXP-A STAYS ALIVE and picks up the next task the proj-monitor/conductor
    assigns (does not die between experiments). This is what kills the init churn.

## LEARNING SYSTEM (two tiers) — warm-start, never re-read bloated logs
  TIER 1 (role-family brain, curated, SMALL):  learning/roles/<role>.md  (e.g. researcher.md,
    orchestrator.md). A fresh/successor agent reads THIS on boot (cheap) — NOT raw history. This breaks
    the v2 death-spiral (re-reading own bloated buglog -> context bloat -> self-kill -> respawn).
  TIER 2 (global per-role, per-date, segregated):  learning/<role>/YYYY-MM-DD.md  (append-only daily).
  ON RETIRE@350k: distill the most valuable learnings -> append to BOTH Tier-1 role brain + Tier-2 dated.

## CRONJOB TABLE (all deterministic; each drops runtime/cron/<job>.alive on success)
| cron                     | freq   | job                                                                 | notifies on end |
| monitor (driver/reaper)  | 5 min  | see MONITOR SPEC below                                              | TROUBLESHOOTER (main navi session); system-health only |
| coordinator              | 2 min  | GPU task queue: free node + committee-approved exp + host_mem_floor OK -> ros exp dispatch; auto-release lease on fault/complete; re-dispatch faulted | orchestrator (dispatch/fault); silent if no GPU work |
| committee health monitor | 1 min  | poll in-flight committee runs: _status.txt==ALL_COMMITTEE_DONE + every .out non-empty + no EMPTY_OUTPUT_NO_VOTE; flag INCOMPLETE/stalled | orchestrator ("CLAIM-X ready to tally" / "INCOMPLETE"); silent if none |
| proj-monitor 1/2/3       | 5 min  | ros lanes (per project): classify seeder liveness; FORWARD committee-ready evidence to committee queue; hold-below-floor (no make-work); open/close tasks on seeder spawn/terminal; keep seeders fed within floor | orchestrator (FORWARD/RESEED?/ADVANCE?); silent on HOLD/AWAIT |

## MONITOR SPEC (the watchdog — 5 responsibilities, dengcchi-defined)
1. CHECK .alive STAMPS: every cronjob writes runtime/cron/<job>.alive on success. Stale > 3x its
   interval => that cron is dead/stalled => escalate to TROUBLESHOOTER.
2. PING AGENTS FOR STALL: heartbeat age + VERIFY OS PROCESS (pgrep/ps PID + CPU%; BUG-26/29 guard — a
   long claude -p turn looks dead while alive+computing). Stale-hb + no process = truly dead.
3. CHECK AGENT SESSION LOGGING: is the agent actually producing output, or wedged (process alive but
   log not growing)? A live process with a frozen log is a distinct, sneakier stall.
4. PROGRESS/COMMIT TIMING (the important one — "work isn't landing"): track TIME-SINCE-LAST-REAL-PROGRESS
   per claim/lane, not just liveness:
     - claim seeder wrote a claim LOCALLY but never COMMITTED to GitHub -> stall
     - committee done but VERDICT not committed -> stall
     - GPU result round-trip: result back -> goes to committee a 2nd time (TWO-PASS committee, below)
     - ORCHESTRATOR is the COMMIT MEDIATOR (responsible for actually committing to GitHub)
     - THRESHOLD: no progress > 20 min (GLOBAL) -> notify ORCHESTRATOR to troubleshoot.
       GPU stage gets slack: > 30 min.
5. MAXIMAL LOGGING/AUDIT: log+audit everything troubleshoot-relevant, ESPECIALLY agent behavior (what
   each agent did, when, produced, where it stuck). Rich forensic trail so any stall is post-hoc
   diagnosable.

## TWO-PASS COMMITTEE (confirmed)
L0 evidence -> committee #1 -> yellow / approve-GPU-exp -> GPU runs -> result back -> committee #2 (now
WITH GPU data) -> verdict. The committee-health cron gates both passes; the orchestrator tallies both.

## ESCALATION CHAIN (dengcchi-confirmed)
  navi-agent session (MAIN debugger / troubleshooter)
        ^                         ^ system-health stalls (monitor #1-3) + monitor-itself-dead
        |  (orchestrator gets ONE shot; if IT is the stall, escalate up)
  orchestrator (LEAN debugger)    <- research events + work-not-landing (monitor #4) + committee tally
        ^
  proj-monitors / coordinator / committee-health crons (research-workflow events)
"Who watches the watchers": monitor checks all other crons via .alive; the MAIN NAVI SESSION checks the
monitor's .alive on its periodic wake (backed by the scheduler's consecutiveErrors/Skips). Optionally a
tiny dead-man cron pings the human if the monitor .alive goes stale.

## STALL TAXONOMY (what the monitor distinguishes)
  cron dead          -> .alive stamp stale > 3x interval
  agent process dead -> stale hb + no PID (ps-verified)
  agent wedged       -> PID alive but session log not growing
  work not landing   -> local-but-uncommitted claim / committee-done-no-verdict / GPU-result-not-resubmitted, > 20m (GPU 30m)

## v3 = FULL STANDBY, ZERO v2 INTERFERENCE
- v3 components are BUILT but on STANDBY; nothing touches the live frozen v2 instance
  (/Users/dengcchi/autonomous-research). v2 loops stay disabled/frozen.
- v3 runs against its OWN instance dir (LOCAL runtime_dir) so test/standby agents never leak into v2
  runtime (the recurring leak trap — always sed runtime_dir to a v3-local path).
- Cut over to v3 only on dengcchi's explicit approval.

## WHAT v3 REUSES vs. ADDS (lean changeset — engine HEAD 39a80cd, 49 commands today)
REUSE AS-IS (already deterministic + concurrency-safe from v2 bugbashes BUG-31..61):
  - Channels (committee queue / GPU task+result / inbox) — per-channel O_EXCL lock (BUG-59)
  - ros lanes (FORWARD/AWAIT/RESEED?/ADVANCE?/HOLD) — the proj-monitor brain (BUG-61)
  - ros reap / tree / task / retire / handoff (supervise.py) — supervision + reaper
  - ros exp dispatch/complete (GPU lease + fault recovery, host_mem_floor) (BUG-53/54/55)
  - ros verdict write (real-6/6 member-role gate) (BUG-56/57/58)
  - run_committee.sh (ALL_COMMITTEE_DONE / EMPTY_OUTPUT_NO_VOTE gate)
ADD (net-new for v3):
  - runtime/cron/<job>.alive stamp convention + a `ros cron-health` check (monitor #1)
  - progress-timing tracker: last-commit / last-verdict / last-GPU-result per claim, with 20m/30m
    thresholds (monitor #4) — likely `ros progress` (read-only, computes time-since-last-landing)
  - learning tiers: learning/roles/<role>.md + learning/<role>/YYYY-MM-DD.md + a retire-time distill step
  - ever-run agent loop contract (350k ceiling, ONE successor, warm-start from Tier-1 role brain)
  - the cron wiring itself (monitor 5m, coordinator 2m, committee-health 1m, proj-monitor 5m) as
    SCRIPTS, not Navi sessions
CLEAN UP (lean):
  - the runtime/ graveyard (months of launch_run*/poll_run*/researcher-*_prompt logs) — v3 starts clean
  - the v2 self-spawn loop jobs (all already disabled) — fresh session sweeps them step 0

## OPEN ITEMS FOR THE IMPLEMENTING SESSION
  - confirm whether ANY standing orchestrator agent vs on-demand (dengcchi leaned: ever-run orchestrator
    as the lean debugger — keep it standing)
  - GPU coordinator: dengcchi confirmed it stays a deterministic cron (not folded judgment)
  - exact `ros progress` / `ros cron-health` command shapes
