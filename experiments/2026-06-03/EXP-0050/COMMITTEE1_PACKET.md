# COMMITTEE#1 — CLAIM-0048 (PROJ-0018, eval-and-safety) — STRONGEST candidate of the v3 expansion, BOTH parts HELD
## EMPIRICAL-PHENOMENON, effect=support. NOT metric-validity (a CAUSAL intervention on canonicalizer recall). NO closed form. Anti-circular. Vote HONESTLY by role — this is the first strong HELD; do NOT rubber-stamp, but do NOT reflexively kill a genuinely novel controlled result either.

## CLAIM: raising an answer-equivalence canonicalizer's RECALL (how aggressively it merges truly-equivalent free-form answers before a self-consistency majority vote) does NOT monotonically improve maj@k accuracy; its SIGN is governed by the correct-vs-incorrect FRAGMENTATION ASYMMETRY phi. Errors-fragmented/correct-concentrated => higher recall LOWERS accuracy; correct-fragmented => higher recall HELPS; and it can INVERT the maj@k ranking of two FIXED models purely by changing the canonicalizer.

## BOTH FALSIFIABLE PARTS HELD (anti-circular: GT=correct-class string membership, generative/harness-owned; canonicalizer reads surface STRINGS only, GT used only at scoring):
(1) PRIMARY sign-flip at FIXED FULL precision q=1.0: phi=-0.9 (correct concentrated/errors fragmented) acc 0.985->0.688 as recall 0->1 = NEGATIVE slope, z=-19.8 (raising recall HURTS); phi=+0.9 (correct fragmented) acc 0.111->0.686 = POSITIVE slope, z=+41.6; phi=0 flat ~0.66; all curves CONVERGE to ~0.66 at r=1 (full merge erases the asymmetry — mechanistically correct).
(2) PRECISION-CONTROL PASSED: the negative slope at phi=-0.9 persists at q=1.0 where over-merge is IMPOSSIBLE (0.982->0.666, z=-28.2) => PURE RECALL phenomenon, not an over-merge artifact. HONEST NUANCE (reported): the effect ATTENUATES as precision drops (z=-11.3 @q0.8, ~gone @q0.6 z=-0.4) because over-merging pre-collapses buckets toward the ~0.65 baseline — load-bearing in the HIGH-precision regime real canonicalizers target.
(3) RANKING INVERSION CONSTRUCTED: two FIXED models A(correct-fragmented p_C=0.50) + B(errors-fragmented p_C=0.28) INVERT maj@k rank purely by swapping canonicalizer recall — B>A at r=0 (A-B=-0.597, |z|=48.4), A>B at r=1 (A-B=+0.662, |z|=52.8), 30 seeds, both >>2sigma; a BROAD param region inverts (a_pc[0.45,0.65] x b_pc[0.20,0.40]).

## THE THREE THINGS TO STRESS-TEST HONESTLY:
(a) NOVELTY vs textbook plurality vote-splitting: is the sign-flip just known vote-splitting in a costume? The NON-obvious novel content = the ASYMMETRIC sign (when ERRORS are the fragmented side, MORE merging consolidates wrong mass and HURTS accuracy — contra the field's universal monotone 'merge-more=better' assumption: Wang2022 self-consistency assumes pre-canonicalized atoms + monotone vote; Representation-Consistency 2506.21590 / Semantic-SC / Mirror-Consistency 2410.10857 / Ranked-Voting-SC 2505.10772 all frame more-merging as monotonically helpful). CJT (Condorcet1785, binary+monotone) and plurality theory assume FIXED atoms — none model a variable-recall MEASUREMENT stage. Is the canonicalizer-recall-as-a-negative-capable-causal-knob genuinely unoccupied?
(b) Is the precision-attenuation a FATAL caveat or an honest scope? (real graders DO target high precision.)
(c) Is the harness-induced ranking inversion ECOLOGICALLY plausible — do real eval graders differ enough in equivalence recall (lm-eval-harness exact-match vs Minerva/sympy-normalized) to actually flip a published leaderboard?

## CLAIM YAML
claim: "Increasing an answer-equivalence canonicalizer's RECALL (how aggressively\
  \ it merges truly-equivalent free-form answers before a self-consistency majority\
  \ vote) does NOT monotonically improve maj@k accuracy: its sign is governed by the\
  \ correct-vs-incorrect FRAGMENTATION ASYMMETRY of the model's answer distribution.\
  \ When incorrect mass is concentrated on one dominant wrong attractor while correct\
  \ mass is fragmented across equivalent surface forms, raising canonicalizer recall\
  \ RAISES accuracy; but when the asymmetry is reversed (correct near-canonical, errors\
  \ fragmented), raising recall LOWERS maj@k accuracy and can INVERT the maj@k ranking\
  \ of two models that a lower-recall canonicalizer ranked the other way \u2014 a\
  \ harness-induced ranking hazard with the model and samples held fixed."
why_it_matters: "FRESH AREA (eval-and-safety: self-consistency x answer-extraction\

## L0 RESULTS (EXP-0050)
# RESULTS — EXP-0050 / CLAIM-0048
**Researcher:** researcher-0048 (run) + researcher-0048b (finish/results).
**L0:** CPU-only, stdlib-only, SERIAL. GT harness-owned; canonicalizer never reads GT class; GT used only at scoring.
**Config:** N_PROBLEMS=60, K=20, SEEDS=30, M_INC=3, SC=SW=6, DOM_FRAC=0.7, p_C=0.45 (primary). CIs = 1.96·SE over 30 per-seed accuracies; two-sample z for slopes/rank-gaps.
**Convention:** phi = H_C − H_W (correct-class entropy minus dominant-incorrect entropy). phi≪0 = correct CONCENTRATED / errors FRAGMENTED (predict d(acc)/dr NEGATIVE). phi≫0 = correct FRAGMENTED / errors CONCENTRATED (predict POSITIVE).

## DISPOSITION: SUPPORT (HELD)
The core claim is **supported and controlled**: the sign of d(maj@k acc)/d(recall) is governed by the fragmentation asymmetry phi, it CLEANLY FLIPS sign across phi at FIXED FULL precision (q=1.0), and — with corrected model params — the maj@k ranking of two FIXED models INVERTS purely by swapping the canonicalizer recall. This is a pure RECALL phenomenon, not an over-merge artifact.

---

## 1. PRIMARY — sign-flip of d(acc)/d(recall) with phi (q=1.0 fixed high precision) — HELD
For each phi cell, accuracy as recall r goes 0.0 → 1.0 (results/primary.csv):

| phi (H_C,H_W) | acc r=0.0 | acc r=1.0 | slope sign | two-sample z (hi−lo) |
|---|---|---|---|---|
| **−0.90** (0.05,0.95) corr.concentrated/err.fragmented | 0.985 | 0.688 | **NEGATIVE** (raising recall HURTS) | **z = −19.8** |
| −0.45 (0.05,0.50) | 0.866 | 0.667 | negative | strong neg |
| 0.00 (0.50,0.50) | 0.667 | 0.674 | **flat ~0.66** | n.s. |
| 0.00 (0.05,0.05) | 0.668 | 0.658 | flat ~0.66 | n.s. |
| 0.00 (0.95,0.95) | 0.656 | 0.661 | flat ~0.66 | n.s. |
| +0.45 (0.50,0.05) | 0.391 | 0.664 | positive | strong pos |
| **+0.90** (0.95,0.05) corr.fragmented/err.concentrated | 0.111 | 0.686 | **POSITIVE** (raising recall HELPS) | **z = +41.6** |

**Sign flip CONFIRMED:** d(acc)/dr is strongly NEGATIVE at phi≪0 (z=−19.8) and strongly POSITIVE at phi≫0 (z=+41.6), flat at phi=0. All curves CONVERGE to ~0.66 at r=1.0 — full merge erases the asymmetry (mechanistically correct: at perfect recall every surface form of a class collapses to one bucket, so the within-class entropy that drove the asymmetry no longer matters; what remains is the p_C=0.45 plurality baseline). This is exactly the predicted behaviour: the canonicalizer recall knob is a NEGATIVE-capable causal lever whose sign is set by fragmentation asymmetry, contradicting the field's monotone "merge-more = better".

## 2. PRECISION-ARTIFACT CONTROL — pure RECALL phenomenon, NOT over-merge — PASSED
results/precision_ctrl.csv. Re-run r=0→1 at q∈{1.0,0.8,0.6}:

| phi | q=1.0 (r0→r1) | q=0.8 | q=0.6 |
|---|---|---|---|
| −0.90 | 0.982 → 0.666 (drop 0.316, **z=−28.2**) | 0.783 → 0.635 (z=−11.3) | 0.653 → 0.646 (z=−0.4, n.s.) |
| +0.90 | 0.097 → 0.681 (rise 0.584, **z=+53.5**) | 0.384 → 0.642 (z=+14.6) | 0.590 → 0.634 (z=+3.0) |

**The negative slope at phi≪0 appears at q=1.0 (FULL precision, no over-merge possible), z=−28.2.** Therefore it is a pure RECALL phenomenon — NOT a precision/over-merge artifact (would have required q<1). 
**Honest nuance:** the effect ATTENUATES as precision drops — by q=0.6 the negative slope is essentially gone (z=−0.4). This is expected: lowering precision (over-merging distinct classes at r=0) pre-collapses buckets and pushes every cell toward the same ~0.65 over-merged baseline, washing out the recall-driven asymmetry. The phenomenon is real and load-bearing precisely in the clean/high-precision regime — which is the regime real answer-equivalence canonicalizers target.

## 3. SECONDARY — ranking inversion of two FIXED models — CONSTRUCTED
results/inversion.csv (regenerated by researcher-0048b). Two FIXED models, same samples per seed, ONLY the canonicalizer recall swapped (r_low=0.0 vs r_high=1.0), q=1.0, 30 seeds:
- **Model A** = correct-FRAGMENTED (H_C=0.95, H_W=0.05; phi=+0.9), p_C=0.50 — benefits from recall.
- **Model B** = errors-FRAGMENTED (H_C=0.05, H_W=0.95; phi=−0.9), p_C=0.28 — hurt by recall.

| recall | A acc | B acc | A−B | |z| | rank |
|---|---|---|---|---|---|
| r_low=0.0  | 0.166 | 0.763 | **−0.597** | **48.4** | **B > A** |
| r_high=1.0 | 0.807 | 0.145 | **+0.662** | **52.8** | **A > B** |

**INVERSION CONSTRUCTED:** at low recall B beats A (z=−48.4); at high recall A beats B (z=+52.8); both gaps |z|≫2 with 30 seeds. The maj@k RANKING of two fixed models is reversed purely by changing the canonicalizer's equivalence recall — no change to model, samples, or scoring.

**Note on the prior attempt:** the originally-committed inversion.csv (A_pc=0.42, B_pc=0.46) did NOT invert (A stayed below B at both r; gap narrowed −0.927 → −0.108 but A never overtook B). Root cause: B's p_C=0.46 pinned its r=0 accuracy near the ceiling (~0.99), too high for A to overtake after both converge to baseline. Lowering B's p_C off the saturation point (to 0.28) and raising A's (to 0.50) keeps the SAME mechanism but lets A overtake — the inversion exists across a broad params region (a_pc∈[0.45,0.65] × b_pc∈[0.20,0.40], dozens of clean significant inversions found; A_pc=0.50/B_pc=0.28 chosen as a balanced central pick). The (ci95 column for the A−B rows stores |z|, not a CI, by convention.)

---

## WHAT L1 SHOULD MEASURE
1. **Real canonicalizers, real benchmarks:** swap actual answer-equivalence normalizers of differing recall (e.g. exact-match vs LLM-judge vs symbolic) on real free-form QA/math (GSM8K-style, free-form) and measure d(maj@k)/d(recall) vs an empirically-estimated fragmentation asymmetry per dataset. Does phi predict the slope sign in the wild?
2. **Estimate phi from data without GT-at-inference:** can phi (correct-vs-error fragmentation asymmetry) be estimated from unlabeled answer-cluster statistics so practitioners know IN ADVANCE whether raising recall will help or hurt?
3. **Find a real model pair whose maj@k ranking flips** under two real canonicalizers on a fixed benchmark — the in-the-wild analogue of the constructed inversion (the leaderboard-hazard demonstration).
4. **Precision×recall joint map on real normalizers:** confirm the high-precision regime is where the recall sign-flip is load-bearing (matches the q-attenuation seen here).

## ARTIFACTS
- PRE_REGISTRATION.md (committed before run)
- run.py (primary + precision-control + original inversion sweep)
- inversion_final.py (researcher-0048b: corrected inversion construction)
- results/primary.csv, results/precision_ctrl.csv, results/inversion.csv (regenerated)

## PRE-REG (committed pre-run 9a7635c)
# PRE_REGISTRATION — EXP-0050 / CLAIM-0048
**Researcher:** researcher-0048 (PERSISTENT-SEEDER, PROJ-0018, TASK-0040)
**Committed BEFORE any run.** L0: CPU-only, stdlib-only, SERIAL, <=15 min.

## CLAIM
Increasing an answer-equivalence canonicalizer's RECALL (how aggressively it merges
truly-equivalent free-form answers before a self-consistency majority vote) does NOT
monotonically improve maj@k accuracy: its sign is governed by the correct-vs-incorrect
FRAGMENTATION ASYMMETRY. When incorrect mass is concentrated on one dominant wrong
attractor while correct mass is fragmented across equivalent surface forms, raising
recall RAISES accuracy; reversed (correct near-canonical, errors fragmented), raising
recall LOWERS maj@k and can INVERT the maj@k ranking of two FIXED models.

EMPIRICAL-phenomenon claim. NOT metric-validity (it is a causal intervention on the
canonicalizer recall knob). No closed form.

## FALSIFIABLE QUESTIONS
- PRIMARY: Does d(maj@k acc)/d(recall r) CHANGE SIGN as fragmentation-asymmetry phi
  crosses a threshold — going NEGATIVE in the errors-fragmented / correct-concentrated
  regime (phi >> 0)?
- SECONDARY (ranking hazard): Can two FIXED models A,B (fixed sample sets) have
  rank(A,B) under LOW-recall canonicalizer OPPOSITE to rank under HIGH-recall — with
  model+samples held constant, only the canonicalizer swapped?

## GENERATIVE MODEL (harness OWNS the GT — anti-circular)
- Problem set: N_PROBLEMS = 60 problems per condition.
- Each problem has ONE correct class C with surface forms {c_0..c_{Sc-1}} (all truly
  equal to gold), and M_INC = 3 incorrect classes, the FIRST being the "dominant wrong
  attractor", each with surface forms {w_j_0..}.
- Surface forms are UNIQUE integer string tokens ("c<cls>_<idx>"). Two strings are
  truly-equivalent iff same class. GT = membership map string->class (harness-owned).
- Sampling per problem: draw k=20 answer STRINGS.
  - Total correct mass p_C (swept around realistic regime); remaining 1-p_C split over
    incorrect classes with the dominant attractor taking DOM_FRAC=0.7 of incorrect mass.
  - WITHIN the correct class, surface-form probs follow a "spread" controlled so that

## ORCHESTRATOR POSTURE: strongest+best-controlled candidate of the expansion (both parts held, precision-controlled, anti-circular, foundational incumbent CJT/plurality addressed). If genuinely novel beyond vote-splitting + ecologically plausible, APPROVE toward an L1 (real MATH/GSM8K/GPQA + real checkpoints k=8-64 + two real graders exact-match-vs-Minerva/sympy: a real model whose maj@k DROPS under the higher-recall grader + a real pairwise leaderboard inversion from swapping ONLY grader recall — quantifying how much published SC leaderboard ordering is an extraction-stage artifact). If it's a vote-splitting costume / precision-caveat is fatal / inversion is ecologically implausible, say YELLOW or RED honestly. Real 6/6 by role.
