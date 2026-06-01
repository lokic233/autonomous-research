# PROJ-0001 — Publication-Hardening + Cross-Pollination (r3)

**Date:** 2026-06-01 · **Agent:** researcher-0001-freshseed-r3 (publication-hardening + cross-project leverage lane, CPU/reading-only)
**Scope:** READ-ONLY on claims/verdicts/maps/experiments. Document-only. NO claim/verdict/map edits, NO experiments,
NO GPU/model CLIs/mapping re-probes (FORBIDDEN per MI350X_CRASH_POSTMORTEM). Live web search used for arXiv-abstract
collision check only. Wrote ONLY this file under prior_art/PROJ-0001/.
**Mandate:** (1) audit PAPER_CAMERAREADY.md for reviewer-attackable claims vs the LATEST 2026 prior art — confirm
no NEW collision since 2026-05-31 (new VMM-CoW paper, or a new ~520K-ceiling paper); (2) check whether any PROJ-0001
finding (vendor-ceiling portability framing, or the E2E throughput-collapse methodology) is a reusable instrument /
baseline for PROJ-0002 (prefix-cache) or PROJ-0003 (failure-attribution).

---

## TL;DR / VERDICT

**Both halves come back AIRTIGHT-with-two-modest-cross-pollination-flags.**

1. **No new collision since 2026-05-31.** A live web/arXiv-abstract sweep on the three headline theses
   (C* HW-VMM-CoW-dominated; A* ~520K per-device `cuMemSetAccess` access-descriptor ceiling = vendor cliff;
   T-TAX compound throughput collapse) surfaced **zero** new paper that (a) does fork/CoW branch divergence over
   the KV cache via CUDA-VMM, or (b) publishes a per-device VMM mapping ceiling as a portability cliff, or
   (c) reports the compound capacity×per-op→throughput-collapse result. The 2026 wave is all **positive-result /
   orthogonal** (KVTC compression, kvcached elastic allocation, Nvidia CMX storage platform, MIG/MPS partitioning,
   general MI300X-vs-H100 benchmarking). The nearest priors (vAttention 2405.04437, PagedAttention 2309.06180)
   are **unchanged and already cited**. **No new must-cite, no new attackable claim. PAPER_CAMERAREADY.md stands.**

2. **Cross-pollination = two modest, honest leverage flags, NEITHER a new claim:**
   - **(X1) The vendor-portability-cliff *instrument* (cross-vendor falsification frame) transfers to PROJ-0002 as
     a baseline-design caveat, NOT a finding.** It reinforces the already-recorded VERDICT-0017 lesson that a
     head-to-head advantage can be a *structural artifact of the baseline* (PROJ-0002's 8x–465x was retired as a
     contiguous-baseline artifact). The PROJ-0001 cross-vendor move ("is this a GPU law or a vendor cliff?") is the
     same falsification reflex PROJ-0002 should apply to any CDC-vs-PIC crossover. Already latent in both projects;
     worth one explicit sentence, not a claim.
   - **(X2) PROJ-0001's E2E-throughput-collapse methodology and PROJ-0003's M1–M11 trap catalog are the SAME
     genus (adversarial measurement discipline) and could be co-cited / cross-referenced, but do NOT merge.**
     PROJ-0003 already owns a self-contained, richer measurement-methodology contribution (M1–M11). PROJ-0001's
     methodology is its *implicit Methods section* (per closure_status / seed2: NOT a separable contribution).
     The honest cross-project note: PROJ-0003 is the methodology paper; PROJ-0001's collapse instrument is one
     more worked example of the same discipline, citable as such but not a shared deliverable.

**Net:** PROJ-0001 is publication-complete and un-attacked by fresh prior art. Cross-pollination yields confirmation
of existing lessons + two co-citation flags, not a new instrument or claim. **This lane confirms airtight.**

---

## 1. Fresh prior-art collision sweep (live, 2026-06-01) — NO new collision

**Method:** live web/arXiv-abstract search (no GPU, no probes) against each of the three headline theses + the
two nearest-neighbor axes (read-only VMM-KV; cross-vendor VMM limits). Cross-checked against the already-recorded
neighbors in related_work.md, MAP-0001, and FRONTIER_SCAN_2026-05-31.md (which already merged 9 forward 2026 SW-side
neighbors).

| Thesis / axis | Closest fresh hit (2026) | Collision? | Why not |
|---|---|---|---|
| **C\*** HW-VMM-CoW dominated for agent KV (fork/CoW branch divergence) | vAttention (2405.04437, unchanged); kvcached (2026, vLLM dynamic KV *allocation* tutorial) | **NO** | Both are read-only / dynamic-**allocation** KV memory mgmt. Neither forks branches via MMU CoW; neither reports a CoW-vs-SW head-to-head. C\* is the negative/characterization angle they structurally do not enter (same boundary as related_work.md). |
| **A\*** ~520K per-device `cuMemSetAccess` access-descriptor ceiling = vendor cliff (AMD no wall) | NVIDIA CMX / Rubin "GPU memory wall" platform (HPCwire 2026-03); general MI300X-vs-H100 benchmarking; "Dissecting CPU-GPU Unified Physical Memory on MI300A" (2508.12743) | **NO** | CMX attacks the **HBM capacity** wall (storage-tier offload), not a per-device VMM **mapping-count** ceiling. The MI300A UPM paper characterizes unified-physical-memory perf, not a VMM access-descriptor budget or a cross-vendor mapping-count cliff. No paper publishes the 523,404-mapping `cuMemSetAccess` ceiling or its absence on AMD. |
| **T-TAX** compound capacity×per-op → E2E throughput collapse (HW 0/8, crash B≥128 vs SW 280→800 tok/s) | "Disaggregated LLM Inference Cuts GPU Waste" (2026-04); KVTC 20x memory compression | **NO** | Disaggregation/compression are positive serving-efficiency mechanisms; neither reports a CoW-branching throughput-collapse table nor a B-grid ceiling-crash boundary. T-TAX's compound negative result is unoccupied. |
| Read-only VMM-KV neighbor | vAttention (2405.04437) | already cited | unchanged since 2024; the read-only-vs-CoW boundary is already fenced in needs_attention #1 + §3 of PUBLICATION_READINESS. |

**Conclusion:** the camera-ready's headline numbers and framing face **no new 2026 collision**. The
already-documented FlashInfer-analytic label, per-device quantifier, K-reconciliation, and ceiling/transient
split (all verified byte-for-byte in PAPER_CAMERAREADY §4) remain the only reviewer-attackable surfaces, and all
four are already pre-defended in PROSE (per PAPER_REVIEW_REDTEAM GO + paper_status in MAP-0001). **No new
hardening action required.** Re-probing the ceiling to "confirm" against a new driver remains FORBIDDEN and is
correctly handled as a driver-version-scoped threat-to-validity, not a re-run.

---

## 2. Cross-project leverage assessment (the complement to the gap-mine lane)

I evaluated whether PROJ-0001's two transferable assets — (i) the **vendor-portability-cliff falsification frame**
and (ii) the **E2E-throughput-collapse measurement methodology** — give PROJ-0002 or PROJ-0003 a reusable
instrument or baseline. Both projects already have mature, self-contained methodology, so the bar for a *new*
cross-project contribution is high. It is not cleared; two modest co-citation/caveat flags survive.

### 2.1 PROJ-0002 (prefix-cache invalidation) — vendor-cliff frame = a baseline-design CAVEAT, already latent
- PROJ-0002's history (VERDICT-0017, related_work.md) already **retired its own 8x–465x head-to-head as a
  STRUCTURAL ARTIFACT of contiguous baselines** and made a real PIC-family baseline MANDATORY. That is exactly
  the PROJ-0001 reflex: *before claiming an advantage is fundamental, ask whether it is an artifact of the thing
  you compared against (a vendor, a baseline) rather than a law.* PROJ-0001 operationalized it cross-VENDOR
  (NVIDIA cliff vs AMD none → "vendor cliff, not GPU law"); PROJ-0002 needs it cross-BASELINE (CDC vs a real PIC
  artifact → "competitive win, not a structural gap").
- **Verdict:** this is a **shared falsification discipline, not a transferable instrument**. PROJ-0002 already
  applies it. The only value-add is one explicit cross-reference sentence in a methods/limitations section
  ("we apply the same artifact-vs-law falsification test PROJ-0001 used cross-vendor, here cross-baseline").
  **NOT a new claim; flag-only.**

### 2.2 PROJ-0003 (failure-attribution) — same measurement-discipline GENUS, but PROJ-0003 already owns the richer artifact
- PROJ-0003's durable contribution is the **M1–M11 adversarial-measurement trap catalog** (null+informed
  baselines, LOSO-vs-LOCO CV, decisive-cell ablation, double-log dedup, naming-confound control, 3-way-alias
  diagnosis, strict reactive/preempt/abandon labeling, pre-registered off-node factorial). PROJ-0001's
  E2E-collapse instrument (sharp B-grid ceiling-crash boundary; ceiling vs transient crash-class separation;
  measured-SW-baseline-that-scales as the load-bearing control) is the **same genus** — adversarial discipline
  that prevents a number from lying — but it is *narrower* and is the paper's implicit Methods section, NOT a
  separable contribution (confirmed by closure_status: seed2 killed the standalone-methodology angle on 4 gates).
- **Verdict:** these **do NOT merge into a shared methods paper.** PROJ-0003 is the methodology contribution;
  PROJ-0001's collapse instrument is best treated as **one worked exemplar of the same discipline, co-citable**
  if PROJ-0003's methodology paper wants a systems-side example of "measure the winner's own breaking point + a
  baseline that scales." **NOT a new claim; co-citation flag-only.**

### 2.3 What is NOT new (explicitly, to avoid re-mining a saturated space)
- The one prior *explicit* PROJ-0003→PROJ-0002 cross-project experiment (harness-recovery-routing → endogenous
  inj/seq distribution, EXP-0036) was **already KILLED** (CONTROL-A: the escape was trajectory truncation, not
  routing; reduces to EXP-0005/0015 cost-map). I did not revive it.
- The PROJ-0001 standalone-methodology angle was **already killed by seed2** (7th consecutive lane). I did not
  revive it. The triad (capacity × per-op cost → collapse) is the paper's implicit Methods section, not a
  separable cross-project deliverable.

---

## 3. Honest bottom line

- **Publication hardening:** PROJ-0001's camera-ready is **airtight against fresh 2026 prior art**. No new
  collision on any of the three theses; no new must-cite; no new attackable claim; the four documented soft
  surfaces remain fully pre-defended. The only correct action on the ceiling is to keep it driver-version-scoped
  (never re-probe).
- **Cross-pollination:** yields **confirmation of existing lessons + two co-citation/caveat flags**
  (X1 cross-vendor→cross-baseline falsification frame for PROJ-0002; X2 PROJ-0001 collapse-instrument as a worked
  exemplar co-citable by PROJ-0003's M1–M11 methodology paper) — **neither is a new claim, neither merges into a
  new shared deliverable.** PROJ-0002 and PROJ-0003 each already own richer, self-contained methodology.
- **Recommendation to orchestrator:** treat PROJ-0001 as DONE/airtight (consistent with project_status). The two
  flags are optional one-sentence cross-references at writing time, NOT seeds and NOT map edits. No GPU, no
  re-probe, no new experiment warranted.

---

## Constraints honored
Wrote ONLY this file under prior_art/PROJ-0001/. No claim/verdict/map edits. No experiments. No GPU/model
CLIs/mapping re-probes (FORBIDDEN per MI350X postmortem). CPU/reading-only. Live web search used ONLY for
arXiv-abstract collision confirmation. Did not touch sibling workspaces (committee_navi*). Did not revive the
already-killed EXP-0036 cross-project angle or the seed2-killed standalone-methodology angle.
