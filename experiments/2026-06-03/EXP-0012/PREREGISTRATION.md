# PRE-REGISTRATION — EXP-0012 (CLAIM-0010, PROJ-0002)
researcher-0011 | L0 CPU-only, stdlib-only, SERIAL, trace simulation (no GPU/model)
Committed BEFORE running any experiment code. Honest pipeline; negatives are WINS.

## 0. WHY THIS EXISTS (the circularity that killed the predecessor)
VERDICT-0009 RED'd CLAIM-0008/EXP-0010 because:
 (C1) CIRCULAR: the causal predictor was handed the EXACT generative features of the
      reference process -> "oracle gap = 0" was a mathematical tautology, not evidence.
 (C2) STRAWMAN baseline: only compared vs recency-truncation (RT); omitted attention-based
      KV eviction (H2O/SnapKV), the real deployed competitor.
 (C3) tool-result-specificity never operationalized.
 (C4) didn't distinguish Scissorhands / ACON.
The INTUITION (tool outputs are verbose + sparsely + predictably re-referenced) survived.
Only the L0 DESIGN was broken. This experiment tests the SAME intuition WITHOUT the flaws.

## 1. HYPOTHESIS (CLAIM-0010, pre-committed, falsifiable)
H1: A causal retention policy that predicts which committed TOOL-RESULT spans get
    re-referenced — using ONLY a NOISY, realizable past-signal proxy (decayed past-attention
    mass + repeat-substring/n-gram hit counts), with realistic span-boundary detection error,
    NEVER reading the latent generative cause — achieves a strictly better
    (context-length, task-success) Pareto than BOTH:
      (a) recency-truncation (RT), AND
      (b) attention-based KV eviction (H2O/SnapKV-style: evict lowest accumulated past-attention),
    on traces where the predictor's FUTURE-reference AUC is MEASURED (not assumed),
    AND the win SURVIVES at realistically-imperfect predictor AUC (< 0.85).

## 2. DECOUPLING GENERATIVE PROCESS FROM PREDICTOR FEATURES (breaks C1 — the whole point)
The trace's TRUE future-reference process is generated from a LATENT per-span variable the
predictor NEVER observes:
  - Each committed span s has a hidden latent "reference-propensity" theta_s drawn from a
    structure that depends on (span semantic role, a hidden topic/callback graph). For
    tool-result spans, theta_s is governed by a latent "callback schedule" — some tool
    results are structurally destined to be re-queried later (e.g. an ID/handle returned
    early and dereferenced much later), others are one-shot. This latent schedule is the
    GENERATIVE CAUSE of future references.
  - Future references are sampled from theta_s (a Bernoulli/Poisson process over future
    decode steps). The predictor CANNOT see theta_s.
  - The predictor observes ONLY noisy OBSERVABLES correlated with theta_s:
       obs_s = g(decayed_past_attention_mass_s, repeat_substring_hits_s) + noise(sigma)
    These are realizable at inference time from the past only.
  - We SWEEP sigma so the predictor's MEASURED future-reference AUC ranges across
    approximately {0.6, 0.7, 0.8, 0.9}. We REPORT all results as a function of MEASURED AUC.
  - NO policy ever reads theta_s. The ORACLE (upper bound, headroom only) is the only thing
    that sees theta_s; it is NOT a competitor, just the ceiling.
INVARIANT (auditable): grep the policy code — `theta` must appear ONLY in (i) trace generation
and (ii) the oracle/AUC-measurement, NEVER in RT/H2O/causal policy decision functions.

## 3. TOOL-RESULT-SPECIFICITY (breaks C3/C4 — must be REAL, not collapse into H2O)
Spans have explicit structural roles: PROSE (model/user turns) vs TOOL_RESULT (appended
tool-output segments). Two properties make tool-result retention DIFFERENT from generic
attention-eviction:
  (S1) Tool-result spans are LONG/verbose (high token count) but their re-reference is SPARSE
       and DELAYED (long gap between commit and re-reference) — so accumulated PAST attention
       (what H2O/SnapKV use) is a WEAK signal for them: a tool result can be referenced once at
       commit, go cold for a long stretch (H2O would evict it), then be re-queried. The latent
       callback schedule explicitly encodes this delayed re-reference for a subset of TR spans.
  (S2) The repeat-substring/n-gram signal (IDs, handles, tokens that recur) is INFORMATIVE for
       tool-result re-reference specifically (handles get dereferenced) but NOT for generic prose.
  => If tool-result re-reference were just "high past attention", causal would NOT beat H2O.
     The whole contribution rests on the delayed/sparse callback structure being predictable
     from the n-gram/handle signal that H2O ignores. If that structure is absent or H2O still
     wins, that is the HONEST NEGATIVE.

## 4. POLICIES (4) — matched token budget B
All policies keep at most B tokens of committed spans; decode proceeds; a future reference to an
evicted span is a MISS.
  (P-RT)   recency-truncation: keep the most recent spans until budget B.
  (P-H2O)  attention-eviction (H2O/SnapKV-style): keep spans with highest ACCUMULATED past
           attention mass (heavy-hitters); evict lowest. Uses ONLY realizable past attention.
  (P-CAUSAL) noisy causal reference predictor: score each span by predicted future-reference
           probability from the NOISY observables (obs_s); keep highest-scoring until B. With
           realistic span-boundary detection error (boundaries jittered).
  (P-ORACLE) upper bound only: keep spans by true theta_s (sees latent). NOT a competitor.

## 5. METRICS
 - Primary: (context-length / budget B, task-success) PARETO.
 - task-success proxies (report both):
     (M1) referenced-span availability: fraction of future reference events that land on a
          retained span (recall of the future-reference process).
     (M2) sharper task proxy: TASK SOLVED iff ALL "critical" future references (the callback
          dereferences — the subset of references that gate task completion) land on retained
          spans (an all-or-nothing chain; one missing handle breaks the task).
 - predictor quality: MEASURED future-reference AUC of obs_s vs realized future references
   (computed per trace, averaged). This is the x-axis.
 - >= 8 seeds. Paired bootstrap 95% CI on (causal - H2O) and (causal - RT) deltas, per budget,
   per AUC regime.

## 6. SWEEPS
 - budget B (context length): a grid (e.g. fractions {0.2,0.3,0.4,0.5,0.6} of total committed tokens).
 - noise sigma: chosen to span measured-AUC {~0.6,0.7,0.8,0.9}.
 - seeds: >= 8.
 - serial execution only (multiprocessing BLOCKED on this Mac). Trust on-disk CSV, not stdout.

## 7. PRE-COMMITTED DECISION RULE / HONEST-NEGATIVE BRANCH
Let delta_H2O(AUC,B) = causal_success - H2O_success (paired, with 95% CI).
 - HELD: there EXISTS a budget regime where causal STRICTLY beats H2O (CI lower bound > 0)
   AT a measured AUC < 0.85, AND also beats RT. (Beating only RT = strawman, NOT held.)
 - PARTIAL: causal beats H2O only at AUC >= 0.85 (unrealistic), OR beats H2O only at a
   single knife-edge budget, OR ties H2O (CI includes 0) while beating RT.
 - NEGATIVE (a WIN): causal does NOT beat H2O at any realistic AUC (<0.85) at any budget,
   OR the apparent win requires AUC>=0.85, OR it collapses to only-beats-RT (strawman).
The honest-negative MUST fire under any of those conditions. We will NOT move goalposts.

## 8. PRIOR-ART CAVEAT (owed sweep — pre-noted)
This L0 is a SIMULATION, not a model run. It does NOT by itself establish novelty vs:
 - H2O (Zhang'23) / SnapKV — accumulated-attention heavy-hitter KV eviction (our P-H2O baseline).
 - Scissorhands (Liu'23) — "persistence of importance": importance is stable over time. Our
   delayed-callback TR structure is the explicit COUNTEREXAMPLE to persistence; that is the
   intended differentiator and must be checked against Scissorhands' claim in L1.
 - ACON (agent-context compression) — real agent tool-output compression; closest applied work.
 - LLMLingua — prompt/prose compression (different target).
A real L1 (real model, real attention as predictor, real tool-agent benchmark accuracy) is
REQUIRED before any novelty claim. This L0 only tests whether the MECHANISM can beat H2O at
realistic AUC IN PRINCIPLE under an honest, non-circular simulation.

## 8b. WHAT A REAL-MODEL L1 MUST MEASURE
 - Use REAL accumulated attention from a real LLM as the H2O signal AND as one predictor input
   (not a synthetic proxy).
 - Measure REAL future-reference AUC by tracking which committed tool-result tokens actually get
   attended-to / dereferenced downstream.
 - Use a REAL tool-agent benchmark (e.g. multi-step tool-calling traces) and report TASK ACCURACY,
   not a synthetic availability proxy.
 - Sweep vs H2O/SnapKV/Scissorhands/ACON head-to-head at matched KV budget.

## 9. EXECUTION
 - serial only; deterministic seeds; write per-config rows to results/results.csv (on-disk = truth).
 - RESULTS.md answers: does noisy-causal beat H2O/SnapKV (not just RT) at realistic AUC (<0.85)?
   in which regime? held/partial/negative.
