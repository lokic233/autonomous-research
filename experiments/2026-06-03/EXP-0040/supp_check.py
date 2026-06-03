import sim_contamination as sc, csv, os
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"results")
rows=[]
for sr,(dl,il) in [(0.5,(100,50)),(0.1,(500,50)),(0.02,(2500,50)),(0.01,(5000,50))]:
    for dth in [0.3,0.4,0.5]:
        rs=[sc.run_config(s,dl,il,0.0,dth,0.8,8) for s in range(7)]
        dr=sum(r['doc_recall'] for r in rs)/7
        dp=sum(r['doc_prec'] for r in rs)/7
        pr=sum(r['pass_recall'] for r in rs)/7
        pp=sum(r['pass_prec'] for r in rs)/7
        gap=sum(r['miss_gap'] for r in rs)/7
        rows.append(dict(span_ratio=sr,doc_thresh=dth,doc_recall=round(dr,4),doc_prec=round(dp,4),
                         pass_recall=round(pr,4),pass_prec=round(pp,4),miss_gap=round(gap,4)))
        print(f'sr={sr} dth={dth} docR={dr:.2f} docP={dp:.2f} passR={pr:.2f} passP={pp:.2f} gap={gap:.2f}',flush=True)
with open(os.path.join(OUT,"supp_lowthresh.csv"),"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
print("DONE supp")
