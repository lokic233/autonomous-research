# PROJ-0011 — Agentic-systems: tool-result early-commit on streaming prefix (STRUCTURAL overlap)
Topic-bias: agentic-systems + inference-optimization. Screened vs all 3 failure shapes (NOT Jensen-floor
tuned-knob; NOT RoPE-wall KV-reuse; NOT predictor-vs-own-logprob relabeling). A STRUCTURAL/latency claim.
Thesis: many long tool results are FRONT-LOADED (the actionable answer is in the first chunk; the rest is
boilerplate/pagination/low-value). If a tool result streams, the agent could begin its next decode on the
PARTIAL prefix once the actionable content has arrived — overlapping reasoning with the tail of tool I/O,
cutting end-to-end step latency. Load-bearing tests: (1) is actionable content actually front-loaded in real
tool results (measurable)? (2) is early-commit CORRECTNESS-SAFE — does committing on the prefix change the
agent's answer vs the full result (the EXP-0004-style break-even: wasted/wrong work when the tail mattered)?
Must beat the serialize-then-read baseline AND bound the wrong-early-commit cost. Honest negative (tails
matter too often / front-loading too rare) is itself a characterization. Two-pass; anti-circular.
