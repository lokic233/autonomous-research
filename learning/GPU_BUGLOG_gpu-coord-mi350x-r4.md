# GPU BUGLOG — gpu-coord-mi350x-r4 (backend-devgpu499-mi350x / MI350X / FRAGILE NODE)

Coordinator: gpu-coord-mi350x-r4 | Backend: backend-devgpu499-mi350x | GPU: MI350X | Node: devgpu499
Spawned by: orchestrator-r4-001 (session be17b683-7e09-426c-90f8-67bcdda9cee8)
My session: fc1c53de-2fae-4083-b99f-e9670a2bf20e
host_mem_floor_gb: 400

---

## BOOT (2026-06-01 ~02:45 PDT / 09:45 UTC) — engine-path reachability resolved + registration

### ENGINE-PATH REACHABILITY (resolved FIRST per spec)
- devgpu499 (GPU node, hostname devgpu499.ldc2.facebook.com): /Users/dengcchi/research-os/engine/ros.py
  and /Users/dengcchi/autonomous-research are **NOT reachable** (ls: No such file or directory).
  => NOT a shared FS. devgpu499 is a Linux GPU box; the Mac home is not mounted there.
- cli:dengcchi-mac (control node, hostname dengcchi-mac): engine ros.py (90KB) + instance dir BOTH present.
- RESOLUTION (matches EXP-0026/0027 cross-node pattern in ENGINE_BUGLOG_orchestrator-r2-001):
  * ALL engine commands (ros register/heartbeat/gpu-task/gpu-result, heartbeat file touch) run on
    cli:dengcchi-mac.
  * ONLY the actual GPU dispatch (HIP/torch kernels) runs on cli:devgpu499.
  * Results copied back from devgpu499:/tmp to the Mac instance for gpu-result submit.

### NODE FACTS (devgpu499)
- Host RAM: 3022 GB total, ~1579 GB free at boot (free -g).
- 8x MI350X GPUs, ~288 GB VRAM each (309220868096 B); several already ~40GB used (shared box).
- This node is the FRAGILE one: hard-crashed 3x in session 511ce2e2 (see MI350X_CRASH_POSTMORTEM.md).

### host_mem_floor CHOICE = 400 GB
- Postmortem danger thresholds were 256-300 GiB; all 3 crashes involved host kernel-mapping-metadata
  exhaustion (unbounded VA/VMM mapping) on alloc (#1,#2) AND teardown (#3, the subtle one -> 4-5h HW repair).
- 400 GB floor on a 3022 GB box leaves ~2.6 TB working headroom while staying well ABOVE the historical
  crash thresholds. Conservative + generous headroom per spec.

### SAFETY DOCTRINE I ENFORCE (from MI350X_CRASH_POSTMORTEM.md R0-R6)
- R0 Necessity gate: don't run experiments a settled thesis doesn't need.
- R1 Cap small: smallest mapping/alloc count that answers the question (NEVER chase 8-figure counts).
- R2 Watchdog BOTH alloc AND teardown; prefer os._exit(0) for teardown of million-object probes.
- R3 External SIGKILL watchdog process at a hard host-RAM floor, independent of the probe's own checks.
- R4 os._exit(0) to skip pathological per-object userspace teardown.
- HARD RULE: REFUSE to dispatch ANY fragile (MI350X) task lacking host_mem_floor_gb. NEVER unbounded VA/VMM.

### REGISTRATION
- backend register --id backend-devgpu499-mi350x --kind gpu --gpu-type MI350X --node devgpu499 --host-mem-floor 400 => OK
- agent register --id gpu-coord-mi350x-r4 --role gpu_coordinator --project _GPU --gpu MI350X --session fc1c53de... => OK
- backend heartbeat #1 (idle) + ros heartbeat #1 (running) => OK
- touched runtime/gpu_heartbeat/devgpu499 => OK
- `ros coordinators` now shows: devgpu499/MI350X gpu-coord-mi350x-r4 alive; ✅ every GPU backend covered.

### STATE
- gpu-task channel EMPTY (no pending tasks). H100 sibling (gpu-coord-h100-r4) alive + idle.
- Run is converged / orchestrator prefers safe H100. Correct posture: IDLE, stay alive + ready.
- Entering ACTIVE standby loop: heartbeat both + touch heartbeat file + re-check gpu-task list each cycle.

## STANDBY (2026-06-01 ~02:46 PDT) — idle, converged, alive+ready
- Ran multiple standby cycles: backend heartbeat #1->#6, agent heartbeat #1->#7, heartbeat file refreshed each.
- gpu-task channel remained EMPTY every cycle. H100 sibling alive+idle. `ros coordinators` => ✅ both backends covered.
- POSTURE (correct per spec): run is converged, orchestrator prefers safe H100 (devgpu014); MI350X sits idle.
  Do NOT invent GPU work. Stay alive + ready; orchestrator submits tasks to the channel when needed.
- No task claimed, no lease held, no fault. Backend idle, no in-flight work. Nothing to strand.
- When a task arrives: it MUST carry host_mem_floor_gb (else REFUSE). On valid task -> claim lease (status busy),
  dispatch on devgpu499 WITH alloc+teardown host-RAM watchdog (os._exit) + external SIGKILL watchdog, poll for
  crash/host-mem, release lease, gpu-result submit, gpu-task ack. NEVER unbounded VA/VMM.
