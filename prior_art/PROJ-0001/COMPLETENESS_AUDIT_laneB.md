# PROJ-0001 Completeness Audit (Rule-3) + Open-Gap Hunt — researcher-0001-laneB

**Date:** 2026-05-31 · **Agent:** researcher-0001-laneB (CPU-only synthesis lane) ·
**Orchestrator session:** 22bd6bef-b84b-4827-a371-87443ea8602f
**Scope:** READ-ONLY audit. No map/claim/verdict edits (out of lane). Findings only.

## TL;DR
PROJ-0001 is **SATURATED**. The negative-result story (HW VMM CoW dominated · ~520K NVIDIA
mapping ceiling = vendor portability cliff · ceiling+CoW+slowdown compound into throughput
collapse · Mapping-Budget Wall · the one real capability delta = attention-visible
write-after-share) is fully told by 5 promoted GREEN claims (CLAIM-0001/0002/0003/0004/0007).
Every adjacent idea I generated maps onto an existing PROMOTED claim or one of the 9 DEAD ideas.
**Recommendation: orchestrator mark PROJ-0001 mature/closed.** No new experiment registered.

## Part 1 — Map / prior-art completeness defects (MAP-0001)

MAP-0001 is an AREA node (GPU KV-cache memory) spanning PROJ-0001 (VMM CoW) AND PROJ-0002
(prefix-cache invalidation / CDC). That sharing is by design, but it introduced these defects:

### D1 — CLAIM-0005 dangling (MINOR, stale linkage)
CLAIM-0005 (PROJ-0001) declares `academic_map_nodes: [MAP-0001]` but is **absent** from
MAP-0001 `associated_claims`. Its content IS represented (red_zone for the k~1.3 crossover
slope + DEAD-0009), so this is a missing ID back-link, not a missing finding.
FIX (orchestrator): add CLAIM-0005 to MAP-0001.associated_claims, OR drop its MAP-0001 tag
since it is now CLOSED (negative result, spawned DEAD-0009).

### D2 — CLAIM-0008 mis-tagged to MAP-0001 (CROSS-PROJECT, not my lane to fix)
CLAIM-0008 (PROJ-0003, recovery competence) declares `academic_map_nodes: [MAP-0001]` but
is semantically a MAP-0002 claim (it appears in MAP-0002 open_gaps, NOT MAP-0001). Looks like
a copy-paste mis-tag. FIX (orchestrator, PROJ-0003 owner): retag CLAIM-0008 -> MAP-0002.

### D3 — Two PROJ-0001 dead ideas not reflected as red_zones (COMPLETENESS GAP)
MAP-0001.associated_dead_ideas lists DEAD-0001..0009, but red_zones only explicitly cover
DEAD-0001, -0002, -0009 (and -0003 via the "HW VMM CoW measure-zero" zone). Missing explicit
red_zone coverage:
  - **DEAD-0004** (super-linear multi-context degradation — retracted measurement artifact).
    Risk: a future agent could re-propose "VMM multi-context degrades super-linearly" without
    seeing it was retracted. Recommend a red_zone: "super-linear multi-ctx degradation = per-worker
    memory artifact, retracted (DEAD-0004); needs clean isolated >linear measurement to revive."
  - **DEAD-0007** (layer-stratified positional KV reusability — 1.5% << 2% kill bar).
    Recommend a red_zone: "layer-stratified positional KV reuse capped at 1.5% real incidence
    (DEAD-0007); revive only if real-trace incidence > 2%."
  - DEAD-0005 (de-chained hash repair = 1.0x) and DEAD-0008 (interior KV-repair not bit-safe)
    and DEAD-0006 (token-prefix predicts KV sharing = RadixAttention) are adjacent to the
    CDC/RadixAttention zones but only IMPLICITLY covered — LOW priority, optional to add.

### D4 — needs_attention.md item #3 is STALE (recommend orchestrator update)
"CLAIM-0005 (injection penalty): sub-quadratic; needs a 3rd independent engine (TensorRT-LLM)
to settle." — OBSOLETE. As of VERDICT-0019 (today) CLAIM-0005 is CLOSED: k is NOT a conserved
exponent (drifts 1.0->2.0 with ctx, accounting-derivable), spawned DEAD-0009. No 3rd engine
needed; the question is settled negative. (related_work.md "Speculative Tool Calls" row is fine.)

### D5 — Freshness OK
MAP-0001 last_updated 2026-05-31T16:48Z (today). prior_art related_work/oss_community current.
The ~520K NVIDIA / AMD-no-wall cross-vendor result (511ce2e2__CROSSVENDOR_RESULT.md) is the
load-bearing evidence for CLAIM-0002/0004 and is intact; its own caveat (re-probe before
paper-track, driver updates) is appropriately logged in needs_attention #2.

## Part 2 — Open-gap hunt (HEAVY early-kill)

I generated candidate adjacent gaps and killed each against the 5 promoted claims + 9 dead ideas:

| Candidate gap | Verdict | Why |
|---|---|---|
| AMD's TRUE mapping ceiling (push past 80M) | **KILL** | (a) gold-plating — CLAIM-0002 already GREEN at 153x divergence; (b) FORBIDDEN: MI350X crash postmortem — unbounded mapping probes (alloc AND teardown) crashed the node 3x, one a 4-5h HW repair. Never re-run. |
| VMM CoW win-region on a 3rd vendor (Intel/Habana) | KILL | Same measure-zero logic as DEAD-0003; CLAIM-0001 found 0/12 win-region. A vendor with a win-region would CONTRADICT promoted claims — revival-only, not an open gap. Also no such HW available (CPU-only). |
| Static branch-policy regret (which recompute policy is best) | KILL (already done) | EXP-LANEB-PROBE already ran this: static-best = CDC hits oracle (regret 0.0); gated policy 1.44x. This is PROJ-0002/CLAIM-0006 territory, not a new PROJ-0001 gap. |
| Idle-window speculative prefill | OUT OF LANE | Owned by laneA; listed in MAP-0001 open_gaps (CLAIM-0002 poc, YELLOW). Not mine. |
| Mapping-budget model on a NON-VMM allocator (does the conserved-budget law generalize?) | KILL | CLAIM-0004 already root-causes it as a per-context VMM mapping-metadata budget (cross-vendor). Non-VMM allocators don't use that metadata path, so "does it generalize" is definitionally no — not an open question. |
| Write-after-share capability beyond bit-identity (latency/atomicity of CoW edit) | WEAK / KILL | CLAIM-0007 establishes the capability delta (bit-identical, kernel-transparent). Any "but is it FAST?" angle is answered by CLAIM-0001/0003: CoW is dominated/collapses. No win-region => no reason to characterize its edit latency as a contribution. |

**Result of hunt: NO genuine open gap found that is neither promoted nor dead.** Everything
adjacent is PROMOTED, DEAD, OUT-OF-LANE (laneA idle-window), or FORBIDDEN (GPU mapping probes).

## Conclusion
PROJ-0001 is a **saturated, mature negative-result project**: 5 promoted GREEN claims tell a
complete architectural indictment of GPU CUDA-VMM for agentic KV branching, 9 dead ideas fence
the dead-ends. The only residual work is (a) the cosmetic map-hygiene fixes D1-D4 above
(orchestrator-only) and (b) paper-track writing of the promoted claims. A saturated project is
a valid end-state. **Recommend the orchestrator mark PROJ-0001 mature/closed.**

(No claims seeded. No verdicts. No map edits. No experiments registered. CPU-only, no GPU probes.)
