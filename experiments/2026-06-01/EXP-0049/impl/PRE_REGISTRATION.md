# EXP-0049 Pre-Registration — LOCKED BEFORE COMPUTATION
# researcher-0014-L0-r4, CLAIM-0014, PROJ-0005

## Pre-Registration Timestamp
2026-06-01 (written BEFORE any churn computation)

## Primary Anti-Tautology Gate (committee fix 3)
The PRIMARY endpoint is the DIFFERENCE between treatment churn and clean-\n-append control churn.
This gate MUST be evaluated BEFORE the delimiter-class predictor AUC is reported.

### Gate Definition
- Treatment: block_churn_frac from tool-result injection (real tool output appended)
- Control: block_churn_frac from clean-newline-append ("\n" appended instead of tool output)
- Test statistic: mean(treatment - control) with 95% bootstrap CI
- PASS: CI lower bound > 0 (treatment churn EXCEEDS control)
- FAIL: CI includes 0 (churn == control => "BPE does BPE" => clean kill)

If this gate FAILS, the delimiter-class predictor AUC is NOT reported as a positive finding.
churn ≈ control means the phenomenon is not tool-result-specific but just generic BPE
boundary behavior at any append point.

## Secondary Gates
- Gate (a): mean block_churn_frac 95% CI excludes 0
- Gate (c): delimiter-class LOO predictor AUC 95% CI > 0.5

## Pass Criteria
ALL THREE gates must pass for CLAIM-0014 to be supported at L0.

## Tokenizers
- gpt2 (50257 vocab, Rust fast backend)
- Qwen2-0.5B (151643 vocab, Rust fast backend)

## Corpora
- Claude Code (~/.claude/projects/**/*.jsonl)
- Codex (~/.codex/sessions/**/*.jsonl)

## Block Size
16 tokens (simulating vLLM APC default)

## Honest-Null Commitment
A CLEAN KILL (any gate fails) is a VALID, PUBLISHABLE result.
It means engines already canonicalize seams, or the phenomenon is not
tool-result-specific. Either finding redirects effort productively.
