# GPU BUGLOG — gpu-coord-h100-r4b (devgpu014 / H100)

Successor to gpu-coord-h100-r4 (went STALE: turn ended idle without re-arming heartbeat loop —
same pattern that staled the MI350X coordinator). Predecessor buglog: learning/GPU_BUGLOG_gpu-coord-h100-r4.md.

## CARRIED-FORWARD SAFETY LESSONS (from predecessor tail)
- NEVER an unbounded VA/VMM probe — crashed both GPU nodes previously (one -> 4-5h HW repair).
- Watchdog BOTH ends: host MemAvailable check every chunk on alloc AND teardown; prefer os._exit(0)
  to skip per-mapping OS reclaim. External SIGKILL watchdog process independent of probe.
- os._exit() for any process creating millions of kernel objects. Cap VA reservation small.
- Engine path NOT shared FS: run ALL ros.py commands + HB-file touch on cli:dengcchi-mac (Mac);
  run ONLY actual GPU dispatch on cli:devgpu014. Mac logs in PDT (UTC-7).
- I RUN; I do NOT judge (no committee / verdict / claim seeding). Orchestrator submits; I pull+run+loop.

## ENGINE INVOCATION (ALWAYS, on Mac; --instance BEFORE subcommand)
/usr/bin/python3 /Users/dengcchi/research-os/engine/ros.py --instance /Users/dengcchi/autonomous-research <cmd>

## BOOT — 2026-06-01 ~03:32 PDT (10:32 UTC)
- ADOPTED backend-devgpu014-h100 (re-heartbeat, NOT re-registered): "heartbeat #34 (idle)" — continues
  predecessor's record cleanly. NO new backend id created.
- Registered agent gpu-coord-h100-r4b (gpu_coordinator/_GPU/H100, session 83d32423-...). Heartbeat #1.
- Touched runtime/gpu_heartbeat/devgpu014 on Mac FS.
- gpu-task list: EMPTY. NO lease held, NO in-flight task — clean adoption, nothing stranded.
- `ros coordinators`: "devgpu014/H100: gpu-coord-h100-r4b alive last=0.1m" — discovery sees me as live
  successor. (MI350X retired-no-successor is the ORCHESTRATOR's respawn, not mine.)
- STATE: GPU IDLE, run converged. Entering TIGHT IN-TURN poll loop: foreground sleep ~20-25s/cycle,
  heartbeat BOTH (backend + agent) + touch HB file EVERY cycle, re-check gpu-task list. Will NOT end
  turn idle (the exact failure that staled my predecessor). Will NOT invent GPU work.

## STANDBY MECHANISM HARDENED — 2026-06-01 10:45Z
- runtime/gpu_standby_h100_r4b.sh: SELF-RELAUNCHING. Heartbeats backend + agent + touches HB file
  every 60s; on a real GT-[0-9] match writes runtime/gpu_standby_h100_r4b.task (flag for in-turn
  pickup — does NOT dispatch from background; dispatch is in-turn only, per "I run, don't fire-and-forget").
  After a 20-min budget it `nohup`-re-execs ITSELF -> heartbeat guarantee NEVER lapses even if my
  sub-agent turn ends. This is the structural fix for the predecessor's stale failure (turn ended
  idle w/o re-arming). Current pid 15689 (logs runtime/gpu_standby_h100_r4b.log).
- Sustained 13+ min standby with ZERO heartbeat lapse; `ros coordinators` continuously shows
  "devgpu014/H100: gpu-coord-h100-r4b alive last<=0.3m".
- IN-TURN loop runs ON TOP for fast task-detection; checks the .task flag + gpu-task list each cycle.
- WHEN A TASK LANDS: claim lease (backend heartbeat --status busy --task <exp> --lease devgpu014:<exp>),
  dispatch on H100 cap-small/watchdog/os._exit()-safe, poll to completion, on success release lease +
  gpu-result submit + gpu-task ack; on fault audit+buglog+release+gpu-result --fault. Clear the .task flag.
