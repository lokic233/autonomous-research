# EXP-0031 — Gemini CLI cross-harness replication: 3rd harness for CLAIM-0011

**Domain:** MAP-0002 (Agent failure attribution & recovery). **CPU-only, stdlib-only, ~3s.**
**Lane:** researcher-0011-laneA. **Claim under test:** CLAIM-0011 (seed) — the durable PROJ-0003 thesis:
*recovery MODALITY is set by the HARNESS ROUTING CONFIGURATION, not error-class/model-reasoning; the
redirectable-vs-terminal GATE TAXONOMY is harness-agnostic, but WHICH modality fires is a per-harness
routing-table fact.*

## Why this experiment
CLAIM-0011 was 2-harness CONFIRMED (MAP-0002 red_zone "harness-routing-as-confound = CROSS-HARNESS-CONFIRMED"):
- **Claude Code:** REDIRECTABLE web gate → **66/66 in-thread cross-tool redirect** (WebFetch→external_web_search).
- **Codex CLI:** structurally-identical REDIRECTABLE URL-block → **0/142 in-thread redirects** (web_search used
  pre-emptively in parallel; blocked `knowledge_load` abandoned).
A **3rd on-node corpus** (Gemini CLI, `~/.gemini/tmp/*/chats/session-*.json`, 62 sessions) was schema-verified
by a prior lane (CLAIM-0009 design Part B1) but NOT analyzed. This experiment parses it and measures Gemini's
recovery modality on its gate(s), to test whether the gate TAXONOMY is consistent across 3 harnesses while the
MODALITY differs per-harness (→ robust 3-harness characterization) — honestly reporting Gemini's small n.

## Data (REAL, on-node)
`~/.gemini/tmp/*/chats/session-*.json`. Schema (re-verified, differs from the CLAIM-0009-design guess):
tool calls live in `messages[].toolCalls[]`, each `{name, args, result[].functionResponse.response, status,
resultDisplay, ...}`; `status ∈ {success, error}` = per-call ground truth; error text in `resultDisplay`
and `functionResponse.response.error`. Parse re-implemented per this schema (EXP-0009/codex_xharness logic
mirrored, parse layer rewritten). **Corpus: 62 session files, 18 with tool calls, 198 tool calls, 60
ground-truth failures.** (44 sessions are pure-text reviewer/debate prompts with no tool calls.)

**Tool inventory (this corpus):** `read_file, write_file, list_directory, glob, grep_search,
run_shell_command, activate_skill`. **NO web/fetch tool exists** — so the clean cross-harness web-block
anchor (CC/Codex) is NOT directly available; Gemini's structural REDIRECTABLE twin is identified instead.

## Method
- Parse → ordered per-session tool-call stream (name, intent, is_error, err_class).
- Error taxonomy (4 observed classes) → gate-type (harness-agnostic):
  - **REDIRECTABLE** = `policy.tool_blocked`: hard tool-block WITH a sanctioned alternative.
  - **GRANT_REQUIRED** = `policy.workspace_boundary` ("Path not in workspace"): policy block, no alt tool
    (needs a corrected/granted path, same tool).
  - **TRANSIENT** = `schema.missing_param`, `arg.bad_regex` (fixable in place / re-runnable).
- BROAD recovery (K=6): SAME_TOOL_RETRY = later success with same tool; CROSS_TOOL_REDIRECT = no same-tool
  success but a later success with a different tool. Per-gate redirect-share + **Wilson 95% CIs**.

## THE REDIRECTABLE ANCHOR (Gemini's web-block analog)
`run_shell_command` is **HARD-BLOCKED in this harness** — every call returns
`Tool "run_shell_command" not found. Did you mean one of: "grep_search", "replace", "cli_help"?`
This is the structural twin of CC's web_disabled and Codex's input_filter: **a blocked tool whose error
message EXPLICITLY names sanctioned alternatives.** Because the blocked tool is not in the inventory, it can
*never* succeed → ANY in-thread recovery is necessarily a cross-tool redirect (the cleanest possible
redirectable-gate probe). 9 blocks observed across the corpus.

## RESULTS

### Per-gate-type modality (n = failures)
| gate-type | n_fail | recovered | redirect | same-tool | redir-share (redir/rec) | Wilson 95% |
|---|---|---|---|---|---|---|
| **REDIRECTABLE** (tool_blocked) | 9 | 6 | **6** | 0 | **1.000** | [0.610, 1.000] |
| GRANT_REQUIRED (workspace_boundary) | 20 | 15 | 4 | 11 | 0.267 | [0.109, 0.520] |
| TRANSIENT (schema/regex) | 31 | 24 | 6 | 18 | 0.250 | [0.120, 0.449] |

The gate-type → modality contrast is exactly as predicted: **REDIRECTABLE recovers ~exclusively by cross-tool
redirect (1.000), while GRANT_REQUIRED / TRANSIENT recover predominantly same-tool (~0.25 redirect-share).**
The REDIRECTABLE Wilson lower bound (0.610) does not overlap the upper bounds of the other two gates (0.520,
0.449) — separation despite small n.

### The REDIRECTABLE anchor (run_shell_command hard-block)
- total blocks: **9**
- recovered IN-THREAD by cross-tool redirect (success within K=6): **6**
- abandoned / no in-thread recovery (all 3 = block at end-of-session, empty window — NOT preemption): 3
- same-blocked-tool "success": **0** (structurally impossible — tool not in inventory)
- **in-thread redirect-share = 6/9 = 0.667, Wilson95 [0.354, 0.879]** (of all blocks)
- **redirect-share AMONG RECOVERED = 6/6 = 1.000, Wilson95 [0.610, 1.000]**
- redirect routes (blocked → recovered-with): run_shell_command→grep_search ×3, →glob ×1, →write_file ×1,
  →read_file ×1. (The agent reroutes the file-discovery `find` intent onto exactly the harness-suggested
  `grep_search`/`glob` alternatives — verified qualitatively: every recovery is the immediate next tool in
  the same gemini turn.)

### 3-harness comparison (the thesis test)
| harness | redirectable gate | blocked tool | sanctioned alt | in-thread redirect | blocks | redir-share (recovered) | modality |
|---|---|---|---|---|---|---|---|
| Claude Code | policy.web_disabled | WebFetch/WebSearch | external_web_search | 66 | 66 | **1.000** | IN-THREAD REDIRECT |
| **Gemini CLI** | policy.tool_blocked | run_shell_command | grep_search/glob/replace | **6** | **9** | **1.000** [0.610,1.000] | **IN-THREAD REDIRECT** |
| Codex CLI | policy.input_filter | knowledge_load (URL) | three_pai_external_web_search | 0 | 142 | **0.000** | ABANDON+PREEMPT |

## VERDICT (honest)

**The GATE TAXONOMY is CONSISTENT across all 3 harnesses.** Each harness has a REDIRECTABLE gate (a hard
tool-block whose error message names a sanctioned alternative): CC's web_disabled, Codex's input_filter URL
block, and Gemini's run_shell_command block. The redirectable-vs-terminal/transient structure is **NOT a
Claude-Code artifact** — it is harness-agnostic. ✔

**The MODALITY is per-harness, exactly as CLAIM-0011 asserts.** On its REDIRECTABLE gate:
- Claude Code redirects in-thread (66/66).
- **Gemini redirects in-thread (6/6 among recovered; 6/9 of all blocks).**
- Codex abandons + pre-empts (0/142).

Gemini's modality **matches Claude Code's** (in-thread redirect), NOT Codex's. This does NOT weaken the thesis —
CLAIM-0011 does not claim every harness is unique; it claims modality is a *per-harness routing-table fact*,
and the taxonomy is harness-agnostic while *which* modality fires is set by the route. The data show **two
distinct modality regimes (in-thread-redirect: CC+Gemini; abandon+preempt: Codex) sitting on top of one
consistent gate taxonomy.** That is precisely the predicted shape, now across **3 independent harnesses with
3 different tool inventories and 3 textually-distinct block messages**. The taxonomy generalizes; the modality
is routing-determined and not error-class/model-reasoning determined (the "tool unavailable, here are
alternatives" error is essentially identical across harnesses, yet Codex's modality differs from CC+Gemini's).

**Effect on CLAIM-0011: SUPPORT.** Strengthens the confound finding from CROSS-HARNESS-CONFIRMED (2) to a
robust **3-harness characterization**: taxonomy-consistent across 3, modality per-harness with ≥2 distinct
regimes observed.

## CAVEATS (anti-overclaim)
- **Small n.** Gemini = 9 REDIRECTABLE blocks (6 recovered). Wilson CI [0.610,1.000] on redir-share-among-
  recovered. Treat as a *directional* 3rd-harness probe, not a powered test. The qualitative pattern
  (every recovery is an immediate next-call switch to a harness-suggested alternative; blocked tool never
  retried) is robust to the small n.
- **Different gate substance.** Gemini's REDIRECTABLE anchor is a *tool-not-in-inventory* block, not a
  *web-access policy* block as in CC/Codex. It is the same STRUCTURE (blocked tool + named sanctioned
  alternative) but a different cause. The web-block — the cleanest cross-harness anchor — is NOT testable on
  Gemini (no web tool in the corpus). Honest: this is a structural twin, not an identical gate.
- **3 "abandon" blocks are end-of-session, not preemption.** Unlike Codex (where web_search runs in parallel
  pre-emptively), Gemini's 3 non-recovered blocks simply have no following call (session ended). So Gemini's
  modality is in-thread-redirect-or-stop, NOT Codex-style parallel-preempt. The 6/6 among-recovered is the
  apples-to-apples comparison to CC's 66/66.
- **GRANT_REQUIRED ≠ a clean terminal pole.** `policy.workspace_boundary` recovers 75% (same-tool, corrected
  path) — it is a grant/correct-and-retry gate, not terminal. Consistent with EXP-0020's finding that the
  terminal pole is un-demonstrable on these research-workload corpora.
- **Single user, overlapping window** (late May 2026), research-task-heavy. Same population caveat as the
  CC/Codex corpora.

## FILES
- impl: `experiments/2026-05-31/EXP-0031/impl/gemini_xharness.py`
- per-class CSV: `experiments/2026-05-31/EXP-0031/results/gemini_per_class.csv`
- per-gate CSV: `experiments/2026-05-31/EXP-0031/results/gemini_per_gate.csv`
- 3-harness CSV: `experiments/2026-05-31/EXP-0031/results/three_harness_redirectable_gate.csv`
- full run log: `experiments/2026-05-31/EXP-0031/results/gemini_xharness_output.txt`
