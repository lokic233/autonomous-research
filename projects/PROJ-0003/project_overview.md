# PROJ-0003 — LLM-serving: prefix-family-aware batch admission
Topic-bias area: llm-serving (+ agent-infra).
Thesis space: continuous-batching schedulers (vLLM/SGLang) typically admit by FCFS/priority, ignoring
which queued requests SHARE a long system+tool-schema prefix. A prefix-family-aware admission policy
that co-schedules requests sharing a prefix into the same running batch maximizes prefix-cache reuse and
cuts aggregate prefill, at a controllable fairness/latency cost. Distinct from PROJ-0001/0002 (eviction,
prefetch) — this is the SCHEDULING/admission axis. Honest results only; two-pass committee.
