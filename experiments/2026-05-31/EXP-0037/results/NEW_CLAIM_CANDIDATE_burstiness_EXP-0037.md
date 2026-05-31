# PROJ-0003 — FRESH-CLAIM CANDIDATE (for orchestrator to seed or kill)

**Agent:** researcher-0003-newseed · **Date:** 2026-05-31 · **CPU-only · document-only (no claim/verdict/map edits)**
**Probe:** EXP-0037 (level 1, --claim none per BUG-25, max 30min) · scripts in `experiments/2026-05-31/EXP-0037/`
**Recommendation:** **SEED (cautiously)** — genuinely-new descriptive angle, replicates across 2 harnesses, survives the lineage's own decisive-cell ablation. Thin-n caveats below.

---

## 1. THE FRESH ANGLE (distinct from the refuted prediction line)

The entire refuted PROJ-0003 lineage (CLAIM-0008/0009/0010/0011) asked a **conditional/predictive** question:
*does error-CLASS predict recovery (occurrence / modality)?* — all refuted or deflated to a 1-bit gate flag.

This candidate asks an **arrival-process / temporal-structure** question with **NO prediction claim and NO
error-class conditioning**:

> **CANDIDATE FINDING:** *Tool-call failures within a real agent session are temporally CLUSTERED
> (over-dispersed / bursty) — significantly more than a within-session Bernoulli/Poisson null — and this
> burstiness REPLICATES across harnesses and is NOT carried by the refuted `web_disabled` gate.*

This is a **descriptive measurement** of WHEN failures arrive in a trace, not WHICH error predicts WHAT
recovery. It is the angle the lineage never touched (chosen angle = (c) temporal structure / burstiness;
angles (a) failure-census and (b) recovery-cost were collision-killed, see §3).

---

## 2. PROBE RESULT (EXP-0037, runs-test on real on-node traces)

**Metric:** per-session Wald–Wolfowitz runs test on the ordered failure-indicator sequence (1=tool_result
error / nonzero exit, 0=success). Negative Z ⇒ fewer runs than a Bernoulli null with the same p ⇒ failures
are **clustered** (bursty). Sessions combined via Stouffer's Z. Codex deduped by `call_id` to neutralize the
EXP-0033 double-log artifact (M5).

| Harness | usable sessions | total tool-results | fail rate | mean per-session Z | Stouffer combined Z | sessions Z<0 |
|---|---|---|---|---|---|---|
| Claude Code | 17 | 1,661 | 0.069 | −0.99 | **−4.07** (p≈2e-5) | 12/17 (71%) |
| Codex (deduped) | 43 | 1,871 | 0.053 | −2.30 | **−15.07** | 33/43 (77%) |

**Decisive-cell ablation (M4):** reclassifying all `web_disabled` failures as non-failures on Claude Code
*strengthens* the signal (Stouffer −4.07 → −4.63). So burstiness is **NOT** a `web_disabled` artifact — the
exact failure mode of the refuted lineage. CC failure mix: other 72 / permission 41 / file_notfound 17 /
web_disabled 7 / timeout 1. The clustering is driven by ordinary permission/file/exec failures.

**Interpretation:** failures beget failures within a window — consistent with cascade / context-poisoning /
stuck-loop dynamics — a real over-dispersion in the failure arrival process. This is a benchmark-style
*characterization* of agent-trace failure dynamics, presentable with Wilson/permutation CIs.

---

## 3. COLLISION CHECK (the reason to trust this is NEW)

### vs the refuted PROJ-0003 lineage — CLEAR
- The lineage is entirely **error-class → recovery** (a conditional law). This is the **temporal arrival
  process** of failures (a marginal/structural fact). No overlap in target estimand.
- Grep of `prior_art/PROJ-0003/` + `registry/academic_map.yaml` for burst/temporal/cluster/inter-arrival/
  overdispersion = **zero hits**. The lineage never measured arrival structure.
- Survives the lineage's own M4 (web_disabled ablation) — does not reduce to the refuted cell.

### vs MAP-0002 occupied_territory / red_zones — CLEAR
- occupied = failure taxonomies, post-hoc summaries, LangGraph time-travel, MAST/AgentBench buckets, and the
  redirectable/terminal gate split. Burstiness is **none of these** (it's an arrival statistic, not a taxonomy
  or a recovery-modality claim).
- red_zone = "harness-routing-as-confound" — **does not apply**: this claim makes no routing/modality
  assertion; it's a within-session marginal. (And it replicates across harnesses, so it isn't a single-harness
  routing artifact.)

### vs known benchmarks — CLEAR (with one neighbor to cite, not a collision)
- **MAST/Cemri 2503.13657, AgentBench, τ-bench/ToolEmu:** static failure *taxonomies* / pass-rate buckets —
  none measure the temporal *clustering* of failures within a trajectory. Orthogonal.
- **Closest neighbors (CITE + DISTINGUISH, not collide):**
  - *The Long-Horizon Task Mirage* (2604.11978) & *Canonical Path Deviation* (2602.19008): study failure
    **POSITION** in curated **benchmark** task trajectories (where in the canonical solution path it breaks).
    This candidate measures the **arrival-process over-dispersion** of *tool-call-level* failures in **real
    production multi-harness** sessions — a statistical clustering claim, not a position-in-task claim, on
    real traces not benchmark runs.
  - *Dissecting Failure Dynamics in LLM Reasoning* (2604.14528): "errors originate from a small number" — but
    that's intra-CoT **reasoning** errors, not tool-call failures across deployed agent harnesses.
- **Verdict:** genuinely-open. Nobody has reported the failure **burstiness coefficient** of real agent
  tool-call traces as a cross-harness benchmark statistic.

---

## 4. SEED-OR-KILL RECOMMENDATION → **SEED (cautiously)**

**Why seed:** (1) genuinely-new estimand the refuted lineage never tested; (2) collision-clear vs MAP-0002 +
MAST/AgentBench/τ-bench + the refuted claims; (3) measurable on existing CPU corpora; (4) replicates 2/2
harnesses (CC −4.07, Codex −15.07); (5) survives M4 web_disabled ablation — NOT the refuted cell; (6) a
descriptive benchmark-style contribution (NeurIPS D&B genre, same venue as the synthesis paper) that could be
a *second* descriptive finding alongside the gate taxonomy.

**Honest caveats the orchestrator must weigh before promoting past level 1:**
- Thin CC n (17 usable sessions; per-session mean Z only −0.99, median −0.41 — the CC signal is carried by
  the Stouffer aggregation, not strong per-session). Codex is the stronger leg.
- Dispersion-index at window=5 was ~1.0 (Poisson) on CC — the runs test (order-sensitive) sees clustering the
  coarse window does not; need to confirm with finer windows + a permutation null per session.
- Failure-labeling is heuristic (is_error flag for CC; "exited with code N" regex for Codex). A clean,
  uniform cross-harness failure definition (M3 discipline) is required before this is publishable.
- Gemini (3rd harness) NOT yet run — the domain's standing bar is 3-harness replication. Quick to add.
- Mechanism is unclaimed (cascade vs context-poisoning vs retry-storm). The claim should stay **purely
  descriptive** ("failures are over-dispersed") and NOT drift into a causal/predictive law — or it risks
  re-entering the refuted prediction territory.

**Proposed claim text for the orchestrator to seed (if it survives a level-2 with Gemini + permutation null):**
> *"In real multi-harness agent traces, tool-call failures are temporally over-dispersed (bursty) within a
> session relative to a Bernoulli null; the burstiness replicates across Claude Code and Codex and is not an
> artifact of the redirectable web_disabled gate."* — a DESCRIPTIVE benchmark statistic, no prediction.

**Suggested next probe (level 2, still CPU, ~30min):** add Gemini; replace runs-test-only with a per-session
permutation null (shuffle the failure indicators, recompute run-count, exact p) + report a burstiness
coefficient (B = (σ_τ − μ_τ)/(σ_τ + μ_τ) on inter-failure gaps) with bootstrap CIs; uniform cross-harness
failure definition.

---

## 5. FILE / ARTIFACT PATHS
- This doc: `prior_art/PROJ-0003/NEW_CLAIM_CANDIDATE_burstiness_EXP-0037.md`
- Probe scripts: `experiments/2026-05-31/EXP-0037/{burst_probe.py,burst_probe2.py,burst_codex.py}`
- Experiment registration: EXP-0037 (level 1, --claim none, CPU-only, max 30min)
