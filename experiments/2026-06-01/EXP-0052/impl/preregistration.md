# PRE-REGISTRATION — EXP-0052 (CLAIM-0016, PROJ-0006)
# Agent-Event-Phase Desynchronization Tax in BATCH Speculative Decoding
# L0 GATING lane — researcher-0016-L0-r6 — prompt_version v001
# Sub-monitor: sub-monitor-0006-r6. Design gate: VERDICT-0059 (6/6 yellow reseed-with-fixes).

**Timestamp (LOCKED, written BEFORE running the main analysis):** 2026-06-01T16:07:18Z
**Engine experiment:** EXP-0052 (registered, status=pending). NO post-hoc edits after this lock.
**Hardware:** Mac CPU, /usr/bin/python3 stdlib ONLY (no torch/numpy/scipy — none installed).
**Reconciliation:** VERDICT-0059.required_evidence == RE-A1..A7 below (UNION baked in; identical set).

------------------------------------------------------------------------
## 0. WHAT IS NEW vs WHAT IS DEAD (scope guard — non-negotiable)
The contribution is CROSS-SEQUENCE BATCH-COMPOSITION (leg a: ragged min-bound tax exists; leg c:
phase-aligned composition recovers it). The phase predictor is ONLY the batch-GROUPING MECHANISM.
It is NOT a standalone dAUC acceptance-discriminator. The single-sequence
agent-phase-over-{running-mean-acceptance + entropy + position} dAUC discriminator was FALSIFIED TWICE
on this SAME EXP-0046 top-1-agreement proxy:
  - DEAD-0011 (CLAIM-0013, VERDICT-0053, EXP-0046): K=8 tool-boundary acceptance cliff is content-confounded;
    real signal is a 1-token (d=1) collapse, 1/8 positions Holm-sig (<4 required), Codex net penalty NEGATIVE.
  - DEAD-0012 (CLAIM-0015, EXP-0050): format-class dAUC over length+entropy JOINT = -0.090 CC
    (CI[-0.400,+0.155]) / -0.322 Codex (CI[-0.450,-0.164]), 95% LB<=0 both (sig-neg Codex). Discriminator dead.
This experiment MUST NOT resurrect that discriminator. Phase here forms BATCH GROUPS only; success is
measured purely as CROSS-SEQUENCE min-bound GOODPUT recovery, never as single-sequence AUC/dAUC.

## 1. THESIS (fixed, not editable post-hoc)
In BATCH speculative decoding, co-batched sequences accept different numbers of draft tokens per round
(ragged tensor); the batch round's goodput is bottlenecked to the MIN accepted-length across the batch.
On real agentic trajectories this ragged variance tracks AGENT-EVENT PHASE (mid-tool-result-injection
TRANSITION = low-accept; formulaic RESUMPTION = high-accept; FREE-FORM reasoning = mid). A phase-aligned
BATCH-COMPOSITION policy (co-batch rounds of the same predicted phase) raises mean accepted-length-per-round
(recovers the ragged min-bound tax) at ZERO accuracy change (SD exact) — AND it must do so OVER a static
per-task difficulty grouping baseline and over a sham running-mean cluster, else phase adds nothing.

## 2. PROXY DEFINITION (reused VERBATIM from EXP-0046; same limits)
No HF cache / no torch on node -> we CANNOT run a real draft/target pair. We reuse the EXP-0046
**corpus-derived top-1-agreement proxy**, identical estimator:
  - Per-session token stream in file order (reuse EXP-0046 cc_streams() / codex_streams()): assistant
    text/thinking = decoded tokens we score; tool_result (CC) / function_call_output (Codex, call_id-dedup)
    = INJECTION; user turns = generic context-shift source.
  - "draft" = trigram-backoff predictor (prev up-to-2 tokens -> bigram -> unigram), trained ONLY on a
    held-out 50/50 session split (deterministic hash of session path). Acceptance measured ONLY on TEST split.
  - acceptance bit a_i := (predictor top-1 == realized assistant token).
  - **PROXY LIMITS (honest, identical to EXP-0046):** a trigram has only 2 tokens of context; its boundary
    sensitivity is CONSERVATIVE. A real neural draft attends the full injected result and could show
    larger/longer phase-conditioned acceptance structure this proxy cannot resolve. A FLAT / NULL result
    (phase composition does not beat the baselines, or tax floor not met) is a VALID, PUBLISHABLE CHEAP KILL.
    We DO NOT force a positive.

## 3. CORPORA (>=2 required; reuse existing parsers)
  - Claude Code: ~/.claude/projects/**/*.jsonl (EXP-0007 tool_result join logic; assistant=text/thinking).
  - Codex: ~/.codex/sessions/**/*.jsonl (EXP-0037 function_call_output call_id dedup).
  - Gemini: ~/.gemini/tmp/**/chats/*.json — PROBED 2026-06-01: messages are only type {user, gemini} with
    content blocks {text} ONLY; NO tool_result injections present -> the tool-TRANSITION phase cannot be
    derived. EXCLUDED (same structural reason EXP-0046 excluded Gemini). CC + Codex satisfy >=2 corpora.
  Each corpus analyzed SEPARATELY (no cross-corpus pooling for the headline); a real effect replicates in BOTH.

## 4. PHASE LABELS (derived from trajectory STRUCTURE; LOCKED, no post-hoc window search)
For each assistant token track (last_boundary_type in {tool,user,none}, dist d = #assistant tokens since
that boundary). Three agent-event phases (reusing EXP-0046 K=8 boundary window; transition sub-window = the
documented d=1..2 collapse zone):
  - **TRANSITION** (mid-injection, expected low-accept): last boundary = tool-result AND 1 <= d <= 2.
  - **RESUMPTION** (formulaic, expected high-accept): (last boundary = tool-result AND 3 <= d <= 8)
       OR (last boundary = user AND 1 <= d <= 8).
  - **FREE_FORM** (free-form reasoning, baseline): d > 8 from any boundary (interior).
  LOCKED constants: K_transition = 2, K_resumption = 8. Phase is a function of (boundary_type, d) ONLY
  (NO running-mean, NO entropy -> deliberately NOT the dead discriminator; it is a coarse structural grouping key).

## 5. SD BATCH-ROUND MODEL (CPU Monte-Carlo; the instrument)
Per session, from its ordered assistant-acceptance bit sequence a_1..a_M build ROUNDS at draft length gamma:
  starting at position p, accepted_len = # leading consecutive accepts in a_p..a_{p+gamma-1} (cap gamma);
  advance p -> p + accepted_len + 1 (target emits the corrected/bonus token). Each round R records:
    accepted_len in {0..gamma};  phase = phase(token at p) [round-start phase];
    running_mean = mean acceptance over the trailing W=32 assistant tokens ending at p-1 (dynamic difficulty,
      available at schedule time, NO phase label);  task_difficulty = the session's OVERALL mean acceptance
      (HISTORICAL per-task static difficulty model, NO dynamic signal);  session_id.
GOODPUT model (mission-specified ragged min-bound): a batch of B rounds advances by
  round_goodput = MIN over the B co-batched rounds of accepted_len. Policy goodput = mean over batches.
SCHEDULER = oracle-pool sort/group then chunk into consecutive batches of B (best achievable grouping for
each key; leftover < B dropped, count logged). This is an UPPER BOUND on each policy's composition benefit;
it is applied IDENTICALLY to every policy so the policy DELTA is fair (caveat documented in analysis).

POLICIES (same pool, same B, same gamma):
  P_random : seeded shuffle then chunk (reference for raw ragged tax).
  P_static : sort by task_difficulty (session mean acceptance) then chunk.  [RE-A1 KILLER BASELINE]
  P_sham   : sort by running_mean (trailing-window acceptance) then chunk.  [RE-A2 SHAM CLUSTER]
  P_phase  : group by phase (3 levels), within phase chunk into B.          [PROPOSED]

## 6. THE 7 PRE-REGISTERED GATES (EXACT DECISION RULES) — RE-A1..A7
PRIMARY CELL (decision cell): corpus in {CC, Codex}, B = 8, gamma = 8. Grid (RE-A5) reported for robustness.
CIs: cluster bootstrap by SESSION, B_boot = 2000, seed 20260601, percentile 95% (2.5/97.5). Each bootstrap
resamples sessions w/ replacement, rebuilds the round pool, re-runs ALL policies, recomputes deltas.

  **RE-A1 [LOAD-BEARING KILLER]:** Delta1 = Goodput(P_phase) - Goodput(P_static).
     PASS iff 95% LOWER bound of Delta1 > 0 (one-sided), in BOTH corpora at the primary cell.
     FAIL => CLAIM KILLED. Honest negative: "agent-event phase adds nothing over per-task difficulty
     clustering for batch-SD composition; use difficulty models, not phase."

  **RE-A2 [SHAM-CLUSTER CONTROL]:** Delta2 = Goodput(P_phase) - Goodput(P_sham).
     PASS iff 95% LB(Delta2) > 0 in BOTH corpora at primary cell. FAIL => phase is indistinct from generic
     dynamic difficulty clustering (Jensen gain), not phase-attributable => downgrade/kill. Report Delta2 + CI.

  **RE-A3 [TAX FLOOR >= 5%]:** raw ragged tax at the tested B:
     tax = (mean_accepted_len - Goodput(P_random)) / mean_accepted_len, where mean_accepted_len = mean
     accepted_len over ALL rounds (= B=1 goodput, the no-min-coupling per-sequence goodput).
     PASS iff tax >= 0.05 (5%) at the primary B in BOTH corpora. Report tax + bootstrap CI per B.
     Also report the parenthetical variant (min-bound vs mean-of-per-batch-maxes). FAIL => leg(a) is a
     foregone min<max triviality => KILL.

  **RE-A4 [WITHIN-SESSION WITHIN-POSITION-BUCKET PERMUTATION NULL]:** position-bucket = raw d
     (d=1,2,...,8, and interior=">8"). Permute phase labels among rounds sharing (session, d-bucket)
     -> this holds position fixed (absorbs position x phase autocorrelation) and shuffles only the
     boundary-type-driven phase distinction. Re-run P_phase under permuted labels, recompute
     Delta1_perm. n_perm = 1000, seed 20260601. p = (#{Delta1_perm >= Delta1_obs} + 1)/(n_perm + 1).
     PASS iff p < 0.05 (observed gain sits above the permuted null) in BOTH corpora at primary cell.

  **RE-A5 [MULTIPLICITY CORRECTION]:** grid = B in {4,8,16,32} x gamma in {4,8} x corpora {CC,Codex}
     x tokenizers {1: stdlib-regex} = family size 16. One-sided bootstrap p for RE-A1 (Delta1):
     p_cell = (#{Delta1_boot <= 0} + 1)/(B_boot + 1). Holm correction across the 16 p_cells.
     Report corrected significance for EVERY cell. (Only 1 tokenizer available -> stated honestly, not 0.)

  **RE-A6 [SCHEDULER OVERHEAD net>0]:** measure with time.perf_counter (>=5 reps, median) the per-round
     cost of (a) phase classification (boundary_type + d comparison) and (b) the grouping/sort batch-formation
     pass; report overhead_seconds_per_round. Convert to token-equivalents via assumed per-token decode time
     T_tok in {1ms, 5ms, 10ms}. net = Delta1 (extra accepted tokens/round) - overhead_seconds_per_round/T_tok.
     PASS iff net > 0 (for T_tok >= 1ms) at primary cell. (Moot/auto-fail-context if RE-A1 already fails.)

  **RE-A7 [CITE DEAD-0011 + DEAD-0012]:** prior_art/PROJ-0006/ records CONFIRMED both prior kills with exact
     numbers (above) and states explicitly: PROJ-0006 novelty = cross-sequence batch-COMPOSITION (legs a+c);
     the phase predictor is the grouping mechanism, NOT the dead standalone single-sequence dAUC discriminator.

## 7. DECISION RULE (terminal, committee-ready either way)
  **CANDIDATE-GRADE POSITIVE** (=> recommend L1 real vLLM/TGI/SGLang batch-SD accepted-length telemetry):
     RE-A1 95% LB(Delta1) > 0 (Holm-corrected) in BOTH corpora primary cell AND RE-A3 tax >= 5% (both corpora)
     AND RE-A2 95% LB(Delta2) > 0 (both corpora) AND RE-A4 perm p < 0.05 (both corpora) AND RE-A6 net > 0,
     with DEAD-0011/0012 cited (RE-A7).
  **CLEAN KILL** (=> first-class publishable negative): RE-A1 LB <= 0 in either corpus primary cell, OR RE-A3
     tax < 5%, OR RE-A2 LB <= 0 (phase == generic difficulty clustering), OR RE-A4 p >= 0.05, OR RE-A6 net <= 0.
  **AMBIGUOUS** (NOT committee-ready): replicates in one corpus not the other / borderline CIs -> report
     honestly, do NOT force; --next states what is needed.
  HARD KILL RULE (mission): KILL if RE-A1 fails CI>0 OR RE-A3 tax floor >=5% not met.

## 8. PROVENANCE
  Every number written to results/*.json with generating script impl/batch_round_model.py + this locked
  pre-registration committed alongside. No session note is source of truth. Negative results preserved verbatim.
  random seed = 20260601 everywhere. prompt_version v001.
