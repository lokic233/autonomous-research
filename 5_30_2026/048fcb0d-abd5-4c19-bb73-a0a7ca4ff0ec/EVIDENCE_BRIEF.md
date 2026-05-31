# EVIDENCE BRIEF — the measured digest the committee reasoned from (source of truth)
All numbers from real runs on <GPU-NODE-A> (H100, driver 580.82) + <GPU-NODE-B> (MI350X, ROCm 7.0.2)
unless noted. Every claim cites a data file in this session's data/ or a named prior work.

## NT1 — Mapping-Budget Wall
- E2 cross-vendor (data/ceiling_safe.jsonl): AMD MI350X HIP VMM aliased one 2MiB handle to
  >19,000,000 mappings, ZERO per-call failures, VRAM flat ~1076 MiB (metadata not data), gran 4 KiB.
  NVIDIA H100 hard-fails at K≈523,404 at cuMemSetAccess. AMD also has a host-STABILITY wall far
  higher (node destabilizes ~20-28M live mappings — see /learning/, do not chase exact ceiling).
- E3a root-cause (data/r1.json, r2.json): R1 (1 VA reserve, alias many) → 523,404 maps, OOM at
  cuMemSetAccess. R2 (1 reserve PER map) → 299,949. Control (clean GPU, 1 ctx) → 523,404 EXACT.
  ⇒ K = per-page access-DESCRIPTOR budget at cuMemSetAccess; reserves also draw from it (R2 weight
  ~1.745 units/pair). NOT a reservation count. R1=control deterministic, 0.000% variance.
- E3d per-context vs per-device (data/e3d_results.jsonl): n=1 [523404]; n=2 [260281,263003] tot
  523284; n=3 [171633,174206,177325] tot 523164 ⇒ per-DEVICE budget, CONSERVED (~523,300 ±0.05%),
  even split (~K/n). [CORRECTION: an earlier n=2 run showed 223,215 = artifact of huge per-worker
  pre-reservation; retracted — see committee_traces/E3D_CORRECTION.md.]
- E3c relevance (data/e3c_result.json): under CoW prefix SHARING, HBM is paid once so the mapping
  budget BINDS — max concurrent branches 1039@8k / 259@32k / 64@128k ctx vs 99/24/6 on naive HBM.
  Labeled a MODEL (K=519936 median), not a measurement.

## NT2 — Prefix-Cache Invalidation Law
- vLLM hash mechanism: hash_block_tokens CHAINS parent_block_hash into each fixed-16-token block
  (verbatim in benchmarks/nt2_segmented_hash.py).
- v1 NULL (data/nt2_result.json): de-chained "segmented hash" → 1.0× recompute reduction at every
  injection point (10/25/50/75/90%). FALSIFIED hash-chaining as the cause. The cascade is block-
  BOUNDARY alignment (insertion shifts all downstream fixed blocks).
- v2 CDC (data/nt2v2_result.json): content-defined chunking → recompute 2.0-2.4% regardless of
  injection position vs fixed-block 10.7-90.1% (5.4-45.4×).
- Wall-clock (data/nt2_wallclock.json): real H100 SDPA prefill over the recomputed span, tool@25%:
  8k ctx fixed 0.613ms vs CDC 0.053ms (incl pessimistic 1.5× overhead) = 11.6×; 32k fixed 8.436ms
  vs CDC 0.071ms = 119.6×. Superlinear on the fixed path (13.8× for 4× ctx = O(n²)); CDC ~flat.
- Prior work: Continuum (arXiv 2511.02230) SCHEDULES around tool pauses; NT2 is a cache-DATA-
  STRUCTURE fix. vLLM APC assumes fixed contiguous blocks.

## NT3 — Attention-Visible MMU Write-After-Share
- E1 address-space (data/e1_result.json): 4-page prefix, fork 2 children, childA overwrites shared
  page 2 (write-after-share CoW). ForkedKV branch VA UNCHANGED after CoW; vLLM-APC block-table entry
  MOVES (slot 61→59). Both: only written page diverges, siblings bit-identical. APC needs block-table
  indirection; ForkedKV does not.
- E1b decode-correctness (data/e1b_result.json): real Qwen2.5-7B layer-0 SDPA on the post-CoW branch
  (via its contiguous VA) vs a full-clone reference with the identical edit → sdpa_output bit_identical
  =TRUE, max_abs_diff=0.0, cow_fired=TRUE, kernel_modified=FALSE.
- Prior work: vAttention (arXiv 2405.04437) = contiguous-VA VMM but read-only/per-request/no fork;
  vLLM APC = block-table CoW (non-contiguous after CoW). Neither does kernel-transparent write-after-share.
