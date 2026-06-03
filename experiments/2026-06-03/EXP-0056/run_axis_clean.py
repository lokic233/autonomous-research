
import time, json
exec(open('/tmp/exp0056_harness.py').read())
import random, math

# Focused AXIS confirmation: L fixed at 640 (=20b, still L>>b, the real regime) but N HUGE so there
# are MANY sources (N/L >> 1) => oracle full-shuffle rho ~ 0 (clean baseline). Then sweep B:
#  - with-batch axis: B in {64,320,1600} (2b,10b,50b) at L=640 -> show flat-high CEILING
#  - with-runlength axis: B in {320,640,1280,3200} = {L/2,L,2L,5L} -> show drop toward ~1
# Override choose_N to force many sources at L=640.
b = B_BATCH
L = 640
N = 256000   # => ~400 sources at L=640; full-shuffle baseline clean

def run_cell_N(B, L, seed, Nfixed):
    grads, labels = gen_stream_grads(seed, L, Nfixed)
    n = len(grads)
    rng_buf = random.Random(seed*7919 + B*31 + L*131 + 1)
    bo = buffer_shuffle_order(n, B, rng_buf)
    V_buf, nb = batch_mean_var(grads, bo, B_BATCH)
    rho_buf = rho_same_source(labels, bo, B_BATCH)
    rng_full = random.Random(seed*104729 + 3)
    fo = list(range(n)); rng_full.shuffle(fo)
    V_full, _ = batch_mean_var(grads, fo, B_BATCH)
    rho_full = rho_same_source(labels, fo, B_BATCH)
    return dict(B=B,L=L,seed=seed,N=n,nbatches=nb,inflation=V_buf/V_full,rho_buf=rho_buf,rho_full=rho_full)

print("focused axis test: L=640 (=20b), N=256000 (~400 sources), b=32", flush=True)
T0=time.time()
res = {}
for B in [64,320,640,1280,1600,3200,6400]:
    cells=[run_cell_N(B,L,s,N) for s in [0,1,2]]
    infl=[c['inflation'] for c in cells]; m=sum(infl)/3
    sd=math.sqrt(sum((x-m)**2 for x in infl)/2); ci=1.96*sd/math.sqrt(3)
    rb=sum(c['rho_buf'] for c in cells)/3; rf=sum(c['rho_full'] for c in cells)/3
    res[B]=(m,ci,rb,rf,cells[0]['nbatches'])
    print(f"  B={B:5d} (={B/b:.0f}b, B/L={B/L:.2f})  infl={m:6.3f} +/-{ci:.3f}  rho_buf={rb:.4f} rho_full={rf:.4f} nb={cells[0]['nbatches']} t={time.time()-T0:.1f}s", flush=True)
import json
json.dump({str(k):v for k,v in res.items()}, open('/tmp/axis2_local.json','w'))
print("done", flush=True)
