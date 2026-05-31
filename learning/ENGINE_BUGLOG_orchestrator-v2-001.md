# Engine/Structure Bug Log — orchestrator-v2-001 (2026-05-31)
Running note of bugs/discrepancies hit while exercising the engine. Captured precisely per the
dual-mission directive. Reported to human via `ros report --blocked/--need`.

## BUG-1 (DOC/PATH) — prompts not in instance; task doc says `prompts/orchestrator/v001.md`
- Task & orchestrator instructions imply prompts live in the INSTANCE (registry/.../prompts...).
- ACTUAL: instance has no `prompts/` dir. Prompts live in the ENGINE repo:
  /Users/dengcchi/research-os/prompts/{orchestrator,session_agents,_shared,committee,monitors}.
- run_committee.sh confirms: it looks for `$INSTANCE/.research-os/prompts/committee` then falls back to
  `$(dirname run_committee.sh)/../prompts/committee`. The `.research-os/prompts` path does NOT exist either.
- IMPACT: low (fallback works) but the documented instance path is wrong/misleading. Severity: doc.

## BUG-2 (DATA INTEGRITY) — stale flat experiment paths inside claim/verdict YAML
- CLAIM-0006 supporting_evidence has `EXP-0003: data_path: experiments/EXP-0003/` (FLAT) and
  `EXP-0002: data_path: experiments/EXP-0002/` (FLAT).
- ACTUAL experiments are NESTED: experiments/2026-05-31/EXP-0003/, experiments/2026-05-31/EXP-0002/.
- Other entries in the SAME claim correctly use nested (experiments/2026-05-30/EXP-A006/).
- So back-links written by the engine are inconsistent: some flat, some nested. A consumer following
  data_path=experiments/EXP-0003/ gets a missing dir. Severity: medium (broken provenance link).

## BUG-3 (VALIDATION/PARITY) — verdict reviewer_votes vs config green_rule:unanimous(6 members)
- research-os.config.yaml committee.green_rule=unanimous with 6 members.
- VERDICT-0007 (CLAIM-0006, final=green) has reviewer_votes = [area_chair: green] ONLY (1 of 6).
- VERDICT-0006 (CLAIM-0005, final=yellow) has reviewer_votes = [area_chair: yellow] ONLY (1 of 6).
- The engine accepted/wrote `final_verdict: green` with a single non-unanimous vote, violating the
  configured green_rule. Either these were migrated stubs OR `ros verdict write` does NOT validate
  vote count against green_rule. Severity: HIGH if verdict write is the path that skipped validation —
  a GREEN can be recorded without committee parity. To be confirmed by exercising `ros verdict write`.

## BUG-4 (CROSS-PROJECT LEAK in report) — PROJ-0002 progress lists a PROJ-0001 claim
- projects/PROJ-0002/2026-05-31/progress_report.md lists CLAIM-0007 under PROJ-0002 ("PROVED").
- CLAIM-0007 actually has project_id: PROJ-0001 (registry/claims/PROJ-0001/.../CLAIM-0007.yaml).
- PROJ-0002 overview roster ALSO lists CLAIM-0007. So progress/overview generation mis-attributes a
  cross-project claim. Severity: medium (wrong project bookkeeping; violates Rule-2 separation in reports).

## BUG-5 (EXP METADATA) — registered experiments carry project_id PROJ-0000 and needs_gpu:true for CPU work
- EXP-0002, EXP-0003, EXP-0004 experiment.yaml all have project_id: PROJ-0000 (a placeholder; real
  project is PROJ-0002 via CLAIM-0006). `ros exp register` did not inherit project from the claim.
- Also needs_gpu: true is the DEFAULT even though these were CPU-only token-proxy runs (researchers
  noted this explicitly: "despite engine default tag"). hardware field left ''. Severity: medium
  (mis-tagged GPU-need could wrongly gate dispatch / pollute resource accounting).

## BUG-6 (CONCURRENCY) — .git/index.lock race between engine writes and manual git commit
- Symptom: `git add -A && git commit` intermittently fails with "Unable to create .git/index.lock:
  File exists" even with NO git process running (ps shows none). Lock self-clears within ~1-2s.
- Cause: `ros report`/`ros heartbeat`/etc. perform their own git staging/commit under .git/index.lock.
  A manual `git add` issued while an engine call is mid-write collides.
- IMPACT: orchestrator's mandated `git add -A && git commit` after milestones can fail spuriously and
  look like a hung/locked repo. Need: serialize engine git ops, or have engine retry-with-backoff, or
  document "engine owns git; do not run manual git concurrently". Severity: medium (operational footgun
  for the exact commit discipline the orchestrator prompt mandates).

## BUG-6 (CONCURRENCY) — .git/index.lock race between engine writes and manual git commit
- Symptom: `git add -A && git commit` intermittently fails with "Unable to create .git/index.lock:
  File exists" even with NO git process running (ps shows none). Lock self-clears within ~1-2s.
- Cause: `ros report`/`ros heartbeat`/etc. perform their own git staging/commit under .git/index.lock.
  A manual `git add` issued while an engine call is mid-write collides.
- IMPACT: orchestrator's mandated `git add -A && git commit` after milestones can fail spuriously and
  look like a hung/locked repo. Need: serialize engine git ops, or have engine retry-with-backoff, or
  document "engine owns git; do not run manual git concurrently". Severity: medium (operational footgun
  for the exact commit discipline the orchestrator prompt mandates).
