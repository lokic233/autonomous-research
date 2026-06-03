# RESULTS — EXP-0023 (L0, CPU sim) — CLAIM-0016
claim=CLAIM-0016 | exp=EXP-0023 | task=TASK-0022 | proj=PROJ-0005
researcher=researcher-0023 | node=cli:dengcchi-mac | 2026-06-03
VERDICT: **PARTIAL / CONDITIONAL** (claim B holds only in a bounded regime; FAILS the
strong bar in the high-verbosity regime where the claim's own intuition predicted it should
win MOST). Anti-circularity holds. Both compressors dominate the truncation strawman.

## SETUP (pre-registered, unchanged)
Synthetic multi-agent traffic: 4 roles, latent receiver-need vectors (UNobserved),
spans = act-on (role-relevant, decided by latent need·topic) + role-irrelevant verbosity.
3 compressors at MATCHED token budget: (a) recency truncation, (b) GENERIC LLMLingua-style
(rank by role-AGNOSTIC salience proxy), (c) ROLE-CONDITIONED (rank by noisy role-match
feature = realizable receiver-role+task signal, NEVER the label). Oracle = rank by true
act-on (upper bound, not a competitor). 8 seeds × 400 msgs; bootstrap 2000× 95% CI on the
per-message (rolecond − generic) task-success delta. Sweep verb_frac{.2,.4,.6,.8} ×
feature_noise{low,med,high}→AUC × ratio{.3,.5,.7}. task-success = act-on token mass kept.

## MATCHED-RATIO CONTROL — PASSED
Actual kept-fraction identical across compressors: target .3→.290/.290, .5→.488/.488,
.7→.683/.683 (generic/rolecond). Comparisons are at genuinely matched token cost.

## (A) IS THERE ROLE-IRRELEVANT VERBOSITY / DOES ROLE-CONDITIONING HELP? — YES, but only
   in a bounded regime, and the effect REVERSES as verbosity grows.
Mean (rolecond − generic) task-success delta by verbosity (avg over noise,ratio):
  verb_frac=0.2: +0.124   (role-conditioning helps strongly)
  verb_frac=0.4: +0.058
  verb_frac=0.6: +0.010   (~tie)
  verb_frac=0.8: -0.053   (GENERIC WINS — role-conditioning HURTS)
By predictability (AUC of role-match vs latent act-on):
  noise=low  AUC≈0.75: +0.103   noise=med AUC≈0.68: +0.038   noise=high AUC≈0.60: -0.037
=> Role-conditioning helps ONLY when act-on is predictable from role (AUC ≳ 0.65–0.70)
   AND verbosity is low-to-moderate. Counter-intuitively it LOSES exactly where the claim
   said the win should be biggest (lots of role-irrelevant verbosity, verb_frac=0.8).

## (B) DOES ROLE-CONDITIONED BEAT GENERIC AT MATCHED RATIO? — CONDITIONAL (the real bar)
Significant cells (bootstrap CI excludes 0), 36 cells = 4 verb × 3 noise × 3 ratio:
  rolecond BEATS generic (CI_lo>0): 21/36
  generic  BEATS rolecond (CI_hi<0): 12/36
  tie (CI∋0): 3/36
Win/lose separates almost perfectly on AUC × verbosity:
  AUC when rolecond WINS:  mean 0.720 (range .629–.815); verb_frac mean 0.38
  AUC when rolecond LOSES: mean 0.623 (range .585–.702); verb_frac mean 0.68
The boundary (per verb×noise, # of 3 ratios sig-positive):
  verb .2: low+3 med+3 high+3   verb .4: low+3 med+3 high −2
  verb .6: low+3 med +2/−1 high −2   verb .8: low +1/−1 med −3 high −3
=> CLAIM (B) HOLDS in the low-verbosity / high-AUC quadrant, FAILS the strong bar in the
   high-verbosity / low-AUC quadrant. Because act-on spans are always "contentful," generic
   salience is itself a strong act-on proxy; when the realizable role signal is noisy
   (low AUC) and most of the message is verbose, generic's broad "keep contentful" beats a
   degraded role-conditioned ranking at the SAME budget.

## TRUNCATION STRAWMAN — both beat it everywhere
rolecond > truncation: 36/36.  generic > truncation: 36/36. Truncation is the floor; the
real contest is rolecond vs generic, as pre-registered.

## ANTI-CIRCULARITY — PASSED
- role-match AUC vs latent act-on: 0.585–0.815 (realizable, degraded view of latent need).
- generic salience AUC vs act-on: ~0.57–0.69 (role-agnostic, lower).
- Oracle act-on mass retained > rolecond in 36/36 cells; mean oracle−rolecond gap = 0.278
  (min 0.082). Role-conditioned NEVER reaches the oracle => it is NOT reading the label.
  No sign of the CLAIM-0008/0013 circularity failure.

## PARETO (task-success at matched token-saved) — frontier owner is REGIME-DEPENDENT:
   verb .2 low-noise ratio .5:  oracle .938 > ROLECOND .766 > generic .535 > trunc .503
   verb .4 high-noise ratio .5: oracle .974 > generic .617 > rolecond .594 > trunc .502
   verb .8 high-noise ratio .5: oracle .999 > GENERIC .742 > rolecond .609 > trunc .520
  => Below the oracle, the Pareto frontier owner FLIPS between rolecond and generic
     depending on (verbosity, AUC). Neither dominates the other globally.

## HELD / PARTIAL / NEGATIVE
**PARTIAL.** Claim B is NOT supported as a general statement. Role-conditioning beats the
strong generic baseline at matched ratio ONLY when (i) act-on is reasonably predictable from
role+task (AUC ≳ 0.65) AND (ii) role-irrelevant verbosity is low-to-moderate. In the
high-verbosity regime — the regime the claim's narrative says should favor role-conditioning
MOST — a generic role-agnostic compressor WINS at matched ratio (CI excludes 0). So the
claim's stated *mechanism* ("verbose messages have role-irrelevant content only a role
filter can drop") is NOT what the sim shows: under a realistic model where act-on content is
also high-salience, a generic salience filter captures act-on content well, and role
conditioning only adds value when the realizable role signal is strong AND verbosity modest.

## CAVEATS / MODEL ASSUMPTIONS THAT DRIVE THE RESULT (honest)
- Result hinges on the act-on↔salience coupling: I made act-on spans always "contentful"
  (high generic salience) and 55% of verbose spans also contentful. If real inter-agent
  act-on content were LOW-salience (terse) while verbosity were HIGH-salience (flowery
  reasoning), generic would fail and role-conditioning would win broadly. The sim cannot
  resolve which is true of REAL traffic — that is the L1 question.
- task-success = act-on token-mass retained (proxy); no real receiver acting/regenerating.

## WHAT A REAL L1 SHOULD MEASURE
- REAL multi-agent traces (AutoGen / CrewAI / LangGraph) with real role taxonomy; extract
  which message spans each receiver actually conditions its next action on (ground truth via
  ablation: drop a span, see if the receiver's downstream action/tool-call changes).
- REAL LLMLingua / LongLLMLingua as the generic baseline (not a proxy), threshold-tuned to
  matched ratio.
- A REAL role-conditioned extractor: small classifier or LLM-judge scoring spans by
  receiver role+task (NOT the act-on label). Measure its AUC vs the ablation ground truth +
  oracle gap.
- REAL task-success: end-to-end task completion / tool-call correctness after compression,
  not token-mass retention.
- CRUCIALLY measure the act-on↔salience correlation in real traffic — that single quantity
  decides whether role-conditioning beats generic (this sim shows the sign of the win flips
  with it).

## PRIOR-ART CAVEAT
- Generic prompt compression is published & role-agnostic: LLMLingua / LongLLMLingua /
  LLMLingua-2 (Microsoft) — perplexity/salience token dropping; NO receiver-role conditioning.
- Multi-agent communication efficiency is an active area: CodeAct (actions-as-code reduces
  NL chatter), "communication-efficient MAS" / "talk less" agent-comms papers, and various
  agent-message-summarization works — several already condition on context.
- The DEAD single-agent CLAIM-0008/0013 (this instance) failed on circularity.
- NOVELTY remaining = the RECEIVER-ROLE-CONDITIONED *inter-agent* span filter specifically.
  Be honest: (compression) and (MAS comms-efficiency) are both well published; the precise,
  testable novelty is narrow AND — per this L0 — its advantage over a generic compressor is
  conditional, not general. Worth an L1 ONLY to measure the real act-on↔salience coupling and
  real role-AUC; if real act-on content is high-salience (likely for action items), generic
  may already capture most of the win and the role-conditioned delta could be small.

## ARTIFACTS
- experiments/2026-06-03/EXP-0023/PRE_REGISTRATION.md (committed before run, 35a3459)
- experiments/2026-06-03/EXP-0023/sim_compress.py
- experiments/2026-06-03/EXP-0023/results/cells.csv  (288 rows: per verb×noise×ratio×seed)
- experiments/2026-06-03/EXP-0023/results/matched_ratio_ci.csv (36 cells + bootstrap CI)
- experiments/2026-06-03/EXP-0023/logs/run.log  (elapsed 49s, serial)
