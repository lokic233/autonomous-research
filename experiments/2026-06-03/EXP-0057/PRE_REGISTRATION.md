# PRE_REGISTRATION — EXP-0057 (CLAIM-0051, committee#1 follow-up)

**Researcher:** researcher-0055 | **Level:** L1-contested (CPU, stdlib, SERIAL, <=15min)
**Committed BEFORE any run.** Resolves the three VERDICT-0049 blockers against CLAIM-0051,
which HELD at L0 (EXP-0056) but received YELLOW with one UNREBUTTED RED (interleaving).

REUSES the EXP-0056 harness verbatim for the core shuffle + label-free metric:
- same sliding-window buffer shuffle (`buffer_shuffle_order`),
- same per-source gradient signatures g_s + within-source noise (`gen_stream_grads`),
- same INFLATION = Var(batch-mean | buffer) / Var(batch-mean | oracle-full-shuffle) (`batch_mean_var`),
- same anti-circular path: GT = source-id + g_s; measurement reads ONLY gradient vectors,
  labels only build the stream + diagnostic rho.

## BLOCKER 1 (★ the unrebutted RED) — INTERLEAVING
L0 modeled a PURELY SEQUENTIAL single-shard stream. Real pipelines INTERLEAVE C shards
concurrently (tf.data.interleave cycle_length=C, WebDataset multi-shard, MosaicML
num_canonical_nodes), cutting the EFFECTIVE same-source run-length the buffer sees WITHOUT
growing B.

**Model (pre-registered):** generate C independent source-runs concurrently; emit in strict
round-robin across the C active runs (cycle_length=C), one item per cycle step from each.
This interleaved stream is THEN fed into the bounded buffer of size B (unchanged harness).
A new source-run replaces a slot in the round-robin when its run of length L is exhausted.
Within each run, items are same-source contiguous of length L (as L0). C=1 reproduces L0.

**Sweep:** C in {1,2,4,8,16} x representative (B,L) grid:
  - realistic point (B=10b=320, L=20b=640)
  - large-L point (B=10b=320, L=200b=6400)
  - plus (B=2b=64, L=640) and (B=50b=1600, L=6400) for axis coverage.
5 seeds. Measure inflation(B,L,C) + rho_buf.

**L_eff HYPOTHESIS (pre-registered):** interleaving acts purely as a run-length reducer, i.e.
inflation(B,L,C) ~= inflation(B, L_eff = L/C) from the L0 single-stream law. Test by comparing
inflation(B,L,C) against the L0 inflation(B, L/C) curve (interpolated). Report relative error.

## BLOCKER 2 — RHO_WITHIN SENSITIVITY
L0 fixed within-source gradient correlation = 0.80 (sigma_sig=1.0, sigma_noise=0.5).
within-corr = sigma_sig^2 / (sigma_sig^2 + sigma_noise^2). Re-derive sigma_noise to hit
targets rho_within in {0.2, 0.5, 0.8}: sigma_noise = sigma_sig * sqrt((1-r)/r).
  r=0.2 -> sigma_noise=2.0 ; r=0.5 -> 1.0 ; r=0.8 -> 0.5.
VERIFY achieved per-component within-source correlation empirically (harness diagnostic).
Measure inflation at the realistic point (B=320, L=640, C=1) for each rho_within. 5 seeds.

## BLOCKER 3 — PER-SHARD-SHUFFLE BASELINE
L0 used oracle-full-shuffle as denominator (favorable to claim). Add a weaker, more realistic
baseline: per-shard-shuffle = shuffle WITHIN each contiguous same-source run of length L, no
cross-shard mixing (preserves run boundaries / global source ordering, randomizes within run).
Report inflation_vs_pershard = Var(batch-mean | buffer) / Var(batch-mean | per-shard-shuffle)
at the realistic point and across the C sweep. Is buffer-shuffle still WORSE than per-shard?

## DECISION RULES (pre-registered, honest)
Let the realistic point be (B=320, L=640).

- **STRENGTHENED + reframe-to-L_eff (effect=support):** interleaving does NOT fully fix it —
  inflation stays >=1.5x at C=16 when L is large (L/C still >= B), AND >=1.5x SURVIVES at
  rho_within=0.2-0.3, AND buffer is still WORSE than per-shard-shuffle. The B-vs-L_eff
  mechanism survives; interleaving works only by cutting L_eff.

- **REFRAME-to-L_eff (effect=keep-exploring):** a moderate C (4-16) COLLAPSES inflation to
  ~1.x at the realistic point, and inflation(B,L,C) is well-predicted by inflation(B,L/C).
  Then "deficit removed ONLY by B growing with L" is FALSIFIED as stated; correct framing is
  "inflation is governed by effective run-length L_eff = L/C; reduce L_eff via interleaving (C)
  OR B/L scaling OR shard pre-shuffle." Mechanism survives, "grow B" framing wrong.

- **WEAKENED (effect=weaken):** >=1.5x REQUIRES rho_within=0.8 (gone at 0.2-0.5) AND
  interleaving with moderate C fixes it AND buffer is NOT worse than per-shard-shuffle —
  practitioner heuristics + interleaving already handle it.

L_eff law verdict (orthogonal report): inflation(B,L,C) ~= inflation(B,L/C) within ~20% rel
error across the sweep => interleaving is an L-reducer (unified law confirmed).

## BUDGET
CPU-only, stdlib-only, SERIAL. Target < 8 min. Adaptive N from L0 (>=400 batches/cell).
Do NOT self-converge; do NOT touch .converged.
