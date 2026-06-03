import sim_recovery as S, statistics
# Check: at alpha=0.04, is policy A hitting MAX_STEPS guard (runaway)? Instrument a copy.
import random, math
def sim_instr(seed, alpha, c, policy, fpr,fnr,sd, cap=200000):
    rng=random.Random(seed); progress=0; onset=None; wasted=0; saved=set()
    det=random.Random(seed^0x9E3779B1); g=0
    while progress<200:
        g+=1
        if g>cap: return wasted, True, progress
        mark=(progress//c)*c
        if progress>0 and progress%c==0 and mark not in saved: saved.add(mark); wasted+=2
        if onset is None: on=True;t=0
        elif progress<onset: on=True;t=0
        else: on=False;t=progress-onset
        if on:
            if onset is None and rng.random()<0.01: onset=progress
            fh=0.002
        else:
            fh=min(0.6, 0.002+alpha*t)
        if rng.random()>=fh: progress+=1; continue
        fp=progress; last=(fp//c)*c
        if policy=='A': r=last
        else:
            if det.random()<fnr or onset is None: r=last
            else:
                if det.random()<fpr: r=max(0,onset-random.Random(seed^fp).randint(2*c,4*c))
                else: r=max(0,onset+int(round(det.gauss(0,sd))))
                r=(r//c)*c
        wasted+=(fp-r); progress=r
        if onset is not None and r<onset: onset=None
        saved={m for m in saved if m<=r}
    return wasted, False, progress
for pol,fpr,fnr in [('A',0,0),('B1',0.1,0.1)]:
    runaway=0; ws=[]
    for i in range(2000):
        w,ra,_=sim_instr(20260603+i,0.04,20,pol,fpr,fnr,3.0)
        ws.append(w); runaway+=ra
    print(f'alpha=0.04 {pol}: mean={statistics.fmean(ws):.1f} runaways={runaway}/2000', flush=True)
