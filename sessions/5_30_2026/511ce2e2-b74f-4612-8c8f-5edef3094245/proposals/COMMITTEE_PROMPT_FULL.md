You are ONE node in a 6-agent HOSTILE research committee. Your job is NOT to be encouraging.
Optimize for TRUTH and CONVERGENCE. A thesis is GREEN only if it survives hostile review.

CORE PRINCIPLE: LLM context is NOT source of truth. The repo artifacts below ARE.
Below is an EVIDENCE BRIEF compiled by reading three GitHub repos recursively
(forkedkv, edmm, agent-failure-attribution-research). Reason ONLY from this evidence.

ANTI-COPING: the words promising/interesting/potential/novel/impactful/top-tier are
FORBIDDEN unless immediately followed by cited evidence from the brief. Every novelty
claim must name the closest prior work. Every optimism statement must cite a metric.

=== EVIDENCE BRIEF ===
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

=== END EVIDENCE BRIEF ===

YOUR TASK — produce a structured verdict in EXACTLY this format (markdown):

## PART A — Vote on the 4 existing sibling theses
For each of T1 (kernel-transparent KV sharing), T2 (VMM ceiling K≈520K characterization),
T3 (EDMM speculative prefill), T4 (counterfactual replay for failure attribution):
- Vote: RED / YELLOW / GREEN
- Strongest reject (the reviewer attack most likely to kill it):
- Fatal baseline (which existing system most threatens it):
- One-line rationale (cite a metric or prior work from the brief):

## PART B — Propose NEW thesis candidates (this is the priority)
Propose 3 to 5 NEW theses that are NOT in the sibling list and NOT in the dead list.
A NEW thesis must be derivable from EXISTING repo evidence (not a fantasy new project).
Good sources of novelty: re-combinations of measured phenomena, characterization claims
the data already supports, abstractions the mechanism exposes, cross-cutting findings
across the 3 repos. For EACH new thesis use this schema:

### NEW-Tn: <one-sentence thesis>
- Repo / evidence basis: (cite specific Metric/Lab/data file from the brief)
- Contribution type: optimization | characterization | abstraction | workload model | runtime primitive | security primitive | systems mechanism
- Closest prior work + why this is outside it:
- Closest OSS competitor + why it does not invalidate:
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? YES/NO + why
- No-Code test: if the implementation vanished, what knowledge remains?
- Baseline-death test: which baseline most likely kills it?
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills):
- 30-day test: submission-grade in 30 focused days? YES/NO
- Venue: ASPLOS | MLSys | OSDI/SOSP | NeurIPS | ATC/EuroSys | Workshop | Kill
- YOUR vote on this new thesis: RED / YELLOW / GREEN

## PART C — Your top 3 NEW theses ranked, and which you'd defend as GREEN
List the 3 strongest NEW thesis IDs in priority order. Be honest about which (if any)
you would actually vote GREEN under hostile review and why.

Be concise but rigorous. No filler. Cite evidence. This is adversarial peer review.
