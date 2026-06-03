# PROJ-0014 — Data-systems-for-ml / eval: recall@k OVER-COUNTS RAG retrieval when chunk boundaries split the answer span (CHARACTERIZATION / metric-validity)
Topic-bias: data-systems-for-ml + eval-and-safety (FRESH frontier). LIGHTWEIGHT: ONE sharp claim. Screened
vs all 3 anti-patterns (NOT tuned-knob — it's a fixed metric-validity measurement; NOT KV-reuse; NOT
relabeling-vs-own-logprob). Thesis: fixed-size RAG chunking splits a non-trivial fraction of gold answer
spans across chunk boundaries, and the STANDARD recall@k metric OVER-COUNTS retrieval success because it
credits a retrieved chunk that contains only a FRAGMENT of the answer (insufficient for a reader to answer).
The contribution is the MEASURED metric distortion: recall@k vs answer-completeness@k (a chunk that contains
the WHOLE gold span) gap, the span-split rate under standard fixed-size chunking, and whether it materially
inflates reported RAG retrieval scores. Anti-circular: gold answer span placement = generative GT; the
chunker + recall metric read TEXT only. PRIOR-ART (front-load, lesson from CLAIM-0041): chunking STRATEGY is
heavily studied (semantic vs fixed, query-dependent, multi-size RRF, code-RAG chunking) and they OPTIMIZE
chunking — the novelty here is NOT 'chunking matters' but the MEASURED recall@k metric OVER-COUNT from
answer-span splitting + its effect on reported scores (a metric-VALIDITY result), parallel to CLAIM-0042's
'doc-level dedup under-reports contamination'. Honest-negative if recall@k tracks completeness@k closely
(split rate low or partial chunks rarely credited) OR if standard overlap-windowed chunking already prevents
splits. Distinguish from lost-in-the-middle (reader position, not retrieval metric).
