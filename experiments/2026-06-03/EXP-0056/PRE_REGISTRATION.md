# PRE-REGISTRATION — EXP-0056 (CLAIM-0051)

**Researcher:** researcher-0054 (PERSISTENT-SEEDER, BUG-115)
**Project:** PROJ-0021 | **Task:** TASK-0046 | **Claim:** CLAIM-0051
**Level:** L0 (CPU-only, pure-Python/stdlib, SERIAL, <=15 min)
**Committed BEFORE running.** Honest pipeline; negatives are wins.

## THE CLAIM (CLAIM-0051)
In a streaming training pipeline using a bounded sliding-window shuffle buffer of size B over data
arriving in contiguous same-source runs of length L (real layout: source/domain-grouped shards),
per-mini-batch gradient-estimate variance is inflated by a factor growing with the residual
same-source co-occurrence rate rho(B,L) and within-source gradient correlation, and this inflation
stays LARGE (>=1.5x) at the buffer sizes practitioners use (B~10-50x batch b) whenever L>=B — so
"buffer a few-x the batch is enough" under-decorrelates, and the deficit is NOT removed by scaling B
with batch b but ONLY by B growing with run-length L.

## LOAD-BEARING GUARD (must NOT collapse to "correlated samples inflate variance")
The textbook fact is trivial and known. The NON-OBVIOUS falsifiable content I must demonstrate:
  (a) STRUCTURAL CEILING: when L>=B, inflation stays LARGE and roughly FLAT as B scales WITH the
      batch (B: 2b -> 10b -> 50b). Cannot buy off the penalty by the practitioner heuristic.
  (b) THE AXIS: penalty falls toward 1 ONLY when B is scaled toward the RUN-LENGTH L (B=L, B=2L).
If I only show "correlated -> inflated variance" without (a)+(b), the outcome is
TEXTBOOK-RESTATEMENT-ONLY (weaken; don't overclaim).

## STREAM MODEL (harness OWNS ground truth)
- N = 200,000 items. d = 32 (gradient dimension).
- S sources. Each source s drawn once: signature vector g_s in R^d, components ~ N(0, sigma_sig^2),
  sigma_sig = 1.0 (deterministic generative fact, fixed per seed).
- Items arrive in CONTIGUOUS runs of length L: run of source s_0 (length L), then source s_1
  (length L), etc. Consecutive runs use distinct sources.
- Each item's "gradient" vector x_i = g_{src(i)} + eps_i, eps_i ~ N(0, sigma_noise^2 I_d),
  sigma_noise = 0.5. Within-source items share g_s => within-source gradient correlation POSITIVE.
- WITHIN-SOURCE CORRELATION (stated): per-component corr =
  sigma_sig^2 / (sigma_sig^2 + sigma_noise^2) = 1.0/(1.0+0.25) = 0.80. (Cross-source corr ~ 0.)
  This positive within-source correlation is the PREMISE that justifies shuffling.

## PIPELINE UNDER TEST (real tf.data / WebDataset sliding-window shuffle)
maintain buffer (list of capacity B). Fill to capacity B from the stream. To EMIT one item:
pick UNIFORM-RANDOM slot index in [0,B), emit buffer[slot], refill that slot from the stream
(or drain remaining uniformly when stream exhausted). Form consecutive mini-batches of size b from
the emitted order. Exactly the production shuffle-buffer mechanic.

## ANTI-CIRCULAR (no source label on measurement path)
- GT = source id + per-source signature g_s, harness-controlled.
- MEASUREMENT path reads ONLY emitted item gradient vectors x_i, computes batch-mean gradient and its
  variance across batches. NEVER reads source labels.
- Source labels used by harness ONLY to (i) construct the stream, (ii) compute the oracle
  full-shuffle baseline, (iii) report diagnostic rho — NOT on the inflation metric path.

## METRIC: variance-inflation factor
For (B,L): emit stream through buffer shuffle, form consecutive batches size b. Per batch compute
batch-mean gradient m = (1/b) sum x_i (d-vector). Across all batches compute total per-component
variance summed over d: V_buffer = sum_j Var_batches(m_j).
IDEAL full-shuffle baseline: SAME N gradients, full uniform permutation, batches size b, V_full same way.
  INFLATION = V_buffer / V_full.
Full shuffle gives standard ~(per-item var)/b reduction; buffer shuffle retains correlated terms when
same-source items co-occur => less reduction => INFLATION > 1.
Measure across >= hundreds of batches and >= 5 seeds; report mean +/- 95% CI (normal approx, SD across seeds).

## DIAGNOSTIC rho(B,L)
rho = fraction of within-batch unordered item pairs that are same-source on the BUFFER-shuffled emitted
order (diagnostic, harness-side; not on inflation metric path). Full-shuffle rho_full reported too.

## THE SWEEP
b = 32 (fixed). B in {2b,10b,50b} = {64,320,1600}. L in {b/2,2b,20b,200b} = {16,64,640,6400}.
=> 3 x 4 = 12 cells. Report inflation + CI + rho per cell.

## THE SCALING-AXIS TEST (the whole ballgame)
Fix large run-length L_fixed = 6400 (= 200b) so L >> all swept B.
  - B-with-batch axis: B in {64,320,1600} at L=6400 -> inflation stays >=1.5x and roughly FLAT.
  - B-with-runlength axis: ADD B in {L/2,L,2L} = {3200,6400,12800} at L=6400 -> inflation drops
    toward 1 as B -> L and beyond.

## SEEDS
seeds = [0,1,2,3,4]. Each seed redraws signatures, noise, stream source order, buffer-shuffle RNG,
full-shuffle RNG. Deterministic per seed (per-seed random.Random instances).

## DECISION BRANCHES (pre-committed)
- CONFIRM / HELD: (i) inflation ~1 (<=1.15x) when L<<B; (ii) inflation >=1.5x when L>=B at realistic
  B (10b,50b); (iii) CEILING: at L=6400 (L>>B), inflation stays >=1.5x and roughly flat as B goes
  64->320->1600; (iv) AXIS: at L=6400, inflation drops toward ~1 (<=1.2x) as B->L and 2L. ALL FOUR.
- HONEST-NEGATIVE: scaling B 10b->50b already drives inflation <1.1x when L>=B, OR inflation never
  exceeds ~1.1x even at L=200b.
- TEXTBOOK-RESTATEMENT-ONLY: correlated->inflation observed but B-vs-L ceiling/axis does NOT cleanly
  separate (scaling with b ALSO fixes it) -> weaken; report only what was shown.

## PRIOR-ART CAVEAT (honest)
Random-reshuffling/GraB (Lu-Guo-DeSa 2205.10733, CD-GraB 2302.00845) assume a FULL PERMUTATION each
epoch — silent on bounded-buffer streaming. MosaicML Streaming/WebDataset/tf.data expose a qualitative
buffer_size knob with NO B-vs-L rule. Sequence-packing (Krell 2107.02027) is a different mechanism.
NOVELTY = the bounded-buffer-vs-run-length provisioning LAW + the structural ceiling (scale B with L,
not b). Honest if textbook restatement or trivially small.

## ANTI-PATTERN SCREEN
1. Not circular: measurement path label-free. 2. Not closed-form headline: empirical grid. 3. GT
harness-owned. 4. Sim-assumed-shape trap avoided: rho is a STRUCTURAL algorithm fact (buffer mechanic)
and within-source corr>0 is shuffling's PREMISE, not assumed conclusion. 5. Negatives are wins.
6. Load-bearing guard prevents textbook-restatement overclaim.
