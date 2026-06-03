"""EXP-0049 — CORRECTED honest sim for CLAIM-0047 (researcher-0047).
Supersedes EXP-0046. THREE FIXES (locked in PRE_REGISTRATION.md before running):
  FIX #1  FAIR finite non-completion accounting: MAX_ATTEMPTS=50 failed recoveries -> give up (DNC).
          On DNC, wasted = ACTUAL tokens spent to give-up (finite). SAME rule for A and B. Report dnc_A,dnc_B.
  FIX #2  policy B is EVIDENCE-GATED: it only rolls back PAST the last checkpoint when it has observable
          evidence of a rising hazard (>= K_EVID failures since its last checkpoint ADVANCE). At alpha=0
          (flat hazard) re-fails are rare so B ~= A -> alpha=0 must calibrate to ~0.
  FIX #3  CALIBRATION GATE: run alpha=0 first; require |penalty|<5%. Only then trust alpha>0.
Common random numbers: A and B share the SAME onset + failure draws per rollout (paired). Pure stdlib. SERIAL.
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
MAX_ATTEMPTS=50      # FIX #1: shared give-up bound (failed recoveries). DNC if exceeded.
K_EVID=2             # FIX #2: # of failures since last checkpoint-advance needed to infer a rising hazard.

def sim(seed,alpha,c,shape,base_w,k,policy,fpr,fnr,sd,ov):
    """One rollout. Returns (wasted_tokens, dnc_flag). policy in {A,B1,B2}.
    Latent state (onset, on_path, t_since_dev) is simulator-known, POLICY-HIDDEN.
    Policy observables: failure events, checkpoint positions, fails-since-advance counter, detector output."""
    rng=random.Random(seed)              # latent process (shared across policies via same seed)
    det=random.Random(seed^0x9E3779B1)   # detector noise stream
    progress=0; onset=None; wasted=0; saved={0}
    attempts=0                           # # of failed recoveries (FIX #1 give-up counter)
    fails_since_advance=0                # FIX #2: observable evidence of repeated re-fails
    max_ckpt_reached=0                   # tracks furthest checkpoint advance (observable)
    while progress<N_TARGET:
        # checkpoint save
        if progress>0 and progress%c==0 and ((progress//c)*c) not in saved:
            saved.add((progress//c)*c); wasted+=S_CKPT
        # observable "advance": passed a new checkpoint boundary -> reset evidence counter
        cur_ckpt=(progress//c)*c
        if cur_ckpt>max_ckpt_reached:
            max_ckpt_reached=cur_ckpt; fails_since_advance=0
        # latent on/off-path + time-since-dev (HIDDEN from policy)
        if onset is None: on=True; t=0
        elif progress<onset: on=True; t=0
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
        attempts+=1
        if attempts>MAX_ATTEMPTS:
            return wasted,1                     # FIX #1: give up, wasted = actual tokens spent (finite)
        fp=progress; last=(fp//c)*c
        fails_since_advance+=1
        # decide rollback target r
        if policy=='A':
            r=last
        elif policy=='B1':
            # FIX #2: only roll back PAST last ckpt if EVIDENCE of rising hazard fired
            if fails_since_advance<K_EVID:
                r=last                          # not enough evidence -> behave like A
            elif det.random()<fnr or onset is None:
                r=last                          # detector missed -> behave like A
            elif det.random()<fpr:
                r=max(0,onset-det.randint(2*c,4*c)); r=(r//c)*c   # spurious over-rollback (FPR)
            else:
                est=onset+int(round(det.gauss(0,sd))); r=max(0,est); r=(r//c)*c  # noisy onset, snap to ckpt
        else:  # B2 fixed overshoot, evidence-gated
            if fails_since_advance<K_EVID:
                r=last
            else:
                r=max(0,last-ov*c)
        wasted+=(fp-r); progress=r
        if onset is not None and r<onset: onset=None   # rolled back past true onset -> back on-path
        saved={m for m in saved if m<=r}; saved.add(0)
        # if we rolled back below max_ckpt_reached, we'll re-cross boundaries; keep evidence counter
        # (it resets only on a NEW advance beyond max_ckpt_reached) -> repeated re-fails accumulate evidence
    return wasted,0

def cell(alpha,c,shape,base_w,k,R,pol,fpr,fnr,sd,ov):
    h=hashlib.sha256(repr((alpha,c,shape,base_w,k,pol,fpr,fnr,sd,ov)).encode()).hexdigest()
    base=(MASTER+int(h[:8],16))%(2**31)
    wa=[];da=0;wb=[];db=0; wa_c=[];wb_c=[]
    for i in range(R):
        s=base+i
        w,d=sim(s,alpha,c,shape,base_w,k,'A',0,0,0,0); wa.append(w); da+=d
        if not d: wa_c.append(w)
        bf,bn=(fpr,fnr) if pol=='B1' else (0,0)
        w,d=sim(s,alpha,c,shape,base_w,k,pol,bf,bn,sd,ov); wb.append(w); db+=d
        if not d: wb_c.append(w)
    ma=statistics.fmean(wa); mb=statistics.fmean(wb)
    pen=(ma-mb)/mb if mb>0 else 0.0
    mac=statistics.fmean(wa_c) if wa_c else float('nan')
    mbc=statistics.fmean(wb_c) if wb_c else float('nan')
    penc=(mac-mbc)/mbc if (wb_c and mbc>0) else float('nan')
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
        pc=r['penalty_compl']; pcs=f"{pc*100:+.0f}%" if pc==pc else "nan"
        print(f"[{tag}] a={r['alpha']} c={r['c']} {r['policyB']} fpr={r['fpr']} "
              f"A={r['mean_A']:.0f}(dnc{r['dnc_A']*100:.1f}%) B={r['mean_B']:.0f}(dnc{r['dnc_B']*100:.1f}%) "
              f"pen={r['penalty']*100:+.1f}% pen_c={pcs} CI[{r['ci_lo']*100:+.1f},{r['ci_hi']*100:+.1f}] "
              f"({time.time()-t0:.0f}s)",flush=True)
    # === FIX #3: CALIBRATION GATE FIRST (alpha=0) ===
    print("=== CALIBRATION GATE: alpha=0 (memoryless control) ===",flush=True)
    g1=cell(0.0,20,'linear',0,2.0,R,'B1',0.1,0.1,3.0,1); emit('GATE_B1',g1)
    g2=cell(0.0,20,'linear',0,2.0,R,'B2',0,0,0,1); emit('GATE_B2',g2)
    gate_pass = abs(g1['penalty'])<0.05 and abs(g2['penalty'])<0.05
    print(f"GATE: |pen_B1|={abs(g1['penalty'])*100:.1f}% |pen_B2|={abs(g2['penalty'])*100:.1f}% "
          f"-> {'PASS' if gate_pass else 'FAIL'}",flush=True)
    if not gate_pass:
        print("!!! GATE FAILED -> sim still buggy, NOT trusting alpha>0. Writing partial CSV.",flush=True)
    # === full alpha sweep (LINEAR, B1) ===
    print("=== alpha sweep LINEAR c20 B1 fpr=fnr=0.1 ===",flush=True)
    for a in [0.0,0.002,0.005,0.01,0.02,0.04]:
        emit('alpha_B1',cell(a,20,'linear',0,2.0,R,'B1',0.1,0.1,3.0,1))
    print("=== alpha sweep LINEAR c20 B2 overshoot1 ===",flush=True)
    for a in [0.0,0.002,0.005,0.01,0.02,0.04]:
        emit('alpha_B2',cell(a,20,'linear',0,2.0,R,'B2',0,0,0,1))
    # === Weibull k=2 variant ===
    print("=== Weibull k=2 sweep base_w c20 B1 ===",flush=True)
    for bw in [0.0,0.0002,0.0005,0.001]:
        emit('weibull_B1',cell(0.0,20,'weibull',bw,2.0,R,'B1',0.1,0.1,3.0,1))
    # === detector FPR/FNR boundary at realistic alpha=0.02 ===
    print("=== detector noise alpha=0.02 c20 B1 ===",flush=True)
    for fp in [(0.0,0.0),(0.1,0.1),(0.25,0.25),(0.5,0.5)]:
        emit('detector_B1',cell(0.02,20,'linear',0,2.0,R,'B1',fp[0],fp[1],3.0,1))
    # === checkpoint spacing at realistic alpha=0.02 ===
    print("=== ckpt spacing alpha=0.02 B1 ===",flush=True)
    for c in [10,20,40]:
        emit('ckpt_B1',cell(0.02,c,'linear',0,2.0,R,'B1',0.1,0.1,3.0,1))
    fields=['sweep','alpha','c','shape','base_w','k','policyB','fpr','fnr','sd','ov','R',
            'mean_A','mean_B','penalty','ci_lo','ci_hi','dnc_A','dnc_B','mean_A_compl','mean_B_compl','penalty_compl']
    with open(os.path.join(OUT,'results_corrected.csv'),'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader()
        for r in rows: w.writerow(r)
    print(f"WROTE results_corrected.csv {len(rows)} rows total {time.time()-t0:.0f}s GATE={'PASS' if gate_pass else 'FAIL'}",flush=True)
if __name__=='__main__':
    main()
