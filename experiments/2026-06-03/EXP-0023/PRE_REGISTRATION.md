# PRE_REGISTRATION — EXP-0023 (L0, CPU-only, stdlib-only, SERIAL, analytic/sim)
claim=CLAIM-0016 | exp=EXP-0023 | task=TASK-0022 | proj=PROJ-0005
researcher=researcher-0023 | node=cli:dengcchi-mac | date=2026-06-03

## CLAIM UNDER TEST (CLAIM-0016)
In multi-agent LLM systems, an EXTRACTIVE inter-agent message compressor that keeps only
the spans the RECEIVING agent will actually act on (predicted from the receiver's
role+task, NOT the full message) cuts total multi-agent token cost at matched
task-success, AND beats BOTH (a) recency/length truncation and (b) a generic role-agnostic
prompt compressor (LLMLingua-style) at matched compression ratio — because inter-agent
messages carry role-irrelevant verbosity a receiver-role-conditioned filter can drop but a
generic compressor cannot.

Two FALSIFIABLE parts:
  (A) Is there role-irrelevant verbosity? i.e. does receiver-role-conditioning HELP at all?
  (B) Does the role-conditioned extractor beat truncation AND generic-LLMLingua-style at
      MATCHED compression ratio + matched task-success? (beating GENERIC is the real bar —
      if it only beats truncation, role-conditioning is empty.)

## WHY PRIOR CLAIMS DIED (committee lessons — HEED)
- CIRCULARITY (CLAIM-0008/0013): predictor must NOT read the ground-truth/generative cause.
  -> Anti-circularity design below: the extractor scores spans from REALIZABLE signal
     (receiver role + task + message text) ONLY; NEVER the latent act-on label. Its
     measured precision/recall must sit BELOW an oracle that knows the act-on spans.
- STRAWMAN BASELINE: must beat a STRONG/TUNED baseline. -> the generic LLMLingua-style
  compressor (b) is the tuned, real bar (it uses a proper salience/information proxy, and
  we sweep its threshold to MATCH ratio exactly). Truncation (a) is the weak floor.

## L0 MULTI-AGENT MESSAGE-TRAFFIC MODEL (synthetic, latent-need generative)
Agents have ROLES r in {planner, worker, critic, tool-broker}. A message from sender to
receiver is a sequence of SPANS. Each span has:
  - tokens (length ~ LogNormal, integer >=1)
  - a LATENT type drawn from receiver-role-conditioned mixture:
      * ACT-ON span: content the receiver will actually act on (role-relevant action).
        Whether a span is act-on is decided by a LATENT receiver-NEED vector n_r (per role)
        dotted with a hidden span-topic vector t (NOT observed by any compressor). 
        act_on = 1[ sigmoid(<n_r, t> + eps) > 0.5 ]  with eps ~ Normal(0, latent_noise).
      * ROLE-IRRELEVANT VERBOSITY span: reasoning chatter, pleasantries, sender-side
        context the receiver ignores. Fraction = VERB_FRAC (swept).
  - REALIZABLE FEATURES (what compressors CAN see), generated from the latent + noise:
      * salience proxy s (generic info/perplexity proxy): correlated with "is this span
        contentful" but role-AGNOSTIC. High for act-on AND for verbose-but-contentful
        reasoning (so a generic compressor keeps contentful chatter the receiver ignores).
      * role-match feature m_r: a NOISY observation of <n_r, t> (receiver-role+task
        signal). corr controlled by feature_noise -> sets predictor AUC. This is the ONLY
        role signal the role-conditioned extractor reads. It is a DEGRADED view of the
        latent need, never the act_on label.
      * recency/position index (for truncation).

Generative truth (act_on per span) is held out; compressors never see it.

## THE THREE COMPRESSORS (all keep tokens up to a budget = target compression ratio)
(a) TRUNCATION: keep most-recent / shortest-position spans until budget. (weak floor)
(b) GENERIC (LLMLingua-style): rank spans by generic salience proxy s (role-AGNOSTIC,
    no receiver conditioning); keep top-s until budget. THRESHOLD TUNED to match ratio.
    This is the STRONG baseline.
(c) ROLE-CONDITIONED extractor: rank spans by role-match feature m_r (receiver role+task
    conditioned); keep top-m until budget. Reads realizable role signal ONLY.
ORACLE (upper bound, NOT a competitor): rank by true act_on; keep act-on first. Defines
    the predictor gap.

## TWO METRICS
1. TASK-SUCCESS = fraction of act-on tokens (mass) retained after compression, averaged
   over messages (the receiver still has what it needed to act). [primary success proxy]
   Secondary binary: message "succeeds" if >= SUCCESS_THRESH (0.9) of its act-on mass kept.
2. TOKEN-COST = total tokens kept (== compression ratio, MATCHED across compressors).

Pareto = (1 - tokens_kept_frac) tokens-saved  vs  task-success. Compare at MATCHED ratio.

## MATCHED-RATIO CONTROL
For each target ratio in {0.3, 0.5, 0.7} all three compressors keep the SAME total token
budget (within rounding). We compare task-success at identical token cost. THE question:
role-conditioned task-success MINUS generic task-success at matched ratio.

## PREDICTOR AUC + ORACLE GAP (anti-circularity check)
- AUC of role-match feature m_r vs latent act_on label (measured, independent ground truth).
- AUC of generic salience s vs act_on (should be lower / role-agnostic).
- Oracle keeps strictly more act-on mass at every ratio -> role-conditioned must sit BELOW
  oracle (confirms it is NOT reading the label). If role-conditioned ~= oracle -> SUSPECT
  CIRCULARITY -> investigate.

## SWEEPS
- VERB_FRAC (role-irrelevant fraction): {0.2, 0.4, 0.6, 0.8}
- feature_noise -> measured AUC of m_r: low/med/high (predictability of act-on from role)
- target ratio: {0.3, 0.5, 0.7}
- SEEDS: >=5 (use 8). N_messages per seed = 400, spans/msg ~ 8-20.
- Bootstrap 95% CI (2000 resamples) on role-conditioned-MINUS-generic task-success delta at
  matched ratio, per (verb_frac, noise, ratio) cell, pooled across seeds.

## HONEST-NEGATIVE BRANCHES (pre-committed; negatives are WINS)
- If inter-agent messages have LITTLE role-irrelevant verbosity (low VERB_FRAC regime) and
  role-conditioning gives ~no task-success gain over generic at matched ratio (CI ∋ 0)
  -> report NEGATIVE for that regime.
- If the role-conditioned filter does NOT beat generic at matched ratio (delta CI ∋ 0 or <0)
  -> CLAIM (B) DIES / PARTIAL. Role-conditioning is empty.
- If role-conditioned only wins when it effectively NEEDS the oracle (i.e. only at AUC~1.0,
  collapses at realistic AUC) -> report it needs an oracle -> NEGATIVE.
- If role-conditioning TANKS task-success anywhere it claims a win -> NEGATIVE.
- HELD only if: there IS role-irrelevant verbosity (gain rises with VERB_FRAC) AND
  role-conditioned beats generic at matched ratio with CI excluding 0 at realistic
  (sub-oracle) AUC, AND sits below oracle (non-circular).

## DELIVERABLES
- sim_compress.py (stdlib only, serial), results/*.csv (raw per-cell), RESULTS.md.
- ros exp complete --exp EXP-0023 --effect <honest> --summary <...> ; git commit.
