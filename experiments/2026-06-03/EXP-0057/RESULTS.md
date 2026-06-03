# RESULTS — EXP-0057 (CLAIM-0051, committee#1 follow-up)

**Researcher:** researcher-0055 | **Level:** L1-contested (CPU, stdlib, SERIAL) | runtime **84.6s**
**Disposition: KEEP-EXPLORING — claim REFRAMED to effective run-length L_eff (mechanism survives,
"deficit removed ONLY by B growing with L" framing FALSIFIED).** Reuses EXP-0056 harness verbatim
(sliding-window buffer shuffle, per-source signatures g_s, label-free INFLATION metric, anti-circular).
Prereg committed a10632c BEFORE any run.

## BLOCKER 1 (★ the unrebutted RED) — INTERLEAVING COLLAPSES INFLATION at moderate C
Round-robin interleave of C concurrent source-runs (tf.data.interleave cycle_length=C), fed into
the bounded buffer. inflation vs oracle-full-shuffle (5 seeds, mean +/- 95% CI):

  realistic point (B=10b=320, L=20b=640):
    C= 1     2      4      8      16
    14.79  9.65   5.34   3.02   1.43      <- C=8 -> 3.0x, C=16 -> 1.43x
  large-L point (B=320, L=200b=6400):
    24.25  11.66  4.92   2.44   0.97      <- C=16 -> ~1.0x (fully fixed)
  (B=64,L=640): 22.83 11.92 5.70 3.04 1.34   (B=1600,L=6400): 19.57 10.44 4.73 2.40 0.99

=> A moderate cycle_length (C=8-16) COLLAPSES inflation to ~1.x at BOTH the realistic AND the
large-L point. The committee's RED is upheld: the claim's "the deficit is removed ONLY by B
growing with run-length L" is **FALSIFIED as stated** — interleaving cuts it WITHOUT growing B.

## L_eff = L/C HYPOTHESIS — interleaving is an L-reducer, but a STRONGER one than pure L/C
Compared observed interleaved inflation(B,L,C) to the L0 sequential law inflation(B, L_eff=L/C):
  - C=1 matches sequential to within 1.5-2.6% (sanity: interleave C=1 == L0 stream). GOOD.
  - C>=2: observed inflation is SUBSTANTIALLY BELOW the sequential-L_eff prediction
    (e.g. B=320,L=6400,C=4: obs 4.92 vs seq(L_eff=1600) 20.34; rel_err 76%).
=> Interleaving does NOT merely shorten one run to L/C; round-robin breaks up ALL C active runs
SIMULTANEOUSLY, so consecutive emitted items rotate across C distinct sources. The buffer then
sees same-source spacing ~C, decorrelating FAR faster than a single sequential run of length L/C.
**Correct unified variable is the residual same-source co-occurrence rho_buf, which interleaving
(C) drives down directly (rho 0.59->0.06 as C 1->16) — NOT a literal L_eff=L/C substitution.**
L_eff=L/C is a CONSERVATIVE upper bound on the harm; interleaving over-delivers.

## BLOCKER 2 — RHO_WITHIN: the >=1.5x bar SURVIVES low within-source correlation
Realistic point (B=320, L=640, C=1), re-derived sigma_noise to hit each target (verified):
  rho_target  rho_achieved  inflation_vs_full
    0.20         0.189          4.36x
    0.50         0.484          9.60x
    0.80         0.791         15.10x
=> Even at rho_within=0.19 (low, plausible per-domain), inflation is **4.36x >> 1.5x**. The bar
does NOT require high correlation; it survives the realistic low end. [supports claim premise]

## BLOCKER 3 — PER-SHARD-SHUFFLE BASELINE: buffer is NOT worse — it's BETTER
Oracle-full-shuffle was a favorable denominator. Against per-shard-shuffle (shuffle within each
contiguous run, no cross-shard mixing — every batch stays ~pure single-source, rho=1.0):
  inflation_vs_per-shard at C=1: 0.58-0.95 across ALL grid points (i.e. buffer BEATS per-shard).
  e.g. realistic point: V_full=1.24, V_buf=18.6, V_pershard=30.6 -> buf/pershard = 0.61.
  (rises above 1 only once interleaving has already crushed V_buf, e.g. C=16 large-L: 4.46 —
   but there V_buf is near-oracle anyway.)
=> Against the WEAKER, more realistic baseline a practitioner would actually compare to,
the bounded buffer is an IMPROVEMENT, not a regression. This blunts the practical-harm framing.

## DECISION (per pre-registered rules) — KEEP-EXPLORING / REFRAME-to-L_eff
- STRENGTHENED rule FAILS: interleaving DOES fix it at C=16 (incl. large-L) AND buffer is NOT
  worse than per-shard.
- WEAKENED rule FAILS: >=1.5x does NOT require rho=0.8 (survives at rho=0.19, 4.36x), so the
  premise is not fragile.
- => REFRAME (keep-exploring) is the honest call: the B-vs-run-length MECHANISM survives (inflation
  IS governed by residual same-source co-occurrence rho_buf), but the headline framing
  "removed ONLY by B growing with L" is WRONG. The correct, defensible reframe:

  **"Bounded shuffle-buffer variance inflation is governed by the residual same-source
  co-occurrence rate rho_buf(B, L, C). Practitioners reduce it by (a) INTERLEAVING C shards
  (cheapest — C=8-16 collapses it to ~1.x without growing B), (b) growing B toward the run-length,
  or (c) shard pre-shuffle. The inflation is real (4-24x vs an oracle full shuffle, survives low
  within-source correlation), but it is NOT worse than the naive per-shard-shuffle baseline, and
  interleaving — standard in tf.data/WebDataset/MosaicML — already mitigates it. The original
  'provision B against L, not b' is one of three levers, not the unique fix."**

## Anti-circular / sim-shape guards (preserved)
GT = source-id + g_s; INFLATION measurement reads ONLY gradient vectors (labels build stream +
diagnostic rho only). rho_buf is produced by the shuffle+interleave mechanic (measured, off-metric).
within-corr targets re-derived from first principles and VERIFIED empirically (0.189/0.484/0.791).

## Files
- PRE_REGISTRATION.md (committed a10632c, before any run)
- harness.py (reuses EXP-0056 harness; adds interleave + per-shard + within-corr diagnostic)
- run_followup.py
- results/interleave.csv, results/leff_check.csv, results/rho_within.csv, results/results.json, results/run.log
