# RE-B8 — Realistic cache-behavior baselines (PROJ-0007 / EXP-0053)

The realized cross-session ceiling is measured against the actual block-level, prefix-chained cache
behaviors of production engines. All characterized from docs/specs at L0; real cross-request APC hit
counters + recovered TTFT require L1 (H100) and are explicitly OUT-OF-SCOPE here (flagged for orchestrator).

## vLLM — Automatic Prefix Caching (docs.vllm.ai/en/latest/design/prefix_caching/), verified 2026-06-01
- Block hash = `hash(parent_hash, tuple(block_tokens), extra)`; "We only cache full blocks." Block sizes
  exemplified at 4 and 16 tokens (EXP-0053 primary block = 16 to match this granularity).
- Prefix-chained invalidation (THE baseline the ceiling is measured against): each block's hash includes the
  PARENT hash, so "any earlier divergence alters all downstream parent hashes, preventing reuse of later
  blocks." Partial-block example: "only the first 2 blocks (8 tokens) hit the cache, because the 3rd block
  only matches 2 of 4 tokens." => a single early differing token (volatile field) strands the entire tail.
  This is exactly the realized-reuse model EXP-0053's block-LCP metric computes.
- `cache_salt`: "injected into the hash of the first block, ensuring that only requests with the same salt
  can reuse cached KV blocks" — i.e. tenant/trust-group isolation; "cache sharing is limited to users or
  requests that explicitly agree on a common salt." Relevant to PROJ-0007: cross-tenant sharing requires an
  agreed salt; a per-session salt would itself be a (deliberate) cross-session prefix break.

## SGLang — RadixAttention / LPM (arxiv 2312.07104, "Efficiently Programming LLMs using SGLang")
- RadixAttention maintains a radix tree of KV-cached token sequences with LRU eviction and cache-aware
  scheduling; longest-prefix-match (LPM) selects the request sharing the longest cached prefix, and a
  routing/cache-aware policy (DFS-order over the radix tree) raises shared-prefix hit rate. This is the
  longest-prefix-match behavior the realized block-LCP approximates; LPM cannot recover content placed AFTER
  the first divergence — consistent with the measured shortfall.

## TensorRT-LLM — block reuse / concurrency (squeezebits vLLM-vs-TRT-LLM #12), verified 2026-06-01
- Proprietary but "likely ... hash tables and LRU-based eviction"; full-block reuse. Quantified throughput
  with shared prefixes: vLLM ~13–32%, TensorRT-LLM up to ~34.7–49% (prefix-ratio sweep 0.1→0.9), with a TRT
  dip near shared-prefix ratio 0.5. Confirms that realized gains scale with the SHARED-PREFIX FRACTION —
  which structural head drift caps below the naive shared-text fraction (the PROJ-0007 quantity).

## Bottom line
All four engines share a full-block, prefix-chained (parent-hash) reuse model in which one early divergent
block forfeits every downstream block. EXP-0053's realized block-LCP faithfully models this; the measured
shortfall is the realized cost of early head drift under exactly these baselines. L1 (real APC hit counters
+ recovered TTFT on H100) remains the only PASS-able open question and is out of L0 scope.
