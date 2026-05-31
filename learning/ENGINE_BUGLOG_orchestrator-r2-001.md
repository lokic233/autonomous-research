# ENGINE BUGLOG — orchestrator-r2-001 (ROUND 2)
Engine: research-os@4a610ee. Instance: /Users/dengcchi/autonomous-research. Control node: cli:dengcchi-mac.
Bug numbering continues from round-1 (last was BUG-14). New bugs start at BUG-15.

## TODO-BUG RE-TESTS (round-1 carryover)

### BUG-2 (stale flat exp paths in claim back-links) — STATUS: CLOSED ✓
- Test: grep all registry/claims for `experiments/EXP-*` (flat) + verify every data_path/artifacts
  back-link resolves to an existing nested dir.
- Result: 0 flat paths; 17/17 back-link paths resolve to existing experiments/<date>/EXP-*/ dirs.
- CLAIM-0006 specifically now uses experiments/2026-05-31/EXP-0003/ etc. (the round-1 offender).
- Verdict: data was repaired; BUG-2 closed for current registry.

### BUG-4 (cross-project leak in progress/overview) — STATUS: ALIVE (data) + ENGINE-GAP
- Test: list CLAIM-* mentioned in each project's progress_report.md vs each claim's project_id.
- Result: projects/PROJ-0002/2026-05-31/progress_report.md lists **CLAIM-0007 under "PROVED"**, but
  CLAIM-0007.project_id = PROJ-0001 (GPU-MMU Write-After-Share — a PROJ-0001 topic). LEAK CONFIRMED.
- Root cause: progress_report.md / project_overview.md are AGENT-AUTHORED markdown. The engine
  (`cmd_projects`, ros.py ~L489) only reads the H1 title + report dates; it has NO generator and NO
  validator that filters claims by project_id. So nothing prevents or detects a cross-project claim
  reference in a project report.
- Expected: engine should offer a `ros projects --validate` (or report generator) that flags claims
  cited in a project doc whose project_id != that project. Actual: no such tooling; leak persists silently.
- Fix options: (a) add project_id-filtered claim listing to a report generator; (b) add a lint that
  scans project docs for CLAIM-ids and asserts project membership.
- Action taken this run: correcting the stale PROJ-0002 report (Rule-3 data hygiene); logging engine gap.

### BUG-1 (prompts path doc) — STATUS: PARTIAL (fallback works; instance path absent)
- run_committee.sh resolves committee prompts at `$INSTANCE/.research-os/prompts/committee` first,
  else fallback `$(dirname run_committee.sh)/../prompts/committee`.
- Actual: instance path .research-os/prompts/committee does NOT exist; only the engine fallback
  /Users/dengcchi/research-os/prompts/committee/ exists (all 6 role prompts + _committee_common).
- Impact: committee runs fine via fallback. But the documented/preferred instance-local override path
  is undocumented-as-absent; an instance expecting to customize committee prompts has no scaffolded dir.
- Severity: low (doc/scaffold). Fix: `ros init` should scaffold .research-os/prompts/, OR doc the fallback.

## NEWLY-FIXED-PATH RE-VALIDATION

### BUG-3 (green_rule enforcement) — HOLDS ✓ (re-confirmed both gates)
- green + 1 vote => REJECTED ("needs all 6 committee votes ... got 1").
- green + 6 votes incl one yellow => REJECTED ("every vote must be green ... got [...yellow]").

### Lifecycle (claim advance + resume) — HOLDS ✓
- `ros claim advance --claim CLAIM-0006 --state committee_pending --next "..."` round-trips; `ros resume`
  immediately reflects new state + next_action. Reboot-resumable.
- MINOR NIT: `ros claim advance` uses `--claim` while `ros agent register` uses `--id`; flag naming
  inconsistent across subcommands (not a bug, ergonomics).

## IN-PROGRESS: real committee runner end-to-end (BUG-12/13 newly-fixed path) — see below.

## ✅ BUG-10 CLOSED + VERIFIED LIVE (engine e1a1b6f, after the 4a610ee report)
The "still open" report was on engine 4a610ee — the atomic-write fix landed in e1a1b6f moments later.
Fix: dump_yaml atomic (tmp+fsync+os.replace) + load_yaml parse-tolerant + heartbeat preserves role.
VERIFIED on the LIVE autonomous-research instance: 30 concurrent interleaved heartbeat+report writes ->
file stays VALID YAML, role preserved=orchestrator, ros report does NOT crash. Resume normal cadence.
(heartbeat_count is now last-writer-wins under concurrency — benign, not corruption.)

## ✅ BUG-10 CLOSED + VERIFIED LIVE (engine e1a1b6f, after the 4a610ee report)
The "still open" report was on engine 4a610ee — the atomic-write fix landed in e1a1b6f moments later.
Fix: dump_yaml atomic (tmp+fsync+os.replace) + load_yaml parse-tolerant + heartbeat preserves role.
VERIFIED on the LIVE autonomous-research instance: 30 concurrent interleaved heartbeat+report writes ->
file stays VALID YAML, role preserved=orchestrator, ros report does NOT crash. Resume normal cadence.
(heartbeat_count is now last-writer-wins under concurrency — benign, not corruption.)

## ============ ROUND-2 FINDINGS (engine research-os@e1a1b6f) ============

### COMMITTEE RUNNER end-to-end (BUG-12/13 newly-fixed paths) — WORKS ✓ (headline round-2 win)
- Ran the REAL shipped run_committee.sh on cli:dengcchi-mac (macOS Bash 3.2) against a CLAIM-0006
  GREEN-upgrade packet. Result: ALL_COMMITTEE_DONE, all 6 .out files NON-EMPTY, ZERO EMPTY_OUTPUT_NO_VOTE.
- All 6 distinct backends invoked & returned real structured votes: novelty_killer(claude-opus-4-8),
  systems_reviewer(codex), evaluation_prosecutor(gemini), theory_skeptic(claude-opus-4-7),
  product_realist(metacode), area_chair(claude-opus-4-6). Parsing the 6 .out for vote token: 6/6 yellow.
- BUG-13 (mapfile/unbound/pyyaml) NOT reproduced — members parsed cleanly. BUG-12 (metacode no-op) NOT
  reproduced — product_realist(metacode) gave a real VOTE: yellow with REAL_USE_CASE/ADOPTION_BARRIER.

### BUG-14 (verdict detail flags) — CONFIRMED FIXED ✓
- `ros verdict write --fatal/--required/--map-delta/--baselines` persisted ALL four lists correctly into
  VERDICT-0012.yaml (fatal_objections, required_evidence, map_delta_proposals, baseline_requirements).
- MINOR NIT (BUG-17, low): the ';' separator is naive — a literal ';' inside a value (e.g. inside parens
  "(neighbor; scheduling/reuse)") gets split into two list items. No escaping. Cosmetic; worth a quote/escape.

### BUG-3 (green_rule) — HOLDS ✓ (both gates, re-confirmed on e1a1b6f)
- green + 1 vote => REJECTED. green + 6 votes incl 1 yellow => REJECTED ("every vote must be green").

### Lifecycle (claim advance + resume) — HOLDS ✓ across a real claim
- CLAIM-0006: verdict_recorded -> committee_pending -> verdict_recorded, each round-tripped through
  `ros resume` immediately. Reboot-resumable. (Nit: `claim advance` uses --claim, `agent register` uses --id.)

### BUG-6 (git index.lock race) — CONFIRMED LIVE, mitigation works
- A `git commit` from the orchestrator FAILED with "Unable to create .git/index.lock: File exists" WHILE
  the committee was running. run_committee.sh itself does NOT call git; the culprit is a BACKEND committee
  CLI (codex `exec`/claude) invoked with CWD=instance repo doing a transient git op that grabs the index lock.
- Expected: engine/orchestrator git ops should not collide with backend tools. Actual: they do.
- Mitigation that worked: retry-with-backoff loop (commit succeeded on retry). FIX: backend CLIs should run
  with CWD outside the instance .git, OR engine should own git with a lock-aware retry. Severity: medium.

### BUG-10 (torn runtime/agents writes) — CLOSED ✓ (confirmed on e1a1b6f per human + my 20-write re-test)
- 20 concurrent interleaved heartbeat+report: file stays valid YAML, role preserved (orchestrator, not
  reset to unknown), no ros report crash. Matches human's 30-write verification. Resumed normal cadence.

### BUG-7 (liveness retire) — HOLDS ✓
- `ros liveness` shows 🏁 retired for completed/failed agents (no revival nagging).

### BUG-15 (NEW, data-integrity, medium) — CLAIM-0008 has stale/wrong academic_map_nodes + mandatory_baselines
- CLAIM-0008 is PROJ-0003 (Agent failure attribution / recovery; "Error-class predicts agent recovery
  competence"). But its claim YAML has academic_map_nodes:[MAP-0001] (the GPU/KV-cache node) and
  mandatory_baselines:[vLLM APC, SGLang RadixAttention, FlashInfer] (KV-cache serving baselines) — these
  belong to PROJ-0001/PROJ-0002 KV-cache work, NOT to failure-attribution. The correct node is MAP-0002
  (Agent failure attribution & recovery), whose known_baselines is [] (none yet).
- Root cause: claim creation/migration seeded a default template (KV-cache map node + the 3 KV baselines)
  and it was never corrected for PROJ-0003. Expected: a claim's academic_map_nodes/mandatory_baselines
  should match its project's domain; engine offers no validation (cousin of BUG-4 cross-project leak).
- Impact: a committee reviewing CLAIM-0008 would be told to use irrelevant KV-cache baselines; the map
  back-link points at the wrong territory. Mis-routes prior-art + baseline demands.
- Fix: engine claim-create should not hardcode KV baselines; add a `ros` lint that flags claim
  academic_map_nodes whose node area is disjoint from the claim's project domain.

### BUG-16 (NEW, low/coordination) — area_chair aggregator races other members' .out under parallel launch
- run_committee.sh launches all 6 members in parallel (`&` + wait). area_chair (claude-opus-4-6) attempts
  to AGGREGATE the other 5 reviewers' outputs, but since it runs CONCURRENTLY it read product_realist.out
  BEFORE metacode finished writing it -> area_chair reported "product_realist: DID_NOT_VOTE (launch
  failure)" and computed a 4/5 quorum, EVEN THOUGH product_realist.out ends NON-EMPTY with a real
  VOTE: yellow. The final on-disk truth is 6/6; only area_chair's internal self-count was stale.
- Why benign HERE: the orchestrator (Rule 1) parses all 6 .out files itself and does NOT trust
  area_chair's self-reported quorum, and the engine green_rule counts --votes, not area_chair's text.
- Why still a bug: if anyone parsed area_chair's quorum/aggregation as authoritative, a real vote would be
  silently dropped. Fix: either (a) run area_chair in a SECOND phase after the other 5 complete (sequential
  aggregation), or (b) document that area_chair output is advisory and the orchestrator must re-tally .out.
  Severity: low (no current miscount) but a latent committee-integrity foot-gun.

## ============ ROUND-2 FINDINGS (engine research-os@e1a1b6f) ============

### COMMITTEE RUNNER end-to-end (BUG-12/13 newly-fixed paths) — WORKS ✓ (headline round-2 win)
- Ran the REAL shipped run_committee.sh on cli:dengcchi-mac (macOS Bash 3.2) against a CLAIM-0006
  GREEN-upgrade packet. Result: ALL_COMMITTEE_DONE, all 6 .out files NON-EMPTY, ZERO EMPTY_OUTPUT_NO_VOTE.
- All 6 distinct backends invoked & returned real structured votes: novelty_killer(claude-opus-4-8),
  systems_reviewer(codex), evaluation_prosecutor(gemini), theory_skeptic(claude-opus-4-7),
  product_realist(metacode), area_chair(claude-opus-4-6). Parsing the 6 .out for vote token: 6/6 yellow.
- BUG-13 (mapfile/unbound/pyyaml) NOT reproduced — members parsed cleanly. BUG-12 (metacode no-op) NOT
  reproduced — product_realist(metacode) gave a real VOTE: yellow with REAL_USE_CASE/ADOPTION_BARRIER.

### BUG-14 (verdict detail flags) — CONFIRMED FIXED ✓
- `ros verdict write --fatal/--required/--map-delta/--baselines` persisted ALL four lists correctly into
  VERDICT-0012.yaml (fatal_objections, required_evidence, map_delta_proposals, baseline_requirements).
- MINOR NIT (BUG-17, low): the ';' separator is naive — a literal ';' inside a value (e.g. inside parens
  "(neighbor; scheduling/reuse)") gets split into two list items. No escaping. Cosmetic; worth a quote/escape.

### BUG-3 (green_rule) — HOLDS ✓ (both gates, re-confirmed on e1a1b6f)
- green + 1 vote => REJECTED. green + 6 votes incl 1 yellow => REJECTED ("every vote must be green").

### Lifecycle (claim advance + resume) — HOLDS ✓ across a real claim
- CLAIM-0006: verdict_recorded -> committee_pending -> verdict_recorded, each round-tripped through
  `ros resume` immediately. Reboot-resumable. (Nit: `claim advance` uses --claim, `agent register` uses --id.)

### BUG-6 (git index.lock race) — CONFIRMED LIVE, mitigation works
- A `git commit` from the orchestrator FAILED with "Unable to create .git/index.lock: File exists" WHILE
  the committee was running. run_committee.sh itself does NOT call git; the culprit is a BACKEND committee
  CLI (codex `exec`/claude) invoked with CWD=instance repo doing a transient git op that grabs the index lock.
- Expected: engine/orchestrator git ops should not collide with backend tools. Actual: they do.
- Mitigation that worked: retry-with-backoff loop (commit succeeded on retry). FIX: backend CLIs should run
  with CWD outside the instance .git, OR engine should own git with a lock-aware retry. Severity: medium.

### BUG-10 (torn runtime/agents writes) — CLOSED ✓ (confirmed on e1a1b6f per human + my 20-write re-test)
- 20 concurrent interleaved heartbeat+report: file stays valid YAML, role preserved (orchestrator, not
  reset to unknown), no ros report crash. Matches human's 30-write verification. Resumed normal cadence.

### BUG-7 (liveness retire) — HOLDS ✓
- `ros liveness` shows 🏁 retired for completed/failed agents (no revival nagging).

### BUG-15 (NEW, data-integrity, medium) — CLAIM-0008 has stale/wrong academic_map_nodes + mandatory_baselines
- CLAIM-0008 is PROJ-0003 (Agent failure attribution / recovery; "Error-class predicts agent recovery
  competence"). But its claim YAML has academic_map_nodes:[MAP-0001] (the GPU/KV-cache node) and
  mandatory_baselines:[vLLM APC, SGLang RadixAttention, FlashInfer] (KV-cache serving baselines) — these
  belong to PROJ-0001/PROJ-0002 KV-cache work, NOT to failure-attribution. The correct node is MAP-0002
  (Agent failure attribution & recovery), whose known_baselines is [] (none yet).
- Root cause: claim creation/migration seeded a default template (KV-cache map node + the 3 KV baselines)
  and it was never corrected for PROJ-0003. Expected: a claim's academic_map_nodes/mandatory_baselines
  should match its project's domain; engine offers no validation (cousin of BUG-4 cross-project leak).
- Impact: a committee reviewing CLAIM-0008 would be told to use irrelevant KV-cache baselines; the map
  back-link points at the wrong territory. Mis-routes prior-art + baseline demands.
- Fix: engine claim-create should not hardcode KV baselines; add a `ros` lint that flags claim
  academic_map_nodes whose node area is disjoint from the claim's project domain.

### BUG-16 (NEW, low/coordination) — area_chair aggregator races other members' .out under parallel launch
- run_committee.sh launches all 6 members in parallel (`&` + wait). area_chair (claude-opus-4-6) attempts
  to AGGREGATE the other 5 reviewers' outputs, but since it runs CONCURRENTLY it read product_realist.out
  BEFORE metacode finished writing it -> area_chair reported "product_realist: DID_NOT_VOTE (launch
  failure)" and computed a 4/5 quorum, EVEN THOUGH product_realist.out ends NON-EMPTY with a real
  VOTE: yellow. The final on-disk truth is 6/6; only area_chair's internal self-count was stale.
- Why benign HERE: the orchestrator (Rule 1) parses all 6 .out files itself and does NOT trust
  area_chair's self-reported quorum, and the engine green_rule counts --votes, not area_chair's text.
- Why still a bug: if anyone parsed area_chair's quorum/aggregation as authoritative, a real vote would be
  silently dropped. Fix: either (a) run area_chair in a SECOND phase after the other 5 complete (sequential
  aggregation), or (b) document that area_chair output is advisory and the orchestrator must re-tally .out.
  Severity: low (no current miscount) but a latent committee-integrity foot-gun.
