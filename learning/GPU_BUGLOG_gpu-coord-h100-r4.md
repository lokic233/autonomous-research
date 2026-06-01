# GPU BUGLOG — gpu-coord-h100-r4 (backend-devgpu014-h100 / H100)

Coordinator: gpu-coord-h100-r4 | Backend: backend-devgpu014-h100 | GPU: NVIDIA H100 (8x, 97871 MiB ea) | Node: devgpu014
Spawned by: orchestrator-r4-001 (session be17b683-7e09-426c-90f8-67bcdda9cee8) | My session: 85dde2fa-cbaa-4e23-b87c-096b7da17300

## SAFETY CONTRACT (from MI350X_CRASH_POSTMORTEM.md — NEVER violate)
- R0 necessity gate: do not run an experiment a settled thesis doesn't need.
- R1 cap small: smallest mapping/alloc count that answers the question (5-10M is conclusive for ceiling probes).
- R2 watchdog BOTH ends: host MemAvailable check every chunk on alloc AND teardown; prefer os._exit(0) to skip per-mapping OS reclaim.
- R3 external SIGKILL watchdog process independent of probe.
- R4 os._exit() for any process creating millions of kernel objects.
- NEVER an unbounded VA/VMM probe — crashed both GPU nodes previously (one -> 4-5h HW repair).
- I RUN; I do NOT judge (no committee / verdict / claim seeding). Orchestrator submits tasks; I pull+run+loop back.

## BOOT — 2026-06-01 ~02:44 PDT (09:44 UTC)
- ENGINE-PATH REACHABILITY (resolved first, per spawn instruction): /Users/dengcchi/research-os + /Users/dengcchi/autonomous-research
  are NOT visible from devgpu014 (`ls` -> No such file or directory). NOT a shared/NFS FS.
  RESOLUTION: run ALL engine (ros.py) commands via cli:dengcchi-mac (the Mac, where engine+instance live);
  run ONLY actual GPU dispatch on cli:devgpu014 (the H100 box). Heartbeat file touched on Mac FS.
- Engine invocation: /usr/bin/python3 /Users/dengcchi/research-os/engine/ros.py --instance /Users/dengcchi/autonomous-research <cmd> (run on Mac).
- H100 node state at boot: 8x H100, all idle (<=120 MiB used, 0% util). Host mem 2.27 TiB total, 1.26 TiB available. Healthy.
- Registered backend-devgpu014-h100 (gpu/H100/devgpu014) + agent gpu-coord-h100-r4 (gpu_coordinator/_GPU/H100). Heartbeat both #1. Touched runtime/gpu_heartbeat/devgpu014.
- gpu-task list: EMPTY (no pending tasks). backend list: was empty before my register.
- STATE: GPU IDLE. Run is converged / claims human-gated per OVERNIGHT_STATUS + engine buglog. Entering tight standby loop — heartbeat both + touch HB file each cycle, re-check gpu-task list. Will NOT invent GPU work.

## STANDBY MECHANISM — 2026-06-01 09:46Z
- runtime/gpu_standby_h100.sh: heartbeats backend + agent + touches HB file every ~55s, logs gpu-task list
  (runtime/gpu_standby_h100.log). Breaks + logs TASK_DETECTED on a real GT-[0-9] match (read-only poll, safe).
- NIT (self, fixed): first detection regex matched the literal word "task" in the "(gpu task channel empty)"
  message -> false TASK_DETECTED. Tightened to `grep -qE 'GT-[0-9]'`. Now correctly idles on empty.
- coordinators discovery confirms orchestrator sees me: "devgpu014/H100: gpu-coord-h100-r4 alive last=0.0m".
  (devgpu499/MI350X has NO coordinator — that's the orchestrator's spawn, not mine.)
- Cadence: relaunch standby loop in-turn when it finishes its cycle budget; claim+dispatch the instant a GT- lands.
