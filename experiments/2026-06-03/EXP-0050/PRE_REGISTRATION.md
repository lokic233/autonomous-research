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
    correct-class normalized entropy = H_C in [0,1].
  - WITHIN the dominant incorrect class, surface-form probs follow entropy H_W in [0,1].
  - phi = H_C - H_W  (correct-class entropy MINUS dominant-incorrect-class entropy).
    phi << 0  => correct concentrated, errors fragmented? NO — careful:
    By the claim's wording phi = (entropy of correct) - (entropy of dominant incorrect).
    phi LARGE NEGATIVE = correct CONCENTRATED, dominant-error FRAGMENTED
       (errors-fragmented / correct-concentrated regime) -> predict d(acc)/dr NEGATIVE.
    phi LARGE POSITIVE = correct FRAGMENTED, dominant-error CONCENTRATED
       -> predict d(acc)/dr POSITIVE.
  (We adopt this consistent convention throughout; the claim's prose label is mapped to
   the sign of phi explicitly here to avoid ambiguity.)
- Entropy of a class with n surface forms is realized via a temperature/Zipf knob; we
  use #forms and a skew exponent to hit target normalized entropy. Sc surface forms for
  correct, Sw for dominant incorrect, fixed Sc=Sw=6 so entropy range is comparable.

## CANONICALIZER (tested signal — reads ONLY surface strings, NEVER GT class)
- Operates on the multiset of k sampled strings. It MERGES string pairs into buckets.
- RECALL r in [0,1]: fraction of truly-equivalent (same-class) string PAIRS that it
  correctly merges. Implemented by, for each class present, with prob r linking each
  surface form to the class's canonical representative (union-find); residual forms
  stay as singletons. r=0 ~ exact-match (no merging across surface forms), r=1 ~ perfect
  merge of every equivalent form. Canonicalizer NEVER sees the class label as GT — it is
  GIVEN an oracle-noisy equivalence signal of strength r (models a real normalizer whose
  equivalence-detection recall is r). It does NOT know which bucket is correct.
- PRECISION q in [0,1]: prob that it does NOT over-merge a genuinely-distinct pair.
  q=1 = never over-merges (clean). q<1 = with prob (1-q) it links two DIFFERENT-class
  representatives (over-merge). Swept SEPARATELY. Primary test holds q=1.0 (high prec).

## SCORING (GT used ONLY here)
- Plurality vote over merged buckets; winning bucket's MEMBER strings are looked up in GT;
  bucket scored CORRECT iff a plurality of its mass is the correct class (bucket label =
  GT class of the strings it contains; for over-merged buckets, label = majority GT class
  in bucket). maj@k = fraction of problems where winning bucket is correct-labeled.

## SWEEPS / SEEDS
- phi grid via (H_C, H_W) pairs: H in {0.05,0.5,0.95}; phi = H_C-H_W spanning -0.9..+0.9.
- recall grid r in {0.0,0.2,0.4,0.6,0.8,1.0}.
- precision: primary q=1.0; control branch q in {1.0,0.8,0.6}.
- p_C fixed at 0.45 (plurality-but-not-majority regime; the interesting regime where
  fragmentation can flip the winner). Also report p_C=0.40 robustness.
- SEEDS = 30 (>=20). N_PROBLEMS=60 -> 1800 problem-instances per cell. Serial, fast.
- 95% CIs via normal approx on per-seed accuracy (n=30 seeds), and bucket via the
  per-seed std error.

## PRIMARY TEST
At fixed q=1.0: fit/measure sign of (acc@r=1.0 - acc@r=0.0) at phi<<0 vs phi>>0.
Require: at phi most-negative, acc(high r) significantly BELOW acc(low r) (CIs disjoint
or two-sample z p<0.05) => d(acc)/dr NEGATIVE. At phi most-positive, acc(high r)
significantly ABOVE acc(low r) => POSITIVE. SIGN FLIP = both hold.

## SECONDARY TEST (ranking inversion)
Construct A = correct-fragmented (phi>0), B = errors-fragmented (phi<0), tuned to
similar maj@k at MID recall. Find (r_low, r_high) with rank(A,B) flipped, CIs significant.

## PRECISION-ARTIFACT CONTROL
Re-run primary at q in {0.8,0.6}. If NEGATIVE slope at phi<<0 ONLY appears when q<1
(over-merge), report PRECISION-ARTIFACT. If it appears at q=1.0, it is a pure RECALL
phenomenon.

## HONEST OUTCOMES
- HELD: sign flips with phi at q=1.0 AND a real ranking inversion constructed.
- HONEST-NEGATIVE: d(acc)/dr >= 0 everywhere at matched precision AND no inversion ->
  field's monotone "merge-more=better" holds; clean publishable negative.
- PRECISION-ARTIFACT: effect only via over-merge -> not a recall phenomenon.

## ANTI-PATTERNS RESPECTED
GT generative + harness-owned; canonicalizer never reads GT; GT only at scoring.
No quantity on both sides. Not metric-validity (causal recall intervention). Not
closed-form. Screened vs Wang2022 (pre-canonicalized atoms + monotone), CJT (binary+
monotone fixed atoms), plurality vote-splitting (fixed atoms), Representation-/Semantic-/
Mirror-/Ranked-Voting-SC (all frame more-merging as monotone-good). Novelty = recall as a
NEGATIVE-capable causal knob tied to fragmentation asymmetry + ranking inversion.
