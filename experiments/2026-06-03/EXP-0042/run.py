#!/usr/bin/env python3
# EXP-0042 / CLAIM-0043 — recall@k over-count from span-splitting. L0 CPU stdlib SERIAL.
# Retriever: BM25-style lexical (sentence-transformers NOT importable on this Mac). STATED.
import random, math, csv, os, time
from collections import Counter

OUT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(OUT, "results"); LOG = os.path.join(OUT, "logs")
os.makedirs(RES, exist_ok=True); os.makedirs(LOG, exist_ok=True)
logf = open(os.path.join(LOG, "run.log"), "w")
def log(*a):
    s = " ".join(str(x) for x in a); print(s); logf.write(s+"\n"); logf.flush()

# distractor vocab (common tokens) + gold tokens (rare/distinctive) + query-topic token
DISTRACT = ["the","a","of","and","to","in","that","is","for","on","with","as","by","at","an",
            "system","data","model","value","result","process","method","table","field","record",
            "report","year","number","case","group","point","line","page","note","text","item",
            "node","edge","graph","query","index","score","rank","list","set","map","key","cell"]

def make_doc(rng, span_len, doc_len_tokens, gold_id):
    # gold span = distinctive tokens; placed at a random token position within doc
    gold = [f"GOLD{gold_id}_{i}" for i in range(span_len)]
    n_distract = doc_len_tokens - span_len
    body = [rng.choice(DISTRACT) for _ in range(n_distract)]
    pos = rng.randint(0, len(body))  # token insert position
    tokens = body[:pos] + gold + body[pos:]
    span = (pos, pos + span_len)  # GROUND TRUTH token offsets [start,end)
    return tokens, span, gold

def chunk(tokens, size, overlap):
    stride = max(1, size - overlap)
    chunks = []  # (tok_start, tok_end, tokens_slice)
    i = 0
    while i < len(tokens):
        end = min(i + size, len(tokens))
        chunks.append((i, end, tokens[i:end]))
        if end >= len(tokens): break
        i += stride
    return chunks

def bm25_scores(chunks, query_tokens, k1=1.5, b=0.75):
    # idf over chunk collection
    N = len(chunks)
    df = Counter()
    for (_,_,ct) in chunks:
        for t in set(ct): df[t]+=1
    avgdl = sum(len(ct) for (_,_,ct) in chunks)/max(1,N)
    scores=[]
    for (s,e,ct) in chunks:
        tf = Counter(ct); dl=len(ct); sc=0.0
        for qt in query_tokens:
            if qt in tf:
                idf = math.log(1 + (N - df[qt] + 0.5)/(df[qt]+0.5))
                f = tf[qt]
                sc += idf * (f*(k1+1))/(f + k1*(1 - b + b*dl/max(1,avgdl)))
        scores.append(sc)
    return scores

def whole_contained(chunk_span_range, gold_span):
    cs, ce = chunk_span_range; gs, ge = gold_span
    return cs <= gs and ge <= ce

def overlaps(chunk_span_range, gold_span):
    cs, ce = chunk_span_range; gs, ge = gold_span
    return cs < ge and gs < ce

def run_cell(seed, chunk_size, overlap, span_len, n_docs, doc_len, k_list, query_frac=0.5, topic_noise=2):
    rng = random.Random(seed*100003 + chunk_size*131 + overlap*17 + span_len)
    split_count = 0
    # per-k tallies
    recall = {k:0 for k in k_list}; comp = {k:0 for k in k_list}
    for gid in range(n_docs):
        tokens, gold_span, gold = make_doc(rng, span_len, doc_len, gid)
        chs = chunk(tokens, chunk_size, overlap)
        # split_rate: does ANY chunk contain the whole span?
        any_whole = any(whole_contained((s,e), gold_span) for (s,e,_) in chs)
        if not any_whole: split_count += 1
        # query = subset of gold tokens (a fragment may match) + topic-noise distractors
        nq = max(1, int(span_len*query_frac))
        qtok = rng.sample(gold, nq) + [rng.choice(DISTRACT) for _ in range(topic_noise)]
        scores = bm25_scores(chs, qtok)
        order = sorted(range(len(chs)), key=lambda i:(-scores[i], i))
        for k in k_list:
            topk = order[:k]
            r = any(overlaps((chs[i][0],chs[i][1]), gold_span) for i in topk)
            c = any(whole_contained((chs[i][0],chs[i][1]), gold_span) for i in topk)
            if r: recall[k]+=1
            if c: comp[k]+=1
    rows=[]
    for k in k_list:
        rows.append(dict(seed=seed, chunk_size=chunk_size, overlap=overlap, span_len=span_len,
                         k=k, n_docs=n_docs, doc_len=doc_len,
                         split_rate=split_count/n_docs,
                         recall=recall[k]/n_docs, completeness=comp[k]/n_docs,
                         overcount=(recall[k]-comp[k])/n_docs))
    return rows

def main():
    t0=time.time()
    SEEDS = list(range(8)); N_DOCS=200; DOC_LEN=300
    CHUNK_SIZES=[32,64,128]; OVERLAPS=[0,8,16,32,64]; SPAN_LENS=[8,16,32]; KS=[1,3,5,10]
    seed_rows=[]
    cells=0
    for cs in CHUNK_SIZES:
      for ov in OVERLAPS:
        if ov>=cs: continue
        for sl in SPAN_LENS:
          for sd in SEEDS:
            seed_rows.extend(run_cell(sd, cs, ov, sl, N_DOCS, DOC_LEN, KS))
            cells+=1
      log(f"chunk_size={cs} done, cells so far={cells}, t={time.time()-t0:.1f}s")
    # write per-seed
    fields=list(seed_rows[0].keys())
    with open(os.path.join(RES,"seeds.csv"),"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(seed_rows)
    # aggregate across seeds -> sweep.csv with mean + 95% CI half-width (t~ via std/sqrt(n)*1.96)
    from statistics import mean, pstdev
    agg={}
    for r in seed_rows:
        key=(r["chunk_size"],r["overlap"],r["span_len"],r["k"])
        agg.setdefault(key,[]).append(r)
    sweep=[]
    for key,rs in sorted(agg.items()):
        cs,ov,sl,k=key
        oc=[x["overcount"] for x in rs]; rc=[x["recall"] for x in rs]
        cm=[x["completeness"] for x in rs]; sr=[x["split_rate"] for x in rs]
        n=len(oc); ci=1.96*(pstdev(oc)/math.sqrt(n)) if n>1 else 0.0
        sweep.append(dict(chunk_size=cs,overlap=ov,span_len=sl,k=k,n_seeds=n,
            split_rate=round(mean(sr),4), recall=round(mean(rc),4),
            completeness=round(mean(cm),4), overcount=round(mean(oc),4),
            overcount_ci95=round(ci,4), overcount_lo=round(mean(oc)-ci,4)))
    with open(os.path.join(RES,"sweep.csv"),"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(sweep[0].keys())); w.writeheader(); w.writerows(sweep)
    log(f"DONE cells={cells} rows={len(seed_rows)} sweep={len(sweep)} t={time.time()-t0:.1f}s")

if __name__=="__main__":
    main()
