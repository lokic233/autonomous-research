# PROJ-0001 — Validated Autonomous-Researcher Experiment Digest

**Project:** PROJ-0001 — "CUDA-VMM is the wrong abstraction for agentic KV branching; build
software prefix-sharing, not HW VMM CoW." **Status: DONE / CLOSED** — converged, triple+
verified, frontier exhausted across 8+ disjoint lanes, claims human-gated.

This file unifies all internal autonomous-researcher / lane notes for PROJ-0001 into one place.
Each section is a concise digest preserving substantive findings, EXP/CLAIM/DEAD ids, and key
numbers. Source notes were folded in and removed. The companion files (needs_attention.md,
oss_community.md, related_work.md) remain as separate prior-art records; publishable paper
artifacts now live under `projects/PROJ-0001/artifacts/`.

---

## 1. The three headline theses (5 promoted GREEN claims)

All measured on H100 (NVIDIA) + MI350X (AMD). Three pillars, backed by promoted claims
CLAIM-0001/0002/0003/0004/0007 (CLAIM-0005 weakened/closed-negative; no CLAIM-0006 in PROJ-0001).

- **C\* — HW VMM CoW is DOMINATED for agent KV (CLAIM-0001).** 0/12 win-region;
  HW VMM CoW is 1.06–2.20× slower than SW prefix-share and 41–152× slower than FlashInfer.
  The 12-cell grid is sub-ceiling, so the loss is driven by the **per-op fork tax, not capacity**.
  "Is CoW ever worth it" = CLOSED, negative.
- **A\* — NVIDIA ~520K per-context VMM mapping ceiling = a VENDOR PORTABILITY CLIFF (CLAIM-0002).**
  Independently reproduced 523,404 ±0.6% per-device `cuMemSetAccess` access-descriptor ceiling.
  AMD MI350X has no wall to 80M maps (153× / ~96× headroom). It is a vendor cliff, NOT a GPU law.
- **T-TAX — the ceiling + CoW + slowdown COMPOUND into end-to-end throughput collapse
  (CLAIM-0003).** HW wins 0/8 fanout regimes and crashes for all B≥128; SW scales 280→800 tok/s.
- **Supporting:** **CLAIM-0004 (Mapping-Budget Wall)** — a conserved per-context VMM mapping
  budget governs branch fanout, root-caused cross-vendor (the predictive resource model).
  **CLAIM-0007** — attention-visible GPU-MMU bit-identical, kernel-transparent write-after-share
  is the ONE real HW-CoW capability delta (and SW matches it bit-for-bit — see DEAD-0001).

### The 10 DEAD ideas (project's kill record, referenced throughout)
- DEAD-0001: SW refcount prefix-share matches HW isolation bit-for-bit + 240× faster at fork.
- DEAD-0002: handle attestation forgeable (userspace int, not HW attestation).
- DEAD-0003: HW-VMM-CoW measure-zero; AMD revival door = predicted-no-anomaly (see §3 G6).
- DEAD-0004: super-linear multi-ctx VMM degradation = retracted per-worker memory artifact.
- DEAD-0005: de-chained hash repair = 1.0× (no gain).
- DEAD-0006: token-prefix sharing predicts KV sharing → RadixAttention already captures it.
- DEAD-0007: layer-stratified positional KV reuse capped at 1.5% real incidence (kill bar 2%).
- DEAD-0008: interior/mid-sequence KV repair NOT bit-safe (max|dK| 4.04 at every layer≥1);
  reframed into CLAIM-0006 (PROJ-0002).
- DEAD-0009: injection-recompute exponent k~1.3 is a regime-local accounting-derivable
  crossover slope (drifts 1.0→2.0 with ctx), not a conserved law (CLAIM-0005 closed-negative).
- DEAD-0010: "positive SW cost model" reduces to refcount + persistent-data-structure accounting.

---

## 2. Completeness & adjacent-gap audits — SATURATED (laneB + laneD, disjoint)

**laneB (completeness audit, 2026-05-31): SATURATED.** Every adjacent idea maps onto an existing
promoted claim or one of the 9/10 DEAD ideas. Recommend mark mature/closed. Map defects flagged
(for orchestrator, not laneB to fix): D1 CLAIM-0005 dangling ID back-link to MAP-0001; D2
CLAIM-0008 mis-tagged to MAP-0001 (belongs MAP-0002, PROJ-0003); D3 DEAD-0004/-0007 lacked
explicit red_zone coverage; D4 needs_attention #3 stale (CLAIM-0005 settled negative per
VERDICT-0019, no 3rd engine needed); D5 freshness OK (MAP-0001 current).

**laneD (adjacent-claim mining + saturation re-test, 2026-05-31): SATURATED — confirms laneB via
a DISJOINT candidate set.** Generated 9 adjacent ideas (3 assigned directions + 6 fresh); every
one KILLED. Representative kills: (1a) precise AMD ceiling = FORBIDDEN (MI350X crash) + gold-plate;
(1b) cross-vendor portability cost model = restates CLAIM-0002+0004 (granule arithmetic identity);
(2a) other batch/fanout regimes = monotone interpolation of GREEN CLAIM-0003; (2b) multi-tenant
super-scaling = DEAD-0004 retracted-artifact zone; (3a) new KV-sharing regime = DEAD-0006;
(3b) layer-stratified reuse = DEAD-0007; (3c) interior edit = DEAD-0008. Three closing forces:
occupied territory, forbidden GPU probe, derivable accounting-identity.

---

## 3. Gap-mine round 3 — EXHAUSTION CONFIRMED (8th disjoint lane) + §G6

**gapmine-r3 (2026-06-01): EXHAUSTION-CONFIRMED, no seedable claim.** 8th disjoint early-kill lane
(after laneB/laneD/laneE/thesis/frontier-2deg/successor-scoping/seed2-methodology). Six FRESH
candidates, all die to the same three forces (accounting-identity / occupied / forbidden-probe):
- **G1** teardown/reclaim asymmetry → DOUBLE-KILL: the O(N) host-reclaim that crashed MI350X 3×
  (incl a 4–5h HW repair) = forbidden probe; also a granule×object-count identity.
- **G2** granule-driven internal fragmentation → occupied by vAttention (arXiv:2405.04437); restates
  CLAIM-0002/0004.
- **G3** bit-exact determinism for replay → DEAD-0001 (SW gives identical bytes).
- **G4** sub-ceiling TLB/page-walk pressure → already inside CLAIM-0001's measured slowdown;
  GPU-gated; occupied by vAttention.
- **G5** shared-prefix bandwidth contention → no HW-vs-SW delta by construction (one physical copy
  read N times under both).
- **G6** AMD HW-VMM-CoW win-region inversion → DEAD-0003 revival door, predicted-no-anomaly.

**§G6 — the one useful (non-seedable) by-product / paper hardening:** CLAIM-0001's 0/12 SW-win
region is expected to TRANSFER to AMD, derivable WITHOUT a probe. The NVIDIA-2MiB / AMD-4KiB granule
asymmetry is double-edged — it relaxes the capacity ceiling on AMD (512× more maps before any wall)
but tightens the per-op fork cost (512× more per-page map syscalls per byte of divergence). Since the
per-op fork tax (not capacity) is the binding reason HW loses, AMD makes the binding loser strictly
worse. ∴ NVIDIA loses on BOTH ceiling and per-op cost; AMD escapes the ceiling but loses HARDER on
per-op. Proposed map-delta (orchestrator-applied): retire DEAD-0003 AMD-revival door as
predicted-no-anomaly. A falsification-first CPU-only cost-model experiment was *designed* (not
dispatched): cost_fork(vendor)=(bytes_diverged/granule)×c_map; SW fork=O(1)/0 syscalls so the
falsifier never fires — confirming transfer analytically; value is a paper appendix only.

---

## 4. Forward-frontier & successor scoping — forward space is occupied / premature

**FRONTIER_SCAN (2026-05-31, 2-degree forward): forward frontier ALSO covered / premature.**
The 1-degree neighborhood (HW VMM CoW wrong) is saturated; the 2-degree complement (the SW winner's
own data structure / metadata / scaling / positive cost model) is a SEPARATE, already-crowded area.
Six forward candidates (F1–F5, F-SC) all KILLED by (1) fresh occupied 2026 territory or (2) the
project's own accounting-identity pattern. Fresh occupants surfaced (not in MAP-0001): ForkKV
(arXiv:2604.06370, SW CoW disaggregated KV multi-agent), TokenDance (2604.03143, collective KV
sharing, 99.3% pool saturation), Tokencake (2510.18586, space+time KV contention), "On 10X Better
Scalability: KV Stores Scale Up KV Cache" (2511.16138, KV-store metadata scaling bottleneck),
SemShareKV (2509.24832), KVShare (2503.16525), QKVShare (2605.03884), CacheSolidarity (2603.10726,
prefix-cache side-channels). One residual closest-to-open candidate **F-NEG** (where does SW
prefix-sharing's OWN structure stop scaling at extreme fanout) — premature, GPU-gated, high
identity-collision risk; documented, NOT seeded. Lean: confirmed-complete.

**SUCCESSOR_PROJECT_SCOPING (2026-05-31): PREMATURE-PARK (bordering OCCUPIED-KILL) — do NOT seed.**
Scopes whether F-NEG / any forward SW-side direction is worth a NEW project. Fails all three seed
gates: (1) the in-memory radix/refcount prefix-tree bookkeeping cliff is an accounting identity
(monotone in node-count × refcount-ops); (2) the one genuinely first-class SW data-structure cliff
is ALREADY PUBLISHED at the storage tier ("On 10X Better Scalability...", arXiv:2511.16138, ICLR
2026, SGLANG-LSM); (3) the multi-agent slice is densely occupied and growing — ForkKV, TokenDance,
Tokencake + fresh PolyKV (2604.24971), Prefill-as-a-Service (2604.15039), prediction-based agent KV
(2605.06472), Strata (2508.18572), Sparse Prefix Caching for Hybrid/Recurrent (2605.05219). No
forward direction is simultaneously non-derivable, unoccupied, and a clean first-class
characterization. Park F-NEG.

**METHODOLOGY_ANGLE_seed2 (2026-05-31): EARLY-KILL — do NOT seed a methodology spin-out.** Tested
a methodology/measurement contribution (the bytes-vs-bookkeeping + cross-vendor-ceiling +
compound-collapse triad T1/T2/T3) analogous to PROJ-0003's M1–M11. Killed: occupied by canonical
systems-benchmarking-methodology literature + restates the 5 claims + fails the accounting-identity
bar. Structurally weaker than PROJ-0003 because PROJ-0001's substance thesis is INTACT (5 GREEN,
PUBLICATION_READINESS=GO), so methodology is not a forced survivor — it is a second, weaker paper.
The methodology is correctly the implicit Methods section of the three-pillar paper, not separable.

**CROSSPOLLINATE (PROJ-0001 ↔ PROJ-0003, 2026-06-01): NO-LEVERAGE.** (Q1) the 0/12-win-region
robustness/CI reporting template is transferable but CLAIM-0012's GREENPATH already independently
arrived at the same discipline (LOSO kill-test, per-session strat-Z, Bonferroni/Holm, Codex as the
lone clean discriminating harness) — nothing new to port. (Q2) the two projects' heterogeneity
framings are STRUCTURALLY OPPOSITE — PROJ-0001 treats cross-vendor heterogeneity as a positive
finding (vendor cliff), PROJ-0003 treats cross-harness heterogeneity as a confound to control
(model≡harness alias, arXiv:2603.02277) — so a forced cross-citation would actively HARM CLAIM-0012.
Recommend NO cross-project methods citation; keep framings separate.

---

## 5. Publication hardening & verification — AIRTIGHT

**PUB_HARDENING_r3 (2026-06-01): AIRTIGHT + two modest cross-pollination flags.** Live arXiv-abstract
sweep on the three headline theses (C*/A*/T-TAX) found ZERO new collision since 2026-05-31: no new
paper does fork/CoW branch divergence over the KV cache via CUDA-VMM, publishes a per-device VMM
mapping ceiling as a portability cliff, or reports the compound capacity×per-op→throughput-collapse
result. The 2026 wave is positive/orthogonal (KVTC compression, kvcached elastic allocation, Nvidia
CMX storage, MIG/MPS partitioning, MI300X-vs-H100 benchmarking); nearest priors (vAttention
2405.04437, PagedAttention 2309.06180) unchanged and already cited. PAPER_CAMERAREADY.md stands.
Cross-pollination = two honest co-citation flags (neither a new claim): (X1) the vendor-portability-
cliff falsification instrument transfers to PROJ-0002 as a baseline-design caveat (reinforces
VERDICT-0017: PROJ-0002's 8×–465× retired as a contiguous-baseline artifact); (X2) PROJ-0001's E2E
throughput-collapse methodology and PROJ-0003's M1–M11 trap catalog are the same genus but do NOT
merge (PROJ-0003 is the methodology paper).

**VERIFY_r3 (2026-06-01): three checks, all PASS.** (1) §G6 AMD-transfer argument is LOGICALLY
AIRTIGHT — stress-tested the hostile-reviewer attack "could AMD's relaxed ceiling flip a cell NVIDIA
lost only to the ceiling?" and it cannot (the 12-cell grid is sub-ceiling; P1–P4 premises all hold).
RECOMMEND APPLY the AMD map-delta. (2) No internal inconsistency between the 5 promoted claim YAMLs
and PAPER_CAMERAREADY.md numbers; the apparent CLAIM-0007-vs-DEAD-0001 tension is a real distinction
("attention-visible write-after-share primitive" vs "bit-identical bytes"), not a contradiction.
(3) No new post-2026-05-31 arXiv collision (independent live sweep confirms PUB_HARDENING).

---

## 6. Floor-hold / consistency lanes (2026-06-01) — collapsed

Hold/floor-check lanes 2026-06-01 (FLOOR_CHECK, FLOOR_CHECK2, FLOOR_HOLD, FLOOR_HOLD4..8):
researchers parked at the ≥2-researcher floor while PROJ-0001 is DONE and claims human-gated; all
prior consistency checks returned CLEAN/CONSISTENT (map-delta consistent across academic_map MAP-0001
↔ DEAD-0003; promoted-GREEN set equality CLAIM-0001/0002/0003/0004/0007, CLAIM-0005 weakened); no
re-audit performed, no new findings, no re-open, no seed.
