# CLAIM-0011 — Prior-Art Positioning (VERDICT-0038 GATE-3)

**Agent:** researcher-0011-gate3 · **Date:** 2026-05-31 · **Mode:** CPU prior-art, read-only.
**Claim:** Agentic failure-recovery **MODALITY** (in-thread redirect vs abandon+preempt) is
determined by the **HARNESS ROUTING CONFIGURATION**, NOT by error-class or model reasoning.
Cross-harness confirmed across 3 harnesses (EXP-0031): CC 66/66 in-thread redirect, Gemini 6/6
in-thread redirect, Codex 0/142 (abandon+preempt). The redirectable-vs-terminal **gate taxonomy**
is harness-agnostic; **which modality fires** is a per-harness routing-table fact.

This doc discharges GATE-3: cite + DISTINGUISH the 4 committee-named clusters, foreground the
EXP-0012 ≤0.2%-over-a-single-gate-bit delta as the anti-tautology argument, and flag any collision.

---

## The axis CLAIM-0011 occupies (stated once, used throughout)

Three orthogonal axes recur in this literature. Keeping them separate is the whole positioning:

1. **WHAT fails** — the failure-mode taxonomy axis (MAST, AgentBench buckets).
2. **HOW the MODEL recovers** — model-driven recovery via self-critique/verbal reinforcement
   (Reflexion, Self-Refine). The NULL CLAIM-0011 refutes.
3. **HOW recovery is ROUTED** — the harness/framework layer that decides the recovery *modality*
   before/around model reasoning. **CLAIM-0011 lives here**, with the specific, falsifiable delta:
   *modality is DETERMINED by harness routing and is invariant to error-class within a gate-type,
   yet FLIPS across harnesses on identical errors.*

The benchmark/measurement genre (τ-bench, ToolEmu) is a cross-cutting *method* axis, not a thesis axis.

---

## EXP-0012 delta — why this is NOT a tautology (the load-bearing quantitative anchor)

The hostile reading of CLAIM-0011 is: *"frameworks handle errors — of course the framework
determines how recovery looks; this is a restatement, not a finding."* EXP-0012 is the specific
quantitative result that defeats that reading. On the single-harness Claude Code corpus
(233 recovered failures, K=6, out-of-sample leave-one-out Brier):

| predictor | out-of-sample LOO-Brier improvement vs null |
|---|---|
| full 17-class error taxonomy | **+40.1%** |
| gate-type only (3-level: REDIRECTABLE / TERMINAL_GRANT / TRANSIENT) | **+41.8%** |
| **gate-BINARY only (single bit: "is this a redirectable hard-block?")** | **+39.4%** |
| error-class lift OVER gate-type-only | **−0.0043 (negative)** |
| error-class lift OVER the single gate bit | **+0.0017 (rounding error, ≤0.2%)** |

Plus: leave-one-CLASS-out CV is **−33%** (the per-class rates do not generalize; the headline
was memorized per-class rates leaked by leave-one-SAMPLE-out), and within-REDIRECTABLE the finer
error-class adds **V=0.000 / LOO-Brier +0.000**.

**The anti-tautology argument, precisely:** the entire 17-class error taxonomy carries essentially
NO predictive information about recovery modality beyond **one bit** of routing state. If "frameworks
handle errors" were the whole story, you would still expect error-CLASS to refine the prediction
(different errors → different framework handlers → different modalities). It does not: ≤0.2% lift.
Modality collapses onto a **single routing bit**, and that bit's *value-to-modality mapping itself
flips across harnesses on the SAME error* (CC/Gemini redirect; Codex abandons). That two-part
structure — (a) modality is a low-dimensional routing fact, not an error-class fact, AND (b) the
routing→modality map is harness-specific on identical inputs — is the non-obvious, non-tautological
content. No prior cluster below states both halves.

---

## (a) MAST / Cemri et al. 2025 — "Why Do Multi-Agent LLM Systems Fail?"  [VERIFIED: abstract + secondary body]

**What they do (verified):** First large systematic multi-agent failure study. MAST taxonomy =
**14 failure modes** in **3 categories** — System Design / Specification issues, Inter-Agent
Misalignment (~36.9% of failures), Task Verification — built from **1600+ annotated traces** across
AutoGen, CrewAI, LangGraph (and others; "MAST-Data, 7 frameworks" in the NeurIPS D&B version).
arXiv 2503.13657; ICLR Building-Trust Workshop 2025; NeurIPS 2025 D&B Track.

**Read depth:** VERIFIED at abstract level + a secondary-source body characterization (an independent
arXiv related-work section quoting the 14-mode / 3-category / 1600-trace structure and the 36.9%
inter-agent figure). I did NOT fetch the MAST PDF body itself; the category names and counts are
cross-confirmed across ≥2 sources, so I treat the *structure* as verified and the *fine internal
definitions* as abstract-level.

**CLAIM-0011 delta:** MAST's axis is **WHAT fails** (axis 1) — it characterizes and counts
failure *modes*. It does **NOT** characterize the recovery **modality** (axis 3): it does not ask,
for an identical error across harnesses, *whether* the agent redirects in-thread vs abandons, nor
attribute that choice to a routing layer. MAST is a taxonomy of failures; CLAIM-0011 is a
characterization of *recovery routing* that is explicitly orthogonal to (and, per EXP-0012,
**not improved by**) any failure taxonomy. Indeed EXP-0012 is the direct empirical statement that a
MAST-style finer failure taxonomy adds ≤0.2% over a single routing bit for predicting modality.
**No collision:** MAST does not pre-empt a routing-determines-modality claim; it occupies a
different axis and MAP-0002 already records it as "occupied taxonomy territory."

---

## (b) Reflexion (Shinn et al., NeurIPS 2023) / Self-Refine — the NULL CLAIM-0011 refutes  [VERIFIED: abstract; Reflexion mechanism from-memory+abstract]

**What they do (verified):** Reflexion (arXiv 2303.11366) reinforces language agents by **verbal
reinforcement** — the agent generates self-reflective text on a failed attempt and uses it as context
for the next attempt; "reinforces by updating language rather than model weights" (verified TL;DR).
Self-Refine is the sibling: iterative self-critique → self-revision within the model. Both locate
recovery competence **inside the model's reasoning loop** (axis 2).

**Read depth:** Reflexion abstract/TL;DR VERIFIED. The mechanism (memory buffer, evaluator,
self-reflection text injected as context) is from-memory + abstract, not a body re-read this session.
Self-Refine is from-memory (no fresh fetch this session) — flagged as such.

**CLAIM-0011 delta — THIS IS THE NULL HYPOTHESIS:** Reflexion/Self-Refine assert recovery is
**model-driven** — a function of the model's self-critique. CLAIM-0011's positive content is the
**refutation of that as the determinant of modality**: across 3 harnesses on identical errors, the
*modality* (redirect vs abandon) is fixed by the harness routing layer, not chosen by model
reasoning — same model class (e.g. frontier LLMs) yields opposite modalities purely as a function
of harness (the GATE-1 interventional arm, still open, is what would make this fully causal). EXP-0012
supplies the observational teeth: if recovery modality were model self-reflection, it would track the
*content* of the error (which the model reasons about) — but it tracks a **single routing bit** and
is invariant to the finer error-class (≤0.2%). That is the signature of a routing fact, not a
reasoning fact. **No collision** — Reflexion is the thing being refuted, not a pre-emption; but note
the honest limit: CLAIM-0011 has NOT yet run the same-model-cross-harness interventional test
(VERDICT-0038 GATE-1), so the refutation of model-as-determinant is currently *observational +
cross-harness*, not *interventional*. Do not overstate it as causally closed.

---

## (c) τ-bench / AgentBench / ToolEmu — the measurement/benchmark GENRE  [VERIFIED: abstracts]

**What they do (verified):**
- **τ-bench** (Yao, Shinn, Razavi, Narasimhan; arXiv 2406.12045): benchmark for tool-agent-user
  interaction; measures task success + **rule-following** in dynamic simulated-user conversations
  (retail/airline). τ²-bench (2506.07982) extends to dual-control. Measures *outcomes/reliability*.
- **AgentBench** (from-memory + MAP-0002 note): multi-environment agent benchmark; reports task
  success and bucketed failure reasons. Verified only as "named in MAP-0002 occupied territory" +
  from-memory; no fresh body fetch this session.
- **ToolEmu** (Ruan et al., ICLR 2024; arXiv 2309.15817): LM-emulated sandbox + LM safety evaluator
  to **identify and quantify risks/failures** of tool-using agents at scale (verified abstract).

**Read depth:** τ-bench and ToolEmu abstracts VERIFIED this session. AgentBench from-memory.

**CLAIM-0011 delta:** This genre **measures** agent behavior — success rates, rule adherence, risk
incidence. It does NOT isolate **recovery modality** as a dependent variable, and crucially does not
**attribute** modality to the harness routing layer vs the model. They are the *method* CLAIM-0011
sits within (real-trace measurement vs a NULL), not a competing thesis. Position: CLAIM-0011's
methodology (per-gate redirect-share with Wilson CIs, out-of-sample LOO-Brier vs informed baselines,
cross-harness replication) is in the same measurement-genre lineage, but the **measured construct is
new** — *routing-determined recovery modality* rather than task success/risk. **No collision.**

---

## (d) LangGraph ToolNode error-handling — FRAMEWORK-MEDIATED recovery (the CLOSEST prior)  [VERIFIED: docs + forum body]

**What they do (verified):** LangGraph's `ToolNode` is explicitly designed with error handling as a
"first-class citizen": it **catches tool exceptions and converts them into structured state updates**,
so the graph's conditional edges can route on the failure (verified: LangChain docs + dev.to writeup).
Patterns include `handle_tool_errors` (return a custom error message to the model so it can
self-correct), node-level **RetryPolicy** (automatic retry/backoff), and fallback edges. A LangChain
forum thread (Dec 2025, VERIFIED body) requests *graceful "Tool not found" handling in ToolNode to
enable agent self-correction* when the LLM hallucinates a non-existent tool — i.e. the framework
mediates whether a tool-not-found error is surfaced to the model for redirect or hard-thrown.

**Read depth:** VERIFIED — LangChain/LangGraph docs + dev.to body + forum-thread body read this
session. This is the cluster I could verify most concretely at body level.

**CLAIM-0011 delta — the precise, defensible distinction:** LangGraph **provides error-handling
hooks** within ONE framework. It demonstrably *mediates* recovery (catch → state update → edge
routing → retry/fallback/surface-to-model). What it does NOT do, and what CLAIM-0011 specifically
claims, is the **cross-harness comparative + determination** result:

- LangGraph offers *configurable* hooks — the developer chooses retry vs fallback vs surface. CLAIM-0011
  is an *empirical, descriptive* finding about **deployed production harnesses** (Claude Code, Codex,
  Gemini CLI) where the routing is a **fixed per-harness fact** the user does not configure, and where
  **identical errors produce systematically opposite modalities ACROSS harnesses** (CC/Gemini redirect
  vs Codex abandon, 66/66 & 6/6 vs 0/142).
- LangGraph documents *that a framework can route errors*. It does NOT establish that **modality is
  DETERMINED by the routing layer rather than the model**, nor that it is **invariant to error-class
  within a gate-type** (EXP-0012's ≤0.2%), nor does it run a **cross-harness identical-error**
  comparison. Those three are CLAIM-0011's specific delta over "frameworks handle errors."
- **Honest hedge / the real risk on this cluster:** the *conceptual claim* "the framework mediates
  recovery" is unambiguously prior art (LangGraph proves it). CLAIM-0011 is NOT novel as "frameworks
  can route errors." Its novelty rests ENTIRELY on (i) the cross-harness *determination*-and-*flip* on
  identical errors and (ii) the EXP-0012 demonstration that error-class is screened off by a single
  routing bit. If a reviewer reads CLAIM-0011 as "the harness routes recovery," LangGraph pre-empts it.
  The defensible framing must foreground (i)+(ii) and avoid the generic phrasing.
- **No direct collision found:** I found NO prior work (LangGraph included) that runs a *cross-harness*
  comparison showing the routing-table *determines* and *flips* recovery modality on identical errors.
  LangGraph documents within-framework hooks, not a cross-framework determination law. So no pre-emption
  of the specific delta — but it is the nearest neighbor and the claim must be phrased against it.

---

## Collision / near-collision audit (the orchestrator-relevant finding)

| candidate | does it pre-empt "cross-harness routing DETERMINES + FLIPS modality on identical errors"? |
|---|---|
| MAST | No — failure taxonomy axis, not recovery-modality; EXP-0012 shows it adds ≤0.2%. |
| Reflexion/Self-Refine | No — it is the *null* (model-driven); CLAIM-0011 refutes, not collides. |
| τ-bench/AgentBench/ToolEmu | No — measurement genre; measures success/risk, not routing-modality. |
| LangGraph ToolNode | **Closest.** Pre-empts the *generic* "framework mediates recovery." Does NOT pre-empt the cross-harness *determination+flip* + EXP-0012 screening-off. Claim survives ONLY in the specific framing. |
| **NEAR-COLLISION (newly surfaced):** "Quantifying Frontier LLM Capabilities for Container Sandbox Escape" (arXiv 2603.02277) | **Flag for orchestrator.** Reports **disengagement rates by MODEL** on failure: GPT-5.2 disengaged 92.3%, GPT-5-mini 60%, Claude 0% (continued to token limit). This is the SAME observable as CLAIM-0011's modality (abandon vs persist) but attributes it to the **MODEL**, not the harness. This is BOTH a tension and an opportunity: it is evidence FOR a model-driven account (the GATE-1 confound — Codex≈GPT abandons, CC/Gemini-Claude persists could be MODEL not HARNESS). CLAIM-0011 MUST address it: the cross-harness flip is currently confounded with model identity (Codex≈OpenAI, CC≈Claude, Gemini≈Google), so "harness routing" vs "model disposition" is exactly the un-discharged GATE-1. Read depth: VERIFIED abstract + body snippet (the disengagement figures). |

**Bottom line for orchestrator:** No prior work pre-empts the *specific* cross-harness
routing-determines-and-flips-modality claim at body level. BUT (1) LangGraph pre-empts the generic
"framework mediates recovery" — the claim must be phrased narrowly; and (2) the sandbox-escape paper
(2603.02277) is a genuine near-collision that gives a **MODEL-disposition** explanation for the same
abandon-vs-persist observable, which sharpens — does not refute — the open GATE-1 confound
(model-vs-harness). This STRENGTHENS the case that GATE-1 (same-model-cross-harness interventional)
is the load-bearing missing evidence, not a formality.

---

## Honest read-depth summary (VERIFIED vs from-memory)

| cluster | source verified this session | depth |
|---|---|---|
| MAST | arXiv 2503.13657 abstract + independent body-quoting related-work + HF/NeurIPS abstracts | abstract + secondary-body (structure verified, fine defs abstract) |
| Reflexion | arXiv 2303.11366 abstract + OpenReview TL;DR | abstract VERIFIED; mechanism from-memory+abstract |
| Self-Refine | — | from-memory (no fresh fetch) |
| τ-bench | arXiv 2406.12045 abstract + τ²-bench abstract | abstract VERIFIED |
| AgentBench | — | from-memory + MAP-0002 note |
| ToolEmu | arXiv 2309.15817 / ICLR 2024 abstract | abstract VERIFIED |
| LangGraph ToolNode | LangChain docs + dev.to body + LangChain forum thread body | **body VERIFIED** (the deepest read) |
| Sandbox-escape near-collision (2603.02277) | abstract + disengagement-rate body snippet | abstract + body-snippet VERIFIED |

I did NOT fetch full PDF bodies of MAST, Reflexion, τ-bench, or ToolEmu this session; their
distinctions above rest on VERIFIED abstracts (+ for MAST a secondary body source). I do not assert
any body-level internal-method distinction I could not read. The LangGraph distinction is the only one
grounded in body-level docs/forum reading, and the sandbox-escape near-collision figures are
body-snippet verified.

## Proposed MAP-0002 deltas (for ORCHESTRATOR — I do not edit the map)
- `key_prior_work` / `occupied_territory`: add explicit citations — MAST/Cemri-2025 (2503.13657),
  Reflexion/Shinn-2023 (2303.11366), τ-bench/Yao-2024 (2406.12045), ToolEmu/Ruan-2024 (2309.15817),
  LangGraph ToolNode error-handling — each tagged with the CLAIM-0011 delta axis (taxonomy / null /
  measurement-genre / framework-hooks-but-not-cross-harness-determination).
- `red_zones`: add the **model-vs-harness confound near-collision** (arXiv 2603.02277, per-MODEL
  disengagement rates) as direct pressure on the still-open GATE-1 interventional arm — the
  cross-harness flip is currently confounded with model identity.
- `open_gaps`: GATE-3 (prior-art positioning) DISCHARGED at the body-where-readable level; the binding
  remaining green-path blocker is GATE-1 (same-model-cross-harness interventional), now reinforced by
  the 2603.02277 near-collision.
