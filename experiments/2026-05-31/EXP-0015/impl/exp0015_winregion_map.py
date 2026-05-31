"""
EXP-0015 (CLAIM-0006) — WIN-REGION MAP with BOOTSTRAP CIs + WORKLOAD-PRIOR SENSITIVITY.
CPU-ONLY, stdlib-only (NO numpy/scipy/torch/CUDA/GPU). <30min, <1GB. Deterministic master seed.

LANE (researcher-0002-laneA): the surviving CLAIM-0006 contribution is the workload-conditioned
WIN-REGION of CDC repair on its accounting line (per EXP-0013/VERDICT-0023: slope~1 is a
CDC-specific accounting identity, NOT a cross-engine law). This experiment SHARPENS *where* in
real agentic traffic CDC actually wins, with proper statistics that EXP-0005 lacked:

  EXP-0005 gave POINT fractions (single seed) + 3 hand-picked sensitivities, win-region defined
  only by inj/seq<=1%. It found count-fraction(<=1%)=24.6% but token-weighted only 3.7%, and a
  large-ctx(S>=50k) conditional of 45.7%. It had NO confidence intervals and NO systematic prior
  sweep.

  THIS experiment adds, on the SAME evidence-grounded workload model (EXP-0005 input_data/sources.md)
  and the SAME cost regimes (EXP-0002 recompute%~=inj/seq; EXP-0006 CDC-vs-fair-PIC margin):
    (1) NONPARAMETRIC BOOTSTRAP CIs (resample tasks with replacement, B reps) on BOTH the
        count-fraction and the token-weighted-fraction of injections in CDC's win-region.
    (2) The JOINT win-region per the lane spec: inj/seq<=1% AND S>=50k (large reused ctx).
        Reported alongside the marginal inj/seq<=1% region for honesty.
    (3) SYSTEMATIC WORKLOAD-PRIOR SENSITIVITY: a grid over the two priors that most move the
        answer -- the heavy-tail dump probability (tool results are large) and the base-context
        scale (how big is the persistent context) -- with the win-region fraction + CI at each
        grid point. This replaces EXP-0005's 3 ad-hoc variants with a sweep, so we can state how
        robust the win-region is to the prior, not just at one prior.
    (4) The TOKEN-WEIGHTED win-region: do CDC-win-region injections carry a meaningful fraction of
        the actual recomputed-token *work*, or are they a count-heavy but token-light corner?

  HONEST QUESTION (lane mandate): is CDC's win-region a meaningful slice of real traffic (supports
  CLAIM-0006 as a useful characterization) or a negligible corner (further weakens it)? We do NOT
  assume the answer; we report fractions + CIs + prior-sensitivity and give an honest verdict.

  PROXY CAVEAT (inherited from EXP-0002/0005/0006): token counts are a PROXY for KV-block recompute
  work, not GPU wall-clock. The CDC win-margin over a FAIR PIC baseline is only ~1.1-1.7x median
  (EXP-0006) and a tie at inj/seq>=5% -- so "win-region" here means the inj/seq<=1% (+S>=50k) corner
  where CDC's residual ~2-6x edge over PIC lives, NOT the retired 8x-465x-vs-contiguous story.
"""
import json, random, statistics, math, csv, os

MASTER_SEED = 20260531
OUTDIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."

# ============================================================================
# Workload model -- VERBATIM size/trajectory distributions from EXP-0005, parameterized by the
# PRIOR knobs we sweep (tail_scale multiplies dump probabilities; ctx_scale scales base context).
# ============================================================================
def make_samplers(rng, tail_scale=1.0, ctx_scale=1.0):
    def sample_base_context():
        r = rng.random()
        if r < 0.30:  base = rng.randint(1200, 3500)
        elif r < 0.70: base = rng.randint(3500, 10000)
        elif r < 0.92: base = rng.randint(10000, 25000)
        else:          base = rng.randint(25000, 45000)
        return max(200, int(base * ctx_scale))

    def heavy_tail(med_lo, med_hi, tail_p, tail_lo, tail_hi):
        if rng.random() < min(0.95, tail_p * tail_scale):
            return rng.randint(tail_lo, tail_hi)
        return rng.randint(med_lo, med_hi)

    def s_file():  return heavy_tail(120, 2000, 0.18, 2000, 30000)
    def s_code():  return heavy_tail(40, 1500, 0.15, 1500, 40000)
    def s_api():   return heavy_tail(80, 2500, 0.20, 2500, 60000)

    TOOL_TYPES = {
        "web_search":   (0.22, lambda: rng.randint(150, 1800)),
        "rag_retrieve": (0.20, lambda: rng.choice([3,4,5]) * rng.choice([128,256,512,1024])),
        "file_read":    (0.22, s_file),
        "code_exec":    (0.18, s_code),
        "api_json":     (0.12, s_api),
        "small_status": (0.06, lambda: rng.randint(5, 60)),
    }
    names = list(TOOL_TYPES.keys())
    weights = [TOOL_TYPES[n][0] for n in names]
    def sample_tool():
        n = rng.choices(names, weights=weights, k=1)[0]
        return n, max(1, int(TOOL_TYPES[n][1]()))
    def sample_traj_len():
        r = rng.random()
        if r < 0.35: return rng.randint(1, 4)
        if r < 0.80: return rng.randint(5, 20)
        return rng.randint(20, 60)
    return sample_base_context, sample_tool, sample_traj_len

CTX_CAP = 1_000_000
LARGE_CTX = 50_000   # S>=50k: CDC's large reused-context regime (SWE-ContextBench >97% cache-read)

def simulate_tasks(rng, n_tasks, tail_scale=1.0, ctx_scale=1.0):
    base_ctx, tool, traj = make_samplers(rng, tail_scale, ctx_scale)
    tasks = []
    for _ in range(n_tasks):
        S = base_ctx(); T = traj(); recs = []
        for _ in range(T):
            _, R = tool()
            ratio = R / S
            recs.append((ratio, R, S))
            S += R
            if S > CTX_CAP: S = int(CTX_CAP * 0.5)
        tasks.append(recs)
    return tasks

def region_fractions(tasks):
    n = 0; tok = 0
    c_win1 = 0; t_win1 = 0
    c_winJ = 0; t_winJ = 0
    n_large = 0; tok_large = 0
    c_win1_large = 0; t_win1_large = 0
    for recs in tasks:
        for ratio, R, S in recs:
            n += 1; tok += R
            is_win1 = ratio <= 0.01
            is_large = S >= LARGE_CTX
            if is_win1: c_win1 += 1; t_win1 += R
            if is_large: n_large += 1; tok_large += R
            if is_win1 and is_large: c_winJ += 1; t_winJ += R; c_win1_large += 1; t_win1_large += R
    if n == 0: return None
    return {
        "n_injections": n, "n_tokens": tok,
        "count_frac_win1": c_win1 / n,
        "token_frac_win1": t_win1 / tok,
        "count_frac_joint_win1_large": c_winJ / n,
        "token_frac_joint_win1_large": t_winJ / tok,
        "large_ctx_share_count": n_large / n,
        "large_ctx_share_token": tok_large / tok,
        "count_frac_win1_GIVEN_large": (c_win1_large / n_large) if n_large else 0.0,
        "token_frac_win1_GIVEN_large": (t_win1_large / tok_large) if tok_large else 0.0,
    }


# ============================================================================
# FAST cluster-bootstrap support: precompute per-TASK summary vectors ONCE, then resample the
# small per-task vectors (O(B*n_tasks)) instead of rescanning all injections (O(B*n_injections)).
# The resampled fractions are IDENTICAL to scanning resampled raw injections (sums are linear).
# Each task aggregate = (n, tok, c_win1, t_win1, c_winJ, t_winJ, n_large, tok_large,
#                        c_win1_large, t_win1_large)
# ============================================================================
def task_aggregates(tasks):
    aggs = []
    for recs in tasks:
        n=tok=c_win1=t_win1=c_winJ=t_winJ=n_large=tok_large=c_w1l=t_w1l=0
        for ratio, R, S in recs:
            n+=1; tok+=R
            w1 = ratio <= 0.01; lg = S >= LARGE_CTX
            if w1: c_win1+=1; t_win1+=R
            if lg: n_large+=1; tok_large+=R
            if w1 and lg: c_winJ+=1; t_winJ+=R; c_w1l+=1; t_w1l+=R
        aggs.append((n,tok,c_win1,t_win1,c_winJ,t_winJ,n_large,tok_large,c_w1l,t_w1l))
    return aggs

def fractions_from_aggs(aggs):
    N=TOK=C1=T1=CJ=TJ=NL=TL=CWL=TWL=0
    for a in aggs:
        N+=a[0];TOK+=a[1];C1+=a[2];T1+=a[3];CJ+=a[4];TJ+=a[5];NL+=a[6];TL+=a[7];CWL+=a[8];TWL+=a[9]
    if N==0: return None
    return {
        "n_injections": N, "n_tokens": TOK,
        "count_frac_win1": C1/N,
        "token_frac_win1": T1/TOK,
        "count_frac_joint_win1_large": CJ/N,
        "token_frac_joint_win1_large": TJ/TOK,
        "large_ctx_share_count": NL/N,
        "large_ctx_share_token": TL/TOK,
        "count_frac_win1_GIVEN_large": (CWL/NL) if NL else 0.0,
        "token_frac_win1_GIVEN_large": (TWL/TL) if TL else 0.0,
    }

def fast_bootstrap(tasks, B, rng, keys):
    aggs = task_aggregates(tasks)
    n = len(aggs)
    samples = {k: [] for k in keys}
    for _ in range(B):
        boot = [aggs[rng.randrange(n)] for _ in range(n)]
        rf = fractions_from_aggs(boot)
        for k in keys:
            samples[k].append(rf[k])
    out={}
    for k in keys:
        srt=sorted(samples[k])
        lo=srt[int(0.025*len(srt))]; hi=srt[min(len(srt)-1,int(0.975*len(srt)))]
        out[k]={"mean":round(statistics.mean(srt),4),"ci95":[round(lo,4),round(hi,4)],
                "sd":round(statistics.pstdev(srt),4)}
    return out

# ============================================================================
# Nonparametric cluster bootstrap: resample TASKS with replacement, recompute fractions, B times.
# Report mean + percentile 95% CI for each fraction of interest.
# ============================================================================
def bootstrap(tasks, B, rng, keys):
    n = len(tasks)
    samples = {k: [] for k in keys}
    idx_range = range(n)
    for _ in range(B):
        boot = [tasks[rng.randrange(n)] for _ in idx_range]
        rf = region_fractions(boot)
        for k in keys:
            samples[k].append(rf[k])
    out = {}
    for k in keys:
        s = sorted(samples[k])
        lo = s[int(0.025 * len(s))]
        hi = s[min(len(s)-1, int(0.975 * len(s)))]
        out[k] = {"mean": round(statistics.mean(s), 4),
                  "ci95": [round(lo, 4), round(hi, 4)],
                  "sd": round(statistics.pstdev(s), 4)}
    return out

KEYS = ["count_frac_win1", "token_frac_win1",
        "count_frac_joint_win1_large", "token_frac_joint_win1_large",
        "large_ctx_share_count", "large_ctx_share_token",
        "count_frac_win1_GIVEN_large", "token_frac_win1_GIVEN_large"]

# ============================================================================
# MAIN
# ============================================================================
results = {
    "experiment": "EXP-0015_winregion_map_bootstrap",
    "claim": "CLAIM-0006", "level": 1, "device": "CPU-only, stdlib-only, NO GPU",
    "method": ("CPU Monte-Carlo workload (EXP-0005 distributions) -> win-region fractions "
               "(count + token-weighted) with cluster-bootstrap 95% CIs; marginal (inj/seq<=1%) "
               "and joint (inj/seq<=1% AND S>=50k); systematic workload-prior sweep."),
    "regime_basis": ("EXP-0002 recompute%~=inj/seq; EXP-0006 CDC-vs-fair-PIC margin ~1.1-1.7x median, "
                     "tie at inj/seq>=5%; EXP-0013 CDC slope 0.958[0.937,0.980] is accounting identity."),
    "win_region_def": "inj/seq<=1% (marginal); inj/seq<=1% AND S>=50k tokens (joint, CDC's home regime).",
}

N_TASKS = 20000
B = 600

rng = random.Random(MASTER_SEED)
base_tasks = simulate_tasks(rng, N_TASKS, 1.0, 1.0)
results["baseline_point"] = {k: round(v,4) if isinstance(v,float) else v
                             for k,v in region_fractions(base_tasks).items()}
boot_rng = random.Random(MASTER_SEED + 1)
results["baseline_bootstrap_ci"] = fast_bootstrap(base_tasks, B, boot_rng, KEYS)

# --- SYSTEMATIC WORKLOAD-PRIOR SWEEP ---
TAIL_SCALES = [0.5, 1.0, 2.0, 3.0]
CTX_SCALES  = [0.5, 1.0, 2.0, 4.0]
sweep = []
SWEEP_KEYS = ["count_frac_win1", "token_frac_win1", "count_frac_win1_GIVEN_large", "large_ctx_share_count"]
for ts in TAIL_SCALES:
    for cs in CTX_SCALES:
        rseed = MASTER_SEED + int(ts*100) + int(cs*1000)
        rng_s = random.Random(rseed)
        tks = simulate_tasks(rng_s, N_TASKS, ts, cs)
        pt = region_fractions(tks)
        brng = random.Random(rseed + 7)
        bci = fast_bootstrap(tks, 300, brng, SWEEP_KEYS)
        sweep.append({
            "tail_scale": ts, "ctx_scale": cs,
            "count_frac_win1": round(pt["count_frac_win1"],4),
            "count_frac_win1_ci95": bci["count_frac_win1"]["ci95"],
            "token_frac_win1": round(pt["token_frac_win1"],4),
            "token_frac_win1_ci95": bci["token_frac_win1"]["ci95"],
            "count_frac_win1_GIVEN_large": round(pt["count_frac_win1_GIVEN_large"],4),
            "count_frac_win1_GIVEN_large_ci95": bci["count_frac_win1_GIVEN_large"]["ci95"],
            "large_ctx_share_count": round(pt["large_ctx_share_count"],4),
        })
results["prior_sweep"] = sweep

cw = [s["count_frac_win1"] for s in sweep]
tw = [s["token_frac_win1"] for s in sweep]
cwl = [s["count_frac_win1_GIVEN_large"] for s in sweep]
results["sweep_summary"] = {
    "count_frac_win1_range": [round(min(cw),4), round(max(cw),4)],
    "count_frac_win1_median": round(statistics.median(cw),4),
    "token_frac_win1_range": [round(min(tw),4), round(max(tw),4)],
    "token_frac_win1_median": round(statistics.median(tw),4),
    "count_frac_win1_GIVEN_large_range": [round(min(cwl),4), round(max(cwl),4)],
    "count_frac_win1_GIVEN_large_median": round(statistics.median(cwl),4),
}

with open(os.path.join(OUTDIR, "results.json"), "w") as f:
    json.dump(results, f, indent=2)

with open(os.path.join(OUTDIR, "results.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["tail_scale","ctx_scale","count_frac_win1","count_frac_win1_lo","count_frac_win1_hi",
                "token_frac_win1","token_frac_win1_lo","token_frac_win1_hi",
                "count_frac_win1_GIVEN_large","cfg_GIVEN_large_lo","cfg_GIVEN_large_hi",
                "large_ctx_share_count"])
    for s in sweep:
        w.writerow([s["tail_scale"], s["ctx_scale"],
                    s["count_frac_win1"], s["count_frac_win1_ci95"][0], s["count_frac_win1_ci95"][1],
                    s["token_frac_win1"], s["token_frac_win1_ci95"][0], s["token_frac_win1_ci95"][1],
                    s["count_frac_win1_GIVEN_large"], s["count_frac_win1_GIVEN_large_ci95"][0],
                    s["count_frac_win1_GIVEN_large_ci95"][1], s["large_ctx_share_count"]])

print(json.dumps({"baseline_point": results["baseline_point"],
                  "baseline_bootstrap_ci": results["baseline_bootstrap_ci"],
                  "sweep_summary": results["sweep_summary"]}, indent=2))
