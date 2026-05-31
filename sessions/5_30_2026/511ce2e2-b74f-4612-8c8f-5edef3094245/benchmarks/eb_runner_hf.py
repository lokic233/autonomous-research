#!/usr/bin/env python3
import os, sys, time, uuid, json, statistics
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
MODEL = "Qwen/Qwen2.5-7B-Instruct"
LENS = [4096, 8192, 16384, 24576, 32768]
POSITIONS = [0.25, 0.50, 0.75]
REPS = 5
CODE_UNIT = ("class HTTPRequestHandler:\n    def dispatch(self, method, path):\n        handler = self._resolve_route(method, path)\n        return handler(self.request)\n\n")
SUFFIX = "Identify the root cause and produce a minimal unified diff."

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
DEV = "cuda:0"
def make_ids(tok, n):
    reps = max(1, n // 30 + 5); ids = tok.encode(CODE_UNIT * reps, add_special_tokens=False)
    while len(ids) < n:
        reps += 100; ids = tok.encode(CODE_UNIT * reps, add_special_tokens=False)
    return ids[:n]
@torch.no_grad()
def prefill_time(model, full_ids, n_cached):
    ids = torch.tensor([full_ids], device=DEV)
    if n_cached > 0:
        out = model(input_ids=ids[:, :n_cached], use_cache=True); past = out.past_key_values
    else:
        past = None
    torch.cuda.synchronize(); rest = ids[:, n_cached:]
    t0 = time.perf_counter()
    model(input_ids=rest, past_key_values=past, use_cache=True)
    torch.cuda.synchronize(); return (time.perf_counter()-t0)*1000
def main():
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.bfloat16, attn_implementation="sdpa").to(DEV).eval()
    # warmup CUDA/kernels to stabilize first-iter timing
    _w = tok.encode(CODE_UNIT*40, add_special_tokens=False)
    prefill_time(model, _w, 256); prefill_time(model, _w, 0)
    suffix_ids = tok.encode(SUFFIX, add_special_tokens=False)
    for L in LENS:
        probe = tok.encode("\n[TOOL_RESULT id=" + "0"*32 + " ts=" + "0"*18 + "] exit=1\n", add_special_tokens=False)
        body = L - len(suffix_ids) - len(probe) - 4
        for P in POSITIONS:
            pre_n = int(body * P); post_n = body - pre_n
            pre = make_ids(tok, pre_n); post = make_ids(tok, post_n)
            clean_ids = pre + post + suffix_ids
            n_cached_hit = len(pre) + len(post); hit = []
            for _ in range(REPS):
                hit.append(prefill_time(model, clean_ids, n_cached_hit))
            cont = []
            for _ in range(REPS):
                tool = tok.encode("\n[TOOL_RESULT id=" + uuid.uuid4().hex + " ts=" + str(time.time_ns()) + "] exit=1\n", add_special_tokens=False)
                cont.append(prefill_time(model, pre + tool + post + suffix_ids, len(pre)))
            emit("hf-transformers-5.6", L, P, hit, cont, len(pre), len(post),
                 "raw recompute: hit=suffix-only prefill, cont=(L-P) recompute from inject pt")
def emit(engine, L, P, hit, cont, pre_n, post_n, notes):
    mh, sh = statistics.median(hit), statistics.pstdev(hit)
    mc, sc = statistics.median(cont), statistics.pstdev(cont)
    pen = mc/mh if mh > 0 else float("nan")
    row = dict(engine=engine, context_len=L, inject_pos_pct=int(P*100),
               ttft_cachehit_ms=round(mh,3), ttft_contaminated_ms=round(mc,3),
               penalty_ratio=round(pen,4), stddev_hit_ms=round(sh,3),
               stddev_cont_ms=round(sc,3), reps=REPS, model=MODEL,
               pre_tokens=pre_n, post_tokens=post_n, notes=notes)
    print("ROW " + json.dumps(row), flush=True)
    sys.stderr.write("L=%d P=%d hit=%.1f cont=%.1f pen=%.2f\n" % (L,int(P*100),mh,mc,pen)); sys.stderr.flush()
if __name__ == "__main__": main()
