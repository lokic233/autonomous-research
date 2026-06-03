# PROJ-0005 — Multi-agent systems: inter-agent communication compression
Topic-bias area: agentic-systems (+ inference-optimization).
Thesis space: in multi-agent LLM systems (planner/worker/critic, debate, tool-broker), inter-agent
messages are verbose NL that re-enters another agent's context as prompt tokens. Does a structured or
extractive compression of agent-to-agent messages cut total system token cost WITHOUT harming task
success — and does it beat trivial truncation AND a generic prompt-compressor (LLMLingua) at matched
compression? Honest results only; two-pass committee; anti-circular, real-baseline.
