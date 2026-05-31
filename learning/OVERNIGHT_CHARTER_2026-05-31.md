# Overnight Autonomous Charter — 2026-05-31 (observer/driver: Navi)
User asleep. Run the bugbash + research seriously until the bar is met. Be truthful; never fabricate.

## THE BAR (what "done well" means)
1. Every advancing claim is EXPERIMENT-DRIVEN: a verdict exists ONLY with cited experiment(s) (ros enforces).
2. ALL prior_art current per project (related_work/oss_community/needs_attention) + academic_map merged from
   committee map-deltas (Rule 3). No stale map nodes.
3. Researchers run in PARALLEL, each locked to ONE project (Rule 2), each early-killing over-explored ideas.
4. Committee verdicts are REAL: 6/6 non-empty votes (check _status.txt = ALL_COMMITTEE_DONE, not INCOMPLETE;
   green_rule enforced). Never a fabricated or partial-counted verdict.
5. Engine bugs found get FIXED (surgical, validated, committed) — keep the buglog current.

## SAFETY (non-negotiable)
- NEVER fabricate a vote/verdict. Partial committee => COMMITTEE_INCOMPLETE => re-run, don't count.
- GPU only via ros exp dispatch + host-mem-floor watchdog. devgpu499 (MI350X) fragile — never dispatch GPU
  there without floor. Read learning/ before any GPU probe. Default CPU-only Level-0/1.
- Atomic writes (BUG-10), idempotent verdicts (BUG-18) already in. Keep pushes on HTTPS remote (port 22 blocked).
- If a hard blocker needs the human (CLI infra down, GPU node down, ambiguous research call): FLAG and PARK,
  don't thrash. Nothing is lost — ros resume picks up state.

## CURRENT IN-FLIGHT (resume targets)
- CLAIM-0006 (PROJ-0002): VERDICT-0017 6/6 YELLOW valid. GREEN-path = CPU prior-art body-distinction
  (2601.06007/Irminsul) OR GPU wall-clock PIC [needs human-go]. Do the CPU prior-art leg overnight.
- CLAIM-0008 (PROJ-0003): weakened; surviving = recovery-MODALITY reframe (a NEW claim). Re-seed + design.
- CLAIM-0005 (PROJ-0001): YELLOW sub-quadratic; needs 3rd-engine evidence.
