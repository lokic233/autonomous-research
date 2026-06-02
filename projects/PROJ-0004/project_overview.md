# PROJ-0004 — Inference-optimization: grammar-region-adaptive speculative decoding
Topic-bias area: inference-optimization.
Thesis space: speculative-decoding draft acceptance rate is STRUCTURALLY higher inside constrained
regions (tool-call/JSON/grammar-constrained spans) than in free prose, because the constrained grammar
collapses the next-token distribution. An agent-aware speculator that lengthens the draft window inside
constrained-grammar regions (and shortens it in free prose) should achieve higher net speedup than a
fixed-length speculator on agentic/tool-calling traffic. Distinct axis (decoding, not cache/schedule).
Honest results only; two-pass committee.
