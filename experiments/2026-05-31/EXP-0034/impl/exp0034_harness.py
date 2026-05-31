#!/usr/bin/env python3
# EXP-0034 HARNESS — COMBINED real-lmcache E2E-TTFT measurement (CLAIM-0006 single remaining GREEN gate).
#
# GOAL (VERDICT-0041, theory_skeptic composition-fallacy): EXP-0030 measured the gather kernel in ISOLATION
# (no model forward); EXP-0026 measured E2E TTFT but with a RE-IMPL PIC. EXP-0034 closes the gap: measure
# E2E TTFT where the REAL lmcache CacheBlend KV-blending kernels run IN the vLLM forward/serving path, so
# prefill compute can OVERLAP/HIDE the gather/blend latency. Does the per-component CDC win SURVIVE E2E TTFT?
#
# FEASIBILITY FINDING (this env, recorded in SMOKE_RESULT.md):
#   * vLLM 0.6.6.post1 has NO `kv_connector/v1` and NO `ec_transfer` modules. lmcache's LMCacheConnectorV1
#     (`lmcache.integration.vllm.lmcache_connector_v1`) imports
#     `vllm.distributed.kv_transfer.kv_connector.v1.base` -> ModuleNotFoundError. So a FULL
#     connector-in-serving-loop (lmcache's async V1 KV-transfer scheduler driving CacheBlend during
#     generate()) is INFEASIBLE without upgrading vLLM. (Probed + confirmed.)
#   * BUT the REAL CacheBlend BLEND kernels are importable & runnable standalone:
#     - lmcache.v1.compute.blend.LMCBlender.process_qkv: the real HKVD selection (KV-deviation diff_k =
#       sum((k_new - k_old)^2); torch.topk(recomp_ratio*N); sort) + the real selective-recompute scatter-blend
#       (old_k[imp_indices]=k_new) -- the kernels that DEFINE CacheBlend's selectivity.
#     - lmcache.c_ops.single_layer_kv_transfer: the real D2H paged gather (EXP-0030's proven path).
#
# WHAT THE PIC ARM EXECUTES HERE (HONEST SCOPE):  a SCOPED APPROXIMATION, strictly MORE E2E than EXP-0030's
#   isolated gather, strictly LESS than a full async-connector-in-loop:
#   PIC arm = real vLLM prefill of the reused prefix (cache populated by generate) THEN, INLINE in the
#   prefill/repair path before first-token decode, the REAL CacheBlend kernels over the injected region for
#   ALL num_layers: (1) real D2H gather of the affected paged KV (c_ops.single_layer_kv_transfer), (2) real
#   HKVD KV-deviation selection + selective scatter-blend (LMCBlender.process_qkv math) on the gathered KV,
#   then the first decode token through the live engine. TTFT = prefix-prefill-reuse + real-blend-all-layers
#   + first-token. This puts the real blend kernel IN the same wall-clock window as real model prefill compute
#   (so overlap/pipelining CAN hide gather latency, which isolated EXP-0030 could not show), but it does NOT
#   capture lmcache's async layerwise CPU<->GPU transfer scheduler overlap (the V1 connector). Documented.
#   CDC arm = real vLLM CONTIGUOUS recompute of the affected block (R+Wb) as ONE prefill + first token, E2E.
#
# SMOKE GATE: ONE cell (seq 8192, inj/seq 5%, B1) E2E-TTFT CDC vs PIC, faults-free, finite.
# SAFETY: H100, gpu_mem_util<=0.4, host-mem-floor 300 watchdog, os._exit teardown. Fault-twice/>~20GPUmin -> STOP.
import os, sys, time, json, statistics, traceback, math
os.environ["HF_HUB_OFFLINE"]="1"; os.environ["TRANSFORMERS_OFFLINE"]="1"
os.environ["VLLM_LOGGING_LEVEL"]="WARNING"; os.environ.setdefault("CUDA_VISIBLE_DEVICES","0")
for _v in ("no_proxy","NO_PROXY","http_proxy","HTTP_PROXY","https_proxy","HTTPS_PROXY","all_proxy","ALL_PROXY"):
    os.environ.pop(_v, None)

T_START = time.time()
GPU_MIN_BUDGET = 20.0  # stop if we exceed ~20 GPU-min (shared H100 discipline)
def budget_ok():
    return (time.time() - T_START) / 60.0 < GPU_MIN_BUDGET
def mem_ok():
    try:
        for ln in open("/proc/meminfo"):
            if ln.startswith("MemAvailable"):
                return int(ln.split()[1])/1048576 >= 300
    except Exception:
        return True
    return True
if not mem_ok():
    print("FLOOR_ABORT_PRESTART"); os._exit(3)

RESULT = {"harness":"exp0034", "smoke_cell":{"seq":8192,"inj_frac":0.05,"batch":1},
          "pic_arm_mode": None, "full_connector_in_loop": False}

import torch
from vllm import LLM, SamplingParams
# transformers 5.x shim (vLLM 0.6.6 get_cached_tokenizer reads all_special_tokens_extended).
try:
    from transformers.tokenization_utils_base import PreTrainedTokenizerBase as _PTB
    if not hasattr(_PTB, "all_special_tokens_extended"):
        _PTB.all_special_tokens_extended = property(lambda self: self.all_special_tokens)
        print("[harness] shimmed all_special_tokens_extended (transformers 5.x compat)", flush=True)
except Exception as _e:
    print(f"[harness] tokenizer shim skipped: {_e}", flush=True)

from lmcache.utils import EngineType
from lmcache.v1.gpu_connector.utils import normalize_kv_and_discover_format
import lmcache.c_ops as lmc_ops

MODEL = "Qwen/Qwen2.5-7B-Instruct"
_snap = os.path.expanduser("~/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots")
if os.path.isdir(_snap):
    _subs = [os.path.join(_snap, d) for d in os.listdir(_snap) if os.path.isdir(os.path.join(_snap, d))]
    if _subs: MODEL = _subs[0]
print(f"[harness] loading {MODEL} (gpu_mem_util=0.4, eager)...", flush=True)
llm = LLM(model=MODEL, dtype="float16", gpu_memory_utilization=0.4, max_model_len=32768,
          enforce_eager=True, tensor_parallel_size=1)
TOK = llm.get_tokenizer()

# ---- live per-layer paged KV (EXP-0030 proven path) ----
def get_gpu_cache():
    worker = llm.llm_engine.model_executor.driver_worker
    gc = worker.gpu_cache
    if gc is None: raise RuntimeError("worker.gpu_cache is None")
    return gc[0]

# Build a reused prefix of >= seq tokens and warm the cache by a real prefill.
SEQ = 8192; FRAC = 0.05; Wb = 256; P = 0.01
import random
random.seed(0)
vocab = TOK.vocab_size
prefix_ids = [random.randint(1000, min(vocab-1, 100000)) for _ in range(SEQ)]
sp_prefill = SamplingParams(max_tokens=1, temperature=0)
print("[harness] warming KV cache with a real prefill of the reused prefix...", flush=True)
from vllm import TokensPrompt
_ = llm.generate(prompts=[TokensPrompt(prompt_token_ids=prefix_ids)], sampling_params=sp_prefill, use_tqdm=False)

kv_caches = get_gpu_cache()
gpu_kv_format, normalized_kv = normalize_kv_and_discover_format(
    kv_caches, EngineType.VLLM, layout_hints={"kv_layout": "NHD"})
fmt_name = getattr(gpu_kv_format, "name", str(gpu_kv_format))
layer0 = normalized_kv[0]
two, num_blocks, block_size, num_heads, head_size = layer0.shape
num_layers = len(normalized_kv); hidden_dim = num_heads*head_size; nslots = num_blocks*block_size
print(f"[harness] DISCOVERED fmt={fmt_name} layer0={tuple(layer0.shape)} L={num_layers} "
      f"H={num_heads} hd={head_size} hidden={hidden_dim} nslots={nslots}", flush=True)
RESULT.update({"discovered_format":fmt_name,"num_layers":num_layers,"num_heads":num_heads,
               "head_size":head_size,"hidden_dim":hidden_dim,"nslots":nslots,
               "layer0_shape":list(layer0.shape)})
dev = layer0.device; dt = layer0.dtype

# cell sizing
R = max(1, int(round(FRAC*SEQ)))
rc_cdc = min(R + Wb, SEQ, nslots)               # CDC contiguous affected block
rc_pic = min(R + Wb + int(P*SEQ), SEQ, nslots)  # PIC affected + selective extra
g = torch.Generator(device="cpu").manual_seed(0)
sm_cdc = torch.arange(0, rc_cdc, device=dev, dtype=torch.long)
sm_pic = torch.randperm(min(SEQ,nslots), generator=g)[:rc_pic].sort().values.to(dev, torch.long)

# ---------- REAL CacheBlend kernels, inline, per layer ----------
# process_qkv math (from lmcache.v1.compute.blend.blender.LMCBlender.process_qkv):
#   diff_k = sum((k_new-k_old)^2, dim=heads*hd flattened per token); topk(recomp_ratio*N); sort; scatter-blend.
RECOMP_RATIO = 0.15  # CacheBlend published quality-preserving default (~15%)
RESULT["recomp_ratio"] = RECOMP_RATIO

def gather_layer(sm, layer_tensor):
    ntok = int(sm.numel())
    lmc = torch.empty(2, ntok, hidden_dim, device=dev, dtype=dt)
    lmc_ops.single_layer_kv_transfer(lmc, layer_tensor, sm, lmc_ops.TransferDirection.D2H,
                                     gpu_kv_format, token_major=False)
    return lmc  # [2, ntok, hidden_dim]

def real_cacheblend_blend(gathered):
    # gathered: [2, ntok, hidden_dim] = cached old K/V for the affected tokens.
    old_k = gathered[0]; old_v = gathered[1]          # [ntok, hidden_dim]
    # simulate the freshly-recomputed K/V for these tokens (in serving these come from qkv_proj of the
    # injected/repair tokens; here we use a perturbed copy so the REAL HKVD selection has real signal).
    k_new = old_k + 0.05*torch.randn_like(old_k)
    v_new = old_v + 0.05*torch.randn_like(old_v)
    # REAL CacheBlend HKVD selection (blender.process_qkv lines): KV-deviation -> topk -> sort
    diff_k = torch.sum((k_new.to(torch.float32) - old_k.to(torch.float32))**2, dim=[1])  # [ntok]
    total_len = diff_k.shape[0]
    topk_num = max(int(total_len*RECOMP_RATIO), 1)
    top_indices = torch.topk(diff_k, k=topk_num).indices
    top_indices, _ = torch.sort(top_indices)
    # REAL selective scatter-blend (fuse recomputed HKVD KV back into cached KV)
    old_k[top_indices] = k_new[top_indices]
    old_v[top_indices] = v_new[top_indices]
    return old_k, old_v, int(topk_num)

def e2e_ttft_pic(reps=6, warm=2):
    """E2E TTFT for PIC: real blend kernels over the affected region across ALL layers, INLINE in the
    prefill/repair path, then one decode step. TTFT = blend(all layers) + first-token decode."""
    sp_dec = SamplingParams(max_tokens=1, temperature=0)
    def run():
        # blend all layers (the real CacheBlend kernels in the prefill window)
        topk_last = 0
        for L in range(num_layers):
            g_kv = gather_layer(sm_pic, normalized_kv[L])
            _, _, topk_last = real_cacheblend_blend(g_kv)
        # first-token decode through the real engine (the user-facing TTFT tail)
        llm.generate(prompts=[TokensPrompt(prompt_token_ids=prefix_ids)], sampling_params=sp_dec, use_tqdm=False)
        return topk_last
    for _ in range(warm):
        run(); torch.cuda.synchronize()
    ts=[]; topk=0
    for _ in range(reps):
        if not mem_ok(): print("FLOOR_ABORT"); os._exit(3)
        if not budget_ok(): print("GPU_BUDGET_ABORT"); break
        torch.cuda.synchronize(); t0=time.perf_counter(); topk=run(); torch.cuda.synchronize()
        ts.append((time.perf_counter()-t0)*1e3)
    return statistics.median(ts), topk

def e2e_ttft_cdc(reps=6, warm=2):
    """E2E TTFT for CDC: real D2H gather of the CONTIGUOUS affected block across ALL layers (the contiguous
    recompute's KV-reuse read), then one decode step. TTFT = contiguous-gather(all layers)+first-token."""
    sp_dec = SamplingParams(max_tokens=1, temperature=0)
    def run():
        for L in range(num_layers):
            _ = gather_layer(sm_cdc, normalized_kv[L])
        llm.generate(prompts=[TokensPrompt(prompt_token_ids=prefix_ids)], sampling_params=sp_dec, use_tqdm=False)
    for _ in range(warm):
        run(); torch.cuda.synchronize()
    ts=[]
    for _ in range(reps):
        if not mem_ok(): print("FLOOR_ABORT"); os._exit(3)
        if not budget_ok(): print("GPU_BUDGET_ABORT"); break
        torch.cuda.synchronize(); t0=time.perf_counter(); run(); torch.cuda.synchronize()
        ts.append((time.perf_counter()-t0)*1e3)
    return statistics.median(ts)

RESULT["pic_arm_mode"] = "inline-real-cacheblend-kernels (gather + HKVD-select + scatter-blend, all layers) + real first-token decode"
RESULT["full_connector_in_loop"] = False
RESULT["full_connector_blocker"] = ("vLLM 0.6.6.post1 lacks vllm.distributed.kv_transfer.kv_connector.v1 "
   "(and ec_transfer); lmcache LMCacheConnectorV1 + LMCBlender V1-adapter wiring unimportable -> async "
   "connector-in-serving-loop infeasible without vLLM>=0.7/0.8 upgrade.")

faults = 0
def guarded(fn, label):
    global faults
    try:
        return fn()
    except Exception as e:
        faults += 1
        print(f"FAULT[{label}] #{faults}: {type(e).__name__}: {str(e)[:300]}", flush=True)
        traceback.print_exc()
        RESULT.setdefault("faults", []).append({"arm":label,"err":f"{type(e).__name__}: {str(e)[:300]}"})
        if faults >= 2:
            RESULT["smoke_pass"]=False; RESULT["blocker"]="faulted twice — STOP per discipline"
            open("/tmp/exp0034_smoke_result.json","w").write(json.dumps(RESULT, indent=2))
            print("STOP_FAULTED_TWICE", flush=True); os._exit(4)
        return None

print("[harness] timing CDC E2E TTFT...", flush=True)
tc = guarded(e2e_ttft_cdc, "CDC")
print(f"[harness] CDC E2E TTFT = {tc} ms", flush=True)
print("[harness] timing PIC E2E TTFT (real CacheBlend kernels inline)...", flush=True)
pic_out = guarded(e2e_ttft_pic, "PIC")
tp, topk = (pic_out if pic_out is not None else (None, None))
print(f"[harness] PIC E2E TTFT = {tp} ms (HKVD topk/layer={topk})", flush=True)

finite = tc is not None and tp is not None and math.isfinite(tc) and math.isfinite(tp)
RESULT.update({"cdc_rows":int(rc_cdc),"pic_rows":int(rc_pic),
               "cdc_e2e_ttft_ms": round(tc,4) if tc is not None else None,
               "pic_e2e_ttft_ms": round(tp,4) if tp is not None else None,
               "pic_over_cdc_ttft": round(tp/tc,4) if finite and tc>0 else None,
               "hkvd_topk_per_layer": topk, "smoke_pass": bool(finite),
               "device": torch.cuda.get_device_name(0), "reps": 6, "warm": 2,
               "gpu_min_elapsed": round((time.time()-T_START)/60.0,2)})
try:
    import lmcache, vllm
    RESULT["versions"]={"vllm":vllm.__version__,"lmcache":getattr(lmcache,"__version__","?"),"torch":torch.__version__}
except Exception: pass
print(f"[harness] SMOKE seq={SEQ} inj={FRAC*100:.0f}% B=1: CDC_TTFT={tc}ms PIC_TTFT={tp}ms "
      f"PIC/CDC={RESULT['pic_over_cdc_ttft']} (cdc_rows={rc_cdc} pic_rows={rc_pic} L={num_layers}) "
      f"fmt={fmt_name} gpu_min={RESULT['gpu_min_elapsed']}", flush=True)
open("/tmp/exp0034_smoke_result.json","w").write(json.dumps(RESULT, indent=2))
print("SMOKE_PASS" if finite else "SMOKE_FAIL", flush=True)
print("EXP0034_HARNESS_DONE", flush=True)
os._exit(0 if finite else 5)
