"""EXP-0046 honest final sweep: report penalty, completion-rate, runaway-rate.
Reports a CAPPED-waste penalty AND a completion-rate metric so the cap-artifact is transparent."""
import random, math, csv, statistics, os, time, hashlib
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"results")
os.makedirs(OUT,exist_ok=True)
MASTER=20260603
CAP=50000  # honest, documented re-execution budget; rollouts exceeding CAP = "did not complete (DNC)"

def sim(seed,alpha,c,shape,base_w,k,policy,fpr,fnr,sd,ov):
    rng=random.Random(seed); progress=0; onset=None; wasted=0; saved=set()
    det=random.Random(seed^0x9E3779B1); g=0
    while progress<200:
        if wasted>CAP: return wasted,1   # DNC (did-not-complete within budget)
        g+=1
        if g>2000000: return wasted,1
        mark=(progress//c)*c
        if progress>0 and progress%c==0 and mark not in saved: saved.add(mark); wasted+=2
        if onset is None: on=True;t=0
        elif progress<onset: on=True;t=0
        else: on=False;t=progress-onset
        if on:
            if onset is None and rng.random()<0.01: onset=progress
            fh=0.002
        else:
            fh=min(0.6,(0.002+alpha*t) if shape=='linear' else (0.002+base_w*(t**(k-1))))
        if rng.random()>=fh: progress+=1; continue
        fp=progress; last=(fp//c)*c
        if policy=='A': r=last
        elif policy=='B1':
            if det.random()<fnr or onset is None: r=last
            else:
                if det.random()<fpr: r=max(0,onset-random.Random(seed^fp).randint(2*c,4*c))
                else: r=max(0,onset+int(round(det.gauss(0,sd))))
                r=(r//c)*c
        else: r=max(0,last-ov*c)
        wasted+=(fp-r); progress=r
        if onset is not None and r<onset: onset=None
        saved={m for m in saved if m<=r}
    return wasted,0

def cell(alpha,c,shape,base_w,k,R,pol,fpr,fnr,sd,ov):
    h=hashlib.sha256(repr((alpha,c,shape,base_w,k,pol,fpr,fnr)).encode()).hexdigest()
    base=(MASTER+int(h[:8],16))%(2**31)
    wa=[];da=0;wb=[];db=0
    for i in range(R):
        s=base+i
        w,d=sim(s,alpha,c,shape,base_w,k,'A',0,0,0,0); wa.append(w); da+=d
        bf,bn=(fpr,fnr) if pol=='B1' else (0,0)
        w,d=sim(s,alpha,c,shape,base_w,k,pol,bf,bn,sd,ov); wb.append(w); db+=d
    ma=statistics.fmean(wa); mb=statistics.fmean(wb)
    pen=(ma-mb)/mb if mb>0 else 0.0
    rb=random.Random(base^0xABCDEF); boots=[]
    for _ in range(300):
        idx=[rb.randrange(R) for _ in range(R)]
        x=statistics.fmean([wa[j] for j in idx]); y=statistics.fmean([wb[j] for j in idx])
        boots.append((x-y)/y if y>0 else 0.0)
    boots.sort(); lo=boots[int(.025*len(boots))]; hi=boots[int(.975*len(boots))]
    return dict(alpha=alpha,c=c,shape=shape,base_w=base_w,k=k,policyB=pol,fpr=fpr,fnr=fnr,sd=sd,ov=ov,R=R,
        mean_A=ma,mean_B=mb,penalty=pen,ci_lo=lo,ci_hi=hi,dnc_A=da/R,dnc_B=db/R)

def main():
    t0=time.time(); R=4000; rows=[]
    def emit(tag,r):
        rows.append({**r,'sweep':tag})
        print(f"[{tag}] a={r['alpha']} c={r['c']} {r['policyB']} fpr={r['fpr']} A={r['mean_A']:.0f}(dnc{r['dnc_A']*100:.0f}%) B={r['mean_B']:.0f}(dnc{r['dnc_B']*100:.0f}%) pen={r['penalty']*100:+.0f}% CI[{r['ci_lo']*100:+.0f},{r['ci_hi']*100:+.0f}] ({time.time()-t0:.0f}s)",flush=True)
    print("=alpha sweep LINEAR c20 B1 fpr=fnr=0.1=",flush=True)
    for a in [0.0,0.002,0.005,0.01,0.02,0.04]:
        emit('alpha_B1',cell(a,20,'linear',0,2.0,R,'B1',0.1,0.1,3.0,1))
    print("=alpha sweep LINEAR c20 B2 overshoot1=",flush=True)
    for a in [0.0,0.002,0.005,0.01,0.02,0.04]:
        emit('alpha_B2',cell(a,20,'linear',0,2.0,R,'B2',0,0,0,1))
    print("=Weibull k2 c20 B1=",flush=True)
    for bw in [0.0,0.0002,0.0005,0.001]:
        emit('weibull_B1',cell(0.0,20,'weibull',bw,2.0,R,'B1',0.1,0.1,3.0,1))
    print("=ckpt spacing alpha=0.01 B1=",flush=True)
    for c in [10,20,40]:
        emit('ckpt_B1',cell(0.01,c,'linear',0,2.0,R,'B1',0.1,0.1,3.0,1))
    print("=detector noise alpha=0.01 c20 B1=",flush=True)
    for fp in [(0.0,0.0),(0.1,0.1),(0.25,0.25),(0.5,0.5)]:
        emit('detector_B1',cell(0.01,20,'linear',0,2.0,R,'B1',fp[0],fp[1],3.0,1))
    fields=['sweep','alpha','c','shape','base_w','k','policyB','fpr','fnr','sd','ov','R','mean_A','mean_B','penalty','ci_lo','ci_hi','dnc_A','dnc_B']
    with open(os.path.join(OUT,'results.csv'),'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader()
        for r in rows: w.writerow(r)
    print(f"WROTE results.csv {len(rows)} rows total {time.time()-t0:.0f}s",flush=True)
main()
