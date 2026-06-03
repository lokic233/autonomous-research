#!/usr/bin/env python3
"""EXP-0036 / CLAIM-0039 — agent step-bubble residual-vs-continuous-batching occupancy sim.
CPU-only, stdlib-only, SERIAL. Discrete-time. No GPU/model. See PRE_REGISTRATION.md.

v2 FIX: arrivals are PRE-SAMPLED per agent (burst lengths, tool-waits, cohort membership) from a
seed that does NOT depend on policy. All three policies replay the IDENTICAL arrival tape -> the
comparison is fully PAIRED; only the scheduling decision differs. (v1 bug: policy was hashed into
the RNG seed AND start_wait drew RNG mid-run, so each policy saw a different arrival stream ->
spurious throughput 'wins'. Fixed.)

Note on correlation: each agent has a tape of wait lengths. To make waits CORRELATED across agents,
we assign cohort waits at the GLOBAL level: a fraction rho of (agent, burst-index) wait-events draw
their wait from a small set of SHARED cohort wait-values keyed by a coarse 'cohort epoch', so many
agents returning around the same window share the same long wait -> aligned (correlated) bubbles.
This is arrival-side and policy-independent.
"""
import random, math, statistics, csv, os, itertools

ART = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(ART, "results")
os.makedirs(RESULTS, exist_ok=True)

def sample_burst(rng, Dmean):
    return max(1, int(rng.expovariate(1.0/Dmean)))

def sample_wait(rng, Wmean, dist):
    if dist == "exponential":
        return max(1, int(rng.expovariate(1.0/Wmean)))
    elif dist == "lognormal-heavytail":
        sigma = 1.2
        mu = math.log(Wmean) - 0.5*sigma*sigma
        return max(1, int(rng.lognormvariate(mu, sigma)))
    raise ValueError(dist)

def build_tapes(M, Dmean, Wmean, wait_dist, rho, horizon, seed, max_events=400):
    """Pre-sample, policy-independently, each agent's (burst_len, wait_len) event sequence.
    Correlation: with prob rho a wait-event uses a SHARED cohort wait value (heavy, aligned)."""
    rng = random.Random(seed*100003 + (hash((M,Dmean,Wmean,wait_dist,round(rho*10))) % 100000))
    # pre-build a pool of cohort wait values (heavy) that get reused -> correlated/aligned waits
    cohort_pool = [sample_wait(rng, Wmean, wait_dist) for _ in range(max(2, M//2))]
    bursts = [[] for _ in range(M)]
    waits  = [[] for _ in range(M)]
    init_wait = []
    for a in range(M):
        init_wait.append(rng.randint(1, max(2, Wmean)))  # stagger start
        for _ in range(max_events):
            bursts[a].append(sample_burst(rng, Dmean))
            if rng.random() < rho:
                waits[a].append(cohort_pool[rng.randrange(len(cohort_pool))])  # shared -> correlated
            else:
                waits[a].append(sample_wait(rng, Wmean, wait_dist))
    return init_wait, bursts, waits

class Agent:
    __slots__ = ("aid","phase","burst_rem","wait_rem","ready_at","burst_start_ready",
                 "tokens_done","bursts_done","lat_samples","ev")
    def __init__(self, aid, init_wait):
        self.aid=aid; self.phase="wait"; self.burst_rem=0; self.wait_rem=init_wait
        self.ready_at=0; self.burst_start_ready=0; self.tokens_done=0; self.bursts_done=0
        self.lat_samples=[]; self.ev=0  # index into tapes

def run_policy(policy, M, B, Dmean, Wmean, wait_dist, rho, horizon, seed, tapes):
    init_wait, bursts, waits = tapes
    agents=[Agent(i, init_wait[i]) for i in range(M)]
    busy_slot_steps=0; ready_ceiling_acc=0; total_steps=0
    maxev=len(bursts[0])

    for step in range(horizon):
        # advance waits -> ready (pull next burst from tape) 
        for a in agents:
            if a.phase=="wait":
                a.wait_rem-=1
                if a.wait_rem<=0:
                    if a.ev>=maxev:  # tape exhausted: park (rare; max_events sized generously) 
                        a.phase="parked"; continue
                    a.phase="ready"; a.burst_rem=bursts[a.aid][a.ev]
                    a.ready_at=step; a.burst_start_ready=step
        ready=[a for a in agents if a.phase in ("ready","decode")]
        ready_ceiling_acc+=min(len(ready),B)

        if policy=="serial":
            running=[a for a in agents if a.phase=="decode"]
            if running: sel=running[:1]
            else:
                cand=sorted([a for a in agents if a.phase=="ready"], key=lambda x:(x.ready_at,x.aid))
                sel=cand[:1]
        elif policy=="cb":
            sel=sorted(ready, key=lambda x:(x.ready_at,x.aid))[:B]
        elif policy=="stepaware":
            decoding=sorted([a for a in ready if a.phase=="decode"], key=lambda x:(x.burst_rem,x.aid))
            wready=sorted([a for a in ready if a.phase=="ready"], key=lambda x:(x.burst_rem,x.ready_at,x.aid))
            sel=(decoding+wready)[:B]
        else: raise ValueError(policy)

        busy=0
        for a in sel:
            if a.phase=="ready": a.phase="decode"
            a.burst_rem-=1; a.tokens_done+=1; busy+=1
            if a.burst_rem<=0:
                a.bursts_done+=1
                a.lat_samples.append(step-a.burst_start_ready+1)
                # enter wait from tape
                a.phase="wait"; a.wait_rem=waits[a.aid][a.ev]; a.ev+=1
        busy_slot_steps+=busy; total_steps+=1

    util=busy_slot_steps/(total_steps*B)
    ceiling=ready_ceiling_acc/(total_steps*B)
    total_tokens=sum(a.tokens_done for a in agents)
    throughput=total_tokens/total_steps
    all_lat=[]
    for a in agents: all_lat.extend(a.lat_samples)
    all_lat.sort()
    def pct(xs,q):
        if not xs: return float('nan')
        return xs[min(len(xs)-1,int(q*len(xs)))]
    return dict(util=util, ceiling=ceiling, throughput=throughput,
                p50=pct(all_lat,0.5), p99=pct(all_lat,0.99),
                total_tokens=total_tokens, nbursts=len(all_lat))

def bootstrap_ci(deltas, nboot=2000, seed=42):
    rng=random.Random(seed); n=len(deltas); means=[]
    for _ in range(nboot):
        means.append(sum(deltas[rng.randrange(n)] for _ in range(n))/n)
    means.sort()
    return means[int(0.025*nboot)], means[int(0.975*nboot)]

def main():
    Ms=[4,8,16,32]; Bs=[2,4,8]; Dmeans=[8,32]
    wait_dists=["exponential","lognormal-heavytail"]; Wmeans=[50,200]
    rhos=[0.0,0.5,0.9]; seeds=[0,1,2,3,4]; horizon=4000

    raw_f=open(os.path.join(RESULTS,"raw_runs.csv"),"w",newline=""); raw_w=csv.writer(raw_f)
    raw_w.writerow(["M","B","Dmean","Wmean","wait_dist","rho","seed","policy",
                    "util","ceiling","residual_idle","throughput","p50","p99","nbursts"])
    cmp_f=open(os.path.join(RESULTS,"policy_compare.csv"),"w",newline=""); cmp_w=csv.writer(cmp_f)
    cmp_w.writerow(["M","B","Dmean","Wmean","wait_dist","rho",
                    "cb_util_mean","ceiling_mean","residual_idle_mean",
                    "serial_tput_mean","cb_tput_mean","stepaware_tput_mean",
                    "tput_delta_c_minus_b_mean","tput_delta_ci_lo","tput_delta_ci_hi",
                    "cb_p99_mean","stepaware_p99_mean","p99_delta_c_minus_b_mean","contention_regime"])

    grid=list(itertools.product(Ms,Bs,Dmeans,Wmeans,wait_dists,rhos))
    print(f"configs={len(grid)} x seeds={len(seeds)} x policies=3 = {len(grid)*len(seeds)*3} runs",flush=True)
    done=0
    for (M,B,Dmean,Wmean,wd,rho) in grid:
        per={p:[] for p in ("serial","cb","stepaware")}
        for sd in seeds:
            tapes=build_tapes(M,Dmean,Wmean,wd,rho,horizon,sd)  # SHARED across the 3 policies
            for p in ("serial","cb","stepaware"):
                r=run_policy(p,M,B,Dmean,Wmean,wd,rho,horizon,sd,tapes)
                per[p].append(r); done+=1
                raw_w.writerow([M,B,Dmean,Wmean,wd,rho,sd,p,
                    f"{r['util']:.5f}",f"{r['ceiling']:.5f}",f"{r['ceiling']-r['util']:.5f}",
                    f"{r['throughput']:.5f}",r["p50"],r["p99"],r["nbursts"]])
            if done%180==0: print(f"  ...{done} runs",flush=True)
        cb_util=statistics.mean(x["util"] for x in per["cb"])
        ceil_m=statistics.mean(x["ceiling"] for x in per["cb"])
        ser_t=statistics.mean(x["throughput"] for x in per["serial"])
        cb_t=statistics.mean(x["throughput"] for x in per["cb"])
        sa_t=statistics.mean(x["throughput"] for x in per["stepaware"])
        tput_d=[per["stepaware"][i]["throughput"]-per["cb"][i]["throughput"] for i in range(len(seeds))]
        p99_d=[per["stepaware"][i]["p99"]-per["cb"][i]["p99"] for i in range(len(seeds))
               if not (math.isnan(per["stepaware"][i]["p99"]) or math.isnan(per["cb"][i]["p99"]))]
        lo,hi=bootstrap_ci(tput_d)
        cb_p99=statistics.mean(x["p99"] for x in per["cb"] if not math.isnan(x["p99"])) if any(not math.isnan(x["p99"]) for x in per["cb"]) else float('nan')
        sa_p99=statistics.mean(x["p99"] for x in per["stepaware"] if not math.isnan(x["p99"])) if any(not math.isnan(x["p99"]) for x in per["stepaware"]) else float('nan')
        regime="starved" if ceil_m<0.98 else "saturated"
        cmp_w.writerow([M,B,Dmean,Wmean,wd,rho,
            f"{cb_util:.5f}",f"{ceil_m:.5f}",f"{ceil_m-cb_util:.5f}",
            f"{ser_t:.5f}",f"{cb_t:.5f}",f"{sa_t:.5f}",
            f"{statistics.mean(tput_d):.5f}",f"{lo:.5f}",f"{hi:.5f}",
            f"{cb_p99:.3f}",f"{sa_p99:.3f}",f"{(statistics.mean(p99_d) if p99_d else float('nan')):.3f}",regime])
    raw_f.close(); cmp_f.close()
    print(f"DONE total_runs={done}",flush=True)

if __name__=="__main__":
    main()
