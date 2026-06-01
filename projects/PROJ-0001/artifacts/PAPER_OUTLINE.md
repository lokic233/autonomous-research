# PROJ-0001 — Paper Outline (Prose-Prep Skeleton)

**Date:** 2026-05-31 · **Agent:** researcher-0001-polish (CPU paper-prep lane) ·
**Orchestrator session:** 22bd6bef-b84b-4827-a371-87443ea8602f
**Scope:** READ-ONLY w.r.t. claims/verdicts/map/experiments. Document-only. NO GPU / model CLIs /
mapping re-probes (FORBIDDEN per MI350X postmortem). Wrote ONLY this file under prior_art/PROJ-0001/.
**Status:** PROJ-0001 is PUBLICATION-READY/MATURE (PUBLICATION_READINESS GO; laneB/laneD/laneE +
forward FRONTIER_SCAN all confirm 1-degree AND 2-degree frontier exhausted). This is the writing
skeleton — every section maps to a promoted claim + EXP id + writeup_note. No new science.

---

## Title (working)
*CUDA-VMM Is the Wrong Abstraction for Agentic KV-Cache Branching: A Three-Pillar Architectural
Indictment.*

## Abstract (source: PUBLICATION_READINESS §1; PAPER_SYNTHESIS_laneE Part 1)
Agentic LLM workloads fork conversation state into many speculative branches that share a long common
prefix, making copy-on-write (CoW) over the KV cache an attractive target for hardware acceleration
via NVIDIA CUDA Virtual Memory Management (VMM) — alias a shared prefix once, let the GPU MMU diverge
branches lazily. We show this abstraction is wrong along three compounding axes, and concede the one
place it is right:
- **(I) Capacity** — a conserved *per-device* ~523,404 (+/-0.6%) access-descriptor budget hard-caps
  CoW branch mappings, charged at `cuMemSetAccess`; AMD MI350X shows no such wall to 80M maps (153x),
  so it is a *vendor portability cliff*, not a universal GPU law. [CLAIM-0002/0004]
- **(II) Per-op cost** — even below the ceiling, HW VMM CoW never wins: 0/12 win-region, 1.06-2.20x
  slower than software prefix-sharing (both arms measured), ~41-152x slower than FlashInfer (analytic
  projection). [CLAIM-0001]
- **(III) Compound** — (I) and (II) multiply into end-to-end throughput collapse: HW wins 0/8 fanout
  regimes, crashes at the ceiling for every B>=128, while software scales 280->800 tok/s. [CLAIM-0003]
- **(Concession)** — the one real HW capability delta: a forked branch's CoW edit is bit-identical to
  a full clone (max_abs_diff=0.0) and attention-kernel-transparent — a write-after-share semantics
  software prefix-sharing cannot structurally express; it does not redeem VMM. [CLAIM-0007]

**Thesis sentence.** For agentic KV-cache branching, HW CUDA-VMM CoW is dominated on per-op cost,
hard-capped by a conserved ~520K per-device mapping budget that is a vendor portability cliff (absent
on AMD), and these compound into end-to-end throughput collapse; the sole structural advantage of HW
CoW — a bit-identical, kernel-transparent write-after-share — does not redeem it. **Build software
prefix-sharing, not HW VMM CoW.**

---

## Section-by-section structure (each section -> claims + EXP ids + writeup_notes)

### 1. Introduction / Motivation
- **Argument:** agentic LLM serving forks state into many speculative branches sharing a long prefix;
  CoW-over-KV via CUDA-VMM looks like the natural HW acceleration. We test that intuition and reject it.
- **Sources:** project_overview; PUBLICATION_READINESS §1; PAPER_SYNTHESIS_laneE Part 1 (the diagram).
- **Claims framed (not yet proven):** preview I/II/III + concession. State this is a *measured negative
  result*, distinguished up front from positive-result prior art (forward-reference §6).
- **No EXP cited here** (motivation only).

### 2. Background / Threat-of-intuition
- **Argument:** what CUDA-VMM offers (cuMemCreate/cuMemMap/cuMemSetAccess, contiguous VA, unmodified
  attention kernel) and why CoW branching seems to fit; define "software prefix-sharing" baseline
  (radix/refcount page table, the vLLM-APC / RadixAttention lineage).
- **Sources:** related_work.md (vAttention/PagedAttention/RadixAttention/FlashInfer rows);
  needs_attention.md #1 (vAttention read-only-vs-CoW boundary).

### 3. PILLAR I — CAPACITY: the per-device mapping cliff  [CLAIM-0002 + CLAIM-0004]
- **Claim text:** "~520K CUDA-VMM **per-device** mapping ceiling is a vendor-specific portability cliff
  (reproduced 523,404 +/-0.6% at `cuMemSetAccess`; AMD no wall at 80M = 153x)."
- **Key numbers + traceability:**
  - 523,404 (+/-0.6%) deterministic ceiling — `EXP-A007/experiment_result/r1.json`
    (`mappings_before_fail:523404, oom_call:cuMemSetAccess`); `EXP-A002/experiment.yaml` (headline);
    `EXP-A003/impl/bench_ET_tax_throughput.py` (`K_CEILING=523404`).
  - PER-DEVICE proof (conserved, splits ~K/n): `EXP-A004/experiment_result/e3d_results.jsonl`
    (n=1:523404; n=2: 260281+263003=523284; n=3: 171633+174206+177325=523164).
  - Cross-vendor (NVIDIA wall vs AMD none, 153x @ 80M; CUDA 12.8 / driver 580.82.07; 2 MiB granule):
    `511ce2e2__CROSSVENDOR_RESULT.md`.
- **writeup_notes to fold in:**
  - CLAIM-0002 evidence_correction: use "**per-device** (conserved, splits ~K/n evenly across
    contexts)" — NOT "per-context". (laneE CONSISTENCY-1, the HIGH weakest link; already corrected in
    YAML + CROSSVENDOR_RESULT.)
  - CLAIM-0002 writeup_note + PAPER_HARDENING ITEM 1: include the **K reconciliation paragraph** —
    523,404 = pure single-reservation alias ceiling (measured, 0% variance); 519,936 = median realized
    B*P over the Metric-4b prefix sweep (522,752 @1GiB -> 516,096 @12GiB), used ONLY as the e3c model
    input. Headline 523,404; label e3c K as model-input median.
- **Driver-version scoping (per corrected needs_attention #2 — see §1 of REPORT below):** present the
  ceiling as measured under CUDA 12.8 / driver 580.82.07; future driver versions = a scoped limitation,
  explicitly NOT a re-probe instruction.

### 4. PILLAR II — PER-OP COST: CoW is dominated below the ceiling  [CLAIM-0001]
- **Claim text:** "HW VMM CoW is dominated for agent KV (0/12 win-region; 1.06-2.20x slower than
  software prefix-sharing, 41-152x slower than FlashInfer)."
- **Key numbers + traceability:**
  - 0/12 win-region + 1.06-2.20x (MEASURED both arms, hw/sw=1.056-2.195): `EXP-A001/experiment_result/
    ec_rollback_e2e.csv` (12 cells = prefix{long4096,short512} x N{4,16} x R{0,4,16}; arms hw_vmm_cow,
    hw_vmm_cow_fullfwd, sw_prefix, flashinfer).
  - 41-152x FlashInfer (ANALYTIC denominator): same CSV, every `flashinfer` row tagged
    `ANALYTIC: 48 paged-steps@~0.03ms + measured sw bookkeeping`.
- **writeup_notes to fold in (CLAIM-0001 writeup_note + PAPER_HARDENING ITEM 2):**
  - Label FlashInfer multiple "(analytic paged-step projection; not a measured FlashInfer run)".
  - State the MEASURED 1.06-2.20x SW domination carries the "dominated" thesis ALONE (self-healing);
    FlashInfer is a bonus widening multiplier.
  - Optional real FlashInfer cell is GPU-safe (kernel latency bench, NOT a mapping probe) but NOT
    required — labeling suffices. [non-blocking polish item (a)]

### 5. PILLAR III — COMPOUND: end-to-end throughput collapse (KEYSTONE)  [CLAIM-0003]
- **Claim text:** "Ceiling + CoW + slowdown COMPOUND into end-to-end throughput collapse: HW wins 0/8
  fanout regimes, crashes for all B>=128, software scales 280->800 tok/s."
- **Key numbers + traceability:** `EXP-A003/experiment_result/et_tax_throughput.csv` (8 hw + 8 sw rows,
  fanout B in {4,16,64,128,256,511,919,1124}):
  - HW 0/8 wins; ceiling crash (`cuMemSetAccess`) at B=128/256/511/919/1124 (every B>=128); B=64 clean.
  - B=16 is `transient_cublas(1of3reps;NOT_ceiling)` — a DIFFERENT failure mode (2/3 reps OK).
  - SW zero crashes, 280.5 (B=4) -> peak 799.79 (B=919) tok/s.
- **writeup_notes to fold in (CLAIM-0003 writeup_note + PAPER_HARDENING ITEM 3):** in any table, split
  the `crashed` column into `ceiling_crash` (B>=128, cuMemSetAccess) vs `transient` (B=16, cuBLAS) so
  the sharp B>=128 boundary reads cleanly. [cosmetic]
- **Why keystone:** multiplies Pillar I (capacity wall) x Pillar II (per-op slowdown) into measured
  serving collapse against a SW baseline that scales -> MLSys headline (target_venue: MLSys).

### 6. The honest write-after-share CONCESSION  [CLAIM-0007]
- **Claim text:** "Attention-Visible GPU-MMU Write-After-Share: a forked branch's CoW edit is
  bit-identical to full-clone (max_abs_diff=0.0), kernel-transparent — a capability software
  prefix-sharing cannot express."
- **Key numbers + traceability:** `EXP-A007/experiment_result/e1b_result.json`
  (`max_abs_diff_vs_clone: 0.0`); supporting e1_result.json / r1.json / r2.json.
- **Rhetorical role (PAPER_SYNTHESIS_laneE Part 1):** the load-bearing concession — "we looked hard
  for a HW win and found exactly this one narrow correctness/capability property; it is orthogonal to
  performance (CLAIM-0001/0003) and does not rescue VMM on capacity or perf grounds." Makes the
  negative result read as rigorous, not motivated.

### 7. Related Work / positioning
- **Source:** related_work.md + MAP-0001 key_prior_work + FRONTIER_SCAN_2026-05-31 forward neighbors.
- **Closest prior art to fence sharply (in the abstract positioning sentence + this section):**
  - **vAttention (arXiv 2405.04437):** CUDA-VMM for KV, contiguous VA, unmodified kernel — but
    **read-only** sharing, **no fork/CoW branching**. Our object is the fork/CoW divergence + the
    per-device budget that binds it — a regime vAttention never enters. (needs_attention #1.)
  - **vLLM PagedAttention / APC (SOSP'23)** + **SGLang RadixAttention (NeurIPS'24):** software
    prefix-sharing — i.e. the baseline that WINS here (0/12, 0/8). RadixAttention captures
    token-prefix=KV sharing == DEAD-0006 (fenced).
  - **FlashInfer:** production paged-attention kernels = the dominant perf baseline (the 41-152x-faster
    analytic reference).
- **The 9 forward SW-neighbors (2026-era, surfaced by FRONTIER_SCAN; SW-side / read-only / multi-agent
  mechanisms — NOT HW-VMM-CoW, so NO must-cite collision, cite as forward-frontier occupancy):**
  ForkKV (2604.06370), TokenDance (2604.03143), Tokencake (2510.18586), "On 10X Better Scalability:
  KV Stores Scale Up KV Cache" (2511.16138), Joint-Encoding of KV-Cache Blocks (2601.03067),
  SemShareKV (2509.24832), KVShare (2503.16525), QKVShare (2605.03884), CacheSolidarity (2603.10726).
  (Optional add: Category-Aware Semantic Caching 2510.26835.)
- **Distinguishing contribution (PUBLICATION_READINESS §3):** ours is the NEGATIVE/characterization
  angle (CoW dominated / vendor ceiling cliff / compounding collapse) + the write-after-share
  capability delta — outside the positive-result, read-only-sharing prior art.

### 8. Conclusion — "build software prefix-sharing"
- Restate the thesis sentence. The forward direction the indictment POINTS to (FRONTIER_SCAN) — the
  SW-prefix-sharing winner's OWN cross-engine scaling characterization (F-NEG) — is flagged as
  future/separate-project work, explicitly NOT a PROJ-0001 claim and gated on a (here-forbidden) GPU
  experiment + a high accounting-identity-collision risk. Do NOT over-promise it.

---

## Claim -> Section -> EXP -> writeup_note map (one-glance)

| Pillar | Section | Claim(s) | EXP id(s) | Headline number(s) | writeup_note / hardening item |
|---|---|---|---|---|---|
| I Capacity | §3 | CLAIM-0002, CLAIM-0004 | EXP-A002, EXP-A004(e3d), EXP-A007(r1) | 523,404 +/-0.6%; per-device split n=1/2/3; AMD 153x@80M | per-context->per-device (evidence_correction); K reconciliation (HARDENING ITEM 1); driver-scoped |
| II Per-op | §4 | CLAIM-0001 | EXP-A001 | 0/12; 1.06-2.20x (measured); 41-152x (analytic) | FlashInfer analytic label (HARDENING ITEM 2) |
| III Compound | §5 (keystone) | CLAIM-0003 | EXP-A003 | 0/8; B>=128 ceiling crash; 280->800 tok/s | ceiling_crash vs transient column split (HARDENING ITEM 3) |
| Concession | §6 | CLAIM-0007 | EXP-A007(e1b) | max_abs_diff=0.0, kernel-transparent | (none — clean) |

## Venue framing (PUBLICATION_READINESS §2c)
- KEYSTONE CLAIM-0003 -> **MLSys** (systems-impact throughput-collapse headline).
- CLAIM-0001/0002/0004/0007 -> **ATC/EuroSys/OSDI** (mechanism/measurement body; can stand alone).

## Constraints honored
No claims seeded. No verdicts. No map edits. No experiments. No GPU / model CLIs / mapping re-probes
(CPU/reading-only). Wrote ONLY prior_art/PROJ-0001/PAPER_OUTLINE.md.
