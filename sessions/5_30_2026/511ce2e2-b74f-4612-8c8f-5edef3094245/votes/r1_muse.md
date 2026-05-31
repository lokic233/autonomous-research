67 skills discovered
## PART A — Vote on the 4 existing sibling theses

**T1: kernel-transparent physical KV sharing**
- Vote: **YELLOW**
- Strongest reject: vAttention (ASPLOS'25) already exposes contiguous VA via CUDA VMM for unmodified kernels; adding CoW is incremental and measured fork latency is ~700× slower than vLLM-APC software baseline, so kernel-transparency alone is not a practical win.
- Fatal baseline: **vAttention (arXiv 2405.04437, ASPLOS'25)** — read-only VMM KV with contiguous VA; **vLLM-APC software prefix sharing** — ~700× faster fork, ~6× larger capacity at 32-block prefix.
- One-line rationale: Metric 3 shows −0.1%..+1.1% attn overhead for VMM-paged KV (data/metric3_attn_overhead.csv) but honest retraction notes software baseline beats CoW on latency and capacity, making the “transparent” claim thin vs vAttention.

**T2: VMM mapping-ceiling K≈520K characterization**
- Vote: **YELLOW**
- Strongest reject: Empirical driver limit on one CUDA version/GPU is a measurement artifact, not a systems mechanism; it describes NVIDIA’s cuMemSetAccess implementation rather than a general architectural principle.
- Fatal baseline: **NVIDIA driver documentation / simple microbenchmark** — K is not documented but can be rediscovered trivially; no system is built on the invariant.
- One-line rationale: Metric 4b shows K = branches×prefix_pages ≈ 520K (±1%) across {1,3,6,12}GiB (data/metric4b_ceiling.csv) and Lab 1 proves ceiling is driver-internal, not Linux VMA (data/lab1_vmmap_count.csv), but this is a “section not paper” characterization.

**T3: EDMM speculative prefill**
- Vote: **RED**
- Strongest reject: B4 recovery is an ORACLE upper bound that injects precomputed block hashes and assumes the runtime can predict the contaminated prompt token sequence during the idle window; V1 fork was never validated live (IPC deadlock), so real hit-rate is unproven.
- Fatal baseline: **vLLM 0.6.6 / SGLang RadixAttention** — both already measure prefix-cache penalty; EDMM adds an unvalidated speculation assumption.
- One-line rationale: ARTIFACT_STATUS states recovery is oracle and “real speculation hit-rate unproven,” while measured penalty is 8.21× (vLLM live) but recovery 1.17× depends on perfect prediction.

**T4: counterfactual replay for failure attribution**
- Vote: **RED**
- Strongest reject: Repo 3 is a multi-agent committee framework with transcripts, not a built system; no implementation, no metrics, no evidence that replay is feasible or that traces can be collected at scale.
- Fatal baseline: **Existing tracing/logging (e.g., AgentTraceStore IDEA_RF_4)** — the only GREEN artifact from Phase 11 is a storage format, not a replay mechanism.
- One-line rationale: agent-failure-attribution-research HEAD 2241c68 contains 9 reviewer personas and transcripts but zero built code; T4 is unbuilt and therefore YELLOW at best, RED under hostile review.

## PART B — Propose NEW thesis candidates

### NEW-T1: Cross-domain heterogeneous CoW policy for agent state (KV + RNG + tool logs + retrieval) with page-granularity specialization
- Repo / evidence basis: forkedkv Metric 5c (tree-of-thought rollback fires CoW exactly once, copies 1 page, siblings uncorrupted); EDMM problem statement (tool-call breaks prefix-cache hash chain, 8.21× penalty); repo 3 ASPLOS debate names “Cross-domain CoW policy (KV+RNG+tool-logs+retrieval, heterogeneous page granularity)” as the genuinely-new architectural angle.
- Contribution type: abstraction | systems mechanism
- Closest prior work + why this is outside it: vAttention (ASPLOS'25) provides VMM-backed contiguous VA for KV but read-only sharing, no fork/CoW, and no RNG/tool state; CXLfork (ASPLOS'25) does CXL-mediated fork but CPU-only and homogeneous. This thesis extends GPU VMM CoW to heterogeneous agent state with differing page sizes and consistency requirements.
- Closest OSS competitor + why it does not invalidate: vLLM-APC / SGLang RadixAttention — software refcounted prefix sharing mandates PagedAttention kernels and does not handle RNG/tool-log divergence; they cannot provide contiguous VA for unmodified kernels nor cross-domain atomic fork.
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? **YES** — FlashInfer speed does not address state divergence across KV, RNG, and tool logs; the bottleneck is correctness and memory management of heterogeneous state, not attention throughput.
- No-Code test: if the implementation vanished, what knowledge remains? GPU VMM can expose contiguous VA for forked heterogeneous state; driver mapping limit K≈520K bounds fan-out; CoW granularity must match domain (e.g., 1 page for KV, smaller for RNG); software detection (not HW fault) is the CoW trigger.
- Baseline-death test: which baseline most likely kills it? vAttention extended with CoW + software checkpointing for RNG/logs — if vAttention adds write-after-fork and composes with existing logging, the cross-domain novelty collapses.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: RNG state CoW alongside KV CoW adds <200µs per fork on H100. Cost: 2 engineer-weeks to instrument CUDA RNG state and tool-log buffer. Min success: 100 forks, median overhead <200µs, bit-identical replay. What it kills: If overhead >1ms or state corruption occurs, the heterogeneous policy is impractical.
- 30-day test: submission-grade in 30 focused days? **NO** — requires RNG/tool integration, correctness proofs, and multi-domain evaluation; >30 days.
- Venue: ASPLOS | MLSys | OSDI/SOSP | NeurIPS | ATC/EuroSys | Workshop | Kill → **Workshop** (unbuilt) or **ASPLOS** (if built)
- YOUR vote on this new thesis: **YELLOW**

### NEW-T2: VA mapping metadata, not HBM capacity or Linux VMA count, is the fundamental scalability limit for fine-grained GPU CoW, with invariant K≈520K mappings on H100 CUDA 12.8
- Repo / evidence basis: forkedkv Metric 4/4b (full-clone OOMs at 6 branches; CoW reaches 84 before OOM at cuMemSetAccess; K≈520K across {1,3,6,12}GiB; data/metric4b_ceiling.csv); Lab 1 (/proc/self/maps=392 VMAs vs vm.max_map_count=67M (0.0006%); ceiling is driver-internal, data/lab1_vmmap_count.csv).
- Contribution type: characterization
- Closest prior work + why this is outside it: vAttention (ASPLOS'25) uses CUDA VMM for KV but does not characterize or model the mapping limit; NVIDIA documentation does not publish K. This thesis provides the first empirical invariant and a predictive model max_branches ≈ 520,000/prefix_pages.
- Closest OSS competitor + why it does not invalidate: vLLM / SGLang — do not use VMM, so they are not subject to K; they cannot invalidate a VMM-specific limit.
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? **YES** — K limits mapping count, independent of attention kernel speed; FlashInfer does not affect cuMemSetAccess.
- No-Code test: if the implementation vanished, what knowledge remains? On H100 with CUDA 12.8 driver 580.82.07, cuMemSetAccess fails after ~520K VA mappings regardless of prefix size; Linux VMA count is irrelevant; this defines a hard fan-out budget for fine-grained CoW.
- Baseline-death test: which baseline most likely kills it? NVIDIA driver update raising K or documenting it as a tunable — if K is version-specific or configurable, the invariant is not general.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: K is stable ±5% across H100s and CUDA 12.8 patch versions. Cost: 1 week to sweep 3 H100s, 2 driver versions. Min success: K = 515K–525K on all runs. What it kills: If K varies >10% or scales with GPU memory, the invariant is not fundamental.
- 30-day test: submission-grade in 30 focused days? **YES** — measurement study with model and validation.
- Venue: ASPLOS | MLSys | OSDI/SOSP | NeurIPS | ATC/EuroSys | Workshop | Kill → **MLSys** (characterization) or **Workshop**
- YOUR vote on this new thesis: **YELLOW**

### NEW-T3: Software CoW detection dominates GPU CoW latency (178µs/page total, D2D copy 13µs (7%)); scratch-pool optimization yields only 3% gain, refuting prior 47% claim
- Repo / evidence basis: forkedkv “CoW cost: ~178µs/page; D2D copy only 13µs (7%). B8 NULL RESULT: scratch-pool only 3% faster (R1's '47% removable' RETRACTED).”
- Contribution type: characterization | workload model
- Closest prior work + why this is outside it: OS CoW studies (CPU page faults) and GPU VMM papers (vAttention, ChunkAttention) measure mapping cost but do not break down software detection vs D2D copy vs VA manipulation; none report the retraction of a 47% optimization claim.
- Closest OSS competitor + why it does not invalidate: vLLM-APC — uses software refcounting, no CoW, so it does not measure CoW path; cannot invalidate the breakdown.
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? **YES** — the cost is in memory management (cuMemMap/Unmap/SetAccess + software detection), not attention; FlashInfer speed is orthogonal.
- No-Code test: if the implementation vanished, what knowledge remains? For GPU VMM CoW, VA manipulation and software write-detection dominate latency; D2D bandwidth is not the bottleneck; scratch-pool caching of VA mappings is ineffective (3% not 47%).
- Baseline-death test: which baseline most likely kills it? Faster CUDA VMM API (e.g., batched cuMemSetAccess) reducing map/unmap latency below 20µs — if NVIDIA optimizes the API, the bottleneck shifts.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: cuMemSetAccess accounts for >50% of 178µs. Cost: 3 days to profile cuMemMap, cuMemUnmap, cuMemSetAccess individually with Nsight. Min success: SetAccess >90µs. What it kills: If D2D copy >50µs, the bandwidth claim is false.
- 30-day test: submission-grade in 30 focused days? **YES** — profiling, retraction, and model fit in 30 days.
- Venue: ASPLOS | MLSys | OSDI/SOSP | NeurIPS | ATC/EuroSys | Workshop | Kill → **ATC/EuroSys** (systems) or **MLSys**
- YOUR vote on this new thesis: **GREEN**

### NEW-T4: Unmodified FlashAttention/SDPA execute correctly on VMM-forked KV with bit-identical outputs across 448 CoW events, proving contiguous VA abstraction sufficient for kernel transparency
- Repo / evidence basis: forkedkv Metric 3 (VMM-paged KV adds −0.1%..+1.1% attn overhead vs contiguous, unmodified FlashAttention/SDPA run on forked branch, data/metric3_attn_overhead.csv); Metric 5b (REAL 28-layer Qwen2.5-7B autoregressive decode, KV on CoW VMM pages, N=8, 3000-tok unaligned prefix: peak HBM 1120 vs 2016 MiB (−44%), 448 CoW events, bit-identical).
- Contribution type: abstraction | runtime primitive
- Closest prior work + why this is outside it: vAttention (ASPLOS'25) provides contiguous VA for read-only KV sharing; this thesis demonstrates CoW (write-after-fork) with bit-identical correctness across hundreds of events, which vAttention does not support.
- Closest OSS competitor + why it does not invalidate: vLLM PagedAttention / FlashInfer — require kernel rewrite to handle non-contiguous pages; they do not provide contiguous VA for unmodified kernels, so they cannot invalidate the transparency claim.
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? **NO** — if FlashInfer were infinitely fast and universally adopted, the need for unmodified kernels diminishes; however, the abstraction still matters for kernels without PagedAttention support. (Partial NO)
- No-Code test: if the implementation vanished, what knowledge remains? CUDA VMM can expose forked KV as contiguous VA; unmodified FlashAttention/SDPA produce bit-identical outputs vs full clone; CoW events do not corrupt sibling branches.
- Baseline-death test: which baseline most likely kills it? vAttention adding CoW support — if vAttention extends to write-after-fork, the novelty collapses to an incremental extension.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: 24 SWE-bench-Verified instances run bit-identical with <2% overhead using unmodified FlashAttention. Cost: 1 week to run full suite. Min success: 100% bit-identical, mean overhead <2%. What it kills: If any divergence or overhead >5%, kernel transparency is broken.
- 30-day test: submission-grade in 30 focused days? **YES** — validation exists (Metric 5, 5b), needs paper writing.
- Venue: ASPLOS | MLSys | OSDI/SOSP | NeurIPS | ATC/EuroSys | Workshop | Kill → **MLSys** or **Workshop**
- YOUR vote on this new thesis: **YELLOW**

### NEW-T5: Tool-call prefix contamination penalty scales superlinearly with context length (1.38× at 4K to 5.41× at 32K vLLM, 1.61× to 5.24× SGLang), and VMM remap recovers to 0.96–1.17× without recompute
- Repo / evidence basis: EDMM P1.3 penalty scaling (vLLM 1.38×(4K)→5.41×(32K); SGLang 1.61×→5.24×. Superlinear, both engines); vLLM live: Radix penalty B/A=8.21×; EDMM recovery C/A=1.17×; Standalone 16K: penalty 4.18×; recovery 0.96×; VMM micro: cuMemMap swap 58µs vs full memcpy+recompute 202µs.
- Contribution type: workload model | characterization
- Closest prior work + why this is outside it: vLLM (SOSP'23) and SGLang (NeurIPS'24) measure prefix-cache hit rate but do not quantify contamination penalty from mid-prompt tool-call injection nor its superlinear scaling; EDMM is first to measure it.
- Closest OSS competitor + why it does not invalidate: vLLM / SGLang — they exhibit the penalty but do not provide recovery; their existence confirms the problem but not the solution.
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? **YES** — penalty is KV cache invalidation and recompute, not attention speed; even infinitely fast attention still pays the recompute cost if KV is discarded.
- No-Code test: if the implementation vanished, what knowledge remains? Mid-prompt tool-call injection breaks RadixAttention hash chain, causing superlinear TTFT penalty; VMM remap can recover to near-baseline (0.96–1.17×) if the correct KV is available; recovery is an oracle upper bound (prediction unproven).
- Baseline-death test: which baseline most likely kills it? Engine-level prefix repair (e.g., SGLang or vLLM adding native contamination recovery) — if engines fix the hash chain without VMM, the characterization is still valid but the mechanism is moot.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: >20% of real-world agent tool calls cause >2× TTFT penalty. Cost: 2 weeks to collect traces from 3 agent workloads. Min success: ≥20% of calls meet threshold. What it kills: If <5%, the problem is rare and not worth optimizing.
- 30-day test: submission-grade in 30 focused days? **YES** — data exists (P1.3, live), needs trace analysis.
- Venue: ASPLOS | MLSys | OSDI/SOSP | NeurIPS | ATC/EuroSys | Workshop | Kill → **MLSys** or **ATC/EuroSys**
- YOUR vote on this new thesis: **YELLOW**

## PART C — Your top 3 NEW theses ranked, and which you'd defend as GREEN

**Ranked:**
1. **NEW-T3** — Software CoW detection dominates GPU CoW latency; scratch-pool 3% not 47%
2. **NEW-T2** — VA mapping metadata K≈520K is the fundamental limit, not HBM or Linux VMA
3. **NEW-T1** — Cross-domain heterogeneous CoW policy for agent state

**Defend as GREEN:**
- **NEW-T3 only.** It survives hostile review because it is a measured, honest retraction with a full cost breakdown (178µs/page, 13µs D2D 7%) and a null result that refutes the authors’ own prior 47% claim. The evidence is in the repo (B8 NULL RESULT), the methodology is profiling (3-day EV experiment), and the conclusion (VA manipulation, not bandwidth, dominates) is falsifiable and useful for future GPU VMM work. It does not rely on unbuilt mechanisms, oracle assumptions, or version-specific invariants beyond the measured stack. The other two are YELLOW: T2 is a solid characterization but risks being dismissed as a “section not paper” driver quirk; T1 is architecturally interesting (and named by the ASPLOS debate as genuinely new) but unbuilt, making it vulnerable to the “no implementation” kill shot.
## PART A — Vote on the 4 existing sibling theses

**T1: kernel-transparent physical KV sharing**
- Vote: **YELLOW**
- Strongest reject: vAttention (ASPLOS'25) already exposes contiguous VA via CUDA VMM for unmodified kernels; adding CoW is incremental and measured fork latency is ~700× slower than vLLM-APC software baseline, so kernel-transparency alone is not a practical win.
- Fatal baseline: **vAttention (arXiv 2405.04437, ASPLOS'25)** — read-only VMM KV with contiguous VA; **vLLM-APC software prefix sharing** — ~700× faster fork, ~6× larger capacity at 32-block prefix.
- One-line rationale: Metric 3 shows −0.1%..+1.1% attn overhead for VMM-paged KV (data/metric3_attn_overhead.csv) but honest retraction notes software baseline beats CoW on latency and capacity, making the “transparent” claim thin vs vAttention.

**T2: VMM mapping-ceiling K≈520K characterization**
- Vote: **YELLOW**
- Strongest reject: Empirical driver limit on one CUDA version/GPU is a measurement artifact, not a systems mechanism; it describes NVIDIA’s cuMemSetAccess implementation rather than a general architectural principle.
- Fatal baseline: **NVIDIA driver documentation / simple microbenchmark** — K is not documented but can be rediscovered trivially; no system is built on the invariant.
- One-line rationale: Metric 4b shows K = branches×prefix_pages ≈ 520K (±1%) across {1,3,6,12}GiB (data/metric4b_ceiling.csv) and Lab 1 proves ceiling is driver-internal, not Linux VMA (data/lab1_vmmap_count.csv), but this is a “section not paper” characterization.

**T3: EDMM speculative prefill**
- Vote: **RED**
- Strongest reject: B4 recovery is an ORACLE upper bound that injects precomputed block hashes and assumes the runtime can predict the contaminated prompt token sequence during the idle window; V1 fork was never validated live (IPC deadlock), so real hit-rate is unproven.
- Fatal baseline: **vLLM 0.6.6 / SGLang RadixAttention** — both already measure prefix-cache penalty; EDMM adds an unvalidated speculation assumption.
- One-line rationale: ARTIFACT_STATUS states recovery is oracle and “real speculation hit-rate unproven,” while measured penalty is 8.21× (vLLM live) but recovery 1.17× depends on perfect prediction.

**T4: counterfactual replay for failure attribution**
- Vote: **RED**
- Strongest reject: Repo 3 is a multi-agent committee framework with transcripts, not a built system; no implementation, no metrics, no evidence that replay is feasible or that traces can be collected at scale.
- Fatal baseline: **Existing tracing/logging (e.g., AgentTraceStore IDEA_RF_4)** — the only GREEN artifact from Phase 11 is a storage format, not a replay mechanism.
- One-line rationale: agent-failure-attribution-research HEAD 2241c68 contains 9 reviewer personas and transcripts but zero built code; T4 is unbuilt and therefore YELLOW at best, RED under hostile review.

## PART B — Propose NEW thesis candidates

### NEW-T1: Cross-domain heterogeneous CoW policy for agent state (KV + RNG + tool logs + retrieval) with page-granularity specialization
- Repo / evidence basis: forkedkv Metric 5c (tree-of-thought rollback fires CoW exactly once, copies 1 page, siblings uncorrupted); EDMM problem statement (tool-call breaks prefix-cache hash chain, 8.21× penalty); repo 3 ASPLOS debate names “Cross-domain CoW policy (KV+RNG+tool-logs+retrieval, heterogeneous page granularity)” as the genuinely-new architectural angle.
- Contribution type: abstraction | systems mechanism
- Closest prior work + why this is outside it: vAttention (ASPLOS'25) provides VMM-backed contiguous VA for KV but read-only sharing, no fork/CoW, and no RNG/tool state; CXLfork (ASPLOS'25) does CXL-mediated fork but CPU-only and homogeneous. This thesis extends GPU VMM CoW to heterogeneous agent state with differing page sizes and consistency requirements.
- Closest OSS competitor + why it does not invalidate: vLLM-APC / SGLang RadixAttention — software refcounted prefix sharing mandates PagedAttention kernels and does not handle RNG/tool-log divergence; they cannot provide contiguous VA for unmodified kernels nor cross-domain atomic fork.
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? **YES** — FlashInfer speed does not address state divergence across KV, RNG, and tool logs; the bottleneck is correctness and memory management of heterogeneous state, not attention throughput.
- No-Code test: if the implementation vanished, what knowledge remains? GPU VMM can expose contiguous VA for forked heterogeneous state; driver mapping limit K≈520K bounds fan-out; CoW granularity must match domain (e.g., 1 page for KV, smaller for RNG); software detection (not HW fault) is the CoW trigger.
- Baseline-death test: which baseline most likely kills it? vAttention extended with CoW + software checkpointing for RNG/logs — if vAttention adds write-after-fork and composes with existing logging, the cross-domain novelty collapses.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: RNG state CoW alongside KV CoW adds <200µs per fork on H100. Cost: 2 engineer-weeks to instrument CUDA RNG state and tool-log buffer. Min success: 100 forks, median overhead <200µs, bit-identical replay. What it kills: If overhead >1ms or state corruption occurs, the heterogeneous policy is impractical.
- 30-day test: submission-grade in 30 focused days? **NO** — requires RNG/tool integration, correctness proofs, and multi-domain evaluation; >30 days.
- Venue: ASPLOS | MLSys | OSDI/SOSP | NeurIPS | ATC/EuroSys | Workshop | Kill → **Workshop** (unbuilt) or **ASPLOS** (if built)
- YOUR vote on this new thesis: **YELLOW**

### NEW-T2: VA mapping metadata, not HBM capacity or Linux VMA count, is the fundamental scalability limit for fine-grained GPU CoW, with invariant K≈520K mappings on H100 CUDA 12.8
- Repo / evidence basis: forkedkv Metric 4/4b (full-clone OOMs at 6 branches; CoW reaches 84 before OOM at cuMemSetAccess; K≈520K across {1,3,6,12}GiB; data/metric4b_ceiling.csv); Lab 1 (/proc/self/maps=392 VMAs vs vm.max_map_count=67M (0.0006%); ceiling is driver-internal, data/lab1_vmmap_count.csv).
- Contribution type: characterization
- Closest prior work + why this is outside it: vAttention (ASPLOS'25) uses CUDA VMM for KV but does not characterize or model the mapping limit; NVIDIA documentation does not publish K. This thesis provides the first empirical invariant and a predictive model max_branches ≈ 520,000/prefix_pages.
- Closest OSS competitor + why it does not invalidate: vLLM / SGLang — do not use VMM, so they are not subject to K; they cannot invalidate a VMM-specific limit.
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? **YES** — K limits mapping count, independent of attention kernel speed; FlashInfer does not affect cuMemSetAccess.
- No-Code test: if the implementation vanished, what knowledge remains? On H100 with CUDA 12.8 driver 580.82.07, cuMemSetAccess fails after ~520K VA mappings regardless of prefix size; Linux VMA count is irrelevant; this defines a hard fan-out budget for fine-grained CoW.
- Baseline-death test: which baseline most likely kills it? NVIDIA driver update raising K or documenting it as a tunable — if K is version-specific or configurable, the invariant is not general.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: K is stable ±5% across H100s and CUDA 12.8 patch versions. Cost: 1 week to sweep 3 H100s, 2 driver versions. Min success: K = 515K–525K on all runs. What it kills: If K varies >10% or scales with GPU memory, the invariant is not fundamental.
- 30-day test: submission-grade in 30 focused days? **YES** — measurement study with model and validation.
- Venue: ASPLOS | MLSys | OSDI/SOSP | NeurIPS | ATC/EuroSys | Workshop | Kill → **MLSys** (characterization) or **Workshop**
- YOUR vote on this new thesis: **YELLOW**

### NEW-T3: Software CoW detection dominates GPU CoW latency (178µs/page total, D2D copy 13µs (7%)); scratch-pool optimization yields only 3% gain, refuting prior 47% claim
- Repo / evidence basis: forkedkv “CoW cost: ~178µs/page; D2D copy only 13µs (7%). B8 NULL RESULT: scratch-pool only 3% faster (R1's '47% removable' RETRACTED).”
- Contribution type: characterization | workload model
- Closest prior work + why this is outside it: OS CoW studies (CPU page faults) and GPU VMM papers (vAttention, ChunkAttention) measure mapping cost but do not break down software detection vs D2D copy vs VA manipulation; none report the retraction of a 47% optimization claim.
- Closest OSS competitor + why it does not invalidate: vLLM-APC — uses software refcounting, no CoW, so it does not measure CoW path; cannot invalidate the breakdown.
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? **YES** — the cost is in memory management (cuMemMap/Unmap/SetAccess + software detection), not attention; FlashInfer speed is orthogonal.
- No-Code test: if the implementation vanished, what knowledge remains? For GPU VMM CoW, VA manipulation and software write-detection dominate latency; D2D bandwidth is not the bottleneck; scratch-pool caching of VA mappings is ineffective (3% not 47%).
- Baseline-death test: which baseline most likely kills it? Faster CUDA VMM API (e.g., batched cuMemSetAccess) reducing map/unmap latency below 20µs — if NVIDIA optimizes the API, the bottleneck shifts.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: cuMemSetAccess accounts for >50% of 178µs. Cost: 3 days to profile cuMemMap, cuMemUnmap, cuMemSetAccess individually with Nsight. Min success: SetAccess >90µs. What it kills: If D2D copy >50µs, the bandwidth claim is false.
- 30-day test: submission-grade in 30 focused days? **YES** — profiling, retraction, and model fit in 30 days.
- Venue: ASPLOS | MLSys | OSDI/SOSP | NeurIPS | ATC/EuroSys | Workshop | Kill → **ATC/EuroSys** (systems) or **MLSys**
- YOUR vote on this new thesis: **GREEN**

### NEW-T4: Unmodified FlashAttention/SDPA execute correctly on VMM-forked KV with bit-identical outputs across 448 CoW events, proving contiguous VA abstraction sufficient for kernel transparency
- Repo / evidence basis: forkedkv Metric 3 (VMM-paged KV adds −0.1%..+1.1% attn overhead vs contiguous, unmodified FlashAttention/SDPA run on forked branch, data/metric3_attn_overhead.csv); Metric 5b (REAL 28-layer Qwen2.5-7B autoregressive decode, KV on CoW VMM pages, N=8, 3000-tok unaligned prefix: peak HBM 1120 vs 2016 MiB (−44%), 448 CoW events, bit-identical).
- Contribution type: abstraction | runtime primitive
- Closest prior work + why this is outside it: vAttention (ASPLOS'25) provides contiguous VA for read-only KV sharing; this thesis demonstrates CoW (write-after-fork) with bit-identical correctness across hundreds of events, which vAttention does not support.
- Closest OSS competitor + why it does not invalidate: vLLM PagedAttention / FlashInfer — require kernel rewrite to handle non-contiguous pages; they do not provide contiguous VA for unmodified kernels, so they cannot invalidate the transparency claim.
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? **NO** — if FlashInfer were infinitely fast and universally adopted, the need for unmodified kernels diminishes; however, the abstraction still matters for kernels without PagedAttention support. (Partial NO)
- No-Code test: if the implementation vanished, what knowledge remains? CUDA VMM can expose forked KV as contiguous VA; unmodified FlashAttention/SDPA produce bit-identical outputs vs full clone; CoW events do not corrupt sibling branches.
- Baseline-death test: which baseline most likely kills it? vAttention adding CoW support — if vAttention extends to write-after-fork, the novelty collapses to an incremental extension.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: 24 SWE-bench-Verified instances run bit-identical with <2% overhead using unmodified FlashAttention. Cost: 1 week to run full suite. Min success: 100% bit-identical, mean overhead <2%. What it kills: If any divergence or overhead >5%, kernel transparency is broken.
- 30-day test: submission-grade in 30 focused days? **YES** — validation exists (Metric 5, 5b), needs paper writing.
- Venue: ASPLOS | MLSys | OSDI/SOSP | NeurIPS | ATC/EuroSys | Workshop | Kill → **MLSys** or **Workshop**
- YOUR vote on this new thesis: **YELLOW**

### NEW-T5: Tool-call prefix contamination penalty scales superlinearly with context length (1.38× at 4K to 5.41× at 32K vLLM, 1.61× to 5.24× SGLang), and VMM remap recovers to 0.96–1.17× without recompute
- Repo / evidence basis: EDMM P1.3 penalty scaling (vLLM 1.38×(4K)→5.41×(32K); SGLang 1.61×→5.24×. Superlinear, both engines); vLLM live: Radix penalty B/A=8.21×; EDMM recovery C/A=1.17×; Standalone 16K: penalty 4.18×; recovery 0.96×; VMM micro: cuMemMap swap 58µs vs full memcpy+recompute 202µs.
- Contribution type: workload model | characterization
- Closest prior work + why this is outside it: vLLM (SOSP'23) and SGLang (NeurIPS'24) measure prefix-cache hit rate but do not quantify contamination penalty from mid-prompt tool-call injection nor its superlinear scaling; EDMM is first to measure it.
- Closest OSS competitor + why it does not invalidate: vLLM / SGLang — they exhibit the penalty but do not provide recovery; their existence confirms the problem but not the solution.
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? **YES** — penalty is KV cache invalidation and recompute, not attention speed; even infinitely fast attention still pays the recompute cost if KV is discarded.
- No-Code test: if the implementation vanished, what knowledge remains? Mid-prompt tool-call injection breaks RadixAttention hash chain, causing superlinear TTFT penalty; VMM remap can recover to near-baseline (0.96–1.17×) if the correct KV is available; recovery is an oracle upper bound (prediction unproven).
- Baseline-death test: which baseline most likely kills it? Engine-level prefix repair (e.g., SGLang or vLLM adding native contamination recovery) — if engines fix the hash chain without VMM, the characterization is still valid but the mechanism is moot.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: >20% of real-world agent tool calls cause >2× TTFT penalty. Cost: 2 weeks to collect traces from 3 agent workloads. Min success: ≥20% of calls meet threshold. What it kills: If <5%, the problem is rare and not worth optimizing.
- 30-day test: submission-grade in 30 focused days? **YES** — data exists (P1.3, live), needs trace analysis.
- Venue: ASPLOS | MLSys | OSDI/SOSP | NeurIPS | ATC/EuroSys | Workshop | Kill → **MLSys** or **ATC/EuroSys**
- YOUR vote on this new thesis: **YELLOW**

## PART C — Your top 3 NEW theses ranked, and which you'd defend as GREEN

**Ranked:**
1. **NEW-T3** — Software CoW detection dominates GPU CoW latency; scratch-pool 3% not 47%
2. **NEW-T2** — VA mapping metadata K≈520K is the fundamental limit, not HBM or Linux VMA
3. **NEW-T1** — Cross-domain heterogeneous CoW policy for agent state

**Defend as GREEN:**
- **NEW-T3 only.** It survives hostile review because it is a measured, honest retraction with a full cost breakdown (178µs/page, 13µs D2D 7%) and a null result that refutes the authors’ own prior 47% claim. The evidence is in the repo (B8 NULL RESULT), the methodology is profiling (3-day EV experiment), and the conclusion (VA manipulation, not bandwidth, dominates) is falsifiable and useful for future GPU VMM work. It does not rely on unbuilt mechanisms, oracle assumptions, or version-specific invariants beyond the measured stack. The other two are YELLOW: T2 is a solid characterization but risks being dismissed as a “section not paper” driver quirk; T1 is architecturally interesting (and named by the ASPLOS debate as genuinely new) but unbuilt, making it vulnerable to the “no implementation” kill shot.
===EXIT_0===
