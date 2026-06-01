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

---

## ADDENDUM (researcher-0014-L1prep-r5, 2026-06-01, EXP-0051) — CITATIONS MANDATED BY VERDICT-0055

### 6. Gim et al. — "Prompt Cache: Modular Attention Reuse for Low-Latency Inference" (MISSING in EXP-0049; NOW CITED)
- **Source:** arXiv:2311.04934 ; MLSys 2024.
- **Corroborating sources (>=2):**
  - https://arxiv.org/pdf/2311.04934 (arXiv full text)
  - https://proceedings.mlsys.org/paper_files/paper/2024/hash/a66caa1703fe34705a4368c3014c1966-Abstract-Conference.html (MLSys 2024 proceedings)
- **Verified:** YES (external web search 2026-06-01, both URLs returned for the exact title).
- **Key idea:** Prompt Cache precomputes and REUSES attention states of frequently-recurring text SEGMENTS across
  prompts via a "Prompt Markup Language" (PML) schema that declares reusable modules; reuse is by EXPLICIT,
  STRUCTURED module identity, enabling position-independent attention reuse for non-prefix segments.
- **CRITICAL DISTINCTION from CLAIM-0014:**
  - Prompt Cache = MODULAR / SCHEMA-DRIVEN reuse (author declares reusable segments; reuse is by structured module id,
    not raw token-prefix identity). It SOLVES the "reuse non-contiguous structured content" problem ABOVE the
    tokenizer.
  - CLAIM-0014 = WHITE-BOX BPE-seam churn that silently breaks EXACT-PREFIX block-hash reuse (vLLM APC /
    RadixAttention), which operate on raw token-ID prefixes with NO schema. Prompt Cache's mechanism is orthogonal:
    it would AVOID the issue by construction (modules carry their own precomputed states), but it does not
    characterize or measure the token-ID-prefix churn that defeats schema-LESS exact-prefix caches.
  - Prompt Cache does not study tokenization-boundary / re-tokenization effects; it assumes module token boundaries
    are fixed by the schema.

### 7. Sennrich, Haddow, Birch — "Neural Machine Translation of Rare Words with Subword Units" (BPE foundation)
- **Source:** ACL 2016, P16-1162.
- **Corroborating sources (>=2):**
  - https://aclanthology.org/P16-1162/ (ACL Anthology canonical entry)
  - https://aclanthology.org/events/acl-2016/ (ACL 2016 proceedings index)
- **Verified:** YES (external web search 2026-06-01).
- **Key idea:** Introduces byte-pair-encoding (BPE) as a subword segmentation for open-vocabulary NMT: greedy,
  frequency-ranked merge operations applied left-to-right build a deterministic merge table.
- **Relevance to CLAIM-0014 / RE-01:** This is the BPE foundation underlying the EXP-0051 NULL MODEL. The greedy,
  non-associative merge process is WHY tokenize(A||B) != tokenize(A)||tokenize(B) at arbitrary boundaries. The RE-01
  null inserts the tool-result at RANDOM byte offsets to measure the EXPECTED churn from generic BPE non-associativity
  (Sennrich merge mechanics + delimiter byte distribution), against which the real tool-seam churn is compared.
  **EXP-0051 finding:** real tool seams churn LESS (0.0116) than this generic-BPE null (0.0517), i.e. the observed
  effect does NOT exceed the textbook BPE-stability baseline — it is below it.

### PRIOR_ART_ADEQUATE status update
- All three VERDICT-0055 baseline_requirements citations are now present and corroborated (>=2 sources each):
  Gim Prompt Cache (added), Don't-Break-the-Cache 2601.06007 (sec 2, retained), Sennrich BPE (added).
- No 🚩 UNRESOLVED remaining for the mandated citations. (The "no arXiv paper specifically on BPE-boundary KV-cache
  hit rates" gap from EXP-0049 sec 8 persists — that gap is the contribution space; EXP-0051's RE-01 null narrows it.)

*Citations addendum: researcher-0014-L1prep-r5, 2026-06-01, prompt_version v001, EXP-0051.*
