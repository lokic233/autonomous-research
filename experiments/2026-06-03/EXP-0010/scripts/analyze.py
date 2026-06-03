#!/usr/bin/env python3
"""EXP-0010 analysis: Pareto + primary metric + oracle-vs-causal gap. stdlib-only."""
import csv, os, math, random
from collections import defaultdict

HERE=os.path.dirname(os.path.abspath(__file__))
RES=os.path.join(HERE,"..","results")
rows=list(csv.DictReader(open(os.path.join(RES,"sweep_all.csv"))))
for r in rows:
    r["success"]=float(r["success"]); r["mean_ctx"]=float(r["mean_ctx"])
    r["peak_ctx"]=float(r["peak_ctx"]); r["budget_frac"]=float(r["budget_frac"])
    r["nc_peak"]=float(r["nc_peak"]); r["seed"]=int(r["seed"]); r["ref_frac"]=float(r["ref_frac"])

def key(r): return (r["verbosity"],r["ref_density"],r["predict"],r["budget_frac"],r["seed"])

# group by (config,seed,budget) -> policy -> success
by=defaultdict(dict)
for r in rows: by[key(r)][r["policy"]]=r

def boot_ci(deltas, n=2000, seed=1):
    rng=random.Random(seed); m=len(deltas)
    if m==0: return (0,0,0)
    means=[]
    for _ in range(n):
        s=sum(deltas[rng.randrange(m)] for _ in range(m))/m
        means.append(s)
    means.sort()
    return (sum(deltas)/m, means[int(0.025*n)], means[int(0.975*n)])

# ---- 1. paired EC-vs-RT and EO-vs-EC success deltas, by regime ----
def agg(filt=None):
    ec_rt=[]; eo_rt=[]; eo_ec=[]; ec_nc=[]
    for k,pol in by.items():
        if filt and not filt(k): continue
        if not all(p in pol for p in ("NC","RT","EC","EO")): continue
        ec_rt.append(pol["EC"]["success"]-pol["RT"]["success"])
        eo_rt.append(pol["EO"]["success"]-pol["RT"]["success"])
        eo_ec.append(pol["EO"]["success"]-pol["EC"]["success"])
        ec_nc.append(pol["EC"]["success"]-pol["NC"]["success"])
    return ec_rt,eo_rt,eo_ec,ec_nc

print("="*90)
print("OVERALL paired success deltas (positive = arm beats RT / oracle beats causal)")
ec_rt,eo_rt,eo_ec,_=agg()
for name,d in [("EC - RT (causal beats truncation?)",ec_rt),
               ("EO - RT (oracle beats truncation)",eo_rt),
               ("EO - EC (ORACLE-CAUSAL GAP)",eo_ec)]:
    m,lo,hi=boot_ci(d)
    wins=sum(1 for x in d if x>0); n=len(d)
    print(f"  {name:42s} mean={m:+.4f}  CI=[{lo:+.4f},{hi:+.4f}]  wins {wins}/{n}")

# ---- 2. by predictability x density (the claim-favorable vs hostile cut) ----
print("="*90)
print("BY predictability x ref_density (mean success per policy; EC-RT delta; oracle gap)")
print(f"{'pred':5s} {'dens':5s} | {'NC':>6s} {'RT':>6s} {'EC':>6s} {'EO':>6s} | {'EC-RT':>7s} {'EO-EC':>7s} {'ECwin%':>7s}")
for pred in ["low","med","high"]:
  for dens in ["0.02","0.08","0.25"]:
    f=lambda k: k[2]==pred and k[1]==dens
    cells=[pol for k,pol in by.items() if f(k) and all(p in pol for p in ("NC","RT","EC","EO"))]
    if not cells: continue
    def mn(p): return sum(c[p]["success"] for c in cells)/len(cells)
    ecrt=[c["EC"]["success"]-c["RT"]["success"] for c in cells]
    eoec=[c["EO"]["success"]-c["EC"]["success"] for c in cells]
    ecwin=sum(1 for x in ecrt if x>0)/len(ecrt)*100
    print(f"{pred:5s} {dens:5s} | {mn('NC'):6.3f} {mn('RT'):6.3f} {mn('EC'):6.3f} {mn('EO'):6.3f} | "
          f"{sum(ecrt)/len(ecrt):+7.4f} {sum(eoec)/len(eoec):+7.4f} {ecwin:6.1f}%")

# ---- 3. by budget_frac (context-length axis -> Pareto) ----
print("="*90)
print("PARETO: success per policy at each budget fraction (mean over all configs/seeds)")
print(f"{'budget':>7s} | {'NC':>6s} {'RT':>6s} {'EC':>6s} {'EO':>6s} | {'EC-RT':>7s} {'EO-EC':>7s}")
for bf in ["0.25","0.5","0.75"]:
    cells=[pol for k,pol in by.items() if str(k[3])==bf and all(p in pol for p in ("NC","RT","EC","EO"))]
    def mn(p): return sum(c[p]["success"] for c in cells)/len(cells)
    ecrt=[c["EC"]["success"]-c["RT"]["success"] for c in cells]
    eoec=[c["EO"]["success"]-c["EC"]["success"] for c in cells]
    print(f"{bf:>7s} | {mn('NC'):6.3f} {mn('RT'):6.3f} {mn('EC'):6.3f} {mn('EO'):6.3f} | "
          f"{sum(ecrt)/len(ecrt):+7.4f} {sum(eoec)/len(eoec):+7.4f}")

# ---- 4. PRIMARY METRIC: tokens saved vs NC at fixed success-loss budget ----
# For each (config,seed), NC success ~ ceiling. Find min budget_frac per policy that keeps
# success >= 0.95 * NC_success. Lower budget achieving the bar = more tokens saved.
print("="*90)
print("PRIMARY: min budget_frac achieving success >= 0.95*NC_success (lower=more saved)")
print("(per config/seed; report fraction of cells where EC needs <= RT budget, and the gap)")
# group by config+seed across budgets
cfgseed=defaultdict(dict)  # (verb,dens,pred,seed) -> bf -> {pol:succ}
for r in rows:
    ck=(r["verbosity"],r["ref_density"],r["predict"],r["seed"])
    cfgseed[ck].setdefault(r["budget_frac"],{})[r["policy"]]=r["success"]
def min_budget(succ_by_bf, pol, target):
    ok=[bf for bf,d in succ_by_bf.items() if d.get(pol,0)>=target]
    return min(ok) if ok else 99.0
rt_better=ec_better=tie=0; ec_b=[]; rt_b=[]; eo_b=[]
for ck,sbf in cfgseed.items():
    nc_succ=max(d.get("NC",0) for d in sbf.values())
    target=0.95*nc_succ
    bRT=min_budget(sbf,"RT",target); bEC=min_budget(sbf,"EC",target); bEO=min_budget(sbf,"EO",target)
    rt_b.append(bRT); ec_b.append(bEC); eo_b.append(bEO)
    if bEC<bRT: ec_better+=1
    elif bEC>bRT: rt_better+=1
    else: tie+=1
n=len(cfgseed)
def mean(x): return sum(x)/len(x)
print(f"  cells={n}  EC needs LOWER budget than RT: {ec_better} ({ec_better/n*100:.1f}%)  "
      f"tie: {tie}  RT better: {rt_better}")
print(f"  mean min-budget-frac: RT={mean(rt_b):.3f}  EC={mean(ec_b):.3f}  EO={mean(eo_b):.3f}  "
      f"(EC-EO oracle gap in budget = {mean(ec_b)-mean(eo_b):+.3f})")

# ---- 5. claim-favorable subset (sparse & high-pred) vs hostile (dense & low-pred) ----
print("="*90)
print("REGIME EXTREMES (primary success-loss-budget view):")
for label,f in [("FAVORABLE sparse(0.02)+high-pred", lambda k:k[1]=='0.02' and k[2]=='high'),
                ("HOSTILE dense(0.25)+low-pred",     lambda k:k[1]=='0.25' and k[2]=='low')]:
    cells=[pol for k,pol in by.items() if f(k) and all(p in pol for p in ("NC","RT","EC","EO"))]
    def mn(p): return sum(c[p]["success"] for c in cells)/len(cells)
    ecrt=[c["EC"]["success"]-c["RT"]["success"] for c in cells]
    eoec=[c["EO"]["success"]-c["EC"]["success"] for c in cells]
    m,lo,hi=boot_ci(ecrt)
    mg,glo,ghi=boot_ci(eoec)
    print(f"  {label}: NC={mn('NC'):.3f} RT={mn('RT'):.3f} EC={mn('EC'):.3f} EO={mn('EO'):.3f}")
    print(f"      EC-RT mean={m:+.4f} CI=[{lo:+.4f},{hi:+.4f}]   ORACLE GAP EO-EC mean={mg:+.4f} CI=[{glo:+.4f},{ghi:+.4f}]")
