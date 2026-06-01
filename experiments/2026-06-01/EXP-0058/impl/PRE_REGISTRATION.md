# EXP-0058 PRE-REGISTRATION — Multi-Tool Batch Admission Mis-Estimation (PROJ-0012 / CLAIM-0023)

**LOCKED (UTC):** `2026-06-01T20:52:44Z`  (committed via `ros commit` BEFORE the main measurement run)
**Agent:** researcher-0023-L0-r7  | **Sub-monitor:** sub-monitor-0012-r7 | **prompt_version:** v001
**Reuses (VERBATIM, imported not re-implemented):** EXP-0055 `whale_prefill_predict.py`
(`auc`, `standardize`, `logistic_fit`, `logistic_pred`, `det_hash`, `canon_args`, `block_text`, `spearman`,
`mass_capture`, `load_corpus`, `parse_codex_session`) and the session-clustered 5-fold CV + 2000x
session-clustered bootstrap dAUC pattern from EXP-0055/0056.

This document FREEZES every metric, threshold, and PASS/KILL decision rule. No threshold may change after this lock.
A clean NEGATIVE is a FIRST-CLASS publishable result. NO gate threshold will be moved to manufacture a PASS.

---

## 0. DESIGN-PHASE GATE RESOLUTIONS (BINDING — resolved with live evidence BEFORE the run)

### FIX-1 — STRAWMAN RESOLUTION (systems_reviewer RED). RESOLVED.
**The strawman to avoid:** shipping vLLM exposes `max_num_batched_tokens` and Sarathi-Serve (arXiv **2403.02310**,
"Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve" — live-verified 2026-06-01) chunks prefill
**by tokens AFTER the payloads exist**. So an admission decision that already knows result token lengths does NOT need a
pre-execution arg-structure oracle. If our "batch" decision happened after results returned, the project would be a
strawman.

**The honest, count-driven, PRE-EXECUTION decision point we establish empirically (live corpus probe, this corpus):**
When an agent emits **parallel tool calls**, the model streams out N `function_call`/`tool_use` items in ONE assistant
turn, **before any tool result text exists**. The agent-runtime / orchestrator must then admit & dispatch that co-issued
batch of N calls. At that instant the result token lengths are genuinely **unknown** (the tools have not run), so the only
information available is the **call COUNT and the call ARGUMENTS**. Budgeting/admitting the batch by call COUNT is the
naive default; a pre-execution **arg-structure oracle** is the proposed improvement. This is the orchestrator-side batch
DISPATCH-sizing decision point named in the charter's FIX-1 reframe, and it is genuinely pre-execution.

**Empirical proof that a genuine co-issued (pre-execution) batch exists in this corpus (Codex):**
- 60.0% of consecutive `function_call` runs have length >= 2 (713 / 1189 runs), i.e. the model emits >= 2 tool calls
  with **NO `function_call_output` in between** — all calls are emitted before any result returns.
- Within a co-issued run, the median timestamp gap between consecutive `function_call` events is **0.001 s** (1 ms),
  p90 = 0.075 s (n = 1713 gaps). This is co-emission inside one model response, not sequential round-trips.
- Cite/disclaim overlap axis (FIX-6): DynaServe (arXiv **2504.09285**, "DynaServe: Unified and Elastic Execution for
  Dynamic Disaggregated LLM Serving" — live-verified 2026-06-01) handles general length heterogeneity, NOT the
  count!=total claim for a co-issued tool batch; Sarathi-Serve/vLLM chunk AFTER tokens exist. Distinct from
  PROJ-0009/DEAD-0018 (per-call WITHIN-tool whale, no count confound). The output/input-length-prediction-for-scheduling
  line (S3 / TetriInfer / SSJF) predicts MODEL-generated length, not tool-RESULT batch mass.

### FIX-4 — VERIFY CO-ISSUED PARALLEL CALLS PER INSTRUMENT (HARD, no silent waiver). RESOLVED.
Live probe of BOTH corpora (this corpus, 2026-06-01):
- **Codex** (`~/.codex/sessions/**/*.jsonl`): genuine co-issued parallel calls EXIST (see FIX-1 numbers). Codex is the
  parallel-batch instrument.
- **Claude Code** (`~/.claude/projects/*/*.jsonl`): **ZERO** co-issued parallel tool calls in this corpus.
  Every assistant message carries exactly ONE `tool_use` (dist {1: 2554}); every user message carries exactly ONE
  `tool_result` (dist {1: 2555}). CC turns are strictly sequential single-call round-trips. The design committee's CC
  "50% multi-call burst / 75.7% top-decile mass" figures were computed by **stream-offset adjacency (gap<5 tok)
  clustering of SEQUENTIAL calls** — those clusters are NOT co-issued batches and using them as the unit would be exactly
  the FIX-1 strawman.

**Binding consequence (declared honestly, NOT a WAIVED-WITH-FLAG escape):** the co-issued parallel-batch claim is
**SINGLE-INSTRUMENT (Codex) BY DESIGN** for this corpus, because CC emits no parallel calls. The CC stream-offset
"bursts" are reported ONLY as a labelled NEGATIVE CONTROL / context (sequential, not co-issued); they are excluded from
the RE-B2 / RE-B2b parallel-batch killer. The cross-instrument HARD GATE **RE-B5 is reported NOT-SATISFIABLE
(single-instrument-by-design)** with the CC probe as the stated reason. RE-B5 cannot contribute a PASS and is NOT waived.

---

## 1. CORE DEFINITIONS (frozen)
- **Token proxy:** tokens = chars / 4.0 (`CHARS_PER_TOK = 4.0`). All gate metrics are ratios or thresholds far from the
  constant, so the proxy cancels / is robust.
- **Session** = one jsonl file. Min length filter: a session must contain `>= 8` tool calls (`MIN_TRIALS = 8`).
- **Co-issued batch (Codex, FROZEN unit):** walking events in FILE/EMISSION order, a batch = a **maximal run of
  consecutive `function_call` events with NO `function_call_output` between them**, within one session (call_id /
  message co-occurrence per FIX-4). Each call in the run is joined to its `function_call_output` by `call_id` (dedup by
  call_id, EXP-0054 neutralizer) to obtain its result text. A batch's calls were ALL emitted before ANY of their results
  existed -> the decision point is genuinely pre-execution.
- **Multi-call batch:** a co-issued batch with `size >= 2`. The RE-B2 / RE-B2b unit is each multi-call batch.
- **batch_total_tok** = sum over the batch's calls of `len(result_text)/4.0` (the joint prefill mass that hits the
  scheduler when the co-issued results return together).
- **whale_label** = 1 iff `batch_total_tok` is strictly above the 90th-percentile of `batch_total_tok` across all
  multi-call batches in that corpus (top decile).
- **Robustness batch def (diagnostic, not a gate):** also recompute the primary RE-B2 dAUC under a stricter co-issued
  definition requiring every within-run consecutive timestamp gap `< 1.0 s`. Reported for transparency; the frozen unit
  is the run-before-output definition above.

## 2. FEATURES (all from args_str ONLY -> RE-B3 no-leakage BY CONSTRUCTION; NO result text in X)

### 2a. Per-CALL pre-execution arg features (from `args_str` only)
For each call: `f = [log1p(arg_tok_len), path_depth(#"/"), glob_count(#`*?{[`), log1p(numeric_max),
has_numeric_limit(0/1), bash_io_flags(# of head|tail|>|>>|"| ")]`. (`arg_tok_len = len(args_str)/4`;
`numeric_max` = max integer literal in args; `has_numeric_limit` = 1 if any integer literal present.)

### 2b. Per-CALL whale predictor -> matched-max-per-call (FIX-2, leakage-safe)
Per-call label = top-decile per-call `result_tok` (within the corpus's batched calls). Fit a session-clustered 5-fold
logistic on the 2a per-call features; emit held-out per-call whale-probability `p_call` (each call scored by a model NOT
trained on its own session). `matched_max_per_call(batch) = max(p_call over the batch's calls)`;
`matched_sum_per_call(batch) = sum(p_call)`. These are pre-execution (args only).

### 2c. Per-BATCH baseline B0 (the JOINT baseline with ALL committee guards)
`B0 = [ log1p(size), log1p(mean_gap_tok), log1p(mean_freq), tool_mix one-hot (top-K tools + OTHER),
        tool-PAIR interaction one-hot (top-K unordered pairs present in the batch),
        tool-TRIPLE interaction one-hot (top-K unordered triples present),
        matched_max_per_call, matched_sum_per_call ]`.
`mean_gap_tok` = mean inter-call stream gap inside the batch; `mean_freq` = mean over calls of the call's tool frequency
in the session. (`TOPK_TOOL=12`, `TOPK_PAIR=16`, `TOPK_TRIPLE=12`.)

### 2d. Per-BATCH augmented B1
`B1 = B0 + joint arg-structure = [ max AND sum over the batch's calls of EACH 2a per-call feature ]`
(12 added continuous features: max/sum of {arg_tok_len, path_depth, glob_count, numeric_max, has_numeric_limit,
bash_io_flags}). These are the "cheap pre-execution joint-argument" features under test.

## 3. ESTIMATION (frozen, reused verbatim)
- Logistic regression, pure-stdlib batch GD, L2 = 1.0, `GD_ITERS=400`, `GD_LR=0.3`, standardized continuous features.
- AUC = Mann-Whitney rank statistic on pooled **session-clustered 5-fold** held-out scores (fold = `det_hash(session)%5`;
  a session never crosses train/test).
- `dAUC = AUC(B1) - AUC(B0)`. 95% CI via **session-clustered bootstrap** (resample sessions w/ replacement, `NBOOT=2000`,
  recompute dAUC on pooled held-out scores). `SEED=20260601`.

---

## GATES — exact metric, threshold, PASS/KILL (ALL FROZEN)

### RE-B0 — MAGNITUDE FLOOR
- Multi-call batch fraction (of all co-issued runs) `>= 25%` **AND** top-decile batches carry `>= 50%` of total
  batched-prefill mass. **KILL** (clean) if batches small/uniform.

### RE-B1 — COUNT-INSUFFICIENCY (anti-tautology)
- Spearman(`size`, `batch_total_tok`) over multi-call batches `< 0.30` (`B1_SPEARMAN_MAX`) **AND** size-only whale-AUC
  `<= 0.60` (`B1_SIZE_AUC_MAX`; size-only logistic, session-clustered CV). PASS = budget-by-count genuinely fails.
- **Premise-kill (honest):** if `size` DOES predict total (Spearman `>= 0.30` or size-only AUC `> 0.60`), the premise is
  wrong -> KILL (budget by count works).

### RE-B2 — LOAD-BEARING KILLER (B1 over the JOINT B0)
- Unit = each multi-call batch. **PASS iff** `dAUC_LB95 > 0` AND `dAUC_point >= 0.03` (`B2_DAUC_FLOOR`) AND
  **all 5 folds' dAUC > 0**.
- `<= 0` -> batch total is unpredictable from joint args given count+mix+pair/triple+matched-max/sum-per-call ->
  **CLEAN NEGATIVE** ("budget chunked-prefill by call count; pre-execution batch-cost oracles add nothing").

### RE-B2b — MATCHED-COUNT + DECOMPOSITION (UPGRADE GATE + EARLY-KILL, FIX-2)
- (a) **Per-size-stratum AUC:** within each batch-size stratum (size = 2,3,4,>=5) with `>= 20` batches, B1 still
  separates whale vs non-whale (held-out AUC `> 0.5`). Report per stratum.
- (b) **DECOMPOSITION vs the max-of-per-call null:** `AUC_maxnull` = AUC of `matched_max_per_call` ALONE predicting the
  batch whale. The joint-arg model must BEAT this null: define `dAUC_decomp = AUC(B1) - AUC_maxnull`.
- **EARLY-KILL TRIGGER (FIX-2, IMMEDIATE TERMINATION):** FIRES iff RE-B2 fails (`dAUC_LB95 <= 0` OR `dAUC_point < 0.03`
  OR not all-folds-positive) **i.e. the joint-arg features add nothing beyond B0's matched-max/sum-per-call** — the batch
  whale reduces to max(independent per-call whales) and the batch axis collapses to the already-killed per-call axis
  (DEAD-0018 re-skin). When it fires, disposition = **EARLY-KILL-DEAD-0018-RESKIN** and the run terminates the claim.
  (`dAUC_decomp <= 0` is the corroborating decomposition statistic, reported alongside.)

### RE-B3 — NO-LEAKAGE
- All X features derive from `args_str` ONLY (pre-execution). NO result text enters X. BY CONSTRUCTION.

### RE-B4 — HEAVY-TAIL MASS GATE
- Lorenz/Gini lift: fraction of total batched-prefill MASS captured in the top-10% **predicted** batches, B1 vs B0
  (`masscap_B1 - masscap_B0`). Descriptor; reported, not a standalone PASS/KILL.

### RE-B5 — CROSS-INSTRUMENT HARD GATE (FIX-4)
- **NOT-SATISFIABLE — SINGLE-INSTRUMENT (Codex) BY DESIGN.** CC emits zero co-issued parallel calls in this corpus
  (probe in FIX-4). Declared honestly; RE-B5 cannot contribute a PASS and is NOT waived. Reported with the CC probe.

### STAT DISCIPLINE (FIX-5)
- Report fold-to-fold dAUC std, ALL 5 folds' signs, and **Herfindahl/effective-n** of positive-class (whale) batch mass
  after session-clustering AND after size-stratification on the binding n. If a handful of batches/sessions drive the AUC
  (HHI `> 0.20`, `HHI_FLAG`) -> flag **YELLOW not GREEN**.

---

## OVERALL DISPOSITION (frozen decision tree)
1. **EARLY-KILL-DEAD-0018-RESKIN** (FIX-2 fired): RE-B2 fails (dAUC adds nothing over matched-max/sum-per-call B0).
   Batch whale = max(per-call whale) -> immediate termination, `result_effect = kill`.
2. **CLEAN-NEGATIVE-KILL:** RE-B0 fails (batches small/uniform) OR RE-B1 premise-kill (size predicts total) OR RE-B2
   `dAUC_LB95 <= 0`. `result_effect = kill`. First-class negative.
3. **PASS-to-committee (single-instrument-flagged, at most YELLOW):** RE-B0 PASS AND RE-B1 PASS AND RE-B2 PASS
   (dAUC_LB95>0, point>=0.03, all-folds-positive) AND RE-B2b not-collapsed (per-stratum AUC>0.5, dAUC_decomp>0).
   Because RE-B5 is single-instrument-by-design and STAT may flag HHI, the ceiling is YELLOW/PASS-WITH-FLAG, never a
   clean GREEN. `result_effect = advance`. Sub-monitor forwards; this agent does NOT convene committee.

## OUTPUTS
- `experiments/2026-06-01/EXP-0058/impl/batch_admission_census.py`
- `experiments/2026-06-01/EXP-0058/results/summary.json`
- `experiments/2026-06-01/EXP-0058/analysis.md` (per-gate verdicts + RE-B2b decomposition + FIX-2 early-kill status +
  Codex single-instrument disposition + stat discipline + clear DISPOSITION)
