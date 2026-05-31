# Lane-E Gap Analysis — fresh hunt for a NEW open-gap claim adjacent to CLAIM-0006
agent: researcher-0002-laneE | role: researcher | date: 2026-05-31
project: PROJ-0002 | reporting to: orchestrator 22bd6bef-b84b-4827-a371-87443ea8602f
constraint: write-only under PROJ-0002; NO claims/verdicts/map edits; CPU-only; READ-ONLY external systems.
VERDICT: **EARLY-KILL all 3 mandated fresh directions.** Prefix-cache-invalidation neighborhood
adjacent to CLAIM-0006 is **CONFIRMED SATURATED**. No defensible new open gap found. Do NOT seed.

## Mandate (3 fresh directions to test, kill if occupied)
1. INTERACTION between prefix-cache invalidation and speculative decoding.
2. KV-cache invalidation under MULTI-AGENT shared-context (does shared-prefix invalidation compound
   differently than single-agent?).
3. A measurable cache-invalidation property arising ONLY in long-horizon agentic loops (not single-turn RAG).

## Collision check basis
Checked vs the 10 body-verified neighbors (Irminsul, EPIC, CacheBlend, Cache-Craft, MEPIC, KVFlow,
CacheClip, Don't-Break-the-Cache, ContiguousKV, variable-block), the cemetery (PROJ-0001 DEAD-0001..0010;
NOTE: there is NO PROJ-0002 cemetery dir — DEAD-0009/0010 sit under PROJ-0001 but are MAP-0001/PROJ-0002-
adjacent red_zones), MAP-0001 red_zones + open_gaps (registry/academic_map.yaml node MAP-0001), and the
4 laneB early-kills (eviction-economics / cumulative-trajectory / tool-result-dependency / static-policy-regret).

---
## Direction 1 — Speculative decoding × prefix-cache invalidation = KILL (occupied + red-zone twin)
COLLISION = FATAL.
- DEAD-0010 (EXP-0018) already KILLED "idle-window speculative prefill": break-even is the generic
  accounting identity h·f ≥ α/(1+α) (no KV-specific anomaly), and the operating point is OCCUPIED by
  arXiv:2511.20048 (agent idle-gap speculation + overhead model, DIRECT TWIN) + arXiv:2605.06472
  (prediction-based KV prefill). MAP-0001 red_zone explicitly bars revival unless body-distinct from
  those AND beats the break-even identity.
- The narrower "draft-token-rejection invalidates speculatively-prefilled KV" angle is generic
  speculative-decoding bookkeeping (SpecAttn 2602.07223, CARD 2508.04462, SpeCache 2503.16163,
  Pivot-Aware SD 2511.00351 all handle accept/reject KV mgmt). No prefix-INVALIDATION-specific law
  survives that isn't already the DEAD-0010 identity.
KILL. No revival path within constraints.

## Direction 2 — Multi-agent shared-context invalidation compounding = KILL (densely occupied)
COLLISION = FATAL. The multi-agent shared-prefix KV space is one of the most crowded sub-fields in 2026:
- KVFlow (2507.07400, body-verified neighbor #5) — workflow-aware eviction/prefetch on shared agent caches.
- **When KV Cache Reuse Fails in Multi-Agent Systems** (2601.08343, Jan 2026) — DIRECTLY studies when
  shared-context KV reuse FAILS (cross-candidate interaction); the closest "invalidation-failure" neighbor.
- TokenDance (2604.03143, collective KV sharing), KVCOMM (2510.12872, cross-context KV comm, O(M) prefill),
  Tokencake (2510.18586, KV-centric multi-agent serving, cross-agent contention/eviction), RelayCaching
  (2603.13289, decode-KV reuse across agents), LRAgent (2602.01053, multi-LoRA shared-backbone KV),
  QKVShare (2605.03884, quantized cross-agent KV, error propagation across 2-5 hops), Segment-Level KV
  Sharing (ICLR'26). The "one agent's edit to a shared prefix invalidates N agents' caches" fan-out is
  exactly the contention/eviction story Tokencake + KVCOMM + KVFlow already own; the fan-out multiplier
  is a linear bookkeeping factor on CLAIM-0006's per-event R/S, not a new law.
KILL. Occupied from every angle (sharing, compounding, fan-out, contention, failure-modes).

## Direction 3 — Compaction-as-prefix-invalidation (long-horizon-only) = KILL (collapses onto CLAIM-0006)
The ONLY direction with a non-obvious, testable core, so I ran EXP-0028 (CPU analytic, --claim none).
HYPOTHESIS: context COMPACTION (replace long history H at p≈0 by short summary G≪H; sequence SHRINKS) is
structurally unlike CLAIM-0006's tool injection (APPEND, sequence GROWS) → maybe a NEW cost surface
unique to long-horizon loops (single-turn RAG never compacts).
RESULT (EXP-0028, machine-zero error on 80-cell grid):
  - CDC compaction recompute fraction == (G+w)/S' == CLAIM-0006's R/S identity with R := summary size G.
    max_abs_err = 0.0. Compaction is NOT a new cost surface — it is CLAIM-0006's cost-map evaluated at R=G.
  - FULL compaction == CLAIM-0006 FULL evaluated at the front p_c≈0 (diverged-suffix recompute).
    max_abs_err = 0.0. This is the attention-sink/p=0 corner the registry ALREADY carves out (Irminsul caveat).
  - "When to compact" break-even T* = C_recompute/(S−S') is a generic accounting identity, structurally
    identical to DEAD-0010's speculate-or-skip ratio. No KV-specific anomaly.
  - The only genuinely-distinct quantity = net cache-FOOTPRINT savings from shrinking S → that is the
    eviction/Continuum-KV-TTL/memory-pressure neighborhood, KILLED as occupied in laneB Candidate A.
  - Prior art on the decision itself: Acon (2510.00615), Active Context Compression (2601.07190), Focus,
    AgentFold (2510.24699), Neural Paging (2603.02228), MEM1 (2506.15841) — compaction policy is its own
    crowded field; none publish an inj/seq-style cost-map, and our identity collapse shows there's nothing
    new to publish on the recompute axis.
KILL. Files: experiments/2026-05-31/EXP-0028/{impl,experiment_result}/.

---
## Net recommendation to orchestrator
EARLY-KILL the laneE hunt. All 3 mandated fresh directions are either occupied by the 10 neighbors +
the broader 2026 multi-agent/compaction literature, or collapse onto CLAIM-0006's single surviving leg
(the R/S accounting identity) + its already-owned open gates (eval gate-B GPU wall-clock) + its
already-flagged caveats (attention-sink p≈0). The prefix-cache-invalidation neighborhood adjacent to
CLAIM-0006 is **CONFIRMED SATURATED** (this independently corroborates laneB's saturation finding from
3 NEW angles + 1 new analytic kill). Do NOT seed a new claim. No map edit proposed (per constraints).
Keep resources on CLAIM-0006 gate-B (real vLLM+CacheBlend serving cell, the load-bearing GREEN-blocker
per VERDICT-0029/0033 + EXP-0027's "advantage is inj/seq-conditional vs fused PIC" honesty correction).

## Files (all under PROJ-0002 paths)
- prior_art/PROJ-0002/CLAIM-0006/laneE_gap_analysis_2026-05-31.md (this file)
- experiments/2026-05-31/EXP-0028/impl/exp0028_compaction_identity.py
- experiments/2026-05-31/EXP-0028/experiment_result/result.md
- experiments/2026-05-31/EXP-0028/experiment_result/results.json
