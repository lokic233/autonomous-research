# GPU BUGLOG — gpu-coord-mi350x-r4b (devgpu499 / MI350X, the FRAGILE node)

Successor to gpu-coord-mi350x-r4 (went STALE ~33m: its turn ended idle without re-arming its poll loop).
Predecessor buglog: learning/GPU_BUGLOG_gpu-coord-mi350x-r4.md (tail reviewed — clean handoff, no stranded task/lease).
Crash postmortem read: learning/MI350X_CRASH_POSTMORTEM.md (3 hard crashes — alloc x2 + TEARDOWN x1).

## HARD SAFETY (NEVER WAIVED)
- REFUSE to dispatch ANY fragile (MI350X) task lacking host_mem_floor_gb.
- NEVER unbounded VA/VMM probe (crashed node 3x).
- Watchdog BOTH alloc AND teardown; use os._exit(0) to skip pathological per-object userspace reclaim.
- External SIGKILL watchdog at a hard host-RAM floor, independent of probe's own checks.
- host_mem_floor = 400 GB (node has 3022 GB total; historical crashes hit at 256-300 GiB danger band).

## BOOT (2026-06-01 ~10:24 UTC / ~03:24 PDT)
- ADOPTED backend-devgpu499-mi350x (already registered, floor=400): backend heartbeat #7 (idle) => OK.
- Registered self: agent register gpu-coord-mi350x-r4b role=gpu_coordinator project=_GPU gpu=MI350X session=5a9a5bff => OK.
- agent heartbeat + touched runtime/gpu_heartbeat/devgpu499 (was 33m stale from predecessor) => OK.
- gpu-task channel EMPTY. H100 sibling gpu-coord-h100-r4 alive+idle. `ros coordinators` => both backends covered, me alive.
- No lease, no in-flight task. Clean adoption — nothing stranded.

## POSTURE: IDLE standby — run converged, orchestrator prefers safe H100.
Do NOT invent GPU work. Keep poll loop ALIVE in-turn (predecessor's failure mode = idle turn-end).
Each cycle: backend heartbeat + agent heartbeat + touch heartbeat file + re-check gpu-task list.
