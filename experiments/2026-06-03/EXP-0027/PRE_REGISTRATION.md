# PRE_REGISTRATION — EXP-0027 (CLAIM-0026)

**Committed BEFORE running any sweep.** Researcher-0027, L0 (CPU-only, stdlib, SERIAL, ≤15 min).

## CLAIM-0026
"In long multi-turn agentic sessions, speculative-decoding draft-model acceptance rate DRIFTS
materially as context grows (early conversational prose → deep tool-call/JSON/structured context),
such that a session-phase-ADAPTIVE draft policy (adjust draft length/model by a cheap detected
context-phase signal) achieves strictly higher net tokens/sec than the BEST-TUNED FIXED draft policy
on agentic traffic."

## Two falsifiable parts
- **(A)** Does draft acceptance actually DRIFT across session phases (acceptance-vs-context-depth)?
- **(B)** Does phase-adaptive beat the BEST-TUNED FIXED draft policy by a MEANINGFUL margin
  (>~a few % net tok/s) at realistic phase mixes — OR does a single tuned k capture ≥~80% of the gain
  (the EXP-0006/EXP-0011 Jensen-floor negative)?

## THROUGHPUT MODEL (speculative decoding, standard)
For draft length k with per-token acceptance probabilities a_1..a_k (geometric-prefix accept):
- E[accepted] = sum_{i=1..k} prod_{j=1..i} a_j   (expected number of accepted draft tokens)
- tokens emitted per spec-decode cycle = E[accepted] + 1  (the +1 is the always-correct bonus/resample)
- cost per cycle = k * c_draft + c_target   (k draft forward passes + 1 target verify pass)
- net tok/s = (E[accepted] + 1) / (k * c_draft + c_target)
We use a single per-phase acceptance rate a (a_j = a constant within a phase), so
E[accepted] = a*(1-a^k)/(1-a). c_target normalized to 1.0; c_draft = r (draft/target cost ratio).
"net tok/s" is in units of 1/c_target (target-passes^-1) — comparisons are ratios so units cancel.

## SESSION-PHASE MODEL
A long session is a mixture of 3 phases with fractions (f_prose, f_tool, f_mixed), sum=1:
- **prose** (early conversational): acceptance a_prose (baseline, moderate).
- **tool/JSON** (deep structured): acceptance a_tool = a_prose + gap. We model gap in BOTH directions:
  - gap>0: structured/low-entropy → draft predicts better (HIGHER acceptance)
  - gap<0: strict JSON the small draft is bad at → LOWER acceptance
  Let the data decide; we sweep gap over a symmetric range.
- **mixed** acceptance a_mixed = midpoint of prose & tool.
DRIFT is operationalized as acceptance varying with context depth; here phase fraction shifts with
session length (deep sessions → more tool/JSON). We report drift = |a_tool - a_prose| and the
session-weighted acceptance spread.

## POLICIES (matched draft model, same a per phase)
- **(a) BEST-TUNED FIXED k\*** — sweep k in 1..32, pick the SINGLE k maximizing session-weighted
  net tok/s = sum_phase f_phase * nettps(k, a_phase). Honest strong baseline.
- **(b) PHASE-ADAPTIVE k_phase** — per-phase argmax_k nettps(k, a_phase), session-weighted, MINUS a
  switching/detection overhead penalty. We model adaptation cost two ways:
  - detection mis-classify rate p_err: with prob p_err the wrong phase's k is used (cost of bad detect).
  - switching overhead s (fractional throughput tax applied to adaptive net tok/s for re-config churn).

## METRICS
- adaptive_gain_pct = 100*(nettps_adaptive - nettps_besttunedfixed)/nettps_besttunedfixed
- fixed_captured_frac = (nettps_besttunedfixed - nettps_baseline_k1) / (nettps_adaptive_ideal - nettps_baseline_k1)
  i.e. of the total improvement over naive k=1, what fraction does the single tuned k already capture.
- Committee bar: HOLD requires adaptive_gain_pct > ~3% AND fixed does NOT capture ≥80% of adaptive gain.

## SWEEP (SERIAL, deterministic — analytic core; seeds only for the stochastic detection-error draw)
- a_prose ∈ {0.55, 0.65, 0.75, 0.85}
- gap (a_tool - a_prose) ∈ {-0.30,-0.20,-0.10, 0, +0.10,+0.20,+0.30}
- r = c_draft/c_target ∈ {0.05, 0.10, 0.20, 0.40}
- phase mix: realistic deep-session {prose .25, tool .55, mixed .20}; plus 2 alt mixes
  {.5,.3,.2} and {.1,.7,.2}
- detection error p_err ∈ {0.0, 0.05, 0.15}
- switching tax s ∈ {0.0, 0.02, 0.05}
- ≥5 seeds for the stochastic p_err realization (seeds 0..4); report mean±std.

## HONEST-NEGATIVE BRANCH (pre-committed)
Report NEGATIVE (Jensen-floor / EXP-0006-0011 outcome) if ANY of:
1. acceptance drift across phases is small in the realistic regime, OR
2. a single best-tuned fixed k captures ≥~80% of the adaptive gain at the realistic phase mix, OR
3. adaptive advantage over best-tuned-fixed is < a few % net tok/s at realistic operating points
   (especially once detection error + switching tax are included).
A negative is a WIN (honest pipeline).

## PRIOR-ART CAVEAT (pre-stated)
Draft-length adaptation is PUBLISHED: EAGLE / EAGLE-2 / Medusa / SpecDec++ / Dynamic-Speculation-
Lookahead all adapt draft length. Novelty here is narrowly the SESSION-PHASE-DRIFT characterization on
long agentic sessions + the specific question of whether it beats best-tuned-fixed. We do NOT claim
adaptive-draft-length is novel.

## L1 (what a real follow-up must measure)
Real draft+target pair on real long agentic traces: real per-phase acceptance, real adaptive-vs-tuned-
fixed tok/s on GPU, real phase-detection + switching cost. L0 here is analytic+sim only.
