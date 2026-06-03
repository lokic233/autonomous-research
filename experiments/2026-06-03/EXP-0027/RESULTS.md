# RESULTS — EXP-0027 (CLAIM-0026)
**Spec-decode session-phase-adaptive vs BEST-TUNED-FIXED draft policy.**
L0 CPU-only, stdlib, SERIAL, analytic core + stochastic detection sim. 3,024 configs, 5 seeds.
Verdict pre-committed in PRE_REGISTRATION.md (committed 5c17b34 BEFORE running).

## VERDICT: NEGATIVE (Jensen-floor) — this is a WIN (honest pipeline)
A single best-tuned fixed draft length k\* captures ~93% (median, realistic+overhead) of the
adaptive gain. Once realistic phase-detection error + switching tax are included, phase-adaptive
**loses** to best-tuned-fixed in the realistic operating regime (mean gain −2.2%). Same failure mode
as EXP-0006 (grammar-region spec-decode) and EXP-0011 (early-exit): per-phase optimum collapses to
the Jensen floor that a single tuned k already sits near.

## (A) Is the acceptance drift real and material? — YES, the drift is real.
Per-phase **optimal draft length k_opt diverges** as acceptance shifts across phases. Sample
(a_prose=0.65, r=0.1, realistic deep-session mix prose/tool/mixed = .25/.55/.20):

| gap (a_tool−a_prose) | a (prose,tool,mixed) | per-phase k_opt | single k\* | ideal gain | fixed captures |
|---|---|---|---|---|---|
| −0.30 | 0.65,0.35,0.50 | 3,1,2 | 2 | 1.41% | 79.3% |
| −0.10 | 0.65,0.55,0.60 | 3,3,3 | 3 | 0.00% | 100% |
|  0.00 | 0.65,0.65,0.65 | 3,3,3 | 3 | 0.00% | 100% |
| +0.20 | 0.65,0.85,0.75 | 3,7,5 | 6 | 1.83% | 94.8% |
| +0.30 | 0.65,0.95,0.80 | 3,15,6 | 11 | **6.88%** | 87.3% |

So acceptance drift genuinely shifts the optimal draft length (k_opt swings 1→15). The premise
of the claim — drift exists and changes the local optimum — is **confirmed**. We modeled BOTH
directions of the structured-context gap (tool/JSON acceptance higher OR lower than prose) and the
divergence appears either way. But "drift exists" is NOT the claim — part (B) is.

## (B) Does phase-adaptive beat BEST-TUNED-FIXED by a meaningful margin? — NO.
The entire committee bar (the EXP-0006/0011 lesson) is: beat the *best-tuned fixed* k, not an
arbitrary baseline. It does not, at realistic operating points.

| operating regime | n | adaptive gain vs best-tuned-fixed (mean / median / p90) | fixed_captured_frac (median) | % configs gain>3% | % configs fixed captures ≥80% |
|---|---|---|---|---|---|
| ALL configs | 3024 | −0.98% / −1.10% / +2.41% | 0.947 | 7.8% | 81.5% |
| realistic_deep, IDEAL (no overhead) | 112 | +1.87% / +1.01% / +5.20% | 0.927 | 22.3% | 80.4% |
| realistic_deep, **WITH overhead** (p_err>0, s>0) | 448 | **−2.22% / −2.00%** / +0.78% | 0.927 | 4.0% | 80.4% |
| ↳ drift≈0 (gap∈[0,0.05)) | 64 | −3.50% | 1.000 | 0% | 100% |
| ↳ small drift (0.05–0.15) | 160 | −2.49% | 0.973 | 2.5% | 92.5% |
| ↳ large drift (0.15–0.50) | 224 | −1.66% | 0.866 | 6.2% | 66.1% |

**The Jensen-floor verdict, all three pre-committed negative triggers fire:**
1. The single best-tuned fixed k captures **≥80% of the adaptive gain** at the realistic mix
   (median 92.7% with overhead, 92.7% even in the ideal/ceiling case). Committee's ≥80% bar = **empty**.
2. Adaptive advantage over best-tuned-fixed is **< a few %** — and goes **negative** (−2.2% mean)
   once realistic detection error (p_err) + switching tax (s) are paid.
3. Only when drift is extreme (gap=±0.30, a_tool reaching 0.95) and overhead is *zero* does adaptive
   reach a meaningful +7–9% (best case: a_prose=0.75, gap=+0.30, r=0.1 → ideal +9.49%, dropping to
   +7.17% with even light overhead p_err=.05/s=.02). That regime (one phase at 95% accept while
   another sits at 65%, dominating 55% of a long session, with free perfect-but-noisy detection) is
   not the realistic operating point and even there a tuned k captures 85.6%.

**Why best-tuned-fixed is so strong (the mechanism):** net tok/s as a function of k is a broad,
concave plateau (the (E[accepted]+1)/(k·r+1) curve is flat near its peak). A single k chosen to
maximize the *session-weighted* throughput lands inside every phase's near-optimal plateau because
the plateaus overlap heavily unless acceptances are pathologically far apart. That overlap is the
Jensen floor — the same geometry that killed EXP-0006 and EXP-0011.

## HONEST framing
- (A) drift real + material to the *local* optimum: **YES**.
- (B) phase-adaptive beats best-tuned-fixed by a meaningful margin at realistic operating points:
  **NO** — tuned-fixed captures ~93%, and adaptive loses net once detection/switching cost is paid.
- Overall: **NEGATIVE / does-not-hold.** This is a clean honest negative and a WIN.

## Artifacts
- PRE_REGISTRATION.md (committed pre-run, 5c17b34)
- run_exp0027.py
- results/exp0027_sweep.csv (3,024 rows, full sweep)
- results/exp0027_summary.json (verdict aggregates)
- logs/run.log

## Prior-art caveat
Draft-length adaptation is PUBLISHED: EAGLE / EAGLE-2 / Medusa / SpecDec++ /
Dynamic-Speculation-Lookahead all adapt draft length dynamically. The only candidate novelty here was
the *session-phase-drift* framing on long agentic traffic + whether it beats best-tuned-fixed. It does
not, so there is no defensible contribution beyond confirming the Jensen floor in yet another setting.

## What a real L1 must measure
Real draft+target model pair (e.g. a small draft + a target LLM) on REAL long agentic traces
(multi-turn tool-calling sessions). Measure: (1) real per-phase acceptance rate vs context depth
(does it actually drift, and how much?); (2) real net tok/s for best-tuned-fixed k\* vs a real
phase-detector-driven adaptive k on GPU; (3) real phase-detection accuracy and real switching/recompile
cost. L0 here is analytic + simulation only — it bounds the *theoretical* ceiling (≤~9% ideal, negative
with overhead) and shows the bar is almost certainly unreachable, which an L1 would only confirm at cost.
