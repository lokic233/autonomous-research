"""FP stress: deliberately create innocent n-gram overlap between uncontaminated docs and
benchmark items, to test whether passage-level OVER-FLAGS (the load-bearing precision control).
We sprinkle real benchmark k-grams (shared 'boilerplate' that legitimately co-occurs, e.g.
common question templates) into INNOCENT docs at controlled rate, and measure passage precision."""
import random, csv, os
import sim_contamination as sc

OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"results")

def run(seed, doc_len, item_len, ngram_k, span_thresh, boiler_rate, boiler_len,
        N=300, M=60, contam_frac=0.2):
    rng=random.Random(seed*7919+int(boiler_rate*1000)*13+boiler_len)
    items=[sc.make_item(rng,item_len) for _ in range(M)]
    item_kgrams=[sc.shingles(it,ngram_k) for it in items]
    # BOILERPLATE: shared spans drawn FROM item vocab (innocent but item-like) that legitimately
    # appear in many docs (e.g. licence text, common phrasing). boiler_len tokens, boiler_rate freq.
    boiler=[ [rng.choice(sc.ITEM_VOCAB) for _ in range(boiler_len)] for _ in range(8) ]
    n_contam=int(N*contam_frac)
    contam_ids=set(rng.sample(range(N),n_contam))
    truth={}
    docs=[]
    for d in range(N):
        base=sc.zipf_doc(rng,sc.DOC_VOCAB,doc_len,None,0.0)
        # inject innocent boilerplate spans (NOT a benchmark item, but item-vocab n-grams)
        ntoks=len(base)
        i=0
        out=[]
        while i<len(base):
            if rng.random()<boiler_rate:
                out.extend(rng.choice(boiler))
            out.append(base[i]); i+=1
        base=out[:doc_len]
        if d in contam_ids:
            it=rng.randrange(M)
            span=list(items[it])
            pos=rng.randrange(0,max(1,doc_len-len(span)))
            base=base[:pos]+span+base[pos+len(span):]; base=base[:doc_len]
            truth[d]=it
        docs.append(base)
    doc_kgr=[sc.shingles(dt,ngram_k) for dt in docs]
    true_pairs=set((d,truth[d]) for d in truth)
    pass_flagged=set()
    for d in range(N):
        ds=doc_kgr[d]
        for i in range(M):
            if sc.passage_level_flag(ds,item_kgrams[i],span_thresh):
                pass_flagged.add((d,i))
    rec=len(pass_flagged&true_pairs)/len(true_pairs) if true_pairs else 0
    prec=len(pass_flagged&true_pairs)/len(pass_flagged) if pass_flagged else 1.0
    return dict(seed=seed,doc_len=doc_len,boiler_rate=boiler_rate,boiler_len=boiler_len,
                span_thresh=span_thresh,pass_recall=round(rec,4),pass_prec=round(prec,4),
                n_flagged=len(pass_flagged),n_true=len(true_pairs))

rows=[]
# boiler_len >= ngram_k creates k-gram collisions; vary how long the innocent shared span is
for blen in [8,16,40]:            # 8=exactly one k-gram; 40=full item-length innocent span
    for brate in [0.02,0.1,0.3]:  # how often innocent boilerplate appears
        for sth in [0.6,0.8]:
            rs=[run(s,500,50,8,sth,brate,blen) for s in range(7)]
            agg=dict(boiler_len=blen,boiler_rate=brate,span_thresh=sth,
                     pass_recall=round(sum(r['pass_recall'] for r in rs)/7,4),
                     pass_prec=round(sum(r['pass_prec'] for r in rs)/7,4),
                     mean_flagged=round(sum(r['n_flagged'] for r in rs)/7,1))
            rows.append(agg)
            print(f"blen={blen} brate={brate} sth={sth} passR={agg['pass_recall']:.2f} passP={agg['pass_prec']:.2f} flagged={agg['mean_flagged']}",flush=True)
with open(os.path.join(OUT,"fp_stress.csv"),"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
print("DONE fp_stress")
