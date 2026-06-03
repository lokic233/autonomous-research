# PROJ-0006 — Inference-optimization: draft-model staleness in agentic speculative decoding
Topic-bias area: inference-optimization (+ agentic-systems).
Thesis space: in LONG multi-turn agentic sessions, does the speculative-decoding draft model's acceptance
rate DRIFT as the running context grows (early prose-y turns vs deep tool-call/JSON-heavy context)? If
acceptance is context-phase-dependent, a fixed draft model is mistuned for part of the session, and a
cheap context-phase-adaptive draft policy (e.g. swap draft / adjust draft length by detected session phase)
could recover speedup. CRITICAL prior-deaths to avoid: EXP-0006 (grammar-region spec-decode) + EXP-0011
(early-exit) both DIED because a single TUNED baseline captured the gain (Jensen floor) — so the bar here
is beating the BEST-TUNED fixed draft policy, and isolating phase-drift from a static per-phase optimum.
Honest results only; two-pass committee; anti-circular; pre-bake the tuned-baseline kill.
