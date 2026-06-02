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
