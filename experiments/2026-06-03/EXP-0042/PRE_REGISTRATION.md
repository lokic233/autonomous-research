# PRE_REGISTRATION — EXP-0042 / CLAIM-0043
Researcher: researcher-0041 | L0 (CPU-only, stdlib-only, SERIAL, <=15 min) | committed BEFORE running.

## CLAIM (CLAIM-0043)
Standard recall@k OVER-COUNTS RAG retrieval success: fixed-size chunking splits a non-trivial
fraction (>20%) of gold answer spans across chunk boundaries, and recall@k credits a retrieved
chunk that contains only a FRAGMENT of the gold span as a hit — so recall@k materially exceeds
answer-completeness@k (the fraction of queries where a retrieved chunk contains the WHOLE gold span),
inflating reported retrieval scores by a measurable margin standard RAG eval does not report.

## POSTURE / SCREEN
Fresh-area (data-systems-for-ml + eval-and-safety), metric-VALIDITY measurement, lightweight, ONE sharp claim.
Screened vs 3 anti-patterns: NOT a tuned-knob (fixed metric-validity measurement); NOT KV-reuse;
NOT predictor-vs-own-logprob. The novelty = the MEASURED recall@k over-count from span-splitting +
its score-distortion. NOT "chunking matters" (published) and NOT lost-in-the-middle (reader-position).

## THREE FALSIFIABLE PARTS
1. Under standard fixed-size chunking, what fraction of gold answer spans get SPLIT across chunk boundaries?
2. Does recall@k (>=1 top-k chunk OVERLAPS gold span by >=1 token) materially exceed
   answer-completeness@k (>=1 top-k chunk CONTAINS the WHOLE gold span)? = the OVER-COUNT.
3. Is the gap >20% AND large enough to change reported RAG retrieval scores?

## CORPUS MODEL (generative ground truth — anti-circularity)
- N_DOCS docs. Each doc = distractor sentences (drawn from a vocab of common tokens) with a GOLD
  ANSWER SPAN inserted at a controlled char/token position. Span = SPAN_LEN distinctive "gold" tokens
  (rare tokens not in distractor vocab) so it is the unique answer to its query.
- Ground truth = the gold span's TOKEN offsets [start,end) in the source doc. This is a generative fact
  we control. The chunker + retriever read ONLY text; the gold offset is used ONLY to DEFINE the metric
  outcome (overlap vs whole-containment) — the legitimate measurement, not circular. Retriever NEVER sees offsets.
- Query = a paraphrase using a subset of the gold tokens (so a FRAGMENT-containing chunk can still
  score well) plus a query-topic token. Realistic: a fragment may or may not retrieve well.

## CHUNKER (fixed-size, configurable)
- Tokenize doc by whitespace. Fixed-size sliding window: CHUNK_SIZE tokens, stride = CHUNK_SIZE - OVERLAP.
- Chunk boundaries computed from token positions ONLY (no gold knowledge).

## RETRIEVER (STATED: lexical token-overlap / BM25-style — sentence-transformers NOT importable on this Mac)
- Score(chunk, query) = BM25-style: sum over query tokens of idf(t)*tf-saturation in chunk.
  IDF computed over the chunk collection. Retrieve top-k chunks by score. This rewards chunks
  containing query (=gold-subset) tokens — so a fragment chunk CAN be a high scorer. Realistic.

## TWO METRICS (the measurement)
- recall@k    = 1 if >=1 of top-k retrieved chunks OVERLAPS the gold span by >=1 token, else 0.
- completeness@k = 1 if >=1 of top-k retrieved chunks CONTAINS the WHOLE gold span [start,end), else 0.
- OVER-COUNT = recall@k - completeness@k (averaged over queries). split_rate = frac of docs where
  NO single chunk contains the whole gold span (span straddles >=1 boundary).

## SWEEPS
- CHUNK_SIZE in {32,64,128}; OVERLAP in {0,8,16,32,64} (incl. overlap>=span control);
  SPAN_LEN in {8,16,32}; k in {1,3,5,10}. SEEDS: >=5 (use 8). N_DOCS=200 per cell.
- CONTROL: when OVERLAP >= SPAN_LEN, a whole span must fit in some window -> split impossible ->
  over-count must -> 0. Verify. Report over-count AS A FUNCTION OF overlap (guards strawman:
  standard practice uses overlap).

## HONEST-NEGATIVE BRANCH (pre-committed)
If recall@k ~ completeness@k (split rate low, OR overlap windows prevent splits, OR fragment chunks
rarely make top-k so over-count negligible), OR the gap does not move reported scores materially ->
REPORT THE NEGATIVE. A negative is a WIN. Never fabricate.

## DECISION RULE
- Part1 PASS if split_rate > 0.20 at standard config (overlap < span).
- Part2 PASS if mean over-count > 0 with CI excluding 0.
- Part3 PASS if over-count > 0.20 (abs) at some standard config AND recall headline >> completeness truth.
- Strawman guard: if over-count > 0.20 ONLY at overlap=0 and ->0 for typical overlap (e.g. 16-64) ->
  report as PARTIAL / fragile (standard overlap kills it).

## OUTPUTS
results/sweep.csv (per-cell aggregates), results/seeds.csv (per-seed for CI), RESULTS.md, logs/run.log.
