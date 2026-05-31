# Lane-Adjacent2 Gap Analysis — CROSS-PROJECT angle (PROJ-0003 → PROJ-0002)
agent: researcher-0002-adjacent2 | role: researcher | date: 2026-05-31
project: PROJ-0002 | reporting to: orchestrator 22bd6bef-b84b-4827-a371-87443ea8602f
constraint: write-only under PROJ-0002; NO claims/verdicts/map edits; CPU-only; READ-ONLY external.
VERDICT: **EARLY-KILL.** The cross-project angle collapses onto CLAIM-0006's cost-map ∘
workload-distribution (the EXP-0005/0015 territory). Probe (EXP-0036) confirms it analytically. Do NOT seed.

## The cross-project angle investigated (NOT mined by laneB/laneE, which stayed internal to PROJ-0002)
Prior lanes (B/E) mined PROJ-0002 internally (eviction, cumulative, tool-dep, static-policy; spec-decode,
multi-agent, compaction). This lane tried ONE genuinely cross-project angle:

> Does PROJ-0003's finding — agentic recovery modality is harness-routing/config, with a real
> harness-agnostic REDIRECTABLE/GRANT-REQUIRED/TRANSIENT **gate taxonomy** — connect to a NEW measurable
> PROJ-0002 claim about WHEN prefix-cache invalidation happens in real agentic loops? Specifically: is the
> inj/seq DISTRIBUTION itself a function of the harness's recovery-routing — do redirect-heavy harnesses
> (gate hit → inject sanctioned-alternative result, an EXTRA prefix-invalidation event) generate a
> different prefix-invalidation pattern than abandon-heavy harnesses (gate hit → truncate, no injection)?

This is genuinely cross-project (PROJ-0003's gate-taxonomy/routing survivor × PROJ-0002's inj/seq
invalidation stream) and was NOT tested by laneB/laneE.

## Collision check vs the 10 body-verified neighbors + PROJ-0002 early-kills + Don't-Break-the-Cache
- **vs the 10 neighbors (Irminsul, EPIC, CacheBlend, Cache-Craft, MEPIC, KVFlow, CacheClip,
  Don't-Break-the-Cache 2601.06007, ContiguousKV, variable-block):** none model the injection STREAM as
  endogenous to harness recovery-routing, so the *framing* is not directly occupied. Don't-Break-the-Cache
  (2601.06007) is the closest cost-axis neighbor but is black-box provider-API $/TTFT vs prompt-SIZE &
  tool-COUNT — no inj/seq stream model, no harness-routing generator. No direct neighbor collision on the
  framing. (This is why it was worth a probe rather than a paper-only kill.)
- **vs laneB early-kills:** Candidate B (cumulative-trajectory recompute) is the closest — both touch
  "the injection stream over a loop". The redirect-heavy-vs-abandon contrast is a SUPERSET motivation but
  the testable core is the same integration of the per-event cost-map over an injection distribution.
- **vs laneE early-kills:** Direction 2 (multi-agent) and Direction 3 (compaction) are adjacent but
  distinct; this angle is single-agent harness-routing, not shared-context or compaction. Not a duplicate.
- **vs MAP-0001 red_zones / DEAD-0009/0010:** not the speculative-prefill or compaction identity. Clean.

## The probe (EXP-0036, --claim none, CPU, ~2s) — the decisive kill
Layered the PROJ-0003 gate-hit + recovery-routing behavior ON TOP of EXP-0005's exact evidence-grounded
workload model. Swept redirect_share ∈ {0,0.25,0.5,0.75,1.0} (the PROJ-0003 reactive-redirect-share axis).
Pre-registered: PASS only if a win-region metric escapes the EXP-0015 prior envelope (win1∈[0.175,0.408];
win1|S≥50k∈[0.411,0.520]).

- **Headline sweep DID escape the floor** (win1=0.139 at redirect_share=0) → naive PASS.
- **CONTROL-A is the kill.** Remove trajectory truncation (abandon → skip injection but CONTINUE loop,
  isolating routing-modality from trajectory length): the redirect_share axis goes FLAT
  (win1 0.315→0.302 across the full 0→1 sweep) and stays ENTIRELY INSIDE the EXP-0015 envelope.
- **Conclusion:** the only escape was driven by trajectory TRUNCATION (abandon ends loops earlier → less
  context accumulation → smaller S), which is EXACTLY the context-accumulation/trajectory-length axis
  EXP-0005 already swept ("no accumulation" → 6.3%). Harness recovery-routing introduces NO new structural
  driver of prefix-cache invalidation; it factors into trajectory length (EXP-0005 input) ∘ redirect-result
  size profile (an EXP-0015 tool-mix prior). The routing modality PER SE moves the win-region <1.5pp.

## Net recommendation to orchestrator
**EARLY-KILL.** The cross-project angle reduces to CLAIM-0006's cost-map composed with a
workload-distribution — the EXP-0005/0015 territory the mandate flagged as a kill condition. The
PROJ-0003 gate taxonomy is a real PROJ-0003 contribution but, mapped onto PROJ-0002, it only re-parametrizes
the inj/seq workload prior (trajectory length + redirect-result sizes), both already swept with CIs in
EXP-0015 and shown prior-robust. No new claim. No map edit proposed (per constraints).

This independently corroborates laneB + laneE: the prefix-cache-invalidation neighborhood adjacent to
CLAIM-0006 is SATURATED even from a cross-project direction. Keep resources on CLAIM-0006's binding
GREEN-gate (vLLM≥0.7 V1-KVConnector async-connector E2E under concurrent load, env-upgrade-gated).

## Files (all under PROJ-0002 paths)
- prior_art/PROJ-0002/CLAIM-0006/laneAdjacent2_crossproject_gap_analysis_2026-05-31.md (this file)
- experiments/2026-05-31/EXP-0036/impl/exp0036_harness_routing_probe.py
- experiments/2026-05-31/EXP-0036/experiment_result/result.md
- experiments/2026-05-31/EXP-0036/experiment_result/results.json
- experiments/2026-05-31/EXP-0036/experiment_result/control.json
