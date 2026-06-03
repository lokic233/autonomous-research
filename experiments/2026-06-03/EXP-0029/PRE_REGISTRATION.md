# PRE_REGISTRATION — EXP-0029 (CLAIM-0028) — L0 CPU-only, stdlib, SERIAL

**Committed BEFORE running any measurement.** Honest pipeline; negatives are WINS.

## Claim under test (CLAIM-0028)
For agent tool-result re-ingestion, a template-structured KV reuse scheme that caches KV for the
FIXED-SCHEMA token positions of a tool's result envelope (recomputing only the variable value spans)
reclaims STRICTLY MORE reusable KV/prefill than exact-prefix caching (vLLM APC / RadixAttention) on
realistic agent traffic where the SAME tool returns the SAME schema with DIFFERENT values — because
exact-prefix breaks at the first differing value token while schema positions are bytewise-identical
AND (load-bearing) the fixed-schema KV is position-stable enough to reuse OR cheaply re-anchored — a
STRUCTURAL reuse a tuned exact-prefix policy cannot capture by construction.

## Two designed-around traps (must respect)
1. **Jensen-floor / tuning trap** (killed EXP-0006/0011/0027): this is NOT a continuous knob. Exact-prefix
   CANNOT capture schema-after-first-differing-value reuse BY CONSTRUCTION — it halts at first mismatch.
   We test a structural/discrete distinction, not a tuned-baseline-absorbs gain.
2. **RoPE position-dependence** (killed EXP-0007/EXP-0009 CDC dedup, position-aware = 0.35–1.46%): KV is
   position-dependent. Schema tokens AFTER a variable-length value span land at SHIFTED absolute
   positions across requests; their KV is NOT bytewise reusable without re-anchoring. THIS is the crux.

## Two falsifiable parts
- **(A)** Is there material schema-identical / value-differing structure in real tool-result traffic
  that exact-prefix caching misses (breaks at first differing value)?
- **(B)** Is the fixed-schema KV actually reusable given RoPE position-dependence — are schema tokens at
  STABLE absolute positions, or only cheaply re-anchorable?

## Tool-result-schema model
A tool result is a fixed structured envelope (JSON-ish) with fixed schema spans (keys, delimiters,
boilerplate, e.g. `{"status":"`, `","rows":[`, `],"id":"`, `"}`) interleaved with VARIABLE value spans
(the status string, the row payload, the id) whose token LENGTH varies across calls. Same tool => same
schema token sequence; different calls => different value tokens AND different value lengths (so schema
tokens after a value are position-shifted). We model N tools, each with a schema template; a trace is a
sequence of tool calls; each call instantiates its tool's schema with fresh random-length values.

## Tokenizer
NO transformers available on this Mac (python3.9, no `transformers`). We use a DETERMINISTIC whitespace/
punctuation word-tokenizer (stated explicitly): split on JSON structural chars and whitespace, each
structural delimiter and each word/number = 1 token. Value spans get a sampled token length per call.
This is an L0 modeling tokenizer; a real-tokenizer + real-KV check is the L1 follow-up.

## Block model
Block size = 16 tokens (vLLM default page). Reuse measured at TOKEN level and re-quantized to blocks.
A block is exact-prefix-reusable iff every token in it (and all preceding) matches a cached request.

## THREE-way measure (report ALL THREE; gap (b)->(c) is the RoPE tax = decides the claim)
For each new call vs a cached prior call of the SAME tool:
- **(a) exact-prefix / APC reuse** = tokens shared from position 0 until the FIRST differing token.
  (Breaks at first value span if any value differs — the realistic case.)
- **(b) template TOKEN-LEVEL reuse (optimistic ceiling)** = ALL fixed-schema token positions, regardless
  of interleaved value differences. This is the "if KV were position-independent" upper bound.
- **(c) POSITION-AWARE template reuse (honest)** = fixed-schema tokens whose ABSOLUTE position is
  IDENTICAL across the two requests. Schema tokens after a variable-length value land at shifted
  positions => NOT in (c). This is the raw-KV-reusable number under RoPE.

Headline metrics:
- **(A) schema-misses-by-exact-prefix fraction** = (template token-level reuse) − (exact-prefix reuse),
  as a fraction of total tokens. The structure APC misses.
- **(B) position-aware reusable fraction vs token-level ceiling** = (c)/(b) and (c) as frac of total.
  The RoPE tax = (b) − (c). THE make-or-break.

## Re-anchor analysis
If we posit a RoPE re-anchor transform R(Δ) to make position-shifted schema KV reusable: per
VERDICT-0008 / EXP-0009, that IS CacheBlend's selective-recompute / re-position mechanism. So either
(c) position-stable reuse (NO re-anchor) is the real novel structural win, OR re-anchoring collapses to
published CacheBlend. We report (c) as the no-re-anchor number and state this explicitly.

## Conditions / sweep
- N tools in {4, 8, 16}; value-length distributions: FIXED-len values (control: schema stays aligned)
  vs VARIABLE-len values (realistic: schema shifts). Block size 16.
- >=5 seeds (use 8). Serial. <=15 min wall. Trust on-disk CSV not stdout.

## HONEST-NEGATIVE branch (fires => report NEGATIVE = WIN)
Report NEGATIVE if ANY of:
1. exact-prefix already captures the reuse (schema is a shared PREFIX before any value), OR
2. schema tokens after the first value span are position-shifted so their KV is NOT reusable without
   re-anchoring (the EXP-0009 RoPE kill) — i.e. (c) collapses far below (b), OR
3. reusable-beyond-prefix position-aware fraction is small (<~a few %) on realistic (variable-len) schemas, OR
4. a re-anchor transform is as expensive as recompute / collapses to CacheBlend.

## Decision rule
- **HELD**: position-aware template-beyond-exact-prefix reuse > ~10% of tokens robustly on the realistic
  (variable-len) regime, WITHOUT re-anchoring => structural win over APC.
- **PARTIAL**: token-level ceiling is large but position-aware is modest yet non-trivial (>~few %).
- **NEGATIVE**: position-aware collapses to ~prefix-only / a few % (the EXP-0009 outcome). WIN.

Predicted (pre-committed hypothesis): mirror of EXP-0009 — token-level ceiling large, position-aware
collapses because the FIRST variable value shifts ALL subsequent schema tokens. NEGATIVE likely.
