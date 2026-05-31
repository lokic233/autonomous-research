## PART A — Vote on the 4 existing sibling theses

T1 (kernel-transparent KV sharing)
- Vote: YELLOW
- Strongest reject (the reviewer attack most likely to kill it): vAttention already gives CUDA VMM KV with contiguous VA and unmodified kernels; forkedkv adds fork/CoW but not enough architecture if framed only as transparent KV sharing.
- Fatal baseline (which existing system most threatens it): vAttention (ASPLOS'25), plus FlashInfer as production paged-kernel pressure.
- One-line rationale (cite a metric or prior work from the brief): Survives only on write-after-fork CoW and branch isolation; contiguous-VA alone is already vAttention, while forkedkv loses to vLLM-APC on fork latency by ~700x and capacity by ~6x at 32-block prefix.

T2 (VMM ceiling K≈520K characterization)
- Vote: YELLOW
- Strongest reject (the reviewer attack most likely to kill it): It is a useful characterization section, not a full systems paper.
- Fatal baseline (which existing system most threatens it): vAttention, because it already established CUDA VMM KV as a serious design point.
- One-line rationale (cite a metric or prior work from the brief): Metric 4/4b and Lab 1 show a stable driver-internal mapping ceiling K≈520K independent of Linux VMA count, but that is narrower than a complete venue-grade contribution.

T3 (EDMM speculative prefill)
- Vote: RED
- Strongest reject (the reviewer attack most likely to kill it): The central recovery result is oracle-backed; real prediction hit-rate is unproven.
- Fatal baseline (which existing system most threatens it): Continuum / LMCache, because they are closing the speculative-prefill and KV-offload window.
- One-line rationale (cite a metric or prior work from the brief): EDMM shows vLLM live recovery C/A=1.17x after an 8.21x TTFT penalty, but ARTIFACT_STATUS says B4 injects precomputed block hashes and the live V1 fork deadlocked.

T4 (counterfactual replay for failure attribution)
- Vote: YELLOW
- Strongest reject (the reviewer attack most likely to kill it): The failure-attribution repo is a framework and transcripts, not a built replay system.
- Fatal baseline (which existing system most threatens it): Existing agent tracing/evaluation frameworks, plus the absence of an implementation baseline in the brief.
- One-line rationale (cite a metric or prior work from the brief): The committee repo names counterfactual replay as YELLOW and unbuilt; forkedkv provides exact branch isolation evidence via Metric 5c, but the cross-state attribution stack is not implemented.

## PART B — Propose NEW thesis candidates (this is the priority)

### NEW-T1: GPU VMM is a good structural-edit primitive and a bad high-fanout allocation primitive for KV workloads.
- Repo / evidence basis: forkedkv CoW cost ~178us/page; VA-swap CoW 59% faster but breaks contiguous VA; vLLM-APC is ~700x faster on fork latency and ~6x larger capacity at 32-block prefix; EDMM cuMemMap swap 50-58us vs ~274ms recompute.
- Contribution type: workload model
- Closest prior work + why this is outside it: vAttention uses CUDA VMM for KV layout, but the brief does not say it characterizes when VMM remapping loses to software refcounting versus wins against recompute.
- Closest OSS competitor + why it does not invalidate: vLLM-APC invalidates high-fanout fork/capacity claims, but not the structural-edit claim where remap avoids recompute.
- Anti-FlashInfer test: YES + infinitely fast paged attention does not remove the cost of recomputing contaminated KV after prompt mutation.
- No-Code test: if the implementation vanished, the surviving knowledge is the boundary condition: VMM remap is useful for sparse structural edits, not for frequent branch allocation.
- Baseline-death test: LMCache / Continuum, if they eliminate the recompute window without VMM remap.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: VMM beats recompute only when edit locality is sparse and prediction is correct. Cost: run EDMM-style swaps across edit sizes and forkedkv CoW across branch fanout. Min success: produce a crossover curve with at least one region where VMM is >5x faster than recompute and one where vLLM-APC is >100x faster than VMM. Kills: blanket VMM-as-speedup framing.
- 30-day test: submission-grade in 30 focused days? YES
- Venue: ATC/EuroSys
- YOUR vote on this new thesis: YELLOW

### NEW-T2: Exact write-after-fork isolation for autoregressive decoding is the defensible primitive, not KV capacity expansion.
- Repo / evidence basis: Metric 5b real 28-layer Qwen2.5-7B decode has bit-identical outputs with 448 CoW events and 44% lower peak HBM; Metric 5c tree-of-thought rollback fires CoW exactly once, copies 1 page, and leaves siblings uncorrupted.
- Contribution type: runtime primitive
- Closest prior work + why this is outside it: vAttention provides VMM KV and contiguous VA but read-only sharing; ChunkAttention shares prefixes but has no write-after-fork path.
- Closest OSS competitor + why it does not invalidate: vLLM PagedAttention / SGLang RadixAttention share prefixes in software, but the brief identifies software prefix-sharing as requiring PagedAttention rather than unmodified attention kernels.
- Anti-FlashInfer test: YES + faster paged kernels do not provide contiguous-VA write-after-fork rollback semantics.
- No-Code test: the remaining knowledge is that branch isolation can be validated at page granularity with exact sibling non-corruption and bit-identical decode.
- Baseline-death test: vLLM/SGLang adding software rollback with equivalent isolation and lower overhead.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: CoW rollback cost scales with modified pages, not branch count. Cost: extend Metric 5c to many rollback depths and dirty-page counts. Min success: CoW events equal dirty pages and sibling corruption remains zero across 24 SWE-bench instances. Kills: claims that this is just memory sharing.
- 30-day test: submission-grade in 30 focused days? YES
- Venue: ASPLOS
- YOUR vote on this new thesis: YELLOW

### NEW-T3: Driver-internal VMM metadata, not HBM bytes or Linux VMAs, is the hidden resource that governs GPU replay fanout.
- Repo / evidence basis: Metric 4/4b full clone OOMs at 6 branches while CoW reaches 84; max branches obey K≈520K/prefix_pages across 1,3,6,12GiB; Lab 1 shows /proc/self/maps=392 versus vm.max_map_count=67M at OOM.
- Contribution type: characterization
- Closest prior work + why this is outside it: vAttention uses CUDA VMM for KV but the brief does not say it reports a stable driver-internal mapping ceiling law.
- Closest OSS competitor + why it does not invalidate: vLLM-APC exceeds forkedkv capacity at 32-block prefix by ~6x, but that strengthens the negative characterization: VMM metadata is the bottleneck.
- Anti-FlashInfer test: YES + attention kernel speed does not change cuMemSetAccess mapping metadata exhaustion.
- No-Code test: K≈520K remains a reusable design constraint for CUDA VMM replay systems.
- Baseline-death test: A newer CUDA driver or GPU generation raising/removing the K ceiling.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: K is stable across allocation size but driver/GPU dependent. Cost: repeat Metric 4b on one additional NVIDIA GPU/driver pair. Min success: either reproduce a stable K within ±10% or show the ceiling moved and identify the dependency. Kills: overgeneralizing one H100/driver result.
- 30-day test: submission-grade in 30 focused days? NO
- Venue: Workshop
- YOUR vote on this new thesis: YELLOW

### NEW-T4: Tool-call prompt contamination is a measurable cross-engine cache invalidation pathology, independent of EDMM’s oracle recovery.
- Repo / evidence basis: EDMM vLLM live penalty B/A=8.21x; P1.3 penalty scaling shows vLLM 1.38x at 4K to 5.41x at 32K and SGLang 1.61x to 5.24x.
- Contribution type: characterization
- Closest prior work + why this is outside it: vLLM PagedAttention and SGLang RadixAttention optimize prefix reuse, but this evidence targets mid-prompt tool-response insertion that breaks the prefix-cache hash chain.
- Closest OSS competitor + why it does not invalidate: SGLang is included as an affected engine, so it is evidence rather than a clean invalidator.
- Anti-FlashInfer test: YES + infinitely fast attention does not restore a broken prefix-cache hash chain.
- No-Code test: the remaining knowledge is that tool-call insertion causes superlinear TTFT penalties across two engines.
- Baseline-death test: Continuum / LMCache, if they already eliminate this penalty in realistic agent traces.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: the penalty occurs on real tool traces, not just constructed prompts. Cost: replay 50 agent traces through vLLM and SGLang. Min success: median TTFT penalty >2x at >=16K context. Kills: toy-workload objection.
- 30-day test: submission-grade in 30 focused days? YES
- Venue: MLSys
- YOUR vote on this new thesis: YELLOW

### NEW-T5: A negative systems result: CUDA VMM CoW should not be sold as a practical replacement for software prefix sharing.
- Repo / evidence basis: forkedkv retracts capacity/speedup framing; vLLM-APC is ~700x faster on fork latency and ~6x larger capacity at 32-block prefix; Metric 5 shows wall-time parity, not speedup, despite 89.9-90.1% fewer KV bytes and 79.9-80.1% lower peak HBM.
- Contribution type: characterization
- Closest prior work + why this is outside it: vLLM PagedAttention and SGLang RadixAttention are the software-sharing baselines; the contribution is the measured failure boundary for VMM CoW against them.
- Closest OSS competitor + why it does not invalidate: vLLM-APC is the competitor and the reason the thesis exists; it kills the optimistic version but supports the negative result.
- Anti-FlashInfer test: YES + the result is about fork latency, capacity, and mapping metadata, not paged attention kernel throughput.
- No-Code test: the remaining knowledge is a falsification of the capacity/speedup story under strong baselines.
- Baseline-death test: None as a negative result; it dies only if forkedkv’s measurements are wrong or an optimized VMM implementation erases the ~700x fork gap.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Hypothesis: the vLLM-APC advantage persists under aligned benchmark settings. Cost: reproduce fork latency and capacity with identical prefixes and branch patterns. Min success: software remains >50x faster on fork or >2x higher capacity. Kills: VMM-CoW-as-serving-upgrade paper.
- 30-day test: submission-grade in 30 focused days? YES
- Venue: Workshop
- YOUR vote on this new thesis: GREEN

## PART C — Your top 3 NEW theses ranked, and which you'd defend as GREEN

1. NEW-T5
2. NEW-T1
3. NEW-T2

I would defend only NEW-T5 as GREEN. It has the cleanest evidence and the fewest heroic assumptions: the brief already contains the self-retraction, the vLLM-APC comparison, wall-time parity, and the mapping-capacity failure mode.

NEW-T1 is YELLOW because it needs a clean crossover study to avoid becoming two disconnected observations. NEW-T2 is YELLOW because exact rollback is real in Metric 5b/5c, but reviewers can still say the use case is narrower than the mechanism.
===EXIT_0===
