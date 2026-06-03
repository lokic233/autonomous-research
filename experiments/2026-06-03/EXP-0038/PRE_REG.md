# PRE-REGISTRATION — EXP-0038 (CHEAP CORPUS-ONLY GATE for CLAIM-0040)
Committed BEFORE running. claim=CLAIM-0040 exp=EXP-0038 task=TASK-0030 proj=PROJ-0011.
Honest pipeline. A "kill before GPU" finding is a WIN.

## Why this gate exists
EXP-0037 (L0) was HELD-PARTIAL with a FAVORABLE break-even, but committee#1 (VERDICT-0038, yellow)
blocked green because EVERY load-bearing EMPIRICAL premise was UNMEASURED — the L0 hand-picked Beta
priors for f_fl and assumed rho. This gate measures the two binding empirical constraints CHEAPLY
(no detector training, no GPU inference — just real distributions + a real tokenizer) so we don't
burn an L1 GPU experiment on a regime that doesn't occur in reality.

## Corpora (real tool-result text; egress on devgpu014 via fwdproxy; venv=/home/dengcchi/sglang-env)
Target ~5 tool CLASSES; for each, fetch real result text from HF datasets (fallback: locally cached):
1. SEARCH/RAG result lists      -> HF: a QA-with-retrieved-passages dataset (e.g. natural_questions / hotpot / trivia_qa contexts, or ms_marco passages). Actionable span = rank/position of the gold/relevant passage among the retrieved list.
2. API / structured-JSON responses -> HF tool/agent datasets carrying JSON tool outputs (e.g. toolbench/ API-Bank style "observation"/"response" fields; fallback BFCL possible_answer JSON). Actionable span = position of the answer-bearing key vs boilerplate/metadata/pagination.
3. CODE-EXEC / test output       -> HF code dataset with execution output / tracebacks (e.g. a SWE/code-exec or mbpp/HumanEval-with-output style). Actionable span = position of the error/result line vs trailing logs.
4. DB / tabular query results    -> structured rows; actionable span = position of the queried field. (use JSON/table from above if a dedicated one isn't reachable)
5. LOG TAILS                     -> log/trace text (adversarial-by-design: actionable line often at the TAIL). Source: any traceback/log field; if none, synthesize-from-real-structure ONLY as an explicit caveat (not counted in headline).

If a class can't be fetched live, fall back to LOCAL BFCL possible_answer JSON for the JSON class and
DOWNGRADE coverage honestly in RESULTS (do NOT fabricate distributions).

## Metric 1 — f_fl (front-loading rate)
For each real result, compute f_fl = fractional start position of the ACTIONABLE span within the result,
measured in TOKENS using a real tokenizer (transformers AutoTokenizer, a Llama/GPT-style BPE).
Heuristic per class (defensible, documented):
- search list: char/token offset of the gold/relevant passage start / total length.
- JSON: token offset of the answer-bearing key's value / total tokens (boilerplate keys = metadata/status/pagination/links precede it -> raises position).
- code-exec: token offset of first error/result line / total; trailing logs after it raise denominator.
- log tail: token offset of the actionable (ERROR/result) line / total.
"front-loaded" = actionable span STARTS within the front 30% (f_fl_start <= 0.30 means content is up front;
report BOTH the start-position distribution and the fraction of results whose actionable content is
within the front 30%). Report distribution (median, IQR, %<=0.3) PER CLASS.

## Metric 2 — rho = T_stream / T_step
rho = (time to stream the FULL tool result) / (time for the agent's next reasoning step/decode).
Using REAL token counts:
- N_result = real tokens in the tool result (measured).
- N_step   = tokens in the next reasoning step. Use a realistic prior: typical agent next-step
  decode length. Use N_step in {64, 128, 256} (report sensitivity) as the next-step decode budget.
- rates: streaming a tool result into context = PREFILL of N_result tokens at prefill throughput
  r_prefill (tok/s); next step = DECODE of N_step tokens at decode throughput r_decode (tok/s).
  Realistic H100-class vLLM: r_prefill ~ 5000-20000 tok/s (we use a band), r_decode ~ 50-120 tok/s.
  rho = (N_result / r_prefill) / (N_step / r_decode).
  ALSO report the network/EOF-stream variant (wait-for-EOF at a network token rate) as a SECOND rho,
  since the production baseline is incremental-prefill (see baseline note).
Report rho distribution PER CLASS under the rate band + N_step sensitivity.

## Metric 3 — JOINT (f_fl, rho) adversarial correlation
Per class and pooled: is high rho (long results) correlated with LOW f_fl (tail-loaded) — the
committee's worry that long log tails simultaneously have low f_fl + high rho + high redo cost?
Report Spearman corr(rho, f_fl_start) and a per-class scatter/table.

## Metric 4 — DUMB-TRUNCATION baseline (analytic on real distributions)
For each result, does "keep first N tokens, drop the rest, NEVER redo" preserve the actionable span?
= fraction of results whose actionable span fully fits within the first N tokens, for N in {128,256,512}.
If dumb-truncation already captures the actionable content on most real front-loaded results, the
early-commit/detector/redo apparatus is UNJUSTIFIED (you don't need a detector or redo — just truncate).
ALSO note INCREMENTAL-PREFILL: production streams tokens into KV continuously; the real baseline is
not wait-for-EOF, so the addressable latency to overlap is smaller than EXP-0037's rho assumed.

## Metric 5 — PRIOR-ART (live web, egress)
Cite + distinguish: LLMCompiler (Kim 2023), CALM (Schuster 2022), Leviathan 2023 spec-decode cost model.
Question: does ANY do correctness-safe committing on a PARTIAL/STREAMING tool RESULT?

## KILL RULE (pre-committed)
- IF real f_fl does NOT clear (actionable content NOT within front 30% for a meaningful fraction —
  operationalize: <50% of results in the dominant tool classes have actionable span starting <=0.3)
  -> recommend KILL (the lucrative front-loaded regime doesn't occur in reality).
- OR IF real rho < 1 for the dominant tool classes (results stream fast vs next step -> little to gain)
  -> recommend KILL.
- OR IF dumb-truncation (N<=512) matches early-commit on real results (actionable span fits for most)
  -> recommend KILL (apparatus unjustified; just truncate, no detector/redo needed).
- ELSE -> recommend proceed-to-detector-feasibility L1.
"Dominant tool classes" = the classes that realistically dominate agent loops (search/RAG + API-JSON +
code-exec); log tails treated as the adversarial stress class.
