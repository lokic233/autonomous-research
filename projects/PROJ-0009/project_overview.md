# PROJ-0009 — Agentic-systems: tool-selection confusability from schema geometry (CHARACTERIZATION)
Topic-bias: agentic-systems (+ agent-infra). Anti-pattern-screened: NOT a Jensen-floor tuned-knob, NOT a
RoPE-wall KV-reuse play. A MEASUREMENT/characterization claim (the surviving shape). Thesis: in multi-tool
agents, wrong-tool-selection errors are predictable from the SCHEMA GEOMETRY of the available tool set
(semantically-overlapping tool descriptions/params -> confusable selections), so a cheap pre-call
schema-overlap signal flags high-confusion toolsets. Must be anti-circular (predict from schema-only
geometry, NOT from the selection-error label/oracle), beat the right baselines (random + a generic
prompt-difficulty predictor + the agent's own tool-choice logprob/confidence — the anti-relabeling test),
and be distinguished from published tool-selection/retrieval work. Honest negative (confusability is not
schema-predictable, or it's just the agent's own logprob relabeled) is itself a publishable characterization.
