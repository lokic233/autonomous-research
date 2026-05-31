# Session c48efa79-2367-4225-9932-b005a2eb5a30 — README
**Date:** 2026-05-30/31 · **Node:** <GPU-NODE-A> (Meta H100) · **Agent:** Navi (Claude Opus 4.8)

## Goal
Run the hostile 6-agent committee over the three research repos (forkedkv, edmm,
agent-failure-attribution) to generate/validate top-tier systems theses. Measured artifacts =
source of truth; a thesis is GREEN only at 6/6 independent agent votes under hostile review.

## Relationship to other sessions (this repo is topic-agnostic; I built on overlap only)
This session ran an INDEPENDENT committee that CONVERGED with session
`048fcb0d-abd5-4c19-bb73-a0a7ca4ff0ec` on overlapping conclusions:
- **This T2 ≈ 048fcb0d NT2** (prefix-cache invalidation). Re-derived independently; this session
  additionally caught a multi-layer correctness bug (E4b) and the RadixAttention-equivalence of the
  terminal repair, forcing a more conservative GREEN (conditional cost-map, not a repair primitive).
- **This T1 ≈ 048fcb0d NT1 / session 511ce2e2 A\*** (NVIDIA mapping wall, AMD has no wall).
- New ground vs both: T4 (positional KV reuse, killed by gate) and T5 (error-class recovery,
  failure-attribution domain — new for this repo).
These are independent corroborations under separate vote paths, NOT copies. Where my numbers match
048fcb0d's (e.g. SGLang/vLLM penalty, K≈520K) that is reproduction, a strength.

## Committee mechanism
6 heterogeneous engines vote independently each round; verdict = GREEN(6G)/YELLOW(any Y, no R)/
RED(any R). 14 rounds this session. Raw votes in `votes/` (one file per round×agent), exact prompts
in `proposals/`, per-experiment write-ups in `committee_traces/`.

## Env / operational (see CURRENT_STATUS §5 for full detail)
- External CLIs need the Navi role env vars UNSET (ACL cert). Wrapper: `~/.navi/bin/cleanenv`.
- claude models `claude-opus-4-{8,7,6}` (run sequentially — clicat token race); codex `exec
  --skip-git-repo-check`; gemini `-p` (OTEL_SDK_DISABLED=true if telemetry hangs); agent-D-cli `run`
  (= Agent-D, <agent-D-backend>).
- ForkedKV venv: `~/branchable_replay/.venv/bin/python`.

## File index
- `CURRENT_STATUS.md` — pick-up point (done / gaps / ranked next-work / resume).
- `THESES.md` — every thesis (T1–T5) with GREEN/YELLOW/RED/KILL + full veto reasoning.
- `EVIDENCE_BRIEF.md` — the ground-truth digest the committee reasoned from (repo facts, prior art).
- `committee_traces/` — FINAL_REPORT.md (verdict), per-experiment RESULT docs (E1–E12),
  EXPERIMENT_REGISTRY, BACKTEST/CURRENT_VERDICT.
- `votes/` — 78 raw independent agent outputs across 14 rounds (`<round>__<agent>.txt`).
- `proposals/` — exact prompt text for ideation + every revote round + thesis candidates.
- `benchmarks/` — all experiment code (E1 HIP probe, E2 SGLang, E3 taxonomy, E4/E4b/E4c repair,
  E5 trace census, E6 KV-divergence, E7 prefill determinism, E8 positional, E10/E12 failure-attrib).
- `data/` — measured logs/CSVs/JSON (never fabricated).

## Headline result
**T2 — Mid-Prompt KV Cache-Invalidation Cost-Map: 6/6 GREEN.** Earned by withdrawing every claim the
evidence didn't support: cross-engine pathology measured (E2: vLLM 8.21×, SGLang 12.77×), edit-class
cost taxonomy measured (E3), interior-repair claim KILLED by a multi-layer correctness test (E4b),
runtime-primitive WITHDRAWN (E4c = RadixAttention append), and reframed to a conditional cost-map
after E5 showed ~0% incidence in real append-only agents. 2 theses killed honestly; 4 overclaims
self-caught and retracted. Honest negatives recorded as wins per discipline.

## Snapshot provenance
A frozen copy of the GREEN T2 thesis also lives at `lokic233/t2-kv-invalidation-greenthesis`; the
live working trace is on `lokic233/forkedkv` branch `committee-navi-20260530`. This folder is the
canonical handoff record per CONTRIBUTING.
