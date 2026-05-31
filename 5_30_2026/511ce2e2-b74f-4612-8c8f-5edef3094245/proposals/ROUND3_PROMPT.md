You are ONE node in a 6-agent HOSTILE research committee (CC4.8, CC4.7, CC4.6, Agent-D,
Codex 5.5, Gemini 3.5). This is the FINAL vote. Two decisive experiments the committee
demanded in round 2 have now been RUN and MEASURED. Vote each thesis RED/YELLOW/GREEN.
GREEN requires the thesis to survive hostile review on the MEASURED evidence — not on
hope. Do NOT vote GREEN to be agreeable; do NOT vote RED out of reflex. Source of truth =
the measured results below + repo artifacts. Optimize for TRUTH.

ANTI-COPING: promising/interesting/novel/impactful/potential/top-tier FORBIDDEN unless
followed by a cited measured number or named prior work.

=== MEASURED RESULT 1 — Cross-vendor VMM mapping ceiling (E2, <committee-workdir>) ===
SAME mapping-ceiling probe run on TWO vendors:
- NVIDIA H100, CUDA 12.8 / driver 580.82.07, 2 MiB granule: HARD CEILING at K≈520,000
  mappings (= branches×prefix_pages, ±1% across {1,3,6,12}GiB prefixes), fails forensically
  at cuMemSetAccess. Independent of vm.max_map_count (392 VMAs used vs 67M available).
- AMD MI350X, ROCm 7.0.2.1 / gfx950, 288GiB HBM, 4 KB granule: mapped 64,000,000
  shared-physical→distinct-VA pages with ZERO driver failure (= 123× NVIDIA's ceiling; this
  is our 244GiB VA-reserve CAP, NOT an AMD driver ceiling — AMD shows NO per-context mapping
  ceiling in the regime where NVIDIA hard-fails).
CONCLUSION: the ~520K ceiling is NVIDIA-DRIVER-SPECIFIC, not a universal GPU-VMM property.
The honest claim is VENDOR DRIVER-ARCHITECTURE DIVERGENCE with portability consequences:
a VMM-based KV/branch/CoW design that scales on AMD hits a hard wall on NVIDIA at 520K.

=== MEASURED RESULT 2 — E-C end-to-end rollback workload (the decisive experiment) ===
Rollback-heavy agentic decode (shared prefix → fork N branches → 48 decode tok/branch with
R shared-page-overwrite CoW rollbacks), run 3 ways on the SAME trace, real Qwen2.5-7B-Instruct
layer 0, 1×H100. Sweep prefix∈{4096,512} × N∈{4,16} × R∈{0,4,16}, 5 reps median.
Arms: hw_vmm_cow (CUDA-VMM CoW + SDPA over contiguous CoW KV — strongest fair HW rep);
sw_prefix (vLLM-APC block-table refcount + identical SDPA math); flashinfer (production paged
kernel, measured at exact shapes + measured bookkeeping, analytically composed).
RESULT — HW-CoW win-region is EMPTY (0/12 cells):
- HW is 1.06×–2.20× SLOWER than software prefix sharing in every cell.
- HW is 41×–152× SLOWER than FlashInfer-paged.
- Closest approach (hypothesis directionally right, never crosses over): long/N=4/R=0 →
  HW 73.07ms vs SW 69.19ms (+5.6%); FI 1.77ms.
- Rollbacks make HW RELATIVELY WORSE (long N=4: HW/SW 1.06×→1.14×→1.30× as R 0→4→16) —
  each rollback = real 2MiB driver CoW remap+sync vs µs software refcount.
- Capacity: both alias ≥64 branches, zero OOM at N≤16. Neither binds. No HW capacity win.
CONCLUSION: even a zero-cost KV mechanism could not close FlashInfer's 40–150× gap. Clean,
measured negative result. (Caveats: single layer for systems metrics; FI arm analytic but
margin 41–152× unaffected; single-GPU/single-driver.)

=== EVIDENCE BRIEF (repo source of truth) ===
__BRIEF__
=== END BRIEF ===

=== THE THESES, RE-STATED ON MEASURED EVIDENCE ===

## A* — "The NVIDIA CUDA-VMM per-context mapping-metadata ceiling (K≈520K) is a vendor-
specific portability cliff for branchable GPU memory, absent on AMD ROCm."
Now backed by TWO-vendor measurement (Result 1). Characterization. Venue: ATC/EuroSys/OSDI.
Contribution = the cross-vendor divergence + the predictive model max_branches≈K/prefix_pages
on NVIDIA + the forensic root-cause (cuMemSetAccess, not VMA sysctl). Anti-FlashInfer: PASS.

## B — "Tool-call mid-prompt injection is a superlinear, cross-engine prefix-cache recompute
pathology: a workload model for agentic serving." (UNCHANGED — no new experiment run for B.)
Measured: vLLM 1.38×→5.41× (4K→32K), SGLang 1.61×→5.24×, 8.21× live. Recovery solution (oracle)
is explicitly OUT of scope; this is the problem-characterization half. Venue: MLSys.

## C* — "When NOT to use hardware GPU CoW for agent KV: an end-to-end negative result and
design-space map." Now backed by Result 2 (measured 0/12 empty win-region) PLUS the repo's
B8 null (178µs/page, 7% data, 3% removable not 47%) and Lab 3b (FlashInfer 5–22%). The
contribution is the MEASURED regime map proving HW VMM CoW is dominated by both software
refcounting (1.06–2.20×) and FlashInfer (41–152×) even in its hypothesised best corner
(long prefix + rollback-heavy + contiguous-VA kernel). Venue: ATC/EuroSys (negative-result).

For EACH of A*, B, C* output EXACTLY:
### <A*|B|C*>
- Vote: RED / YELLOW / GREEN
- Strongest remaining reviewer attack:
- Does the measured evidence resolve your round-2 objection? (yes/no + why)
- Venue you'd bet on:

Then:
### FINAL
- List which of A*/B/C* you vote GREEN. Be explicit. If you would NOT vote GREEN on one,
  state the single remaining experiment or change needed.
- Honesty check: are you voting GREEN on real measured evidence, or hope? Defend it.
