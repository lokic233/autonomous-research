# PRE-REGISTRATION — EXP-0013 (L1, CLAIM-0010, PROJ-0002)
researcher-gpu-0013 | node devgpu014 (8×H100) | model: Qwen/Qwen2.5-1.5B-Instruct (HF transformers, eager attn, output_attentions=True)
TASK-0012 | committee-approved VERDICT-0011 (unanimous 6/6 YELLOW)
Pre-registered BEFORE running. Honest pipeline — a negative result is a WIN.

## What L0 (EXP-0012) established and what it ENGINEERED
L0 PARTIAL-HELD: a noisy causal predictor (0.55·ngram_hit + 0.45·decayed_past_attn + noise) beats
H2O/SnapKV on the task-chain metric ONLY because H2O scores 0.000 — it evicts "delayed cold-then-hot
callback" tool-result spans (low accumulated attention shortly after commit, hot only many turns later).
BUT L0 *engineered* this cold-then-hot structure into the generative trace model. The committee's #1
required_evidence: DOES THIS STRUCTURE ACTUALLY EXIST IN REAL TOOL-AGENT TRACES?

## THE LOAD-BEARING HYPOTHESIS (H1) — pre-registered
On real multi-step tool-agent traces run through a real LLM (Qwen2.5-1.5B-Instruct), committed
tool-result spans exhibit DELAYED COLD-THEN-HOT callback structure at MEANINGFUL frequency:
a non-trivial fraction of tool-result spans receive LOW accumulated attention in the K turns right
after commit (so H2O would evict them at that budget) but receive HIGH attention many turns LATER.

### Pre-registered decision rule (operationalized)
- "Span": token range of a single committed tool-result (real tool-call formatting via Qwen chat template tool role).
- "Accumulated attention" of a span at decode step t = sum over span key-tokens of attention mass
  received from the current query token, averaged over heads, summed over a chosen layer set
  (report mid+late layers; also report all-layer). This is the SAME signal used as the H2O eviction
  score AND as a predictor input (per required_evidence #2).
- "COLD at commit-window" = span's accumulated-attention rank is in the BOTTOM half (would be evicted
  by H2O at budget_frac≈0.5) during the window of K=2 turns immediately after the span is committed.
- "HOT later" = at some turn ≥ commit_turn + DELAY (DELAY≥3 turns), the span receives attention in
  the TOP quartile of currently-live spans (i.e., it is re-referenced).
- "cold-then-hot fraction" = (# tool-result spans that are COLD-at-commit AND HOT-later) / (# tool-result spans).

### HONEST-NEGATIVE BRANCH (pre-committed, report any of these as the answer):
(N1) If real traces do NOT exhibit cold-then-hot delayed callbacks at meaningful frequency
     (pre-registered threshold: meaningful = ≥15% of tool-result spans; rare = <5%), the claim's
     premise FAILS → report NEGATIVE, recommend WEAKEN/KILL.
(N2) If H2O's REAL accumulated attention ALREADY attends strongly to handle/ID tokens AT COMMIT TIME
     (so those spans are NOT cold when evicted — H2O catches them), the gap over H2O collapses →
     report NEGATIVE.
(N3) If the noisy causal predictor (ngram/handle recurrence + decayed past-attn) does NOT beat H2O on
     real future-reference AUC for critical-handle refs (CI_lo ≤ 0), OR does not beat H2O/SnapKV/RT on
     real pass@1 at matched KV budget → report NEGATIVE.
(N4) If prior art (A2SF / ArkVale / InfiniGen / Quest) already subsumes the tool-result-span +
     lexical-handle-recurrence slice → novelty kill, report it.

## METHOD (pre-registered)
1. TRACES: Construct realistic ReAct-style multi-tool agent transcripts with a REAL agent loop driving
   Qwen2.5-1.5B-Instruct (real tokenizer, real chat template, real tool-call/tool-result role formatting).
   Tools return verbose results containing identifiers/handles (file paths, IDs, ticket numbers, hashes)
   that the task later requires re-referencing (callback). Multi-step (≥6 tool calls/session), multiple
   sessions/seeds. STATE exactly which (no offline benchmark assumed installable; will state tau-bench
   availability). The CALLBACK requirement is task-intrinsic (the final answer needs an earlier handle),
   NOT injected into attention — we MEASURE whether attention goes cold-then-hot, we do not force it.
2. ATTENTION: extract real per-step attention; compute per-span accumulated attention as above.
3. #1 cold-then-hot frequency measurement (graded + binarized).
4. AUC: real future-reference AUC of (a) noisy proxy, (b) H2O past-attention — separately for OVERALL
   refs and CRITICAL-HANDLE (delayed-callback) refs. Bootstrap CI over spans/seeds.
5. pass@1 at matched KV budget: CAUSAL-retention vs H2O vs SnapKV vs recency-truncation (RT). Eviction
   applied to the real KV cache (or simulated by masking evicted spans' keys), decode the final answer,
   exact-match against the required handle. Matched budget_frac sweep.
6. Prior-art sweep: fetch ≥2 sources (arxiv egress confirmed) on A2SF/ArkVale/InfiniGen/Quest/ACON/
   Scissorhands/H2O/SnapKV; report whether any subsumes tool-result-span + lexical-handle slice.
7. Sensitivity: real n-gram/handle hit rate (L0 assumed 0.80), real span-boundary detection error (L0 asserted 10%).

## BUDGET / SAFETY
≤120 min wall, ≤2 GPU-h, 1 GPU (CUDA_VISIBLE_DEVICES=0). Bounded memory; clean GPU procs at end; watch host RAM.

## PRIMARY OUTCOME
The answer to #1 (cold-then-hot frequency in REAL traces) is the single load-bearing result. Everything
else is conditional on it. If it's rare, the claim ends cleanly — and that is a WIN.
