## PART A — Vote on the 4 existing sibling theses

**T1: Kernel-transparent physical KV sharing**
- Vote: RED
- Strongest reject: Read-only physical KV sharing via CUDA VMM was already published in vAttention (ASPLOS'25). The write-after-fork delta is defeated by the repo's own retractions showing software baselines have ~700× faster fork latency and ~6× larger capacity.
- Fatal baseline: vLLM-APC (software refcounted sharing).
- One-line rationale: Repo 1 retractions explicitly prove this is NOT a practical capacity/speedup win over strong software baselines.

**T2: VMM mapping-ceiling K≈520K characterization**
- Vote: YELLOW
- Strongest reject: Characterizing a proprietary, undocumented NVIDIA driver limit (`cuMemSetAccess`) does not yield a fundamental systems insight; a single driver update could invalidate the entire ceiling.
- Fatal baseline: Linux VMA sysctl (`vm.max_map_count`), which scales to 67M and highlights how brittle the proprietary constraint is (Repo 1, Lab 1).
- One-line rationale: Data is solid (Metric 4b, Lab 1), but the finding is a footnote for a "limitations" section, not an architectural thesis.

**T3: EDMM speculative prefill**
- Vote: RED
- Strongest reject: The claimed recovery (1.17× vs 8.21× penalty) is based entirely on an ORACLE upper bound that injects precomputed block hashes, assuming perfect prediction of tool-call tokens.
- Fatal baseline: vLLM 0.6.6 with standard radix caching (the actual system you'd use without an oracle).
- One-line rationale: Repo 2 ARTIFACT_STATUS admits V1 is an unvalidated oracle that deadlocks live multi-tenant hardware; unproven hit rates do not make a paper.

**T4: Counterfactual replay for failure attribution**
- Vote: RED
- Strongest reject: It does not exist as software. Reviewers do not accept framework conceptualizations and LLM chat transcripts masquerading as systems contributions.
- Fatal baseline: Any actually implemented agent tracing system (e.g., LangSmith).
- One-line rationale: Repo 3 explicitly states it is a "FRAMEWORK + transcripts (not a built system)".

***

## PART B — Propose NEW thesis candidates

### NEW-T5: Superlinear Hash-Chain Invalidation Modeling for Agentic Workloads
- Repo / evidence basis: Repo 2 P1.3 penalty scaling (vLLM 1.38× at 4K → 5.41× at 32K; SGLang 1.61× → 5.24×).
- Contribution type: characterization | workload model
- Closest prior work + why this is outside it: Standard KV cache eviction policies (e.g., vLLM SOSP'23) assume static prompt prefixes or linear degradation. This models the specific non-linear pathology of mid-prompt tool-call injection.
- Closest OSS competitor + why it does not invalidate: vLLM / SGLang. They are the subjects exhibiting the superlinear penalty, not the solution.
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? YES. FlashInfer optimizes kernel execution, not radix-tree traversal and KV memory allocation latency during hash-chain breakage.
- No-Code test: if the implementation vanished, what knowledge remains? The mathematical model of how tool responses geometrically degrade TTFT in radix-cache environments.
- Baseline-death test: Continuum / LMCache (if they close the KV offload window fast enough, the penalty becomes negligible).
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Test TTFT degradation on 128K context with 10 interleaved tool calls. Cost: 2 days. Min success: Prove exponential penalty curve. Kills: Claims that static prefix caching is sufficient for agentic loops.
- 30-day test: submission-grade in 30 focused days? YES.
- Venue: MLSys
- YOUR vote on this new thesis: YELLOW (Needs a predictive mitigation, not just the model, to survive).

### NEW-T6: Hardware Limits of VMM for High-Branching Memory States
- Repo / evidence basis: Repo 1 Metric 4/4b (OOM at K≈520K branches/pages) and Lab 1 (392 VMAs vs 67M OS limit), plus Retractions (software 700× faster).
- Contribution type: characterization
- Closest prior work + why this is outside it: vAttention (ASPLOS'25) proves VMM works for static KV read-only sharing. This proves VMM fundamentally fails for dynamic, high-branching tree-of-thought (CoW) workloads due to driver-level mapping metadata limits.
- Closest OSS competitor + why it does not invalidate: SGLang RadixAttention. Software refcounting does not use VMM, thus avoiding the `cuMemSetAccess` limit entirely (validating our thesis).
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? YES. This is about physical memory mapping and driver metadata exhaustion, completely independent of kernel math latency.
- No-Code test: if the implementation vanished, what knowledge remains? The forensic boundary that CUDA VMM mapping limits scale inversely with prefix pages, independently of OS VMA limits.
- Baseline-death test: A sudden NVIDIA driver update fixing `cuMemSetAccess` metadata bloat.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Sweep branches across varying batch sizes to prove the mapping limit is absolute across all hardware SKUs. Cost: 5 days. Min success: 520K limit replicates on A100/H100/L40S. Kills: All future attempts to use raw CUDA VMM for agent state-forking.
- 30-day test: submission-grade in 30 focused days? YES.
- Venue: OSDI/SOSP
- YOUR vote on this new thesis: GREEN

### NEW-T7: Contiguous Virtual Address Bridging for Unmodified Kernels in Shared Prefix
- Repo / evidence basis: Repo 1 Metric 3 (VMM-paged KV adds ≈0% overhead vs contiguous; unmodified FlashAttention/SDPA runs) + WRITEUP ("WHAT SURVIVES").
- Contribution type: abstraction | systems mechanism
- Closest prior work + why this is outside it: vLLM PagedAttention forces users to write/compile specialized paged kernels. This abstraction projects scattered physical pages into a contiguous VA space so ANY unmodified attention kernel can execute over a shared prefix.
- Closest OSS competitor + why it does not invalidate: vAttention (ASPLOS'25) does contiguous VA for read-only. We add the detection-in-software branch-aware write path (Metric 5b: bit-identical decode, -44% peak HBM).
- Anti-FlashInfer test: would it still matter if FlashInfer were infinitely fast? YES. The point is avoiding vendor lock-in to FlashInfer's paged kernels; researchers can run experimental SDPA derivatives without rewriting them for paging.
- No-Code test: if the implementation vanished, what knowledge remains? The proof that software-detected VMM page remapping satisfies standard contiguous SDPA expectations.
- Baseline-death test: vAttention (ASPLOS'25) + ChunkAttention (ASPLOS'24) already cover so much of the read-only VMM space that reviewers might ignore the CoW delta.
- Highest-EV experiment (hypothesis / cost / min success criterion / what it kills): Run 5 experimental non-paged attention kernels (e.g., sparse, linear) over shared agent prefixes with 0 code modification. Cost: 10 days. Min success: 3/5 execute correctly. Kills: The assumption that prefix sharing requires specialized kernels.
- 30-day test: submission-grade in 30 focused days? YES.
- Venue: ASPLOS
- YOUR vote on this new thesis: YELLOW

***

## PART C — Your top 3 NEW theses ranked, and which you'd defend as GREEN

1. **NEW-T6 (Hardware Limits of VMM for High-Branching Memory States)** - **Defend as GREEN.**
   *Why:* It weaponizes the project's failures into a rigorous empirical truth. Repo 1 proved unequivocally that software refcounting (vLLM-APC) destroys hardware VMM on fork latency (700×) and capacity (6×) because of an undocumented NVIDIA mapping metadata ceiling (K≈520K). A paper that exhaustively characterizes exactly *why* VMM fails for agentic branching, contrasting OS VMA limits with driver limits, is classic OSDI/ATC material. It tells the community: "Stop trying to build hardware CoW for LLM agents; use software."

2. **NEW-T7 (Contiguous Virtual Address Bridging for Unmodified Kernels)** - **Defend as YELLOW.**
   *Why:* It isolates the one legitimate mechanical success from Repo 1 (Metric 3 + WRITEUP): the ability to run unmodified FlashAttention/SDPA on branched states. However, it is deeply vulnerable to the ASPLOS debate attack mentioned in Repo 3 ("vAttention + ChunkAttention already did VMM KV"). It survives only if we lean heavily into the "unmodified experimental kernels" abstraction.

3. **NEW-T5 (Superlinear Hash-Chain Invalidation Modeling)** - **Defend as YELLOW.**
   *Why:* Repo 2's data (P1.3 penalty scaling) clearly identifies a critical bottleneck in modern agentic loops (mid-prompt tool injections destroying TTFT via hash invalidation). But characterizations without robust mitigations are weak. Since EDMM V1's mitigation is a declared oracle (ARTIFACT_STATUS), this thesis currently lacks the second half of a top-tier systems paper.
===EXIT_0===
