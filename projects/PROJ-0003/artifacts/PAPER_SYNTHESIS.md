# PROJ-0003 — PAPER SYNTHESIS (honest negative-result + measurement-methodology paper)

**Domain:** MAP-0002 — Agent failure attribution & recovery (workload models)
**Synthesizer:** researcher-0003-synth · **Date:** 2026-05-31 · **CPU-only, paper-track, document-only**
**Status of this doc:** synthesis OUTLINE of the durable surviving contribution of the
PROJ-0003 failure-attribution lineage. This is a **NEGATIVE result + a measurement methodology**,
framed as such. It does NOT edit any claim/verdict/map/experiment.

> **One-line thesis.** *Error-class does not predict agentic recovery; the cross-harness "recovery-modality"
> signal that looked like a finding is largely a measurement artifact plus a 3-way alias (harness x model x
> error-naming); the durable contributions are (1) a redirectable-vs-terminal **gate taxonomy** that is real
> and harness-agnostic, and (2) the **adversarial measurement discipline** that caught the artifacts — a
> "how to honestly measure agentic-recovery attribution, and the traps" contribution.*

---

## 0. Provenance & honesty posture (read first)

This paper is a *post-mortem-as-contribution*. The PROJ-0003 lineage set out to show **error-class predicts
agent recovery** (CLAIM-0008) and was driven down a refutation chain by its own adversarial gauntlet:

```diagram
CLAIM-0008  error-class -> recovery OCCURRENCE
   | EXP-0007 (support, but LOWER-BOUND label)  V=0.64, LOO-Brier -35% vs null
   | EXP-0008 (REFUTE under workaround scoring)  V 0.64->0.24 n.s.; LOO-Brier ~0
   v   surviving kernel re-seeded ->
CLAIM-0009  error-class -> recovery MODALITY (same-tool vs cross-tool)
   | EXP-0009 (support)  V=0.717, LOO-Brier +40.6%
   | EXP-0012 (DEFLATE)  error-class adds <=0.2% over a single REDIRECTABLE bit;
   |                      leave-one-CLASS-out CV = -33%; error-class == gate-type
   | EXP-0020 (terminal pole UN-demonstrable on this corpus)
   | EXP-0019 (flat routing-table REFUTED; fine layer high-entropy)
   v   reframed ->
CLAIM-0010  TWO-LAYER (coarse gate-table deterministic / fine adaptive)
   | EXP-0022 (PARTIAL: fine layer is learnable/context-conditioned, not "adaptive")
   | EXP-0029 (DEFLATE: coarse determinism is web_disabled-CARRIED; U 0.381->0.034 w/o it)
   v   cross-harness probe ->
CLAIM-0011  recovery modality is determined by HARNESS ROUTING (cross-harness)
   | EXP-0031 (support, 3-harness gate taxonomy consistent)
   | EXP-0032 (WEAKEN: inventory-overlap confound discharged; naming confound LIVE)
   | EXP-0033 (LARGELY REFUTE: Codex DOUBLE-LOG artifact -> CC-vs-Codex contrast dissolves;
   |            Gemini residual perfectly confounded with error-naming)
   v
DURABLE SURVIVOR = the gate TAXONOMY (real, harness-agnostic) + the MEASUREMENT METHODOLOGY.
The routing-vs-model-vs-prompt SEPARATION is observationally inseparable on-node (off-node-blocked).
```

**Why this is publishable.** Negative results + a transferable measurement methodology are an explicit fit
for **NeurIPS Datasets & Benchmarks** and measurement/eval workshops. The contribution is *not* "we found
that X predicts Y." It is *"here is a construct everyone wants to measure (agentic recovery attribution),
here are the specific traps that make naive measurements lie, here is the discipline that catches them, and
here is the one experiment that would actually settle it — which is off-node-blocked and we say so."*

---

## 1. THE NEGATIVE RESULT (what is refuted, stated precisely)

### 1.1 Error-class does NOT predict recovery OCCURRENCE (refuted, EXP-0007 -> EXP-0008)
- The apparent strong signal (Cramer's V=0.64, out-of-sample LOO-Brier -35% vs a class-agnostic null,
  permanent-vs-transient phi=0.45) was an artifact of a **lower-bound recovery definition** (same-intent
  retry only) plus one decisive cell: `policy.web_disabled` scored 0/109 "unrecoverable."
- That cell is **not unrecoverable** — it is a *redirectable gate*: the blocked `WebFetch` is replaced by a
  sanctioned `external_web_search`, 66/109 = 0.606, all audited as genuine same-goal recoveries.
- Once cross-tool workarounds are counted (EXP-0008, same corpus, K=6 window, intent-class matched), the
  signal **washes out**: V 0.644 -> 0.239 (permutation p=0.164, n.s.); LOO-Brier improvement +0.087 -> ~0
  (no gain over the null); the permanence axis collapses (phi 0.454 -> 0.138). **Occurrence-prediction is
  refuted.**

### 1.2 Recovery MODALITY collapses to a single gate-type bit (deflated, EXP-0009 -> EXP-0012)
- The surviving kernel — error-class predicts the *modality* (same-tool retry vs cross-tool redirect) — looked
  strong (EXP-0009: V=0.717, LOO-Brier +40.6%, robust to many knobs).
- **EXP-0012 dismantles the "error-class" framing:** the full 17-class taxonomy adds **<=0.2%** out-of-sample
  over a **single 1-bit REDIRECTABLE flag** (lift over gate-type-only LOO-Brier = -0.0043, *negative*).
  Leave-one-CLASS-out CV is **-33%** (per-class rates were memorized via leave-one-*sample*-out, they do NOT
  generalize to unseen classes). Within-REDIRECTABLE the finer class adds V=0.000. **error-class -> gate-type
  is a perfect function; the two are observationally inseparable on this single-harness corpus.** What predicts
  modality is one bit of *routing/config* state, not the error taxonomy.

### 1.3 The TWO-LAYER reframe deflates to "partial + web_disabled-carried" (EXP-0019/0022/0029)
- The flat "low-entropy routing table" thesis is **refuted** (EXP-0019: per-class next-tool norm-entropy 0.738
  ~= global 0.714; routing-only predictor worse than null).
- The coarse-deterministic / fine-adaptive reframe (CLAIM-0010) only *partially* holds: the fine layer is
  **context-conditioned and learnable** (LOO lift +0.09..+0.19), not free/adaptive (EXP-0022); and the coarse
  determinism is **carried by `web_disabled`** — drop it and Theil U(modality|gate) collapses 0.381 -> 0.034
  (EXP-0029). What survives is a quantified residual-entropy *floor* (~48%+ situation-dependent), not the
  original adaptive claim.

### 1.4 The cross-harness "modality regime" is LARGELY A MEASUREMENT ARTIFACT (EXP-0031 -> EXP-0033)
- The headline contrast (Claude Code 66/66 in-thread redirect vs Codex 0/142 abandon) **does not survive clean
  data.** **EXP-0033: Codex double-logs every tool call** (`function_call` + `mcp_tool_call_end`); EXP-0032
  double-counted (304). Deduped to 152 canonical blocks, **Codex's web twin fires BEFORE the block 152/152 ->
  Codex PREEMPTS 100%, it does not abandon/isolate.** So CC (79% preempt, 0.116 reactive) and Codex (100%
  preempt, 0.000 reactive) are *both preempt-dominant*; reactive rates overlap near zero. CC's own 66/66 drops
  to 2/43 under a uniform strict definition.
- The only nonzero in-thread reactive redirect is **Gemini (2/9, tiny n)** — and Gemini is the **only** harness
  whose block error *names an in-inventory alternative*. Modality is therefore **perfectly confounded with
  error-naming**, consistent with a **prompt/naming-driven** explanation, not harness-routing.

### 1.5 The binding separation (routing vs model vs prompt) is OBSERVATIONALLY INSEPARABLE on-node
- On every on-node corpus, modality is a **perfect 3-way alias**: HARNESS x MODEL (Claude Code=Claude,
  Codex=gpt-5.5, Gemini=Gemini — a perfect diagonal) x ERROR-NAMING (only Gemini names an in-inventory twin).
- The one model-agnostic harness present (OpenCode, 80 sessions) **logs neither model nor tool/error/outcome**
  — so the same-model-cross-harness cell cannot be run on-node. The near-collision arXiv:2603.02277 (per-MODEL
  disengagement: GPT-5.2 92% vs Claude 0%) gives a model-disposition account of the *same* abandon-vs-persist
  observable, making the alias load-bearing. **This separation is genuinely off-node-blocked** (see Section 4).

> **Net negative result (headline):** *Error-class does not predict agentic recovery (occurrence refuted;
> modality collapses to a 1-bit gate-type flag, <=0.2% over it); the apparent cross-harness modality signal is
> largely a measurement artifact (Codex double-log) plus an error-naming confound; and routing-vs-model-vs-prompt
> is observationally inseparable on single-harness / family-aliased traces.*

---

## 2. THE METHODOLOGY (the real, transferable contribution)

This is the part that is *positive* and *durable*. Every refutation above was produced by a specific piece of
adversarial measurement discipline. Packaged together, this is a reusable "how to honestly measure agentic
recovery attribution — and the traps" toolkit. **Each technique is paired with the trap it caught.**

| # | Discipline | The trap it caught (concrete) | Where |
|---|---|---|---|
| M1 | **Null-baseline comparison** (class-agnostic / modality-agnostic floor; report lift over NULL *and* over an *informed* baseline, not just over chance) | A predictor can beat chance and still be useless — error-class beat the null but added <=0.2% over a 1-bit gate flag | EXP-0008/0012 |
| M2 | **Out-of-sample leave-one-SAMPLE-out vs leave-one-CLASS-out CV** | LOSO leaks per-class rates (looked like +40%); LOCO (-33%) reveals the predictor memorized per-class rates and does NOT generalize to unseen classes | EXP-0012 |
| M3 | **Uniform / decoupled recovery definitions** (same-intent retry = LOWER bound; cross-tool workaround = UPPER bound; report both; K-sensitivity sweep) | The headline signal was a *definitional* artifact of the lower-bound label; broadening the definition washed it out (V 0.64->0.24) | EXP-0007/0008 |
| M4 | **Ablate the decisive cell** (leave-one-CLASS-out on the cell carrying the effect) | "Coarse layer is deterministic" was carried entirely by `web_disabled`: U 0.381 -> 0.034 without it | EXP-0029 (also EXP-0012) |
| M5 | **Double-log de-duplication** (canonicalize tool-call events before counting) | Codex logs every call twice; the entire CC-vs-Codex contrast was a 2x double-count — deduped, the contrast dissolves | EXP-0033 |
| M6 | **Naming-confound control** (does the error TEXT name an in-inventory alternative?) | The only residual cross-harness signal (Gemini 2/9) is perfectly confounded with error-naming -> prompt-driven, not routing-driven | EXP-0032/0033 |
| M7 | **3-way-alias diagnosis** (enumerate harness x model x error-text collinearity in the corpus inventory) | Established that "harness routing" cannot be separated from "model disposition" (2603.02277) or "error-naming" on any on-node corpus | v2 design Part B |
| M8 | **Strict reactive vs preempt vs abandon labeling** (a twin call BEFORE the block is PREEMPT, not redirect; only post-block in-thread is a reactive REDIRECT) | Lenient "any twin call after window" inflated redirect counts; the honest cross-harness-comparable metric is strict reactive-redirect-share with Wilson CIs | EXP-0032/0033 |
| M9 | **Anti-tautology delta test** ("if frameworks-handle-errors were the whole story, error-CLASS would still refine modality") | Frames the <=0.2% result as the *content*, distinguishing the finding from the trivially-true "frameworks route errors" (LangGraph ToolNode) | EXP-0012 + prior-art positioning |
| M10 | **Window/terminality sensitivity** (sweep K; test whether a "terminal" pole is class-determined or window-determined) | The "terminal" pole is window-dependent (term_rate 0.53->0.16 as K 3->24) and class-INDEPENDENT (V=0.238 n.s.) -> diffuse goal-abandonment, not a terminal error class | EXP-0020 |
| M11 | **The v2 factorial that WOULD resolve it off-node** (de-alias model x harness x error-text via a model-agnostic-harness pivot, pre-registered CI-separation pass/fail) | Specifies the *only* design that breaks the 3-way alias; pre-registers the KILL conditions so the result cannot be talked into a YELLOW | v2 design Part A |

**The methodological thesis:** agentic-recovery measurement is *unusually* prone to four specific lies —
(a) lower-bound outcome definitions, (b) one-cell-carried effects, (c) duplicate-log inflation, and (d)
harness/model/error-text collinearity. M1-M11 are the controls that catch each. This is the paper's primary
intended-reusable artifact (the gauntlet + the trap catalog).

---

## 3. WHAT SURVIVES as a positive claim (stated against what was refuted)

**Be precise about the survivor vs the casualties.**

### 3.1 SURVIVES (defensible positive)
- **The redirectable-vs-terminal GATE TAXONOMY is real and harness-agnostic.** Three structurally-equivalent
  gate types recur across all three on-node harnesses (EXP-0031): each harness has a **REDIRECTABLE** hard-block
  with a named sanctioned alternative (CC `web_disabled`; Codex `input_filter`; Gemini tool-not-in-inventory),
  a **GRANT-REQUIRED** permission gate (recovers same-tool only), and **TRANSIENT** failures (same-tool
  dominant). Per-gate redirect-shares are non-overlapping (REDIRECTABLE ~1.0 vs GRANT ~0.27 vs TRANSIENT ~0.25,
  Wilson CIs). The *taxonomy* — that gate TYPE (a low-dimensional routing/config fact), not the fine error
  class, is the right conditioning variable for recovery modality — is the durable structural finding.
- **Modality is a low-dimensional routing fact, not an error-class fact** (EXP-0012's 1-bit result), *within a
  harness*. This is the anti-tautology content: a 17-class taxonomy adds <=0.2% over one bit.

### 3.2 REFUTED / not defensible (do NOT claim)
- error-class -> recovery **occurrence** (refuted, Section 1.1).
- error-class -> recovery **modality** as anything beyond the gate-type bit (deflated to <=0.2%, Section 1.2).
- a flat low-entropy **routing table** (refuted, EXP-0019); a free **adaptive** fine layer (deflated to
  learnable/context-conditioned, EXP-0022).
- a demonstrable **terminal pole** on this corpus (un-demonstrable; window-dependent + class-independent,
  EXP-0020).
- **WHICH modality fires is determined by the harness routing layer** — this is the largely-refuted /
  unresolved claim. The cross-harness contrast was a double-log artifact (EXP-0033); the residual is
  naming-confounded (Section 1.4). **The taxonomy survives; the routing-DETERMINES-modality law does not (on-node).**

> **The honest one-sentence positive:** *There is a harness-agnostic gate taxonomy (redirectable / grant-required
> / transient) that is the correct low-dimensional conditioning variable for recovery modality; but WHICH modality
> fires within a gate is NOT error-class-determined and is NOT shown to be harness-routing-determined — that
> separation is off-node-blocked.*

---

## 4. VENUE FRAMING + the single weakest link

### 4.1 Venue
- **Primary: NeurIPS Datasets & Benchmarks (D&B) Track.** D&B explicitly welcomes negative results, measurement
  critiques, and methodology contributions. The paper's spine is a *measurement-discipline* contribution with a
  real-trace corpus and a refutation chain — squarely in scope. (MAP-0002 already records D&B as the lineage's
  target venue; the closest neighbor MAST/Cemri 2025 is itself a NeurIPS 2025 D&B paper, so the venue fit and
  the positioning neighbor coincide.)
- **Secondary: a measurement/evaluation workshop** (e.g. an agent-eval or "lessons from negative results"
  workshop) — appropriate if reviewers want the methodology foregrounded over a dataset artifact.
- **Framing discipline:** title and abstract must lead with the **negative + methodology** ("Measuring Agentic
  Recovery Attribution: A Negative Result and the Traps That Produce False Positives"), NOT a positive finding.
  Per the prior-art positioning, any phrasing near "the framework mediates recovery" is pre-empted by LangGraph
  ToolNode and must be avoided; the defensible deltas are (i) the cross-harness gate taxonomy and (ii) the
  EXP-0012 error-class-screened-off-by-one-bit result, presented as *measurement findings*, not laws.

### 4.2 Positioning (one line each)
- **MAST/Cemri (2503.13657):** WHAT-fails taxonomy axis — orthogonal; EXP-0012 shows a finer failure taxonomy
  adds <=0.2% for predicting recovery modality. No collision.
- **Reflexion/Self-Refine (2303.11366):** model-driven recovery = the NULL this work problematizes (modality
  tracks a routing bit, not error content) — but the refutation is observational, not interventional.
- **tau-bench / ToolEmu (2406.12045 / 2309.15817):** measurement GENRE we sit within; the measured construct
  (routing-conditioned recovery modality) is new.
- **LangGraph ToolNode:** closest prior — pre-empts the GENERIC "framework routes errors"; does NOT do the
  cross-harness comparison. Forces the narrow framing.
- **Container Sandbox Escape (2603.02277):** near-collision — per-MODEL disengagement gives a model-disposition
  account of the same observable; this is exactly the confound that makes the off-node interventional binding.

### 4.3 THE SINGLE WEAKEST LINK (state it openly in the paper)
**The off-node interventional gap.** Every causal-sounding claim ("harness routing determines modality") is
*observational* and confounded by a perfect on-node **harness x model x error-naming** alias. The one experiment
that resolves it — the **v2 factorial** (OpenCode-pivot, cells C1-C6: same model in two harnesses, same harness
with two models, error-text held fixed/named-vs-unnamed; N>=30/cell; Wilson CI separation; logistic GLM on
harness+model+errortext; pre-registered PASS = |R(C1)-R(C2)|>0.5 AND R(C2)~R(C3), pre-registered KILL =
model-disposition or error-text dominates) — **cannot be run on-node** because the only model-agnostic harness
(OpenCode) logs neither model nor tool outcomes. The paper must present the gate taxonomy + methodology as the
contribution and the v2 factorial as the explicitly-scoped, pre-registered future work that would convert the
observational characterization into a causal law. **Do not overclaim causal determination.**

---

## 5. PROPOSED PAPER STRUCTURE (section map)

1. **Introduction** — agentic recovery attribution is a construct everyone wants to measure; naive measurements
   lie; we report a negative result and the discipline that produced it.
2. **Related work & the three axes** — WHAT-fails (MAST) / HOW-model-recovers (Reflexion=null) /
   HOW-routed (this work); LangGraph pre-empts the generic phrasing; 2603.02277 is the model-vs-harness pressure.
3. **Corpus & taxonomy** — real Claude Code / Codex / Gemini traces; the 17-class error taxonomy; the
   redirectable / grant-required / transient gate taxonomy (the survivor, Section 3.1).
4. **The negative result** — the EXP-0007->0008 occurrence refutation; EXP-0009->0012 modality-to-1-bit
   deflation; EXP-0019/0022/0029 two-layer deflation (Section 1).
5. **The measurement artifacts** — Codex double-log (EXP-0033); naming confound (EXP-0032/0033); the 3-way alias
   (Section 1.4-1.5).
6. **Methodology (the contribution)** — M1-M11 trap catalog (Section 2); the adversarial gauntlet as a reusable protocol.
7. **The interventional gap & pre-registered v2 factorial** — what would settle it; why it is off-node-blocked;
   the pre-registered pass/kill conditions (Section 4.3).
8. **Conclusion** — what survives (gate taxonomy + methodology) vs what is refuted; an honest call for off-node
   harness-controlled interventional studies of agentic recovery.

**Limitations to state plainly:** single-harness for the core numbers; decisive cells rest on small n
(web_disabled n~109, perm_denied n~30, Gemini blocks n=9); no cleanly-terminal class sampled at n>=10; the
causal claim is off-node-blocked.

---

## 6. SUMMARY FOR ORCHESTRATOR

- **Negative result:** error-class does not predict recovery (occurrence refuted EXP-0008; modality collapses
  to a 1-bit gate flag, <=0.2% over it, EXP-0012); cross-harness modality signal is largely a Codex double-log
  ARTIFACT (EXP-0033) + error-naming confound; routing vs model vs prompt is observationally inseparable on-node.
- **Survives:** the redirectable / grant-required / transient GATE TAXONOMY (harness-agnostic, EXP-0031) +
  modality-is-a-1-bit-routing-fact within a harness. **Refuted:** occurrence prediction, error-class modality
  prediction, flat routing table, adaptive fine layer, terminal pole, and routing-DETERMINES-modality (on-node).
- **Methodology = the real contribution:** M1-M11 (null + informed baselines, LOSO-vs-LOCO CV, uniform/decoupled
  recovery defs, decisive-cell ablation, double-log dedup, naming-confound control, 3-way-alias diagnosis,
  strict reactive-vs-preempt-vs-abandon labeling, anti-tautology delta, window/terminality sensitivity, and the
  pre-registered off-node v2 factorial).
- **Venue:** NeurIPS Datasets & Benchmarks (negative result + measurement methodology); secondary = an
  agent-eval/measurement workshop. Lead with the negative+methodology framing; avoid the LangGraph-preempted
  generic phrasing.
- **Weakest link:** the off-node interventional gap — the harness x model x error-naming alias is unbreakable
  on-node (OpenCode logs no model/outcome); the v2 factorial is the only resolver and it is off-node-blocked.
