# PROJ-0005 Prior Art — Validated by researcher-0014-L0-r4
# CLAIM-0014: Tool-Result Re-Tokenization Boundary Churn Defeats Exact-Prefix KV-Cache Reuse

## 1. Token Healing / Boundary Healing (FOUNDATIONAL — the phenomenon is KNOWN)

### 1a. Lundberg & Ribeiro — "The Art of Prompt Design: Prompt Boundaries and Token Healing" (2023)
- **Source:** https://medium.com/data-science/the-art-of-prompt-design-prompt-boundaries-and-token-healing-3b2448b0be38
- **Verified:** YES (web-fetched 2026-06-01)
- **Key finding:** BPE tokenization is greedy and NON-ASSOCIATIVE: tokenize(A||B) ≠ tokenize(A) || tokenize(B)
  when the boundary straddles a merge-pair. ~70% of the 10k most common tokens in StableLM are prefixes
  of longer tokens, meaning prompt boundaries routinely cause token-ID divergence. Token healing = back up
  one token before the prompt boundary, then constrain the first generated token to match the backed-up prefix.
- **Author:** Scott Lundberg, Senior Researcher at Microsoft Research.
- **Relevance to CLAIM-0014:** This establishes the MECHANISM — BPE non-associativity at seams — as KNOWN
  FOLKLORE. CLAIM-0014's novelty is NOT the mechanism itself, but the CHARACTERIZATION contribution:
  delimiter-conditioned churn rate + model-free predictor + silent APC/RadixAttention block-hash miss on
  real agent traces, measured at block granularity.

### 1b. Microsoft Guidance Library — Token Healing Feature
- **Source:** https://github.com/guidance-ai/guidance
- **Verified:** YES (web-fetched 2026-06-01; token healing is a built-in feature, documented in blog/README history)
- **Key detail:** Guidance implements token healing as default behavior for Transformer models — automatically
  backs up generation by one token at prompt/completion boundaries to fix BPE boundary bias.
- **Relevance:** Production-deployed mitigation exists for the generation direction; CLAIM-0014 addresses the
  CACHE-INVALIDATION direction (not generation quality), which token healing does NOT fix (it heals the
  generated continuation, not the cached KV prefix hash).

## 2. "Don't Break the Cache" — arXiv:2601.06007 (CLOSEST AGENTIC CACHE-COST NEIGHBOR)

- **Source:** https://arxiv.org/abs/2601.06007
- **Verified:** YES (web-fetched 2026-06-01; title, authors, abstract confirmed)
- **Full title:** "Don't Break the Cache: An Evaluation of Prompt Caching for Long-Horizon Agentic Tasks"
- **Authors:** Lumer, Nizar, Jangiti, Frank, Gulati, Phadate, Subbiah
- **Key findings:** Prompt caching reduces API costs 41-80% and TTFT 13-31% across OpenAI/Anthropic/Google
  for multi-turn agentic tool-calling workloads. Dynamic tool results and traditional function calling can
  break cache prefixes. Optimal strategy: place cacheable content at prompt start, dynamic content at end.
  Ablation over prompt sizes 500-50k tokens, tool counts 3-50.
- **CRITICAL DISTINCTION from CLAIM-0014:**
  - 2601.06007 = BLACK-BOX provider-API evaluation ($/TTFT as observables; treats caching as opaque)
  - CLAIM-0014 = WHITE-BOX tokenizer mechanism (BPE boundary churn as the CAUSE of cache miss) +
    model-free delimiter-class predictor + block-granularity measurement against vLLM APC hash schedule
  - 2601.06007 does NOT discuss tokenization boundaries, BPE seam effects, or re-tokenization.
    The cache-breaking they observe is prompt-STRUCTURE level (content placement), not TOKEN-ENCODING level.
  - CLAIM-0014 identifies a specific mechanism that 2601.06007's methodology cannot observe (black-box API).

## 3. vLLM Automatic Prefix Caching (APC) — Block-Hash Design
- **Source:** https://docs.vllm.ai/en/latest/design/prefix_caching/
- **Verified:** YES (web-fetched 2026-06-01)
- **Key details:** SHA-256 hash of (parent_hash, block_tokens_tuple, extra_hashes). Block size configurable
  (default varies; examples use 4 and 16). Only FULL blocks cached. Contiguous full-block prefix matches only.
  LRU eviction, reverse-order freeing.
- **Relevance:** This is the PRODUCTION cache mechanism CLAIM-0014 targets. A single token-ID divergence
  at any position within a block invalidates that block's hash AND all downstream blocks (parent-hash chain).
  The block-hash design means even 1 token shift at position k invalidates ceil((total-k)/block_size) blocks.
- **No mention of re-tokenization boundary issues** — the design ASSUMES token IDs are stable across turns.

## 4. SGLang RadixAttention — Token-Level Prefix Tree
- **Source:** https://www.lmsys.org/blog/2024-01-17-sglang/
- **Verified:** YES (web-fetched 2026-06-01)
- **Key details:** Radix tree keyed by token-ID sequences, page size = 1 token. Automatic prefix matching,
  LRU eviction. Dynamic node splitting for shared prefixes.
- **Relevance:** Same vulnerability as vLLM APC — token-ID divergence at position k invalidates the entire
  suffix. RadixAttention's token-level granularity means even a single divergent token ID breaks the match.
- **No mention of re-tokenization effects** — assumes token IDs are stable.

## 5. BPE Non-Associativity — General Knowledge
- **Source (secondary):** https://sebastianraschka.com/blog/2025/bpe-from-scratch.html
- **Verified:** YES (web search 2026-06-01)
- **Key point:** BPE merge operations are greedy left-to-right; tokenizing a string incrementally (prefix
  then suffix) does not in general produce the same token sequence as tokenizing the full string at once.
  This is a structural property of the algorithm, not a bug.

## SYNTHESIS FOR CLAIM-0014

The phenomenon (BPE non-associativity at string boundaries) is KNOWN FOLKLORE, documented by Lundberg (2023)
and implemented as "token healing" in Microsoft Guidance. However:

1. **No prior work measures the CACHE-INVALIDATION consequence** — token healing fixes generation quality,
   not KV-cache hash integrity. The cache-hit→miss demotion from re-tokenization is UNMEASURED.
2. **"Don't Break the Cache" (2601.06007)** is the closest neighbor but operates at BLACK-BOX API level;
   it cannot observe the tokenizer-level mechanism. It measures $/TTFT, not block-level hash invalidation.
3. **Neither vLLM APC nor SGLang RadixAttention documentation acknowledges** re-tokenization as a cache
   invalidation source — both implicitly assume token-ID stability across turns.
4. **CLAIM-0014's contribution** = CHARACTERIZATION: delimiter-conditioned churn rate + model-free predictor
   + silent block-hash miss quantification on real agent traces. This is genuinely unmeasured in prior work.
   Frame as characterization, NOT mechanism discovery.

🚩 UNRESOLVED: No arXiv paper found specifically studying "BPE boundary effects on KV-cache hit rates."
The gap between token-healing (generation quality) and cache-invalidation (serving efficiency) appears
genuinely unstudied as of 2026-06-01.

---
*Prior art search: researcher-0014-L0-r4, 2026-06-01, prompt_version v001*
