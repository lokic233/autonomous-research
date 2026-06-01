# RE-B7 — Vendor prompt-caching guidance as QUANTIFIED prior art (PROJ-0007 / EXP-0053)

The mechanism PROJ-0007 quantifies (volatile / dynamically-ordered fields placed EARLY in the shared head
break cross-session prefix reuse) is **already documented vendor guidance**, with quantified invalidation
rules. This is the prior art the thesis quantifies — and it is precisely why the RE-B1 KILLER fires: the
shortfall is a *documented prompt-engineering anti-pattern*, not a novel architectural ceiling.

## Anthropic — Prompt caching (platform.claude.com/docs/en/build-with-claude/prompt-caching)
Verified 2026-06-01.
- Order/placement: "Cache prefixes are created in the following order: `tools`, `system`, then `messages`."
  "Place static content (tool definitions, system instructions, context, examples) at the beginning of your
  prompt." "Place cached content at the prompt's beginning for best performance."
- Varying-suffix rule (THE mechanism B measures): "For a prompt with a static prefix and a varying suffix
  (timestamps, per-request context, the incoming message), [place the breakpoint at] the end of the static
  prefix, not the varying block."
- Cumulative-hash invalidation: "Because the hash is cumulative, covering everything up to and including the
  breakpoint, changing any block at or before the breakpoint produces a different hash on the next request."
  "Changes at each level invalidate that level and all subsequent levels." "Modifying tool definitions
  (names, descriptions, parameters) invalidates the entire cache."
- Exact-match: "Cache hits require 100% identical prompt segments ... up to and including the block marked
  with cache control."
- The "common mistake" = EXACTLY the PROJ-0007 failure mode, documented: a per-request block with a
  timestamp + user message after a large static context → "The timestamp differs, so the prefix hash ...
  differs ... No cache hit. You pay for a fresh cache write on every request and never get a read."
- Quantified params: lookback window = 20 blocks; up to 4 breakpoints; min cacheable 1,024–4,096 tokens
  (model-dependent); TTL 5 min default (refreshed on use) / 1 h optional; cache-read tokens = 0.1× base.

## OpenAI — Prompt caching (developers.openai.com/api/docs/guides/prompt-caching)
Verified 2026-06-01.
- "Cache hits are only possible for exact prefix matches within a prompt."
- "Structure prompts with static or repeated content at the beginning and dynamic, user-specific content at
  the end."
- Threshold: "Caching is enabled automatically for prompts that are 1024 tokens or longer." Below that,
  "`cached_tokens` will be zero."
- Lifetime: in-memory "5 to 10 minutes of inactivity, up to a maximum of one hour"; extended up to 24 h.
- Quantified payoff: "Prompt Caching can reduce latency by up to 80% and input token costs by up to 90%."

## Implication for PROJ-0007
Both vendors (a) document prefix/cumulative-hash invalidation, (b) explicitly instruct putting volatile
fields (timestamps/per-request context) AFTER the static prefix, and (c) name the exact timestamp-in-head
failure mode. PROJ-0007's measured shortfall is the *realized cost* of NOT following this guidance — a
prompt-engineering PSA, confirming the RE-B1 honest-kill reading rather than a new architectural ceiling.
