# PROJ-0002 — Validated Autonomous-Researcher Experiment Digest

**Project:** PROJ-0002 — "Prefix-cache invalidation + KV reusability under agentic edits."
**Thesis:** mid-prompt tool injection breaks prefix-cache hash chains; characterize the cost-map +
a cheap content-defined-chunking (CDC) repair. **Status: CLOSED / PARKED** — CLAIM-0007 promoted
(VERDICT-0008); CLAIM-0006 honestly PARKED at the vLLM≥0.7 env-gate (VERDICT-0043, 4/6-conditional);
adjacent territory exhausted across SIX independent lanes; paper submittable.

This file unifies all internal autonomous-researcher / lane notes for PROJ-0002 (from both
`prior_art/PROJ-0002/` and the former `prior_art/PROJ-0002/CLAIM-0006/` subdir) into one place. Each
section is a concise digest preserving substantive findings, EXP/CLAIM/DEAD ids, key numbers, and the
honest dispositions. Source notes were folded in and removed. The companion files (needs_attention.md,
oss_community.md, related_work.md) remain separate prior-art records; publishable paper artifacts now
live under `projects/PROJ-0002/artifacts/`.

---

## 1. CLAIM-0006 — the Prefix-Cache Invalidation Law + CDC win-region (PARKED, honest 4/6)

**Claim:** mid-prompt tool injection breaks the prefix-cache hash chain; CDC (content-defined chunking,
rolling-hash boundaries) repair re-syncs downstream KV → ~2% recompute vs full-suffix recompute.

### Baseline positioning (Lane A, EXP-0003) — the DEAD-0006 falsification SURVIVED
- All 3 mandatory baselines do CONTIGUOUS shared-prefix reuse; NONE re-syncs a post-insertion suffix.
  - **vLLM APC** (SOSP'23): fixed 16-tok blocks, `hash(prefix+block)`, contiguous longest-prefix match.
    Mid-prefix insertion shifts token→block alignment AND diverges content → all blocks after p recomputed.
  - **SGLang RadixAttention** (arXiv 2312.07104): token-granularity (page=1 tok) radix tree. Removes
    vLLM's alignment penalty but NOT suffix-divergence: insertion forks a new branch → ~(1−f) suffix recompute.
  - **FlashInfer**: kernel library, no cache policy; recompute fraction == host engine's.
- **EXP-0003 (CPU):** CDC ≤2.38% (position-INDEPENDENT) vs all 3 baselines 10.1–90.1% (= (1−f) suffix,
  position-DEPENDENT). CDC vs binding Radix baseline: 8.3×–465×, grows with ctx. RadixAttention does NOT
  drop cheap under injection → **CLAIM-0006 does NOT collapse into DEAD-0006** (re-sync ≠ shared-prefix match).
  Prior session 048fcb0d on real vLLM `hash_block_tokens`: fixed-block recompute up-to-90%; CDC ~2.0–2.4%;
  H100 wall-clock 11.6×@8k, 119.6×@32k.
- Skeptic (local_skeptic): "ready" with one MUST-VERIFY (the Radix arm = the DEAD-0006 falsification test);
  report the full f-curve not a hero number (45×@10% vs 5×@90%); recompute-COUNT ≠ wall-clock.

### Serving evidence + the binding YELLOW (EXP-0026 / EXP-0027 confound)
- **EXP-0026** (real vLLM 0.6.6 PagedAttention, Qwen2.5-7B, H100): CDC wins ALL 12 serving cells on TTFT
  (PIC/CDC 1.05–1.79×) and throughput (CDC/PIC 1.00–1.13×). BUT the PIC arm was a faithful RE-IMPL
  (scattered paged-gather), NOT the published lmcache CacheBlend FUSED kernel (arXiv 2405.16444, EuroSys'25 Best Paper).
- **EXP-0027** (oracle/fused-PIC roofline, zero gather/launch overhead): CDC's serving advantage is
  CONDITIONAL — wins only at HIGH inj/seq (25%: oraclePIC/CDC 1.05–1.18×); LOSES at LOW inj/seq (1–5%:
  oraclePIC/CDC 0.61–0.99×). VERDICT-0033 fatal objection: the EXP-0026 win was partly a re-impl gather artifact.

### Novelty boundary (gate-A) — FULLY CLOSED at body level (10/10 neighbors, ZERO cost-map collision)
- **Two separable contributions, opposite novelty status:**
  - **MECHANISM (CDC-over-radix repair): NOT novel / DEAD.** Body-confirmed twin **Irminsul (arXiv 2605.05696)**
    — extends SGLang radix with content-hash keying over CDC-chunked segments + Gear-hash rolling boundaries
    (xxHash64, chunk ~2^k clamped [32,512]); publishes token-recovery%/prefill-energy, NOT a cost-map. Now
    indexed ×2 (Semantic Scholar CorpusId 288013360 + OpenAlex W7160639578) → collision firm. Plus PIC genus
    (EPIC 2410.15332, CacheBlend 2405.16444, Cache-Craft 2502.15734, MEPIC 2512.16822, KVFlow 2507.07400,
    CacheClip 2510.10129) — all body-verified distinct on cost-map but corroborate mechanism-genus occupancy.
    CDC insertion-resilience itself is decades-old (FastCDC/Rabin/US patents).
  - **FRAMING (the Invalidation LAW + conditional inj/seq recompute cost-map + head-to-head recompute-fraction
    vs APC/Radix/FlashInfer): NOVEL.** No collision. This is the only defensible committee story.
- **"Don't Break the Cache" (arXiv 2601.06007, PwC)** — the #1 collapse-fear, REFUTED at body level: it
  measures $-cost & TTFT vs PROMPT-SIZE / tool-COUNT (black-box provider API, no engine), NOT recompute-fraction
  vs inj/seq; no position-independence finding. Cite as closest empirical neighbor / motivation.
- The 2 MEDIUM tail candidates also cleared: **ContiguousKV (2601.13631)** offload-I/O-speedup; **variable-block
  diffusion (2604.23994)** decoding-quality — neither publishes the cost-map. Gate-A → 10/10 body-read.
- **Defensible novelty kernel (narrow):** engine-internal recompute-COST as a function of inj/seq (slope~1)
  under agentic mid-prompt injection, measured on real vLLM-APC/Radix/FlashInfer accounting, + the
  workload-conditioned CDC win-region (real traffic lands at median inj/seq ~2.8%, CDC-wins ~25% by count,
  ~46% conditioned on S≥50k). NOT novel: the CDC mechanism, the slope~1 "law" (accounting identity
  recompute=(R+W)/S≈R/S, Pope 2211.05102 / Kwon 2309.06180), position-independence (caveat p=0 attention-sink).

### Disposition: CLAIM-0006 PARKED, honest 4/6-conditional
- Binding remaining GREEN-blocker is the ORTHOGONAL **eval gate (B)**: true async V1-KVConnector E2E under
  concurrent load on real lmcache CacheBlend at the ~5% crossover. Env-blocked: vLLM 0.6.6.post1 lacks the
  V1 KVConnector API; source-built lmcache `c_ops` ABI cannot survive a vLLM≥0.7 upgrade without an
  unauthorized rebuild → **VERDICT-0043, parked HUMAN decision.** EXP-0034 (in-window) IS a landed result;
  only the true-async-under-concurrent-load axis is declared future work (must not be re-inflated to "DONE").
- **CLAIM-0007 PROMOTED (VERDICT-0008):** Attention-Visible GPU-MMU Write-After-Share — a forked branch's
  CoW edit is bit-identical and kernel-transparent.

---

## 2. EXP-0040 — descriptive injection-arrival burstiness candidate → DO-NOT-SEED (kill is sound)

The CLAIM-0012 descriptive pivot (which succeeded in PROJ-0003) applied to PROJ-0002's INJECTION stream:
*are large prefix-cache invalidation events temporally over-dispersed (bursty) within a session, vs a
permutation null fixing the result-size multiset and shuffling only ORDER?* (EXP-0040, level 1, CPU ~2.3s.)
- **V1 (inj/seq>5% "costly invalidation"): COLLIDES with EXP-0005.** Big runs-Z (CC −10.3, Codex −13.3) but
  events front-load (CC mean-pos 0.34, 27/40 sessions); the within-session permutation null collapses the
  signal (CC perm_p median 0.12) = the EXP-0005 accumulation axis / EXP-0036 CONTROL-A reduction. **DEAD.**
- **V2 (raw top-1/3 result SIZE, S-growth removed): genuinely-new framing, confound correctly removed (mean-pos
  ~0.51/0.58, not front-loaded), distinct from EXP-0005's i.i.d. assumption — BUT replicates 1 of 2 harnesses.**
  Codex significant (perm_p median 0.076, 27/62 p<0.05); Claude NOT (perm_p median 0.30, 4/39); Gemini has no
  tool-call data. 1/2 < the domain's cross-harness bar (CLAIM-0012 was cautioned at 2/2 + missing Gemini).
- **Disposition: DO-NOT-SEED** — V2 dies on EMPIRICS, not novelty (no web work occupies a within-session
  result-size arrival-clustering statistic). Revive ONLY if a 2nd harness beyond Codex shows permutation-
  significant raw-result-size arrival clustering — not CPU-reachable (no extra harness corpora locally).

---

## 3. Adjacent-claim exhaustion — SATURATED across SIX independent lanes (all EARLY-KILL / DO-NOT-SEED)

Every 1-degree adjacency of CLAIM-0006 is in the claim itself, a MAP-0001 red_zone, a body-verified neighbor,
or collapses to an accounting identity. The occupancy map (re-derived, not inherited):

| Adjacent angle | Status | Killing reason |
|---|---|---|
| inj/seq cost-map + win-region | CLAIM-0006 (occupied) | the surviving leg |
| CDC-over-radix repair MECHANISM | DEAD (red_zone) | Irminsul 2605.05696 twin (×2-indexed); PIC genus |
| slope~1 as cross-engine law | DEAD | accounting identity (EXP-0013, contiguous R²=0.0007) |
| injection exponent k~1.3 | DEAD-0009 | regime-local crossover, Pope/Kwon FLOP-derivable |
| idle-window speculative prefill | DEAD-0010 | speculate-or-skip identity; 2511.20048 + 2605.06472 occupy |
| compaction-as-prefix-invalidation | DEAD (EXP-0028) | == R/S identity at R:=summary; footprint=eviction/TTL |
| layer-stratified positional KV reuse | DEAD-0007 | <1.5% real incidence; revive only >2% |
| eviction-vs-recompute economics | KILL (laneB-A) | Continuum/KVFlow + 9 2026 eviction works; crowded |
| cumulative-trajectory recompute | KILL (laneB-B) | trivial integral of cost-map over EXP-0005 |
| tool-result DEPENDENCY (semantic staleness) | KILL (laneB-C) | ToolCacheAgent (ICLR'26) + hierarchical-caching dep-graph |
| count-vs-volume static-policy regret | KILL (laneB-D) | regret==0; CDC pointwise-dominates (analytic); no crossover |
| spec-decode × invalidation | KILL (laneE-1) | DEAD-0010 twin + generic SD bookkeeping |
| multi-agent shared-context compounding | KILL (laneE-2) | densely occupied (KVFlow/Tokencake/KVCOMM/2601.08343) |
| harness-routing → endogenous inj/seq | DEAD (EXP-0036) | CONTROL-A: reduces to trajectory-length ∘ result-size prior |
| repair DISPATCHER (route CDC vs PIC on inj/seq) | HOLD (laneD) | min-selection identity risk; provenance-blocked on un-measured crossover |
| descriptive invalidation-arrival burstiness | DO-NOT-SEED (EXP-0040) | V1 collides EXP-0005; V2 1/2-harness |

- **laneB-D analytic kill (EXP-LANEB-PROBE, 289,807 injections):** static_best=CDC; regret_static_best_vs_oracle
  = **0.0**; ratio-gated policy regret +143.6% (gating to FULL on large dumps is STRICTLY WORSE). CDC = R is a
  POINTWISE lower bound: FULL−CDC=(1−pos)·S≥0, PIC−CDC=R·(factor−1)≥0 → CDC weakly dominates → oracle==CDC,
  no crossover exists. The bimodality (24.6% CDC-win by count / 3.7% by volume; 36.5%/80.7% degrade) collapses
  onto CLAIM-0006's single surviving leg. (Honest caveat: recompute-TOKEN proxy; wall-clock arithmetic-intensity
  penalty = eval gate-B, already owned.)
- **laneE kill (EXP-0028, compaction, machine-zero on 80-cell grid):** CDC compaction recompute == (G+w)/S' ==
  CLAIM-0006's R/S identity at R:=summary G (max_abs_err 0.0); "when to compact" break-even = generic identity
  (== DEAD-0010 ratio); only distinct quantity = footprint savings = the killed eviction neighborhood.
- **laneAdjacent2 cross-project kill (EXP-0036, harness-routing):** headline sweep escaped the floor (win1=0.139)
  but **CONTROL-A is the kill** — removing trajectory truncation flattens the redirect_share axis (win1 0.315→0.302,
  entirely inside the EXP-0015 envelope). Harness recovery-routing adds NO new structural driver; it factors into
  trajectory length (EXP-0005) ∘ redirect-result-size profile (EXP-0015 prior). Routing per se moves win-region <1.5pp.
- **laneD dispatcher → HOLD/do-not-seed:** value rests on the real CDC-vs-fused-PIC crossover (NOT yet measured —
  the true-lmcache residual); "route to cheaper of two known methods by a threshold" is a generic min-selection
  identity class (DEAD-0010, EXP-0028); adaptive-repair-routing axis NOT body-cleared vs EPIC/KVFlow/CacheClip
  scheduling. Correct sequencing: measure crossover first, then re-evaluate. Premature to seed.
- **r3 final vet (ADJACENT_CLAIM_r3):** KILL / DO-NOT-SEED. After re-deriving occupancy + a fresh 2026-06-01 web
  sweep (2604.05404, 2506.02006, 2511.20048/2512.15834, 2605.00737, 2601.08343), no CPU-doable, genuinely-novel,
  non-identity, non-cemetery adjacent claim exists. Saturation confirmed by SIX lanes (laneB + laneE + laneD +
  adjacent2 + descseed + r3 vet). Recommendation: concentrate on CLAIM-0006's single binding GREEN-gate + CLAIM-0007.

---

## 4. True-lmcache / CacheBlend follow-up — RIGOROUS EXPERIMENT DESIGN (gate-B, env-blocked)

Design-only doc (laneD, CPU; no experiment registered). Runs once env `ros-vllm` (operator-owned, lmcache
source-built against torch 2.5.1 on devgpu014) is GREEN — orchestrator owns GPU dispatch.
- **Why it exists:** EXP-0026's CDC win was partly a re-impl gather artifact; EXP-0027's oracle bound predicts
  CDC LOSES at low inj/seq (1–5%). Decisive question: does CDC beat the REAL published fused CacheBlend kernel,
  ESPECIALLY at low inj/seq where the oracle says it should not?
- **Surface:** dense LOW-inj/seq sweep (the decisive regime). **Two arms:** A = CDC contiguous recompute
  (unchanged from EXP-0026); B = REAL lmcache CacheBlend fused KV-blending path (the new thing). Metrics: TTFT +
  batched throughput; ≥3 reps + CI; pre-registered pass/fail to let the committee resolve GREEN vs YELLOW.
- **Operational lessons carried:** DO NOT pip-install lmcache into the working env (it BROKE vLLM last time —
  logged); DO NOT touch py312conda or run model CLIs from this lane; unbounded VMM probes can crash the node.

---

## 5. Floor-hold / consistency lanes (2026-06-01) — collapsed

Six+ independent VERIFY-only floor passes (verify-r3, packaging-r3, FLOOR_CHECK_r3, FLOOR_CHECK2_r3,
FLOOR_HOLD_r3, FLOOR_HOLD4..8_r3) ALL independently confirm **PAPER_DRAFT_r3_FINAL.md SUBMITTABLE-AS-IS / GO /
CLEAN**, both flagged nits resolved (§5.1 EXP-0030 table; §3 "median inj/seq=2.8%"→EXP-0005 cite), the env-gate
(vLLM≥0.7) present/consistent/not-overclaimed across all placements, bibliography 13 arXiv ids internally
consistent (no orphan/uncited). CLAIM-0006 stays correctly PARKED (VERDICT-0043, 4/6-conditional); CLAIM-0007
promoted (VERDICT-0008). No open research; lanes held the ≥2/project researcher floor only — effort → PROJ-0003.
