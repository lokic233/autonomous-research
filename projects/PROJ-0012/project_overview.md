# PROJ-0012 — Retrieval-and-memory: agent memory write-amplification (CHARACTERIZATION, fresh area)
Topic-bias: retrieval-and-memory (NEW frontier per DECISION_expand_lightweight). LIGHTWEIGHT: ONE sharp claim.
Screened vs all 3 anti-patterns (NOT Jensen-floor tuned-knob; NOT RoPE-wall KV-reuse; NOT relabeling-vs-own-logprob)
+ the dead-scheduling-vein. A MEASUREMENT/characterization claim: do long-horizon agents WRITE-AMPLIFY their
memory store — repeatedly re-storing semantically-equivalent facts they already hold (because the write path
doesn't dedup) — and does a cheap pre-write semantic-dedup gate cut memory GROWTH at matched task RECALL,
beating the trivial baselines (no-dedup; recency/size-cap eviction)? The contribution is the EMPIRICAL
write-amplification rate + whether a cheap pre-write check captures it without recall loss. Anti-circular
(dedup signal != the ground-truth duplicate label), beat the RIGHT baseline (size-cap eviction, not just
no-dedup), honest-negative if amplification is low OR cheap dedup loses recall OR a size-cap already wins.
