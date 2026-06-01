# SUBMONITOR BUGLOG — sub-monitor-0006-r6
Project: PROJ-0006 ("Agent-Event-Phase Desynchronization Tax in Batch Speculative Decoding")
Spawned by: orchestrator-r6-001 (session cbed2b7c-cc39-46fb-9dba-24cc9ab9aeff)
Session: 3cc62589-6c7d-4f14-84cc-eae5fef0645b
Node: cli:dengcchi-mac ONLY
Floor N = researcher pool (work-gated; only ONE genuine open CPU lane = EXP-0052 L0)

## STATE INHERITED (verified via liveness/registry, not narrative)
- PROJ-0006 = FRESH. First claim CLAIM-0016, seeded yellow VERDICT-0059 (design committee 6/6 reseed-with-fixes).
- L0 gating exp = EXP-0052 (CPU-only, registered, status=pending, linked VERDICT-0059). impl/ was MISSING -> created.
- EXP-0046 acceptance proxy present: results/acceptance_proxy.json (7486B) + impl/acceptance_proxy.py. REUSE.
- Corpora present: ~/.codex/sessions, ~/.claude/projects, ~/.gemini (bonus). >=2 satisfied.
- DEAD-0011 + DEAD-0012 (PROJ-0004 cemetery) = the SAME single-seq dAUC discriminator falsified TWICE on the
  SAME EXP-0046 proxy. PROJ-0006 novelty = CROSS-seq batch-COMPOSITION (legs a+c), NOT that dead discriminator.
- Pool EMPTY at boot (no researcher-0016 in liveness) = fresh, confirmed.

## KEY LESSONS (carried from sub-monitor-0004/0005 buglogs)
- macOS SPAWN: BOTH --dangerously-disable-osx-sandbox AND --dangerously-skip-permissions REQUIRED (one alone =>
  sandbox_apply: Operation not permitted + death). + --dangerously-enable-internet-mode (prior-art web verify),
  + --add-dir for BOTH /Users/dengcchi/autonomous-research and /Users/dengcchi/research-os, + --model claude-opus-4-8.
- claude -p buffers stdout to run-end -> empty/sparse boot log is NORMAL. Verify via ros liveness + EXP run.log,
  NOT the launcher log.
- Engine ALWAYS: /usr/bin/python3 /Users/dengcchi/research-os/engine/ros.py --instance /Users/dengcchi/autonomous-research <cmd>
- Researcher file-writes: bash heredoc only; NEVER navi file-transfer (401s); stdlib-only at /usr/bin/python3.

## TIMELINE
- 2026-06-01 ~09:00Z — BOOT. Read sub-monitor.md + project_overview.md IN FULL. Registered sub-monitor-0006-r6
  (session 3cc62589), heartbeat #1 OK. liveness: PROJ-0006 pool EMPTY (fresh). Verified EXP-0052 registered/pending,
  EXP-0046 proxy assets present, DEAD-0011/0012 present, CLAIM-0016 + VERDICT-0059 present. Created EXP-0052/impl/
  + prior_art/PROJ-0006/.
- 2026-06-01 ~09:03Z — Wrote durable prompt runtime/researcher-0016-L0-r6_prompt.md (119L): all 7 RE gates
  RE-A1..A7 baked into a timestamped preregistration mandate; RE-A1 flagged LOAD-BEARING/KILLER (phase-composition
  MUST beat STATIC-TASK-TYPE GROUPING baseline, 95% LB>0); RE-A3 >=5% tax floor; sham-cluster (A2), within-session
  within-position perm null (A4), Holm/BH multiplicity (A5), scheduler overhead net>0 (A6), DEAD-0011/0012 cite (A7);
  COMPOSITION+RECOVERY framing (predictor = grouping mechanism only, NOT standalone dAUC); KILL rule pre-registered;
  TETRIS/ECHO/Batch-SD-Done-Right/Semi-Clairvoyant non-collision; heredoc/stdlib-only/reuse-EXP-0046 rules;
  self-complete contract with committee-ready definition (positive OR honest kill both terminal).
  SPAWN researcher-0016-L0-r6 via claude -p with BOTH mandatory macOS flags + internet-mode + both --add-dir +
  --model claude-opus-4-8. Process ALIVE (RSS growing, sandbox disabled cleanly, NO sandbox_apply error,
  AI Gateway/Vertex up). Floor=work-gated: 1 spawned on the ONLY genuine open CPU lane (EXP-0052). No 2nd CPU lane
  of open work exists (L1 vLLM telemetry = H100/orchestrator-dispatched) -> correctly NOT refilling a 2nd slot.
  No committee-ready evidence yet -> no queue submit.

- 2026-06-01 ~16:20Z — CYCLE#2. heartbeat #2 OK. researcher-0016-L0-r6 = 💓 RUNNING (last=0.0m, last report 16:16Z).
  HEALTHY + ON-TASK (claude -p mid-run, NOT a stall). Verified progress (not narrative):
  · preregistration.md LOCKED 2026-06-01T16:07:18Z BEFORE run (RE-A1..A7 exact rules, reconciled = VERDICT-0059
    required_evidence union). Pre-reg gate satisfied. Scope-guard section 0 explicitly cites DEAD-0011 + DEAD-0012
    (RE-A7) and forbids resurrecting the single-seq dAUC discriminator; success measured ONLY as cross-seq min-bound
    goodput recovery. Gemini EXCLUDED (no tool_result injection structure) — CC+Codex satisfy >=2 corpora.
  · batch_round_model.py built+smoke-tested (reuses EXP-0046 cc_streams/codex_streams + trigram predictor).
  · results/batch_round_model.json = PRELIMINARY: RE-A1 delta1(phase MINUS static-task-grouping) ~0, p~0.45-0.53,
    95% CI STRADDLES 0 in visible cells (B4_g4 CI[-0.0011,+0.0009]; B8_g4 CI[-0.0003,+0.0005]) -> KILL TRENDING on
    the load-bearing gate. Structural cause (researcher-reported): ~97.5% tokens FREE_FORM (transition+resumption
    <3% combined); between-session difficulty std 0.088-0.104 DWARFS phase deviations -> phase grouping adds nothing
    over static difficulty grouping. Min-bound goodput ~0 at B>=4 (proxy acc ~0.28).
  · Researcher correctly adding a CLEARLY-LABELED EXPLORATORY regime-sweep (lift alpha_base to resolvable regime,
    preserve real difficulty spread + phase deviations + phase mix) to test KILL ROBUST vs INSTRUMENT-LIMITED before
    completing full B_boot=2000/n_perm=1000. Honest-science move, NOT a forced positive. Good.
  STATUS = running (NOT terminal). NO queue submit (forward only on status=completed). Floor=1 held (EXP-0052 is the
  only open CPU lane; L1 vLLM/H100 telemetry = orchestrator-dispatched). No make-work refill. No blocker to escalate.

- 2026-06-01 ~16:26Z — CYCLE#3. heartbeat #3 OK. researcher-0016-L0-r6 = 💓 RUNNING (last=4.5m within 15m kick,
  last report 16:21Z). HEALTHY mid-run (full B_boot=2000/n_perm=1000 on CC bootstrap; regime sweep queued).
  PROGRESS verified:
  · PRIOR-ART (RE-A7 + non-collision) DONE, arXiv ids body-verified, written to
    prior_art/PROJ-0006/validated_autonomous_researcher_exps.md with DEAD-0011/0012 citations + scope statement:
      - TETRIS=2502.15197 (ACL2025, in-batch token SELECTION) = NON-COLLIDE.
      - Batch-SD-Done-Right=2510.22876 (EqSpec correctness + EXSpec "dynamically groups same-length sequences")
        = CLOSEST / MEDIUM — generic grouping lever PARTIALLY prior-occupied by LENGTH (not phase).
      - Semi-Clairvoyant=2505.17074 (IJCAI2025 LAPS-SD, request ordering by acceptance features for latency) = MEDIUM.
      - ECHO=2604.09603 (batch super-tree depth/width budget gating) = LOW (future-date flagged).
      Researcher judgement: NO prior does phase-aligned batch COMPOSITION, but the generic similar-acceptance/length
      grouping lever is PARTIALLY prior-occupied. (Committee will weigh this — NOT my call to judge.)
  · EXP-0052 still status=pending (full run + regime sweep executing; run_full.log present). NOT terminal.
  STATUS = running. NO queue submit (forward only on status=completed). Floor=1 held (only open CPU lane; L1=H100/
  orchestrator). No make-work refill. No blocker to escalate. RE-A1 kill-trend unchanged from cycle#2 (awaiting full).

- 2026-06-01 ~16:31Z — CYCLE#4. heartbeat #4 OK. researcher-0016-L0-r6 = 💓 RUNNING (last=4.8m within 15m kick,
  last report 16:21Z). HEALTHY: full run COMPLETED both corpora (run_full.log: claude_code 363.3s, codex 465.4s,
  CC 83 usable / Codex 85 usable sessions) -> now in EXPLORATORY regime-sweep phase. ~14min report gap = heavy
  compute (828s bootstrap + sweep), normal for claude -p buffering. EXP-0052 still status=pending (no ros exp
  complete, no --status completed) = NOT terminal.
  REAL-PROXY RESULTS now complete across ALL 16 cells (2 corpora x B{4,8,16,32} x gamma{4,8}). RE-A1 KILLER
  delta1(phase MINUS static-task-grouping): 95% CI STRADDLES 0 in EVERY cell, NO cell LB>0, p=0.41-1.00. CC range
  delta1 -0.00016..+0.00076; Codex -0.00041..+0.00148, all CI include 0. => clean consistent HONEST-NEGATIVE on the
  load-bearing gate in the real-proxy regime (= project's pre-registered kill pathway: "phase adds nothing over
  per-task difficulty clustering"). NOTE: tax~0.99-1.00 (>>5% floor) but that is the degenerate min-bound collapse
  at proxy acc~0.28 -> hence the researcher's EXPLORATORY regime-sweep to test KILL ROBUST vs INSTRUMENT-LIMITED.
  That robust-vs-instrument distinction is the RESEARCHER's to resolve + COMMITTEE's to judge — I do NOT adjudicate.
  STATUS = running. NO queue submit (forward only on status=completed; awaiting sweep + analysis.md + exp complete).
  Floor=1 held (only open CPU lane; L1=H100/orchestrator). No make-work refill. No blocker. RE-A1 trend now FULLY
  RESOLVED in real-proxy (null); terminal pending the exploratory robustness check + self-complete.
