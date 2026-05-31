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

### BUG-15 — CONFIRMED + FIXED this run (CLAIM-0008 wrong map/baselines)
- researcher-failattr-r2 independently re-confirmed CLAIM-0008 had academic_map_nodes:[MAP-0001] +
  KV-cache mandatory_baselines. Fixed: academic_map_nodes:[MAP-0002], mandatory_baselines:
  ['class-agnostic recovery rate (NULL baseline)']. Engine still has NO validator (gap stands).

### BUG-18 (NEW, medium, data-integrity) — `ros verdict write` is NON-IDEMPOTENT under retry -> duplicate orphan verdict
- Symptom: a SINGLE EXP-0006 `ros verdict write` produced TWO verdict files — VERDICT-0013 AND
  VERDICT-0014 — with BYTE-IDENTICAL content (same claim, same EXP-0006, same fatal/required/map-delta)
  and the SAME created_at timestamp (14:30:43Z). Only VERDICT-0014 was back-linked into the claim's
  verdict_history + EXP-0006.linked_verdicts; VERDICT-0013 was an ORPHAN (no claim/exp references it).
- Engine analysis: cmd_verdict_write (ros.py ~L537) has exactly ONE def, ONE set_defaults, ONE
  dump_yaml(path) — the engine does NOT double-write internally. So the duplicate came from the COMMAND
  being invoked TWICE (a harness/transport retry of the tool call within the same wall-clock second:
  first call wrote 0013, the retry recomputed next_id->0014 and wrote again). Same BUG-6/retry family:
  non-idempotent writes + retries => duplicates.
- Why it matters: next_id() scans existing files for max+1, so a retry does NOT collide on the ID; it
  SILENTLY creates a second, higher-numbered verdict. The registry ends with a duplicate verdict and a
  dangling ID gap; a naive reader counting verdicts or trusting the latest-id is misled. The orphan is
  invisible from the claim side (not in verdict_history).
- Expected: verdict write should be idempotent OR detect "this exact (claim, experiments, votes, content)
  verdict already exists for today" and refuse/return the existing id. Actual: writes a duplicate.
- Fix options: (a) content-fingerprint dedup (like cemetery_conflict already does for DEAD ideas — reuse
  _fingerprint) before writing; (b) make next_id+write atomic (lock or O_EXCL create) so a retry is a
  no-op; (c) the orchestrator/engine should own a request-id to dedupe retries.
- Remediation this run: removed orphan VERDICT-0013 (verified zero references first); VERDICT-0014 is the
  canonical EXP-0006 verdict. CLAIM-0008's VERDICT-0015 did NOT dupe (single write succeeded once).
- Severity: medium (data-integrity; silent duplicate; not caught by any engine check).

### NOTE: VERDICT-0004 gap is PRE-EXISTING (not mine) — present before round-2.

### BUG-15 — CONFIRMED + FIXED this run (CLAIM-0008 wrong map/baselines)
- researcher-failattr-r2 independently re-confirmed CLAIM-0008 had academic_map_nodes:[MAP-0001] +
  KV-cache mandatory_baselines. Fixed: academic_map_nodes:[MAP-0002], mandatory_baselines:
  ['class-agnostic recovery rate (NULL baseline)']. Engine still has NO validator (gap stands).

### BUG-18 (NEW, medium, data-integrity) — `ros verdict write` is NON-IDEMPOTENT under retry -> duplicate orphan verdict
- Symptom: a SINGLE EXP-0006 `ros verdict write` produced TWO verdict files — VERDICT-0013 AND
  VERDICT-0014 — with BYTE-IDENTICAL content (same claim, same EXP-0006, same fatal/required/map-delta)
  and the SAME created_at timestamp (14:30:43Z). Only VERDICT-0014 was back-linked into the claim's
  verdict_history + EXP-0006.linked_verdicts; VERDICT-0013 was an ORPHAN (no claim/exp references it).
- Engine analysis: cmd_verdict_write (ros.py ~L537) has exactly ONE def, ONE set_defaults, ONE
  dump_yaml(path) — the engine does NOT double-write internally. So the duplicate came from the COMMAND
  being invoked TWICE (a harness/transport retry of the tool call within the same wall-clock second:
  first call wrote 0013, the retry recomputed next_id->0014 and wrote again). Same BUG-6/retry family:
  non-idempotent writes + retries => duplicates.
- Why it matters: next_id() scans existing files for max+1, so a retry does NOT collide on the ID; it
  SILENTLY creates a second, higher-numbered verdict. The registry ends with a duplicate verdict and a
  dangling ID gap; a naive reader counting verdicts or trusting the latest-id is misled. The orphan is
  invisible from the claim side (not in verdict_history).
- Expected: verdict write should be idempotent OR detect "this exact (claim, experiments, votes, content)
  verdict already exists for today" and refuse/return the existing id. Actual: writes a duplicate.
- Fix options: (a) content-fingerprint dedup (like cemetery_conflict already does for DEAD ideas — reuse
  _fingerprint) before writing; (b) make next_id+write atomic (lock or O_EXCL create) so a retry is a
  no-op; (c) the orchestrator/engine should own a request-id to dedupe retries.
- Remediation this run: removed orphan VERDICT-0013 (verified zero references first); VERDICT-0014 is the
  canonical EXP-0006 verdict. CLAIM-0008's VERDICT-0015 did NOT dupe (single write succeeded once).
- Severity: medium (data-integrity; silent duplicate; not caught by any engine check).

### NOTE: VERDICT-0004 gap is PRE-EXISTING (not mine) — present before round-2.

### CONSISTENCY SWEEP (end of round-2 cycle)
- All claim experiment back-link paths resolve to existing nested dirs ✓ (BUG-2 stays closed).
- Orphan verdicts (not in any claim verdict_history): VERDICT-0010 ONLY — and it is PRE-EXISTING
  (created 13:48:41Z round-1, commit d93bb5f/b80c998, a superseded GREEN on CLAIM-0006 before the
  VERDICT-0011 reframe). NOT a round-2 dupe; left intact as historical record. The round-2 dupe
  (VERDICT-0013, BUG-18) was already removed.
- Lifecycle: 3 in-flight claims, all with current next_action; CLAIM-0006/0008 now evidence_ready with
  clear GREEN-blockers (both require human go / GPU territory).

### ROUND-2 BUG SCOREBOARD
- CONFIRMED FIXED (newly-fixed paths held): committee runner e2e (BUG-12/13), BUG-14 (verdict detail),
  BUG-3 (green_rule), BUG-10 (atomic runtime writes), BUG-7 (liveness retire), lifecycle advance/resume.
- TODO carryover: BUG-2 CLOSED; BUG-4 data-fixed + engine-gap logged; BUG-6 confirmed LIVE (mitigated);
  BUG-1 partial (fallback works).
- NEW round-2: BUG-15 (CLAIM-0008 wrong map/baselines — self-fixed), BUG-16 (area_chair parallel-race — FIXED by engine 6667c9e: chair-last ordering),
  BUG-16 (area_chair parallel-race miscounts — benign, latent), BUG-17 (map-delta ';' split nit),
  BUG-18 (verdict write non-idempotent under retry -> duplicate orphan — remediated).

### CONSISTENCY SWEEP (end of round-2 cycle)
- All claim experiment back-link paths resolve to existing nested dirs ✓ (BUG-2 stays closed).
- Orphan verdicts (not in any claim verdict_history): VERDICT-0010 ONLY — and it is PRE-EXISTING
  (created 13:48:41Z round-1, commit d93bb5f/b80c998, a superseded GREEN on CLAIM-0006 before the
  VERDICT-0011 reframe). NOT a round-2 dupe; left intact as historical record. The round-2 dupe
  (VERDICT-0013, BUG-18) was already removed.
- Lifecycle: 3 in-flight claims, all with current next_action; CLAIM-0006/0008 now evidence_ready with
  clear GREEN-blockers (both require human go / GPU territory).

### ROUND-2 BUG SCOREBOARD
- CONFIRMED FIXED (newly-fixed paths held): committee runner e2e (BUG-12/13), BUG-14 (verdict detail),
  BUG-3 (green_rule), BUG-10 (atomic runtime writes), BUG-7 (liveness retire), lifecycle advance/resume.
- TODO carryover: BUG-2 CLOSED; BUG-4 data-fixed + engine-gap logged; BUG-6 confirmed LIVE (mitigated);
  BUG-1 partial (fallback works).
- NEW round-2: BUG-15 (CLAIM-0008 wrong map/baselines — self-fixed), BUG-16 (area_chair parallel-race — FIXED by engine 6667c9e: chair-last ordering),
  BUG-16 (area_chair parallel-race miscounts — benign, latent), BUG-17 (map-delta ';' split nit),
  BUG-18 (verdict write non-idempotent under retry -> duplicate orphan — remediated).

### BUG-16 — FIXED by engine 6667c9e (verified). run_committee.sh now runs 5 reviewers in parallel,
  `wait`s, then runs area_chair LAST with the 5 finished reviewer .out files injected into its prompt
  ("=== REVIEWER VOTES TO AGGREGATE ==="). Chair quorum is now real, not raced. Confirmed at source
  (engine/run_committee.sh L71-83 + L38-58).

### INFRA NOTE (NOT an engine bug) — committee re-run #2 hit 5/6 EMPTY_OUTPUT (backend CLI breakage)
- Ran the real committee a SECOND time (engine 6667c9e, chair-last) on the EXP-0006 fair-PIC packet.
  launch.log CONFIRMS BUG-16 fix: "(reviewers done; running area_chair to aggregate)" — chair ran LAST.
- BUT 5/6 outputs were empty, all correctly flagged EMPTY_OUTPUT_NO_VOTE (BUG-12 fix working as designed):
  - claude-opus-4-8/4-7/4-6 (novelty_killer/theory_skeptic/area_chair): `sandbox-exec: sandbox_apply:
    Operation not permitted` — macOS sandbox profile cannot be applied (likely resource/concurrency
    pressure; ~55 stale backend procs were lingering from prior runs).
  - codex (systems_reviewer): `Could not locate macOS sandbox profile profile.sb` — codex CLI
    install/profile issue (PERSISTENT, needs reinstall).
  - gemini (evaluation_prosecutor): `Cannot find module '../build/Debug/pty.node'` — gemini CLI
    node-pty native module broken (PERSISTENT, needs reinstall).
  - metacode (product_realist): returned only "4 skills discovered" (40B) — explored fs, never voted.
- ENGINE BEHAVED CORRECTLY: every failure surfaced as EMPTY_OUTPUT_NO_VOTE; no silent miscount. I wrote
  NO verdict (Rule 1: never infer/fabricate missing votes). Reverted CLAIM-0006 to evidence_ready.
- DISTINCTION FROM ROUND 1: run #1 (~40min earlier, packet v1) got a clean 6/6 with the SAME backends,
  so the claude `sandbox_apply` is plausibly transient (load); but codex profile.sb + gemini pty.node
  look like genuine install breakage that will recur until those CLIs are reinstalled on the node.
- ACTION: the EXP-0006 finding already has a recorded verdict (VERDICT-0014, evidence-update). A fresh
  6/6 committee re-vote is BLOCKED on backend-CLI health (codex/gemini reinstall + sandbox headroom),
  which is operator/infra territory, not engine.

### INFRA NOTE (NOT an engine bug) — committee re-run #2 hit 5/6 EMPTY_OUTPUT (backend CLI breakage)
- Ran the real committee a SECOND time (engine 6667c9e, chair-last) on the EXP-0006 fair-PIC packet.
  launch.log CONFIRMS BUG-16 fix: "(reviewers done; running area_chair to aggregate)" — chair ran LAST.
- BUT 5/6 outputs were empty, all correctly flagged EMPTY_OUTPUT_NO_VOTE (BUG-12 fix working as designed):
  - claude-opus-4-8/4-7/4-6 (novelty_killer/theory_skeptic/area_chair): `sandbox-exec: sandbox_apply:
    Operation not permitted` — macOS sandbox profile cannot be applied (likely resource/concurrency
    pressure; ~55 stale backend procs were lingering from prior runs).
  - codex (systems_reviewer): `Could not locate macOS sandbox profile profile.sb` — codex CLI
    install/profile issue (PERSISTENT, needs reinstall).
  - gemini (evaluation_prosecutor): `Cannot find module '../build/Debug/pty.node'` — gemini CLI
    node-pty native module broken (PERSISTENT, needs reinstall).
  - metacode (product_realist): returned only "4 skills discovered" (40B) — explored fs, never voted.
- ENGINE BEHAVED CORRECTLY: every failure surfaced as EMPTY_OUTPUT_NO_VOTE; no silent miscount. I wrote
  NO verdict (Rule 1: never infer/fabricate missing votes). Reverted CLAIM-0006 to evidence_ready.
- DISTINCTION FROM ROUND 1: run #1 (~40min earlier, packet v1) got a clean 6/6 with the SAME backends,
  so the claude `sandbox_apply` is plausibly transient (load); but codex profile.sb + gemini pty.node
  look like genuine install breakage that will recur until those CLIs are reinstalled on the node.
- ACTION: the EXP-0006 finding already has a recorded verdict (VERDICT-0014, evidence-update). A fresh
  6/6 committee re-vote is BLOCKED on backend-CLI health (codex/gemini reinstall + sandbox headroom),
  which is operator/infra territory, not engine.

### BUG-18 — FIXED by engine 60e0032 (verified). `ros verdict write` is now IDEMPOTENT: a repeat write
  with same claim+experiments+final is a no-op ("↩︎ idempotent: VERDICT-0014 already records yellow for
  CLAIM-0006 citing ['EXP-0006'] — not creating a duplicate"). Verdict count stayed 13, no orphan.
  --allow-dup forces a real duplicate if ever needed. Closes the retry-orphan class.

### STATUS: committee BLOCKED (operator). CLAIM-0006 lifecycle=blocked, blocking_on="committee backend
  CLIs down (codex profile.sb / gemini pty.node / claude sandbox_apply) — operator reinstall needed".
  Valid verdict preserved: VERDICT-0012 (6/6 YELLOW) + VERDICT-0014 (EXP-0006 evidence-update). NO forced
  verdict. Committee re-runs paused until operator restores codex+gemini+claude CLIs. Continuing CPU-only
  registry/lifecycle/research work meanwhile.

### EXP-0008 — CLAIM-0008 WEAKENED (VERDICT-0016). Adversarial outcome-def decoupling: error-class->recovery
  signal washes out when cross-tool workarounds are counted (V 0.644->0.239 n.s., LOO-Brier gain ->~0,
  permanence phi 0.454->0.138). EXP-0007's headline was driven by web_disabled 0/109 = a REDIRECTABLE gate
  scored as terminal. Rule-3: MAP-0002 + prior_art updated (redirectable-vs-terminal split, recovery-modality
  reframe). The committee gauntlet philosophy worked at the EXPERIMENT level: the follow-up honestly killed
  the strong framing. CLAIM-0008 stays weakened.

### ONBOARDING NIT (not a bug) — `ros` is not on PATH for spawned researchers
- researcher-recovery-outcome-r2 reported "ros is not an invocable CLI on cli:dengcchi-mac" and worked around
  it by hand-authoring EXP-0008/experiment.yaml to match EXP-0007's schema (correct, no collision, engine
  reads it fine). Cause: there is no `ros` shim on PATH; the engine is invoked as
  `/usr/bin/python3 /Users/dengcchi/research-os/engine/ros.py --instance <ROOT> ...`. Researchers should be
  TOLD the full invocation (I did include it in the task, but the agent still tried bare `ros`). Cheap fix:
  add a `ros` wrapper script to /usr/local/bin, OR always pass researchers the full python invocation +
  emphasize bare `ros` won't work. Not an engine bug.

### BUG-19 (NEW, low) — no `ros agent retire/complete`; a finished orchestrator lingers as ☠️ DEAD-nagging
- `ros agent` only has `register` (no retire/complete/done). When an orchestrator session ENDS without a
  terminal state (e.g. round-1 orchestrator-v2-001 handed off to me and stopped), liveness shows it ☠️ DEAD
  past the 45m grace with "orchestrator should revive" — but it should NOT be revived (it legitimately
  finished + handed off). BUG-7 retires agents whose ROLE/last-report marks completed/failed, but there is
  no way for an agent to self-mark terminal, and `ros report` has --done/--blocked/--need but no
  --status=completed/retired. So a cleanly-finished agent is indistinguishable from a crashed one.
- Expected: a `ros agent retire --id X` (or `ros report --agent X --status completed`) that flips the agent
  to 🏁 retired so liveness stops nagging a handoff. Actual: it nags indefinitely as DEAD.
- Impact: false "revive me" signal; a fresh orchestrator reading liveness could wrongly try to revive a
  superseded predecessor. Severity: low (cosmetic/operational), but pollutes the liveness dashboard.

### NUMBERING NOTE: the operator labeled the committee-sandbox fix "BUG-19" (engine db3e67d). My buglog had
  already used BUG-19 for the "no agent retire/complete" liveness gap. To avoid collision, the
  committee-sandbox issue is recorded here as BUG-20.

### BUG-20 (was operator's "BUG-19") — FIXED by engine db3e67d. NESTED-SANDBOX committee failure.
- ROOT CAUSE (corrects my earlier "CLIs down/reinstall" hypothesis): the navi daemon runs UNSANDBOXED;
  when run_committee.sh spawned claude/codex/gemini/metacode, each tried to apply its OWN inner macOS
  sandbox -> `sandbox_apply: Operation not permitted` / `sandbox-exec` EXIT 71 -> empty output. That is
  why run #2 hit 5/6 EMPTY_OUTPUT_NO_VOTE while run #1 (different process context) had succeeded.
- FIX: run_committee.sh now passes --dangerously-disable-osx-sandbox to ALL 6 backends (claude via
  ${CLAUDE_SANDBOX_FLAG:-...}, codex/gemini/metacode inline). Operator validated all 6 round-trip.
- LESSON: the EMPTY_OUTPUT_NO_VOTE flag (BUG-12 fix) + Rule-1 (refuse verdict on <full committee) were
  exactly right — they turned a silent nested-sandbox failure into a visible, safe block instead of a
  fabricated verdict. The "reinstall" guess was wrong but the SAFE BEHAVIOR was correct.
- My BUG-19 (no `ros agent retire/complete`) remains a separate, still-open low-sev finding.

### COMMITTEE RUN #3 (engine db3e67d, BUG-20 sandbox fix) — CLEAN 6/6 ✓ (round-2 headline, fully closed)
- After --dangerously-disable-osx-sandbox on all 6 backends: ALL_COMMITTEE_DONE, all 6 .out non-empty,
  ZERO EMPTY_OUTPUT_NO_VOTE. All 6 distinct models voted YELLOW with REAL structured content (codex +
  metacode both produced real votes this time, unlike sandbox-broken run #2).
- BUG-16 chair-last VERIFIED in the live run: launch.log shows "(reviewers done; running area_chair to
  aggregate)" THEN "done: area_chair" — chair saw all 5 finished reviewer votes (no race), aggregated a
  correct 5/5 quorum (matching the on-disk truth). The round-1 area_chair race is gone.
- Wrote VERDICT-0017 (Rule 1, all 6 --votes + enriched --fatal/--required/--map-delta/--baselines via the
  BUG-14 flags; used --allow-dup since it's a genuine NEW committee verdict citing the same EXP set as the
  prior evidence-update VERDICT-0014). Rule-3: MAP-0001 + prior_art merged (Pope/Kwon accounting identity,
  2601.06007 distinction-unverified edge, two retired legs, single-leg framing).
- NET: the full committee->verdict->map cycle now works end-to-end on macOS with all 6 real models. The
  EMPTY_OUTPUT flag + Rule-1 refusal correctly bridged the sandbox-broken interval without a fake verdict.
