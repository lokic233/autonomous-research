# EXP-0038 (L2) — CLAIM-0012 burstiness: 3-harness + permutation null + B[CI]

**Agent:** researcher-0012-burst-L2 · **Date:** 2026-05-31 · **CPU/stdlib-only · max 30min**
**Claim:** CLAIM-0012 (PURELY DESCRIPTIVE): tool-call failures are temporally OVER-DISPERSED within a
session vs a within-session Bernoulli null; replicates across harnesses; NOT a web_disabled artifact.
**Extends:** EXP-0037 (L1). Reuses burst_probe.py (CC) + burst_codex.py (Codex dedup-by-call_id) +
EXP-0031 gemini parser (toolCalls[].status success/error).
**Impl:** `experiments/2026-05-31/EXP-0038/impl/burst_L2.py` · **CSV:** `results/{harness_summary,per_session}.csv`

---

## VERDICT: **SUPPORT** (with one honest qualifier on the burstiness-coefficient leg)

The over-dispersion **replicates to a 3rd harness (Gemini)** and **survives a non-parametric per-session
permutation null in all 3 harnesses**. The M4 web_disabled ablation holds (CC strengthens, others
unchanged). The order-sensitive arrival-structure signal (runs / permutation) is robust. The *gap-CV
burstiness coefficient B* is clean for Codex, marginal-positive for CC, and CI-crosses-0 for Gemini
(thin gap counts) — so B as a point statistic is well-supported for Codex and directionally positive
(corrected) for all three, but its CI is only strictly >0 for Codex (and CC's lower bound ~0).

---

## 1. GEMINI 3rd HARNESS — REPLICATES ✅

Parsed `~/.gemini/tmp/*/chats/session-*.json`, `messages[].toolCalls[].status ∈ {success,error}`.

| stat | value |
|---|---|
| usable sessions (≥8 tool-results, both ok+err) | **10** |
| total tool-results / failures / fail-rate | 172 / 52 / 0.302 |
| **Stouffer analytic Z** | **−3.84** |
| **Stouffer permutation Z** | **−3.90** |
| per-session Z<0 fraction (analytic / perm) | 0.80 / **0.90** |
| dispersion index (var/mean, w=5) | 1.94 (overdispersed) |

3-harness replication = the D&B bar is met (CC −4.07, Codex −15.07, **Gemini −3.84**, all same sign).

## 2. PER-SESSION PERMUTATION NULL — HOLDS ✅ (CC leg does NOT collapse)

Per session: shuffle the 0/1 failure-indicator sequence N=2000×, recompute #runs; clustered = fewer runs.
Per-session permutation-Z (vs permuted moments) combined via Stouffer; per-session p-values via add-one
exact, combined via Fisher (Wilson-Hilferty z).

| harness | Stouffer **perm** Z | (analytic Z) | Fisher z | frac sessions perm p<.05 |
|---|---|---|---|---|
| Claude Code | **−4.07** | −4.07 | +1.97 | 0.18 |
| Codex (deduped) | **−15.14** | −15.07 | +7.70 | 0.35 |
| Gemini | **−3.90** | −3.84 | +2.99 | 0.20 |

The permutation Stouffer is **near-identical to the analytic Wald-Wolfowitz Z in all 3 harnesses** → the
L1 analytic null was NOT fragile to the small-n / heuristic-label concerns. The thin CC leg (median
per-session Z only −0.41, carried by aggregation) survives the non-parametric null intact (−4.07).

## 3. BURSTINESS COEFFICIENT B [bootstrap 95% CI] — Codex clean, CC/Gemini noisier

Goh-Barabási B=(σ−μ)/(σ+μ) on **pooled inter-failure gaps**; bootstrap = resample sessions (N=2000).
Raw B is finite-size biased toward −1 for short series → also report Kim&Jo(2016) corrected B_c.
**B>0 / dispersion>1 = bursty.**

| harness | gaps | B (raw) [CI] | **B_corrected [CI]** | dispersion idx |
|---|---|---|---|---|
| Claude Code | 98 | 0.356 [−0.012, 0.384] | **0.417 [0.001, 0.453]** | 1.63 |
| Codex | 56 | 0.218 [0.053, 0.314] | **0.270 [0.072, 0.395]** | 1.41 |
| Gemini | 42 | 0.164 [−0.388, 0.244] | **0.213 [−0.419, 0.319]** | 1.94 |

- **Codex:** B>0 with CI strictly above 0 — unambiguously bursty.
- **CC:** point B>0, corrected-B CI lower bound ≈ 0 (just positive) — directional, thin.
- **Gemini:** point B>0 but CI crosses 0 (only 42 gaps / 10 sessions) — **inconclusive on B alone.**
- **Dispersion index >1 for all three** (1.41–1.94), agreeing with bursty direction.
- HONEST DIAGNOSTIC: *per-session* B is NEGATIVE for all harnesses (−0.19/−0.50/−0.49) — this is the
  known Goh-Barabási finite-size bias with only 3–8 failures/session, NOT real anti-bursting. Hence the
  runs/permutation test (order-based, unbiased) and the **pooled corrected B** are the trustworthy
  burstiness statistics; per-session raw B is uninformative here and is reported only as a caveat.

## 4. M4 web_disabled ABLATION (reclassify web_disabled→non-failure) — HOLDS ✅ across all 3 + permutation

| harness | Stouffer perm Z (base → M4) | corrected B (base → M4) |
|---|---|---|
| Claude Code | −4.07 → **−4.93** (STRENGTHENS) | 0.417 → 0.408 |
| Codex | −15.14 → −14.84 (≈unchanged) | 0.270 → 0.266 |
| Gemini | −3.90 → −3.87 (no web tool; unchanged) | 0.213 → 0.213 |

Reclassifying web_disabled as non-failure on CC **strengthens** the clustering signal under the
permutation null (−4.07→−4.93) — burstiness is driven by ordinary perm/fs/exec failures, NOT the refuted
redirectable web_disabled cell. Confirmed under permutation + all 3 harnesses. (Gemini has no web tool, so
the ablation is trivially a no-op there — consistent with "not a web_disabled artifact".)

---

## HONEST CRUX RESOLUTION

Does the burstiness replicate across all 3 harnesses with a proper permutation null + CI-bounded B?
- **Arrival-structure over-dispersion (runs / permutation null): YES, robustly, all 3 harnesses**, CC leg
  intact under non-parametric null. This is the core of CLAIM-0012 and it is **supported**.
- **CI-bounded burstiness coefficient B: PARTIAL** — strictly CI>0 only for Codex; CC corrected-B CI
  barely positive; Gemini B CI crosses 0 (too few gaps). Point estimates + dispersion index all bursty.
- **Net:** a solid DESCRIPTIVE 3-harness over-dispersion claim. The honest weakening is that the *single
  scalar B coefficient* is only CI-clean on the strong (Codex) leg; the claim should lead with the
  permutation/runs over-dispersion result + dispersion index, and report B with the per-harness CIs and
  the finite-size caveat rather than asserting B>0 uniformly. Gemini's B is the thinnest leg.

## CAVEATS (carried forward)
- Heuristic failure labels (CC is_error; Codex "exited with code N"/error-text; Gemini status==error).
- Gemini n is small (10 usable sessions, 42 gaps); replicates on the order-test but B-CI is inconclusive.
- Stays PURELY descriptive: arrival-process only, no error-class conditioning, no recovery prediction.
- Mechanism unclaimed (cascade vs context-poisoning vs retry-storm).

## FILES
- impl/burst_L2.py · results/harness_summary.csv · results/per_session.csv · logs/run2.log
