# PROJ-0023 — Eval-and-safety: n-gram decontamination is a LENGTH-BIASED test-set sampler -> inflates post-decontam accuracy (EMPIRICAL PHENOMENON)
Fresh area: eval-and-safety (benchmark integrity / decontamination methodology). EMPIRICAL-phenomenon. Survivor of
scout-H. THESIS: standard GPT-3/Llama n-gram-overlap decontamination ('remove any test item sharing an >=k-gram with
the training corpus') deletes test items with prob MONOTONE-INCREASING in item length (union-bound over per-n-gram
match events), so the SURVIVING benchmark shifts toward SHORTER items; when item difficulty is length-correlated
(empirically true on QA/reasoning), this length-selection biases post-decontam accuracy UPWARD by a margin growing
with corpus n-gram coverage, persisting at production k in {8,13}, EVEN THOUGH the filter never inspects difficulty
or labels. The harm is a property of the MITIGATION, not of contamination. Passes 6.5 of 7 killers: NOT metric-validity
(causal selection effect on the surviving population's estimand); NOT closed-form-tautology (removal-rises-with-length
is union-bound-flavored but the HEADLINE accuracy-inflation magnitude depends on coverage x length-dist x length-
difficulty curve, measured not forced; can come out null at alpha=0); foundational incumbent ADDRESSED (Brown2020
GPT-3 n-gram decontam 2005.14165, Llama3 Dubey 2407.21783 8-gram — benchmarked vs THEIR k); NOT known-mechanism-costume
(not 'selection bias relabeled' — the specific non-obvious mechanism is a CONTENT-AGNOSTIC filter acting as a
DIFFICULTY-biased sampler because longer items have combinatorially more corpus-collision chances; practitioners
believe decontam only removes CONTAMINATED items, claim is it removes CLEAN LONG items too); NOT wrong-currency
(reported benchmark accuracy in pct points, the release-decision number); NOT killer-#7 OMITTED-MITIGATION (the harm
IS the standard mitigation; the counter-mitigation raise-k 8->13->25 is MODELED + shown to only shift the removal curve
right, not remove monotonicity). RESIDUAL killer-#6 FLAG (honest): the inflation SIGN/SIZE hinges on length<->difficulty
being positive — documented for QA/reasoning (QuALITY 2112.08608, LongICLBench 2404.02060, med-QA 2310.07225) but
weaker on MCQ w/ answer-option boilerplate. MITIGATED: the STRUCTURAL composition-shift (survivors shorter) is
UNCONDITIONAL (holds even at difficulty _|_ length); the headline inflation is reported as a fn of a SWEPT coupling
alpha with an EXPLICIT alpha=0 honest-negative (flat slope -> informative 'composition-shifting but score-safe', not
dead). Anti-circular: GT = item true difficulty d_i + correct-prob p_i (harness-held, NEVER read by the filter); the
filter reads ONLY token sequences + corpus n-gram set. ALPHA=0 CONTROL is the load-bearing falsification (separates a
real selection-bias effect from a structural shift that doesn't move the score). L1 CONFIRMATORY (L0 anchors the
removal-monotonicity structurally): real MMLU/GSM8K/QuALITY + real GPT-3/Llama n-gram decontam vs a real web n-gram
corpus (C4/Pile) -> confirm removal-rises-with-length + survivor-shorter (anchored), measure real length-difficulty
slope from public per-item accuracy, report realized inflation.
