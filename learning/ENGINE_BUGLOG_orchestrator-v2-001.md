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

## BUG-3 CONFIRMED (HIGH) — `ros verdict write` does NOT validate votes against green_rule
- Source: /Users/dengcchi/research-os/engine/ros.py cmd_verdict_write (lines ~573 & ~610).
- The function builds reviewer_votes purely from the --votes string and writes final_verdict=args.final
  with NO check against config committee.green_rule (unanimous) or member count (6). It will happily
  record final_verdict:green with one vote, mismatched votes, or NO --votes at all.
- CONSEQUENCE: the "GREEN requires unanimous 6/6 committee" rule is convention only, unenforced by the
  engine. Explains VERDICT-0006/0007 having 1 reviewer_vote each. A buggy/lazy orchestrator can mint a
  GREEN with zero committee parity. Rule-1 (claim+verdict parity) is NOT machine-enforced.
- FIX SUGGESTION: in cmd_verdict_write, if final in {green,promote}: require len(votes)==len(config
  committee.members) and (green_rule==unanimous => all votes green); else exit nonzero. Also validate
  vote roles match configured member roles.

## BUG-8 (CODE) — cmd_verdict_write defined TWICE (verbatim duplicate)
- ros.py defines `def cmd_verdict_write(args)` at ~line 573 AND again identically at ~line 610.
- Python uses the SECOND; the first is dead code. Smells like a bad merge/paste. Severity: low-fn
  (harmless today) but a maintenance hazard — a fix applied to one copy won't take effect.

## BUG-9 (CODE) — `verdict` subparser registered TWICE in main()
- main() calls `sub.add_parser("verdict")` and wires the `write` subcommand TWICE (lines ~660 & ~667).
- Re-adding a subparser with the same name is fragile (argparse behavior); the second registration's
  args/defaults win. Same bad-merge signature as BUG-8. Severity: low but confirms duplicated block.

## BUG-7 (LIVENESS UX) — completed agents flagged "should revive" forever
- `ros liveness` lists prior-session agents (orchestrator-main-001, researcher-cdc-baselines-A,
  researcher-cdc-robustness-B) as "☠️ DEAD (past 45m grace — orchestrator should revive)" even though
  their WORK IS COMPLETE (they pinged done + their EXPs are completed). There is no `--status completed`
  retirement that removes them from the revive nudge. An orchestrator that obeys the nudge would
  RESPAWN finished work / duplicate completed lanes. Need a terminal/retired state honored by liveness.

## BUG-3 CONFIRMED (HIGH) — `ros verdict write` does NOT validate votes against green_rule
- Source: /Users/dengcchi/research-os/engine/ros.py cmd_verdict_write (lines ~573 & ~610).
- The function builds reviewer_votes purely from the --votes string and writes final_verdict=args.final
  with NO check against config committee.green_rule (unanimous) or member count (6). It will happily
  record final_verdict:green with one vote, mismatched votes, or NO --votes at all.
- CONSEQUENCE: the "GREEN requires unanimous 6/6 committee" rule is convention only, unenforced by the
  engine. Explains VERDICT-0006/0007 having 1 reviewer_vote each. A buggy/lazy orchestrator can mint a
  GREEN with zero committee parity. Rule-1 (claim+verdict parity) is NOT machine-enforced.
- FIX SUGGESTION: in cmd_verdict_write, if final in {green,promote}: require len(votes)==len(config
  committee.members) and (green_rule==unanimous => all votes green); else exit nonzero. Also validate
  vote roles match configured member roles.

## BUG-8 (CODE) — cmd_verdict_write defined TWICE (verbatim duplicate)
- ros.py defines `def cmd_verdict_write(args)` at ~line 573 AND again identically at ~line 610.
- Python uses the SECOND; the first is dead code. Smells like a bad merge/paste. Severity: low-fn
  (harmless today) but a maintenance hazard — a fix applied to one copy won't take effect.

## BUG-9 (CODE) — `verdict` subparser registered TWICE in main()
- main() calls `sub.add_parser("verdict")` and wires the `write` subcommand TWICE (lines ~660 & ~667).
- Re-adding a subparser with the same name is fragile (argparse behavior); the second registration's
  args/defaults win. Same bad-merge signature as BUG-8. Severity: low but confirms duplicated block.

## BUG-7 (LIVENESS UX) — completed agents flagged "should revive" forever
- `ros liveness` lists prior-session agents (orchestrator-main-001, researcher-cdc-baselines-A,
  researcher-cdc-robustness-B) as "☠️ DEAD (past 45m grace — orchestrator should revive)" even though
  their WORK IS COMPLETE (they pinged done + their EXPs are completed). There is no `--status completed`
  retirement that removes them from the revive nudge. An orchestrator that obeys the nudge would
  RESPAWN finished work / duplicate completed lanes. Need a terminal/retired state honored by liveness.

## BUG-5 CONFIRMED (independently, by researcher-cdc-workload-B)
- `ros exp register --level 0` (CPU-only) defaulted needs_gpu:true + max_gpu_hours:0.25 in EXP-0005.
- Researcher had to hand-edit the experiment.yaml to needs_gpu:false. Level-0 (and any --hardware cpu)
  should default needs_gpu:false / max_gpu_hours:0. Confirmed twice (EXP-0002/3/4 by prior session, now
  EXP-0005). Severity: medium (mis-tag pollutes GPU accounting + could wrongly gate dispatch).

## BUG-5 CONFIRMED (independently, by researcher-cdc-workload-B)
- `ros exp register --level 0` (CPU-only) defaulted needs_gpu:true + max_gpu_hours:0.25 in EXP-0005.
- Researcher had to hand-edit the experiment.yaml to needs_gpu:false. Level-0 (and any --hardware cpu)
  should default needs_gpu:false / max_gpu_hours:0. Confirmed twice (EXP-0002/3/4 by prior session, now
  EXP-0005). Severity: medium (mis-tag pollutes GPU accounting + could wrongly gate dispatch).

## BUG-10 (HIGH, DATA CORRUPTION) — torn write of runtime/agents/<id>.yaml; ros report then CRASHES
- Trigger: rapid `ros heartbeat` immediately followed by `ros report` on the same agent id (the exact
  ~every-2min discipline the orchestrator prompt mandates). The two commands BOTH read-modify-write
  runtime/agents/orchestrator-v2-001.yaml with no locking/atomic-rename/truncate.
- Result: file became (see learning/BUG-10_corrupted_*.yaml.evidence):
    line 7  note: awaiting EXP-0005 completion + priorart-A final ping; committee packet drafting
    line 8  iorart-A final ping; committee packet drafting        <- STRAY trailing bytes (no truncate)
    line 9  heartbeat_count: 12                                    <- DUPLICATE key
    line 10 last_report_ts: '2026-05-31T13:36:22Z'
  i.e. a shorter write was layered over a longer previous file's bytes (open('w') without truncate, OR
  two writers interleaved), producing invalid YAML with a duplicate mapping key.
- Then `ros report` crashes hard: cmd_report -> load_yaml -> yaml.safe_load raises on the torn file
  (Traceback at ros.py:490). The orchestrator's OWN state file becoming unparseable BREAKS its mandated
  reporting loop. Also note role got reset to 'unknown' (heartbeat writer doesn't preserve role).
- FIX: write runtime/agent files atomically (tmp + os.replace) and/or single-writer; load_yaml should be
  defensive (duplicate-key-tolerant / fall back to {} on parse error instead of crashing the whole CLI).
- Severity: HIGH — self-inflicted by the prescribed heartbeat+report cadence; corrupts agent liveness
  state and disables `ros report` until manually repaired.

## BUG-10 (HIGH, DATA CORRUPTION) — torn write of runtime/agents/<id>.yaml; ros report then CRASHES
- Trigger: rapid `ros heartbeat` immediately followed by `ros report` on the same agent id (the exact
  ~every-2min discipline the orchestrator prompt mandates). The two commands BOTH read-modify-write
  runtime/agents/orchestrator-v2-001.yaml with no locking/atomic-rename/truncate.
- Result: file became (see learning/BUG-10_corrupted_*.yaml.evidence):
    line 7  note: awaiting EXP-0005 completion + priorart-A final ping; committee packet drafting
    line 8  iorart-A final ping; committee packet drafting        <- STRAY trailing bytes (no truncate)
    line 9  heartbeat_count: 12                                    <- DUPLICATE key
    line 10 last_report_ts: '2026-05-31T13:36:22Z'
  i.e. a shorter write was layered over a longer previous file's bytes (open('w') without truncate, OR
  two writers interleaved), producing invalid YAML with a duplicate mapping key.
- Then `ros report` crashes hard: cmd_report -> load_yaml -> yaml.safe_load raises on the torn file
  (Traceback at ros.py:490). The orchestrator's OWN state file becoming unparseable BREAKS its mandated
  reporting loop. Also note role got reset to 'unknown' (heartbeat writer doesn't preserve role).
- FIX: write runtime/agent files atomically (tmp + os.replace) and/or single-writer; load_yaml should be
  defensive (duplicate-key-tolerant / fall back to {} on parse error instead of crashing the whole CLI).
- Severity: HIGH — self-inflicted by the prescribed heartbeat+report cadence; corrupts agent liveness
  state and disables `ros report` until manually repaired.

## BUG-11 (ENGINE GAP) — no `ros claim update`; Rule-1 claim edits require raw YAML writes
- Rule 1 + orchestrator prompt: "ANY claim that advances is written by YOU via `ros seed new` or by
  UPDATING the claim." But the CLI exposes only: seed{new}, verdict{write}, exp{register,complete,dispatch}.
  There is NO `ros claim update` / `ros claim set-status` / claim-edit path.
- So updating claim status/text/evidence/novelty_hypothesis (which the orchestrator MUST do constantly)
  means hand-editing registry YAML — exactly the unguarded read-modify-write that caused BUG-10 corruption.
- Consequence: the "engine owns the ledger" invariant is half-true: creation+verdict-append are engine ops,
  but the bulk of claim mutation is manual + unvalidated + non-atomic. Need a `ros claim update` with atomic
  write + schema validation. Severity: medium-high (forces unsafe manual edits of the core ledger).

## BUG-11 (ENGINE GAP) — no `ros claim update`; Rule-1 claim edits require raw YAML writes
- Rule 1 + orchestrator prompt: "ANY claim that advances is written by YOU via `ros seed new` or by
  UPDATING the claim." But the CLI exposes only: seed{new}, verdict{write}, exp{register,complete,dispatch}.
  There is NO `ros claim update` / `ros claim set-status` / claim-edit path.
- So updating claim status/text/evidence/novelty_hypothesis (which the orchestrator MUST do constantly)
  means hand-editing registry YAML — exactly the unguarded read-modify-write that caused BUG-10 corruption.
- Consequence: the "engine owns the ledger" invariant is half-true: creation+verdict-append are engine ops,
  but the bulk of claim mutation is manual + unvalidated + non-atomic. Need a `ros claim update` with atomic
  write + schema validation. Severity: medium-high (forces unsafe manual edits of the core ledger).

## BUG-12 (RUNNER GAP) — run_committee.sh cannot invoke the configured `metacode` backend
- research-os.config.yaml committee member product_realist uses backend `metacode` (a real distinct model).
- run_committee.sh run_one() case-matches only claude-*/opus*/sonnet*, codex*, gemini*. `metacode` falls to
  the default `*)` branch which runs `${COMMITTEE_GENERIC_CLI:-cat}` — i.e. by default it just `cat`s the
  prompt to the .out file (NO model invoked). So 1 of 6 committee votes would be a NO-OP echo, silently.
- Worse: it's SILENT — _status.txt still says ALL_COMMITTEE_DONE; product_realist.out would contain the
  packet text, not a vote, and a naive parser could miscount it.
- Also: `metacode` takes the message as an ARG (`metacode run "<msg>"`), not stdin, and is slow to start
  (>5s, needs a longer timeout) — the generic stdin `cat` shape wouldn't fit it even if wired.
- WORKAROUND THIS RUN: provide COMMITTEE_GENERIC_CLI=a wrapper that reads stdin and calls `metacode run --yolo`.
- FIX: add a `metacode*)` case to run_one() (metacode run --yolo "$full") + bump per-member timeout.
- Severity: HIGH (silent loss of a committee member => unanimous-GREEN rule can be met with only 5 real votes).

## BUG-12 (RUNNER GAP) — run_committee.sh cannot invoke the configured `metacode` backend
- research-os.config.yaml committee member product_realist uses backend `metacode` (a real distinct model).
- run_committee.sh run_one() case-matches only claude-*/opus*/sonnet*, codex*, gemini*. `metacode` falls to
  the default `*)` branch which runs `${COMMITTEE_GENERIC_CLI:-cat}` — i.e. by default it just `cat`s the
  prompt to the .out file (NO model invoked). So 1 of 6 committee votes would be a NO-OP echo, silently.
- Worse: it's SILENT — _status.txt still says ALL_COMMITTEE_DONE; product_realist.out would contain the
  packet text, not a vote, and a naive parser could miscount it.
- Also: `metacode` takes the message as an ARG (`metacode run "<msg>"`), not stdin, and is slow to start
  (>5s, needs a longer timeout) — the generic stdin `cat` shape wouldn't fit it even if wired.
- WORKAROUND THIS RUN: provide COMMITTEE_GENERIC_CLI=a wrapper that reads stdin and calls `metacode run --yolo`.
- FIX: add a `metacode*)` case to run_one() (metacode run --yolo "$full") + bump per-member timeout.
- Severity: HIGH (silent loss of a committee member => unanimous-GREEN rule can be met with only 5 real votes).

## BUG-13 (HIGH, BLOCKER) — run_committee.sh DOES NOT RUN on this control node (macOS)
- launch.log: `run_committee.sh: line 19: mapfile: command not found` then `line 47: MEMBERS[@]: unbound
  variable` then a `ModuleNotFoundError: No module named 'yaml'`.
- ROOT CAUSE A: macOS default /bin/bash is 3.2 (GPL2 era); `mapfile` (readarray) is Bash 4+. The member
  list is never populated -> `set -u` makes MEMBERS[@] an unbound-variable fatal -> ZERO committee members
  run. NO .out files, NO _status.txt. SILENT-ish (only in launch.log).
- ROOT CAUSE B: the heredoc reads members via bare `python3` (line ~20). On this node only
  /usr/bin/python3 has pyyaml; bare `python3` -> first PATH python WITHOUT pyyaml -> import error.
- IMPACT: the committee literally cannot convene via the provided runner on the configured control_node
  (cli:dengcchi-mac). This blocks every GREEN/verdict that requires committee parity. Severity: HIGH blocker.
- FIX: (1) shebang `#!/usr/bin/env bash` AND require bash>=4 (brew bash) OR replace `mapfile` with a
  while-read loop (Bash 3.2 safe). (2) use `${PYTHON:-/usr/bin/python3}` not bare `python3`, document the
  pyyaml requirement. (3) since members run with `&` + `wait` but MEMBERS empty, also guard empty-member case.
- WORKAROUND THIS RUN: orchestrator ran a Bash-3.2-safe corrected launcher using /usr/bin/python3 to read
  members + invoking the 4 backend CLIs directly (claude/codex/gemini/metacode-wrapper), same prompts dir.

## BUG-13 (HIGH, BLOCKER) — run_committee.sh DOES NOT RUN on this control node (macOS)
- launch.log: `run_committee.sh: line 19: mapfile: command not found` then `line 47: MEMBERS[@]: unbound
  variable` then a `ModuleNotFoundError: No module named 'yaml'`.
- ROOT CAUSE A: macOS default /bin/bash is 3.2 (GPL2 era); `mapfile` (readarray) is Bash 4+. The member
  list is never populated -> `set -u` makes MEMBERS[@] an unbound-variable fatal -> ZERO committee members
  run. NO .out files, NO _status.txt. SILENT-ish (only in launch.log).
- ROOT CAUSE B: the heredoc reads members via bare `python3` (line ~20). On this node only
  /usr/bin/python3 has pyyaml; bare `python3` -> first PATH python WITHOUT pyyaml -> import error.
- IMPACT: the committee literally cannot convene via the provided runner on the configured control_node
  (cli:dengcchi-mac). This blocks every GREEN/verdict that requires committee parity. Severity: HIGH blocker.
- FIX: (1) shebang `#!/usr/bin/env bash` AND require bash>=4 (brew bash) OR replace `mapfile` with a
  while-read loop (Bash 3.2 safe). (2) use `${PYTHON:-/usr/bin/python3}` not bare `python3`, document the
  pyyaml requirement. (3) since members run with `&` + `wait` but MEMBERS empty, also guard empty-member case.
- WORKAROUND THIS RUN: orchestrator ran a Bash-3.2-safe corrected launcher using /usr/bin/python3 to read
  members + invoking the 4 backend CLIs directly (claude/codex/gemini/metacode-wrapper), same prompts dir.

## ============ RESOLUTIONS (engine commit research-os@1be8366) ============
- BUG-3 (HIGH) FIXED: ros verdict write now enforces green_rule (green/promote need all 6 votes, unanimous=>all green). Validated.
- BUG-5 FIXED: exp register defaults CPU (no needs_gpu unless --gpu or gpu-hours>0); inherits project_id from claim; hardware=cpu. Validated.
- BUG-7 FIXED: liveness retires completed/failed agents (🏁), no longer nags revival. Validated.
- BUG-8/9 FIXED: removed all duplicate function defs + duplicate main() subparser block (AST dedup).
- BUG-2 (data integrity, stale flat exp paths in CLAIM-0006): TODO — needs a one-time registry repair pass on existing claim back-links (flat experiments/EXP-x -> nested experiments/<date>/EXP-x).
- BUG-4 (PROJ-0002 progress mis-lists PROJ-0001 CLAIM-0007): TODO — project_overview/progress generation must filter by project_id strictly.
- BUG-6 (git index.lock race): MITIGATED conceptually (engine should own git / retry-with-backoff); not yet coded. Operational: don't run manual git concurrent with engine.
- BUG-1 (prompts path doc): doc-only; engine run_committee fallback works.

## ============ RESOLUTIONS (engine commit research-os@1be8366) ============
- BUG-3 (HIGH) FIXED: ros verdict write now enforces green_rule (green/promote need all 6 votes, unanimous=>all green). Validated.
- BUG-5 FIXED: exp register defaults CPU (no needs_gpu unless --gpu or gpu-hours>0); inherits project_id from claim; hardware=cpu. Validated.
- BUG-7 FIXED: liveness retires completed/failed agents (🏁), no longer nags revival. Validated.
- BUG-8/9 FIXED: removed all duplicate function defs + duplicate main() subparser block (AST dedup).
- BUG-2 (data integrity, stale flat exp paths in CLAIM-0006): TODO — needs a one-time registry repair pass on existing claim back-links (flat experiments/EXP-x -> nested experiments/<date>/EXP-x).
- BUG-4 (PROJ-0002 progress mis-lists PROJ-0001 CLAIM-0007): TODO — project_overview/progress generation must filter by project_id strictly.
- BUG-6 (git index.lock race): MITIGATED conceptually (engine should own git / retry-with-backoff); not yet coded. Operational: don't run manual git concurrent with engine.
- BUG-1 (prompts path doc): doc-only; engine run_committee fallback works.

## BUG-14 (ENGINE GAP) — `ros verdict write` cannot capture committee detail (fatal_objections/required_evidence/map_delta/baselines)
- `ros verdict write` flags = --claim --final --experiments --votes --committee-version --date only.
- It hardcodes fatal_objections=[], required_evidence=[], map_delta_proposals=[], baseline_requirements=[]
  (empty). So the substantive committee output (the WHOLE point of the review) cannot be recorded via the
  engine — it requires a manual YAML edit afterward (which then hits the BUG-6/tmp-race fragility).
- FIX: add --fatal/--required/--map-delta/--baselines flags OR accept a --from-out <committee_out_dir> that
  parses the role .out files. Severity: medium (verdicts are recorded but hollow without manual enrichment).

## NOTE re BUG-6 family — atomic-write .tmp disappears mid os.replace
- My own atomic writes (tmp + os.replace) intermittently FileNotFoundError on the .tmp during replace, even
  though the replace SUCCEEDS (target ends up correct). Implies a concurrent watcher/process (engine git add,
  or an editor/indexer) removes *.tmp under the registry. Reinforces BUG-6: something races file ops in this
  repo. Workaround: write tmp OUTSIDE the repo (e.g. /tmp) then os.replace in, or tolerate the post-replace error.

## BUG-14 (ENGINE GAP) — `ros verdict write` cannot capture committee detail (fatal_objections/required_evidence/map_delta/baselines)
- `ros verdict write` flags = --claim --final --experiments --votes --committee-version --date only.
- It hardcodes fatal_objections=[], required_evidence=[], map_delta_proposals=[], baseline_requirements=[]
  (empty). So the substantive committee output (the WHOLE point of the review) cannot be recorded via the
  engine — it requires a manual YAML edit afterward (which then hits the BUG-6/tmp-race fragility).
- FIX: add --fatal/--required/--map-delta/--baselines flags OR accept a --from-out <committee_out_dir> that
  parses the role .out files. Severity: medium (verdicts are recorded but hollow without manual enrichment).

## NOTE re BUG-6 family — atomic-write .tmp disappears mid os.replace
- My own atomic writes (tmp + os.replace) intermittently FileNotFoundError on the .tmp during replace, even
  though the replace SUCCEEDS (target ends up correct). Implies a concurrent watcher/process (engine git add,
  or an editor/indexer) removes *.tmp under the registry. Reinforces BUG-6: something races file ops in this
  repo. Workaround: write tmp OUTSIDE the repo (e.g. /tmp) then os.replace in, or tolerate the post-replace error.

## VERIFICATION (engine research-os@4a610ee, by orchestrator-v2-001)
- BUG-13 FIXED ✓: shipped run_committee.sh now runs ALL 6 members on macOS Bash 3.2 (smoke test:
  ALL_COMMITTEE_DONE, "members: 6", no mapfile/unbound-variable/pyyaml errors).
- BUG-12 FIXED ✓: metacode backend (product_realist) is now actually invoked by the shipped runner and
  returned a real structured vote (not a `cat` no-op). New EMPTY_OUTPUT_NO_VOTE err-flag present for the
  zero-output case (didn't trigger here since all 6 voted).
- BUG-3 FIXED ✓: `ros verdict write --final green --votes area_chair:green` (1 of 6) is now REJECTED:
  "green_rule=unanimous: green needs all 6 committee votes via --votes; got 1. (use --override-rule ...)".
  Committee parity is now machine-enforced for green/promote.
- BUG-14 FIXED ✓: `ros verdict write` now has --fatal/--required/--map-delta/--baselines (';'-sep).
- NEW: `ros resume` lists in-flight claims + next_action; `ros claim advance --state <vocab> --next ...`
  maintains the resume pointer. lifecycle states: blocked/committee_pending/done/drafted/evidence_ready/
  experiment_designing/experiment_running/prior_art_pending/verdict_recorded.

## VERIFICATION (engine research-os@4a610ee, by orchestrator-v2-001)
- BUG-13 FIXED ✓: shipped run_committee.sh now runs ALL 6 members on macOS Bash 3.2 (smoke test:
  ALL_COMMITTEE_DONE, "members: 6", no mapfile/unbound-variable/pyyaml errors).
- BUG-12 FIXED ✓: metacode backend (product_realist) is now actually invoked by the shipped runner and
  returned a real structured vote (not a `cat` no-op). New EMPTY_OUTPUT_NO_VOTE err-flag present for the
  zero-output case (didn't trigger here since all 6 voted).
- BUG-3 FIXED ✓: `ros verdict write --final green --votes area_chair:green` (1 of 6) is now REJECTED:
  "green_rule=unanimous: green needs all 6 committee votes via --votes; got 1. (use --override-rule ...)".
  Committee parity is now machine-enforced for green/promote.
- BUG-14 FIXED ✓: `ros verdict write` now has --fatal/--required/--map-delta/--baselines (';'-sep).
- NEW: `ros resume` lists in-flight claims + next_action; `ros claim advance --state <vocab> --next ...`
  maintains the resume pointer. lifecycle states: blocked/committee_pending/done/drafted/evidence_ready/
  experiment_designing/experiment_running/prior_art_pending/verdict_recorded.

## BUG-10 STILL OPEN after engine 4a610ee (regression-survivor)
- The 4a610ee update fixed BUG-3/12/13/14 but NOT BUG-10. runtime/agents/<id>.yaml still torn-writes on the
  heartbeat->report race; `ros report` still crashes with a yaml parse traceback when it does; role still
  reset to 'unknown' by the heartbeat writer. Recurred + manually repaired again this session.
- Still needs: atomic write (tmp + os.replace) for runtime/agents + parse-tolerant load_yaml + role preserved
  by heartbeat. HIGH because it's triggered by the prescribed heartbeat+report cadence.

## BUG-10 STILL OPEN after engine 4a610ee (regression-survivor)
- The 4a610ee update fixed BUG-3/12/13/14 but NOT BUG-10. runtime/agents/<id>.yaml still torn-writes on the
  heartbeat->report race; `ros report` still crashes with a yaml parse traceback when it does; role still
  reset to 'unknown' by the heartbeat writer. Recurred + manually repaired again this session.
- Still needs: atomic write (tmp + os.replace) for runtime/agents + parse-tolerant load_yaml + role preserved
  by heartbeat. HIGH because it's triggered by the prescribed heartbeat+report cadence.
