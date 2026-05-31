# PROJ-0001 — Forward / 2-Degree Frontier Scan (where does the indictment thesis POINT NEXT?)

**Date:** 2026-05-31 · **Agent:** researcher-0001-frontier (forward-frontier lane, CPU-only, reading/literature only) ·
**Orchestrator session:** 22bd6bef-b84b-4827-a371-87443ea8602f
**Scope:** READ-ONLY. NO claim/verdict/map edits, NO experiments, NO seeding, NO binding to any promoted claim.
NO GPU / model CLIs / memory probes (MI350X_CRASH_POSTMORTEM honored). Wrote ONLY this file.
**Mandate:** the 1-degree neighborhood of PROJ-0001 is SATURATED (laneB completeness + laneD adjacent-hunt
both reach saturation via disjoint candidate sets; 5 GREEN promoted + 10 DEAD). This lane is explicitly a
**2-degree FORWARD scan**: given the proven thesis "software prefix-sharing beats HW VMM CoW for agentic KV
branching," where does it POINT NEXT, and is any forward direction genuinely open?

---

## TL;DR / VERDICT

**The forward frontier is ALSO covered / premature. PROJ-0001's 5-claim CoW/ceiling thesis is complete.**
I generated 6 forward (2-degree) candidates spanning the three forward questions in the brief (next SW
bottleneck; cross-request dedup; branch-metadata cost; and a positive SW-side cost-model characterization).
Every one is killed by ONE of two forces:

1. **Fresh occupied territory** I surfaced that was NOT in MAP-0001's key_prior_work (all 2026-era):
   ForkKV (arXiv:2604.06370, SW **copy-on-write** disaggregated KV for multi-agent), TokenDance
   (arXiv:2604.03143, collective KV sharing + quantified multi-agent **redundancy/scaling-gap**), Tokencake
   (arXiv:2510.18586, KV-cache-centric multi-agent serving, space+time contention), "On 10X Better
   Scalability: KV Stores Scale Up KV Cache" (arXiv:2511.16138, KV-cache **metadata-overhead scaling
   bottleneck** of the storage data structure), SemShareKV (arXiv:2509.24832) / KVShare (2503.16525) /
   QKVShare (2605.03884) / Category-Aware Semantic Caching (2510.26835) (**cross-request semantic / near-dup
   KV dedup beyond exact-prefix**), CacheSolidarity (arXiv:2603.10726, prefix-cache **side channels /
   multi-tenant** isolation), and the classic persistent-data-structure / structural-sharing snapshot line
   (e.g. arXiv:2003.07395) that already characterizes branch-bookkeeping cost.
2. **The project's OWN established accounting-identity kill pattern** (DEAD-0009 / DEAD-0010 / the
   slope~1 and "cost-model" red_zones, and laneD's cross-cutting saturation observation): a "positive SW
   cost model" reduces to textbook refcount + persistent-data-structure path-copy accounting (O(1) refcount /
   O(log n) structural sharing), i.e. a deterministic restatement, not a non-derivable anomaly.

**ONE candidate (F-NEG below) is the closest to genuinely-open** — a *measured negative* "where does
software prefix-sharing's OWN data structure stop scaling at extreme branch fanout, cross-engine?" — but it
is **premature, not seeded**: it requires GPU/serving measurement (none permitted here), its most likely
outcome is another accounting-identity (the structure is monotone in nodes x refcount-ops), and the
multi-agent-redundancy framing of that question is already being eaten by ForkKV/TokenDance/Tokencake. I
document it for the orchestrator to judge; I do **not** recommend seeding it as-is and it is **not** bound to
any promoted claim. Both "confirmed complete" and "F-NEG is a maybe-open seed for a *separate* future project"
are honest reads; I lean **confirmed-complete** on the weight of evidence.

---

## Why this is a 2-degree scan, not a re-mine of the saturated 1-degree

The 1-degree neighborhood is all about **HW VMM CoW being wrong** (CLAIM-0001/0002/0003/0004/0007 + DEAD-0001..0010).
laneB + laneD exhausted it. The 2-degree question is the *complement*: now that SW prefix-sharing is the
established winner, what is the next open question **about the SW winner itself** (its data structure, its
metadata, its scaling, its positive cost model) — a forward direction the indictment thesis points to but
does NOT itself claim. That is the space I scanned. The finding is that the SW-winner space is a SEPARATE,
already-crowded research area (vLLM-APC / RadixAttention + the 2026 multi-agent-KV-sharing wave), not an open
extension of PROJ-0001.

---

## Per-candidate forward ledger (HEAVY early-kill, 2-degrees out)

### Forward question (1): the NEXT bottleneck in SW agentic-KV-branching

| # | Forward candidate | Verdict | Collision evidence (literature + project) |
|---|---|---|---|
| F1 | **SW prefix-sharing data-structure's own scaling limit at extreme branch fanout** (radix/refcount tree metadata cost, node count, eviction bookkeeping when fanout -> 10^4-10^6 branches) | **KILL — occupied (fresh) + identity** | "On 10X Better Scalability: KV Stores Scale Up KV Cache" (arXiv:2511.16138) IS the KV-cache-storage **metadata-overhead scaling bottleneck** paper (file-per-object metadata, I/O, poor scalability -> KV-store layout). "Joint Encoding of KV-Cache Blocks for Scalable LLM Serving" (arXiv:2601.03067) attacks the block-metadata growth under concurrency. The *radix-tree* node/eviction cost is RadixAttention/vLLM-APC territory + the persistent-data-structure literature (structural-sharing snapshot trees, arXiv:2003.07395) which already gives the O(log n) path-copy / O(1) refcount cost. Any "law" here = deterministic data-structure accounting = the laneD cross-cutting saturation kill (DEAD-0009/0010 mode). |
| F2 | **Cost of the branch-metadata itself** (refcount/CoW-bookkeeping per branch as a first-class characterized tax) | **KILL — identity + DEAD-0009/0010 pattern** | This is exactly the failure mode the project already named: the SW fork tax is bounded by refcount-update + structural-sharing pointer ops, a textbook accounting identity (CLAIM-0001 already MEASURED SW fork as 240x faster than HW at fork — the metadata cost is already inside the winning baseline's measured number). No non-derivable anomaly; revival door only if a metadata cost is measured that is NOT predicted by refcount + node-count accounting. |
| F3 | **Concurrency / lock contention on the shared prefix structure at high fanout** (the SW tree as a contended object) | **KILL — generic-CS occupied** | Reduces to the general concurrent-data-structure / contention-resolution literature (arXiv:2604.14530 "Fast Concurrent Primitives Despite Contention"; arXiv:2408.13779 "Concurrent Data Structures Made Easy"). Not KV-specific; the LLM-serving scheduling angle is "LLM Query Scheduling with Prefix Reuse" (arXiv:2502.04677). No KV-branching-specific open law; a contention measurement is a generic systems result, not a forward extension of the indictment. |

### Forward question (1b): cross-request KV dedup (beyond intra-request prefix sharing)

| # | Forward candidate | Verdict | Collision evidence |
|---|---|---|---|
| F4 | **Cross-request / cross-agent KV deduplication** (share KV beyond a single request's exact prefix — semantic / near-duplicate / collective) | **KILL — densely occupied (fresh)** | SemShareKV (arXiv:2509.24832, token-level LSH semantic-similar-prompt KV sharing), KVShare (2503.16525, semantic-aware multi-user KV sharing), QKVShare (2605.03884, quantized cross-agent KV handoff), Category-Aware Semantic Caching (2510.26835), and crucially **TokenDance** (2604.03143, "Collective KV Cache Sharing" — explicitly quantifies and attacks multi-agent cross-request KV **redundancy**, 99.3% pool saturation) + **Tokencake** (2510.18586) + ICLR-2026 "Collaborative Memory ... Segment-Level KV Cache Sharing" (openreview c8adae36). This is a hot, crowded area. Also: DEAD-0006 already fenced "token-prefix predicts KV sharing -> RadixAttention captures it"; the semantic-extension is owned by the SemShare/KVShare line. KILL. |

### Forward question (2): a DEFENSIBLE POSITIVE SW-side characterization (what the right abstraction's cost model IS)

| # | Forward candidate | Verdict | Collision evidence |
|---|---|---|---|
| F5 | **A positive cost model of the winning SW prefix-sharing abstraction** (the project's claims are all "HW is wrong"; state affirmatively what the SW abstraction's cost model IS — $/branch, fork cost, share cost, scaling form) | **KILL — identity (the project's own pattern), and partly pre-stated** | The SW cost model is: fork = refcount bump + (CoW divergence on write) structural-sharing path-copy; capacity = sum of unique (non-shared) pages; this is the textbook persistent / functionally-shared data-structure accounting (arXiv:2003.07395 structural sharing; standard radix/refcount). PROJ-0001 already MEASURED the load-bearing positive numbers (SW scales 280->800 tok/s, fork 240x faster than HW, 0/12 + 0/8 HW-win) — the positive SW characterization is already *in* the indictment as the winning baseline. Promoting it to a standalone "cost-model" claim is the exact DEAD-0003 / "cost-model" / slope~1 red_zone failure: a deterministic restatement of a conserved quantity, no non-derivable anomaly. KILL as a new thesis. |

### Adjacent forward direction surfaced during the scan (NOT one of the 3 brief questions, flagged for completeness)

| # | Forward candidate | Verdict | Collision evidence |
|---|---|---|---|
| F-SC | **Multi-tenant safety/side-channel of SW prefix-sharing** (sharing the prefix structure across tenants leaks timing) | **KILL — occupied (fresh) + DEAD-0001 family** | CacheSolidarity (arXiv:2603.10726) IS the prefix-caching side-channel / multi-tenant-isolation paper. And the *isolation-as-a-primitive* angle is buried by DEAD-0001 (SW matches HW isolation bit-identically + 240x faster) / DEAD-0002 (handle attestation forgeable). KILL. |

### The one closest-to-open candidate (documented, NOT seeded)

| # | Forward candidate | Verdict | Honest assessment |
|---|---|---|---|
| **F-NEG** | **A MEASURED NEGATIVE: "where does software prefix-sharing's OWN data structure stop scaling at extreme branch fanout, characterized cross-engine?"** — i.e. the SW-winner's *own cliff* (if any), analogous to how PROJ-0001 found HW's 520K cliff. Does the SW radix/refcount tree have an analogous fanout/concurrency regime where its bookkeeping (not the KV bytes) dominates, and is that regime cross-engine (vLLM-APC vs RadixAttention vs FlashInfer) or engine-specific? | **MAYBE-OPEN but PREMATURE — do NOT seed as-is** | This is the only candidate not fully pre-killed: it is a *negative/characterization* in the same rigorous spirit as PROJ-0001 (find the winner's own breaking point), and I found NO paper that measures a SW-prefix-sharing *data-structure* cliff cross-engine as a first-class result (the 2026 wave attacks redundancy/contention with new *mechanisms*; none publishes the bookkeeping-vs-bytes crossover as a characterized law). **HOWEVER three forces make it premature, not a clean seed:** (a) it REQUIRES GPU/serving measurement — forbidden here, CPU-only; (b) its most probable outcome is yet another accounting identity (bookkeeping cost is monotone in node-count x refcount-ops -> derivable -> the DEAD-0009/0010 / "cost-model" red_zone kill the project has applied five times); (c) the *multi-agent-redundancy* slice of this question is already being eaten by ForkKV / TokenDance / Tokencake — a new entrant must body-distinguish from all three. **NET: a possible seed for a SEPARATE future project (the SW-winner's own scaling characterization), explicitly NOT a PROJ-0001 extension and NOT bound to any promoted claim. I lean toward it being premature/identity-bound; orchestrator to judge whether the cross-engine *measured-crossover* framing clears the identity bar with a real serving experiment.** |

---

## Cross-cutting observation: why the forward frontier is also closed

The two load-bearing quantities of the SW winner — the **prefix-sharing tree's bookkeeping** (refcount +
structural-sharing path-copy) and the **unique-page capacity** — are BOTH textbook-derivable accounting
identities, the same structural reason laneD gave for the 1-degree saturation. So any forward "SW cost-model"
or "SW scaling-law" candidate is pre-killed by the project's own identity test UNLESS it produces a measured,
non-derivable anomaly (a SW cliff not predicted by node-count x refcount accounting). Simultaneously, the
*non*-accounting forward slices (cross-request dedup, multi-agent collective sharing, side-channels,
contention, metadata-storage scaling) are each now a crowded, separately-owned 2026 research area (ForkKV,
TokenDance, Tokencake, SemShareKV/KVShare/QKVShare, CacheSolidarity, "10X KV-Stores", Joint-Encoding). There
is no forward direction that is BOTH (a) a non-derivable open question AND (b) unoccupied AND (c) a genuine
extension of the CoW/ceiling indictment rather than a separate area. F-NEG is the single residual "maybe,"
and it is gated on a forbidden GPU experiment + a high identity-collision risk.

## Recommendation to orchestrator
- **Treat PROJ-0001's 5-claim CoW/ceiling thesis as COMPLETE** (consistent with PUBLICATION_READINESS GO and
  laneB/laneD saturation). The forward 2-degree frontier does not yield a clean open extension.
- **F-NEG is the only documented residual.** If the orchestrator wants a *successor* project (not a PROJ-0001
  claim), the candidate is: "the SW-prefix-sharing winner's OWN cross-engine scaling characterization — does
  bookkeeping ever dominate bytes, and is there a SW cliff analogous to NVIDIA's 520K?" — but it must (1) clear
  the accounting-identity bar with a measured non-derivable anomaly, (2) body-distinguish from ForkKV
  2604.06370 / TokenDance 2604.03143 / Tokencake 2510.18586 / "10X KV-Stores" 2511.16138, and (3) be run on a
  GPU/serving env (forbidden in this lane). I did NOT seed it.
- **MAP-0001 key_prior_work is missing the 2026 forward neighbors** I surfaced (ForkKV 2604.06370, TokenDance
  2604.03143, Tokencake 2510.18586, "10X KV-Stores" 2511.16138, SemShareKV 2509.24832, KVShare 2503.16525,
  QKVShare 2605.03884, CacheSolidarity 2603.10726, Joint-Encoding 2601.03067). These do NOT collide with the
  5 promoted claims (all are SW-side / read-only-sharing / multi-agent mechanisms, not HW-VMM-CoW), so they are
  NOT a must-cite gap for the publication — but the orchestrator may want them logged as the forward-frontier
  occupancy that closes the 2-degree space. (Map edit is out of my lane — flag only.)

## Files / paths referenced
- This file: prior_art/PROJ-0001/FRONTIER_SCAN_2026-05-31.md
- Inputs: prior_art/PROJ-0001/{PUBLICATION_READINESS.md, PAPER_SYNTHESIS_laneE.md, ADJACENT_GAP_HUNT_laneD.md,
  COMPLETENESS_AUDIT_laneB.md, related_work.md, 511ce2e2__CROSSVENDOR_RESULT.md, needs_attention.md}
- registry/academic_map.yaml (MAP-0001), registry/claims/PROJ-0001/2026-05-31/CLAIM-{0001,0002,0003,0004,0007}.yaml
- registry/cemetery/PROJ-0001/{2026-05-30,2026-05-31}/DEAD-0001..0010.yaml
- PROJ-0002 prefix-cache neighbors: prior_art/PROJ-0002/CLAIM-0006/novelty_boundary_2026-05-31.md
- Forward literature (NEW, surfaced this lane): arXiv 2604.06370, 2604.03143, 2510.18586, 2511.16138,
  2601.03067, 2509.24832, 2503.16525, 2605.03884, 2510.26835, 2603.10726, 2502.04677, 2604.14530, 2003.07395

(No claims seeded. No verdicts. No map edits. No experiments registered. No binding to any promoted claim.
CPU/reading-only — no GPU/model CLIs/memory probes. Wrote ONLY prior_art/PROJ-0001/FRONTIER_SCAN_2026-05-31.md.)
