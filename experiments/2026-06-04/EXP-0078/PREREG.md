# PRE-REGISTRATION — EXP-0078 / CLAIM-0065 / PROJ-0035

**Agent:** researcher-0065  **Parent:** orchestrator-r8-001  **Date:** 2026-06-04
**Level:** 0 (CPU)  **Node:** cli:dengcchi-mac (Python 3.12.13+meta, isolated venv)

> Committed BEFORE running any measurement. Honest negatives/kills are WINS.

## THE CLAIM (CLAIM-0065)
The data team's choice of HOW MANY SHARDS a rare source is split into silently sets the
minimum batch-level source imbalance achievable by a fixed `IterableDataset.shuffle(buffer_size=N)`.
For realistic configs, the realized early-training per-batch fraction of the rare source diverges
from the configured `interleave_datasets(probabilities=p)` mix by >20-40pp, as a function of
SHARD COUNT (not p or N alone). Mechanism: a rare source in few shards enters the shuffle buffer
in contiguous bursts → buffer holds ZERO rare-source examples for long stretches, then a glut →
bimodal/time-localized per-batch fraction, NOT Bernoulli(p). Configured p is correct in
epoch-MEAN, violated at every STEP.

## ★★ THE KILL-SHOT CONTROL (decisive, run conceptually first)
**Does the divergence SHRINK MONOTONICALLY as the rare source's shard count rises {1,4,16,64}?**
- If `interleave_datasets`'s per-example cycling already spreads a few-shard rare source finely
  enough that the buffer never starves → divergence ≈ 0 INDEPENDENT of shard count → **FALSIFIED**.
- The claim SURVIVES only if divergence is LARGE at B-shards=1 AND shrinks MONOTONICALLY toward
  the Bernoulli null as B-shards→64.

## EXPERIMENT DESIGN
- Two synthetic sources written as local Parquet, then loaded via
  `load_dataset("parquet", data_files=..., split=..., streaming=True)`:
  - **A** (common): 90% of examples, written as **64 shards**.
  - **B** (rare): 10% of examples, written as **{1, 4, 16, 64}** shards (4 configs).
  - Each example has fields: `{source: "A"|"B", idx: int}` so A/B are distinguishable.
  - Total examples sized so each config iterates ~2000 batches of 256 = ~512k consumed.
    A pool ≈ 600k, B pool ≈ 70k (≈10.4% of total) — `stopping_strategy="all_exhausted"`.
- For each B-shard-count config × N ∈ {1000, 10000}:
  - `interleave_datasets([A, B], probabilities=[0.9, 0.1], seed=0, stopping_strategy="all_exhausted")`
  - `.shuffle(seed=0, buffer_size=N)`
  - Iterate, form batches of **256**, over the first **~2000 steps**.
- **REAL PATH ONLY**: must use `interleave_datasets → .shuffle` (the production path).
  Do NOT bypass interleave or hand-construct starvation. Use real streaming Parquet shards.

## METRICS (per B-shard-count × N)
- **(a)** max consecutive batches with ZERO B examples (zero-B-run length).
- **(b)** std-dev of per-batch B-fraction across steps vs Bernoulli(0.1) expectation.
- **(c)** realized vs configured (0.10) B-fraction over a sliding window (e.g. 50 batches).

### Bernoulli null reference (batch=256, p=0.1)
Per-batch count ~ Binomial(256, 0.1). SD of count = sqrt(256·0.1·0.9) = 4.8.
**SD of per-batch fraction = 4.8/256 ≈ 0.01875.** Expected max zero-B run with p=0.1, n=256
per batch: P(0 B in a batch) = 0.9^256 ≈ 2.6e-12 → essentially NEVER a zero-B batch under the
null. So ANY long zero-B run is already off-null.

## ★ PRE-REGISTERED NULL (claim FALSIFIED if this holds)
Realized per-batch B-fraction SD ≈ Bernoulli null (≤2× ⇒ ≤0.0375) AND zero-B runs ≤ a few
batches, **INDEPENDENT of B's shard count** (flat across {1,4,16,64}).

## ★ IT-MATTERS THRESHOLD (claim SUPPORTED only if ALL hold)
1. At B-shards=1: ≥1 contiguous run of **≥(0.9·buffer/256)** all-B-absent batches
   (N=1000 → ≥3.5 → ≥4 batches; N=10000 → ≥35 batches), AND
2. per-batch B-fraction SD **≥3× Bernoulli** (≥0.056), AND
3. divergence **monotonically shrinks** as B-shard count rises 1→4→16→64 (the lever is shard
   count, not p/N).

## CONTROL
B written as **64 shards** (matching A) → expect convergence to the Bernoulli null
(isolates shard cardinality as the cause; rules out buffer_size alone).

## ★ COULD-IT-FAIL (honest)
If HF's `CyclingMultiSourcesExamplesIterable` round-robins B's single shard's examples into the
stream finely enough that the buffer never starves → null holds → **FALSIFIED**. Will report
honestly. No rigging.

## MECHANISM TO VERIFY IN INSTALLED SOURCE (before trusting result)
1. `interleave_datasets(probabilities=p)` → `_interleave_iterable_datasets` →
   `RandomlyCyclingMultiSourcesExamplesIterable`: does it cycle at the EXAMPLE level by sampling
   a source index ~Categorical(p) per output example, pulling the NEXT example from that source's
   own (shard-sequential) sub-iterator?
2. `.shuffle(buffer_size=N)` → `BufferShufflingIterable` / `ShuffledDataSourcesArrowExamplesIterable`:
   does it fill a reservoir buffer of N by pulling SEQUENTIALLY from the upstream (interleaved)
   stream, emit a random buffer slot, and refill from the head?
3. KEY QUESTION: when B occupies 1 shard, B's examples are emitted by interleave only when the
   Categorical picks source B — which is independent of shard count. So WHY would few shards
   starve the buffer? → Because interleave reads each source's shards SEQUENTIALLY; with B in 1
   shard, once B's single shard is exhausted, source B yields StopIteration and (under
   all_exhausted) is dropped/cycled — B's examples are CONCENTRATED in the prefix of the stream
   where B's shard is being consumed, NOT uniformly across the full interleaved stream. With B in
   64 shards, B's shards are interleaved with A's across the whole stream → B examples spread out.
   Document the ACTUAL behavior observed in source + empirically.

## DISPOSITION RULE
- All 3 IT-MATTERS conditions hold → **SUPPORT** → submit to committee (do NOT self-converge).
- Null holds (flat/small divergence across shard counts) → **KILL** → write RESULTS, may converge.
- Partial (divergence present but not monotonic, or fails magnitude) → **WEAKEN**, report honestly.
