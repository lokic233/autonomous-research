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

### BUG-20b — FIXED by engine ad2bf6d (claude concurrency empties). + ORCHESTRATOR LESSON.
- Root cause: 4 overlapping claude processes on the AI gateway -> 2 returned EMPTY despite starting (a
  single claude call is fine). FIX: run_committee.sh now staggers member launches ~3s AND auto-retries
  ONCE on empty output (EMPTY flag now annotated "(after 1 retry)").
- ORCHESTRATOR INTEGRITY NOTE: in MY committee_run_3 all 6 .out happened to be non-empty with real vote
  blocks (I verified sizes + grepped real VOTE: lines + read area_chair's full aggregation), so VERDICT-0017
  was written on 6 genuine votes. But the operator flagged that claude-concurrency CAN empty 2 members
  intermittently — run_3 got lucky on timing. LESSON: file-size alone is not sufficient proof of a vote;
  always (a) check .err for EMPTY_OUTPUT_NO_VOTE AND (b) confirm each .out contains an actual
  "ROLE: x VOTE: y" / "FINAL_VERDICT:" block before counting it. The stagger+retry fix makes 6/6 reliable
  rather than timing-luck-dependent; re-running into committee_run_4 to confirm.

### BUG-21 (NEW, HIGH) — run_committee.sh reports ALL_COMMITTEE_DONE with MISSING members (no .out AND no .err)
- committee_run_4 (engine ad2bf6d, staggered launch): launch.log printed "done" for only 4 of 6 members
  (gemini, theory_skeptic, codex, novelty_killer) yet wrote `ALL_COMMITTEE_DONE` + "members: 6".
- product_realist (metacode) and area_chair (claude-opus-4-6) produced NEITHER a .out NOR a .err file —
  they were effectively NEVER invoked / silently dropped. Confirmed: the only claude-opus-4-6 proc on the
  box (PID 25397) started 07:30 = committee_run_3, NOT run_4 (08:36). No new metacode proc since 08:36.
- WHY IT'S DANGEROUS: unlike BUG-12 (empty .out -> EMPTY_OUTPUT_NO_VOTE flag in .err), here there is NO
  .err at all, so the EMPTY-flag safety net does NOT fire. A naive parser counting "votes present" would
  see 4 YELLOW + ALL_COMMITTEE_DONE and could wrongly treat it as complete. The runner's completion
  signal is decoupled from actual per-member output existence.
- LIKELY CAUSE: the new stagger loop (`run_one & ; sleep 3` per member) + chair-last `wait` interacts
  badly — product_realist (metacode, slow >5s to start) backgrounded then the loop/`wait`/chair path
  dropped it; area_chair (chair-last, run AFTER `wait`) also never produced files. The `&` + `sleep 3` +
  `wait` + sequential-chair sequence likely loses the metacode background job and/or the chair invocation
  under certain timing. Needs: (a) the runner MUST verify each member has a .out (or an EMPTY .err flag)
  before writing ALL_COMMITTEE_DONE — fail/flag MISSING_MEMBER otherwise; (b) ensure metacode's slow start
  + chair-last are both actually awaited.
- ORCHESTRATOR ACTION (Rule 1 held): did NOT fabricate the 2 missing votes. VERDICT-0017 (from run_3,
  re-verified to contain all 6 GENUINE vote blocks) remains the valid 6/6 record for CLAIM-0006. No new
  verdict written from the incomplete run_4. Reported via ros report.
- Severity: HIGH — a false completion signal that bypasses the EMPTY-flag safety net could, with a less
  careful orchestrator, produce a verdict on a partial committee (the exact failure the green_rule + Rule-1
  + EMPTY-flag layers exist to prevent).

### BUG-22 (NEW, HIGH) — gemini (no </dev/null) DRAINS the while-read loop's stdin -> last 2 members never launched; gate bypassed
- committee_run_5 (engine fb4a63b, the BUG-21 gating fix): _status.txt = ALL_COMMITTEE_DONE, but only 4/6
  members produced files. product_realist(metacode) + area_chair(claude-4-6) had NO .out AND NO .err —
  the loop NEVER reached them. launch.log shows exactly 4 "done:" lines.
- ROOT CAUSE (classic bash foot-gun): the launch loop is `while read -r role backend; do ... run_one & ...
  done < "$MEMBERS_FILE"`. run_one invokes the backend CLI. claude/codex/metacode all use `</dev/null`,
  but GEMINI does NOT (line 62 main + line 73 retry: `gemini --dangerously... -p "$full" >out 2>err` with
  NO stdin redirect). When gemini is backgrounded (`&`), it INHERITS the loop's stdin fd = $MEMBERS_FILE
  and READS/DRAINS the remaining lines. gemini (evaluation_prosecutor) is member 3; after it drains stdin,
  the `while read` gets EOF -> loop exits having processed only the first 4 members it managed to read
  before/around the drain; members 5 (product_realist) + 6 (area_chair) are silently dropped.
- WHY THE BUG-21 GATE DIDN'T CATCH IT: the gate iterates `$ALL_ROLES`, which is accumulated INSIDE the
  same loop — so it only ever contained the 4 roles the loop actually read. The gate verified 4/4 present
  -> false ALL_COMMITTEE_DONE. The gate must verify against the AUTHORITATIVE member list (.members.txt /
  config), NOT the loop-accumulated variable that the stdin-drain truncated.
- FIX (two parts, both needed):
  (1) add `</dev/null` to the gemini invocation in BOTH the main case (line 62) and the retry case (line
      73) — matches claude/codex/metacode and stops the stdin drain. (Belt-and-suspenders: redirect the
      whole loop's stdin, e.g. read on fd 3: `while read -r role backend <&3; do ...; done 3< "$FILE"`.)
  (2) gate completion against the full member count from .members.txt/config, not $ALL_ROLES, so a
      truncated loop can never yield a passing gate.
- ORCHESTRATOR ACTION (Rule 1 held AGAIN): 4/6 only — did NOT write a verdict from run_5. VERDICT-0017
  (run_3, verified 6 genuine vote blocks) remains the valid 6/6 record. Reported.
- Severity: HIGH — same false-complete class as BUG-21 but via a different mechanism (stdin drain), and it
  DEFEATS the BUG-21 gate. This is why the gate must key off the authoritative member list.
- NOTE: run_3 succeeded because (per launch.log) its timing happened to let the loop read all 6 before
  any gemini drain took effect on that run; it was timing-luck, consistent with the operator's earlier
  observation. The stdin-drain is the deterministic root cause that makes drops recur.

### BUG-22 — FIXED by engine 953dbc3 (VERIFIED end-to-end in committee_run_6). 
- Source verified: gemini now </dev/null (line 62+73), all run_one children </dev/null, launch loop reads on
  FD 9 (`while read ... <&9; done 9< $MEMBERS_FILE`) so no child can drain it, ALL_ROLES computed via awk
  over the members file INDEPENDENTLY (line 89) so the gate always sees all 6.
- committee_run_6 (CLAIM-0009): clean gated 6/6 — _status=ALL_COMMITTEE_DONE, all 6 .out present + non-empty
  with real vote blocks, ZERO members dropped (the BUG-21/22 false-DONE is gone). BUG-20b auto-retry recovered
  3 transient claude/codex/metacode empties mid-run; final = real 6/6 YELLOW. Wrote parity VERDICT-0020
  (--allow-dup to supersede the 1-vote VERDICT-0018; idempotency guard correctly blocked the plain re-write).
- The full committee runner is now ROBUST across all 4 failure modes my runs exposed: nested-sandbox (20),
  claude-concurrency-empties (20b), false-ALL_DONE-with-missing (21), gemini-stdin-drain (22).

### COMMITTEE VALUE DEMONSTRATED: VERDICT-0020 (6/6) was SHARPER than my 1-vote VERDICT-0018.
- The committee surfaced the PREDICTOR-MISATTRIBUTION confound (error-class vs gate-type are colinear in the
  corpus; the signal may be the harness routing table, not error-class) — an objection my single-vote review
  MISSED. This is the concrete payoff of the full-committee bar over a 1-vote evidence-update: it caught an
  overclaim. Scope of CLAIM-0009 narrowed accordingly; harness-routing-as-confound added to MAP-0002 red_zones.

### BUG-23 (NEW, low) — `ros exp register` then re-register leaves an orphan PENDING experiment + dangling active_experiments
- researcher-modality-ablation-0009 registered EXP-0011, then ran/completed the work as EXP-0012 (likely a
  re-register after a false start). EXP-0011 was left status=pending with no result, AND CLAIM-0009.active_
  experiments still listed EXP-0011 (a dangling pointer to a never-completed experiment).
- Impact: low — a pending orphan inflates the experiment count + leaves a stale active_experiments entry that
  `ros resume` would surface as in-flight forever. No data corruption.
- Remediation this run: removed the EXP-0011 stub dir + cleared it from CLAIM-0009.active_experiments.
- Fix (engine, optional): `ros exp register` could warn if the claim already has a pending experiment; or a
  `ros exp abandon/gc` to retire never-completed pending experiments + clear their active_experiments back-link.

### EXP-0012 — CLAIM-0009 WEAKENED to a config-fact (VERDICT-0021); committee objections DATA-CONFIRMED.
- The full 6/6 committee (VERDICT-0020) flagged definitional-inflation + predictor-misattribution; EXP-0012
  (the CPU follow-up I dispatched to test them) CONFIRMED both with data: ablated LOO-Brier +40.1%->+2.2%,
  leave-one-CLASS-out -33%, error-class lift over gate-type-only = -0.0043 (1 bit ~= full taxonomy).
- Outcome: error-class framing RETIRED; CLAIM-0009 restated as a gate-type+routing CHARACTERIZATION (config
  fact). harness-routing-as-confound promoted OPEN_RISK -> CONFIRMED in MAP-0002. This is the committee->
  experiment->verdict loop working as designed: a 6/6 objection drove a targeted experiment that honestly
  weakened the claim. No fabrication; truth tracked.

### BUG-24 (NEW, medium) — `ros exp gc --apply` races ACTIVE researchers; retires a pending exp that's mid-flight
- `ros exp gc --apply` retired 3 "orphan pending" experiments: EXP-0001 + EXP-0004 (legit old stubs) BUT ALSO
  EXP-0013, which an ACTIVE researcher (researcher-0006-priorart-stats, Task B stats-pass) had JUST registered
  and was mid-run on — its impl/stats_pass.py (9KB) was already written; it simply hadn't reached
  `ros exp complete` yet. gc flipped status=pending->retired + cleared the CLAIM-0006 backlink. When the
  researcher finishes and runs `exp complete --exp EXP-0013`, it would hit a retired experiment (lost work /
  conflict).
- ROOT CAUSE: gc's definition of "orphan" = status==pending with no result, but a freshly-registered
  experiment that an active researcher is still working on is ALSO status==pending-with-no-result. gc cannot
  distinguish "abandoned stub" from "in-progress." No age/heartbeat guard.
- Impact: medium — silently retires live work; the researcher's completion then races a retired record.
- Remediation this run: orchestrator un-retired EXP-0013 (restored status=pending + active_experiments backlink)
  since its impl/ was present and the researcher was live.
- Fix (engine): gc should only retire pending experiments older than some grace (e.g. registered >30-60m ago)
  OR whose owning researcher is not in liveness as running OR that have an empty impl/ dir. Add an age/owner
  guard so gc never reaps an in-flight experiment.
- LESSON for orchestrator: run `ros exp gc` only when NO researchers are active (check liveness first), or
  pass a dry-run + eyeball the list before --apply. I ran --apply while a researcher was mid-flight.

### BUG-25 (NEW, HIGH / data-integrity) — `ros exp complete --effect kill --claim <X>` will KILL a PROMOTED 6/6-GREEN claim with NO guard
- researcher-0001-laneA was told (by my task) to `exp register --claim CLAIM-0002` for the idle-window
  speculative-prefill GAP. But CLAIM-0002 is the PROMOTED 6/6-GREEN mapping-ceiling thesis — the gap merely
  REFERENCES it as adjacent in MAP-0001; the gap is NOT itself a registered claim. When the researcher ran
  `exp complete --effect kill`, the engine auto-flipped CLAIM-0002 status promoted->killed AND buried it as
  DEAD-0010 — destroying a promoted claim.
- ROOT CAUSE: `exp complete --effect kill` unconditionally transitions the bound claim to killed + writes a
  cemetery entry, with NO check that the claim is promoted/GREEN (which should be near-immutable) and no
  confirmation. A single mis-bound experiment can erase a top result.
- TWO bugs here: (a) ENGINE: a kill on a promoted claim must REQUIRE explicit override/confirmation (promoted
  claims are near-terminal; killing one should not be a silent side-effect of an experiment completion);
  (b) ORCHESTRATOR (mine): my researcher task said `--claim CLAIM-0002` when the gap is not that claim — I
  pointed it at a promoted claim. Researcher tasks for a GAP that isn't a registered claim must NOT bind to an
  existing claim id; either seed a fresh claim first or use `--claim none`.
- REMEDIATION (researcher self-repaired, orchestrator verified): CLAIM-0002 restored to status=promoted/
  stage=paper-track/lifecycle=done (matches committed good state a2908b3, git diff vs HEAD empty = correct).
  DEAD-0010 rewritten to record the GAP idea (original_claim_id:'' + flag note), NOT CLAIM-0002's death.
- Severity: HIGH — silent destruction of a promoted 6/6-GREEN claim. Engine fix: guard kill-on-promoted.
- LESSON: when dispatching a researcher on a MAP open_gap that is not a registered claim, do NOT pass an
  existing --claim id (esp. a promoted one). Seed the claim first, or scope the experiment to --claim none.

### BUG-26 (NEW, low/operational) — GPU scheduler probe flaps when the node heartbeat file goes stale (>15m)
- `ros gpu poll --node devgpu014` returned "unreachable (probe failed)" even though the node was verified-alive
  (ran a vLLM env probe on it seconds earlier). Cause: the node's probe_cmd checks runtime/gpu_heartbeat/<node>
  is mtime < 15min; nothing was refreshing that heartbeat file, so it went stale and the probe failed.
- The _old_probe (ssh nvidia-smi) was replaced by a heartbeat-file check, but there's no running agent on the
  node refreshing runtime/gpu_heartbeat/<node>. So after 15m idle the scheduler treats a healthy free node as
  unreachable and won't pull queued exps.
- Remediation this run: orchestrator `touch runtime/gpu_heartbeat/devgpu014` after directly verifying the node
  is alive (env probe succeeded) -> poll then pulled EXP-0026 correctly.
- Fix: either (a) run a per-node heartbeat refresher (cron/agent on the node touches the file), or (b) the poll
  probe should fall back to the live ssh nvidia-smi check (_old_probe) when the heartbeat file is stale, before
  declaring unreachable. Low severity (orchestrator can refresh after verifying liveness) but it silently stalls
  the pull scheduler.

### LESSON (operational, not an engine bug) — `pip install lmcache` BROKE the shared vLLM env
- Pursuing committee path (1) (measure published lmcache CacheBlend), I pip-installed lmcache 0.4.6 into
  py312conda. It pulled numpy 2.2.6 (vLLM needs <2.0), transformers 5.9.0, outlines 0.0.44, tokenizers 0.22 —
  BREAKING vLLM 0.6.6 (ProcessorMixin import failure). I had verified vLLM worked moments before.
- REMEDIATION: pinned back numpy<2.0 + outlines==0.1.11 + transformers 4.46.3 + tokenizers 0.20.3 -> vLLM
  imports cleanly again (verified). lmcache 0.4.6 is now itself broken by the downgrade, but vLLM (the shared
  resource + the thing EXP-0026 used) is the priority and is intact.
- LESSON: NEVER pip-install a heavy package into a shared, working env without a throwaway/cloned env first.
  lmcache 0.4.6 has hard deps (numpy2/transformers5) incompatible with vLLM 0.6.6. To actually run the
  published lmcache kernel (committee path 1), it needs an ISOLATED env (conda clone) — do that next time, or
  pursue path (2)/(3) which don't touch the env.
- SILVER LINING: path (2) (oracle-PIC roofline, EXP-0027) needed only torch (unaffected), and it gave the
  MORE INFORMATIVE answer anyway — CDC's serving advantage is CONDITIONAL vs a fused PIC (vindicating the
  committee's re-impl skepticism). So the broken-env detour still produced the decisive honest result.

### LESSON (orchestration topology) — researcher locked to GPU node can't see the instance/ros.py (which live on the control node)
- I dispatched researcher-0002-harness locked to cli:devgpu014 to build the EXP-0030 connector harness. It
  correctly STOPPED: the research-os instance + ros.py + EXP-0026/0027/0030 artifacts are on cli:dengcchi-mac
  (control node), NOT devgpu014 (GPU node, which has only the vllm/lmcache science env). A single-node-locked
  researcher can't register/heartbeat/read-background/write-deliverable for a cross-node experiment.
- The cross-node GPU workflow (proven in EXP-0026/0021/0025) is: ORCHESTRATOR writes the script to
  devgpu014:/tmp, runs it in ros-vllm, copies results back to the Mac instance. GPU experiments are
  inherently orchestrator-driven (INVARIANT 3) — a GPU-node-locked researcher can't bridge to the instance.
- LESSON: do NOT delegate cross-node GPU-harness work to a node-locked researcher. Either (a) orchestrator
  builds it directly (cross-node), or (b) give the researcher BOTH nodes + the explicit instance path on the Mac.
- Researcher's env verification was valuable: lmcache LMCacheConnectorV1 lives at
  integration/vllm/lmcache_connector_v1.py + vllm_v1_adapter.py; it needs the LIVE vLLM v1 engine forward-context
  to get correctly-shaped kv_caches (confirms the full-connector integration is the real path — the flagged
  "30-day step" — not a quick harness).

### EXP-0030 DECISION — true-lmcache kernel deferred as documented future-work; CLAIM-0006 to committee on the HONEST BRACKET
- A faithful real-lmcache measurement requires the full vLLM-v1 + LMCacheConnectorV1 integration (live engine
  forward-context for correct KV shapes). That is too costly to build correctly tonight, and a shortcut risks
  crashes/misleading numbers (worse than the honest bracket). Per operator guidance, taking the BRACKET to the
  committee: EXP-0026 (CDC wins vs re-impl PIC) + EXP-0027 (CDC conditional vs oracle/fused PIC) bracket the
  answer; true kernel lands between -> CDC serving advantage is inj/seq-CONDITIONAL, magnitude pending full
  integration. EXP-0030 stays a documented future-work item (the connector harness, ~the science's "30-day step").

### DISCIPLINE NOTE (self) — always pass ALL 6 --votes incl area_chair
- VERDICT-0041 was written with 5 --votes (omitted area_chair, which DID vote yellow in committee_run_14).
  final_verdict was correctly yellow (no green fabricated) but the record was incomplete. Monitor flagged it.
  FIX: patched VERDICT-0041 to include area_chair:yellow (+ corrections note). LESSON: when parsing a committee
  run, ALWAYS tally all 6 .out (5 reviewers + area_chair) into --votes — a GREEN promote REQUIRES a true 6/6,
  and even YELLOW records should be complete. Re-verify the area_chair .out vote token every run.

### CLI NIT (researcher-flagged, minor) — `ros agent heartbeat` invalid; heartbeat is TOP-LEVEL `ros heartbeat --agent <id>`
- Multiple researchers tried `ros agent heartbeat ...` (mirroring `ros agent register`) and hit "invalid choice"; the
  correct form is the top-level `ros heartbeat --agent <id>`. The `ros agent register` output even suggests the
  top-level form, but the parallel-structure expectation (register under `ros agent`, so heartbeat under `ros agent`)
  trips researchers. Cosmetic/ergonomics — suggest either aliasing `ros agent heartbeat` -> `ros heartbeat`, or
  documenting it prominently in the researcher prompt. NOT blocking (researchers still register + complete work).

### LESSON (orchestration, orchestrator-r3-001 2026-06-01) — researcher sub-agents DIE writing large files via base64-through-context
- ROOT CAUSE (diagnosed from agent_run.logs, not guessed): two r3 researcher lanes (crosspollinate-r3 sess 2b00aa2d, original ablations-r3) terminated with runStatus=error. The navi workspace->Mac file-transfer DOWNLOAD 401s on this Mac node (monitor-flagged), so researchers fall back to base64-encoding their deliverable and `cat`-ing the blob back through the MODEL CONTEXT. On the 4096-max-token researcher model, round-tripping a ~12-16KB base64 string blows the output/context budget mid-write and the run errors out AFTER the analysis is done but BEFORE the file lands. crosspollinate had a complete, correct 12KB analysis staged to /tmp/note_b64.txt and died cat-ing it.
- RECOVERY that worked: respawn with an explicit CRITICAL FILE-WRITE RULE — write files DIRECTLY on the node via bash heredoc (cat > path <<'EOF' ... EOF), never file-transfer, never base64-through-context; keep heredocs modest and split into multiple files if large. ablations2-r3 (respawn) followed this and successfully wrote 311+199-line scripts + is producing real ablation results (Codex LOSO full dBIC=28.32 Z=-14.04; gate-stripped CC shows self-excitation is PARTLY MECHANICAL — alpha jumps but dBIC drops to ~1.x when permission_gates stripped).
- ALSO: node has NO numpy/scipy (only stdlib python at /usr/local/bin/python3 + /usr/bin/python3); the EXP-0041/0042/0043 machinery is stdlib-only by design — tell stats researchers to reuse it, not import numpy.
- ALSO: researchers must use the FULL engine path /Users/dengcchi/research-os/engine/ros.py (a relative `engine/ros.py` fails — the engine repo is NOT under the instance dir).
- STANDING FIX baked into all subsequent r3 researcher prompts: heredoc-direct file writes + stdlib-only + full ros.py path.

### ARCHITECTURE UPDATE (dengcchi, commit 220d535, 2026-06-01) — SUB-MONITOR delegation + committee QUEUE. ADOPT ON NEXT REBOOT (additive; current run unaffected).
- NEW per-project SUB-MONITOR role: prompts/orchestrator/subagent/sub-monitor.md. On (re)boot, spawn ONE sub-monitor per active project. The sub-monitor OWNS that project's researcher pool: keeps it at floor (research.researchers_per_project), and does ALL researcher-health debugging (investigate-on-death -> diagnose -> respawn-with-fix). ORCHESTRATOR DELEGATES researcher floor/health/debug to sub-monitors and STOPS spawning/poking researchers directly (direct-researcher-spawn path is now DEPRECATED).
- NEW committee-submission QUEUE (replaces ros inbox as the candidate-work channel):
  * `ros queue list` -> pull pending committee-ready submissions a sub-monitor pushed via `ros queue submit`.
  * convene the hostile committee on each (run_committee.sh -> verify ALL_COMMITTEE_DONE + every .err clean of EMPTY_OUTPUT_NO_VOTE), write the parity verdict (real 6/6 for green; unanimous rule; never --override-rule without explicit human OK), then `ros queue ack --id <Q-id> --by orchestrator-<id> --answer <verdict>`.
  * `ros inbox` is now ONLY for sub-monitor HARD-BLOCKER escalations.
- ops_metrics tracks claim_submissions/pending/acked per project; operational/README.md surfaces submission->verdict throughput.
- GLOBAL retire-and-respawn rule codified: at 35% / ~350k tokens, long-running/standby agents (orchestrator, monitor, sub-monitors) must retire with a graceful handoff (the r2 orchestrator DIED at ~51% with 400s — do not exceed; hand off earlier).
- ORCHESTRATOR remains SOLE authority for claims/verdicts/committee/GPU. All safety preserved (real 6/6 green, COMMITTEE_INCOMPLETE never counts, devgpu499 host_mem_floor, never force-demote, CLAIM-0006 parked on vLLM>=0.7).
- ADOPTION PLAN (next reboot): (1) read prompts/orchestrator/subagent/sub-monitor.md; (2) spawn 3 sub-monitors (PROJ-0001/0002/0003), each owning its researcher floor+health; (3) switch my loop from direct-researcher-management to: ros queue list -> committee -> verdict -> queue ack, + handle sub-monitor hard-blockers from ros inbox; (4) honor the 35% retire-and-handoff.

### BUG-27 (monitor 6433b2c0, 2026-06-01) — unvalidated --date minted a phantom verdicts/<PROJ>/9999-01-01/ dir
- SYMPTOM (dengcchi flagged): no new claims/cemetery under date 2026-06-01 → suspected researcher claim-path
  misconfig. INVESTIGATION: seed path is FINE (test seed landed correctly in claims/<PROJ>/2026-06-01/). The
  real find was a stray verdicts/PROJ-0002/9999-01-01/VERDICT-0010.yaml — a 6/6-GREEN for CLAIM-0006 written
  by an early/test run that passed `--date 9999-01-01`. It was an ORPHAN (not in CLAIM-0006 verdict_history;
  the claim is really weakened/4-6 parked per VERDICT-0043). The sentinel date hid it at the bottom of sorts.
- WHY registry looked frozen on 06-01: NOT a bug — researchers since 06-01 are on hold/verify/gapmine lanes
  that (correctly) found frontiers exhausted/human-gated, so they write prior_art notes but never `ros seed
  new` or advance a claim. registry/ is correctly quiescent (symptom of human-gated state, not broken plumbing).
- FIX: engine ros.py _valid_date() — rejects malformed / sentinel / out-of-window (-30d..+1d UTC) --date values,
  warns on stderr, falls back to UTC today. Used by obj_dir() (all new objects) + cmd_verdict_write. No phantom
  date folders can ever be minted again. Orphan VERDICT-0010 moved to registry/_quarantine/ (documented, not
  deleted); status verdict count 47→46 (phantom no longer counted).

### BUG-28 (monitor 87aa00c3, 2026-06-01 ~16:07Z) — ros submonitors false-positive on .converged projects
- SYMPTOM: after PROJ-0001/0004/0005 marked .converged (throughput refill), `ros submonitors` flagged all 3 as
  "❌ NO sub-monitor / ☠️ DEAD — orchestrator MUST spawn a replacement" every cycle, because their retired/dead
  sub-monitors (0004-r5 45m, 0005-r5 70m) had no live successor. But a CONVERGED project's arc is closed — it
  needs NO sub-monitor. The false-positive risked a future orchestrator needlessly respawning sub-monitors for
  dead projects (make-work, the v2 anti-pattern).
- FIX (commit 9ef6827): cmd_submonitors now excludes _is_converged_project() projects from the discovery list;
  reports them separately as "N converged (no sub-monitor needed): PROJ-...". Only ACTIVE (investing/blocked)
  projects require sub-monitor coverage. Verified: now shows "4 active; 3 converged" + "✅ every active project
  has a live sub-monitor" instead of "⚠️ 3 need respawn".
- (Pairs with the cmd_projects concurrent-investment capacity check that ALSO uses _is_converged_project.)

## BUG-31..34 (2026-06-02, monitor 16b52fb1 + dengcchi directive) — AGENT SPRAWL / LINGERING SESSIONS / NO TASK TRACKING
ROOT CAUSE: the entire sub-monitor + orchestrator lifecycle was PROMPT-DRIVEN with NO engine primitive.
Agents self-spawned successors via spawn_agent(new_session) + self-retired at 35% ctx — but the 35% was
consumed re-reading their own bloated handoff prompt + 131-line buglog, NOT real work. Result:
sub-monitor-0015 churned r8->r36 (28+ generations, ~5 NO-CHANGE cycles each) in hours; 191 agent yamls
registered, 52 stuck status:running (nothing ever flipped a dead agent out of 'running'). 18h / 363
commits / ZERO new science (all autosave + retire-respawn + buglog cycles). Self-maintenance became the
workload. (Diagnosed with dengcchi awake; he directed: fix the architecture, no lingering agents, no
lingering researchers, orchestrator must own an incrementing task-id + notification mechanism.)

- BUG-31 Lingering agents: no reaper. FIX: `ros reap [--apply]` (engine/supervise.py). Flips past-grace
  agents still in an alive state -> superseded (fresher r-version live) | retired (converged/no-project,
  clean) | dead (ACTIVE project, no successor -> NOTIFY). Applied once: 45 lingering -> 26 superseded,
  17 retired, 2 dead. status:running 52 -> 9.
- BUG-32 Heartbeat-only handoff: retiring agent passed no STATE about its monitored researcher/seeder.
  FIX: `ros handoff --from --to --researcher-state --seeder-state --open-work --evidence-delta
  [--reseed-needed] [--task]`. Writes a structured handoff artifact + transfers the task carrying state;
  --reseed-needed emits a RESEED_NEEDED orchestrator notification (dead seeder + open work -> dispatch fresh).
- BUG-33 No system task tracking: no incrementing job id / parent-assignee tree. FIX: task ledger
  `ros task open|update|list` -> registry/tasks/TASK-NNNN.yaml (incrementing via next_id, parent edge =
  supervision tree, evidence_delta field). `ros tree` renders the live supervision tree.
- BUG-34 No structured coverage-loss notification: submonitors only PRINTED. FIX: reaper + handoff drop
  action-flagged AGENT_DOWN / TASK_ORPHANED / RESEED_NEEDED entries into the orchestrator inbox (Channel).
FILES: engine/supervise.py (new, ~210 lines, stdlib+pyyaml), engine/ros.py (+5 handlers, +4 subparsers,
_sup_helpers bundle to avoid circular import). AST-validated; all 4 commands smoke-tested on live instance.
NOTE: orchestrator/sub-monitor PROMPT loops were DISABLED in the scheduler (4 jobs) to stop the spawn
runaway while this landed. NEXT (design, not yet done): collapse sub-monitors into orchestrator sub-agents
or a single multi-lane poller so the architecture STRUCTURALLY cannot sprawl; rewire spawn to set parent
edge + open a TASK; mark researchers 'completed' on EXP terminal so they aren't reaped as false-dead.

## BUG-35..41 (2026-06-02, monitor 16b52fb1 — BUGBASH w/ dengcchi, 3 focus areas) — RETIRE/INHERIT/HIERARCHY edges
Bugbash in isolated /tmp/bugbash instance (found+fixed a test-hygiene leak first: config runtime_dir was
absolute -> test agents leaked into LIVE runtime; cleaned + made test runtime_dir local).

- BUG-35 handoff did NOT re-parent the researcher TASK (only moved the monitor task) -> researcher's
  supervisory parent broke silently on sub-monitor retire.
- BUG-36 handoff did not register successor nor flip predecessor -> `submonitors` still showed the OLD
  sub-monitor alive; successor was fiction until a separate prompt step. Split-state if prompt died mid-handoff.
- BUG-37 retire was 3 non-atomic prompt steps (handoff + register + stop-hb) -> any interruption = ghost.
  FIX BUG-35/36/37: `ros retire --from --to [--project --researcher-state --seeder-state --open-work
  --evidence-delta --reseed-needed --by]` — ONE atomic engine call: registers successor inheriting
  parent/project edges, re-parents EVERY task assigned-to OR parented-by frm -> to, re-parents EVERY
  supervised agent (parent==frm) -> to, flips frm->retired(+retired_to), writes structured handoff,
  optional RESEED_NEEDED notify. Tested: alive-researcher inherit clean; dead-researcher+reseed notifies
  orchestrator + reap orphans the task (belt-and-suspenders).
- BUG-38 (minor) retire leaves the dead researcher's task assignee=corpse; reap independently re-flags it
  orphaned + notifies. Acceptable (double-signal). 
- BUG-39 self-retire (from==to) bricked the lane (final write = retired -> false coverage gap). FIX: reject.
- BUG-40 retire to an id already held by a DIFFERENT live agent clobbered it (flipped a live researcher's
  role to sub-monitor). FIX: reject clobber of a live different-role/non-successor agent.
- BUG-41 ★ THE RECURRING FALSE-FLAG (cost every prior monitor cycles): `ros submonitors` (and
  `coordinators`) kept the FRESHEST-BY-AGE agent per project, ignoring status. When a sub-monitor retired
  in the SAME tick its successor registered, the just-retired r1 (age 0.0m) tied/beat the live r2 ->
  "retired-no-successor — respawn" FALSE-FLAG (risked double-spawn). FIX: prefer a LIVE agent over a
  terminal one (status beats age; freshest only within same liveness class). Applied to BOTH submonitors
  + coordinators. This is the root cause of the "0013/0015 lane false-flag" my predecessors hand-waved.

NEW CMDS: ros retire, ros project-tree (area-3 hierarchical memory: project->live sub-monitor(+gen count)
->claim-seeders[active/killed]->live researchers; reads COMMITTED registry index not per-agent jsonl/
buglog -> bounded memory, fixes the "re-read 131-line buglog every generation -> 35% ctx -> respawn"
overflow loop). agent register gains --parent (supervision-tree edge). tree now renders nested hierarchy.
FILES: engine/supervise.py (+retire +project_tree +guards), engine/ros.py (+cmd_retire +cmd_project_tree,
--parent on register, submonitors+coordinators live-preference fix, nested tree). AST-validated; all edges
tested in isolation. Live coordinators regression-clean.

## BUG-43..52 (2026-06-02, monitor 16b52fb1 — BUGBASH #2: concurrency/atomicity/recovery) 
Discovered a PRIOR timed-out turn of mine had written (uncommitted) fixes BUG-43/46/47/48/49 to
supervise.py that were NEVER VALIDATED. Bugbash #2 validated them, found one fatal + several real bugs.

- BUG-43 task-id race: next_id (max-scan+write) collided under concurrent `task open`. FIX (recovered):
  _alloc_task_id via O_CREAT|O_EXCL placeholder + bump-on-collision. VALIDATED: 8 parallel -> 8 unique.
- BUG-46 task status not validated (typo silently corrupts ledger). FIX (recovered): validate vs TASK_STATES.
- BUG-47 terminal task (done/dropped) was mutable (could be reopened). FIX (recovered): immutable unless _internal.
- BUG-48 blind RESEED_NEEDED could make orchestrator double-spawn onto a still-live researcher. FIX
  (recovered): _live_researchers cross-check -> downgrade to RESEED_CONFLICT ("verify, do not double-spawn").
- BUG-49 reaper superseding an agent didn't re-parent its LIVE children -> tree fragments. FIX (recovered):
  re-parent children + parented-tasks to the live successor on supersede. VALIDATED.
- ★ BUG-50 (NEW, fatal): the recovered BUG-43 _alloc_task_id used re.search but supervise.py NEVER imported
  `re` -> EVERY `ros task open` crashed NameError (silent under backgrounded stderr; the 8-parallel test
  produced ZERO files). This is why uncommitted/unvalidated code is dangerous. FIX: import re. Re-validated
  8 parallel -> 8 unique, no empty placeholders.
- BUG-51 (cosmetic): cmd_retire printed "RESEED_NEEDED" even when handoff downgraded to RESEED_CONFLICT.
  FIX: retire() now propagates reseed_conflict; cmd_retire prints the accurate one.
- ★ BUG-52 (NEW, HIGH-SEVERITY, pre-existing in core engine): next_id() for CLAIM/EXP/VERDICT/DEAD was
  non-atomic (max-scan+return). 6 parallel `seed new` ALL got CLAIM-0001 and clobbered each other -> 5 of 6
  claims SILENTLY LOST. Same for verdicts/experiments/cemetery. Any concurrent seed/verdict by two
  sub-monitors/orchestrators destroyed scientific ledger data. FIX: next_id now serializes under a per-
  (root,kind) O_EXCL lockfile (30s stale-break) + persists a reservation high-watermark covering the window
  before the caller writes its file. VALIDATED: 6 parallel seed -> CLAIM-0001..0006 unique; 5 parallel
  verdict -> VERDICT-0001..0005 unique. Reap verified idempotent (double-apply clean).
FILES: engine/supervise.py (+re import, +retire reseed_conflict propagation; BUG-43/46/47/48/49 recovered),
engine/ros.py (next_id atomic lock+reservation; cmd_retire accurate reseed print). AST-valid; all tested in
isolated /tmp/bb* instances. NOTE: bugbash also caught a TEST-HYGIENE issue — config runtime_dir was
absolute, leaking test agents into live runtime; always set a local runtime_dir for test instances.

## BUG-53..55 (2026-06-02, monitor 16b52fb1 — BUGBASH #3: full GPU cycle self-troubleshoot, dengcchi napping)
Goal (dengcchi): self-troubleshoot until a GPU exp runs a FULL cycle with no problems. Walked the entire
pipeline in isolated /tmp/gpu: seed -> exp register(GPU) -> committee-approve(verdict --approves-exp) ->
gpu-task submit -> exp dispatch -> gpu-result submit -> drain/ack -> exp complete. Found 3 real bugs.

- BUG-53 `gpu status` was BLIND to the v2 gpu-task CHANNEL (only read the legacy gpu_queue), so it
  reported "QUEUE 0 pending" while tasks waited in the channel orchestrators actually use. An orchestrator
  checking status would think nothing's queued. FIX: gpu status now also surfaces the gpu-task channel
  pending list ("TASK CHANNEL (N pending)").
- ★ BUG-54 (safety) `exp dispatch` wrote node_lease onto the experiment.yaml but NOT into the shared
  gpu_queue leases map that `gpu status`/`gpu poll`/`gpu release` read -> node showed FREE after dispatch
  -> a 2nd dispatch could DOUBLE-BOOK the GPU (critical on fragile MI350X). And `exp complete` never
  released the lease -> node leased forever. FIX: dispatch records the lease + REFUSES an already-leased
  node (double-book guard); exp complete releases the lease. VALIDATED: BUSY after dispatch, double-book
  refused, FREE after complete.
- ★ BUG-55 (safety/recovery) a FAULTED GPU run (`gpu-result submit --fault`) left the node leased FOREVER
  (esp. fragile MI350X stuck BUSY -> orchestrator never re-dispatches). FIX: on --fault, auto-release the
  node lease + mark exp 'faulted' (not stuck 'running'); `exp dispatch` now accepts 'faulted' exps for
  re-dispatch (recovery). VALIDATED full cycle: dispatch->fault(auto-free,faulted)->re-dispatch(recovered)
  ->success->complete(free).
ALSO VERIFIED CLEAN: committee-approval gate refuses un-approved exps at BOTH gpu-task submit AND dispatch;
fragile-node host_mem_floor gate refuses no-floor MI350X at BOTH entry points (never waived); result/task
channels drain+ack correctly; claim lifecycle propagates (evidence_ready). H100 (non-fragile) + MI350X
(fragile) both run a full cycle with zero manual intervention.
FILES: engine/ros.py (cmd_gpu_status task-channel view, cmd_exp_dispatch lease record+double-book guard,
cmd_exp_complete lease release, cmd_gpu_result_submit fault auto-release+faulted state, dispatch accepts
faulted). AST-valid; all tested in isolation.

## 2026-06-02 ~14:30 UTC — BUGBASH #4 (true e2e baking, monitor successor): COMMITTEE/VERDICT GATING

Probed the SCIENTIFIC GATE (`ros verdict write` green/promote enforcement) in isolated /tmp/bb_committee
(local runtime_dir, no leak). The committee DISPATCH side (run_committee.sh) was already hardened
(BUG-12/20b/21/22: EMPTY_OUTPUT_NO_VOTE, ALL_COMMITTEE_DONE gate, COMMITTEE_INCOMPLETE, FD-9 short-read
guard). But the CONSUMPTION side — how ros.py tallies the votes a human/orchestrator passes via --votes —
had two integrity holes that let a non-real-6/6 pass as green/promote:

- ★ BUG-56 (HIGH-SEV integrity) green/promote gate counted VOTES not MEMBERS. Old check was just
  `len(parsed) >= nmembers` + "no value != green". So `novelty_killer:green,novelty_killer:green,...`
  (duplicate role padding the count to 6) with **area_chair=FINAL_VERDICT entirely MISSING** PASSED as
  "6/6 green". The single most important gate in the system (real 6/6 for green) could be satisfied
  without the chair ever voting and with a member double-counted. ROOT CAUSE: no per-role coverage check.
- ★ BUG-57 (integrity) arbitrary/unknown role names accepted. `a:green,b:green,...,f:green` (none of them
  configured committee members) PASSED. A typo'd or fabricated slate, or one that swaps a real member for
  a placeholder, sailed through. ROOT CAUSE: voted roles never validated ⊆ configured member roles.

FIX (ros.py cmd_verdict_write, green/promote branch): the gate now derives member_roles from config
committee.members and requires, for green/promote (unless --override-rule):
  (1) EVERY configured member role present by name (missing area_chair -> REFUSE),
  (2) each role appears AT MOST ONCE (no duplicate-role padding),
  (3) NO unknown roles (votes ⊆ configured members),
  (4) unanimous rule: every member's vote == green (lists the specific non-green role:vote).
--override-rule still bypasses (explicit escape hatch, prints votes N/6). yellow/red/kill/needs-more
unchanged (no unanimity requirement — honest yellow/kill is first-class).

VALIDATED (11 probes, all correct):
  3-votes->REFUSE missing 3; 6-with-1-yellow->REFUSE non-green; full-6-distinct-green->PASS;
  dup-role-pad(area_chair missing)->REFUSE duplicate; 7-bogus-roles->REFUSE missing all; 6-bogus->REFUSE;
  area_chair-swapped-for-x->REFUSE missing area_chair; promote-full-6->PASS; override-rule-2-votes->PASS.
SAFETY: real 6/6 (every named member green) now structurally required for green/promote; area_chair can
no longer be silently dropped; no fabricated/duplicate roles count. COMMITTEE_INCOMPLETE (dispatch side)
still never produces an ALL_COMMITTEE_DONE. AST-valid.

## 2026-06-02 ~14:45 UTC — BUGBASH #4 cont: VERDICT->CLAIM lifecycle/status consistency (BUG-58/58b)

Walked seed->exp->green->promote->stray-kill in isolated /tmp/bb2_lifecycle. Two state-machine bugs:

- ★ BUG-58 (lifecycle/UX) a GREEN verdict (real 6/6 pass) set claim next_action = the YELLOW/RED string
  "address required_evidence to advance". So every green claim lingered in `ros resume` telling the
  orchestrator to fix evidence it had ALREADY cleared — exactly the kind of phantom open-work that fed the
  agent-sprawl idleness (an orchestrator re-reading a green as "still needs evidence"). ROOT CAUSE: the
  verdict_write else-branch lumped green with yellow/red. FIX: green now sets status='green' +
  lifecycle='verdict_recorded' + an honest next_action ("promote or close; green-lift/follow-on optional,
  not required"). Green stays non-terminal (green-lift/promote may follow, e.g. the egress-held CLAIM-0026
  path) but no longer reads as unfinished.

- ★ BUG-58b (SAFETY) a PROMOTE *verdict* never set claim status='promoted' — only the exp_complete
  --effect promote path did. But the BUG-25 demote-guard (refuses a stray kill/weaken exp from
  auto-demoting a top result) keys on status=='promoted'. So a claim promoted by COMMITTEE VERDICT was
  left status='seed' and was NOT protected — a mis-bound kill exp could silently auto-demote a 6/6-green
  promoted result. FIX: promote verdict now sets status='promoted' (and kill verdict sets status='dead'),
  mirroring exp_complete. VALIDATED: after promote verdict, status='promoted'; a subsequent stray
  `exp complete --effect kill` on that claim is REFUSED by the BUG-25 guard (needs explicit --force-demote
  + fresh committee). Top results are now actually immutable to stray exps regardless of promote path.

FILES: engine/ros.py cmd_verdict_write (green/promote/kill claim status+next_action). AST-valid.

## 2026-06-02 ~15:00 UTC — BUGBASH #4 cont: ★ BUG-59 (HIGH-SEV silent data loss) — Channel rmw race

Stress-tested the COMMITTEE QUEUE end-to-end (Area 3). 6 PARALLEL `ros queue submit` of DISTINCT claims
-> only 2 survived. Four submissions collided on the same Q-id and CLOBBERED each other.

★ BUG-59 (HIGH-SEV, silent data loss) channeling/channel.py Channel.submit/ack did a non-atomic
  READ-MODIFY-WRITE: _read() current state -> _next_id (= len+1) -> append -> _dump. _dump is atomic
  PER-WRITE (tempfile+os.replace), but two concurrent submitters both read the same state, compute the
  SAME next id, and the 2nd os.replace overwrites the 1st. SAME class as BUG-43/52 (registry next_id),
  but in the CHANNEL layer — which backs the orchestrator INBOX, the COMMITTEE QUEUE, and the GPU
  TASK + RESULT channels. Real-world impact: two sub-monitors submitting committee requests at the same
  time -> one researcher's work silently never reviewed; two GPU results landing together -> one
  faulted/completed run the orchestrator never drains (node stuck, or a real result lost). Prior bugbashes
  hardened registry next_id but NEVER stress-tested the Channel — this was live the whole time.

FIX: serialize the whole submit/ack read-modify-write under a per-channel O_EXCL lockfile (_FileLock,
  30s timeout, 60s stale-lock reclaim for crashed holders) — same pattern as the BUG-52 next_id fix.
  Also: cmd_queue_submit did a SECOND unlocked read-modify-write (the queue_id back-compat mirror) AFTER
  submit() returned -> re-introduced the race; moved the mirror INSIDE submit() (new mirror_id_key arg,
  written under the lock). And cmd_queue_ack's legacy back-compat branch did another unlocked rmw -> folded
  into Channel.ack via a new mirror_key arg (matches legacy queue_id items inside the lock).

VALIDATED (isolated /tmp/bb3_qrace, /tmp/bb4_gpurace):
  - 6 parallel committee submits -> 6 UNIQUE Q-ids, all 6 survive, queue_id mirrored on all 6, no stderr.
  - 6 parallel GPU-RESULT submits (distinct exps) -> 6 unique GR-ids, all survive (the scariest channel).
  - submit/ack/re-submit-after-ack regression clean; dedup still blocks duplicate PENDING; re-review
    after ack re-queues correctly.
FILES: channeling/channel.py (_FileLock + locked submit/ack + mirror_id_key/mirror_key), ros.py
  (cmd_queue_submit mirror inside lock, cmd_queue_ack via mirror_key). AST-valid.

## 2026-06-02 ~15:20 UTC — BUGBASH #4 cont: BUG-60 (anti-sprawl) — researcher false-DEAD on EXP-terminal

This is one of dengcchi's named anti-sprawl items ("mark researchers 'completed' on EXP-terminal so they
aren't reaped as false-dead"). Walked the reaper interaction with a finished researcher.

★ BUG-60 (anti-sprawl / false-DEAD) `ros exp complete` updated the experiment + the claim ledger but
  NEVER touched the RESEARCHER AGENT's status. So a researcher that finished its only experiment stayed
  status:running in runtime/agents/, went past-grace, and `ros reap` flagged it DEAD (ACTIVE project, no
  live successor) — a FALSE coverage gap that fired a spurious AGENT_DOWN notification and tempted the
  orchestrator/sub-monitor to RESPAWN a researcher whose work was already done. This false-DEAD churn is a
  direct contributor to the agent-sprawl idleness dengcchi diagnosed (the system constantly "rescuing"
  agents that had simply finished).

FIX: `ros exp complete --by <agent>` (explicit owner id — NO fragile id string-matching, which is the
  BUG-26/29 trap) now marks the owning RESEARCHER agent 'completed' on EXP-terminal, but ONLY if:
    (a) it's a researcher (never a sub-monitor/orchestrator/coordinator),
    (b) it has NO OTHER pending/running/dispatched/faulted experiment (don't kill an agent mid-second-exp).
  Owner resolves from --by, or the experiment's recorded ran_by/dispatched_by (so GPU-dispatched exps
  auto-resolve). Reaper then sees a terminal agent and leaves it alone (no DEAD, no AGENT_DOWN, no respawn).
VALIDATED (/tmp/bb5_reaper): single-exp researcher -> completed on exp complete, reap reports "no lingering
  agents" (was DEAD-flagged before); two-exp researcher stays 'running' after 1st exp completes, flips to
  'completed' only after the LAST exp completes.
FILES: engine/ros.py cmd_exp_complete (owner auto-complete block) + exp complete --by arg. AST-valid.

## 2026-06-02 ~15:35 UTC — BUGBASH #4 cont: BUG-60b + full-lifecycle cross-command integration test

Ran a FULL claim lifecycle in one isolated instance (/tmp/bb6_e2e, /tmp/bb7_taskclose) exercising the new
reaper/task/retire/tree primitives together: agent-register(orch->sub-monitor->researcher supervision tree)
-> seed -> task open -> exp register -> exp complete --by (auto-completes researcher) -> queue submit
-> queue list -> green verdict (real 6/6) -> queue ack -> resume. ALL consistent end-to-end:
  - exp complete --by flips researcher to completed AND (BUG-60b below) closes its open task;
  - reap correctly reports "no lingering agents" (completed researcher is terminal, NOT false-DEAD);
  - tree renders orch->sub-monitor->[completed]researcher hierarchy;
  - green verdict sets status=green + honest next_action; resume shows it correctly.

★ BUG-60b (task-ledger tidiness / anti-sprawl) found during the integration test: a researcher that
  auto-completes on EXP-terminal left its assigned TASK still status:open forever -> stale-open tasks
  accumulate for finished researchers (and a future reap of any re-flagged agent could orphan them). FIX:
  when exp complete --by marks a researcher completed, it now also closes that researcher's open/active
  tasks (status=done, via supervise.task_update _internal, best-effort/non-fatal). VALIDATED: TASK-0001
  goes open->done on exp complete; `task list --open` empty after. The task ledger no longer leaks tasks
  for done researchers.
FILES: engine/ros.py cmd_exp_complete (task-close in the owner-complete block). AST-valid.

## 2026-06-02 ~16:00 UTC — BUGBASH #4: THE BIG ONE — structural anti-sprawl (design + `ros lanes`)

Addressed dengcchi's top structural item: collapse the N self-spawning sub-monitor SESSIONS (the root
cause of the 18h productive-idleness sprawl) into a SINGLE multi-lane POLLER. Wrote the design doc
(learning/DESIGN_anti-sprawl_single-poller.md) + built the engine primitive it relies on.

DESIGN (full doc): EXACTLY 2 standing sessions — poller + orchestrator — instead of 4-15 self-replicating
ones. A "lane" = one active project's observe+forward duty (what a sub-monitor did), but a lane is a LOOP
ITERATION, not a session. No lane spawns a session. Only the poller + orchestrator hand off, one
generation at a time, only at their own context limit -> generation growth bounded to O(time), not
O(time x projects). The 28-generation sub-monitor-0015 churn becomes structurally impossible.

NEW: `ros lanes` (read-only — computes a plan, never spawns/mutates). For every active (non-converged)
project it emits the ONE next action the single poller should take:
  HOLD    = below floor, no open work -> NO-OP (silent; no commit -> kills the 363-commits/no-science churn)
  AWAIT   = researcher running OR committee submission pending -> just heartbeat
  FORWARD = claim evidence_ready + not yet queued -> poller `ros queue submit` (observe+forward; never judge)
  RESEED? = no live researcher + open non-terminal/non-green claim -> FLAG for orchestrator (lane NEVER
            auto-respawns; orchestrator owns reseed via the existing reaper AGENT_DOWN/RESEED_NEEDED notif)
Exits non-zero if any lane is FORWARD/RESEED? so the poller wrapper branches; one poller heartbeat replaces
N sub-monitor heartbeats.

VALIDATED (/tmp/bb9_lanes, 4 projects exercising all states): FORWARD (evidence_ready unqueued), AWAIT
(live researcher), RESEED? (open claim no researcher), HOLD (converged excluded). Verified the full lane
state machine CLOSES: FORWARD -> (poller queues) -> AWAIT (pending) -> (orchestrator acks + green verdict)
-> HOLD (silent, no make-work). A green claim with no pending queue correctly becomes a silent HOLD.

STATUS: design + primitive READY. NOT YET MIGRATED — the system stays FROZEN until dengcchi approves the
poller-session cutover (write ONE poller schedule job, remove the per-sub-monitor loop jobs, reap the
historical roster once). Anti-sprawl invariants (auto-open task on spawn = BUG-60 task wiring; researcher
auto-complete on EXP-terminal = BUG-60; atomic task-id + notifications = BUG-31..34/52/59) are all in place.
FILES: engine/ros.py cmd_lanes + parser; learning/DESIGN_anti-sprawl_single-poller.md. AST-valid.

## 2026-06-02 ~15:55 UTC — BUG-61 (ros lanes mis-classified verdict_recorded as RESEED?) — found via Navi-orchestrator validation

While watching the Navi-session orchestrator (validation instance) run a full pipeline, both lanes whose
claims had a recorded YELLOW verdict showed RESEED? for ~34 min, and the orchestrator correctly hesitated
(a yellow doesn't mean "spawn a fresh L0").

★ BUG-61 (lane classification) `ros lanes` lumped EVERY non-terminal/non-green in-flight claim into
  RESEED? — including verdict_recorded (committee already ruled, e.g. yellow/needs-more-evidence). But a
  verdict_recorded claim is a DIFFERENT state than a fresh drafted claim:
    - drafted / experiment_designing, no researcher -> genuinely RESEED? (spawn an L0 researcher).
    - verdict_recorded (yellow) -> ADVANCE? : the committee asked for SPECIFIC required_evidence. The
      right move is an ORCHESTRATOR-JUDGMENT targeted follow-up (or accept the honest yellow as converged)
      — NOT a blind reseed that re-runs the same L0 the committee already saw.
  Conflating them would make a real orchestrator churn (re-running redundant experiments) or look stuck.
FIX: cmd_lanes now splits open_claims into reseed_open (lifecycle != verdict_recorded) vs verdict_open
  (== verdict_recorded). New ADVANCE? action (🔬) for verdict_open with the last verdict result + guidance
  "dispatch TARGETED follow-up for required_evidence OR accept/converge (NOT a blind reseed)". RESEED? now
  fires only for un-experimented claims. Both are actionable (exit 3). Updated the orchestrator charter +
  self-check job to handle ADVANCE? as a judgment call (no make-work, no 'await dengcchi').
VALIDATED (/tmp/bb_lanes2 + live validation instance): drafted claim -> RESEED?; yellow-verdict claim ->
  ADVANCE?. The validation instance's 2 yellows reclassified RESEED? -> ADVANCE? correctly.
FILES: engine/ros.py cmd_lanes. AST-valid.

## 2026-06-02 ~19:10 UTC — v3 PHASE 1: read-only monitor eyes (ros cron-health + ros progress) [v3-impl session#2]

NOT a bug fix — these are the two net-new READ-ONLY engine commands the v3 deterministic monitor cron
needs (DESIGN_v3_lean_architecture.md monitor jobs #1 and #4). Lowest-risk phase: pure reads, no spawn,
no mutate. Built against engine HEAD 39a80cd -> committed 03dcd71 (pushed HTTPS lokic233/research-os).

`ros cron-health` (monitor #1): reads runtime/cron/<job>.alive stamps. Every v3 cron drops its .alive on
  a successful run; this flags FRESH / STALE (age > alive_stale_x x interval) / NEVER_STARTED per cron,
  reading the interval+stale-multiplier from config `crons:` (falls back to design defaults monitor=5/
  coordinator=2/committee_health=1/proj_monitor=5, all x3). Exit 3 + "ESCALATE TO TROUBLESHOOTER" on any
  dead/stalled cron. `--cron <name>` checks a single cron.

`ros progress` (monitor #4, "work isn't landing"): time-since-last-REAL-progress per in-flight claim (not
  liveness). Three stall types from the v3 stall taxonomy:
   - local-but-uncommitted    : `git status --porcelain` shows the claim's registry file dirty + mtime > stall_min
   - committee-done-no-verdict : a committee_run_*<CLAIM>* dir has _status==ALL_COMMITTEE_DONE but the newest
                                 verdict file mtime is OLDER than that run's finish — TWO-PASS aware (a pass#1
                                 verdict can't mask a pass#2 run that finished later with no new verdict)
   - gpu-result-not-resubmitted: an unacked gpu_results channel item for one of the claim's active/cited exps
  Thresholds from config progress.stall_min(20) / gpu_stall_min(30). Over threshold -> exit 3 + "NOTIFY
  ORCHESTRATOR". Worst-first ordering. Green/terminal claims excluded; pending-queue claims not double-flagged.

VALIDATED (isolated /tmp instances, LOCAL runtime_dir -> zero live leak): cron FRESH/STALE/NEVER_STARTED +
  --cron filter; all 3 stall types fire then resolve cleanly (commit / verdict / ack); two-pass pass#2-after-
  pass#1-verdict correctly stalls then clears when a newer verdict lands; no false positives on a fully
  committed/dispositioned instance. Regression: status/lanes/--help intact on live v2; live v2 untouched.
FILES: engine/ros.py (cmd_cron_health, cmd_progress, _cron_table, _alive_age_min, _git_committed_clean +
  2 parser entries). AST-valid. v3 instance config (crons:/progress:) already carries the thresholds.

## 2026-06-02 ~19:20 UTC — v3 PHASES 2-4 [v3-impl session#2] (engine dbe4274)

P2 TWO-TIER LEARNING (529beda): `ros learn warm|note|distill`. Tier-1 learning/roles/<fam>.md (curated
  warm-start, read on boot) + Tier-2 learning/<fam>/YYYY-MM-DD.md (append-only daily). _role_family folds
  agent ids -> 7 families (committee = the 6 member roles). distill appends to BOTH tiers @retire,
  warns >16KB. Seeded v3 Tier-1 brains (orchestrator/researcher/committee, bef778b in v3 instance).
P3 EVER-RUN CONTRACT (61e4309): heartbeat --tokens (-> tokens_used) + `ros ceiling` (read-only):
  OVER(>=350k)/WARN(>=85%)/OK per live ever-run agent. Full lifecycle validated: OVER -> learn distill ->
  ros retire atomic to ONE successor -> drops off, successor OK. Agents do NOT self-kill at ctx%.
P4 THE 4 CRONS as deterministic SCRIPTS (dbe4274): engine/crons/*.sh + ros notify (escalation primitive
  -> orchestrator inbox | troubleshooter file). Each WRAPS hardened primitives (no BUG-31..61 regression),
  drops runtime/cron/<job>.alive ONLY on success. monitor(5m): cron-health #1 --exclude monitor ->
  troubleshooter, progress #4 -> orchestrator; coordinator(2m): self-feed -> exp dispatch (engine owns
  lease/floor/approval refusal); committee_health(1m): ALL_COMMITTEE_DONE+no EMPTY_OUTPUT_NO_VOTE ->
  READY else INCOMPLETE (idempotent sentinel); proj_monitor(5m): ros lanes -> FORWARD/RESEED?/ADVANCE?.
  cron-health gains --exclude (monitor doesn't self-flag; MAIN NAVI watches the monitor's .alive).
  All validated in isolated /tmp instances (LOCAL runtime_dir, zero live leak). Regression clean.
NEXT: P5 wire-up (cron entries in STANDBY — not enabled) + standby validation cycle -> escalate dengcchi
  for cutover. THEN bugbash rounds (dengcchi requested).

## 2026-06-02 ~20:55 UTC — v3 BUGBASH ROUND 1: BUG-62..64 (cron robustness; minimal fixes) [v3-impl session#2]
- BUG-62 (path safety): _common.sh stamped .alive to '/cron' when RUNTIME_DIR() couldn't resolve (broken
  python/missing config); no-stamp was ACCIDENTAL (relied on /cron unwritable). FIX: resolve once, fail-fast
  exit 1 if empty/'/'. (engine 84db8a0)
- BUG-63 (notify churn): proj_monitor re-notified RESEED?/ADVANCE? every 5m for a stuck lane -> orchestrator
  inbox churn. FIX: one sentinel per (lane,action) under $CRON_DIR/.proj_notified; notify ONCE, clear when
  the lane leaves that state. FORWARD self-clears (queue dedup). (engine 2266950)
- BUG-64 (notify churn): monitor (CRON_DEAD/WORK_NOT_LANDING) + coordinator (GPU_FAULT) re-escalated every
  cycle. FIX: _changed sentinel — re-notify only when the condition CONTENT changes (new failure still
  escalates; unchanged stays quiet; clears when condition ends). (engine 06fb8ef)
- All 3 minimal, reuse the existing sentinel-file pattern (no new mechanism). Standby cycle stays clean.
