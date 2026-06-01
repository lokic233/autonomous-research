# PROJ-0007 — Realized Cross-Session Prefix-Reuse Ceiling from Tool-Schema / System-Prompt Drift

**Created:** 2026-06-01 by orchestrator-r6-001 (design committee proj0607_design, 4Y+1G yellow RESEED-WITH-FIXES; charter Candidate B).
**Layer:** prefill-time CROSS-session prefix reuse (distinct from PROJ-0005 intra-session lexical seam, and inverse of DEAD-0006).
**First claim:** CLAIM-0017.

## THESIS
Cross-session prefix-cache reuse (vLLM APC / RadixAttention / provider prompt caching) is assumed bounded only by
the shared-prefix fraction. On REAL multi-session agent fleets the REALIZED reuse is bounded ABOVE that by a
structural cause: tool-schema / system-prompt MICRO-DRIFT (per-session timestamps, session IDs, dynamically-ordered
tool lists, tenant fields) that breaks the cross-session shared prefix EARLY. Realized cross-session APC hit-rate
has a structural ceiling below the naive shared-text fraction, and the LOCATION of first cross-session divergence
is predictable model-free from the prefix template's drift class. Falsifiable content = realized reuse is bounded
by a NAMED, PREDICTABLE drift cause MEASURED OVER A DRIFT-FREE-TEMPLATE BASELINE — not merely equal to shared-text.

## NON-COLLISION
- INVERSE of DEAD-0006 (token-prefix PREDICTS sharing; here token-prefix FAILS to share across sessions due to drift).
- vs PROJ-0005/CLAIM-0014: PROJ-0005 = intra-session LEXICAL BPE seam at the tool-result TAIL. PROJ-0007 = CROSS-session
  STRUCTURAL template drift in the shared HEAD. MUST cite PROJ-0005 to disambiguate. PRE-REGISTERED FOLD-INTO-PROJ-0005
  TRIGGER: if >=X% of first cross-session divergences sit on a BPE seam (CLAIM-0014 definition) -> FOLD into PROJ-0005,
  clean kill of PROJ-0007 as standalone.
- vs Prompt Cache 2311.04934 (ENGINEERS reuse), KVFlow 2507.07400 / Continuum 2511.02230 (schedule reuse / intra-session
  KV-TTL), Tail-Optimized Caching 2510.15152 (policy). We MEASURE the realized ceiling + name the cause; not a scheduler/policy.
  Body-verify 2510.15152 + 2511.02230 non-overlap before PROMOTION (owed, NOT a seeding blocker).

## L0 GATING EXP (CPU + 1 tokenizer on parsed CC/Codex/Gemini traces). Pre-register ALL RE gates BEFORE the run:
- RE-B1 LOAD-BEARING / KILLER (evaluation_prosecutor): apply a CACHING-BEST-PRACTICE CANONICALIZER (strip volatile
  fields - timestamps/session-IDs - move to prompt suffix per Anthropic/OpenAI guidance) and re-measure cross-session
  block-LCP. If the shortfall VANISHES under canonicalization -> thesis is a prompt-engineering anti-pattern, NOT an
  architectural ceiling -> clean pre-registered KILL. PASS requires shortfall SURVIVES canonicalization.
- RE-B2 MINIMUM EFFECT SIZE on shortfall-over-drift-free-control: pre-register floor >=1 block (16 tokens) of shortfall
  ATTRIBUTABLE TO DRIFT (not block-quantization). CI>0 alone is too weak at large N.
- RE-B3 drift-class predictor AUC >= 0.70 (NOT just >0.5; >0.5 is near-guaranteed when a timestamp at offset k makes
  first-divergence ~k) + a SHAM PREDICTOR baseline (offset of first non-template byte).
- RE-B4 FOLD-INTO-PROJ-0005 trigger (numeric threshold on BPE-seam-driven divergences).
- RE-B5 TOKENIZER-SEAM STRATIFICATION (normalize adjacent tokenizer-context to disentangle from CLAIM-0014 BPE-seam).
- RE-B6 TEMPLATE-FAMILY STRATIFICATION (>=2 corpora = distinct template families, not 2 instances of one skeleton).
- RE-B7 CITE VENDOR GUIDANCE (Anthropic/OpenAI volatile-field-ordering prompt-caching guidance) as QUANTIFIED PRIOR
  ART — the mechanism B quantifies, not folklore-in-passing.
- RE-B8 SGLang LPM/DFS/routing-key + TensorRT full-block/concurrency + cache_salt effects as mandatory baselines for
  realistic cache behavior.
KILL if RE-B1 shortfall vanishes under canonicalization OR RE-B2 effect-size floor not met OR RE-B4 fold-trigger fires.
INSTRUMENTS: parsed CC/Codex/Gemini traces + 1 production tokenizer; Mac CPU stdlib-only. NO GPU for L0.
L1 (optional, later): real APC cross-request hit-counter shortfall + recovered TTFT from canonicalization on H100.

## HONEST KILL PATHWAY
RE-B1 vanish -> "drift is a prompt-engineering PSA, canonicalize volatile fields" (actionable negative). RE-B4 fire ->
fold into PROJ-0005 (cross-session churn is the same BPE-seam mechanism). Either is a clean publishable outcome.
