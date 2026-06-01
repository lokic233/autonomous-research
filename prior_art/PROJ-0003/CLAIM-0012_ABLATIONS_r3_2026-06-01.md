# CLAIM-0012 — VERDICT-0047 BLOCKING ABLATIONS SYNTHESIS

**Date:** 2026-06-01 (UTC) · **Agent:** researcher-0012-ablations2-r3 · **CPU/stdlib-only, READ + local-Python on cli:dengcchi-mac**
**Mandate:** clear VERDICT-0047's 3 BLOCKING ablations for CLAIM-0012 H2 (discriminating self-excitation BEYOND static rate-heterogeneity).
**Scope:** re-analyzed EXISTING logged traces (`~/.codex/sessions`, `~/.claude/projects`, `~/.gemini`). No GPU, no new collection, no map/verdict edits, no fabrication, did NOT call `ros exp complete`.
**Artifacts:** `experiments/2026-06-01/EXP-0044/impl/{ablations.py, ablations_gate.py}`, `results/{codex_loso.csv, latent_cox_vs_hawkes.csv, gate_stripped_hawkes.csv, ablations_b1_b2.json, gate_stripped.json}`, `logs/{run_b1b2.log, run_b3.log}`.
**Machinery reuse:** EXP-0041 `burst_L3.py` parsers + tool-stratified permutation; EXP-0042 `robust_L4.py` Cox/Hawkes fitter (imported, not rebuilt).

---

## TL;DR HONEST VERDICT: **YELLOW → committee-GREEN-READY for the NARROWED claim** (3-harness-descriptive H1 + **Codex-clean** H2). All 3 BLOCKING ablations resolve in H2's favor *on Codex*. The ablations also **sharpen the honest scope**: they FALSIFY the Gemini discriminating leg (mechanical gate artifact) and leave CC's weak leg as a side-result (survives gate-stripping but stays LOSO/Bonferroni-fragile per EXP-0042). The defensible green claim is **1 strong harness (Codex), not 3.**

| BLOCKING test | Codex | CC | Gemini | H2 effect |
|---|---|---|---|---|
| **B1 Codex LOSO** | **PASS** (n/a) | (n/a) | (n/a) | H2 NOT a single-session artifact on the sole strong harness |
| **B2 latent-state Cox** | **PASS** (ΔBIC +15.0 vs steelman) | marginal (+8.9) | **FAIL** (−0.45, absorbed) | Codex memory survives steelman; Gemini "memory" = time-varying heterogeneity |
| **B3 gate-stripped Hawkes** | (Codex genuine-exec already, not gate-driven) | survives (α stable, gates not the driver) | **FALSIFIED** (α→0, ΔBIC→−9.4) | Gemini self-excitation is mechanical gate clustering |

**Net: H2 SURVIVES on Codex against all three steelman attacks. H2 is killed on Gemini and remains fragile-but-not-gate-driven on CC.** This is exactly the narrowed "1 clean harness" position the prior GREEN-path synthesis recommended — now defended against the committee's specific BLOCKING objections.

---

## CORPUS (recounted; grown slightly since prior synthesis)
Codex sessions ≥8 calls: **64** (46 mixed-label, usable for permutation/Hawkes); **2001** total calls, **106** failures, **60** inter-failure gaps. (Prior synthesis cited ~45 sess / 1545 calls / 59 gaps — corpus grew; results strengthened, not weakened.) Full-corpus Codex Hawkes reproduces the prior result: **ΔBIC = +28.32, α = 4.45, β = 1.25** (prior: +26.85, α=4.30).

---

## BLOCKING-1 — CODEX LOSO  ✅ **PASS** (the most critical test; never run on Codex before)

The single-session ablation that destroyed CC (Stouffer −2.33 → −0.89, p~0.19 in EXP-0042) was run on **every one of the 46 mixed-label Codex sessions in turn**. For each removal I recomputed (a) Hawkes ΔBIC, (b) tool-stratified-permutation Stouffer Z + p, (c) whole-session-permutation Stouffer Z. Full distribution in `results/codex_loso.csv`.

- **Hawkes ΔBIC across all 46 single-session removals: range [17.60, 30.67], median 27.79.** Every removal stays **far above the BIC>6 "strong" threshold.** The worst case (ΔBIC=17.60) is dropping `rollout-2026-05-30T05-22-43…` (19 calls, **6 failures**, the most failure-dense session, per-session z_strat = −3.92). Even removing the single most influential session leaves ΔBIC ≈ 17.6 — **~3× the threshold.**
- **Tool-stratified-permutation Stouffer p = 0.000 for ALL 46 removals** (min Z still ≈ −13.4; full-corpus −14.04). Whole-perm Stouffer p = 0.000 for all 46.
- **PASS criteria (both required): ΔBIC>6 for all removals = TRUE; tool-strat significant for all removals = TRUE → BLOCKING-1 PASS.**

**Read:** Codex H2 is **not a single-session artifact.** This is the asymmetry the committee correctly flagged (the test that killed CC was never run on Codex); run now, Codex survives it decisively — in stark contrast to CC, which collapsed under the identical test in EXP-0042.

---

## BLOCKING-2 — TIME-VARYING / LATENT-STATE COX (steelman static-heterogeneity null; arXiv 2604.15084)  ✅ **PASS on Codex** (FAIL on Gemini, marginal on CC)

The prior Cox was per-TOOL-rate only — NOT the steelman where a slow latent "hard-subtask" phase elevates ALL tool rates without any per-event memory. I added two such static/slow-varying-heterogeneity nulls (each a multiplier on the per-tool baseline, **no self-excitation**) and recomputed ΔBIC vs Hawkes (`results/latent_cox_vs_hawkes.csv`):
- **(b) phase-Cox:** early/mid/late tertile additive logit offset per session, fit by coordinate ascent.
- **(c) HMM-Cox:** 2-state (easy/hard) latent difficulty, sticky transition matrix, fit by EM forward-backward. The latent state modulates the whole-session rate — the literal "hard phase elevates all tools" steelman.

ΔBIC = BIC(best static-heterogeneity model) − BIC(Hawkes). >6 ⇒ Hawkes memory still earns its params over the steelman.

| harness | plain-Cox BIC | phase-Cox BIC | HMM-Cox BIC | Hawkes BIC | best static | **ΔBIC (best static − Hawkes)** | survives steelman? |
|---|---|---|---|---|---|---|---|
| **codex** | 753.20 | **739.88** | 1142.26 | **724.88** | phase-Cox | **+15.0** | **YES** |
| claude_code | 753.89 | 769.29 | 1055.10 | 744.98 | plain-Cox | +8.91 | marginal-yes |
| gemini | 199.02 | 197.46 | **184.81** | 185.26 | HMM-Cox | **−0.45** | **NO (absorbed)** |

- **Codex: PASS.** The phase-stratified Cox *does* improve over plain Cox (753.2 → 739.9 — there IS some time-varying heterogeneity), but Hawkes self-excitation (724.9) still beats the best static model by **ΔBIC = +15.0**. Genuine per-event memory remains after the steelman absorbs the slow-varying component.
- **Gemini: FAIL.** The HMM latent-difficulty model (184.81) *matches/beats* Hawkes (185.26), ΔBIC = −0.45. Gemini's apparent self-excitation IS fully explained by time-varying/latent heterogeneity — consistent with B3 below.
- **CC: marginal** (+8.91 over plain Cox; phase/HMM don't help CC). CC clears 6 but weakly, and per EXP-0042 CC fails the LOSO/Bonferroni discriminating bar anyway.
- **Caveat (disclosed):** the HMM-Cox EM is heavily penalized by BIC param count and on Codex its `gamma` collapsed to a degenerate −13.8 (an EM local optimum on a sparse 106-failure signal); the BINDING steelman for Codex is therefore phase-Cox, not HMM. The Codex ΔBIC=+15.0 conclusion does not depend on the HMM fit. For Gemini the HMM is well-behaved (gamma [−2.36, +0.58]) and is the one that absorbs Hawkes.

---

## BLOCKING-3 — GATE-STRIPPED HAWKES REFIT (CC + Gemini)  → **Gemini FALSIFIED, CC SURVIVES**

Re-classified each CC/Gemini failure as deterministic-gate vs genuine-exec using classifiers matched to the **actual on-node error strings** (I inspected raw snippets and CORRECTED an initial mis-classifier — see Methods note), then refit Hawkes on the genuine-exec residual (`results/gate_stripped_hawkes.csv`). Two strip modes: gate→is_err=0 (keep call) and drop-call.

**Failure-category breakdown (this corpus snapshot):**
- **Gemini (52 fails): schema_argerror 26 + path_gate 16 + file_notfound 9 = 51/52 (98%) deterministic gates; only 1 genuine exec failure.** (Confirms the prior synthesis's ~98%-trivial figure.)
- **CC (127 fails): genuine_exec 73 + permission_gate 34 + file_notfound 15 + web_gate 5.** NOTE: this CC snapshot is **genuine-exec-heavy** (real `Exit code N`: ping/ssh/http/file-not-found), with FEWER true permission gates than the prior synthesis's 33% — corpus drifted toward genuine failures.

| harness | config | α | ΔBIC | verdict |
|---|---|---|---|---|
| gemini | baseline | 3.55 | +13.76 | — |
| gemini | strip path+schema gates (→ok) | **0.0** | **−9.36** | **self-excitation COLLAPSES** |
| gemini | strip path+schema gates (drop) | **0.0** | **−8.89** | **mechanical artifact confirmed** |
| claude_code | baseline | 1.50 | +8.91 | — |
| claude_code | strip permission_gate (→ok) | 1.65 | +9.54 | survives (α stable) |
| claude_code | strip permission_gate (drop) | 1.50 | +8.24 | survives |
| claude_code | strip all gates (→ok) | 1.20 | +8.11 | survives |

- **Gemini: FALSIFIED.** Removing the deterministic path/schema gates collapses α to **exactly 0.0** and flips ΔBIC negative (−9.36 / −8.89). After stripping, only ~8–10 failures remain across the corpus — Gemini's entire "self-exciting cascade" was the agent repeatedly emitting malformed/out-of-workspace tool calls that cluster by construction. **Mechanical, not stochastic.**
- **CC: SURVIVES gate-stripping.** α is essentially invariant (1.5 → 1.2–1.65) and ΔBIC stays ~8–10 across all strip modes. CC's (weak) self-excitation is **NOT a permission-gate artifact** — the gates were not driving it. CC's fragility is the LOSO-collapse / Bonferroni-failure already documented in EXP-0042, a different (aggregation) problem, not a mechanical-gate one.

---

## METHODS NOTE (honesty / reproducibility)
- **Classifier correction:** my first B3 run used loose substring patterns that (i) dumped real Gemini `"params must have required property"` / `"Path not in workspace"` errors into `genuine_exec`, and (ii) false-matched the generic word "permission" on CC SSH `"connection is not …"` warnings. I inspected raw on-node snippets, rewrote both classifiers to the literal observed strings, and re-ran. The corrected Gemini breakdown (98% gate) reproduces the EXP-0043 label audit; the corrected CC breakdown reflects this snapshot's genuine-exec-heavy composition. Both classifiers are in `ablations_gate.py` with the matched strings documented inline.
- **Environment:** node has NO numpy/scipy; all stats are stdlib-only (matching the prior EXP-0041/0042 design). `/usr/local/bin/python3` runs the ablations; `/usr/bin/python3` runs the ros engine (it has pyyaml). No file-transfer/base64 used — scripts written via heredoc directly on-node.
- **Permutations:** NPERM=2500, seeds fixed (20260601 / 20260531). Hawkes via grid+local-refine (no external optimizer), identical to EXP-0042.

---

## DETERMINATION

**H1 (3-harness temporal over-dispersion, within-session permutation null, survives Bonferroni):** unchanged — GREEN-grade descriptive, as all 6 reviewers already granted.

**H2 (discriminating self-excitation beyond static rate-heterogeneity):**
- **Codex: GREEN-grade, now defended against all 3 BLOCKING attacks.** LOSO-robust (ΔBIC≥17.6 for every single-session removal), beats the steelman time-varying/latent-state Cox (+15.0), genuine-exec failure semantics (not gate-driven). This is the committee's "sole strong harness" and it survives the exact tests that were missing.
- **Gemini: KILLED as a discriminating leg.** Both B2 (latent-Cox absorbs it) and B3 (gate-strip collapses α→0) independently show its self-excitation is a deterministic malformed-call / path-gate artifact, not stochastic memory. Should be reported as a trivial-population negative, not a supporting harness.
- **CC: remains fragile but NOT for the gate reason.** B3 shows CC's weak self-excitation is not gate-driven (α stable under stripping); its weakness is the EXP-0042 LOSO-collapse + Bonferroni-failure (aggregation-carried). Report as caveated/weak, not as a clean second harness.

**COMMITTEE-READINESS: The narrowed claim is GREEN-READY.** Frame H2 as **one clean harness (Codex)**: *"On Codex — the harness with genuine heterogeneous exec-failure semantics — tool-call-failure over-dispersion exceeds static AND time-varying/latent-state per-tool rate-heterogeneity (tool-stratified permutation + Cox-vs-Hawkes ΔBIC=+28; leave-one-session-out ΔBIC≥17.6 for all 46 sessions; survives a phase/HMM-modulated steelman static-heterogeneity null at ΔBIC=+15), placing it in the self-exciting/cascade region rather than the memoryless heavy-tailed regime. The self-excitation is absent once deterministic gate-failures are removed on Gemini (α→0) and aggregation-fragile on Claude Code — so the discriminating result is reported as one strong harness, not a uniform law."* This does NOT force a 3-harness GREEN; it concedes Gemini (killed) and CC (fragile) honestly while the Codex core is now defended against every BLOCKING objection in VERDICT-0047.

## FILES
- `prior_art/PROJ-0003/CLAIM-0012_ABLATIONS_r3_2026-06-01.md` (this doc)
- `experiments/2026-06-01/EXP-0044/impl/{ablations.py, ablations_gate.py}`
- `experiments/2026-06-01/EXP-0044/results/{codex_loso.csv, latent_cox_vs_hawkes.csv, gate_stripped_hawkes.csv, ablations_b1_b2.json, gate_stripped.json}`
- `experiments/2026-06-01/EXP-0044/logs/{run_b1b2.log, run_b3.log}`
