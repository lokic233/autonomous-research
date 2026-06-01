# EXP-0055 PRE-REGISTRATION — Within-Tool Pre-Execution Prediction of Result-Prefill Whales

**Project:** PROJ-0009  **Claim:** CLAIM-0020  **Researcher:** researcher-0020-L0-r7 (sub-monitor-0009-r7)
**LOCKED-TS: 2026-06-01T19:11:52Z**  (frozen BEFORE the main run; committed before any results exist)
**Seed:** 20260601   **Stack:** pure Python stdlib (no numpy/torch), Mac CPU. Reuses EXP-0054 parse/JOIN/auc/
logistic/session-clustered-CV/2000x-bootstrap machinery.

---

## THESIS (within-tool, pre-execution)
Tool-RESULT prefill cost is extreme heavy-tail. The NON-TRIVIAL claim is: WITHIN a high-volume tool class, a
CHEAP PRE-EXECUTION feature of the ARGUMENTS predicts which call will be a result-prefill WHALE (top-decile
result token length) **over and above** a JOINT baseline that ALREADY includes tool identity + an arg-template
feature (sub-tool identity). If arg-STRUCTURE features add nothing over the arg-template-tightened baseline, the
thesis is FALSIFIED as mere sub-tool identity recovery → **CLEAN PUBLISHABLE NEGATIVE**. We do not force a positive.

## UNIT OF ANALYSIS
One row per tool CALL (NOT per repeat — that was EXP-0054). Corpora: CC (`~/.claude/projects/*/*.jsonl`) and
Codex (`~/.codex/sessions/**/*.jsonl`), parsed with the EXP-0054 JOIN layer (tool_use→tool_result by id for CC;
function_call→output by call_id for Codex). Sessions with `>= MIN_TRIALS=8` calls retained.

## LABEL (per call, per tool corpus)
`result_tok = len(result)/CHARS_PER_TOK` with `CHARS_PER_TOK = 4.0` (char proxy, identical to EXP-0054).
Within each tool's call set: `thr = result_tok at the 90th percentile rank`; `y = 1 if result_tok > thr else 0`
(strict `>` so boundary ties do not inflate the positive rate). Actual `pos_rate` is reported per tool — NOT
assumed to be exactly 0.10. The label is computed PER TOOL (within-tool top decile); the pooled variant computes
labels per tool then pools rows.

## POWER FLOOR (committee floor)
A tool is "powered" iff `n >= 150 calls` AND both label classes present AND `pos_rate >= 0.02`. Candidate tools:
Bash, Read, Grep, Edit, Write, Glob, Task, WebFetch (+ any tool clearing the floor). We REPORT per-tool `n` and
which tools clear the floor. The HEADLINE gate is evaluated WITHIN each powered tool (the within-tool
non-triviality). We ALSO report a POOLED-across-powered-tools variant (TOOL one-hot in B0), explicitly labeled.

## FEATURES (RE-A2 no-leakage BY CONSTRUCTION: X is derived from `args_str` ONLY; result text NEVER enters X)
**B0 — arg-template-tightened JOINT baseline [FIX-1, the UPGRADE GATE]:**
- `log1p(gap_tok)` — token gap from previous call's end to this call's start (position/cadence)
- `log1p(tool_freq)` — per-session frequency of this tool
- TOOL one-hot — ONLY in the pooled variant (constant within a single tool, dropped there)
- **ARG-TEMPLATE one-hot** — mechanistic sub-tool identity from args:
  - Bash (or any arg with `command`): basename of first shell token (e.g. `git`, `ls`, `python3`, `cat`)
  - Read/Write/Edit/Glob (path-like arg): file extension (`.py`, `.md`, …) or `noext`
  - WebFetch/WebSearch: URL host
  - else: sorted JSON top-level key signature; final fallback: first whitespace token of `args_str`
  - Bucketed to the top-24 templates by within-tool frequency; remainder → `OTHER`.

**B1 = B0 + ARG-STRUCTURE features (pre-execution, `args_str` only), mechanistically motivated by "what makes a
result big":**
- `log1p(arg_char_len)` — longer arg payload
- `path_depth` = count of `/` in args_str — deeper target paths
- `glob_breadth` = count of `*` `?` `{` `[` in args_str — wildcard breadth → more files matched
- `log1p(numeric_max)` — largest integer literal in args (limit/offset/count/-n)
- `n_flags` = count of `-x`/`--x` flag tokens — e.g. `ls -la`, `grep -r`
- `has_pipe` = 1 if `|` or `>` present in args — pipelines/redirects reshape result size

## PRE-REGISTERED RE GATES (frozen)
- **RE-A0 (magnitude floor, NOT load-bearing):** top-decile-result-LENGTH calls carry `>= 50%` of total
  result-prefill tokens (live ref 78.9%). Measured per corpus (all calls) and reported per powered tool. Pass/fail.
- **RE-A1 (LOAD-BEARING KILLER, over the arg-template-tightened JOINT B0):** PASS iff
  `dAUC_LB95 > 0` AND `dAUC_point >= 0.03`, where `dAUC = AUC(B1) - AUC(B0)` from session-clustered 5-fold CV
  held-out scores; LB95 from 2000× session-clustered bootstrap. Evaluated PER powered tool. If `dAUC <= 0` (or
  point `< 0.03`) vs the arg-template-tightened B0 → thesis FALSIFIED as sub-tool identity recovery → CLEAN NEGATIVE.
- **RE-A2 (no-leakage):** features from `args_str` ONLY (pre-execution); result text never in X. By construction;
  asserted in code.
- **RE-A3 (cross-instrument HARD GATE):** replicate on Codex. SIGN AGREEMENT REQUIRED for an overall PASS (CC and
  Codex `dAUC` same sign for the powered tool(s) shared across corpora). Signs disagree → not a robust PASS.
- **RE-A4 (heavy-tail MASS gate, secondary) [FIX-2]:** AUC on a thresholded label discards heavy-tail structure.
  Report BOTH (a) Spearman rank corr of B1 held-out score vs raw `result_tok` (session-clustered bootstrap CI),
  and (b) top-decile MASS-capture lift: fraction of TOTAL result-prefill mass captured by the top-10%-scored calls
  under B1 vs B0.
- **RE-A5 (within-session permutation control) [FIX-3]:** PERMUTE the `glob_breadth` and `path_depth` arg-structure
  features WITHIN each session, re-fit B1, recompute dAUC. If the dAUC SURVIVES within-session permutation, the
  signal is a session-level project-size confound (NOT a within-call pre-execution signal) → kill the causal
  reading. Report permuted dAUC alongside real dAUC.
- **STAT DISCIPLINE:** report fold-to-fold dAUC std across the 5 folds; require ALL 5 folds POSITIVE
  (sign-stability) for a clean PASS. Report Herfindahl index (HHI) of positive-class (whale) result-mass across
  sessions — if `HHI > 0.2`, flag that AUC is dominated by 2-3 sessions (robustness caveat).

## DISPOSITION RULE (decided by RE-A1, gated by A3/A5/stat-discipline)
- **PASS** iff ≥1 powered tool has RE-A1 PASS (`dAUC_LB95>0` AND `dAUC_point>=0.03`) AND all-5-folds-positive
  AND RE-A3 sign-agreement holds for that tool across CC/Codex AND RE-A5 permuted dAUC does NOT survive
  (permuted dAUC point `< 0.03` or `<= 0`).
- **KILL-NEGATIVE** otherwise. The fired gate is named explicitly in `results/analysis.md`.
- A clean negative (B1 adds nothing over arg-template B0) is the EXPECTED outcome and is FIRST-CLASS science.

## FROZEN CONSTANTS
`SEED=20260601  CHARS_PER_TOK=4.0  MIN_TRIALS=8  TOP_DECILE=0.90  POWER_N=150  POWER_POS_FLOOR=0.02
TEMPLATE_TOPK=24  NFOLD=5  NBOOT=2000  L2=1.0  GD_ITERS=400  GD_LR=0.3  A1_POINT_FLOOR=0.03  A0_SHARE_FLOOR=0.50
HHI_FLAG=0.2`

## OSS PRIOR-ART (live-verified arXiv IDs, 2026-06-01T19:11:52Z, via external web search)
The lineage of OUTPUT-LENGTH prediction predicts **MODEL-generated** length from the PROMPT, to schedule decode:
- **S³** "Increasing GPU Utilization during Generative Inference for Higher Throughput" — arXiv **2306.06000**
  (NeurIPS 2023). *Verified.*
- **TetriInfer** "Inference without Interference: Disaggregate LLM Inference for Mixed Downstream Workloads" —
  arXiv **2401.11181**. *Verified.* (predicts response length to disaggregate prefill/decode)
- **SSJF** "Efficient Interactive LLM Serving with Proxy Model-based Sequence Length Prediction" —
  arXiv **2404.08509**. *Verified.* (proxy model predicts output length for speculative shortest-job-first)

Chunked-prefill / prefill scheduling mechanisms chunk AFTER the input tokens already exist (they do NOT predict
a result's size before it is produced):
- **SARATHI** "Efficient LLM Inference by Piggybacking Decodes with Chunked-prefills" — arXiv **2308.16369**.
  *Verified.*
- **Sarathi-Serve** "Taming Throughput-Latency Tradeoff in LLM Inference" — arXiv **2403.02310**. *Verified.*
- **vLLM / PagedAttention** "Efficient Memory Management for Large Language Model Serving with PagedAttention" —
  arXiv **2309.06180**. *Verified.*
- **SGLang / RadixAttention** — LMSYS blog (2024-01-17) + arXiv **2312.07104**. *arXiv ID carried from prior
  PROJ-0009/0010 verification; blog/project verified live, exact ID treated as high-confidence not re-fetched.*

**NON-OVERLAP STATEMENT.** This experiment predicts EXTERNAL TOOL-RESULT length (filesystem/exec output of a
Bash/Read/Grep/… call) from PRE-EXECUTION ARGUMENT STRUCTURE — a quantity set by the environment, not by the
model. This is mechanistically DISTINCT from the S³/TetriInfer/SSJF output-length lineage (model-generated length
from prompt) and from chunked-prefill (vLLM/Sarathi-Serve/SGLang), which chunk tokens that ALREADY EXIST and do
not forecast a not-yet-produced result's size. No fabricated citations; any ID not live-fetched this run is flagged.

## HARD RULES
NEVER fabricate numbers or citations. NEVER force a positive. Pure stdlib only. Honest pass-or-kill.
