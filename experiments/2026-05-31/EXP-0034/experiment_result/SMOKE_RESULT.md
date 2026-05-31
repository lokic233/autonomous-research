# EXP-0034 SMOKE RESULT — COMBINED real-lmcache E2E-TTFT harness, 1-cell GPU smoke

**Agent:** researcher-0034-e2e (researcher lane; CPU/minimal-GPU smoke only). **Date:** 2026-05-31.
**Claim:** CLAIM-0006 (Prefix-Cache Invalidation Law + CDC win-region; serving leg). **Gate:** the single
remaining GREEN gate per VERDICT-0041 (theory_skeptic composition-fallacy).
**Scope:** Validate the E2E-TTFT harness for the COMBINED measurement. Did NOT run the 12-cell grid; did NOT
`ros gpu queue`; did NOT lease via the scheduler. Orchestrator owns the full-grid GPU dispatch.

## VERDICT: SMOKE PASS ✅ — harness works, zero faults, finite CDC + PIC E2E-TTFT numbers.
But the PIC arm is a **SCOPED APPROXIMATION (inline real-CacheBlend kernels), NOT a true async
connector-in-serving-loop** — because a true connector-in-loop is **INFEASIBLE in this env** (vLLM 0.6.6
lacks the V1 KVConnector API). See §FEASIBILITY. READY for orchestrator to GPU-queue EXP-0034 **as the scoped
approximation** (or to take the connector-infeasibility finding to committee / fall back to path-b writeup).

## Environment (pinned)
- **Node:** devgpu014, **device:** NVIDIA H100 (97871 MiB). GPU idle before+after (106 MiB, 0% util).
- **Python env:** `/home/dengcchi/.conda/envs/ros-vllm/bin/python` (operator-owned, source-built lmcache at
  `/home/dengcchi/LMCache-src/lmcache`, editable install).
- **Versions:** vLLM **0.6.6.post1**, lmcache **0.1.dev1** (source-built, `c_ops` backend loads),
  torch **2.5.1+cu124**.
- **Model:** Qwen2.5-7B-Instruct fp16, local HF snapshot (offline). gpu_mem_util **0.4**, max_model_len 32768,
  enforce_eager, tensor_parallel=1.
- Same 2 env gotchas as EXP-0030 baked in: (1) strip proxy env vars (`no_proxy` contains `[::1]` → httpx
  URLPattern crash); (2) shim transformers 5.x `all_special_tokens_extended` → `all_special_tokens`.

## FEASIBILITY INVESTIGATION (the load-bearing finding — what the connector path needs and why it's blocked)
I investigated `lmcache.integration.vllm.lmcache_connector_v1.LMCacheConnectorV1` / `vllm_v1_adapter.py` to
drive the REAL CacheBlend through vLLM's KV-transfer connector during a real `generate()`, per the task.

**A TRUE connector-in-serving-loop is INFEASIBLE in this env.** Concretely (probed + confirmed):
- `LMCacheConnectorV1` and `vllm_v1_adapter.py` import
  `from vllm.distributed.kv_transfer.kv_connector.v1.base import ...` and `from vllm.v1.core.sched.output ...`.
  **vLLM 0.6.6.post1 has NO `kv_connector/v1/` directory** (only the V0 connector: `base.py`,
  `simple_connector.py`) and **no `ec_transfer`** module. Importing `lmcache_connector_v1` →
  `ModuleNotFoundError: No module named 'vllm.distributed.kv_transfer.kv_connector.v1'` (verified).
- The blender (`lmcache.v1.compute.blend.blender.LMCBlender`) is only *driven during generate()* by the V1
  adapter's layerwise-retrieve loop (`vllm_v1_adapter.py` L806–833: `self.blender.blend(...)` inside the
  `use_layerwise` retrieve path). That loop is the part that needs the missing vLLM V1 connector + scheduler.
- The full blend forward (`LMCBaseModel.compute_layer` → `LMCFlashAttnBackend.forward_contiguous`) also reads
  newer-vLLM `FlashAttentionImpl` attributes (`vllm_flash_attn_version`, `num_heads_q`, …) not present in
  0.6.6's attention impl — a second incompatibility independent of the connector.
- **Conclusion:** the published async CacheBlend connector-in-serving-loop requires **vLLM ≥0.7/0.8** (V1
  engine + V1 KVConnector). Building/validating that is an env-upgrade task, NOT a one-cycle harness task,
  and is out of scope per the discipline (do not rebuild the operator env).

**What IS importable & runnable standalone (confirmed):** `LMCBlenderBuilder`, `infer_model_from_vllm`, and —
critically — the **real CacheBlend BLEND kernels**: `LMCBlender.process_qkv`'s HKVD math (KV-deviation
`diff_k = Σ(k_new−k_old)²` → `torch.topk(recomp_ratio·N)` → sort → selective scatter-blend
`old_k[imp_indices]=k_new`) and `lmcache.c_ops.single_layer_kv_transfer` (the real D2H paged gather,
EXP-0030's proven path). So the harness drives the **real CacheBlend selectivity kernels** inline.

## WHAT THE PIC ARM EXECUTES (the precise honest scope)
PIC arm = **inline real-CacheBlend-kernels**, strictly MORE E2E than EXP-0030's isolated gather, strictly LESS
than a full async connector-in-loop:
1. Real vLLM prefill of the reused prefix (KV cache populated by a real `generate()`).
2. **INLINE in the prefill/repair window, before first-token decode**, the REAL CacheBlend kernels over the
   affected (injected) region for **ALL 28 layers**: (a) real D2H paged gather
   `c_ops.single_layer_kv_transfer` of the affected paged KV; (b) real HKVD KV-deviation selection +
   selective scatter-blend (`LMCBlender.process_qkv` math) at the **published r%=15% recompute ratio**.
3. Real **first-token decode** through the live vLLM engine.
- **E2E TTFT(PIC) = prefix-prefill-reuse + real-blend(all layers) + first-token.**
- CDC arm = real vLLM CONTIGUOUS recompute of the affected block (R+Wb) — real D2H paged read of the
  contiguous range (all 28 layers) + real first-token decode. **E2E TTFT(CDC) = contiguous-read + first-token.**

**WHAT IS CAPTURED vs the full connector:**
- ✅ The REAL lmcache CacheBlend selectivity kernels (HKVD KV-deviation, topk, selective scatter-blend) — the
  kernels that *define* PIC in the literature — run in the **same wall-clock window as real model prefill +
  first-token compute**, so pipelining/overlap CAN hide gather latency. (EXP-0030's isolated gather could not
  show any overlap; this closes that specific composition-fallacy gap qualitatively.)
- ✅ Real vLLM PagedAttention non-contiguous paged KV layout (discovered format `NL_X_TWO_NB_BS_NH_HS`).
- ✅ Real D2H gather (CDC contiguous vs PIC scattered slot_mapping).
- ❌ **NOT captured:** lmcache's async layerwise CPU↔GPU transfer scheduler overlap (the V1 connector's
  prefetch/store pipelining), and the full `compute_layer` blend-attention recompute (`forward_contiguous`).
  The "freshly recomputed K/V" fed to the HKVD selector is a perturbed copy of the cached KV (so the
  KV-deviation selection has real signal) rather than the output of a real layer recompute of the injected
  tokens. The blend-attention's contribution to TTFT is therefore approximated by the gather+select+blend
  cost, not a full attention recompute over the blended KV.

## 1-CELL SMOKE NUMBERS (seq 8192, inj/seq 5%, batch 1; 6 reps median, 2 warmup; r%=15%)
| arm | what runs | rows (affected tokens) | E2E TTFT (ms, median) |
|---|---|---|---|
| CDC | contiguous D2H read (all 28L) + first token | 666 | **263.22** |
| PIC | gather + real HKVD-select + scatter-blend (all 28L) + first token | 747 | **271.31** |

- **PIC/CDC E2E-TTFT = 1.0308** (>1 ⇒ CDC faster). At this one cell the per-component CDC advantage SURVIVES
  the combined E2E path, but at a *narrower* margin (~3%) than EXP-0026's re-impl TTFT (1.07 @8k/5%) and well
  inside the regime EXP-0027's oracle flagged. Real HKVD topk = **112 tokens/layer** (15% of 747).
- Both finite, **ZERO faults**, **0.38 GPU-min** elapsed. NOT a decision number — it only certifies the
  combined E2E harness runs faults-free and is timeable. The full grid (12 cells × batch, 30 reps + bootstrap
  CI, the r% / quality-gate arm) per FOLLOWUP_DESIGN is the orchestrator's to dispatch.

## Safety / teardown
H100 (non-fragile), gpu_mem_util 0.4, host-mem-floor 300 watchdog, `os._exit(0)` teardown, ~20-GPU-min hard
budget + fault-twice→STOP guards (per the MI350X crash-loop postmortem discipline). Zero faults; budget used
0.38 GPU-min; GPU clean post-run (106 MiB, 0%). Another user shares this H100 — discipline respected.

## Deliverable
- Harness: `experiments/2026-05-31/EXP-0034/impl/exp0034_harness.py` (md5 e523923e…, byte-identical to the
  copy that ran on devgpu014:/tmp).
- This file. Raw JSON: devgpu014:/tmp/exp0034_smoke_result.json (mirrored below).

## STATUS for the orchestrator
- **Harness works: YES** (faults-free, finite E2E-TTFT, clean teardown).
- **True connector-in-serving-loop: NO** — infeasible in this env (vLLM 0.6.6 has no V1 KVConnector;
  lmcache's CacheBlend connector path needs vLLM ≥0.7/0.8). **PIC arm = scoped approximation** (inline real
  CacheBlend selectivity kernels in the prefill window + real first-token), documented above with the exact
  capture/gap statement.
- **READY for orchestrator to GPU-queue EXP-0034 as the SCOPED approximation.** Recommendation: the
  orchestrator should decide (or take to committee) whether the scoped inline-real-kernel E2E result answers
  VERDICT-0041's composition-fallacy (real blend kernel IN the prefill window, overlap-able) sufficiently, or
  whether the committee requires the full async-connector E2E — which would require a vLLM≥0.7/0.8 env upgrade
  (a separate operator task), in which case path-b (the honest-scope writeup) is the fallback.
