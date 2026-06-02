# COMMITTEE#1 REVIEW PACKET — CLAIM-0005 (PROJ-0004), evidence EXP-0006 (L0)

## PASS: committee#1 (post-L0, pre-GPU). HONEST PARTIAL/leans-negative (effect=weaken). The baseline is the BEST-TUNED fixed draft window (the key control) — adaptive is never worse but the realistic-regime win is small. Do NOT inflate; do NOT auto-red an honest negative. If candidate-grade for a real-trace/GPU pass, state SPECIFIC required_evidence (researcher: the result hinges on real per-region acceptance p_constrained/p_prose AND the real emitted-token constrained fraction f). novelty_killer: live >=2-source prior-art sweep OWED (no egress at L0) — STRONG overlap risk with entropy/confidence-adaptive speculative decoding (EAGLE/EAGLE-2, Medusa, SpecInfer, 2024 confidence-adaptive draft-length works). The residual novelty is narrowly the GRAMMAR-REGION label as the adaptation signal on agentic traffic — and this result undercuts even that.

## THE CLAIM (CLAIM-0005)
claim: On agentic/tool-calling traffic, an adaptive speculative-decoding policy that
  lengthens the draft window inside constrained-grammar regions (tool-call/JSON spans,
  where next-token entropy collapses and draft acceptance is structurally higher)
  and shortens it in free prose achieves strictly higher net tokens/sec than a fixed-length
  speculator at matched draft model, because acceptance rate is region-dependent and
  a fixed window under-drafts in constrained regions and over-drafts in prose.
why_it_matters: 'Spec-decode acceptance is region-dependent: constrained grammar collapses

## L0 EVIDENCE — EXP-0006 RESULTS (effect: weaken; PARTIAL leans-negative)
# RESULTS — EXP-0006 (CLAIM-0005), L0 CPU-only analytic + MC

**Claim:** A region-adaptive speculative-decoding draft window (long k in constrained
tool-call/JSON spans, short k in prose) beats a fixed-length speculator at matched draft
model on agentic traffic, because acceptance is region-dependent.

**VERDICT: PARTIAL (leans NEGATIVE at realistic operating points).**

The mechanism is real and directionally confirmed, but once the fixed window is *tuned per
workload* (the honest baseline), it captures almost all of the available gain at realistic
agentic constrained-fractions. Adaptive only wins meaningfully when constrained spans are a
large fraction of emitted tokens AND the acceptance gap is large.

## Headline numbers (adaptive vs BEST-TUNED-fixed, 288-point grid)
| Metric | Value |
|---|---|
| Median gain across full grid | **+2.52%** |
| Median gain, realistic f ≤ 0.35 | **+1.56%** |
| Median gain, realistic agentic cell (f∈{0.1,0.2}, gap≤0.30) | **+1.33%** (max +3.98%) |
| Median gain, low f∈{0.1,0.2} (all gaps) | +1.84% |
| Max gain (extreme: f=0.60, gap=0.42, r=0.05) | **+18.7%** |
| Min gain | +0.11% |
| Fraction of grid with gain ≥ 5% | 29.9% |
| Fraction of *realistic* grid (f≤0.35) with gain ≥ 5% | **14.1%** |

Adaptive is **never worse** than best-fixed (gain ≥ 0 everywhere — expected, since adaptive's
per-region optima dominate any single shared k), so this is a strict-but-often-tiny win.

## Win-region map (the committee's crux: where does adaptive actually pay?)
Median adaptive gain rises monotonically with both the constrained fraction f and the
acceptance gap (p_constrained − p_prose):

- by f:   0.05→**0.7%**, 0.10→1.3%, 0.20→2.5%, 0.35→4.3%, 0.50→5.8%, 0.60→**6.3%**
- by gap: 0.10→**0.8%**, 0.20→1.4%, 0.30→2.7%, 0.42→**7.5%**
- by cost ratio r: weakly decreasing (r=0.05→3.0%, r=0.35→2.0%) — cheaper drafts help adaptive
  slightly more (longer constrained windows stay net-positive).

**Pre-registered honest-negative trigger FIRED:** median realistic-cell gain (1.33%) < the
3% threshold, and the f∈{0.1,0.2} median (1.84%) < the 5% threshold. The claim's strong form
("strictly higher net tok/s" implying a *useful* win on agentic traffic) does NOT hold at
realistic operating points; it holds only in a high-f / high-gap corner.

## Why the tuned fixed window is so strong
The optimal fixed k is small and region-blended: across the grid the best fixed k is almost
always 2–7 (mode k=2). A single small k is already near-optimal for prose (where p is low and
long drafts waste compute) and only mildly suboptimal in constrained spans. Because realistic
traces are prose-dominated (small f), the trace-level throughput is governed by the prose
region, where adaptive and best-fixed pick nearly the same k. Adaptive's big constrained-k
(e.g. k_c=29 at p=0.97) only moves the needle when constrained tokens are a large share.

## Validation
- Monte-Carlo cross-check (5 seeds × 200k tokens at 4 representative points) matches the
  closed-form E[a]/tps to **rel err < 0.06%** at every point (all pass <2% gate). The analytic
  model is sound.

## Verdict rationale
- HELD would require ≥~5% median at realistic f — observed ~1.3–1.8%. Not met.
- NEGATIVE would require the gain to vanish — it does not; there is a genuine, monotone,
  large-corner win (up to ~19%) at high constrained fraction + large gap.
- → **PARTIAL**: real mechanism, win concentrated in a high-f/high-gap sub-region; tuned
  fixed window captures essentially all of the gain on prose-dominated agentic traffic.

## What a GPU pass should measure (to move PARTIAL→HELD or →NEGATIVE)
1. **Real per-region draft acceptance** on actual agent traces with a real draft+target pair
   (e.g. a 1–7B draft vs a 70B target). The whole result hinges on (p_constrained, p_prose, f).
   Our sim swept plausible ranges; only measurement settles which corner real traffic sits in.
2. **The real constrained-fraction f of emitted tokens** on production agentic/tool-calling
   traces (not prompts — *emitted* tokens). If f is genuinely ≥0.35 (heavy JSON/tool-arg
   output), adaptive could reach the 5–18% regime and flip to HELD.
3. **Within-region acceptance autocorrelation** — we assumed i.i.d. Bernoulli per region; real
   grammar-constrained spans may have even higher / bursty acceptance, which would *favor*
   adaptive (longer safe windows). Worth measuring.
4. **Wall-clock net tok/s** including draft launch/verify overheads and KV management, not just
   the analytic cost-ratio proxy.

## Prior-art caveat (no egress — owed at committee)
No literature search performed (sandbox has no network). Likely closely related and MUST be
swept before any novelty claim: **EAGLE / EAGLE-2** (dynamic/confidence-driven draft trees),
**Medusa** (multi-head speculative heads), **SpecInfer** (tree-based speculative verification),
and explicitly **entropy/region-adaptive or confidence-adaptive speculative decoding** (several
2024 works adapt draft length to model confidence — which would subsume the "lengthen in
low-entropy regions" idea). The novelty here, if any, is narrowly the *grammar-region*
labeling as the adaptation signal on *agentic/tool-call* traffic — and even that is undercut
by this result: tuning a single fixed k already captures most of the gain at realistic f.

## Artifacts
- PRE_REGISTRATION.md (committed BEFORE runs, commit a1bb48f)
- scripts/specdec_sim.py (stdlib, deterministic grid + seeded MC)
- results/sweep.csv (288 grid points), results/summary.json
- logs/run.log

## PRE-REGISTRATION (committed PRE-run, git a1bb48f)
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

## ORCHESTRATOR NOTES
- The honest control: baseline = BEST-TUNED fixed k (swept k 1..32, per-workload optimum), NOT a strawman fixed window. Adaptive median gain only +1.33% in the realistic agentic cell; +18.7% only at an extreme corner (f=0.60, gap=0.42). Pre-registered honest-negative trigger fired.
- MC validates closed-form to <0.06% rel err (288 pts).
- The deciding real-world unknowns: real p_constrained/p_prose on agent traces with a real draft+target pair, and the real EMITTED-token constrained fraction f (if f>=0.35 in reality it could flip toward HELD).
- theory_skeptic: is region-adaptive draft length anything beyond known entropy/confidence-adaptive spec-decode? The grammar-region label vs an entropy threshold is the only candidate delta — and a confidence-adaptive speculator would capture most of this for free.
