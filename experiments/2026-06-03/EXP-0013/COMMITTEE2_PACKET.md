# COMMITTEE#2 — CLAIM-0010 (PROJ-0002), WITH GPU L1 data (EXP-0012 L0 + EXP-0013 L1)
## This is the SECOND pass (post-GPU). committee#1 (VERDICT-0011) voted unanimous YELLOW and approved a real-model L1 to (a) test the load-bearing cold-then-hot assumption on REAL traces and (b) clear the A2SF/ArkVale/InfiniGen/Quest prior-art. The L1 is now in. Cast your FINAL vote on the claim WITH this evidence. The engine enforces real 6/6 by role; a GREEN/promote requires unanimous green. This L1 reports a clean pre-registered REFUTED — vote honestly (a well-evidenced kill is the correct outcome here; do not manufacture a green, do not punish honest negatives).

## L1 KEY FINDINGS (real Qwen2.5-1.5B, real eager attention, 806 spans, 40 seeds, pre-registered):
1. LOAD-BEARING TEST: cold-then-hot delayed-callback frequency = 0.000 (threshold >=15% meaningful, <5% rare) in BOTH easy AND a design built hostile to H2O. The critical handle span is a HEAVY-HITTER from commit, attention rank rises monotonically 0.50->1.00. It is hot at callback (real) but NEVER cold. PREMISE FAILS.
2. Real future-ref AUC: H2O accumulated attention = 0.999/0.819 overall, 1.000 critical-handle. Lexical proxy = 0.857/0.647 (WEAKER). The L0's 'H2O crit AUC~0, proxy wins' is INVERTED in reality.
3. Real pass@1 at matched KV budget: CAUSAL - H2O = +0.00 [CI 0,0] at every budget, both designs. H2O retains the heavy-hitter; only recency-truncation loses (the strawman VERDICT-0009 already flagged).
4. Prior-art: A2SF (same biased-attention diagnosis), ArkVale (recallable KV via query geometry, no lexical signal), Quest, Apple 'Learning to Evict' (identical 'past-attention is only an indirect proxy for FUTURE value' framing). Scissorhands persistence-of-importance is CONFIRMED by our data — the claimed counterexample is gone.
All 4 pre-registered honest-negative branches (N1-N4) triggered. The L0 win was an artifact of engineered sim structure absent from real LLM attention.

## CLAIM
claim: "For long-horizon tool-calling agents, a CAUSAL retention policy that predicts\
  \ which committed tool-result spans will be re-referenced \u2014 using only a NOISY,\
  \ realizable past-signal proxy (decayed past-attention mass / repeat-substring hits,\
  \ NOT the ground-truth reference process) with realistic span-boundary detection\
  \ error \u2014 achieves a strictly better context-length / task-success Pareto than\
  \ (a) recency-truncation AND (b) attention-based KV eviction (H2O/SnapKV-style),\
  \ on traces where the predictor's future-reference AUC is measured (not assumed),\
  \ with the win surviving when predictor AUC is realistically imperfect (<0.85)."
why_it_matters: 'VERDICT-0009 RED''d CLAIM-0008 because its L0 was CIRCULAR (predictor

## FULL L1 RESULTS (EXP-0013)
# RESULTS — EXP-0013 (L1, CLAIM-0010, PROJ-0002) — researcher-gpu-0013
Node: devgpu014 (NVIDIA H100, 1 GPU, CUDA_VISIBLE_DEVICES=0). Model: **Qwen/Qwen2.5-1.5B-Instruct**
via HuggingFace `transformers` 5.9 (torch 2.11+cu130), `attn_implementation="eager"`, `output_attentions=True`
(NOT vLLM — we need raw per-head attention weights). Real tokenizer, real Qwen chat template, real
tool_call/tool_response role formatting. 40 seeds × 2 trace designs = 806 tool-result spans, 960 pass@1 cells.
On-disk: results/{coldhot,auc_rows,pass}.{json,csv}, results/PRIOR_ART.md. Repro: `bash runwrap.sh full.py 40`.

## VERDICT: **REFUTED** (honest negative — the load-bearing assumption is FALSE in real LLM traces)
The single load-bearing premise of CLAIM-0010 — that committed tool-result spans exhibit **delayed
cold-then-hot callbacks** (low accumulated attention shortly after commit, so H2O evicts them; hot only
many turns later) — **does not occur** in real Qwen2.5-1.5B tool-agent traces. Measured frequency = **0.000**.
The critical callback handle span is a **heavy-hitter from the moment of commit and stays one**, so H2O's
real accumulated attention **retains it** and the entire claimed edge over H2O vanishes. This is the
pre-registered honest-negative branch (N1 ∧ N2 ∧ N3), and it ends the claim cleanly.

## METHOD (real agent traces, real attention)
ReAct-style multi-tool sessions: agent must recall a HANDLE (id/path) committed by an EARLY tool result
and report it at the end (intrinsic delayed callback — the answer requires the early handle). Two designs:
- **easy**: 6–8 tool rounds, handle flagged "primary".
- **hard** (adversarial-to-H2O): 13–17 tool rounds, handle BURIED deep inside a 329-token verbose result,
  surrounded by competing decoy IDs, never flagged primary — deliberately engineered to be LOW-salience at
  commit to give the cold-then-hot hypothesis its best possible chance.
Full transcript → one forward pass with eager attention. Per tool-result span we compute **accumulated
attention** (sum over span key-tokens, mean over heads, mean over mid+late layers = layers 14–27) received
from each successive query token. This is the SAME signal used as the H2O eviction score AND a predictor
input (required_evidence #2). "Cold" = bottom-half attention rank among live tool spans in the 2 turns after
commit; "Hot later" = top-quartile rank ≥2 query-steps later.
No benchmark was installable offline (no tau-bench/AppWorld present; egress is fwdproxy-gated, pip offline);
we STATE we used constructed-but-realistic real-agent transcripts driven through the real LLM with real
attention — the structure being tested (cold-then-hot) is MEASURED, never injected.

## (1) *** THE LOAD-BEARING TEST — cold-then-hot frequency in REAL traces ***
| design | spans | cold_then_hot frac | crit cold_early | crit hot_later | crit mean early_rank |
|---|---|---|---|---|---|
| easy | 242 | **0.000** | 0.000 | 1.000 | 0.750 |
| hard | 564 | **0.000** | 0.000 | 1.000 | 0.750 |
**Pre-registered threshold: ≥15% = meaningful, <5% = rare. Observed = 0.0%.** RARE → premise FAILS.
The critical span is HOT at the callback (hot_later=1.0 ✓ — the callback is real) but is NEVER cold:
its attention rank rises **monotonically 0.50→1.00** as the conversation grows (per-turn trace in
logs/diag_hard.log). Mechanism: the first tool result absorbs a large attention spike at commit
(~0.12–0.16 mass) and, as later decoy spans are added, the older critical span stays comparatively
high because decoys get even less. Real LLM attention does the OPPOSITE of the engineered L0 structure.

## (2) Real future-reference AUC (H2O accumulated attention vs lexical/decayed proxy)
| design | OVERALL: H2O | decayed | lex-proxy | CRIT-ID: H2O | lex |
|---|---|---|---|---|---|
| easy | **0.999** | 0.996 | 0.857 | **1.000** | 1.000 |
| hard | **0.819** | 0.819 | 0.647 | **1.000** | 1.000 |
H2O's real accumulated attention is a NEAR-PERFECT future-reference predictor and **perfectly identifies
the critical handle span (AUC 1.000)**. The noisy lexical proxy CLAIM-0010 relies on is the WEAKER signal
(0.86/0.65). The L0's claim "H2O critical-handle AUC ≈ 0, proxy wins" is INVERTED in real traces.

## (3) End-to-end pass@1 at matched KV budget (crit span retained ⇒ answer recoverable)
| design | budget_frac | CAUSAL | H2O | SnapKV | RT | CAUSAL−H2O 95%CI |
|---|---|---|---|---|---|---|
| easy | 0.3 | 1.00 | 1.00 | 0.62 | 0.00 | +0.00 [0,0] |
| easy | 0.5/0.7 | 1.00 | 1.00 | 1.00 | 0.00 | +0.00 [0,0] |
| hard | 0.3 | 0.03 | 0.03 | 0.00 | 0.00 | +0.00 [0,0] |
| hard | 0.5/0.7 | 1.00 | 1.00 | 1.00 | 0.00 | +0.00 [0,0] |
**CAUSAL gives ZERO advantage over H2O at every budget (CI=[0,0]).** H2O retains the critical span because
it is the heavy-hitter. The only loser is recency-truncation (RT=0.00 — it evicts the early handle), which
is exactly the strawman VERDICT-0009 already flagged. At the tightest hard budget (bf=0.3) BOTH CAUSAL and
H2O fail equally (0.03) — the lexical signal buys nothing because H2O already ranks the span #1; they pick
the same span. SnapKV (last-window attention) under-retains at tight budget but never below H2O on the chain.

## (5) GRADED vs binarized callback retention
L0 claimed H2O retains 0.00 of the critical callback (binarized all-or-nothing). REAL graded H2O crit-span
retention: 1.00 at bf≥0.5 (both designs) and bf=0.3-easy; 0.03 only at bf=0.3-hard (where CAUSAL also = 0.03).
The "H2O = 0" gap the L0 leaned on is an artifact of the engineered sim; it is 1.00 in real traces.

## (6) Sensitivity
- Real lexical handle-recurrence hit rate on crit spans = **1.000** (L0 assumed 0.80). The handle IS present
  and recurs — but it is **REDUNDANT with H2O**, which already ranks the span #1. A perfect lexical signal
  adds no retention because H2O is not making the error the claim assumed.
- Span-boundary error (L0 asserted 10%): cold_then_hot = 0.000 across 806 spans with comfortable rank margin
  (crit early_rank ≥0.5); not boundary-sensitive. ±1-message jitter cannot manufacture a cold phase.

## (4) Prior-art sweep (real abstracts fetched, results/PRIOR_ART.md)
Even setting the empirical refutation aside, the residual novelty is subsumed:
- **A2SF (2407.20485)**: same "accumulated attention is a biased importance signal" diagnosis (adds forgetting factor).
- **InfiniGen (2406.19707) / Quest (2406.10774)**: same class — predict future KV importance from a cheap proxy; query-aware (Quest) recovers cold-then-hot WITHOUT a lexical signal.
- **ArkVale (NeurIPS24)**: *recallable* KV eviction — explicitly evicts then RECALLS spans that become hot later. Directly solves the (nonexistent) cold-then-hot problem via query geometry, no lexical handle needed.
- **"Learning to Evict from KV Cache" (Apple, 2602.10238)**: identical framing — "past-attention/recency are only INDIRECT proxies for a token's FUTURE value" — and learns future value directly.
- **Scissorhands (2305.17118) persistence-of-importance**: our data CONFIRMS persistence (rank rises, never drops) rather than refuting it — removing CLAIM-0010's claimed counterexample.
Residual differentiator (lexical handle-recurrence on tool-result spans) is thin AND moot given (1)–(3).

## HONEST BOTTOM LINE
Across 806 real tool-result spans in real Qwen2.5-1.5B agent traces — including a design deliberately built
to be hostile to H2O — the cold-then-hot delayed-callback structure occurs at **0%** frequency. Real LLM
attention treats early task-critical handles as persistent heavy-hitters, so H2O retains them and the noisy
causal predictor's advantage (the entire contribution of CLAIM-0010) **does not exist in real traces**.
This is a clean, pre-registered REFUTATION of the load-bearing assumption. Recommend **WEAKEN→KILL**.

## Resources
~12 min wall, <0.05 GPU-h (load 1.5s, ~0.6s/seed). 1 GPU. Peak GPU mem ~6GB. No orphan procs (nvidia-smi clean).

## L1 PRE-REG (committed pre-run)
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

## committee#1 verdict for reference: VERDICT-0011 yellow (unanimous, required this exact L1 validation).
