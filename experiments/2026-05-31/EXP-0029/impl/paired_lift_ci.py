#!/usr/bin/env python3
"""EXP-0029 addendum: PAIRED bootstrap CI on the LOSO context-model lift over modal baseline,
per gate, LEAK-FREE features. This is the rigorous significance test for the FINE layer:
resample the (correct_base, correct_ctx) PAIRS and bootstrap the mean difference. CI excluding 0
= a genuine out-of-sample, leak-free context signal."""
import importlib.util, os, glob, random, math
from collections import defaultdict, Counter
spec=importlib.util.spec_from_file_location("rt", os.path.join(os.path.dirname(os.path.abspath(__file__)),"reframe_retest.py"))
rt=importlib.util.module_from_spec(spec); spec.loader.exec_module(rt)
random.seed(20260531); B=4000
rows,_,_=rt.load_rows()
LEAKFREE={"kw","prior","cls"}
print("PAIRED LOSO lift bootstrap (ctx - modal), leak-free features {cls,kw,prior}:")
csv=[]
for g in ["REDIRECTABLE","GRANT_REQUIRED","TRANSIENT"]:
    grp=[r for r in rows if r["gate"]==g]; n=len(grp)
    if n<10: continue
    # per-row correctness for base (LOSO modal) and ctx (LOSO NB)
    base_ok=[]; ctx_ok=[]
    for r in grp:
        train=[x for x in grp if x["sid"]!=r["sid"]]
        c=Counter(x["next"] for x in train); bp=c.most_common(1)[0][0] if c else None
        cp=rt.predict_oos(train, r, LEAKFREE)
        base_ok.append(1 if bp==r["next"] else 0)
        ctx_ok.append(1 if cp==r["next"] else 0)
    diffs=[c-b for c,b in zip(ctx_ok,base_ok)]
    obs=sum(diffs)/n
    stats=[]
    for _ in range(B):
        s=[diffs[random.randrange(n)] for _ in range(n)]
        stats.append(sum(s)/n)
    stats.sort(); lo=stats[int(0.025*B)]; hi=stats[int(0.975*B)]
    p_le0 = sum(1 for x in stats if x<=0)/B
    sig = lo>0
    print(f"  {g:15s} n={n:4d} lift={obs:+.3f} paired-boot95%[{lo:+.3f},{hi:+.3f}] P(lift<=0)={p_le0:.3f} {'SIGNIFICANT' if sig else 'n.s.'}")
    csv.append((g,n,obs,lo,hi,p_le0,sig))
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","experiment_result","paired_lift_ci.csv")
with open(out,"w") as f:
    f.write("gate,n,lift,paired_lo,paired_hi,P_lift_le0,significant\n")
    for g,n,o,lo,hi,p,s in csv: f.write(f"{g},{n},{o:.4f},{lo:.4f},{hi:.4f},{p:.4f},{s}\n")
print("CSV:",out)
