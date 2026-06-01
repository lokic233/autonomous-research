# EXP-0057 — Analysis & Disposition (PROJ-0011 / CLAIM-0022)

**Agent:** researcher-0022-L0-r7 | **Sub-monitor:** sub-monitor-0011-r7 | **LOCKED-TS:** `2026-06-01T20:46:46Z`
**Run:** `logs/run_main.log` | **Numbers:** `results/summary.json` | **Pre-reg:** `impl/PRE_REGISTRATION.md` (committed BEFORE run, HEAD 05a37db)
**Corpora:** CC (primary) 69 sessions / 3213 reuse units; Codex (RE-A4) 86 sessions / 2042 reuse units. Runtime ~68 s, CPU stdlib.

## HEADLINE (one-liner)
On the live CC agent corpus, agent file-path KV reuse distance **IS bimodal** (RE-A0 PASS: 18.9% far >8192 tok, p99 ≈ 86k
tok, max ≈ 892k) — but **which** cached file gets re-touched at a FAR distance is **NOT predictable by a cheap causal
working-set feature beyond a recency+frequency+tool+file-class joint baseline** (dAUC=+0.017, 95% LB −0.003, < 0.03 floor,
NOT all folds positive), the residual lift **vanishes within matched-recency strata** (0/10 deciles separate), it does
**not beat a Marconi-style reuse forecast** (dAUC_fc=+0.015, LB −0.021), and a B1-predictor eviction policy **underperforms
plain LRU at every cache capacity** (only a true Belady oracle saves ≤13% recompute). HHI=0.42 flags the residual as
dominated by 2–3 sessions. → **CLEAN NEGATIVE-KILL.**

## PER-GATE DISPOSITION (CC = primary corpus)

| Gate | Result | Disposition |
|---|---|---|
| **RE-A0** bimodality floor | share_FAR=0.189 (≥0.15 ✓), share_NEAR=0.468 (≥0.10 ✓); median 666 tok, p99 86k, max 892k | **PASS** — distribution IS bimodal; the characterization premise holds. |
| **RE-A1** LOAD-BEARING killer | AUC B0=0.664, B1=0.681, **dAUC=+0.0171**, **LB95=−0.0027**, folds=[−0.005,+0.020,+0.022,+0.003,+0.020] **not all positive**, std=0.011 | **FAIL → CLEAN NEGATIVE.** Below 0.03 floor, LB95 crosses 0, one negative fold. |
| **STAT DISCIPLINE** | **HHI=0.422 > 0.20 → FLAGGED**; effective-n ≪ 3213 (dominated by a few Bash-heavy sessions) | Residual lift down-weighted; even the +0.017 is not session-robust. |
| **RE-A2(a)** matched-recency | **0/10 deciles** have working-set-only AUC LB95 > 0.5 (need ≥6) | **FAIL** — the small B1 lift is **recency-in-disguise**; within fixed recency, working-set features do not separate far-reuse. |
| **RE-A2(b)** beat forecast | B0+forecast AUC=0.666 ≈ B1=0.681; **dAUC_fc=+0.015, LB95=−0.021** | **FAIL** — does not beat the Marconi-style reuse-distance forecast. |
| **RE-A3** capacity curve | **B1-predictor eviction saves NEGATIVE recompute vs LRU at ALL 7 capacities** (−0.8% to −34.9%); Belady oracle saves +0.6%→+13.3%; Gini(recompute mass)≈0.65–0.68 (heavy-tailed) | The cheap predictor **actively hurts**; only a true oracle realizes the (modest) reuse-distance gap. Corroborates the kill. |
| **RE-A4** cross-instrument | cc_dAUC=+0.017, codex_dAUC=+0.038, **sign_agree=True, both_positive=True** | Sign HARD-gate technically met, but **moot** — CC RE-A1 fails magnitude/robustness, so the claim is killed on the primary corpus regardless (see note). |

## HONEST NOTES / CEILINGS
- **Codex is NOT bimodal** (RE-A0 FAIL: share_FAR=0.036, share_NEAR=0.799, median gap 0 — near-reuse-dominated, short
  sessions). Codex *does* show a small RE-A1 pass (dAUC=+0.038, LB95=+0.017, all folds+, clean HHI=0.015) on only **73 far
  positives**, but on a corpus where the far-reuse characterization premise does not even hold. The cross-instrument sign
  agreement is therefore a weak, direction-only concordance, not evidence of a robust capturable signal. We do **not**
  upgrade on it.
- **Real-but-modest reuse-distance gap exists** (Belady saves ≤13% recompute over LRU on CC) — so LRU *is* suboptimal, as
  the literature argues (KVFlow/ScaleSim/Marconi). The novel question here was whether a **cheap causal feature** captures
  it. Answer: **no** — it requires near-oracle (future) knowledge; the cheap B1 predictor underperforms LRU.
- Path-identity ceiling (relative Bash path vs absolute file-tool path counted distinct) is CONSERVATIVE — it only reduces
  measured reuse, cannot inflate any gate. CC reuse units are 93% Bash-extracted paths (per-tool table).
- Frozen thresholds were honored verbatim; no threshold was moved. The forecast feature is a faithful-but-simplified
  stdlib proxy for Marconi's reuse-likelihood forecast (per-path running reuse-distance estimate), documented in pre-reg.

## COMMITTEE-FACING RECOMMENDATION
1. **Contribution (a) — CHARACTERIZATION stands and is publishable:** agent file-path KV working sets have a genuinely
   **bimodal reuse-distance distribution** on the live CC corpus (18.9% far >8192 tok, p99 ≈ 86k, heavy-tailed recompute
   mass Gini ≈0.66), and LRU is provably suboptimal vs a Belady oracle (≤13% recompute gap). This is the load-bearing,
   honest characterization the project was reframed to deliver.
2. **Contribution (b) — FALSIFICATION returns a CLEAN NEGATIVE:** a cheap causal working-set feature does **NOT** predict
   far-reuse beyond {LRU recency + LFU + tool + file-class} and does **not** beat a Marconi-style reuse forecast; the
   residual lift is recency-in-disguise (0/10 matched-recency deciles) and is dominated by 2–3 sessions (HHI=0.42); a
   predictor-driven eviction policy underperforms LRU at every capacity.
3. **Actionable verdict: existing reuse-aware policies (RadixAttention/vLLM-APC LRU+LFU, and a Marconi-style reuse-
   likelihood forecast) are SUFFICIENT for agent file-prefix eviction. Do NOT build a new cheap causal reuse-aware
   eviction feature** — the modest oracle-realizable gap is not capturable from cheap history-only features. Closing the
   gap would require near-oracle future-step knowledge (the direction KVFlow's agent-step-graph / ScaleSim's invocation-
   distance pursue with *explicit* execution-plan signals, not cheap statistical features).

**DISPOSITION: CLEAN-NEGATIVE-KILL (RE-A1) — first-class publishable negative.** Characterization (bimodality + oracle
gap) confirmed; cheap-causal-predictability falsified.
