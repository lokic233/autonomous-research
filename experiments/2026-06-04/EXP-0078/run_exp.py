#!/usr/bin/env python3
"""EXP-0078 / CLAIM-0065 — shard-cardinality x shuffle-buffer coupling.
Real interleave_datasets -> .shuffle path. Measures per-batch rare-source (B) fraction.
"""
import os, sys, json, time, math, shutil
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import datasets
from datasets import load_dataset, interleave_datasets

print(f"datasets={datasets.__version__} pyarrow={pa.__version__} numpy={np.__version__}", flush=True)

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
RES  = os.path.join(BASE, "results")
os.makedirs(RES, exist_ok=True)

# ---- corpus sizes ----
# A=90%, B=10%. Want ~2000 batches*256 = 512k consumed before A exhausts (all_exhausted cycles B).
N_A = 600_000          # common source A
N_B = 66_667           # rare source B  -> B/(A+B) = 0.10
A_SHARDS = 64
B_SHARD_COUNTS = [1, 4, 16, 64]
BATCH = 256
N_STEPS = 2000
BUFFERS = [1000, 10000]
SEED = 0

def write_parquet_shards(out_dir, n_rows, n_shards, source_label):
    """Write n_rows examples for one source, split contiguously into n_shards parquet files."""
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    files = []
    # contiguous split (the realistic default: rows 0..k in shard0, etc.)
    bounds = np.linspace(0, n_rows, n_shards + 1).astype(int)
    for s in range(n_shards):
        lo, hi = bounds[s], bounds[s+1]
        idx = np.arange(lo, hi, dtype=np.int64)
        tbl = pa.table({
            "source": pa.array([source_label] * len(idx)),
            "idx": pa.array(idx),
        })
        fp = os.path.join(out_dir, f"shard-{s:04d}.parquet")
        pq.write_table(tbl, fp)
        files.append(fp)
    return files

def build_data():
    print("Building Parquet shards...", flush=True)
    a_files = write_parquet_shards(os.path.join(DATA, "A_64"), N_A, A_SHARDS, "A")
    b_files = {}
    for bc in B_SHARD_COUNTS:
        b_files[bc] = write_parquet_shards(os.path.join(DATA, f"B_{bc}"), N_B, bc, "B")
    print(f"  A: {len(a_files)} shards ({N_A} rows); B: { {k:len(v) for k,v in b_files.items()} }", flush=True)
    return a_files, b_files

def run_config(a_files, b_files_for_bc, b_shard_count, buffer_size):
    # Load each source as a streaming IterableDataset over its parquet shards
    dsA = load_dataset("parquet", data_files=a_files, split="train", streaming=True)
    dsB = load_dataset("parquet", data_files=b_files_for_bc, split="train", streaming=True)
    inter = interleave_datasets(
        [dsA, dsB],
        probabilities=[0.9, 0.1],
        seed=SEED,
        stopping_strategy="all_exhausted",
    )
    shuf = inter.shuffle(seed=SEED, buffer_size=buffer_size)

    b_fracs = []           # per-batch B fraction
    b_counts = []          # per-batch B count
    it = iter(shuf)
    for step in range(N_STEPS):
        cnt_b = 0
        n = 0
        try:
            for _ in range(BATCH):
                ex = next(it)
                if ex["source"] == "B":
                    cnt_b += 1
                n += 1
        except StopIteration:
            if n == 0:
                break
        if n == 0:
            break
        b_counts.append(cnt_b)
        b_fracs.append(cnt_b / n)
    b_fracs = np.array(b_fracs, dtype=float)
    b_counts = np.array(b_counts, dtype=int)

    # metrics
    # (a) max consecutive batches with ZERO B
    max_zero_run = 0
    cur = 0
    for c in b_counts:
        if c == 0:
            cur += 1
            max_zero_run = max(max_zero_run, cur)
        else:
            cur = 0
    # (b) std-dev of per-batch B-fraction
    std_frac = float(b_fracs.std()) if len(b_fracs) else float("nan")
    mean_frac = float(b_fracs.mean()) if len(b_fracs) else float("nan")
    # sliding window 50-batch realized fraction range
    win = 50
    if len(b_fracs) >= win:
        sw = np.convolve(b_fracs, np.ones(win)/win, mode="valid")
        sw_min, sw_max = float(sw.min()), float(sw.max())
    else:
        sw_min = sw_max = float("nan")
    # zero-fraction of batches
    zero_batch_frac = float((b_counts == 0).mean()) if len(b_counts) else float("nan")
    return {
        "b_shard_count": b_shard_count,
        "buffer_size": buffer_size,
        "n_batches": len(b_counts),
        "max_zero_B_run": int(max_zero_run),
        "frac_batches_zero_B": zero_batch_frac,
        "mean_b_fraction": mean_frac,
        "std_b_fraction": std_frac,
        "sliding50_min_frac": sw_min,
        "sliding50_max_frac": sw_max,
        "b_fracs": b_fracs.tolist(),
        "b_counts": b_counts.tolist(),
    }

def main():
    t0 = time.time()
    a_files, b_files = build_data()
    bernoulli_sd = math.sqrt(256*0.1*0.9)/256  # 0.01875
    print(f"Bernoulli null per-batch-fraction SD = {bernoulli_sd:.5f}", flush=True)

    rows = []
    series = {}
    for buf in BUFFERS:
        for bc in B_SHARD_COUNTS:
            t1 = time.time()
            r = run_config(a_files, b_files[bc], bc, buf)
            dt = time.time() - t1
            series[f"B{bc}_N{buf}"] = {"b_fracs": r.pop("b_fracs"), "b_counts": r.pop("b_counts")}
            r["std_over_bernoulli"] = r["std_b_fraction"]/bernoulli_sd
            r["wall_s"] = round(dt,1)
            rows.append(r)
            print(f"  B-shards={bc:>2} N={buf:>5}: batches={r['n_batches']} "
                  f"maxZeroBrun={r['max_zero_B_run']} fracZeroBatch={r['frac_batches_zero_B']:.3f} "
                  f"meanFrac={r['mean_b_fraction']:.4f} stdFrac={r['std_b_fraction']:.5f} "
                  f"(={r['std_over_bernoulli']:.2f}x null) "
                  f"sw50=[{r['sliding50_min_frac']:.3f},{r['sliding50_max_frac']:.3f}] {dt:.1f}s", flush=True)

    # write results json + CSVs
    out = {"versions": {"datasets": datasets.__version__, "pyarrow": pa.__version__, "numpy": np.__version__},
           "bernoulli_sd": bernoulli_sd, "config": {"N_A":N_A,"N_B":N_B,"A_SHARDS":A_SHARDS,
           "B_SHARD_COUNTS":B_SHARD_COUNTS,"BATCH":BATCH,"N_STEPS":N_STEPS,"BUFFERS":BUFFERS,"SEED":SEED},
           "rows": rows}
    with open(os.path.join(RES, "metrics.json"), "w") as f:
        json.dump(out, f, indent=2)
    # per-config CSV of b_fraction series
    for k, v in series.items():
        fp = os.path.join(RES, f"series_{k}.csv")
        with open(fp, "w") as f:
            f.write("step,b_count,b_fraction\n")
            for i,(c,fr) in enumerate(zip(v["b_counts"], v["b_fracs"])):
                f.write(f"{i},{c},{fr}\n")
    # summary table CSV
    with open(os.path.join(RES, "summary_table.csv"), "w") as f:
        f.write("buffer_size,b_shard_count,n_batches,max_zero_B_run,frac_batches_zero_B,mean_b_fraction,std_b_fraction,std_over_bernoulli,sliding50_min,sliding50_max\n")
        for r in rows:
            f.write(f"{r['buffer_size']},{r['b_shard_count']},{r['n_batches']},{r['max_zero_B_run']},"
                    f"{r['frac_batches_zero_B']:.4f},{r['mean_b_fraction']:.5f},{r['std_b_fraction']:.6f},"
                    f"{r['std_over_bernoulli']:.3f},{r['sliding50_min_frac']:.4f},{r['sliding50_max_frac']:.4f}\n")
    print(f"DONE in {time.time()-t0:.1f}s. Results in {RES}", flush=True)

if __name__ == "__main__":
    main()
