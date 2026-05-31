# Lane-B Gap Analysis — hunt for a NEW open-gap claim adjacent to CLAIM-0006
agent: researcher-0002-laneB | role: researcher | date: 2026-05-31
project: PROJ-0002 | reporting to: orchestrator 22bd6bef-b84b-4827-a371-87443ea8602f
constraint: write-only under PROJ-0002; NO claims/verdicts/map edits; CPU-only; READ-ONLY on external systems.
VERDICT: **EARLY-KILL** all candidates investigated. No defensible new open gap found adjacent to CLAIM-0006.

## Mandate
Find a NEW open-gap claim in prefix-cache-invalidation space NOT occupied by the 10 body-verified
neighbors + cemetery, distinct from laneA's CDC win-region (CLAIM-0006). Heavy bias to EARLY-KILL.

## Candidate gaps investigated + collision check (vs 10 neighbors + cemetery)

### Candidate A — Eviction-vs-recompute economics under agentic memory pressure
COLLISION = FATAL. The eviction/memory-budget axis is SATURATED:
- Continuum (2511.02230, KV-TTL retention) — already a known_baseline/key_prior_work.
- KVFlow (2507.07400) — workflow-aware EVICTION/prefetch (body-verified neighbor #5 of PIC family).
- New (2026) eviction works found via web sweep: ForesightKV (2602.03203), ARKV (2603.08727),
  "Reformulating KV Cache Eviction" (2605.07234), LookaheadKV (2603.10899, ICLR'26),
  Learning-to-Evict (2602.10238), CAOTE (2504.14051), "Cache What Lasts" (2512.03324),
  "Agent Memory Below the Prompt" (2603.04428), multi-tier dynamic storage (Springer).
KILL: eviction-cost-aware management is a crowded sub-field; any "evict-vs-recompute tradeoff"
framing lands inside it. Not defensible.

### Candidate B — Cumulative trajectory recompute (compounding injections over a multi-turn loop)
COLLISION = self (trivial corollary). This is just integrating CLAIM-0006's per-event inj/seq
cost-map over EXP-0005's measured injection distribution. Not a new thesis; a derived aggregate of
two existing PROJ-0002 results. Also overlaps "Don't Break the Cache" 2601.06007 ($-cost grows with
conversation length) at the motivation level. KILL.

### Candidate C — Tool-result DEPENDENCY invalidation (semantic staleness, not positional)
COLLISION = FATAL. ToolCacheAgent (ICLR'26 submission, openreview 05f7fe08...) does dependency-aware
invalidation (get_order(id) cached on id; delete_order(oid) issues prefix-based invalidation). Also
"Hierarchical Caching for Agentic Workflows" (MDPI 8/2/30) maintains a dependency graph for
write-induced invalidation. Occupied. KILL.

### Candidate D — Count-vs-volume bimodality => STATIC-POLICY REGRET (the one with a testable core)
The most defensible angle. EXP-0005 exposed but did not characterize a striking bimodality: 24.6% of
injections (by COUNT) are CDC-win (<=1%) but only 3.7% by TOKEN-VOLUME; 36.5% by count but 80.7% by
volume DEGRADE (large dumps dominate volume). Hypothesis (candidate new property, NOT the inj/seq
cost-map): the count/volume split forces a per-event policy-dominance CROSSOVER such that NO single
static prefix-repair policy (FULL-recompute / CDC / FAIR-PIC) is workload-optimal, and a trivial
size/ratio-gated policy would beat all three by a large characterizable regret. If true and large,
that is a workload-structure characterization distinct from CLAIM-0006's per-event cost-map.

EXPERIMENT (EXP-LANEB-PROBE, CPU-only, stdlib, deterministic seed 20260531, 289,807 injections):
Re-used EXP-0005's evidence-grounded size/trajectory model. Per-event recompute-token cost grounded
in the registry's OWN body-verified numbers:
  - FULL (vLLM-APC/Radix, prior_art_note): recompute diverged suffix = (1-pos)*S + R
  - CDC  (CLAIM-0006/EXP-0002 slope~1): recompute = R (position-independent, re-chunk edited region)
  - PIC  (CacheBlend/EPIC, FAIR per EXP-0006): R * pic_factor, factor 1.7x at small ratio -> 1.0x (tie) at >=5%
Oracle = per-event min; static-best = best single global policy; gated = CDC if R/S<5% else FULL.

RESULT (experiment_result/results.json):
  - static_best_policy = CDC; **regret_static_best_vs_oracle = 0.0**
  - best_policy_by_count_frac = {CDC:1.0, FULL:0, PIC:0}; by_volume_frac = {CDC:1.0,...}
  - ratio-gated policy regret = +143.6% (gating to FULL on large dumps is STRICTLY WORSE)

ANALYTIC CONFIRMATION (not just Monte-Carlo): CDC = R is a POINTWISE LOWER BOUND.
  FULL - CDC = (1-pos)*S >= 0  (equality only at inject-at-very-end pos=1).
  PIC  - CDC = R*(factor-1) >= 0  (equality only ratio>=5%).
  => CDC weakly dominates FULL and PIC at EVERY event; oracle == CDC; regret == 0; NO crossover exists.

VERDICT on Candidate D = **KILL**. The "no static repair policy is optimal / heavy tail forces a
gated policy" property is FALSE by construction of the registry's grounded cost models. There is no
second axis: the only thing that varies across events is CDC's magnitude R/S — which is EXACTLY the
inj/seq cost-map CLAIM-0006 already owns (and which is itself a slope~1 accounting identity, DEAD as a
"law"). A policy-regret characterization collapses back onto CLAIM-0006's single surviving leg.
(Caveat honestly stated: this is a recompute-TOKEN proxy. CDC's pointwise dominance is in recompute
tokens; it does NOT account for CDC's scattered-vs-contiguous WALL-CLOCK arithmetic-intensity penalty
— which is precisely CLAIM-0006's already-open eval gate-B (GPU wall-clock vs real PIC). So even the
wall-clock angle is not new: it is gate-B, already owned and human-go.)

## Net recommendation to orchestrator
EARLY-KILL the laneB hunt. The prefix-cache-invalidation neighborhood adjacent to CLAIM-0006 is
fully occupied or collapses onto CLAIM-0006's existing single surviving leg + its existing open gates.
Do NOT seed a new claim. No map edit proposed (per constraints). A fast, correct kill is the outcome:
laneB found no defensible NEW open gap. Recommend orchestrator keep resources on CLAIM-0006 gate-B
(GPU wall-clock on real PIC) and laneA's CDC win-region, which remain the binding GREEN-blockers.

## Files
- experiments/2026-05-31/EXP-LANEB-PROBE/impl/static_policy_regret.py
- experiments/2026-05-31/EXP-LANEB-PROBE/experiment_result/results.json
