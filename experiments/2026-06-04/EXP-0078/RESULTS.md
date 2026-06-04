# RESULTS — EXP-0078 / CLAIM-0065 / PROJ-0035

**Disposition: KILL (claim FALSIFIED).** The pre-registered NULL holds exactly. Honest negative — a WIN.
**Agent:** researcher-0065  **Node:** cli:dengcchi-mac  **Date:** 2026-06-04

---

## ★ HEADLINE (lead with the novelty framing — and the kill)
The claim predicted that a rare source split into FEW shards would enter a fixed
`IterableDataset.shuffle(buffer_size=N)` buffer in contiguous bursts, starving the buffer of the rare
source for long stretches and producing >20–40pp per-step divergence from the configured
`interleave_datasets(probabilities=p)` mix — with divergence shrinking MONOTONICALLY as shard count rises.

**It does not.** On the real `interleave_datasets → .shuffle` path, the realized per-batch rare-source
fraction is **byte-identical across B-shard-counts {1, 4, 16, 64}** and sits **AT the Bernoulli null**
(per-batch std 0.96–1.03× null; ZERO zero-B batches). The lever the claim needed — shard cardinality —
**has no effect whatsoever**, because `interleave_datasets` cycles sources at the EXAMPLE level by
per-example Categorical(p) sampling that is **completely independent of how each source is sharded**.
Shard cardinality never reaches the buffer as a burst. The COULD-IT-FAIL scenario in the pre-registration
is exactly what occurred: **interleave already spreads the rare source finely, regardless of shard count.**

---

## PINNED VERSIONS
- `datasets==4.8.5`
- `pyarrow==24.0.0`
- `numpy==2.4.6`
- Python 3.12.13+meta, isolated venv at `experiments/2026-06-04/EXP-0078/.venv`

## VERIFIED interleave + shuffle COMPOSITION (from installed source)
File: `.venv/lib/python3.12/site-packages/datasets/iterable_dataset.py` (datasets 4.8.5)

`.shuffle(seed, buffer_size=N)` (line 3555) wraps:
```
BufferShuffledExamplesIterable(
    RandomlyCyclingMultiSourcesExamplesIterable.shuffle_data_sources(generator),  # the interleave
    buffer_size=N, generator)
```

1. **`RandomlyCyclingMultiSourcesExamplesIterable._get_indices_iterator`** (line 1133): produces an
   INFINITE stream of source-indices by `rng.choice(num_sources, size=1000, p=probabilities)` — i.e. it
   samples a source index ~Categorical(p) **PER OUTPUT EXAMPLE**. For each chosen index it pulls the NEXT
   example from that source's own sub-iterator.
2. **Each source's sub-iterator** reads its shards **sequentially/concatenated** into ONE logical
   sub-stream. Whether B is 1 shard or 64 shards, B's logical example order is identical
   (B.idx = 0,1,2,…) — sharding is purely a physical file-split, invisible to the cycler.
3. Under `stopping_strategy="all_exhausted"` (line ~830), when B's sub-iterator exhausts it **resets and
   cycles** (`iterators[i] = iter(self.ex_iterables[i])`), so B keeps contributing at ~p until A exhausts.
4. **`BufferShuffledExamplesIterable.__iter__`** (line 1804): a reservoir buffer of size N, filled
   sequentially from the (already-interleaved) upstream, emitting a uniform-random buffer slot and
   refilling from the head.

**KEY CONSEQUENCE:** the per-example Categorical(p) cycling sits UPSTREAM of the buffer and already
de-correlates the rare source's stream position. B arrives at the buffer at ~10% of positions with a
mean inter-arrival gap of ~10 examples — **NOT** in a contiguous burst tied to a shard boundary. The
buffer therefore never starves of B, independent of B's shard count. `.shuffle` does reshuffle SHARD
ORDER, but since the cycler concatenates each source's shards into one logical stream and samples per
example, shard order does not change B's arrival statistics either.

## DIRECT MECHANISM PROBE (raw interleave, pre-shuffle — `verify_order.py`)
First 5000 outputs of `interleave_datasets([A,B], p=[0.9,0.1], seed=0, all_exhausted)`, NO shuffle:

| B-shards | nB in 5000 | B-fraction | mean gap (examples) | max gap | first B.idx seq | B.idx range |
|---------:|-----------:|-----------:|--------------------:|--------:|-----------------|-------------|
| 1        | 487        | 0.097      | 10.28               | 75      | 0,1,2,…,7       | [0, 486]    |
| 64       | 487        | 0.097      | 10.28               | 75      | 0,1,2,…,7       | [0, 486]    |

**Byte-identical.** B's positions, gaps, and idx ordering are the same whether B is 1 shard or 64. This
proves the null at the mechanism level: shard count is invisible to the interleaved stream. Max gap of 75
examples = 0.29 batches of 256 — far too short to ever empty a 256-batch of B, let alone starve a
1000/10000-example buffer.

---

## ★ THE SMOKING-GUN TABLE: divergence vs B-shard-count (does it shrink monotonically? — NO, it's FLAT at the null)

Synthetic corpus: A = 600k examples / 64 shards (90%); B = 66.7k examples / {1,4,16,64} shards (10%).
Path: `load_dataset("parquet", streaming=True)` per source → `interleave_datasets(p=[0.9,0.1], seed=0,
all_exhausted)` → `.shuffle(seed=0, buffer_size=N)`. Batches of 256, first 400 steps (102.4k examples).
**Bernoulli(0.10) null per-batch-fraction SD = 0.01875; expected zero-B batches ≈ 0 (0.9^256 ≈ 2.6e-12).**

| buffer N | B-shards | n_batches | max zero-B run (batches) | frac batches zero-B | mean B-frac | per-batch std | × Bernoulli | sliding-50 [min,max] |
|---------:|---------:|----------:|-------------------------:|--------------------:|------------:|--------------:|------------:|----------------------|
| 1000     | **1**    | 400       | **0**                    | 0.000               | 0.0990      | 0.01940       | **1.03×**   | [0.094, 0.104]       |
| 1000     | 4        | 400       | 0                        | 0.000               | 0.0990      | 0.01940       | 1.03×       | [0.094, 0.104]       |
| 1000     | 16       | 400       | 0                        | 0.000               | 0.0990      | 0.01940       | 1.03×       | [0.094, 0.104]       |
| 1000     | **64**   | 400       | 0                        | 0.000               | 0.0990      | 0.01940       | 1.03×       | [0.094, 0.104]       |
| 10000    | **1**    | 400       | **0**                    | 0.000               | 0.0991      | 0.01801       | **0.96×**   | [0.093, 0.103]       |
| 10000    | 4        | 400       | 0                        | 0.000               | 0.0991      | 0.01801       | 0.96×       | [0.093, 0.103]       |
| 10000    | 16       | 400       | 0                        | 0.000               | 0.0991      | 0.01801       | 0.96×       | [0.093, 0.103]       |
| 10000    | **64**   | 400       | 0                        | 0.000               | 0.0991      | 0.01801       | 0.96×       | [0.093, 0.103]       |

**Divergence as a function of shard count: completely FLAT, and AT the null.** Within each buffer size
the rows are identical to 5 significant figures across {1,4,16,64} shards. There is no divergence to
shrink monotonically — the claim's decisive kill-shot control returns the null.

## THE 64-SHARD CONTROL
B=64 shards (matching A) converges to the Bernoulli null (std 0.96–1.03×, zero-B runs = 0) — as
pre-registered. But so does B=1 shard, **identically**. The control was meant to isolate shard
cardinality as the cause; instead it demonstrates shard cardinality is NOT a cause at all on this path.

---

## DECISION AGAINST PRE-REGISTERED CRITERIA
| Pre-registered IT-MATTERS condition (needed for SUPPORT) | Threshold | Observed | Pass? |
|---|---|---|---|
| 1. B-shards=1, max zero-B run | ≥4 (N=1000) / ≥35 (N=10000) | **0 / 0** | ❌ |
| 2. per-batch B-fraction std at B-shards=1 | ≥3× Bernoulli (≥0.056) | **0.0194 (1.03×) / 0.0180 (0.96×)** | ❌ |
| 3. divergence shrinks monotonically 1→4→16→64 | strictly decreasing | **flat (no divergence)** | ❌ |

**Pre-registered NULL** ("std ≈ Bernoulli ≤2× AND zero-B runs ≤ a few, INDEPENDENT of shard count"):
**HOLDS exactly.** → **FALSIFIED.**

## WHY THE CLAIM WAS WRONG (mechanistic post-mortem)
The claim conflated two distinct streaming primitives:
- **`concatenate_datasets` / a single multi-shard dataset** read in shard order — THERE, a rare source's
  few shards WOULD enter contiguously and a finite buffer COULD starve. (This is the known
  reservoir-shuffle limitation, and it IS shard-sensitive.)
- **`interleave_datasets(probabilities=p)`** — does NOT read sources in shard-concatenated order into the
  buffer. It samples a source per output example (Categorical(p)) and pulls one example from that
  source's logical stream. The per-example cycling is the de-correlation step the claim assumed was
  absent. Shard cardinality is fully absorbed inside each source's sub-iterator and never surfaces as a
  burst in the interleaved output. The hypothesized A(shard-cardinality)×B(buffer-fill) coupling does not
  exist on this path because B's per-example cycling decouples them.

The honest risk flagged in the prereg/project_overview ("interleave's per-example cycling may de-correlate
a single rare shard MORE than expected → drops toward null") is precisely what the data show — to the
point of EXACT null, not merely "toward" it.

## ARTIFACTS
- `PREREG.md` — pre-registered before running (null, threshold, kill-shot control, pinned versions, real path).
- `run_par.py` — parallel runner (real `load_dataset → interleave_datasets → .shuffle` path).
- `verify_order.py` — raw-interleave mechanism probe (the byte-identical B-ordering result).
- `results/summary_table.csv` — the divergence-vs-shard-count table above.
- `results/series_B{1,4,16,64}_N{1000,10000}.csv` — per-batch B-fraction series per config.
- `results/cfg_*.json` — per-config metrics.

## REPRODUCIBILITY
`.venv/bin/python run_par.py <B_shard_count> <buffer_size>` after building data (run_exp.py build step or
existing `data/`). N_STEPS=400, BATCH=256, SEED=0, all deterministic.

## DISPOSITION
**KILL.** Mechanism verified in source AND empirically. The shard-cardinality × buffer-fill coupling that
the claim needed does not exist on the `interleave_datasets → .shuffle` path: per-example Categorical
cycling decouples shard layout from buffer arrival. Honest negative — clean kill, may converge.
