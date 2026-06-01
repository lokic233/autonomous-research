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

- 2026-06-01 ~13:18Z — researcher-0014-L1prep-r5 SELF-COMPLETED (terminal report, committed b6c521c).
  EXP-0051 delivered the full CPU-doable RE subset for VERDICT-0055:
    RE-01 BPE null = HONEST PARTIAL-KILL (seam churn 0.0116 < generic-BPE null 0.0517; delta -0.040
      95%CI[-0.0414,-0.0386] NEGATIVE all 6 cells -> 'excess churn over BPE' novelty FALSIFIED).
    RE-02 3x2 grid + Llama-3-128k -> CORPUS-bound (all Codex cells ~0/reversed), confound broken.
    RE-05 Holm+BH (18 tests): gate-a 6/6, gate-c 6/6, gate-b 3/6 (claude_code only = corpus-collapse).
    RE-06 block{8,16,32} monotone 0.0110/0.0116/0.0129, ~99% blocks survive.
    Chat-template control = 95.8% mitigation. Citations added (Gim 2311.04934, DBTC 2601.06007,
    Sennrich ACL2016) -> PRIOR_ART_ADEQUATE closed. Title re-framed to regime-(a)-only.
  Researcher --next = COMMITTEE-READY (recommend RETAIN yellow, do NOT promote). CPU lane EXHAUSTED.
- 2026-06-01 ~13:18Z — DUTY(b): ros queue submit -> Q-0004 (CLAIM-0014, exps EXP-0049,EXP-0051,
  kind=committee, by sub-monitor-0005-r5, researcher researcher-0014-L1prep-r5). Forwarded WITHOUT judging.
- 2026-06-01 ~13:18Z — NO-REFILL DECISION (work-gated floor): researcher reports CPU lane EXHAUSTED;
  the only remaining PROJ-0005 open work is RE-03 (H100/orchestrator-dispatched) + RE-04 (orchestrator).
  No 2nd CPU lane of open work exists -> correctly SIT BELOW floor (1->0 live as lane completes). Refilling
  = make-work. Re-check open_gaps / advanceable claims each cycle; refill only if orchestrator's committee
  re-convene opens a new CPU follow-on. Pool now 0/2 live with NO open CPU work = correct quiescent state.

- 2026-06-01 ~13:24Z — CYCLE (no change). researcher-0014-L1prep-r5 = completed/retired (clean, no zombie).
  Q-0004 still PENDING in committee-queue (orchestrator has not re-convened yet). No new VERDICT-0005x.
  ros resume: CLAIM-0014 = evidence_ready / status=weakened -> packet staged, awaiting ORCHESTRATOR committee,
  not awaiting me. No open CPU follow-on. Correctly holding pool below floor (no make-work). RE-03/RE-04 remain
  orchestrator/H100 out-of-scope. Heartbeat #3. Quiescent-correct.

- 2026-06-01 ~13:29Z — CYCLE (no change). Q-0004 still PENDING (no re-convene). CLAIM-0014 evidence_ready/
  weakened. No new verdict, no open CPU work. Pool quiescent-correct (below floor by design). Heartbeat #4.

- 2026-06-01 ~13:34Z — CYCLE (no change). Q-0004 still PENDING (orchestrator not re-convened). CLAIM-0014
  evidence_ready/weakened. No new verdict/CPU work. Pool quiescent-correct. Heartbeat #5.

- 2026-06-01 ~13:39Z — CYCLE (no change). Q-0004 PENDING ~20m (orchestrator re-convene = orchestrator
  authority, not poked by me). CLAIM-0014 evidence_ready/weakened. No new CPU work. Quiescent-correct. Heartbeat #6.

- 2026-06-01 ~13:44Z — CYCLE (no change). Q-0004 PENDING. CLAIM-0014 evidence_ready/weakened. No new CPU
  work. Quiescent-correct. Heartbeat #7.

- 2026-06-01 ~13:49Z — CYCLE (no change). Q-0004 PENDING ~30m. CLAIM-0014 evidence_ready/weakened. No new
  CPU work. Quiescent-correct. Heartbeat #8.

- 2026-06-01 ~13:54Z — CYCLE (no change). Q-0004 PENDING ~35m. CLAIM-0014 evidence_ready/weakened. No new
  CPU work. Quiescent-correct. Heartbeat #9. Context budget healthy (well below 35% retire threshold).

- 2026-06-01 ~13:59Z — CYCLE (no change). Q-0004 PENDING ~40m. CLAIM-0014 evidence_ready/weakened. No new
  CPU work. Quiescent-correct. Heartbeat #10.

- 2026-06-01 ~14:03Z — STATE CHANGE: orchestrator picked up Q-0004 + RE-CONVENED committee. Q-0004 gone from
  queue; VERDICT-0057 recorded. CLAIM-0014 now verdict_recorded / weakened.
  VERDICT-0057 = 4 yellow / 2 red -> final YELLOW, CHARACTERIZED / DO-NOT-PROMOTE (zero reviewers recommend
  promotion). UNANIMOUS findings driven by my forwarded RE packet (EXP-0051):
    · RE-01 BPE null FALSIFIES excess-over-baseline novelty (seam churn 0.0116 < null 0.0517, neg 6/6 cells).
    · RE-02 collapses tokenizer-general law (corpus x tokenizer confound) -> NO economic case for RE-03.
    · RE-03/RE-04 (H100/L1) explicitly NOT DISPATCHED -> L1 GPU spend BLOCKED.
    · Revival would require a fundamentally different regime.
  OUTCOME: CLAIM-0014 terminal (bounded-characterization yellow, do-not-promote). PROJ-0005 CPU work EXHAUSTED;
  L1 blocked. NO refill (no open work — correct quiescent end-state). DUTY(b) packet did its job: honest
  re-convene reached, GPU spend correctly blocked. Heartbeat #11.

- 2026-06-01 ~14:09Z — STANDBY CYCLE (terminal-confirmed). No PROJ-0005 queue items, no new verdict, no open
  gaps; CLAIM-0014 = verdict_recorded/weakened (closed). Refreshed recurring loop message to closed-end-state
  (schedule_message_freshness required) — now standby-only: act only on NEW gap/revival/follow-on CPU lane.
  Pool 0 = correct. Heartbeat #12. Context healthy.

- 2026-06-01 ~14:14Z — STANDBY (no change). CLAIM-0014 closed/verdict_recorded; no queue/verdict/gap. Pool 0 = correct. Heartbeat #14.

- 2026-06-01 ~14:19Z — STANDBY (no change). CLAIM-0014 closed; no queue/verdict/gap. Pool 0 = correct. Heartbeat #15.
