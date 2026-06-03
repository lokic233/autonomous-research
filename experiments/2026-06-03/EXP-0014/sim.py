#!/usr/bin/python3
# EXP-0014 L0 — empirical characterization of intra-step tool-call parallelism + correctness-safety.
# CPU-only, stdlib-only, SERIAL. Honest pipeline. Ground-truth DAGs by construction.
import random, csv, statistics, math, os, json

ART = "/Users/dengcchi/autonomous-research-v3/experiments/2026-06-03/EXP-0014"
RES = os.path.join(ART, "results")
os.makedirs(RES, exist_ok=True)

# ----------------------------------------------------------------------------------
# A "step" is a list of tool calls. Each call: id, reads (set of resource keys it
# CONSUMES), writes (set it PRODUCES). A true dependency edge A->B exists iff:
#   D1 data: B.reads intersects A.writes  (B consumes a value A produced)
#   D2 side-effect/order: B.writes intersects A.writes  OR  B.writes intersects A.reads
#       (write-write or read-after... we model write conflicts on shared resources)
# This is the GROUND-TRUTH DAG. The analyzer rebuilds it from reads/writes.
# ----------------------------------------------------------------------------------

def true_edges(calls):
    """Return set of (i,j) i<j ground-truth dependency edges (j depends on i)."""
    edges = set()
    for j in range(len(calls)):
        for i in range(j):
            a, b = calls[i], calls[j]
            data_dep = bool(b["reads"] & a["writes"])
            # side-effect / ordering: shared write target, or b writes what a touched
            order_dep = bool(b["writes"] & a["writes"]) or bool(b["writes"] & a["reads"])
            if data_dep or order_dep:
                edges.add((i, j))
    return edges

def independent_calls(calls, edges):
    """A call j is independent iff no edge (i,j) with i<j (no dep on a PRIOR same-step call)."""
    dependents = {j for (i, j) in edges}
    return [j for j in range(len(calls)) if j not in dependents]

def critical_path_depth(calls, edges):
    """Longest chain length (# nodes) in the DAG = ideal-parallel depth."""
    n = len(calls)
    depth = [1] * n
    for j in range(n):
        for i in range(j):
            if (i, j) in edges:
                depth[j] = max(depth[j], depth[i] + 1)
    return max(depth) if n else 0

# ---------------- Archetype generators (return list of calls with reads/writes) -----------------
_rid = [0]
def rk():  # unique resource key
    _rid[0] += 1
    return f"r{_rid[0]}"

def gen_fanout(rng):
    # k independent retrievals/searches feeding ONE aggregator that depends on all.
    k = rng.choice([2,3,3,4,4,5])
    calls = []
    produced = []
    for _ in range(k):
        w = rk()
        calls.append({"reads": set(), "writes": {w}})  # independent external query
        produced.append(w)
    # aggregator depends on all k (reads all their outputs). Present ~80% of the time.
    if rng.random() < 0.8:
        calls.append({"reads": set(produced), "writes": {rk()}})
    return calls

def gen_sequential(rng):
    # read -> transform -> (transform) -> write chain. Each consumes prior. Independence ~ none.
    n = rng.choice([2,3,3,4])
    calls = []
    prev = None
    for _ in range(n):
        reads = {prev} if prev is not None else set()
        w = rk()
        calls.append({"reads": reads, "writes": {w}})
        prev = w
    return calls

def gen_mixed(rng):
    # fan-out of k independent lookups feeding a dependent synthesis, plus 1-2 independent side calls.
    k = rng.choice([2,3,3])
    calls = []
    produced = []
    for _ in range(k):
        w = rk()
        calls.append({"reads": set(), "writes": {w}})
        produced.append(w)
    # synthesis depends on the lookups
    syn = rk()
    calls.append({"reads": set(produced), "writes": {syn}})
    # independent side calls (e.g., log a metric, fetch unrelated config) - truly independent
    for _ in range(rng.choice([1,1,2])):
        calls.append({"reads": set(), "writes": {rk()}})
    rng.shuffle(calls)  # realistic: order within a step isn't pre-sorted
    return calls

def gen_single(rng):
    return [{"reads": set(), "writes": {rk()}}]

ARCHS = {"fanout": gen_fanout, "sequential": gen_sequential, "mixed": gen_mixed, "single": gen_single}

def sample_step(mix, rng):
    r = rng.random()
    c = 0.0
    for name, frac in mix.items():
        c += frac
        if r <= c:
            return name, ARCHS[name](rng)
    return "single", gen_single(rng)

# ---------------- Metric A: f_indep as a function of mix ----------------
def analyze_mix(mix, n_steps, seed):
    rng = random.Random(seed)
    tot_calls = 0; tot_indep = 0
    step_fracs = []; widths = []; depths = []; speedups = []
    multi_call_steps = 0
    for _ in range(n_steps):
        _name, calls = sample_step(mix, rng)
        edges = true_edges(calls)
        indep = independent_calls(calls, edges)
        n = len(calls)
        tot_calls += n
        tot_indep += len(indep)
        step_fracs.append(len(indep)/n)
        widths.append(len(indep))
        d = critical_path_depth(calls, edges)
        depths.append(d)
        speedups.append(n/d if d else 1.0)
        if n > 1: multi_call_steps += 1
    return {
        "f_indep_callwt": tot_indep/tot_calls,                 # call-weighted
        "f_indep_stepavg": statistics.mean(step_fracs),        # step-averaged
        "mean_width": statistics.mean(widths),
        "mean_depth": statistics.mean(depths),
        "mean_speedup": statistics.mean(speedups),             # equal-latency ideal
        "frac_multicall": multi_call_steps/n_steps,
    }

# ---------------- Metric B: correctness-safety under detector error ----------------
def corrupted_under_detector(calls, edges, e, rng):
    """Detector misses each TRUE edge with prob e (false negative). If it misses a
    load-bearing edge (a real dependency), the dependent call is dispatched in parallel
    and consumes a stale/absent result -> step corrupted. We treat EVERY true edge as
    load-bearing for the final answer (conservative-but-honest: a missed data/order dep
    can corrupt). Returns True if step would produce a wrong result."""
    for (_i, _j) in edges:
        if rng.random() < e:   # detector MISSED this true dependency edge
            return True
    return False

def analyze_safety(mix, n_steps, e_grid, seed):
    rng = random.Random(seed * 7919 + 13)
    # generate steps once, evaluate all e on same steps for comparability
    steps = []
    for _ in range(n_steps):
        _n, calls = sample_step(mix, rng)
        steps.append((calls, true_edges(calls)))
    out = {}
    for e in e_grid:
        drng = random.Random(seed * 104729 + int(e*1e6) + 1)
        corrupted = 0; parallelizable_steps = 0
        for calls, edges in steps:
            # a step is "parallelized" if it has >1 call with any independence to exploit
            indep = independent_calls(calls, edges)
            if len(calls) > 1 and len(indep) >= 1:
                parallelizable_steps += 1
                if corrupted_under_detector(calls, edges, e, drng):
                    corrupted += 1
        out[e] = corrupted / parallelizable_steps if parallelizable_steps else 0.0
    return out

# ---------------- Metric C: heterogeneous-latency speedup ----------------
def hetero_speedup(mix, n_steps, seed):
    """Real tools have heterogeneous latency. Ideal-parallel wall-clock = sum over
    DAG levels of (max tool latency in that level). Serial = sum of all latencies.
    Latencies lognormal. Speedup = serial / parallel."""
    rng = random.Random(seed * 31 + 5)
    speeds = []
    for _ in range(n_steps):
        _n, calls = sample_step(mix, rng)
        edges = true_edges(calls)
        n = len(calls)
        # assign latency to each call (lognormal, median 1.0, sigma 0.6 -> realistic spread)
        lat = [math.exp(rng.gauss(0.0, 0.6)) for _ in range(n)]
        serial = sum(lat)
        # compute level (longest-path depth) of each node, group, take max per level
        level = [0]*n
        for j in range(n):
            for i in range(j):
                if (i,j) in edges:
                    level[j] = max(level[j], level[i]+1)
        from collections import defaultdict
        bylevel = defaultdict(list)
        for j in range(n):
            bylevel[level[j]].append(lat[j])
        parallel = sum(max(v) for v in bylevel.values())
        speeds.append(serial/parallel if parallel>0 else 1.0)
    return statistics.mean(speeds)

# ============================ RUN ============================
SEEDS = [0,1,2,3,4]
N_STEPS = 4000
E_GRID = [0.0, 0.01, 0.05, 0.10, 0.20]

# Mix grid: vary fan-out fraction (the parallelism-rich archetype) with the rest split.
# We define named mixes spanning pessimistic -> optimistic, plus a "balanced realistic" anchor.
def mk_mix(fanout, sequential, mixed, single):
    s = fanout+sequential+mixed+single
    return {"fanout":fanout/s, "sequential":sequential/s, "mixed":mixed/s, "single":single/s}

MIXES = {
    # name : (fanout, sequential, mixed, single)
    "pessimistic_seq_heavy": mk_mix(0.05, 0.55, 0.15, 0.25),
    "single_heavy":          mk_mix(0.10, 0.20, 0.15, 0.55),
    "balanced_realistic":    mk_mix(0.25, 0.30, 0.30, 0.15),
    "fanout_lean":           mk_mix(0.40, 0.20, 0.30, 0.10),
    "optimistic_fanout":     mk_mix(0.60, 0.10, 0.25, 0.05),
}

print("=== Metric A: f_indep vs mix (5 seeds) ===")
rowsA = []
for name, mix in MIXES.items():
    perseed = [analyze_mix(mix, N_STEPS, s) for s in SEEDS]
    agg = {k: statistics.mean(d[k] for d in perseed) for k in perseed[0]}
    sd_callwt = statistics.pstdev([d["f_indep_callwt"] for d in perseed])
    rowsA.append({"mix":name, "f_indep_callwt":round(agg["f_indep_callwt"],4),
                  "f_indep_callwt_sd":round(sd_callwt,4),
                  "f_indep_stepavg":round(agg["f_indep_stepavg"],4),
                  "mean_width":round(agg["mean_width"],3),
                  "mean_depth":round(agg["mean_depth"],3),
                  "mean_speedup_eqlat":round(agg["mean_speedup"],3),
                  "frac_multicall":round(agg["frac_multicall"],3)})
    print(f"  {name:24s} f_indep(callwt)={agg['f_indep_callwt']:.3f}±{sd_callwt:.3f}  "
          f"stepavg={agg['f_indep_stepavg']:.3f}  speedup_eqlat={agg['mean_speedup']:.2f}")

print("\n=== Metric B: f_wrong vs detector error (balanced_realistic + extremes) ===")
rowsB = []
for name in ["pessimistic_seq_heavy","balanced_realistic","optimistic_fanout"]:
    mix = MIXES[name]
    perseed = [analyze_safety(mix, N_STEPS, E_GRID, s) for s in SEEDS]
    for e in E_GRID:
        vals = [d[e] for d in perseed]
        rowsB.append({"mix":name, "detector_fn_rate":e,
                      "f_wrong_mean":round(statistics.mean(vals),4),
                      "f_wrong_sd":round(statistics.pstdev(vals),4)})
    line = "  ".join(f"e={e}:{statistics.mean([d[e] for d in perseed]):.3f}" for e in E_GRID)
    print(f"  {name:24s} {line}")

print("\n=== Metric C: heterogeneous-latency speedup vs mix (5 seeds) ===")
rowsC = []
for name, mix in MIXES.items():
    vals = [hetero_speedup(mix, N_STEPS, s) for s in SEEDS]
    eq = [analyze_mix(mix, N_STEPS, s)["mean_speedup"] for s in SEEDS]
    rowsC.append({"mix":name,
                  "speedup_eqlat":round(statistics.mean(eq),3),
                  "speedup_hetero":round(statistics.mean(vals),3),
                  "speedup_hetero_sd":round(statistics.pstdev(vals),3)})
    print(f"  {name:24s} eqlat={statistics.mean(eq):.2f}  hetero={statistics.mean(vals):.2f}")

# ---------------- write CSVs (trust on-disk, not stdout) ----------------
def write_csv(path, rows):
    with open(path,"w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    return path

write_csv(os.path.join(RES,"metricA_findep_vs_mix.csv"), rowsA)
write_csv(os.path.join(RES,"metricB_fwrong_vs_detector_error.csv"), rowsB)
write_csv(os.path.join(RES,"metricC_latency_headroom.csv"), rowsC)

# also dump the mix definitions for reproducibility
with open(os.path.join(RES,"mix_definitions.json"),"w") as f:
    json.dump(MIXES, f, indent=2)

print("\nWROTE CSVs to", RES)
print("DONE")


# ============================ METRIC A' (exploitable parallelism) ============================
def analyze_parallelism(mix, n_steps, seed):
    rng = random.Random(seed)
    multicall = 0; tot = 0
    indep_calls_mc = 0; tot_calls_mc = 0
    steps_width_ge2 = 0
    for _ in range(n_steps):
        tot += 1
        _n, calls = sample_step(mix, rng)
        edges = true_edges(calls)
        indep = independent_calls(calls, edges)
        if len(calls) > 1:
            multicall += 1
            tot_calls_mc += len(calls)
            indep_calls_mc += len(indep)
            if len(indep) >= 2:
                steps_width_ge2 += 1
    return {
        "frac_steps_width_ge2": steps_width_ge2/tot,
        "f_indep_among_multicall": indep_calls_mc/tot_calls_mc if tot_calls_mc else 0.0,
        "frac_multicall": multicall/tot,
    }

if __name__ == "__main__":
    print("\n=== Metric A' : exploitable parallelism ===")
    rowsAp = []
    for name, mix in MIXES.items():
        ps = [analyze_parallelism(mix, N_STEPS, s) for s in SEEDS]
        agg = {k: statistics.mean(d[k] for d in ps) for k in ps[0]}
        sd = statistics.pstdev([d["frac_steps_width_ge2"] for d in ps])
        rowsAp.append({"mix":name,
            "frac_steps_width_ge2":round(agg["frac_steps_width_ge2"],4),
            "frac_steps_width_ge2_sd":round(sd,4),
            "f_indep_among_multicall":round(agg["f_indep_among_multicall"],4),
            "frac_multicall":round(agg["frac_multicall"],4)})
        print(f"  {name:24s} steps_w>=2={agg['frac_steps_width_ge2']:.3f}  "
              f"f_indep|mc={agg['f_indep_among_multicall']:.3f}")
    write_csv(os.path.join(RES,"metricA2_exploitable_parallelism.csv"), rowsAp)
    print("wrote metricA2")
