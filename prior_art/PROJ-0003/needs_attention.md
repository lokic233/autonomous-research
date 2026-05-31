# PROJ-0003 prior-art / MAP-0002 deltas — from EXP-0007 (researcher-failattr-r2)

## What MAP-0002 lists as OCCUPIED (early-kill check)
- failure taxonomies — OCCUPIED. (e.g. "Why Do Multi-Agent LLM Systems Fail?" MAST taxonomy 2025;
  AgentBench/τ-bench failure buckets.) A *static taxonomy alone* is dead-on-arrival as a contribution.
- post-hoc summaries — OCCUPIED.
- LangGraph time-travel (deterministic only) — OCCUPIED.

## What EXP-0007 measured that is NOT a bare taxonomy (the surviving novelty)
The contribution that survives is NOT "here is a taxonomy" but a *quantified predictive law on REAL traces*:
error-class → recovery-competence, measured against a class-agnostic NULL baseline with effect size + honest
out-of-sample (leave-one-out Brier) validation + leave-one-session-out robustness. Specifically:
  - error-class is OUT-OF-SAMPLE predictive of recovery (LOO-Brier −35% vs null; Cramér's V=0.64).
  - the dominant axis is **provenance/permanence**: agent-uncontrollable harness/policy gates
    (web_disabled 0/109) are near-unrecoverable; environmental/transient errors recover 0.63–1.0.
  - permanent-vs-transient split φ=0.45 on 356 real failures, robust across 26/37 sessions.
This is the MAP-0002 `open_gap: real-trace failure census` + sharpens `error-class -> recovery competence`.

## Proposed MAP-0002 delta (for ORCHESTRATOR to apply — I do not write the map)
- known_baselines: add **"class-agnostic recovery rate (NULL)"** as the mandatory baseline for any
  error-class→recovery claim. (NOT KV-cache baselines — CLAIM-0008's stored vLLM/SGLang/FlashInfer
  baselines are BUG-15, wrong domain.)
- open_gaps: `error-class -> recovery competence` can move toward GREEN-characterization. The remaining
  honest gaps to fully close it: (1) **cross-harness** generality (corpus is Claude-Code-only; policy-block
  taxonomy is harness-specific); (2) **outcome-definition decoupling** — count cross-tool workarounds as
  recovery (current label = same-intent retry success = lower bound); (3) intervention test: does telling
  the agent the error-class *causally* change recovery (vs the observational result here).
- occupied_territory: note that a *static failure taxonomy* is occupied; the live novelty is the
  *predictive characterization vs null on real traces*, not the taxonomy.

## Honest risk
The strongest cell (policy.web_disabled 0/109) is partly mechanically circular: a hard policy block is
unrecoverable partly because the agent cannot retry it to success. The genuinely non-trivial signal is the
within-transient spread + the out-of-sample Brier gain. A hostile reviewer will push on the circularity;
the defense is the LOO-Brier and the within-transient variation, not the 0/109 cell alone.

## Update 2026-05-31 (EXP-0008 / VERDICT-0016 — orchestrator-r2-001)
- **CLAIM-0008 WEAKENED by its own adversarial follow-up.** EXP-0007's error-class->recovery signal is
  OUTCOME-DEFINITION-DEPENDENT. Counting cross-tool workarounds (EXP-0008): Cramér's V 0.644->0.239
  (n.s.), out-of-sample LOO-Brier gain +0.087->~0, permanence φ 0.454->0.138. Truth is BRACKETED:
  EXP-0007 = same-intent LOWER bound, EXP-0008 = intent-class UPPER bound.
- **New taxonomy insight (map-worthy):** `policy.web_disabled` is a REDIRECTABLE gate, not terminal —
  the agent reroutes blocked WebFetch -> sanctioned `external_web_search` 61% of the time (66/109,
  audited as genuine same-goal recoveries). Failure-attribution taxonomies should split REDIRECTABLE
  vs TERMINAL policy gates; "permanence" is not a property of the error class alone.
- **Surviving defensible claim:** error-class predicts recovery MODALITY (same-tool retry vs cross-tool
  redirect), NOT recovery OCCURRENCE — a narrower, different claim than CLAIM-0008. Would need a re-seed
  + cross-harness + interventional evidence.
- **Limits:** single-harness (Claude Code); decisive cell n=109; redirect behavior harness-specific.
