# PROJ-0019 — Data-systems-for-ml: dedup REPRESENTATIVE-SELECTION induces a quality skew in the surviving corpus (order x heterogeneity), sign-flipping keep-first vs keep-last (EMPIRICAL PHENOMENON)
Fresh area: data-systems-for-ml (training-data curation / dedup pipelines). EMPIRICAL-phenomenon, NO closed form
(skew magnitude is an emergent product of within-cluster quality variance x order-quality correlation rho x
cluster-size dist; the LSH S-curve — the closed-form part — is DELIBERATELY EXCLUDED as the headline). Passes all
5 anti-patterns (scout-verified): NOT metric-validity (causal distributional effect on the RETAINED dataset from a
pipeline policy, not 'metric miscounts'); NOT closed-form (S-curve excluded; skew requires simulating cluster
formation under correlated ordering; honest-negative reachable); NOT foundational-incumbent-miss (benchmarked vs
Lee2021 seminal LM-dedup + Broder MinHash/Indyk-Motwani LSH + 2503.07879 unequal-quality — representative-selection
axis untouched by all); NOT known-mechanism-costume (selection-under-ordering of heterogeneous cluster members —
NOT chaining/regression-to-mean/Jensen; a newly-named curation bias); NOT wrong-currency (measured in the surviving
corpus's quality distribution, bound-independent, apples-to-apples on identical clusters). Ecologically plausible
(real crawl order correlated; real pipelines BigCode/datatrove/NeMo/datasketch keep-first by default; high-dup docs
skew higher-quality per 2503.07879). THESIS: when near-dup clusters contain members differing in a quality-correlated
observable (length/completeness), the standard keep-FIRST-encountered convention induces a systematic predictable
skew in the surviving corpus's quality distribution, governed by the order-quality correlation rho — and the skew
FLIPS SIGN between keep-first and keep-last while keep-random is unbiased, EVEN THOUGH all three remove the IDENTICAL
cluster set. Anti-circular: GT = latent quality q (generative, harness-owned); the dedup policy reads ONLY token-sets
+ stream positions, NEVER q; skew measured post-hoc. Honest-negative (reachable): at REALISTIC rho the skew may be
within noise of keep-random / not sign-flip / swamped by detection FP variance -> keep-arbitrary default vindicated
(publishable null). ORCHESTRATOR GUARD (load-bearing, brief the researcher): the sign-flip risks being NEAR-TRIVIAL
(if high-q appears first, keep-first obviously over-selects high-q). The NON-OBVIOUS falsifiable content is (a) the
MAGNITUDE at REALISTIC rho (estimated from real crawl-order clustering, NOT adversarial rho=1) and (b) that it's
INVISIBLE to standard dedup audits (identical cluster removal / FP rate). Must show the effect is LARGE at realistic
rho + audit-invisible, else it's a near-tautology -> weaken.
