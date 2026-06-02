# RESULTS — EXP-0002 (L0): adaptive 3-class KV/prefix retention vs LRU / pin-shared-prefix / naive-2class

- **Claim:** CLAIM-0002 · **Experiment:** EXP-0002 · **Project:** PROJ-0001 · **Researcher:** researcher-0002
- **Level:** L0, CPU-only, stdlib-only, seeded, no GPU, no network. Wall-clock ~4 min.
- **Pre-registration:** committed BEFORE run (git f880159).
- **Artifacts:** `sim.py`, `results/results.csv`, `results/summary.json`, `logs/run.log`, `logs/stdout.log`.

## Setup (frozen in PRE_REGISTRATION)

- Trace: 40 sessions × 8 turns, interleaved arrival, block=16, radix/prefix-hash chaining,
  content-addressed proxy tokens. prefix_len=2048 tok (128 blk/session).
- **Two-typed scratch:** per turn, 8 blk **COMMITTED** (USER+ASSISTANT context, accumulated, re-read
  by ALL later turns → temporal locality) + 8 blk **TRANSIENT** (one-shot TOOL-RESULT payload at
  the tail, dropped after its turn → truly cold, never re-referenced).
- Four policies, capacity matched EXACTLY: **lru**, **pin_shared_prefix** (pin only cross-session
  SHARED prefix blocks; LRU on rest — the KEY ABLATION), **naive2** (pin full hot prefix, evict ALL
  scratch first — the refuted predecessor reference), **adaptive3** (protect SHARED-prefix FLOOR;
  COMMITTED scratch = normal LRU; evict TRANSIENT first).
- Sweeps: cap_frac ∈ {0.25, 0.5, 0.75, 1.0, 1.5} of distinct hot working set;
  shared_prefix_frac ∈ {0.25, 0.5, 0.75, 0.90}. Seeds = {11,23,47,71,97,113} (n=6).
- Stats: paired bootstrap (2000 resamples) on per-session Δhit / Δrecompute, 3-class − LRU and
  3-class − pin. "Win" = 95% CI excludes 0.

## Headline numbers — POOLED over shared_frac & seeds (mean hit-rate; recompute tokens)

| cap_frac | LRU hit | pin hit | naive2 hit | **adaptive3 hit** | LRU recomp | a3 recomp |
|---------:|--------:|--------:|-----------:|------------------:|-----------:|----------:|
| 0.25 | 0.3787 | 0.5036 | 0.5119 | **0.5082** | 547,133 | 433,117 |
| 0.50 | 0.5772 | 0.5772 | 0.5907 | **0.5896** | 372,335 | 361,395 |
| 0.75 | 0.6455 | 0.6455 | 0.6558 | **0.6633** | 312,167 | 296,499 |
| 1.00 | 0.7020 | 0.7020 | 0.7133 | **0.7251** | 262,466 | 242,123 |
| 1.50 | 0.7883 | 0.7883 | 0.8010 | **0.8178** | 186,414 | 160,425 |

### adaptive3 − baseline Δhit, pooled, bootstrap 95% CI (all CIs exclude 0)

| cap | a3 − LRU Δhit [95% CI] | a3 − PIN Δhit [95% CI] | a3 − LRU Δrecomp [CI] | a3 − PIN Δrecomp [CI] |
|----:|------------------------|------------------------|----------------------:|----------------------:|
| 0.25 | +0.1295 [+0.1157, +0.1438] | +0.0046 [+0.0035, +0.0059] | −2,850 [−3,166, −2,548] | −102 [−129, −77] |
| 0.50 | +0.0124 [+0.0106, +0.0144] | +0.0124 [+0.0106, +0.0144] | −274 [−316, −232] | −274 [−316, −232] |
| 0.75 | +0.0178 [+0.0156, +0.0200] | +0.0178 [+0.0156, +0.0200] | −392 [−441, −343] | −392 [−441, −343] |
| 1.00 | +0.0231 [+0.0206, +0.0256] | +0.0231 [+0.0206, +0.0256] | −509 [−563, −454] | −509 [−563, −454] |
| 1.50 | +0.0295 [+0.0269, +0.0321] | +0.0295 [+0.0269, +0.0321] | −650 [−707, −592] | −650 [−707, −592] |

All Δhit are positive with 95% CI excluding 0; all Δrecompute negative with CI excluding 0.
→ **adaptive3 strictly Pareto-dominates BOTH required baselines (LRU and pin-shared-prefix) at
every cap_frac.**

## Committee question 1 — Does 3-class strictly Pareto-dominate BOTH LRU and pin-shared-prefix?

**YES, across the full sweep.** At every cap_frac (pooled) AND at every one of the 20
(cap_frac × shared_prefix_frac) cells, adaptive3 has higher hit-rate and lower recompute than
both LRU and pin-shared-prefix, with paired-bootstrap 95% CIs excluding 0 (per-cell a3−PIN Δhit
ranges +0.0004 … +0.0376, all CI>0). Strict Pareto dominance over the two required baselines holds.

(Caveat vs the *reference* policy naive2 — see Q3.)

## Committee question 2 — Is the 3-class advantage MORE than trivial shared-prefix pinning?

**YES, decisively — in 19 of 20 regimes the pin baseline captures 0% of the gap.** Fraction of the
(a3 − LRU) hit-gap already captured by pin-shared-prefix, per (cap, shared_frac):

| cap \ sf | 0.25 | 0.50 | 0.75 | 0.90 |
|---------:|-----:|-----:|-----:|-----:|
| 0.25 | 0.0% | 0.0% | 0.0% | **99.9%** |
| 0.50 | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.75 | 0.0% | 0.0% | 0.0% | 0.0% |
| 1.00 | 0.0% | 0.0% | 0.0% | 0.0% |
| 1.50 | 0.0% | 0.0% | 0.0% | 0.0% |

In 19/20 cells pin == LRU exactly (LRU already keeps the frequently-reused hot prefix resident
when there is any headroom, so pinning it adds nothing). The 3-class win there comes entirely from
**evicting TRANSIENT tool payloads first while keeping COMMITTED conversation scratch** — i.e. the
tool-boundary/3-class distinction, NOT shared-prefix pinning. The committee's ≥80% "empty-framing"
threshold is NOT met across the sweep.

**The ONE exception:** cap=0.25 + shared_prefix_frac=0.90. There plain LRU thrashes catastrophically
(hit 0.1678) and ANY prefix protection rescues it (pin 0.6672, naive2 0.6729, a3 0.6676). In that
single deep-starvation/high-shared corner the win IS ~trivial shared-prefix pinning (pin captures
99.9% of the gap). This is the lone regime where the committee's objection bites. Even there
a3 still edges pin (+0.0004 Δhit, CI>0), but the marginal value of the 3-class machinery over plain
pinning is negligible in that corner. The pooled "96.4% captured by pin" at cap=0.25 reported in
stdout is an artifact of this one cell dominating the pool — disaggregated, it is isolated.

## Committee question 3 — Does it INVERT (lose) at cap ≥ 1 like naive2 did?

**NO — adaptive3 fixes the inversion.** The refuted naive2 lost to LRU with headroom (EXP-0001:
−1.4..−1.7pp at cap≥1). adaptive3 instead GAINS over LRU at headroom: **+2.3pp (cap=1.0), +3.0pp
(cap=1.5)**, recompute −509 / −650 tokens, CIs excluding 0. adaptive3 also beats naive2 itself at
headroom (a3 − naive2 Δhit: +0.0075 @0.75, +0.0118 @1.0, +0.0168 @1.5). The mechanism worked as
hypothesized: treating COMMITTED scratch as normal LRU (instead of evict-first) preserves the
temporal locality that naive2 threw away, eliminating the headroom inversion.

**Honest blemish (vs the naive2 *reference*, not a required baseline):** under deep starvation,
naive2 slightly out-hits adaptive3 — a3 − naive2 Δhit = −0.0037 @cap0.25, −0.0011 @cap0.5. When the
cache cannot even hold the hot prefixes, aggressively evicting ALL scratch (naive2) frees marginally
more room for prefix than a3's gentler COMMITTED-as-LRU treatment. So adaptive3 is NOT the single
best policy in every regime — naive2 wins the deepest-starvation hit-rate by a hair. But adaptive3
beats both *required* baselines (LRU, pin) everywhere, and dominates naive2 once cap≥0.75.

## Verdict: **PARTIAL (strongly positive, held-leaning)**

Against the pre-registered HELD/NEGATIVE/PARTIAL rule:
- ✅ Strict Pareto dominance over BOTH required baselines (LRU, pin-shared-prefix) at EVERY
  cap_frac and EVERY shared_prefix_frac, all CIs exclude 0.
- ✅ Advantage over pin is NON-trivial (pin captures 0% of the gap in 19/20 regimes; far below the
  80% "empty-framing" line). It does NOT collapse to shared-prefix pinning, except in one extreme
  corner (cap=0.25 ∧ sf=0.90).
- ✅ Does NOT invert at cap≥1 — it strictly improves with headroom, fixing naive2's defect.

Two reasons it is **PARTIAL** rather than clean HELD:
1. In the single deep-starvation/high-shared corner (cap=0.25, sf=0.90), the win reduces to
   ~trivial shared-prefix pinning (pin ≈ a3).
2. adaptive3 does not dominate the *naive2 reference* under starvation (cap≤0.5): naive2 out-hits
   it by ≤0.4pp there. (naive2 is not one of the two required baselines, but the pre-registration
   asked us to check the inversion fix vs naive2, and honesty requires reporting that naive2 is
   marginally better in the deepest-starvation hit-rate.)

Net: the CLAIM-0002 thesis — "a 3-class committed-vs-transient policy with a hot-prefix floor beats
LRU and pin-shared-prefix across the sweep without inverting at headroom, and the win is not trivial
shared-prefix pinning" — is **substantially supported**, with the honest qualifier that under deep
cache starvation (cap=0.25) the distinction degenerates (becomes shared-prefix pinning at sf=0.90)
and aggressive evict-all (naive2) is marginally better. The compelling, robust regime is cap ≥ 0.5
through 1.5×, where the 3-class win is real, monotonically increasing with headroom, and entirely
attributable to the transient-vs-committed distinction (not prefix pinning).

## Candidate-grade for a GPU pass?

**YES — candidate-grade.** The simulation answers all three committee questions with seeded n=6,
paired bootstrap CIs, ablation against the exact "trivial shared-prefix pinning" null, and a clean
disaggregated story. The mechanism (evict transient tool payloads first, keep committed
conversation scratch as LRU, floor the shared prefix) is directly expressible as a retention policy
over vLLM `enable_prefix_caching` block hashes. Recommended GPU validation: real vLLM with
`enable_prefix_caching=True` on **devgpu014 / H100** (NEVER the fragile MI350X devgpu499), measuring
real prefix-cache hit-rate / TTFT / recomputed-prefill-tokens on a two-typed agentic trace, swept
over `--gpu-memory-utilization` (the real-world cap_frac proxy). Expect the L0 effect to be clearest
at moderate-to-high cache headroom; expect the deep-starvation corner to be noisier.

## OWED at committee (no egress at L0)

A live prior-art sweep is still OWED before promotion — this L0 had no network:
- **SGLang / RadixAttention** (radix-tree prefix sharing + LRU eviction — our LRU+radix baseline is
  a fair proxy, but the real comparison must cite their eviction policy).
- **Prompt Cache** (Gim et al., MLSys 2024) — modular/position-independent prompt segment reuse.
- **CachedAttention** (Gao et al., USENIX ATC 2024) — KV reuse across multi-turn conversations
  (directly overlaps the COMMITTED-scratch reuse mechanism — must distinguish our 3-class eviction
  contribution from their reuse contribution).
- **TensorRT-LLM** token-range / block retention priority knobs (the pin/floor mechanism may already
  be partially expressible there — must check novelty of the committed-vs-transient *classification*).
The novelty hinges on the explicit COMMITTED-vs-TRANSIENT (tool-payload) classification driving
eviction priority; the prior-art sweep must confirm none of the above already do this.
