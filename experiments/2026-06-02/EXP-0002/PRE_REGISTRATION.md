# PRE_REGISTRATION — EXP-0002 (L0, CPU-only trace-driven prefix-cache simulation)

- **Claim:** CLAIM-0002
- **Experiment:** EXP-0002
- **Task:** TASK-0002
- **Project:** PROJ-0001
- **Researcher:** researcher-0002
- **Hardware:** CPU-only, stdlib-only, seeded, no GPU, no network.
- **Wall-clock budget:** <= 15 min.
- **Date pre-registered:** 2026-06-02 (committed to git BEFORE any run).

## Background / why this experiment exists

VERDICT-0001 RED'd the naive predecessor CLAIM-0001. EXP-0001 (the predecessor L0) showed a
naive 2-class policy ("pin hot prefix [system + tool-schema], evict ALL scratch first") beats
LRU ONLY under cache starvation (cap_frac < 0.5x of the hot working set), and STRICTLY LOSES
with headroom (cap_frac >= 1x: -1.4..-1.7pp hit-rate, +14.5k..17.7k recomputed tokens). The
reason: conversational scratch has REAL temporal locality (it is re-read by later turns of the
same session), which LRU captures for free but which "evict-scratch-first" throws away.

The committee raised TWO objections to be answered here:
1. The surviving starvation win might be TRIVIAL shared-prefix pinning (just keeping the
   cross-session shared system+tool-schema prefix resident), not anything about tool boundaries
   or scratch classification.
2. Demanded ablations + more seeds (n=3 flagged as fragile).

## Hypothesis (CLAIM-0002, to test)

An adaptive **3-class** KV/prefix retention policy that distinguishes:
- **COMMITTED-conversation scratch** (USER+ASSISTANT text appended to running context, re-read by
  ALL later turns of that session — has temporal locality), from
- **TRANSIENT scratch** (one-shot TOOL-RESULT payload, consumed in its arrival turn, NEVER
  re-referenced — truly cold), and
- protects a **hot-prefix FLOOR** (cross-session shared system + tool-schema prefix),

achieves a **strictly better hit-rate / recompute Pareto frontier** than BOTH
(a) plain LRU AND (b) a pin-shared-prefix-only baseline, across the FULL capacity sweep AND across
shared_prefix_frac in {0.25,0.5,0.75,0.9} — i.e. the win does NOT collapse to trivial shared-prefix
pinning and does NOT invert (lose) with cache headroom (cap_frac >= 1).

## The FOUR policies compared (capacity matched EXACTLY across all four)

(a) **LRU** — plain least-recently-used over all blocks.
(b) **pin-shared-prefix-only** (KEY ABLATION) — pin/protect ONLY the cross-session SHARED
    system+tool-schema prefix blocks (the ones identical across sessions); plain LRU on everything
    else. NO tool-boundary / scratch tagging. If the 3-class policy cannot clearly beat THIS, the
    claim is dead (the framing is "empty" / trivial shared-prefix pinning).
(c) **naive 2-class** (the refuted predecessor) — pin hot prefix (full per-session prefix), evict
    ALL scratch first (committed + transient lumped together). Included as a REFERENCE to show
    whether 3-class fixes its headroom inversion.
(d) **adaptive 3-class** (the claim) — protect a hot-prefix FLOOR; treat COMMITTED scratch as
    LRU-managed NORMAL blocks (do NOT evict-first); evict TRANSIENT scratch FIRST.

Eviction priority for 3-class: TRANSIENT (LRU within) -> COMMITTED+other (LRU within) ->
hot-prefix above the protected floor (LRU within) -> protected floor (only if nothing else left).

## Trace model (two-typed scratch — the whole point)

Reuses/extends EXP-0001 simulator: block=16, radix/prefix-hash chaining, content-addressed proxy
tokens, 40 sessions x 8 turns, interleaved arrival.

Each turn now produces TWO scratch components:
- **COMMITTED scratch** (class `COMMIT`): USER+ASSISTANT text appended to the session's running
  context. It is re-read by ALL later turns of that session (accumulated history -> temporal
  locality). Reused.
- **TRANSIENT scratch** (class `TRANSIENT`): a one-shot TOOL-RESULT payload, present ONLY in the
  turn it arrives, then dropped from the running context. Never re-referenced (truly cold).

Per-turn prompt block order (radix prefix semantics): HOT prefix -> accumulated COMMITTED history
-> this turn's new COMMITTED scratch -> this turn's TRANSIENT tool payload (tail). The TRANSIENT
payload is at the TAIL and is NOT carried into the next turn's prompt.

New parameter: **committed:transient ratio** (committed_blocks : transient_blocks per turn).
Default split of the prior `scratch_len` (256 tok = 16 blocks) into committed/transient. We fix
committed=8 blocks, transient=8 blocks per turn (1:1) as the registered default, and the prior
scratch is thus refactored — NOT changed in total size — so capacities stay comparable.

## Metrics (per policy x cap_frac x shared_prefix_frac x seed)

- **Primary:** prefix-cache HIT RATE (cached_prompt_tokens / total_prompt_tokens), radix semantics
  (a block hits only if resident AND its full prefix chain is resident).
- **Secondary:** RECOMPUTED prompt tokens (total - cached).
- Also recorded: evictions.

## Sweeps (FROZEN)

- **Capacity:** cap_frac in {0.25, 0.50, 0.75, 1.0, 1.5} of the distinct hot-prefix working set.
- **shared_prefix_frac:** {0.25, 0.50, 0.75, 0.90}.
- **Seeds:** {11, 23, 47, 71, 97, 113} (n=6 >= 5, committee flagged n=3 as fragile).

Fixed: n_sessions=40, turns_per_session=8, prefix_len=2048, committed=8 blk/turn,
transient=8 blk/turn.

## Statistics

For (3-class - LRU) and (3-class - pin-shared-prefix-only), at each cap_frac (pooled over
shared_prefix_frac and seeds, AND also reported per shared_prefix_frac): compute a PAIRED
BOOTSTRAP CI (>= 2000 resamples) on per-session Delta-hit and per-session Delta-recompute.
A "win" = 95% CI excludes 0 in the favorable direction. Report mean +/- std AND the bootstrap CI.

## Pre-registered decision rule (HONEST-NEGATIVE branch)

Report the result as one of held / partial / negative per these rules:

- **HELD** iff the 3-class policy STRICTLY Pareto-dominates BOTH LRU and pin-shared-prefix-only
  (higher hit, lower recompute, 95% CI excluding 0) across the FULL cap sweep AND all four
  shared_prefix_frac values, AND it does NOT invert at cap_frac >= 1, AND its advantage over
  pin-shared-prefix-only is a MEANINGFUL fraction of the gap to LRU.
- **NEGATIVE** iff ANY of:
  - 3-class does NOT strictly Pareto-dominate BOTH baselines; OR
  - its advantage over pin-shared-prefix-only is < 20% of the (3-class vs LRU) gap (i.e. >= 80%
    of the win is already captured by pin-shared-prefix-only => it COLLAPSES to trivial
    shared-prefix pinning, framing is empty); OR
  - it INVERTS (loses hit-rate / gains recompute) at any cap_frac >= 1.
- **PARTIAL** = wins in some regimes (e.g. starvation only, or some shared_prefix_frac only) but
  fails one or more HELD conditions without triggering a full negative. Explicitly enumerate which.

A negative result is a WIN — it is reported honestly, not buried.

## Reproducibility

`/usr/bin/python3 sim.py` from the EXP-0002 dir. Stdlib-only, deterministic given seeds.
Outputs: results/results.csv, results/summary.json, logs/run.log.
