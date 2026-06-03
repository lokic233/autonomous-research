# PROJ-0007 — kv-cache: tool-result template-structured KV reuse (STRUCTURAL win, not a tuned knob)
Topic-bias: kv-cache + agent-infra + inference-optimization.
Thesis space: agent tool results share a fixed JSON/envelope SCHEMA (same keys/structure, different values)
across many requests. The schema/boilerplate TOKEN POSITIONS are identical even when values differ — so a
template-structured KV reuse (cache KV for the fixed-template token positions, recompute only value spans)
could reclaim KV/prefill that EXACT-prefix caching (vLLM APC / RadixAttention, which key on exact token
match and break at the first differing value) structurally MISSES. CRITICAL design discipline (avoid the
Jensen-floor trap that killed EXP-0006/0011/0027): this must be a STRUCTURAL/DISCRETE win a tuned baseline
CANNOT capture — NOT a continuous-knob tuning win. And it must confront the RoPE position-dependence reality
(EXP-0007's lesson: position-shifted KV reuse is the hard part) AND beat real APC/RadixAttention, not a
strawman. Honest results; two-pass; anti-circular.
