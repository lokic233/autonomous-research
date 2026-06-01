# Prior-Art & Non-Collision — PROJ-0006 (Batch-SD Phase-Composition)
# Scout: researcher-0016-L0-r6 | prompt v001 | 2026-06-01 | web-verified BEFORE interpreting L0
# Anti-hallucination: every "exists"/"collides" cites a retrievable source; >=2 sources for any kill.

## CLAIM-0016 — Agent-Event-Phase Desynchronization Tax in Batch Speculative Decoding

### RE-A7 — PREDECESSOR KILLS (CONFIRMED in this repo's cemetery; cite both)
- **DEAD-0011** (original CLAIM-0013, killing EXP-0046, VERDICT-0053): "Tool-boundary acceptance cliff"
  FALSIFIED at L0 on the SAME top-1-agreement trigram proxy, both corpora. Real signal = a 1-token (d=1)
  collapse (acc 0.025 CC / 0.051 Codex vs interior 0.253/0.271), 1/8 positions Holm-sig (< required 4/8),
  Codex net penalty NEGATIVE. Highest-priority content-type-matched splice null KILLS it (drop reproduced at
  non-boundary positions). => content-type, NOT a position-from-boundary phase discriminator.
- **DEAD-0012** (original CLAIM-0015, killing EXP-0050): "Format-transition speculation cost" FALSIFIED at L0.
  LOAD-BEARING dAUC(format-class - length+entropy JOINT) = **-0.090 CC (CI[-0.400,+0.155]) / -0.322 Codex
  (CI[-0.450,-0.164])**, 95% LB<=0 both (sig-neg Codex). length+entropy JOINT (AUC 0.571/0.897) BEATS
  format-class (0.480/0.575). The standalone single-sequence agent-phase-over-{running-mean+entropy+position}
  acceptance DISCRIMINATOR is DEAD (twice).

**SCOPE STATEMENT (mandatory):** PROJ-0006 / CLAIM-0016 novelty is **CROSS-SEQUENCE BATCH-COMPOSITION**
(leg a: ragged min-bound tax; leg c: phase-aligned composition recovers it), NOT the dead single-sequence
standalone dAUC discriminator. The phase predictor here is the **batch-GROUPING MECHANISM ONLY** (it forms
groups; it is never scored as a standalone AUC/dAUC). EXP-0052 does NOT resurrect DEAD-0011/0012.

### EXTERNAL PRIOR ART (web-verified 2026-06-01; arXiv ids body-checked)
| ref | id (VERIFIED) | venue | core mechanism | lever | difference from CLAIM-0016 | collision |
|---|---|---|---|---|---|---|
| TETRIS | **2502.15197** | ACL 2025 (acl-long.1598) | "actively selects the most promising draft TOKENS (for every request in a batch) to be accepted when verified in parallel" | in-batch token SELECTION | TETRIS prunes WHICH TOKENS to verify GIVEN a batch; we decide WHICH SESSIONS share a batch (membership). Orthogonal levers. | LOW-MED |
| Batch SD Done Right | **2510.22876** | arXiv 2025 | EqSpec: correctness invariants (rectangular alignment, position-ID contiguity, KV-shift) for ragged accepted lengths; **EXSpec: cross-batch scheduling that "dynamically groups same-length sequences"** | correctness + (EXSpec) length-grouping composition | EXSpec groups by CURRENT TOKEN LENGTH to kill re-alignment overhead (a correctness-derived perf opt); we group by PREDICTED ACCEPTANCE PHASE to raise the min-bound accepted-length (goodput). Different key + objective — BUT the composition/grouping lever is PARTIALLY OCCUPIED here. | **MEDIUM (closest)** |
| Semi-Clairvoyant (LAPS-SD) | **2505.17074** | IJCAI 2025 | "adaptively scheduling requests according to their features during decoding"; multi priority queues + preemption keyed on acceptance-rate stability; minimizes avg latency (~39% cut) | request ORDERING/preemption (latency) | Orders/prioritizes requests by dynamic acceptance features (JCT-style); does NOT compose batches by agent-event phase for min-bound goodput. Adjacent: acceptance-aware scheduling lever is occupied. | MEDIUM |
| ECHO | **2604.09603** | arXiv (2026-04; FUTURE-DATE vs Jan-2026 cutoff — flagged) | "sparse confidence gating to manage the batch as a unified super-tree, elastically pivoting budget between depth and width"; budgeted scheduling | per-batch tree depth/width budget gating | Reallocates a shared speculation budget over the batch tree; not membership composition by phase. | LOW |

### COLLISION VERDICT
- **No prior work does PHASE-ALIGNED batch COMPOSITION for SD** (the specific charter delta). NOT FOUND as an
  exact collision => the precise lever is novel-in-naming.
- **HOWEVER the composition/grouping lever is NOT fully unoccupied:** Batch-SD-Done-Right/EXSpec already
  "dynamically groups same-length sequences" (grouping by current length) and Semi-Clairvoyant/LAPS-SD already
  schedules by dynamic acceptance features. So the *generic* "group similar-acceptance/length sequences to
  reduce ragged waste" idea is PARTIALLY PRIOR-OCCUPIED. The only clearly-unclaimed sub-lever is using
  AGENT-EVENT PHASE specifically as the grouping key — which is exactly what EXP-0052 was built to test.
- **Sources:** arXiv abstracts (2502.15197, 2510.22876 HTML, 2505.17074, 2604.09603) + secondary
  (aclanthology acl-long.1598, ijcai.org/proceedings/2025, huggingface/papers, databubble) — >=2 per claim.
- **Freshness:** verified 2026-06-01 (fast-moving SD/serving topic; re-verify before any promotion/L1).
- **PROMOTION DEBT (owed before any candidate->paper):** body-verify TETRIS full PDF mechanism + confirm
  ECHO (future-date single-primary-source) once cutoff passes; deeper EXSpec-vs-phase composition diff.
