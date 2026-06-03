#!/usr/bin/env python3
"""
EXP-0040 / CLAIM-0042 — doc-level near-dedup vs passage/n-gram span-match contamination gap.
L0: CPU-only, stdlib-only, SERIAL. Anti-circular: detectors read only TEXT; ground truth is the
generative embedding fact (which item-span we put into which doc). Negatives are wins.
"""
import random, csv, hashlib, os, time
from collections import defaultdict

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)

# ---- vocab / tokens ----
def make_vocab(n, prefix):
    return [f"{prefix}{i}" for i in range(n)]

DOC_VOCAB = make_vocab(4000, "d")      # background training vocab
ITEM_VOCAB = make_vocab(1200, "b")     # benchmark vocab (distinct slice)
SYN = make_vocab(1200, "s")            # synonym pool for paraphrase

# common phrases injected into docs AND occasionally near items -> innocent n-gram overlap
COMMON_PHRASES = [["the","of","and","in","to"][:1]]  # placeholder; real ones below
def make_common_phrases(rng, count, plen):
    ph = []
    pool = make_vocab(60, "c")  # small shared phrase vocab -> realistic recurring phrases
    for _ in range(count):
        ph.append([rng.choice(pool) for _ in range(plen)])
    return ph

def zipf_doc(rng, vocab, length, common_phrases, common_rate):
    toks = []
    while len(toks) < length:
        if common_phrases and rng.random() < common_rate:
            toks.extend(rng.choice(common_phrases))
        else:
            # zipf-ish: bias toward low indices
            idx = min(len(vocab)-1, int(rng.random()**2 * len(vocab)))
            toks.append(vocab[idx])
    return toks[:length]

def make_item(rng, length):
    return [rng.choice(ITEM_VOCAB) for _ in range(length)]

def paraphrase_span(rng, span, frac):
    out = list(span)
    nchg = int(len(span)*frac)
    idxs = rng.sample(range(len(span)), nchg) if nchg <= len(span) else range(len(span))
    for i in idxs:
        # synonym swap OR local reorder
        if rng.random() < 0.5:
            out[i] = rng.choice(SYN)
    # light reorder: swap a few adjacent pairs
    for _ in range(int(nchg*0.3)):
        j = rng.randrange(len(out)-1) if len(out) > 1 else 0
        out[j], out[j+1] = out[j+1], out[j]
    return out

# ---- detectors (text only) ----
def shingles(tokens, k):
    return set(tuple(tokens[i:i+k]) for i in range(len(tokens)-k+1)) if len(tokens) >= k else set()

def jaccard(a, b):
    if not a and not b: return 0.0
    u = len(a | b)
    return (len(a & b) / u) if u else 0.0

def doc_level_flag(doc_sh, item_sh, thresh):
    return jaccard(doc_sh, item_sh) >= thresh

def passage_level_flag(doc_kgram_set, item_kgrams, span_thresh):
    """fraction of item k-grams present anywhere in the doc's k-gram set >= span_thresh.
    (window=doc; equivalent to substring/n-gram contamination check at k-gram granularity).
    doc_kgram_set precomputed once per doc."""
    if not item_kgrams: return False
    hits = sum(1 for g in item_kgrams if g in doc_kgram_set)
    return (hits / len(item_kgrams)) >= span_thresh

def run_config(seed, doc_len, item_len, paraphrase, doc_thresh, span_thresh, ngram_k,
               N=300, M=60, contam_frac=0.2, common_rate=0.12):
    rng = random.Random(seed*100003 + doc_len*131 + int(paraphrase*1000)*17
                        + int(doc_thresh*100)*7 + int(span_thresh*100)*3 + ngram_k)
    common = make_common_phrases(rng, 40, ngram_k)  # phrases length == k => create k-gram collisions
    items = [make_item(rng, item_len) for _ in range(M)]
    item_kgrams = [shingles(it, ngram_k) for it in items]
    item_shingles = item_kgrams  # whole-item shingle set (same k) for doc-level jaccard

    n_contam = int(N*contam_frac)
    contam_doc_ids = set(rng.sample(range(N), n_contam))
    # truth: dict doc_id -> item_id embedded (the generative fact)
    truth = {}
    docs = []
    for d in range(N):
        base = zipf_doc(rng, DOC_VOCAB, doc_len, common, common_rate)
        if d in contam_doc_ids:
            it_id = rng.randrange(M)
            span = paraphrase_span(rng, items[it_id], paraphrase) if paraphrase > 0 else list(items[it_id])
            pos = rng.randrange(0, max(1, doc_len - len(span)))
            base = base[:pos] + span + base[pos+len(span):]
            base = base[:doc_len]
            truth[d] = it_id
        docs.append(base)

    doc_shingles = [shingles(dt, ngram_k) for dt in docs]

    # evaluate per (doc,item) pair only for pairs that matter:
    # truth pairs = embedded ones. For precision we must consider ALL flagged pairs.
    # To keep O(N*M) bounded we restrict the candidate item to the embedded item for truth recall,
    # but for FALSE POSITIVES we test each doc against ALL M items (so innocent overlap can fire).
    true_pairs = set((d, truth[d]) for d in truth)

    doc_flagged = set()
    pass_flagged = set()
    for d in range(N):
        ds = doc_shingles[d]   # precomputed doc k-gram set (reused for both detectors)
        for i in range(M):
            if doc_level_flag(ds, item_shingles[i], doc_thresh):
                doc_flagged.add((d, i))
            if passage_level_flag(ds, item_kgrams[i], span_thresh):
                pass_flagged.add((d, i))

    def recall(flagged):
        if not true_pairs: return 0.0
        return len(flagged & true_pairs) / len(true_pairs)
    def precision(flagged):
        if not flagged: return 1.0  # no flags => vacuously no false positives
        return len(flagged & true_pairs) / len(flagged)

    doc_recall = recall(doc_flagged)
    pass_recall = recall(pass_flagged)
    doc_prec = precision(doc_flagged)
    pass_prec = precision(pass_flagged)

    # MISS GAP: true pairs caught by passage but missed by doc-level
    caught_pass_missed_doc = (pass_flagged & true_pairs) - doc_flagged
    miss_gap = len(caught_pass_missed_doc) / len(true_pairs) if true_pairs else 0.0

    # reported contamination RATE (doc-level granularity: a doc is "contaminated" if flagged with ANY item)
    docs_flagged_doc = set(d for (d,i) in doc_flagged)
    docs_flagged_pass = set(d for (d,i) in pass_flagged)
    true_docs = set(truth.keys())
    rate_true = len(true_docs)/N
    rate_doc = len(docs_flagged_doc)/N
    rate_pass = len(docs_flagged_pass)/N
    # precision at the doc level for the rate (are flagged docs truly contaminated?)
    doc_rate_prec = (len(docs_flagged_doc & true_docs)/len(docs_flagged_doc)) if docs_flagged_doc else 1.0
    pass_rate_prec = (len(docs_flagged_pass & true_docs)/len(docs_flagged_pass)) if docs_flagged_pass else 1.0

    return dict(seed=seed, doc_len=doc_len, item_len=item_len, span_ratio=round(item_len/doc_len,4),
                paraphrase=paraphrase, doc_thresh=doc_thresh, span_thresh=span_thresh, ngram_k=ngram_k,
                doc_recall=round(doc_recall,4), pass_recall=round(pass_recall,4),
                doc_prec=round(doc_prec,4), pass_prec=round(pass_prec,4),
                miss_gap=round(miss_gap,4),
                rate_true=round(rate_true,4), rate_doc=round(rate_doc,4), rate_pass=round(rate_pass,4),
                doc_rate_prec=round(doc_rate_prec,4), pass_rate_prec=round(pass_rate_prec,4),
                n_true_pairs=len(true_pairs), n_doc_flagged=len(doc_flagged), n_pass_flagged=len(pass_flagged))

def main():
    t0=time.time()
    SEEDS = list(range(7))
    ITEM_LEN = 50
    doc_lens = [100, 500, 2500, 5000]   # span_ratio 0.5,0.1,0.02,0.01
    paraphrases = [0.0, 0.2, 0.4]
    doc_threshs = [0.5, 0.8]
    span_threshs = [0.6, 0.8]
    NGRAM_K = 8
    rows=[]
    cfg_count=0
    for dl in doc_lens:
        for pp in paraphrases:
            for dth in doc_threshs:
                for sth in span_threshs:
                    cfg_count+=1
                    for s in SEEDS:
                        rows.append(run_config(s, dl, ITEM_LEN, pp, dth, sth, NGRAM_K))
        print(f"  done doc_len={dl} elapsed={time.time()-t0:.1f}s", flush=True)
    # write raw
    raw_path = os.path.join(OUT,"raw_results.csv")
    with open(raw_path,"w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    # aggregate across seeds
    agg=defaultdict(list)
    keys=("doc_len","item_len","span_ratio","paraphrase","doc_thresh","span_thresh","ngram_k")
    for r in rows:
        agg[tuple(r[k] for k in keys)].append(r)
    def mean(xs): return sum(xs)/len(xs)
    def std(xs):
        m=mean(xs); return (sum((x-m)**2 for x in xs)/len(xs))**0.5
    sumrows=[]
    metric_cols=["doc_recall","pass_recall","doc_prec","pass_prec","miss_gap",
                 "rate_true","rate_doc","rate_pass","doc_rate_prec","pass_rate_prec"]
    for k,group in agg.items():
        row=dict(zip(keys,k)); row["n_seeds"]=len(group)
        for c in metric_cols:
            vals=[g[c] for g in group]
            row[c+"_mean"]=round(mean(vals),4); row[c+"_std"]=round(std(vals),4)
        sumrows.append(row)
    sumrows.sort(key=lambda r:(r["span_ratio"], r["paraphrase"], r["doc_thresh"], r["span_thresh"]))
    sum_path=os.path.join(OUT,"summary.csv")
    with open(sum_path,"w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(sumrows[0].keys())); w.writeheader(); w.writerows(sumrows)
    print(f"DONE {len(rows)} rows, {len(sumrows)} configs, {len(SEEDS)} seeds in {time.time()-t0:.1f}s")
    print("RAW:",raw_path)
    print("SUM:",sum_path)

if __name__=="__main__":
    main()
