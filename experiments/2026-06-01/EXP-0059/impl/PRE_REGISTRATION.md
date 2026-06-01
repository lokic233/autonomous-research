# EXP-0059 PRE-REGISTRATION (LOCKED)

**LOCK TIMESTAMP (UTC):** 2026-06-01T22:43:20Z  (`date -u` pasted before any measurement)
**Agent:** researcher-0024-L0-r7   **Sub-monitor:** sub-monitor-0013-r7
**Project:** PROJ-0013   **Claim:** CLAIM-0024
**Level:** L0, Mac CPU, pure-stdlib analysis + production tokenizer (EXP-0049 venv: gpt2 Rust fast — token counting only).
**Prompt version:** v001.

This file is committed (`ros commit`) BEFORE the main census run. Everything below is FROZEN. No threshold moves after commit.

CHARTER DISTINCTION (frozen): This is a **CHARACTERIZATION + POLICY-COMPARISON**, NOT a dAUC-predictability claim. No
logistic predictor, no dAUC gate. Deliverable = the GAP (realized vs canonicalized-max cross-session sharable
fraction) + its CONCENTRATION (per-volatile-class Lorenz/Gini + marginals) + a capacity-sim recompute-saved gap +
the collision cost. The unlocked mass is reported as an **UPPER BOUND** on recoverable mass (FIX-2), not a shippable
gain.

---
## THESIS (restated, falsifiable)
SGLang RadixAttention (2312.07104) / vLLM APC (2309.06180) share KV across requests by exact token-prefix match at
the radix branch point. The REALIZED cross-session exact-prefix sharable fraction on real agent traces is capped
below the structural maximum because a small, identifiable set of VOLATILE tokens (timestamps, abspaths, PIDs,
session UUIDs, cwd, ...) inside otherwise-identical system/tool-schema HEAD prefixes forces an early branch.
QUANTIFY: (i) realized exact-prefix sharable fraction (FLOOR), (ii) canonicalized-max after a FROZEN cheap
canonicalizer masking k volatile classes (CEILING), (iii) per-class unlocked KV mass + Lorenz/Gini (the
normalization BUDGET), (iv) capacity-sim recompute saved, (v) collision/alias cost. NOT a predictor.

CLEAN NEGATIVE is first-class: realized ~ canonicalized-max (volatile tokens NOT the bottleneck), OR unlocked mass
diffuse across many idiosyncratic classes (no cheap normalization lever).

## DATA / UNIT OF ANALYSIS (frozen)
- Corpora: Claude Code (`~/.claude/projects/*/*.jsonl`) and Codex (`~/.codex/sessions/**/*.jsonl`). REPORTED
  SEPARATELY with honest discordance disclosure (RE-A3). No averaging across instruments.
- **HEAD per session** = leading shared template text the model receives, volatile fields in NATURAL position.
  Reconstructed via the EXP-0053 parsers VERBATIM:
  - Codex: `base_instructions.text` (session_meta) ++ developer-role envelope text in trace order.
  - Claude Code: reconstructed `<env>` block from REAL per-session in-trace values (cwd, gitBranch, version,
    sessionId, ISO date) ++ first user-message template. Flagged reconstructed-envelope.
  - CC sessions grouped by drift-free 400-char template prefix; the LARGEST group = the cross-session fleet family
    (EXP-0053 convention). Codex uses all sessions with base+dev heads.
- **Reference R per corpus** = the median-head-length session (deterministic medoid proxy). Each OTHER session i is
  measured vs R. Distribution over n-1 sessions; session-clustered bootstrap.
- **Tokenizer:** gpt2 (Rust fast, EXP-0049 venv). **Block size:** 16 tokens (APC/RadixAttention page granularity).

## FROZEN VOLATILE-CLASS TAXONOMY + REGEXES (FIX-1)
Value-only spans (labels like "Session ID:" stay STATIC/shared). Non-overlapping, earliest-start wins; on identical
(start,end) the more SPECIFIC class (lower priority number) wins. Sentinel ` VOL ` replaces masked spans, which are
relocated to a HEAD SUFFIX (length-consistent canonicalizer, EXP-0053 convention).

Priority (specific first), name, regex literal:
1. `session_uuid` : `(?<=Session ID: )[0-9a-fA-F-]{8,}` AND `(?<=sessionId: )[0-9a-fA-F-]{8,}` AND
   `(?<="sessionId":")[0-9a-fA-F-]{8,}`  — session identifiers, context-anchored.
2. `cwd`          : `(?<=Working directory: )/[^\s"',:;\n]+` AND `(?<=cwd: )/[^\s"',:;\n]+`  — working dir, anchored.
3. `pid`          : `(?i)\bpid[\s:=]+\d{2,7}\b`
4. `timestamp`    : `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?`
5. `date`         : `(?<!\d)\d{4}-\d{2}-\d{2}(?!T)`
6. `uuid`         : `[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}`  (generic, non-anchored)
7. `abspath`      : `/(?:Users|home)/[^\s"',:;\n]+`  (generic abs path, non-anchored)
8. `version`      : `(?<!\d)\d+\.\d+\.\d+(?:\.\d+)?`
9. `epoch`        : `(?<!\d)1[0-9]{9}(?![0-9])`
10. `gitbranch`   : `(?<=Current branch: )[^\s\n]+` AND `(?<=gitBranch": ")[^"\n]+`
11. `sandbox`     : `` `sandbox_mode` is `[\w-]+` `` AND `` `(read-only|danger-full-access|workspace-write)` ``
12. `approval`    : `` `approval_policy` is `[\w-]+` `` AND `Approval policy is currently [\w-]+` AND
    `Approvals are your mechanism[^.]*\.`

**SEMANTIC class split (for FIX-2 / FIX-3 collision cost):**
- INERT (masking ~certainly output-equivalent): `session_uuid, pid, timestamp, date, uuid, epoch`.
- POTENTIALLY-SEMANTIC (masking MAY change model behavior — alias risk): `cwd, abspath, version, gitbranch,
  sandbox, approval`.

## CANONICALIZER (frozen)
- `mask_subset(text, S)` = strip spans whose class in S, replace in-place with sentinel, RELOCATE stripped text to a
  `<<VOLATILE_SUFFIX>>` head suffix. (No list-block sorting in the PRIMARY budget — list reorder is a different
  mechanism, not a volatile token class; a list-sort sensitivity is reported separately and is NOT part of the budget.)
- FLOOR = raw head, S = {} (no canonicalization).
- CEILING (canonicalized-max) = `mask_subset(text, ALL_CLASSES)`.
- Per-class marginal (add-one-in) = `mask_subset(text, {k})` vs FLOOR.
- Reference R is canonicalized the SAME way for each variant (block_lcp on matched variants).

## METRIC DEFINITIONS (frozen)
For session i vs reference R (gpt2 token-id lists), block size 16:
- `realized_raw(i)` = (# leading 16-tok blocks identical between raw heads) x 16 [TOKENS] = exact-prefix a radix
  cache reuses cross-session = FLOOR.
- `canon_max(i)`    = block_lcp on `mask_subset(ALL)` heads = CEILING.
- `gap(i)`          = canon_max(i) - realized_raw(i) = total recoverable KV mass for session i [TOKENS, >=0].
- `unlocked_k(i)`   = block_lcp(mask {k}) - realized_raw(i) = marginal prefix unlocked by masking class k alone.
- `realized_frac`   = mean realized_raw / mean canon_max (corpus-level FLOOR/CEILING ratio).
- per-class unlocked MASS = sum over sessions of unlocked_k(i). Lorenz/Gini computed across the 12 classes on these
  masses (FIX-4: ALSO report each class's Lorenz/marginal SEPARATELY, since Gini on k=3 is degenerate).

## GATES, THRESHOLDS, DECISIONS (FROZEN — verbatim from charter)

### RE-A0  MAGNITUDE FLOOR
- Metric: `realized_frac = mean(realized_raw) / mean(canon_max)`.
- **PASS (gap exists to explain)** iff realized_frac <= 0.6 (i.e. realized <= 0.6 of canonicalized-max; >=40%
  relative gap).
- **CLEAN KILL (first-class negative)** iff realized_frac > 0.6 (realized ~ canonicalized-max -> no ceiling; volatile
  tokens are NOT the bottleneck). Report and STOP forcing a positive.

### RE-A1  LOAD-BEARING CONCENTRATION (measurement, NOT a dAUC)
- After the FROZEN canonicalizer, do the **top-3 volatile classes (by unlocked mass) unlock >= 50% of total
  recoverable KV mass**? Denominator = sum of per-class marginal unlocked mass (cross-checked against gap).
- **PASS** iff top3_share >= 0.50 (concentrated cheap budget). **FAIL / CLEAN NEGATIVE** iff top3_share < 0.50
  (diffuse across many idiosyncratic classes -> no cheap lever). Lorenz/Gini reported; per-class marginals (FIX-4).

### RE-A2  POLICY COMPARISON (capacity sim)
- Simulate cross-session radix prefix sharing WITH vs WITHOUT canonicalizer at FIXED capacity C (sweep C as fraction
  of distinct heads). Sessions processed in deterministic file order; cache = up to C most-recently-used head
  anchors; per session, hit_tokens = max over cached anchors of block_lcp; recompute = len(head) - hit_tokens.
- Report: recompute-token-mass saved = recompute_raw - recompute_canon; hit-rate delta = hitrate_canon -
  hitrate_raw, at each C. **Decisive GAP** = the recompute mass saved by canonicalization at fixed capacity.
- Disposition: PASS = positive recompute-saved with non-trivial hit-rate delta at fixed capacity; else negative.

### RE-A3  ROBUSTNESS
- Session-clustered **2000x bootstrap** CI on the top-3 unlocked-mass fraction. The bootstrap MUST include
  **CLASS-SELECTION** as a variance source (FIX-1): each iter resamples BOTH sessions (clustered, with replacement)
  AND the 12 classes (with replacement), recomputing top-3 share within the resample.
- **HHI of unlocked mass across SESSIONS** (per-session gap shares); HHI > 0.2 => flag domination (one/few sessions
  drive the budget).
- CC AND Codex reported SEPARATELY; honest discordance disclosure.

## COMMITTEE MANDATORY FIXES (restated as analysis plan — NON-NEGOTIABLE)
- **[FIX-1 class-selection variance]** taxonomy + regexes FROZEN above; RE-A3 bootstrap resamples classes too.
- **[FIX-2 UPPER BOUND]** Report unlocked mass as an UPPER BOUND on recoverable mass, NOT a shippable gain. Prompt-
  output-equivalence under masking is NOT demonstrated at L0 -> default to UPPER BOUND. Stated explicitly in
  analysis.md. The POTENTIALLY-SEMANTIC class split flags where the upper bound is loosest.
- **[FIX-3 COLLISION]** Measure the regex-masking cache-collision FALSE-POSITIVE rate: among prefix matches that
  exist ONLY after canonicalization (the unlocked blocks), what fraction involve a masked span whose RAW value
  genuinely DIFFERS across the two sessions (true alias) vs IDENTICAL raw value (no-op unlock). Split by INERT vs
  POTENTIALLY-SEMANTIC classes (the semantic-class alias rate = the real cost side of the budget). Reported.
- **[FIX-4 PER-CLASS LORENZ]** Report per-class Lorenz/marginal SEPARATELY + full per-class marginal contribution to
  gap closure. Gini on k=3 near-degenerate -> give the marginals. If top-3 HHI driven by ONE class, flagged.

## OVERALL DISPOSITION RULE (honest, per corpus)
- RE-A0 KILL (realized_frac > 0.6) -> CLEAN NEGATIVE: no ceiling, volatile tokens not the bottleneck. STOP.
- RE-A0 PASS + RE-A1 FAIL (top3 < 50%) -> CLEAN NEGATIVE: gap is real but diffuse, no cheap normalization lever.
- RE-A0 PASS + RE-A1 PASS + RE-A2 positive recompute-saved -> POSITIVE normalization-budget characterization
  (reported as UPPER BOUND, with collision cost disclosed).
- CC vs Codex discordance reported explicitly, never averaged.

## RNG / REPRODUCIBILITY
Bootstrap RNG seeded 20260601. Bootstrap B=2000 (session+class clustered). Deterministic medoid (median head length).
Block 16. gpt2 tokenizer. No GPU. No network during the measurement run.

LOCKED-TS 2026-06-01T22:43:20Z
