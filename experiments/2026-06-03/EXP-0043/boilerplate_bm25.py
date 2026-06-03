#!/usr/bin/env python3
"""EXP-0043 / CLAIM-0044: shared-boilerplate BM25 answer-rank inverted-U.
Stdlib only, SERIAL, CPU. See PRE_REGISTRATION.md.
"""
import math, random, csv, os, sys, time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RES  = os.path.join(HERE, "results")
LOGS = os.path.join(HERE, "logs")
os.makedirs(RES, exist_ok=True); os.makedirs(LOGS, exist_ok=True)

K1, B = 1.2, 0.75

# ---------- standard BM25 (stdlib) ----------
def idf(N, df):
    # Robertson/Sparck-Jones add-1 (non-negative) variant
    return math.log((N - df + 0.5) / (df + 0.5) + 1.0)

def build_index(docs):
    """docs: list[list[str]]. returns (N, avgdl, df, doclens)."""
    N = len(docs)
    doclens = [len(d) for d in docs]
    avgdl = sum(doclens) / N if N else 0.0
    df = Counter()
    for d in docs:
        for t in set(d):
            df[t] += 1
    return N, avgdl, df, doclens

def bm25_score(query_terms, doc_counter, doclen, N, avgdl, df):
    s = 0.0
    for t in query_terms:
        d = df.get(t, 0)
        if d == 0:
            continue
        f = doc_counter.get(t, 0)
        if f == 0:
            continue
        denom = f + K1 * (1.0 - B + B * doclen / avgdl)
        s += idf(N, d) * (f * (K1 + 1.0)) / denom
    return s

def rank_answer(docs, query_terms, answer_id):
    """Return (rank(1-based), answer_score, top_distractor_score_excl_answer)."""
    N, avgdl, df, doclens = build_index(docs)
    counters = [Counter(d) for d in docs]
    scores = []
    for i in range(N):
        scores.append((bm25_score(query_terms, counters[i], doclens[i], N, avgdl, df), i))
    # sort by score desc, tie-break by doc id asc (deterministic)
    scores.sort(key=lambda x: (-x[0], x[1]))
    rank = None; ans_score = None
    for pos, (sc, i) in enumerate(scores, start=1):
        if i == answer_id:
            rank = pos; ans_score = sc
            break
    # top score among non-answer docs
    top_other = max(sc for sc, i in scores if i != answer_id)
    return rank, ans_score, top_other, avgdl, df, doclens[answer_id]

# ---------- Zipf sampler (stdlib) ----------
def make_zipf_sampler(vocab, s, rng):
    # weights ~ 1/rank^s
    n = len(vocab)
    weights = [1.0 / ((r + 1) ** s) for r in range(n)]
    cum = []
    acc = 0.0
    for w in weights:
        acc += w; cum.append(acc)
    total = cum[-1]
    def sample():
        x = rng.random() * total
        # binary search
        lo, hi = 0, n - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cum[mid] < x: lo = mid + 1
            else: hi = mid
        return vocab[lo]
    return sample

# ---------- corpus construction ----------
def build_corpus(seed, N=2000, V=3000, zipf_s=1.07, sent_per_doc=5, words_per_sent=10,
                 n_query_terms=5, n_distractors=30):
    rng = random.Random(seed)
    content_vocab = ["c%d" % i for i in range(V)]
    samp = make_zipf_sampler(content_vocab, zipf_s, rng)

    # query terms: pick rare-ish content tokens (from the tail) so they are discriminative
    # use deterministic tail slice + shuffle by seed
    tail = content_vocab[V - 500:]  # rarer tokens
    rng.shuffle(tail)
    query_terms = tail[:n_query_terms]
    qset = set(query_terms)

    dl = sent_per_doc * words_per_sent  # base content length

    docs = []
    answer_id = rng.randrange(N)
    distractor_ids = set()
    while len(distractor_ids) < n_distractors:
        j = rng.randrange(N)
        if j != answer_id:
            distractor_ids.add(j)

    for i in range(N):
        toks = [samp() for _ in range(dl)]
        if i == answer_id:
            # plant ALL query terms (a few copies of each to ensure dominance) + filler
            for q in query_terms:
                # replace a couple positions with the query term
                for _ in range(2):
                    toks[rng.randrange(dl)] = q
        elif i in distractor_ids:
            # plant a random SUBSET of query terms (not all) -> plausible competitor
            k = rng.randint(1, max(1, n_query_terms - 1))
            sub = rng.sample(query_terms, k)
            for q in sub:
                for _ in range(2):
                    toks[rng.randrange(dl)] = q
        docs.append(toks)
    return docs, query_terms, answer_id, sorted(distractor_ids)

def make_boilerplate(L, b_vocab_n=40, seed_off=0):
    # fixed boilerplate token pool, disjoint from content vocab ("bp%d")
    pool = ["bp%d" % i for i in range(b_vocab_n)]
    if L <= 0:
        return []
    # deterministic: repeat the pool to length L (truncate). identical block for everyone.
    out = []
    while len(out) < L:
        out.extend(pool)
    return out[:L]

# ---------- sanity unit check ----------
def sanity_check():
    lines = []
    lines.append("=== BM25 sanity unit check (k1=%.2f b=%.2f) ===" % (K1, B))
    # tiny hand-checkable corpus
    docs = [
        ["a", "b", "c"],        # doc0
        ["a", "a", "d"],        # doc1
        ["e", "f", "g", "a"],   # doc2
    ]
    query = ["a"]
    N, avgdl, df, doclens = build_index(docs)
    lines.append("docs=%r" % docs)
    lines.append("N=%d avgdl=%.6f doclens=%r df['a']=%d" % (N, avgdl, doclens, df['a']))
    # hand compute
    df_a = 3  # 'a' appears in all 3 docs
    assert df['a'] == df_a, "df mismatch"
    idf_a = math.log((N - df_a + 0.5)/(df_a + 0.5) + 1.0)
    lines.append("idf('a') = ln((3-3+0.5)/(3+0.5)+1) = %.9f" % idf_a)
    avgdl_hand = (3 + 3 + 4) / 3.0
    assert abs(avgdl - avgdl_hand) < 1e-12
    def hand(f, dl):
        return idf_a * (f*(K1+1.0)) / (f + K1*(1.0 - B + B*dl/avgdl_hand))
    exp = [hand(1,3), hand(2,3), hand(1,4)]
    got = [bm25_score(query, Counter(d), len(d), N, avgdl, df) for d in docs]
    for i,(e,g) in enumerate(zip(exp,got)):
        lines.append("doc%d: hand=%.12f impl=%.12f diff=%.2e" % (i,e,g,abs(e-g)))
        assert abs(e-g) < 1e-9, "BM25 impl mismatch doc%d" % i
    # doc1 has f=2 for 'a' -> should outscore doc0 (f=1, same len) and doc2 (f=1, longer)
    order = sorted(range(3), key=lambda i: -got[i])
    lines.append("rank order by score: %r (expect doc1 first)" % order)
    assert order[0] == 1, "expected doc1 to rank #1"
    lines.append("SANITY PASS: impl matches hand calc to <1e-9 and ranking correct.")
    return "\n".join(lines)

# ---------- main sweep ----------
def main():
    t0 = time.time()
    sanity = sanity_check()
    with open(os.path.join(RES, "sanity.txt"), "w") as f:
        f.write(sanity + "\n")
    print(sanity)
    sys.stdout.flush()

    L_VALUES = [0, 8, 16, 32, 64, 128, 256, 512, 1024]
    FRACS = [0.0, 0.25, 1.0]   # share boilerplate with this fraction of distractors (answer always gets it)
    SEEDS = list(range(20))
    B_VOCAB_N = 40

    raw_path = os.path.join(RES, "raw_results.csv")
    rawf = open(raw_path, "w", newline="")
    w = csv.writer(rawf)
    w.writerow(["seed","frac","L","rank","answer_score","top_distractor_score",
                "bp_idf_mean","lennorm_answer","answer_len","n_docs_with_bp"])

    for seed in SEEDS:
        base_docs, query_terms, answer_id, distractor_ids = build_corpus(seed)
        bp_pool = ["bp%d" % i for i in range(B_VOCAB_N)]
        for frac in FRACS:
            # which distractors get boilerplate
            ndist = len(distractor_ids)
            n_bp_dist = int(round(frac * ndist))
            # deterministic subset given seed+frac
            rng2 = random.Random((seed << 8) ^ int(frac * 1000) ^ 0xABCD)
            bp_distractors = set(rng2.sample(distractor_ids, n_bp_dist)) if n_bp_dist > 0 else set()
            bp_doc_ids = {answer_id} | bp_distractors
            for L in L_VALUES:
                bp = make_boilerplate(L, B_VOCAB_N)
                docs = []
                for i, d in enumerate(base_docs):
                    if i in bp_doc_ids and L > 0:
                        docs.append(bp + d)   # prepend identical boilerplate
                    else:
                        docs.append(d)
                rank, ans_sc, top_other, avgdl, df, ans_len = rank_answer(docs, query_terms, answer_id)
                # mechanism: mean idf of boilerplate tokens that are actually present
                if L > 0:
                    N = len(docs)
                    idfs = [idf(N, df.get(t,0)) for t in bp_pool if df.get(t,0) > 0]
                    bp_idf_mean = sum(idfs)/len(idfs) if idfs else 0.0
                else:
                    bp_idf_mean = 0.0
                lennorm = (1.0 - B + B * ans_len / avgdl)
                w.writerow([seed, frac, L, rank, "%.6f"%ans_sc, "%.6f"%top_other,
                            "%.6f"%bp_idf_mean, "%.6f"%lennorm, ans_len, len(bp_doc_ids)])
        rawf.flush()
        print("seed %d done @ %.1fs" % (seed, time.time()-t0)); sys.stdout.flush()
    rawf.close()
    print("RAW written: %s  (elapsed %.1fs)" % (raw_path, time.time()-t0))

if __name__ == "__main__":
    main()
