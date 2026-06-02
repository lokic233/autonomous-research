# PROJ-0002 — Agentic-systems: speculative tool-call prefetch
Topic-bias area: agentic-systems (+ inference-optimization).
Thesis space: in tool-calling agents, the LLM serially decodes {tool_name, then the full argument JSON}
before the tool is invoked, so tool latency is fully serialized AFTER decode. If the tool NAME + the
high-confidence leading arguments are decoded early, an executor can SPECULATIVELY pre-warm/begin the
tool call (e.g. connection setup, arg-independent prefetch, or full call when args are high-confidence)
and overlap it with the remaining decode — cutting end-to-end agent step latency. Cemetery-checked vs
PROJ-0001 (KV eviction). Honest results only; two-pass committee.
