import csv, statistics, os
RES="results"
def load(f):
    with open(os.path.join(RES,f)) as fh: return list(csv.DictReader(fh))
smart=load("sweep_smart.csv"); blind=load("sweep_blind.csv"); be=load("breakeven.csv")
def fl(x): 
    try: return float(x)
    except: return float('nan')

# aggregate smart over seeds: group by (f_fl,mix,acc,rho,W)
from collections import defaultdict
agg=defaultdict(list)
for r in smart:
    k=(r['f_fl'],r['remainder_mix'],r['acc'],r['rho'],r['W'])
    agg[k].append(r)
cells=[]
for k,rows in agg.items():
    dLs=[fl(r['dL']) for r in rows]; pcts=[fl(r['pct_reduction']) for r in rows]
    pcf=[fl(r['p_correct_given_fire']) for r in rows if r['p_correct_given_fire']!='']
    cells.append({'f_fl':float(k[0]),'mix':k[1],'acc':float(k[2]),'rho':float(k[3]),'W':float(k[4]),
        'dL_mean':statistics.mean(dLs),'dL_min':min(dLs),'dL_max':max(dLs),
        'pct_mean':statistics.mean(pcts),'pct_sd':statistics.pstdev(pcts),
        'pcf':statistics.mean(pcf) if pcf else float('nan'),
        'win_all_seeds': all(d>0 for d in dLs)})

print("=== SMART: overall win rate (cells with mean dL>0) ===")
wins=[c for c in cells if c['dL_mean']>0]
print(f"{len(wins)}/{len(cells)} cells mean-win; robust(all 7 seeds win): {sum(c['win_all_seeds'] for c in cells)}")

print("\n=== Effect of detector accuracy (avg pct_reduction across all f_fl,rho,W,mix) ===")
byacc=defaultdict(list)
for c in cells: byacc[c['acc']].append(c['pct_mean'])
for a in sorted(byacc): 
    v=byacc[a]; print(f" acc={a:.2f}: mean pct_red={statistics.mean(v):+.2f}%  win-frac={sum(x>0 for x in v)/len(v):.2f}")

print("\n=== Effect of front-load fraction (avg over acc>=0.8 only, realistic detector) ===")
byf=defaultdict(list)
for c in cells:
    if c['acc']>=0.8: byf[c['f_fl']].append(c['pct_mean'])
for f in sorted(byf): print(f" f_fl={f:.1f}: mean pct_red={statistics.mean(byf[f]):+.2f}%")

print("\n=== Effect of latency ratio rho (acc>=0.8, f_fl>=0.5) ===")
byr=defaultdict(list)
for c in cells:
    if c['acc']>=0.8 and c['f_fl']>=0.5: byr[c['rho']].append(c['pct_mean'])
for r in sorted(byr): print(f" rho={r}: mean pct_red={statistics.mean(byr[r]):+.2f}%")

print("\n=== Effect of wrong-commit penalty W (low-acc regime acc<=0.7) ===")
byw=defaultdict(list)
for c in cells:
    if c['acc']<=0.7: byw[c['W']].append(c['pct_mean'])
for w in sorted(byw): print(f" W={w}: mean pct_red={statistics.mean(byw[w]):+.2f}%  win-frac={sum(x>0 for x in byw[w])/len(byw[w]):.2f}")

print("\n=== WHERE does it lose? worst cells ===")
for c in sorted(cells,key=lambda x:x['dL_mean'])[:6]:
    print(f" f_fl={c['f_fl']} {c['mix']} acc={c['acc']} rho={c['rho']} W={c['W']}: pct={c['pct_mean']:+.1f}% pcf={c['pcf']:.2f}")

print("\n=== REALISTIC region: acc in {0.7,0.8}, f_fl in {0.3,0.5} (plausible), all W,rho,mix ===")
real=[c for c in cells if c['acc'] in (0.7,0.8) and c['f_fl'] in (0.3,0.5)]
rwin=[c for c in real if c['dL_mean']>0]
print(f" {len(rwin)}/{len(real)} mean-win; robust(all seeds): {sum(c['win_all_seeds'] for c in real)}")
print(f" mean pct_red over realistic region: {statistics.mean([c['pct_mean'] for c in real]):+.2f}%")

print("\n=== BLIND detectability ablation (no signal, fixed d) — win rate ===")
bagg=defaultdict(list)
for r in blind: bagg[(r['f_fl'],r['remainder_mix'],r['rho'],r['W'],r['d_fixed'])].append(fl(r['dL']))
bcells=[(k,statistics.mean(v),all(x>0 for x in v)) for k,v in bagg.items()]
bw=[c for c in bcells if c[1]>0]
print(f" blind cells mean-win: {len(bw)}/{len(bcells)}; robust: {sum(c[2] for c in bcells)}")
# blind only wins when front-load is high AND d small by luck
print(" blind win examples:", [ (k,round(m,3)) for k,m,_ in sorted(bcells,key=lambda x:-x[1])[:4]])
print(" blind worst:", [ (k,round(m,3)) for k,m,_ in sorted(bcells,key=lambda x:x[1])[:4]])

print("\n=== BREAK-EVEN p* table (required P(correct|fire) to net-win per fire) ===")
print(" d_fire rho  W   G(gain) P(pen) p*")
for r in be:
    if r['d_fire'] in ('0.2','0.5'):
        print(f"  {r['d_fire']:>4} {r['rho']:>4} {r['W']:>4} {float(r['gain_G']):>6.2f} {float(r['penalty_P']):>5.1f}  {float(r['pstar']):.3f}")
