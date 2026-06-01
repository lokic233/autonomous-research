# EXP-0051 — PRE-REGISTRATION (LOCKED)  CLAIM-0014 / PROJ-0005 / L0 L1-prep lane
# researcher-0014-L1prep-r5 | prompt v001 | Mac CPU | reuse EXP-0049 venv (transformers 4.57.6, Rust tokenizers)
# LOCKED 2026-06-01T13:00:49Z  — written BEFORE the RE-01 null model is computed (anti-tautology discipline).
# THIS FILE IS LOCKED. No post-hoc edits to the null definition, metrics, or pass rules.
# Satisfies the CPU-doable subset of VERDICT-0055 required_evidence: RE-01, RE-02, RE-05, RE-06.
# RE-03 (real vLLM/SGLang APC counters + TTFT, H100) and RE-04 (deployed-stack regime-(a) prevalence)
#   are EXPLICITLY OUT OF SCOPE here (orchestrator/H100-dispatched). NOT run.

## 0. WHAT EXP-0049 ESTABLISHED (the baseline we extend; verified, not trusted)
- 6215 seams, 2 tokenizers {gpt2, qwen2-0.5b} x 2 corpora {claude_code, codex}, block=16.
- Aggregate: gate-a PASS (mean block-churn 0.0110, CI [0.0100,0.0119]); gate-b PASS (diff vs clean-\n control
  +0.0032, CI [0.0023,0.0041]); gate-c PASS (delimiter AUC 0.724, CI [0.703,0.745]).
- KNOWN HETEROGENEITY (committee's concern): gate-b sign-FLIPS per cell — Qwen2 diff -0.0008, Codex diff -0.0057.
  Aggregate pass is driven by GPT-2 x ClaudeCode. Chat-template control: 95% churn reduction (0.0110 -> 0.0005).

## 1. RE-01 — THE BPE NULL MODEL (LOAD-BEARING; the headline novelty gap)

### 1.1 The question
The observed aggregate seam churn is 0.0110. Is that MORE than you'd get from inserting the SAME tool-result
text by the SAME append operation at a GENERIC byte boundary (no tool-injection delimiter structure)? If observed
== null, the effect is "BPE does BPE" (generic non-associativity) and the tool-seam novelty is an HONEST PARTIAL-KILL.

### 1.2 NULL DEFINITION (LOCKED — chosen before computation)
For each real injection seam (prefix P, tool-result text R) the OBSERVED churn appends R at the TRUE seam (end of P,
preceded by the conversation's actual delimiter). The NULL keeps the SAME R and the SAME single-append operation but
relocates the seam to a RANDOM in-context byte offset, destroying the tool-injection delimiter structure while
preserving merge-table depth + R's own byte distribution:
  - Draw K=5 random offsets off ~ Uniform{20 .. len(P_trunc)} (seed=42, deterministic per-seam stream).
  - NULL cached path   = encode(P_trunc[:off]) ++ encode(R)         (same naive-concat structure as treatment)
  - NULL retokenized   = encode(P_trunc[:off] ++ R)                  (full re-tokenize at the random seam)
  - null_churn(off)    = block-invalidation-fraction(cached, retok)  (SAME chained-block rule, SAME block size)
  - per-seam null_churn = mean over the K offsets.
This isolates: does the tool-seam DELIMITER CLASS cause EXCESS churn beyond appending R at an arbitrary byte?
(Secondary, reported not gated: a length-preserving delimiter-byte-shuffle variant; mechanism-confirmatory only.)

### 1.3 RE-01 METRIC + PASS RULE (LOCKED)
- per-seam delta = observed_seam_churn - per-seam null_churn.
- Cluster/seam bootstrap (B=10000, seed=42) of mean(delta); report point + 95% CI; also report per-cell (3x2) deltas.
- PASS-for-RE01 (novelty survives) = mean(delta) > 0 AND 95% CI EXCLUDES 0 (lower bound > 0), AGGREGATE.
- PARTIAL / HONEST-KILL = CI includes 0 (observed indistinguishable from generic BPE) OR sign-flips per cell.
- We DO NOT force a positive. observed==null is a publishable honest narrowing of the novelty claim.

## 2. RE-02 — 3 TOKENIZERS x 2 CORPORA (break the single-cell confound) [LOCKED]
- Tokenizers: gpt2 (50257), qwen2-0.5b (151643), llama-3-128k (HF "NousResearch/Meta-Llama-3-8B", vocab 128000,
  is_fast=True — VERIFIED reachable+cached this session). Corpora: claude_code, codex. => 6-cell grid.
- Per cell report: n, mean block_churn, churn-minus-clean-\n-control (diff), delimiter AUC, RE-01 delta vs null.

## 3. RE-05 — PER-CELL GATES + MULTIPLE-COMPARISON CORRECTION [LOCKED]
- For EACH of 6 cells evaluate: gate-a (churn CI excludes 0), gate-b (churn>clean-\n control, CI on diff>0),
  gate-c (delimiter AUC CI>0.5). Up to 18 tests.
- Per-test p-value from the bootstrap (two-sided for AUC-vs-0.5 and diff-vs-0; one-sided lower-bound for gate-a>0):
  p = 2*min(frac(boot<=0), frac(boot>=0)) for diff/AUC-0.5 ; for gate-a, p = frac(boot_mean<=0).
- Correction: BOTH Holm-Bonferroni AND Benjamini-Hochberg FDR at alpha=0.05 across the 18 tests (stdlib impl).
- Report which cells survive correction. Honest headline = post-correction survivor count (committee bar:
  "aggregate-only pass while 3/4 cells fail is NOT candidate-grade").

## 4. RE-06 — BLOCK-SIZE SENSITIVITY {8,16,32} [LOCKED]
- Re-chunk the SAME token-ID sequences (no re-tokenization) at block_size in {8,16,32} per cell.
- Report mean block-churn + gate-a/b per block size per cell. Expectation stated a priori: smaller blocks ->
  more blocks, finer granularity -> a single divergent token invalidates a SMALLER fraction's worth of tokens
  but the chained-invalidation suffix count rises; we report the measured monotonicity, no gate flips assumed.

## 5. ENGINEERING INVARIANTS (LOCKED)
- random.seed(42). MAX_PREFIX_CHARS=4096 (carried from EXP-0049 for CPU tractability + comparability).
- Chained block invalidation: first divergent block invalidates all downstream (vLLM parent-hash chain) — verbatim
  from EXP-0049 compute_block_invalidation. Bootstrap = seam-level resample (B per metric as above).
- Production Rust HF fast tokenizers ONLY. Analysis layer pure-stdlib (math/statistics/random). No torch/numpy.
- Determinism check: re-run must reproduce mean churn to 1e-9 (seeded). Corpora live: ~/.claude/projects, ~/.codex/sessions.

## 6. WHAT WOULD FALSIFY EACH SUB-CLAIM (anti-coping)
- "tool-seam churn exceeds generic BPE"  -> falsified by RE-01 delta CI includes 0 (HEADLINE honest kill of novelty).
- "effect generalizes beyond GPT-2 x CC" -> falsified by RE-05: <=2/6 cells survive MC correction on gate-b.
- "block-level fleet impact"             -> falsified if RE-06 shows churn ~0 / >95% blocks survive at all block sizes.
