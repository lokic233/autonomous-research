# SUBMONITOR BUGLOG — sub-monitor-0005-r5 (PROJ-0005)

Project: PROJ-0005 — Tool-Result Re-Tokenization Boundary Churn (CLAIM-0014)
Spawned by: orchestrator-r5-001 (session 5b4e5cff-9888-48a1-bd41-61fdb5fe975d)
Successor to: sub-monitor-0005-r4 (DIED at context limit, no graceful handoff)
Session: 59ac0b2e-02e0-40b9-9fef-8b7614b47a2c
Node: cli:dengcchi-mac ONLY
Floor N = 2 (work-gated)

## STATE INHERITED (verified, not narrative)
- CLAIM-0014: L0 cheap-kill EXP-0049 ran, all 3 gates PASS aggregate. Committee committee_run_23 ->
  VERDICT-0055 = 6/6 YELLOW (held honestly, NOT promoted). Must satisfy RE-01..RE-06 to advance.
- CPU-doable RE subset = RE-01 (BPE null model), RE-02 (Llama-3 tokenizer+corpus), RE-05 (per-slice
  multiple-comparison correction), RE-06 (block-size sensitivity) + missing citations (Gim 2311.04934,
  Don't-Break-the-Cache 2601.06007, Sennrich BPE ACL2016) + title re-frame to regime-a-only.
- RE-03 (real vLLM/SGLang APC counters, H100) = L1/orchestrator-dispatched. FLAG, do not run.
- RE-04 (deployed-stack prevalence) = out-of-scope for this researcher.

## KEY LESSONS (carry from r4 + this incarnation)
- Launch researchers on Mac with BOTH: --dangerously-disable-osx-sandbox AND --dangerously-skip-permissions
  (+ --dangerously-enable-internet-mode for web prior-art). macOS sandbox_apply error without disable-osx-sandbox.
- Engine ALWAYS: /usr/bin/python3 /Users/dengcchi/research-os/engine/ros.py --instance /Users/dengcchi/autonomous-research <cmd>
- claude -p buffers to run-end -> empty boot log is NORMAL; verify via ros liveness + EXP run.log, not the launcher log.
- TOOLING correction: RE items REQUIRE real Rust tokenizers -> reuse EXP-0049/.venv (transformers 4.57.6,
  fast tokenizers). Analysis layer (BPE null, mult-comparison) is pure-stdlib. NOT stdlib-only overall.

## TIMELINE
- 2026-06-01 ~13:08Z — BOOT (provider 5xx interrupted the first boot turn AFTER it had already spawned the
  researcher). Re-registered sub-monitor-0005-r5 (session 59ac0b2e). Heartbeat #1 OK.
- 2026-06-01 ~13:09Z — VERIFIED via liveness: researcher-0014-L1prep-r5 ALREADY ALIVE (running, last=6.5m),
  spawned by the interrupted first turn (cc session 27535b3e). Prompt file (9311B, RE-01/02/05/06 + citations
  + re-frame, venv-based tooling) and log present. NO DUPLICATE SPAWN. Researcher registered EXP-0051, built
  impl, parsed corpora (335 sessions, 6409 seams: claude_code 4010 / codex 2399), tokenizing 3 cells
  (gpt2 done, qwen2-0.5b done, llama-3-128k in progress = RE-02 confound-breaker live). Healthy + on-task.
- Pool: 1/2 lanes live on PROJ-0005 (researcher-0014-L1prep-r5). 2nd floor slot HELD: the only other open
  PROJ-0005 work (RE-03 real-APC) is H100/orchestrator-dispatched, NOT mine to fill. Refilling a 2nd CPU lane
  now = make-work (no second independent CPU lane of open work exists). Hold at 1 until L1prep reports --next.
