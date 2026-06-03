# RESULTS — EXP-0029 (CLAIM-0028) — L0 CPU-only, stdlib, SERIAL

**Claim:** a template-structured KV reuse scheme caching KV for the FIXED-SCHEMA token positions of a
tool-result envelope (recomputing only variable value spans) reclaims STRICTLY MORE reusable KV/prefill
than exact-prefix caching (vLLM APC / RadixAttention) on agent traffic where the SAME tool returns the
SAME schema with DIFFERENT values — *AND* the fixed-schema KV is position-stable enough to reuse without
re-anchoring.

## VERDICT: **NEGATIVE** (honest negative = WIN). Mirrors EXP-0009's RoPE kill.
Part (A) HOLDS: there IS large schema structure exact-prefix misses. Part (B) FAILS: RoPE
position-dependence makes that structure NOT reusable once a variable-length value shifts it.
Numbers read from on-disk CSVs (`results/template_kv_reuse_agg.csv`, `results/diag_where.csv`), not stdout.

## Setup
- Tokenizer: DETERMINISTIC word/punct tokenizer. **No `transformers` on this Mac (python3.9)** — stated
  per pre-registration; real-tokenizer + real-KV check is the L1 follow-up.
- Tool-result envelope model: fixed JSON-ish schema spans (`{`, `"key":`, `,`, `[`, `]`, `}`) interleaved
  with VARIABLE value spans (status/id literals 1–3 tok, scalars 1–2 tok, array payloads 3–30 tok).
  Same tool => same schema sequence; each call => fresh values + (var mode) fresh value LENGTHS.
- Block size 16. 8 seeds. N tools ∈ {4,8,16}; complexity (fields) ∈ {3,6}. Cache = first call of each tool.
- Two regimes: **var** (realistic — values vary in length, schema SHIFTS) and **fixed** (control — value
  lengths constant, schema stays aligned).

## Three-way reuse (fraction of total tokens, mean over 8 seeds)
- (a) exact-prefix/APC: tokens shared pos0 .. first differing token.
- (b) template TOKEN-level ceiling: all schema tokens (position-independent upper bound).
- (c) POSITION-AWARE (honest): schema tokens at IDENTICAL absolute position across the two requests.

### Realistic regime (var — the claim's actual case)
| N | cx | (a) prefix | (b) token-ceiling | (c) **position-aware** | schema missed by APC (b−a) | **RoPE tax (b−c)** | **posaware beyond prefix (c−a)** | c/b |
|---|----|-----------|------------------|------------------------|----------------------------|--------------------|----------------------------------|-----|
| 4 | 3  | 0.116 | 0.415 | **0.171** | 0.299 | **0.244** | **0.055** | 0.41 |
| 4 | 6  | 0.060 | 0.421 | **0.111** | 0.361 | **0.310** | **0.051** | 0.26 |
| 8 | 3  | 0.126 | 0.445 | **0.189** | 0.319 | **0.256** | **0.063** | 0.42 |
| 8 | 6  | 0.063 | 0.439 | **0.123** | 0.376 | **0.316** | **0.060** | 0.28 |
| 16| 3  | 0.121 | 0.429 | **0.179** | 0.308 | **0.250** | **0.058** | 0.42 |
| 16| 6  | 0.063 | 0.436 | **0.117** | 0.373 | **0.320** | **0.053** | 0.27 |

### Control regime (fixed — schemas aligned, no length shift)
| N | cx | (a) prefix | (b) ceiling | (c) posaware | RoPE tax | c/b |
|---|----|-----------|-------------|--------------|----------|-----|
| 8 | 3  | 0.218 | 0.778 | 0.778 | **0.000** | 1.0 |
| 8 | 6  | 0.113 | 0.780 | 0.780 | **0.000** | 1.0 |
(all fixed cells: RoPE tax = 0, c/b = 1.0)

## Interpretation — the make-or-break (RoPE position tax)
1. **Part (A) is real and large.** Exact-prefix/APC misses huge schema structure: token-level the schema
   is 42–44% of tokens but APC captures only 6–13% (it breaks at the FIRST differing value token).
   schema-missed-by-APC = **30–38%** of tokens. So the *opportunity* the claim points at exists.
2. **Part (B) fails — RoPE kills it.** The position-aware reusable fraction collapses to **11–19%**, only
   **26–42% of the token-level ceiling** survives. The RoPE tax (b−c) is **0.24–0.32** — the dominant term.
3. **The honest structural win over APC is only ~5–6%** (posaware-beyond-prefix c−a = 0.051–0.063),
   BELOW the pre-registered 10% HELD threshold. Same shape as EXP-0009 (CDC: 0.35–1.46%); here the
   template model is more favorable (5–6%) but still small and still sub-threshold.
4. **WHERE the reuse survives (diag_where.csv, N=8 cx=6):** schema tokens BEFORE the first variable value
   are **100% position-aware reusable (3971/3971)** — but that is EXACTLY the prefix APC already takes.
   Schema tokens AFTER the first variable value: **only 14.9% reusable (3448/23199)**, and **85% of all
   schema tokens live there.** The first variable-length value shifts every downstream schema token to a
   new absolute position => new RoPE rotation => KV not reusable. The residual 14.9% is COINCIDENTAL
   alignment (two calls happening to sample the same value length). This is the EXP-0007/0009 reality.
5. **Control proves the mechanism, not the claim.** In `fixed` mode (no length shift) c/b = 1.0 and APC
   itself jumps to 11–22% — but aligned-length tool results are not the claim's realistic premise; the
   claim is explicitly about DIFFERENT values, which in practice means different LENGTHS, which shift.

## Re-anchor analysis
To recover the 0.24–0.32 RoPE tax you must apply a position re-anchor R(Δ) to shifted schema KV. Per
VERDICT-0008 / EXP-0009 that IS CacheBlend's selective-recompute/re-position mechanism — published. So:
- WITHOUT re-anchor, position-aware structural win over APC = ~5–6% (sub-threshold) — the honest number.
- WITH re-anchor, the scheme COLLAPSES TO CacheBlend (not novel).
Either way the claim's distinctive "schema KV is position-stable enough to reuse WITHOUT re-anchoring"
is FALSE: 85% of schema tokens are post-first-value and shifted.

## Held / partial / negative
- **HELD:** NO — position-aware beyond-prefix (5–6%) is below the ~10% threshold and not position-stable.
- **PARTIAL:** the token-level CEILING is large (42–44%) and APC genuinely misses 30–38% of structure —
  the opportunity is real — but it is NOT realizable as raw-KV reuse under RoPE.
- **NEGATIVE (honest headline):** RoPE position-dependence kills it. The first variable-length value
  shifts all downstream schema tokens; only the pre-value prefix (already APC's) is position-stable.
  This is a WIN: the claim was designed around the RoPE trap and the trap still fires on the realistic
  variable-length regime, exactly as it killed EXP-0009's CDC dedup.

## Prior art caveat
- vLLM APC / RadixAttention: exact-prefix only — confirmed it breaks at first value, captures 6–13%.
- **Prompt Cache (Gim et al.)**: modular, POSITION-INDEPENDENT segment reuse via precomputed position ids —
  this is precisely the mechanism that WOULD realize the 42–44% token-level ceiling, and it ALREADY EXISTS.
  Our template-structured scheme without re-anchoring is a weaker (5–6%) special case; with re-anchoring
  it is Prompt Cache / CacheBlend. No novelty gap.
- CacheBlend: selective recompute / re-anchor = the R(Δ) transform that recovers the tax (published).
- EXP-0009 (this instance): CDC dedup died on RoPE (0.35–1.46% position-aware). EXP-0029 confirms the same
  kill with an explicit tool-result-schema template model (5–6%); the structure is more legible but the
  RoPE tax (0.24–0.32) is the same wall.

## What a real GPU L1 should measure
1. Real-tokenizer envelopes (Llama/Qwen BPE) + REAL KV tensors: bytewise/allclose equality of fixed-schema
   token KV across two same-tool calls at SHIFTED absolute positions — confirm the 14.9% residual is real
   coincidental-length alignment, not tokenizer artifact.
2. Real vLLM APC reuse vs a template-reuse harness (and vs Prompt Cache's position-independent reuse) on a
   real agent trace, measuring prefill FLOPs saved — does template-without-re-anchor beat APC by >5%? Predict no.
3. Cost of R(Δ) re-anchor vs recompute on H100 — confirm it collapses to CacheBlend's published cost model.
