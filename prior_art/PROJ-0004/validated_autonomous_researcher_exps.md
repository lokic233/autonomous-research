# PROJ-0004 Prior-Art & Citation Verification — CLAIM-0013
# Tool-Boundary Acceptance Cliff in Speculative Decoding for Agent Trajectories
# Scout: researcher-0013-L0-r4 (L0 lane) | prompt v001 | 2026-06-01T11:33Z

## CLAIM-0013 SECTION — prior-art posture
Thesis = within-trajectory, POSITION-indexed draft-acceptance penalty localized to the K=8 decode
steps AFTER each tool-result resumption boundary, surviving content-type / context-shift / entropy
controls. Distinct from the known axes:
- 2510.02128 "Disparate Impacts of SD" — TASK-DOMAIN axis (the named null), NOT position/boundary.
- 2405.19715 SpecDec++ — whole-dataset OOD, not recurring intra-sequence spike.
- EAGLE / EAGLE-2 / Medusa / REST — acceptance baselines (body-level must-cite).
Occupied territory check (registry/academic_map.yaml): PROJ-0004 node = decode-time within-trajectory
position-indexed acceptance at tool-result boundaries; NOT per-op fork-cost [PROJ-0001], NOT
invalidation cost-map [PROJ-0002], NOT failure attribution [PROJ-0003]. Cemetery registry/cemetery/
PROJ-0004/ is EMPTY -> direction is genuinely open (not a revived dead idea). Proceed.

------------------------------------------------------------------------
## CITATION-VERIFICATION SUBSECTION (6 UNVERIFIED future-dated cites from charter)
Method: WebFetch arxiv.org/abs/<id> + WebSearch cross-check. Per skill_literature, ">=2 independent
sources" required to assert existence; single-source flagged as such. Verified 2026-06-01T11:30Z.

| arxiv id | status | title (verbatim where retrieved) | collision w/ CLAIM-0013? |
|----------|--------|----------------------------------|--------------------------|
| 2601.11580 | **CONFIRMED-EXISTS** (2 sources: arxiv WebFetch + WebSearch/ResearchGate) | "Speculative Decoding: Performance or Illusion?" | **COLLISION-RISK — DIFFERENTIABLE (see below)** |
| 2604.14682 | CONFIRMED-EXISTS (1 source: arxiv WebFetch) | "Acceptance Dynamics Across Cognitive Domains in Speculative Decoding" | NO — task/cognitive-DOMAIN axis (a 2nd named domain-null, like 2510.02128); reinforces our control, does not occupy position/boundary |
| 2602.10238 | CONFIRMED-EXISTS (1 source: arxiv WebFetch) | "Learning to Evict from Key-Value Cache" (KVP, RL eviction) | NO — KV-cache eviction axis |
| 2604.25975 | CONFIRMED-EXISTS (1 source: arxiv WebFetch) | "Rethinking KV Cache Eviction via a Unified Information-Theoretic Objective" (CapKV) | NO — KV-cache eviction axis |
| 2605.04178 | CONFIRMED-EXISTS (1 source: arxiv WebFetch) | "Microbenchmark-Driven Analytical Performance Modeling Across Modern GPU Architectures" | NO — GPU perf modeling |
| 2604.13519 | **UNRESOLVED / NOT-CONFIRMED** | WebFetch summary-model REFUSED (future-date guard); WebSearch did NOT surface this exact id | UNKNOWN — could not authenticate; treat as NOT-a-confirmed-non-collision |

### >>> LOUD FLAG: 2601.11580 "Speculative Decoding: Performance or Illusion?" <<<
Independently confirmed REAL (arxiv + ResearchGate). First systematic SD study on production vLLM
(v0.10.1.1, H100; n-gram/EAGLE/EAGLE-3/Draft/MTP; Llama3.1-8B & Llama3-70B; 6 datasets incl.
ShareGPT chat, InstructCoder code-edit, GSM8K). **Key overlap:** finds "acceptance length varies
markedly across OUTPUT TOKEN POSITIONS, requests, and datasets" and computes a theoretical SD upper
bound from "position-specific acceptance statistics."
- WHY IT IS A COLLISION RISK: it already establishes that acceptance is POSITION-dependent on real
  vLLM SD telemetry — i.e., generic decode-position acceptance variation is now PUBLISHED prior art.
  Our L1 "real vLLM accepted-length telemetry" (committee fix #7) overlaps its method.
- WHY IT IS STILL DIFFERENTIABLE (novelty survives, narrowed): 2601.11580 reports position variation
  GENERICALLY (decode offset from request start, aggregated over datasets); it does NOT (a) isolate
  the TOOL-RESULT RESUMPTION BOUNDARY as the causal driver on AGENTIC tool-calling trajectories,
  (b) run the content-type-matched-null / context-shift / entropy controls, or (c) make the
  boundary-aware-scheduling claim. Our contribution must be framed as: "we localize the WHY of
  position-dependent acceptance to the tool-result boundary, with falsification controls, on agentic
  workloads" — NOT "we discover position-dependent acceptance" (that is now 2601.11580's).
- ACTION: cite 2601.11580 as both MOTIVATION and the must-beat baseline for L1; sharpen CLAIM-0013
  framing to the boundary-localization + controls. If L0 nulls, 2601.11580 + 2510.02128 are the
  corroborating prior art for the negative note.

### Note on single-source confirmations
2604.14682 / 2602.10238 / 2604.25975 / 2605.04178 are single-source (WebFetch content-read only); the
summary model flagged future submission dates. None occupy the position/boundary axis, so collision
risk is LOW regardless; existence asserted at single-source confidence. 2604.13519 remains UNRESOLVED
and must NOT be treated as a confirmed non-collision.

------------------------------------------------------------------------
## CLAIM-0013 L0 RESULT (EXP-0046, 2026-06-01) — added post-run
**Outcome: FALSIFIED at L0 (clean kill), both corpora.** Top-1-agreement proxy on CC (n=70) + Codex
(n=76). Real signal = single-token (d=1) acceptance collapse (acc 0.025/0.051 vs interior 0.253/0.271,
Holm-sig, replicated) — but the content-type-matched null (control 1) reproduces it (CC splice d=1 pen
0.239 ~ boundary 0.228; Codex splice 0.263 > boundary 0.220). diff_content CI includes 0 (CC) / negative
(Codex); no K=8 cliff (1/8 Holm-sig vs >=4 required); does not survive entropy conditioning. => the
position-dependent acceptance reported generically by **2601.11580** is NOT attributable to the
tool-result boundary on agentic traces; corroborates **2510.02128** (content/task, not position).
Artifact: projects/PROJ-0004/artifacts/NEGRESULT_CLAIM-0013_tool_boundary_acceptance_L0.md. No L1 spend
motivated. (2604.13519 remains UNRESOLVED but is moot for a negative result.)

------------------------------------------------------------------------
## CLAIM-0015 (Format-Transition Speculation Cost) — prior-art verification (researcher-0015-L0-r5, 2026-06-01T12:57Z)
Verified via WebFetch/WebSearch against arxiv.org. Each "exists" below is content-read from the abstract page.

### COLLISION FLAG (carried from r4) — RESOLVED: DIFFERENTIATED, novelty survives
- **2601.11580 "Speculative Decoding: Performance or Illusion?"** (Liu, Yu, Park, Stoica, Cheung) —
  **CONFIRMED-EXISTS** (2-source: prior r4 confirmation + this WebFetch). Systematic vLLM study of SD
  variants (n-gram/EAGLE/EAGLE-3/Draft-Model/MTP); establishes a theoretical speedup upper bound and reports
  **"acceptance length varies markedly across output token positions, requests, and datasets."**
  => establishes GENERIC position-dependent acceptance. **DOES NOT** propose format-class pre-draft gating,
  does NOT use a length+entropy joint baseline, does NOT localize to the content-format transition, and lacks
  all 4 of our controls. **NOT A NOVELTY KILL.** DIFFERENTIATION (explicit): CLAIM-0015 contributes
  (i) localization to the FORMAT-TRANSITION boundary, (ii) the length+entropy JOINT baseline discriminator
  (RE-1), (iii) matched-format prose->prose splice control (RE-3), (iv) cross-corpus split (RE-4),
  (v) d=1 concentration test (RE-6), (vi) format-class-vs-draft-entropy head-to-head ROC (RE-7). If our L0
  nulls, 2601.11580 is the corroborating prior art for the negative (its position-dependence is NOT format-
  transition-attributable, mirroring how EXP-0046 found it is not tool-boundary-attributable).

### 6-CITATION MANDATORY VERIFY (all CONFIRMED-EXISTS, all NON-COLLIDING with model-free pre-draft format gating)
- **SVIP 2411.18462** "Draft Model Knows When to Stop: Self-Verification SD for Long-Form Generation"
  (Zhang, Xu, Liang, Chen, He, Wang, Tu) — CONFIRMED. Training-free dynamic draft LENGTH via **draft
  entropy** at RUNTIME ("a high entropy indicates a low acceptance rate"). = the draft-entropy-thresholding
  baseline (RE-7). RUNTIME draft-confidence, NOT pre-draft model-free format-class. Non-collision; it IS a
  required baseline our format-class predictor must beat (RE-1/RE-7).
- **Nightjar 2512.22420** "Nightjar: Dynamic Adaptive SD for LLM Serving" (Li, Zhang, Zhang, Wang, Fu, Lai)
  — CONFIRMED. MAB planner that **"proactively disables SD when the planner determines speculation is no
  longer beneficial"** + CPU draft offload, resource/batch-aware. RUNTIME load-adaptive disabling, NOT
  format-class. Non-collision (added to mandatory related-work per VERDICT-0054).
- **Prompt Cache 2311.04934** "Prompt Cache: Modular Attention Reuse for Low-Latency Inference" (Gim et al.,
  MLSys'24) — CONFIRMED. Precompute/reuse attention states of recurring prompt segments. KV/attention reuse,
  NOT SD acceptance. Non-collision; contextual (tool results are the dynamic non-cacheable segment).
- **Don't-Break-the-Cache 2601.06007** "An Evaluation of Prompt Caching for Long-Horizon Agentic Tasks"
  (Lumer et al.) — CONFIRMED. Evaluates caching strategies incl. **excluding dynamic tool results**; agentic
  multi-turn. NOT SD. Non-collision; corroborates that tool-result injections are the disruptive agentic
  event our claim is about.
- **Sennrich BPE 1508.07909** "Neural Machine Translation of Rare Words with Subword Units" (Sennrich,
  Haddow, Birch, ACL'16) — CONFIRMED. BPE/subword units; rare words split into smaller subwords. Foundational
  context: non-prose payloads (JSON/code/stdout) tokenize into rarer subword sequences, which underpins WHY a
  length+entropy joint baseline could absorb the format effect (RE-1 risk). Non-collision; cited for the
  tokenization-distribution mechanism.
- **TALON 2601.07353** "TALON: Confidence-Aware SD with Adaptive Token Trees" (Liu, Lv, Shen, Sun, Sun) —
  RE-VERIFIED CONFIRMED. Training-free budget-driven adaptive tree; deterministic-vs-uncertain branches drive
  tree shape ("deep-and-narrow for deterministic contexts, shallow-and-wide for uncertain branches").
  CONFIDENCE/uncertainty gating under token budget, NOT content-format. Non-collision; adaptive-SD-family baseline.
- **SpecBound 2604.12247** "SpecBound: Adaptive Bounded Self-Speculation with Layer-wise Confidence
  Calibration" (Wen, Feng) — RE-VERIFIED CONFIRMED (content-read; future-dated submission noted, single-source
  existence). Self-draft; bounds speculation length by **per-token decoding difficulty** + layer-wise
  temperature annealing of early-exit confidence. CONFIDENCE/difficulty gating, NOT format. Non-collision;
  adaptive-SD-family baseline.

### NOVELTY CELL ASSESSMENT (for the committee; researcher does NOT decide novelty)
The adaptive-SD family (SVIP/TALON/SpecBound/Nightjar/SpecDec++) ALL gate on RUNTIME draft confidence /
entropy / difficulty / load — i.e. they need a draft forward (or load signal) to decide. CLAIM-0015's distinct
cell = **model-free, PRE-draft suppression keyed on the injected payload's FORMAT CLASS**, justified ONLY IF
format-class beats both (a) the length+entropy joint null and (b) draft-entropy thresholding (RE-1/RE-7). No
verified prior work occupies that exact cell. The whole novelty therefore lives or dies on RE-1's dAUC lower
bound (load-bearing). Honest risk: format-class may merely proxy payload length + subword-rarity (Sennrich) ->
RE-1 kill -> collapses into the confidence-gated family. EXP-0050 is built to detect exactly that.
