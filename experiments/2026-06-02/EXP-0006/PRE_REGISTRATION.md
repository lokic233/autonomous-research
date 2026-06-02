# PRE-REGISTRATION — EXP-0006 (L0, CPU-only, analytic + trace-driven sim)

**Claim CLAIM-0005:** On agentic/tool-calling traffic, an adaptive speculative-decoding
policy that lengthens the draft window inside constrained-grammar regions (tool-call/JSON
spans, where next-token entropy collapses and draft acceptance is structurally higher) and
shortens it in free prose achieves strictly higher net tokens/sec than a fixed-length
speculator at matched draft model, because acceptance rate is region-dependent: a fixed
window under-drafts in constrained regions and over-drafts in prose.

**Pre-registered BEFORE any runs.** Honest pipeline: negative/conditional results are WINS.
The KEY CONTROL is the BEST-TUNED fixed window (tuned per workload), not an arbitrary fixed k.

## 1. Speculative-decoding throughput model (standard, block/leftmost-acceptance)
- Draft model proposes k tokens autoregressively; target verifies all k in one parallel
  forward pass + (on the leftmost rejection or full acceptance) emits 1 extra "free" token.
- Per-token acceptance prob p (region-dependent, see §2). Acceptances are i.i.d. Bernoulli(p)
  within a region for the L0 analytic model (standard assumption; matches the geometric
  accepted-length used in the speculative-decoding literature).
- Expected accepted draft tokens out of k:  E[a] = sum_{i=1..k} p^i  (prob first i all accepted).
  (Leftmost-acceptance: token i counts only if tokens 1..i all accepted.)
- Tokens emitted per verification STEP = E[a] + 1  (the +1 = the bonus/target token always
  emitted when k draft tokens are verified, standard in spec-dec).
- COST per verification step (in target-forward-equivalents):
    cost(k) = k * c_draft + c_target
  where c_target = 1 (one target forward over the k+1 positions, parallel) and
  c_draft = r = (draft per-token cost / target per-token cost), the draft/target cost RATIO.
  (Draft runs k sequential steps each costing r; target runs once costing 1.)
- NET throughput proxy (tokens emitted per unit target-equivalent time):
    tps(k, p) = (E[a] + 1) / (k * r + 1)
  This is the standard "expected tokens per spec-dec step / cost per step" speedup proxy.
  Higher = better. We report tps and the speedup vs no-speculation baseline (tps_base = 1/(1)=1
  emitted per target step at cost 1, i.e. 1 token/target-forward).

## 2. Region model (the crux)
- A trace is a token stream where each token is labeled CONSTRAINED (tool-call/JSON span,
  grammar collapses entropy) or PROSE (free natural language).
- Region acceptance: p_constrained (HIGH, swept 0.85..0.97) and p_prose (LOWER, swept 0.55..0.75).
- Constrained fraction f = fraction of emitted tokens that fall in constrained regions
  (swept 0.05..0.6; realistic agent traces: tool args/JSON are a minority but non-trivial).
- Region-level expected tps is computed per region with that region's p, then the trace-level
  net tokens/sec is the token-weighted harmonic-style aggregate:
  to emit a target number of tokens T, time = T_constrained/tps_constrained + T_prose/tps_prose
  (time adds across regions; tokens add). So trace tps = 1 / ( f/tps_eff_constr + (1-f)/tps_eff_prose ),
  where tps_eff_region uses the policy's chosen k for that region and that region's p.
  (Token-weighted harmonic mean of per-region throughputs — correct because throughput=tokens/time
  and total time is additive.)

## 3. Policies
- (a) FIXED window: single k applied in ALL regions. BASELINE = BEST-TUNED fixed: we sweep
  k in 1..K_MAX and pick the k* that MAXIMIZES the trace-level tps for THAT workload
  (this is the honest, strong baseline — a fixed speculator tuned to the workload mix).
- (b) ADAPTIVE: pick k_constrained = argmax_k tps(k, p_constrained) and
  k_prose = argmax_k tps(k, p_prose) independently (each region at its own per-region optimum),
  apply the right k in each region. Trace tps via the §2 aggregate.
- Optimal per-region k is found by exhaustive sweep over k in 1..K_MAX (K_MAX=32). Deterministic.

## 4. Metric & comparison
- PRIMARY: trace-level net tokens/sec proxy (tps). Compare ADAPTIVE vs BEST-TUNED-FIXED.
- gain = tps_adaptive / tps_best_fixed - 1  (relative % win). Report as function of
  f and the gap (p_constrained - p_prose), and the cost ratio r.
- Also report adaptive vs no-spec baseline and best-fixed vs no-spec for context.

## 5. Sweeps (full grid, deterministic — model is analytic so NO stochasticity needed; we
  ALSO run a Monte-Carlo cross-check with >=5 seeds to validate the closed-form E[a]).
- p_constrained in {0.85, 0.90, 0.94, 0.97}
- p_prose in {0.55, 0.65, 0.75}
- f in {0.05, 0.10, 0.20, 0.35, 0.50, 0.60}
- r (c_draft/c_target) in {0.05, 0.10, 0.20, 0.35}  (smaller draft => cheaper draft)
- K_MAX = 32
- Monte-Carlo cross-check: 5 seeds x 200k tokens at a few representative grid points;
  assert simulated tps within ~2% of analytic.

## 6. HONEST-NEGATIVE branch (pre-committed)
Report NEGATIVE or PARTIAL (not "held") if ANY of:
- The MEDIAN adaptive-vs-best-fixed gain across the realistic grid (f<=0.35) is < 3%
  (i.e. a single tuned fixed k already captures nearly all the gain).
- The win only appears at unrealistic constrained fractions (f >= 0.5) or extreme gaps.
- At realistic f (~0.1-0.2) the gain is < ~5%.
VERDICT levels:
- HELD: meaningful gain (>~5% median) across the realistic grid, robust to r.
- PARTIAL: gain real but concentrated in a sub-region (high f and/or high gap), small elsewhere.
- NEGATIVE: tuned fixed window captures essentially all of it at realistic f.
We will report the actual numbers and the win-region map regardless.

## 7. Reproducibility
- Pure stdlib Python3, CPU-only, no network, deterministic grid + seeded MC.
- Script: scripts/specdec_sim.py  -> results/*.csv + results/summary.json
- <= 15 min wall clock.
