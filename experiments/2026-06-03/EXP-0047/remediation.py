#!/usr/bin/env python3
"""EXP-0047 / CLAIM-0045: committee#1 L0 remediation.
Reuses EXP-0043's verified BM25 + EXP-0044's corpus/template build. Stdlib, SERIAL, CPU.
Adds: (1) b-sweep parameterized BM25, (2) BM25L variant, (3) score-margin. See PRE_REGISTRATION.md.
"""
import math, random, csv, os, sys, time, importlib.util
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RES  = os.path.join(HERE, "results"); LOGS = os.path.join(HERE, "logs")
os.makedirs(RES, exist_ok=True); os.makedirs(LOGS, exist_ok=True)

# import verified BM25 + corpus builder from EXP-0043
E43 = os.path.join(os.path.dirname(HERE), "EXP-0043", "boilerplate_bm25.py")
spec = importlib.util.spec_from_file_location("bm25mod", E43)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

K1 = 1.2
idf = m.idf            # ln((N-df+0.5)/(df+0.5)+1)  -- our baseline non-negative idf
build_index = m.build_index
build_corpus = m.build_corpus

# ---------- parameterized scoring ----------
def bm25_score_b(query_terms, doc_counter, doclen, N, avgdl, df, b):
    """Standard BM25 with explicit b (k1=K1). b=0 => no length normalization."""
    s = 0.0
    Bnorm = (1.0 - b + b * doclen / avgdl)
    for t in query_terms:
        d = df.get(t, 0)
        if d == 0: continue
        f = doc_counter.get(t, 0)
        if f == 0: continue
        denom = f + K1 * Bnorm
        s += idf(N, d) * (f * (K1 + 1.0)) / denom
    return s

def bm25l_score(query_terms, doc_counter, doclen, N, avgdl, df, b=0.75, delta=0.5):
    """BM25L (Lv & Zhai, CIKM 2011). c = f / B(D); score = IDF * (k1+1)*(c+delta)/(k1 + c + delta).
    Uses the SAME baseline idf as our BM25 for a controlled comparison."""
    s = 0.0
    Bnorm = (1.0 - b + b * doclen / avgdl)
    for t in query_terms:
        d = df.get(t, 0)
        if d == 0: continue
        f = doc_counter.get(t, 0)
        if f == 0: continue
        c = f / Bnorm
        s += idf(N, d) * ((K1 + 1.0) * (c + delta)) / (K1 + c + delta)
    return s

def rank_with(scorer, docs, query_terms, answer_id):
    """Generic ranker; scorer(query, counter, doclen, N, avgdl, df) -> score.
    Returns (rank, answer_score, top_other_score, avgdl, df, answer_len)."""
    N, avgdl, df, doclens = build_index(docs)
    counters = [Counter(d) for d in docs]
    scored = []
    for i in range(N):
        scored.append((scorer(query_terms, counters[i], doclens[i], N, avgdl, df), i))
    scored.sort(key=lambda x: (-x[0], x[1]))
    rank = None; ans_score = None
    for pos, (sc, i) in enumerate(scored, start=1):
        if i == answer_id:
            rank = pos; ans_score = sc; break
    top_other = max(sc for sc, i in scored if i != answer_id)
    return rank, ans_score, top_other, avgdl, df, doclens[answer_id]

# ---------- template (identical to EXP-0044) ----------
def apply_template(base_docs, tmpl_qterms, L, tmpl_dist):
    if L > 0:
        rep = (tmpl_qterms * ((L // len(tmpl_qterms)) + 1))[:L]
    else:
        rep = []
    docs = []
    for i, d in enumerate(base_docs):
        if i in tmpl_dist and L > 0:
            docs.append(rep + d)        # ONLY distractors; answer stays clean
        else:
            docs.append(d)
    return docs

def templated_set(seed, frac, t_q, distractor_ids):
    ndist = len(distractor_ids)
    n_tmpl = int(round(frac * ndist))
    rng2 = random.Random((seed << 10) ^ int(frac*1000) ^ (t_q*7) ^ 0x5151)
    return set(rng2.sample(distractor_ids, n_tmpl)) if n_tmpl > 0 else set()

# ---------- sanity / hand checks ----------
def sanity():
    lines = []
    base = m.sanity_check()   # re-run EXP-0043's verified BM25 unit check
    lines.append(base)
    lines.append("")
    lines.append("=== EXP-0047 additional checks ===")
    # tiny corpus
    docs = [["a","b","c"], ["a","a","d"], ["e","f","g","a"]]
    query = ["a"]
    N, avgdl, df, doclens = build_index(docs)
    cs = [Counter(d) for d in docs]
    # (1) bm25_score_b with b=0.75 must EQUAL the imported m.bm25_score (which fixes b=0.75)
    for i,d in enumerate(docs):
        a = bm25_score_b(query, cs[i], doclens[i], N, avgdl, df, 0.75)
        bb = m.bm25_score(query, cs[i], doclens[i], N, avgdl, df)
        lines.append("doc%d: bm25_score_b(b=0.75)=%.12f  m.bm25_score=%.12f  diff=%.2e" % (i,a,bb,abs(a-bb)))
        assert abs(a-bb) < 1e-12, "b=0.75 must match baseline"
    # (2) b=0: length-norm OFF -> denom = f + k1, independent of doclen.
    #     doc1 (f=2) must score same regardless of how long we pad it.
    d1_short = bm25_score_b(query, Counter(["a","a","d"]), 3, N, avgdl, df, 0.0)
    d1_long  = bm25_score_b(query, Counter(["a","a"]+["z"]*100), 102, N, avgdl, df, 0.0)
    lines.append("b=0: doc score for f=2 short(len3)=%.9f long(len102)=%.9f diff=%.2e (must be ~0)"
                 % (d1_short, d1_long, abs(d1_short-d1_long)))
    assert abs(d1_short - d1_long) < 1e-9, "b=0 must remove length dependence"
    # (3) BM25L hand-check: delta=0 -> c/(k1+c) shape; verify formula by hand on doc0 (f=1,len3,b=0.75)
    Bnorm = (1-0.75+0.75*3/avgdl); c = 1.0/Bnorm
    idf_a = idf(N, df['a'])
    hand_l = idf_a * ((K1+1.0)*(c+0.5))/(K1 + c + 0.5)
    impl_l = bm25l_score(query, cs[0], 3, N, avgdl, df, 0.75, 0.5)
    lines.append("BM25L doc0 hand=%.12f impl=%.12f diff=%.2e" % (hand_l, impl_l, abs(hand_l-impl_l)))
    assert abs(hand_l-impl_l) < 1e-12, "BM25L formula mismatch"
    # (4) BM25L lower-bounds long-doc penalty: for a matching term in a LONG doc, BM25L >= BM25.
    longlen = 200
    bl = bm25l_score(query, Counter(["a"]+["z"]*199), longlen, N, avgdl, df, 0.75, 0.5)
    bm = bm25_score_b(query, Counter(["a"]+["z"]*199), longlen, N, avgdl, df, 0.75)
    lines.append("long doc (len200, f=1): BM25L=%.9f  BM25=%.9f  (BM25L>=BM25? %s)" % (bl, bm, bl>=bm))
    assert bl >= bm - 1e-12, "BM25L should not over-penalize long docs vs BM25"
    lines.append("EXP-0047 SANITY PASS: b-param matches baseline; b=0 removes len-dep; BM25L hand-verified; BM25L>=BM25 on long doc.")
    return "\n".join(lines)

# ---------- main ----------
def main():
    t0 = time.time()
    s = sanity()
    with open(os.path.join(RES, "sanity.txt"), "w") as f: f.write(s + "\n")
    print(s); sys.stdout.flush()

    SEEDS = list(range(20))
    L_VALUES = [0, 4, 8, 16, 32, 64, 128, 256, 512]

    # ---- REMEDIATION 1: b-SWEEP on strongest cell (frac=1.0, T_qterms=2) ----
    B_VALUES = [0.0, 0.25, 0.5, 0.75, 1.0]
    bsw = open(os.path.join(RES, "bsweep.csv"), "w", newline=""); wb = csv.writer(bsw)
    wb.writerow(["seed","b","L","rank","answer_score","top_distractor_score","dist_lennorm_mean"])
    # ---- REMEDIATION 3: score-margin (strongest cell, standard BM25 b=0.75) -> reuse b=0.75 rows ----
    for seed in SEEDS:
        base_docs, query_terms, answer_id, distractor_ids = build_corpus(seed)
        tmpl_qterms = query_terms[:2]
        tmpl_dist = templated_set(seed, 1.0, 2, distractor_ids)
        for b in B_VALUES:
            for L in L_VALUES:
                docs = apply_template(base_docs, tmpl_qterms, L, tmpl_dist)
                rank, ans_sc, top_other, avgdl, df, ans_len = rank_with(
                    lambda q,c,dl,N,ad,dff: bm25_score_b(q,c,dl,N,ad,dff,b), docs, query_terms, answer_id)
                if tmpl_dist and L > 0:
                    lns = [(1.0 - b + b*len(docs[i])/avgdl) for i in tmpl_dist]
                    dln = sum(lns)/len(lns)
                else:
                    dln = (1.0 - b + b*1.0)
                wb.writerow([seed, b, L, rank, "%.6f"%ans_sc, "%.6f"%top_other, "%.6f"%dln])
        bsw.flush()
        if seed % 5 == 0: print("bsweep seed %d @ %.1fs" % (seed, time.time()-t0)); sys.stdout.flush()
    bsw.close()
    print("bsweep done @ %.1fs" % (time.time()-t0)); sys.stdout.flush()

    # ---- REMEDIATION 2: BM25L on FULL grid (L x frac x T_qterms) ----
    FRACS = [0.5, 1.0]; T_QS = [1, 2]
    blf = open(os.path.join(RES, "bm25l_raw.csv"), "w", newline=""); wl = csv.writer(blf)
    wl.writerow(["seed","frac","t_qterms","L","rank","answer_score","top_distractor_score"])
    for seed in SEEDS:
        base_docs, query_terms, answer_id, distractor_ids = build_corpus(seed)
        for t_q in T_QS:
            tmpl_qterms = query_terms[:t_q]
            for frac in FRACS:
                tmpl_dist = templated_set(seed, frac, t_q, distractor_ids)
                for L in L_VALUES:
                    docs = apply_template(base_docs, tmpl_qterms, L, tmpl_dist)
                    rank, ans_sc, top_other, avgdl, df, ans_len = rank_with(
                        lambda q,c,dl,N,ad,dff: bm25l_score(q,c,dl,N,ad,dff,0.75,0.5), docs, query_terms, answer_id)
                    wl.writerow([seed, frac, t_q, L, rank, "%.6f"%ans_sc, "%.6f"%top_other])
        blf.flush()
        if seed % 5 == 0: print("bm25l seed %d @ %.1fs" % (seed, time.time()-t0)); sys.stdout.flush()
    blf.close()
    print("ALL done @ %.1fs" % (time.time()-t0)); sys.stdout.flush()

if __name__ == "__main__":
    main()
