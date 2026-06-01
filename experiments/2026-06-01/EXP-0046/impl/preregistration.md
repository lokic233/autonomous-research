# PRE-REGISTRATION — EXP-0046 (CLAIM-0013, PROJ-0004)
# Tool-Boundary Acceptance Cliff in Speculative Decoding for Agent Trajectories
# L0 GATING lane — researcher-0013-L0-r4 — prompt_version v001

**Timestamp (written BEFORE running the main analysis):** 2026-06-01T11:33:15Z
**Engine experiment:** EXP-0046 (registered, status=pending); committee gate VERDICT-0050.
**Hardware:** Mac CPU, /usr/bin/python3 stdlib ONLY (no torch/numpy/scipy — none installed).

------------------------------------------------------------------------
## 1. THESIS (fixed, not editable post-hoc)
On real agentic tool-calling trajectories, a speculative-decoding draft model's token-acceptance
rate drops a measurable, position-localized amount in the K=8 decode steps immediately AFTER each
tool-result injection (the resumption boundary). This boundary penalty — NOT task domain, NOT
generic content-type, NOT local target-entropy — is a distinct within-trajectory driver of
accepted-length variance.

## 2. PROXY DEFINITION (stated plainly, with limits — this is NOT a real SD draft/target pair)
There is NO HF cache and NO torch on this node, so we CANNOT run a real draft+target model pair.
We use a **corpus-derived top-1-agreement proxy**:
  - Token stream per session is built in file order: assistant-generated text (CC `text`/`thinking`
    blocks; Codex `agent_message` + `message:assistant` `output_text`) = the DECODED tokens we score;
    tool-result text (CC `tool_result` blocks; Codex `function_call_output`) = the INJECTION;
    real user turns (CC `user` text; Codex `user_message`) = the generic-context-shift source.
  - "draft" = a trigram backoff next-token predictor (context = previous up-to-2 tokens ->
    bigram -> unigram), trained ONLY on a held-out TRAIN split of sessions (50/50 split by a
    deterministic hash of the session path; acceptance is measured ONLY on TEST-split sessions).
    This is leakage-free at the session level.
  - "accepted" for a decoded token := (predictor top-1 == realized token).  Acceptance signal =
    P(top-1 agreement) as a function of distance-from-tool-boundary.
  - **PROXY LIMITS (honest):** a trigram has only 2 tokens of context memory, so its sensitivity
    to the injected result is conservative — it feels the boundary via (a) tool-result tokens
    sitting in the immediate n-gram context for the first ~2 positions, and (b) result-derived
    low-frequency assistant content (echoed paths/numbers/keys) persisting several tokens. A real
    neural draft model attends over the full injected result; its cliff could be larger/longer than
    this proxy resolves. This proxy MOTIVATES OR KILLS the L1 vLLM real-SD telemetry lane; it does
    not by itself confirm a real accepted-length cliff. A flat/null proxy result is a VALID,
    PUBLISHABLE cheap kill.

## 3. CORPORA (>=2 required; reuse existing parsing logic)
  - Claude Code: ~/.claude/projects/**/*.jsonl  (214 sessions) — join tool_result->tool_use by id
    (EXP-0007 logic); assistant text = `text`/`thinking` blocks.
  - Codex: ~/.codex/sessions/**/*.jsonl  (99 sessions) — dedup function_call_output by call_id
    (EXP-0037 logic); assistant text = agent_message + assistant output_text.
  - Gemini available (~/.gemini, 72 files) but stores tool calls without a clean interleaved
    assistant-text stream -> EXCLUDED as messy per charter allowance; CC+Codex are the >=2 corpora.
  Each corpus analyzed SEPARATELY (no pooling across corpora for the headline); a real effect
  should replicate in BOTH.

## 4. FIXED PARAMETERS (no post-hoc selection)
  - **K = 8** decode positions after each boundary (positions d = 1..8). NO post-hoc window search.
  - Interior/baseline = decoded tokens at distance > K (=> >8) from the most recent boundary of ANY
    kind (tool OR user) — the within-trajectory baseline acceptance.
  - n-gram order = 3 (trigram backoff). random seed = 20260601 (bootstrap + any resampling).
  - Bootstrap = cluster bootstrap by SESSION, B = 2000 reps, percentile 95% CI (2.5/97.5).

## 5. PRIMARY ENDPOINT + PRE-REGISTERED MARGINS (decided NOW, before seeing results)
  Per-position boundary penalty:  penalty_tool(d) = acc_interior - acc_tool(d),  d=1..8.
  - **PASS-A (effect exists):** mean over d=1..8 of penalty_tool(d) >= **0.02** (2 percentage
    points absolute) AND its bootstrap 95% CI excludes 0.
  - Multiple-comparison: **Holm correction** over the 8 per-position one-sided tests
    H0: penalty_tool(d) <= 0. Require Holm-significant penalty_tool(d) > 0 at **>= 4 of 8** positions.

## 6. THE 4 CONTROLS = THE PASS GATE (all must hold for a candidate-grade POSITIVE)
  (1) **CONTENT-TYPE-MATCHED NULL (highest-priority cheap killer):** splice the IDENTICAL
      tool-result text at a matched NON-boundary interior location in the SAME session, recompute
      acceptance of the following decoded tokens (spliced positions 1..K). Define
      penalty_splice(d) = acc_interior - acc_spliced(d).  REQUIRE
      diff_content(d) = penalty_tool(d) - penalty_splice(d) with mean over d=1..K having 95% CI > 0
      (pre-registered min superiority = **0.01**). If penalty_tool ~= penalty_splice -> the drop is
      tool-result-text-as-context (content-type), NOT position -> **FALSIFIED (clean publishable kill)**.
  (2) **NON-TOOL CONTEXT-SHIFT BASELINE:** penalty_user(d) at generic user-turn boundaries.
      REQUIRE diff_shift(d) = penalty_tool(d) - penalty_user(d), mean over d=1..K, 95% CI > 0
      (pre-registered min superiority = **0.01**). Else effect is generic context-shift, not tool-specific.
  (3) **TARGET-ENTROPY CONDITIONING:** at each decoded token compute predictor Shannon entropy H of
      the backed-off next-token distribution. Stratify into H quartiles; recompute boundary penalty
      WITHIN each stratum; pooled within-stratum penalty = stratum-size-weighted mean. REQUIRE the
      within-stratum mean boundary penalty (d=1..K) bootstrap 95% CI > 0. Else it's just
      "higher-entropy text is harder to speculate," not a distinct position effect.
  (4) **PRE-REGISTRATION (this file):** K, margins, Holm, proxy — all fixed above before running.

## 7. DECISION RULE (terminal, committee-ready either way)
  - **CANDIDATE-GRADE POSITIVE** (=> recommend L1 vLLM real-SD telemetry): PASS-A holds AND ALL of
    controls (1),(2),(3) hold with their pre-registered CI>0 superiority, in BOTH corpora.
  - **CLEAN KILL** (=> negative-result note; tells serving teams boundary-aware SD scheduling is not
    worth building; corroborates 2510.02128): PASS-A fails (CI includes 0 / mean < 0.02), OR ANY of
    controls (1),(2),(3) nulls it (superiority CI includes 0 / boundary <= the null), in either the
    pooled or per-corpus view -> thesis killed at L0. A null is a SUCCESS.
  - **AMBIGUOUS** (NOT committee-ready): replicates in one corpus but not the other, or borderline
    CIs -> report honestly, do NOT force; --next states what is needed.

## 8. PROVENANCE
  Every reported number is written to results/*.json + *.csv with the generating script
  (impl/acceptance_proxy.py) and this pre-registration committed alongside. No session note is
  source of truth. Negative results preserved verbatim.
