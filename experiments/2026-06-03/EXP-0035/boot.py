#!/usr/bin/env python3
"""Fast pooled bootstrap CIs on the two key deltas, per (K,rho,sigma).
Subsample pooled cell to fixed N=4000 for tractable serial bootstrap (B=400)."""
import random, math, csv, os
import importlib.util
spec=importlib.util.spec_from_file_location("re_",os.path.join(os.path.dirname(os.path.abspath(__file__)),"run_exp.py"))
m=importlib.util.module_from_spec(spec)
# we only need run_cell/auc/standardize; import without running main
import sys
ART=os.path.dirname(os.path.abspath(__file__)); RES=os.path.join(ART,"results")

def sigmoid(x):
    if x<-60: return 0.0
    if x>60: return 1.0
    return 1.0/(1.0+math.exp(-x))
def auc(scores,labels):
    pos=[s for s,l in zip(scores,labels) if l==1]; neg=[s for s,l in zip(scores,labels) if l==0]
    if not pos or not neg: return 0.5
    paired=sorted(zip(scores,labels),key=lambda x:x[0]); ranks=[0.0]*len(paired); i=0
    while i<len(paired):
        j=i
        while j+1<len(paired) and paired[j+1][0]==paired[i][0]: j+=1
        r=(i+j)/2.0+1
        for k in range(i,j+1): ranks[k]=r
        i=j+1
    sp=sum(rk for rk,(s,l) in zip(ranks,paired) if l==1); npos=len(pos); nneg=len(neg)
    return (sp-npos*(npos+1)/2.0)/(npos*nneg)
def standardize(xs):
    mu=sum(xs)/len(xs); v=sum((x-mu)**2 for x in xs)/len(xs); sd=math.sqrt(v) if v>0 else 1.0
    return [(x-mu)/sd for x in xs]
VOCAB=200
def make_tool_schema(rng,topic,spread):
    center=int(topic*(VOCAB-1)); n=rng.randint(8,14); toks=set()
    for _ in range(n):
        toks.add((center+int(rng.gauss(0,spread)))%VOCAB)
    for _ in range(rng.randint(1,3)): toks.add(rng.randint(0,VOCAB-1))
    return toks
def cos_bag(a,b):
    if not a or not b: return 0.0
    return len(a&b)/math.sqrt(len(a)*len(b))
def run_cell(seed,K,rho,sigma_lp,N=4000):
    rng=random.Random(seed*1000+K*17+int(rho*100)+int(sigma_lp*100)); rows=[]
    b0,bc,bd=-1.2,2.6,1.8
    for i in range(N):
        d=rng.random(); base=rng.random(); c=max(0.0,min(1.0,rho*d+(1-rho)*base))
        t0=rng.random(); gap=(1.0-c)*0.5+rng.uniform(-0.03,0.03); sign=1 if rng.random()<0.5 else -1
        t_dist=max(0.0,min(1.0,t0+sign*gap)); topics=[t0,t_dist]+[rng.random() for _ in range(K-2)]
        schemas=[make_tool_schema(rng,tp,6.0) for tp in topics]
        sims=[cos_bag(schemas[a],schemas[b]) for a in range(K) for b in range(a+1,K)]
        max_sim=max(sims); mean_sim=sum(sims)/len(sims)
        p_err=sigmoid(b0+bc*(c-0.5)+bd*(d-0.5)); y=1 if rng.random()<p_err else 0
        lp=-(0.9*c+0.7*d)+rng.gauss(0,sigma_lp); diff_pred=d+rng.gauss(0,0.25)
        rows.append((y,max_sim,mean_sim,lp,diff_pred,c,d,p_err))
    return rows

def stat_delta_combo(samp):
    y=[r[0] for r in samp]; lp=[r[3] for r in samp]; maxs=[r[1] for r in samp]
    combo=[a+b for a,b in zip(standardize([-x for x in lp]),standardize(maxs))]
    return auc(combo,y)-auc([-x for x in lp],y)
def stat_delta_sd(samp):
    y=[r[0] for r in samp]; maxs=[r[1] for r in samp]; diffp=[r[4] for r in samp]
    return auc(maxs,y)-auc(diffp,y)
def boot(rows,fn,B=400,seed=0):
    rng=random.Random(seed); n=len(rows); vals=[]
    for _ in range(B):
        samp=[rows[rng.randrange(n)] for _ in range(n)]; vals.append(fn(samp))
    vals.sort(); return vals[int(0.025*B)],vals[int(0.975*B)]

Ks=[3,6,12]; rhos=[0.0,0.5]; sigmas=[0.5,1.5]; seeds=[1,2,3,4,5]
out=open(os.path.join(RES,"bootstrap.csv"),"w",newline=""); w=csv.writer(out)
w.writerow(["K","rho","sigma_lp","N","auc_schema_max","auc_diff","auc_logprob","auc_combo","auc_oracle",
            "delta_combo_minus_logprob","ci_lo","ci_hi","delta_schema_minus_diff","ci_lo2","ci_hi2"])
for K in Ks:
  for rho in rhos:
    for sig in sigmas:
      rows=[]
      for sd in seeds: rows.extend(run_cell(sd,K,rho,sig,N=800))  # 800*5=4000 pooled
      y=[r[0] for r in rows]; lp=[r[3] for r in rows]; maxs=[r[1] for r in rows]
      diffp=[r[4] for r in rows]; c=[r[5] for r in rows]
      a_smax=auc(maxs,y); a_diff=auc(diffp,y); a_lp=auc([-x for x in lp],y)
      combo=[a+b for a,b in zip(standardize([-x for x in lp]),standardize(maxs))]; a_combo=auc(combo,y)
      a_orac=auc(c,y); d_combo=a_combo-a_lp; d_sd=a_smax-a_diff
      lo,hi=boot(rows,stat_delta_combo,B=400,seed=K+int(rho*10))
      lo2,hi2=boot(rows,stat_delta_sd,B=400,seed=K+99)
      w.writerow([K,rho,sig,len(rows),f"{a_smax:.4f}",f"{a_diff:.4f}",f"{a_lp:.4f}",f"{a_combo:.4f}",f"{a_orac:.4f}",
                  f"{d_combo:.4f}",f"{lo:.4f}",f"{hi:.4f}",f"{d_sd:.4f}",f"{lo2:.4f}",f"{hi2:.4f}"])
      out.flush()
out.close(); print("BOOT DONE")
