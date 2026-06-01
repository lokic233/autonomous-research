# PROJ-0004 — RESEED Candidate Charters (post-CLAIM-0013 kill)

**Author:** researcher-proj4-reseed-r4 (orchestrator-r4-001, session be17b683)
**Date:** 2026-06-01
**Context:** CLAIM-0013 (K=8 position-from-boundary acceptance cliff) was KILLED clean at L0 (DEAD-0011 / VERDICT-0053).
The kill experiment EXP-0046 surfaced TWO robust, replicated findings worth a fresh PROJ-0004 claim:
  (S1) A DRAMATIC single-token (d=1) acceptance COLLAPSE immediately after a tool-result injection:
       top-1-agreement acc ~0.025 (CC) / ~0.051 (Codex) vs interior baseline ~0.253/0.271, Holm-sig,
       replicated BOTH corpora — but it is a CONTENT-TYPE-TRANSITION cost (prose-after-non-prose), NOT
       a boundary-position effect (proven by the content-spliced null, control C1).
  (S2) Codex post-tool resumption text at d>=3 is MORE predictable than interior baseline (formulaic
       resumptions "Now I'll ...", acc up to 0.48) — a speedup opportunity, inverse of the killed cliff.
**Hard non-collision constraints (load-bearing):**
  - MUST NOT re-litigate DEAD-0011's killed POSITION cliff. DEAD-0011 revival_conditions require a real
    neural SD pair showing a d>=2 position-from-boundary cliff EXCEEDING the content-spliced null — OUT OF
    SCOPE here. Both charters below are explicitly NOT position-from-boundary claims.
  - PROJ-0002 = SEMANTIC prefix-invalidation cost-map (content edit -> recompute). PROJ-0005 = LEXICAL
    BPE re-tokenization seam churn (prefill hit->miss). Both charters below are DECODE-time draft-acceptance.
  - PROJ-0003 = failure attribution. Distinct.
**Instruments:** already-parsed CC/Codex/Gemini agent-trace corpora (EXP-0046 reused them); EXP-0046
  acceptance_proxy.py + acceptance_proxy.json on-node; Mac CPU stdlib-only (NO torch/HF cache); H100
  devgpu014 ros-vllm 0.6.6 / ros-vllm07 via GPU coordinator for any real-SD L1 confirm.

---

## CANDIDATE A — Format-Transition Speculation Cost: the d=1 collapse is a PREDICTABLE per-turn waste site, mitigable model-free
**(STRONGEST + cheapest-to-first-signal — RECOMMENDED. Builds directly on surviving finding S1, framed CORRECTLY as content-transition not position.)**

### 1. THESIS
The single-token acceptance collapse EXP-0046 found at the first assistant token after a tool-result
injection is a CONTENT-FORMAT-TRANSITION cost — predicting the first prose token after injected non-prose
(JSON / code / stdout / table) is hard *wherever that prose-after-non-prose transition occurs*, and the
SIZE of that one-token cost is PREDICTABLE, model-free, from the FORMAT CLASS of the injected payload
(JSON vs code vs stdout vs table vs short-scalar). Because the cost is concentrated at exactly d=1 (already
established), a 1-token speculation SUPPRESSION (don't speculate the single transition token; resume normal
speculation at d>=2) recovers a quantifiable fraction of per-turn wasted draft FLOPs at zero accuracy cost
(SD is exact). This is a content-transition characterization + an actionable model-free serving policy —
NOT a position-from-boundary claim (DEAD-0011).

### 2. NOVELTY vs PRIOR ART (web-verified 2026-06-01, precise delta)
- **"Disparate Impacts of Speculative Decoding" (arXiv:2510.02128)** — establishes acceptance ≈ drafter
  fitness (1−rq) varies by TASK/language axis (global per-task quantity). Delta: we localize a recurring
  INTRA-sequence rq spike to a single content-format-TRANSITION token and predict its magnitude from the
  preceding payload's format class. We instantiate their theory at a transition granularity they never
  isolate; we CITE 2510.02128 as the named confounder and frame the d=1 cost as a content effect (exactly
  what their theory predicts, now measured at the transition).
- **"Acceptance Dynamics Across Cognitive Domains in SD" (arXiv:2604.14682, Mahmoud)** — varies acceptance
  by cognitive TASK domain (cross-task). Delta: our axis is intra-turn content-FORMAT transition (JSON/code/
  stdout), orthogonal to cognitive domain; the cost recurs many times within ONE task at each tool return.
- **Berkeley "Efficient LLM System with Speculative Decoding" (EECS-2025-224 / escholarship 2cm0c15n)** —
  benchmarks find "acceptance behavior varies dramatically across token positions, requests, and datasets"
  and verification is the dominant cost. Delta: that is an AGGREGATE position/request/dataset variance
  observation; we give the MECHANISM for one specific, dominant, recurring position (the format-transition
  token), make it model-free PREDICTABLE from payload format class, and tie it to a 1-token suppression policy.
- **"Optimizing Agentic LM Inference via Speculative Tool Calls" (arXiv:2512.15834, Nichols/Bhatele LLNL)** —
  speculates the TOOL CALL / parallelizes around tool waits (gaps from waiting on tool completion). Delta:
  opposite side of the boundary — they speculate emitting/executing the call; we characterize the acceptance
  COST of the first token *after the result returns* and resumption begins, and a suppression mitigation there.
- **Adaptive-length / confidence-gated SD family — SpecDec++ (2405.19715), TALON (2601.07353), SpecBound
  (2604.12247), PACER (2602.01274), SpecKV (2605.02888)** — all gate speculation on DRAFT-MODEL confidence/
  entropy learned at run time (a trained head or per-step probability). Delta + NON-COLLISION: our gate is
  a MODEL-FREE, payload-format-derived, single-token suppression decidable BEFORE any draft forward pass
  (you know the preceding span was JSON/stdout from the harness, no acceptance-prediction head needed). We
  must show the format-class gate is NOT already subsumed by an entropy/confidence gate (control: condition
  on draft entropy at d=1; the format-class signal must add predictive value, AUC CI>0.5 over the entropy null).
- **Non-collision check:** distinct from DEAD-0011 (we explicitly DO NOT claim a position-from-boundary
  effect; the cost is content-transition, concentrated at d=1, and we cite the splice-null finding as the
  basis). Distinct from PROJ-0005 (prefill-time BPE seam) and PROJ-0002 (semantic invalidation). Not in any
  cemetery duplicate_pattern.

### 3. FIRST FALSIFIABLE CLAIM (CLAIM-shaped)
CLAIM-A0: "Across >=2 agent-trace corpora, the first-assistant-token (d=1) acceptance cost after a tool-result
injection (a) is PREDICTABLE from the injected payload's FORMAT CLASS alone (JSON / code / stdout / table /
short-scalar), with a model-free multiclass-or-regression predictor achieving AUC (or rank-correlation) whose
95% CI excludes 0.5 (resp. 0), AND (b) is overwhelmingly concentrated at d=1 (re-confirming EXP-0046: >=80%
of the cumulative cost over d=1..K sits at d=1, CI>threshold), SO THAT (c) a 1-token speculation-suppression
policy recovers a measured fraction X% of per-turn wasted draft-verify FLOPs (FLOPs spent drafting tokens
that get rejected at the transition) at zero accuracy change. PASS requires (a) AUC/corr CI excludes
chance AND (b) >=80% concentration at d=1 AND the format-class signal survives a draft-ENTROPY-conditioning
control (adds AUC over entropy-only). FAIL / negative: format class does NOT predict the d=1 cost (CI
includes chance) -> the cost is format-blind (uniform transition tax), which is ITSELF a clean publishable
result (one-token suppression still works, just not format-tunable); OR the cost is NOT d=1-concentrated in
real-SD telemetry -> reverts toward the killed cliff territory and dies."

### 4. CHEAP GATING EXP (Level-0, CPU, stdlib, hours; what a negative looks like)
- **L0 (Mac CPU, reuse EXP-0046 harness):** From the already-parsed CC/Codex corpora, for each tool-result
  turn: (i) classify the injected payload's format class by cheap model-free regexes (JSON-ish {}/[], code-
  fence/indent, stdout/log lines, markdown table |---|, short scalar). (ii) Recompute the top-1-agreement
  d=1 acceptance cost per turn (already have the proxy). (iii) Fit a model-free predictor (format class ->
  d=1 cost) with session-clustered bootstrap CI on AUC/rank-corr; report d=1 concentration share; run the
  entropy-conditioning control (does format class add over predictor-entropy quartiles at d=1?). (iv)
  Estimate FLOPs recovered = (mean draft tokens proposed per turn that fail at d=1) x (per-turn count).
- **Negative look:** AUC CI straddles 0.5 (format class uninformative) OR concentration < 80% at d=1 OR
  format signal vanishes under entropy conditioning. A flat/format-blind result is still informative
  (uniform 1-token transition tax + suppression) and is reported honestly, NOT spun as the format claim.
- **L1 (H100 devgpu014, OPTIONAL, GPU-coordinator gated):** confirm with REAL vLLM SD accepted-length
  telemetry (ngram/EAGLE draft) that the d=1 cost is real (not a 2-gram proxy artifact) and that 1-token
  suppression recovers wall-clock/verify-FLOPs on a capped trajectory set. Watchdog + HBM cap; H100 only
  (honor MI350X postmortem). Only spend if L0 AUC clears the gate.

### 5. WHY IT MATTERS (Meta inference-opt / agent-infra)
Agentic serving (coding agents, tool-calling assistants) is THE workload where SD is deployed and decode
dominates cost; every tool return triggers exactly one of these transition tokens, many times per session.
If the d=1 transition token is a reliable, format-predictable rejection site, a near-zero-cost serving
policy (skip speculating 1 token after each tool return, or pick draft-length=0 for that step) recovers
wasted verify FLOPs at zero accuracy/quality risk (SD is exact) — a clean serving win on a real Meta-shaped
workload, decidable model-free from the harness without a trained acceptance head. The negative (format-
blind) still hands serving teams a simple universal 1-token suppression rule.

### 6. FEASIBILITY on-node
- L0: Mac CPU stdlib only; reuses EXP-0046's acceptance_proxy.py + parsed corpora + acceptance_proxy.json
  -> first signal in HOURS, no GPU, no install. The format-class regexes are trivial.
- L1: ros-vllm 0.6.6 / ros-vllm07 on H100 supports ngram/EAGLE SD accepted-length telemetry; bounded,
  watchdogged, via GPU coordinator. NOT required for the first signal.
- Highest reuse, lowest first-signal cost, directly on the load-bearing surviving finding. RECOMMENDED.

---

## CANDIDATE B — Resumption Super-Predictability: post-tool agent resumptions are MORE speculation-friendly than interior text
**(cheap, complementary; builds on surviving finding S2 — the INVERSE of the killed cliff.)**

### 1. THESIS
After the d=1 transition token, agent post-tool RESUMPTION text (d>=3) is MORE predictable than interior
baseline text because resumptions are formulaic ("Now I'll ...", "The output shows ...", "Based on the
results, ..."). Therefore the post-tool resumption WINDOW is a positive speculation opportunity: a serving
policy can speculate MORE AGGRESSIVELY (longer draft length / a small resumption-phrase n-gram drafter)
in the resumption window than in interior text, raising accepted-length per drafting round. This is the
INVERSE of the killed cliff — a speedup, not a penalty — and is a content-predictability claim, NOT a
position-from-boundary penalty claim (so it cannot revive DEAD-0011).

### 2. NOVELTY vs PRIOR ART (web-verified 2026-06-01, precise delta)
- **Staged Speculative Decoding (arXiv:2308.04623)** — n-gram models cheaply decode "easy/obvious" tokens
  (whitespace) in batch. Delta: we show a SPECIFIC, recurring, semantically-rich easy region (formulaic
  agent RESUMPTION prefixes) on real agent traces, quantify its excess predictability over interior baseline,
  and tie a window-conditioned draft-length boost (or a tiny resumption-phrase drafter) to it.
- **"Optimizing Agentic LM Inference via Speculative Tool Calls" (arXiv:2512.15834)** — speculates the tool
  call / hides tool-wait latency. Delta: we exploit predictability AFTER the result returns (the resumption
  text), an axis they do not touch; complementary lever.
- **"Disparate Impacts of SD" (2510.02128) / "Acceptance Dynamics Across Cognitive Domains" (2604.14682)** —
  acceptance varies by task/domain (global). Delta: we identify a within-trajectory region (resumption
  window) that is SYSTEMATICALLY EASIER than the same task's interior, conditioning on a structural agent
  event (tool return) rather than task identity.
- **Adaptive-length SD (SpecDec++ 2405.19715, TALON 2601.07353, SpecBound 2604.12247)** — increase draft
  length when draft is confident (run-time learned). Delta + NON-COLLISION: we provide a MODEL-FREE
  STRUCTURAL prior (you are in a post-tool resumption window -> raise draft length) usable WITHOUT a
  confidence head, and must show it adds value over a confidence-only gate (control as in A).
- **Non-collision check:** explicitly NOT a position-from-boundary PENALTY (DEAD-0011 is a penalty/cliff;
  this is a predictability GAIN). Distinct from PROJ-0002/0005 (prefill). Not in any duplicate_pattern.

### 3. FIRST FALSIFIABLE CLAIM
CLAIM-B0: "Across >=2 agent-trace corpora, mean draft acceptance in the post-tool resumption window (d in
[3, W]) EXCEEDS the trajectory interior baseline by a margin whose session-clustered 95% CI excludes 0, AND
this excess is attributable to formulaic resumption prefixes (it shrinks under a control that masks/holds-out
the first M resumption tokens), SO THAT a window-conditioned draft-length boost raises measured accepted-
length-per-round by Y% in the window. PASS = excess CI>0 AND survives a 'remove formulaic prefix' control
(showing the gain is the formulaic head, not a global per-corpus artifact) AND is replicated in >=2 corpora.
FAIL / negative: resumption window acceptance is NOT above interior (CI includes 0 or negative) in one/both
corpora -> the EXP-0046 Codex super-predictability was corpus-specific / proxy-specific and does not
generalize; report honestly as a non-result. (Note EXP-0046 saw this in Codex but NOT clearly in CC, so
cross-corpus replication is the real risk and the honest gate.)"

### 3a. KNOWN RISK (stated up front, anti-coping)
EXP-0046 observed the d>=3 super-predictability strongly in CODEX but the CC table shows d=3 penalty ~ -0.026
(near baseline), NOT a clear gain. So B's cross-corpus replication is GENUINELY at risk; the L0 gate's
>=2-corpora requirement is the honest kill condition. Do not seed B as primary unless A is also seeded.

### 4. CHEAP GATING EXP (Level-0, CPU, hours; what a negative looks like)
- **L0:** reuse EXP-0046 corpora/proxy; compute resumption-window (d in [3,W]) acceptance vs interior with
  session-clustered bootstrap CI in BOTH CC and Codex; run the formulaic-prefix-holdout control; estimate
  accepted-length-per-round gain from a window-conditioned draft-length boost.
- **Negative look:** CI includes 0 / negative in CC (or both) -> not replicated -> kill cheaply (the Codex
  signal was corpus-specific). This is the most likely failure mode and is fine to report.
- **L1 (optional, GPU-coordinator):** real vLLM SD accepted-length telemetry confirming the window boost.

### 5. WHY IT MATTERS (Meta inference-opt / agent-infra)
A model-free structural rule "you just returned from a tool -> the next sentence is formulaic -> draft
longer / use a cheap resumption n-gram drafter" raises accepted-length-per-round exactly in the high-
frequency post-tool region of agent serving, at zero accuracy cost. It is the positive twin of Candidate A
(A suppresses the 1 bad transition token; B exploits the easy resumption phrase right after) — together
they form a complete model-free post-tool SD scheduling micro-policy.

### 6. FEASIBILITY on-node
- L0: Mac CPU stdlib, reuses EXP-0046 harness/corpora -> first signal in hours, no GPU. Cross-corpus
  replication is the only real cost/risk.
- L1: H100 ros-vllm telemetry, optional, via GPU coordinator.

---

## RECOMMENDATION
**Seed CANDIDATE A as the fresh PROJ-0004 first claim (CLAIM-shaped CLAIM-A0).** It (1) builds directly on
the LOAD-BEARING surviving finding (the replicated d=1 collapse), (2) is framed CORRECTLY as a content-
format-transition cost citing 2510.02128 — so it CANNOT revive the killed position-cliff (DEAD-0011), (3) is
cheapest-to-first-signal (reuses EXP-0046 proxy + corpora, CPU/stdlib, hours), (4) has a clean actionable
serving payoff (model-free 1-token suppression recovering verify FLOPs at zero accuracy cost) that is novel
vs the entropy/confidence-gated adaptive-length family (model-free, harness-decidable, pre-draft), and (5)
has an informative negative (uniform format-blind transition tax -> still a universal suppression rule).
**Seed CANDIDATE B as a companion/second claim ONLY** (its cross-corpus replication is genuinely at risk —
EXP-0046 saw the resumption gain in Codex but not clearly in CC; the >=2-corpora gate is the honest kill).
A+B together = a complete model-free post-tool SD micro-policy (suppress the bad transition token, exploit
the easy resumption phrase), which is the strongest framing for the reseeded PROJ-0004.
