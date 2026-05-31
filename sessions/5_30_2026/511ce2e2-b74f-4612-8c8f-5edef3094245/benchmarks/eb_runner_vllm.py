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

from vllm import LLM, SamplingParams
def make_filler(tok, n):
    reps = max(1, n // 30 + 5); text = CODE_UNIT * reps
    ids = tok.encode(text, add_special_tokens=False)
    while len(ids) < n:
        text += CODE_UNIT * 50; ids = tok.encode(text, add_special_tokens=False)
    return tok.decode(ids[:n])
def main():
    llm = LLM(model=MODEL, gpu_memory_utilization=0.55, max_model_len=32768,
              enforce_eager=True, trust_remote_code=True, enable_prefix_caching=True)
    sp = SamplingParams(max_tokens=1, temperature=0.0)
    tok = llm.get_tokenizer(); llm.generate(["warmup"], sp)
    for L in LENS:
        body = L - 160
        for P in POSITIONS:
            pre_n = int(body * P); post_n = body - pre_n
            pre = make_filler(tok, pre_n); post = make_filler(tok, post_n)
            clean = pre + post + SUFFIX
            llm.generate([clean], sp); hit = []
            for _ in range(REPS):
                llm.generate([clean], sp); time.sleep(0.2)
                t0 = time.perf_counter(); llm.generate([clean], sp)
                hit.append((time.perf_counter()-t0)*1000)
            cont = []
            for _ in range(REPS):
                llm.generate([clean], sp); time.sleep(0.2)
                tool = "\n[TOOL_RESULT id=" + uuid.uuid4().hex + " ts=" + str(time.time_ns()) + "] exit=1\n"
                contaminated = pre + tool + post + SUFFIX
                t0 = time.perf_counter(); llm.generate([contaminated], sp)
                cont.append((time.perf_counter()-t0)*1000)
            emit("vllm-0.6.6", L, P, hit, cont, pre_n, post_n,
                 "prefix-cache hash-chain break via mid-prompt UUID tool injection")
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
