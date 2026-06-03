# RESULTS — EXP-0052 / CLAIM-0049
researcher-0050 (PERSISTENT-SEEDER, BUG-115) | L0 CPU-only stdlib SERIAL | 474s (<15min) | N=15000, 22 seeds (10 for sigma sweep)

## VERDICT: NEAR-TAUTOLOGY (orchestrator's guard A fired) — keep-arbitrary default essentially vindicated

The phenomenon is REAL, CLEAN, and AUDIT-INVISIBLE — but its MAGNITUDE at realistic rho is small
(0.0125 SD), BELOW the pre-registered "matters" threshold (0.05 SD). Even at adversarial rho=1.0 the
skew is only 0.064 SD. The sign-flip is genuine and not a *pure* tautology (it is invisible to standard
dedup audits), but the effect is too small at realistic crawl-order correlation to be a practical
quality-biasing knob. We report this HONESTLY: guard A failed; the claim does not HOLD at the
interesting bar.

## What HELD (the mechanism is exactly as claimed)
- **Sign-flip: exact.** Df ≈ -Dl at every rho (keep-first and keep-last bias the surviving quality in
  opposite directions). e.g. rho=+1.0: Df=-0.0640±0.0009, Dl=+0.0649±0.0008.
- **Monotone in rho, zero-crossing at rho=0.** Df: +0.0383 (rho=-0.6) → +0.0124 (-0.2) → +0.0002 (0)
  → -0.0125 (+0.2) → -0.0640 (+1.0). Linear, monotone, anti-symmetric.
- **rho=0 unbiased.** Df=+0.0002±0.0009, Dl=+0.0007±0.0009 — both within CI of 0. keep-random is the
  neutral baseline.
- **Monotone in within-cluster quality variance.** At rho=0.2: sigma_within 0.0→Df≈0 (no spread => no
  skew possible, sanity ✓), 0.5→-0.0036, 1.0→-0.0122, 1.5→-0.0220.
- **GUARD B — AUDIT-INVISIBLE: confirmed.** All 3 policies operate on the IDENTICAL detected cluster set
  (1111 clusters), remove the IDENTICAL count of docs (2548/2548/2548), identical removal rate (0.1699),
  identical FP (8.5 docs mean). A standard dedup audit (cluster-removal + FP-loss only) sees NO
  difference between keep-first/last/random. The skew is genuinely undetectable by standard audits.

## What FAILED — GUARD A (the load-bearing magnitude check)
- Pre-registered realistic-rho band [0.1,0.4], headline rho=0.2, "matters" threshold |Df| >= 0.05 SD.
- **Measured at rho=0.2: |Df| = 0.0125 SD.** Below threshold by 4x.
- Across the entire realistic band: rho=0.1→0.0063, 0.2→0.0125, 0.3→0.0188, 0.4→0.0248 SD. All small.
- Even ADVERSARIAL rho=1.0 yields only 0.064 SD. The effect simply is not large at any plausible rho.
- => The phenomenon is real but practically negligible. The orchestrator's #1 concern (near-tautology
  / tiny-at-realistic-rho) is VINDICATED: this is NOT an interesting quality-biasing knob in practice.

## Why the magnitude is small (mechanism honesty)
The skew per cluster is bounded by (within-cluster q range) x (how much position-ranking correlates
with q WITHIN a cluster). At realistic rho the GLOBAL order-q correlation only weakly penetrates the
WITHIN-cluster ordering (cluster members are near in the stream only by chance), so keep-first picks a
near-random member per cluster. Only ~17% of docs are removed, and the per-removed-doc bias is a small
fraction of an SD; diluted across the whole surviving corpus (83% singletons untouched), the corpus-mean
shift is tiny. This is structural, not a tuning artifact.

## NOT a pure tautology, but not interesting either
The naive worry "high-q first => keep-first obviously over-selects high-q" predicts the SIGN. But:
(a) the effect is present and audit-invisible (guard B) — that part is non-obvious and TRUE; yet
(b) the MAGNITUDE at realistic rho is too small to matter (guard A) — so the non-obvious part doesn't
rescue practical relevance. Net: an honest near-tautology / negative. keep-first (BigCode/datatrove/NeMo
default) is FINE; the representative-selection choice is not a meaningful corpus-quality lever at
realistic crawl-order correlation.

## Artifacts
- PRE_REGISTRATION.md (committed BEFORE run, commit 9bfae70)
- run_exp.py (pure stdlib: random, hashlib universal-hash MinHash, math, statistics, csv)
- results/rho_sweep.csv  — Df,Dl,Dr vs rho (11 rhos x 22 seeds, 95% CI)
- results/sigma_sweep.csv — Df,Dl vs within-cluster variance at rho=0.2
- results/guardB_audit.csv — audit-invisibility proof (identical clusters/removal/FP)
- logs/run.log — full run log

## Prior-art caveat (honest)
Lee2021 (seminal LM dedup; keeps arbitrary representative, never studies which survives) — consistent with
our finding that the choice doesn't matter much. Broder/Indyk-Motwani (MinHash/LSH S-curve; orthogonal —
we hold detection FIXED, not our headline). 2503.07879 (high-dup higher-quality; our premise for the
size-quality coupling). D4 2308.12284 (which-clusters, not within-cluster). BigCode/datatrove/NeMo
keep-first default — VINDICATED by this negative. Novelty attempted = representative-selection as a
quality-biasing knob under order x heterogeneity with the keep-first/last sign-flip at identical cluster
removal. Result: the knob is real but negligibly small at realistic rho => honest near-tautology.

## What L1 should measure (if pursued despite the negative)
Real datatrove/datasketch MinHashLSH over a FineWeb/SlimPajama/Stack slice. ESTIMATE the TRUE
within-shard order-quality correlation rho empirically (by domain/shard/timestamp) — our whole verdict
hinges on whether realistic rho is really ~0.1-0.4. If a real corpus has STRONG within-cluster ordering
(e.g. canonical-URL-first crawl artifacts make near-dups adjacent AND quality-sorted), rho_within could be
much higher than the global rho and the effect could resurface. Run keep-first/last/random at IDENTICAL
cluster sets; measure surviving-corpus quality-proxy distribution; budget-permitting pretrain 160M LMs to
check for a downstream eval gap. PREDICTION from L0: no meaningful downstream gap unless within-cluster
ordering is strongly quality-sorted (unlikely in standard crawls).
