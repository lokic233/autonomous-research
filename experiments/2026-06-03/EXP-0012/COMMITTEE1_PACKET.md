# COMMITTEE#1 — CLAIM-0010 (PROJ-0002), evidence EXP-0012 (L0)
## THIS IS A REDESIGN of CLAIM-0008, which YOU (committee) RED'd in VERDICT-0009 for: (1) CIRCULARITY (predictor features = generative params -> tautological oracle-gap-0); (2) RT-only STRAWMAN baseline (no H2O/SnapKV); (3) tool-result-specificity not operationalized; (4) Scissorhands/ACON undistinguished. This L0 was built to fix ALL FOUR. Verify it actually did. Vote HONESTLY+HOSTILELY — this is the instance's best green-candidate, so scrutinize the circularity-break and the H2O baseline hardest. If candidate-grade, name SPECIFIC GPU/real-model required_evidence. novelty_killer: live >=2-source prior-art sweep OWED — MUST distinguish Scissorhands (persistence-of-importance), ACON (real agent compression, AppWorld), H2O/SnapKV, LLMLingua.

## HOW THE 4 PRIOR REDS WERE ADDRESSED (audit these claims):
1. CIRCULARITY BROKEN: latent reference-propensity theta is read ONLY in generate_trace() + policy_ORACLE (audit: grep theta in sim.py). RT/H2O/CAUSAL never see it. CAUSAL scores from NOISY observables only (0.55*ngram_hit + 0.45*decayed_past_attention + noise) + 10% span-boundary detection error. Predictor AUC is MEASURED not assumed.
2. RIGHT BASELINE: 3 policies + oracle — recency-trunc, H2O/SnapKV attention-eviction (keep highest accumulated PAST attention), noisy CAUSAL predictor, ORACLE (theta, upper bound only). Token budget matched.
3. TOOL-RESULT-SPECIFIC: the win is on DELAYED-CALLBACK tool-result spans (cold-when-evicted, hot-later) that H2O's past-attention provably misses — not generic prose.
4. TWO AUCs reported: overall-ref AUC ~0.49-0.61 (weak, expected — H2O catches those) vs critical-handle AUC ~0.59-0.82 (the decision-relevant axis).

## CLAIM
claim: "For long-horizon tool-calling agents, a CAUSAL retention policy that predicts\
  \ which committed tool-result spans will be re-referenced \u2014 using only a NOISY,\
  \ realizable past-signal proxy (decayed past-attention mass / repeat-substring hits,\
  \ NOT the ground-truth reference process) with realistic span-boundary detection\
  \ error \u2014 achieves a strictly better context-length / task-success Pareto than\
  \ (a) recency-truncation AND (b) attention-based KV eviction (H2O/SnapKV-style),\
  \ on traces where the predictor's future-reference AUC is measured (not assumed),\
  \ with the win surviving when predictor AUC is realistically imperfect (<0.85)."
why_it_matters: 'VERDICT-0009 RED''d CLAIM-0008 because its L0 was CIRCULAR (predictor

## L0 RESULTS (EXP-0012, effect=keep-exploring, PARTIAL-HELD)
# RESULTS — EXP-0012 (CLAIM-0010, PROJ-0002) — researcher-0011
L0 CPU-only, stdlib-only, SERIAL trace simulation. 64 seeds. Paired bootstrap (5000) 95% CI.
On-disk truth: `results/results.csv` (6400 rows). Full table: `RESULTS_TABLE.md`. Repro: `python3 sim.py && python3 analyze.py`.

## VERDICT: PARTIAL-HELD (scope-limited, mechanism-specific, honest)
The noisy causal predictor **does beat H2O/SnapKV at realistic measured AUC (<0.85)** — but ONLY
on the sharp task-chain metric (M2), only at moderate-to-large budgets, and the effect decays as
critical-handle AUC drops. On aggregate availability (M1) it merely **ties** H2O. This is NOT the
strawman (it genuinely beats H2O, not just RT), and it is NOT circular (predictor never sees the
latent cause). But it is narrower than a clean "strictly-better-Pareto-everywhere" HELD.

## DID WE BREAK THE CIRCULARITY? YES.
- The latent reference-propensity `theta` (the GENERATIVE CAUSE of future references) is read ONLY
  in `generate_trace()` (trace gen) and `policy_ORACLE` (upper bound). Audit:
  `grep 's\["theta"\]' sim.py` -> appears in generate_trace + oracle only. RT/H2O/CAUSAL never touch it.
- CAUSAL scores spans from NOISY observables only: `0.55*ngram_hit + 0.45*decayed_past_attention + N(0,sigma)`,
  plus realistic span-boundary detection error (10% adjacent-span score blending).
- Predictor quality is MEASURED, not assumed: we report future-reference AUC computed from the noisy
  observables vs realized references, swept across sigma. NO "oracle gap = 0" tautology.

## DID WE USE THE RIGHT BASELINES? YES — 3 + oracle.
(P-RT) recency-truncation. (P-H2O) attention-eviction = keep highest accumulated PAST attention
(H2O/SnapKV heavy-hitter). (P-CAUSAL) noisy reference predictor. (P-ORACLE) sees theta = upper bound only.
Token budget matched across all four.

## TWO AUCs (the honest x-axis distinction)
- overall-ref AUC ≈ 0.49–0.61: the noisy proxy is a WEAK predictor of *generic* references. Correct &
  expected — most generic refs go to non-delayed high-saliency spans that H2O ALSO catches via past
  attention. There is no edge to be had there.
- **critical-handle AUC ≈ 0.59–0.82** (the DECISION-RELEVANT axis): the proxy's ability to identify the
  *delayed-callback tool-result spans* whose re-reference GATES the task. This is what CLAIM-0010 is about
  ("which committed tool-result spans get re-referenced"). The n-gram/handle signal carries this; H2O's
  past-attention does NOT (those spans are COLD when evicted, hot only later).

## HEADLINE PARETO (m2_task = all-critical-callbacks-retained; 64 seeds)
| crit_AUC | budget_frac | CAUSAL | H2O | RT | ORACLE | (CAUSAL−H2O) 95%CI | beats H2O? |
|---|---|---|---|---|---|---|---|
| 0.823 | 0.3 | 0.27 | 0.00 | 0.00 | 0.73 | [+0.062,+0.234] | YES |
| 0.823 | 0.5 | 0.42 | 0.00 | 0.00 | 1.00 | [+0.141,+0.359] | YES |
| 0.823 | 0.6 | 0.55 | 0.00 | 0.00 | 1.00 | [+0.188,+0.406] | YES |
| 0.779 | 0.5 | 0.30 | 0.00 | 0.00 | 1.00 | [+0.125,+0.328] | YES |
| 0.779 | 0.6 | 0.41 | 0.00 | 0.00 | 1.00 | [+0.156,+0.359] | YES |
| 0.716 | 0.6 | 0.30 | 0.00 | 0.00 | 1.00 | [+0.094,+0.281] | YES |
| 0.635 | 0.6 | 0.16 | 0.00 | 0.00 | 1.00 | [+0.016,+0.156] | YES |
| 0.588 | any | 0.00 | 0.00 | 0.00 | varies | [+0.000,+0.000] | no (tie) |
| <0.72 | frac≤0.4 | 0.00–0.06 | 0.00 | 0.00 | — | CI incl. 0 | no (tie) |

**KEY**: On the task-chain metric, H2O and RT score 0.000 essentially EVERYWHERE — they NEVER retain
the delayed cold callback handles. CAUSAL is the only realizable policy that does, because it reads the
n-gram/handle signal H2O ignores. That is the entire, non-circular, tool-result-specific contribution.

## DOES IT BEAT THE ATTENTION-EVICTION BASELINE AT AUC < 0.85? YES, conditionally.
- Robust win (CI_lo>0) at crit_AUC ∈ {0.823, 0.779} for frac≥0.4; extends to crit_AUC=0.635 at frac=0.6.
- Decays out: at frac≤0.3 and/or crit_AUC≤0.72, the win shrinks to a tie (CI includes 0).
- At crit_AUC=0.588 it ties at 0 (both fail). So the win needs crit_AUC ≳ 0.64 AND a non-tight budget.

## WHERE IT DOES *NOT* WIN (honest negatives within the experiment)
- Aggregate availability (M1): CAUSAL ≈ H2O (beats H2O in only 2/25 cells, both at top AUC). H2O is a
  genuinely strong baseline for the bulk of references. The causal policy buys you the *critical chain*,
  not better average recall. If your task cares about average recall, H2O is as good and simpler.
- Tight budgets (frac=0.2–0.3) at realistic AUC: tie. No free lunch when budget is brutal.

## CLASSIFICATION RATIONALE (vs PREREGISTRATION sec 7)
Prereg HELD = "strictly beats H2O+RT at AUC<0.85 in SOME regime, and beats RT too." That literally holds
(9 cells). But prereg also flags PARTIAL if the win is knife-edge or metric-specific. The win is REAL and
non-circular, beats H2O specifically (not strawman), and survives at clearly-realistic AUC=0.64–0.78 — but
it is confined to the task-chain metric and decays at tight budgets. We report it as **PARTIAL-HELD** to
avoid overclaiming: the mechanism works, the regime is bounded, and the headroom-to-oracle is large
(oracle hits 1.0 where CAUSAL hits 0.3–0.55 — the noisy proxy leaves most of the win on the table).

## PRIOR-ART CAVEAT (sweep owed before any novelty claim)
This is a SIMULATION, not a model run. It establishes the MECHANISM is sound in principle, not novelty.
- **H2O (Zhang'23) / SnapKV**: accumulated-attention heavy-hitter eviction = our P-H2O. We beat it ONLY
  on delayed-cold callbacks; on heavy-hitters they're equal. Differentiator = the COLD-THEN-HOT span.
- **Scissorhands (Liu'23) "persistence of importance"**: claims token importance is temporally STABLE.
  Our delayed-callback structure is the explicit COUNTEREXAMPLE (importance is NON-persistent: cold at
  commit, hot later). The contribution lives EXACTLY in the regime where Scissorhands' assumption breaks.
  An L1 MUST test whether real tool-agent traces actually violate persistence (if they don't, this dies).
- **ACON (agent-context compression)**: closest applied work; real agent tool-output compression. Head-to-head owed.
- **LLMLingua**: prose/prompt compression — different target (not KV, not tool-specific). Lower priority.

## WHAT A REAL-MODEL L1 MUST MEASURE
1. Use REAL accumulated attention from a real LLM as the H2O signal AND as a predictor input (not synthetic).
2. Measure REAL future-reference AUC by tracking which committed tool-result tokens actually get
   attended-to/dereferenced downstream — and specifically the DELAYED-reference subset (the whole edge).
3. Use a REAL multi-step tool-agent benchmark; report TASK ACCURACY, not a synthetic availability proxy.
4. Head-to-head at matched KV budget vs H2O / SnapKV / Scissorhands / ACON.
5. VERIFY the load-bearing assumption empirically: do real tool-result references violate persistence-of-
   importance (cold-then-hot)? If real traces don't have delayed cold callbacks, the edge over H2O vanishes.

## LIMITATIONS / THREATS TO VALIDITY (brutal)
- The win is ENGINEERED INTO the generative model (we built delayed cold callbacks H2O can't catch).
  L0 shows: IF such structure exists AND the n-gram proxy tracks it at AUC≳0.64, THEN causal beats H2O.
  It does NOT show real tool traces have this structure — that is the single biggest open risk (see L1 #5).
- crit_AUC=0.823 is borderline (≈0.85). The clean sub-0.78 wins (0.78, 0.72, 0.64 at frac≥0.4–0.6) are
  the load-bearing realistic-AUC evidence.
- Synthetic n-gram signal is generous (0.80 hit rate for true handles). Real handle-recurrence may be noisier.

## PRE-REG (committed pre-run)
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

## ORCHESTRATOR NOTE: honest bounds the researcher disclosed — ties H2O on AGGREGATE availability (M1, beats H2O in only 2/25 cells); ties at tight budgets (frac<=0.3) and at crit-AUC<=0.588; LARGE oracle headroom (oracle 1.0 where CAUSAL 0.3-0.55). The win is real, non-circular, beats the RIGHT baseline, but is task-chain-metric-specific + regime-bounded. A real-model L1 (real attention as predictor on real tool-agent traces, real task pass@1) is the natural ask if candidate-grade.
