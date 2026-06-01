# _NEW PROJECT CHARTERS — candidate seeds for PROJ-0006 / PROJ-0007

**Author:** research-design researcher (sub-agent, orchestrator dispatch)
**Node:** cli:dengcchi-mac · **Instance:** /Users/dengcchi/autonomous-research
**Date:** 2026-06-01
**Purpose:** Draft 3 NEW-project candidate charters (topic-bias areas only) for a hostile design committee to
run, then seed the 2 strongest as PROJ-0006 / PROJ-0007. NOTHING seeded here; design-only deliverable.

**Topic bias (config new_project_topic_bias):** agent-infra / inference-optimization / llm-serving / kv-cache /
agentic-systems. All 3 charters are inside this set.

## OCCUPIED-TERRITORY SNAPSHOT (what PROJ-0001..0005 + the cemetery already own — every charter below is checked against this)
- **PROJ-0001 (DONE/published):** HW CUDA-VMM CoW is dominated for agentic KV branching; 520K per-context mapping
  ceiling = vendor cliff; throughput collapse. PER-OP FORK-COST + MAPPING-CAPACITY axis. (CLAIM-0001..0005)
- **PROJ-0002:** SEMANTIC prefix-cache invalidation cost-map; CDC-over-radix vs PIC family. CONTENT-edit -> recompute
  fraction. (CLAIM-0006 yellow, CLAIM-0007)
- **PROJ-0003:** Agent failure attribution / recovery; failure over-dispersion (Hawkes/Cox). (CLAIM-0008..0012)
- **PROJ-0004:** DECODE-time SD draft-acceptance — within-trajectory position-indexed penalty at tool-result
  resumption boundaries, reframed as a CONTENT-FORMAT-TRANSITION cost (single-sequence acceptance dynamics). (CLAIM-0013)
- **PROJ-0005:** LEXICAL/tokenizer-layer exact-prefix KV-cache hit->miss demotion from BPE boundary churn at
  tool-result seams (prefill-time, block-granularity). (CLAIM-0014)
- **DEAD (do not revive):** HW VMM CoW (CLAIM-0001/0003), HW isolation primitive (DEAD-0001), handle attestation
  (DEAD-0002), CDC-over-radix repair MECHANISM (DEAD, Irminsul twin), super-linear VMM degradation (DEAD-0004),
  layer-stratified positional KV reuse <=1.5% (DEAD-0007), idle-window speculative prefill (DEAD-0010, occupied by
  arXiv:2511.20048 + 2605.06472), compaction-as-prefix-invalidation (DEAD, EXP-0028), position-from-boundary SD
  acceptance cliff (DEAD-0011), model-free format-class pre-draft SD gate (DEAD-0012), mid-prompt recompute
  exponent k~1.3 (DEAD-0009), descriptive injection-arrival burstiness (DO-NOT-SEED).
- **FORWARD-FRONTIER SW-side (do not collide):** ForkKV, TokenDance, Tokencake, 10X-KV-Stores, SemShareKV, KVShare,
  QKVShare, CacheSolidarity, Joint-Encoding, PolyKV, Prefill-aaS, Strata, Sparse Prefix Caching.

## INSTRUMENTS / ENV (cheapest-to-first-signal = CPU-only on existing trace corpora)
- Already-parsed Claude Code / Codex / Gemini agent-trace corpora (reused by PROJ-0003 EXP-0007/0012/0031/0033,
  PROJ-0004 EXP-0046). Mac CPU, stdlib-only, NO torch/HF heavy work on the Mac.
- H100 devgpu014: ros-vllm 0.6.6 / ros-vllm07 (vLLM 0.22 V1 KVConnector) via GPU coordinator — for OPTIONAL L1 only.
- MI350X devgpu499: fragile, host_mem_floor=400GB NEVER waived (MI350X_CRASH_POSTMORTEM binding). Avoid where possible.

---

## CANDIDATE A — Agent-Event-Phase Desynchronization Tax in Batch Speculative Decoding
**(STRONGEST + cheapest-to-first-signal — RECOMMENDED to seed as PROJ-0006. CPU-only L0 on existing corpora; clean
unoccupied co-batching axis; informative negative; lowest accounting-identity risk of the three.)**

### 1. THESIS
In batch speculative decoding (the production deployment mode), co-batched sequences accept *different* numbers
of draft tokens per round — the "ragged tensor" problem — and the round is bottlenecked to the *minimum* accepted
length (every sequence stalls on the slowest acceptor). On REAL agentic trajectories this ragged variance is not
i.i.d. per-request difficulty: it is driven by *agent-event phase* — at any wall-clock round, co-batched agent
sessions are in different structural phases (mid-tool-result-injection low-acceptance transition vs formulaic
high-acceptance resumption vs free-form reasoning), and that phase is **predictable model-free from each session's
in-flight agent event stream** (last tool returned, tokens-since-tool-return). THEREFORE a structure-aware
**batch-composition / phase-alignment** policy — group sessions whose predicted acceptance-phase is similar into
the same SD micro-batch — measurably reduces the min-bound ragged tax (raises mean accepted-length-per-round at
fixed batch size) at ZERO accuracy change (SD is exact). The falsifiable content is that the *agent-event-conditioned*
component of ragged-acceptance variance is load-bearing OVER a per-request-difficulty baseline.

### 2. NOVELTY vs PRIOR ART (web-verified 2026-06-01, body-level deltas + arXiv IDs)
- **"Batch Speculative Decoding Done Right" (arXiv:2510.22876)** — NAMES the ragged-tensor problem but its
  contribution is *output-distribution CORRECTNESS* (existing batch-SD impls violate exactness under ragged
  acceptance). Delta: we are not a correctness paper; we characterize the *throughput tax* of ragged acceptance
  and attribute its predictable structure to agent events, then drive a batch-composition mitigation. Different
  dependent variable (goodput vs distributional validity). MUST-CITE as the ragged-tensor primitive.
- **TETRIS (ACL 2025, "Optimal Draft Token Selection for Batch SD")** — selects, per round, WHICH proposed draft
  tokens across the batch to verify/accept to maximize batch throughput. Delta + NON-COLLISION: TETRIS optimizes
  *token selection within a given batch composition*; we change the *batch composition itself* using a model-free
  agent-phase predictor decided BEFORE drafting. Orthogonal lever; we must show phase-aligned composition adds
  goodput over TETRIS-style in-batch selection (or is composable with it), not restate it.
- **ECHO (arXiv:2604.09603, "Elastic SD with Sparse Gating for High-Concurrency")** — gates *whether each request
  speculates* based on the compute-bound high-concurrency regime (verification compute is the bottleneck). Delta:
  ECHO's gate is a per-request speculate/no-speculate decision keyed on concurrency; ours is a *cross-request
  phase-grouping* decision keyed on agent-trajectory structure. We must show the agent-phase signal adds over an
  ECHO-style concurrency/per-request gate (the discriminator below).
- **"Optimizing SD for Serving Using Goodput" (arXiv:2406.14066, Liu et al.)** — picks the global proposed length
  to maximize goodput from an aggregate acceptance-rate model. Delta: that is a single global knob from aggregate
  statistics; we exploit *within-batch, within-trajectory* phase heterogeneity that a global length ignores.
- **MineDraft (arXiv:2603.18016) / SpecRouter (arXiv:2505.07680) / Semi-Clairvoyant SD scheduling
  (arXiv:2505.17074)** — batch-parallel drafting / multi-level routing / SD request scheduling. Delta: none compose
  the batch by *predicted agent-event acceptance phase*; scheduling there is request-level priority, not
  intra-round phase alignment of the verification tensor.
- **"Disparate Impacts of SD" (arXiv:2510.02128) / "Acceptance Dynamics Across Cognitive Domains"
  (arXiv:2604.14682)** — acceptance varies by TASK/drafter-fitness (global, per-request). THIS IS THE CONFOUND we
  must beat: ragged variance could be pure per-request task difficulty, not agent phase. Our discriminator
  (below) is designed to isolate the agent-event-conditioned component over a per-request difficulty baseline.
- **NON-COLLISION check:** distinct from PROJ-0004 (single-sequence position-indexed acceptance penalty; we are
  the CROSS-SEQUENCE BATCH-COMPOSITION consequence of phase heterogeneity — a different unit of analysis and a
  different lever). Distinct from PROJ-0002/0005 (prefill-time). Not DEAD-0010/0012 (no idle-window prefill, no
  pre-draft format gate as the claim — the claim is batch composition). Not in any cemetery duplicate_pattern.

### 3. FIRST FALSIFIABLE CLAIM (CLAIM-shaped)
CLAIM-A0: "Across >=2 agent-trace corpora, in a simulated batch-SD verification model (batch round bottlenecked to
the min accepted length over the co-batched sequences), (a) the realized ragged tax (mean lost-acceptance =
mean_per_round[ max_in_batch(accept_len) - min_in_batch(accept_len) ], equivalently the goodput gap vs a
synchronized-phase ideal) has a 95% session-clustered-bootstrap CI excluding 0; AND (b) an agent-event-phase
predictor (features: last-tool-class, tokens-since-tool-return bucketed) predicts per-sequence per-round accepted
length with a session-clustered dAUC (or dR^2) over a PER-REQUEST-DIFFICULTY-MATCHED baseline (sequence id +
running-mean-acceptance + local target entropy) whose 95% CI EXCLUDES 0 — i.e. the agent-phase signal is
load-bearing beyond per-request difficulty (the 2510.02128 confound); AND (c) a phase-aligned batch-composition
policy (greedily co-batch sequences with similar predicted phase) recovers a measured fraction X% of the ragged
tax (raises mean accepted-length-per-round at fixed batch size B) in simulation. PASS requires (a) AND (b) AND
(c)>0. NEGATIVE/KILL: (b) dAUC CI includes 0 -> ragged variance is per-request difficulty, NOT agent phase ->
phase-aligned composition cannot help -> clean publishable negative (tells serving teams: compose batches by
per-request acceptance estimate, agent structure adds nothing); OR (a) ragged tax ~0 under realistic batch sizes
-> ragged tensor is not a material agent-serving cost (also informative)."

### 3a. DISCRIMINATOR DESIGN (load-bearing; learned from CLAIM-0015 RE-1 = dAUC over a length+entropy joint baseline)
The whole claim lives or dies on leg (b). The pre-registered baseline is a JOINT per-request-difficulty model:
{sequence fixed effect (running mean acceptance) + local target-distribution entropy proxy + position-in-decode}.
The agent-phase predictor must beat THAT baseline's AUC/R^2 with a CI excluding 0, on held-out sessions, with the
session as the bootstrap cluster unit. This directly attacks the confound that "agent phase" is just a proxy for
"this is an easy/hard request" or "this token is high/low entropy." Permutation null: shuffle the tool-event
labels WITHIN session (preserving the per-request difficulty marginal) and re-fit; the real dAUC must exceed the
permuted-null dAUC distribution.

### 4. CHEAP GATING EXP (Level-0, Mac CPU, stdlib, hours; what a negative looks like)
- **L0 (Mac CPU, reuse PROJ-0004 EXP-0046 acceptance proxy + parsed CC/Codex corpora):** (i) per sequence per
  decode position, take the top-1-agreement acceptance proxy already built in EXP-0046 as the per-token accept
  signal; segment each trajectory into agent-event phases (tool-return transition / resumption window / free
  reasoning) from the parsed event stream. (ii) Build a SIMULATED batch-SD round model: draw B sequences,
  advance each by its proposed length, the round commits min accepted length; tabulate the ragged tax across many
  random batch draws (Monte Carlo over the corpus), session-clustered bootstrap CI. (iii) Fit the phase predictor
  and the per-request-difficulty baseline; report dAUC with CI + the within-session permutation null (leg b).
  (iv) Re-run the Monte Carlo under a phase-aligned composition policy; report recovered fraction X% (leg c).
  Pure CPU, stdlib, no GPU, no weights — first signal in HOURS.
- **Negative look:** dAUC CI includes 0 (phase not load-bearing over difficulty) OR ragged tax ~0 at realistic B.
  Either is a clean, honest, publishable negative and is reported as such (no "promising" spin).
- **L1 (H100 devgpu014, OPTIONAL, GPU-coordinator gated):** confirm with REAL vLLM batch-SD accepted-length
  telemetry (ngram/EAGLE draft) that (1) the simulated ragged tax is real, not a 2-gram-proxy artifact, and (2)
  phase-aligned composition recovers wall-clock goodput on a capped co-batched trajectory set. Watchdog + HBM cap;
  H100 only (honor MI350X postmortem). Spend ONLY if L0 leg (b) clears the dAUC gate.

### 5. WHY IT MATTERS (Meta inference-opt / agent-infra)
Batch SD is THE production SD mode; agent serving (coding agents, tool-callers) co-batches many concurrent
sessions, and decode dominates cost. If agent-event phase predictably structures ragged-acceptance variance, a
model-free, harness-decidable batch-composition rule recovers verification goodput at zero accuracy/quality risk
(SD is exact) — a real fleet-efficiency lever on a Meta-shaped workload, distinct from any single-sequence SD
characterization. The negative (variance is per-request difficulty) hands serving teams a clean "compose by
per-request acceptance estimate, ignore agent structure" rule and retires a plausible-but-empty lever cheaply.

### 6. ACCOUNTING-IDENTITY RISK (anti-coping, stated up front)
Leg (a) alone (ragged tax > 0) is close to an arithmetic identity (min <= max over a heterogeneous batch is
trivially >=0). It is NOT the claim. The load-bearing, non-identity content is leg (b): that AGENT-EVENT PHASE
predicts the per-sequence acceptance over a per-request-difficulty baseline (a measured, falsifiable, beat-the-
confound result), and leg (c): that a phase-aligned composition recovers a measured fraction. (b)+(c) are the
contribution; (a) is just the setup. This is what keeps A out of the DEAD-0009/0010 / CLAIM-0006 "reduces to a
break-even identity" trap.

### 7. FEASIBILITY on-node
- L0: Mac CPU stdlib, reuses EXP-0046 proxy + parsed corpora -> first signal in hours, no GPU, no install. The
  batch-SD Monte Carlo round model is a few dozen lines. HIGHEST reuse, lowest first-signal cost.
- L1: ros-vllm07 batch-SD accepted-length telemetry on H100, bounded + watchdogged, via GPU coordinator. NOT
  required for the first signal.

---

## CANDIDATE B — Realized Cross-Session Prefix-Reuse Ceiling: tool-schema / system-prompt drift bounds APC hit-rate on agent fleets
**(CPU-first census + structural-ceiling claim; cleanest "measure the realized bound + name the structural cause"
axis; solid #2 to seed as PROJ-0007. Manage the accounting-identity risk explicitly.)**

### 1. THESIS
Prefix-cache reuse (vLLM APC / RadixAttention / provider prompt caching) across CONCURRENT agent sessions is
universally assumed to be bounded only by the shared-prefix fraction (system prompt + tool schema). On REAL
multi-session agent fleets the *realized* concurrent-session reuse is bounded ABOVE that, by a structural cause:
**tool-schema / system-prompt micro-drift** (per-session injected timestamps, session IDs, dynamically-ordered
tool lists, tenant-specific schema fields) that breaks the cross-session shared prefix EARLY — so the realized
cross-session APC hit-rate has a structural ceiling well below the naive shared-text fraction, and the LOCATION
of the first cross-session divergence is **predictable model-free from the prefix-assembly template's drift class**
(volatile-field position). The falsifiable content is that realized cross-session reuse is bounded by a NAMED,
PREDICTABLE drift cause — measured over a drift-free template baseline — NOT merely equal to the shared-text fraction.

### 2. NOVELTY vs PRIOR ART (web-verified 2026-06-01, body-level deltas + arXiv IDs)
- **Prompt Cache (arXiv:2311.04934)** — modular attention reuse over overlapping segments (system msg, templates).
  Delta: Prompt Cache ENGINEERS reuse by pre-declaring reusable modules; we MEASURE the realized cross-session
  ceiling on un-instrumented real agent traces and attribute the shortfall to drift class. They build a mechanism;
  we characterize a fleet-level ceiling + its structural cause.
- **KVFlow (arXiv:2507.07400)** — prefix-cache scheduling/reuse for multi-AGENT workflows (within a workflow).
  Delta + NON-COLLISION: KVFlow optimizes reuse scheduling assuming the shared prefix is shared; we quantify the
  upstream ceiling on HOW MUCH is actually cross-session-shared on real fleets and why it falls short. We do NOT
  propose a scheduler (that is KVFlow / Continuum territory).
- **Tail-Optimized Caching (arXiv:2510.15152)** — optimal prompt-caching policy for TAIL latency. Delta: a policy
  result on hit/miss economics; we are a census + structural-ceiling characterization, not a policy. Cite as the
  policy frontier our ceiling feeds.
- **Continuum (arXiv:2511.02230, KV-TTL)** — multi-turn agent scheduling with KV time-to-live (WITHIN-session
  retention across tool gaps). Delta: Continuum is intra-session temporal retention; ours is CROSS-session spatial
  reuse ceiling. Different axis. NON-COLLISION explicit.
- **PROJ-0005 / CLAIM-0014 (own, sibling)** — BPE re-tokenization seam churn demotes a WITHIN-session exact-prefix
  hit to a miss at the tool-result seam. Delta + NON-COLLISION: PROJ-0005 is intra-session, lexical, at the tool
  seam; B is CROSS-session, structural template drift (volatile fields in the system/tool-schema prefix), at the
  prefix head. Must cite PROJ-0005 to disambiguate: B's churn is in the SHARED HEAD across sessions, not the tail
  seam within a session. (If L0 finds the dominant cross-session divergence is actually BPE-seam-driven, B FOLDS
  into PROJ-0005 and is killed — a clean honest outcome, pre-registered.)
- **DigitalOcean/Anthropic prompt-caching practitioner guidance** — "session-affinity routing, ordered prompt
  templates" already named as hit-rate levers (UNVERIFIED beyond blog-level; treat as practitioner folklore, not
  a measured ceiling). Delta: we give the MEASURED ceiling + a falsifiable drift-class predictor on real traces,
  which the practitioner guidance asserts qualitatively but does not quantify.
- **NON-COLLISION check:** distinct from DEAD-0006 (token-prefix predicts SHARING — B is the opposite: token
  prefix FAILS to share across sessions because of drift), from PROJ-0002 (semantic invalidation), from the
  CacheSolidarity/Joint-Encoding side-channel & encoding frontier (B is a benign efficiency census, no security
  claim, no encoding mechanism). Not in any cemetery duplicate_pattern.

### 3. FIRST FALSIFIABLE CLAIM
CLAIM-B0: "Across >=2 agent-trace corpora and >=2 production tokenizers, when concurrent agent sessions are
assembled as the engine would (system prompt + tool schema + turn history), the realized cross-session
longest-common-token-ID-prefix (LCP), measured at BLOCK granularity against a real block-hash schedule
(block=16), is SHORTER than the naive shared-TEXT-prefix length by a margin whose 95% CI excludes 0, the
shortfall EXCEEDS a drift-free-template control (sessions assembled with volatile fields canonicalized) with CI>0
on the difference (the pre-registered anti-tautology endpoint), AND the position of first cross-session block
divergence is predicted (AUC CI>0.5) by the prefix template's drift class alone (model-free, volatile-field
position). PASS = all three. NEGATIVE/KILL: shortfall ~0 or == the drift-free control -> engines/templates
already canonicalize the shared head, cross-session reuse IS the shared-text fraction (then the ceiling claim is
empty and B dies cleanly, telling serving teams cross-session reuse is not silently drift-bounded); OR
drift-class non-predictive -> unstructured, not a characterizable ceiling -> KILL."

### 3a. ACCOUNTING-IDENTITY RISK (anti-coping, stated up front — this is B's main hazard)
"Realized cross-session hit-rate <= shared-prefix fraction" is a TAUTOLOGY. B is explicitly NOT that claim. The
non-identity, load-bearing content is the DELTA over the DRIFT-FREE-TEMPLATE control (leg 2): that realized reuse
falls short of the shared-TEXT prefix specifically BECAUSE of volatile-field drift, by a measured margin that
VANISHES when volatile fields are canonicalized. That delta is a measured, falsifiable, mechanism-attributed
result, not an arithmetic identity. If the committee judges leg-2 still reduces to "drift breaks prefix =
definitionally," B should be DOWNGRADED — that is the honest failure mode and the reason B is ranked #2, not #1.

### 4. CHEAP GATING EXP (Level-0, Mac CPU, stdlib + one HF tokenizer, hours)
- **L0 (Mac CPU):** from the parsed CC/Codex/Gemini corpora, reconstruct per-session prefix assembly (system
  prompt + tool schema + history) as the engine would; tokenize with >=2 production tokenizers; for each pair of
  concurrent sessions compute block-granularity cross-session LCP; compare to naive shared-text-prefix length;
  bucket the first-divergence position by drift class (timestamp / session-id / tool-ordering / tenant-field);
  bootstrap CI; run the drift-free-template control (canonicalize volatile fields) as the anti-tautology endpoint;
  fit the model-free drift-class predictor + report AUC CI. Pure tokenizer, no GPU, no weights.
- **Negative look:** shortfall ~0 / == control / drift-class non-predictive -> kill cheaply, publishable negative.
- **L1 (H100 devgpu014, OPTIONAL, bounded):** confirm the simulated cross-session LCP shortfall converts to real
  vLLM APC cross-request cache-hit-counter shortfall + measure recovered TTFT from volatile-field canonicalization
  on a capped concurrent-session set. Watchdog + HBM cap; H100 only. MI350X not required.

### 5. WHY IT MATTERS (Meta inference-opt / agent-infra)
Cross-session prefix reuse (system prompt + tool schema shared across thousands of concurrent agent sessions) is
a dominant fleet-level TTFT/cost lever. A measured ceiling + a model-free drift-class predictor yields a trivial
mitigation (canonicalize / hoist volatile fields out of the cached head before hashing) recovering prefill FLOPs
at fleet scale. A negative (engines already canonicalize) redirects effort. Zero data-collection cost.

### 6. FEASIBILITY on-node
- L0: Mac CPU + one HF tokenizer (or pure-Python BPE) -> first signal in hours, no GPU, no weights. Reuses the
  PROJ-0003 trace corpus. Tokenizer is the only dependency (already used by PROJ-0005).
- L1: H100 devgpu014 ros-vllm 0.6.6 APC cross-request hit/miss counters; bounded + watchdogged.
- Risk: the drift-free-template control is the make-or-break (anti-tautology). If volatile-field reconstruction
  from the parsed traces is unreliable, B's anti-tautology endpoint weakens -> fall back to A.

---

## CANDIDATE C — Verification-Compute Crossover: agent-trajectory structure predicts WHERE batch-SD turns net-negative
**(CPU-first analytic + trace overlay; companion / weakest of the three by design — carries the highest
accounting-identity risk; included for committee completeness, NOT recommended as a primary seed.)**

### 1. THESIS
In high-concurrency batch serving, SD flips from a speedup to a net SLOWDOWN once verification compute (target
forward over B*(proposed_len) tokens) exceeds the saved decode steps — the well-known compute-bound regime (ECHO
2604.09603). The (modest) new content: the crossover operating point is reached MORE OFTEN, and is PREDICTABLE,
in the LOW-acceptance agent-event phases (post-tool transition tokens), so a model-free, agent-phase-gated
"speculate / don't speculate" decision (suppress speculation during predicted low-acceptance agent phases)
recovers wasted verification FLOPs vs a phase-blind global SD on / off.

### 2. NOVELTY vs PRIOR ART (web-verified 2026-06-01) + HONEST WEAKNESS
- **ECHO (arXiv:2604.09603)** — elastic SD with sparse gating for the compute-bound high-concurrency regime;
  gates speculation per request. Delta: ECHO gates on concurrency/compute-bound state; we gate on predicted
  agent-event ACCEPTANCE PHASE. THIN delta — ECHO's gate could already subsume an "acceptance is currently low"
  signal. We MUST show the agent-phase gate beats an ECHO-style acceptance-estimate gate with CI>0; if it does
  not, C is DEAD (reduces to ECHO + a per-request acceptance estimate).
- **Goodput SD (arXiv:2406.14066)** — global proposed-length to maximize goodput from aggregate acceptance.
  Delta: per-phase rather than global. **ACCOUNTING-IDENTITY HAZARD:** the speculate-or-not break-even
  (expected accepted tokens vs verification cost) is a generic accounting identity — the SAME failure class that
  killed DEAD-0010 (idle-window break-even) and DEAD-0009 (recompute exponent) and dogged CLAIM-0006. C's
  contribution can ONLY survive if the agent-phase gate beats the break-even identity AND beats ECHO's gate on
  measured goodput; the identity itself is NOT a contribution.
- **NON-COLLISION:** overlaps PROJ-0004 (single-sequence low-acceptance phase) and Candidate A (batch SD) — C is
  the per-request speculate/skip consequence, the weakest, most-occupied framing. Distinct from DEAD-0010 only if
  it beats the break-even identity on a MEASURED goodput curve.

### 3. FIRST FALSIFIABLE CLAIM
CLAIM-C0: "In a batch-SD goodput model on >=2 agent corpora, an agent-event-phase-gated speculate/skip policy
recovers verification FLOPs / raises goodput over (a) phase-blind global SD AND (b) an ECHO-style per-request
acceptance-estimate gate, with 95% CI excluding 0 on BOTH. PASS requires beating BOTH. KILL: no advantage over
(b) -> reduces to ECHO + acceptance estimate, or to the speculate-or-skip break-even identity (DEAD-0010 class)."

### 4. CHEAP GATING EXP (Level-0, Mac CPU, hours)
- **L0:** reuse EXP-0046 acceptance proxy + corpora; build the batch-SD goodput model (saved decode vs
  verification compute over B); overlay agent-event phase; compare phase-gated vs phase-blind vs ECHO-style
  acceptance-estimate gate; session-clustered bootstrap CI on the pairwise goodput advantage.
- **Negative look:** no win over the ECHO-style gate -> KILL (most likely outcome; C is high-risk).

### 5. WHY IT MATTERS / 6. FEASIBILITY
Same family as A (verification-FLOP recovery on agent serving), CPU-first on existing corpora. But C is the
weakest: thin delta vs ECHO + a live accounting-identity hazard (break-even). Included only so the committee can
hostile-test it against A; NOT recommended as a primary seed.

---

## RECOMMENDATION (rank for seeding PROJ-0006 / PROJ-0007)

**Seed CANDIDATE A as PROJ-0006 (strongest).**
1. Cleanest unoccupied axis: batch-SD ragged-acceptance is owned at the CORRECTNESS level (2510.22876) and the
   in-batch token-selection level (TETRIS) and the concurrency-gate level (ECHO) — but the *agent-event-phase
   batch-COMPOSITION* lever, and the claim that agent structure (not per-request difficulty) drives the ragged
   tax, is empty. CROSS-SEQUENCE unit of analysis -> does not collide with PROJ-0004's single-sequence penalty.
2. Cheapest-to-first-signal: CPU-only, stdlib, reuses the EXP-0046 acceptance proxy + parsed corpora; first
   signal in hours; no GPU, no weights, no install.
3. Lowest accounting-identity risk of the three: the load-bearing leg (b) is a MEASURED dAUC over a per-request-
   difficulty baseline with a within-session permutation null (designed to beat the 2510.02128 confound, learning
   from CLAIM-0015 RE-1) — not a break-even arithmetic identity. Leg (a) is acknowledged as the trivial setup.
4. Best instruments fit + informative either way: phase-aligned composition recovers goodput (positive) or
   ragged variance is per-request difficulty (clean negative -> "compose by acceptance estimate, ignore agent
   structure"). Optional H100 L1 confirms wall-clock only if the L0 dAUC gate clears.

**Seed CANDIDATE B as PROJ-0007 (solid #2).**
1. Clean "measure the realized ceiling + name the structural cause" axis: prior work BUILDS cross-session reuse
   (Prompt Cache) or SCHEDULES it (KVFlow/Continuum); none measures the realized concurrent-session reuse ceiling
   on real agent fleets and attributes the shortfall to tool-schema/system-prompt drift with a model-free
   drift-class predictor. Cross-session + structural -> orthogonal to PROJ-0005 (intra-session, lexical seam) and
   PROJ-0002 (semantic). CPU-first, hours, reuses traces + one tokenizer.
2. Honest hazard, managed: the bare ceiling ("hit-rate <= shared-text fraction") is a tautology; B's contribution
   is the DELTA over a drift-free-template control. That control is the make-or-break and the reason B is #2, not
   tied-#1. If the committee judges leg-2 still reduces to "drift breaks prefix definitionally," B downgrades.

**Do NOT seed CANDIDATE C** as a primary. C is included for committee completeness and hostile contrast; it has a
thin delta vs ECHO (2604.09603) and a live speculate-or-skip break-even accounting-identity hazard (DEAD-0010
class). It can only survive if it beats an ECHO-style per-request acceptance gate on measured goodput — most
likely it does not. If the committee KILLS A or B at L0, C is the fallback only after its identity risk is
re-examined.

**Why A+B over A+C:** A and B are on DIFFERENT layers (A = decode-time batch-SD verification goodput; B =
prefill-time cross-session prefix reuse ceiling), so they diversify the portfolio across the two dominant agent-
serving cost centers (decode + prefill), both CPU-first, both with pre-registered anti-confound / anti-tautology
endpoints, neither colliding with PROJ-0001..0005 or the cemetery. A+C would double down on batch-SD verification
(redundant axis + C's identity risk).

## CITATION-VERIFICATION NOTES (honesty)
- All arXiv IDs above were surfaced by live web search on 2026-06-01 with title + abstract excerpts (2510.22876,
  2604.09603, 2406.14066 [v1 2406], 2510.02128, 2604.14682, 2603.18016, 2505.07680, 2505.17074, 2311.04934,
  2507.07400, 2510.15152, 2511.02230). TETRIS sourced from ACL Anthology 2025.acl-long.1598 (no arXiv id
  confirmed in search — cite as ACL 2025; arXiv id UNVERIFIED).
- BODY-LEVEL deltas above are based on ABSTRACTS + the existing academic_map body-verification notes (KVFlow,
  Continuum, Prompt Cache are already body-characterized in the registry). Full-body verification of 2510.22876,
  2604.09603, TETRIS, 2510.15152 is OWED before promotion (abstract-level here) — flagged for the committee, not
  claimed as body-verified.
- DigitalOcean / Anthropic / Medium prompt-caching guidance for Candidate B is PRACTITIONER-FOLKLORE
  (blog-level), explicitly marked UNVERIFIED as a measured ceiling; B's novelty does not rest on it.
