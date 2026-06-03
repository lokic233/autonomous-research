# RESULTS — EXP-0038 / CLAIM-0040 — CHEAP CORPUS-ONLY GATE
**Streaming-prefix semantic early-commit on agent tool RESULTS.** L0-budget GATE prescribed by
committee#1 (VERDICT-0038, yellow): measure the load-bearing EMPIRICAL premises (f_fl, rho) on REAL
tool-result corpora BEFORE any detector/GPU work. No detector training, no GPU inference — real
distributions + real tokenizer (gpt2 BPE). Honest pipeline; a kill-before-GPU is a WIN.
Run: cli:devgpu014, venv /home/dengcchi/sglang-env (egress via fwdproxy). N=1641 real records.

## VERDICT: **KILL** (fails the pre-registered gate on TWO independent criteria)

Real tool results are **NOT in the lucrative regime EXP-0037's favorable break-even required.**
The favorable p* map of EXP-0037 was real math over an UNREAL operating point. On real corpora the
operating point does not occur: **rho ≪ 1 for every realistic tool class**, and where rho is high
(one artificial class) the result is **not front-loaded** and **dumb-truncation already wins** — the
exact adversarial triple-bind the committee feared. Recommend KILL; do not spend an L1 GPU experiment.

---

## CORPORA (real tool-result text, 5 tool classes, N=1641)
| class | source (HF, live egress) | what the "result" is | N |
|---|---|---|---|
| search_rag | hotpotqa/hotpot_qa (distractor) | 10 retrieved passages; actionable = ground-truth supporting passages | 400 |
| web_search | mandarjoshi/trivia_qa (rc) | ranked web search-result descriptions; actionable = answer-bearing span | 300 |
| api_json    | THUDM/AgentInstruct (kg, webshop) | API/JSON tool observations; actionable = value next gpt-turn consumes | 600 |
| code_exec_log | THUDM/AgentInstruct (os) | real bash/OS execution output; actionable = result/error line | 300 |
| db_query    | THUDM/AgentInstruct (db) | SQL query result rows; actionable = queried field | 41 |

Ground-truth actionable span: for RAG = labeled supporting passages; for AgentInstruct = the exact
token span the agent's NEXT turn (gpt) quotes/acts on (real downstream dependency, not a guess).
N_step (next reasoning step length) = REAL tokens of that next gpt turn.

---

## (1) f_fl — REAL front-loading rate  [GATE: actionable content in front ~30%]
Fractional START position of actionable span (tokens, gpt2 BPE):

| class | n | median f_fl_start | IQR | %start≤0.30 | %END≤0.30 |
|---|---|---|---|---|---|
| api_json | 600 | 0.073 | [0.01,0.36] | 68.3% | 61.2% |
| code_exec_log | 300 | 0.037 | [0.00,0.10] | 79.0% | 79.0% |
| db_query | 41 | 0.020 | [0.01,0.12] | 97.6% | 92.7% |
| search_rag | 400 | 0.263 | [0.10,0.44] | 55.0% | **5.5%** |
| web_search | 300 | 0.154 | [0.04,0.38] | 68.3% | 67.0% |
| **DOMINANT pooled** | 1600 | **0.120** | — | **67.0%** | — |

**f_fl clears ≥0.3 front-loading for short structured results** (api/code/db/web): the actionable
span both starts AND ends inside the front 30%. But the ONE long class (search_rag) is the opposite:
the actionable span STARTS early (0.263) but **only 5.5% have it END in the front 30%** — supporting
passages are scattered across the list. → f_fl is FINE where results are short, FAILS where they're long.

## (2) rho = T_stream / T_step — REAL latency ratio  [GATE: rho ≥ 1]
rho = (N_result/r_prefill) / (N_step/r_decode). Realistic H100 vLLM: r_prefill 5k–15k tok/s, r_decode 50–120 tok/s.

| class | medN_result | medN_step | med rho (fav) | med rho (mid) | med rho (adv) | %rho≥1 (mid) |
|---|---|---|---|---|---|---|
| api_json | 48 | 48 | 0.022 | 0.007 | 0.003 | 0.0% |
| code_exec_log | 46 | 48 | 0.023 | 0.008 | 0.003 | 0.0% |
| db_query | 109 | 143 | 0.017 | 0.006 | 0.002 | 0.0% |
| web_search | 225 | 11 | 0.508 | 0.169 | 0.071 | 0.0% |
| search_rag | 1274 | 11 | 2.734 | 0.911 | 0.380 | 36.5% |
| **DOMINANT pooled** | — | — | **0.197** | **0.066** | **0.027** | **9.1%** |

**rho FAILS catastrophically.** Real tool results are SHORT (46–225 tok) and prefill into context
~instantly relative to the next decode step. Only search_rag clears rho≥1 — and ONLY because (a) it's
the artificial 1274-tok HotpotQA distractor set, and (b) I optimistically set its next-step = an
11-token answer-emit. **Re-tested with a realistic reasoning next-step (N_step∈{64,128,256}),
search_rag collapses to rho=0.02–0.48, 0% clearing rho≥1 in EVERY rate band.** There is no real
tool class where results stream slower than the agent's next step. rho≥1 is essentially empty.

## (3) JOINT (f_fl, rho) — adversarial correlation  [committee's worry: long tail = low f_fl AND high rho AND high redo]
Spearman corr(rho, f_fl_start), positive = adversarial:
- api_json −0.574, code_exec_log −0.374, db_query −0.253, web_search −0.364 (BENIGN: longer→earlier).
- search_rag **+0.091** and it's the ONLY high-rho class — and its actionable-END is the worst (5.5%≤0.3).
**The adversarial bind is real and concentrated exactly where the committee feared:** the single class
with non-trivial rho (search_rag) is also the single class that is NOT end-front-loaded and where
truncation breaks (below). Everywhere rho is high enough to matter, f_fl fails; everywhere f_fl is
good, rho≪1 (nothing to overlap). The two premises are anti-correlated in the regime that pays.

## (4) DUMB-TRUNCATION vs early-commit  [GATE: if truncation matches, apparatus unjustified]
% of results whose actionable span FULLY fits in first N tokens (keep first N, never redo, no detector):

| class | medN_result | N≤128 | N≤256 | N≤512 |
|---|---|---|---|---|
| api_json | 48 | 100% | 100% | 100% |
| code_exec_log | 46 | 100% | 100% | 100% |
| db_query | 109 | 100% | 100% | 100% |
| web_search | 225 | 91.3% | 99.7% | 100% |
| search_rag | 1274 | 0.0% | 2.8% | 14.5% |

**DUMB-TRUNCATION at N=512 fully captures actionable content for 4/5 classes (100%/100%/100%/100%).**
For the short structured/code/API/DB/web classes — i.e. everywhere rho is low — a parameter-free
truncate-and-never-redo baseline is already correct. No detector, no redo, no semantic-commit machinery
needed. The early-commit apparatus only *could* add value on search_rag (where truncation fails at
0–14.5%) — but that is precisely the class where (a) actionable content is NOT front-loaded (5.5% end
≤0.3) so early-commit would commit WRONG, and (b) the gain shown earlier was an artifact that vanishes
under a realistic next-step. Apparatus is UNJUSTIFIED on the real distribution.

**INCREMENTAL-PREFILL note (the real production baseline):** production agent stacks (vLLM/TGI/SGLang)
stream tokens into the KV cache via chunked/continuous prefill as they arrive — they do NOT wait for
EOF. EXP-0037's rho implicitly modeled a wait-for-EOF stall. With incremental prefill the addressable
latency is only the residual gap between last-token-arrival and next-step-need, which for 46–225-tok
results is sub-100ms on H100. The thing early-commit overlaps is largely already overlapped in prod.

## (5) PRIOR-ART (live web; distinguish)
- **LLMCompiler — Kim et al. 2023 (arXiv:2312.04511, ICML 2024).** Overlaps agent latency by planning a
  DAG of function CALLS and dispatching independent calls in PARALLEL. Operates at the CALL-graph level;
  does NOT commit on a partial/streaming tool RESULT, and is lossless (no correctness-safety break-even
  on result prefixes). Orthogonal mechanism — and it already captures the inter-call latency this claim
  targets, without any redo risk.
- **CALM — Schuster et al. 2022 (arXiv:2207.07061, NeurIPS 2022).** Confidence-thresholded EARLY-EXIT in
  the LM's own decode (per-token layer skipping) with sequence-level consistency guarantees. The
  confidence-gated-commit idea is the conceptual ancestor of this claim's "detector fires on a prefix,"
  but CALM commits on the MODEL's internal confidence about its OWN generation, not on a partial external
  tool RESULT. No tool-result semantics.
- **Leviathan et al. 2023 spec-decoding cost model.** The p*-style break-even (accept-prob × cost) is the
  algebraic ancestor of EXP-0037's p*; spec-decode is LOSSLESS (verified), so it has no semantic-redo
  penalty W and no front-loading dependence. Different object entirely.
- **No prior work does correctness-safe semantic committing on a partial/streaming tool RESULT.** That
  niche is genuinely open — but this gate shows the niche is empty in practice: the regime where it would
  pay (long, slow-streaming, front-loaded, truncation-resistant results) does not occur in real corpora.

---

## GATE VERDICT: **KILL** — do NOT proceed to detector-feasibility L1.
Pre-registered kill rule fired on TWO independent criteria + the joint bind:
1. **rho < 1 for dominant classes** → FIRED HARD. Median rho 0.007–0.508; 0–9% clear rho≥1; the lone
   exception (search_rag) collapses to 0% under a realistic next-step. Real tool results stream fast
   relative to reasoning. **Nothing meaningful to overlap.** (kill criterion #2)
2. **Dumb-truncation matches early-commit** → FIRED. N≤512 truncation fully captures actionable content
   for 4/5 classes (100%). The detector/redo apparatus is unjustified everywhere rho is low. (kill #3)
3. **Adversarial (f_fl, rho) correlation** → CONFIRMED. The only high-rho class is the only non-end-
   front-loaded one and the only truncation-resistant one. The premises are anti-correlated in the
   paying regime — early-commit would commit WRONG exactly where it has time to commit at all.
4. f_fl ALONE clears ≥0.3 for short classes — but f_fl was never the binding constraint; rho is.

EXP-0037's favorable p* break-even was correct math over an operating point (rho≥2, long slow-streaming
front-loaded results) that **does not exist in real agent tool traffic.** The honest negative is: the
mechanism is real, but its lucrative regime is empirically empty, and the cheap baseline (truncate /
incremental-prefill) already captures the available latency without any correctness risk.
**This gate saved a wasted GPU L1. That is the win.**

## Reproducibility / paths (on cli:devgpu014:/home/dengcchi/ros-EXP-0038/)
- gate.py — corpus fetch + per-record f_fl/rho/actionable-span extraction (real tokenizer)
- analyze.py — metrics 1–4 + joint Spearman + incremental-prefill/search_rag interrogation
- results/records.json (1641), results/per_record.csv, results/counts.json, results/analysis.txt
- PRE_REG.md committed BEFORE running (HEAD 9e9a788). Corpora + method + kill rule pre-registered.
