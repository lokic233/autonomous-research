# PROJ-0029 — Tokenization/preprocessing x Data-systems CROSS-AREA: dedup false-negatives driven by normalizer DIVERGENCE between the model tokenizer + the deduper (EMPIRICAL PHENOMENON)
2nd cross-area coupling claim (different seam from CLAIM-0058 runtime->safety). Couples TOKENIZATION/PREPROCESSING (the
model tokenizer's normalization form NFC/NFKC/NFKD/casefold — owned by the modeling team for vocab efficiency) x DATA-
SYSTEMS (the dedup pipeline's recall — owned by the data-platform team, tuned via shingle-k/perms/bands/threshold). SEAM:
the deduper's OWN normalizer + the model tokenizer's normalizer are configured INDEPENDENTLY in different subsystems +
routinely diverge; the coupling = the DIVERGENCE. PRIMARY THESIS (the robust, load-bearing claim): dedup document-pair
FALSE-NEGATIVE rate (missed true duplicates, where 'true duplicate' = IDENTICAL under the MODEL's normalization) is
driven by the Unicode-equivalence DIVERGENCE between the deduper's normalizer and the model tokenizer's — NOT by surface
edit distance. When the model normalizes MORE strongly than the deduper (tokenizer NFKC+casefold, deduper NFC-only/raw),
a class of pairs identical FROM THE MODEL'S PERSPECTIVE (same token seq) escapes the deduper. SECONDARY/FLAGGED (riskier,
NOT the headline): the FN rate jumps in DISCRETE STEPS as the normalizable-pair fraction crosses LSH-band thresholds. ★
ORCHESTRATOR GUARD on the step sub-claim: banded LSH INHERENTLY has a step-shaped S-curve collision probability (textbook)
— the L0 MUST ISOLATE any genuine equivalence-class step from the LSH-S-curve artifact (else trips killer #2/#9). The
PRIMARY divergence-drives-FN result does NOT depend on the step structure + is the robust claim; if the step is just the
LSH S-curve, DOWNGRADE to primary-only (still novel, still cross-area, clean null). NULL EXITS (genuine): (a) typo-arm
(non-normalizable random edits, matched edit-distance) FN flat across deduper normalizers -> divergence irrelevant; (b)
deduper=NFKC+casefold (matches model) -> FN collapses to baseline (confirms the coupling IS the divergence); (c) FN smooth
in edit-distance not stepped -> step sub-claim falsified (primary survives). Passes killers: #10 genuine null (corpus can
be built so dup pairs differ only by random typos -> divergence irrelevant -> flat; not construction-forced); #9 not-
textbook ('normalize before hashing' is textbook, but that a SECOND subsystem's [the model's] normalizer sets the dedup
recall ceiling, + the divergence is the driver, is not — Lee2022/UAX#15 are the incumbents this builds on, silent on the
seam); Lesson-A defense = the cause lives in a subsystem (tokenizer normalization) dedup researchers NEVER instrument as an
input (verified uncrossed, zero direct hits); Lesson-B alias control = HOLD shingle-set size + raw edit-distance FIXED
across arms, vary ONLY normalizable-vs-random-typo (FN moves only in the normalizable arm -> cause is divergence not
difficulty) + sweep Jaccard threshold (step persists or is an artifact); Lesson-C + #7 production baseline = real MinHash
config (k=5 char or word-13gram, 128 perms, threshold~0.8, WITH its own NFC normalization), standard mitigation 'normalize
in the deduper too' modeled (force both identical -> FN to baseline = the null arm); NOT metric-validity (FN = missed-true-
dup-pairs/total, GT=identical-under-model-normalization HARNESS-OWNED, deduper never reads GT = anti-circular); NOT closed-
form (MinHash collision under partial-overlap + non-linear equivalence collapse, measured); RUNTIME-MITIGATION irrelevant
(recall/correctness property not a fixed cost). BOUNDARY (orchestrator-verified DISTINCT): CLAIM-0045=BM25 ranking inverted-
U (different mechanism/metric/area); CLAIM-0048=eval-aggregation canonicalizer-recall (eval not dedup); CLAIM-0054=CC-dedup
chaining (graph-topology internal to dedup, not a normalizer-divergence equivalence-class effect); CLAIM-0042=contamination
granularity. NO collision. PRIOR-ART: side-A Unicode UAX#15 + tokenizer-normalization-for-fertility (Arnett2025); side-C Lee2022
dedup + Kandpal2022 + BigCode near-dedup + Noise-Robust-Dedup ICLR23 (all frame dedup recall as shingle/threshold/hash +
surface-noise, NEVER an external model-normalizer); seam ZERO direct hits. L1: real multilingual C4/OSCAR shard + a real
tokenizer HF normalizer config (model side) + datatrove/text-dedup MinHash (data side) -> rate of model-identical dup pairs
surviving production dedup purely from normalizer divergence + whether aligning the deduper's normalizer recovers them
(hidden duplicate exposure -> memorization/privacy/contamination risk from the unaudited seam).
