#!/usr/bin/env python3
"""
EXP-0010 (CLAIM-0005, level 1) -- CPU-ONLY recompute-cost scaling-exponent characterization.

QUESTION (surviving question after EXP-A005 weakened the super-quadratic framing):
  Is the SUB-quadratic exponent k ~ 1.3 of mid-prompt tool-injection recompute a ROBUST,
  CHARACTERIZABLE regularity, or just a local fit / artifact?

WHAT THIS IS / IS NOT (HONEST):
  - CPU token-count / analytic FLOP-cost PROXY, same methodology family as PROJ-0002
    EXP-0002 / EXP-0003 (recompute-fraction microbench on token streams, stdlib only,
    NO GPU, NO torch, NO model CLI). It is NOT GPU wall-clock.
  - EXP-A005 measured the EMPIRICAL exponent on H100/MI350X TTFT and got k=1.29-1.31.
    Here we (A) re-fit EXP-A005's own GPU TTFT data with a PROPER bootstrap CI + R^2 +
    model-comparison, and (B) reconstruct the recompute cost surface analytically to ask
    whether k~1.3 is a fixed LAW or a regime-dependent LOCAL value.
  - We do NOT revive the super-quadratic discovery framing (DEAD / red-zone). Honest target
    contribution is a CORRECTED characterization.

COST MODEL (transformer prefill decomposition; Pope 2211.05102 / Kwon 2309.06180 algebra,
flagged in academic_map as accounting-identity territory -> used only as a PROXY):
  Naive recompute-whole-suffix baseline: injection at frac f breaks the prefix-cache hash
  chain; engine recomputes N = (1-f)*L + tool tokens, each attending causally to all
  preceding (kept prefix P=f*L plus recomputed-so-far):
      attn_flops ~ nl*d*( N*P + N*(N-1)/2 )   ([L*N + N^2/2] form, attention-bound -> k->2)
      mlp_flops  ~ nl*c_mlp*d^2*N              (linear -> k->1)
  => exponent k of cost(N) ~ N^k SITS BETWEEN 1 and 2 and DRIFTS with attention/MLP balance
     (P + N/2)/(c_mlp*d). "k~1.3" is a single law ONLY if that balance is fixed. Crux tested.
"""
import csv, math, random, json, os, statistics, hashlib
random.seed(1234)

ROOT = "/Users/dengcchi/autonomous-research"
A005_CSV = ROOT + "/experiments/2026-05-30/EXP-A005/input_data/eb_injection_scaling.csv"
OUT_DIR  = ROOT + "/experiments/2026-05-31/EXP-0010"

def loglog_fit(xs, ys):
    lx = [math.log(x) for x in xs]; ly = [math.log(y) for y in ys]; n = len(lx)
    mx = sum(lx)/n; my = sum(ly)/n
    sxx = sum((x-mx)**2 for x in lx); sxy = sum((lx[i]-mx)*(ly[i]-my) for i in range(n))
    k = sxy/sxx; b = my - k*mx
    yhat = [k*lx[i]+b for i in range(n)]
    resid = [ly[i]-yhat[i] for i in range(n)]
    ss_res = sum(r*r for r in resid); ss_tot = sum((y-my)**2 for y in ly)
    r2 = 1 - ss_res/ss_tot if ss_tot > 0 else float('nan')
    se = math.sqrt(ss_res/(n-2)/sxx) if n > 2 else float('nan')
    signs = [1 if r > 0 else -1 for r in resid]
    runs = 1 + sum(1 for i in range(1, len(signs)) if signs[i] != signs[i-1])
    return {"k": k, "intercept_b": b, "r2": r2, "se": se, "n": n, "resid": resid, "sign_runs": runs}

def bootstrap_ci(xs, ys, B=4000):
    n = len(xs); ks = []; idx = list(range(n))
    for _ in range(B):
        s = [random.choice(idx) for _ in range(n)]
        bx = [xs[i] for i in s]; by = [ys[i] for i in s]
        if len(set(bx)) < 2: continue
        ks.append(loglog_fit(bx, by)["k"])
    ks.sort()
    lo = ks[int(0.025*len(ks))]; hi = ks[int(0.975*len(ks))]
    return lo, hi, statistics.median(ks), statistics.pstdev(ks)

def two_segment_fit(xs, ys):
    pts = sorted(zip(xs, ys)); n = len(pts)
    if n < 6: return None
    best = None
    for split in range(2, n-2):
        left = pts[:split]; right = pts[split:]
        if len(set(p[0] for p in left)) < 2 or len(set(p[0] for p in right)) < 2: continue
        fl = loglog_fit([p[0] for p in left],  [p[1] for p in left])
        fr = loglog_fit([p[0] for p in right], [p[1] for p in right])
        ss = sum(r*r for r in fl["resid"]) + sum(r*r for r in fr["resid"])
        if best is None or ss < best["ss"]:
            best = {"ss": ss, "split_x": pts[split][0], "k_left": fl["k"],
                    "k_right": fr["k"], "n_left": len(left), "n_right": len(right)}
    return best

def load_a005():
    rows = list(csv.DictReader(open(A005_CSV)))
    for r in rows:
        r["context_len"] = int(r["context_len"]); r["inject_pos_pct"] = int(r["inject_pos_pct"])
        r["ttft_contaminated_ms"] = float(r["ttft_contaminated_ms"])
        r["post_tokens"] = int(r["post_tokens"]); r["pre_tokens"] = int(r["pre_tokens"])
    return rows

def part_A():
    rows = load_a005(); engines = sorted(set(r["engine"] for r in rows))
    out = {"description": "Proper re-fit of EXP-A005 GPU TTFT recompute exponent (bootstrap CI + R2 + model-comp)",
           "per_engine_pos": [], "pooled_p50": {}}
    px, py = [], []
    for e in engines:
        for P in (25, 50, 75):
            pts = sorted([(r["post_tokens"], r["ttft_contaminated_ms"]) for r in rows
                          if r["engine"] == e and r["inject_pos_pct"] == P and r["post_tokens"] > 0])
            if len(pts) < 3: continue
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            f = loglog_fit(xs, ys); lo, hi, med, sd = bootstrap_ci(xs, ys); seg = two_segment_fit(xs, ys)
            if hi < 1.85: vq = "SUB-quadratic (CI upper < 1.85)"
            elif lo > 2.15: vq = "SUPER-quadratic (CI lower > 2.15) [DEAD red-zone framing]"
            else: vq = "consistent-with-quadratic (1.85-2.15)"
            rec = {"engine": e, "inject_pos_pct": P, "k_ols": round(f["k"],4),
                   "ols_se": round(f["se"],4), "r2": round(f["r2"],5),
                   "boot_ci95": [round(lo,4), round(hi,4)], "boot_median_k": round(med,4),
                   "resid_sign_runs": f["sign_runs"], "n": f["n"], "k_vs_2_verdict": vq}
            if seg: rec["piecewise"] = {"split_N": seg["split_x"], "k_left": round(seg["k_left"],3),
                                        "k_right": round(seg["k_right"],3),
                                        "ss_single": round(sum(r*r for r in f["resid"]),6),
                                        "ss_piecewise": round(seg["ss"],6)}
            out["per_engine_pos"].append(rec)
            if P == 50: px += xs; py += ys
    f = loglog_fit(px, py); lo, hi, med, sd = bootstrap_ci(px, py)
    out["pooled_p50"] = {"k_ols": round(f["k"],4), "r2": round(f["r2"],5),
                         "boot_ci95": [round(lo,4), round(hi,4)], "n": f["n"], "resid_sign_runs": f["sign_runs"]}
    return out

D_MODEL = 3584; N_LAYER = 28; C_MLP = 8.0

def recompute_flops(L, f, tool, d=D_MODEL, nl=N_LAYER, c_mlp=C_MLP):
    P = int(f * L); N = (L - P) + tool
    attn = nl * d * (N * P + N * (N - 1) / 2.0)
    mlp  = nl * c_mlp * d * d * N
    return attn + mlp, N, P

def fit_local_k(L_list, f, tool):
    pts = sorted((recompute_flops(L, f, tool)[1], recompute_flops(L, f, tool)[0]) for L in L_list)
    return loglog_fit([p[0] for p in pts], [p[1] for p in pts])

def part_B():
    out = {"description": "Analytic FLOP-proxy: local recompute exponent k across L regimes (Qwen2.5-7B scale)",
           "model": {"d_model": D_MODEL, "n_layer": N_LAYER, "c_mlp": C_MLP}, "regimes": [], "drift_summary": {}}
    L_grids = {
        "A005-window_4k-32k":   [4096, 8192, 16384, 24576, 32768],
        "small-ctx_256-2k":     [256, 512, 1024, 1536, 2048],
        "large-ctx_64k-512k":   [65536, 131072, 262144, 393216, 524288],
        "asymptotic_1M-8M":     [1000000, 2000000, 4000000, 6000000, 8000000],
    }
    tools = {"small-inject_40tok": 40, "large-inject_1000tok": 1000}
    fracs = [0.25, 0.5, 0.75]; all_ks = []
    for gname, grid in L_grids.items():
        for tname, tool in tools.items():
            for fr in fracs:
                fo = fit_local_k(grid, fr, tool)
                out["regimes"].append({"L_regime": gname, "inject": tname, "inject_frac": fr,
                                       "k_local": round(fo["k"],4), "r2": round(fo["r2"],6), "se": round(fo["se"],5)})
                all_ks.append((gname, tname, fr, fo["k"]))
    ks = [k for tup in all_ks for k in (tup[3],)]
    a005cell = [k for g,t,fr,k in all_ks if g.startswith("A005") and "small" in t and fr == 0.5]
    order = ["small-ctx_256-2k","A005-window_4k-32k","large-ctx_64k-512k","asymptotic_1M-8M"]
    mono = [round(next(k for g,t,fr,k in all_ks if g==o and "small" in t and fr==0.5),4) for o in order]
    out["drift_summary"] = {"k_min": round(min(ks),4), "k_max": round(max(ks),4),
                            "k_range_span": round(max(ks)-min(ks),4),
                            "k_A005window_smallinject_p50": round(a005cell[0],4) if a005cell else None,
                            "n_regime_cells": len(ks), "all_below_2": all(k < 2.0 for k in ks),
                            "smallinject_p50_by_growing_ctx": dict(zip(order, mono)),
                            "monotone_increasing_toward_2": all(mono[i] <= mono[i+1] for i in range(len(mono)-1))}
    return out

def radix_recompute_tokens(base, contam):
    n = min(len(base), len(contam)); lcp = 0
    while lcp < n and base[lcp] == contam[lcp]: lcp += 1
    return len(contam) - lcp
def naive_recompute_tokens(base, contam):
    return len(contam)

def part_C():
    out = {"description": "Recompute-token-count: naive-whole-suffix vs radix-LCP baseline (EXP-0003 family proxy)", "rows": []}
    TOOL = 40
    for CTX in [4000, 8000, 32000]:
        base = [random.randint(10, 50000) for _ in range(CTX)]
        tool = [random.randint(10, 50000) for _ in range(TOOL)]
        for fr in [0.25, 0.5, 0.75]:
            p = int(CTX*fr); contam = base[:p] + tool + base[p:]
            naive = naive_recompute_tokens(base, contam); radix = radix_recompute_tokens(base, contam)
            out["rows"].append({"ctx": CTX, "inject_frac": fr, "naive_recompute_tok": naive,
                                "radix_recompute_tok": radix, "naive_vs_radix_x": round(naive/max(radix,1),3),
                                "radix_recompute_pct_of_naive": round(100*radix/naive,2)})
    return out

if __name__ == "__main__":
    R = {"experiment": "EXP-0010", "claim": "CLAIM-0005", "device": "CPU",
         "note": "token-count / analytic FLOP-cost proxy; NO GPU/torch/model-CLI. NOT wall-clock.",
         "partA_refit_a005_gpu_ttft": part_A(),
         "partB_analytic_flop_regime_drift": part_B(),
         "partC_naive_vs_radix_tokencount": part_C()}
    os.makedirs(OUT_DIR + "/experiment_result", exist_ok=True)
    json.dump(R, open(OUT_DIR + "/experiment_result/exp0010_results.json", "w"), indent=2)
    print(json.dumps(R, indent=2))
