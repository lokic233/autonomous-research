# EXP-0049 Results Analysis — researcher-0014-L0-r4
# CLAIM-0014, PROJ-0005, Level-0, CPU-only

## HEADLINE: ALL THREE GATES PASS (aggregate) — CLAIM-0014 SUPPORTED at L0

### Gate (a): block-churn CI excludes 0 — PASS
- mean block_churn_frac = 0.0110 [0.0100, 0.0119] (95% bootstrap CI)
- 9.6% of injection seams (1196/12430) have at least one invalidated block
- ~1.1% of blocks are invalidated per seam on average

### Gate (b): churn > control CI>0 on diff — PASS (AGGREGATE; see per-slice caveats)
- mean diff (treatment - control) = 0.0032 [0.0023, 0.0041]
- Treatment churn EXCEEDS clean-\n-append control in aggregate
- **CAVEAT — per-tokenizer heterogeneity:**
  - GPT-2: diff = +0.0072 (treatment > control) ✓
  - Qwen2-0.5B: diff = -0.0008 (treatment ≈ control) ✗
- **CAVEAT — per-corpus heterogeneity:**
  - Claude Code: diff = +0.0084 ✓
  - Codex: diff = -0.0057 (control > treatment!) ✗
- INTERPRETATION: The anti-tautology gate passes in aggregate (driven by GPT-2 × Claude Code),
  but the effect is NOT universal across all tokenizer×corpus cells. The Qwen2 tokenizer's
  larger vocabulary (151K vs 50K) means fewer merge boundaries are straddled at seams.
  Codex tool results may have more BPE-friendly structure.

### Gate (c): delimiter-class predictor AUC > 0.5 — PASS
- AUC = 0.724 [0.703, 0.745]
- Model-free delimiter-class-only predictor strongly separates churn vs no-churn
- Strongest predictors of churn: space (100%), colon (100%), angle_bracket (57%),
  period (54%), double_newline (48%), bracket_close (38%)
- single_newline: 0% churn (newline acts as a clean BPE boundary)
- json_close_brace: 3.7% churn (most common delimiter, n=8158)

## CRITICAL FINDING: CHAT-TEMPLATE CONTROL (committee fix 6)
- Churn WITHOUT template delimiter: 1.10%
- Churn WITH <|tool_result|> template: 0.05% (95% REDUCTION)
- **PRODUCTION IMPLICATION: In serving systems that inject chat-template delimiters
  (e.g., <|im_start|>, <tool_call>, etc.) before tool results, these special tokens
  RESET BPE state at the seam, nearly eliminating boundary churn.**
- This is an INFORMATIVE NEGATIVE for practical fleet impact: properly templated
  engines already mitigate this effect. The churn is real but TEMPLATE-PREVENTABLE.

## REGIME STRATIFICATION (committee fix 2)
- All results assume regime (a) = full-prompt-retokenize-per-turn
- Regime (b) = token-ID-cache/delta-tokenize has STRUCTURALLY ZERO churn
- The headline 1.1% mean block churn applies ONLY to regime (a)
- HONEST FRAMING: if the serving engine caches token IDs and only encodes new text
  (regime b), this entire phenomenon does not exist. The claim is regime-conditional.

## NON-COLLISION ATTESTATION vs DEAD-0006 (committee fix 7)
- DEAD-0006: "token-prefix sharing PREDICTS KV sharing" — killed as trivial
  (RadixAttention already does this)
- CLAIM-0014 = INVERSE: re-tokenization BREAKS the assumed token-prefix identity
- NOT a re-litigation: DEAD-0006 says "prefix predicts sharing" (true but trivial);
  CLAIM-0014 says "the prefix itself is not stable" (the ID sequence changes at seams)
- Complementary findings, not contradictory

## HONEST CHARACTERIZATION (committee fix 4)
Re-tokenization ≠ concatenation is KNOWN FOLKLORE (token healing, Lundberg 2023).
This work's contribution is a CHARACTERIZATION:
1. Delimiter-conditioned block-churn rate on real agent traces (1.1% mean, 0-32% by class)
2. Model-free delimiter-class predictor (AUC 0.72) — no attention/semantic signal needed
3. Silent APC/RadixAttention block-hash miss quantification at block=16 granularity
4. Chat-template canonicalization as a near-complete mitigation (95% reduction)
5. Tokenizer-dependence: larger-vocab tokenizers show less churn (Qwen2 < GPT-2)

## WEAKNESSES TO REPORT
1. Gate (b) does not pass for all tokenizer×corpus cells individually (only in aggregate)
2. Chat-template control shows the effect is nearly eliminated in production — practical
   fleet impact may be minimal for engines using proper templates
3. Only 2 tokenizers tested; production Llama-3 tokenizer is gated (could not test)
4. Prefix truncation to 4096 chars for CPU tractability — longer prefixes may differ

## VERDICT: PASS (with caveats)
Candidate-grade for committee review. The phenomenon is REAL and MEASURABLE, but
TEMPLATE-PREVENTABLE and TOKENIZER-DEPENDENT. The honest framing is:
"BPE boundary churn at tool-result seams is a characterizable phenomenon, predictable
from delimiter class alone, but largely mitigated by proper chat-template injection."
