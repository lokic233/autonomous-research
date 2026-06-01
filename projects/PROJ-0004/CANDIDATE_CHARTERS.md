# PROJ-0004 — Candidate Project Charters

**Author:** researcher-proj4-design-r4 (orchestrator-r4-001, session be17b683)
**Date:** 2026-06-01
**Bias:** Meta-community-valuable topics — agent-infra / inference-opt / LLM-serving / KV-cache / agentic-systems.
**Constraint:** must NOT collide with PROJ-0001/0002/0003 occupied_territory or any cemetery dead idea (DEAD-0001..0010).
**Instruments available to exploit for fast first signal:** agent-trace corpora (Claude Code / Codex / Gemini, already parsed in PROJ-0003 EXP-0007/0012/0031/0033); vLLM source-built ros-vllm 0.6.6 on devgpu014 (+ isolated vLLM>=0.7 env being built); lmcache/CacheBlend kernels (used in PROJ-0002 EXP-0030/0034); GPU-memory characterization harness (PROJ-0001); H100 devgpu014 [safe], MI350X devgpu499 [fragile].

---

## CANDIDATE A — Tool-Boundary Acceptance Cliff in Speculative Decoding for Agent Trajectories
**(STRONGEST + cheapest-to-first-signal — recommended)**

### 1. THESIS
On real agentic tool-calling trajectories, a speculative-decoding draft model's token-acceptance rate drops by a measurable, position-localized amount in the K decode steps immediately following each tool-result injection (the resumption boundary), because the draft must continue text conditioned on externally-injected, non-self-generated tokens it never produced — and this boundary penalty, not task "cognitive domain", is the dominant within-trajectory driver of accepted-length variance.

### 2. NOVELTY vs PRIOR ART
- **"Speculative Decoding: Performance or Illusion?" (arXiv:2601.11580, Liu/Stoica/Cheung)** — measures SD speedup under *production batch sizes* and finds verification is the bottleneck. Delta: it measures aggregate batch-level speedup, NOT a *within-trajectory, position-indexed* acceptance curve, and uses generic chat/code datasets, not tool-call resumption boundaries.
- **"Acceptance Dynamics Across Cognitive Domains in SD" (arXiv:2604.14682)** — varies acceptance by *task domain* (the cross-task axis). Delta: our axis is the *intra-trajectory tool-boundary* (within a single agent task), a different decomposition; we claim the boundary term dominates the domain term.
- **"The Disparate Impacts of Speculative Decoding" (arXiv:2510.02128)** — gives the rp/rq acceptance theory (acceptance ≈ drafter fitness 1−rq). Delta: we predict and measure that rq SPIKES locally at injected-token boundaries; theirs is a global per-task quantity. We instantiate their theory at a new granularity.
- **SpecDec++ (arXiv:2405.19715)** — measures OOD acceptance on HumanEval/GSM8K and adapts candidate length. Delta: OOD here = whole-dataset shift; we measure a *recurring intra-sequence OOD spike* caused by tool output, and tie adaptive candidate-length policy to boundary detection rather than global discard-rate.
- **ToolSpec (arXiv:2604.13519)** — schema-aware SD for the *tool-call argument generation* itself. Delta: opposite side of the boundary — ToolSpec speeds up emitting the call; we characterize the acceptance penalty *after the result returns* and resumption begins.
- **Non-collision check:** distinct from DEAD-0010 (idle-window speculative *prefill* break-even identity — that is engine-side prefill speculation; this is decode-time draft acceptance, a measured empirical curve, not an accounting identity). Distinct from MAP-0001 KV-reuse works. Not in any cemetery duplicate_pattern.

### 3. FIRST FALSIFIABLE CLAIM (CLAIM-shaped)
CLAIM-A0: "Across >=2 agent-trace corpora and >=2 (target, draft) pairs, mean draft acceptance rate in the first K=8 decode positions after a tool-result injection is lower than the trajectory-baseline acceptance by a margin whose 95% CI excludes 0 and exceeds the cross-domain acceptance spread reported as confounder." PASS = boundary penalty CI>0 AND boundary penalty > domain-spread. FAIL = CI includes 0, or boundary effect <= domain effect (then it's a domain story, already occupied by 2604.14682).

### 4. CHEAP GATING EXP (Level-0/1)
- **L0 (CPU, stdlib, hours):** Re-use the already-parsed CC/Codex/Gemini trace corpora. For each trajectory, segment into pre-tool / post-tool token spans. Run a small open draft+target pair (e.g. via a tiny HF model on Mac CPU, or teacher-forcing logprob agreement as an acceptance proxy: a token is "accepted" iff draft top-1 == target top-1) over each span. Compute position-indexed acceptance vs distance-from-boundary; bootstrap CI; compare boundary penalty to a domain-shuffle null.
- **L1 (H100 devgpu014, vLLM 0.6.6 SD, bounded):** confirm the proxy with real vLLM speculative decoding (ngram or EAGLE draft) wall-clock + accepted-length telemetry on a capped set of trajectories. Watchdog + VA/HBM cap (honor MI350X_CRASH_POSTMORTEM; H100 only). Cleanup script kills the server on exit.
- **KILL / negative value:** if the position-indexed curve is flat (no boundary dip) the thesis dies cheaply — and that negative is itself informative: it would say "SD acceptance on agent traces is governed by global task fitness, not injection boundaries," directly corroborating 2510.02128/2604.14682 and telling Meta serving teams that boundary-aware SD scheduling is NOT worth building.

### 5. WHY IT MATTERS (Meta inference-opt / agent-infra)
Agentic serving (tool-calling assistants, coding agents) is exactly the workload where SD is deployed and where decode dominates cost. If acceptance reliably craters at tool boundaries, a boundary-aware policy (suppress speculation for K steps post-injection, or re-warm the draft) recovers wasted verification FLOPs — the #1 lever named by SpecDecode-Bench. If it doesn't, that saves teams from building it. Either way it's a serving-cost result on a real Meta-shaped workload.

### 6. FEASIBILITY on-node
- L0: Mac CPU stdlib + (optional) a small local model — fully runnable, first signal in hours, no GPU.
- L1: H100 devgpu014 ros-vllm 0.6.6 supports ngram/EAGLE SD telemetry; bounded, watchdogged. MI350X NOT required (avoid fragile node).
- Trace corpora already on-node from PROJ-0003 → zero data-collection cost.

---

## CANDIDATE B — KV Prefix-Cache Working-Set Thrash Under Tool-Driven Context Growth
**(medium cost; exploits PROJ-0002/lmcache instruments; higher collision risk — manage carefully)**

### 1. THESIS
In multi-turn agent serving under a fixed KV-cache budget, tool results monotonically grow each session's live context, so the cache working-set per active session grows within a session while the number of concurrent sessions stays fixed — driving an eviction/thrash regime in which standard LRU/priority eviction evicts blocks that will be re-referenced within the same session at a measurably higher rate than in non-agentic (single-turn) workloads, and a session-locality-aware eviction reduces re-prefill bytes by a margin whose CI excludes 0.

### 2. NOVELTY vs PRIOR ART
- **Continuum (arXiv:2511.02230, KV-TTL)** — schedules multi-turn agents by giving KV a time-to-live. Delta: Continuum manages *retention horizon*; we characterize the *intra-session re-reference / thrash law* under within-session working-set growth and test an eviction-policy delta against it as a baseline (not orthogonal — must beat it).
- **"Learning to Evict from KV Cache" (arXiv:2602.10238)** and **"Rethinking KV Eviction via Information-Theoretic Objective" (arXiv:2604.25975)** — learned/principled *intra-context token eviction* for long-context quality. Delta: those evict *tokens within one sequence for quality*; we evict *blocks across sessions for serving throughput* and our signal is re-prefill bytes, not perplexity.
- **TensorRT-LLM priority-based eviction / EpiCache (arXiv:2509.17396)** — priority and episodic cache management. Delta: episodic = conversational QA episodes; we condition on *tool-result injection* as the working-set-growth driver and quantify the agentic-vs-single-turn thrash gap.
- **Non-collision check:** must avoid DEAD-0006 (token-prefix predicts KV sharing → RadixAttention already captures) — this is NOT a sharing-prediction claim, it is an eviction/re-reference-rate claim under capacity pressure. Must avoid CLAIM-0006 cost-map (that is invalidation/recompute on edits; this is capacity-eviction). Risk: could reduce to a generic LRU-vs-workload accounting identity (the PROJ-0001/0002 kill pattern) — gate must check the re-reference rate is NOT predicted by sequence-length distribution alone.

### 3. FIRST FALSIFIABLE CLAIM
CLAIM-B0: "Under a fixed-budget KV cache at fixed concurrency, replaying real agent traces yields an intra-session block re-reference-after-eviction rate that exceeds a single-turn workload matched on total-token volume, with CI>0; and the excess is NOT eliminated by controlling for per-sequence length (permutation null on the length multiset)." FAIL if the agentic excess vanishes under the length-matched permutation null → reduces to a length-distribution accounting identity (DEAD-pattern), kill.

### 4. CHEAP GATING EXP
- **L0 (CPU):** trace-driven cache simulator (stdlib) — feed real agent trace token-lengths-per-turn into an LRU block cache at fixed budget/concurrency; measure re-reference-after-eviction vs a length-matched single-turn synthetic; permutation null on the length multiset. Hours, no GPU.
- **L1 (H100, optional):** confirm re-prefill-byte delta on real vLLM APC with a session-locality eviction hook, bounded, watchdogged.
- **KILL / negative value:** if the permutation null erases the agentic excess, the thrash is just a length-distribution effect — informative because it tells serving teams agent KV pressure is captured by existing length-aware admission, no new eviction policy needed.

### 5. WHY IT MATTERS
KV-cache budget is the binding constraint for agent serving density (sessions/GPU). A real thrash law + a cheap eviction delta directly raises serving density for Meta's agent fleets; a negative result retires a tempting-but-empty policy direction.

### 6. FEASIBILITY on-node
- L0: Mac CPU stdlib simulator — fast first signal, no GPU. Trace corpora on-node.
- L1: vLLM APC eviction hook on H100 (ros-vllm 0.6.6 or the >=0.7 env). MI350X not needed.

---

## CANDIDATE C — Cross-Vendor KV Decode-Bandwidth Wall: H100 vs MI350X Under Agentic Long-Tail Context
**(exploits the unique H100+MI350X dual-vendor instrument from PROJ-0001; pairs with the published 520K ceiling result)**

### 1. THESIS
For agentic decode (large per-session KV, low arithmetic intensity, long-tail context lengths), end-to-end decode throughput is HBM-bandwidth-bound in a regime where the H100/MI350X performance ordering INVERTS relative to the compute-bound prefill ordering — i.e. the vendor that wins prefill loses agentic-decode at high KV-residency, and the crossover context-length is predictable from the (bandwidth, KV-bytes/token) ratio, not from FLOPs.

### 2. NOVELTY vs PRIOR ART
- **"Mind the Memory Gap" (arXiv:2503.08311)** — large-batch LLM inference is memory-bound on a single H100, low L1/L2 hit. Delta: single-vendor, batch-size axis; we add the *cross-vendor inversion* and the *agentic KV-residency / context-long-tail* axis.
- **"Microbenchmark-Driven Analytical Perf Modeling Across GPU Architectures" (arXiv:2605.04178, Blackwell + CDNA3)** and **"AMD MI300X GPU Performance Analysis" (arXiv:2510.27583)** — cross-arch microbenchmarks / analytical roofline. Delta: those are generic kernel/roofline models; we make a *workload-specific, falsifiable serving claim* (agentic-decode ordering inversion + predictable crossover) and validate end-to-end on vLLM, not microbenchmarks.
- **PROJ-0001 (own, DONE)** — established the NVIDIA ~520K VMM mapping ceiling = vendor portability cliff (capacity axis). Delta / non-collision: PROJ-0001 is the *per-op fork-cost + mapping-capacity* axis (CoW branching); THIS is the *steady-state decode-bandwidth* axis, a different physical quantity. Must explicitly NOT restate CLAIM-0001/0002/0003 (the AMD-transfer note already closed the per-op axis analytically). The decode-bandwidth ordering is a genuinely separate measurement.
- **Non-collision check:** not in cemetery; DEAD-0004 (super-linear multi-ctx degradation, retracted) is a different (memory-artifact) phenomenon — this claim is a clean bandwidth-bound ordering, must use isolated single-context-at-a-time measurement to avoid the DEAD-0004 trap.

### 3. FIRST FALSIFIABLE CLAIM
CLAIM-C0: "There exists a context length L* above which MI350X decode throughput (tok/s) at fixed batch overtakes (or is overtaken by) H100 in the OPPOSITE direction to the prefill ordering at the same L, and L* is predicted within +-20% by the analytic bandwidth/KV-bytes ratio." FAIL if no inversion is observed across the measurable context range, OR the ordering matches prefill everywhere (then it's just 'AMD has more bandwidth', occupied by tomshardware/2510.27583 spec-sheet level → kill).

### 4. CHEAP GATING EXP
- **L0 (CPU, analytic):** roofline calculator — decode is memory-bound at intensity ~1 op/byte; compute predicted tok/s = HBM_BW / (KV_bytes_per_token * layers * 2). Plug published H100 (3.35 TB/s) vs MI350X HBM BW; solve for the L* where ordering crosses prefill ordering. If the analytic model predicts NO crossover in the feasible range, kill before touching a GPU.
- **L1 (H100 devgpu014 safe; MI350X devgpu499 with host_mem_floor MANDATORY + watchdog + cleanup):** measure decode tok/s vs context length, single context at a time (avoid DEAD-0004 multi-worker artifact), >=3 reps, capped context to stay under host_mem_floor on MI350X.
- **KILL / negative value:** if no inversion, the result is "agentic-decode vendor ordering = prefill ordering = bandwidth spec sheet" — informative as a clean negative that tells Meta procurement the agentic-decode case doesn't change the H100-vs-MI350X calculus beyond raw BW.

### 5. WHY IT MATTERS
Meta runs heterogeneous fleets (the user has both H100 and MI350X). A predictable agentic-decode crossover length tells schedulers which vendor to route long-context agent sessions to — a direct fleet-efficiency lever, and a natural companion paper to the published PROJ-0001 vendor-cliff result.

### 6. FEASIBILITY on-node
- L0 analytic: Mac CPU, minutes — and it is a hard gate (kills cheaply if no crossover predicted).
- L1: H100 safe; MI350X ONLY with host_mem_floor + watchdog + bounded context (MI350X_CRASH_POSTMORTEM is binding — the unbounded probe that crashed the node in committee_naviC must not recur). vLLM 0.6.6 runs on both; decode-tok/s telemetry is standard.

---

## RECOMMENDATION
**Candidate A (Tool-Boundary Acceptance Cliff)** is the strongest:
1. **Cheapest to first signal** — a CPU teacher-forcing acceptance proxy on already-parsed agent traces gives a position-indexed curve in hours, before any GPU.
2. **Cleanest novelty delta** — the within-trajectory tool-boundary axis is unoccupied; the three closest works (2601.11580, 2604.14682, 2510.02128) measure batch-level / cross-domain / global-fitness axes, all distinguishable at body level.
3. **Lowest accounting-identity risk** — it is a measured empirical acceptance curve, not a break-even identity (the failure mode that killed DEAD-0009/0010 and demoted CLAIM-0006); the domain-spread null is the built-in anti-coping control.
4. **Exploits two existing instruments at once** (agent-trace corpora + vLLM SD on H100) and lands squarely in inference-opt / agent-infra Meta value.
5. **Informative either way** — a flat curve is a publishable negative that redirects serving teams.

Candidate C is the best *companion-to-PROJ-0001* option and has a hard analytic L0 gate, but carries MI350X operational risk. Candidate B has the highest collision/identity risk (Continuum + eviction-policy crowding) and should be third priority.
