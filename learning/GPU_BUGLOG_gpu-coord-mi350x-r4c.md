# GPU BUGLOG — gpu-coord-mi350x-r4c (devgpu499 / MI350X, the FRAGILE node)

Hardened successor to gpu-coord-mi350x-r4b (kept drifting STALE: its turn ended when idle, no in-turn poll to re-arm).
STRUCTURAL FIX (this round): a DETACHED background heartbeat loop (runtime/gpu_standby_mi350x_r4c.sh) launched by
orchestrator-r4-001 owns heartbeats — every 60s it HBs backend + agent + touches runtime/gpu_heartbeat/devgpu499,
self-re-execs every 20m, and writes runtime/gpu_standby_mi350x_r4c.task as a FLAG when it sees a real GT-[0-9] task.
So heartbeats NEVER lapse across turn boundaries. My job: confirm loop alive, register, DISPATCH flagged tasks in-turn
(fragile-node-safe with host-mem watchdog), keep agent registered. I can end my turn when idle — the loop keeps me alive.
Predecessors reviewed: GPU_BUGLOG_gpu-coord-mi350x-r4b.md + r4.md (both clean handoffs — no stranded task/lease).
Crash postmortem read: MI350X_CRASH_POSTMORTEM.md (3 hard crashes: alloc x2 + TEARDOWN x1; final = 4-5h HW repair).

## HARD SAFETY (NEVER WAIVED, even during GPU auto-approve window)
- REFUSE to dispatch ANY fragile (MI350X) task lacking host_mem_floor_gb.
- NEVER unbounded VA/VMM probe (crashed node 3x). Cap small (R1). Necessity gate first (R0).
- Watchdog BOTH alloc AND teardown; use os._exit(0) to skip pathological per-object userspace reclaim (R2,R4).
- External SIGKILL watchdog at a hard host-RAM floor, independent of the probe's own checks (R3).
- host_mem_floor = 400 GB (node has 3022 GB total; historical crashes hit at 256-300 GiB danger band).
- Node lifecycle (repair/reboot) is HUMAN territory (R6). I RUN; I do NOT judge (no committee/verdict/claim).

## BOOT (2026-06-01 ~10:55 UTC / ~03:55 PDT)
- Detached standby loop CONFIRMED ALIVE: ps shows pid 23104 `bash runtime/gpu_standby_mi350x_r4c.sh`;
  log tail shows "idle @ 10:54:24Z — both HB + file touched"; heartbeat file touched ~30s prior. NOT relaunched (already up).
- Re-registered self with MY session id: agent register gpu-coord-mi350x-r4c role=gpu_coordinator project=_GPU
  gpu=MI350X session=89025938-d84a-491e-aeb9-4c148cbb99c4 => OK.
- Backend backend-devgpu499-mi350x: fresh (last HB 0.4m, status idle). Adopted — did NOT register new backend.
- gpu-task channel EMPTY. Task flag (runtime/gpu_standby_mi350x_r4c.task) ABSENT. No lease, no in-flight task.
  Nothing stranded. Clean adoption.

## POSTURE: IDLE standby — run converged at human gates, orchestrator prefers safe H100 (devgpu014).
Do NOT invent GPU work. The detached loop owns heartbeats so I CAN end my turn when idle.
On re-invoke WITH a flagged task: necessity-gate it, verify host_mem_floor_gb present (else REFUSE), claim lease
(backend heartbeat status=busy --task <exp> --lease devgpu499:<exp>), dispatch on devgpu499 WITH alloc+teardown
host-RAM watchdog (os._exit) + external SIGKILL watchdog, poll for crash/host-mem, on success release lease +
gpu-result submit + gpu-task ack; on FAULT audit+buglog+release+gpu-result submit --fault. Clear .task flag after.
