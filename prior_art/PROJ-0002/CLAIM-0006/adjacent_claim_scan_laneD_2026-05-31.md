# ADJACENT-CLAIM SCAN — PROJ-0002 (researcher-0002-laneD, 2026-05-31, DESIGN/READ-only)

**Purpose:** is there a NEW, non-occupied PROJ-0002 claim worth seeding? Checked vs the 10 body-verified
neighbors + the MAP-0001 red_zones (cemetery) in registry/academic_map.yaml. NO claim/map edits made.

## OCCUPANCY MAP (what is already taken/dead — early-kill set)
The 1-degree neighborhood of CLAIM-0006 is HEAVILY mined. Already taken or DEAD per academic_map red_zones:
- inj/seq recompute COST-MAP + win-region — **CLAIM-0006 itself** (occupied).
- CDC-over-radix repair MECHANISM — DEAD (Irminsul twin, x2-indexed; PIC genus).
- slope~1 as a cross-engine law — DEAD (accounting identity; EXP-0013 per-engine, contiguous R2=0.0007).
- injection recompute exponent k~1.3 — DEAD-0009 (regime-local crossover, Pope/Kwon FLOP-derivable).
- idle-window speculative prefill — DEAD-0010 (generic speculate-or-skip identity; arXiv:2511.20048 +
  2605.06472 occupy).
- compaction-as-prefix-invalidation (long-horizon) — DEAD (EXP-0028; == R/S identity, eviction/TTL occupied).
- layer-stratified positional KV reuse — DEAD-0007 (capped <1.5% real incidence; revive only if >2%).
- 10 body-verified PIC/cost neighbors (Irminsul, EPIC, CacheBlend, Cache-Craft, MEPIC, KVFlow, CacheClip,
  "Don't Break the Cache", ContiguousKV, variable-size-block) — all distinct, none leaves a cost-map gap.

## CANDIDATE FOUND — and my recommendation: DO NOT SEED YET (early-kill / hold)

**Candidate "DISPATCH-0006":** a *content-injection-aware repair DISPATCHER* — a serving-time policy that, per
injection event, selects CDC (contiguous recompute) vs fused-PIC (CacheBlend selective recompute) using the
measured inj/seq crossover. Motivation is genuinely NEW and falls directly out of EXP-0027 + the true-lmcache
design: the two methods have an inj/seq crossover (PIC wins low inj/seq, CDC wins high), so neither dominates —
a dispatcher that routes on inj/seq could beat BOTH single-method baselines across the realistic agentic
workload (EXP-0005 median inj/seq ~2.8%, heavy tail).

**Why I recommend HOLD / early-kill rather than seed now:**
1. **Provenance/measurement-blocked, identically to CLAIM-0006's residual.** The dispatcher's entire value
   rests on the *real* CDC-vs-fused-PIC crossover, which is exactly what the true-lmcache follow-up (this
   design) has NOT yet measured. Seeding a dispatcher claim before the crossover is measured would repeat the
   re-impl-vs-published confound the committee is currently holding YELLOW on. **The crossover must be
   measured first** (by the very experiment designed here) — then a dispatcher claim has an empirical anchor.
2. **High accounting-identity / occupied-genus risk.** "Route to the cheaper of two known methods by a measured
   threshold" is a generic select-the-min policy — the same class the map already retired twice (DEAD-0010
   speculate-or-skip, EXP-0028 when-to-compact break-even). A reviewer will demand the dispatcher beat the
   trivial "always pick the per-cell winner" oracle by a non-identity margin, AND that adaptive KV-repair
   routing isn't already in the PIC-family scheduling work (KVFlow does workflow-aware reuse/scheduling;
   CacheClip selects tokens). Real collision risk in the EPIC/KVFlow scheduling neighborhood — NOT yet
   body-cleared for a *routing/dispatch* axis (the 10 neighbors were cleared for the cost-map axis, not this).
3. **Correct sequencing:** the honest move is to (a) run the true-lmcache experiment, (b) get the measured
   crossover, (c) THEN decide if a dispatcher is more than an accounting identity. Seeding now is premature.

**Verdict: HOLD (do not seed). Re-evaluate ONLY after the true-lmcache crossover is measured** and only if the
dispatcher can be shown to beat the per-cell-winner oracle by a margin that is not a trivial min-selection
identity, and after a body-level prior-art clearance specifically on the *adaptive-repair-routing* axis
(EPIC/KVFlow/CacheClip scheduling) — which has NOT been done (prior clearance was cost-map-axis only).

## NO OTHER non-occupied candidate found
Every other 1-degree adjacency is in CLAIM-0006, a red_zone, or a body-verified neighbor. No clean open lane.
