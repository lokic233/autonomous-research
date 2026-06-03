#!/usr/bin/env python3
"""EXP-0010 sweep driver. SERIAL, stdlib-only. Writes CSVs to ../results/."""
import sys, os, csv, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import gen_trace2, simulate

VERBOSITY = [64,256,1024]
REF_DENSITY = [0.02,0.08,0.25]
PREDICT = ["low","med","high"]
BUDGET_FRAC = [0.25,0.5,0.75]
SEEDS = list(range(8))
POLICIES = ["NC","RT","EC","EO"]

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","results")
os.makedirs(OUT, exist_ok=True)

t0=time.time()
rows=[]
n_cfg=0
for verb in VERBOSITY:
  for dens in REF_DENSITY:
    for pred in PREDICT:
      for seed in SEEDS:
        # build ONE trace per (verb,dens,pred,seed); all policies replay the SAME trace.
        spans_by_turn, refs, all_spans, total = gen_trace2(seed, verb, dens, pred)
        # NC peak (no budget) determines budget fractions for THIS trace
        nc_mean, nc_peak, nc_succ, nc_dem = simulate(spans_by_turn, refs, all_spans, total, "NC", 10**12)
        # realized distinct-referenced fraction (sanity on sparsity)
        distinct_ref = len(set(s for r in refs.values() for s in r))
        ref_frac = distinct_ref/max(1,len(all_spans))
        for bf in BUDGET_FRAC:
          budget = nc_peak*bf
          for pol in POLICIES:
            # NC ignores budget; record once per bf for paired comparison
            if pol=="NC":
              mc,pk,sc,dm = nc_mean, nc_peak, nc_succ, nc_dem
            else:
              # IMPORTANT: re-gen trace so ref_count/seen state is fresh per policy run.
              sbt2, refs2, all2, tot2 = gen_trace2(seed, verb, dens, pred)
              mc,pk,sc,dm = simulate(sbt2, refs2, all2, tot2, pol, budget)
            rows.append(dict(verbosity=verb, ref_density=dens, predict=pred, seed=seed,
                             budget_frac=bf, policy=pol, mean_ctx=round(mc,2),
                             peak_ctx=pk, success=round(sc,5), demands=dm,
                             nc_peak=nc_peak, ref_frac=round(ref_frac,4),
                             n_spans=len(all_spans)))
        n_cfg+=1
        if n_cfg % 20 == 0:
          sys.stderr.write(f"  {n_cfg} configs, {time.time()-t0:.1f}s\n"); sys.stderr.flush()

with open(os.path.join(OUT,"sweep_all.csv"),"w",newline="") as f:
  wri=csv.DictWriter(f, fieldnames=list(rows[0].keys())); wri.writeheader(); wri.writerows(rows)

sys.stderr.write(f"DONE {len(rows)} rows, {n_cfg} configs, {time.time()-t0:.1f}s -> results/sweep_all.csv\n")
print(f"WROTE {len(rows)} rows")
