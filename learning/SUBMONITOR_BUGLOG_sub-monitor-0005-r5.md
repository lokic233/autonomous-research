# SUBMONITOR BUGLOG — sub-monitor-0005-r5 (PROJ-0005)

Project: PROJ-0005 — Tool-Result Re-Tokenization Boundary Churn (CLAIM-0014)
Spawned by: orchestrator-r5-001 (session 5b4e5cff-9888-48a1-bd41-61fdb5fe975d)
Successor to: sub-monitor-0005-r4 (DIED at context limit, no graceful handoff)
Session: 59ac0b2e-02e0-40b9-9fef-8b7614b47a2c
Node: cli:dengcchi-mac ONLY
Floor N = work-gated. Current open work = L1-prep RE items (RE-01/02/05/06 + citations + re-frame).

## KEY LESSONS (carried from r4)
- LAUNCH RESEARCHERS WITH BOTH dangerous flags on macOS:
  claude --dangerously-disable-osx-sandbox --dangerously-skip-permissions --dangerously-enable-internet-mode
  ...-p  (only --skip-permissions -> sandbox_apply: Operation not permitted DEATH).
- Engine ALWAYS: /usr/bin/python3 /Users/dengcchi/research-os/engine/ros.py --instance /Users/dengcchi/autonomous-research <cmd>
- Researchers: heredoc-direct file writes ONLY. FULL engine path. claude -p buffers to run-end -> empty boot log is NORMAL.
- NEVER convene committee / write verdict / seed claim / touch GPU. Escalate committee-ready via ros queue submit; hard blockers via ros report --need.

## STATE @ BOOT (verified via liveness, not narrative)
- CLAIM-0014: L0 cheap-kill EXP-0049 RAN (n_seams=6215, gate-a/b/c all PASS aggregate).
  Committee convened (committee_run_23) -> VERDICT-0055 = 6/6 YELLOW (held honestly, NOT promoted).
  Disposition: real-but-template-preventable(95% mitigation), tokenizer/corpus-dependent
  (gate-b aggregate-only, Qwen2~0/Codex<0), novelty=characterization-only.
- To ADVANCE: RE-01..RE-06 + mandatory citations (Gim Prompt Cache 2311.04934 MISSING,
  Don't-Break-the-Cache 2601.06007, Sennrich BPE ACL2016) + RE-FRAME title to regime-a-only.
- EXP-0049 impl present: experiments/2026-06-01/EXP-0049/impl/retokenization_churn.py (30KB),
  .venv has transformers+huggingface_hub (gpt2 + Qwen2-0.5B fast tokenizers). Reuse it.
- Researcher pool EMPTY (researcher-0014-L0-r4 completed+retired). sub-monitor-0005-r4 = DEAD/no-handoff
  (orchestrator's revive net; I am its successor — proceeding, not reviving r4).

## TIMELINE
