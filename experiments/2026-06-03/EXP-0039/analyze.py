import csv, statistics, random, os
RES="/Users/dengcchi/autonomous-research-v3/experiments/2026-06-03/EXP-0039/results"
def rd(n):
    with open(os.path.join(RES,n)) as f: return list(csv.DictReader(f))
amp=rd("amplification.csv"); pol=rd("policies.csv")
def fl(x): 
    try: return float(x)
    except: return float('nan')

# (A) amplification by restore_rate
print("=== (A) WRITE-AMPLIFICATION (true latent fact-id re-store fraction) ===")
for rr in [0.2,0.4,0.6]:
    vals=[fl(r['amplification_rate']) for r in amp if fl(r['restore_rate'])==rr]
    print(f"  restore_rate={rr}: amplification mean={statistics.mean(vals):.3f} "
          f"min={min(vals):.3f} max={max(vals):.3f}  (>25%? {statistics.mean(vals)>0.25})")
allamp=[fl(r['amplification_rate']) for r in amp if fl(r['restore_rate'])>0]
print(f"  ALL realistic (restore>0): mean={statistics.mean(allamp):.3f}")

def boot(d,B=2000,seed=7):
    if not d: return (float('nan'),)*3
    rng=random.Random(seed); n=len(d); m=[sum(d[rng.randrange(n)] for _ in range(n))/n for _ in range(B)]
    m.sort(); return statistics.mean(d), m[int(.025*B)], m[int(.975*B)]

print("\n=== (B) DEDUP vs SIZE-CAP vs NO-DEDUP at MATCHED CAP ===")
print("Per (restore,paraphrase,horizon,cap,thr): recall + dedup-minus-sizecap delta (mean over 5 seeds)\n")
hdr=f"{'rr':>4}{'pr':>5}{'hz':>6}{'cap':>5}{'thr':>5} | {'r_nodedupUNC':>13}{'r_sizecap':>10}{'r_dedup':>9}{'r_oracle':>9} | {'dd-sc':>7}{'or-dd':>7}{'gPrec':>7}{'gRec':>7}{'sz_dd':>6}"
print(hdr); print("-"*len(hdr))
# group
from collections import defaultdict
g=defaultdict(list)
for r in pol:
    k=(r['restore_rate'],r['paraphrase_rate'],r['horizon'],r['cap'],r['thr'])
    g[k].append(r)
delta_by_thr=defaultdict(list)
all_deltas=[]
win_rows=[]
for k in sorted(g.keys(), key=lambda x:(float(x[0]),float(x[1]),x[2],float(x[3]),float(x[4]))):
    rs=g[k]
    def m(c): return statistics.mean([fl(r[c]) for r in rs])
    dd_sc=m('dedup_minus_sizecap_recall'); or_dd=m('oracle_minus_dedup_recall')
    gp=statistics.mean([fl(r['gate_prec']) for r in rs if r['gate_prec']!=''])
    gr=statistics.mean([fl(r['gate_rec']) for r in rs if r['gate_rec']!=''])
    print(f"{k[0]:>4}{k[1]:>5}{k[2]:>6}{k[3]:>5}{k[4]:>5} | "
          f"{m('recall_nodedup_uncapped'):>13.3f}{m('recall_sizecap'):>10.3f}"
          f"{m('recall_dedup'):>9.3f}{m('recall_oracle'):>9.3f} | "
          f"{dd_sc:>7.3f}{or_dd:>7.3f}{gp:>7.2f}{gr:>7.2f}{m('size_dedup'):>6.0f}")
    delta_by_thr[k[4]].append(dd_sc)
    all_deltas.append(dd_sc)
    if dd_sc>0.01: win_rows.append(k)

print("\n=== dedup-minus-sizecap recall DELTA — bootstrap 95% CI (over all configs' per-config means) ===")
for thr in ['0.3','0.5','0.7']:
    mn,lo,hi=boot(delta_by_thr[thr])
    print(f"  thr={thr}: mean delta={mn:+.4f}  CI[{lo:+.4f},{hi:+.4f}]  excl0={'YES' if (lo>0 or hi<0) else 'no'}")
mn,lo,hi=boot(all_deltas)
print(f"  ALL: mean delta={mn:+.4f}  CI[{lo:+.4f},{hi:+.4f}]  excl0={'YES' if (lo>0 or hi<0) else 'no'}")

# Per-seed delta for the BEST regime (low paraphrase, long horizon) at a representative thr
print("\n=== seed-level delta, best regime: paraphrase=0.0, horizon=long, cap=120, thr=0.5 ===")
sel=[r for r in pol if r['paraphrase_rate']=='0.0' and r['horizon']=='long' and r['cap']=='120' and r['thr']=='0.5']
ds=[fl(r['dedup_minus_sizecap_recall']) for r in sel]
# aggregate across restore rates per seed
bysd=defaultdict(list)
for r in sel: bysd[r['seed']].append(fl(r['dedup_minus_sizecap_recall']))
seed_means=[statistics.mean(v) for v in bysd.values()]
mn,lo,hi=boot(seed_means)
print(f"  per-seed mean delta={seed_means}  boot CI[{lo:+.4f},{hi:+.4f}]")

print("\n=== gate precision/recall overall (lexical vs fact_id) + ORACLE GAP ===")
gps=[fl(r['gate_prec']) for r in pol if r['gate_prec']!='']
grs=[fl(r['gate_rec']) for r in pol if r['gate_rec']!='']
ogap=[fl(r['oracle_minus_dedup_recall']) for r in pol]
print(f"  gate precision: mean={statistics.mean(gps):.3f}  gate recall: mean={statistics.mean(grs):.3f}")
print(f"  oracle-minus-dedup recall gap: mean={statistics.mean(ogap):.4f} max={max(ogap):.4f}")
print(f"\n  # configs where dedup beats sizecap by >0.01: {len(win_rows)} / {len(g)}")
print("DONE_ANALYZE")
