# PROJ-0005 — Candidate Project Charters

**Author:** researcher-proj5-design-r4 (orchestrator-r4-001, session be17b683)
**Date:** 2026-06-01
**Why:** PROJ-0001 converged/published -> freed an investing slot (now 3/4). This designs the refill-to-4 replacement.
**Bias:** Meta-valuable: agent-infra / inference-optimization / LLM-serving / KV-cache / agentic-systems.
**Non-collision constraint:** must NOT collide with PROJ-0001 (HW VMM CoW / 520K ceiling / per-op fork-cost), PROJ-0002 (semantic prefix-invalidation cost-map / CDC-vs-PIC), PROJ-0003 (failure attribution / over-dispersion), PROJ-0004 (within-trajectory position-indexed SD draft-acceptance at tool-result resumption boundaries), or cemetery DEAD-0001..0010.
**Instruments to reuse for fast first signal:** agent-trace corpora (Claude Code / Codex / Gemini, parsed in PROJ-0003 EXP-0007/0012/0031/0033); a real production tokenizer (HF, CPU, stdlib-adjacent); vLLM ros-vllm 0.6.6 + isolated ros-vllm07 (vLLM 0.22) on devgpu014 [H100, safe]; lmcache/CacheBlend (PROJ-0002 EXP-0030/0034); GPU-mem harness + dual-vendor H100/MI350X (PROJ-0001); MI350X devgpu499 [fragile, host_mem_floor mandatory].

---

## CANDIDATE A — Tool-Result Re-Tokenization Boundary Churn Defeats Exact-Prefix KV-Cache Reuse
**(CPU-first, cheapest-to-first-signal, cleanest unoccupied axis — RECOMMENDED)**

### 1. THESIS
On real agentic trajectories, injecting a tool result into an ongoing context perturbs the BPE token boundaries of the tokens straddling the injection seam (and, for streamed/whitespace-variant tool outputs, of the result span itself), so the re-tokenized token-ID prefix diverges from the cached prefix at a measurable, structurally-predictable rate — silently demoting an exact-prefix-cache (vLLM APC / RadixAttention block-hash) HIT to a MISS for a quantifiable fraction of tool-call turns, and this token-boundary churn is predictable model-free from the seam's delimiter class WITHOUT any attention or semantic signal.

### 2. NOVELTY vs PRIOR ART (web-verified 2026-06-01)
- **"Tokenization Multiplicity Leads to Arbitrary Price Variation in LLM-as-a-service" (arXiv:2506.06446)** — shows the SAME string can tokenize to different ID sequences, affecting *billing*. Delta: their consequence is PRICE; ours is a *serving-throughput* consequence (exact-prefix KV-cache hit->miss demotion at the *tool-result injection seam*), with a *position/delimiter-conditioned churn rate* on real agent traces. Different dependent variable, different mechanism site.
- **"Sampling from Your Language Model One Byte at a Time" (arXiv:2506.14123)** — tokenization-induced *generation distortion* and byte-level resampling. Delta: that is a *quality/distribution* effect on output; ours is a *cache-reuse* effect on the input prefix at injection boundaries. No serving-cache claim there.
- **vLLM Automatic Prefix Caching design doc (vllm-project prefix_caching.md) / RadixAttention (NeurIPS'24)** — block-hash exact-prefix reuse. Delta: both ASSUME the incoming request re-tokenizes to a byte-identical ID prefix; we show that assumption *breaks at tool-result seams* and quantify the resulting silent miss rate. We attack the cache's correctness-of-hit premise, not its policy.
- **CacheBlend (arXiv:2405.16444) / EPIC (arXiv:2410.15332) / PROJ-0002 CLAIM-0006 cost-map** — selective recompute on *semantic* edits (WHERE you inject changes the recompute fraction). Delta / NON-COLLISION: PROJ-0002 is the *semantic-invalidation* axis (content changed -> recompute K/V). Ours is a *lexical/tokenizer* axis: even when content is appended cleanly and SHOULD be a perfect prefix extension, the BPE boundary shift makes the ID sequence diverge so the hit is lost *before any semantic recompute question arises*. Orthogonal failure layer; must cite PROJ-0002 to disambiguate.
- **ContiguousKV (arXiv:2601.13631)** — append-suffix re-prefill / read-amplification (granularity-aligned). Delta: that is I/O granularity for *appended* tokens; ours is *boundary churn of already-cached tokens* (the seam tokens change ID), a correctness-of-reuse issue, not an I/O-granularity issue.
- **NON-COLLISION check:** distinct from PROJ-0004 (decode-time draft acceptance — this is prefill-time prefix-cache hit/miss); distinct from DEAD-0006 (token-prefix predicts KV sharing — this is the OPPOSITE: token-prefix *fails* to predict reuse because the IDs churn); not in any cemetery duplicate_pattern.

### 3. FIRST FALSIFIABLE CLAIM (CLAIM-shaped)
CLAIM-A0: "Across >=2 agent-trace corpora and >=2 production tokenizers, the fraction of tool-result-injection turns whose re-tokenized token-ID prefix DIVERGES from the naive concatenation-cached prefix (= a silent exact-prefix-cache miss or boundary-block invalidation) has a 95% CI excluding 0, exceeds a whitespace-stable control (clean newline-delimited append) by a margin whose CI excludes 0, and is predicted (AUC CI>0.5) by the seam's delimiter class alone (model-free)." PASS = churn-rate CI>0 AND > whitespace-stable-control AND delimiter-class predictive. FAIL = churn ~0, OR equal to the clean-append control (then engines already normalize seams -> no problem), OR delimiter class non-predictive (then it's unstructured noise, not a characterizable law).

### 4. CHEAP GATING EXP (Level-0, CPU, stdlib + one HF tokenizer; hours; watchdog+cleanup)
- **L0 (Mac CPU):** for each trajectory, reconstruct the pre-injection context and the post-injection context as the engine would assemble them; tokenize (a) the cached-prefix-then-append path and (b) the full re-tokenized path; compute the longest common token-ID prefix; the churn event = LCP < len(cached prefix). Bucket by delimiter class (JSON `}`-to-text, raw stdout, code fence, trailing-whitespace-variant). Bootstrap CI; compare vs a clean-`\n`-append control; fit a model-free delimiter-class predictor and report AUC with CI. Pure tokenizer, no GPU, no model weights.
- **L1 (H100 devgpu014, OPTIONAL, bounded):** confirm the simulated miss converts to a REAL vLLM APC hit->miss (cache-hit counters) and measure the recompute TTFT cost on a capped trajectory set. Watchdog + HBM cap; H100 only; cleanup kills server on exit. MI350X NOT required.
- **KILL / why a negative is still informative:** if churn ~0 or == the clean-append control, the result is "production engines already canonicalize tool-result seams; agentic prefix-cache reuse is NOT silently lost to tokenization" — a clean negative that tells serving teams to stop suspecting tokenizer churn and look elsewhere (PROJ-0002 semantic axis), and retires a plausible-but-empty hypothesis cheaply.

### 5. WHY IT MATTERS (Meta inference-opt / agent-infra)
Exact-prefix KV reuse (APC / RadixAttention) is THE dominant TTFT optimization for multi-turn agent serving. A silent, structurally-predictable hit->miss rate at tool seams is wasted prefill FLOPs on every affected turn at fleet scale; the model-free delimiter predictor yields a trivial mitigation (seam canonicalization before hashing). A negative redirects effort. Either way it is a serving-cost result on a real Meta-shaped agent workload, with zero data-collection cost.

### 6. FEASIBILITY on-node
- L0: Mac CPU + one HF tokenizer (or pure-Python BPE) — fully runnable, first signal in hours, no GPU, no model weights. Trace corpora already on-node from PROJ-0003.
- L1: H100 devgpu014 ros-vllm 0.6.6 exposes APC hit/miss counters; bounded + watchdogged. MI350X avoided (fragile).

---

## CANDIDATE B — Kernel-Maturity-Controlled Decode-Bandwidth Crossover Length L* (H100 vs MI350X)
**(PROJ-0001 companion; refined to BEAT the prior committee's spec-sheet kill; carries MI350X operational risk)**

### 1. THESIS
For agentic decode (large per-session KV, arithmetic intensity ~1 op/byte), there exists a context length L* at which the H100/MI350X decode-throughput ordering INVERTS relative to the compute-bound prefill ordering, AND with MATURITY-MATCHED kernels (same attention backend family, same KV dtype, same GQA group size) the measured L* falls within +-20% of the analytic prediction L* = f(HBM_BW, KV_bytes/token); the FALSIFIABLE content is the quantitative L* prediction, NOT the bare ordering (which AMD ROCm public guidance already states).

### 2. NOVELTY vs PRIOR ART (web-verified 2026-06-01)
- **AMD ROCm public guidance** already states "H100 lower prefill latency, longer decode latency due to lower memory bandwidth" with the 5.325 vs 3.35 TB/s numbers. Delta: that is the BARE ORDERING (spec-sheet). Our ONLY claimed contribution is the FALSIFIABLE quantitative crossover L* within +-20%, validated E2E with maturity-matched kernels — explicitly NOT the ordering. (This is the exact refinement the PROJ-0004 design committee demanded before C-like ideas can seed.)
- **"Microbenchmark-Driven Analytical Perf Modeling Across GPU Architectures" (arXiv:2605.04178, Blackwell + CDNA3, 1.31% / 0.09% MAE)** — analytical models per arch, validated on Rodinia/SPEChpc *kernels*. Delta: theirs are generic kernel roofline models; ours is a *workload-specific serving claim* (agentic decode L* crossover) validated *end-to-end on vLLM*, not microbenchmarks, and the contribution is the +-20% prediction band, not the model derivation.
- **"Mind the Memory Gap" (arXiv:2503.08311)** — single-H100, batch-size axis, decode is memory-bound. Delta: single-vendor; we add the CROSS-VENDOR inversion + the agentic long-tail-context axis + a falsifiable L*.
- **PROJ-0001 (own, DONE)** — established the per-op fork-cost + 520K mapping-capacity vendor cliff (CoW branching). Delta / NON-COLLISION: PROJ-0001 is the per-op-fork-cost + mapping-capacity axis; the AMD-transfer note already closed it analytically. THIS is the STEADY-STATE DECODE-BANDWIDTH axis — a different physical quantity, no mapping/CoW involved. Must explicitly NOT restate CLAIM-0001/0002/0003.
- **NON-COLLISION check:** distinct from DEAD-0004 (super-linear multi-context degradation = per-worker memory artifact) — this MUST use isolated single-context-at-a-time decode measurement to avoid that trap.

### 3. FIRST FALSIFIABLE CLAIM
CLAIM-B0: "With maturity-matched kernels (matched attention backend, KV dtype, GQA group), there is a context length L* at which MI350X decode tok/s overtakes H100 in the OPPOSITE direction to the prefill ordering at the same L, and the measured L* is within +-20% of the analytic HBM_BW/KV_bytes prediction." FAIL = no inversion in the measurable range, OR ordering matches prefill everywhere (then = spec-sheet 'AMD has more BW' -> KILL), OR measured L* outside +-20% under matched kernels (then the analytic predictor is wrong / kernel-maturity-confounded -> KILL).

### 4. CHEAP GATING EXP (Level-0 analytic CPU = hard gate; Level-1 GPU bounded)
- **L0 (Mac CPU, minutes, HARD gate):** roofline calculator: decode tok/s ~ HBM_BW / (2 * layers * KV_bytes_per_token); plug H100 3.35 TB/s vs MI350X published HBM BW; solve for L* where the decode ordering crosses the prefill ordering. If NO crossover predicted in the feasible context range, KILL before any GPU.
- **L1 (H100 devgpu014 safe; MI350X devgpu499 with host_mem_floor MANDATORY + watchdog + cleanup):** measure decode tok/s vs context length, ONE context at a time (avoid DEAD-0004), >=3 reps, matched attention backend / KV dtype / GQA across both vendors; capped context under MI350X host_mem_floor. Compare measured L* to L0 prediction.
- **KILL / informative negative:** no inversion, or unmatched-kernel-confounded L* -> "agentic-decode vendor ordering = prefill ordering = raw-BW spec sheet; matched-maturity kernels do not produce a predictable crossover" -> tells Meta procurement the agentic-decode case does NOT change the H100-vs-MI350X calculus beyond raw BW. Companion negative to the published PROJ-0001 vendor-cliff result.

### 5. WHY IT MATTERS
Meta runs heterogeneous H100+MI350X fleets. A maturity-matched, falsifiable agentic-decode crossover L* tells schedulers which vendor to route long-context agent sessions to — a direct fleet-efficiency lever and a natural companion paper to the published PROJ-0001 vendor cliff.

### 6. FEASIBILITY on-node
- L0 analytic: Mac CPU, minutes; hard kill if no crossover predicted.
- L1: H100 safe; MI350X ONLY with host_mem_floor + watchdog + bounded context (MI350X_CRASH_POSTMORTEM binding — the committee_naviC unbounded probe that crashed the node must not recur). vLLM 0.6.6 runs both; decode-tok/s telemetry standard. RISK: maturity-matched kernels across vendors is non-trivial; if matching fails, L* is confounded and the project should fall back to A.

---

## CANDIDATE C — Schema-Position Dormant-Token Survival Law for Tool-Result KV Retention
**(CPU-first characterization; rides the Transactional-Attention finding; medium collision-management)**

### 1. THESIS
Within a tool result, WHICH tokens become "dormant-essential" (near-zero attention during decode yet load-bearing for a later generation step — e.g. an ID/path/credential field) is predictable MODEL-FREE from the token's STRUCTURAL POSITION in the tool-result schema (JSON value-after-key, code-block identifier, table cell), and a schema-position retention rule preserves downstream TASK CORRECTNESS at a given KV budget at a measurably higher rate than attention-score eviction AND than purely lexical anchor-adjacency retention.

### 2. NOVELTY vs PRIOR ART (web-verified 2026-06-01)
- **Transactional Attention (arXiv:2604.11288)** — "dormant tokens" (credentials/keys/config) get 0% retrieval under H2O/TOVA/SnapKV/StreamingLLM/PyramidKV/DynamicKV at K=16; TA protects tokens ADJACENT to lexical anchors ("key:", "password:"); TA-Fast is the attention-free anchor variant. Delta: TA is a RETENTION MECHANISM keyed on *immediate lexical anchors*. Ours is a WORKLOAD-LEVEL CHARACTERIZATION + predictor: we claim dormancy-essentiality is predictable from *schema position* (structural depth/role), not just adjacent-anchor lexemes, and we show TA-Fast's anchor heuristic measurably OVER-retains (anchored-but-inert fields) and UNDER-retains (essential fields with no adjacent anchor, e.g. positional array elements). Different unit of prediction (schema role vs lexical neighbor) + a head-to-head against TA-Fast as the named baseline.
- **CAOTE (arXiv:2504.14051) / G-KV (arXiv:2512.00504) / Reformulating KV Eviction (arXiv:2605.07234)** — attention-output-error / global-attention eviction. Delta: all are *attention-signal* eviction; dormant tool tokens are precisely where attention signal fails (TA's premise). We are model-free/structural and benchmark downstream TASK correctness, not perplexity/attention reconstruction.
- **SideQuest (arXiv:2602.22603)** — uses the LRM ITSELF to reason about token usefulness (an auxiliary reasoning task). Delta: SideQuest is EXPENSIVE model-driven selection; ours is a CHEAP model-free schema-position predictor; we test whether structure alone recovers most of the model-driven benefit.
- **PTE / "Beyond Accuracy" (arXiv:2604.05404)** — tool-response bloat latency metric (Prefill Token Equivalents). Delta: PTE measures the COST of keeping bloated tool output; we predict WHICH parts are safely droppable without breaking the task. Complementary, not overlapping.
- **NON-COLLISION check:** must avoid DEAD-0007 (layer-stratified positional KV reuse capped at 1.5% incidence) — that is LAYER-positional reuse for prefill-FLOP saving; ours is SEQUENCE/SCHEMA-positional importance for eviction-correctness, different axis. Must avoid DEAD-0006 (token-prefix predicts sharing). Risk: could reduce to "structure predicts importance ~ TA-Fast anchors already capture it" -> the gate MUST show schema-position beats anchor-adjacency with CI>0 on task correctness, else KILL.

### 3. FIRST FALSIFIABLE CLAIM
CLAIM-C0: "At a fixed KV budget on real function-calling / tool-result traces, a model-free schema-position retention rule preserves downstream task-correct generation at a rate whose advantage over (a) attention-score eviction AND (b) TA-Fast lexical-anchor-adjacency has a 95% CI excluding 0." FAIL = no advantage over TA-Fast anchors (reduces to the occupied lexical-anchor mechanism) OR no advantage over attention eviction (structure adds nothing) -> KILL.

### 4. CHEAP GATING EXP (Level-0/1, CPU-leaning)
- **L0 (Mac CPU, hours):** label tool-result tokens by schema role (a deterministic parser over the JSON/code/table structure in the traces — stdlib). Build a synthetic retrieval probe per trajectory (later step must reproduce a specific tool-result field). Simulate budgeted eviction under (i) attention-score (replay logged/proxy attention), (ii) TA-Fast anchor-adjacency, (iii) schema-position rule. Score field-recovery correctness; bootstrap CI on the pairwise advantage.
- **L1 (H100, bounded):** confirm on a real model with logged attention + actual decode that schema-position retention preserves correctness where attention eviction drops it; capped, watchdogged, H100 only.
- **KILL / informative negative:** if schema-position does not beat TA-Fast anchors, the result is "lexical anchor adjacency (already published) is sufficient; structural schema role adds nothing" — informative, retires the structural-predictor direction, and corroborates TA.

### 5. WHY IT MATTERS
Agent contexts are dominated by tool-result tokens (SideQuest, PTE both confirm). A cheap model-free retention rule that keeps task correctness at lower KV budget raises agent serving density; the head-to-head with TA-Fast cleanly establishes whether structure beats lexical anchors. Direct KV-budget lever for Meta agent fleets.

### 6. FEASIBILITY on-node
- L0: Mac CPU stdlib parser + simulated budget eviction on parsed traces — fast first signal, no GPU. Risk: needs a credible attention-score proxy (logged or teacher-forced) for baseline (i); fall back to published H2O/SnapKV attention-score formulas on a small local model.
- L1: H100 devgpu014 with logged attention; bounded, watchdogged. MI350X not needed.

---

## RECOMMENDATION

**Candidate A (Tool-Result Re-Tokenization Boundary Churn) is the strongest — recommend seeding it.**

1. **Cleanest unoccupied axis.** Web-verified: tokenization-multiplicity work targets PRICING (2506.06446) and GENERATION DISTORTION (2506.14123); NO prior work characterizes exact-prefix KV-cache hit->miss demotion from re-tokenization at tool-result injection seams. It attacks the *correctness-of-hit* premise of APC/RadixAttention, which everyone ASSUMES holds.
2. **Cheapest to first signal + lowest accounting-identity risk.** Pure-tokenizer CPU simulation on already-parsed traces gives a churn-rate curve in HOURS with NO GPU and NO model weights. It is a MEASURED lexical event, not a break-even identity (the failure mode that killed DEAD-0009/0010 and dogged CLAIM-0006), and the clean-append control + model-free delimiter predictor are built-in anti-coping controls.
3. **Crisp non-collision.** It is a LEXICAL/tokenizer layer, explicitly orthogonal to PROJ-0002's SEMANTIC invalidation cost-map, to PROJ-0004's DECODE-time draft acceptance, and the inverse of DEAD-0006.
4. **Informative either way** — a flat/zero churn result is a publishable negative that tells serving teams engines already canonicalize seams.

**Candidate C** is a strong CPU-first #2 but carries a real reduction risk to the already-published Transactional-Attention lexical-anchor mechanism; its gate (beat TA-Fast with CI>0 on task correctness) is the make-or-break and should be the first thing run if A stalls.

**Candidate B** is the best PROJ-0001 companion and has a HARD analytic L0 kill-gate, and it directly satisfies the prior committee's bar for re-proposing a C-like decode-bandwidth idea (falsifiable +-20% L* under matched-maturity kernels, not the bare ordering). But it carries MI350X operational fragility and a kernel-maturity-matching risk that could confound L*. Seed only as a companion after A's L0 resolves.

**Refill-to-4 note:** A is CPU-only to first signal and reuses the PROJ-0003 trace corpus + PROJ-0002 vLLM/APC instruments — fastest path to a real first signal that refills the 4th investing slot without GPU contention.
