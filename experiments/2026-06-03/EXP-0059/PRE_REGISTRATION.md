# PRE_REGISTRATION — EXP-0059 (CLAIM-0053)
researcher-0057 | PROJ-0023 | TASK-0049 | L0 CPU-only stdlib SERIAL <=15min
Committed BEFORE running. Honest pipeline; negatives are wins.

## CLAIM (CLAIM-0053)
Standard GPT-3/Llama n-gram-overlap benchmark decontamination ("remove any test item
sharing an >=k-gram with the training corpus") deletes test items with probability
MONOTONE-INCREASING in item length (union bound over per-n-gram match events), so the
SURVIVING benchmark shifts toward SHORTER items. When item difficulty is length-correlated
(empirically true on QA/reasoning), this length-selection biases post-decontam accuracy
UPWARD by a margin growing with corpus n-gram coverage c, persisting at production k in
{8,13}. Harm is a property of the MITIGATION (decontam), not of contamination.

## BENCHMARK MODEL (harness OWNS GT — strictly anti-circular)
- M items (M=4000). Each item i = token sequence over a Zipfian vocab (|V|=5000, s=1.07).
- Length L_i drawn from a realistic right-skewed dist: L_i = clip( round(lognormal(mu=3.0,
  sigma=0.6)) , Lmin=12, Lmax=400 ). (median ~20 tokens, long tail — QA/reasoning-like.)
- TRUE difficulty: d_i = alpha * g(L_i) + (1-alpha) * eps_i
    g(L_i) = (rank-normalized length to ~N(0,1)): standardize log(L_i).
    eps_i ~ N(0,1) independent of length.
    => alpha=0 : difficulty INDEPENDENT of length. alpha>0 : longer = harder.
- TRUE correct-answer prob: p_i = sigmoid(-d_i)  (harder => lower p).
- alpha SWEPT in {0, 0.3, 0.6, 0.9}.

## TRAINING CORPUS + FILTER (tested signal; reads ONLY tokens + corpus n-gram set)
- Corpus n-gram set: built so that each individual k-gram of an item matches with
  per-n-gram prob q, where q is set by coverage c. We model the corpus as a set; we draw,
  for each k-gram position, a Bernoulli(q) "this k-gram is in corpus" with q controlled by c.
  (Equivalent to a Zipfian-sampled corpus n-gram bag of the given coverage; we instrument q
  directly so the union-bound prediction is exact and testable.)
- c SWEPT in {low, med, high} -> q in {0.002, 0.01, 0.05} per-k-gram match prob.
- FILTER: remove item i iff ANY k-gram of item i is in corpus n-gram set.
    # k-grams in item of length L = max(0, L - k + 1). Removal ~ Bernoulli over these.
- k SWEPT in {8, 13, 25} (production values 8,13; 25 = high-k mitigation probe).
- ANTI-CIRCULARITY: filter NEVER reads d_i/p_i/labels. GT used ONLY at scoring time.

## MEASUREMENTS
(a) STRUCTURAL ANCHOR (must hold):
    - removal-rate as function of L_i: monotone increasing?
    - survivor mean-length < full-set mean-length?
    - sim removal vs union-bound prediction P(remove|L) = 1 - (1-q)^(L-k+1). Check match.
(b) HEADLINE: acc_full = mean p_i over ALL items; acc_surv = mean p_i over SURVIVORS.
    Delta = acc_surv - acc_full, as function of (alpha, c, k). Multiple seeds + 95% CI.

## CONTROLS / TESTS
- alpha=0 CONTROL (LOAD-BEARING): Delta ~ 0 (composition shifts but score-safe). If
  |Delta|>~CI at alpha=0 => sim bug (filter seeing difficulty) -> FIX. REQUIRED for support.
- alpha>0: Delta > 0, growing with alpha and with c.
- k-SWEEP mitigation: does Delta persist across k {8,13,25}? Does production-k drive
  removal->0 (then honest-negative)?

## DECISION RULES (pre-committed)
- HELD/SUPPORT iff ALL: (1) structural anchor holds (removal monotone-increasing in L AND
  survivor mean-len < full mean-len AND matches union-bound within tolerance) AND
  (2) alpha=0 Delta ~ 0 (|Delta| <= 2 CI half-widths, i.e. CI covers 0) AND
  (3) Delta grows positive with alpha at realistic params AND grows with c AND
  (4) Delta persists (stays >0, CI excludes 0) across production k in {8,13}.
- FALSIFIED iff Delta ~ 0 even at high alpha (0.9) AND high c (0.05) [structural shift may
  still happen but score never moves].
- TRIVIALLY-SMALL iff Delta non-trivial only at implausibly extreme c, OR production-k
  (8,13) drives removal-rate -> ~0 so no meaningful selection.

## SEEDS / BUDGET
- N_SEEDS = 8 per (alpha,c,k) cell. M=4000. Pure stdlib (random, math, statistics). SERIAL.
