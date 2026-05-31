"""
EXP-0005 Lane-B WORKLOAD REALISM: empirical distribution of inj/seq for agentic tool-use.
CPU-ONLY, deterministic, token-count PROXY (NO GPU/torch/CUDA). <30min, <1GB.

CRUX (committee will attack): is inj/seq <= 1% (the CDC-wins-big regime, recompute <~2.4% per
EXP-0002 cost law recompute% ~= inj/seq) the COMMON case in real agentic workloads, or a cherry-
picked corner? If real tool results are large relative to context, the 2% win is rare.

We DO NOT assume the answer. We model the AGENT TRAJECTORY honestly: context grows step by step as
tool results accumulate. At each step a new tool result of size R_t is injected into a context of
current length S_t. The decision-relevant quantity is inj/seq = R_t / S_t at the moment of injection.
We Monte-Carlo over (workload mix, trajectory) using EVIDENCE-GROUNDED size distributions (input_data/
sources.md) and report the FRACTION of injections in each regime, plus token-WEIGHTED fractions
(big dumps matter more), plus sensitivity to the heavy-tail assumption.
"""
import json, random, statistics, math

random.seed(20260531)  # deterministic

# ---- Evidence-grounded size distributions (tokens). See input_data/sources.md for citations. ----
# Persistent base context = system prompt + tool schemas. dev.to audit: 22,945 tok (11 srv);
# claude-code#16466: ~15k single heavy server. Light agents far less. Model lognormal-ish via choices.
def sample_base_context():
    # tokens of system prompt + tool schemas + initial user task, before any tool result
    # mixture: light agent (~2k), typical (~8k), heavy MCP (~23k), very heavy (~40k)
    r = random.random()
    if r < 0.30:  return random.randint(1200, 3500)     # light: few tools, short sys prompt
    if r < 0.70:  return random.randint(3500, 10000)    # typical multi-tool agent
    if r < 0.92:  return random.randint(10000, 25000)   # heavy MCP (dev.to 22,945)
    return random.randint(25000, 45000)                 # very heavy / many servers

def heavy_tail(med_lo, med_hi, tail_p, tail_lo, tail_hi):
    """Most results modest; with prob tail_p a large 'dump'."""
    if random.random() < tail_p:
        return random.randint(tail_lo, tail_hi)
    return random.randint(med_lo, med_hi)

# file_read: most reads are a function/section (a few hundred-2k); tail = whole large file
def sample_file_read():   return heavy_tail(120, 2000, 0.18, 2000, 30000)
# code_exec stdout: most short logs/results; tail = verbose test output / traceback / data dump
def sample_code():        return heavy_tail(40, 1500, 0.15, 1500, 40000)
# api_json: most modest records; tail = unbounded dataset (OpenBB MCP 210,004 tok worst case)
def sample_api():         return heavy_tail(80, 2500, 0.20, 2500, 60000)

# Tool-result size by tool TYPE, drawn from cited ranges. Heavy right tail for file/code/api dumps.
TOOL_TYPES = {
    # name: (weight, sampler) -- weights = rough mix of agentic tool calls
    "web_search":   (0.22, lambda: random.randint(150, 1800)),     # 5 results + snippets, Brave-style
    "rag_retrieve": (0.20, lambda: random.choice([3,4,5]) * random.choice([128,256,512,1024])), # k*chunk
    "file_read":    (0.22, sample_file_read),                      # heavy tail
    "code_exec":    (0.18, sample_code),                           # stdout, heavy tail
    "api_json":     (0.12, sample_api),                            # JSON resp, heavy tail incl dumps
    "small_status": (0.06, lambda: random.randint(5, 60)),         # ack/status/short answer
}

_names = list(TOOL_TYPES.keys())
_weights = [TOOL_TYPES[n][0] for n in _names]
def sample_tool():
    n = random.choices(_names, weights=_weights, k=1)[0]
    return n, max(1, int(TOOL_TYPES[n][1]()))

# Trajectory length: number of tool calls in a task (agentic loops). Mix short/med/long-horizon.
def sample_traj_len():
    r = random.random()
    if r < 0.35: return random.randint(1, 4)     # short task
    if r < 0.80: return random.randint(5, 20)    # typical
    return random.randint(20, 60)                # long-horizon (SWE agent)

CTX_CAP = 1_000_000  # 1M-token frontier; injections beyond cap would trigger compaction (modeled)

def classify(ratio):
    if ratio <= 0.01: return "CDC_WINS(<=1%)"
    if ratio <= 0.05: return "MID(1-5%)"
    return "CDC_DEGRADES(>5%)"

def run(n_tasks=20000, compaction=True):
    counts = {"CDC_WINS(<=1%)":0, "MID(1-5%)":0, "CDC_DEGRADES(>5%)":0}
    tok_weight = {"CDC_WINS(<=1%)":0.0, "MID(1-5%)":0.0, "CDC_DEGRADES(>5%)":0.0}
    by_tool = {}  # tool -> regime counts
    ratios = []
    n_injections = 0
    for _ in range(n_tasks):
        S = sample_base_context()          # current sequence length
        T = sample_traj_len()
        for _ in range(T):
            name, R = sample_tool()
            # inj/seq at the moment THIS result is injected (into context-so-far)
            ratio = R / S
            reg = classify(ratio)
            counts[reg] += 1
            tok_weight[reg] += R           # weight by injected tokens (big dumps weigh more)
            by_tool.setdefault(name, {"CDC_WINS(<=1%)":0,"MID(1-5%)":0,"CDC_DEGRADES(>5%)":0})
            by_tool[name][reg] += 1
            ratios.append(ratio)
            n_injections += 1
            # context grows by the injected result (the realistic agentic accumulation)
            S += R
            if compaction and S > CTX_CAP:
                S = int(CTX_CAP * 0.5)     # context compaction/summarization kicks in
    tot = n_injections
    twt = sum(tok_weight.values())
    frac = {k: counts[k]/tot for k in counts}
    tfrac = {k: tok_weight[k]/twt for k in tok_weight}
    ratios.sort()
    pct = lambda p: ratios[min(len(ratios)-1, int(p*len(ratios)))]
    return {
        "n_tasks": n_tasks, "n_injections": tot, "compaction": compaction,
        "count_fraction": {k: round(v,4) for k,v in frac.items()},
        "token_weighted_fraction": {k: round(v,4) for k,v in tfrac.items()},
        "ratio_percentiles": {"p10":round(pct(.10),5),"p25":round(pct(.25),5),
            "p50":round(pct(.50),5),"p75":round(pct(.75),5),"p90":round(pct(.90),5),
            "p95":round(pct(.95),5),"p99":round(pct(.99),5)},
        "by_tool_count_fraction": {t:{k:round(c[k]/sum(c.values()),3) for k in c} for t,c in by_tool.items()},
    }

# Main run + sensitivity (vary heavy-tail probability scaling and base-context size)
out = {"experiment":"EXP-0005_workload_realism",
       "method":"CPU Monte-Carlo, token-count PROXY for KV blocks; trajectory-aware inj/seq; NO GPU",
       "regime_law":"recompute% ~= inj/seq (EXP-0002); CDC_WINS<=1% (recompute<~2.4%), DEGRADES>5%",
       "main": run(20000, compaction=True)}

# Sensitivity S1: NO context accumulation (each tool result vs only base context) -> adversarial worst case
def run_no_accum(n_tasks=20000):
    counts={"CDC_WINS(<=1%)":0,"MID(1-5%)":0,"CDC_DEGRADES(>5%)":0}
    for _ in range(n_tasks):
        S=sample_base_context(); T=sample_traj_len()
        for _ in range(T):
            _,R=sample_tool(); counts[classify(R/S)]+=1
    tot=sum(counts.values())
    return {k:round(counts[k]/tot,4) for k in counts}
out["sensitivity_no_accumulation"] = run_no_accum(20000)

# Sensitivity S2: heavier tails (double dump probability) -> stress the "tool dumps are large" hypothesis
def boost_tails():
    global sample_file_read, sample_code, sample_api
    TOOL_TYPES["file_read"]=(0.22, lambda: heavy_tail(120,2000,0.36,2000,30000))
    TOOL_TYPES["code_exec"]=(0.18, lambda: heavy_tail(40,1500,0.30,1500,40000))
    TOOL_TYPES["api_json"] =(0.12, lambda: heavy_tail(80,2500,0.40,2500,60000))
boost_tails()
out["sensitivity_heavy_tails_2x"] = run(20000, compaction=True)["count_fraction"]

json.dump(out, open("/tmp/exp0005_workload.json","w"), indent=2)
print(json.dumps(out, indent=2))

# Sensitivity S3 (FAIR-TO-CDC): condition on LARGE context (S>=50k tokens) at injection time.
# This is CDC's best case (long-lived, heavily-reused context per SWE-ContextBench >97% cache-read).
def run_large_ctx(n_tasks=20000, thresh=50000):
    counts={"CDC_WINS(<=1%)":0,"MID(1-5%)":0,"CDC_DEGRADES(>5%)":0}; seen=0
    # reset tails to baseline
    TOOL_TYPES["file_read"]=(0.22, sample_file_read)
    TOOL_TYPES["code_exec"]=(0.18, sample_code)
    TOOL_TYPES["api_json"] =(0.12, sample_api)
    for _ in range(n_tasks):
        S=sample_base_context(); T=sample_traj_len()
        for _ in range(T):
            name,R=sample_tool()
            if S>=thresh:
                counts[classify(R/S)]+=1; seen+=1
            S+=R
            if S>1_000_000: S=500_000
    tot=max(1,seen)
    return {"n_injections_in_large_ctx":seen,
            "fraction_of_all":round(seen/291454,3),
            **{k:round(counts[k]/tot,4) for k in counts}}
import json as _j
_o=_j.load(open("/tmp/exp0005_workload.json"))
_o["sensitivity_large_ctx_ge50k"]=run_large_ctx(20000,50000)
_j.dump(_o,open("/tmp/exp0005_workload.json","w"),indent=2)
print("LARGE_CTX(>=50k):", _o["sensitivity_large_ctx_ge50k"])

# Sensitivity S3 (FAIR-TO-CDC): condition on LARGE context (S>=50k tokens) at injection time.
# This is CDC's best case (long-lived, heavily-reused context per SWE-ContextBench >97% cache-read).
def run_large_ctx(n_tasks=20000, thresh=50000):
    counts={"CDC_WINS(<=1%)":0,"MID(1-5%)":0,"CDC_DEGRADES(>5%)":0}; seen=0
    # reset tails to baseline
    TOOL_TYPES["file_read"]=(0.22, sample_file_read)
    TOOL_TYPES["code_exec"]=(0.18, sample_code)
    TOOL_TYPES["api_json"] =(0.12, sample_api)
    for _ in range(n_tasks):
        S=sample_base_context(); T=sample_traj_len()
        for _ in range(T):
            name,R=sample_tool()
            if S>=thresh:
                counts[classify(R/S)]+=1; seen+=1
            S+=R
            if S>1_000_000: S=500_000
    tot=max(1,seen)
    return {"n_injections_in_large_ctx":seen,
            "fraction_of_all":round(seen/291454,3),
            **{k:round(counts[k]/tot,4) for k in counts}}
import json as _j
_o=_j.load(open("/tmp/exp0005_workload.json"))
_o["sensitivity_large_ctx_ge50k"]=run_large_ctx(20000,50000)
_j.dump(_o,open("/tmp/exp0005_workload.json","w"),indent=2)
print("LARGE_CTX(>=50k):", _o["sensitivity_large_ctx_ge50k"])
