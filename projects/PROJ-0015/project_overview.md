# PROJ-0015 — Data-systems-for-ml: shared-boilerplate -> non-monotone (inverted-U) answer-rank displacement under BM25 (EMPIRICAL PHENOMENON)
Topic-bias: data-systems-for-ml (corpus hygiene x retrieval). LIGHTWEIGHT: ONE sharp claim. ARCHETYPE PIVOT
(away from the dead metric-validity vein): this is an EMERGENT empirical phenomenon with NO closed-form
predictor, NOT a metric-definition gap. Screened vs all 3 anti-patterns (NOT tuned-knob, NOT KV-reuse, NOT
relabeling-vs-logprob — it's a property of a FIXED standard BM25 retriever under a VARIED data condition).
Thesis: when a planted answer doc + its distractors share an identical boilerplate block, the answer doc's
BM25 rank degrades NON-MONOTONICALLY (inverted-U) as boilerplate length grows — an intermediate length
maximally displaces it from top-k, then further growth PARTIALLY RECOVERS rank, because IDF-decay of now-
corpus-frequent boilerplate terms vs BM25 length-normalization penalizing the content-bearing answer doc
cross over at a corpus-statistics-dependent point with no closed form. PRIOR-ART (front-loaded): 'Collapse of
Dense Retrievers' (2503.05037) = STATIC length/position/literal biases, not a non-monotone response to a
controllable preprocessing var; document-expansion-hurts (2604.05087/2504.21015) adds DISTINCT text to one
doc (opposite info-theoretic regime — boilerplate is maximally NON-discriminative/low-IDF); set-compositional
IR (2605.03824)/salient-phrase (2110.06918) = query semantics, orthogonal. Novelty = the shared-boilerplate ->
answer-rank inverted-U + its crossover. Anti-circular: GT = which doc-id carries the planted answer (generative
fact); tested signal = BM25 score/rank (token stats only, never reads GT label). Honest-negative (informative):
if monotone OR flat (IDF fully neutralizes), inverted-U FALSIFIED — itself a clean corpus-hygiene finding.
