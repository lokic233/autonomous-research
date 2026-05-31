You are ONE node in a 6-agent HOSTILE research committee (CC4.8, CC4.7, CC4.6, Agent-D,
Codex 5.5, Gemini 3.5). Round 1 (independent free generation) is complete. All 6 of you,
generating independently, CONVERGED onto the same small set of theses. Below are the 3
most-converged candidates, RE-SHARPENED to survive their round-1 kill-shots. Your job now:
vote each RED/YELLOW/GREEN under hostile review. Optimize for TRUTH, not consensus theater.
Do NOT vote GREEN to be agreeable. Source of truth = the repo evidence, not this prompt.

ANTI-COPING: promising/interesting/novel/impactful/potential/top-tier are FORBIDDEN unless
followed by a cited metric or named prior work.

=== EVIDENCE (from repos read 2026-05-30) ===
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

=== END EVIDENCE ===

=== THE 3 CONVERGED + SHARPENED THESES ===

## GREEN-CANDIDATE-A — "The GPU VMM mapping-metadata ceiling: a structural, driver-internal
limit on fine-grained branchable GPU memory."
Claim: For any CUDA/HIP VMM scheme that maps shared physical pages into many virtual
addresses (the CoW/branch case), the scaling limit is NOT HBM capacity and NOT the Linux
VMA sysctl — it is a per-context driver mapping-metadata ceiling. On H100/CUDA-12.8 this is
K = branches × prefix_pages ≈ 520K (±1%, Metric 4b, 4 prefix sizes), failing forensically at
cuMemSetAccess (Lab 1: 392 VMAs vs vm.max_map_count=67M, 0.0006% used). Contribution:
characterization + the predictive model max_branches ≈ K/prefix_pages.
SHARPENING vs round-1 "single-driver/section-not-paper" kill: the committee is ACQUIRING
cross-vendor data — the SAME probe is being run on an AMD MI350X (gfx950, ROCm/HIP) right now.
If a finite driver-internal ceiling reproduces on a SECOND vendor, the claim upgrades from
"NVIDIA quirk" to "structural property of GPU VMM as currently designed." Vote on the thesis
CONDITIONAL on that cross-vendor result landing (state your vote for both outcomes).
Venue if cross-vendor holds: OSDI/ATC. Anti-FlashInfer: PASS. No-Code: PASS.

## GREEN-CANDIDATE-B — "Tool-call mid-prompt injection is a superlinear, cross-engine
prefix-cache recompute pathology: a workload model for agentic serving."
Claim: Injecting a tool result mid-prompt breaks the prefix-cache hash chain and forces
recompute whose penalty grows SUPERLINEARLY with context and reproduces across two
independent production engines: vLLM 1.38×(4K)→5.41×(32K), SGLang 1.61×→5.24×; 8.21× live
through vLLM 0.6.6 at realistic context. This is a measured workload property, decoupled
entirely from EDMM's (oracle) recovery solution. Contribution: workload model + measurement.
SHARPENING vs round-1 "cache invalidation is known" kill: the contribution is not "invalidation
exists" — it is the SUPERLINEAR EXPONENT, its reproduction across two engines, and a model
predicting penalty from injection POSITION (not just length). No cited prior work
(SGLang/Continuum/LMCache) quantifies this curve. Venue: MLSys. Anti-FlashInfer: PASS.

## GREEN-CANDIDATE-C — "When NOT to use hardware GPU CoW: a design-space decomposition and
honest negative result."
Claim: GPU VMM CoW is decomposed: a single 2MiB-page CoW = 178µs, of which only 13µs (7%) is
the unavoidable D2D copy; 93% is driver mapping work (cuMemSetAccess ~50µs + cuMemUnmap ~30µs).
The B8 NULL RESULT refutes the project's own R1 "47% removable via scratch-pool" claim
(measured: only 3% removable). Against a vLLM-APC software baseline, HW VMM CoW is ~700× slower
on fork latency and ~6× smaller capacity at a 32-block prefix. CONTRIBUTION = the regime map:
HW VMM CoW is net-positive ONLY when [long shared prefix AND an unmodified contiguous-VA kernel
is required]; otherwise software refcounting dominates. Contribution: characterization +
negative result. SHARPENING vs round-1 "anti-FlashInfer collapses the win-region" kill: state
explicitly whether the win-region is non-empty once a production paged kernel (FlashInfer,
5–22% gap per Lab 3b) is the baseline. Venue: ATC/EuroSys (negative-result friendly).



=== LIVE CROSS-VENDOR RESULT (just measured on AMD MI350X gfx950, ROCm/HIP) ===
The SAME mapping-ceiling probe was run on AMD MI350X. RESULT: AMD does NOT reproduce the
K≈520K ceiling. AMD VMM granularity is 4KB (vs NVIDIA 2MB) and the probe mapped 4,000,000
shared-physical→distinct-VA pages with ZERO driver failure (hit our safety cap, not a real
ceiling; a higher-cap re-run is in flight). IMPLICATION: the 520K ceiling is NVIDIA-driver-
SPECIFIC, not a universal GPU-VMM property. This CHANGES Thesis A: the honest claim is no
longer 'structural limit of GPU VMM' but 'vendor driver-architecture DIVERGENCE — NVIDIA
enforces a low per-context mapping-metadata ceiling (520K) that AMD does not, which is itself
a characterization result with portability consequences for any VMM-based KV/branch system.'
Vote A on THIS corrected framing, not the original.
=== END LIVE RESULT ===

=== END THESES ===

For EACH of A, B, C output EXACTLY:
### <A|B|C>
- Vote: RED / YELLOW / GREEN  (if conditional on the cross-vendor result, give BOTH:
  "GREEN if AMD reproduces / YELLOW if not")
- The single strongest remaining reviewer attack:
- What evidence would flip your vote to GREEN (be specific and falsifiable):
- Venue you'd actually bet on:

Then:
### FINAL
- Which of A/B/C do you vote GREEN today (list), and which are conditional-GREEN and on what.
- If you vote nothing GREEN, say so plainly and state the ONE experiment that would change it.
Be brutal and concrete. Cite evidence.
