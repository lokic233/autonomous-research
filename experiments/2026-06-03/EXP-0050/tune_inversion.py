#!/usr/bin/env python3
"""Search for (A,B) params giving a SIGNIFICANT ranking inversion across recall."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# import the machinery from run.py without re-running its __main__ sweep
import importlib.util
spec=importlib.util.spec_from_file_location("runmod", os.path.join(os.path.dirname(os.path.abspath(__file__)),"run.py"))
# run.py executes sweeps at import -> instead inline the needed funcs by exec of the top portion.
# Simpler: re-define minimal here by reading functions. We'll just re-implement via exec of run.py up to MAIN.
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"run.py")).read()
src=src.split("# ============ MAIN SWEEP ============")[0]
g={"__file__": os.path.join(os.path.dirname(os.path.abspath("x")),"run.py")}
exec(src,g)
run_cell=g["run_cell"]
import statistics as st, math as m
def zdiff(x,y):
    mx,my=st.mean(x),st.mean(y); sx=st.pstdev(x)/m.sqrt(len(x)); sy=st.pstdev(y)/m.sqrt(len(y))
    se=m.sqrt(sx*sx+sy*sy) or 1e-9; return (mx-my)/se, mx-my
# A = correct-fragmented (h_C high, h_W low) -> helped by recall.
# B = errors-fragmented (h_C low, h_W high) -> hurt by recall.
# We want A<B at r=0, A>B at r=1, both significant.
best=None
for a_pc in [0.45,0.50,0.55,0.60]:
    for b_pc in [0.30,0.34,0.38,0.42]:
        A_lo=run_cell(a_pc,0.95,0.05,0.0,1.0,base_seed=37)
        A_hi=run_cell(a_pc,0.95,0.05,1.0,1.0,base_seed=37)
        B_lo=run_cell(b_pc,0.05,0.95,0.0,1.0,base_seed=137)
        B_hi=run_cell(b_pc,0.05,0.95,1.0,1.0,base_seed=137)
        z_lo,d_lo=zdiff(A_lo,B_lo); z_hi,d_hi=zdiff(A_hi,B_hi)
        inv=(d_lo<0 and d_hi>0 and abs(z_lo)>1.96 and abs(z_hi)>1.96)
        tag="INVERT" if inv else ""
        print(f"a_pc={a_pc} b_pc={b_pc} | r0: A={st.mean(A_lo):.3f} B={st.mean(B_lo):.3f} d={d_lo:+.3f}(z{z_lo:+.0f}) | r1: A={st.mean(A_hi):.3f} B={st.mean(B_hi):.3f} d={d_hi:+.3f}(z{z_hi:+.0f}) {tag}")
        if inv and (best is None or min(abs(z_lo),abs(z_hi))>best[0]):
            best=(min(abs(z_lo),abs(z_hi)),a_pc,b_pc)
print("BEST:",best)
