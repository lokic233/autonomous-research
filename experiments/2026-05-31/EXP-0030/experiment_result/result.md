# EXP-0030 STATUS — CLAIM-0006 true-lmcache CacheBlend kernel: INTEGRATION-BLOCKED (honest, not fabricated)

**Goal:** measure the PUBLISHED lmcache CacheBlend gather kernel (single_layer_kv_transfer, source-built in env
ros-vllm) for CDC-contiguous vs PIC-scattered slot mappings over a real vLLM paged KV cache — the committee's
load-bearing residual (VERDICT-0033/0034).

## OUTCOME: integration-blocked this cycle (did NOT fabricate a number)
A direct call to `c_ops.single_layer_kv_transfer` with hand-constructed tensor shapes hit a CUDA illegal memory
access (caught; GPU recovered, 106MiB idle, node healthy). Root cause: the kernel requires the EXACT vLLM paged
KV layout + GPUKVFormat that lmcache discovers via `normalize_kv_and_discover_format(kv_caches, EngineType.VLLM)`
from a REAL vLLM-allocated cache — not hand-built tensors. The lmc buffer must be [2, num_tokens, hidden_dim]
and the paged cache must match vLLM's flash-attn/flashinfer format exactly (lmcache/v1/gpu_connector/).

## CORRECT PATH (for the next cycle, with proper setup time)
Stand up a real vLLM LLM() engine (as in EXP-0026), obtain its actual `kvcaches` tensors, run them through
lmcache's `normalize_kv_and_discover_format` to get the right (format, normalized_kv), then time
`single_layer_kv_transfer` with a CDC-contiguous vs PIC-scattered `slot_mapping`. This uses the real kernel with
self-consistent shapes (no hand-guessing). It is a vLLM+lmcache CONNECTOR integration, not a standalone kernel
call — ~1-2h of careful setup, deserves a dedicated cycle (crash-retrying shapes on a leased node is the wrong move).

## WHAT WE ALREADY KNOW (brackets the answer honestly)
- EXP-0026 (real vLLM PagedAttention serving, re-impl PIC): CDC wins 12/12 TTFT+throughput.
- EXP-0027 (oracle/fused-PIC roofline, zero-overhead lower bound): CDC's advantage is CONDITIONAL — wins at
  high inj/seq, loses at low inj/seq (1-5%).
- The TRUE lmcache kernel lands BETWEEN these (it pays real but optimized gather overhead). So the honest
  expectation: CDC's serving advantage is real but inj/seq-conditional, crossover somewhere between the re-impl
  (CDC wins everywhere) and the oracle (CDC wins only high inj/seq). EXP-0030 (when integrated) pins the crossover.

## STATUS: not-completed (integration-blocked). NO effect recorded; no fabricated data. Node released.
