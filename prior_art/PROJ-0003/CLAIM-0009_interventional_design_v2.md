# CLAIM-0009 / CLAIM-0011 — Interventional Design v2: disentangling MODEL from HARNESS

**Author:** researcher-0009-design · **Date:** 2026-05-31 · **Domain:** MAP-0002 · **CPU-only (design + on-node proxy)**
**Builds on:** `CLAIM-0009_crossharness_interventional_design.md` (v1, researcher-0003-laneD). Do not re-read v1's
Part A1–A2 setup — this doc inherits it and adds the model-vs-harness layer the v1 design did not address.

## 0. Why v2 exists (the new confound v1 missed)
v1 designed the cross-harness + interventional arms to break **harness-routing-vs-error-class**. Since v1, two
things changed the load-bearing question:

1. **The cross-harness "regime difference" mostly evaporated under scrutiny.** EXP-0033 found Codex logs every
   tool call **twice** (`function_call` + `mcp_tool_call_end`); v1/EXP-0032 double-counted. Deduped, Codex
   **preempts 100%** (web twin fires *before* the block 152/152), it does NOT "abandon/isolate". So CC (79%
   preempt) and Codex (100% preempt) are *both* preempt-dominant; the headline CC-66/66-redirect-vs-Codex-0/142
   contrast collapses to **CC 0.116 reactive vs Codex 0.000 reactive** (overlapping-near-zero), and CC's own
   66/66 drops to 2/43 under a uniform strict definition. The ONLY harness with nonzero in-thread reactive
   redirect is **Gemini (2/9)** — and Gemini is also the ONLY harness whose block error *names an in-inventory
   tool* ("did you mean grep_search/replace/cli_help"). So modality is **perfectly confounded with error-naming**
   AND with harness AND with model, all three collinear at the canonical-block level.

2. **arXiv:2603.02277 (per-MODEL disengagement)** reports the *same* abandon-vs-persist observable but attributes
   it to the **MODEL** (GPT-5.2 92% disengage vs Claude 0%). This maps exactly onto the on-node harness lineup
   (Codex = GPT-5.5, CC = Claude, Gemini = Gemini-3.x), so the apparent "harness routing" difference could
   equally be **model disposition**. Model and harness are **perfectly aliased** in every on-node corpus.

**=> The binding question is no longer "harness-routing vs error-class". It is "HARNESS-ROUTING vs MODEL-DISPOSITION
vs ERROR-NAMING", and all three are collinear on-node.** v2 specifies the experiment that breaks that 3-way alias.

---

## PART A — THE v2 INTERVENTIONAL DESIGN (2×2×… factorial that de-aliases model, harness, error-text)

### A1. The one clean idea: cross the two factors that are currently glued together
On-node, MODEL ⊗ HARNESS is a perfect diagonal (only 3 of 9 cells populated: Claude×ClaudeCode, GPT×Codex,
Gemini×Gemini). The interventional test must populate the **off-diagonal**: run the **same model in two harnesses**
and the **same harness with two models**, on an **identical, controlled, redirectable error**, with **error text
held fixed** (so naming can't sneak in). This needs harness control we do not have on-node (see Part B), so it is
specified here as the off-node gold-standard battery.

### A2. Factors (each must vary independently of the others)
- **F_harness** ∈ {Claude Code, OpenCode, Codex} — three distinct routing/policy layers. Crucially, **OpenCode is
  model-agnostic** (it can run Claude, GPT, or Gemini behind the same routing layer), which is what makes
  same-model-cross-harness possible.
- **F_model** ∈ {a Claude model, an OpenAI model} (optionally a Gemini model) — the disposition axis from 2603.02277.
- **F_errortext** — controlled: the SAME synthetic block, same error string, in all cells (kills the EXP-0033
  naming confound). Two variants run as a sub-factor: error-text that **names an in-inventory alternative** vs
  error-text that **does not** — to measure the naming effect *orthogonally* to model and harness.

### A3. The controlled error (the "redirectable hard-block" stimulus)
A single MCP/tool shim that, when the agent calls a URL-fetch tool (`web_fetch`/`WebFetch`/`knowledge_load`),
returns a deterministic hard-block: `"External webpage access is not permitted."` A sanctioned twin
(`web_search`) is **present in inventory in all cells**. This is the structural twin already validated across
all 3 on-node harnesses (CC web_disabled, Codex input_filter, Gemini twin) — so the stimulus is realistic.
Two error-text variants:
  - **UNNAMED:** `"External webpage access is not permitted."`
  - **NAMED:**   `"External webpage access is not permitted. Use web_search instead."` (web_search IS in inventory)

### A4. The cells (minimum viable de-aliasing set)
Populate at least these cells (each a fixed battery of N tasks that deterministically hit the block):

| cell | harness | model | error-text | purpose |
|---|---|---|---|---|
| C1 | Claude Code | Claude | unnamed | on-node baseline anchor (matches existing corpus) |
| C2 | **OpenCode** | **Claude** | unnamed | SAME MODEL, DIFFERENT HARNESS vs C1 → isolates harness |
| C3 | **OpenCode** | **OpenAI (GPT)** | unnamed | SAME HARNESS as C2, DIFFERENT MODEL → isolates model |
| C4 | Codex | OpenAI (GPT) | unnamed | on-node baseline anchor for GPT/Codex diagonal |
| C5 | OpenCode | Claude | **named** | naming sub-factor vs C2 (model+harness held) → isolates error-text |
| C6 | OpenCode | OpenAI | named | naming sub-factor vs C3 |

The **load-bearing comparisons** are the off-diagonal pairs that on-node data CANNOT give:
- **C1 vs C2** (Claude in CC vs Claude in OpenCode): model held, harness varies.
- **C2 vs C3** (Claude vs GPT, both in OpenCode): harness held, model varies.
- **C2 vs C5** and **C3 vs C6**: model+harness held, error-text varies (naming).

### A5. Outcome metric (single, pre-registered, strict)
For each blocked call, within a K=6 same-task window, label modality:
- **REDIRECT** = a `web_search` (twin) call that is *reactive* (issued **after** the block, in-thread, same sub-task).
- **PREEMPT** = twin fired **before** the block (not error-driven; must be reported separately, NOT counted as redirect).
- **ABANDON** = no twin call after the block (terminal-for-that-tool).
Primary statistic per cell: **strict reactive-redirect-share** = REDIRECT / (REDIRECT + ABANDON) among blocks where
the twin did NOT already preempt. Report Wilson 95% CI. (This strict definition is the one EXP-0033 showed is the
only honest cross-harness-comparable measure; lenient any-after-window is reported as a secondary descriptive only.)

### A6. EXACT PASS/FAIL (which hypothesis wins)
Let R(cell) = strict reactive-redirect-share with Wilson CI; require N≥30 blocks/cell (powered to resolve a
0.5-absolute difference at non-overlapping 95% CIs).

- **HARNESS-ROUTING WINS (CLAIM-0009/0011 desired GREEN):** modality **flips with harness, holding model constant**.
  i.e. **|R(C1) − R(C2)| > 0.5 with non-overlapping CIs** (Claude redirects differently in CC vs OpenCode), AND
  **R(C2) ≈ R(C3)** (overlapping CIs — GPT and Claude behave the SAME within OpenCode). => routing layer drives
  modality; the model is screened off. This is the result that *survives* 2603.02277.
- **MODEL-DISPOSITION WINS (2603.02277 confound REAL, CLAIM dies):** modality **tracks the model, holding harness
  constant**. i.e. **|R(C2) − R(C3)| > 0.5 with non-overlapping CIs** (Claude vs GPT differ inside the SAME
  OpenCode harness), AND **R(C1) ≈ R(C2)** (Claude behaves the SAME across CC and OpenCode). => the recovery
  modality is a property of the model's policy, and the entire PROJ-0003 "harness routing" thesis is a model-alias
  artifact. **This is the kill condition — it must be pre-registered as such.**
- **ERROR-TEXT WINS (naming, EXP-0033 confound REAL):** within a fixed (model,harness) cell, **|R(C2) − R(C5)| > 0.5**
  (and C3 vs C6) with non-overlapping CIs → the agent redirects only when the error *names* the twin; modality is
  prompt-following, neither harness nor model. Also a kill condition for the routing thesis.
- **INTERACTION / MIXED:** any other pattern (e.g. both harness AND model contribute) → report the ANOVA-style
  decomposition (variance of R attributable to F_harness vs F_model vs F_errortext via a logistic GLM with the
  three factors); the thesis is *partially* supported only if F_harness retains a significant coefficient after
  conditioning on F_model and F_errortext.

### A7. Why this is the minimal sufficient design
- It is the **only** design that breaks the model⊗harness diagonal, because OpenCode is the pivot that runs a
  non-native model behind a non-native routing layer. Without a model-agnostic harness you can NEVER separate
  the two from observational traces (proven below: every on-node corpus is single-model-per-harness on the
  cross-harness axis).
- Error-text is controlled by construction (same shim), so the third confound is neutralized in the same battery.
- Pass/fail is a pre-registered CI-separation on a single strict metric, so it cannot be talked into a YELLOW.

---

## PART B — ON-NODE DATA CHECK (is ANY of this answerable without off-node harness control?)

### B1. Inventory of on-node agent-trace corpora and their MODEL labels
| harness corpus | path | sessions | model(s) recorded | tool-call + error data? |
|---|---|---|---|---|
| **Claude Code** | `~/.claude/projects/**/*.jsonl` | 189 files | **6 Claude variants**: opus-4-6 (3023 msgs), opus-4-8 (349), haiku-4-5 (53), opus-4-7 (48), sonnet-4-5 (2), sonnet-4-6 (1) | YES (`tool_use`/`tool_result.is_error`) |
| **Codex CLI** | `~/.codex/sessions/**/*.jsonl` | 92–93 | **gpt-5.5 ONLY** (92/92; `payload.model`) | YES (function_call/exit codes) |
| **Gemini CLI** | `~/.gemini/tmp/*/chats/session-*.json` | 65 | **3 Gemini variants**: gemini-3.1-pro-preview-customtools (71), gemini-3-flash-preview (9), gemini-3.1-pro-preview (3) | YES (`toolCalls[].functionResponse`) |
| **OpenCode (Meta wrapper)** | `~/.config/opencode/meta/rules/*.json` + `~/.local/share/opencode/storage/` | 80 | **NONE recorded** (hook audit log only) | **NO** — only `user_prompt_submit`/`post_tool_use` event *counts*; no tool name, no error, no outcome, no model. `session_diff/*` are 2-byte empty. |
| uie-companion | `~/.uie-companion/sessions.json` | 0 | — | empty list |
| .opencode, .cursor, .fb-sks-agent, .llms, .navi | — | configs/skills/state only | — | no traces |

### B2. The decisive structural finding
**On the cross-harness axis, MODEL is perfectly aliased with HARNESS:**
- Claude Code = 100% Claude family. Codex = 100% gpt-5.5. Gemini = 100% Gemini family.
- The one harness that *could* break the alias — **OpenCode (model-agnostic)** — exists on-node with 80 sessions,
  **but its logs record neither the model nor any tool-call outcome** (only that *some* tool ran). It is unusable
  for a modality or model probe.
=> **The same-model-cross-harness comparison (C1 vs C2) is GENUINELY OFF-NODE-BLOCKED.** No on-node corpus has the
same model under two harnesses with recoverable tool-call traces.

### B3. What IS on-node-answerable: a WITHIN-harness, cross-MODEL proxy
Both Claude Code (6 Claude variants) and Gemini (3 Gemini variants) ran **multiple models under ONE harness**.
This cannot separate OpenAI-vs-Claude disposition (it's all one family per harness), but it DOES test a weaker
prediction of the model-disposition hypothesis: *if modality were a fine-grained model property, even sibling
model variants (esp. across capability tiers: opus vs haiku, pro vs flash) might differ; if it is the harness
routing layer, all models under one harness should behave identically.*

**Proxy run (CPU, read-only, `/tmp/cc_model_modality.py`): Claude Code redirectable web-block (WebFetch
"Internet mode is not enabled"), modality split by emitting model.**

| model | calls | err | broad-recR | web-blocks | reactive-redirect | redir-share (Wilson 95%) |
|---|---|---|---|---|---|---|
| claude-opus-4-6 | 3374 | 353 | 0.901 | 42 | 39 | **0.929 [0.810, 0.975]** |
| claude-opus-4-8 | 172 | 40 | 0.750 | 1 | 1 | 1.000 [0.207, 1.000] |
| claude-haiku-4-5 | 34 | 0 | — | 0 | 0 | — |
| claude-opus-4-7 | 11 | 0 | — | 0 | 0 | — |
| (sonnet variants) | ~3 | 0 | — | 0 | 0 | — |
| **opus tier (agg)** | — | 393 | 0.885 | **43** | **40** | **0.930 [0.814, 0.976]** |

### B4. Which way the on-node proxy leans (HONEST)
- **The redirectable web-block fires almost only under opus-4-6 (42/43 blocks).** haiku/sonnet/opus-4-7 emitted
  **zero** web-blocks in the corpus, so there is **no within-CC cross-model contrast available on the redirectable
  gate** — the cells that would test "does a cheaper Claude tier abandon more?" are empty (n=0). This is itself a
  finding: the redirectable-gate stimulus is *not naturally sampled* across Claude tiers on-node.
- What the data DOES show: the two Claude models that hit the gate (opus-4-6, opus-4-8) **both redirect at ≥0.93**,
  i.e. modality does **not** flip across the Claude variants that were tested. This is **weakly consistent with the
  harness-routing reading** (modality constant across same-family models under one harness) and **weakly against** a
  strong per-model-disposition reading — *but it is uninformative about the OpenAI-vs-Claude axis that 2603.02277
  is actually about*, because every cell here is Claude. n=43 blocks, single tier effectively.
- **Lean: very weakly toward harness-routing, but the proxy CANNOT touch the load-bearing OpenAI-vs-Claude
  disposition question.** The 2603.02277 confound (GPT abandons / Claude persists) is between *families*, and
  no on-node harness mixes families with usable traces.

### B5. Verdict on on-node answerability
- **Same-model-cross-harness (C1 vs C2):** OFF-NODE-BLOCKED. (OpenCode could host it but logs no model/outcomes.)
- **Same-harness-cross-FAMILY-model (C2 vs C3):** OFF-NODE-BLOCKED. (No on-node harness runs two model families.)
- **Within-harness-cross-SAME-FAMILY-model:** on-node-doable and DONE (B3) — leans weakly harness-routing but is
  under-powered (redirect gate only sampled in opus tier) and family-blind.
- **Error-text/naming sub-factor:** on-node it is perfectly confounded with harness (EXP-0033); only the controlled
  off-node battery (C2 vs C5) can isolate it.

---

## PART C — PROPOSED MAP-0002 / claim notes (for ORCHESTRATOR — I do not edit the map)
1. The binding gate is now **GATE-1 reframed**: a model-agnostic-harness factorial (Part A) that crosses
   F_model × F_harness × F_errortext on an identical controlled redirectable block, with pre-registered CI-separation
   pass/fail (A6). This subsumes v1's interventional arm and the cross-harness arm.
2. **On-node disentanglement is genuinely off-node-blocked** on the load-bearing axis: model ⊗ harness is a perfect
   diagonal in all 4 on-node corpora; the only model-agnostic harness present (OpenCode, 80 sess) logs neither model
   nor tool outcomes. Record this so no future agent re-hunts the node expecting a same-model-cross-harness slice.
3. The within-CC cross-model proxy (B3) is a *weak* prior toward harness-routing (modality ~0.93 redirect across the
   2 Claude variants that hit the gate; cheaper tiers never hit it) — directional only, family-blind, NOT a
   substitute for GATE-1.

## FILES
- this design: `prior_art/PROJ-0003/CLAIM-0009_interventional_design_v2.md`
- on-node proxy script (scratch, read-only): `/tmp/cc_model_modality.py`
- builds on: `prior_art/PROJ-0003/CLAIM-0009_crossharness_interventional_design.md` (v1)
