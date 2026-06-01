# EXP-0051 Results Analysis — researcher-0014-L1prep-r5
# CLAIM-0014, PROJ-0005, Level-0, CPU-only | prompt_version v001 | extends EXP-0049
# Satisfies CPU-doable VERDICT-0055 required_evidence: RE-01, RE-02, RE-05, RE-06.
# OUT OF SCOPE (orchestrator/H100-dispatched, NOT run): RE-03 (real vLLM/SGLang APC counters + TTFT, H100), RE-04 (deployed regime-(a) prevalence).

## REFRAMED ABSTRACT (proposed map_delta — VERDICT-0055 map_delta_proposals)

**Title (proposed):** *"Delimiter-conditioned BPE boundary churn under non-templated retokenization (regime-(a) only):
a characterization — and why it is smaller than generic BPE perturbation and largely template-preventable."*

Injecting a tool result into an ongoing agent context and re-tokenizing the full prompt (regime (a)) perturbs BPE
token boundaries at the injection seam, demoting a fraction of exact-prefix KV-cache blocks (vLLM APC / RadixAttention
block hash) from HIT to MISS. Across 3 production Rust tokenizers {GPT-2, Qwen2-0.5B, Llama-3-128k} x 2 agent-trace
corpora {Claude Code, Codex} (6409 seams, block=16), the phenomenon is REAL but SMALL and NON-GENERALIZING:
mean block-churn 1.16% aggregate (~99% of blocks survive). Three findings re-frame it away from a fleet-impact claim:
(1) **It is SMALLER than generic BPE churn.** A pre-registered BPE null model — the SAME tool-result text appended at a
RANDOM in-context byte offset (generic, no tool-seam delimiter) — yields 5.17% churn, i.e. **4.0 points MORE** than the
real seam (delta = -0.040, 95% CI [-0.0414, -0.0386], negative in ALL 6 cells). Tool-injection seams land on
BPE-friendly boundaries (newlines, JSON braces) and are therefore *more benign* than arbitrary insertions; the
"tool seams cause EXCESS churn" novelty is an **honest partial-kill**. (2) **It does not generalize across corpora.**
The anti-tautology gate-b (churn > clean-\n control) survives multiple-comparison correction in 3/6 cells — exactly the
three Claude-Code cells; ALL three Codex cells fail or reverse (Codex tool-result churn ~0.09%, control exceeds
treatment). The aggregate gate-b pass is a corpus artifact (Claude Code), not a tokenizer-general effect.
(3) **It is ~96% chat-template-preventable** (0.0116 -> 0.0005 with a `<|tool_result|>` special-token delimiter).
Net: a delimiter-conditioned, model-free-predictable (AUC 0.63-1.00) but small, corpus-bound, template-mitigated,
regime-(a)-only characterization — NOT a candidate-grade fleet-cost mechanism.

---

## PER-RE DISPOSITION (honest)

### RE-01 — BPE NULL MODEL — **PARTIAL-KILL of the novelty (load-bearing)**
- observed mean block-churn (block16) = 0.011597; random-offset NULL = 0.051661.
- delta (observed - null) = **-0.040065**, 95% bootstrap CI [-0.041444, -0.038626] (B=10000, seed=42).
- NEGATIVE and CI-excludes-0 in ALL 6 cells (gpt2/qwen2/llama x cc/codex), delta range -0.025 .. -0.060.
- **VERDICT:** The pre-registered RE-01 PASS condition (observed > null, CI lower bound > 0) is NOT met; the *reverse*
  is significant. Tool-result injection seams produce LESS boundary churn than the same text inserted at an arbitrary
  byte. INTERPRETATION: real tool seams follow clean delimiters (newline / `}` / `]`) that BPE tokenizes stably,
  whereas random offsets routinely split mid-token. This is the headline honest result the committee asked for: the
  "excess churn over a textbook BPE baseline" claim does not hold; the seam structure is benign-to-protective.
  (We do NOT force a positive — per pre-registration sec 6 this falsifies "tool-seam churn exceeds generic BPE".)

### RE-02 — 3 TOKENIZERS x 2 CORPORA — **DELIVERED; effect is corpus-bound, not tokenizer-general**
- Full 6-cell grid run with production Rust tokenizers incl. Llama-3-128k (NousResearch/Meta-Llama-3-8B, vocab 128000,
  is_fast=True). Per-cell mean churn (block16):
    gpt2: cc 0.0104 / codex 0.0056 ;  qwen2: cc 0.0204 / codex 0.0009 ;  llama-3: cc 0.0204 / codex 0.0009.
- Llama-3 tracks Qwen2 (both large-vocab): HIGHER churn than GPT-2 on Claude Code (~0.020 vs 0.010) but near-ZERO on
  Codex (~0.0009). Adding Llama-3 does NOT rescue generalization; it CONFIRMS the corpus split. The EXP-0049
  "Qwen2 underperforms" observation is now correctly attributed: the real axis is **corpus (Codex collapses), not
  tokenizer**. Delimiter AUC: gpt2 0.98-0.999 (strong), qwen2/llama 0.63 cc / ~1.0 codex.

### RE-05 — PER-CELL GATES + MULTIPLE-COMPARISON CORRECTION — **DELIVERED; gate-b 3/6 post-correction**
- 18 tests (6 cells x {gate-a churn>0, gate-b churn>control, gate-c AUC>0.5}). Holm-Bonferroni AND Benjamini-Hochberg
  FDR at alpha=0.05 (stdlib). A cell "passes" only if it rejects H0 AND the raw direction is correct.
- **gate-a: 6/6 survive** (Holm & BH) — block-churn is real & nonzero in every cell.
- **gate-c: 6/6 survive** — delimiter class predicts churn in every cell (model-free).
- **gate-b: 3/6 survive** (Holm & BH) — the three Claude-Code cells only. Codex cells: gpt2 p=0.188 (no excess);
  qwen2 & llama p~0 but in the WRONG direction (control churns MORE: diff -0.013 / -0.014). This is exactly the
  committee's bar: "aggregate-only pass while cells fail is NOT candidate-grade." The anti-tautology gate is a
  Claude-Code-corpus phenomenon.

### RE-06 — BLOCK-SIZE SENSITIVITY {8,16,32} — **DELIVERED; small & monotone, no rescue**
- Aggregate mean churn: block8 = 0.010958, block16 = 0.011597, block32 = 0.012856 (monotone increasing with block
  size: coarser blocks -> a divergence invalidates a larger contiguous suffix fraction). At every block size ~99% of
  blocks SURVIVE. No block size lifts churn to fleet-material levels; the committee fix-1 falsification threshold
  (">95% blocks survive => no fleet-FLOP claim") is effectively met at all three block sizes (98.7-99.5% survive).

### CHAT-TEMPLATE CONTROL (now HEADLINE, not appendix) — **96% mitigation confirmed on the 3-tokenizer grid**
- mean churn raw 0.011597 -> with `<|tool_result|>` special-token delimiter 0.000488 = **95.8% reduction**.
  Production serving that injects chat-template/special-token delimiters before tool results resets BPE state at the
  seam and nearly eliminates the effect. This is the baseline_requirement: default-chat-template serving is the
  headline regime, and there the effect is ~0.

## SANITY / REPRODUCIBILITY
- Reimplementation reproduces EXP-0049: gpt2+qwen2 subset mean churn (block16) = 0.010847 vs EXP-0049's 0.010953
  (diff from live-corpus growth 6215 -> 6409 seams). Chained-block invalidation rule + delimiter classifier + corpus
  parsers reused verbatim. seed=42; pure-stdlib analysis (math/statistics/random); no numpy/torch.

## CITATIONS ADDED (VERDICT-0055 baseline_requirements; PRIOR_ART_ADEQUATE gap closed)
- Gim et al., "Prompt Cache: Modular Attention Reuse for Low-Latency Inference," arXiv:2311.04934, MLSys 2024
  (corroborated: MLSys 2024 proceedings + arXiv). Distinguished from CLAIM-0014 in prior_art.
- "Don't Break the Cache" arXiv:2601.06007 (white-box-vs-black-box delta; already in prior_art, retained).
- Sennrich, Haddow, Birch, "Neural Machine Translation of Rare Words with Subword Units," ACL 2016 (P16-1162;
  corroborated: ACL Anthology + ACL-2016 events). BPE foundation for the RE-01 null model.

## OVERALL DISPOSITION
CLAIM-0014 is a **real but small, corpus-bound, template-preventable, regime-(a)-only characterization whose central
novelty (excess churn over a BPE baseline) is falsified by the RE-01 null** (seams churn LESS than generic BPE).
Recommendation: retain at yellow / do NOT promote to candidate; adopt the reframed title; gate-b corpus-collapse +
RE-01 null + 96% template mitigation are the HEADLINE. The economic case for the L1 H100 spend (RE-03) is weak given
these results; RE-03 and RE-04 remain orchestrator-dispatched but should be weighed against this honest narrowing.
