# PROJ-0001 — Publication-Readiness Assessment (Top-Level Thesis Assembly + Go/No-Go Gate)

**Date:** 2026-05-31 · **Agent:** researcher-0001-thesis (top-level thesis-assembly lane, CPU-only) ·
**Orchestrator session:** 22bd6bef-b84b-4827-a371-87443ea8602f
**Scope:** READ-ONLY. NO claim/verdict/map edits, NO experiments, NO GPU/model CLIs/mapping re-probes
(FORBIDDEN per MI350X postmortem). This is the publication go/no-go gate for the PROJ-0001 paper.
**Inputs:** PAPER_SYNTHESIS_laneE.md (3-pillar synthesis + weakest-link), PAPER_HARDENING_2026-05-31.md
(resolved audit items), the 5 promoted claims (CLAIM-0001/0002/0003/0004/0007) incl writeup_notes +
evidence_corrections, registry/academic_map.yaml (MAP-0001), related_work.md, CROSSVENDOR_RESULT.md.

---

## VERDICT: GO — the PROJ-0001 paper is PUBLICATION-READY. Recommend marking PROJ-0001 DONE/MATURE.

All four laneE consistency defects are now resolved IN the promoted claims (verified below). No
remaining hostile-reviewer weak link beyond what is already documented and fenced. The negative-result
thesis is cleanly distinguished from vAttention and the occupied territory in MAP-0001. Venue framing
(MLSys for the keystone CLAIM-0003) is sound. No new experiment is required (and none is permitted).

---

## 1. TOP-LEVEL THESIS STATEMENT (paper abstract)

**Title (working):** *CUDA-VMM Is the Wrong Abstraction for Agentic KV-Cache Branching: A Three-Pillar
Architectural Indictment.*

**Abstract.**
Agentic LLM workloads fork conversation state into many speculative branches that share a long common
prefix, making copy-on-write (CoW) over the KV cache an attractive target for hardware acceleration via
NVIDIA's CUDA Virtual Memory Management (VMM) — alias a shared prefix once, let the GPU MMU diverge
branches lazily. We show this abstraction is the wrong one, along three compounding axes, and concede
the one place it is right.

- **(I) CAPACITY — a per-device vendor cliff [CLAIM-0002/0004].** A *conserved per-device* CUDA-VMM
  access-descriptor budget — measured at **523,404 mappings (+/-0.6%)**, deterministic to 0.000% variance
  across three independent paths, charged at `cuMemSetAccess` — hard-caps how many CoW branch mappings a
  device can hold. The budget is device-wide and splits evenly across contexts (n=1: 523,404; n=2:
  ~260K each; n=3: ~174K each), so it is *not* per-context: concurrent branching divides one fixed pool.
  AMD MI350X exhibits no such wall up to 80M mappings (**153x** more headroom), so this is a
  *vendor-specific portability cliff*, not a universal GPU law.
- **(II) PER-OP COST — CoW is dominated even below the ceiling [CLAIM-0001].** Even where capacity is not
  binding, HW VMM CoW *never wins*: across a 12-cell prefix x fanout x rollback grid it is **0/12** in any
  win-region, **1.06-2.20x slower than software prefix-sharing** (measured on both arms), and on an
  analytic paged-step projection ~**41-152x slower than FlashInfer**.
- (III) **COMPOUND — end-to-end throughput collapse [CLAIM-0003, the keystone].** The capacity cliff (I)
  and the per-op slowdown (II) *multiply*: across 8 fanout regimes HW wins **0/8**, crashes at the mapping
  ceiling for **every B>=128** (`cuMemSetAccess`), while software prefix-sharing scales cleanly **280->800
  tok/s**. The effective branch ceiling collapses by orders of magnitude under realistic load.
- **(Concession) The one real capability delta [CLAIM-0007].** We looked hard for a HW win and found
  exactly one: a forked branch's CoW edit is **bit-identical to a full clone (max_abs_diff = 0.0)** and
  **attention-kernel-transparent** — a write-after-share semantics that software prefix-sharing cannot
  structurally express. This narrow correctness/capability property does not rescue VMM on capacity or
  performance grounds.

**Thesis sentence.** *For agentic KV-cache branching, hardware CUDA-VMM copy-on-write is dominated on
per-operation cost, hard-capped by a conserved ~520K per-device mapping budget that is a vendor
portability cliff (absent on AMD), and these compound into end-to-end throughput collapse; the sole
structural advantage of HW CoW — a bit-identical, kernel-transparent write-after-share — does not
redeem it. Build software prefix-sharing, not HW VMM CoW.*

The four pillars are **non-redundant** (capacity / per-op speed / end-to-end / capability — distinct
axes), the keystone (III) is correctly the headline, and (Concession) is the rhetorical load-bearer
that makes the negative result read as rigorous rather than motivated. This is a publishable shape.

---

## 2. PUBLICATION-READINESS CHECKLIST

### 2a. Are all 5 claims' evidence chains now consistent? YES — all four laneE defects resolved.

| laneE finding | Sev | Resolution location (verified) | Status |
|---|---|---|---|
| CONSISTENCY-1: per-context -> per-device contradiction (the HIGH weakest link) | HIGH | `CLAIM-0002.yaml` + `CLAIM-0004.yaml` `evidence_corrections` (2026-05-31, orchestrator-r2-001): quantifier fixed to per-device; claim text now reads "per-device". `CROSSVENDOR_RESULT.md`: 0 "per-context" / 5 "per-device" occurrences — propagation fixed. | **RESOLVED** |
| CONSISTENCY-2: K=519,936 vs 523,404 unreconciled | MED | `CLAIM-0002.yaml` `writeup_notes` + PAPER_HARDENING ITEM 1: same quantity, two methods (523,404 = pure single-reservation ceiling; 519,936 = median realized B*P, e3c model input). Primary reconciliation pre-existed in committee_traces; 6/6 GREEN cast after it. | **RESOLVED** |
| CONSISTENCY-3: FlashInfer 41-152x is analytic, not measured | MED | `CLAIM-0001.yaml` `writeup_notes`: FlashInfer multiple labeled "(analytic paged-step projection)"; measured 1.06-2.20x SW domination (hw/sw=1.056-2.195, both arms measured) carries the "dominated" thesis alone (self-healing). | **RESOLVED (label)** |
| CONSISTENCY-4: B>=128 boundary vs B=16 transient | LOW | `CLAIM-0003.yaml` `writeup_notes`: split `crashed` -> `ceiling_crash` (B>=128, `cuMemSetAccess`) vs `transient` (B=16 cuBLAS, NOT_ceiling); B=64 clean confirms sharp boundary. | **RESOLVED (cosmetic)** |

**Internal consistency of the 5 claims (laneE Part 2, re-confirmed):** mutually consistent and
non-contradictory. 0/12 (per-op, EXP-A001) and 0/8 (fanout, EXP-A003) are different grids both
reporting zero HW wins (reinforcing). CLAIM-0007's capability delta is orthogonal (correctness, not
performance) to CLAIM-0001/0003 domination — no contradiction. DEAD-0003 (decision-procedure) is
correctly killed because 0/12 makes the "when-to-use-VMM" TRUE-branch measure-zero; the project claims
*domination*, not a decision procedure. The 523,404 headline is now consistent across CLAIM-0002,
EXP-A002, EXP-A007/r1, EXP-A003 `K_CEILING`, and EXP-A004 e3d n=1.

### 2b. Any REMAINING hostile-reviewer weak link beyond what is documented? NO new weak link.

The single HIGH weakest link laneE identified (the per-device resource model behind the keystone) is the
one a hostile reviewer would attack, and it is now fixed at the claim level + propagated to prior-art.
I searched for a *new* exploitable inconsistency beyond the documented four and found none. Residual
items are all already-documented and non-blocking:

- **(non-blocking, optional) FlashInfer is analytic.** Survives review *with the label* because the
  measured SW domination independently carries "dominated". A real FlashInfer cell is GPU-safe (kernel
  latency bench, NOT a mapping probe) and OPTIONAL — it only widens an already-proven gap. Not required
  for GO.
- **(prior-art doc hygiene, non-blocking) `needs_attention.md` lines 7 + 9** still say "re-probe before
  paper-track" / "re-run prior-art search before promotion". Re-probing the mapping ceiling is FORBIDDEN
  (MI350X postmortem). This is a stale *instruction in a notes file*, NOT a claim defect — the claims
  already scope the ceiling to its measured driver. RECOMMEND (orchestrator/cosmetic): reword to a
  driver-version-scoped statement ("scoped to the measured CUDA 12.8 / driver 580.82.07 stack"), do NOT
  re-probe. Does not gate publication.
- **(cosmetic, out of project scope) MEMORY.md "96x"** is an older AMD run's number; the claims correctly
  headline the largest clean watchdog-safe run (80M = 153x). Not a claim defect.

No hostile-reviewer kill-shot remains in the evidence chain.

### 2c. Is the venue framing sound? YES.

- **CLAIM-0003 (keystone, end-to-end throughput collapse) -> MLSys.** Correct: it is the systems-impact
  headline (compounding capacity x per-op cost into measured serving collapse, with a software baseline
  that scales). MLSys is the right home for a throughput-collapse keystone with a clean negative result.
- **CLAIM-0001 (CoW dominated) + CLAIM-0002/0004 (vendor ceiling) + CLAIM-0007 (capability delta) ->
  ATC/EuroSys/OSDI.** Correct supporting-venue framing for the mechanism/measurement claims; they are the
  body the MLSys keystone rests on (or stand alone as an ATC/EuroSys systems paper).
- The cross-vendor framing ("NVIDIA cliff, AMD none, 153x") makes the capacity pillar *falsifiable and
  stronger* — a portability-cliff claim, not an unfalsifiable universal law — which is exactly what a
  systems committee rewards. Sound.

---

## 3. CONTRIBUTION vs PRIOR-ART — FINAL CHECK

**The negative-result thesis is clearly distinguished from the occupied territory in MAP-0001.**

| Occupied territory (MAP-0001) | What it does | How PROJ-0001 is distinct |
|---|---|---|
| **vAttention** (arXiv 2405.04437) | CUDA-VMM for KV, contiguous VA, unmodified attention kernel | **read-only** VMM-KV sharing; **no fork/CoW branching**. PROJ-0001's object is fork/CoW branch divergence + the per-device mapping budget that binds it — a regime vAttention never enters. Fenced sharply in needs_attention #1. |
| PagedAttention / vLLM APC (SOSP'23) | paged KV + software prefix caching | per-request lifecycle, software refcount; no HW-MMU branch CoW. It is the *software baseline that wins* in PROJ-0001 (0/12, 0/8). |
| SGLang RadixAttention (NeurIPS'24) | radix-tree prefix sharing, software refcount | software, not HW MMU CoW; the token-prefix=KV sharing it captures is exactly DEAD-0006 (correctly fenced). |
| FlashInfer | production paged-attention kernels | the dominant perf baseline (the 41-152x-faster reference, now correctly labeled analytic). |
| Continuum / Irminsul / EPIC/MEPIC / CacheBlend / Cache-Craft | KV-TTL retention; CDC-over-radix; PIC recompute | belong to the **CLAIM-0006 (PROJ-0001 sibling, YELLOW)** invalidation-cost-map lineage, NOT to the 5 promoted CoW/ceiling claims. No collision with the negative-result thesis. |

**The three distinguishing contributions** — (1) "VMM CoW is *dominated* for agentic KV" (a measured
negative result, not a sharing scheme), (2) "the 520K per-device mapping ceiling is a *vendor portability
cliff*" (cross-vendor, root-caused to a conserved device-wide access-descriptor budget), and (3) "these
*compound* into end-to-end throughput collapse" — occupy the **negative/characterization** angle that the
positive-result prior art (which all proposes mechanisms to *use* VMM/paging/sharing) structurally does
not. The capability delta (CLAIM-0007, bit-identical write-after-share) is the one positive finding and
is outside the read-only-sharing prior art.

**Citation-gap check:** related_work.md covers the perf baselines (FlashInfer, PagedAttention/APC,
RadixAttention), the capacity/VMM neighbor (vAttention), and the retention/CDC neighbors. MAP-0001
`key_prior_work` is comprehensive (vAttention, PagedAttention, RadixAttention, Continuum, Irminsul, the
full PIC genus, Pope KV-accounting). **No must-cite gap** for the 5 promoted claims. The red_zones
correctly fence every dead-end adjacent to the promoted claims (HW VMM CoW DEAD via 0001/0003; isolation
DEAD-0001; attestation DEAD-0002; super-linear DEAD-0004; layer-stratified DEAD-0007). One optional
addition: explicitly cite vAttention as the *closest* prior art in the abstract's positioning sentence
so a reviewer immediately sees the read-only-vs-CoW boundary — a writing choice, not a missing citation.

---

## 4. GO / NO-GO

**GO.** The 5 promoted claims compose into a clean, well-fenced 3-pillar architectural indictment +
honest concession; all four laneE consistency defects are resolved in the claims and propagated to
prior-art; no new hostile-reviewer weak link remains; venue framing (MLSys keystone + ATC/EuroSys/OSDI
support) is sound; and the negative-result thesis is clearly distinguished from vAttention and the rest
of MAP-0001's occupied territory with no must-cite gap.

**Recommendation to orchestrator:** mark **PROJ-0001 DONE / MATURE** for the 5-claim CoW/ceiling thesis.
The only paper-track work left is *writing* (fold the writeup_notes labels into prose: per-device
quantifier, K reconciliation paragraph, FlashInfer "(analytic)" label, ceiling_crash/transient table
split) plus two optional, non-blocking polish items: (a) one real FlashInfer cell (GPU-safe, widens an
already-proven gap), (b) reword the stale `needs_attention.md` re-probe lines to a driver-version-scoped
statement (do NOT re-probe). None of these gate submission.

**Note on CLAIM-0006:** the sibling invalidation-cost-map claim remains 6/6 YELLOW (gate-A novelty
closed; gate-B real-lmcache-CacheBlend serving crossover deferred as future work) — it is NOT part of
this 5-claim publication and does not gate it. PROJ-0001's *promoted-claim* thesis is independently
publication-ready.

---

## Files / paths referenced
- This file: prior_art/PROJ-0001/PUBLICATION_READINESS.md
- Claims: registry/claims/PROJ-0001/2026-05-31/CLAIM-{0001,0002,0003,0004,0007}.yaml
  (evidence_corrections on 0002/0004; writeup_notes on 0001/0002/0003)
- Synthesis: prior_art/PROJ-0001/PAPER_SYNTHESIS_laneE.md (3-pillar + weakest-link)
- Hardening: prior_art/PROJ-0001/PAPER_HARDENING_2026-05-31.md (ITEM 1/2/3 resolutions)
- Map: registry/academic_map.yaml (MAP-0001)
- Prior-art: prior_art/PROJ-0001/related_work.md, 511ce2e2__CROSSVENDOR_RESULT.md, needs_attention.md
- Postmortem (re-probe FORBIDDEN): learning/MI350X_CRASH_POSTMORTEM.md

(No claims seeded. No verdicts. No map edits. No experiments. No GPU/model CLIs/mapping probes.
CPU-only. Wrote ONLY prior_art/PROJ-0001/PUBLICATION_READINESS.md.)
