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

## Update 2026-05-31 (VERDICT-0017, real 6/6 committee — engine db3e67d nested-sandbox fix)
- **Surviving novelty narrowed to a SINGLE leg**: the engine-internal inj/seq recompute cost-map
  characterization. Two legs RETIRED by committee consensus:
  1. The 8x-465x head-to-head = STRUCTURAL ARTIFACT of contiguous baselines (EXP-0006).
  2. slope~1 "law" + position-independence = MECHANISM-DERIVED accounting identity, not an emergent
     discovery — follows from contiguous-prefix KV accounting (**Pope et al. arXiv:2211.05102**,
     **Kwon et al. PagedAttention arXiv:2309.06180**). Demote "law" -> "accounting identity we quantify".
- **Novelty GREEN-gate (unverified)**: "Don't Break the Cache" (2601.06007) reports cost ~
  injected-tool-tokens / prompt-size — the SAME functional form. Distinction reduces to measurement
  granularity (engine-internal vs black-box) and is UNVERIFIED at body level. If 2601.06007 already
  publishes the cost-map at comparable granularity, the contribution collapses to a replication.
- **Eval GREEN-gate**: token-count proxy conflates CDC contiguous-chunk recompute (high arithmetic
  intensity) vs PIC scattered-HKVD (gather/scatter, kernel overhead). At the ~5% fraction-tie crossover,
  wall-clock could diverge 2-3x in either direction. MLSys needs GPU wall-clock on a REAL PIC artifact
  (CacheBlend/EPIC published, not the re-impl).

## Update 2026-05-31 (researcher-novelty-boundary-0006) — BODY-LEVEL distinction (closes VERDICT-0017 gate A, mostly)
Full per-neighbor analysis: CLAIM-0006/novelty_boundary_2026-05-31.md. I retrieved & parsed the FULL
HTML BODIES of the two GREEN-gate works (2601.06007, 2605.05696) — body-level, not abstract-only. PIC
family = abstract-level reads (scoped honestly below).

### Per-neighbor distinction table — does it publish CLAIM-0006's surviving leg?
Leg = engine-internal recompute-FRACTION-vs-inj/seq COST-MAP + position-not-driver finding.
| Work | (a) recompute% vs inj-size cost-map | (b) position-indep-OF-COST finding | (c) engine-internal vs black-box | Read depth | VERIFIED? |
|---|---|---|---|---|---|
| **Don't Break the Cache** 2601.06007 | **NO** (measures $-cost & ms-TTFT, axes = prompt-SIZE + tool-COUNT, not inj/seq) | **NO** (only layout heuristic "put dynamic content at end") | **BLACK-BOX provider API** (no vLLM/SGLang/engine) | FULL BODY §1-7+App | **VERIFIED** — collapse-to-replication worry is FALSE |
| **Irminsul** 2605.05696 | **NO** (metrics = token-recovery%, prefill ENERGY, hit-rate, attn-sink fractions; partition-shift diagnostic predicts its OWN recovery, not a cost contour) | NO (does an attn-sink/first-chunk analysis, not a cost-vs-position law) | engine (SGLang radix) | FULL BODY §1-8+App | **VERIFIED** — mechanism TWIN, but no cost-map |
| EPIC 2410.15332 | NO (TTFT, up-to-8x) | NO | engine | abstract | partial (abstract) |
| CacheBlend 2405.16444 | NO (selective recompute; speedup/quality) | NO | engine | abstract | partial (abstract) |
| Cache-Craft 2502.15734 | NO (-51% redundant compute, single RAG aggregate, not f(inj/seq)) | NO | engine | abstract | partial (abstract) |
| MEPIC 2512.16822 | NO (block-level recompute, mem-efficient PIC) | NO | engine | abstract | partial (abstract) |
| KVFlow 2507.07400 | NO (workflow-aware EVICTION/prefetch, not invalidation) | NO | engine | abstract | partial (abstract) |
| CacheClip 2510.10129 | NO (RAG KV reuse, TTFT) | NO | engine | abstract | partial (abstract) |

### Key verified findings
1. **2601.06007 does NOT collapse CLAIM-0006.** BODY: §3.3 "we measure two primary metrics: API cost
   and TTFT"; "linear" = $-savings vs PROMPT-SIZE (500-50k) and flat vs TOOL-COUNT (3-50). It has NO
   inj/seq axis, NO recompute-FRACTION, NO engine, NO position-independence finding (grep-confirmed:
   zero hits for vLLM/SGLang/radix/recompute-fraction/inj-seq/slope/cost-map). The "same functional
   form" fear (VERDICT-0017) is refuted at body level. This was the #1 GREEN-blocker → now CLOSED.
2. **Irminsul is the mechanism TWIN** (CDC content-hash keying over SGLang radix + Gear-hash rolling
   boundaries) — CDC-over-radix MECHANISM novelty is DEAD (body-confirmed). But Irminsul publishes NO
   inj/seq recompute-fraction cost-map; its metrics are token-recovery% + prefill energy + hit-rate +
   attn-sink fractions. CLAIM-0006's surviving leg is genuinely distinct from Irminsul's deliverable.
3. **Irminsul >=2-INDEX rule now SATISFIED** (was the LaneA single-source flag): Semantic Scholar
   (CorpusId 288013360) + OpenAlex (W7160639578) both index it as of 2026-05-31. (DBLP "irminsul" hit
   is a DIFFERENT work — discard.) Caveat: same primary work indexed x2, not 2 independent corroborating
   works; independent mechanism-genus corroboration comes from the PIC family (multi-source).
4. **slope~1 is an ACCOUNTING IDENTITY, not a law** — CONFIRMED. recompute=(R+W)/S ≈ R/S=inj/seq by
   contiguous-chunk KV bookkeeping (Pope 2211.05102 / Kwon PagedAttention 2309.06180). Position-flatness
   is the same identity, EXCEPT the p=0 attention-sink (Irminsul body confirms sink is sequence-start-
   local → genuinely position-dependent there; CLAIM-0006 must caveat). Only the achieved near-W=0
   re-sync on realistic inserts + the empirical inj/seq workload distribution (EXP-0005) are *measured*.

### Residual GREEN-blockers (assertion-only / not body-verified)
- PIC-family (EPIC/CacheBlend/Cache-Craft/MEPIC/KVFlow/CacheClip) distinction is ABSTRACT-level only —
  cannot 100%-exclude an appendix cost-map. LOW risk, cheap to close (CPU body reads). RECOMMEND before
  committee re-vote.
- Eval GREEN-gate (GPU wall-clock on REAL PIC artifact at ~5% crossover) is ORTHOGONAL and still the
  binding blocker — untouched here (GPU, human-go).
