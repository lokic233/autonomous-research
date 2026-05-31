# autonomous-research

A **research-os instance** — durable, version-controlled research state for autonomous AI-systems research.
Runs on the [research-os](https://github.com/lokic233/research-os) engine. First-class objects, not session logs.

## Structure (research-os compliant)
```
registry/
  claims/      CLAIM-xxxx.yaml   — first-class claims (seed/active/weakened/killed/promoted)
  experiments/ EXP-xxxx.yaml     — registered experiments (no compute without one)
  verdicts/    VERDICT-xxxx.yaml — committee verdicts
  cemetery/    DEAD-xxxx.yaml    — killed ideas (resurrection-guarded)
  academic_map.yaml · baselines.yaml · projects.yaml
experiments/   EXP-xxxx/         — experiment artifacts (results, analysis)
prior_art/     CLAIM-xxxx/       — prior-art packets
sessions/      raw execution logs (forensic only — NOT source of truth)
learning/      crash postmortems + operational lessons
projects/      project lifecycle
```
Config (`research-os.config.yaml`) is git-ignored here (Meta-internal: nodes, committee backends, cert glue)
— it lives in the private `research-os-meta` repo.

## Current state (migrated from sessions 511ce2e2 / 048fcb0d / c48efa79)
**Theme (PROJ-0001):** GPU CUDA-VMM is the wrong abstraction for agentic KV branching.
- **Promoted (6/6 GREEN):** CLAIM-0001 (HW CoW dominated), 0002 (NVIDIA mapping-ceiling cliff),
  0003 (compounding throughput collapse), 0004 (mapping-budget wall), 0006 (prefix-cache invalidation
  law + CDC repair), 0007 (attention-visible write-after-share, bit-identical).
- **Active/YELLOW:** CLAIM-0005 (injection penalty — sub-quadratic, capped), 0008 (error-class→recovery).
- **Cemetery (8 killed):** HW isolation primitive, handle-attestation, VMM decision-procedure, super-linear
  artifact, segmented-hash, KV-divergence model, layer-stratified reusability, interior KV-repair.

## Lineage
Sessions under `sessions/5_30_2026/` are the raw forensic logs that produced this state. The registry —
not those logs — is the source of truth. New work goes through the engine (`ros seed/exp/...`).
