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

## SELF-FEED MODEL ADOPTED + EXP-0045 PICKED UP — 2026-06-01 11:34Z (engine b667696)
- NEW MODEL: coordinator self-feeds. `ros gpu-pending --gpu-type H100` -> EXP-0045/CLAIM-0006 (async-V1-connector
  E2E, window-approved until 2026-06-02T09:28:58Z, floor=0 H100 non-fragile). Self-submitted ->
  GT-0001 (`ros gpu-task submit --exp EXP-0045 --gpu-type H100 --by gpu-coord-h100-r4b`). Lease claimed:
  backend heartbeat --status busy --task EXP-0045 --lease devgpu014:EXP-0045.
- INCIDENT: detached standby loop DIED during the engine update (old pid 15689 gone; last HB 11:24:59Z ->
  I was at 6.3m, still < 15m kick). RELAUNCHED pid=96927 (PPID 1, detached, survives turn end). Orchestrator
  had updated the script to ALSO flag gpu-pending items to .task. Lesson: after any engine/script update,
  VERIFY the standby pid is still alive (pgrep) — an update can orphan/kill it.
- H100 PREP (node=cli:devgpu014, NO ssh/cert): GPUs 1-7 free (~4MiB), GPU0 41GB used by other tenant;
  8x97GB. ros-vllm07 env: vLLM 0.22.0, python3.12 (symlink py3.12). Ready for instant dispatch.
- WAITING on harness (per orchestrator: I run the GPU, researcher writes the science). researcher-0006-asyncE2E-r4
  ALIVE+active (last 8.2m, sub-monitor-0002 owns its health). 11:33:40Z it cleared 2 lmcache 0.4.6 blockers
  (sitecustomize monkeypatch re-registers live vLLM model w/ lmcache VLLMModelTracker; LMCACHE_TRACK_USAGE=false
  for py-cpuinfo crash) and is BOOTING real LMCacheConnectorV1 + CacheBlend (chunk256/local_cpu/use_layerwise=async/
  enable_blending/recompute_ratio0.15, 28 layers) in vLLM 0.22 on H100. impl/ NOT yet on disk -> POLLING.
- RUN PLAN when harness lands: copy experiments/2026-06-01/EXP-0045/impl/ -> cli:devgpu014, run with
  ~/.conda/envs/ros-vllm07/bin/python watchdog-safe (15min wall / 2 GPU-hr / 80GB budget), copy results back
  to Mac experiments/2026-06-01/EXP-0045/results/, then gpu-result submit + gpu-task ack GT-0001 +
  report --done "GR-xxxx ready". FALLBACK if 0.22 sig drift bites: pip install vllm==0.7.3 INTO ros-vllm07
  ONLY (NEVER touch ros-vllm 0.6.6).
