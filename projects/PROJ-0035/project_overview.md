# PROJ-0035 — Training-efficiency x Data/sharding CROSS-AREA: shard-cardinality silently sets the achievable per-batch source-balance floor of a fixed streaming shuffle buffer (NEW NON-OBVIOUS COUPLING)

8th cross-area coupling claim, FIRST-GREEN (CLAIM-0059) shape, the FIRST one deliberately screened to clear the
SHARPENED incremental-composition ceiling (the test the committee articulated when it yellowed CLAIM-0064): a coupling
GREENS only if NEITHER endpoint, from its OWN side, predicts the composed outcome.

## THE SEAM (two independently-owned subsystems)
- A = DATASET PACKAGER (data/curation team): how the corpus is sharded on disk. A low-volume source is often written
  into FEW shards (sometimes 1) -- shard count chosen for file-size/upload convenience. HF Hub convention; load_dataset
  (streaming=True) reads shards in listed order; docs recommend n_shards % world_size == 0 for DIVISIBILITY only --
  nothing about shuffle quality.
- B = STREAMING TRAINER (training/infra team): interleave_datasets(probabilities=p) then .shuffle(seed, buffer_size=N).
  IterableDataset.shuffle fills a buffer of buffer_size by pulling SEQUENTIALLY from the upstream stream, samples
  randomly from the buffer, refills from the head; reshuffles shard ORDER but within a shard records emit CONTIGUOUSLY.
- DIVERGENCE: A picks shard count for storage ergonomics; B picks buffer_size for RAM. Independently defaulted.

## PRIMARY THESIS (public-measurable, decisive L0)
When a rare source occupies very few shards, ALL its examples enter the buffer in one/few contiguous bursts -> for a
large fraction of training the buffer holds ZERO rare-source examples, then a glut -> per-batch realized rare-source
fraction is BIMODAL + time-localized, not Bernoulli(p). Realized early-training batch composition diverges from the
configured p by >20-40pp for the rarest source, as a function of SHARD COUNT (not p or N alone). Configured p correct in
epoch-MEAN, violated at every STEP.

## ★★ WHY IT CLEARS THE INCREMENTAL-COMPOSITION TEST (load-bearing)
A's owner (only A's side): "source X written as 1/few shards" predicts NOTHING about balance -- contiguous storage is the
universal correct default, example COUNT unchanged, "I stored exactly p_X, mix correct." B's owner (only B's side): "I
set p + buffer_size=N" -> "realized mix converges to p, buffer_size only affects local shuffle randomness"; B has NO
visibility into per-source shard count + interleave gives correct mix IN EXPECTATION. The surprise (bimodal rare-source
starvation -> >20-40pp per-step divergence) emerges ONLY from A-shard-granularity x B-buffer-fill-from-stream-head.
NEITHER endpoint predicts it alone. = CLAIM-0059 structure (NFKC vs NFC each correct on its own side; dedup-escape only emergent).

## NULL EXIT / COULD-IT-FAIL (the make-or-break — run FIRST)
If interleaves per-example cycling already spreads a few-shard source finely enough that the buffer never starves
(divergence ~0 independent of shard count) -> FALSIFIED. The decisive control: divergence must SHRINK MONOTONICALLY as
rare-source shard count rises {1,4,16,64} -- the smoking gun that SHARD COUNT (not p/N) is the lever. If HF's
CyclingMultiSourcesExamplesIterable round-robins B's single shard finely enough -> null holds -> claim dies.

## KILLER SCREEN (cleared — see CLAIM-0065)
#1 measured = realized per-batch source fraction vs configured p (direct observable). #2 reservoir-shuffle incumbent
(tf.data buffer), claim is the shard x buffer COMPOSITION not the shuffle. #4 currency = pp of batch composition over
steps (what training teams budget). #5 vanilla HF datasets + Parquet shards (literal default for open multi-source
corpora). #6 mitigation (many shards / per-sample shuffle / Mosaic StreamingDataset) is exactly what's NOT default in HF;
Mosaic engineering AROUND it = evidence the seam is real+unsolved, not prior art. #7 baseline = the users own configured
p intent (strongest). #8 L0 CAN fail (interleave example-cycling may spread the rare source -> null). #9 prod-framework
prior-art current: HF docs document buffer-fill + interleave-probabilities SEPARATELY, none connect shard cardinality ->
realized per-batch mix under a finite buffer. #10 public-measurable (synthetic/public + open lib). #11 version-stable
(reservoir buffer + shard-sequential streaming stable since datasets 1.x).

## HONEST RISK
interleaves per-example cycling may de-correlate a single rare shard MORE than expected -> shard-count lever weakens ->
drops toward null. The L0 control isolates exactly this (the monotonicity-in-shard-count test is decisive). Secondary:
a reviewer says B "should know" buffer_size limits shuffle quality -> defense = the failure is SOURCE-BALANCE/curriculum
(not generic shuffle quality) driven by A's INVISIBLE shard count. Scout-K self-rating GREEN-eligible (conditional on the control).

## POSTURE
EXPAND/LIGHTWEIGHT: ONE sharp claim (CLAIM-0065), normal pipeline. L0 = CPU, the shard-count-monotonicity control FIRST
as the kill-shot. Owner: orchestrator-r8-001.
