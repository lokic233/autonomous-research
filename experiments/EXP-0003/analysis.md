# EXP-0003 Analysis — Baseline positioning for CLAIM-0006 (Lane A)
agent: researcher-cdc-baselines-A | role: researcher | prompt_version: v001 | date: 2026-05-31
device: CPU-ONLY (token-stream recompute-COUNT model; no GPU, no kernels). budget: <30min, <1GB. 1 node, single run, deterministic seed.

## Question
Under a single MID-PREFIX tool insertion (40 tokens spliced at fractional position f; original suffix
preserved), what fraction of the sequence does each mandatory baseline RECOMPUTE, and where does CDC's
~2% land relative to each? Specifically: does SGLang RadixAttention's token-granularity already make
the recompute cheap (which would collapse CLAIM-0006 into DEAD-0006)?

## Method
Reuse/recompute-count model on token streams. Arms:
- vLLM APC: fixed 16-tok blocks, hash(prefix+block), contiguous longest-prefix match -> recompute all blocks from first diverged block.
- RadixAttention (SGLang): token-granularity (page=1 tok) shared-prefix match -> recompute all tokens after longest common prefix. [DEAD-0006 falsification arm]
- FlashInfer: kernel lib, no cache policy -> recompute fraction == host engine (reported == RadixAttention).
- CDC: content-defined chunking (rolling-hash boundaries), verbatim mechanism from sess 048fcb0d nt2_cdc.py -> downstream chunks re-sync.
Metric reported in TOKENS (common denominator). ctx in {4k,8k,32k}, f in {.1,.25,.5,.75,.9}. data: results.json.

## Measured (recompute % of sequence)
| ctx | f | vLLM APC | RadixAttention | FlashInfer | CDC | CDC vs Radix |
|----:|--:|--------:|--------------:|----------:|----:|----------:|
| 4000 |0.10| 90.08 | 90.10 | 90.10 | 1.36 | 66.2x |
| 4000 |0.25| 75.40 | 75.25 | 75.25 | 2.38 | 31.7x |
| 4000 |0.50| 50.40 | 50.50 | 50.50 | 1.88 | 26.8x |
| 4000 |0.75| 25.79 | 25.74 | 25.74 | 1.93 | 13.3x |
| 4000 |0.90| 10.71 | 10.89 | 10.89 | 1.31 |  8.3x |
| 8000 |0.10| 90.04 | 90.05 | 90.05 | 0.61 |147.8x |
| 8000 |0.25| 75.10 | 75.12 | 75.12 | 0.70 |107.9x |
| 8000 |0.50| 50.20 | 50.25 | 50.25 | 0.76 | 66.2x |
| 8000 |0.75| 25.30 | 25.37 | 25.37 | 0.82 | 30.9x |
| 8000 |0.90| 10.36 | 10.45 | 10.45 | 0.90 | 11.7x |
|32000 |0.10| 90.01 | 90.01 | 90.01 | 0.19 |465.2x |
|32000 |0.25| 75.02 | 75.03 | 75.03 | 0.20 |375.6x |
|32000 |0.50| 50.05 | 50.06 | 50.06 | 0.27 |188.7x |
|32000 |0.75| 25.07 | 25.09 | 25.09 | 0.15 |164.1x |
|32000 |0.90| 10.09 | 10.11 | 10.11 | 0.17 | 58.9x |

## Verdict (honest, one paragraph)
CDC's recompute fraction is position-INDEPENDENT and ≤2.38% across all 15 (ctx,f) cells, while ALL THREE
mandatory baselines are position-DEPENDENT at ≈(1−f) of the sequence (10.1%–90.1%). The decisive
finding for novelty defence: **SGLang RadixAttention's token-granularity does NOT make this cheap** —
under an INSERTION it recomputes 10.1%–90.1%, essentially IDENTICAL to vLLM fixed-block in token terms
(token-granularity removes vLLM's block-ALIGNMENT shift but NOT the suffix-DIVERGENCE: the post-insertion
tokens are a new divergent radix branch). So CLAIM-0006 does NOT collapse into DEAD-0006 (DEAD0006_collapse
= False: radix min 10.1% >> CDC max 2.38%). FlashInfer has no cache policy of its own (kernel lib) so its
recompute fraction == the host engine. CDC's advantage over the BINDING baseline (RadixAttention) ranges
8.3x (worst case: late inject f=0.9, ctx=4k) to 465x (early inject f=0.1, ctx=32k), and GROWS with context
length. EFFECT: keep-exploring (supports CLAIM-0006's baseline positioning; the ~2% is a real, baseline-
beating win that no mandatory baseline matches, but the magnitude is position- and length-dependent — must
be reported as a curve, not a hero number).

## Caveats / honest scope
1. Recompute-COUNT model, NOT wall-clock. Prior NT2_WALLCLOCK (H100) already showed the count reduction
   translates to TTFT (11.6x@8k, 119.6x@32k); a cross-VENDOR wall-clock (e.g. MI350X) head-to-head against
   real vLLM/SGLang engines would be a Level-1/2 GPU experiment -> REQUEST from orchestrator, NOT run here.
2. CDC % here dips below the claimed ~2% (to 0.15–0.9% at large ctx) because random tool tokens rarely
   create boundary collisions; the ~2.0–2.4% headline is the CONSERVATIVE upper measurement. This
   strengthens (does not weaken) the claim, but the ~2% should be quoted as "≤~2.4%, position-independent."
3. Single seed, single-sequence insertion (suffix preserved, i.e. genuine insertion not rewrite). Real
   agentic traces (EDMM) and multi-insertion sequences are future work.
4. vLLM/RadixAttention near-identical token% is expected (both are contiguous-prefix reuse); the model does
   not separately credit vLLM's extra block-alignment loss, so vLLM's REAL penalty is >= shown.
