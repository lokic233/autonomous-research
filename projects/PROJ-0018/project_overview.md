# PROJ-0018 — Eval-and-safety: answer-canonicalizer RECALL has a SIGN-FLIPPING effect on maj@k (fragmentation-asymmetry-governed); harness-induced leaderboard inversion (EMPIRICAL PHENOMENON)
Fresh area: eval-and-safety (self-consistency / majority-vote aggregation x answer-extraction stage). EMPIRICAL-
phenomenon archetype, NO closed form (the sign-flip/inversion region of maj@k under a partially-merged fragmented
multinomial has no algebraic identity). Passes all 8 failure modes (scout-verified): NOT metric-validity (causal
intervention on canonicalizer recall, observe sign of Daccuracy + ranking flips); NOT closed-form; foundational
incumbent ADDRESSED (CJT Condorcet1785 binary+monotone, plurality vote-splitting assume FIXED atoms — novel
content = a measurement-stage recall knob whose effect CHANGES SIGN with fragmentation asymmetry, which none
state); NOT known-mechanism-costume (textbook vote-splitting: merging helps the split side; novel = the ASYMMETRIC
sign flip — when ERRORS are fragmented, higher recall consolidates WRONG mass + demotes correct -> ranking
inversion); NOT wrong-currency (measured in maj@k accuracy + pairwise rank exactly); NOT 3 anti-patterns (recall
is the swept INDEPENDENT variable, not an under-tuned baseline; no KV-reuse; no logprobs/relabeling — votes over
discrete surface forms); ecologically valid (lm-eval-harness/Minerva/sympy graders differ in equivalence recall).
THESIS: raising an answer-equivalence canonicalizer's RECALL (how aggressively it merges truly-equivalent free-form
answers before self-consistency majority vote) does NOT monotonically improve maj@k accuracy — its SIGN is governed
by the correct-vs-incorrect FRAGMENTATION ASYMMETRY. Errors concentrated + correct fragmented -> higher recall
HELPS; correct near-canonical + errors fragmented -> higher recall LOWERS maj@k and can INVERT the maj@k ranking
of two models (model+samples held FIXED, only the canonicalizer changes). Anti-circular: GT = which surface-form
strings belong to the correct equivalence class (harness-owned generative fact); the canonicalizer reads ONLY
surface strings, NEVER the GT label; scoring uses GT only at scoring time. Honest-negative (informative): if
d(acc)/d(recall)>=0 everywhere + no inversion under matched-PRECISION canonicalizers -> field's monotone
'merge-more=better' assumption HOLDS, self-consistency robust to extraction recall (clean publishable negative).
Precision-control rules out over-merge artifact. Prior-art: Wang2022 self-consistency (2203.11171, assumes
pre-canonicalized atoms, monotone vote); CJT/plurality social-choice (fixed atoms); Representation-Consistency
(2506.21590)/Semantic-SC/Mirror-Consistency/Ranked-Voting-SC (ALL frame more-merging as monotonically helpful).
Delta = canonicalizer recall as a causal knob w/ a NEGATIVE-capable sign tied to fragmentation asymmetry + the
harness-induced leaderboard ranking inversion.
