# Fresh Prior-Art / Novelty Re-Search — CLAIM-0006 (Lane: prior-art/novelty)
agent: researcher-cdc-priorart-A | role: researcher | prompt_version: v001
date: 2026-05-31 | scope: REQUIRED freshness re-search (>14d, fast-moving area, heading to committee)
project: PROJ-0002 | claim: CLAIM-0006 (Prefix-Cache Invalidation Law + CDC repair, conditional inj/seq cost-map)

## Why this re-search
Freshness rule fired: fast-moving area (vLLM/SGLang/LMCache/FlashInfer KV-cache), >14 days since last
prior-art pass, and CLAIM-0006 is heading to committee. Lane A (researcher-cdc-baselines-A) already
positioned the 3 MANDATORY BASELINES mechanistically. THIS note is the independent NOVELTY hunt:
does any 2024-2026 work already do (a) content-defined / shift-tolerant / insertion-resilient prefix-
cache REPAIR, or (b) characterize recompute cost as a function of injection-size/context (the inj/seq
cost-map)? Separating NAMING novelty from MECHANISM novelty.

## Headline finding (read this first)
The CLAIM-0006 artifact has TWO separable contributions, with OPPOSITE novelty status:

1. MECHANISM — "CDC (content-defined chunking, rolling-hash boundaries) over a radix/prefix cache to
   re-sync KV after a mid-prompt insertion." This is **NOT novel**. It collides hard with IRMINSUL
   (arXiv 2605.05696, 2026-05-07), which literally "extends SGLang's radix cache with content-hash
   keying over CDC-chunked segments" using a Gear-hash rolling boundary. Adjacent corroboration:
   Cache-Craft (small-fraction recompute to FIX a reused chunk-cache), EPIC/MEPIC (position-independent
   caching), CacheBlend/CacheClip (selective recompute of non-prefix KV). AND the underlying CDC
   insertion-resilience property is decades-old storage-dedup prior art (FastCDC, Rabin chunking,
   US patents). => The CDC-repair idea is, at the mechanism level, already in the literature.
   CAVEAT (anti-hallucination rule): the EXACT Irminsul mechanism-identity is currently a SINGLE
   retrievable independent index (arXiv; Semantic Scholar has not indexed it yet — 24 days old). Per
   the rule, a novelty KILL requires >=2 independent sources. So this is a STRONG NOVELTY-WEAKENING
   FLAG, not an admissible KILL on its own. Re-verify when a 2nd index (Semantic Scholar / DBLP /
   venue) picks it up. It is reckless to take CLAIM-0006 to committee claiming the CDC repair as the
   novel core.

2. FRAMING / CHARACTERIZATION — the "Prefix-Cache Invalidation LAW" + the CONDITIONAL inj/seq
   recompute COST-MAP (recompute% tracks injection_tokens/seq_len with slope~1; position/depth is
   NOT the cost driver; ~2% holds iff inj/seq <= ~1%, blows up to 20-53% otherwise) + the head-to-head
   recompute-FRACTION positioning against vLLM-APC / SGLang-RadixAttention / FlashInfer. This framing
   is **NOVEL** — NO prior work found derives recompute as f(inj/seq) for autoregressive prefix caches,
   and none presents the conditional cost-map contour. The closest empirical neighbor ('Don't Break the
   Cache', 2601.06007) is a black-box provider-API study (cost/TTFT vs prompt size & tool-call count),
   not an engine-internal recompute-fraction cost-map and not a repair mechanism.

## Closest prior work (ranked by collision risk to CLAIM-0006)
| rank | work | id/url | what it does | collision to CLAIM-0006 |
|---|---|---|---|---|
| 1 | Irminsul: MLA-Native Position-Independent Caching for Agentic LLM Serving | arXiv:2605.05696 (2026-05-07) https://arxiv.org/abs/2605.05696 | extends SGLang radix cache w/ content-hash keying over **CDC-chunked** segments + Gear-hash rolling boundaries + delta-rotation on RoPE k_r; recovers ~83% of prompt tokens above exact-prefix on agentic traffic, 63% prefill-energy savings | **FATAL on MECHANISM** (same CDC-over-radix repair, same agentic-shift motivation: "bit-identical tokens at shifted positions void prefix caches at first byte of divergence"). Does NOT do the inj/seq cost-map or the 'invalidation law' framing. Single independent source (arXiv only) => flag, not yet an admissible kill. |
| 2 | Cache-Craft: Managing Chunk-Caches for Efficient RAG | arXiv:2502.15734 https://arxiv.org/abs/2502.15734 | reuse precomputed chunk-KVs at arbitrary positions; identify reusable chunk-caches + perform a SMALL fraction of recomputation to FIX the cache to keep quality; -51% redundant compute vs prefix-caching | HIGH: "small-fraction recompute to fix a reused cache" is conceptually the repair CLAIM-0006 measures; but it's RAG chunk-reuse (not mid-prompt tool-injection on the live prefix) and not CDC/rolling-hash. Independent of Irminsul (2nd source that the "fix-with-partial-recompute" family exists). |
| 3 | EPIC: Efficient Position-Independent Context Caching | arXiv:2410.15332 (ICML'25) https://arxiv.org/abs/2410.15332 | formalizes Position-Independent Caching (PIC); LegoLink fixes attention-sink at chunk start; up to 8x TTFT | MEDIUM: PIC = reuse KV regardless of prefix position. CLAIM-0006's CDC is a PIC-family idea. EPIC is the canonical PIC reference; cite as the prior-art umbrella the CDC repair sits inside. |
| 4 | MEPIC: Memory-Efficient PIC | arXiv:2512.16822 https://arxiv.org/abs/2512.16822 | memory-efficient PIC: page-aligned chunk KV, block-level recompute (only first block request-specific), RoPE fusion | MEDIUM: same PIC family; block-level partial recompute echoes the repair. |
| 5 | CacheBlend (EuroSys'25 Best Paper) | arXiv:2405.16444 https://arxiv.org/abs/2405.16444 | reuse precomputed KV regardless of prefix/non-prefix; selectively recompute a small subset of tokens to partially update each reused cache | MEDIUM: the original "selective partial recompute of non-prefix KV" paper; CLAIM-0006's repair is the same genus (partial recompute), different trigger (insertion vs concatenation) and different boundary policy (CDC). |
| 6 | CacheClip | arXiv:2510.10129 https://arxiv.org/abs/2510.10129 | KV reuse for RAG; addresses prefix-only limitation w/ effective reuse | MEDIUM (same family as CacheBlend). |
| 7 | Don't Break the Cache: Eval of Prompt Caching for Long-Horizon Agentic Tasks | arXiv:2601.06007 (PwC) https://arxiv.org/abs/2601.06007 | black-box eval across OpenAI/Anthropic/Google; cost -41..80%, TTFT -13..31%; "place dynamic content at end avoids breaking cache"; ablation vs prompt size (500-50k) & tool-call count (3-50) -> "universal linear" cost/TTFT | MEDIUM on the COST axis: closest empirical neighbor to the cost-map idea, BUT black-box (no engine recompute fraction), no f(inj/seq) law, no repair mechanism, no head-to-head vs APC/Radix/FlashInfer. Good to CITE as motivation + to distinguish (they observe "linear in size"; CLAIM-0006 derives recompute ~ inj/seq with the position-NOT-driver result). |
| 8 | Towards a Collaborative Memory for Agentic Workflow: Breaking the Prefix Barrier w/ Segment-Level KV Cache Sharing | ICLR'26 submission (OpenReview) | segment-level KV sharing across agents | LOW-MED: PIC-family, multi-agent sharing, not mid-prompt insertion-repair. |
| 9 | KVFlow | arXiv:2507.07400 | workflow-aware KV eviction (steps-to-execution), prefetch | LOW: eviction policy, orthogonal to invalidation-repair. |
| 10 | Continuum | arXiv:2511.02230 | KV time-to-live retention for multi-turn agents | LOW (already in related_work; orthogonal retention). |
| 11 | CDC storage-dedup ancestry | FastCDC; Rabin; US11928092B2 "Word-aware CDC"; ETH "Breaking & Fixing CDC" | content-defined chunking is insertion-resilient: an edit creates new chunks but surrounding chunk boundaries are preserved | FOUNDATIONAL: this is WHY CDC localizes an insertion. Means the CORE PROPERTY CLAIM-0006 relies on is textbook prior art; novelty cannot rest on "CDC is insertion-resilient." |

## Novelty verdict (mine; the COMMITTEE decides, I only make their job hallucination-proof)
- MECHANISM (CDC repair over radix/prefix cache): **NOT novel.** Collides with Irminsul (mechanism-
  identical) + sits inside the PIC / partial-recompute family (EPIC, MEPIC, CacheBlend, Cache-Craft).
  Anti-hallucination caveat: Irminsul is presently a SINGLE independent index, so this is a loud
  WEAKEN/flag rather than a formal >=2-source KILL. Either way: do NOT pitch the CDC repair as the
  novel contribution.
- FRAMING (Invalidation LAW + conditional inj/seq cost-map + head-to-head recompute-fraction vs the 3
  mandatory baselines): **novel** — no collision found in this search. This is the defensible core.
- DEAD-checks: not re-proposing DEAD-0005 (de-chaining, measured 1.0x), DEAD-0006 (token-prefix=>KV
  sharing already captured by Radix — Lane A's EXP-0003 showed Radix stays 10-90%, so CLAIM-0006 does
  NOT collapse into it), or DEAD-0008 (interior repair not bit-safe — CLAIM-0006 is recompute-COUNT,
  not bit-exact interior patch). Clear of the cemetery.

## Recommended reframe for committee (so it survives the Irminsul collision)
Pitch CLAIM-0006 as a CHARACTERIZATION/LAW paper, not a mechanism paper:
"the conditional inj/seq recompute cost-map for agentic prefix-cache invalidation, with CDC repair as a
KNOWN (Irminsul/PIC-family) realization whose win-region this work maps and bounds." The novel deliverable
is the cost-map + the position-is-not-the-driver result + the where-it-wins curve vs APC/Radix/FlashInfer,
NOT the CDC mechanism. Must CITE Irminsul, Cache-Craft, EPIC/MEPIC, CacheBlend prominently as the
mechanism prior art.
