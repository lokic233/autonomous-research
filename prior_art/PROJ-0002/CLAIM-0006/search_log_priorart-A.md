# Search Log — CLAIM-0006 fresh prior-art/novelty re-search
agent: researcher-cdc-priorart-A | claim: CLAIM-0006 | date: 2026-05-31 | prompt_version: v001
schema: {timestamp, agent_id, claim_id, queries, sources_searched, results_found, results_discarded, open_questions}

- ts: 2026-05-31T13:1x
  queries:
    - "content-defined chunking KV cache prefix reuse LLM inference insertion"
    - "CacheBlend KV cache reuse non-prefix LLM RAG 2024"
    - "EPIC position-independent prefix caching LLM serving"
    - "prompt cache modular attention reuse precomputed KV segments"
  sources_searched: [web_search -> arXiv, OpenReview, LMCache docs, vLLM docs, ICML]
  results_found:
    - "Irminsul arXiv:2605.05696 (CDC over SGLang radix, agentic PIC) -- TOP collision"
    - "EPIC arXiv:2410.15332 (PIC, LegoLink)"
    - "MEPIC arXiv:2512.16822 (memory-efficient PIC)"
    - "CacheBlend arXiv:2405.16444 (selective non-prefix recompute, EuroSys'25 best paper)"
    - "CacheClip arXiv:2510.10129"
    - "Prompt Cache arXiv:2311.04934 (modular attention reuse, PML)"
    - "ChunkAttention / ChunkKV / KVShare (compression/share families, lower relevance)"
  results_discarded: [KV-compression-only works (ChunkKV, PyramidInfer, KVzip) -- orthogonal to invalidation-repair]
  open_questions: ["Does Irminsul present an inj/seq cost-map? (-> checked: NO)"]

- ts: 2026-05-31T13:2x
  queries:
    - "Irminsul verify arXiv id 2605.05696 (arXiv abs page + arXiv API id_list)"
    - "Semantic Scholar arXiv:2605.05696 cross-check (>=2-source rule)"
  sources_searched: [curl arxiv.org/abs, export.arxiv.org/api, api.semanticscholar.org]
  results_found:
    - "Irminsul REAL: submitted 2026-05-07, authors Bole Ma / Jan Eitzinger / Harald Koestler"
    - "Irminsul body: uses Gear-hash rolling-hash CDC (chunk ~2^k tokens clamped [32,512], k=7); xxHash64 fingerprint; metric=token-recovery% + prefill-energy; NO 'injection'/'recompute fraction'/'cost map'/'2%'/'invalidation law' tokens"
    - "Semantic Scholar: NOT yet indexed (too new) -> mechanism collision is presently SINGLE independent source"
  results_discarded: []
  open_questions: ["When a 2nd index (Sem.Scholar/DBLP/venue) picks up Irminsul, re-verify -> then a formal >=2-source novelty KILL on the mechanism becomes admissible."]

- ts: 2026-05-31T13:3x
  queries:
    - "prefix cache recompute cost as function of edit position insertion size LLM serving model"
    - "content-defined chunking rolling hash KV cache prefix repair LLM agentic tool injection"
    - "agentic LLM serving prefix cache invalidation tool call mid-prompt TTFT cascade benchmark"
    - "SGLang radix cache content hash chunk insertion resilient 2026"
    - "Dont Break the Cache 2601.06007 full read (cost axis)"
    - "EDMM prefix cache cascade tool injection TTFT 8x agentic edit KV reuse"
    - "recompute fraction tracks injection length / sequence length prefix cache scaling law"
    - "Irminsul content-addressed CDC SGLang radix MLA Bole Ma (2nd retrieval path)"
    - "prefix cache invalidation law two percent injection/sequence ratio conditional cost map"
    - '"content-defined chunking" KV cache LLM 2026 shift tolerant insertion resilient prefix'
  sources_searched: [web_search -> arXiv, OpenReview ICLR'26, Google Patents, ETH research-collection, GitHub topics]
  results_found:
    - "Cache-Craft arXiv:2502.15734 (chunk-cache + small-fraction recompute to FIX cache)"
    - "Don't Break the Cache arXiv:2601.06007 (PwC, black-box provider-API agentic prompt-cache eval; cost/TTFT vs size & tool-count; 'linear')"
    - "ICLR'26 'Breaking the Prefix Barrier w/ Segment-Level KV Cache Sharing' (OpenReview)"
    - "KVFlow arXiv:2507.07400 (workflow-aware eviction)"
    - "CDC storage-dedup ancestry: FastCDC, Rabin, US11928092B2 word-aware CDC, ETH 'Breaking & Fixing CDC' -> CDC insertion-resilience is textbook prior art"
  results_discarded:
    - "Neural scaling-law papers (2602.07488 etc.) -- 'scaling law' is unrelated (model loss, not recompute)"
    - "Generic cache-invalidation patents (web caches) -- unrelated domain"
    - "TokenDance/QKVShare/Joint-Encoding -- multi-agent sharing/quant, not insertion-repair or cost-map"
  open_questions:
    - "No prior work derives recompute ~ f(inj/seq) for autoregressive prefix cache -> conditional cost-map FRAMING appears NOVEL."
    - "Mechanism (CDC-over-radix) already exists (Irminsul) -> pitch the LAW/cost-map, not the mechanism."

## Source independence accounting (for the anti-hallucination >=2-source rule)
- "partial/selective recompute to FIX a reused KV cache exists" : >=2 independent sources
  (CacheBlend 2405.16444 ; Cache-Craft 2502.15734 ; EPIC 2410.15332 ; MEPIC 2512.16822) -> SOLID.
- "CDC content-defined chunking is insertion-resilient (localizes edits)" : >=2 independent
  (FastCDC/Rabin literature ; US11928092B2 ; ETH 'Breaking & Fixing CDC') -> SOLID (but it's storage, not LLM).
- "CDC-over-SGLang-radix as the SPECIFIC LLM prefix-cache repair mechanism" : 1 source (Irminsul, arXiv only)
  -> NOT yet >=2 ; mechanism collision is a strong FLAG/WEAKEN, NOT an admissible KILL until 2nd index appears.
