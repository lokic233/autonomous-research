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
# COMMITTEE EVIDENCE BRIEF — <committee-workdir> (isolated workspace)
Source of truth = GitHub repo artifacts read 2026-05-30. NOT chat memory.
Three repos under ~/<committee-workdir>/repos/: forkedkv, edmm, agent-failure-attribution-research.

## REPO 1: forkedkv (HEAD 6befa5d, 29 commits, 2026-05-29 → 05-30)
Title: "Forkable GPU Memory for Replayable Agent Execution"
HW: 1×H100 97GiB, CUDA 12.8, driver 580.82.07. Every claim cites data/*.csv + bench/*.py.
MECHANISM: branch-aware copy-on-write of attention KV pages on the GPU MMU via CUDA VMM
(cuMemCreate/Map/Unmap/RetainAllocationHandle). Fork aliases parent physical HBM pages
(refcounted, zero copy); write to shared page detected in SOFTWARE → driver-level per-page remap.
EVIDENCE (measured, honest, repeatedly self-corrected):
- Metric 3: VMM-paged KV adds −0.1%..+1.1% attn overhead vs contiguous (≈0%). Unmodified
  FlashAttention/SDPA run on forked branch. data/metric3_attn_overhead.csv
- Metric 4/4b: full-clone OOMs at 6 branches (12GiB prefix); CoW reaches 84 before OOM at
  cuMemSetAccess. Ceiling is VA mapping-metadata, NOT data. K = branches×prefix_pages ≈ 520K
  (±1%) across {1,3,6,12}GiB. max_branches ≈ 520,000/prefix_pages. data/metric4b_ceiling.csv
- Lab 1: at OOM, /proc/self/maps=392 VMAs vs vm.max_map_count=67M (0.0006%). Ceiling is
  DRIVER-INTERNAL (cuMemSetAccess), independent of Linux VMA sysctl. data/lab1_vmmap_count.csv
- Metric 5 (24 real SWE-bench-Verified instances): 89.9–90.1% fewer KV bytes, 79.9–80.1%
  lower peak HBM, wall-time≈parity. data/metric5_e2e.csv
- Metric 5b: REAL 28-layer Qwen2.5-7B autoregressive decode, KV on CoW VMM pages. N=8,
  3000-tok unaligned prefix: peak HBM 1120 vs 2016 MiB (−44%), 448 CoW events, bit-identical.
- Metric 5c: tree-of-thought rollback fires CoW exactly once, copies 1 page, siblings uncorrupted.
- CoW cost: ~178µs/page; D2D copy only 13µs (7%). B8 NULL RESULT: scratch-pool only 3% faster
  (R1's "47% removable" RETRACTED). VA-swap CoW 59% faster but breaks contiguous VA.
HONEST RETRACTIONS (this is a strength): R4 retracts "OS-style CoW / page-fault-on-write"
(detection is software, not HW fault). Lab 3b: FlashInfer production baseline CORRECTS Lab 3's
"2.3x SDPA faster" → real delta only 5–22%. Against vLLM-APC software baseline: software is
~700× faster on fork latency, ~6× larger capacity at 32-block prefix. NOT a practical
capacity/speedup win over strong software baseline.
WHAT SURVIVES (per repo's own WRITEUP): (1) forensic characterization of GPU VMM mapping
ceiling K≈520K; (2) physical KV sharing exposed as CONTIGUOUS VA so unmodified attention
kernels run — the one thing software prefix-sharing (which mandates PagedAttention) cannot do.

## REPO 2: edmm (HEAD 640f67c, 10 commits, 2026-05-26 → 05-27)
Title: "EDMM: Execution-Driven Memory Management for Agentic LLM Workloads"
PROBLEM: tool-call response injected mid-prompt breaks prefix-cache hash chain → full KV
recompute. Measured 8.21× TTFT penalty through vLLM 0.6.6 live engine (Qwen2.5-7B, H100).
SOLUTION: CUDA VMM (cuMemMap) remaps physical pages in µs; speculatively pre-compute
anticipated KV during tool-call idle window; pointer swap ~50–58µs vs ~274ms recompute.
EVIDENCE:
- vLLM live: Radix penalty B/A=8.21×; EDMM recovery C/A=1.17×.
- Standalone 16K: penalty 4.18×; recovery 0.96×.
- VMM micro: cuMemMap swap 58µs vs full memcpy+recompute 202µs.
- P1.3 penalty scaling: vLLM 1.38×(4K)→5.41×(32K); SGLang 1.61×→5.24×. Superlinear, both engines.
- P0.1/0.2/0.5 PROVEN: 28 KV layers VMM-backed; attention visibility via remap; token determinism.
CAVEAT (ARTIFACT_STATUS): B4 recovery is an ORACLE upper bound — injects precomputed block
hashes; assumes runtime can PREDICT contaminated prompt token sequence during idle window.
V1 fork not validated live (IPC deadlock on multi-tenant H100). Real speculation hit-rate unproven.

## REPO 3: agent-failure-attribution-research (HEAD 2241c68, 2 commits)
A multi-agent committee FRAMEWORK + transcripts (not a built system). 9 reviewer personas,
3-tier fallback, public-source citation verification (≥2 of S2/OpenAlex/arXiv/GitHub = kill).
Phase 11 fresh-direction backtest: IDEA_RF_4 "AgentTraceStore — trace-specialized storage
format with columnar layout" reached GREEN (codex→claude). Others YELLOW (Decoder Telemetry
Sidechannel, OpinionShift cross-boundary inconsistency, PromptDelta static taint, Trajectory
Specialization JIT). ASPLOS debate: 4-way consensus that forkedkv's GPU-state CoW is strongest
ASPLOS framing, 35–45% accept prob with HW data. Strongest attack: "vAttention(ASPLOS'25)+
ChunkAttention(ASPLOS'24) already did VMM KV; remove agent motivation and nothing
architectural remains." Cross-domain CoW policy (KV+RNG+tool-logs+retrieval, heterogeneous
page granularity) named as the genuinely-new architectural angle.

## PRIOR-WORK BOUNDARY (known threats)
- vAttention (arXiv 2405.04437, ASPLOS'25): CUDA VMM for KV, contiguous VA, unmodified kernel —
  but READ-ONLY sharing, no fork/CoW.
- ChunkAttention (ASPLOS'24): chunked shared-prefix, no write-after-fork path.
- vLLM PagedAttention (SOSP'23), SGLang RadixAttention (NeurIPS'24): SOFTWARE refcounted sharing.
- FlashInfer: production paged-attention kernels.
- CXLfork (ASPLOS'25): CXL-mediated fork, CPU-only.
- Continuum / LMCache: closing the speculative-prefill / KV-offload window (months).

## SIBLING-COMMITTEE PRIOR THESES (do NOT re-propose these as "new"):
T1 kernel-transparent physical KV sharing (YELLOW, thin vs vAttention);
T2 VMM mapping-ceiling K≈520K characterization (YELLOW, "section not paper");
T3 EDMM speculative prefill (YELLOW/RED-risk, recovery is oracle);
T4 counterfactual replay for failure attribution (YELLOW, unbuilt).
Dead: kernel-speedup, capacity-headline, OS-CoW framing, scratch-pool, checkpoint-protocol,
agent-CI-cache, EDMM-mechanism-novelty.

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
