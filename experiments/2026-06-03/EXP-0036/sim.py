#!/usr/bin/env python3
"""EXP-0036 / CLAIM-0039 — agent step-bubble residual-vs-continuous-batching occupancy sim.
CPU-only, stdlib-only, SERIAL. Discrete-time. No GPU/model. See PRE_REGISTRATION.md.

Model: M agents alternate DECODE BURST (~D tokens) and TOOL-WAIT (~W steps, possibly correlated cohort).
GPU has B decode slots; per step each admitted in-DECODE agent emits 1 token.
Three policies: (a) serial floor, (b) continuous batching (Orca/vLLM, greedy work-conserving),
(c) agent-step-aware (SJF-on-remaining-burst ordering under contention).
We also compute the ready-work ceiling = E[min(#ready,B)]/B (max achievable util given arrivals).
"""
import random, math, statistics, csv, os, sys, itertools

ART = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(ART, "results")
os.makedirs(RESULTS, exist_ok=True)

def sample_burst(rng, Dmean):
    # geometric-ish burst length, min 1
    p = 1.0 / Dmean
    return max(1, int(rng.expovariate(p)) )  # exponential rounded, mean ~Dmean

def sample_wait(rng, Wmean, dist):
    if dist == "exponential":
        return max(1, int(rng.expovariate(1.0/Wmean)))
    elif dist == "lognormal-heavytail":
        # lognormal with same mean Wmean, high variance (sigma=1.2 -> heavy tail)
        sigma = 1.2
        mu = math.log(Wmean) - 0.5*sigma*sigma
        return max(1, int(rng.lognormvariate(mu, sigma)))
    raise ValueError(dist)

class Agent:
    __slots__ = ("aid","phase","burst_rem","wait_rem","ready_at","burst_start_ready",
                 "tokens_done","bursts_done","lat_samples")
    def __init__(self, aid):
        self.aid = aid
        self.phase = "wait"      # start staggered in wait so arrivals spread
        self.burst_rem = 0
        self.wait_rem = 0
        self.ready_at = 0        # step it becomes ready (decode) 
        self.burst_start_ready = 0  # step current burst became ready (for latency)
        self.tokens_done = 0
        self.bursts_done = 0
        self.lat_samples = []    # per-burst completion latency

def run_policy(policy, M, B, Dmean, Wmean, wait_dist, rho, horizon, seed):
    rng = random.Random(seed*100003 + hash((policy,M,B,Dmean,Wmean,wait_dist,round(rho*10))) % 100000)
    agents = [Agent(i) for i in range(M)]
    # stagger initial waits so not all ready at step 0
    for a in agents:
        a.wait_rem = rng.randint(1, max(2, Wmean))
        a.phase = "wait"
    # cohort mechanism: when an agent finishes a burst, with prob rho it joins a shared cohort wait
    # that returns at a single shared step (correlated bubble). We maintain a "pending cohort" that
    # accumulates joiners and assigns them all the SAME wait length, sampled once per cohort formation.
    busy_slot_steps = 0
    ready_ceiling_acc = 0  # sum over steps of min(#ready, B)
    total_steps = 0
    # cohort state
    cohort_wait = None

    def start_wait(a, step):
        nonlocal cohort_wait
        a.phase = "wait"
        if rng.random() < rho:
            # join correlated cohort: shared wait length (sampled once, reused for the cohort window)
            if cohort_wait is None:
                cohort_wait = sample_wait(rng, Wmean, wait_dist)
            a.wait_rem = cohort_wait
        else:
            a.wait_rem = sample_wait(rng, Wmean, wait_dist)

    for step in range(horizon):
        # 1) advance waits -> become ready (enter decode) 
        for a in agents:
            if a.phase == "wait":
                a.wait_rem -= 1
                if a.wait_rem <= 0:
                    a.phase = "ready"
                    a.burst_rem = sample_burst(rng, Dmean)
                    a.ready_at = step
                    a.burst_start_ready = step
        # cohort resets once its members have left wait (approx: reset each step if no one waiting on it)
        # simpler: reset cohort_wait periodically so new cohorts form
        if cohort_wait is not None and not any(x.phase=="wait" for x in agents):
            cohort_wait = None

        # 2) collect ready agents (phase ready or decoding) 
        ready = [a for a in agents if a.phase in ("ready","decode")]
        nready = len(ready)
        ready_ceiling_acc += min(nready, B)

        # 3) select up to B to run this step per policy
        if policy == "serial":
            # at most 1 agent on GPU; an in-progress burst keeps the GPU until done
            running = [a for a in agents if a.phase=="decode"]
            if running:
                sel = running[:1]
            else:
                # pick earliest-ready
                cand = sorted([a for a in agents if a.phase=="ready"], key=lambda x:(x.ready_at,x.aid))
                sel = cand[:1]
        elif policy == "cb":
            # continuous batching: fill B slots, FCFS by ready_at among all ready (decode+ready) 
            cand = sorted(ready, key=lambda x:(x.ready_at, x.aid))
            sel = cand[:B]
        elif policy == "stepaware":
            # agent-step-aware: prioritize agents with SHORTEST remaining burst (fast turnover),
            # tie-break earliest ready. Already-decoding kept (no preemption) then SJF fills rest.
            decoding = [a for a in ready if a.phase=="decode"]
            waiting_ready = [a for a in ready if a.phase=="ready"]
            decoding.sort(key=lambda x:(x.burst_rem, x.aid))
            waiting_ready.sort(key=lambda x:(x.burst_rem, x.ready_at, x.aid))
            sel = (decoding + waiting_ready)[:B]
        else:
            raise ValueError(policy)

        # 4) execute: each selected emits 1 token
        sel_set = set(id(a) for a in sel)
        busy = 0
        for a in sel:
            if a.phase == "ready":
                a.phase = "decode"
            a.burst_rem -= 1
            a.tokens_done += 1
            busy += 1
            if a.burst_rem <= 0:
                # burst complete
                a.bursts_done += 1
                a.lat_samples.append(step - a.burst_start_ready + 1)
                start_wait(a, step)
        busy_slot_steps += busy
        total_steps += 1

    util = busy_slot_steps / (total_steps * B)
    ceiling = ready_ceiling_acc / (total_steps * B)
    total_tokens = sum(a.tokens_done for a in agents)
    throughput = total_tokens / total_steps
    all_lat = list(itertools.chain.from_iterable(a.lat_samples for a in agents))
    all_lat.sort()
    def pct(xs, q):
        if not xs: return float('nan')
        k = min(len(xs)-1, int(q*len(xs)))
        return xs[k]
    p99 = pct(all_lat, 0.99)
    p50 = pct(all_lat, 0.50)
    return dict(util=util, ceiling=ceiling, throughput=throughput,
                p50=p50, p99=p99, total_tokens=total_tokens,
                nbursts=len(all_lat))

def bootstrap_ci(deltas, nboot=2000, seed=42):
    rng = random.Random(seed)
    n = len(deltas)
    means = []
    for _ in range(nboot):
        s = sum(deltas[rng.randrange(n)] for _ in range(n))/n
        means.append(s)
    means.sort()
    lo = means[int(0.025*nboot)]
    hi = means[int(0.975*nboot)]
    return lo, hi

def main():
    Ms = [4, 8, 16, 32]
    Bs = [2, 4, 8]
    Dmeans = [8, 32]
    wait_dists = ["exponential", "lognormal-heavytail"]
    Wmeans = [50, 200]
    rhos = [0.0, 0.5, 0.9]
    seeds = [0,1,2,3,4]
    horizon = 4000

    raw_path = os.path.join(RESULTS, "raw_runs.csv")
    cmp_path = os.path.join(RESULTS, "policy_compare.csv")
    raw_f = open(raw_path, "w", newline="")
    raw_w = csv.writer(raw_f)
    raw_w.writerow(["M","B","Dmean","Wmean","wait_dist","rho","seed","policy",
                    "util","ceiling","residual_idle","throughput","p50","p99","nbursts"])
    cmp_f = open(cmp_path, "w", newline="")
    cmp_w = csv.writer(cmp_f)
    cmp_w.writerow(["M","B","Dmean","Wmean","wait_dist","rho",
                    "cb_util_mean","ceiling_mean","residual_idle_mean",
                    "serial_tput_mean","cb_tput_mean","stepaware_tput_mean",
                    "tput_delta_c_minus_b_mean","tput_delta_ci_lo","tput_delta_ci_hi",
                    "cb_p99_mean","stepaware_p99_mean","p99_delta_c_minus_b_mean",
                    "contention_regime"])

    grid = list(itertools.product(Ms,Bs,Dmeans,Wmeans,wait_dists,rhos))
    print(f"configs={len(grid)} x seeds={len(seeds)} x policies=3 = {len(grid)*len(seeds)*3} runs", flush=True)
    done=0
    for (M,B,Dmean,Wmean,wd,rho) in grid:
        per = {p:[] for p in ("serial","cb","stepaware")}
        for sd in seeds:
            for p in ("serial","cb","stepaware"):
                r = run_policy(p, M,B,Dmean,Wmean,wd,rho,horizon,sd)
                per[p].append(r)
                resid = r["ceiling"] - r["util"]
                raw_w.writerow([M,B,Dmean,Wmean,wd,rho,sd,p,
                    f"{r['util']:.5f}", f"{r['ceiling']:.5f}", f"{resid:.5f}",
                    f"{r['throughput']:.5f}", r["p50"], r["p99"], r["nbursts"]])
                done+=1
            if done % 90 == 0:
                print(f"  ...{done} runs done", flush=True)
        # aggregate
        cb_util = statistics.mean(x["util"] for x in per["cb"])
        ceil_m  = statistics.mean(x["ceiling"] for x in per["cb"])
        resid_m = ceil_m - cb_util
        ser_t   = statistics.mean(x["throughput"] for x in per["serial"])
        cb_t    = statistics.mean(x["throughput"] for x in per["cb"])
        sa_t    = statistics.mean(x["throughput"] for x in per["stepaware"])
        # paired deltas (c - b) per seed
        tput_deltas = [per["stepaware"][i]["throughput"] - per["cb"][i]["throughput"] for i in range(len(seeds))]
        p99_deltas  = [per["stepaware"][i]["p99"] - per["cb"][i]["p99"] for i in range(len(seeds))]
        dmean = statistics.mean(tput_deltas)
        lo,hi = bootstrap_ci(tput_deltas)
        cb_p99 = statistics.mean(x["p99"] for x in per["cb"])
        sa_p99 = statistics.mean(x["p99"] for x in per["stepaware"])
        p99dm = statistics.mean(p99_deltas)
        # contention regime: avg ready vs B -> use util-vs-ceiling proxy; mark if ceiling<1 (work-starved)
        regime = "starved" if ceil_m < 0.98 else "saturated"
        cmp_w.writerow([M,B,Dmean,Wmean,wd,rho,
            f"{cb_util:.5f}", f"{ceil_m:.5f}", f"{resid_m:.5f}",
            f"{ser_t:.5f}", f"{cb_t:.5f}", f"{sa_t:.5f}",
            f"{dmean:.5f}", f"{lo:.5f}", f"{hi:.5f}",
            cb_p99, sa_p99, f"{p99dm:.3f}", regime])
    raw_f.close(); cmp_f.close()
    print(f"DONE total_runs={done}", flush=True)
    print(f"raw -> {raw_path}", flush=True)
    print(f"cmp -> {cmp_path}", flush=True)

if __name__ == "__main__":
    main()
