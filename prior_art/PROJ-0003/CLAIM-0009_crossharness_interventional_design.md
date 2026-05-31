# CLAIM-0009 — Cross-Harness + Interventional Experiment Design (+ on-node data-hunt result)

**Author:** researcher-0003-laneD · **Date:** 2026-05-31 · **Domain:** MAP-0002 · **CPU-only (design + small replication)**
**Status of CLAIM-0009:** WEAKENED to a gate-type+harness-routing CHARACTERIZATION (config fact). Per
VERDICT-0020 (6/6 yellow) + VERDICT-0021 + EXP-0012: error-class & gate-type are **observationally
INSEPARABLE** on the single Claude Code corpus (error-class lift over gate-type-only LOO-Brier = −0.0043;
1 REDIRECTABLE bit ≈ full 17-class taxonomy; error-class→gate-type is a perfect function). The two
remaining GREEN-path blockers are NON-CPU-on-this-corpus:
  (1) **cross-harness replication** — need a 2nd agent-trace corpus to break "routing-as-constant".
  (2) **interventional routing-alteration** — alter the harness route for one class, verify modality
       follows the RULE, not the error-class.

This document (a) designs both experiments precisely with exact pass/fail, and (b) reports the on-node
data-hunt: a **second AND third agent-trace corpus DO exist on this node** (OpenAI Codex CLI:
`~/.codex/sessions`, 89 sessions; Gemini CLI: `~/.gemini/tmp/*/chats`, 62 sessions), and a SMALL
cross-harness check was run on the Codex corpus. **The gate is therefore PARTIALLY UNBLOCKED on-node**
(observational cross-harness is now CPU-doable); only the interventional arm still needs harness control.

---

## PART A — EXPERIMENT DESIGNS

### A1. The exact confound to break
On Claude Code, every error-class maps to exactly one gate-type (`error-class → gate-type` is a perfect
function), so the modality signal cannot be attributed to error-class vs gate-type. Two ways to break it:
- **Cross-harness:** if the SAME error-class maps to a DIFFERENT gate-type (or recovers with a DIFFERENT
  modality) under a different harness, then modality is the harness's routing rule, not an intrinsic
  property of the error-class. Conversely, if the gate→modality mapping replicates across harnesses
  despite different tool inventories, the gate-type characterization generalizes (the desired GREEN result).
- **Interventional:** hold the error fixed, change ONLY the harness route, and watch modality change.
  This is the gold-standard causal separation.

---

### A2. CROSS-HARNESS REPLICATION — design

**Goal.** Test whether the *redirectable-vs-terminal gate taxonomy* and the *gate-type→modality* mapping
replicate on ≥1 non-Claude-Code agent-trace corpus.

**What a 2nd corpus must contain (sufficiency criteria):**
1. Ordered tool-call traces with (a) tool name, (b) call arguments, (c) per-call success/failure ground
   truth (exit code, error string, or structured error flag), and (d) enough volume for ≥10 failures in
   ≥2 distinct gate-types.
2. At least ONE harness-level policy/permission gate (a tool blocked with a *sanctioned alternative*
   available) so the REDIRECTABLE pole is testable. Without this, only the TRANSIENT/SAME-TOOL pole
   is observable (still useful as a contrast).
3. Distinct tool inventory / routing layer from Claude Code (so "routing-as-constant" is genuinely
   broken, not the same harness relabeled).

**Candidate corpora (in priority order):**
- **OpenAI Codex CLI** (`~/.codex/sessions/**/*.jsonl`) — rollout logs; `function_call`/
  `function_call_output` joined by `call_id`; shell via `exec_command` (exit codes), web via MCP
  `three_pai_external_web_search`, URL-fetch via `knowledge_load` (MCP, can be input-filter-blocked).
  **PRESENT ON NODE — used for the A2 check below.**
- **Gemini CLI** (`~/.gemini/tmp/*/chats/session-*.json`) — `messages[].toolCalls[].result[].functionResponse`;
  tools `glob/read_file/run_shell_command/...`. **PRESENT ON NODE (62 sessions) — schema verified, not
  yet analyzed; a viable third corpus.**
- **External (off-node) public agent-trace logs** if more harness diversity is wanted:
  SWE-agent trajectory `.traj` files, OpenHands/OpenDevin event-stream logs, LangGraph checkpoint/run
  traces. These add genuinely different routing layers (SWE-agent has a fixed ACI command set;
  OpenHands has a sandboxed bash+browser+editor with explicit error events; LangGraph exposes a
  deterministic node graph). Off-node = needs download (NOT on this node).

**Method (reuse EXP-0009 machinery, re-implement the parse layer per schema):**
- Parse → ordered calls with intent-class + canonical routing-tool id + is_error.
- Classify failures into an error taxonomy; map each to a gate-type
  (REDIRECTABLE = hard tool-block w/ sanctioned alternative; GRANT_REQUIRED = permission gate;
  TRANSIENT = fixable-in-place / re-runnable).
- BROAD recovery (same-intent retry success OR cross-tool same-intent success within K=6).
- Modality label SAME_TOOL_RETRY vs CROSS_TOOL_REDIRECT (A-wins-ties; report B-priority + STRICT
  cross-tool-NAME variants).
- Per-gate redirect-share + Wilson 95% CI; gate→modality Theil U / Cramér's V; out-of-sample LOO-Brier.

**EXACT PASS/FAIL (the test that separates error-class from gate-type):**
- **PASS-as-gate-characterization (the GREEN-positive result):** the *gate-type → modality* mapping
  replicates — REDIRECTABLE gates recover ≫50% by cross-tool redirect, GRANT_REQUIRED / TRANSIENT
  recover ≫50% same-tool — **even though the harness has a different tool inventory and the error-class
  labels differ.** This shows the rule is the *gate semantics* (is there a sanctioned alternative?), a
  cross-harness regularity, not a Claude-Code artifact.
- **PASS-as-error-class-rescue (would REVIVE the retired framing):** a single error-class predicts the
  SAME modality across harnesses *even when its gate-type differs between harnesses*. (Strong, unexpected.)
- **FAIL / harness-specific (WEAKEN further):** the gate→modality mapping does NOT replicate — e.g. a
  REDIRECTABLE web-block recovers by redirect on harness 1 but by same-tool-retry (or no recovery) on
  harness 2. Then "redirectable gate ⇒ cross-tool redirect" is a Claude-Code routing artifact, not a
  general law. **(This is what the on-node Codex check actually found — see Part B.)**

---

### A3. INTERVENTIONAL ROUTING-ALTERATION — design

**Goal.** Causally separate error-class from gate-type by changing ONLY the route, error held fixed.

**Setup (needs harness control — NOT on this node; requires a runnable Claude-Code-like or Codex-like
harness with editable tool/policy config):**
- Fix a single error-class with a clean gate (e.g. the web/URL-fetch block).
- **Arm 1 (REDIRECTABLE, control):** blocked tool + a sanctioned alternative present (the natural config).
- **Arm 2 (GRANT-REQUIRED intervention):** SAME block, but REMOVE/disable the sanctioned alternative tool
  AND add a "request-permission/approve" affordance → the gate is now grant-required, error-class unchanged.
- **Arm 3 (TERMINAL intervention):** SAME block, remove BOTH the alternative AND any grant path → terminal.
- Replay a fixed battery of N≥30 tasks that hit this error per arm (same task set across arms).

**EXACT PASS/FAIL:**
- **PASS (modality follows the RULE, not the error-class — confirms gate-type characterization causally):**
  recovery modality TRACKS the arm: Arm1 → cross-tool redirect-share ≫ 0.5; Arm2 → same-tool/grant-share
  ≫ 0.5; Arm3 → terminal (recovery ≈ 0). The error-class was identical in all arms, so the modality
  change is *caused* by the route. Quantitative bar: redirect-share differs by >0.5 (absolute) between
  Arm1 and Arm2 with non-overlapping Wilson 95% CIs.
- **FAIL (modality is intrinsic to the error/agent reasoning):** modality is invariant across arms
  (e.g. the agent keeps trying to redirect even when no alternative exists, or keeps same-tool-retrying
  even when a sanctioned alternative is offered) → modality is driven by the model's policy about the
  *error*, not the harness route. This would REFUTE the gate-type-determines-modality claim.

**Cheaper CPU-only proxy (if no live harness):** a natural-experiment version — find, *within or across
existing corpora*, the SAME error-class appearing under DIFFERENT available-alternative configurations
(e.g. web-block sessions where `external_web_search` IS vs ISN'T in the tool inventory) and compare
modality. This is quasi-interventional (route varies, error fixed) but observational. The on-node Codex
corpus already supplies a partial instance (web-fetch blocked + web_search always available, yet the
agent does NOT redirect the blocked call — see Part B), which is itself evidence the routing rule is
harness-specific.

---

## PART B — ON-NODE DATA-HUNT + SMALL CROSS-HARNESS CHECK

### B1. Data-hunt result (what agent-trace corpora exist on this node)
| corpus | path | volume | usable? |
|---|---|---|---|
| Claude Code (primary) | `~/.claude/projects/**/*.jsonl` | ~78 sess / ~373 fail | the original corpus |
| **OpenAI Codex CLI** | `~/.codex/sessions/**/*.jsonl` | **89 sess / 1737 calls / 93 fail** | **YES — 2nd harness, checked below** |
| **Gemini CLI** | `~/.gemini/tmp/*/chats/session-*.json` | **62 sess**, `toolCalls[].functionResponse` | YES — 3rd harness, schema verified, NOT yet analyzed |
| `.gemini/history/*` | — | empty `.project_root` markers only | no |
| `committee_naviC` | `~/committee_naviC` | empty / gone | no |
| `.opencode`, `.cursor`, `.fb-sks-agent`, `.uie-companion`, `.llms`, `.navi` | — | configs/skills/logs, no tool-call traces | no |

**A second (and third) cross-harness corpus EXISTS on the node** — the observational cross-harness gate
is NOT blocked on external data. (The *interventional* arm still needs a controllable harness, off-node.)

### B2. Small cross-harness check on the Codex corpus (CPU, EXP-0009 logic re-implemented for Codex schema)
Corpus after join + <2-call drop: **63 sessions, 1737 tool calls, 93 ground-truth failures**
(nonzero exit codes for `exec_command`; "showing 0 … filtered" for web-search). **Global broad-recovery
rate = 0.774** (higher than Claude Code's ~0.64; Codex shell errors are more recoverable).

Per-class modality (n = failures; redir_share = cross-tool fraction among recovered):

| class | n | rec_rate | redir_share | gate-type (Codex) |
|---|---|---|---|---|
| proc.exit_nodetail | 35 | 0.543 | 0.842 | TRANSIENT |
| cmd.notfound | 31 | 0.968 | 0.933 | TRANSIENT |
| fs.notfound | 13 | 0.769 | 0.500 | TRANSIENT |
| fs.exists | 8 | 0.875 | 0.429 | TRANSIENT |
| code.build | 5 | 1.000 | 0.200 | TRANSIENT |
| proc.timeout | 1 | 1.000 | 0.000 | TRANSIENT |

**Plus a REDIRECTABLE-gate analog found in Codex:** the MCP `knowledge_load` (URL-fetch) tool is
**input-filter BLOCKED 142/142 times** ("Input filtering is enabled … External webpage access is not
permitted"), while `three_pai_external_web_search` is **available 429/429 times**. This is the structural
twin of Claude Code's `policy.web_disabled` REDIRECTABLE gate (blocked URL-fetch + sanctioned web-search
alternative).

### B3. The decisive cross-harness contrast (this is the scientifically important part)
On Claude Code, the REDIRECTABLE web gate recovers **100% by cross-tool redirect** (66/66
WebFetch/WebSearch → external_web_search, *within the same failed sub-task thread*). On Codex, the
structurally-identical REDIRECTABLE gate behaves **differently**: after a `knowledge_load` block the
agent does **NOT** redirect that blocked call to `web_search`; instead `web_search` is used as a
*separate, always-available* tool (429 successful calls running in parallel to the 142 blocks), and the
blocked `knowledge_load` is simply abandoned rather than rerouted.

**Interpretation (honest):**
- The *taxonomy* replicates: Codex HAS a redirectable hard-block gate (input_filter on URL-fetch) and a
  sanctioned alternative (web_search) — so the redirectable-vs-terminal/transient structure is NOT a
  Claude-Code-only artifact.
- The *modality rule does NOT replicate cleanly*: "redirectable gate ⇒ the blocked call is recovered by
  in-thread cross-tool redirect" is a **Claude-Code routing behavior**, not a universal law. Codex's
  agent treats the same gate as effectively terminal-for-that-tool + uses the alternative pre-emptively.
- This is exactly the A2 **FAIL / harness-specific** outcome — and it is *informative*: it directly
  demonstrates that recovery MODALITY is a property of the **harness's routing/policy layer**, NOT of the
  error-class (the error — "external webpage access not permitted" — is essentially identical to Claude
  Code's web_disabled, yet the modality differs). **This is independent cross-harness corroboration of
  EXP-0012's conclusion (modality = gate-type+routing, not error-class) — now shown ACROSS harnesses.**

### B4. Caveats (anti-overclaim)
- Codex failure ground-truth = nonzero exit code / empty-web-result; coarser than Claude Code's
  structured `is_error`. The `proc.exit_nodetail`/`proc.exit1` buckets lump heterogeneous shell errors.
- Codex has NO grant-required permission gate sampled (no `perm_denied` analog at n≥10), and no clean
  terminal class — same TWO-pole limitation as Claude Code (consistent with EXP-0020).
- The Codex modality redirect-shares are inflated by the `exec:<headcmd>` canonicalization (a shell
  retry with a different head-cmd counts as cross-tool); a STRICT same-binary variant would lower them.
  The qualitative cross-harness contrast (web-block NOT redirected in-thread) is robust to this.
- Single user, overlapping time window (late May 2026), research-task-heavy workload — not a
  representative agent-deployment sample. Replication on Gemini (3rd corpus) + an off-node corpus
  (SWE-agent/OpenHands) would strengthen.
- n is small (93 Codex failures); treat as a *directional* cross-harness probe, not a powered test.

---

## PART C — PROPOSED MAP-0002 DELTAS (for ORCHESTRATOR to apply — I do not write the map)
1. open_gaps: cross-harness replication is **PARTIALLY DISCHARGED on-node** — a 2nd (Codex, 89 sess/93
   fail) and 3rd (Gemini, 62 sess) agent-trace corpus exist locally; Codex check run.
2. **NEW cross-harness finding (red_zone refinement):** the redirectable-gate TAXONOMY replicates on
   Codex (input_filter URL-block + web_search alternative = structural twin of web_disabled), but the
   MODALITY RULE does NOT — Codex does not in-thread-redirect the blocked call (0 redirect of 142 blocks;
   web_search used pre-emptively in parallel). → corroborates "modality = harness routing layer, not
   error-class" ACROSS harnesses; promotes the EXP-0012 confound from single-harness-inseparable to
   **cross-harness-confirmed (routing is harness-specific)**.
3. open_gaps: the GREEN-positive "gate-type→modality replicates" result was NOT obtained (Codex shows the
   rule is harness-specific). To get a clean replication, need a harness whose routing redirects blocked
   calls in-thread (or the interventional arm). Gemini corpus (on-node) is the next cheap CPU check.
4. open_gaps: INTERVENTIONAL arm remains genuinely blocked — needs a controllable harness (off-node).
   A CPU quasi-interventional proxy (same error, alternative-present vs alternative-absent inventories)
   is now partially instantiated by the Codex contrast.

## FILES
- this design: `prior_art/PROJ-0003/CLAIM-0009_crossharness_interventional_design.md`
- codex check scripts (scratch, /tmp, not under PROJ): `/tmp/codex_xharness.py`, `/tmp/codex_redirgate.py`
