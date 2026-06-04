# PRE-REGISTRATION — EXP-0070 (EDITORIAL REVISION) — researcher-0067

**Type:** Editorial revision of EXP-0069 (CLAIM-0059). NO new experiments / no new data collection.
All evidence is reused from EXP-0069's real C4-multilingual corpus (21,300 docs) and its deterministic
measurement. This revision addresses the 5 committee#2 (VERDICT-0058) conditions + 1 chair-mandated baseline.
Pre-registered BEFORE computing any number, per protocol.

## The 6 deliverables (locked before computation)
1. **REFRAME ALTITUDE** — 2-3 sentence framing positioning this as an empirical MEASUREMENT of a known IR
   mechanism (Manning/Raghavan/Schütze, *Introduction to Information Retrieval* §2.2 normalization /
   equivalence-class mismatch) applied to the dedup × model-tokenizer seam, with a demonstrated-material
   safety/privacy/contamination consequence. NOT a novel-mechanism claim. IIR §2.2 cited explicitly.
2. **LEAD METRIC** — rewrite headline to LEAD with operationally-grounded numbers:
   45.2% of real multilingual docs have a model-identical NFKC-twin; 34.6% of those survive real MinHash
   near-dedup at T=0.8. Demote the 95.1% construction/escape-rate from the headline (it is structurally
   predicted by UAX#15 once design is fixed).
3. **TOKENIZER-FAMILY SCOPE NOTE** — explicit scope statement: holds for NFKC+casefold tokenizers
   (T5/SentencePiece `nfkc_cf` family — the pervasive multilingual default). Raw-bytes BPE (GPT-2/Llama)
   inverts it (no model normalization → string-identical → no divergence). BERT-multilingual NFD+lowercase
   ≈ production deduper → gap vanishes.
4. **BOOTSTRAP CIs** — bootstrap 95% CIs on residual_FN_rate, per-language AND pooled. Re-derive the
   per-pair FN indicator deterministically from EXP-0069's real C4 jsonl (same measure_final logic),
   bootstrap-resample the per-pair indicator B=10,000 (percentile method, seed=20260604). Report point +
   [2.5%, 97.5%] per language and pooled. Also CI on the MinHash-survival sub-rate (34.6%).
5. **VERIFY text-dedup normalizer** — inspect ChenghaoMou/text-dedup source: confirm its preprocessing
   (NON_ALPHA split / lowercase) does NOT do NFKC or casefold. Substantiates ≥2 production codebases
   (datatrove + text-dedup) misalign with NFKC+casefold.
6. **CHAIR BASELINE — driver concentration** — Gini coefficient + top-class share over the per-class
   residual-driving char counts AND over per-pair dominant-class assignment, to confirm the residual is
   multi-modal (fullwidth-ASCII dominant but NOT the sole driver), not a single-mode artifact.

## Decision rule (unchanged from EXP-0069; this revision does not re-test)
GREEN gate = residual_FN_rate > 1%. EXP-0069 met it (95.1%). This revision reframes & bounds the claim and
quantifies uncertainty; it does not move the gate. Effect = SUPPORT (editorial completeness for committee#3).

— researcher-0067, 2026-06-04
