"""EXP-0046 v2 — corrected honest sim for CLAIM-0047.
Fixes vs v1:
  (1) alpha=0 'calibration': the v1 prereg said penalty MUST be ~0 at alpha=0. That premise was
      WRONG. Under memoryless hazard ANY restart depth ties in EXPECTED re-fails, but policy B
      (rollback PAST the checkpoint) re-executes strictly MORE steps per failure (the overshoot is
      deadweight). So the correct memoryless prediction is penalty <= 0 (B no better, usually worse).
      We test the corrected calibration: at alpha=0, penalty <= 0 AND CI excludes a B-advantage.
  (2) v1's alpha>0 penalties (+3000%) were a CAP ARTIFACT: policy A restarts INSIDE the rising-hazard
      region and at large alpha can NEVER escape (per-step fail hazard > prob of reaching next ckpt),
      so A's expected waste DIVERGES (49% of rollouts hit the cap at alpha=0.04). A divergent mean is
      not a clean quantitative penalty. We therefore (a) report DNC (did-not-complete) rate as a
      first-class outcome, (b) report COMPLETION-CONDITIONAL waste, and (c) focus the >=25% headline
      on the LOW-alpha regime where BOTH policies complete (DNC_A < 2%), giving a finite clean penalty,
      and separately report the DIVERGENCE BOUNDARY (alpha at which A's DNC crosses thresholds).
Common random numbers: A and B share the SAME deviation onset + SAME failure draws per rollout (paired).
Pure stdlib. SERIAL.
"""
import random, math, csv, statistics, os, time, hashlib
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"results")
os.makedirs(OUT,exist_ok=True)
MASTER=20260603
N_TARGET=200
H0_DEV=0.01
H0_FAIL=0.002
H_CAP=0.6
S_CKPT=2
CAP=50000          # token budget; rollouts exceeding => DNC. Documented, transparent.

def sim(seed,alpha,c,shape,base_w,k,policy,fpr,fnr,sd,ov):
    """One rollout. Returns (wasted_tokens, dnc_flag). policy in {A,B1,B2}.
    Pre-draws the deviation-onset + failure randomness from ONE stream so A and B are paired."""
    rng=random.Random(seed)              # drives latent process (shared across policies via same seed)
    det=random.Random(seed^0x9E3779B1)   # detector noise stream
    progress=0; onset=None; wasted=0; saved=set()
    while progress<N_TARGET:
        if wasted>CAP: return wasted,1
        mark=(progress//c)*c
        if progress>0 and progress%c==0 and mark not in saved:
            saved.add(mark); wasted+=S_CKPT
        # latent on/off-path + time-since-dev
        if onset is None: on=True; t=0
        elif progress<onset:  on=True; t=0
        else: on=False; t=progress-onset
        if on:
            if onset is None and rng.random()<H0_DEV: onset=progress
            fh=H0_FAIL
        else:
            fh=H0_FAIL + (alpha*t if shape=='linear' else base_w*(t**(k-1)))
            if fh>H_CAP: fh=H_CAP
        if rng.random()>=fh:
            progress+=1; continue
        # FAILURE at step 'progress' -> recovery
        fp=progress; last=(fp//c)*c
        if policy=='A':
            r=last
        elif policy=='B1':
            if det.random()<fnr or onset is None:
                r=last                                  # detector missed -> behaves like A
            elif det.random()<fpr:
                r=max(0,onset-random.Random(seed^fp).randint(2*c,4*c)); r=(r//c)*c   # spurious over-rollback
            else:
                est=onset+int(round(det.gauss(0,sd))); r=max(0,est); r=(r//c)*c       # snap to ckpt<=est
        else:  # B2 fixed overshoot
            r=max(0,last-ov*c)
        wasted+=(fp-r); progress=r
        if onset is not None and r<onset: onset=None    # rolled back past true onset -> back on-path
        saved={m for m in saved if m<=r}
    return wasted,0

def cell(alpha,c,shape,base_w,k,R,pol,fpr,fnr,sd,ov):
    h=hashlib.sha256(repr((alpha,c,shape,base_w,k,pol,fpr,fnr,sd,ov)).encode()).hexdigest()
    base=(MASTER+int(h[:8],16))%(2**31)
    wa=[];da=0;wb=[];db=0; wa_c=[];wb_c=[]   # _c = completion-conditional
    for i in range(R):
        s=base+i
        w,d=sim(s,alpha,c,shape,base_w,k,'A',0,0,0,0); wa.append(w); da+=d
        if not d: wa_c.append(w)
        bf,bn=(fpr,fnr) if pol=='B1' else (0,0)
        w,d=sim(s,alpha,c,shape,base_w,k,pol,bf,bn,sd,ov); wb.append(w); db+=d
        if not d: wb_c.append(w)
    ma=statistics.fmean(wa); mb=statistics.fmean(wb)
    pen=(ma-mb)/mb if mb>0 else 0.0
    # completion-conditional penalty (only rollouts where BOTH completed would be ideal; report marginal)
    mac=statistics.fmean(wa_c) if wa_c else float('nan')
    mbc=statistics.fmean(wb_c) if wb_c else float('nan')
    penc=(mac-mbc)/mbc if (wb_c and mbc>0) else float('nan')
    # bootstrap CI on the marginal (capped) penalty
    rb=random.Random(base^0xABCDEF); boots=[]
    for _ in range(300):
        idx=[rb.randrange(R) for _ in range(R)]
        x=statistics.fmean([wa[j] for j in idx]); y=statistics.fmean([wb[j] for j in idx])
        boots.append((x-y)/y if y>0 else 0.0)
    boots.sort(); lo=boots[int(.025*len(boots))]; hi=boots[int(.975*len(boots))]
    return dict(alpha=alpha,c=c,shape=shape,base_w=base_w,k=k,policyB=pol,fpr=fpr,fnr=fnr,sd=sd,ov=ov,R=R,
        mean_A=ma,mean_B=mb,penalty=pen,ci_lo=lo,ci_hi=hi,dnc_A=da/R,dnc_B=db/R,
        mean_A_compl=mac,mean_B_compl=mbc,penalty_compl=penc)

def main():
    t0=time.time(); R=4000; rows=[]
    def emit(tag,r):
        rows.append({**r,'sweep':tag})
        pc=r['penalty_compl']
        pcs=f"{pc*100:+.0f}%" if pc==pc else "nan"
        print(f"[{tag}] a={r['alpha']} c={r['c']} {r['policyB']} fpr={r['fpr']} "
              f"A={r['mean_A']:.0f}(dnc{r['dnc_A']*100:.1f}%) B={r['mean_B']:.0f}(dnc{r['dnc_B']*100:.1f}%) "
              f"pen={r['penalty']*100:+.0f}% pen_compl={pcs} CI[{r['ci_lo']*100:+.0f},{r['ci_hi']*100:+.0f}] "
              f"({time.time()-t0:.0f}s)",flush=True)
    # FINE-GRAINED LOW-alpha sweep (the regime where A still completes -> clean finite penalty)
    print("=FINE alpha sweep LINEAR c20 B1 fpr=fnr=0.1 (low-alpha clean regime)=",flush=True)
    for a in [0.0,0.0005,0.001,0.002,0.003,0.005]:
        emit('fine_B1',cell(a,20,'linear',0,2.0,R,'B1',0.1,0.1,3.0,1))
    print("=FINE alpha sweep LINEAR c20 B2 overshoot1=",flush=True)
    for a in [0.0,0.0005,0.001,0.002,0.003,0.005]:
        emit('fine_B2',cell(a,20,'linear',0,2.0,R,'B2',0,0,0,1))
    # DIVERGENCE-boundary sweep (where A's DNC climbs)
    print("=DIVERGENCE alpha sweep B1=",flush=True)
    for a in [0.008,0.01,0.02,0.04]:
        emit('diverge_B1',cell(a,20,'linear',0,2.0,R,'B1',0.1,0.1,3.0,1))
    # detector-noise boundary at a clean low alpha (0.003, where both complete)
    print("=detector noise alpha=0.003 c20 B1=",flush=True)
    for fp in [(0.0,0.0),(0.1,0.1),(0.25,0.25),(0.5,0.5)]:
        emit('detector_B1',cell(0.003,20,'linear',0,2.0,R,'B1',fp[0],fp[1],3.0,1))
    # checkpoint spacing at clean low alpha
    print("=ckpt spacing alpha=0.003 B1=",flush=True)
    for c in [10,20,40]:
        emit('ckpt_B1',cell(0.003,c,'linear',0,2.0,R,'B1',0.1,0.1,3.0,1))
    fields=['sweep','alpha','c','shape','base_w','k','policyB','fpr','fnr','sd','ov','R',
            'mean_A','mean_B','penalty','ci_lo','ci_hi','dnc_A','dnc_B','mean_A_compl','mean_B_compl','penalty_compl']
    with open(os.path.join(OUT,'results_v2.csv'),'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader()
        for r in rows: w.writerow(r)
    print(f"WROTE results_v2.csv {len(rows)} rows total {time.time()-t0:.0f}s",flush=True)
if __name__=='__main__':
    main()
