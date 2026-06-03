import time, csv, statistics, math
from harness2 import run_cell, ci95
t0=time.time()
Ks=[3,5,10,20,50]; temps=[0.05,0.15,0.40]; sigmas=[0.10,0.30]; SEEDS=list(range(8)); N=500
gap_labels=["<=0.10","<=0.20","<=0.30","<=0.45",">0.45"]

# ---- GUARD 1: stream-misroute & oos-frac vs K, robust across temp x sigma ----
rows=[]
for temp in temps:
  for sigma in sigmas:
    for K in Ks:
      sr,of,gr=[],[],[]
      for s in SEEDS:
        r=run_cell(K,temp,sigma,seed=1000+s,n_requests=N)
        sr.append(r['stream_rate']); of.append(r['oos_frac']); gr.append(r['gad_rec'])
      m,c=ci95(sr); ofm,_=ci95(of)
      rows.append(dict(temp=temp,sigma=sigma,K=K,
        stream_misroute_mean=round(m,4),stream_misroute_ci=round(c,4),
        oos_frac_mean=round(ofm,4),gad_recovery=round(statistics.mean(gr),5),
        monitor_recall=0.0))
      print(f"temp={temp} sigma={sigma} K={K:2d}  stream_misroute={m:.3f}±{c:.3f}  oos_frac={ofm:.3f}  gad={statistics.mean(gr):.4f}")
with open('results/stream_misroute_vs_K_robustness.csv','w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

# ---- near-miss DANGER: misroute confidence by gap bin (K=10) ----
print("\n--- misroute confidence by neighbor-gap (near->far), K=10 ---")
conf_rows=[]
for temp in temps:
  for sigma in sigmas:
    agg=[[] for _ in gap_labels]
    for s in SEEDS:
      r=run_cell(10,temp,sigma,seed=3000+s,n_requests=N)
      for k,v in enumerate(r['conf_by_bin']):
        if v is not None: agg[k].append(v)
    means=[round(statistics.mean(a),3) if a else None for a in agg]
    conf_rows.append(dict(temp=temp,sigma=sigma,**{gap_labels[k]:means[k] for k in range(len(gap_labels))}))
    print(f"temp={temp} sigma={sigma}  misroute_conf by gap (near->far): {means}")
with open('results/misroute_confidence_vs_gap.csv','w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(conf_rows[0].keys())); w.writeheader(); w.writerows(conf_rows)

# ---- GUARD 2: escape-recall vs proximity (K=10) ----
print("\n--- escape-recall by neighbor-gap (near->far), K=10 ---")
esc_rows=[]
def esc_prior_for(temp): return -0.18/temp
for temp in temps:
  for sigma in sigmas:
    agg=[[] for _ in gap_labels]
    for s in SEEDS:
      r=run_cell(10,temp,sigma,seed=2000+s,n_requests=N,esc_prior=esc_prior_for(temp))
      for k,v in enumerate(r['esc_by_bin']):
        if v is not None: agg[k].append(v)
    means=[round(statistics.mean(a),3) if a else None for a in agg]
    esc_rows.append(dict(temp=temp,sigma=sigma,**{gap_labels[k]:means[k] for k in range(len(gap_labels))}))
    print(f"temp={temp} sigma={sigma}  esc_recall by gap (near->far): {means}")
with open('results/escape_recall_vs_proximity.csv','w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(esc_rows[0].keys())); w.writeheader(); w.writerows(esc_rows)
print(f"\nelapsed {time.time()-t0:.1f}s")
