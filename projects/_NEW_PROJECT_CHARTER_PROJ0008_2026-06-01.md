# _NEW PROJECT CHARTER — candidate seeds for PROJ-0008

**Author:** research-design researcher (sub-agent, orchestrator dispatch)
**Node:** cli:dengcchi-mac · **Instance:** /Users/dengcchi/autonomous-research
**Date:** 2026-06-01
**Purpose:** Draft 2 NEW-project candidate charters (topic-bias areas only) for a hostile design committee.
Seed the strongest as PROJ-0008. NOTHING seeded here; design-only deliverable.

**Topic bias (config new_project_topic_bias):** agent-infra / inference-optimization / llm-serving / kv-cache /
agentic-systems. Both charters are inside this set.

---

## INSTRUMENT REALITY (drives both designs — read first)
The cheapest-to-first-signal instrument is the already-parsed CC/Codex/Gemini agent-trace corpora on Mac CPU
(stdlib-only). A HARD lesson from the PROJ-0004 lineage (DEAD-0011/0012): the EXP-0046 trigram top-1-agreement
proxy **structurally erases multi-token positional SD signal at d>=3** (2-token proxy window). So decode-time
*positional* acceptance axes are EXHAUSTED at L0 (DEAD-0011 position cliff, DEAD-0012 format-class d=1 gate)
and CANNOT be cheaply re-opened on this instrument. What the CPU instrument CAN measure cleanly:
(i) d=1 acceptance (exhausted), and (ii) **turn / call / session-level structural quantities** (counts, byte-identity,
inter-event token gaps, determinism classes). **Both charters below are turn/call-level PREFILL-side claims**, not
decode-positional claims — by deliberate design, so the cheap-kill gate is actually decisive on this instrument
(not instrument-predetermined like DEAD-0011's d>=2 null).

## OCCUPIED-TERRITORY SNAPSHOT (checked against academic_map.yaml + cemetery + live web, 2026-06-01)
- **PROJ-0001 (DONE):** HW CUDA-VMM CoW dominated; 520K per-context mapping ceiling; throughput collapse. (CLAIM-0001..0005)
- **PROJ-0002 (yellow):** SEMANTIC prefix-cache invalidation cost-map (content-EDIT -> recompute fraction); CDC-over-radix vs PIC. (CLAIM-0006)
- **PROJ-0003 (DONE):** Agent failure attribution / recovery; failure over-dispersion (Hawkes/Cox). (CLAIM-0008..0012)
- **PROJ-0004 (reseeded):** DECODE-time SD draft-acceptance d=1 content-transition cost (CLAIM-0015 KILLED DEAD-0012; CLAIM-0013 KILLED DEAD-0011).
- **PROJ-0005 (investing):** LEXICAL/BPE re-tokenization seam churn at tool-result injection (prefill hit->miss, block-granularity). (CLAIM-0014)
- **PROJ-0006 (DONE/KILLED):** batch-SD agent-event-PHASE composition tax KILLED (DEAD-0014: phase adds nothing over static difficulty/length grouping).
- **PROJ-0007 (IN FLIGHT):** REALIZED cross-session prefix-reuse ceiling from tool-schema / system-prompt DRIFT (volatile fields break cross-session APC). (CLAIM-0017)
- **DEAD (do not revive):** HW VMM CoW; HW isolation; handle attestation; CDC-over-radix MECHANISM (Irminsul twin); super-linear VMM;
  layer-stratified positional KV reuse; recompute exponent k~1.3; **idle-window speculative prefill (DEAD-0010)**;
  compaction-as-prefix-invalidation (EXP-0028); **position-from-boundary SD cliff (DEAD-0011)**; **model-free format-class pre-draft SD gate (DEAD-0012)**;
  **verification-compute crossover = ECHO + break-even identity (DEAD-0013)**; **agent-event-PHASE batch-SD composition tax (DEAD-0014)**.
- **FORWARD-FRONTIER SW-side (do not collide):** ForkKV, TokenDance, Tokencake, 10X-KV-Stores, SemShareKV, KVShare, QKVShare,
  CacheSolidarity, Joint-Encoding, PolyKV, Prefill-aaS, Strata, Sparse Prefix Caching, DroidSpeak, PrefillShare.

---

## CANDIDATE A — Redundant Tool-Call Prefill Tax: byte-identical mid-trajectory tool re-invocations that PREFIX-CACHING STRUCTURALLY CANNOT RECOVER
**(STRONGEST + cheapest-to-first-signal — RECOMMENDED to seed as PROJ-0008. CPU-only L0 on existing corpora; clean
unoccupied prefill axis; informative negative; LOWEST accounting-identity risk; pre-measured live signal.)**

### 1. THESIS
On real long-horizon agent trajectories, a measurable fraction of tool invocations are **byte-identical (or
result-equivalent) re-invocations of an EARLIER call in the SAME session** (re-reading the same file, re-running the
same shell command, re-issuing the same search). Each such re-invocation pays a **full prefill (the re-injected
result) + a decode round** that an exact-prefix KV-cache (vLLM APC / RadixAttention block-hash / provider prompt
caching) **structurally CANNOT recover**, because the two identical calls are separated by a large, divergent span
of intervening agent tokens — so the cached *prefix* up to the second call differs from the first, and prefix-caching
only reuses *prefixes*, never *interior repeated content*. The falsifiable content: this redundant-call prefill tax
(a) is a non-trivial fraction of total tool-call prefill on >=2 corpora, (b) **SURVIVES an APC/RadixAttention prefix-reuse
baseline** (the load-bearing discriminator — the tax is NOT already eaten by prefix caching), and (c) the per-call
recoverability is predictable model-free from the call's **tool-output determinism class** (READ-stable vs WRITE/volatile).
This is a prefill-recompute *characterization on real traces* + a named structural cause, NOT a new caching mechanism.

### 2. NOVELTY vs PRIOR ART (web-verified 2026-06-01, body-level deltas + arXiv IDs)
- **ICLR-2026-submission "automatically caching tool call results" (openreview 05f7fe08...; READ/WRITE cacheability + LLM-driven
  invalidation planner)** — PROPOSES a tool-result cache (classifies READ/WRITE, infers cacheability, generates expiry/invalidation).
  Delta: they BUILD a memo system + planner and report hit-rate on benchmark tool-usage skew (BIG-bench-Hard movie-recommend: avg
  reuse 13.55). We do NOT build a cache; we MEASURE, on REAL coding-agent traces, the **prefill-FLOP tax of redundant calls that
  survives exact-prefix KV-caching**, and the *gap* between byte-identical reuse and determinism-class reuse. Their hit-rate is a
  benchmark-skew artifact; our tax is the realized waste under a *prefix-cache* baseline (a system they do not measure against).
- **LLM-dCache (arXiv:2406.06799, Microsoft)** — GPT-driven localized DATA caching for tool-augmented LLMs (cache tool data, let the
  model manage it). Delta: a mechanism for caching tool *data*; we characterize the realized *prefill-recompute* incidence + the
  APC-non-recoverability of identical re-calls on real agent sessions. Orthogonal (mechanism vs measurement-of-residual-waste).
- **SemanticALLI (arXiv:2601.16286)** — caches REASONING/intermediate logic (semantic, embedding-keyed) in agentic pipelines. Delta:
  semantic reasoning reuse; ours is exact tool-call identity + the prefix-cache non-recovery structural argument. Different keying, different cost site.
- **Agentic Compilation / "Rerun Crisis" (arXiv:2604.09718)** — web-automation agents re-querying the model in a loop; proposes
  COMPILING repetitive web tasks to skip inference. Delta: their redundancy is whole-LOOP re-execution of a repetitive task (compile-away);
  ours is *within one session* byte-identical TOOL re-calls and the precise claim that **prefix-caching cannot recover them because of
  intervening-token divergence** (a KV-cache-architecture argument they never make). We cite as motivation for "agents repeat work".
- **"Efficient LLM Serving for Agentic Workflows: A Data Systems Perspective" (arXiv:2603.16104)** — notes agentic workflows exhibit
  "extensive redundancy from overlapping prompts and intermediate results due to speculative/parallel exploration." Delta: that is a
  data-systems framing of OVERLAPPING-PREFIX redundancy (which prefix-caching DOES catch); our contribution is the COMPLEMENT —
  interior, non-prefix, exact-repeat redundancy that prefix-caching provably MISSES, quantified on real traces with the gap measured.
- **PROJ-0002 (SEMANTIC invalidation)** non-collision: PROJ-0002 = a content EDIT to a cached prefix forces recompute (edit->recompute
  cost-map). Candidate A = a byte-IDENTICAL repeat that is NOT a prefix and so is never cached at all (no edit; the repeat is interior).
  Opposite phenomenon (identity-non-reuse vs edit-invalidation). MUST cite PROJ-0002 to disambiguate.
- **PROJ-0005 (BPE seam) / PROJ-0007 (cross-session drift)** non-collision: PROJ-0005 = intra-session LEXICAL tokenizer churn demoting a
  HIT to a MISS; PROJ-0007 = CROSS-session template drift breaking the shared HEAD. Candidate A = WITHIN-session INTERIOR exact-repeat that
  was never a reusable prefix in the first place (a third, distinct miss-mode). DroidSpeak/PrefillShare/KV-relay = CROSS-agent/sub-agent
  prefill reuse (different sessions sharing context); ours is single-session interior self-repetition.
- **Non-collision vs cemetery:** distinct from DEAD-0010 (idle speculative prefill — we recompute REALIZED repeats, not speculate
  future ones), DEAD-0011/0012/0013/0014 (all DECODE-time SD; this is PREFILL). Not in any duplicate_pattern.
- **UNVERIFIED-citation flag:** the ICLR-2026 READ/WRITE tool-caching submission is anonymous-under-review (openreview PDF, no arXiv ID);
  body-read but provenance UNVERIFIED. Body-verify the 2603.16104 + 2601.16286 + 2604.09718 redundancy framings before PROMOTION
  (LOW risk, ~1hr CPU; not a seeding blocker — all are mechanism/benchmark works, none measure the APC-non-recoverable interior-repeat tax).

### 3. FIRST FALSIFIABLE CLAIM (CLAIM-shaped) — CLAIM-A0
"Across >=2 agent-trace corpora (CC + Codex; Gemini if call data permits), within-session byte-identical tool
re-invocations constitute a fraction f of total tool-call prefill tokens whose session-clustered 95% CI excludes 0,
AND this redundant-call prefill tax SURVIVES an exact-prefix KV-cache (APC/RadixAttention block-hash, block=16) baseline
— operationalized as: the second-and-later identical call's prefix (tokens 0..call_start) differs from the first call's
cached prefix for >=1 block in >=95% of repeats (so prefix-reuse recovers 0 of the repeat's prefill), with the
intervening-token gap distribution reported — AND the per-call APC-non-recoverability is predicted model-free
(AUC CI excludes 0.5) by the call's tool-output DETERMINISM CLASS (READ-stable / WRITE-mutating / VOLATILE-time-or-network)
OVER A STRONG BASELINE: the determinism-class predictor must beat (i) a raw inter-call TOKEN-GAP predictor and (ii) a
tool-CALL-FREQUENCY (popularity) predictor on the same task, dAUC 95% lower bound > 0 (the LOAD-BEARING discriminator —
learning from DEAD-0012's RE-1: beat the obvious confound, here gap+frequency, not just chance).
PASS requires: (a) f CI>0 AND (b) >=95% of repeats prefix-cache-unrecoverable (intervening divergence) AND
(c) determinism-class dAUC LB>0 over BOTH gap and frequency baselines.
FAIL / negatives (all clean + publishable): (b) fails — most repeats ARE adjacent / prefix-reusable -> APC already
recovers them -> tax is illusory, clean kill; OR (c) fails — redundancy is fully explained by inter-call token-gap or
tool popularity (no determinism-class lift) -> reduces to 'agents repeat popular tools' (a workload-distribution
restatement, demote); OR f ~ 0 -> agents rarely self-repeat -> kill."

### 4. CHEAP GATING EXP (Level-0, CPU, stdlib, hours; what a negative looks like)
- **L0 (Mac CPU, reuse EXP-0007 CC tool_result join + EXP-0037 Codex call_id dedup parsers, EXP-0042 bootstrap idioms):**
  (i) per session, extract ordered (tool_name, canonicalized-args) tuples; flag exact-identity repeats (byte-equal args).
  (ii) For each repeat: compute intervening-token gap (tokens between first call and repeat) -> APC-recoverability flag
  (gap>0 AND >=1 block of prefix divergence => prefix-cache cannot recover the repeat's prefill). (iii) Tax f = redundant-call
  prefill tokens / total tool-call prefill tokens, session-clustered bootstrap CI. (iv) Assign each tool a determinism class
  by a small fixed rule table (Read/Glob/Grep/WebFetch=READ; Edit/Write=WRITE; Bash/exec=VOLATILE-or-WRITE by command regex;
  time/random/network commands=VOLATILE). Fit a model-free class->recoverability predictor; report dAUC over the token-gap AND
  tool-frequency baselines with paired bootstrap. PRE-REGISTER all RE gates before the run.
- **PRE-MEASURED live signal (this design session, CC corpus, n=226 files):** 9.8% of within-session tool calls are byte-identical
  repeats; **100% of repeats have intervening tokens (median gap 12,512 tokens)** => prefix-caching structurally cannot recover
  them (the APC-survival discriminator already looks alive); READ dup-rate 3.1% vs WRITE/Bash 11.4% (a real, non-obvious
  determinism asymmetry — and note WRITE/Bash repeats MORE, so the naive 'READ is the cacheable class' story is WRONG, which is
  exactly the kind of confound the discriminator must adjudicate, not assume).
- **Pre-registered RE gates (load-bearing discriminator design, learning from the kills):**
  - **RE-A1 (LOAD-BEARING / KILLER):** determinism-class dAUC over the {token-gap + tool-frequency} JOINT baseline, 95% LB>0,
    BOTH corpora. If the joint baseline matches/beats class -> redundancy is gap/popularity, not determinism -> demote to
    workload-distribution restatement (the DEAD-0012 RE-1 / DEAD-0014 RE-A1 pattern: beat the obvious confound or die).
  - **RE-A2 (APC-survival, KILLER):** >=95% of repeats prefix-cache-unrecoverable. If engines/harness already canonicalize so
    repeats are adjacent/prefix-reusable -> clean kill (tax illusory).
  - **RE-A3 (result-equivalence vs byte-identity):** report byte-identical AND result-equivalent (same tool+args, different call_id)
    separately; the PRIMARY endpoint is byte-identical (conservative); equivalence is a secondary upper bound.
  - **RE-A4 (minimum effect size):** pre-register f floor >= a meaningful prefill fraction (e.g. >=2% of tool-call prefill tokens),
    not just CI>0 at large N.
  - **RE-A5 (cross-corpus):** f and class-lift must replicate sign on CC AND Codex (>=2 distinct harness families).
  - **RE-A6 (anti-tautology):** exclude trivially-cacheable adjacent retries (a re-call within K tokens of the first, e.g. a transient
    error retry) from the tax — those ARE prefix-reusable and would inflate f; the surviving tax must be the LONG-GAP interior repeats.
- **Negative look:** RE-A1 fails (gap/frequency explains it) OR RE-A2 fails (repeats prefix-reusable) OR f<2%. Each is a clean,
  publishable negative ("agent self-repetition is rare / already prefix-cached / fully popularity-driven").
- **L1 (H100 devgpu014, OPTIONAL, GPU-coordinator gated):** confirm the prefill-FLOP tax in real vLLM with APC ENABLED — replay a
  capped set of sessions, count prefill tokens recomputed at each redundant call under RadixAttention, and the recovered TTFT/prefill-FLOPs
  from an interior-content memo cache. Watchdog + HBM cap; H100 only (honor MI350X postmortem). Only spend if L0 clears RE-A1+RE-A2.

### 5. WHY IT MATTERS (Meta inference-opt / agent-infra)
Coding/tool-calling agents are the production agentic workload, and prefill dominates their cost (large re-injected tool
results). If a measurable, determinism-class-predictable fraction of tool-call prefill is byte-identical interior repetition
that prefix-caching provably cannot recover, that is (a) a clean characterization gap in the agent-serving literature (everyone
measures prefix-overlap reuse; nobody measures the interior-exact-repeat residual under an APC baseline), and (b) motivates a
cheap, model-free interior-content memo (key on tool+args determinism class, not embeddings) that recovers prefill at zero
quality risk for READ-stable calls. The negative (repeats are rare / popularity-driven / already prefix-cached) is itself a
useful 'prefix-caching is sufficient for agent self-repetition' result.

### 6. FEASIBILITY on-node
- L0: Mac CPU stdlib only; reuses EXP-0007/EXP-0037 parsers + EXP-0042 bootstrap -> first signal in HOURS, no GPU, no install.
  Live signal already measured this session (9.8% repeats, 100% prefix-unrecoverable, READ/WRITE asymmetry). HIGHEST reuse, lowest first-signal cost.
- L1: ros-vllm 0.6.6 / ros-vllm07 on H100 with APC enabled; bounded, watchdogged, via GPU coordinator. NOT required for the first signal.

### 7. ACCOUNTING-IDENTITY RISK ASSESSMENT (the gate that killed DEAD-0009/0010/0013)
LOW. The claim is an EMPIRICAL incidence + a SURVIVAL-vs-baseline test, not a derived break-even formula. f, the prefix-unrecoverability
rate, and the determinism-class dAUC are all MEASURED quantities with no closed-form identity reduction. The only identity-adjacent piece
("a repeat costs a prefill") is exactly why RE-A2 (APC-survival) and RE-A6 (exclude adjacent retries) are mandatory: without them, "a
repeat costs a prefill" would be a trivial restatement. With them, the load-bearing content is *which* repeats survive prefix-caching and
*whether determinism class predicts it over gap+popularity* — none of which is an accounting identity.

---

## CANDIDATE B — Tool-Output Determinism Ceiling: the realized cross-call KV/result reuse ceiling is bounded BELOW byte-identity by tool-output determinism CLASS
**(cheap, complementary; the prefill-side determinism-class characterization that A leans on, promoted to a standalone reuse-ceiling claim. SECOND choice — narrower, more collision-exposed to the ICLR-2026 READ/WRITE cacheability work.)**

### 1. THESIS
The naive upper bound on tool-result reuse (memoization / KV-handoff) is "fraction of calls that are byte-identical
repeats." On real agent traces this OVERSTATES achievable reuse, because many same-(tool,args) re-invocations return
DIFFERENT results (WRITE-mutating state, VOLATILE time/network output) and are NOT safely reusable. The REALIZED reuse
ceiling is bounded by tool-output DETERMINISM CLASS, and the gap between byte-identical-args incidence and
determinism-safe reuse is large and predictable model-free from tool identity + a small command-regex feature.
Falsifiable content = the determinism-class-corrected reuse ceiling is measurably BELOW the byte-identical-args ceiling
(CI>0 on the gap) and the correction is predictable model-free, OVER a 'same-args => same-result' naive baseline.

### 2. NOVELTY vs PRIOR ART (web-verified 2026-06-01)
- **ICLR-2026 READ/WRITE tool-caching submission (openreview 05f7fe08..., UNVERIFIED provenance)** — closest neighbor: classifies tools
  READ/WRITE and infers cacheability + invalidation. Delta (load-bearing): they ASSUME a READ/WRITE classification and BUILD the cache;
  we MEASURE, on real traces, how far the determinism-safe reuse ceiling falls BELOW the byte-identical-args ceiling, and show WRITE/VOLATILE
  same-args re-calls (which a naive byte-args memo would wrongly hit) are a large, predictable fraction — i.e. we quantify the *error* of
  the naive same-args assumption their planner exists to avoid. This is a characterization/measurement contribution, not a caching system.
  COLLISION RISK is real and committee-load-bearing: the delta must be 'measured realized ceiling + naive-assumption error rate', not 'a READ/WRITE cache'.
- **LLM-dCache (2406.06799), SemanticALLI (2601.16286), Don't-Break-the-Cache (2601.06007)** — caching mechanisms / prompt-cache eval;
  none measure the byte-args-vs-determinism-class reuse-ceiling GAP on real coding-agent traces. Cite as caching-landscape.
- **PROJ-0002/0005/0007 non-collision:** same as Candidate A (semantic edit / BPE seam / cross-session drift are all distinct miss-modes).
- **Cemetery:** prefill-side, not decode-SD; not in any duplicate_pattern.

### 3. FIRST FALSIFIABLE CLAIM — CLAIM-B0
"Across >=2 corpora, the determinism-safe tool-result reuse ceiling (fraction of same-(tool,args) re-calls whose result is
provably reusable: READ-stable, no intervening WRITE to the same target, non-VOLATILE) is BELOW the byte-identical-args
ceiling by a margin whose session-clustered 95% CI excludes 0, AND the per-call reuse-safety is predicted model-free
(AUC CI>0.5) by tool identity + command-regex features OVER a naive 'same-args => same-result' baseline (which predicts
all repeats reusable). PASS = gap CI>0 AND predictor AUC LB>0.5 over the naive-all-reusable baseline AND replicates on
CC+Codex. FAIL = gap ~ 0 (byte-args reuse is already safe -> naive memo is fine, clean negative) OR predictor no better
than naive (determinism class adds nothing) OR same-args re-calls too rare to bound a ceiling."

### 4. CHEAP GATING EXP (Level-0, CPU, hours)
- **L0:** reuse A's parsers; for each same-(tool,args) re-call, determine result-equivalence (compare the two tool_result payloads
  byte-wise / normalized) -> empirical 'same-args => same-result' rate per determinism class; gap = byte-args-ceiling minus
  determinism-safe-ceiling, session-clustered bootstrap CI; model-free predictor vs naive-all-reusable.
- **PRE-MEASURED hint (this session):** WRITE/Bash same-args dup-rate (11.4%) >> READ (3.1%), and Bash re-runs frequently return
  different output (state-mutating / time-varying) -> the determinism gap looks real and non-trivial; but result-equivalence must be
  measured directly (the L0 primary endpoint), not assumed.
- **Pre-registered RE gates:** RE-B1 (KILLER) gap CI>0 over the naive 'same-args reusable' baseline; RE-B2 predictor AUC LB>0.5 over
  naive; RE-B3 cross-corpus sign replication; RE-B4 minimum gap effect-size floor; RE-B5 result-equivalence measured on actual payloads
  (not inferred from tool class — anti-tautology: the class must PREDICT measured equivalence, not DEFINE it).
- **Negative look:** RE-B1 gap~0 (byte-args memo is already safe) or RE-B5 class fails to predict measured equivalence -> clean kill.
- **L1 (optional, GPU-coordinator):** quantify recovered prefill from a determinism-class-gated memo vs a naive byte-args memo (false-hit cost).

### 5. WHY IT MATTERS
Tells agent-serving cache designers the realized headroom for tool-result memoization and the error rate of the naive byte-args
assumption — a measurement the caching-system papers presuppose but never report on real traces.

### 6. FEASIBILITY
L0 Mac CPU stdlib, reuses A's parsers -> hours. L1 optional.

### 7. ACCOUNTING-IDENTITY RISK
LOW-MEDIUM. The gap and the predictor are measured. Minor risk: 'WRITE tools mutate state' is near-tautological if determinism
class is DEFINED by mutation — RE-B5 forbids this (class must PREDICT measured result-equivalence on actual payloads, not be defined by it).

---

## RECOMMENDATION
**Seed CANDIDATE A as PROJ-0008's first claim (CLAIM-A0).** Rationale:
1. **Cheapest-to-first-signal AND already de-risked in this design session.** The headline phenomenon is PRE-MEASURED on the CC
   corpus: 9.8% byte-identical within-session repeats, **100% with intervening tokens (median gap 12.5k) => prefix-caching structurally
   cannot recover them**, plus a non-obvious READ(3.1%)/WRITE-Bash(11.4%) determinism asymmetry. The load-bearing discriminator
   (RE-A2 APC-survival) already looks alive on real data — the rarest property in this portfolio (most charters die because the
   discriminator collapses; A's primary discriminator is pre-confirmed live, only the determinism-class lift RE-A1 is genuinely at risk).
2. **Cleanest unoccupied axis.** Every neighbor (PROJ-0002 edit-invalidation, PROJ-0005 BPE seam, PROJ-0007 cross-session drift,
   DroidSpeak/PrefillShare cross-agent reuse, the redundancy works 2603.16104/2604.09718) measures PREFIX-overlap reuse or BUILDS a cache.
   A owns the COMPLEMENT — interior, non-prefix, exact-repeat prefill waste that prefix-caching provably MISSES, quantified under an APC
   baseline on real traces. Nobody occupies it.
3. **Instruments fit perfectly + dodge the PROJ-0004 instrument trap.** A is a turn/call-level PREFILL claim, exactly what the CPU
   trigram/parse instrument measures cleanly — so the cheap-kill gate is DECISIVE (unlike DEAD-0011's d>=2 null which was instrument-predetermined).
   Reuses EXP-0007/EXP-0037/EXP-0042 code; first signal in hours, no GPU.
4. **Lowest accounting-identity risk in the portfolio.** Empirical incidence + survival-vs-baseline + predict-over-confound; RE-A2 and
   RE-A6 are explicitly engineered to prevent the 'a repeat costs a prefill' triviality from being the contribution. Contrast with the
   DEAD-0010/0013 break-even-identity kills — A has no closed-form to collapse to.
5. **Strong load-bearing discriminator learned from the kills.** RE-A1 forces determinism-class to beat the {token-gap + tool-frequency}
   JOINT baseline (the DEAD-0012 RE-1 dAUC-over-length+entropy / DEAD-0014 RE-A1 over-static-difficulty pattern), so 'agents repeat
   popular tools after a long gap' (the obvious confound) cannot masquerade as the finding.
6. **Informative negative either way:** repeats rare / already prefix-cached / pure popularity -> a clean 'prefix-caching suffices for
   agent self-repetition' result.

**Seed CANDIDATE B as a companion/second claim ONLY** (it is the determinism-class half that A already leans on, promoted to a
reuse-ceiling claim). B is narrower and more collision-exposed to the ICLR-2026 READ/WRITE cacheability submission, so its committee
survival depends on holding the delta strictly to 'measured realized ceiling + naive-assumption error rate', not 'a READ/WRITE cache'.
A+B together form a complete prefill-side picture: A = the APC-non-recoverable redundant-call TAX; B = the determinism-bounded reuse CEILING
that says how much of that tax is actually safely recoverable. If the committee wants ONE, seed A.

**Owed-before-promotion (not seeding blockers):** body-verify 2603.16104 / 2601.16286 / 2604.09718 redundancy framings; resolve the
ICLR-2026 READ/WRITE submission provenance (currently UNVERIFIED, anonymous-under-review). Both ~1hr CPU; neither blocks the L0 cheap-kill.
