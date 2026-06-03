
import time, json, sys
sys.path.insert(0, '/tmp')
# inline the harness by exec
exec(open('/tmp/exp0056_harness.py').read())

OUT = '/Users/dengcchi/autonomous-research-v3/experiments/2026-06-03/EXP-0056/results/'
import os
os.makedirs(OUT, exist_ok=True)

T0 = time.time()
b = B_BATCH

# THE SWEEP grid: B in {2b,10b,50b}, L in {b/2,2b,20b,200b}
Bgrid = [2*b, 10*b, 50*b]            # 64,320,1600
Lgrid = [b//2, 2*b, 20*b, 200*b]      # 16,64,640,6400

# THE AXIS extra: fixed L=6400, add B in {L/2,L,2L}
L_fixed = 200*b   # 6400
Baxis_extra = [L_fixed//2, L_fixed, 2*L_fixed]  # 3200,6400,12800

raw = []
grid_results = {}   # (B,L)->agg

def do(B, L):
    cells = [run_cell(B, L, s) for s in SEEDS]
    for c in cells: raw.append(c)
    a = agg(cells)
    grid_results[(B,L)] = a
    print(f"  B={B:6d} L={L:6d}  infl={a['mean']:7.3f} +/-{a['ci']:.3f}  rho_buf={a['rho_buf']:.4f} rho_full={a['rho_full']:.4f}  nb={a['nbatches']} t={time.time()-T0:.1f}s", flush=True)
    return a

print("=== GRID SWEEP (B x L) ===", flush=True)
for L in Lgrid:
    for B in Bgrid:
        do(B, L)

print("=== AXIS EXTRA (L=6400 fixed, B->L) ===", flush=True)
for B in Baxis_extra:
    if (B, L_fixed) not in grid_results:
        do(B, L_fixed)

elapsed = time.time() - T0
print(f"=== DONE total {elapsed:.1f}s, {len(raw)} cells ===", flush=True)

# serialize
out = {
  'config': dict(D=D, sigma_sig=SIGMA_SIG, sigma_noise=SIGMA_NOISE, b=b, seeds=SEEDS,
                 within_source_corr=SIGMA_SIG**2/(SIGMA_SIG**2+SIGMA_NOISE**2),
                 Bgrid=Bgrid, Lgrid=Lgrid, L_fixed=L_fixed, Baxis_extra=Baxis_extra),
  'grid': [dict(B=B, L=L, **a) for (B,L),a in grid_results.items()],
  'raw': raw,
  'elapsed_s': elapsed,
}
with open(OUT+'results.json','w') as f:
    json.dump(out, f, indent=2)

# CSV
with open(OUT+'inflation_grid.csv','w') as f:
    f.write("B,L,Lb_ratio,Bb_ratio,inflation_mean,inflation_ci95,inflation_sd,rho_buf,rho_full,nbatches,n_seeds\n")
    for (B,L),a in sorted(grid_results.items()):
        f.write(f"{B},{L},{L/b:.2f},{B/b:.2f},{a['mean']:.5f},{a['ci']:.5f},{a['sd']:.5f},{a['rho_buf']:.5f},{a['rho_full']:.5f},{a['nbatches']},{a['n_seeds']}\n")
print("wrote", OUT+'results.json', "and inflation_grid.csv', flush=True)" if False else "wrote results.json + inflation_grid.csv", flush=True)
