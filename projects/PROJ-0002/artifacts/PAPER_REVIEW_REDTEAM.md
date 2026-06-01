# PAPER_REVIEW_REDTEAM.md — Adversarial Self-Review of PAPER_DRAFT_FINAL.md (CLAIM-0006)

**Reviewer lane:** researcher-0006-review (hostile MLSys reviewer + VERDICT-0043 condition auditor)
**Reporting to:** orchestrator 22bd6bef · **Date:** 2026-05-31 · **Mode:** READ-ONLY, document-only (no claim/verdict/map/exp edits)
**Target:** prior_art/PROJ-0002/CLAIM-0006/PAPER_DRAFT_FINAL.md
**Evidence base:** VERDICT-0043, CLAIM-0006.yaml, EXP-0013/0015/0026/0027/0030/0034 result.md (+ EXP-0014/0021/0023/0025 support), novelty_boundary_2026-05-31.md
**Bottom line:** ✅ **SUBMISSION-READY (go).** All 4 VERDICT-0043 finalization conditions are met; every number traces to a cited EXP file; no over-claim re-inflated. Two cosmetic punch-list items only (non-blocking).

---

## 1. VERDICT-0043 CONDITION CHECK

VERDICT-0043 named these binding finalization conditions (area_chair "do regardless" + the framing of the two YELLOWs). Audited one-by-one against the draft:

| # | Condition (verbatim intent) | Status | Evidence in draft |
|---|---|---|---|
| C1 | EXP-0034 scoped-approx stated in the SETUP section, NOT buried | ✅ **MET** | §2.2 is a dedicated, bold-headed setup subsection: *"SCOPE STATEMENT — EXP-0034 is a SCOPED in-window approximation, NOT a true async KVConnector measurement."* States vLLM 0.6.6 lacks `kv_connector.v1` API, cites the EXP-0034 SMOKE `full_connector_blocker`, and bounds the omission direction (more overlap → shrinks, not flips, margin). It is in §2 (Setup), read **before** any result. Matches EXP-0034 SMOKE_RESULT lines 32–43 verbatim in substance. |
| C2a | Report the 8k/5% = 1.0032 cell honestly: median (not CI), 12/12 directional consistency as the evidence | ✅ **MET** | §6.2 explicitly states the harness reports **per-cell MEDIANS over 6 reps and does NOT compute a per-cell bootstrap CI** (`statistics.median(ts)`, reps=6 — I verified this in EXP-0034/impl, line 176/194). It declines to quote a CI it did not measure, calls 0.32% @ 6 reps "operationally a TIE," and frames the evidence as **12/12 directional consistency, not per-cell significance.** Honest and harness-accurate. |
| C2b | Cite CacheBlend / LMCache / vLLM-PagedAttention / SGLang / Irminsul BY NAME | ✅ **MET** | All five cited by name with arXiv IDs in §2.1, §5, §6, §7.3, abstract, conclusion: CacheBlend arXiv:2405.16444; LMCache (github.com/LMCache/LMCache + LMCache 0.1.dev1 kernel); vLLM/PagedAttention arXiv:2309.06180; SGLang RadixAttention arXiv:2312.07104; Irminsul arXiv:2605.05696 (named as the CDC-over-radix mechanism twin). |
| C3 | (product_realist) Frame the win honestly as marginal + regime-confined; lead with negative adoption guidance | ✅ **MET** | Abstract leads with *"the serving win is real but operationally MARGINAL and REGIME-CONFINED"* and *"primary practical value is NEGATIVE ADOPTION GUIDANCE."* §7.1 leads §7 with the same three-point framing (0.3–2.9% marginal; S≥50k confined; "when NOT to use CDC"). Title itself says "Honest Competitive Bracket." |

**All four conditions MET.** No condition buried, softened, or skipped.

---

## 2. NUMBER-TRACEABILITY AUDIT (every headline number → cited EXP file)

Every quantitative claim in the draft was traced to a result.md. **No invented number; all match the registry evidence.**

| Draft claim | Cited EXP | Registry value | Match |
|---|---|---|---|
| CDC slope 0.958 [0.937, 0.980], R²=0.972 | EXP-0013 | 0.958 [0.937,0.980], R²=0.972, n=225 | ✅ exact |
| vLLM-APC/Radix/FlashInfer R²=0.0007 (position-driven) | EXP-0013 | 0.476/0.475/0.475, R²=0.0007 | ✅ exact |
| Position spread 69.3 pp vs CDC 0.13 pp | EXP-0013 | 69.3 pp / 0.13 pp (max 0.52) | ✅ exact |
| Engine-averaged slope 0.258, R²=0.075 | EXP-0013 | 0.258, R²=0.075 | ✅ exact |
| Attn-sink: CDC 0.12% / vLLM 0.22% / Radix 0.014% / PIC 3.47% | EXP-0013 | 0.119/0.217/0.014/3.467% | ✅ exact |
| Margin medians 1.77×/6.20×/1.29× | EXP-0013 | 1.77 [1.56,1.87] / 6.20 [5.15,6.86] / 1.29 [1.25,1.33] | ✅ exact |
| Win-region inj/seq≤1% = 100% [Wilson 0.972,1.0] | EXP-0013 | 135/135, [0.972,1.0] | ✅ exact |
| Token-frac win-region 0.037 [0.0361,0.0379]; ≤8.1% all priors | EXP-0015 | 0.0370 [0.0361,0.0379]; range 0.027–0.081 | ✅ exact |
| Count-frac GIVEN S≥50k = 0.457 [0.453,0.461]; 41–52% / median 0.477 | EXP-0015 | 0.4573 [0.4531,0.4613]; 0.411–0.520, median 0.477 | ✅ exact |
| 20k tasks / 291,454 injections; median inj/seq 2.8%; count≤1%=0.246 | EXP-0015/0005 | 291,454 inj, 20k tasks; 0.2461 [0.2426,0.2495] | ✅ exact |
| ~81% of tokens in degrade band | EXP-0005 (via 0015) | ~81% >5% degrade | ✅ exact |
| EXP-0026 CDC 12/12, TTFT 1.05–1.79×, thru 1.00–1.13×, PIC 0/12 | EXP-0026 | 12/12 both metrics; TTFT 1.05–1.79; thru 1.00–1.13 | ✅ exact |
| EXP-0027 oracle: CDC 2/6, loses low inj/seq 0.612–0.991× | EXP-0027 | 2/6; 0.612/0.637/0.966/0.991 lose; 1.054/1.175 win | ✅ exact |
| EXP-0030 gather: 12/12, CI excl 1.0 in 11/12, 8k/0.5% tie [0.994,1.028], 28k/0.5%=1.265 | EXP-0030 | identical full table | ✅ exact |
| EXP-0034 in-window E2E: 12/12, 1.003–1.029×, 8k/5%=1.0032 | EXP-0034 | identical full table; 8k/5%=1.003 | ✅ exact |
| §6.4: EXP-0014 1.02–2.68× (32k/0.1%=2.68); EXP-0021 all 8 excl 1.0, 32k/1%=1.129 [1.128,1.151], 30 reps; EXP-0025 22/24 CDC, 2/24 PIC 0.993–0.994; EXP-0023 band [1.10,2.03]/[1.00,1.28], 0/8 invert | EXP-0014/0021/0025/0023 | all verified exact | ✅ exact |

**VERDICT: zero untraced numbers, zero invented numbers.** Draft's self-discipline ("every number copied, not re-derived") holds.

---

## 3. STRONGEST REVIEWER REJECTION + REBUTTAL STATUS

**Strongest hostile rejection (the composition / async-connector scope — the eval_prosecutor's KILLER):**
> *"EXP-0034 is an in-window approximation that structurally HANDICAPS PIC by omitting LMCache's async layerwise transfer scheduler — PIC's primary latency-hiding mechanism. At the 0.32% min-margin (8k/5%) any async shrinkage is effectively a tie. The 'CDC wins 12/12 E2E' headline is therefore an evaluation strawman until measured on vLLM≥0.7 V1 KVConnector under CONCURRENT load."*

**Rebuttal status in draft: HONESTLY CONCEDED, NOT REBUTTED — and this is the correct disposition.** The draft does not try to beat this objection; it:
1. Scopes EXP-0034 as an in-window approximation up front (§2.2), explicitly NOT a true async-connector result.
2. Concedes the omitted async overlap would *shrink* (not flip) CDC's margin within the measured band, and could compress 8k/5% to a tie (§2.2, §6.2, §7.2).
3. Declares the true async-connector E2E (vLLM≥0.7 V1 KVConnector under concurrent load) as **future work and the explicit env-gated path to unanimous GREEN** (§7.2), matching VERDICT-0043's "one un-measured axis."
4. Reframes the whole paper as path-(b) **honest-conditional characterization** whose primary value is negative adoption guidance — which does NOT depend on winning the async axis.

This is the only viable rebuttal for a path-(b) paper: the objection is a GREEN-promotion blocker (it keeps the claim YELLOW under green_rule=unanimous), but it is **not a validity flaw** for an honest-conditional submission. The draft's framing is exactly what the area_chair (who voted GREEN) argued. **Rebuttal posture: appropriate and sufficient for submission; insufficient only for unanimous-GREEN promotion (which requires the env upgrade — out of scope here).**

A second-tier reviewer rejection ("EXP-0026's 12/12 is a re-impl artifact") is **pre-empted**: the draft cites EXP-0027 (oracle shows CDC *loses* at low inj/seq, conceding EXP-0026 was partly gather-overhead) and EXP-0030 (real LMCache kernel resolves the bracket toward CDC). The bracket is presented honestly with its internal tension intact.

---

## 4. OVER-CLAIM RE-INFLATION CHECK (should be NONE)

Scanned for the four killed framings. **NONE re-inflated.** Each appears only as an explicit denial:

| Killed framing | Status | Where |
|---|---|---|
| Universal CDC-win / "CDC beats PIC everywhere" | ✅ NOT present | §8 explicitly: *"What it is NOT: a paper claiming CDC universally beats PIC."* Win is everywhere framed as marginal + conditional. |
| Cross-engine slope LAW / emergent law | ✅ NOT present | §3.2 + conclusion: slope≈1 is a *"mechanism-derived accounting identity (CacheBlend §4 + Pope), NOT an emergent law"*; engine-averaged slope explicitly called *"an artifact."* |
| Token-weighted / unconditional win | ✅ NOT present | Abstract + §4.1/4.2: token-weighted framing *"UNSUPPORTED"*; ≤8.1% under any prior; win is conditional count-level (S≥50k) only. |
| True-async-connector serving result | ✅ NOT present | §2.2 + §6 + §7: EXP-0034 repeatedly labeled scoped in-window approximation, *"we do not claim it as a true async-connector result"*; async is declared future work. |

The "~2%" anchor is also correctly demoted to a *conditional cost-map contour* (§3.4), not a CDC property. No over-claim leakage.

---

## 5. GO / NO-GO VERDICT + PUNCH-LIST

### VERDICT: ✅ **GO — SUBMISSION-READY** as a path-(b) honest-conditional-characterization paper (MLSys).

The paper carries 4 GREEN / 2 YELLOW / 0 RED (VERDICT-0043). The two YELLOWs are scope-constraints (un-measured async axis + marginal-win framing), both addressed honestly in prose rather than papered over. All four finalization conditions are met; all numbers trace; no over-claim re-inflated. The honesty discipline is genuinely strong — the draft repeatedly argues *against its own headline*, which is exactly the posture a hostile reviewer cannot easily attack.

### PUNCH-LIST (all NON-BLOCKING; cosmetic / nice-to-have):

1. **[MINOR — wording nuance on C2a]** VERDICT-0043 literally says *"report the 8k/5% CI explicitly."* No per-cell CI exists (harness computes median over 6 reps only). The draft's resolution — state plainly that no CI was computed and lean on 12/12 directional consistency — is the **honest** answer and matches the harness, but a literal-minded reviewer cross-checking the verdict text may note the word "CI." **Recommendation:** keep as-is; optionally add one clause noting the analogous EXP-0030 8k/0.5% gather CI [0.994,1.028] *does* include 1.0 as the nearest measured-CI proxy (the draft already does this in §6.2 — so arguably already satisfied). No change required.

2. **[COSMETIC]** §2.1 / §6 mix "S≥50k" (abstract/headline) with the cost-map's "inj/seq" axis; a fresh reader may briefly conflate the count-level S≥50k win-region with the token-level negligibility. The draft handles this in §4.1–4.2 with the "two axes point opposite directions" framing — clear, but a single forward-reference from the abstract to §4.1 would harden it. Optional.

3. **[OPTIONAL provenance polish]** novelty_boundary line 12 historically flagged the PIC family as "ABSTRACT-LEVEL only," later upgraded to FULL BODY (lines 204–209, TASK-A outcome line 366: "10/10 body-verified"). The draft's "10/10 full LaTeXML HTML bodies" claim is **accurate to the final state**, but if a reviewer audits the trail they'll see the upgrade. No action needed — final state is correct and consistent.

**None of the punch-list items block submission.** The paper is internally consistent, fully evidence-grounded, and honest about its single binding residual (the env-gated true-async axis).

---

## APPENDIX — Heartbeat / process note
- Registered: researcher-0006-review (role=researcher). Heartbeats sent via `ros heartbeat --agent researcher-0006-review` (the `agent` subcommand only supports `register`; heartbeat is a top-level subcommand).
- READ-ONLY: no claims/verdicts/map/experiments touched; EXP-0034 NOT run/modified; CPU-only; wrote only this file under prior_art/PROJ-0002/CLAIM-0006/.
