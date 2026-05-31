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
