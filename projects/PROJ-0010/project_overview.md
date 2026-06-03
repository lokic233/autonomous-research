# PROJ-0010 — LLM-serving: cross-agent step-interleaving for GPU-bubble fill (STRUCTURAL throughput)
Topic-bias: llm-serving + agent-infra. Screened against ALL THREE observed failure shapes:
  (1) NOT a Jensen-floor tuned-knob; (2) NOT a RoPE-wall KV-reuse play; (3) NOT a predictor-vs-own-logprob
  relabeling play (the new 3rd anti-pattern that killed CLAIM-0015/0037/0038 — a cheap external signal
  predicting what the model's own confidence already encodes). This is a SYSTEMS/throughput claim: the win
  is structural occupancy, not prediction.
Thesis: in multi-agent serving, each agent alternates SHORT decode bursts (tool-call formatting / brief
reasoning) with LONG external tool-waits (network/exec). A single agent leaves the GPU idle during its
tool-waits ("step bubbles"). CROSS-AGENT step-interleaving — scheduling other agents' decode into one
agent's bubble — could raise effective GPU decode-utilization / aggregate throughput vs naive per-agent
serving, AT MATCHED per-agent latency. Must confront the REAL question: continuous batching ALREADY fills
bubbles across requests — so is there ANY residual win specific to the agent step-bubble structure, or does
vanilla continuous batching already capture it? (the likely honest-negative). Must beat real continuous
batching, not a serial strawman. Honest results; two-pass; the negative (continuous batching already
captures it) is a publishable characterization.
