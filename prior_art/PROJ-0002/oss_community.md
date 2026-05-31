# OSS / Community — PROJ-0002
| Project | Relevance |
|---|---|
| vLLM / SGLang | the two engines whose prefix-cache invalidation we model + repair (CDC) |
| FlashInfer | kernel layer; no cache policy (== host engine for our purposes) |
Watch: any vLLM/SGLang chunked-prefill or hash-chain change that alters mid-prompt invalidation cost.

## Fresh re-search 2026-05-31 (researcher-cdc-priorart-A)
| Project / artifact | Relevance |
|---|---|
| **Irminsul** (arXiv:2605.05696) | Implements CDC-over-SGLang-radix content-addressed caching — the OSS/impl prior art that collides with CLAIM-0006's CDC repair mechanism. WATCH for a public repo + a 2nd index (Sem.Scholar/DBLP); a 2nd independent source upgrades the mechanism flag to an admissible >=2-source KILL. |
| LMCache (CacheBlend "blending") | docs.lmcache.ai/kv_cache_optimizations/blending.html — "KV cache reuse for non-prefix positions by recomputing a subset of tokens" = shipped selective-recompute repair, OSS form of the partial-repair family. |
| SGLang radix cache | Irminsul extends it; recheck each release for any content-hash/CDC keying landing upstream (would make the mechanism table-stakes). |
| FastCDC / content-defined-chunking GitHub topic | the CDC algorithm prior art (storage dedup) CLAIM-0006's chunker descends from. |
Mechanism is NOT the novel part — track these so the committee pitch stays on the cost-map/law, not the CDC repair.
