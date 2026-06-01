# CLAIM-0009 — Cross-Harness + Interventional FINALIZED PROTOCOL (r3 reconciliation)

**Author:** researcher-0009-xharness-r3 · **Date:** 2026-06-01 · **Domain:** MAP-0002 · **CPU-only**
**Reconciles:** `CLAIM-0009_crossharness_interventional_design.md` (v1) + `CLAIM-0009_interventional_design_v2.md` (v2) + `CLAIM-0009_interventional_PROTOCOL.md` (consolidated)
**Executed NOW:** apples-to-apples cross-harness Cramér's V on the Codex corpus (second already-collected harness).
**Status of the parent project (per registry/academic_map.yaml):** PROJ-0003 is recorded DONE / negative-result+methodology paper FINALIZED; all 4 claims refuted/deflated. This document does NOT overturn that — it reconciles the interventional designs into one runnable spec AND reports an honest, freshly-run cross-harness number with its caveats.

---

## TL;DR (honest)

1. **The single canonical interventional protocol is the consolidated `CLAIM-0009_interventional_PROTOCOL.md`** (OpenCode-pivot 6-cell factorial C1–C6, GLM, pre-registered PASS/KILL, n=50/cell TARGET). v1 and v2 are fully subsumed; nothing in them needs separate execution. See §1 for the reconciliation map.
2. **The interventional manipulation = a deterministic tool-block shim** (§2). It IS causally interpretable: the same byte-identical block is injected across cells while harness/model/error-naming are crossed; the control is the UNNAMED arm and the on-node anchor cells. This is a genuine *do(error-class)* intervention, not re-observation — but it is **off-node-blocked** because no on-node harness is simultaneously controllable, model-agnostic, AND fully logged (OpenCode logs 0/6 required fields).
3. **CPU-runnable NOW:** the cross-harness *observational* replication on the **Codex** corpus (already collected, `~/.codex/sessions`). I ran it. **Result: Codex error-class → recovery-modality Cramér's V = 0.586, perm-p = 0.0002, N=78 recovered failures.** The Claude-Code anchor (EXP-0009) was V=0.717. So the *association replicates on a second independent harness* — both strong, both perm-p=0.0002.
4. **BUT the cross-harness replication does NOT deliver the GREEN the claim needs**, for two honest reasons: (a) the **gate STRUCTURE differs** between harnesses — Codex has no `web_disabled` clean REDIRECTABLE policy-gate; its V is carried by transient exec failures (`cmd.notfound`, `proc.exit_nodetail`) redirecting to other exec tools, not the REDIRECTABLE-vs-TERMINAL policy dichotomy that is CLAIM-0009's actual mechanism; (b) under a **uniform strict + double-log-deduped** definition (EXP-0033) the dramatic CC-vs-Codex modality CONTRAST collapses — both harnesses are PREEMPT-dominant with near-zero *reactive* redirect (CC 0.116, Codex 0.000). So "modality is a clean harness-agnostic law" is **not** supported; "error-class associates with modality within each harness" **is** (V 0.59–0.72), but the association is harness-SPECIFIC in its mechanism.
5. **What still blocks 6/6 GREEN:** the **interventional** leg (do-manipulation that de-aliases harness × model × error-naming) — genuinely off-node-blocked — and a **sampled TERMINAL class** (still absent in both corpora). The cross-harness leg is now *runnable and run*, but it lands as honest-mixed, not GREEN.

---

## 1. RECONCILIATION — one protocol, three docs

| doc | what it contributed | disposition |
|---|---|---|
| v1 (`..._crossharness_interventional_design.md`) | first cross-harness arm (A2) + interventional "remove the alternative" arms (Arm1/2/3) + a CPU quasi-interventional proxy | **SUBSUMED.** Its quasi-interventional proxy (alternative-present vs absent) is already discharged on-node via the Codex contrast; its rebuild-affordance arms are folded into the cleaner factorial route-variation. |
| v2 (`..._interventional_design_v2.md`) | the C1–C6 OpenCode-pivot factorial + strict modality metric | **SUBSUMED.** Same cells/metric, but under-specified the equivalence-test power. |
| PROTOCOL (`..._interventional_PROTOCOL.md`) | locked N tiers, byte-exact injection strings, full GLM/LRT, §7 harness+logging requirements, pre-registered PASS/KILL tree | **CANONICAL. This is the single runnable spec.** Nothing to add except the freshly-run cross-harness number below and the explicit terminal-class fix (§4). |

**Decision: execute `CLAIM-0009_interventional_PROTOCOL.md` verbatim when an off-node controllable+logged harness exists. v1/v2 are archival.** This r3 doc adds (a) the executed Codex cross-harness V, (b) a sharpened terminal-class sampling fix, (c) the CPU-NOW vs new-run vs blocked triage, (d) the CLAIM-0010 note.

---

## 2. THE INTERVENTIONAL MANIPULATION — why it is causal, and what the control is

**The manipulation (do(error-class)):** a single MCP/tool shim registered as `url_fetch`. On every call it returns a **deterministic, content-free hard-block** (byte-identical error string). A functional sanctioned twin `web_search` is present in inventory in *every* cell. Two error-text variants run as a sub-factor:
- UNNAMED: `External webpage access is not permitted.`
- NAMED:   `External webpage access is not permitted. Use web_search instead.`

**Why this is causal, not re-observation:** in EXP-0009/0031/0032/0033 the error-class was *observed* as it naturally occurred — so error-class is perfectly aliased with HARNESS × MODEL × ERROR-NAMING (the 3-way alias). The shim **manipulates** the stimulus: the SAME block is injected into different (harness, model, naming) cells with everything else byte-identical, and the agent's modality is measured. That is do(stimulus) with the confounders crossed as factors → the GLM coefficient on F_harness *after conditioning on F_model + F_error_naming* is the causal estimand. The naming sub-factor is a within-design intervention on the error TEXT (the EXP-0033 live confound), held against an otherwise-identical block.

**The control(s):**
- **UNNAMED arm** is the control for the NAMED arm (isolates the error-text effect: C2 vs C5, C3 vs C6).
- **On-node anchor cells** C1 (CC×Claude) and C4 (Codex×GPT) are positive controls: they must reproduce the observed on-node behavior (C1 ≈ CC redirect rate; C4 ≈ Codex preempt-dominant), proving the shim/battery faithfully reproduce the natural stimulus before any off-diagonal cell is trusted.
- **Pivot control:** C2 (OpenCode×Claude) vs C1 (CC×Claude) — *model held, harness varies* → isolates harness. C2 vs C3 (OpenCode×GPT) — *harness held, model varies* → isolates model.

This is exactly the manipulation specified in PROTOCOL §1–§3; it is correct and causally interpretable. It is **off-node-blocked solely by harness logging** (PROTOCOL §7.2/§7.3): on-node OpenCode logs 0/6 required fields (no model, no tool name, no args, no outcome/error, no order/ids beyond opaque counts), so the de-aliasing cells cannot be parsed even if run.

---

## 3. CROSS-HARNESS — EXECUTED NOW on the second already-collected harness (Codex)

**Provenance:** `~/.codex/sessions/**/*.jsonl` — REAL, already-collected local Codex CLI rollout logs (no new data run). 69 sessions ≥2 calls, 104 ground-truth failures. Parse/intent/routing logic mirrors EXP-0009 verbatim (`prior_art/PROJ-0003/crossharness_scripts/codex_xharness.py`), extended only to compute the among-recovered Cramér's V + 5000-shuffle permutation the same way EXP-0009 T1 did.
**Impl:** `experiments/2026-06-01/EXP-XHARNESS-r3/impl/codex_cramersv.py` · **Output:** `.../results/codex_cramersv_out.txt`.

### Result (apples-to-apples with EXP-0009 Claude-Code V=0.717)

| harness | corpus | N (recovered) | classes | global redirect p0 | **Cramér's V** | perm-p |
|---|---|---|---|---|---|---|
| **Claude Code** (EXP-0009) | ~/.claude/projects, 74 sess | 232 | 16 | 0.504 | **0.717** | 0.0002 |
| **Codex** (this run, EXP-XHARNESS-r3) | ~/.codex/sessions, 69 sess | **78** | 6 | 0.756 | **0.586** | **0.0002** |

Codex per-class (among recovered): `cmd.notfound` 34/36 redirect (0.944) · `proc.exit_nodetail` 16/19 (0.842) · `fs.notfound` 5/10 (0.500) · `fs.exists` 3/7 (0.429) · `code.build` 1/5 (0.200) · `proc.timeout` 0/1.

### Honest reading
- **REPLICATES (the weak claim):** error-class is a strong, out-of-sample-significant predictor of recovery modality on a *second independent harness* (V=0.586, perm-p=0.0002). The "error-class → HOW you recover" association is not a single-harness artifact.
- **DOES NOT replicate (the strong claim = CLAIM-0009's mechanism):** the **REDIRECTABLE-vs-TERMINAL policy-gate dichotomy** does not transfer. Codex has **no `web_disabled` hard policy-block and no `perm_denied` contrast** — both load-bearing cells of EXP-0009 are absent. Codex's V is carried by *transient exec* failures (`cmd.notfound`/`proc.exit_nodetail`) redirecting to other exec tools — a different mechanism (try-another-command), not the policy-gate routing that is CLAIM-0009's claimed law. The two harnesses agree that error-class matters but disagree on *which gate structure* produces the redirects.
- **CONTRAST collapses under uniform strict def (EXP-0033, already on record):** the headline CC 66/66 vs Codex 0/142 difference is a definition+double-log artifact; under strict reactive + dedup both harnesses are PREEMPT-dominant (CC reactive 0.116, Codex 0.000). So a *cross-harness law about WHICH modality fires* is refuted; only the *within-harness error-class→modality association* survives, harness-specifically.

**Verdict on the cross-harness leg:** runnable → RUN → lands **MIXED/honest-partial**, not GREEN. It strengthens "error-class predicts modality" to 2 harnesses but simultaneously shows the mechanism is harness-specific, consistent with the FINALIZED negative-result disposition in academic_map.

---

## 4. TERMINAL-CLASS SAMPLING FIX (the third GREEN requirement)

**The gap:** in both EXP-0009 (CC) and the Codex corpus, **no class is cleanly TERMINAL** (recovery≈0 AND redirect≈0). EXP-0009's `fs.perm` was the only 0-recovery cell (n=1, uncallable). The trichotomy REDIRECTABLE / SAME-TOOL / TERMINAL is established on essentially two policy cells; the terminal pole is *censored*, not sampled.

**The fix (engineered into the protocol battery, not a re-analysis):** add a **TERMINAL stimulus arm** to the §2 task battery — a tool-block for which **no sanctioned twin exists in inventory AND the gate cannot be granted in-thread**:
- Concretely: a `secure_resource_fetch` shim that hard-blocks with an error that names NO alternative and explicitly states the resource is permanently unavailable (`Access permanently denied; no alternative resource exists.`), AND ensure inventory contains no same-intent twin for it. This is the structural analog of a true absorbing failure (revoked credential to a single-source resource).
- Run it as a 7th factor level `F_gate ∈ {REDIRECTABLE, GRANT_REQUIRED, TERMINAL}` crossed minimally (TERMINAL × {CC, OpenCode} at n≥30 each) so the terminal pole is sampled by construction, not left to corpus chance.
- **Pre-registered TERMINAL check:** the TERMINAL arm should show recovery≈0 AND redirect≈0 (Wilson upper < 0.15 on both). If agents nonetheless redirect (e.g. fabricate an alternative), that is itself a finding (the trichotomy is leaky).

**Why it can't be done as CPU re-analysis NOW:** no logged corpus contains a true terminal gate (every observed gate had an available modality). The terminal pole must be *injected*; it is part of the off-node battery, not the existing logs. This is the one piece that is irreducibly a new (CPU-only, if a controllable harness existed) data run.

---

## 5. TRIAGE — CPU-NOW vs new-CPU-run vs BLOCKED

| step | status | detail |
|---|---|---|
| Cross-harness V on a 2nd already-collected harness (Codex) | **DONE NOW (CPU)** | V=0.586, perm-p=0.0002 — ran on `~/.codex/sessions`. See §3. |
| Cross-harness V on a 3rd harness (Gemini) | **DONE on record (EXP-0031/0032/0033)** | Gemini n=9 blocks; taxonomy-consistent but tiny n; naming perfectly confounded with harness. |
| Uniform strict + double-log-dedup contrast | **DONE on record (EXP-0033)** | collapses the CC-vs-Codex contrast → PREEMPT-dominant both. |
| Reconcile v1/v2/PROTOCOL into one spec | **DONE NOW (CPU/writing)** | §1 — PROTOCOL is canonical. |
| Interventional do(error-class) de-aliasing factorial (C1–C6) | **BLOCKED (off-node)** | needs a controllable, model-agnostic, fully-logged harness (OpenCode/SWE-agent/OpenHands). On-node OpenCode logs 0/6 fields (PROTOCOL §7.3). Propose to orchestrator; do NOT dispatch. |
| Terminal-class sampled arm | **BLOCKED (needs new run, CPU-only if harness existed)** | no logged corpus has a true terminal gate; must be injected via the §4 TERMINAL shim. |

**Nothing further is CPU-extractable from existing logs** beyond what is now run/on-record: the de-aliasing and the terminal pole both require *injecting* a controlled stimulus, which requires the off-node logged harness.

---

## 6. SHARED CROSS-HARNESS INSTRUMENT — note for CLAIM-0010

CLAIM-0010 (two-layer reframe) is per `CLAIM-0010_final_determination.md` recommended **WIND-DOWN to a negative-result note** — both pillars dissolve (coarse layer = the 1-bit gate-type config-fact + the EXP-0033 measurement artifact cell; fine layer = a CC-policy-specific crumb over a ~0.6–0.74 residual-entropy floor). It has **no surviving standalone claim**.

- **Shared instrument:** the SAME OpenCode-pivot factorial + `url_fetch`/`web_search` shim + strict/deduped modality labeling (PROTOCOL §1–§4) is the instrument that would also serve CLAIM-0010. Specifically, the GLM (§5.5) decomposition is exactly the test of whether a "coarse layer" (gate-type) survives once harness/model/naming are conditioned — i.e. whether the two-layer structure is real or a config-bit + floor.
- **required_evidence CLAIM-0010 needs** (if it were to be revived rather than wound down): (a) the off-node cross-harness factorial showing the *coarse* gate→modality table holds across ≥2 harnesses **under the strict deduped definition** (not the lenient one that produced the artifact cell), AND (b) the *fine* context-conditioned lift (+12.6 pts in REDIRECTABLE) replicating outside the single CC `web_disabled` cell on a second harness. Per the final determination, (a) already went the wrong way (the carrying cell is a CC-specific policy hook + measurement artifact), so the honest path is wind-down, not revival. The instrument is shared with CLAIM-0009; if CLAIM-0009's interventional run ever executes, CLAIM-0010's coarse/fine questions are answered as a by-product of the same GLM — no separate run needed.

---

## 7. FILES
- this doc: `prior_art/PROJ-0003/CLAIM-0009_XHARNESS_r3_2026-06-01.md`
- canonical protocol: `prior_art/PROJ-0003/CLAIM-0009_interventional_PROTOCOL.md`
- executed cross-harness impl/output: `experiments/2026-06-01/EXP-XHARNESS-r3/impl/codex_cramersv.py`, `.../results/codex_cramersv_out.txt`
- anchors: EXP-0009 (CC V=0.717), EXP-0031/0032/0033 (Gemini + dedup correction), CLAIM-0010_final_determination.md
