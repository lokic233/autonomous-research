# LaneB probe: STATIC-POLICY REGRET of a single global prefix-repair policy under the
# heavy-tailed agentic injection workload (EXP-0005 model). CPU-only, stdlib, deterministic.
# Tests candidate NEW property: does the count/volume bimodality force a gated policy (large regret
# for any static policy), or does one policy (CDC) just dominate (=> KILL, no new property)?
import random, json
random.seed(20260531)

def sample_base_context():
    r = random.random()
    if r < 0.30:  return random.randint(1200, 3500)
    if r < 0.70:  return random.randint(3500, 10000)
    if r < 0.92:  return random.randint(10000, 25000)
    return random.randint(25000, 45000)

def heavy_tail(med_lo, med_hi, tail_p, tail_lo, tail_hi):
    if random.random() < tail_p: return random.randint(tail_lo, tail_hi)
    return random.randint(med_lo, med_hi)
def sample_file_read(): return heavy_tail(120, 2000, 0.18, 2000, 30000)
def sample_code():      return heavy_tail(40, 1500, 0.15, 1500, 40000)
def sample_api():       return heavy_tail(80, 2500, 0.20, 2500, 60000)

TOOL_TYPES = {
    "web_search":   (0.22, lambda: random.randint(150, 1800)),
    "rag_retrieve": (0.20, lambda: random.choice([3,4,5]) * random.choice([128,256,512,1024])),
    "file_read":    (0.22, sample_file_read),
    "code_exec":    (0.18, sample_code),
    "api_json":     (0.12, sample_api),
    "small_status": (0.06, lambda: random.randint(5, 60)),
}
_names=list(TOOL_TYPES.keys()); _weights=[TOOL_TYPES[n][0] for n in _names]
def sample_tool():
    n=random.choices(_names,weights=_weights,k=1)[0]
    return n, max(1,int(TOOL_TYPES[n][1]()))
def sample_traj_len():
    r=random.random()
    if r<0.35: return random.randint(1,4)
    if r<0.80: return random.randint(5,20)
    return random.randint(20,60)

def pic_factor(ratio):
    if ratio>=0.05: return 1.0
    return 1.0 + 0.7*(1 - ratio/0.05)   # EXP-0006: 1.7x edge small ratio -> tie at 5%

def costs(R,S,pos):
    full=(1.0-pos)*S + R          # recompute diverged suffix
    cdc =R                        # slope~1, position-independent
    pic =R*pic_factor(R/S)        # selective scattered (FAIR PIC per EXP-0006)
    return {"FULL":full,"CDC":cdc,"PIC":pic}

def run(n_tasks=20000):
    pol={"FULL":0.0,"CDC":0.0,"PIC":0.0}; oracle=0.0; gated=0.0; n=0
    best_count={"FULL":0,"CDC":0,"PIC":0}; best_vol={"FULL":0.0,"CDC":0.0,"PIC":0.0}
    for _ in range(n_tasks):
        S=sample_base_context(); T=sample_traj_len()
        for _ in range(T):
            _,R=sample_tool(); pos=random.random(); c=costs(R,S,pos)
            for k in pol: pol[k]+=c[k]
            bp=min(c,key=c.get); bc=c[bp]; oracle+=bc
            best_count[bp]+=1; best_vol[bp]+=bc
            gated+=(c["CDC"] if R/S<0.05 else c["FULL"])
            S+=R; n+=1
    sb=min(pol,key=pol.get)
    return {
      "n_inj":n,
      "policy_total_recompute_tokens":{k:round(v) for k,v in pol.items()},
      "oracle_total":round(oracle),
      "static_best_policy":sb,
      "regret_static_best_vs_oracle":round((pol[sb]-oracle)/oracle,4),
      "regret_ratio_gated_vs_oracle":round((gated-oracle)/oracle,4),
      "best_policy_by_count_frac":{k:round(v/n,4) for k,v in best_count.items()},
      "best_policy_by_volume_frac":{k:round(v/oracle,4) for k,v in best_vol.items()},
    }
out=run()
print(json.dumps(out,indent=2))
