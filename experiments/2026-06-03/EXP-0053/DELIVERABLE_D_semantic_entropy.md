# DELIVERABLE D — Distinction from semantic-entropy (Kuhn 2023 / Farquhar 2024)

Semantic entropy (Kuhn et al. 2023, "Semantic Uncertainty"; Farquhar et al. 2024, Nature)
clusters multiple sampled generations by bidirectional-entailment *meaning equivalence* and
computes the entropy *over meaning clusters* as an **uncertainty / hallucination-detection signal**
for a SINGLE model — higher semantic entropy => the model is less certain / more likely confabulating.
Its meaning-clustering is deployed to make the model's OWN confidence estimate more honest; it never
changes which answer is selected and is agnostic to ground-truth ranking between models.

CLAIM-0048 is a different object. (1) The clustering (here: the *canonicalizer*) is applied at the
**grader/aggregation** step, not as an uncertainty read-out: it merges answer *surface forms* into
equivalence buckets that then VOTE under maj@k. (2) The quantity of interest is **accuracy of the
selected answer**, not calibration of an uncertainty score. (3) The claimed phenomenon is a
**sign-flip on plurality accuracy**: varying canonicalizer RECALL (how aggressively numerically/
semantically equal surface forms are merged) can, in the fragmentation-asymmetric (phi<<0) regime,
**invert the maj@k ranking of two models** with samples held fixed — a comparative, ground-truth-scored
effect that semantic entropy, being a single-model uncertainty estimator, does not predict or describe.
In short: semantic entropy = meaning-clustering FOR UNCERTAINTY of one model; CLAIM-0048 =
recall-of-merging FLIPPING comparative plurality ACCURACY across models.
