"""
EXP-0036 — Cross-project probe (PROJ-0003 -> PROJ-0002): does HARNESS RECOVERY-ROUTING
shape the prefix-cache invalidation (inj/seq) distribution beyond the EXP-0005/0015 prior envelope?

CPU-ONLY, deterministic (seed 20260531), token-count PROXY. NO GPU/torch/CUDA/model CLIs.
Agent: researcher-0002-adjacent2 | --claim none (new-idea probe, NOT bound to CLAIM-0006) | <30min.

CROSS-PROJECT HYPOTHESIS (the genuinely-fresh angle this lane was asked to test):
  PROJ-0003's durable survivor = a harness-agnostic GATE TAXONOMY (REDIRECTABLE / GRANT-REQUIRED /
  TRANSIENT) and the observation that WHICH recovery modality fires is a low-dim routing/config fact.
  A redirectable gate, when hit, makes the harness INJECT a sanctioned-alternative tool result into
  the prefix (an EXTRA injection event). An abandon/terminal harness does NOT inject (loop truncates).
  => Conjecture: the inj/seq STREAM that EXP-0005 takes as i.i.d. tool draws is partly ENDOGENOUS to
     the harness recovery-routing: redirect-heavy harnesses generate extra alternative-result
     injections; abandon-heavy harnesses truncate.

KILL TEST (pre-registered): If sweeping the harness recovery-routing parameter (redirect_share in
  [0,1], the PROJ-0003 reactive-redirect-share axis) moves the CDC win-region metrics NO FURTHER than
  the EXP-0015 4x4 prior-sweep ALREADY spans, then this is just another point inside the existing
  workload-prior envelope -> COLLAPSES onto EXP-0005/0015 territory -> EARLY-KILL.
  EXP-0015 envelopes (16 priors): count-frac win1 (inj/seq<=1%): 0.175-0.408 ; win1|S>=50k: 0.411-0.520
  PASS (genuinely new axis) only if redirect-routing pushes a metric OUTSIDE its EXP-0015 range.
"""
import json, random, statistics

random.seed(20260531)

def sample_base_context():
    r = random.random()
    if r < 0.30:  return random.randint(1200, 3500)
    if r < 0.70:  return random.randint(3500, 10000)
    if r < 0.92:  return random.randint(10000, 25000)
    return random.randint(25000, 45000)

def heavy_tail(med_lo, med_hi, tail_p, tail_lo, tail_hi):
    if random.random() < tail_p:
        return random.randint(tail_lo, tail_hi)
    return random.randint(med_lo, med_hi)

def sample_file_read():   return heavy_tail(120, 2000, 0.18, 2000, 30000)
def sample_code():        return heavy_tail(40, 1500, 0.15, 1500, 40000)
def sample_api():         return heavy_tail(80, 2500, 0.20, 2500, 60000)

TOOL_TYPES = {
    "web_search":   (0.22, lambda: random.randint(150, 1800)),
    "rag_retrieve": (0.20, lambda: random.choice([3,4,5]) * random.choice([128,256,512,1024])),
    "file_read":    (0.22, sample_file_read),
    "code_exec":    (0.18, sample_code),
    "api_json":     (0.12, sample_api),
    "small_status": (0.06, lambda: random.randint(5, 60)),
}
_names = list(TOOL_TYPES.keys())
_weights = [TOOL_TYPES[n][0] for n in _names]
def sample_tool():
    n = random.choices(_names, weights=_weights, k=1)[0]
    return n, max(1, int(TOOL_TYPES[n][1]()))

GATE_HIT_RATE = 0.12
def sample_redirect_result(): return random.randint(150, 1800)   # sanctioned web/search alternative

def run(redirect_share, n_tasks=20000, condition_S=50000):
    ratios = []
    ratios_bigctx = []
    for _ in range(n_tasks):
        S = sample_base_context()
        traj = random.randint(1, 60)
        t = 0
        while t < traj:
            name, R = sample_tool()
            if S >= 1:
                r = R / S
                ratios.append(r)
                if S >= condition_S: ratios_bigctx.append(r)
            S += R
            t += 1
            if random.random() < GATE_HIT_RATE:
                if random.random() < redirect_share:
                    Ralt = sample_redirect_result()
                    r = Ralt / S
                    ratios.append(r)
                    if S >= condition_S: ratios_bigctx.append(r)
                    S += Ralt
                    t += 1
                else:
                    break
            if S > 1_000_000:
                S = sample_base_context()
    def frac_le(xs, thr): return sum(1 for x in xs if x <= thr) / len(xs) if xs else 0.0
    return {
        "redirect_share": redirect_share,
        "n_injections": len(ratios),
        "count_frac_win1": frac_le(ratios, 0.01),
        "count_frac_win1_bigctx": frac_le(ratios_bigctx, 0.01),
        "median_inj_seq": statistics.median(ratios) if ratios else None,
        "n_bigctx": len(ratios_bigctx),
    }

results = [run(rs) for rs in (0.0, 0.25, 0.5, 0.75, 1.0)]
EXP0015 = {"win1": (0.175, 0.408), "win1_bigctx": (0.411, 0.520)}
win1_vals    = [r["count_frac_win1"] for r in results]
win1_bc_vals = [r["count_frac_win1_bigctx"] for r in results]
escapes_win1    = any(v < EXP0015["win1"][0]-1e-9 or v > EXP0015["win1"][1]+1e-9 for v in win1_vals)
escapes_win1_bc = any(v < EXP0015["win1_bigctx"][0]-1e-9 or v > EXP0015["win1_bigctx"][1]+1e-9 for v in win1_bc_vals)
verdict = "PASS-NEW-AXIS" if (escapes_win1 or escapes_win1_bc) else "KILL-COLLAPSES-ONTO-EXP0015"

out = {
    "exp": "EXP-0036", "agent": "researcher-0002-adjacent2",
    "claim": "none (cross-project new-idea probe)",
    "hypothesis": "harness recovery-routing (redirect vs abandon) shifts inj/seq win-region beyond EXP-0015 prior envelope",
    "gate_hit_rate": GATE_HIT_RATE, "sweep": results,
    "win1_range_observed": [min(win1_vals), max(win1_vals)],
    "win1_bigctx_range_observed": [min(win1_bc_vals), max(win1_bc_vals)],
    "exp0015_envelope": EXP0015,
    "escapes_win1": escapes_win1, "escapes_win1_bigctx": escapes_win1_bc,
    "verdict": verdict,
}
with open(__file__.replace("impl/exp0036_harness_routing_probe.py","experiment_result/results.json"),"w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))

# ---- ADDENDUM: mechanism-discrimination control ----
# The redirect_share=0 (abandon) escape below EXP-0015's floor could be an ARTIFACT of trajectory
# truncation (abandon -> break -> shorter traj -> less context accumulation -> smaller S), which is
# the SAME accumulation/ctx-scale lever EXP-0005 already swept ('no accumulation' -> 6.3%). Discriminate:
#  CONTROL-A: abandon WITHOUT truncation (gate hit -> skip injection but CONTINUE the loop).
#             If win1 returns INTO the EXP-0015 envelope, the escape was just truncation = OLD axis.
#  CONTROL-B: redirect with a DUMP-sized alternative (not web-class) -> tests if the size-profile of
#             the redirect result (the only genuinely-PROJ-0003-specific structural input) matters.
import random as _r, statistics as _s, json as _j
def run_ctrl(redirect_share, truncate_on_abandon, alt_sampler, n_tasks=20000, condition_S=50000):
    _r.seed(20260531)
    ratios=[]; rb=[]
    for _ in range(n_tasks):
        S=sample_base_context(); traj=_r.randint(1,60); t=0
        while t<traj:
            name,R=sample_tool()
            if S>=1:
                rr=R/S; ratios.append(rr)
                if S>=condition_S: rb.append(rr)
            S+=R; t+=1
            if _r.random()<GATE_HIT_RATE:
                if _r.random()<redirect_share:
                    Ralt=alt_sampler(); rr=Ralt/S; ratios.append(rr)
                    if S>=condition_S: rb.append(rr)
                    S+=Ralt; t+=1
                else:
                    if truncate_on_abandon: break
                    # else: skip injection, continue loop (no truncation)
            if S>1_000_000: S=sample_base_context()
    fle=lambda xs,thr:(sum(1 for x in xs if x<=thr)/len(xs)) if xs else 0.0
    return {"redirect_share":redirect_share,"truncate":truncate_on_abandon,
            "win1":fle(ratios,0.01),"win1_bigctx":fle(rb,0.01),"n":len(ratios)}

ctrlA = [run_ctrl(rs, False, sample_redirect_result) for rs in (0.0,0.5,1.0)]  # abandon=no-truncate
ctrlB = [run_ctrl(rs, True, sample_code) for rs in (0.0,0.5,1.0)]              # redirect=dump-sized alt
ctrl_out={"control_A_no_truncation":ctrlA,"control_B_dump_alt":ctrlB,
          "note":"If ctrl_A win1 falls back inside EXP-0015 [0.175,0.408] for all rs, the escape was truncation=accumulation axis (OLD). EXP-0015 win1_bigctx envelope=[0.411,0.520]."}
with open("experiments/2026-05-31/EXP-0036/experiment_result/control.json","w") as f:
    _j.dump(ctrl_out,f,indent=2)
print(_j.dumps(ctrl_out,indent=2))
