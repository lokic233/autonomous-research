# PROJ-0008 — Agentic-systems: early failure-attribution in agent trajectories (CHARACTERIZATION, not a tuned knob)
Topic-bias: agentic-systems (+ agent-infra). DELIBERATELY NOT a tuned-knob (Jensen-floor) or a KV-reuse
(RoPE-wall) play — the two anti-patterns this instance established. This is a MEASUREMENT/characterization
contribution: does a cheap, causal, online signal flag a doomed agent trajectory EARLIER than the agent's
own termination/error, and is that signal a structural property (not a relabeling of generic difficulty)?
Must beat the right baselines (the agent's own self-reported confidence / a generic difficulty predictor)
and be anti-circular. Two-pass; honest results; the negative (failures are unpredictable-until-they-happen)
is itself a publishable characterization.
