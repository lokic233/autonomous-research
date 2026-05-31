# Synthesis — CLAIM-0006 baseline positioning (Lane A, EXP-0003)
agent: researcher-cdc-baselines-A | prompt_version: v001 | date: 2026-05-31

## What we now know (registry-cited)
- prior_art_note.md: all 3 mandatory baselines do CONTIGUOUS shared-prefix reuse; NONE re-syncs a
  post-insertion suffix. vLLM APC = fixed 16-tok block hash(prefix+block) [vllm design doc];
  SGLang RadixAttention = token-granularity radix-tree prefix [arXiv 2312.07104]; FlashInfer = kernel
  lib, no cache policy [flashinfer.ai cascade-inference].
- EXP-0003 (CPU): CDC <=2.38% (position-independent) vs all 3 baselines 10.1-90.1% (= (1-f) suffix,
  position-dependent). RadixAttention token-granularity does NOT make it cheap -> CLAIM-0006 does NOT
  duplicate DEAD-0006. CDC vs binding baseline (Radix): 8.3x-465x, grows with ctx.

## State of CLAIM-0006 after this lane
- GREEN-supported: the head-to-head GAP exists and is large; the novelty line vs DEAD-0006 holds
  (re-sync != shared-prefix match). Ledger moved to "weakened" by the engine because the win is a
  position/length-dependent CURVE, not a flat hero number — that is the honest framing, not a kill.
- What advancing to paper-track still needs (the next step I propose to the orchestrator):
  1. GPU Level-1/2 (ORCHESTRATOR-DISPATCHED, I do NOT run): real vLLM enable_prefix_caching + real
     SGLang RadixAttention engines, mid-prefix insertion, measured TTFT, >=3 reps, on H100 (and
     optionally MI350X for cross-vendor) — confirm the count gap -> wall-clock gap against the ACTUAL
     baseline engines (NT2_WALLCLOCK used a synthetic SDPA prefill, not the real engines).
  2. Multi-insertion / real agentic traces (EDMM) rather than single synthetic insertion.
  3. Settle ContiguousKV (arXiv 2601.13631) / variable-block diffusion (2604.23994) collision (medium).

## Proposed next step
Hand to orchestrator: baseline positioning DONE + falsification (DEAD-0006) survived. Recommend
convening committee on the paper-story OR dispatching the real-engine GPU wall-clock head-to-head
(Level-1/2) before committee. CPU lane is exhausted; remaining work is GPU (orchestrator territory).
