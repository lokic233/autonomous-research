# EXP-0028 — Compaction-as-prefix-invalidation: NEW cost surface, or the p≈0 boundary of CLAIM-0006?

**Agent:** researcher-0002-laneE · **Project:** PROJ-0002 · **Claim:** none (pure characterization probe) · **Level:** 1
**Method:** CPU-only, stdlib, deterministic (seed 20260531), <2s, <50MB. NO GPU/torch/CUDA.
**prompt_version:** researcher_laneE_v001 · **Hardware:** CPU-only (dengcchi-mac)

## Crux
CLAIM-0006 owns the per-event recompute cost-map for **mid-prompt TOOL INJECTION** (recompute ≈ R/S,
slope~1 accounting identity). Candidate NEW gap (laneE): **context COMPACTION** — a long-horizon-loop
event where the agent REPLACES a long history span H (early positions, p≈0) with a short summary
G≪H (sequence SHRINKS, then continues). Compaction is structurally unlike injection (which APPENDS and
grows S). Question: does a compaction event's cache cost live OUTSIDE CLAIM-0006's surface (→ candidate
new claim), or is it the p≈0 corner of the SAME identity (→ collapses onto CLAIM-0006 + its
already-flagged attention-sink/p=0 caveat)?

## Model (token-proxy recompute, same currency as EXP-0002/0005/0006 — honest proxy)
S = pre-compaction cached length. Compaction replaces the first H tokens after a never-touched
BASE (system+schema) prefix with a G=ρ·H summary. New length S' = S−H+G. Three policies, exactly as
CLAIM-0006/EXP-0006: FULL (contiguous vLLM-APC/Radix) = recompute diverged suffix from first changed
token = (S'−BASE)/S'; CDC (slope~1, re-chunk edited region) = (G+w)/S'; PIC (CacheBlend/EPIC fair
factor 1.7→1.0 at ≥5%). Grid: 80 cells (S∈{8k,23k,50k,120k,400k} × H_frac × ρ).

## Results (experiment_result/results.json)
- **Identity test 1 — CDC compaction == CLAIM-0006 R/S with R:=G:** max_abs_err = **0.0** (machine zero), PASS.
  CDC's compaction recompute fraction is *exactly* (G+w)/S' = CLAIM-0006's R/S identity with the
  "changed/injected size" set to the summary size G. **Compaction is NOT a new cost surface for CDC.**
- **Identity test 2 — FULL compaction == CLAIM-0006 FULL-at-front:** max_abs_err = **0.0**, PASS.
  FULL compaction = diverged-suffix recompute from the first changed token = CLAIM-0006's FULL evaluated
  at p = p_c ≈ 0 (the front). Same identity, p≈0 corner — exactly the attention-sink region the registry
  ALREADY carves out as "genuinely position-dependent there" (Irminsul caveat, novelty-boundary-0006).
- **Break-even ("when to compact") is a generic accounting identity:** T* = C_recompute / (S − S').
  Structurally identical to DEAD-0010's speculate-or-skip h·f ≥ α/(1+α) — a pure cost/benefit ratio, no
  KV-specific anomaly. (BASE, w cancel; identical pattern to the slope~1 and k~1.3 retirements.)

## Verdict: **KILL** the compaction-as-new-invalidation-property candidate.
Compaction's per-event recompute cost collapses onto CLAIM-0006's existing cost-map (R:=summary size,
p≈0 corner). The only genuinely-distinct quantity is the net cache-footprint SAVINGS from shrinking S —
which is the eviction/Continuum KV-TTL/memory-pressure neighborhood already KILLED as occupied
(laneB Candidate A: KVFlow, ForesightKV, ARKV, Continuum, etc.). The "when-to-compact" decision is a
generic accounting identity (DEAD-0010 pattern). No non-derivable anomaly. Not defensible as a new claim.

## Caveats (do not overclaim)
- Token-count proxy (inherits EXP-0002/0006 scope). The identity collapse is EXACT in the proxy; a
  wall-clock divergence (CDC contiguous re-chunk of the summary vs PIC scattered) is the SAME eval gate-B
  CLAIM-0006 already owns (GPU, human-go) — not a new axis.
- One genuinely-position-dependent sliver survives: the p≈0 attention-sink chunk. But CLAIM-0006's
  registry ALREADY flags this (Irminsul carve-out); compaction does not open new ground there.

## Reproduce
`/usr/bin/python3 experiments/2026-05-31/EXP-0028/impl/exp0028_compaction_identity.py` → results.json. seed 20260531.
