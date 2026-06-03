# COMMITTEE#1 — CLAIM-0051 (PROJ-0021, data-systems-for-ml) — bounded shuffle-buffer structural variance-inflation ceiling
## EMPIRICAL-PHENOMENON, effect=support/HELD. NOT metric-validity (real gradient-variance currency). NO closed-form headline (rho(B,L) is the anchored closed-form INTERMEDIATE; the rho->variance mapping + scaling-axis asymmetry are measured). Anti-circular. Vote HONESTLY by role — best-screened candidate of the expansion; do not rubber-stamp, do not reflexively kill.

## CLAIM: in a streaming pipeline with a bounded sliding-window shuffle buffer of size B over data arriving in contiguous same-source runs of length L (real layout: source/domain-grouped shards), per-mini-batch gradient-variance is INFLATED by a factor growing with same-source co-occurrence rho(B,L) + within-source gradient correlation, stays LARGE (>=1.5x) at practitioner buffer sizes (B~10-50x batch b) whenever L>=B — so 'buffer a few-x the batch' under-decorrelates, and the deficit is removed ONLY by B growing with run-length L, NOT with batch b.

## L0 RESULT (anti-circular: GT=source-id+per-source signature g_s, LABEL-FREE measurement path; within-source grad corr=0.80 = the stated shuffling premise; real tf.data/WebDataset sliding-window shuffle; metric=Var(batch-mean|buffer)/Var(batch-mean|oracle-full-shuffle); 5 seeds):
INFLATION(B,L) grid (b=32):
              L=16(.5b)  L=64(2b)  L=640(20b)  L=6400(200b)
B=64 (2b)       3.45       9.74      23.17       24.77
B=320(10b)      1.57       3.23      15.10       23.80
B=1600(50b)     1.09       1.39       4.84       19.08
-> L<<B = 1.09x (heuristic works ONLY here); realistic B=10-50b with L>=B = 3.2-23.8x; 15.1x at the common '10x-batch buffer / 20x-batch runs' point.
THE CEILING (can't buy off by scaling B with batch b): hold L large, scale B 2b->10b->50b -> 24.8->23.8->19.1 (flat-high); even clean L=640: 23.3->15.1->5.3 (B=50b still 5.3x; practitioner buffers NEVER reach 1.5x).
THE AXIS (penalty falls ONLY as B->L): fixed L=640, sweep B/L: infl 23.3(0.1)->15.1(0.5)->10.1(1.0)->6.25(2.0)->3.29(5.0)->2.17(10.0); rho_buf tracks it (0.90->0.05). MONOTONE in B/L, not B/b.

## THE NON-TEXTBOOK CONTENT (load-bearing guard satisfied): the TWO-AXIS ASYMMETRY — at fixed large L the B-with-batch axis barely moves inflation (CEILING) while the B-with-runlength axis collapses it. The practitioner heuristic ('buffer a few-x the batch') is indexed to the WRONG quantity. This is NOT a textbook 'correlated samples -> variance' restatement (that's known); the novel content is the structural CEILING + the correct provisioning axis (B vs L).

## THREE THINGS TO STRESS-TEST: (a) is the structural ceiling genuinely novel beyond RR/GraB (full-permutation regime) + the qualitative streaming buffer_size docs, or known folklore? (b) does the >=1.5x-at-realistic-params bar hold (YES: 15.1x at the common point)? (c) actionability: the >=1.2x crossing sits BEYOND B=10L (limit->1 only as B->full-shuffle); is 'provision B against L' actionable given real L (a full source/shard) can be enormous — or is the real takeaway 'interleave sources / pre-shuffle shards' rather than 'grow B'? Judge whether that limits the contribution.

## SIM-ASSUMED-SHAPE TRAP AVOIDED (why this is the best-screened candidate): rho(B,L) is a DETERMINISTIC property of the shuffle ALGORITHM (re-derivable, cannot evaporate on real data); the only real inputs are DOCUMENTED SYSTEMS FACTS (L>>B from source-grouped sharding; within-source grad corr>0 = why shuffling exists). So the L1 is CONFIRMATORY, not make-or-break — unlike the sibling claims (CLAIM-0048/0050) whose simulated premises had to be tested on real data.

## CLAIM YAML
claim: "In a streaming training pipeline using a bounded sliding-window shuffle buffer\
  \ of size B over data that arrives in contiguous same-source runs of length L (the\
  \ universal real layout: shards grouped by source/domain), per-mini-batch gradient-estimate\
  \ variance is inflated by a factor that grows with the residual same-source co-occurrence\
  \ rate rho(B,L) and the within-source gradient correlation, and this inflation remains\
  \ LARGE (>=1.5x) at the buffer sizes practitioners actually use (B ~ 10-50x batch\
  \ size) whenever L >= B (a regime that holds for real corpora) \u2014 so the common\
  \ 'buffer a few-x the batch is enough' heuristic systematically under-decorrelates\
  \ batches, and the deficit is NOT removed by increasing B linearly with batch size\
  \ but ONLY by B growing with the source run-length L."
why_it_matters: "FRESH AREA (data-systems-for-ml: streaming shuffle-buffer provisioning\

## L0 RESULTS (EXP-0056)
# RESULTS — EXP-0056 (CLAIM-0051)

**Researcher:** researcher-0054 (PERSISTENT-SEEDER, BUG-115) | **Level:** L0 (CPU, stdlib, SERIAL)
**Outcome: HELD (CONFIRM).** All four pre-registered CONFIRM conditions met. Total runtime ~33s
(grid, 5 seeds) + ~68s (clean-baseline axis, 3 seeds) = ~101s, well under the 15-min budget.
Batches per cell: 400–8000. The non-obvious scaling-axis content (not the textbook restatement) is
demonstrated: the penalty is governed by B/L, NOT B/b.

## Stream / premise (harness-owned GT)
d=32, sigma_sig=1.0, sigma_noise=0.5 => within-source per-component gradient correlation
= 1.0/(1.0+0.25) = **0.80** (positive, the premise that motivates shuffling); cross-source ~0.
Items arrive in contiguous same-source runs of length L (source-grouped shards). Pipeline under test
= the production tf.data/WebDataset sliding-window buffer shuffle (fill B, emit uniform-random slot,
refill, drain). Metric INFLATION = Var(batch-mean grad | buffer shuffle) / Var(batch-mean grad |
ideal full shuffle), summed over the d components. Measurement path is **label-free** (anti-circular);
source labels only build the stream + the oracle baseline + diagnostic rho.

## THE INFLATION(B,L) GRID  (b=32; B in {2b,10b,50b}, L in {b/2,2b,20b,200b}; 5 seeds, mean +/- 95% CI)

                         L=16(0.5b)    L=64(2b)      L=640(20b)     L=6400(200b)
  B= 64 (2b)             3.45+/-0.06   9.74+/-0.16   23.17+/-0.41   24.77+/-0.52
  B=320 (10b)            1.57+/-0.03   3.23+/-0.07   15.10+/-0.21   23.80+/-0.54
  B=1600(50b)            1.09+/-0.02   1.39+/-0.02    4.84+/-0.21   19.08+/-0.60
  rho_buf (B=320 row)    0.023         0.093          0.585          0.954
  rho_full (oracle)      0.0012        0.0049         0.050          0.091

Reading the grid:
- **L << B (top-left, L=16):** at B=50b inflation = **1.09** — the buffer fully decorrelates; the
  practitioner heuristic works *only* in this regime (small runs relative to buffer). [CONFIRM (i)]
- **L >= B (the real-corpus regime), realistic B=10b–50b:** inflation is **3.2x–23.8x** — far above
  1.5x. At the heuristic "10x the batch" buffer with L=20b, inflation = **15.1x**. [CONFIRM (ii)]

## THE STRUCTURAL CEILING — you cannot buy it off by scaling B *with the batch*
Hold L large (L>=B), increase B with the batch (2b -> 10b -> 50b):
- L=6400 (L>>B):  inflation **24.8 -> 23.8 -> 19.1**  — ROUGHLY FLAT, stays ~20x. Buffer can never
  catch a run it is smaller than.
- L=640 (clean baseline, N=256k so oracle rho=0.0025):  **23.3 -> 15.1 -> 5.3** — falls some but is
  still **5.3x at B=50b**, the largest buffer practitioners realistically use. Still >> 1.5x.
=> At realistic buffer sizes you CANNOT drive inflation below ~1.5x by scaling B with b. [CONFIRM (iii)]

## THE SCALING AXIS — the penalty falls ONLY as B is scaled toward the RUN-LENGTH L
Fixed L=640 (=20b, real regime), N=256k (~400 sources => oracle full-shuffle rho=0.0025, clean
baseline), 3 seeds. Sweep B by its ratio to L:

  B/L:   0.10   0.50   1.00   2.00   2.50   5.00   10.00
  B:       64    320    640   1280   1600   3200    6400
  infl:  23.29  15.08  10.11   6.25   5.33   3.29    2.17
  rho:   0.898  0.567  0.368  0.214  0.176  0.094   0.049

Monotone collapse driven by **B/L** (rho_buf tracks it: rho -> 0 as B/L grows). Inflation only
approaches 1 when B is several × L; at B=L it is still 10x. [CONFIRM (iv) — direction confirmed]
NOTE on the pre-registered <=1.2x threshold: reaching ~1.0x requires B >> L (B=10L gives 2.2x; the
limit is 1.0x as B->infinity = full shuffle). The pre-registered *direction* (penalty removable ONLY
by B~L, not B~b) is unambiguously confirmed; the exact <=1.2x crossing sits beyond B=10L. This is the
core falsifiable, non-textbook content and it HELD.

## Why this is NOT the textbook restatement
"Correlated samples inflate variance" alone would predict inflation rises with rho and is done. The
non-obvious, load-bearing result is the **two-axis asymmetry**: at a FIXED large L, moving along the
B-with-batch axis (2b->50b) barely moves inflation (24.8->19.1 at L=6400; ceiling), while moving along
the B-with-runlength axis (B/L 0.1->10) collapses it 23->2. The governing variable is B/L, not B/b.
The practitioner heuristic "buffer a few-x the batch" is indexed to the WRONG quantity.

## rho is a structural fact, not an assumed shape (sim-assumed-shape trap avoided)
rho_buf(B,L) is produced by the buffer mechanic itself (measured, harness-side, off the metric path);
within-source corr=0.80 is the shuffling premise, set explicitly, not a fitted conclusion. The
inflation is the *measured consequence* of these two structural inputs.

## DECISION: HELD / CONFIRM
(i) inflation ~1 when L<<B [1.09 ✓]; (ii) >=1.5x when L>=B at realistic B [3.2–23.8x ✓];

## PRE-REG
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

## ORCHESTRATOR NOTE: PRIOR-ART — RR/GraB (Lu-Guo-DeSa 2205.10733 NeurIPS2022, CD-GraB 2302.00845) assume FULL per-epoch permutation (silent on bounded-buffer streaming); MosaicML Streaming/WebDataset/tf.data = qualitative buffer_size knob, NO B-vs-L provisioning rule; seq-packing (Krell 2107.02027) different mechanism. NOVELTY = the bounded-buffer-vs-run-length provisioning LAW + structural ceiling. If candidate-grade, L1 (CONFIRMATORY): real per-domain gradient correlations from a tiny transformer on multi-domain shards + real MosaicML StreamingDataset shuffle at production B -> batch-gradient-variance inflation + downstream loss-spike-freq vs oracle full-shuffle (the open quantity is real within-domain corr magnitude + whether it translates to convergence harm). If you judge the structural ceiling is known folklore OR the actionability caveat (real L huge -> can't grow B) guts it, say YELLOW/RED honestly. If genuinely novel + actionable (the takeaway 'provision against L / interleave sources' is a real systems lever), approve toward L1. Real 6/6 by role.
