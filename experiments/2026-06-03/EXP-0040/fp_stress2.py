"""FP stress v2 — the HARD test of the precision control.
Innocent docs legitimately QUOTE a benchmark item PARTIALLY (a real-world confound:
a doc cites part of a question without being the contaminating eval instance). We inject,
into INNOCENT (non-ground-truth) docs, a contiguous PARTIAL prefix of a random benchmark item
covering 'quote_frac' of its tokens. Ground-truth contamination = a FULL item embed elsewhere.
We then sweep span_thresh and see whether passage-level mislabels the partial-quote docs as
contaminated (false positives) -> precision drop. This shows span_thresh is a REAL FP knob."""
import random, csv, os
import sim_contamination as sc
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"results")

def run(seed, span_thresh, quote_frac, quote_doc_frac, doc_len=500,item_len=50,k=8,N=300,M=60,contam_frac=0.2):
    rng=random.Random(seed*104729+int(span_thresh*100)*101+int(quote_frac*100)*7+int(quote_doc_frac*100))
    items=[sc.make_item(rng,item_len) for _ in range(M)]
    item_kgrams=[sc.shingles(it,k) for it in items]
    n_contam=int(N*contam_frac)
    contam_ids=set(rng.sample(range(N),n_contam))
    truth={}
    docs=[]
    for d in range(N):
        base=sc.zipf_doc(rng,sc.DOC_VOCAB,doc_len,None,0.0)
        if d in contam_ids:
            it=rng.randrange(M); span=list(items[it])  # FULL verbatim embed = true contamination
            pos=rng.randrange(0,max(1,doc_len-len(span)))
            base=base[:pos]+span+base[pos+len(span):]; base=base[:doc_len]; truth[d]=it
        elif rng.random()<quote_doc_frac:
            # INNOCENT partial quote: a contiguous PREFIX of a random item (legit citation, not eval instance)
            it=rng.randrange(M); qlen=max(k,int(item_len*quote_frac)); span=list(items[it][:qlen])
            pos=rng.randrange(0,max(1,doc_len-len(span)))
            base=base[:pos]+span+base[pos+len(span):]; base=base[:doc_len]
            # NOTE: not added to truth -> if flagged, it's a false positive
        docs.append(base)
    doc_kgr=[sc.shingles(dt,k) for dt in docs]
    true_pairs=set((d,truth[d]) for d in truth)
    pf=set()
    for d in range(N):
        ds=doc_kgr[d]
        for i in range(M):
            if sc.passage_level_flag(ds,item_kgrams[i],span_thresh): pf.add((d,i))
    rec=len(pf&true_pairs)/len(true_pairs) if true_pairs else 0
    prec=len(pf&true_pairs)/len(pf) if pf else 1.0
    return rec,prec,len(pf)

rows=[]
for qfrac in [0.5,0.7,0.9]:          # how much of the item the innocent doc quotes
    for sth in [0.4,0.6,0.8,0.95]:   # passage threshold
        rs=[run(s,sth,qfrac,0.2) for s in range(7)]
        rec=sum(r[0] for r in rs)/7; prec=sum(r[1] for r in rs)/7; nf=sum(r[2] for r in rs)/7
        rows.append(dict(quote_frac=qfrac,span_thresh=sth,pass_recall=round(rec,4),
                         pass_prec=round(prec,4),mean_flagged=round(nf,1)))
        print(f"quote_frac={qfrac} sth={sth} passR={rec:.2f} passP={prec:.2f} flagged={nf:.1f}",flush=True)
with open(os.path.join(OUT,"fp_stress2.csv"),"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
print("DONE fp2")
