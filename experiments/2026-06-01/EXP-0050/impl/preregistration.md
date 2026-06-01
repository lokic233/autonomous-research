# EXP-0050 — PRE-REGISTRATION (LOCKED)  CLAIM-0015 / PROJ-0004 / L0 gating lane
# researcher-0015-L0-r5 | prompt v001 | Mac CPU stdlib-only | LOCKED 2026-06-01T12:57:14Z
# THIS FILE IS LOCKED BEFORE THE MAIN ANALYSIS RUNS. No post-hoc edits to metrics/gates.
# Pass gate = VERDICT-0054 required_evidence RE-1..RE-8 (design verdict for CLAIM-0015).

## 0. CLAIM UNDER TEST (CLAIM-0015)
The single-token (d=1) acceptance collapse at the first assistant token after a tool-result
injection is a CONTENT-FORMAT-TRANSITION cost (prose-after-non-prose), whose size is PREDICTABLE
MODEL-FREE from the injected payload's FORMAT CLASS (JSON / code / stdout / table / scalar / prose),
and which ADDS predictive value OVER a length+entropy JOINT baseline. The cost is >=80% concentrated
at d=1; a 1-token speculation-suppression recovers a measured fraction of per-turn wasted draft-verify
FLOPs at zero accuracy cost (SD remains exact). This is NOT a position-from-boundary claim (DEAD-0011);
it is built ON the EXP-0046 content-spliced null (the d=1 collapse is the surviving finding).

## 1. PROXY & ITS LIMITS (honest, carried from EXP-0046)
- "draft" = trigram-backoff top-1 next-token predictor trained on a HELD-OUT 50/50 session split.
- "target" = realized assistant token. accept := (draft top-1 == realized token).
- A trigram has only 2 tokens of context, so its boundary/format sensitivity is CONSERVATIVE. This L0
  proxy MOTIVATES OR KILLS the L1 vLLM real-SD telemetry lane; it does NOT confirm a real accepted-length
  cliff. A flat / null / dAUC<=0 proxy result is a VALID, PUBLISHABLE cheap kill. WE DO NOT FORCE A POSITIVE.
- No torch / no HF cache / no numpy / no scipy on this node. /usr/bin/python3 stdlib ONLY.

## 2. UNIT OF ANALYSIS (RE-2)
- One unit = one TOOL->ASSISTANT TRANSITION (= one d=1 token: the first assistant token after a tool result).
- Features per unit (ALL model-free except draft_entropy_d1):
  (a) format_class in {json, code, stdout, table, scalar, prose} of the injected tool-result payload (regex).
  (b) payload_len = #tokens in the tool-result payload (continuous; log1p used in models).
  (c) payload_entropy = Shannon entropy (bits) of the payload's own token-frequency distribution.
  (d) draft_entropy_d1 = trigram predictor next-token conditional entropy at the d=1 position (= "draft
      confidence"; used ONLY for the RE-7 head-to-head, NOT in the RE-1 joint baseline).
- Label per unit: accept_d1 in {0,1}.
- BOOTSTRAP UNIT = per-conversation (session) cluster resample (NOT per-token). B=2000, seed=20260601.
  We ALSO report the actual n units and n positives (accepts) per format-class per corpus (RE-2).
- A secondary per-tool-call-cluster bootstrap (resample transitions) is reported as a sensitivity check.

## 3. MODELS / SCORES (fit on TRAIN split, scored on TEST split; AUC = rank-based Mann-Whitney on TEST)
- M_format   : score(unit) = TRAIN Laplace-smoothed accept-rate for that unit's format_class.
- M_lenent   : logistic regression on standardized [log1p(payload_len), payload_entropy] (the JOINT baseline).
- M_draftent : logistic regression on standardized [draft_entropy_d1] (the adaptive-SD / draft-confidence baseline, RE-7).
- M_blind    : "always suppress d=1" (format-BLIND). AUC := 0.5 by construction (no discrimination); used for
               the throughput/FLOPs comparison, not an AUC contender.
- Logistic regression = plain-Python batch gradient descent (standardized features, L2=1e-3, 2000 iters, lr=0.5).
- AUC computed on TEST units. Positive class for AUC = accept_d1==1.

## 4. THE 8 PRE-REGISTERED GATES (RE-1..RE-8) — EXACT DECISION RULES

### RE-1 [LOAD-BEARING]  dAUC(format | length+entropy JOINT)
- Metric: dAUC_RE1 = AUC(M_format) - AUC(M_lenent), on TEST.
- Paired cluster-bootstrap (resample TEST sessions; recompute BOTH AUCs on the SAME resample; take diff).
- PASS GATE: 95% LOWER bound of dAUC_RE1 > 0  (point estimate alone is NOT sufficient).
- KILL: if lower bound <= 0, format-class adds nothing over length+entropy joint -> novelty dies into the
  confidence-gated SD family -> CLEAN HONEST KILL. Reported per corpus AND pooled.

### RE-2  bootstrap unit + n reporting
- Bootstrap = per-conversation (sec 2). Report table: per corpus x format_class -> {n_units, n_accept, accept_rate}.

### RE-3  matched-format prose->prose splice control
- "format-transition cost" must EXCEED a same-format (prose->prose) discontinuity.
- prose->prose control units = (a) tool results classified format_class==prose, AND (b) USER-turn->assistant
  d=1 transitions (user text = prose). Define:
    dip(X) = interior_acc - mean accept_d1 over unit-set X.
    nonprose set = format_class in {json,code,stdout,table,scalar}.
- Metric: gap_RE3 = dip(nonprose) - dip(prose-control). Cluster-bootstrap CI.
- PASS: 95% lower bound of gap_RE3 > 0 (non-prose dips MORE than prose->prose).
- KILL: lower bound <= 0 -> the d=1 dip is GENERIC discontinuity, not a format transition.

### RE-4  cross-corpus train/test split (corpus-confound guard)
- Direction 1: train models on CC, evaluate AUC/dAUC on Codex. Direction 2: train Codex, eval CC.
- Report dAUC_RE1 (format vs len+ent joint) for BOTH directions with cluster-bootstrap CI.
- Interpreted alongside within-corpus; a positive that does NOT transfer cross-corpus is flagged as
  corpus-artifact-suspect (consistent with VERDICT-0054 Candidate-B note).

### RE-5  "X% FLOPs recovered" + exactness
- Denominator = per-turn total draft-verify FLOPs = sum over drafted positions of (draft_fwd + verify_fwd).
  Model the standard 1-token-lookahead SD step: each speculated position costs 1 draft forward + its share of
  the batched verify forward. Define recovered_frac = (FLOPs saved by suppressing the d=1 draft when it would
  be rejected) / (per-turn total). We REPORT recovered_frac as: f = P(reject@d1) * (cost_draft_d1 / per_turn_total),
  using the EMPIRICAL P(reject@d1) and a transparent FLOP cost model (draft:verify param-ratio rho as a swept
  parameter rho in {1/8, 1/4} typical EAGLE/ngram drafts). Report point + variance (cluster-bootstrap over P(reject@d1)).
- EXACTNESS ARGUMENT (formal, written): SD is exact iff suppression changes ONLY the DRAFT LENGTH, not the
  verifier input distribution. At d=1 suppression = draft_length 0 for that step; the verifier then decodes that
  one token itself from the SAME context, so the output distribution is UNCHANGED (identical to vanilla decoding
  of that token). Therefore suppression is provably accuracy-neutral. We CONFIRM numerically: draft_length=0 for
  1 step reproduces the verifier's own next-token (trivially exact). This is a correctness ARGUMENT, not a tunable.

### RE-6  >=80% d=1 concentration (quantitative)
- cost_d = interior_acc - accept(d) for d=1..K, K=8 (matches EXP-0046).
- share = |cost_1| / sum_{d=1..K} |cost_d|.
- PASS: 95% LOWER bootstrap bound of share > 0.80 (NOT a point estimate).
- NOTE (locked, honest): using |.| in the denominator makes accumulated proxy NOISE at d=2..8 INFLATE the
  denominator, biasing share DOWNWARD -> this is a CONSERVATIVE (hard-to-pass) concentration test. EXP-0046
  point share ~ 0.57 (CC) suggests this gate may FAIL; if so that is a clean honest kill of the ">=80% at d=1"
  sub-claim, reported as such.

### RE-7  entropy head-to-head full ROC/AUC at d=1
- dAUC_RE7 = AUC(M_format) - AUC(M_draftent), paired cluster-bootstrap CI (full ROC, not partial-dependence).
- Also report, at the train-chosen Youden-J threshold of M_format applied to TEST: FDR (=1-precision) and
  FNR (=1-recall) for the "suppress d=1" decision (positive=token will be REJECTED, i.e. suppression is correct).
- PASS (for the model-free-beats-draft-confidence sub-claim): 95% lower bound dAUC_RE7 > 0.
- KILL: lower bound <= 0 -> draft-entropy thresholding already captures it; no pre-draft model-free advantage.

### RE-8  classification overhead vs single-token draft forward
- Measure regex format-classifier wall-clock per payload (median over all payloads, >=3 timed reps).
- Compare to a single-token draft forward pass cost. On THIS node we cannot run a real draft forward; we
  therefore report (a) absolute classifier latency per payload (us), and (b) the threshold argument: a real
  ngram/EAGLE draft forward at H100 scale is ~O(50us-1ms) for a small draft; if classifier latency >> that, the
  model-free advantage is ILLUSORY. We report the measured number and the explicit comparison band; the L1 lane
  must confirm against a real draft-forward microbench. If classifier latency exceeds a 1ms upper-band draft
  forward, we FLAG the model-free advantage as overhead-negated.

## 5. CORPORA (reuse EXP-0046 parsers; >=2 corpora required)
- Claude Code: ~/.claude/projects/**/*.jsonl (tool_result joined; payload = tool-result content).
- Codex: ~/.codex/sessions/**/*.jsonl (function_call_output, dedup by call_id; payload = output).
- Usable session filter (carried from EXP-0046): >=50 assistant tokens AND >=1 tool result.
- 50/50 deterministic session split (basename-hash parity), reused for within-corpus RE-1/RE-3/RE-6/RE-7.

## 6. FORMAT CLASSIFIER (regex, locked rules; applied to RAW payload text BEFORE tokenization)
Priority order (first match wins):
  1. scalar : stripped payload is a single short line (<=24 chars) matching a number / bool / null / single short token.
  2. json   : stripped starts with '{' or '[' AND contains '":' or matches /"[^"]+"\s*:/ ; or python-dict-ish /'[^']+':/.
  3. table  : >=2 lines AND (markdown pipe rows /^\s*\|.*\|/ on >=2 lines) OR (>=2 lines with >=2 runs of 2+ spaces aligning columns).
  4. code   : contains a fenced block ``` OR high bracket/operator density (>=0.06 of chars in {};()=<>] per char)
              OR >=2 code keywords (def|function|class|import|return|const|let|var|public|void|#include).
  5. stdout : >=2 lines (multiline) not matching above (logs / tracebacks / terminal output / file listings).
  6. prose  : default (single-or-multi line natural-language text; the matched-format control class for RE-3).
- Classifier is pure-regex/stdlib; its per-payload latency is the RE-8 measurement target.

## 7. DECISION SUMMARY (committee-ready terminal states)
- CANDIDATE-POSITIVE iff ALL of: RE-1 dAUC lower bound > 0 (within-corpus, pooled) AND RE-3 gap lower bound > 0
  AND RE-6 share lower bound > 0.80 AND RE-7 dAUC lower bound > 0 AND format-class beats blind-suppression on the
  reported operating metric AND RE-4 transfers (both directions positive or at least not sign-flipped) AND RE-8
  classifier latency within the draft-forward band.
- CLEAN KILL iff any LOAD-BEARING gate fails: RE-1 lower bound <= 0 (primary kill), OR RE-3 generic-discontinuity,
  OR RE-6 not d=1-concentrated, OR RE-8 overhead-negated. Each is independently publishable.
- A messy/ambiguous result (e.g. RE-1 positive within-corpus but sign-flips cross-corpus, or wide CIs from
  underpower) is NOT committee-ready -> report ambiguity honestly via --next; do NOT overclaim.

## 8. WHAT WOULD FALSIFY EACH SUB-CLAIM (anti-coping)
- "format-class predictive beyond length+entropy"  -> falsified by RE-1 lower bound <= 0.
- "it's a format TRANSITION not generic discontinuity" -> falsified by RE-3 lower bound <= 0.
- ">=80% concentrated at d=1" -> falsified by RE-6 lower bound <= 0.80.
- "model-free beats draft-confidence gating" -> falsified by RE-7 lower bound <= 0.
- "model-free advantage is real (not overhead)" -> falsified by RE-8 classifier latency > draft-forward band.
