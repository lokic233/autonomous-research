import csv, statistics, sys, os
R=os.path.join(os.path.dirname(__file__),"..","results")+"/"
def load(f):
    rows=list(csv.DictReader(open(R+f)))
    for r in rows:
        for k in r:
            try: r[k]=float(r[k])
            except: pass
    return rows
mf=load("matched_fairness.csv"); unb=load("unbounded.csv"); allr=load("sweep_all.csv")
def sav(r): return (r["fcfs_recomp_mean"]-r["pfa_recomp_mean"])/r["fcfs_recomp_mean"]*100 if r["fcfs_recomp_mean"]>0 else 0
print(f"TOTAL matched cells={len(mf)} CI<0 wins={len([r for r in mf if r['ci_hi']<0])}")
print("\n=== MATCHED FAIRNESS by cache regime ===")
print(f"{'regime':6}{'cells':>6}{'CI<0':>6}{'meanSav%':>9}{'fairRatio':>10}{'meanW':>7}{'fcfsHit':>8}{'pfaHit':>8}")
for rg in ["one","few","all"]:
    rs=[r for r in mf if r["regime"]==rg]
    if not rs: continue
    wins=[r for r in rs if r["ci_hi"]<0]
    print(f"{rg:6}{len(rs):>6}{len(wins):>6}{statistics.mean([sav(r) for r in rs]):>8.1f}%{statistics.mean([r['fair_ratio'] for r in rs]):>10.3f}{statistics.mean([r['W'] for r in rs]):>7.1f}{statistics.mean([r['fcfs_hit'] for r in rs]):>8.3f}{statistics.mean([r['pfa_hit'] for r in rs]):>8.3f}")
print("\n=== regime x load ===")
for rg in ["one","few","all"]:
    for ln in ["light","heavy"]:
        rs=[r for r in mf if r["regime"]==rg and r["lname"]==ln]
        if not rs: continue
        wins=[r for r in rs if r["ci_hi"]<0]
        print(f"{rg:5}{ln:7} wins={len(wins)}/{len(rs)} sav={statistics.mean([sav(r) for r in rs]):5.1f}%")
print("\n=== UNBOUNDED W (fairness cost of pure greed) ===")
for rg in ["one","few","all"]:
    rs=[r for r in unb if r["regime"]==rg]
    if not rs: continue
    print(f"{rg:5} sav={statistics.mean([sav(r) for r in rs]):5.1f}% fairRatio={statistics.mean([r['fair_ratio'] for r in rs]):.2f}")
print("\n=== top one-regime matched wins ===")
for r in sorted([r for r in mf if r["regime"]=="one"],key=sav,reverse=True)[:6]:
    print(f"K={int(r['K'])} skew={r['skew']} {r['lname']} B={int(r['B'])} W={int(r['W'])} sav={sav(r):5.1f}% CI=[{r['ci_lo']:.0f},{r['ci_hi']:.0f}] fair={r['fair_ratio']:.3f} hit {r['fcfs_hit']:.2f}->{r['pfa_hit']:.2f}")
