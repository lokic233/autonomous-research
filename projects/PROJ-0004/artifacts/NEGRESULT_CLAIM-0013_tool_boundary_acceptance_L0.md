# Negative Result — No Distinct Tool-Boundary Acceptance Cliff (L0 proxy)
## CLAIM-0013, PROJ-0004 — "Tool-Boundary Acceptance Cliff in Speculative Decoding for Agent Trajectories"
researcher-0013-L0-r4 | prompt v001 | 2026-06-01 | evidence: EXP-0046 (L0, CPU, stdlib top-1-agreement proxy)
Pre-registration: experiments/2026-06-01/EXP-0046/impl/preregistration.md (locked before run)
Committee gate: VERDICT-0050 (required_evidence = the 4 controls below)

## TL;DR
On two real agentic tool-calling corpora (Claude Code n=70, Codex n=76 sessions), the hypothesized
**position-localized acceptance penalty over K=8 decode steps after each tool-result injection does NOT
exist** as a distinct boundary phenomenon. There is a striking but **single-token (d=1 only)** acceptance
collapse (~5-10x: acceptance 0.025-0.051 vs interior baseline 0.25-0.27, Holm-significant, replicated),
but the pre-registered highest-priority control — splicing the identical tool-result text at non-boundary
positions — **reproduces (Claude Code) or exceeds (Codex) the entire drop**. The effect is therefore a
**content-type/context artifact, not a tool-boundary position effect**. CLAIM-0013 is FALSIFIED at L0.

## What we measured (top-1-agreement proxy)
"Acceptance" := a trigram-backoff next-token predictor (trained on a held-out 50/50 session split) has
top-1 == the realized assistant token. We index acceptance by distance d from the most recent tool-result
boundary and compare to the within-trajectory interior baseline (d>8). This is a CPU/stdlib stand-in for
real speculative-decoding draft/target agreement (no GPU/torch on node); see Limits.

## Result vs the 4 committee-required controls (all pre-registered)
1. **Content-type-matched null [decisive killer]:** diff_content = mean(boundary_penalty - spliced_penalty)
   = -0.015 (CC, CI[-0.055,+0.007], includes 0) and -0.075 (Codex, CI[-0.110,-0.040], NEGATIVE). The
   boundary penalty does not exceed the content-spliced-elsewhere penalty -> content-type, not position.
2. **Non-tool context-shift:** boundary exceeds generic user-turn shift only in CC (+0.050, CI>0); fails
   in Codex (underpowered: sparse user boundaries). Moot — controls 1 & the primary endpoint already fail.
3. **Entropy conditioning:** within predictor-entropy strata the pooled boundary penalty does not survive
   (CC +0.026 CI includes 0; Codex -0.059 CI<0).
4. **Pre-registration:** K=8 + margins + Holm fixed before running. Only 1/8 positions Holm-significant
   (required >=4/8). Net mean penalty: CC +0.043 (CI includes 0), Codex -0.079 (NEGATIVE).

Gate outcome: CANDIDATE-POSITIVE = NO in both corpora -> **CLEAN KILL** per the pre-registered rule.

## Why this is useful (the negative is the product)
- **For serving teams:** a boundary-aware SD scheduling policy that suppresses/re-warms speculation for K
  steps after each tool result is **NOT motivated** by this evidence. Any real wasted-verification recovery
  is confined to the single first post-injection token (and is itself content-driven), not a K-step window.
- **Corroborates 2510.02128** ("Disparate Impacts of SD": task/content axes, not within-trajectory
  position, drive acceptance variance) and contextualizes 2601.11580 ("SD: Performance or Illusion?",
  which reports GENERIC position-dependent acceptance on vLLM): the position dependence is not attributable
  to the tool-result resumption boundary on agentic workloads.
- The d=1 collapse is a real, replicated, explainable phenomenon: predicting the first prose token after
  injected non-prose (code/JSON/stdout/newlines) is hard wherever that transition occurs.

## Limits (honest)
Trigram top-1-agreement proxy, not a real draft/target SD pair; its boundary sensitivity is conservative
(2-token context window + result-derived content). A real neural draft attends over the full injected
result and could, in principle, show a longer cliff this proxy cannot resolve — but the proxy gives NO
positive evidence for one and shows the detectable effect is content-confounded. Single node, single proxy,
CC+Codex only (Gemini excluded as messy). The L1 GPU vLLM real-SD accepted-length telemetry lane would be
the only way to confirm a real cliff; this L0 gate produced no signal justifying that spend.

## Prior-art posture / novelty
COLLISION FLAG (verified, differentiable): 2601.11580 already establishes generic position-dependent SD
acceptance on production vLLM — so "position-dependent acceptance exists" is prior art; our (now negative)
contribution is the boundary-localization-with-controls question, which we answer in the negative.
Full citation verification: prior_art/PROJ-0004/validated_autonomous_researcher_exps.md.
