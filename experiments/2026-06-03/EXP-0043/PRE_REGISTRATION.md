# PRE_REGISTRATION — EXP-0043 (CLAIM-0044)

**Researcher:** researcher-0042 | **Level:** L0 (CPU-only, stdlib, SERIAL, <=15 min)
**Project:** PROJ-0015 (data-systems-for-ml: corpus hygiene x retrieval) | **Task:** TASK-0034
**Committed BEFORE any run.** Honest pipeline; negatives are WINS. Trust on-disk CSVs, not stdout.

## THE CLAIM (CLAIM-0044)
When a planted answer document and its distractors share an IDENTICAL boilerplate block,
the answer doc's rank under standard BM25 (k1=1.2, b=0.75) degrades NON-MONOTONICALLY
(inverted-U) as boilerplate length L grows: an intermediate L maximally displaces the answer
doc out of top-k, after which further boilerplate growth PARTIALLY RECOVERS its rank — because
(i) IDF-decay of now-corpus-frequent boilerplate terms and (ii) BM25 document-length
normalization penalizing the answer doc are opposing forces that cross over at a
corpus-statistics-dependent point with no closed-form predictor.

This is an EMPIRICAL-PHENOMENON claim (NOT metric-validity gap; BM25 rank used correctly as-is).
Screened vs the 3 anti-patterns: NOT tuned-knob (k1/b fixed at standard), NOT KV-reuse,
NOT relabeling-vs-logprob. Property of a FIXED retriever under a VARIED data condition.

## THE FALSIFIABLE QUESTION (three-way, all reportable)
As shared-boilerplate length L grows, does rank(answer doc) trace an INVERTED-U (worsens to a
maximum displacement at some intermediate L, then PARTIALLY RECOVERS)?
  - INVERTED-U HELD: interior L where mean rank is significantly WORSE than BOTH L=0 and L=max,
    and the L=max rank recovers significantly below the interior peak. Turning point not
    predictable from a naive monotone model.
  - MONOTONE: rank just gets worse (or just gets better) with L — inverted-U FALSIFIED.
  - FLAT: IDF fully neutralizes boilerplate -> negligible rank change — FALSIFIED.

## CORPUS MODEL (a generative fact the harness controls)
- N = 2000 short docs. Each doc = SENT_PER_DOC sentences of DISTINCT random "content" tokens
  drawn from a ZIPFian vocabulary (stdlib Zipf sampler; exponent s, vocab V) to mimic real TF skew.
- Query Q = a fixed set of QUERY_TERMS rare-ish content tokens.
- ANSWER doc (exactly one, id = answer_id): its content contains ALL query terms (plus filler),
  so under BM25 with no boilerplate it ranks #1 (verified at L=0 in sanity).
- DISTRACTORS (n_distractors ~= 30): docs whose content contains SOME (a random subset) of the
  query terms but NOT all — lexically plausible competitors that crowd the top of the ranking.
- All other docs: pure random Zipf content (background).

## MANIPULATION (the controllable preprocessing variable)
- BOILERPLATE = a fixed block of B_VOCAB distinct boilerplate tokens (disjoint from content vocab),
  repeated/truncated to length L tokens. Prepended IDENTICALLY to a controlled set of docs.
- PRIMARY sweep: L in {0, 8, 16, 32, 64, 128, 256, 512, 1024} tokens.
- SECONDARY sweep (boilerplate spread fraction — drives how corpus-frequent boilerplate becomes,
  hence IDF-decay): frac in {answer-only, answer+25% distractors, answer+ALL distractors}.
  (answer-only: boilerplate terms stay rare -> high IDF; all-distractors: boilerplate terms become
   common in the candidate set -> IDF decays.)
- For each (L, frac): prepend the L-token boilerplate to the designated docs, re-index BM25 over
  the WHOLE corpus, issue the fixed query Q, record rank(answer_id) (1 = best).

## BM25 (standard, stdlib)
- IDF (Robertson/Sparck-Jones, the BM25+ "add-1" non-negative variant — STATED):
    idf(t) = ln( (N - df(t) + 0.5) / (df(t) + 0.5) + 1 )
- score(D,Q) = sum_{t in Q} idf(t) * ( f(t,D)*(k1+1) ) / ( f(t,D) + k1*(1 - b + b*|D|/avgdl) )
  with k1 = 1.2, b = 0.75. |D| = doc length in tokens; avgdl = mean doc length over corpus.
- SANITY UNIT CHECK (logged before sweep): a tiny 3-doc hand-checkable corpus; recompute BM25
  by hand and assert the implementation matches to 1e-9, and assert the expected doc ranks #1.

## METRIC
- rank(answer | L, frac) = 1-based rank of answer_id when docs sorted by BM25 score desc
  (ties broken by doc id, deterministic). Lower = better. Reported as mean +/- 95% CI over seeds.

## MECHANISM DECOMPOSITION (to SHOW the crossover or its absence)
For each (L, frac) log:
- bp_idf(L) = mean idf of boilerplate tokens (proxy for IDF-decay as boilerplate spreads/grows).
- lennorm(L) = the BM25 length-normalization denominator factor for the ANSWER doc:
    (1 - b + b*|answer_doc|/avgdl)  — grows as L lengthens the answer doc, suppressing its
    content-term tf contribution.
- Also log the answer doc's BM25 score and the top-distractor BM25 score, to see the gap.
- A genuine inverted-U requires these two forces to CROSS OVER: at small L, length-norm
  penalty dominates (rank worsens); at large L (esp. when boilerplate is corpus-frequent),
  bp IDF collapse + saturation lets the answer doc's genuine content reassert -> rank recovers.

## ANTI-CIRCULARITY
GT = which doc-id carries the planted answer span (answer_id) — a generative fact the harness
controls. The tested signal = BM25 score/rank computed PURELY from token statistics; it NEVER
reads the GT label. "Is this the answer doc" is used ONLY at evaluation time to map rank->outcome.

## SWEEP / SEEDS / BUDGET
- L in {0,8,16,32,64,128,256,512,1024} (9 values) x frac in {0.0, 0.25, 1.0} (3) = 27 configs.
- SEEDS = 0..19 (>=20 corpus seeds). N=2000 docs, ~30 distractors, V~3000 Zipf vocab.
- SERIAL, stdlib only, target <=15 min. (27*20 = 540 corpus builds + indexes; each O(N) — fine.)

## DECISION RULE (rigorous, not eyeballing)
Per frac, let r(L) = mean rank over seeds, with 95% CI half-width h(L) (t or normal approx).
- INVERTED-U HELD (per frac) iff there EXISTS interior L* (0 < L* < 1024) such that:
    (a) r(L*) - h(L*) > r(0) + h(0)        [interior significantly WORSE than L=0]
    (b) r(L*) - h(L*) > r(1024) + h(1024)  [interior significantly WORSE than L=max => recovery]
    i.e. the interior peak's CI excludes BOTH endpoint means (the stated test).
- MONOTONE: r(L) is (statistically) non-decreasing or non-increasing with no interior peak
  satisfying (a)+(b).
- FLat: max_L r(L) - min_L r(L) is within CI noise (negligible; IDF absorbs).
- Overall claim HELD iff inverted-U holds for >=1 frac with the recovery being statistically clear;
  report per-frac. Otherwise report MONOTONE or FLAT (clean negative — a WIN).

## HONEST-NEGATIVE BRANCH
If monotone or flat: report it plainly with the IDF/length-norm decomposition explaining WHY
(e.g. "length-norm penalty monotone-dominates; IDF decay never catches up at these L" => monotone;
or "boilerplate IDF ~ 0 by construction once spread, content terms unaffected" => flat). State
inverted-U FALSIFIED. This is a clean corpus-hygiene fact either way.

## PRIOR-ART CAVEAT (precise, honest)
'Collapse of Dense Retrievers' (2503.05037) = STATIC length/position/literal biases, NOT a
non-monotone response to a controllable preprocessing variable. Document-expansion-hurts
(2604.05087, 2504.21015) adds DISTINCT text to one doc (opposite info-theoretic regime;
boilerplate is maximally NON-discriminative / low-IDF). Set-compositional IR (2605.03824) /
salient-phrase (2110.06918) = query semantics (orthogonal). Novelty = the shared-boilerplate ->
answer-rank inverted-U + its IDF/length-norm crossover. Be honest if L0 shows monotone/flat.

## OUTPUTS
- results/raw_results.csv   (per seed x L x frac: rank, answer_score, top_distractor_score, bp_idf, lennorm, answer_len)
- results/summary.csv       (per L x frac aggregated across seeds: mean/CI of rank, mean bp_idf, mean lennorm)
- results/sanity.txt        (BM25 unit-check transcript)
- RESULTS.md                (curves, inverted-U test, IDF-vs-lennorm crossover, outcome, held/falsified)
