# EXP-0061 — PRE-REGISTRATION (FROZEN)
**Project:** PROJ-0015 · **Claim:** CLAIM-0026 · **Verdict link:** VERDICT-0071
**Agent:** researcher-0026-L0-r8 · **Node:** cli:dengcchi-mac · **Level:** 0 (Mac CPU, stdlib only, NO numpy/scipy)
**LOCK-TS:** 2026-06-01T23:44:20Z
**Type:** CHARACTERIZATION — descriptive RESULT only. NO predictor, NO dAUC, NO eviction mechanism. The headline numbers ARE the contribution. A clean negative is first-class.

This file is committed via `ros commit` BEFORE any measurement. All thresholds, denominators, the char-proxy tokenizer, and operational field definitions below are FROZEN. No threshold moves after this lock.

---

## 1. THESIS (mandatory fix #1 — TOKEN MASS, not "serving dollar")
We deliver the FIRST granular **token-mass** decomposition of real agent serving traces: **where the agent serving PREFILL TOKEN MASS lives** — tool-result vs tool-call-arg vs decode-interstitial (assistant text/reasoning) — with its heavy-tail (Gini) and cross-instrument structure.
Token mass != cost mass: prefill is ~10–100x cheaper per token than decode (Splitwise 2311.18677 / DistServe 2401.09670 $/tok asymmetry). We therefore report **token mass** as the HEADLINE. An OPTIONAL **SECONDARY** cost-weighted variant (RE-A4) using a published prefill-vs-decode $/token ratio is reported SECONDARY, never headline.

## 2. CONTRIBUTION & EXPLICIT CONCESSION (mandatory fix #2)
The contribution = the GRANULAR decomposition (tool-result vs arg vs decode-interstitial) + heavy-tail Gini (cacheable hot spots) + cross-instrument replication.
**We EXPLICITLY concede that "prefill-heavy" is already ASSUMED by DistServe / SplitWise.** The bare direction ("agent serving is prefill-dominated") is NOT the claim and any "rediscovers prefill-heaviness" reading is rejected. The novel delta is: (i) the *granular* result-vs-arg-vs-decode split measured on real tool-loops, (ii) the heavy-tail *concentration* the caching literature assumes but never measures on agent traces, (iii) *cross-instrument* replication.

## 3. CORPORA & UNIT
- **CC** = Claude Code: `~/.claude/projects/*/*.jsonl` (277 files present at lock).
- **Codex** = `~/.codex/sessions/**/*.jsonl` (125 files present at lock).
- Session-inclusion filter (reused from EXP-0057): a session is included iff it yields **>= MIN_TRIALS = 8** tool calls (parsed via parse_cc_session/parse_codex_session). Sessions below floor dropped.
- Bootstrap unit for ALL CIs = the **session** (session-clustered resample with replacement).

## 4. TOKENIZER / CHAR-PROXY (mandatory fix #7)
- **char/4 proxy**: token_mass(x) = len(x) / 4.0, applied **identically** to numerator and every denominator. CHARS_PER_TOK = 4.0 (same constant as EXP-0054/0055/0057).
- This proxy is **monotone** in char length and **cancels exactly in every ratio** (all shares, Gini, top-decile fractions are scale-invariant, so they are identical to raw-char ratios). Absolute token-mass figures are reported in char/4 units. We deliberately avoid the gpt2-venv tokenizer used in EXP-0059 to keep this run pure-stdlib and robust on-node; we disclose that BPE token counts would differ in absolute value but NOT in any reported share/Gini (monotone, applied identically). This is the CONSERVATIVE, transparent choice.

## 5. OPERATIONAL DEFINITIONS — pinned to parser FIELD NAMES (mandatory fix #7)
Field semantics for `result` / `args_str` are reused VERBATIM from parse_cc_session / parse_codex_session (EXP-0057). The decomposition assigns EVERY content character of the *dynamic* stream to exactly ONE mutually-exclusive class:

| Class | Symbol | CC source (message.role, content block) | Codex source (payload.type / role) |
|---|---|---|---|
| tool-result | **R** | role=user, block type=`tool_result` → `block_text(b)` | type=`function_call_output` → `output` |
| tool-call-arg | **A** | role=assistant, block type=`tool_use` → `canon_args(input)` | type=`function_call` → `canon_args(arguments)` |
| decode-interstitial text | **TX** | role=assistant, block type=`text` → `text` | type=`message`, role=assistant → input/output_text |
| decode-interstitial reasoning | **TH** | role=assistant, block type=`thinking` → `thinking` | type=`reasoning` → reasoning text |
| user prompt text | **U** | role=user, content str OR block type=`text` | type=`message`, role=user → input_text |
| structural/other | **O** | any other block type → json.dumps(b) | any other response-item not above |
| STATIC system prefix | **S** | reconstructed env+first-user head (EXP-0059 cc_heads) — LOWER BOUND (CC system prompt is NOT in logs) | type=`session_meta`/base_instructions + role=developer messages |

- **Decode** := A + TX + TH (everything the model generates: args are decoded too).
- **Mirror-event de-duplication (Codex):** payload types `agent_message`, `user_message`, `mcp_tool_call_end`, `exec_command_end`, `mcp_tool_call_begin`, `token_count`, `task_started`, `task_complete`, `turn_aborted` are HIGH-LEVEL MIRRORS of the response-item stream and are **excluded** from all mass buckets. Verified at lock: all 992 `mcp_tool_call_end` call_ids also appear as `function_call_output` (100% overlap) → results are fully captured by R with zero double-counting.
- `block_text`, `canon_args` reused verbatim from EXP-0057.

## 6. STATIC vs DYNAMIC (mandatory fix #4)
- **Dynamic per-turn stream** = R + A + TX + TH + U + O (the per-message marginal content). This is the marginal prefill+decode that recurs every turn. **All RE gates and the headline run on the DYNAMIC stream.**
- **Static prefix S** = system-prompt / base-instructions head, KV-cached after turn 1 (~0 marginal compute). Reported SEPARATELY as a share `S/(S+dynamic)`. CC's S is a documented LOWER BOUND (CC system prompt is not present in the JSONL logs; we use the EXP-0059 reconstructed env+first-user head). Codex S is well-captured (base_instructions + developer).
- "Tool-result dominated" in all headline claims refers to the **DYNAMIC marginal prefill**, NOT total KV memory.

## 7. THREE DENOMINATORS — result-share f = R / D (mandatory fix #3; committed BEFORE seeing numbers)
All three computed on the DYNAMIC stream; result-share f = R / D:
- **D1 = RAW STREAM SPAN** = R + A + TX + TH + U + O  (every dynamic content char; the largest decode/non-result bucket).
- **D2 = NON-OVERHEAD MASS** = R + A + TX + TH + U  (drop structural O).
- **D3 = ASSISTANT-TEXT(+ARG)-DECODE** = R + A + TX + TH  (result vs the model's own decode + user text removed; i.e. result vs decode only). [reported]
- Also reported for transparency: **D3' = R + TX** (result vs assistant-text-blocks-only, the purest prefill-result-vs-decode-text split).

**HEADLINE = the MOST CONSERVATIVE denominator = the one giving the SMALLEST result-share f.** By construction D1 >= D2 >= D3 (mutually-exclusive non-negative components), so the most-conservative is **D1 = RAW STREAM SPAN**. We pre-commit D1 as the headline denominator.

> Committee-label reconciliation (frozen, transparent): the design committee named the headline "assistant-text-block-only = largest decode = most conservative." With mutually-exclusive component accounting, the *largest decode bucket* (and therefore the *most conservative*, smallest-result-share) denominator is the one whose decode side absorbs ALL non-result content = **D1 (raw span)**, matching the pre-measured `result/span` = 0.626 (CC) / 0.861 (Codex) and the borderline LB95 0.498–0.502 note. We therefore implement the committee's INTENT (most-conservative = headline) and report D1 as headline, while ALSO reporting D3' (the literal "result-vs-assistant-text-only" reading) as a robustness point. If the two readings ever disagreed on the >0.50 verdict we would report BOTH; they bracket the truth.

**If headline (D1) conservative result-share < 0.50 → we report "tool-result is the LARGEST single component," NOT "majority."** (committed downgrade rule.)

## 8. RE GATES (FROZEN)
- **RE-A0 (LOAD-BEARING):** pooled result-share f on the CONSERVATIVE denominator D1, 2000x session-clustered bootstrap **LB95 > 0.50 on CC AND Codex**. Clean negative if CC LB95 crosses 0.50 (then downgrade per §7).
- **RE-A1 (concentration):** top-decile result-mass share — sort tool calls by result token-mass desc, share held by the top ceil(10%) of calls; 2000x session-clustered bootstrap **LB95 > 0.50 on BOTH** corpora. PLUS **Gini** over per-call result token-mass with 2000x session-clustered bootstrap CI (fix #6).
- **RE-A2 (denominator robustness):** report f under D1/D2/D3(/D3'); conservative D1 = headline (fix #3).
- **RE-A3 (cross-instrument HARD GATE, fix #5):** on the chosen denominator D1, **BOTH LB95 > 0.50 AND |f_CC − f_Codex| < 0.40**. Direction-only with divergent magnitude → "instrument-dependent magnitude," NOT "replicated dominance."
- **GINI DELTA CI (fix #6):** 2000x paired session-clustered bootstrap CI on `Gini_CC − Gini_Codex`. No headline point estimate without a CI.
- **STAT — HHI-by-session:** HHI over per-session total result token-mass (premeasure ~0.170, near the 0.20 flag). If HHI > 0.20 we flag domination AND report the **session-median result-share** (median over sessions of session R/D1) as the robust headline alongside the pooled value.

## 9. CLEAN-NEGATIVE CRITERIA (mandatory fix #8) — first-class
Declare CLEAN-NEGATIVE if EITHER:
(a) RE-A0 conservative LB95 < 0.50 on CC OR Codex (tool-result is not a majority of the served dynamic mass), OR
(b) Gini < 0.50 on EITHER corpus (no heavy tail → no cacheable hot spots → boring uniform mass).
A clean negative is reported as the result, not hidden.

## 10. MANDATORY BASELINES
- **(a) CHAT contrast:** no ShareGPT/chat trace is available on-node (DOCUMENTED ABSENCE, flagged). Contrast point uses a PUBLISHED chat prefill/decode mix: in multi-turn chat the served stream is decode-dominated / input is human text — DistServe (2401.09670) and Splitwise (2311.18677) characterize chat with modest input:output token ratios (order ~1–10:1 input:output depending on workload; ShareGPT medians ~ a few hundred prompt tokens vs hundreds of decode tokens). We report our measured agent result-share and contrast it against this published chat regime, flagging the absence of an on-node chat corpus as a limitation.
- **(b) DistServe ASSUMED mix:** DistServe (2401.09670) and Splitwise (2311.18677) ASSUME a prefill/decode workload mix to size disaggregated prefill/decode pools but do not measure agent tool-loops. We cite their assumed mix and show the measured agent result/decode ratio diverges (agent prefill is dominated by EXTERNAL tool-result text, not human prompt text).

## 11. MANDATORY RELATED WORK (fix #9 — cite + one-line differentiate)
- **DistServe 2401.09670** — prefill/decode disaggregation; ASSUMES the workload mix, does not measure the prefill/decode token-mass split of real agent tool-loops.
- **SplitWise 2311.18677** — phase-split serving on the prompt/decode $/tok asymmetry; assumes, never measures, the agent tool-loop split.
- **DuetServe 2511.04791** — concurrent prefill/decode scheduling; orthogonal scheduling knob, no agent token-mass census.
- **Sarathi-Serve 2403.02310** — chunked-prefill to hide decode stalls; assumes prefill-heavy, does not decompose agent tool-result mass.
- **Parrot 2405.19888** — LLM-app dataflow/Semantic Variables; optimizes orchestration, does not measure the result/arg/decode mass split.
- **Autellix 2502.13965** — agent program scheduling; scheduler-level, no granular token-mass decomposition.
- **RadixAttention 2312.07104** — prefix-tree KV reuse; caches shared prefixes, does not measure the prefill/decode token-mass split of real agent tool-loops.
- **vLLM-APC 2309.06180** — PagedAttention/automatic prefix caching; serves prefixes, does not measure the prefill/decode token-mass split of real agent tool-loops.

## 12. FROZEN CONSTANTS
SEED=20260601 · NBOOT=2000 · CHARS_PER_TOK=4.0 · MIN_TRIALS=8 · TOPDECILE=0.10 · A0_THRESH=0.50 · A1_THRESH=0.50 · CROSS_MARGIN=0.40 · GINI_NEG_THRESH=0.50 · HHI_FLAG=0.20.
Bootstrap percentiles: LB95 = 2.5th pct, UB95 = 97.5th pct, sorted draws. Session-clustered resample (sessions with replacement, all calls of a picked session included).

## 13. DELIVERABLES
impl/{PRE_REGISTRATION.md, decomposition_census.py, analysis.md} + results/summary.json + results/per_session_{cc,codex}.csv.
On completion: `ros exp complete`, advance CLAIM-0026, report to sub-monitor-0015-r8. Do NOT self-judge, do NOT convene a committee, do NOT touch GPU.
