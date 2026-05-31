# EXP-0030 SMOKE RESULT — true-lmcache CacheBlend gather harness, 1-cell GPU smoke

**Agent:** researcher-0002-harness2 (CPU build on devgpu014, MINIMAL GPU smoke only). **Date:** 2026-05-31.
**Scope:** Validate the vLLM+lmcache connector harness that the FAULTED prior attempt
(`/tmp/exp0030_lmcache.py`, illegal-mem-access) could not. Did NOT run the 12-cell grid; did NOT lease via the
scheduler. Orchestrator owns the full-grid GPU dispatch.

## VERDICT: SMOKE PASS ✅ — harness works, no fault, finite CDC + PIC numbers. READY for the 12-cell EXP-0030.

## Environment (pinned, recorded — load-bearing for the committee)
- **Node:** devgpu014, **device:** NVIDIA H100 (97871 MiB).
- **Python env:** `/home/dengcchi/.conda/envs/ros-vllm/bin/python` (operator-owned, source-built lmcache).
- **Versions:** vLLM **0.6.6.post1**, lmcache **0.1.dev1** (source-built, c_ops backend loads), torch **2.5.1+cu124**.
- **Model:** Qwen2.5-7B-Instruct fp16, loaded from local HF snapshot (offline). gpu_mem_util **0.4**,
  max_model_len 32768, enforce_eager, tensor_parallel=1.

## The fix (why the prior call FAULTED, and what this harness does instead)
The prior attempt hand-built KV shapes and **GUESSED** `GPUKVFormat.NL_X_NB_BS_HS` — that is the **vLLM MLA**
(3-D inner) format, which is WRONG for Qwen2.5-7B (GQA, flash-attn). It also used a `[2, ntok, NH, HS]` lmc
buffer. Both mismatched the kernel's expected layout → CUDA illegal memory access.

This harness instead:
1. Stands up a real vLLM `LLM()` and reaches the **LIVE** per-layer paged KV cache:
   `llm.llm_engine.model_executor.driver_worker.gpu_cache[0]` → `List[Tensor]`, one tensor per layer
   (list_depth=1, tensor_dim=5 — exactly the `DiscoverableKVCache` shape lmcache expects).
2. Runs that list through
   `normalize_kv_and_discover_format(kv_caches, EngineType.VLLM, layout_hints={"kv_layout":"NHD"})`
   to **DISCOVER** the correct `(gpu_kv_format, normalized_kv)` — no hand-guessing.
3. Builds the **CORRECT** lmc buffer `[2, num_tokens, num_heads*head_size]` (token_major=False), matching the
   connector's store path (`tmp_gpu_buffer_obj.tensor` + `self.kvcaches[layer]` + `slot_mapping` + `D2H` +
   `gpu_kv_format`), and calls the real `c_ops.single_layer_kv_transfer`.

## DISCOVERED FORMAT + SHAPES (the key deliverable)
- **gpu_kv_format = `NL_X_TWO_NB_BS_NH_HS`** — lmcache's "vLLM non-MLA flash attention" (NHD) format.
  (NOT the MLA `NL_X_NB_BS_HS` the prior attempt guessed.)
- lmcache detection log: `list_depth: 1, tensor_dim: 5`; `GPU KV Cache Dimensions: [28][2, 22463, 16, 4, 128]`;
  `vLLM KV cache layout: NHD`.
- **Per-layer paged KV tensor shape: `[2, 22463, 16, 4, 128]`**
  = `[2, num_blocks=22463, block_size=16, num_heads=4, head_size=128]`, fp16, cuda:0.
- num_layers = **28**, hidden_dim = num_heads*head_size = **512**, nslots = num_blocks*block_size = **359408**.
- **Correct lmc buffer (per arm): `[2, num_tokens, 512]`** (token_major=False, non-MLA).

## 1-CELL SMOKE NUMBERS (seq 8192, inj/seq 5%, batch 1; single-layer gather, 10 reps median, 3 warmup)
| arm | slot_mapping | rows (tokens gathered) | single-layer gather (ms, median) |
|---|---|---|---|
| CDC | contiguous (`arange(0, rc)`) | 666 | **0.01394** |
| PIC | scattered (sorted randperm) | 747 | **0.01378** |

- **PIC/CDC gather ratio = 0.9882** (>1 ⇒ CDC cheaper; here ≈ parity, PIC marginally cheaper at this tiny cell).
- Both finite, no fault. NOTE: this is the **per-single-layer gather-kernel cost only** (one layer, the
  D2H gather half) — it is a *plumbing smoke*, NOT a decision number. The full 12-cell run sums over all 28
  layers, sweeps inj/seq {0.5,1,2,5,10,25%} × seq {8k,28k} × batch, with reps/CI per the FOLLOWUP_DESIGN.
  Do not read the 0.99 here as the experimental answer — it only proves the kernel path is correct and timeable.

## Safety / teardown
H100 (non-fragile), gpu_mem_util 0.4, host-mem-floor 300 watchdog, `os._exit(0)` teardown. Post-run GPU clean
(106 MiB → idle, 0% util; node healthy). Single fault would retry once; two faults → STOP + report (per the
MI350X crash-loop postmortem discipline). Zero faults occurred.

## Deliverable
- Validated harness: `experiments/2026-05-31/EXP-0030/impl/exp0030_harness.py` (copied from
  devgpu014:/tmp/exp0030_harness.py).
- This file: `experiments/2026-05-31/EXP-0030/experiment_result/SMOKE_RESULT.md`.

## Operational notes for the orchestrator (env gotchas baked into the harness)
1. **Proxy crash:** node's `no_proxy` contains `[::1]`, which httpx's URLPattern parser rejects
   (`Invalid port: ':1]'`), crashing even offline HF lookups. The harness strips all proxy env vars + loads
   the model from the local HF snapshot dir. (This is why the model load initially failed.)
2. **transformers 5.x incompat:** ros-vllm has transformers **5.9.0**, which DROPPED
   `all_special_tokens_extended` that vLLM 0.6.6's `get_cached_tokenizer` reads. The harness shims it
   (aliases to `all_special_tokens`) before `LLM()` init. Without the shim, LLM() raises AttributeError.
   (py312conda has transformers 4.46.3 + NO lmcache — so the run MUST be in ros-vllm with this shim.)

## STATUS: READY for orchestrator to GPU-queue the 12-cell EXP-0030.
The connector path is validated, format discovered, kernel call faults-free and timeable. The full grid still
needs: per-layer loop over all 28 layers, the 6×2 inj/seq×seq surface (+ batch {1,8,32}), 30 reps + bootstrap
CI per cell, and the CacheBlend r% / quality-gate arm per the FOLLOWUP_DESIGN §3–§7. Those are the orchestrator's
to dispatch; this smoke only certifies the kernel plumbing is correct (no more illegal-mem-access).
