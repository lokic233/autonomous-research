# PRE_REGISTRATION — EXP-0052 / CLAIM-0049
researcher-0050 (PERSISTENT-SEEDER, BUG-115) | L0 CPU-only stdlib SERIAL <=15min
Committed BEFORE running. Honest pipeline; negatives are wins.

## CLAIM (CLAIM-0049)
When near-dup clusters contain members differing in a quality-correlated observable
(token-set size / "completeness"), the dedup RETENTION POLICY (keep-first vs keep-last vs
keep-random) induces a systematic SKEW in the surviving corpus's latent-quality distribution.
The skew is governed by the order-quality correlation rho, FLIPS SIGN between keep-first and
keep-last, and keep-random is unbiased — EVEN THOUGH all three remove the BYTE-IDENTICAL
cluster set. Empirical phenomenon, no closed form.

## ★ LOAD-BEARING GUARD (orchestrator's #1 concern: near-tautology risk)
If high-q docs appear first (rho>0), keep-first OBVIOUSLY over-selects high-q — trivial alone.
Claim is INTERESTING only if BOTH:
  (A) skew is LARGE at REALISTIC rho (estimate rho from real crawl batching, NOT adversarial rho=1).
  (B) skew is INVISIBLE to standard dedup audits (identical clusters removed, identical FP/removal
      rates) — no standard audit would catch it.
If effect only at adversarial rho, OR tiny at realistic rho, OR audit-detectable => NEAR-TAUTOLOGY (weaken).

## GENERATIVE WORLD (harness OWNS ground truth)
- N docs (N=80000). Vocab V=20000 tokens.
- Each doc has latent quality q ~ Normal(0,1) (q = GT, harness-owned, NEVER seen by detector/policy).
- Base doc length L drawn so that token-set size CORRELATES with q: completeness = sigmoid-ish;
  doc token-count = base_len * (1 + beta*q_member) where high-q members are longer/more complete
  (matches real finding 2503.07879: high-dup higher-quality, longer/more complete docs).
- Near-dup clusters: fraction f_clust=0.30 of docs belong to clusters of size k~Uniform{2,3,4,5}.
  Cluster built from a shared base token-set; each member = base set perturbed (drop/add tokens)
  s.t. within-cluster Jaccard >= 0.8 (high near-dup). Members differ in q (within-cluster q spread
  controlled by sigma_within) AND in completeness (size correlates with member q via beta).
- STREAM POSITION: assign each doc a position with tunable order-quality correlation rho.
  Implemented via Gaussian copula: position_score = rho*q + sqrt(1-rho^2)*noise; sort by score
  => Spearman(position, q) ~ rho. rho>0 => high-q tends FIRST; rho<0 => reversed; rho=0 random.

## DETECTOR (reads ONLY observables: token-sets; never q)
- REAL MinHash + LSH in pure stdlib: num_perm=64 hash permutations via hashlib (sha1 of token+seed,
  take min). LSH banding: b bands x r rows (b*r=64), tuned so S-curve threshold ~0.8.
- Candidate pairs from LSH buckets -> union-find connected components = detected near-dup clusters.
- Detector is BLIND to q and to stream position content.

## RETENTION POLICIES (read ONLY positions/observables, NEVER q)
- keep-FIRST: per cluster keep member with smallest stream position; drop rest.
- keep-LAST: per cluster keep member with largest stream position; drop rest.
- keep-RANDOM: per cluster keep a uniformly random member (seeded); drop rest.
- All keep all singletons. All three remove the IDENTICAL set of clusters (same detection).

## ANTI-CIRCULARITY
GT = latent q (generative, harness-owned). Detector sees only token-sets. Policies see only
positions. Skew measured AFTER the fact: compare retained-set mean q across the 3 policies.
No policy ever reads q. No circular use of q in detection or retention.

## MEASUREMENTS
PRIMARY: Delta_first(rho) = mean_q(keep-first survivors) - mean_q(keep-random survivors).
         Delta_last(rho)  = mean_q(keep-last  survivors) - mean_q(keep-random survivors).
Report in units of corpus quality SD (so "fraction of a quality SD").
rho sweep: {-0.6,-0.4,-0.2,0.0, 0.1,0.2,0.3,0.4 (REALISTIC band), 0.6,0.8,1.0 (adversarial)}.
>=20 seeds per rho; report mean +/- 95% CI.

GUARD A (REALISTIC rho): Estimate plausible rho for real crawls. Reasoning: crawls are batched
  by source/shard/time; within-shard quality is correlated (same domain ~ similar quality), and
  shard order is roughly source-clustered. A plausible *global* order-quality Spearman is modest:
  most ordering is within-shard-arbitrary, but cross-shard quality clustering leaks a weak global
  trend. Pre-register realistic band rho in [0.1, 0.4], headline rho=0.2. Report |Delta| there
  in SD units. "Matters" threshold (pre-registered): |Delta| >= 0.05 SD at rho=0.2.

GUARD B (AUDIT-INVISIBILITY): Verify across the 3 policies: (i) identical set of detected clusters,
  (ii) identical count of docs removed, (iii) identical removal rate and (iv) identical FP set
  (a standard audit checks cluster-removal + FP loss only). Confirm byte-identical removed-cluster
  set. If all identical => audit-invisible (no standard audit distinguishes the policies).

## OUTCOME BRANCHES (pre-registered)
- HELD: |Delta_first(rho=0.2)| >= 0.05 SD (guard A passes) AND clean sign-flip
  (sign(Delta_first) = -sign(Delta_last) across rho) AND keep-random Delta within CI of 0
  AND |Delta| monotone increasing in |rho| AND monotone in within-cluster q variance
  AND audit-invisibility confirmed (guard B).
- HONEST-NEGATIVE: skew within noise at realistic rho, OR no sign-flip, OR keep-random biased,
  OR swamped by detection FP => keep-arbitrary default vindicated.
- NEAR-TAUTOLOGY: effect ONLY at adversarial rho (tiny at rho<=0.4), OR audit-detectable
  => weaken, orchestrator's guard fired.

## EXTRA CHECK: within-cluster variance sweep
Sweep sigma_within in {0.0, 0.5, 1.0, 1.5}. CONFIRM requires |Delta| grows with sigma_within
(no within-cluster q spread => no skew possible, sanity).

## SEEDS / REPRO
master_seed=12345; per-seed = master_seed + seed_idx; >=20 seeds. Pure stdlib (random, hashlib,
math, statistics, csv). SERIAL (no multiprocessing). All CSVs written to results/.

## ANTI-PATTERNS screened
1. No closed-form fit dressed as discovery (empirical sweep). 2. Not measuring detector S-curve
(orthogonal; we hold detection FIXED). 3. GT harness-owned, not proxy-circular. 4. Guard against
near-tautology explicitly (guards A+B). 5. Honest negative/near-tautology branches pre-committed.
