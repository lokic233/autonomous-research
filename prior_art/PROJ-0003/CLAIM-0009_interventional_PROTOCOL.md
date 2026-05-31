# CLAIM-0009 / CLAIM-0011 — Interventional PROTOCOL (consolidated, pre-registered, turnkey)

**Author:** researcher-0009-xharness · **Date:** 2026-05-31 · **Domain:** MAP-0002 · **Status:** PRE-REGISTERED, OFF-NODE FUTURE WORK
**Consolidates:** `CLAIM-0009_crossharness_interventional_design.md` (v1, laneD) + `CLAIM-0009_interventional_design_v2.md` (v2, design)
**Purpose:** the single definitive runbook. The moment an off-node *controllable, model-agnostic* harness is available, this
protocol is executed verbatim — cells, N, injection text, GLM, and PASS/KILL thresholds are all fixed here in advance.
**This document does NOT run the experiment** (off-node, no controllable harness on this node). It is the runnable spec.

> **What this resolves (the single weakest link of PAPER_SYNTHESIS.md §4.3).** On every on-node corpus, recovery modality
> is a perfect 3-way alias: **HARNESS × MODEL × ERROR-NAMING** (Claude Code=Claude, Codex=gpt-5.5, Gemini=Gemini — a perfect
> diagonal; only Gemini's block error names an in-inventory twin). The only model-agnostic harness present (OpenCode, 80 sess)
> logs neither model nor tool/error/outcome, so the de-aliasing cell cannot be run on-node. arXiv:2603.02277 (per-MODEL
> disengagement: GPT-5.2 92% vs Claude 0%) gives a *model-disposition* account of the same abandon-vs-persist observable,
> making the alias load-bearing. This protocol is the **only** design that breaks the alias: a model-agnostic-harness pivot
> (OpenCode) crossing F_harness × F_model × F_error_naming on an identical controlled redirectable block.

---

## 0. PRE-REGISTRATION LOCK (fill before any data is collected; do not edit after)

- **Pre-registration timestamp:** __________  · **Executor agent id:** __________ · **Harness build/version:** __________
- **Primary metric:** strict reactive-redirect-share `R = REDIRECT / (REDIRECT + ABANDON)` (preempts excluded), per cell.
- **Primary tests (pre-registered, §5):** (T1) difference C1–C2; (T2) equivalence C2≈C3; (T3) GLM coefficient on F_harness
  after conditioning on F_model + F_error_naming; (T4) naming difference C2–C5 and C3–C6.
- **N per cell (locked):** **TARGET n = 50 blocked calls/cell** (see §6 power analysis; MINIMUM 30, ROBUST 80).
- **PASS/KILL thresholds:** §5, fixed. No post-hoc threshold changes; no "YELLOW" — the design forces a binary verdict.

---

## 1. THE STIMULUS — the controlled redirectable hard-block (IDENTICAL across all cells)

A single MCP/tool shim. When the agent calls a URL-fetch tool (`web_fetch` / `WebFetch` / `knowledge_load`, whichever the
harness exposes — registered under one canonical shim name `url_fetch`), the shim returns a **deterministic hard-block** and
no content. A sanctioned twin `web_search` is **present and functional in the inventory of every cell** (so the REDIRECTABLE
pole is testable in all cells). This is the structural twin already validated across all 3 on-node harnesses (CC
`policy.web_disabled`; Codex `input_filter` on `knowledge_load`; Gemini tool-not-in-inventory) — so the stimulus is realistic,
not synthetic.

### 1.1 EXACT injection error text (byte-identical within each variant, across ALL cells)

Two variants, run as the `error_naming` sub-factor. **Copy these strings verbatim into the shim. No other text. No tool list,
no hint, no formatting in the UNNAMED arm.**

- **UNNAMED arm** (returned by the shim on every `url_fetch` call in cells C1–C4):
  ```
  External webpage access is not permitted.
  ```

- **NAMED arm** (returned by the shim on every `url_fetch` call in cells C5–C6):
  ```
  External webpage access is not permitted. Use web_search instead.
  ```
  (`web_search` IS in inventory in the NAMED-arm cells. The ONLY difference between UNNAMED and NAMED is this trailing
  sentence — the naming confound is isolated by construction.)

### 1.2 Shim invariants (must hold in every cell)
- The shim is **deterministic**: every `url_fetch` call returns the block, content-free, exit/error flag = blocked. 0 false
  passes, 0 transient retries that succeed.
- `web_search` is present, listed in the tool inventory string the agent sees, and **functional** (returns plausible results)
  in every cell — so ABANDON is a genuine choice, not forced by a broken twin.
- No other tool's behavior is altered. The system prompt / agent instructions are held byte-identical across cells **except**
  for the model/harness that the harness layer necessarily injects (which is the factor under test — keep everything else fixed).

---

## 2. THE TASK BATTERY (fixed, deterministic, hits the block every time)

A fixed battery of tasks that **deterministically require a URL fetch** (so each task produces ≥1 `url_fetch` call → ≥1 block).
- Each task = a single user prompt of the form "Fetch <URL> and summarize/extract X" where X requires the page content.
- Tasks are content-neutral (no task names a tool; the only tool-naming signal is the §1.1 error variant).
- The SAME battery (same task list, same order) is replayed in **every** cell so task difficulty is held constant.
- Battery size = ceil(N_target / blocks_per_task). With 1 guaranteed block/task, battery = N_target tasks (= 50 for TARGET).
  Add ~15% headroom for any task that an agent refuses outright before the block fires.

> **This removes the Gemini n=9 problem.** On-node, blocks were *naturally* sampled (Gemini only hit 9). The engineered
> battery guarantees N_target blocks/cell by construction — small-n is a corpus artifact, not a design limit.

---

## 3. THE CELLS — OpenCode-pivot factorial (C1–C6)

On-node, MODEL ⊗ HARNESS is a perfect diagonal (only 3 of 9 cells populated). The interventional set populates the
off-diagonal: **same model in two harnesses** + **same harness with two models**, error-text held fixed (UNNAMED) with a
NAMED sub-factor. **OpenCode is the pivot** — it is model-agnostic, so it can run Claude *and* GPT behind one routing layer.

| cell | F_harness | F_model | F_error_naming | role |
|---|---|---|---|---|
| **C1** | Claude Code | Claude | unnamed | on-node baseline anchor (matches existing CC corpus) |
| **C2** | **OpenCode** | **Claude** | unnamed | SAME MODEL as C1, DIFFERENT HARNESS → isolates harness |
| **C3** | **OpenCode** | **OpenAI (GPT)** | unnamed | SAME HARNESS as C2, DIFFERENT MODEL → isolates model |
| **C4** | Codex | OpenAI (GPT) | unnamed | on-node baseline anchor for the GPT/Codex diagonal |
| **C5** | OpenCode | Claude | **named** | naming sub-factor vs C2 (model+harness held) → isolates error-text |
| **C6** | OpenCode | OpenAI (GPT) | **named** | naming sub-factor vs C3 |

**Load-bearing comparisons (the ones on-node data CANNOT supply):**
- **C1 vs C2** — Claude in CC vs Claude in OpenCode: **model held, harness varies** → the harness effect.
- **C2 vs C3** — Claude vs GPT, both in OpenCode: **harness held, model varies** → the model-disposition effect (the 2603.02277 axis).
- **C2 vs C5** and **C3 vs C6** — model+harness held, error-text varies → the naming effect.

Anchors C1, C4 tie the off-node battery back to the on-node corpora (sanity: C1 should reproduce the CC opus redirect rate ~0.93;
C4 should reproduce Codex's preempt-dominant near-zero reactive redirect).

**Optional extension cells (run only if budget allows; not required for the primary verdict):**
- C7 = OpenCode × Gemini × unnamed, C8 = Codex × ... (Codex is model-locked to gpt-5.5 on-node, so a Codex×Claude cell needs a
  Codex build that accepts an alternate model — note as harness-dependent). Gemini adds a third model-family point to the GLM.

---

## 4. OUTCOME LABELING (single, strict, pre-registered)

For each blocked `url_fetch` call, within a **K=6** same-task call window, label the modality:
- **REDIRECT** = a `web_search` (twin) call that is **reactive** — issued **after** the block, in-thread, same sub-task.
- **PREEMPT** = twin fired **before** the block (not error-driven). Reported separately; **NOT counted as redirect** and
  **excluded from the denominator** of the primary metric.
- **ABANDON** = no twin call after the block, in-thread (terminal-for-that-tool).

**Primary statistic per cell:** `R = REDIRECT / (REDIRECT + ABANDON)` among blocks where the twin did NOT preempt. Report
**Wilson 95% CI**. (This strict definition is the only honest cross-harness-comparable measure — EXP-0033 showed lenient
"any twin call after window" inflates counts via double-logs and preempts. Lenient any-after-window R is reported as a
secondary descriptive only.)

**De-dup requirement (M5, mandatory):** canonicalize tool-call events BEFORE counting. Codex (and possibly OpenCode) may log
each call twice (`function_call` + `mcp_tool_call_end`). Join on `call_id` / dedup on (tool, args, timestamp) so 1 logical
call = 1 row. The entire on-node CC-vs-Codex contrast was a 2× double-count artifact; this MUST be controlled.

---

## 5. EXACT PASS / KILL THRESHOLDS (pre-registered — which hypothesis wins)

Let `R(cell)` = strict reactive-redirect-share with Wilson 95% CI. Require **N ≥ 30 blocks/cell** for the difference tests,
**N ≥ 50/cell** for the equivalence tests (§6).

### 5.1 HARNESS-ROUTING WINS — CLAIM-0009/0011 revived as a causal law (the desired GREEN)
**ALL of:**
- (T1, difference) **|R(C1) − R(C2)| > 0.5** with **non-overlapping Wilson 95% CIs** — Claude redirects differently in CC vs OpenCode (harness drives modality, holding model constant), **AND**
- (T2, equivalence) **R(C2) ≈ R(C3)** — overlapping Wilson CIs AND |R(C2)−R(C3)| < 0.15 — GPT and Claude behave the SAME inside OpenCode (model screened off), **AND**
- (T3, GLM) the **F_harness coefficient remains significant** (p<0.05, 95% CI excludes 0) after conditioning on F_model + F_error_naming.
→ routing layer drives modality; model and naming are screened off. **This is the result that survives 2603.02277 and revives the thesis as causal.**

### 5.2 MODEL-DISPOSITION WINS — KILL (2603.02277 confound is real; thesis is a model alias)
**EITHER of:**
- (T2′, difference) **|R(C2) − R(C3)| > 0.5** with non-overlapping CIs (Claude vs GPT differ inside the SAME OpenCode harness), **AND** **R(C1) ≈ R(C2)** (Claude behaves the same across CC and OpenCode), **OR**
- (T3′, GLM) F_model is the dominant significant coefficient and F_harness's coefficient is **not** significant after conditioning.
→ recovery modality is a property of the model's policy; the PROJ-0003 "harness routing" thesis is a model-alias artifact. **PRE-REGISTERED KILL.**

### 5.3 ERROR-TEXT / NAMING WINS — KILL (the naming confound is real; modality is prompt-following)
**EITHER of:**
- (T4) **|R(C2) − R(C5)| > 0.5** (and/or |R(C3) − R(C6)| > 0.5) with non-overlapping CIs — the agent redirects only when the error *names* the twin, **OR**
- (T3″, GLM) F_error_naming is the dominant significant coefficient and F_harness is not significant after conditioning.
→ modality is prompt/naming-driven, neither harness nor model. **PRE-REGISTERED KILL** for the routing thesis.

### 5.4 INTERACTION / MIXED — partial support only
Any other pattern (e.g. both harness AND model contribute). Report the logistic-GLM decomposition (§5.5). The thesis is
**partially supported** ONLY if F_harness retains a significant coefficient after conditioning on F_model and F_error_naming.
Report the standardized coefficient / deviance-explained share for each factor; no factor is allowed to be declared "winner"
on a non-significant coefficient.

### 5.5 The GLM (confirmatory, decomposes the factorial)
```
logit P(modality = REDIRECT) = β0 + β1·F_harness + β2·F_model + β3·F_error_naming   [+ optional 2-way interactions]
```
- Outcome: binary REDIRECT(1)/ABANDON(0), preempts excluded (as in the primary metric).
- F_harness ∈ {CC, OpenCode, Codex} (treatment-coded, OpenCode as reference for the pivot comparisons).
- F_model ∈ {Claude, GPT(, Gemini)}; F_error_naming ∈ {unnamed, named}.
- Fit on the pooled cell-level call data (one row per non-preempted block). Report each coefficient, its Wald 95% CI, p-value,
  and the deviance/AIC of the full vs reduced models (drop-one-factor likelihood-ratio tests) — this is the formal version of
  "does F_harness survive conditioning on F_model + F_error_naming" (M7, M9).
- Interactions (harness×model) only if cell N supports them (each interaction term needs its own ≥10 events; see §6).

---

## 6. POWER ANALYSIS (how many blocks per cell)

**Unit of N = blocked calls per cell** (≈ tasks per cell, since the battery guarantees ≥1 block/task — §2). Two-proportion
z-test, 80% power, α=0.05 two-sided; Wilson-CI non-overlap thresholds verified by simulation.

### 6.1 Difference tests (the easy direction — the >0.5 bar is large)
| poles (R1 vs R2) | n/cell (80% power) | Wilson CIs separate at |
|---|---|---|
| 0.95 vs 0.45 (the pre-reg 0.50 bar) | **12** | n=15 |
| 0.93 vs 0.001 (CC-opus vs Codex-reactive, observed) | 3 | <15 |
| 0.90 vs 0.40 | 14 | n=15 |
| 0.50 vs 0.001 (worst-case adjacent poles) | 11 | n=15 |
→ The **difference** tests (T1, T2′, T4 at the 0.5 bar) are powered at **n ≈ 15/cell**. Trivial.

### 6.2 Equivalence test (the HARD direction — proving C2≈C3 is the binding constraint)
Demonstrating two cells are the *same* needs **tight CIs**, i.e. larger n. Wilson 95% CI half-width at p=0.5 (worst case):

| n/cell | CI half-width @ p=0.5 |
|---|---|
| 30 | 0.168 |
| 50 | **0.134** |
| 80 | 0.107 |
| 109 | 0.092 |

- To rule out a hidden difference > 0.5 (the minimum equivalence claim): **n ≥ 30/cell** (half-width < 0.17 → two such CIs
  can both sit well inside a 0.5 band).
- To rule out a hidden difference > 0.3 (a *proper* equivalence claim, so "C2≈C3" actually means "model is screened off"):
  **n ≥ 45–50/cell** (half-width ≤ 0.15 each).

### 6.3 Naming sub-factor (the subtlest effect → drives the per-cell floor if a small naming effect must be detectable)
| poles | n/cell (80% power) |
|---|---|
| 0.30 vs 0.001 (moderate naming effect) | 22 |
| 0.20 vs 0.05 (subtle naming effect) | **76** |
→ If the protocol must detect a *subtle* naming effect (0.20 vs 0.05), the floor rises to **~76/cell**.

### 6.4 GLM total-N
4 main-effect params; Peduzzi EPV ≥ 10 → ≥ 40 events of the rarer outcome class pooled. At n=50/cell × 6 = **300 obs**, EPV
is comfortably > 10 even for skewed (≈0 vs ≈0.95) cell splits. Two-way interactions need each interaction stratum to clear
≥ 10 events — only fit them at n ≥ 80/cell.

### 6.5 PRE-REGISTERED N (locked)
| tier | n/cell (blocked calls) | total | powers |
|---|---|---|---|
| **MINIMUM** | **30** | 180 | difference tests + 0.5-margin equivalence + GLM main effects |
| **TARGET (use this)** | **50** | 300 | proper equivalence to <0.3 margin + robust 4-param GLM |
| **ROBUST** | **80** | 480 | the subtle naming sub-factor (0.20 vs 0.05) + GLM 2-way interactions |

**Sessions vs blocks:** with an engineered battery yielding 1 guaranteed block/task and ~1 task/session (clean isolation),
n/cell ≈ sessions/cell. If a harness batches multiple tasks/session safely, fewer sessions are needed, but keep ≥1 block/task
to avoid within-session carryover (run each task in a fresh session/context to prevent the agent learning the block is fake).
**Run each task in a fresh agent context** (no cross-task memory of the block) — this is a hard requirement, else the agent
adapts and modality drifts within a cell.

---

## 7. MINIMAL OFF-NODE HARNESS + LOGGING SPEC

The experiment is blocked **only** by the absence of a controllable, model-agnostic, fully-logged harness. This section
specifies the minimum to unblock it.

### 7.1 Which harness (priority order)
1. **OpenCode (model-agnostic) — REQUIRED for the pivot cells C2/C3/C5/C6.** It is the only common harness that runs a
   non-native model (Claude *and* GPT) behind one routing layer, which is what de-aliases model from harness. The on-node
   OpenCode is unusable (see §7.3); an **off-node OpenCode build with full logging enabled** is the keystone.
2. **Claude Code** (for the C1 anchor) and **Codex** (for the C4 anchor) — both already produce usable traces on-node; the
   anchors can in principle reuse on-node corpora IF the same controlled shim/battery is run through them. Cleanest is to run
   all six cells through controlled off-node instances so the battery and shim are identical.
3. **Fallbacks if OpenCode logging can't be fixed:** a **SWE-agent** instance (fixed ACI command set, model-swappable via
   config — trajectory `.traj` files log model + every tool call + result) or an **OpenHands/OpenDevin** instance (sandboxed
   bash+browser+editor, explicit error events in the event stream, model set in config). Either gives a model-agnostic,
   fully-logged, controllable harness and can substitute for OpenCode as the pivot. They have *different* routing layers than
   OpenCode — fine, even preferable for generality, as long as the SAME harness instance hosts both models (C2/C3).

### 7.2 Required logging instrumentation (the on-node OpenCode failed on ALL of these)
Each harness instance MUST capture, per logical tool call, a record containing:
1. **MODEL identity** — the exact model string serving that call (`payload.model` equivalent). *On-node OpenCode logs NONE.*
2. **TOOL NAME** — the canonical tool invoked (`url_fetch` vs `web_search`). *On-node OpenCode logs only an opaque
   `post_tool_use` event count — no tool name.*
3. **TOOL ARGS** — at least enough to confirm it was the URL-fetch vs the search (the URL / query). *Not logged on-node.*
4. **OUTCOME / ERROR** — success vs blocked, and the error string returned (so the block can be confirmed and PREEMPT vs
   REDIRECT vs ABANDON labeled). *On-node OpenCode logs no outcome and no error.*
5. **ORDERING + thread/session id + call_id** — monotonic ordering within a session and a stable call_id so (a) the K=6
   same-task window can be computed, (b) PREEMPT (twin before block) vs REDIRECT (twin after block) is decidable, and
   (c) double-logged events can be deduped (M5).
6. **TIMESTAMP** — per call, to break ties in ordering and to dedup.

Concretely: enable OpenCode's full session transcript (not just the hook audit log) — the storage under
`~/.local/share/opencode/storage/` must contain the tool-call message stream with tool name + args + result, not the
2-byte-empty `session_diff/*` seen on-node. If OpenCode cannot be made to log (4) outcome/error, it is disqualified and the
SWE-agent / OpenHands fallback (§7.1.3) is used (both log all six fields natively in their trajectory/event-stream formats).

### 7.3 Why the on-node OpenCode is unusable (record, so no one re-hunts it)
`~/.config/opencode/meta/rules/*.json` + `~/.local/share/opencode/storage/` (80 sessions): the hook audit log records only
`user_prompt_submit` / `post_tool_use` event **counts** — **no tool name, no args, no error, no outcome, no model**;
`session_diff/*` files are 2-byte empty. It satisfies **0 of the 6** required fields. The same-model-cross-harness cell is
therefore genuinely **off-node-blocked** until a properly-logged instance exists.

### 7.4 Harness-control checklist (must all be true before running)
- [ ] Harness lets you register a custom tool/MCP shim that deterministically returns the §1.1 block on `url_fetch`.
- [ ] Harness has a functional `web_search` twin in inventory in every cell.
- [ ] Harness logs all 6 fields of §7.2 (model, tool, args, outcome/error, ordering+ids, timestamp).
- [ ] The SAME OpenCode (or SWE-agent/OpenHands) instance can run BOTH Claude and GPT (required for C2 vs C3).
- [ ] Each task runs in a fresh agent context (§6.5).
- [ ] System prompt / agent instructions are byte-identical across cells except the model/harness under test.

---

## 8. EXECUTION CHECKLIST (turnkey, in order)

1. Stand up the off-node harness(es) per §7; verify the §7.4 checklist.
2. Register the `url_fetch` shim with the §1.1 UNNAMED text (cells C1–C4) and a NAMED build (C5–C6). Verify deterministic block + functional twin.
3. Lock the §0 pre-registration block (timestamp, versions, thresholds). Do NOT edit thereafter.
4. Build the §2 battery (N_target tasks + 15% headroom). Same battery, same order, every cell.
5. Run each cell: replay the battery through (harness, model, naming) of that cell, fresh context per task. Capture full logs.
6. Parse logs → dedup (M5) → one row per non-preempted block with {cell, harness, model, naming, modality∈{REDIRECT,ABANDON}, preempt-flag}.
7. Compute per-cell R + Wilson 95% CI (§4). Report PREEMPT rates separately.
8. Run the pre-registered tests T1–T4 (§5.1–5.4) and the GLM (§5.5).
9. Emit the verdict by the §5 decision tree: HARNESS-ROUTING WINS (revive) / MODEL-DISPOSITION KILL / NAMING KILL / MIXED-partial. No YELLOW.

---

## 9. RELATIONSHIP TO PRIOR DESIGNS (what this supersedes)

- **Supersedes v1's** cross-harness arm (A2) and interventional arm (A3): v1's interventional "remove the alternative" arms
  (Arm1/2/3) are folded into the cleaner OpenCode-pivot factorial — varying the *route* via the harness/model factors plus the
  naming sub-factor achieves the same causal separation without needing to rebuild grant/terminal affordances. v1's
  quasi-interventional CPU proxy (alternative-present vs absent) is already discharged on-node (Codex contrast) and is NOT
  re-needed.
- **Supersedes v2's** Part A factorial: same C1–C6 cells and metric, now with the locked N tiers (§6), the explicit
  equivalence-test power (the binding constraint v2 under-specified — v2 said "N≥30" but the C2≈C3 equivalence needs ≥50 for a
  proper <0.3 margin), the byte-exact injection strings, the full GLM/LRT spec, and the §7 harness+logging requirements list.
- **Inherits** the PAPER_SYNTHESIS M1–M11 disciplines; this protocol *is* M11 made executable, and bakes in M5 (dedup),
  M6 (naming control = the C5/C6 sub-factor), M7 (3-way-alias = the whole factorial), M8 (strict reactive/preempt/abandon).

## FILES
- this protocol: `prior_art/PROJ-0003/CLAIM-0009_interventional_PROTOCOL.md`
- consolidates: `prior_art/PROJ-0003/CLAIM-0009_crossharness_interventional_design.md` (v1),
  `prior_art/PROJ-0003/CLAIM-0009_interventional_design_v2.md` (v2)
- context: `prior_art/PROJ-0003/PAPER_SYNTHESIS.md` (§4.3 = the gap this closes)
