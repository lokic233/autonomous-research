#!/usr/bin/env python3
"""
EXP-0054 / CLAIM-0050 — L0 discrete-event M/G/1 sim.
Input-length-SJF vs FCFS p99 latency across (rho, tau) for VLM serving.
CPU-only, stdlib-only, SERIAL. Anti-circular: GT never visible to scheduler.
"""
import math, random, csv, os, statistics, json, heapq
from bisect import insort

ART = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ART, "results")
os.makedirs(RES, exist_ok=True)

# ---- marginals -------------------------------------------------------------
# decode_length ~ lognormal(mu_d, sigma_d), heavy tail (sigma_d=1.0)
MU_D, SIG_D = 4.0, 1.0          # E[len]~e^{4.5}~90 tokens, heavy tail
# input_token_count ~ lognormal(mu_p, sigma_p), image-token dominated, large
MU_P, SIG_P = 6.5, 0.8         # ~e^{6.5}~665 input tokens typical (VLM image-heavy)
# true_service_time = c_decode * decode_length + c_prefill * input_tokens
C_DECODE = 1.0                  # decode is the serial bottleneck
C_PREFILL = 0.002              # prefill cheap/parallel per-token

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def lognorm_from_z(z, mu, sig):
    # z is standard normal; map via copula -> uniform -> lognormal quantile
    u = norm_cdf(z)
    u = min(max(u, 1e-12), 1 - 1e-12)
    # lognormal inverse cdf = exp(mu + sig * Phi^{-1}(u)) ; but Phi^{-1}(u)=z, so:
    return math.exp(mu + sig * z)

def gen_workload(n, rho_g, rng):
    """Gaussian copula: correlated (Z_proxy, Z_true) with Pearson rho_g."""
    reqs = []
    for _ in range(n):
        z_t = rng.gauss(0, 1)
        z_p = rho_g * z_t + math.sqrt(max(0.0, 1 - rho_g*rho_g)) * rng.gauss(0, 1)
        decode_len = lognorm_from_z(z_t, MU_D, SIG_D)
        input_tok  = lognorm_from_z(z_p, MU_P, SIG_P)
        true_svc = C_DECODE * decode_len + C_PREFILL * input_tok
        reqs.append({"input_tok": input_tok, "true_svc": true_svc, "decode_len": decode_len})
    return reqs

def kendall_tau(xs, ys, sample=1500, rng=None):
    """O(m^2) Kendall tau on a subsample (stdlib only)."""
    m = len(xs)
    if m > sample:
        idx = rng.sample(range(m), sample)
        xs = [xs[i] for i in idx]; ys = [ys[i] for i in idx]
    n = len(xs); c = d = 0
    for i in range(n):
        xi, yi = xs[i], ys[i]
        for j in range(i+1, n):
            sx = (xs[j] > xi) - (xs[j] < xi)
            sy = (ys[j] > yi) - (ys[j] < yi)
            p = sx * sy
            if p > 0: c += 1
            elif p < 0: d += 1
    tot = c + d
    return (c - d) / tot if tot else 0.0

# ---- discrete-event single-server queue ------------------------------------
def simulate(reqs, lam, policy, warmup=200, rng=None):
    """Non-preemptive single server. Poisson arrivals rate lam.
    policy='fcfs' or 'sjf'(input_tok). Returns list of latencies (post-warmup)."""
    n = len(reqs)
    # arrival times
    t = 0.0; arr = []
    for _ in range(n):
        t += rng.expovariate(lam); arr.append(t)
    # event-driven: process arrivals into a ready set, serve in policy order
    server_free = 0.0
    completed = []  # (completion_order_index, latency)
    # We need next-arrival driven; use index pointer.
    # ready holds indices of arrived-but-unserved.
    # For sjf we need min input_tok; keep sorted list of (key, idx).
    ready = []   # for fcfs: list (FIFO via index order, since arrivals sorted)
    ready_sjf = []  # sorted [(input_tok, idx)]
    i = 0  # next arrival idx
    served = 0
    # advance: server picks next job when free
    while served < n:
        # ensure at least one job ready or advance server_free to next arrival
        if not ((ready or ready_sjf)):
            # jump to next arrival
            if i < n:
                server_free = max(server_free, arr[i])
            # fall through to admit
        # admit all arrivals that have arrived by server_free
        while i < n and arr[i] <= server_free:
            if policy == 'fcfs':
                ready.append(i)
            else:
                insort(ready_sjf, (reqs[i]["input_tok"], i))
            i += 1
        # if still nothing ready (server idle waiting), and arrivals remain
        if policy == 'fcfs':
            have = bool(ready)
        else:
            have = bool(ready_sjf)
        if not have:
            if i < n:
                server_free = arr[i]
                if policy == 'fcfs':
                    ready.append(i)
                else:
                    insort(ready_sjf, (reqs[i]["input_tok"], i))
                i += 1
            else:
                break
        # pick next job
        if policy == 'fcfs':
            idx = ready.pop(0)
        else:
            _, idx = ready_sjf.pop(0)
        start = max(server_free, arr[idx])
        finish = start + reqs[idx]["true_svc"]
        server_free = finish
        latency = finish - arr[idx]
        completed.append((served, latency))
        served += 1
        # re-admit arrivals up to new server_free next loop
    lats = [l for (o, l) in completed if o >= warmup]
    return lats

def pctl(sorted_vals, q):
    if not sorted_vals: return float('nan')
    k = (len(sorted_vals)-1) * q
    f = math.floor(k); c = math.ceil(k)
    if f == c: return sorted_vals[int(k)]
    return sorted_vals[f]*(c-k) + sorted_vals[c]*(k-f)

# ---- sweep -----------------------------------------------------------------
RHO_GS = [0.95, 0.80, 0.62, 0.46, 0.31, 0.16, 0.0, -0.16, -0.31, -0.46, -0.62, -0.75]
RHOS = [0.70, 0.80, 0.90, 0.95]
N = 4000; K = 12; WARMUP = 200

def mean_ci(vals):
    if len(vals) < 2: return (vals[0] if vals else float('nan'), 0.0)
    m = statistics.mean(vals); s = statistics.stdev(vals)
    return m, 1.96 * s / math.sqrt(len(vals))

def main():
    rng_master = random.Random(20260603)
    rows = []
    for rho_g in RHO_GS:
        # measure realized tau once (representative seed)
        wl0 = gen_workload(N, rho_g, random.Random(hash(("tau", rho_g)) & 0xffffffff))
        tau = kendall_tau([r["input_tok"] for r in wl0],
                          [r["true_svc"] for r in wl0],
                          sample=1200, rng=random.Random(7))
        # E[svc] for lambda
        e_svc = statistics.mean([r["true_svc"] for r in wl0])
        for rho in RHOS:
            lam = rho / e_svc
            p99_fcfs=[]; p99_sjf=[]; mean_fcfs=[]; mean_sjf=[]
            for seed in range(K):
                wlseed = random.Random((hash((rho_g, rho, seed)) & 0xffffffff))
                wl = gen_workload(N, rho_g, wlseed)
                r1 = random.Random(1000+seed); r2 = random.Random(1000+seed)
                lf = sorted(simulate(wl, lam, 'fcfs', WARMUP, r1))
                ls = sorted(simulate(wl, lam, 'sjf', WARMUP, r2))
                p99_fcfs.append(pctl(lf, 0.99)); p99_sjf.append(pctl(ls, 0.99))
                mean_fcfs.append(statistics.mean(lf)); mean_sjf.append(statistics.mean(ls))
            pf_m, pf_ci = mean_ci(p99_fcfs); ps_m, ps_ci = mean_ci(p99_sjf)
            mf_m, mf_ci = mean_ci(mean_fcfs); ms_m, ms_ci = mean_ci(mean_sjf)
            ratio = ps_m / pf_m if pf_m else float('nan')
            rows.append(dict(rho_g=rho_g, tau=round(tau,4), rho=rho,
                p99_fcfs=round(pf_m,3), p99_fcfs_ci=round(pf_ci,3),
                p99_sjf=round(ps_m,3), p99_sjf_ci=round(ps_ci,3),
                p99_ratio=round(ratio,4),
                mean_fcfs=round(mf_m,3), mean_fcfs_ci=round(mf_ci,3),
                mean_sjf=round(ms_m,3), mean_sjf_ci=round(ms_ci,3),
                e_svc=round(e_svc,3)))
            print(f"tau={tau:+.3f} rho={rho:.2f} | p99 FCFS={pf_m:8.2f} SJF={ps_m:8.2f} ratio={ratio:.3f}")
    fn = os.path.join(RES, "sweep.csv")
    with open(fn, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("WROTE", fn)

if __name__ == "__main__":
    main()
