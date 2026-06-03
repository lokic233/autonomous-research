# COMMITTEE#1 — CLAIM-0043 (PROJ-0014, data-systems-for-ml / eval-and-safety — 3rd EXPANSION claim)
## metric-VALIDITY measurement study, effect=keep-exploring / PARTIAL-CONFIRM (conditional, magnitude sim-inflated — flagged honestly). Screened vs all 3 anti-patterns (NOT tuned-knob — fixed metric-validity measurement; NOT KV-reuse; NOT predictor-vs-own-logprob). Anti-circular. Vote honestly.

## TWO FRAMINGS THE ORCHESTRATOR EXPLICITLY ASKS YOU TO STRESS-TEST (sibling claim CLAIM-0042 just died on exactly these — judge them hard here):
(i) IS THE BASELINE THE REAL STANDARD PRACTICE, NOT A STRAWMAN? The claim's baseline = recall@k as the headline retrieval metric reported in RAG eval. Is recall@k (>=1 retrieved chunk overlaps the gold span) genuinely THE standard reported RAG retrieval metric? (It is widely used — recall@k / hit@k is the standard retrieval metric in RAG eval.) Or is there a tool-purpose mismatch? Judge precisely. The sibling CLAIM-0042 died because it mis-cast a corpus-dedup tool as 'the standard contamination practice'. Do NOT let an analogous mis-cast pass here.
(ii) IS THERE AN OBVIOUS COMPETITOR METRIC THAT TRIVIALLY CLOSES THE GAP? CLAIM-0042 was killed by an omitted Containment metric (|A&B|/|item|) that trivially closed its gap. For THIS claim: is 'answer-completeness@k' (chunk contains the WHOLE gold span) itself the obvious fix any practitioner would use, making the 'over-count' a known/trivial correction rather than a discovery? Or is the point that recall@k IS what gets reported and completeness@k is NOT standard, so the over-count is unreported in practice? Decide whether that's a genuine metric-validity contribution or folklore.

## L0 FINDINGS (anti-circular: GT=gold span char/token offset; retriever=BM25 LEXICAL, no embeddings; 8 seeds x 200 docs/cell):
MECHANISM IS EXACT: over-count == split-rate to high precision (a split means recall@k still hits an overlapping FRAGMENT chunk while NO chunk wholly contains the span). 95% CI excludes 0 in every split>0 cell.
(1) SPLIT RATE rises with span_len, falls with chunk_size/overlap (as the mechanism predicts). >20% at many standard configs: chunk32/ov0 span8=0.224/span16=0.456/span32=0.965; chunk64/ov0 span16=0.215/span32=0.458; chunk128/ov0/span32=0.247. NOT >20% everywhere (short span + big chunk = low). Conditional PASS.
(2) SCORE-DISTORTION dramatic where splits occur: chunk64/ov0/span16 recall 100% vs completeness 78.5% (+21.5pts); chunk32/ov0/span16 100% vs 54.4% (+45.6); chunk32/ov0/span32 100% vs 3.5% (+96.5 — recall says 'solved', truth says 'broken'). >20% confirmed across long-span/low-overlap standard configs.
(3) OVERLAP-CONTROL (the load-bearing strawman guard) PASSES EXACTLY: overlap>=span_len -> over-count=0 (chunk64/span16/k5: ov0=0.215, ov8=0.122, ov16=0.000, ov32=0.000). Standard overlap DOES kill it — but only when overlap>=gold-span length; real gold spans (15-40+ tok sentences/phrases) frequently EXCEED typical ~10-20%-of-chunk overlaps, so the surviving regime is realistic, NOT a 'zero-overlap is bad' strawman. BUT short-answer + adequate-overlap -> over-count=0, where the claim is FALSE (reported honestly).

## HONEST CAVEAT (researcher-flagged, load-bearing): recall@k=1.000 in EVERY cell because unique/distinctive gold tokens make the lexical retriever always rank a fragment chunk in top-1 -> the result is k-invariant and the ABSOLUTE magnitude is UPPER-BOUND-flavored ('given the fragment is retrievable'). A real dense retriever sometimes MISSES the fragment entirely, which would shrink the gap. This is the #1 thing an L1 must resolve.

## CLAIM
claim: "Standard recall@k OVER-COUNTS RAG retrieval success: fixed-size chunking splits\
  \ a non-trivial fraction (>20%) of gold answer spans across chunk boundaries, and\
  \ recall@k credits a retrieved chunk that contains only a FRAGMENT of the gold span\
  \ (insufficient to answer) as a hit \u2014 so recall@k materially exceeds answer-completeness@k\
  \ (the fraction of queries where a retrieved chunk contains the WHOLE gold span),\
  \ inflating reported retrieval scores by a measurable margin that standard RAG eval\
  \ does not report."
why_it_matters: "FRESH AREA (data-systems-for-ml + eval-and-safety). LIGHTWEIGHT:\

## L0 RESULTS (EXP-0042)
# RESULTS — EXP-0042 / CLAIM-0043
researcher-0041 | L0 CPU stdlib SERIAL | 6.3s wall (<<15 min) | 8 seeds, 200 docs/cell, doc_len=300 tok
Retriever: BM25-style LEXICAL (sentence-transformers NOT importable on this Mac — STATED). Honest pipeline.
Raw: results/sweep.csv (144 cells), results/seeds.csv (1152 rows), logs/run.log. Trust CSVs.

## VERDICT: PARTIAL-CONFIRM — the over-count is REAL and large, but is CONDITIONAL on overlap < span.
The claim's mechanism is verified and the over-count exceeds 20% across many standard configs, BUT the
load-bearing overlap-control shows standard overlap ELIMINATES it whenever overlap >= span_len. So the
claim holds for LONG gold spans / SMALL overlaps and is FALSE for short spans with adequate overlap.

## PART 1 — SPLIT RATE (fraction of docs where NO chunk holds the whole gold span)
Split rate rises with span_len, falls with chunk_size and overlap, exactly as the mechanism predicts.
Representative (overlap < span), k-independent:
  - chunk=32, overlap=0:  span8=0.224, span16=0.456, span32=0.965   (ALL >20%)
  - chunk=64, overlap=0:  span8=0.093, span16=0.215, span32=0.458   (span>=16 >20%)
  - chunk=128,overlap=0:  span8=0.043, span16=0.114, span32=0.247   (span32 >20%)
  - chunk=64, overlap=8:  span16=0.122, span32=0.395
  - chunk=64, overlap=16: span32=0.275 (overlap<span here, since span=32)
=> Part 1 PASSES: split rate >20% at many STANDARD configs (esp. long spans / small chunks / low overlap).
   It is NOT >20% everywhere (short span + big chunk = low split). Honest: depends on span_len vs chunk/overlap.

## PART 2 — RECALL@k vs COMPLETENESS@k OVER-COUNT (recall - completeness)
The over-count equals the split rate to high precision (mechanism is exactly: split => recall hits an
overlapping fragment chunk while no chunk wholly contains the span => completeness misses). k-invariant
here (lexical retriever always ranks an overlapping chunk in top-1, see CAVEAT). k=5 examples:
  - chunk=32, ov=0,  span16: recall=1.000 comp=0.544 OVERCOUNT=0.456 [CI95 lo=0.440]  >20%, CI excludes 0
  - chunk=32, ov=0,  span32: recall=1.000 comp=0.035 OVERCOUNT=0.965 [lo=0.956]       >20%
  - chunk=64, ov=0,  span16: recall=1.000 comp=0.785 OVERCOUNT=0.215 [lo=0.203]       >20%
  - chunk=64, ov=16, span32: recall=1.000 comp=0.725 OVERCOUNT=0.275 [lo=0.253]       >20%
  - chunk=128,ov=0,  span32: recall=1.000 comp=0.752 OVERCOUNT=0.247 [lo=0.234]       >20%
=> Part 2 PASSES: over-count > 0 with 95% CI excluding 0 in every split>0 cell. Materially exceeds 20%
   in all long-span / low-overlap standard configs.

## PART 3 — >20% AND DOES IT MOVE REPORTED SCORES?
YES, dramatically, where splits occur. The HEADLINE recall@k overstates true answer-completeness@k by:
  - 21.5 points (chunk64/ov0/span16): reported 100% vs true 78.5%
  - 45.6 points (chunk32/ov0/span16): reported 100% vs true 54.4%
  - 96.5 points (chunk32/ov0/span32): reported 100% vs true  3.5%  <- recall says "solved", truth says "broken"
This is exactly the metric-validity failure the claim asserts: recall@k reports near-perfect retrieval
while completeness@k (whole-span-in-one-chunk, what a reader actually needs) is near zero.
=> Part 3 PASSES on the magnitude AND score-distortion axis (conditional, see below).

## OVERLAP CONTROL (THE LOAD-BEARING STRAWMAN GUARD) — over-count as a FUNCTION OF overlap
Pre-registered: when overlap >= span_len, a whole span must fit in some window => split impossible =>
over-count must -> 0. CONTROL PASSES EXACTLY (0/all cells with overlap>=span & k>=3 have over-count>0):
  chunk=64, span=16, k=5:  overlap=0 -> 0.215 ;  overlap=8 -> 0.122 ;  overlap=16 -> 0.000 ;  overlap=32 -> 0.000
=> Standard overlap DOES kill the over-count — but ONLY when overlap >= the gold span length.
   The honest framing: the over-count is a function of (overlap / span_len). Real gold answer spans
   (a sentence/phrase, often 15-40+ tokens) frequently EXCEED typical chunk overlaps (often ~10-20% of
   chunk = 12-25 tok for 128-tok chunks), so the regime where the over-count survives is REALISTIC, not
   a strawman of "zero-overlap is bad." But the result is NOT unconditional: short answers + adequate
   overlap => over-count = 0, and the claim would be FALSE there.

## HELD-OUT / NEGATIVE / PARTIAL
- NEGATIVE cells (honest, a WIN): short span (8 tok) + overlap>=8 => split=0, over-count=0. The claim
  fails here. Reported truthfully.
- The k=1 rows show a tiny over-count (~0.005-0.05) even at overlap>=span: an artifact of top-1 ranking
  occasionally picking a fragment chunk over the whole-span chunk on score ties; vanishes by k>=3.
- PARTIAL overall: confirmed mechanism + large conditional over-count + clean control; NOT an
  unconditional >20% claim.

## CAVEATS (honest limits of this L0 sim — MUST read before trusting the magnitude)
1. recall@k = 1.000 in EVERY cell because gold tokens are UNIQUE distinctive tokens => the lexical
   retriever ALWAYS ranks an overlapping (fragment) chunk in top-1. This INFLATES the absolute
   over-count vs reality (a real retriever sometimes misses the fragment chunk entirely, lowering BOTH
   recall and the gap). The over-count here is an UPPER-BOUND-flavored estimate of the metric gap given
   "the fragment is retrievable." The k-invariance is a direct consequence and is a sim artifact, not a
   real-world property.
2. Lexical BM25, not a dense bi-encoder. A dense retriever may behave differently (semantic match to a
   fragment vs whole span). L1 must test a real dense retriever.
3. Synthetic corpus + synthetic spans. The split-rate distribution depends on real answer-span length
   distributions and real chunker behavior.

## WHAT A REAL L1 SHOULD MEASURE
- REAL QA corpus with REAL gold-answer spans: Natural Questions (short + long answers), HotpotQA, or a
  Wikipedia-passage QA set with char-offset gold spans.
- REAL chunkers: LangChain RecursiveCharacterTextSplitter (fixed-size + overlap) AND semantic chunking,
  swept over realistic sizes (256/512/1024 tok) and overlaps (0/10%/20%).
- REAL dense retriever: a sentence-embedding bi-encoder (e.g. all-MiniLM / bge / e5) AND BM25; measure
  recall@k vs whole-span-completeness@k under each.
- THE downstream test the L0 cannot do: feed top-k to a reader and measure EM/F1 under recall@k-selected
  vs completeness@k-selected chunks. The real question is whether the recall@k over-count actually COSTS
  answer accuracy (a fragment chunk that's a "recall hit" but can't answer the question). That converts a
  metric-validity result into a downstream-cost result.

## PRIOR-ART CAVEAT (precise)
Chunking-STRATEGY work is heavy and PUBLISHED (semantic vs fixed-size, query-dependent chunking,
multi-size RRF, code-RAG chunking studies) — they OPTIMIZE chunking. This is NOT that. This is also NOT
lost-in-the-middle (a reader-position effect). The (modest, conditional) novelty here is the MEASURED
recall@k metric OVER-COUNT caused by gold-span splitting and its score-distortion (reported recall vs
whole-span completeness) — a metric-VALIDITY result. Honest scope: it is conditional on overlap < span,
and the absolute magnitude is sim-inflated by the always-retrievable-fragment assumption (caveat 1).

## PRE-REG (committed pre-run 7e08e8f)
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

## ORCHESTRATOR NOTE: LIGHTWEIGHT. If candidate-grade, L1 = real NQ/HotpotQA/Wikipedia-QA gold spans + real chunkers (LangChain RecursiveCharacterTextSplitter fixed+overlap AND semantic, sizes 256/512/1024, overlaps 0/10/20%) + a REAL dense retriever (MiniLM/bge/e5 bi-encoder AND BM25) + crucially the DOWNSTREAM reader EM/F1 under recall@k-selected vs completeness@k-selected chunks — does the over-count actually COST answer accuracy? (converts metric-validity into downstream-cost). PRIOR-ART (precise): chunking-STRATEGY work is heavy + published but OPTIMIZES chunking; this is NOT that and NOT lost-in-the-middle (reader-position). Modest novelty = the measured recall@k metric OVER-COUNT from gold-span splitting + score-distortion (metric-VALIDITY), conditional on overlap<span, magnitude sim-inflated by the always-retrievable-fragment assumption. If you judge it's already-folklore (completeness@k is the obvious fix any practitioner uses) OR the always-retrievable assumption makes the magnitude meaningless OR the conditional scope is too narrow, say so — converge and move to the next fresh area (don't deep-mine PROJ-0014).
