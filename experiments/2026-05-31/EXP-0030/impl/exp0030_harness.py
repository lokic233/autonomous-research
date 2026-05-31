#!/usr/bin/env python3
# EXP-0030 HARNESS — REAL lmcache CacheBlend gather kernel (single_layer_kv_transfer) over a LIVE vLLM
# PagedAttention KV cache, CDC-contiguous slot_mapping vs PIC-scattered slot_mapping.
#
# FIX vs the FAULTED prior attempt (/tmp/exp0030_lmcache.py): that one hand-built KV shapes + GUESSED
# GPUKVFormat.NL_X_NB_BS_HS (the MLA 3-D format) and used a [2,ntok,NH,HS] lmc buffer -> illegal mem access.
# THIS harness:
#   1. Stands up a real vLLM LLM() (Qwen2.5-7B fp16, gpu_mem_util<=0.4, max_model_len 32768, enforce_eager, tp=1).
#   2. Grabs the LIVE per-layer gpu_cache List[Tensor] from the engine and runs it through lmcache
#      normalize_kv_and_discover_format(kv_caches, EngineType.VLLM, layout_hints={"kv_layout":"NHD"})
#      to DISCOVER the correct (gpu_kv_format, normalized_kv) — no hand-guessing.
#   3. Builds the CORRECT lmc buffer [2, num_tokens, num_heads*head_size] (token_major=False, per the connector
#      store path: tmp_gpu_buffer_obj.tensor + self.kvcaches[layer] + slot_mapping + D2H + gpu_kv_format).
#   4. Times c_ops.single_layer_kv_transfer for CDC (contiguous slot_mapping) vs PIC (scattered slot_mapping).
#   SMOKE GATE: ONE tiny cell (seq 8192, inj/seq 5%, batch 1). Must not fault + produce finite CDC + PIC numbers.
# SAFETY: H100, gpu_mem_util<=0.4, host-mem-floor 300 watchdog, os._exit(0) teardown. Fault-twice -> STOP.
import os, sys, time, json, statistics, traceback
os.environ["HF_HUB_OFFLINE"]="1"; os.environ["TRANSFORMERS_OFFLINE"]="1"
os.environ["VLLM_LOGGING_LEVEL"]="WARNING"; os.environ.setdefault("CUDA_VISIBLE_DEVICES","0")
# The no_proxy env var contains "[::1]" which httpx's URLPattern parser rejects ("Invalid port: ':1]'"),
# crashing even offline HF lookups. Strip proxy vars so the (offline, local-snapshot) load never touches httpx.
for _v in ("no_proxy","NO_PROXY","http_proxy","HTTP_PROXY","https_proxy","HTTPS_PROXY","all_proxy","ALL_PROXY"):
    os.environ.pop(_v, None)

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

RESULT = {"harness":"exp0030", "smoke_cell":{"seq":8192,"inj_frac":0.05,"batch":1}}

import torch
from vllm import LLM, SamplingParams
# ros-vllm has transformers 5.9.0 which DROPPED `all_special_tokens_extended` that vLLM 0.6.6's
# get_cached_tokenizer reads. Shim it to alias all_special_tokens so the (compat) tokenizer cache works.
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
# Prefer the local HF snapshot path to fully avoid any HF API/network lookup (offline node).
_snap = os.path.expanduser("~/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots")
if os.path.isdir(_snap):
    _subs = [os.path.join(_snap, d) for d in os.listdir(_snap) if os.path.isdir(os.path.join(_snap, d))]
    if _subs:
        MODEL = _subs[0]
print(f"[harness] loading {MODEL} on vLLM PagedAttention (gpu_mem_util=0.4, eager)...", flush=True)
llm = LLM(model=MODEL, dtype="float16", gpu_memory_utilization=0.4, max_model_len=32768,
          enforce_eager=True, tensor_parallel_size=1)

# Warm the KV cache with one short prefill so the engine has allocated gpu_cache.
sp = SamplingParams(max_tokens=1, temperature=0)
llm.generate(["alpha beta gamma delta tool result code data"], sp, use_tqdm=False)

# --- Reach the LIVE per-layer gpu_cache List[Tensor] from the v0 engine ---
def get_gpu_cache():
    eng = llm.llm_engine
    worker = eng.model_executor.driver_worker
    gc = worker.gpu_cache  # List[List[Tensor]] indexed [virtual_engine][layer]
    if gc is None:
        raise RuntimeError("worker.gpu_cache is None")
    layer_list = gc[0]  # virtual_engine 0 -> List[Tensor], one per layer
    return layer_list

kv_caches = get_gpu_cache()
print(f"[harness] live gpu_cache: num_layers={len(kv_caches)} layer0.shape={tuple(kv_caches[0].shape)} "
      f"dtype={kv_caches[0].dtype} dev={kv_caches[0].device}", flush=True)

# --- DISCOVER the correct format via lmcache (the FIX) ---
gpu_kv_format, normalized_kv = normalize_kv_and_discover_format(
    kv_caches, EngineType.VLLM, layout_hints={"kv_layout": "NHD"}
)
fmt_name = getattr(gpu_kv_format, "name", str(gpu_kv_format))
layer0 = normalized_kv[0]
# flash-attn NHD: [2, num_blocks, block_size, num_heads, head_size]
two, num_blocks, block_size, num_heads, head_size = layer0.shape
hidden_dim = num_heads * head_size
nslots = num_blocks * block_size
print(f"[harness] DISCOVERED gpu_kv_format={fmt_name}  layer0.shape={tuple(layer0.shape)}  "
      f"num_blocks={num_blocks} block_size={block_size} num_heads={num_heads} head_size={head_size} "
      f"hidden_dim={hidden_dim} nslots={nslots}", flush=True)
RESULT["discovered_format"] = fmt_name
RESULT["layer0_shape"] = list(layer0.shape)
RESULT["num_layers"] = len(normalized_kv)
RESULT["num_blocks"] = int(num_blocks); RESULT["block_size"] = int(block_size)
RESULT["num_heads"] = int(num_heads); RESULT["head_size"] = int(head_size)
RESULT["hidden_dim"] = int(hidden_dim); RESULT["nslots"] = int(nslots)

dev = layer0.device; dt = layer0.dtype

def time_transfer(slot_mapping, layer_tensor, reps=10, warm=3):
    """Time D2H gather of len(slot_mapping) tokens from the live paged layer into a correct lmc buffer."""
    ntok = int(slot_mapping.numel())
    # CORRECT lmc buffer (token_major=False, non-MLA): [2, num_tokens, hidden_dim]
    lmc = torch.empty(2, ntok, hidden_dim, device=dev, dtype=dt)
    sm = slot_mapping.to(dtype=torch.long, device=dev)
    def run():
        lmc_ops.single_layer_kv_transfer(
            lmc, layer_tensor, sm,
            lmc_ops.TransferDirection.D2H, gpu_kv_format, token_major=False,
        )
    for _ in range(warm):
        run(); torch.cuda.synchronize()
    ts = []
    for _ in range(reps):
        if not mem_ok(): print("FLOOR_ABORT"); os._exit(3)
        torch.cuda.synchronize(); t0 = time.perf_counter(); run(); torch.cuda.synchronize()
        ts.append((time.perf_counter()-t0)*1e3)
    return statistics.median(ts), lmc

# --- SMOKE cell: seq 8192, inj/seq 5%, batch 1 ---
seq = 8192; frac = 0.05; Wb = 256; p = 0.01
R = max(1, int(round(frac*seq)))
rc_cdc = min(R + Wb, seq)               # CDC recompute set (contiguous)
rc_pic = min(R + Wb + int(p*seq), seq)  # PIC recompute set (scattered, selective extra)
rc_cdc = min(rc_cdc, nslots); rc_pic = min(rc_pic, nslots)

# CDC: CONTIGUOUS slot_mapping (one contiguous token range)
sm_cdc = torch.arange(0, rc_cdc, device=dev, dtype=torch.long)
# PIC: SCATTERED slot_mapping (selective tokens spread across the paged cache -> real non-contiguous gather)
g = torch.Generator(device="cpu").manual_seed(0)
perm = torch.randperm(min(seq, nslots), generator=g)[:rc_pic]
sm_pic = perm.sort().values.to(device=dev, dtype=torch.long)

layer_t = normalized_kv[0]
faults = 0
def try_time(sm, label):
    global faults
    try:
        ms, _ = time_transfer(sm, layer_t)
        return ms
    except Exception as e:
        faults += 1
        print(f"KERNEL_FAULT[{label}] #{faults}: {type(e).__name__}: {str(e)[:300]}", flush=True)
        traceback.print_exc()
        RESULT.setdefault("faults", []).append({"arm":label,"err":f"{type(e).__name__}: {str(e)[:300]}"})
        if faults >= 2:
            RESULT["smoke_pass"] = False
            RESULT["blocker"] = "faulted twice — STOP per discipline"
            open("/tmp/exp0030_smoke_result.json","w").write(json.dumps(RESULT, indent=2))
            print("STOP_FAULTED_TWICE", flush=True); os._exit(4)
        return None

tc = try_time(sm_cdc, "CDC")
tp = try_time(sm_pic, "PIC")

import math
finite = tc is not None and tp is not None and math.isfinite(tc) and math.isfinite(tp)
RESULT["cdc_rows"] = int(rc_cdc); RESULT["pic_rows"] = int(rc_pic)
RESULT["cdc_gather_ms"] = round(tc,5) if tc is not None else None
RESULT["pic_gather_ms"] = round(tp,5) if tp is not None else None
RESULT["pic_over_cdc"] = round(tp/tc,4) if finite and tc>0 else None
RESULT["smoke_pass"] = bool(finite)
RESULT["device"] = torch.cuda.get_device_name(0)
try:
    import lmcache, vllm
    RESULT["versions"] = {"vllm": vllm.__version__, "lmcache": getattr(lmcache,'__version__','?'),
                          "torch": torch.__version__}
except Exception:
    pass
RESULT["reps"] = 10
print(f"[harness] SMOKE seq={seq} inj={frac*100:.0f}% B=1: "
      f"CDC_gather={tc}ms PIC_gather={tp}ms PIC/CDC={RESULT['pic_over_cdc']} "
      f"(cdc_rows={rc_cdc} pic_rows={rc_pic}) format={fmt_name}", flush=True)
open("/tmp/exp0030_smoke_result.json","w").write(json.dumps(RESULT, indent=2))
print("SMOKE_PASS" if finite else "SMOKE_FAIL", flush=True)
print("EXP0030_HARNESS_DONE", flush=True)
os._exit(0 if finite else 5)
