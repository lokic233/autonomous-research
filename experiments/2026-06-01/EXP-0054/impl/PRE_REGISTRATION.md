# EXP-0054 PRE-REGISTRATION — Redundant Tool-Call Prefill Tax (PROJ-0008 / CLAIM-0018)

**LOCKED (UTC):** `2026-06-01T17:40:50Z`  (committed via `ros commit` BEFORE the main measurement run)
**Agent:** researcher-0018-L0-r6  | **Sub-monitor:** sub-monitor-0008-r6 | **prompt_version:** v001
**Satisfies:** VERDICT-0062 required_evidence (RE-A1 tool-identity joint; RE-A2 exact-prefix rescope + non-prefix tier-2;
RE-A3 result-equivalence co-primary; RE-A4 FLOPs/TTFT cost; RE-A6 structural retry; RE-A7 intervening-WRITE conditioning).

This document FREEZES every metric, threshold, and PASS/KILL decision rule. No threshold may change after this lock.
If a metric produces an artifact mid-run, it is re-operationalized to a length/intent-consistent form of the FROZEN
intent (thresholds unchanged) and the diagnosis is documented — a flawed metric will NOT be allowed to manufacture a PASS.

---

## 0. CORPORA & PARSING (frozen)
- **CC:** `~/.claude/projects/*/*.jsonl`. Reuse EXP-0041 `parse_cc` layer: pass-1 map `tool_use.id -> (name, input)`;
  pass-2 walk `tool_result` blocks in file order, join by `tool_use_id`, carry `is_error`, result text.
- **Codex:** `~/.codex/sessions/**/*.jsonl`. Reuse EXP-0041 `parse_codex` layer: map `function_call.call_id -> (name, arguments)`;
  walk `function_call_output` in order, **dedup by `call_id`** (EXP-0033/0037 double-log neutralizer), carry output text.
- A **session** = one jsonl file. Min length filter: a session must contain `>= 8` tool calls (MIN_TRIALS, matches prior EXP).
- BOTH corpora required (RE-A5). Mac CPU, pure stdlib (`json, glob, os, re, math, statistics, random, hashlib`). NO numpy/torch.

## 1. CORE DEFINITIONS (frozen)
- **Canonical call signature** `sig = tool_name + "\x00" + json.dumps(input, sort_keys=True, default=str)`.
  Key-order-insensitive; this is the unit of "byte-identical re-invocation" (the CALL, not the result).
- **Byte-identical repeat**: a tool call whose `sig` byte-equals an EARLIER call's `sig` in the SAME session.
  The first occurrence of a `sig` is the *original*; every later occurrence is a *repeat*. `prior` = the most-recent
  earlier occurrence of the same `sig`.
- **Token proxy (frozen, stdlib):** token length of any context segment = `chars / 4.0` (4 chars/token).
  ALL gate metrics that use tokens are RATIOS or thresholds far from the constant; ratios are invariant to the
  chars/token constant (it cancels). Gaps reported as `char_gap/4` token-estimates for comparability with the
  design-session median (12,512). A real tokenizer (EXP-0049 venv) is NOT required and will not be used; rationale:
  every gate decision is a ratio or a >>16-token threshold, robust to the proxy.
- **Call footprint (prefill tokens of one call)** = `len(canonical_args_str) + len(result_text)` in chars, /4 for tokens.
- **token_gap(repeat)** = chars between the END of `prior`'s footprint and the START of `repeat` in file/serialization
  order, /4. (Intervening divergent span.)

## 2. RE-A6 ANTI-TAUTOLOGY — STRUCTURAL RETRY EXCLUSION (frozen, applied FIRST, defines the surviving population)
A repeat is **excluded** from the tax population if EITHER:
  (a) **structural retry**: its `prior` same-`sig` occurrence had `is_error == True` (re-invoked because the earlier
      attempt FAILED — corrective, not redundant). This is the structural heuristic (same tool+args following an error
      on a prior call to the same tool); it has NO gap cutoff, so it correctly catches long-gap retry-after-investigation.
  (b) **adjacent/trivially-prefix-reusable**: `token_gap < K`, with **K = 200 tokens** (≈ one reasoning step / one
      tool turn; far below the 12.5k design median). Justification: at gap < 200 tok the intervening divergence is
      small enough that exact-prefix block reuse plausibly survives, so these are NOT a clean exact-prefix-unrecoverable
      tax and are conservatively removed.
- **SURVIVING TAX POPULATION** = byte-identical repeats whose `prior` SUCCEEDED (`is_error==False`) AND `token_gap >= K`.
  These are LONG-GAP interior repeats of a prior SUCCESS — the genuine redundant re-invocation tax.
- Report counts at each filter stage (all repeats -> minus retries -> minus adjacent -> surviving) for transparency.

## 3. DETERMINISM CLASS — STATE-AWARE (frozen; RE-A7 conditioning baked in)
For every call assign a base class by tool name:
  - **READ-like** (deterministic-candidate): `Read, Glob, Grep, LS, NotebookRead` (CC); `read*/list*/grep*` patterns (Codex).
  - **MUTATING**: `Write, Edit, MultiEdit, NotebookEdit` (CC); `apply_patch`/`write`/`edit` (Codex).
  - **VOLATILE**: `Bash, WebFetch, WebSearch, Task` (CC); `exec_command`/`shell`/`*` (Codex default).
**State conditioning (RE-A7):** a READ-like repeat is **DETERMINISTIC** iff NO intervening MUTATING or VOLATILE call to
the SAME target (same `file_path` for file tools; for Bash/exec, any intervening write to a path named in the read args)
occurs between `prior` and `repeat`. A READ-like repeat WITH an intervening same-target mutation -> class **INVALIDATED**.
Final determinism class ∈ {`DETERMINISTIC`, `INVALIDATED`, `VOLATILE`, `MUTATING`}. This is strictly MORE than tool
identity (it reads session state) — that surplus is exactly what must beat the tool-identity baseline in RE-A1.

## 4. RESULT-EQUIVALENCE LABEL (frozen; RE-A3 co-primary)
For each surviving repeat: `result_equiv = (result_text(repeat) == result_text(prior))` byte-equality.
This is the output-recoverability label (byte-identical ARGS != byte-identical RESULT for VOLATILE/MUTATING).

---

## GATES — exact metric, threshold, PASS/KILL rule (ALL FROZEN)

### RE-A1 — LOAD-BEARING / KILLER: determinism-class dAUC over JOINT {gap + tool-freq + TOOL-IDENTITY one-hot}
- **Task:** predict the binary `result_equiv` label over the surviving-tax population, per corpus.
- **Baseline model B0 features:** `token_gap` (continuous, log1p), `tool_frequency` (count of this tool's calls in the
  session, log1p), `tool_identity` (one-hot over tool names). Logistic regression, pure-stdlib batch gradient descent,
  L2 reg λ=1.0, standardized features.
- **Augmented model B1 = B0 + determinism_class one-hot.**
- **AUC:** out-of-sample via **session-clustered 5-fold CV** (folds split on session id, never leak a session across
  train/test) to prevent in-sample AUC inflation. AUC = rank statistic (Mann-Whitney) on pooled held-out scores.
- **dAUC = AUC(B1) − AUC(B0).** CI via **session-clustered bootstrap** (resample sessions with replacement, B=2000,
  refit CV each resample is too costly -> instead: fit once, bootstrap the held-out per-call scores BY SESSION to get
  the dAUC sampling distribution; 95% LB = 2.5th pct).
- **PASS:** dAUC 95% LB > 0 on **BOTH** corpora (determinism class adds discriminative power beyond gap+freq+tool-identity).
- **KILL/DEMOTE:** if dAUC 95% LB <= 0 on either corpus -> determinism class is collinear with / dominated by tool
  identity -> **DEMOTE** claim to "agents repeat popular tools" workload restatement (clean negative, first-class).
- *Degeneracy guard:* if `result_equiv` is near-constant (var < 0.01) in a corpus's surviving population, AUC is
  undefined; report as "label degenerate -> determinism prediction vacuous" = DEMOTE for that corpus (honest).

### RE-A2 — EXACT-PREFIX-SURVIVAL KILLER (rescoped to exact-prefix caches; block = 16)
- **Metric (exact-prefix non-recoverable):** for each surviving repeat, exact-prefix caching can serve the repeat's
  content only if the live token-prefix up to the repeat shares a common prefix (block-aligned, 16-tok blocks) with a
  cached sequence that EXTENDS past the original's position. The only candidate cache is the original's prefix; it
  diverges right after the original (intervening tokens differ). Non-recoverable iff intervening divergent span
  `>= 1 block (16 tokens)` between the longest-common-prefix end and the repeat. Operationally:
  `non_recoverable = (token_gap >= 16)`. (Since surviving pop already has token_gap >= K=200 >> 16, this is a check,
  not a tautology with the K filter — we still report the raw fraction.)
- **PASS:** `>= 95%` of surviving repeats exact-prefix-non-recoverable.
- **KILL:** `< 95%` exact-prefix-recoverable share too high -> tax illusory under exact-prefix caching -> KILL.
- **TIER-2 scope boundary (mandatory, RE-A2 fix #4):** report the fraction of byte-identical repeats whose CONTENT is
  addressable by NON-PREFIX KV reuse (CacheBlend 2405.16444 / PromptCache 2311.04934 / LMCache) = 100% of byte-identical
  repeats are content-addressable interior matches (the args are literally identical). STATE explicitly: "this study
  characterizes the tax under production-deployed EXACT-PREFIX caches; non-prefix interior KV fusion is a published
  mechanism we do NOT implement/evaluate — it is our named scope boundary, not claimed structurally impossible."

### RE-A3 — RESULT-EQUIVALENCE CO-PRIMARY with byte-identical f
- **Metric:** `result_equiv_rate` = fraction of surviving repeats with `result_text(repeat)==result_text(prior)`,
  reported per corpus AND per determinism class. Reported ALONGSIDE byte-identical f (no conflation).
- **No standalone threshold** (co-primary descriptor), BUT: if `result_equiv_rate ~ 0` (< 5%) for the whole surviving
  population, the repeats carry NO recoverable output -> the recoverable tax is illusory -> contributes to KILL (per
  project_overview honest-kill pathway "RE-A3 result-equivalence ~0 -> tax illusory").
- The **recoverable-tax** subset used for f (RE-A4) = surviving repeats that are BOTH exact-prefix-non-recoverable AND
  `result_equiv==True` (a content cache could legitimately have served the identical output).

### RE-A4 — EFFECT-SIZE FLOOR + COST TRANSLATION
- **f (token fraction):** `f = sum(footprint_tokens of recoverable-tax repeats) / sum(footprint_tokens of ALL tool calls)`
  per corpus. Footprint = (canonical_args + result_text) chars /4. Session-clustered bootstrap 95% CI (B=2000).
- **PASS condition (a):** f point estimate `>= 2%` AND its 95% CI excludes 0, on at least the primary corpus (CC) with
  same-sign replication on Codex (RE-A5).
- **KILL:** f < 2% (or CI includes 0) -> agents rarely self-repeat recoverably -> KILL.
- **Cost translation (mandatory fix #3):** translate f into FLOPs and TTFT under realistic chunked-prefill batching:
  - Prefill FLOPs/token ≈ `2 * N_params` (dense fwd). Report for N_params ∈ {8e9, 70e9}.
  - Wasted prefill FLOPs/session = f * (total tool-call prefill tokens) * 2 * N_params.
  - TTFT impact: at a representative prefill throughput (A100 ~ chunked-prefill, assume ~2e3 tok/s effective for 70B,
    ~1e4 tok/s for 8B per published vLLM chunked-prefill numbers), wasted tokens -> added prefill latency per session.
  - $ grounding: at ~$2/GPU-hr, convert wasted GPU-seconds -> $/1k-sessions. Report as a grounded estimate, not a bare %.

### RE-A5 — CROSS-CORPUS SIGN REPLICATION
- **PASS:** sign agreement CC vs Codex on (i) f > 0, and (ii) the determinism-class effect direction (DETERMINISTIC
  class has HIGHER result_equiv_rate than VOLATILE/MUTATING). Both directions must agree.
- **KILL/weaken:** opposite signs -> not a cross-corpus regularity.

### RE-A6 — ANTI-TAUTOLOGY (operationalized in §2 above; structural retry + K=200). 
- **PASS:** a non-empty surviving population remains AFTER structural-retry + adjacent exclusion (the tax is not an
  artifact of retries/adjacency). Report the surviving fraction.
- **KILL:** if surviving population is empty / negligible (< 30 repeats pooled per corpus) -> underpowered / tautological
  -> cannot sustain the claim -> KILL/inconclusive.

### RE-A7 — DETERMINISM CLASS CONDITIONED ON INTERVENING-WRITE STATE (operationalized in §3).
- **PASS (acknowledgement/test):** report `result_equiv_rate` for READ-like repeats split by DETERMINISTIC vs
  INVALIDATED (intervening same-target write). Expectation: DETERMINISTIC >> INVALIDATED. If the predictor cannot
  condition on state (e.g., target extraction fails), explicitly acknowledge the ceiling. The state-conditioning is the
  surplus that powers RE-A1; if INVALIDATED is empty, note that intervening-write invalidation is rare in this corpus
  (ceiling acknowledged) — not a failure, a documented boundary.

---

## OVERALL CLAIM DISPOSITION (frozen decision tree)
- **PROMOTE-ready (committee submit)** iff: RE-A1 PASS both corpora AND RE-A2 PASS (>=95%) AND RE-A4 f>=2% CI>0 (CC)
  AND RE-A5 sign-agree AND RE-A6 non-empty surviving pop. (RE-A3/A7 are descriptors/conditioners feeding A1.)
- **DEMOTE** (clean negative): RE-A1 fails -> "agents repeat popular tools."
- **KILL** (clean negative): RE-A2 < 95% (exact-prefix recovers) OR f < 2% OR result_equiv_rate ~ 0 OR surviving pop empty.
- An honest negative is a FIRST-CLASS publishable outcome. NO gate threshold will be moved to manufacture a PASS.

## OUTPUTS
- `experiments/2026-06-01/EXP-0054/impl/redundant_prefill_census.py` (this run)
- `experiments/2026-06-01/EXP-0054/results/*.csv` + `*.json` (per-gate raw)
- `experiments/2026-06-01/EXP-0054/results/analysis.md` (per-gate PASS/KILL verdicts + committee required_evidence)
