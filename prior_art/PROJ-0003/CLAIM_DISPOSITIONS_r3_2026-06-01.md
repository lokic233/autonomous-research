# PROJ-0003 — Claim Dispositions (wind-down) for the non-live claims

**Author:** researcher-0003-winddown-r3 · **Date:** 2026-06-01 (UTC) · **Domain:** MAP-0002 · **CPU/doc-only**
**Scope:** Consolidated, current disposition of the PROJ-0003 claims that are **NOT** the live committee-bound
claim. The single live, committee-bound claim is **CLAIM-0012** (failure burstiness / over-dispersion),
YELLOW under **VERDICT-0047**, with a bounded GREEN-path in flight (EXP-0044, owned by ablations-r3) — it is
**out of scope here** except as the reference point that everything else is *not*.
**Purpose:** make the negative-result+methodology paper's "claim-status / what-we-honestly-found" section
accurate and submission-ready, incorporating the new r3 cross-harness evidence (CLAIM-0009 XHARNESS Codex V=0.586).
**Honesty posture:** salvage is not a goal. Where a claim is dead, it is marked dead. This document recommends
only; it makes **no** claim/verdict/map edits. Proposed MAP-0002 deltas are in §4.

**Companion docs (authoritative sources this consolidates, not supersedes):**
`CLAIM-0009_XHARNESS_r3_2026-06-01.md`, `CLAIM-0010_final_determination.md`, `CLAIM-0011_final_determination.md`,
`PAPER_SYNTHESIS.md`, `PAPER_REVIEW_REDTEAM.md`, `registry/academic_map.yaml` (MAP-0002).

---

## 1. DISPOSITION TABLE (one coherent view of the non-live claims)

All four claims below carry a registry `final_verdict: yellow` on their latest verdict. **In this lineage
"YELLOW" never meant "promising-and-open"** — it is the gauntlet's "not-GREEN, not-cemetery, disposition-pending"
state. Every one of these four has since been driven to a final researcher determination (refuted or
deflated-to-a-config-fact) and **folded into the negative-result+methodology synthesis**. None is open. None
needs a committee re-convene.

| Claim | What it asserted | Controlling verdict (latest) | Honest status (one line) | Disposition |
|---|---|---|---|---|
| **CLAIM-0008** | error-class predicts recovery **OCCURRENCE** | **VERDICT-0016** (yellow; chain V0009→V0015→V0016) | **DEAD / refuted.** Apparent signal (V=0.64) was a *lower-bound* recovery-definition artifact carried by one cell (`web_disabled` scored 0/109 "unrecoverable"); once cross-tool workarounds are counted the signal washes out (V 0.64→0.24, perm-p=0.164 n.s.; LOO-Brier +0.087→~0; permanence φ 0.45→0.14). | DONE — refuted; folded into synthesis §1.1. |
| **CLAIM-0009** | error-class predicts recovery **MODALITY** (same-tool retry vs cross-tool redirect) | **VERDICT-0027** (yellow; chain V0018→V0020→V0021→V0026→V0027) | **MIXED → folded-as-config-fact.** The *within-harness* association is REAL and now **replicates on a 2nd independent harness** (Codex Cramér's **V=0.586, perm-p=0.0002, N=78**, vs Claude-Code EXP-0009 V=0.717) — but the *mechanism does not transfer* (Codex has no `web_disabled`/`perm_denied` policy-gate; its V is carried by transient-exec redirects, a different gate structure), and EXP-0012 collapses the within-harness effect to a **1-bit gate-type flag** (full 17-class taxonomy adds ≤0.2%; LOCO −33%). The clean cross-harness *mechanism* law and the interventional de-aliasing leg are **off-node-blocked**. | DONE — deflated to config-fact + the gate taxonomy; folded into synthesis §1.2 / §3.1. **Revival = off-node interventional (v2 OpenCode-pivot factorial).** |
| **CLAIM-0010** | **TWO-LAYER** recovery: coarse gate-table deterministic + fine adaptive | **VERDICT-0044** (yellow; chain V0030→V0035→V0044) | **DEAD as a standalone thesis.** Both pillars dissolve: the coarse "layer" is 91% one cell (`web_disabled`; Theil-U 0.381→0.034 w/o it, EXP-0029) and that cell's "deterministic redirect" is the EXP-0033 measurement artifact (~79% PREEMPT mislabeled as reactive redirect); EXP-0012 reduces the coarse layer to the same 1-bit gate-type config-fact. The fine layer's only material lift (+12.6 pts) lives in that same artifact cell and is CC-policy-specific; the durable remainder is the **negative result** (a ~0.6–0.74 residual-entropy floor). | DONE — deflated-to-config-fact + residual-floor negative result; folded into synthesis §1.3. |
| **CLAIM-0011** | recovery modality is **determined by HARNESS ROUTING** (cross-harness) | **VERDICT-0042** (yellow; chain V0036→V0038→V0039→V0040→V0042) | **DEAD / refuted on-node.** The headline cross-harness contrast (CC 66/66 redirect vs Codex 0/142 abandon) was a **Codex double-log artifact** — deduped, Codex PREEMPTS 152/152; both harnesses are preempt-dominant. The only surviving significant difference (CC reactive 5/43 vs Codex 0/152, Fisher p=0.0004) is **direction-wrong** vs the claim and **perfectly aliased with MODEL disposition** (arXiv:2603.02277). What survives is the (non-novel, pre-existing EXP-0008/MAP-0002) gate taxonomy, not a routing law. | DONE — refuted-on-node; folded into synthesis §1.4. **Revival = same off-node v2 factorial.** |

**Cross-cutting:** the three claims that touch modality (0009/0010/0011) all reduce to the *same* two
components — (a) the harness-agnostic **gate taxonomy** (redirectable / grant-required / transient), which
survives as a *characterization*, and (b) the negative results (no occurrence prediction; modality is a 1-bit
routing fact, not error-class; large residual-entropy floor; cross-harness *routing law* not supported). The
genuinely durable positive contribution across all of them is the **M1–M11 measurement methodology** that
caught the artifacts (PAPER_SYNTHESIS §2). Nothing here is salvaged as an open forward claim.

---

## 2. THE NEW r3 CROSS-HARNESS EVIDENCE — what it changes, precisely

The r3 cross-harness run (`CLAIM-0009_XHARNESS_r3_2026-06-01.md`, EXP-XHARNESS-r3 on the already-collected
Codex corpus) is the **only material evidence change** since the four claims were dispositioned on 2026-05-31.
It is honestly **MIXED**, and it moves nothing back to "open":

- **What it ADDS (the weak claim, strengthened):** error-class → recovery-modality is now an **out-of-sample,
  second-harness-significant** association — Codex **V=0.586, perm-p=0.0002, N=78 recovered failures**, apples-to-apples
  with EXP-0009's Claude-Code V=0.717. The "error-class predicts HOW you recover" association is therefore
  *not* a single-harness artifact. This is a real, citable, positive replication of the **association**.
- **What it does NOT deliver (the strong claim, still not GREEN):** the **mechanism does not transfer.** Codex
  has no `web_disabled` hard policy-block and no `perm_denied` contrast — both load-bearing cells of EXP-0009
  are absent. Codex's V is carried by *transient exec* failures (`cmd.notfound` 0.944, `proc.exit_nodetail`
  0.842) redirecting to other exec tools — a "try-another-command" mechanism, not the REDIRECTABLE-vs-TERMINAL
  policy-gate dichotomy that is CLAIM-0009's actual claimed law. Under the uniform strict + double-log-deduped
  definition (EXP-0033) the dramatic CC-vs-Codex modality *contrast* also collapses (both PREEMPT-dominant).
- **Net effect on disposition:** CLAIM-0009 stays **DONE / deflated-to-config-fact**, with its status sharpened
  from "association supported (single harness)" to "**association replicates cross-harness (V 0.59–0.72), but
  harness-SPECIFIC in mechanism; the clean harness-agnostic routing law remains off-node-blocked.**" This is a
  *more honest* statement, not a revival.

This finding is incorporated into the paper claim-status framing in §3.

---

## 3. PAPER CLAIM-STATUS SECTION — "What We Honestly Found" (draft, r3-current)

> Drop-in replacement/refresh for the claim-status framing in PAPER_SYNTHESIS §1/§3. Updated to reflect
> VERDICT-0047 (the live CLAIM-0012 boundary) and the r3 XHARNESS Codex V=0.586 finding. Lead with the
> negative + methodology; do not overclaim. Every number traces to an experiment on record.

### 3.1 Claim-status summary (paper-facing)

The lineage set out to show **error-class predicts agentic recovery**. Under its own adversarial gauntlet it
was driven to a negative result with one surviving characterization and a reusable measurement methodology.
Honest per-claim status:

1. **Recovery OCCURRENCE is not error-class-predictable (REFUTED).** The apparent strong predictor (V=0.64)
   was an artifact of a lower-bound recovery definition concentrated in a single redirectable-gate cell; under
   a workaround-aware definition the effect vanishes (V 0.64→0.24, n.s.; no LOO-Brier gain over a class-agnostic
   null).

2. **Recovery MODALITY is a 1-bit routing/config fact, not an error-class fact (DEFLATED).** Conditioning on a
   single REDIRECTABLE gate-bit captures the effect; the full 17-class error taxonomy adds **≤0.2%** out-of-sample
   and **fails to generalize to unseen classes** (leave-one-CLASS-out CV = −33%). The *within-harness*
   error-class→modality **association is real and replicates across two independent harnesses** (Claude Code
   Cramér's V=0.717; Codex **V=0.586, perm-p=0.0002, N=78**) — but it is **harness-specific in mechanism**: the
   Claude-Code effect is carried by a policy-gate redirect (`web_disabled`→sanctioned web search), whereas the
   Codex effect is carried by transient-exec "try-another-command" redirects, with **no** equivalent policy-gate
   structure present. So: the *association* is harness-robust; the *mechanism / clean harness-agnostic routing
   law* is not, and is **off-node-blocked**.

3. **The two-layer (coarse-deterministic / fine-adaptive) reframe does not survive (DEFLATED to config-fact +
   noise floor).** The coarse "layer" is 91% one cell, and that cell's "determinism" is a measurement artifact
   (≈79% preemptive parallel tool-firing mislabeled as reactive redirect). The fine layer's only material lift is
   inside that same artifact cell and is single-harness/CC-policy-specific. The durable content is the negative
   result: recovery tool-choice has a large (~48%+) irreducible, situation-dependent residual-entropy floor.

4. **Recovery modality is NOT shown to be harness-routing-determined (REFUTED on-node).** The headline
   cross-harness contrast was a Codex double-log artifact; deduped, both harnesses are preempt-dominant. The
   one surviving significant difference is direction-wrong relative to the claim and is perfectly aliased with
   per-model disposition (arXiv:2603.02277). The routing-vs-model-vs-error-naming separation is a perfect
   on-node 3-way alias and is genuinely off-node-blocked.

**What survives as a positive characterization (not a law):** a **harness-agnostic gate taxonomy**
(REDIRECTABLE / GRANT-REQUIRED / TRANSIENT) that is the correct *low-dimensional conditioning variable* for
recovery modality, recurring structurally across all three on-node harnesses. **What is the real contribution:**
the **M1–M11 adversarial measurement discipline** (null+informed baselines, LOSO-vs-LOCO CV, decoupled recovery
definitions, decisive-cell ablation, double-log dedup, naming-confound control, 3-way-alias diagnosis, strict
reactive-vs-preempt labeling, anti-tautology delta, window/terminality sensitivity, and the pre-registered
off-node v2 factorial) — a "how to honestly measure agentic-recovery attribution, and the traps" toolkit.

### 3.2 One-paragraph version (abstract-grade)

> *Error-class does not predict whether an agent recovers (occurrence refuted), and predicts only a single
> bit of recovery modality — a routing/config gate-type flag, not the 17-class error taxonomy (which adds
> ≤0.2%). The within-harness error-class→modality association is real and replicates on a second independent
> harness (Cramér's V = 0.59–0.72, perm-p ≤ 2e-4), but the underlying mechanism is harness-specific (a policy
> redirect on one harness, transient-exec retries on another), and the apparent cross-harness "routing
> regime" was largely a double-log measurement artifact plus a per-model-disposition / error-naming confound.
> The durable contributions are (1) a harness-agnostic gate taxonomy that is the right conditioning variable
> for recovery modality, and (2) the adversarial measurement discipline that caught each of these traps. The
> one experiment that would convert the observational characterization into a causal routing law — a
> model-agnostic-harness interventional factorial — is off-node-blocked, and we say so.*

### 3.3 Scope guard vs the live claim
This claim-status section covers ONLY CLAIM-0008/0009/0010/0011. **CLAIM-0012** (real-trace tool-call failures
are temporally over-dispersed / bursty within a session) is a separate, **live, descriptive** characterization
claim at YELLOW (VERDICT-0047) with a bounded CPU GREEN-path in flight (Codex LOSO + latent-state Cox +
gate-stripped Hawkes refit, EXP-0044). It must be presented as the lineage's *current* forward work, not as
part of the refuted/deflated set, and its status should be quoted from VERDICT-0047, not frozen.

---

## 4. OPEN vs DONE + committee status

### 4.1 DONE (dispositioned; no further on-node work; no committee re-convene)
- **CLAIM-0008** — DONE, refuted. Controlling: VERDICT-0016. Nothing open.
- **CLAIM-0009** — DONE, deflated-to-config-fact. Controlling: VERDICT-0027. The r3 XHARNESS run is the *last*
  CPU-extractable evidence from existing logs; it lands MIXED and is incorporated. Nothing further is
  CPU-extractable.
- **CLAIM-0010** — DONE, deflated-to-config-fact + residual-floor. Controlling: VERDICT-0044. Nothing open.
- **CLAIM-0011** — DONE, refuted-on-node. Controlling: VERDICT-0042. Nothing open.

### 4.2 OPEN, but only as explicitly-scoped, off-node-blocked **revival conditions** (NOT active work)
These are documented revival doors on wound-down notes, not open claims:
- **The off-node interventional v2 factorial** (`CLAIM-0009_interventional_PROTOCOL.md`, canonical): the
  OpenCode-pivot 6-cell factorial (C1–C6, GLM, pre-registered PASS/KILL, n≈50/cell) that de-aliases
  harness × model × error-naming. Resolves CLAIM-0009 (mechanism) and CLAIM-0011 (routing law), and answers
  CLAIM-0010's coarse/fine questions as a GLM by-product. **Blocked:** no on-node harness is simultaneously
  controllable, model-agnostic, AND fully logged (OpenCode logs 0/6 required fields).
- **A sampled TERMINAL gate class** (XHARNESS_r3 §4): the trichotomy's terminal pole is censored in every
  corpus; it must be *injected* via a no-twin hard-block shim, i.e. part of the off-node battery, not a
  CPU re-analysis.

Both are future-work, not pending committee items. They are correctly recorded in the synthesis (§4.3, M11)
as the paper's stated limitation + the experiment that would settle it.

### 4.3 Committee status — CONFIRMED: no re-convene needed for these four
**CLAIM-0012 is the only live, committee-bound claim in PROJ-0003** (VERDICT-0047, YELLOW; GREEN-path owned by
ablations-r3 / EXP-0044). CLAIM-0008/0009/0010/0011 are each at a terminal researcher determination, folded
into the negative-result+methodology synthesis, with their controlling YELLOW verdicts standing as the last
committee word. None has a GREEN-path that requires a committee, none is awaiting a vote, and none should be
re-packeted: the only thing that could revive 0009/0010/0011 is the off-node interventional battery, which is
blocked and is recorded as future work, not as an open committee question. **No committee re-convene is
warranted for any of the four.**

---

## 5. PROPOSED MAP-0002 DELTAS (recommend only — orchestrator applies; this file edits nothing)

> Rationale: the existing MAP-0002 narrative still says CLAIM-0009's cross-harness leg is "harness-specific /
> NOT met" and predates the r3 quantified Codex V. It should record the *quantified* replication-of-association
> alongside the mechanism-non-transfer, so the map and the paper agree.

1. **CLAIM-0009 line (currently "Clean 'gate→modality REPLICATES' NOT met (harness-specific)"):** append —
   *"r3 cross-harness (EXP-XHARNESS-r3, 2026-06-01): error-class→modality ASSOCIATION replicates on Codex
   (Cramér's V=0.586, perm-p=0.0002, N=78) vs CC V=0.717 — association is harness-ROBUST; but mechanism is
   harness-SPECIFIC (Codex transient-exec redirects, no policy-gate / no `web_disabled`|`perm_denied` cell).
   CPU corpus now exhausted; clean routing law remains off-node-blocked. Disposition unchanged: DONE/deflated-to-config-fact."*
2. **`project_status` / claim roster:** keep CLAIM-0008/0010/0011 as DONE-refuted/deflated; restate CLAIM-0009
   as **DONE — deflated-to-config-fact, association cross-harness-replicated (V 0.59–0.72), mechanism
   off-node-blocked** (rather than the older "SUPPORTED, folded-as-config-fact" phrasing, which under-states
   the mechanism caveat now that the 2nd-harness number is in hand).
3. **No change** to the four claims' `final_verdict` registry entries, to CLAIM-0012's live status, or to the
   off-node v2 revival-door records (they remain correct).

---

## 6. FILES
- this doc: `prior_art/PROJ-0003/CLAIM_DISPOSITIONS_r3_2026-06-01.md`
- new cross-harness evidence: `prior_art/PROJ-0003/CLAIM-0009_XHARNESS_r3_2026-06-01.md`
  (impl/output `experiments/2026-06-01/EXP-XHARNESS-r3/`)
- final determinations: `prior_art/PROJ-0003/CLAIM-0010_final_determination.md`,
  `prior_art/PROJ-0003/CLAIM-0011_final_determination.md`
- synthesis + red-team: `prior_art/PROJ-0003/PAPER_SYNTHESIS.md`, `prior_art/PROJ-0003/PAPER_REVIEW_REDTEAM.md`
- live-claim boundary (out of scope here): `registry/verdicts/PROJ-0003/2026-06-01/VERDICT-0047.yaml`,
  `prior_art/PROJ-0003/CLAIM-0012_GREENPATH_r3_2026-05-31.md`
- controlling verdicts: CLAIM-0008→VERDICT-0016, CLAIM-0009→VERDICT-0027, CLAIM-0010→VERDICT-0044,
  CLAIM-0011→VERDICT-0042 (all `final_verdict: yellow`, all dispositioned to DONE per researcher determinations).
