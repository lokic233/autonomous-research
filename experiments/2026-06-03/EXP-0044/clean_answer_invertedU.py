#!/usr/bin/env python3
"""EXP-0044 / CLAIM-0045: clean-answer inverted-U under query-term-bearing DISTRACTOR template.
Reuses EXP-0043's verified BM25 + Zipf corpus. Stdlib only, SERIAL, CPU. See PRE_REGISTRATION.md.
"""
import math, random, csv, os, sys, time, importlib.util
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RES  = os.path.join(HERE, "results"); LOGS = os.path.join(HERE, "logs")
os.makedirs(RES, exist_ok=True); os.makedirs(LOGS, exist_ok=True)

# import the verified BM25 + corpus builder from EXP-0043
E43 = os.path.join(os.path.dirname(HERE), "EXP-0043", "boilerplate_bm25.py")
spec = importlib.util.spec_from_file_location("bm25mod", E43)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

K1, B = m.K1, m.B  # 1.2, 0.75
idf = m.idf

def main():
    t0 = time.time()
    # re-run sanity from the imported (verified) impl
    sanity = m.sanity_check()
    with open(os.path.join(RES, "sanity.txt"), "w") as f:
        f.write(sanity + "\n")
    print(sanity); sys.stdout.flush()

    L_VALUES   = [0, 4, 8, 16, 32, 64, 128, 256, 512]
    FRACS      = [0.5, 1.0]
    T_QTERMS_S = [1, 2]
    SEEDS      = list(range(20))

    raw_path = os.path.join(RES, "raw_results.csv")
    rawf = open(raw_path, "w", newline=""); w = csv.writer(rawf)
    w.writerow(["seed","frac","t_qterms","L","rank","answer_score","top_distractor_score",
                "qterm_idf_mean","dist_lennorm_mean","answer_len","n_templated_distractors"])

    for seed in SEEDS:
        base_docs, query_terms, answer_id, distractor_ids = m.build_corpus(seed)
        for t_q in T_QTERMS_S:
            tmpl_qterms = query_terms[:t_q]   # template mentions first t_q query terms
            for frac in FRACS:
                ndist = len(distractor_ids)
                n_tmpl = int(round(frac * ndist))
                rng2 = random.Random((seed << 10) ^ int(frac*1000) ^ (t_q*7) ^ 0x5151)
                tmpl_dist = set(rng2.sample(distractor_ids, n_tmpl)) if n_tmpl > 0 else set()
                for L in L_VALUES:
                    # build template of length L by repeating the query-term subset
                    if L > 0:
                        rep = (tmpl_qterms * ((L // len(tmpl_qterms)) + 1))[:L]
                    else:
                        rep = []
                    docs = []
                    for i, d in enumerate(base_docs):
                        if i in tmpl_dist and L > 0:   # ONLY distractors; answer stays clean
                            docs.append(rep + d)
                        else:
                            docs.append(d)
                    rank, ans_sc, top_other, avgdl, df, ans_len = m.rank_answer(docs, query_terms, answer_id)
                    # mechanism: IDF of the template query terms (collapses as L spreads them)
                    N = len(docs)
                    q_idfs = [idf(N, df.get(t, 0)) for t in tmpl_qterms if df.get(t, 0) > 0]
                    qterm_idf_mean = sum(q_idfs)/len(q_idfs) if q_idfs else 0.0
                    # mean length-norm factor for templated distractors
                    if tmpl_dist and L > 0:
                        lns = [(1.0 - B + B*len(docs[i])/avgdl) for i in tmpl_dist]
                        dist_lennorm_mean = sum(lns)/len(lns)
                    else:
                        dist_lennorm_mean = (1.0 - B + B*1.0)  # ~1 ref
                    w.writerow([seed, frac, t_q, L, rank, "%.6f"%ans_sc, "%.6f"%top_other,
                                "%.6f"%qterm_idf_mean, "%.6f"%dist_lennorm_mean, ans_len, len(tmpl_dist)])
        rawf.flush()
        print("seed %d done @ %.1fs" % (seed, time.time()-t0)); sys.stdout.flush()
    rawf.close()
    print("RAW written: %s  (elapsed %.1fs)" % (raw_path, time.time()-t0))

if __name__ == "__main__":
    main()
