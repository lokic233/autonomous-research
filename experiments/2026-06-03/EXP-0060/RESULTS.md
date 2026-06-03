# RESULTS — EXP-0060 (CLAIM-0052) — L1 DENSE-ENCODER (killer #4 resolution)

researcher-0058 | PROJ-0022 | TASK-0050 | L1 GPU H100 devgpu014 | ran 43.5s, 12 seeds/cell
Encoders: BAAI/bge-base-en-v1.5 + intfloat/e5-base-v2 (real dense, GPU) + lexical TF reference.
Registry: realistic NL MCP-style (8 domains grounded in 398 LIVE-harvested real Glama editorial
descriptions); harness-owned coverage knob c; GT harness-held, never embedded into any score.

## OUTCOME: **WEAKEN** — killer #4 has REAL force. A dense stage-1 PARTIALLY RECOVERS the gap
(TOST REJECTS equivalence with lexical), and the editorial coverage gap contributes only ~1-3pp of
the dense routing loss; the dominant loss is generic same-domain confusability (present at c=1.0).
The structural ceiling re-emerges only asymptotically (large S, top-m=1), where it is entangled with
ordinary routing collapse. The L0 lexical strawman OVERSTATED the ceiling. NOT a clean SUPPORT,
NOT a clean KILL.

## The #4 resolution (HEADLINE) — does dense close the coverage gap?
reachable-recall @ COVERAGE-GAP ITEMS, top-m=1 (vs FLAT no-ceiling baseline):
```
 enc        S   c | FLAT  ed_gap ±ci   | lexical ed_gap  (delta dense-lex)
 bge      10 0.5 |1.000  0.673 .026   |  0.236            +0.436
 bge      10 0.7 |1.000  0.576 .042   |  0.208            +0.368
 e5       10 0.5 |0.973  0.663 .021   |  0.236            +0.426
 bge      20 0.5 |0.986  0.210 .020   |  0.101            +0.109
 bge      40 0.5 |0.954  0.064 .010   |  0.039            +0.025
 bge      40 0.9 |0.952  0.023 .017   |  0.023            -0.000
```
- DENSE RECOVERS THE GAP SUBSTANTIALLY AT SMALL S: at S=10, BGE reaches 0.58-0.67 reachable-recall
  at coverage-gap items vs lexical's 0.18-0.24 — semantic neighbors (shared-domain boilerplate)
  DO surface the GT server when the distinctive capability is absent. This is exactly the Xiao2018
  vocab-mismatch recovery the killer #4 predicted, and the L0 lexical arm (~0 recovery by
  construction) could not see it.
- BUT recovery COLLAPSES with registry size: dense gap-recall(m=1) 0.62 (S=10) -> 0.18 (S=20) ->
  0.04 (S=40). At realistic MCP scale the gap is effectively NOT closed.

## TOST equivalence (pre-registered, bound +/-0.05) on paired delta rr_gap(dense)-rr_gap(lexical)
```
  BGE - lexical : mean +0.1728  90%CI [+0.0501, +0.2955]  => NOT EQUIVALENT (dense recovers more)
  e5  - lexical : mean +0.1649  90%CI [+0.0410, +0.2887]  => NOT EQUIVALENT (dense recovers more)
```
The pre-registered "dense doesn't help" null is REJECTED, not merely unfalsified: a dense stage-1
recovers meaningfully more coverage-gap items than the lexical L0 arm. => killer #4 is REAL.

## CONFOUND AUDIT (decisive) — most of the dense routing loss is NOT the coverage gap
Decomposing dense two-stage loss (FLAT - ed_rr, m=1) into the c=1.0 floor (same-domain
confusability, present at FULL coverage) vs coverage-attributable loss:
```
 S   c | FLAT  ed_m1 tot_loss  c1_floor  cov_attributable
10 0.5 |1.000 0.769  0.231     0.214      0.018
20 0.5 |0.986 0.414  0.573     0.540      0.033
40 0.5 |0.954 0.219  0.735     0.719      0.016
40 0.9 |0.952 0.229  0.722     0.719      0.003
```
The editorial coverage gap (the CLAIM's specific mechanism) explains only **0.002-0.033** of dense
reachable-recall loss. The dominant term (0.21 -> 0.72 as S grows) is generic same-domain routing
collapse at top-m=1 — present even at c=1.0 (no coverage gap at all) and LARGELY CLOSED by raising
m (BGE ed_m3 at S=40 recovers to 0.60-0.66 from 0.22 at m1). The claim attributes to "editorial
coverage" a loss that is mostly ordinary top-m routing difficulty.

## Pooled-member-schema (ecological) baseline — no ecological-kill, but no ceiling-rescue either
Pooled-member stage-1 (ReDDE big-doc) gap-recall(m=1): S=10 ~0.78-0.80, S=20 ~0.44, S=40 ~0.24.
Pooling helps but does NOT drive effective coverage -> 1 at scale (would need ~1.0). So the
ecological-kill condition did NOT trigger; but pooling also confirms the residual loss is routing,
not a hard topological wall.

## Coverage effect IS real and present for dense (isolated from domain noise)
delta_cov = rr(covered) - rr(gap) at m=1 is positive everywhere for dense (BGE 0.19-0.41; e5
0.21-0.41) and LARGER than lexical at S>=20. So a coverage gap genuinely does depress per-item
routing — the phenomenon EXISTS. It is just (a) partially recoverable by dense semantics and
(b) a minor contributor to aggregate reachable-recall vs same-domain confusability.

## Mechanism / anti-circular
GT harness-held, never embedded. Of dense editorial two-stage misses, mean 41-42% are coverage-gap
items (vs 33% lexical) — i.e. dense misses are MORE concentrated on gap items than lexical, but a
MAJORITY of dense misses (~58%) are covered items lost to same-domain confusability — the opposite
of the L0 finding (100% of L0 misses were coverage-gap). This is the cleanest single refutation of
the L0's "misses are EXACTLY the coverage gap" with a real encoder.

## Honest disposition
- L0 (lexical, token-bag, token queries): 100% of misses = coverage gap, stronger-stage-1 (lexical)
  doesn't help -> looked like a clean structural ceiling.
- L1 (dense, NL paraphrased queries, real-style descriptions): the lexical arm was a STRAWMAN.
  A dense encoder recovers a large fraction of gap items at small/medium S (TOST rejects
  equivalence), the coverage gap explains only ~1-3pp of aggregate loss, and the residual ceiling
  is dominated by generic same-domain routing collapse closed by raising m. => the claim's
  load-bearing differentiator ("NOT closed by a stronger stage-1 representation") is FALSE at
  realistic scales and only holds asymptotically where it is confounded. **WEAKEN.**

## What a green-track recovery would require (for committee#2)
A registry where (i) the distinctive capability leaves NO semantic trace in the editorial blurb
(genuinely orthogonal capabilities under one server), AND (ii) the c=1.0 same-domain floor is
near-zero (so the measured loss is provably coverage-attributable, not routing), AND (iii) the
dense recovery still vanishes. The current real-grounded registry does not exhibit this cleanly.

## Artifacts (instance: experiments/2026-06-03/EXP-0060/)
- PRE_REGISTRATION.md (committed BEFORE run, commit 9a93d12)
- harness.py (registry + dense/e5/lexical retrievers + eval; GPU-capped, os._exit)
- results/results.json (36 cells x 12 seeds, all metrics + CIs)
- results/tables.txt (Tables A-D + confound audit + TOST + S-scaling)
- results/real_mcp_descs.json (398 LIVE-harvested real Glama MCP editorial descriptions)
- raw on devgpu014: ~/exp0060/
