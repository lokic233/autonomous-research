# EXP-0053 PRE-REGISTRATION (LOCKED)

**LOCK TIMESTAMP (UTC):** 2026-06-01T16:09:03Z  (`date -u` pasted before any measurement)
**Agent:** researcher-0017-L0-r6   **Project:** PROJ-0007   **Claim:** CLAIM-0017   **Verdict satisfied:** VERDICT-0060
**Level:** L0, Mac CPU, stdlib analysis + production tokenizer (EXP-0049 venv: transformers 4.57.6 Rust fast).
**Prompt version:** v001.

This file is committed (`ros commit`) BEFORE the main measurement run. Thresholds below are FROZEN.

---
## THESIS (restated, falsifiable)
Cross-SESSION prefix-cache reuse (vLLM APC / RadixAttention / provider prompt caching) is bounded ABOVE the
naive shared-text fraction by a STRUCTURAL cause: tool-schema / system-prompt MICRO-DRIFT (per-session
timestamps, session-IDs, dynamically-ordered tool/skill lists, cwd/tenant fields) embedded EARLY in the
shared HEAD, which breaks the cacheable cross-session prefix before most of the shared content.
Falsifiable content = realized reuse bounded by a NAMED, PREDICTABLE drift cause, measured over a
DRIFT-FREE-TEMPLATE baseline — NOT merely equal to shared-text, and NOT a prompt-engineering anti-pattern
that a caching-best-practice canonicalizer removes (RE-B1 KILLER).

## NON-COLLISION (frozen)
- INVERSE of DEAD-0006: there token-prefix PREDICTS sharing; here token-prefix FAILS to share cross-session.
- DISTINCT from PROJ-0005 / CLAIM-0014: PROJ-0005 = intra-session LEXICAL BPE seam at the tool-result TAIL.
  PROJ-0007 = CROSS-session STRUCTURAL template drift in the shared HEAD. The RE-B4 fold-trigger is the
  boundary test: if cross-session first-divergences are predominantly BPE-seam (same chars, shifted tokens)
  rather than structural (different chars), the two collapse -> FOLD into PROJ-0005.

## DATA / UNIT OF ANALYSIS (frozen)
- Corpora (real production trace fleets): Claude Code (~248 jsonl, ~/.claude), Codex (109 jsonl, ~/.codex),
  Gemini (~84 chat json, ~/.gemini). Reuse EXP-0051 corpus-parsing layer for message extraction.
- **HEAD per session** = the leading template text the model receives that is intended to be shared across
  sessions, with volatile fields in their NATURAL production position:
  - **Codex (FAMILY 1, fully in-trace):** base_instructions.text (session_meta) ++ developer envelope in
    trace order [permissions, skills_instructions, available_skills]. Ground truth observed at lock time:
    base_instructions byte-IDENTICAL across all 109 sessions; available_skills block has 109 DISTINCT hashes
    (drifts every session) = the dynamically-ordered tool/skill list; permissions/skills_instructions ~4
    variants (cwd/sandbox/policy drift).
  - **Claude Code (FAMILY 2):** reconstructed env block using REAL per-session in-trace values
    (cwd, gitBranch, version, sessionId, ISO date from timestamp) in CC's documented env format, ++ the
    first user-message template text (static role skeleton). Env values are real (from trace); the wrapper
    format is CC's public `<env>` layout. Flagged as reconstructed-envelope in results.
  - **Gemini (FAMILY 3, sensitivity):** messages[0..k] role-template text + session envelope
    (sessionId/startTime/projectHash). Gemini stores no in-prompt system block; near-zero in-PROMPT drift
    expected -> reported as a degenerate/low-drift control family, NOT counted toward the >=2-family gate.
- **Reference R per family** (models APC warmed by one session, reused by the rest): the median-head-length
  session of the family (deterministic medoid proxy). Each OTHER session i is measured vs R -> distribution
  over n-1 sessions, bootstrapped. (Sensitivity: also report group-wide common-prefix consensus.)
- **Tokenizer:** PRIMARY = gpt2 (Rust fast). SECONDARY (RE-B5 robustness) = qwen2-0.5b. Both from EXP-0049 venv.
- **Block size:** 16 tokens (APC/RadixAttention page granularity). Sensitivity at 8 and 32 reported.

## METRIC DEFINITIONS (frozen)
For session i vs reference R, token sequences H_i, H_R (tokenizer T):
- **realized_block_LCP(i)** = (# leading 16-tok blocks identical between H_i and H_R) x 16  [TOKENS].
  = the cross-session prefix an APC/RadixAttention cache actually reuses.
- **naive_shared(i)** = difflib.SequenceMatcher(H_i, H_R).ratio()-derived matched-token count
  = 2*M/(len_i+len_R) as a fraction, and matched-token COUNT for token units
  = the position-agnostic shared content (realistic upper bound a content-addressed/reordered cache hits).
- **shortfall(i)** = naive_shared_tokens(i) - realized_block_LCP(i)  [TOKENS, >=0 expected].
- A **canonicalizer** C (RE-B1) maps each head -> caching-best-practice form: strip volatile fields
  (ISO-8601 timestamps; UUID/session-IDs; absolute cwd/home paths; version strings; tenant ids) replacing
  with a fixed sentinel, AND canonicalize dynamically-ordered list blocks (available_skills / tool lists)
  by SORTING entries lexicographically, AND relocate the stripped volatile tokens to the head SUFFIX
  (per Anthropic/OpenAI guidance). Recompute realized/ naive/ shortfall on C(H).
- A **drift-free template control** D = head with ALL volatile fields neutralized to constants AND list
  blocks sorted (the theoretical no-drift skeleton). realized_block_LCP_D(i) = clean-baseline prefix.
- **drift_cost(i)** = realized_block_LCP_D(i) - realized_block_LCP_raw(i)  [TOKENS] = prefix lost to drift.

## GATES, THRESHOLDS, DECISIONS (FROZEN — pass/kill rules)

### RE-B1  LOAD-BEARING / KILLER  (caching-best-practice canonicalizer)
- Metric: shortfall_after = mean over sessions of [naive_shared_tokens(C) - realized_block_LCP(C)].
- **KILL (pre-registered honest negative)** if shortfall_after collapses to the block-quantization floor:
  shortfall_after mean < 16 tokens OR its 95% bootstrap CI lower bound <= 0. Interpretation: drift is a
  PROMPT-ENGINEERING anti-pattern (sort tool lists + move volatile fields to suffix) -> actionable PSA,
  NOT an architectural ceiling. Reported as a first-class negative.
- **PASS** iff shortfall_after mean >= 16 tokens AND 95% CI lower bound >= 16 tokens (shared content remains
  stranded outside the cacheable prefix even after best-practice canonicalization = architectural ceiling,
  driven by genuine cross-session tool-set MEMBERSHIP differences, not mere ordering).

### RE-B2  MINIMUM EFFECT SIZE  (drift-attributable, over drift-free control, not quantization)
- Metric: mean drift_cost over sessions [TOKENS].
- **PASS** iff mean drift_cost >= 16 tokens (>=1 full block) AND 95% bootstrap CI lower bound >= 16 tokens.
- **KILL** otherwise (effect indistinguishable from a single-block quantization artifact).

### RE-B3  DRIFT-CLASS PREDICTOR of first-divergence LOCATION
- Task: pool 16-tok blocks across all (i vs R) comparisons; binary label = 1 iff block is the FIRST
  divergent block for that comparison, else 0. Predictor score(block) = drift-class signal: presence of a
  volatile field instance (timestamp / UUID / path / version / list-reorder boundary) in that block, scored
  by earliness (earlier drift-class field => higher score). Model-free.
- **SHAM predictor**: score(block) = indicator of the first block containing ANY non-template byte (first
  byte differing from the static skeleton), no drift-class knowledge.
- **PASS** iff real-predictor AUC >= 0.70 AND real AUC > sham AUC (95% CIs; real beats sham, not just >0.5).
- **FAIL/weaken** otherwise.

### RE-B4  FOLD-INTO-PROJ-0005 numeric trigger
- For each comparison's FIRST divergent token: classify BPE-SEAM-DRIVEN vs STRUCTURAL. Window the underlying
  CHARACTER streams of H_i and H_R around the divergence char-offset (+/- 32 chars). If the characters are
  IDENTICAL (same text, divergence is a token-boundary shift only = CLAIM-0014 seam) -> BPE-seam-driven.
  If characters DIFFER -> structural drift.
- Threshold **X = 50%** (reasoning: a simple majority is the defensible boundary — if most cross-session
  first-divergences are the SAME mechanism PROJ-0005 already owns, PROJ-0007 is not a standalone phenomenon).
- **FOLD (clean kill of PROJ-0007 standalone)** iff >= 50% of first-divergences are BPE-seam-driven.
- **STAY DISTINCT** iff < 50% (majority structural = genuine content drift in the head = PROJ-0007 territory).

### RE-B5  TOKENIZER-SEAM STRATIFICATION
- Recompute first-divergence char-offsets under BOTH gpt2 and qwen2-0.5b. A STRUCTURAL divergence is
  tokenizer-invariant (same char-offset +/- small under both); a pure BPE seam is tokenizer-specific.
  Report: fraction of first-divergences that are tokenizer-invariant (structural), and re-report RE-B2
  drift_cost with seam-adjacent (tokenizer-specific) divergences excluded. This disentangles structural
  drift from the CLAIM-0014 seam mechanism. (Diagnostic; no independent pass/kill — feeds RE-B4 robustness.)

### RE-B6  TEMPLATE-FAMILY STRATIFICATION
- >=2 DISTINCT template families REQUIRED: Codex (family 1) AND Claude Code (family 2) are distinct skeletons.
  Gemini reported as low-drift sensitivity family (not counted toward the gate). All gates reported PER FAMILY.
- **PASS** iff the headline outcome (PASS or KILL) is consistent in DIRECTION across the >=2 counted families;
  divergence across families is reported explicitly, not averaged away.

### RE-B7  VENDOR GUIDANCE AS QUANTIFIED PRIOR ART
- Cite Anthropic + OpenAI prompt-caching guidance on volatile-field placement / static-first field ordering
  / cache-breakpoint invalidation as the QUANTIFIED mechanism B measures against (not folklore). Verified via
  internet at run time; saved to prior_art/PROJ-0007/. (Deliverable gate, not statistical.)

### RE-B8  REALISTIC CACHE-BEHAVIOR BASELINES
- Characterize from docs/specs: SGLang LPM (longest-prefix-match radix) / DFS routing-key, TensorRT-LLM
  full-block reuse + concurrency, and cache_salt effects, as the realistic cache behaviors the realized
  ceiling is measured against. Real APC cross-request hit counters require L1/H100 -> explicitly flagged
  OUT-OF-SCOPE for this L0. Saved to prior_art/PROJ-0007/. (Deliverable gate, not statistical.)

## OVERALL KILL RULE (any one fires -> HONEST NEGATIVE, report + STOP, do NOT force a positive)
1. RE-B1 shortfall VANISHES under canonicalization (shortfall_after < 16 tok or CI_lo <= 0), OR
2. RE-B2 drift-attributable effect-size floor not met (mean drift_cost < 16 tok or CI_lo < 16 tok), OR
3. RE-B4 fold-trigger fires (>= 50% of first-divergences BPE-seam-driven) -> fold into PROJ-0005.
An honest negative (prompt-eng PSA, or fold) is a FIRST-CLASS publishable outcome. NEVER fabricate data.

## DELIVERABLES MAP (-> VERDICT-0060 required_evidence)
impl/PRE_REGISTRATION.md (this, committed pre-run) ; impl/ harness (parser->cross-session block-LCP->
canonicalizer->drift-free control->drift-class predictor+sham->bootstrap CIs) ; results/summary.json
(per-family per-gate pass/kill, effect sizes+CIs, AUCs) ; results/analysis.md (narrative, RE-B1 verdict,
RE-B4 fold decision) ; results/per_row CSV ; prior_art/PROJ-0007/ (RE-B7 + RE-B8).

## RNG / REPRODUCIBILITY
All bootstrap + null/predictor RNG seeded 42 (matches EXP-0049/0051 convention). Bootstrap B=10000 for
scalar CIs, B=2000 for AUC CIs. Deterministic medoid (median head length). No GPU. No network during the
measurement run (network only for RE-B7/B8 prior-art, recorded separately).
