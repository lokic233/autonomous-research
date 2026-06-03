# PROJ-0013 — Eval-and-safety: passage-level eval contamination under document-level dedup (CHARACTERIZATION)
Topic-bias: eval-and-safety + data-systems-for-ml (NEW frontier). LIGHTWEIGHT: ONE sharp claim. Screened vs
all 3 anti-patterns (NOT tuned-knob; NOT KV-reuse; NOT relabeling-vs-own-logprob) — it's a data/eval
MEASUREMENT claim. Thesis: training-corpus dedup is usually done at DOCUMENT granularity, but eval-benchmark
items (questions/answers/passages) can appear as SHORT SPANS embedded inside training documents that are NOT
document-level near-duplicates of the benchmark — so DOCUMENT-level dedup systematically UNDER-COUNTS
passage-level eval contamination. The contribution is the EMPIRICAL gap: how much benchmark contamination
does doc-level dedup miss that passage/n-gram-level detection catches? Anti-circular (contamination GT =
actual benchmark-span presence, detector = n-gram/embedding span match, not the label), beat the right
baseline (document-level near-dup, the standard practice), honest-negative if the gap is small or doc-level
already catches it. Distinguish from known n-gram contamination checks — novelty is the MEASURED doc-vs-passage
gap + its effect on reported contamination rates.
