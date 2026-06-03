import os, statistics as st, math as m, csv
D="/Users/dengcchi/autonomous-research-v3/experiments/2026-06-03/EXP-0050"
src=open(os.path.join(D,"run.py")).read().split("# ============ MAIN SWEEP ============")[0]
g={"__file__":os.path.join(D,"run.py")}; exec(src,g)
run_cell=g["run_cell"]
def msci(xs):
    mn=st.mean(xs); se=(st.pstdev(xs)/m.sqrt(len(xs))) if len(xs)>1 else 0; return mn,1.96*se
def zdiff(x,y):
    mx,my=st.mean(x),st.mean(y); sx=st.pstdev(x)/m.sqrt(len(x)); sy=st.pstdev(y)/m.sqrt(len(y))
    se=m.sqrt(sx*sx+sy*sy) or 1e-9; return (mx-my)/se,mx-my
A_PC,B_PC=0.50,0.28
A_lo=run_cell(A_PC,0.95,0.05,0.0,1.0,base_seed=37)
A_hi=run_cell(A_PC,0.95,0.05,1.0,1.0,base_seed=37)
B_lo=run_cell(B_PC,0.05,0.95,0.0,1.0,base_seed=137)
B_hi=run_cell(B_PC,0.05,0.95,1.0,1.0,base_seed=137)
z_lo,d_lo=zdiff(A_lo,B_lo); z_hi,d_hi=zdiff(A_hi,B_hi)
rows=[]
for nm,xs in [("A_lo",A_lo),("A_hi",A_hi),("B_lo",B_lo),("B_hi",B_hi)]:
    mn,c=msci(xs); rows.append(dict(branch="inversion",model=nm,acc=round(mn,4),ci95=round(c,4)))
rows.append(dict(branch="inversion",model="A-B@r_low",acc=round(d_lo,4),ci95=round(abs(z_lo),2)))
rows.append(dict(branch="inversion",model="A-B@r_high",acc=round(d_hi,4),ci95=round(abs(z_hi),2)))
with open(os.path.join(D,"results","inversion.csv"),"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["branch","model","acc","ci95"]); w.writeheader(); w.writerows(rows)
print(f"A_pc={A_PC} B_pc={B_PC} SC=SW=6, M_INC=3, DOM_FRAC=0.7, K=20, N=60, SEEDS=30, q=1.0")
print(f"r_low=0.0 : A={st.mean(A_lo):.4f} B={st.mean(B_lo):.4f}  A-B={d_lo:+.4f}  |z|={abs(z_lo):.1f}  -> A BELOW B")
print(f"r_high=1.0: A={st.mean(A_hi):.4f} B={st.mean(B_hi):.4f}  A-B={d_hi:+.4f}  |z|={abs(z_hi):.1f}  -> A ABOVE B")
print("INVERSION CONSTRUCTED:", (d_lo<0 and d_hi>0 and abs(z_lo)>2 and abs(z_hi)>2))
print("wrote inversion.csv")
