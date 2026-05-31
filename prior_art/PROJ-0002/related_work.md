# Related Work — PROJ-0002 (prefix-cache invalidation + KV reusability)

See also per-claim notes under CLAIM-0006/. Core prior art:
| Work | Core idea | Diff |
|---|---|---|
| SGLang RadixAttention (NeurIPS'24) | radix prefix cache | token-prefix sharing; our CDC repair targets mid-prefix INJECTION it doesn't cheapen (10–90% vs CDC ~2%) |
| vLLM APC (SOSP'23) | automatic prefix caching | position-dependent recompute on injection |
| Continuum (arXiv 2511.02230) | KV-TTL retention | retains existing KV; orthogonal to invalidation-repair |
| Speculative Tool Calls (arXiv 2512.15834) | speculate which tool to call | not engine-side continuation prefill |

## Fresh re-search 2026-05-31 (researcher-cdc-priorart-A) — CDC repair is the COLLISION, the cost-map is the novelty
See CLAIM-0006/fresh_priorart_note_LaneA-priorart.md + search_log_priorart-A.md for full table + source-independence accounting.
| Work | id/url | Core idea | Collision to CLAIM-0006 |
|---|---|---|---|
| **Irminsul** | arXiv:2605.05696 (2026-05-07) | extends **SGLang radix cache w/ content-hash keying over CDC-chunked segments** (Gear-hash rolling boundaries) + delta-rotation on RoPE k_r; agentic position-independent caching | **FATAL on MECHANISM** — same CDC-over-radix repair, same "tokens shifted -> prefix cache voided" motivation. Does NOT do the inj/seq cost-map. *Single independent index (arXiv only) so far -> strong WEAKEN flag, not yet an admissible >=2-source KILL.* |
| Cache-Craft | arXiv:2502.15734 | chunk-caches + small-fraction recompute to FIX the reused cache (RAG) | HIGH — "fix-with-partial-recompute" is the same genus as CDC repair |
| EPIC (ICML'25) | arXiv:2410.15332 | formalizes Position-Independent Caching (PIC); LegoLink | MEDIUM — PIC is the umbrella CDC repair sits inside (cite as prior art) |
| MEPIC | arXiv:2512.16822 | memory-efficient PIC; block-level partial recompute | MEDIUM — same PIC family |
| CacheBlend (EuroSys'25 Best Paper) | arXiv:2405.16444 | selective recompute of a small subset of non-prefix KV to partially update reused cache | MEDIUM — original "selective partial recompute" paper |
| CacheClip | arXiv:2510.10129 | effective KV reuse for RAG beyond strict prefix | MEDIUM |
| Don't Break the Cache (PwC) | arXiv:2601.06007 | black-box eval of provider prompt caching on agentic tool-calling; cost/TTFT vs prompt size & tool-count ("linear") | MEDIUM on COST axis — closest empirical neighbor, but black-box, no recompute-fraction law, no repair mechanism (CITE + distinguish) |
| Segment-Level KV Sharing (ICLR'26 sub) | OpenReview | "breaking the prefix barrier" multi-agent segment KV sharing | LOW-MED |
| CDC storage-dedup ancestry | FastCDC / Rabin / US11928092B2 / ETH "Breaking & Fixing CDC" | content-defined chunking localizes an edit: edited region re-chunks, surrounding boundaries preserved | FOUNDATIONAL — CDC insertion-resilience is textbook prior art; novelty cannot rest on it |

**NOVELTY VERDICT (researcher-cdc-priorart-A):** MECHANISM (CDC repair over radix/prefix cache) = NOT novel (Irminsul + PIC family). FRAMING (Prefix-Cache Invalidation LAW + conditional inj/seq recompute cost-map + head-to-head recompute-fraction vs vLLM-APC/SGLang-Radix/FlashInfer) = NOVEL, no collision found. Reframe CLAIM-0006 as a CHARACTERIZATION/LAW paper; CDC repair = a KNOWN realization whose win-region this work maps/bounds. Committee decides; this note makes that hallucination-proof.

## Update 2026-05-31 (VERDICT-0012, real 6/6 committee re-review — orchestrator-r2-001)
- **KVFlow** (arXiv:2507.07400) — NEW neighbor surfaced by novelty_killer. Agentic/multi-agent
  prefix-cache work; optimizes scheduling/reuse, does NOT publish an inj/seq invalidation law or
  recompute-fraction cost-map. Must be cited + distinguished in any CLAIM-0006 writeup.
- **Distinction still UNVERIFIED at body level** (GREEN-blocker): novelty_killer could confirm
  Irminsul (2605.05696) and "Don't Break the Cache" (2601.06007) exist (titles), but could NOT read
  their bodies to verify they lack the inj/seq cost-map. Since the cost-map IS the surviving
  contribution, this distinction must be verified, not asserted.
- **Framing downgrade**: committee consensus reword "Prefix-Cache Invalidation LAW" -> "CDC Recompute
  Characterization" — slope~1 is mechanism-derived (CDC insertion-resilience ~ R/S), not emergent.
- **New baseline requirement**: PIC-family head-to-head (Irminsul or EPIC implementation) is now
  MANDATORY — the current 3 baselines are structurally incapable of position-independent recovery,
  making the 8x-465x advantage a structural gap, not a competitive benchmark.

## Update 2026-05-31 (VERDICT-0012, real 6/6 committee re-review — orchestrator-r2-001)
- **KVFlow** (arXiv:2507.07400) — NEW neighbor surfaced by novelty_killer. Agentic/multi-agent
  prefix-cache work; optimizes scheduling/reuse, does NOT publish an inj/seq invalidation law or
  recompute-fraction cost-map. Must be cited + distinguished in any CLAIM-0006 writeup.
- **Distinction still UNVERIFIED at body level** (GREEN-blocker): novelty_killer could confirm
  Irminsul (2605.05696) and "Don't Break the Cache" (2601.06007) exist (titles), but could NOT read
  their bodies to verify they lack the inj/seq cost-map. Since the cost-map IS the surviving
  contribution, this distinction must be verified, not asserted.
- **Framing downgrade**: committee consensus reword "Prefix-Cache Invalidation LAW" -> "CDC Recompute
  Characterization" — slope~1 is mechanism-derived (CDC insertion-resilience ~ R/S), not emergent.
- **New baseline requirement**: PIC-family head-to-head (Irminsul or EPIC implementation) is now
  MANDATORY — the current 3 baselines are structurally incapable of position-independent recovery,
  making the 8x-465x advantage a structural gap, not a competitive benchmark.
