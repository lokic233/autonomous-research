# EXP-0042 (L4 ROBUSTNESS) — CLAIM-0012 stats-robustness blockers (VERDICT-0046)

**Agent:** researcher-0012-robust · **Claim:** CLAIM-0012 · **Level:** 2 (CPU, stdlib-only)
**Reuses:** EXP-0041 `burst_L3.py` parsers + runs-test + tool-stratified permutation (imported as module).
**Estimand:** purely DESCRIPTIVE failure arrival-process; no error-class conditioning, no recovery prediction.
**Corpora (sessions ≥8 calls, this run):** CC 41 files / 19 shufflable, Codex 63 / 45, Gemini 11 / 10.

---

## (1) CC-LEG ROBUSTNESS — the load-bearing item. **VERDICT: CC tool-strat signal is FRAGILE / aggregation-carried.**

The committee flagged CC's per-session median tool-stratified-Z = 0 as structurally identical to the
EXP-0040 failure mode that was KILLED (a per-session-null result resurrected only by Stouffer aggregation).
The full distribution confirms the concern.

**Per-session tool-stratified-Z distribution (CC, 19 shufflable sessions):**
- median = **0.0**, mean = −0.535
- quantiles: p0=−6.40, p5=−3.77, p10=−2.28, p25=−0.14, **p50=0.00**, p75=+0.46, p90=+0.55, p95=+0.79
- histogram (edges −6,−4,−3,−2,−1,−.5,0,.5,1,2,4,6): counts `[0,1,0,2,0,1,12,2,0,0,0]`
- **12 of 19 sessions sit in the [−0.5, 0) bin = z_strat ≈ 0** (no within-tool clustering at all).
- Only **3 sessions are meaningfully negative** (z_strat ≤ −1.9): the 862-call session (−6.40), a 150-call (−3.48), and a 67-call (−1.88).
- fraction of sessions with z_strat < 0: **0.263**; fraction with per-session p<0.05: **0.105** (2 of 19).

**Size-weighted vs unweighted Stouffer:**
- Unweighted Stouffer = **−2.334** (p = 0.0098) — matches the EXP-0041 headline ~0.009.
- Size-weighted (w = √n_calls) Stouffer = **−6.585** (p = 2.3e-11) — LOOKS far stronger, **but this is an artifact**: the weight up-weights the single 862-call session (w=29.4) ~4–9× over every other session (w≈3–8). Weighting doesn't add evidence; it leans harder on the one outlier.

**Leave-one-SESSION-out (LOSO) sensitivity — the kill test:**
- Dropping the single 862-call session (`1c2df215…`, z_strat=−6.40):
  - unweighted Stouffer −2.334 → **−0.891 (p ≈ 0.19, NON-significant)**
  - weighted Stouffer −6.585 → **−2.402 (p ≈ 0.008)**
- The unweighted CC leg **collapses below significance on removal of one session.** Even the weighted leg loses ~64% of its Z. Dropping the 2 largest negative sessions drives unweighted to ~−1.6 (ns).

**Honest read:** CC's tool-stratified (rate-stratified) signal is **NOT robustly present at the session level** —
12/19 sessions show literally zero within-tool clustering, and the aggregate is carried by 1–3 large sessions.
This is the EXP-0040 pattern the project's own standard rejects. **The within-tool temporal-memory component
is real for CC only in a handful of long sessions; it does not generalize across the CC corpus.**

---

## (2) COX-only vs COX+HAWKES BIC — **Hawkes self-excitation EARNS its parameters on ALL 3 harnesses.**

Model on the failure-arrival process over call-index (each session its own time origin):
- **Cox-only** = per-tool baseline failure rate λ₀(tool) — i.e. pure rate-heterogeneity (the Cox-mixture
  alternative the committee flagged). k = #distinct tools.
- **Cox+Hawkes** = logit(λ₀(tool)) + α·Σ_{prior fails j} exp(−β·(t−j)); k = #tools + 2 (α self-excitation, β decay).
  α MLE'd by grid + local refine (stdlib; no numpy/scipy on host). ΔBIC = BIC(Cox) − BIC(Cox+Hawkes); >0 ⇒ memory earns its params.

| harness | n_calls | n_tools | Cox BIC | Hawkes BIC | α | β | **ΔBIC** | LR 2Δℓℓ |
|---|---|---|---|---|---|---|---|---|
| claude_code | 1317 | 15 | 750.10 | 740.35 | 1.25 | 0.45 | **+9.74** | 24.11 |
| codex | 1545 | 5 | 739.10 | 712.25 | 4.30 | 1.20 | **+26.85** | 41.54 |
| gemini | 159 | 7 | 199.02 | 185.26 | 3.55 | 1.15 | **+13.76** | 23.90 |

All three: ΔBIC > 6 (the conventional "strong" threshold) and α > 0 — **genuine temporal memory / self-excitation
beyond rate-heterogeneity, quantified.** This is the strongest positive result in this lane: even after granting the
Cox model a free per-tool rate for every tool, adding a 2-param Hawkes kernel improves fit enough to pay for itself
on every harness. Resolves the committee's "'both contribute' asserted not quantified" objection in favor of "both contribute."
(Caveat: CC's Hawkes win is the pooled-corpus fit; per §1 the CC clustering is concentrated in few sessions, so its
α=1.25 is the weakest of the three — consistent with §1.)

---

## (3) MULTIPLE-COMPARISON CORRECTION — family of 9 discriminating-ablation Stouffer tests.

(one-sided clustered Stouffer-p per harness × {whole-perm, tool-strat, retry-collapse@0.6}; m=9)

| test | p_raw | Bonferroni | survives? | Holm | survives? |
|---|---|---|---|---|---|
| codex:whole_perm / tool_strat / retry_06 | ~0 | ~0 | ✅ | ~0 | ✅ |
| gemini:whole_perm | 5.2e-5 | 4.7e-4 | ✅ | 1.6e-4 | ✅ |
| gemini:retry_collapse_06 | 5.9e-6 | 5.3e-5 | ✅ | 3.0e-5 | ✅ |
| gemini:tool_strat | 3.8e-4 | 3.5e-3 | ✅ | 7.7e-4 | ✅ |
| claude_code:whole_perm | 3.0e-6 | 2.7e-5 | ✅ | 1.8e-5 | ✅ |
| claude_code:retry_collapse_06 | 2.8e-5 | 2.6e-4 | ✅ | 1.1e-4 | ✅ |
| **claude_code:tool_strat** | **8.6e-3** | **0.078** | **❌ FAILS** | 8.6e-3 | ⚠️ "passes" |

- **CC tool-strat is the ONLY test that fails Bonferroni** (0.0086 → 0.078 > 0.05).
- It "survives" Holm at 0.0086 only **artifactually**: it is the largest p in the family (rank 9/9), so Holm's
  step-down multiplier has decayed to (m−i)=1 by the time it reaches CC — i.e. Holm gives it a free pass *because
  every other test was so strong*, not because CC's tool-strat is itself robust. This is a known Holm quirk for the
  weakest member; it should not be read as CC tool-strat being corrected-significant.
- **Codex (3/3) and Gemini (3/3) survive both corrections decisively.** CC's whole-session and retry-collapse
  ablations survive; only its **rate-stratified** (tool-strat) ablation does not.

---

## HONEST VERDICT

**CLAIM-0012 holds robustly at 2 harnesses (Codex + Gemini), NOT cleanly at 3.** The rate-stratified within-tool
temporal-memory component — the discriminating evidence that the over-dispersion isn't trivial rate-heterogeneity —

- **Codex:** decisive (per-session signal broad, ΔBIC +26.9, survives Bonferroni at ~0).
- **Gemini:** solid (ΔBIC +13.8, tool-strat survives Bonferroni at 3.5e-3).
- **Claude Code:** **fragile/aggregation-carried.** 12/19 sessions z_strat=0; unweighted Stouffer collapses to ns
  under LOSO (drop 1 session → p≈0.19); fails Bonferroni (0.078); the weighted Stouffer only looks strong because
  it over-weights the one 862-call session. This is the EXP-0040 failure mode by the project's own standard.

**What survives for CC:** the *whole-session* over-dispersion (Stouffer −4.07-class, survives Bonferroni) and the
retry-collapse ablation. What does NOT robustly survive for CC is the *rate-stratified* claim (within-tool memory
beyond tool-rate heterogeneity). And the Cox-vs-Hawkes BIC (a pooled fit) DOES favor Hawkes on CC (ΔBIC +9.7) — so
there is *some* CC self-excitation, but it lives in a few long sessions, not corpus-wide.

**Recommended reframe (descriptive, defensible):**
- Over-dispersion / burstiness of tool-call failures: **3-harness** (CC + Codex + Gemini), robust.
- Within-tool temporal-memory surviving rate-stratification: **2-harness strong (Codex + Gemini)**; CC weak —
  present in pooled Hawkes BIC and a few long sessions but NOT a robust per-session corpus-wide effect, and its
  tool-strat p does not survive Bonferroni.

---

## Files
- `impl/robust_L4.py` — analysis (CPU/stdlib, imports EXP-0041 burst_L3.py)
- `results/cc_per_session_strat.csv` — per-session whole/tool-strat Z + p for CC
- `results/cc_loso.csv` — LOSO unweighted & weighted Stouffer for every dropped session
- `results/cox_vs_hawkes.csv` — Cox vs Cox+Hawkes logL/BIC/α/β/ΔBIC per harness
- `results/multiple_comparison.csv` — Bonferroni + Holm over the 9-test family
- `results/robust_L4.json` — full bundle
- `logs/run.log` — run output
