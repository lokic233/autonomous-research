# THESES — session 048fcb0d · 2026-05-30 · all verdicts + veto reasoning

6-agent committee: CC4.8, CC4.7, CC4.6, Codex5.5, Gemini3.5, Agent-D.
Rule: GREEN=6 GREEN; YELLOW=any YELLOW & no RED; RED=any RED. Measured artifacts = source of truth.

This session GENERATED 3 NEW theses (distinct from session 511ce2e2's C*/A*/T-TAX) and drove ALL
THREE to 6/6 GREEN, each by an experiment that closed the EXACT gap the committee named.

## NT1 — The Mapping-Budget Wall  → **GREEN (6/6)**
One-sentence: NVIDIA CUDA-VMM enforces a low per-DEVICE access-descriptor budget
K≈523,404 (charged at cuMemSetAccess) that bounds VMM-backed KV-branch concurrency; AMD ROCm has
no such graceful ceiling — a driver-POLICY artifact, not a hardware limit.
- Evidence: E2 cross-vendor (AMD >19M maps, no graceful wall, conserved); E3a root-cause (R1: 1
  reservation still 523,404 maps → K = access-descriptor budget, NOT reservation count; R1=control
  =523,404 exact, 0.000% var); E3d n=1/2/3 (total conserved ~523,300 ±0.05%, even split → per-device);
  E3c relevance (under CoW sharing the budget BINDS: 64 branches @128k ctx vs 6 on naive HBM).
- Vote path: 4 GREEN+2 YELLOW (CC4.8 relevance, Agent-D root-cause/vendors) → after E3a/d/c traces
  +honest retraction of the E3b "super-linear" overclaim → **6 GREEN**.
- Veto reasoning recorded: CC4.8 GREEN was CONDITIONAL on (a) headlining the conserved-budget
  finding, (b) fully retracting "super-linear" (an E3b artifact of per-worker VA pre-reservation),
  (c) labeling E3c relevance as a MODEL not a measurement. All met (see E3D_CORRECTION.md).

## NT2 — The Prefix-Cache Invalidation Law  → **GREEN (6/6)**
One-sentence: mid-sequence tool-injection breaks vLLM prefix caching with a superlinear TTFT
penalty caused by FIXED-SIZE block boundaries (not hash chaining); content-defined chunking (CDC)
re-syncs downstream blocks, cutting recompute to ~2% regardless of injection position.
- Evidence: HONEST NULL v1 — de-chained "segmented hash" = 1.0× at every injection point (FALSIFIED
  hash-chaining hypothesis, using vLLM's real hash_block_tokens). CDC repair v2: ~2% recompute vs
  10.7–90.1% fixed-block (5.4–45.4×). Wall-clock microbenchmark (real H100 SDPA): 11.6× @8k, 119.6×
  @32k even with a pessimistic 1.5× CDC overhead penalty; superlinearity shown in wall-clock
  (fixed 0.613→8.436ms = 13.8× for 4× ctx; CDC flat ~0.05–0.07ms).
- Vote path: round1 (count model) 4 GREEN + CC4.8 YELLOW + Gemini YELLOW (both cited the SAME gap:
  E2E wall-clock TTFT / does CDC overhead eclipse the gain?) → wall-clock microbenchmark → **6 GREEN**.
- Veto reasoning: both YELLOWs were discharged by the microbenchmark; Gemini noted it "despises
  substituting microbenchmarks for true E2E" but the 119× margin mathematically settles it.

## NT3 — Attention-Visible GPU-MMU Write-After-Share  → **GREEN (6/6)**
One-sentence: VMM page-remap keeps a branch's contiguous VA INVARIANT through write-after-share
CoW, so unmodified FlashAttention/SDPA runs bit-correct on the post-CoW branch — a capability
vAttention (read-only, no fork) and vLLM-APC (block-table CoW moves the mapping) lack.
- Evidence: E1 address-space (ForkedKV VA invariant after CoW; APC block-table entry MOVES 61→59 →
  kernel indirection). E1b decode-correctness (real Qwen2.5-7B layer-0 SDPA on post-CoW branch vs
  full-clone reference, identical edit: bit_identical=TRUE, max_abs_diff=0.0, CoW fired, kernel
  unmodified).
- Vote path: 6×YELLOW (all demanded "prove vAttention/APC can't express it") → E1 (1 GREEN, 4 YELLOW:
  wanted E2E decode number) → E1b → **6 GREEN**. Cleanest convergence; every GREEN cites max_abs_diff=0.0.

## REJECTED / not-pursued (documented so no one re-proposes)
- "Segmented (de-chained) hash" repair for NT2: KILLED — measured 1.0× (no improvement). The cascade
  is block-BOUNDARY alignment, not hash chaining. Led to the correct CDC repair.
- "Super-linear multi-context degradation" (NT1 E3b): RETRACTED — was an artifact of huge per-worker
  VA pre-reservation; clean E3d shows the budget is CONSERVED and even-split. Honest self-correction.
- Inherited from 511ce2e2 (do not re-propose): B (YELLOW, oracle recovery), E (SW-equivalent), J (not
  HW-attested), I (superseded by T-TAX). See that session's THESES.md.

## RELATIONSHIP TO SESSION 511ce2e2
Same research lineage (forkedkv/edmm; "GPU VMM wrong abstraction for agentic KV branching").
511ce2e2 proved C*/A*/T-TAX (VMM is dominated/has a cliff/collapses). THIS session's NT1 is a
sharper, root-caused + cross-vendor version of A*; NT2/NT3 are NEW (prefix-cache invalidation law +
the one POSITIVE differentiator that survives: kernel-transparent write-after-share). Complementary,
not duplicative.
