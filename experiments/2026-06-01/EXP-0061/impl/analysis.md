# EXP-0061 — Analysis: Agent Serving Prefill Token-Mass Decomposition
**PROJ-0015 / CLAIM-0026 / VERDICT-0071** · researcher-0026-L0-r8 · Level-0 (Mac CPU, stdlib)
**Pre-reg LOCK-TS** 2026-06-01T23:44:20Z (commit 8e60c29, BEFORE measurement). **Type:** CHARACTERIZATION (no predictor, no dAUC).
**Disposition:** **GREEN-PASS** — all frozen RE gates met on both instruments.

## 1. Headline (token mass, NOT dollars — fix #1)
Tool-result text is the **MAJORITY of the dynamic served token mass** in real agent tool-loops, on the **most-conservative** denominator (D1 = raw stream span), replicated across two independent instruments:

| | tool-result share f (D1, conservative) | LB95 (2000x session-clustered) | RE-A0 (>0.50) |
|---|---|---|---|
| **Claude Code** | **0.657** | **0.569** | PASS |
| **Codex** | **0.770** | **0.748** | PASS |

Both LB95 > 0.50 → tool-result is a *majority*, not merely the largest component. (The pre-measured borderline `result/span` LB95 0.498–0.502 lifted clear of 0.50 once decode-interstitial reasoning/text were bucketed cleanly per the frozen operational definitions; no threshold was moved — see §7 reconciliation.)

## 2. Contribution & explicit concession (fix #2)
We **concede** that "agent serving is prefill-heavy" is already ASSUMED by DistServe/SplitWise; the bare direction is NOT the claim. The novel, measured deltas are:
1. **Granular split** — result vs arg vs decode-interstitial, per content class (Table §3).
2. **Heavy-tail concentration** — Gini + top-decile result mass with CIs (the cacheable hot spots the caching literature assumes but never measures on agent traces).
3. **Cross-instrument replication** with an equivalence margin.

## 3. Granular decomposition (char/4 token-mass proxy; shares are tokenizer-invariant)
Dynamic per-turn content classes (token mass, char/4; pooled):

| class | CC tok | CC % of D1 | Codex tok | Codex % of D1 |
|---|---|---|---|---|
| **R** tool-result | 1,763,558 | **65.7%** | 2,879,412 | **77.0%** |
| **A** tool-call args | 408,732 | 15.2% | 146,438 | 3.9% |
| **TX** assistant text (decode) | 209,059 | 7.8% | 119,411 | 3.2% |
| **TH** reasoning (decode)* | 57,311 | 2.1% | 416,758* | 11.1%* |
| **U** user prompt | 246,276 | 9.2% | 156,704 | 4.2% |
| **O** structural | 0 | 0.0% | 19,220 | 0.5% |
| *(static prefix S, separate)* | 125,897 (LB) | — | 685,280 | — |

\*Codex reasoning is stored **encrypted** (`encrypted_content`, base64+AES, ~1.33x plaintext); counting it as decode is **conservative** — it enlarges the denominator and can only *lower* the result-share. CC `thinking` is plaintext.

## 4. RE gate results (all frozen pre-measurement)
- **RE-A0 (load-bearing):** PASS both. CC f=0.657 (LB95 0.569), Codex f=0.770 (LB95 0.748), conservative denominator D1.
- **RE-A1 (heavy tail):**
  - Top-decile result mass: CC 0.788 (LB95 0.618), Codex 0.579 (LB95 0.545) — **both LB95 > 0.50, PASS**. The top 10% of tool-result returns hold the majority of all result token mass.
  - Gini (per-call result mass, 2000x CI): CC **0.863** [0.779, 0.903]; Codex **0.749** [0.732, 0.764] — both ≫ 0.50, no clean-negative heavy-tail flag.
- **RE-A2 (denominator robustness, fix #3):** monotone as designed (D1 ≤ D2 ≤ D3 ≤ D3′). CC 0.657 / 0.657 / 0.723 / 0.894; Codex 0.770 / 0.774 / 0.808 / 0.960. The conservative D1 is the headline; every alternative denominator only *raises* the result-share. CC has zero structural mass so D1=D2.
- **RE-A3 (cross-instrument HARD GATE, fix #5):** PASS. Both LB95 > 0.50 **AND** |f_CC − f_Codex| = **0.113 < 0.40**. This is *replicated dominance*, not instrument-dependent magnitude.
- **Gini-delta CI (fix #6):** Gini_CC − Gini_Codex = **0.114** [0.027, 0.160] — excludes 0 → CC is **structurally more concentrated** (heavier-tailed) than Codex; a genuine cross-instrument structural difference, reported with its CI.
- **STAT — HHI-by-session (result tok):** CC 0.166, Codex 0.016 — **both below the 0.20 flag**, so the pooled estimate is not driven by one session. Robust **session-median** result-share (D1): CC 0.573, Codex 0.757 (both > 0.50), corroborating the pooled headline.

## 5. Static vs dynamic (fix #4)
"Tool-result dominated" refers to **dynamic marginal prefill**, not static KV memory. Static prefix share: Codex **15.5%** (base_instructions + developer, well-captured); CC **4.5%** *(documented LOWER BOUND — the Claude Code system prompt is not present in the JSONL logs; S = first-user/env head only)*. After turn 1 the static prefix is KV-cached (~0 marginal compute), so the recurring per-turn compute is dominated by the dynamic tool-result prefill measured above.

## 6. Mandatory baselines
- **(b) DistServe assumed mix (2401.09670) / Splitwise (2311.18677):** the disaggregation literature sizes prefill/decode pools assuming a chat mix where prefill = *human prompt* text. Our measured agent **result/decode token ratio** = CC 2.61, Codex 4.22 (result alone vs all model decode A+TX+TH) — agent prefill is dominated by **external tool-result text**, not human prompt, diverging from the assumed chat regime.
- **(a) CHAT contrast — DOCUMENTED ABSENCE (flagged):** no ShareGPT/chat corpus is available on-node. Published chat regimes (DistServe/Splitwise) are characterized by modest human-prompt-driven input and decode-comparable output (input:output order ~1–10:1, with decode a large share of served stream). The agent tool-loop inverts this: external tool-result *prefill* is the majority of served mass and is heavy-tailed (Gini 0.75–0.86) — structurally different from chat. This contrast rests on published chat numbers, not an on-node chat trace; treat as a flagged limitation.

## 7. Denominator/committee-label reconciliation (transparency)
Pre-reg §7 committed D1 (raw span) as the most-conservative headline *before* measurement. The committee note called the headline "assistant-text-block-only = largest decode = most conservative." Under mutually-exclusive component accounting the *largest decode bucket* (all non-result content) **is** D1 (raw span), giving the smallest result-share and matching the pre-measured `result/span`. The literal "result-vs-assistant-text-only" reading (D3′) gives 0.894 (CC) / 0.960 (Codex) — far higher. Both readings agree the verdict is well above 0.50; we lead with the conservative D1.

## 8. SECONDARY (RE-A4) — cost-weighted (NOT headline; fix #1)
Token mass ≠ cost mass. Weighting decode at 10× / 100× prefill $/tok (Splitwise/DistServe asymmetry), tool-result's share of serving **dollars** falls to CC 0.198 / 0.025 and Codex 0.273 / 0.040. **The token-mass majority does NOT carry over to dollars** — this is exactly why the thesis is framed as token mass (prefill is cheap per token). Reported SECONDARY only; it bounds the (lesser) $-relevance and pre-empts a "this is the cost story" misread.

## 9. Limitations
- **char/4 proxy** (monotone, applied identically to numerator+denominator): all shares/Gini/top-decile are scale-invariant, identical to raw-char ratios; absolute token figures are approximate (BPE would differ in magnitude, not in any share).
- **CC static prefix** is a lower bound (system prompt absent from logs).
- **Codex reasoning** mass is the encrypted blob (conservative over-count of decode).
- **Chat baseline** is published-number contrast, not an on-node trace.
- L0 corpora: CC 74 sessions / 2,581 result-calls; Codex 93 / 3,084 (>=8 result-calls each).

## 10. Related work (fix #9 — cited + differentiated in PRE_REGISTRATION §11)
DistServe 2401.09670, SplitWise 2311.18677, DuetServe 2511.04791, Sarathi-Serve 2403.02310, Parrot 2405.19888, Autellix 2502.13965, RadixAttention 2312.07104, vLLM-APC 2309.06180 — all implement disaggregation/caching/scheduling knobs but **do not measure the prefill/decode token-mass split of real agent tool-loops**, which this experiment supplies.

## 11. Disposition
**GREEN-PASS.** Tool-result text is the majority (CC 0.66 / Codex 0.77, conservative denominator, both LB95 > 0.50), heavy-tailed (Gini 0.86 / 0.75, top-decile > 0.50 both), and cross-instrument-replicated (|Δ| 0.11 < 0.40 margin). The granular decomposition + heavy-tail concentration + cross-instrument replication is the contribution; the bare prefill-heavy direction is conceded as prior. Cost-weighting (SECONDARY) correctly shows this is a token-mass, not dollar, result.
