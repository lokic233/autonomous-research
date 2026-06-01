# CUDA-VMM Is the Wrong Abstraction for Agentic KV-Cache Branching: A Three-Pillar Architectural Indictment

**Project:** PROJ-0001 · **Status:** Publication-ready (5 promoted GREEN claims; DONE/MATURE).
**Draft:** PAPER_DRAFT.md (full submittable prose). **Target venues:** MLSys (keystone, end-to-end
throughput collapse) primary; ATC / EuroSys / OSDI (mechanism + measurement body) supporting.

> Every quantitative claim in this draft traces to a promoted claim (CLAIM-0001/0002/0003/0004/0007)
> and a registered experiment (EXP-A001/A002/A003/A004/A007). Experiment ids are cited inline. No
> number in this draft was invented; all are sourced from the verified result files.

---

## Abstract

Agentic LLM workloads fork conversation state into many speculative branches that share a long common
prefix, making copy-on-write (CoW) over the KV cache an attractive target for hardware acceleration via
NVIDIA's CUDA Virtual Memory Management (VMM) — alias a shared prefix once, then let the GPU MMU diverge
branches lazily by mapping fresh physical pages over the shared virtual addresses. We test this intuition
directly and show the abstraction is the wrong one, along three compounding axes, and we concede the one
place it is right.

- **(I) Capacity — a per-device vendor cliff [CLAIM-0002 / CLAIM-0004; EXP-A002, EXP-A004, EXP-A007].**
  A *conserved per-device* CUDA-VMM access-descriptor budget — measured at **523,404 mappings (+/-0.6%)**,
  deterministic to 0.000% variance across three independent paths and charged at `cuMemSetAccess` —
  hard-caps how many CoW branch mappings a device can hold. The budget is device-wide and splits evenly
  across contexts (n=1: 523,404; n=2: ~260K each; n=3: ~174K each), so it is *not* per-context: concurrent
  branching divides one fixed pool. AMD MI350X exhibits no such wall up to 80,000,000 mappings (**153x**
  more headroom), so this is a *vendor-specific portability cliff*, not a universal GPU law.
- **(II) Per-op cost — CoW is dominated even below the ceiling [CLAIM-0001; EXP-A001].** Even where
  capacity is not binding, HW VMM CoW *never wins*: across a 12-cell prefix x fanout x rollback grid it is
  **0/12** in any win-region, **1.06-2.20x slower than software prefix-sharing** (both arms measured), and
  on an analytic paged-step projection ~**41-152x slower than FlashInfer**.
- **(III) Compound — end-to-end throughput collapse [CLAIM-0003; EXP-A003] (the keystone).** The capacity
  cliff (I) and the per-op slowdown (II) *multiply*: across 8 fanout regimes HW wins **0/8**, crashes at the
  mapping ceiling for **every B>=128** (`cuMemSetAccess`), while software prefix-sharing scales cleanly
  **280->800 tok/s**. The effective branch ceiling collapses by orders of magnitude under realistic load.
- **(Concession) The one real capability delta [CLAIM-0007; EXP-A007].** We looked hard for a HW win and
  found exactly one: a forked branch's CoW edit is **bit-identical to a full clone (max_abs_diff = 0.0)** and
  **attention-kernel-transparent** — a write-after-share semantics that software prefix-sharing cannot
  structurally express. This narrow correctness/capability property does not rescue VMM on capacity or
  performance grounds.

**Thesis.** *For agentic KV-cache branching, hardware CUDA-VMM copy-on-write is dominated on per-operation
cost, hard-capped by a conserved ~520K per-device mapping budget that is a vendor portability cliff (absent
on AMD), and these compound into end-to-end throughput collapse; the sole structural advantage of HW CoW —
a bit-identical, kernel-transparent write-after-share — does not redeem it. Build software prefix-sharing,
not HW VMM CoW.*

---

## 1. Introduction / Motivation

Modern agentic LLM serving no longer treats a conversation as a single linear sequence. An agent forks its
state into many *speculative branches*: it explores several tool calls, samples multiple candidate
continuations, runs tree-search over reasoning paths, or maintains a fan-out of sub-agent conversations.
All of these branches share a long common prefix — the system prompt, the tools manifest, the conversation
so far — and diverge only at the tail. The dominant cost of serving such workloads is the KV cache, and the
dominant *opportunity* is that the shared prefix's KV need only be stored once.

This shape — one long shared prefix, many short divergent tails — is the textbook motivation for
copy-on-write. And once one frames the problem as CoW over the KV cache, NVIDIA's CUDA Virtual Memory
Management (VMM) API looks like the natural hardware acceleration: reserve a contiguous virtual address
range, back the shared prefix with physical pages once, alias those pages into each branch's virtual range,
and let the GPU MMU diverge branches lazily by mapping fresh physical pages over the shared addresses on
first write. The attention kernel never changes — it sees a contiguous virtual KV buffer per branch — and
the divergence is handled entirely in the page tables. On paper, this is exactly what CoW hardware is for.

**We test that intuition and reject it.** This paper is a *measured negative result*: we built both the
hardware VMM-CoW branching mechanism and a software prefix-sharing baseline (a radix/refcount page table in
the vLLM-APC / RadixAttention lineage), measured them head-to-head on production GPUs (NVIDIA H100, AMD
MI350X), and found that HW VMM CoW loses on every axis that matters. We organize the indictment as three
compounding pillars plus one honest concession:

- **(I) Capacity (Section 3).** CUDA-VMM enforces a hard, conserved *per-device* mapping ceiling — ~523,404
  access descriptors — that caps how many CoW branch mappings a device can hold, and that AMD does not
  enforce. This is a vendor portability cliff.
- **(II) Per-op cost (Section 4).** Even below that ceiling, HW VMM CoW is *dominated* — it never wins
  against software prefix-sharing across a 12-cell grid, and is far slower than production paged-attention
  kernels.
- **(III) Compound (Section 5).** The capacity cliff and the per-op slowdown multiply into an end-to-end
  serving throughput collapse: HW wins zero of eight fanout regimes and crashes at the ceiling under load,
  while software scales. This is the paper's keystone.
- **(Concession, Section 6).** There is exactly one thing HW CoW does that software cannot: a bit-identical,
  kernel-transparent write-after-share. We concede it precisely so the negative result reads as rigorous
  rather than motivated.

We distinguish this contribution up front from the positive-result prior art (Section 7). Existing
CUDA-VMM-for-KV work (notably vAttention, arXiv:2405.04437) uses VMM for *read-only* prefix sharing and never
enters the fork/CoW branching regime that the per-device budget binds. Software prefix-sharing systems
(vLLM PagedAttention/APC, SGLang RadixAttention) propose mechanisms to *use* sharing; here, software
prefix-sharing is simply the baseline that *wins*. Our angle is the negative/characterization one: VMM CoW
is dominated, the ceiling is a vendor cliff, and these compound — a regime the positive-result literature
structurally does not occupy.

---

## 2. Background

### 2.1 CUDA Virtual Memory Management and the CoW-branching intuition

The CUDA VMM API (`cuMemCreate`, `cuMemMap`, `cuMemSetAccess`, and the reservation primitive
`cuMemAddressReserve`) decouples virtual address reservation from physical backing. A program reserves a
contiguous virtual range, creates physical allocation handles, maps handles into virtual offsets, and then
*grants access* to a mapped range via `cuMemSetAccess`. Crucially, a single physical handle can be mapped
into many distinct virtual addresses — this is what makes aliasing (and therefore CoW) expressible at the
driver level rather than in the kernel.

For agentic KV branching, the intended use is:
1. Back the shared prefix's KV pages with physical handles once.
2. For each new branch, reserve a contiguous virtual KV range and alias the shared prefix handles into it,
   granting read access via `cuMemSetAccess`.
3. On the branch's first divergence, allocate fresh physical pages and remap (the copy-on-write step),
   leaving the prefix untouched and shared.

The appeal is that the attention kernel is *unmodified*: each branch presents a contiguous virtual KV
buffer, and all divergence lives in the GPU MMU. This is the abstraction we indict.

### 2.2 Software prefix-sharing (the baseline)

The software baseline is the now-standard radix/refcount page-table approach. KV is stored in fixed-size
blocks; a block table maps logical positions to physical blocks; shared prefix blocks carry a reference
count, and divergence allocates a fresh block and decrements/increments refcounts. This is the lineage of
vLLM PagedAttention with Automatic Prefix Caching (APC) and SGLang RadixAttention: token-prefix equality
implies KV-block sharing, captured in a software radix tree. The fork cost is a bounded refcount-update plus
structural-sharing pointer ops — a textbook accounting cost. In this paper, software prefix-sharing is not a
contribution; it is the measured baseline that HW VMM CoW must beat, and does not.

### 2.3 The read-only-vs-CoW boundary (vs vAttention)

It is essential to fence the closest prior art at the outset. vAttention (arXiv:2405.04437) also uses
CUDA-VMM for the KV cache and also keeps the attention kernel unmodified, but it does so for *read-only*
contiguous-VA KV — it does not fork branches and does not perform CoW divergence. The object of this paper
is precisely the fork/CoW divergence step and the per-device access-descriptor budget that binds it — a
regime vAttention never enters. We return to this in Section 7.

---

## 3. Pillar I — Capacity: the per-device mapping cliff
### [CLAIM-0002 + CLAIM-0004; EXP-A002, EXP-A004 (e3d), EXP-A007 (r1)]

**Claim.** The NVIDIA ~520K CUDA-VMM *per-device* mapping ceiling is a vendor-specific portability cliff:
we reproduce **523,404 mappings (+/-0.6%)**, the failure charged at `cuMemSetAccess`, while AMD MI350X shows
no wall to 80,000,000 mappings (**153x**).

### 3.1 The ceiling is deterministic and charged at `cuMemSetAccess`

When branch mappings are aliased into virtual ranges and access is granted, the device exhausts a fixed
access-descriptor budget and the *next* `cuMemSetAccess` call fails. The exhaustion point is a hard
constant: **523,404 mappings**, deterministic to 0.000% variance across three independent measurement paths
— the one-reservation alias probe (EXP-A007/`r1.json`: `mappings_before_fail: 523404`, `va_reserves: 1`,
`oom_call: cuMemSetAccess`), the clean-GPU control, and the n=1 context sweep (EXP-A004/`e3d_results.jsonl`,
n=1 -> 523,404). It is the headline value in EXP-A002 (`experiment.yaml`: "523,404 +/-0.6%") and the
`K_CEILING = 523404` constant driving the throughput experiment (EXP-A003/`impl/bench_ET_tax_throughput.py`).
The failure is independent of OS-level VMA limits (`vm.max_map_count`): the device fails at ~523K access
descriptors while the process holds only a few hundred VMAs, confirming the limit lives in the NVIDIA driver
/ GPU mapping-metadata layer, not the host kernel.

### 3.2 The budget is per-device, not per-context (conserved, splits ~K/n)

The single most important characterization — and the one a hostile reviewer would attack hardest — is
*what* is conserved. The budget is **per-device**: it is a single device-wide pool that all contexts draw
from, splitting approximately evenly across them. EXP-A004's clean per-device sweep (`e3d_results.jsonl`)
shows the total mapping count holding constant while dividing across contexts:

| Contexts (n) | Per-context mappings | Total |
|---|---|---|
| 1 | 523,404 | 523,404 |
| 2 | 260,281 + 263,003 | 523,284 |
| 3 | 171,633 + 174,206 + 177,325 | 523,164 |

The total is conserved at ~523,300 (+/-0.05%) and splits ~K/n — the textbook signature of a *per-device*
budget shared across contexts, not a per-context one. This is exactly what the original promotion consensus
headlined ("the conserved per-device budget"), and it is the correct framing: two concurrent branching
contexts each get ~260K mappings, not ~520K each. (An earlier draft phrasing "per-context" was a wording
defect that inverted this evidence; the corrected, evidence-aligned framing is per-device, per the
CLAIM-0002/0004 evidence corrections.)

### 3.3 Reconciling the two ceiling numbers (523,404 vs 519,936)

The ceiling appears in the artifacts as two numbers that are the *same underlying per-device
access-descriptor budget measured two ways*; we state the reconciliation explicitly to forestall any
apparent inconsistency. **523,404** is the pure single-reservation alias ceiling — the budget charged at
`cuMemSetAccess`, deterministic to 0.000% variance across the three independent paths above — and is the
value this paper headlines (523,404 +/-0.6%). **519,936** is the *median realized B x P* (branches x
prefix-pages) over the older Metric-4b prefix-size sweep (522,752 mappings at a 1 GiB prefix down to 516,096
at a 12 GiB prefix; median 519,936), used solely as the input constant K to the e3c
deployment-envelope *model* (EXP-A004/`e3c_relevance.py`), not as a measurement. It sits a fraction below
the pure ceiling because multi-branch runs also spend VA reservations, which draw from the *same* per-device
budget at a heavier weight than a bare mapping. The two numbers therefore bracket the ceiling consistently —
a ~0.66% spread predicted by the reservation-overhead model — rather than being a genuine inconsistency. We
headline 523,404 (measured ceiling) and label 519,936 as a model input (median B x P).

### 3.4 Cross-vendor: NVIDIA wall, AMD none (153x) — a portability cliff, not a GPU law

The ceiling is **NVIDIA-driver-specific**. On AMD MI350X (ROCm 7.0.2.1, gfx950, 288 GiB HBM), a
triple-watchdog-safe probe mapped **all 80,000,000** shared-physical -> distinct-VA pages
(`hipMemMap` + `hipMemSetAccess` each) with **zero driver failure** — **153x** NVIDIA's 520K wall — and 80M
was our own hard cap, not an AMD ceiling. This is corroborated across three independent AMD runs at three
scales (4M, 50M, 80M mappings), none of which hit a mapping-metadata wall, against NVIDIA's reproducible
hard failure at the *same* ~520K. AMD's VMM granule is 4 KiB versus NVIDIA's 2 MiB (a 512x finer granule),
and AMD draws no access-descriptor ceiling in any safely reachable VA range
(`511ce2e2__CROSSVENDOR_RESULT.md`).

The honest characterization is therefore a **vendor driver-architecture divergence with portability
consequences**: a VMM-CoW branching design that scales on AMD hits a hard wall on NVIDIA. This is a
*stronger and more falsifiable* claim than "structural GPU limit" — it survives the "single-driver quirk"
objection precisely *because* we measured the divergence rather than asserting universality.

**Threat to validity (driver-version scope).** The NVIDIA ceiling was measured under **CUDA 12.8 / driver
580.82.07** on H100 with a 2 MiB granule. We present it as scoped to that measured driver stack; future
NVIDIA driver versions are an explicitly stated scoped limitation, not a claim of permanence. (Per the
project's safety record, re-probing the mapping ceiling is operationally hazardous — unbounded VMM mapping
probes destabilized host nodes during data collection — so the scoping is a stated threat-to-validity, not a
re-run instruction.)

---

## 4. Pillar II — Per-op cost: CoW is dominated below the ceiling
### [CLAIM-0001; EXP-A001]

**Claim.** Even where capacity is not binding, HW VMM CoW is *dominated* for agentic KV: **0/12** win-region,
**1.06-2.20x slower** than software prefix-sharing (both arms measured), and **41-152x slower** than
FlashInfer (analytic paged-step projection).

### 4.1 The grid

EXP-A001 (`ec_rollback_e2e.csv`) measures a 12-cell grid — prefix {long 4096, short 512} x branch
fanout N {4, 16} x rollback depth R {0, 4, 16} — with four arms per cell:

- `hw_vmm_cow` — measured (SDPA contiguous decode over CoW KV + real driver CoW);
- `hw_vmm_cow_fullfwd` — measured (full real-model forward per token);
- `sw_prefix` — measured (SDPA contiguous decode + software block-table bookkeeping);
- `flashinfer` — *analytic* (48 paged-steps at ~0.03 ms/batch + measured SW bookkeeping; **not** a real
  FlashInfer run).

### 4.2 HW VMM CoW never wins (0/12), 1.06-2.20x slower than software

Across all 12 cells, HW VMM CoW has **zero win-region**: there is no prefix/fanout/rollback combination in
which it beats software prefix-sharing. The measured per-op slowdown ratio `hw_vmm_cow / sw_prefix` ranges
from **1.056** (minimum, at long prefix / N=4 / R=0) to **2.195** (maximum, at short prefix / N=16 / R=16) —
i.e. **1.06-2.20x slower than software prefix-sharing**. Both numerator and denominator are *measured* arms,
so this result is self-healing: the "HW VMM CoW is dominated" thesis stands on measured data alone.

### 4.3 The FlashInfer multiple is analytic (and a bonus)

Against production paged-attention kernels the gap is far wider — `hw_vmm_cow / flashinfer` ranges from
**41.3** to **151.5** (i.e. **41-152x slower than FlashInfer**) — but we label this explicitly as an
**analytic paged-step projection, not a measured FlashInfer run**: the FlashInfer arm is constructed as
(paged-step latency x 48 steps) + a measured SW-bookkeeping term, with no real FlashInfer kernel invocation
in the dataset. We present it as a *bonus widening multiplier* on top of the already-proven measured SW
domination, not as a load-bearing measurement. A real FlashInfer cell would be a GPU-safe kernel-latency
bench (not a mapping probe) and would only widen an already-proven gap; it is not required for the thesis.

The takeaway: below the ceiling, where one might expect the GPU MMU's lazy divergence to pay off, HW VMM CoW
is simply slower than a software refcount table on every cell — and dramatically slower than the production
kernel baseline.

---

## 5. Pillar III — Compound: end-to-end throughput collapse (KEYSTONE)
### [CLAIM-0003; EXP-A003]

**Claim.** The capacity cliff (Pillar I) and the per-op slowdown (Pillar II) *compound* into end-to-end
throughput collapse: HW wins **0/8** fanout regimes, crashes at the ceiling for **every B>=128**, while
software prefix-sharing scales **280->800 tok/s**.

This is the paper's keystone. Pillars I and II each characterize a single axis; Pillar III shows they
*multiply* in a realistic serving loop. EXP-A003 (`et_tax_throughput.csv`) sweeps branch fanout
B in {4, 16, 64, 128, 256, 511, 919, 1124}, running both a HW VMM CoW arm and a software prefix-sharing arm
end-to-end.

### 5.1 HW: zero wins, and a sharp ceiling crash at B>=128

The HW arm wins **0 of 8** fanout regimes. More damningly, it *crashes at the mapping ceiling* for every
B>=128. We separate the two distinct failure modes the data records (and recommend any published table do
the same), so the boundary reads cleanly:

| B | HW result | crash class | crash call |
|---|---|---|---|
| 4 | clean | — | none |
| 16 | crashed | **transient** | `transient_cublas(1of3reps; NOT_ceiling)` (2/3 reps OK) |
| 64 | clean | — | none |
| 128 | crashed | **ceiling** | `cuMemSetAccess@B~63` |
| 256 | crashed | **ceiling** | `cuMemSetAccess@B~210` |
| 511 | crashed | **ceiling** | `cuMemSetAccess@B~360` |
| 919 | crashed | **ceiling** | `cuMemSetAccess_ceiling(illegal_access)@B~171` |
| 1124 | crashed | **ceiling** | `cuMemSetAccess@B~357` |

The ceiling crash (`cuMemSetAccess`) first appears at **B=128** and occurs at **every** B>=128
(128/256/511/919/1124). The only sub-128 crash is B=16, and it is a *different* failure mode — a transient
cuBLAS execution failure on 1 of 3 reps (2/3 reps succeeded), explicitly tagged `NOT_ceiling`. B=64 is
clean, confirming the B>=128 ceiling boundary is sharp. Distinguishing `ceiling_crash` from `transient` in
the table prevents a skimming reader from misreading the B=16 row as a fuzzy boundary.

### 5.2 Software: zero crashes, scales 280 -> 800 tok/s

The software prefix-sharing arm has **zero crashes** across all 8 fanout regimes and scales cleanly from
**280.5 tok/s** (B=4) to a peak of **799.79 tok/s** (B=919) — i.e. **280->800 tok/s**. Where HW collapses
at the ceiling, software's throughput *rises* with fanout because prefix sharing amortizes the shared KV
across more branches.

### 5.3 Why this is the keystone

Pillar III multiplies the capacity wall (Pillars I: CLAIM-0002/0004) by the per-op slowdown (Pillar II:
CLAIM-0001) into a measured serving collapse, against a software baseline that *scales*. The 0/12 per-op
result (EXP-A001) and the 0/8 fanout result (EXP-A003) are different measurement grids both reporting zero
HW wins — mutually reinforcing, not redundant. The effective branch ceiling collapses by orders of magnitude
under realistic load: an idealized ~520K mapping budget becomes, in vivo, a crash at B=128. This is the
systems-impact headline — the reason the keystone targets MLSys.

---

## 6. The honest write-after-share CONCESSION
### [CLAIM-0007; EXP-A007]

**Claim.** Attention-visible GPU-MMU write-after-share: a forked branch's CoW edit is **bit-identical to a
full clone (max_abs_diff = 0.0)** and **attention-kernel-transparent** — a capability software
prefix-sharing cannot structurally express.

We looked hard for a hardware win and found exactly one. When a branch performs a CoW edit after aliasing
the shared prefix, the resulting KV is **bit-identical to a full clone**: EXP-A007 (`e1b_result.json`)
reports `max_abs_diff_vs_clone: 0.0` (corroborated by `e1_result.json`, `r1.json`, `r2.json`). The
divergence is fully transparent to the attention kernel — the kernel sees a contiguous virtual KV buffer and
needs no modification to observe the post-write state. This is a genuine *write-after-share* semantics:
hardware lets a branch mutate shared-prefix-derived state in place, observed correctly by the unmodified
kernel, with zero numerical drift from a full copy.

Software prefix-sharing cannot structurally express this. A refcount block table shares blocks read-only and
must allocate a fresh block on divergence; it cannot offer an in-place, kernel-transparent,
bit-identical write over shared addresses — that is exactly the property the GPU MMU provides.

**Rhetorical role.** This concession is the paper's load-bearer. It is a *correctness/capability* property,
orthogonal to the *performance* domination of CLAIM-0001/0003: it does not contradict the negative result,
and it does not rescue VMM on capacity (Pillar I) or performance (Pillars II/III) grounds. We concede it so
the indictment reads as rigorous rather than motivated: we searched for a hardware advantage, found exactly
this one narrow capability, and report that it does not redeem the abstraction.

---

## 7. Related Work / Positioning

Our contribution occupies the *negative/characterization* angle: VMM CoW is dominated, the per-device
ceiling is a vendor cliff, and these compound into collapse — plus the one capability delta. The
positive-result prior art proposes mechanisms to *use* VMM/paging/sharing and structurally does not occupy
this angle.

**Closest prior art (fenced sharply).**
- **vAttention (arXiv:2405.04437)** — CUDA-VMM for KV, contiguous VA, unmodified attention kernel, but
  **read-only** sharing with **no fork/CoW branching**. Our object is the fork/CoW divergence step *and* the
  per-device access-descriptor budget that binds it — a regime vAttention never enters. This is the single
  most important boundary to state in the positioning sentence.
- **vLLM PagedAttention / APC (SOSP'23)** and **SGLang RadixAttention (NeurIPS'24)** — software
  prefix-sharing via paged KV and radix/refcount trees. These are not competitors; software prefix-sharing
  is the baseline that *wins* here (0/12 in EXP-A001, 0/8 in EXP-A003). RadixAttention's token-prefix = KV
  sharing is exactly the territory we fence as already-occupied (it is the project's DEAD-0006).
- **FlashInfer** — production paged-attention kernels; the dominant performance baseline (the 41-152x-faster
  analytic reference of Section 4).

**Adjacent 2026-era forward neighbors (occupancy, not collision).** A frontier scan surfaced a wave of 2026
KV-sharing work that is *adjacent but not colliding*: all are software-side, read-only-sharing, or
multi-agent mechanisms — none is HW-VMM-CoW — so none is a must-cite collision for the five promoted claims;
we cite them as forward-frontier occupancy. They are: ForkKV (arXiv:2604.06370, software copy-on-write
disaggregated KV for multi-agent), TokenDance (arXiv:2604.03143, collective KV sharing + quantified
multi-agent redundancy/scaling-gap), Tokencake (arXiv:2510.18586, KV-cache-centric multi-agent serving),
"On 10X Better Scalability: KV Stores Scale Up KV Cache" (arXiv:2511.16138, KV-store metadata-overhead
scaling bottleneck), Joint Encoding of KV-Cache Blocks (arXiv:2601.03067, block-metadata growth under
concurrency), SemShareKV (arXiv:2509.24832), KVShare (arXiv:2503.16525), QKVShare (arXiv:2605.03884)
(cross-request semantic / near-duplicate KV dedup beyond exact-prefix), and CacheSolidarity
(arXiv:2603.10726, prefix-cache side channels / multi-tenant isolation). (An optional further neighbor is
Category-Aware Semantic Caching, arXiv:2510.26835.)

**Distinguishing contributions.** (1) "VMM CoW is *dominated* for agentic KV" — a measured negative result,
not a sharing scheme. (2) "The ~520K per-device mapping ceiling is a *vendor portability cliff*" —
cross-vendor, root-caused to a conserved device-wide access-descriptor budget. (3) "These *compound* into
end-to-end throughput collapse" — the keystone. The capability delta (CLAIM-0007, bit-identical
write-after-share) is the one positive finding and sits outside the read-only-sharing prior art.

---

## 8. Conclusion — Build software prefix-sharing, not HW VMM CoW

For agentic KV-cache branching, hardware CUDA-VMM copy-on-write is dominated on per-operation cost
(0/12, 1.06-2.20x slower than software; EXP-A001), hard-capped by a conserved ~520K per-device mapping
budget that is a vendor portability cliff absent on AMD (523,404 +/-0.6%; AMD no wall at 80M = 153x;
EXP-A002/A004/A007), and these compound into end-to-end throughput collapse (HW 0/8, crashes at every
B>=128, software scales 280->800 tok/s; EXP-A003). The sole structural advantage of HW CoW — a bit-identical,
kernel-transparent write-after-share (max_abs_diff = 0.0; EXP-A007) — is a narrow correctness/capability
property orthogonal to performance, and does not redeem the abstraction. **The engineering conclusion is to
build software prefix-sharing, not HW VMM CoW.**

**Forward direction (future / separate work, explicitly not a PROJ-0001 claim).** The indictment points
toward characterizing the software-prefix-sharing winner's *own* cross-engine scaling limit — does the SW
radix/refcount tree have an analogous fanout/concurrency regime where its bookkeeping (not the KV bytes)
dominates, and is that regime cross-engine (vLLM-APC vs RadixAttention vs FlashInfer) or engine-specific?
This is the only residual frontier candidate, and we deliberately do *not* claim it: it requires a
GPU/serving experiment outside this work's scope, its most probable outcome is a derivable accounting
identity (bookkeeping cost is monotone in node-count x refcount-ops), and its multi-agent-redundancy slice is
already being addressed by ForkKV / TokenDance / Tokencake. We flag it as a possible separate future project,
not a claim of this paper, to avoid over-promising.

---

## Appendix A — Claim -> Section -> Experiment -> Headline Number Map

| Pillar | Section | Claim(s) | Experiment id(s) | Headline number(s) |
|---|---|---|---|---|
| I Capacity | 3 | CLAIM-0002, CLAIM-0004 | EXP-A002, EXP-A004 (e3d), EXP-A007 (r1) | 523,404 +/-0.6%; per-device split n=1/2/3; AMD 153x @ 80M |
| II Per-op | 4 | CLAIM-0001 | EXP-A001 | 0/12; 1.06-2.20x (measured); 41-152x (analytic) |
| III Compound (keystone) | 5 | CLAIM-0003 | EXP-A003 | 0/8; B>=128 ceiling crash; 280->800 tok/s |
| Concession | 6 | CLAIM-0007 | EXP-A007 (e1b) | max_abs_diff = 0.0, kernel-transparent |

## Appendix B — Number Traceability (every quantitative claim -> source file)

| Number | Meaning | Source |
|---|---|---|
| 523,404 (+/-0.6%) | per-device mapping ceiling at `cuMemSetAccess` | EXP-A007/`r1.json`; EXP-A002/`experiment.yaml`; EXP-A004/`e3d_results.jsonl` (n=1); EXP-A003/`bench_ET_tax_throughput.py` (`K_CEILING`) |
| n=1: 523,404; n=2: 260,281+263,003=523,284; n=3: 171,633+174,206+177,325=523,164 | per-device conservation + ~K/n split | EXP-A004/`e3d_results.jsonl` |
| 519,936 | median realized B x P (model input, not ceiling); spread 522,752 @1GiB -> 516,096 @12GiB | EXP-A004/`e3c_relevance.py`, `e3c_result.json` |
| 153x @ 80,000,000 (AMD no wall); also 4M, 50M runs | cross-vendor divergence; CUDA 12.8 / 580.82.07; ROCm 7.0.2.1 gfx950 | `511ce2e2__CROSSVENDOR_RESULT.md` |
| 0/12; 1.06-2.20x (recomputed 1.056-2.195, both measured) | per-op domination vs SW | EXP-A001/`ec_rollback_e2e.csv` |
| 41-152x (recomputed 41.3-151.5; ANALYTIC denominator) | vs FlashInfer (analytic paged-step projection) | EXP-A001/`ec_rollback_e2e.csv` (`flashinfer` rows tagged ANALYTIC) |
| 0/8; ceiling crash every B>=128; B=16 transient cuBLAS; SW 280.5 -> 799.79 tok/s | end-to-end throughput collapse | EXP-A003/`et_tax_throughput.csv` |
| max_abs_diff = 0.0 | bit-identical write-after-share vs full clone | EXP-A007/`e1b_result.json` |

---

*Draft status: full submittable prose, all 8 sections + abstract + 2 appendices complete. Every
quantitative claim traces to a promoted claim and a registered experiment (cited inline + Appendix B). No
number invented. Written under prior_art/PROJ-0001/ only; no claims/verdicts/map edits/experiments.*
