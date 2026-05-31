# PROJ-0001 → Successor-Project Scoping: the SW-prefix-sharing winner's OWN scaling cliff?

**Date:** 2026-05-31 · **Agent:** researcher-0001-successor (forward successor-project scoping lane, CPU/reading-only) ·
**Orchestrator session:** 22bd6bef-b84b-4827-a371-87443ea8602f
**Scope:** READ-ONLY. NO claims / verdicts / map edits / seeding / experiments. NO GPU / model CLIs / memory probes
(MI350X_CRASH_POSTMORTEM honored). Wrote ONLY this file, under prior_art/PROJ-0001/.
**Mandate (NOT a PROJ-0001 extension):** PROJ-0001 ("CUDA-VMM is the wrong abstraction; build SW prefix-sharing,
not HW VMM CoW") is DONE — 5 promoted GREEN, 1+2-degree frontier exhausted (laneB/D/E/thesis/frontier/polish).
The forward FRONTIER_SCAN_2026-05-31.md flagged ONE residual closest-to-open direction (**F-NEG**) as a possible
*separate successor project*. This lane scopes whether F-NEG (or any forward SW-side direction) is worth SEEDING
AS A NEW PROJECT (not a PROJ-0001 claim), with heavy honesty.

---

## TL;DR / RECOMMENDATION

**RECOMMEND: PREMATURE-PARK (lean), bordering OCCUPIED-KILL — do NOT seed as a new project now.**

The successor question — *"now that SW prefix-sharing wins, where does the SW winner's OWN data structure hit a
scaling cliff (analogous to NVIDIA's 520K per-device ceiling), and is that a NEW first-class characterization no
published work draws?"* — is **attractive in spirit** (it is the exact dual of PROJ-0001's HW-ceiling finding) but
**fails the seed bar on all three of the gates a new project would have to clear**:

1. **The in-memory radix/refcount prefix-tree's own bookkeeping cliff is an ACCOUNTING IDENTITY** (the project's
   own DEAD-0009/0010 / slope~1 / "cost-model" red-zone kill pattern, applied 5×). Bookkeeping cost is monotone &
   derivable in (node-count × refcount-ops); a "law" here restates a conserved quantity, not a non-derivable anomaly.
2. **The ONE place a SW data-structure scaling cliff is genuinely first-class is ALREADY PUBLISHED**: the
   **storage/disk tier** — "On 10X Better Scalability: KV Stores Scale Up KV Cache" (arXiv:2511.16138, **ICLR 2026**,
   SGLANG-LSM) characterizes the file-per-object **metadata-overhead scalability bottleneck** of the KV-cache store
   and fixes it with an LSM layout. That IS "the SW KV data structure hits a metadata scaling cliff," published.
3. **The multi-agent slice is now densely occupied and getting MORE crowded by the week** — ForkKV (2604.06370, SW
   **CoW** multi-LoRA agent scaling), TokenDance (2604.03143, quantified multi-agent redundancy/scaling-gap, 99.3%
   pool saturation), Tokencake (2510.18586, space+time KV contention), plus FRESH occupants this lane surfaced that
   were in NEITHER MAP-0001 NOR the frontier scan: **PolyKV** (2604.24971, shared compressed multi-agent pool),
   **Prefill-as-a-Service** (2604.15039, cross-DC KVCache), **prediction-based agent KV** (2605.06472),
   **Strata** (2508.18572, hierarchical context caching), **Sparse Prefix Caching for Hybrid/Recurrent** (2605.05219).

There is **no forward SW-side direction that is simultaneously (a) non-derivable / not-an-identity, (b) unoccupied,
and (c) a clean first-class characterization**. F-NEG is the single residual "maybe," and it is gated on a forbidden
GPU/serving experiment with a high identity-collision risk and a now-published storage-tier analog. **Park it.**

---

## (a) The precise measurable claim a successor project WOULD make

Stripped to its strongest defensible form, the successor claim is:

> **"Software prefix-sharing's own in-memory branch data structure (the radix/refcount prefix tree of the
> vLLM-APC / SGLang-RadixAttention lineage) has a characterizable regime, at extreme branch fanout / concurrency,
> where its BOOKKEEPING cost (node-count, refcount/CoW pointer ops, eviction metadata, tree contention) — not the
> KV bytes — becomes the binding scaling constraint; and this crossover is (or is not) cross-engine (vLLM-APC vs
> RadixAttention vs FlashInfer), giving a SW-side cliff dual to NVIDIA's ~520K per-device VMM ceiling."**

Two measurable sub-quantities:
- **(a1) bytes-vs-bookkeeping crossover fanout F\*** — the branch count at which per-branch metadata bytes/ops
  overtake the unique-KV-page bytes (or at which tree-mutation latency overtakes attention latency).
- **(a2) cross-engine universality** — whether F\* (and its shape) is an engine-specific artifact or a portable
  law across ≥2 independent SW prefix-sharing engines (the dual of "NVIDIA wall vs AMD none").

This is well-posed and falsifiable. The problem is **what the answer almost certainly IS** (see (d)).

---

## (b) Collision check — vs the 9 forward neighbors, ForkKV, and the broader 2026 KV-store-scaling literature

### B.1 The frontier-scan's 9 forward SW-neighbors (re-verified this lane, body/abstract level)
| Work | id | What it occupies | Eats the successor claim? |
|---|---|---|---|
| **ForkKV** | 2604.06370 | SW **copy-on-write** *disaggregated* KV for multi-LoRA agent scaling — a CoW *mechanism* to scale #agents | **Partial-eats the multi-agent-redundancy / CoW-scaling SLICE.** It is a SW-CoW scaling system; a successor must body-distinguish "we *characterize the data-structure cliff*" from "they *build a CoW mechanism to push the cliff out*." High collision on framing. |
| **TokenDance** | 2604.03143 | Quantifies multi-agent KV **redundancy / scaling-gap** (99.3% pool saturation, P99 136s) + collective sharing mechanism | **Eats the "quantify the multi-agent scaling gap" framing** — they already publish the redundancy-driven scaling cliff *as motivation* + a fix. |
| **Tokencake** | 2510.18586 | KV-cache-centric multi-agent serving; space + time **contention** | Eats the contention slice (F3 in frontier scan). |
| **10X-KV-Stores / SGLANG-LSM** | 2511.16138 | **ICLR 2026.** SW **storage-layer metadata-overhead scalability bottleneck** of the KV store (file-per-object → LSM) | **DIRECTLY eats the "SW KV data structure hits a metadata scaling cliff" thesis — at the storage tier.** This is the published first-class SW-data-structure scaling-cliff characterization. The successor would have to argue the *in-GPU radix tree* tier is a *different, also-first-class* cliff — and that tier is an accounting identity (see (d)). |
| SemShareKV | 2509.24832 | cross-request semantic/near-dup KV dedup | Orthogonal mechanism; not a cliff characterization. |
| KVShare | 2503.16525 | semantic-aware multi-user KV sharing | Orthogonal mechanism. |
| QKVShare | 2605.03884 | quantized cross-agent KV handoff | Orthogonal mechanism. |
| CacheSolidarity | 2603.10726 | prefix-cache **side-channel / multi-tenant** isolation | Different axis (security); also DEAD-0001 family. |
| Joint-Encoding | 2601.03067 | block-metadata growth under concurrency (Huawei) | Eats the block-metadata-scaling slice. |

### B.2 FRESH occupants surfaced THIS lane (in NEITHER MAP-0001 NOR the frontier scan) — the space is *still filling*
- **PolyKV** (2604.24971): shared asymmetrically-compressed KV pool for multi-agent — "rather than a separate KV
  cache per agent ... writes a compressed cache once and injects into N agent contexts." Directly attacks the
  per-agent-copy scaling cost.
- **Prefill-as-a-Service** (2604.15039): KVCache scaling across datacenters (transfer-bound deployment cliff).
- **Prediction-based agent-workflow KV management** (2605.06472): dynamic agent-workflow KV reuse/scaling.
- **Strata** (2508.18572): hierarchical context caching scaling for long-context serving.
- **Sparse Prefix Caching for Hybrid/Recurrent** (2605.05219): prefix-cache scaling for SSM/recurrent serving.

These five appearing since the frontier scan is itself **negative evidence for seeding now**: the multi-agent /
prefix-cache scaling area is a hot, fast-moving 2026 wave; a new entrant must out-run a moving, crowded front.

### B.3 The in-memory radix-tree bookkeeping cliff specifically — IS IT published as a first-class law?
**No published work characterizes the in-GPU radix/refcount prefix-tree's bytes-vs-bookkeeping crossover as a
first-class cross-engine law** (consistent with the frontier scan's F-NEG read). The 2026 wave attacks redundancy
(TokenDance), contention (Tokencake), per-agent copies (PolyKV/ForkKV), storage metadata (10X-KV-Stores/Joint-
Encoding) with NEW MECHANISMS — none publishes "here is where the SW tree's own bookkeeping overtakes bytes,
cross-engine" as the headline result. So the *narrow* characterization is technically unoccupied — **but that is
the SAME reason it is an accounting identity nobody bothers to publish as a law** (see (d)). "Unoccupied because
trivial/derivable" is not "open."

**Collision verdict: PARTIALLY-OCCUPIED + the unoccupied residual is identity-bound.** The multi-agent-redundancy
and storage-metadata slices are occupied (ForkKV/TokenDance/Tokencake/PolyKV/10X-KV-Stores). The one unoccupied
slice (in-GPU radix-tree bookkeeping crossover) is unoccupied because it reduces to derivable accounting.

---

## (c) What experiment would test it — and the GPU/serving flag

To clear the seed bar the successor would need a **MEASURED, NON-DERIVABLE crossover**, i.e.:
- Drive ≥2 independent SW prefix-sharing engines (vLLM-APC, SGLang-RadixAttention; FlashInfer as kernel baseline)
  to extreme branch fanout (10^4–10^6 branches) and measure, per fanout, the split between (i) unique-KV-page
  bytes/latency and (ii) tree bookkeeping (node-count, refcount/CoW pointer ops, eviction metadata, lock
  contention) — locating F\* and testing whether it is engine-specific or portable (the AMD-vs-NVIDIA dual).
- Critically, show F\* (or its shape) is NOT predicted by the textbook node-count × refcount-ops accounting —
  i.e. a real anomaly (super-linear bookkeeping blowup, a contention phase-transition, a cross-engine divergence
  no model predicts). Without a non-derivable anomaly, the result is DEAD-0009/0010 on arrival.

**FLAG: this is unavoidably a GPU / live-serving experiment** (real engines, real KV pages, real fanout under load),
and likely a multi-GPU / high-memory one at 10^4–10^6 branches. It is **FORBIDDEN in this lane (CPU/reading-only)**
and was the explicit reason the frontier scan declined to seed F-NEG. Any seed decision must route through the
human GPU-go gate. NB also the MI350X_CRASH_POSTMORTEM: unbounded mapping/fanout probes have crashed nodes before —
a fanout-to-10^6 experiment needs a hard watchdog + capped reservation.

---

## (d) Genuinely-open, or premature/occupied? — the honest read

**Premature/identity-bound, leaning toward not-seedable.** Three independent forces, any one of which alone would
justify parking:

1. **Identity bar (the project's own 5×-applied kill).** The two load-bearing quantities of the SW winner — the
   prefix tree's bookkeeping (refcount + structural-sharing path-copy, O(1)/O(log n)) and unique-page capacity —
   are textbook-derivable accounting identities (persistent / functionally-shared data structures; radix/refcount;
   CacheBlend's body-confirmed "r% recompute ⇒ r% overhead" identity in the PROJ-0002 cost-map work). A "SW cliff
   law" is the DEAD-0003 / slope~1 / "cost-model" red-zone failure unless it produces a measured anomaly NOT
   predicted by node-count × refcount accounting. **Probable outcome: another accounting identity.**
2. **Published storage-tier analog.** 10X-KV-Stores (ICLR 2026) already owns "the SW KV data structure has a
   metadata-overhead scaling cliff" at the tier where it is a *real, non-trivial systems result* (file-system
   metadata, I/O, locality). The successor's only unoccupied tier (in-GPU radix bookkeeping) is the one where the
   cliff is an identity. The interesting tier is taken; the open tier is trivial.
3. **Crowded, accelerating front.** ForkKV / TokenDance / Tokencake / PolyKV / Joint-Encoding + the 5 fresh 2026
   occupants this lane surfaced mean the multi-agent / prefix-cache scaling slice is being actively colonized; a
   new entrant must body-distinguish from ≥10 works and out-run a moving target.

**What WOULD flip it to seed-as-new-project (the narrow door, left explicitly open for the orchestrator):**
A *preliminary* (human-GPU-go) measurement that finds a **non-derivable cross-engine anomaly** — e.g. one engine's
radix tree exhibits a super-linear bookkeeping blowup or a contention phase-transition at a fanout the other engine
does NOT, NOT predicted by node-count × refcount accounting, AND distinct from a storage-tier (10X-KV-Stores) or
redundancy (TokenDance) or per-agent-copy (PolyKV/ForkKV) effect. That would be a genuine "SW winner's own vendor-
style cliff" dual to PROJ-0001's 520K ceiling and could anchor a real successor project. Absent that anomaly —
which the identity argument predicts will NOT appear — it stays parked. This is a high-risk, GPU-gated probe, not a
ready seed.

---

## RECOMMENDATION TO ORCHESTRATOR

- **PREMATURE-PARK** (do not seed F-NEG as a new project now). Lean toward this over OCCUPIED-KILL only because the
  *narrow* in-GPU radix-bookkeeping cross-engine characterization is technically unoccupied — but it is unoccupied
  because identity-bound, and the seed bar is not met on any of (a)/(b)/(c).
- **NOT a PROJ-0001 extension** either way — PROJ-0001's 5-claim thesis is COMPLETE; this would be a separate project
  or nothing.
- **Conditional revival door (human GPU-go only):** if the orchestrator wants to gamble a small preliminary probe,
  the ONE thing that justifies it is hunting a *non-derivable cross-engine bookkeeping anomaly* (per (d)). If a
  capped, watchdogged probe finds no anomaly beyond node-count × refcount accounting → OCCUPIED-KILL it permanently
  (identity confirmed). If it finds a real anomaly → THEN seed a separate successor project, body-distinguished from
  ForkKV 2604.06370 / TokenDance 2604.03143 / Tokencake 2510.18586 / PolyKV 2604.24971 / 10X-KV-Stores 2511.16138.
- **Forward-occupancy log (flag only, map edit out of lane):** MAP-0001 and the frontier scan are missing 5 fresh
  2026 occupants: PolyKV 2604.24971, Prefill-as-a-Service 2604.15039, prediction-based agent KV 2605.06472, Strata
  2508.18572, Sparse Prefix Caching 2605.05219. None collides with the 5 promoted PROJ-0001 claims (all SW-side,
  not HW-VMM-CoW), so NOT a must-cite gap for the PROJ-0001 paper — logged as successor-space occupancy.

## Files / inputs referenced
- This file: prior_art/PROJ-0001/SUCCESSOR_PROJECT_SCOPING.md
- prior_art/PROJ-0001/{FRONTIER_SCAN_2026-05-31.md, PAPER_OUTLINE.md, PAPER_SYNTHESIS_laneE.md, related_work.md}
- prior_art/PROJ-0002/CLAIM-0006/novelty_boundary_2026-05-31.md (cost-map accounting-identity prior_art)
- Literature: arXiv 2604.06370 (ForkKV), 2604.03143 (TokenDance), 2510.18586 (Tokencake), 2511.16138 (10X-KV-Stores
  /SGLANG-LSM, ICLR 2026), 2601.03067 (Joint-Encoding), 2604.24971 (PolyKV, FRESH), 2604.15039 (Prefill-as-a-Service,
  FRESH), 2605.06472 (prediction-based agent KV, FRESH), 2508.18572 (Strata, FRESH), 2605.05219 (Sparse Prefix
  Caching, FRESH), 2509.24832 (SemShareKV), 2503.16525 (KVShare), 2605.03884 (QKVShare), 2603.10726 (CacheSolidarity)

(No claims seeded. No verdicts. No map edits. No experiments registered. No binding to any promoted claim.
CPU/reading-only — no GPU/model CLIs/memory probes. Wrote ONLY prior_art/PROJ-0001/SUCCESSOR_PROJECT_SCOPING.md.)
