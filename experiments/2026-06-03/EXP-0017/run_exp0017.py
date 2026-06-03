#!/usr/bin/env python3
# EXP-0017 (L0, CLAIM-0013) — in-context redundancy gate, anti-circular measurement study.
# stdlib-only, SERIAL. Honest pipeline. See PRE_REGISTRATION.md.
import random, math, csv, os, hashlib
from collections import deque, Counter

ART = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ART, "results")
os.makedirs(RES, exist_ok=True)

# ---------- vocabulary / corpus ----------
FILLER = ("the a of to in on with for and or but agent system step turn note recall context window "
          "we then thus user query result value data point info detail summary plan action observe").split()

def make_corpus(rng, N_items, core_len=6, vocab=400):
    # each item has a CORE keyword set (its semantic identity in text) + we can paraphrase by swapping
    # some core words for synonyms drawn from a per-item synonym pool. item_id is the LATENT label.
    words = [f"w{i}" for i in range(vocab)]
    items = []
    for iid in range(N_items):
        core = rng.sample(words, core_len)
        syn  = rng.sample(words, core_len)  # paraphrase pool (disjoint-ish surface forms)
        items.append({"iid": iid, "core": core, "syn": syn})
    return items

def render_span(rng, item, paraphrase, span_len=18):
    # Build a text span for an item. If paraphrase, replace a large fraction of core words with synonyms
    # (so lexical overlap with the canonical query is LOW) — models a redundant-but-reworded recall.
    core = item["core"]
    if paraphrase:
        # replace ~70% of core tokens with synonyms
        toks = []
        for i, c in enumerate(core):
            if rng.random() < 0.70:
                toks.append(item["syn"][i])
            else:
                toks.append(c)
    else:
        toks = list(core)
    # pad with filler noise
    pad = [rng.choice(FILLER) for _ in range(span_len - len(toks))]
    out = toks + pad
    rng.shuffle(out)
    return out

def render_query(rng, item):
    # The query always uses the CANONICAL core tokens (the agent asks in canonical form) + light filler.
    # Detectability hinges on whether the RESIDENT span was paraphrased.
    toks = list(item["core"]) + [rng.choice(FILLER) for _ in range(4)]
    rng.shuffle(toks)
    return toks

# ---------- cheap check signals (realizable; NO item-id) ----------
def jaccard(a_set, b_set):
    if not a_set and not b_set: return 0.0
    u = len(a_set | b_set)
    return len(a_set & b_set) / u if u else 0.0

DIM = 64
def hashed_vec(tokens):
    v = [0.0]*DIM
    for t in tokens:
        h = int(hashlib.md5(t.encode()).hexdigest(), 16)
        idx = h % DIM
        sign = 1.0 if (h >> 8) & 1 else -1.0
        v[idx] += sign
    return v

def cosine(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(y*y for y in b))
    if na==0 or nb==0: return 0.0
    return dot/(na*nb)

def check_score(query_toks, resident_spans, mode="jaccard"):
    # max overlap of query vs any resident span. resident_spans = list of (token_list)
    qset = set(query_toks)
    best = 0.0
    if mode == "jaccard":
        for sp in resident_spans:
            best = max(best, jaccard(qset, set(sp)))
    else:  # hashed embedding cosine
        qv = hashed_vec(query_toks)
        for sp in resident_spans:
            best = max(best, cosine(qv, hashed_vec(sp)))
    return best

# ---------- trace generation ----------
def gen_trace(rng, T, N_items, W, p_repeat, paraphrase_rate, span_len=18):
    """Returns list of decision records. Each retrieval-decision turn yields:
       {gt_redundant, query_toks, resident_spans(snapshot), iid}
       GT redundancy = target iid is resident in the window (item-id bookkeeping, INDEPENDENT of text)."""
    items = make_corpus(rng, N_items)
    # window holds entries: {"iid":..., "toks":[...]} ; bounded to W
    window = deque(maxlen=W)
    recent_items = deque(maxlen=W)  # items recently targeted (for p_repeat sampling)
    records = []
    for t in range(T):
        # choose target need
        if recent_items and rng.random() < p_repeat:
            target = rng.choice(list(recent_items))
        else:
            target = rng.randrange(N_items)
        item = items[target]
        # GT redundancy: is an entry with this iid currently resident?
        resident_iids = [e["iid"] for e in window]
        gt_red = (target in resident_iids)
        query_toks = render_query(rng, item)
        resident_spans = [e["toks"] for e in window]  # snapshot BEFORE this turn's retrieval
        records.append({
            "iid": target,
            "gt_redundant": 1 if gt_red else 0,
            "query_toks": query_toks,
            "resident_spans": resident_spans,
        })
        # NOW the agent (in always-retrieve world) retrieves -> a span gets added to window.
        # If the target was already resident, the freshly-retrieved span is a (possibly paraphrased) dup.
        paraphrase = (rng.random() < paraphrase_rate)
        span = render_span(rng, item, paraphrase, span_len)
        window.append({"iid": target, "toks": span})
        recent_items.append(target)
    return records

# ---------- metrics ----------
def roc_auc(scores, labels):
    # Mann-Whitney U based AUC. labels in {0,1}.
    pos = [s for s,l in zip(scores,labels) if l==1]
    neg = [s for s,l in zip(scores,labels) if l==0]
    if not pos or not neg: return float('nan')
    # rank-based
    paired = sorted(zip(scores, labels))
    # assign average ranks
    n = len(paired); ranks = [0.0]*n
    i = 0
    while i < n:
        j = i
        while j+1 < n and paired[j+1][0]==paired[i][0]:
            j += 1
        avg = (i + j)/2.0 + 1.0
        for k in range(i, j+1): ranks[k] = avg
        i = j+1
    sum_ranks_pos = sum(r for r,(s,l) in zip(ranks, paired) if l==1)
    np_, nn = len(pos), len(neg)
    auc = (sum_ranks_pos - np_*(np_+1)/2.0) / (np_*nn)
    return auc

def prf_at_tau(scores, labels, tau):
    tp=fp=fn=tn=0
    for s,l in zip(scores,labels):
        pred = 1 if s>=tau else 0
        if pred==1 and l==1: tp+=1
        elif pred==1 and l==0: fp+=1
        elif pred==0 and l==1: fn+=1
        else: tn+=1
    prec = tp/(tp+fp) if (tp+fp) else float('nan')
    rec  = tp/(tp+fn) if (tp+fn) else float('nan')
    f1 = (2*prec*rec/(prec+rec)) if (prec and rec and not math.isnan(prec) and not math.isnan(rec) and (prec+rec)>0) else 0.0
    return prec, rec, f1, tp, fp, fn, tn

def bootstrap_ci(vals, fn, B=2000, seed=0):
    rng = random.Random(seed)
    n = len(vals); out=[]
    for _ in range(B):
        sample = [vals[rng.randrange(n)] for _ in range(n)]
        out.append(fn(sample))
    out.sort()
    lo = out[int(0.025*B)]; hi = out[int(0.975*B)]
    return lo, hi

# ---------- experiment driver ----------
SEEDS = [101,202,303,404,505,606,707,808]
TAUS = [round(x*0.05,3) for x in range(0,21)]  # 0.00..1.00

def eval_skip_policy(records, skip_decisions):
    """skip_decisions: list of bool aligned with records (True=skip retrieval).
       Task success at a turn = needed item available:
         - if we retrieve -> available (success)
         - if we skip -> available ONLY if gt_redundant (item genuinely resident)
       Returns (accuracy, skip_rate)."""
    n=len(records); succ=0; skips=0
    for r,skip in zip(records, skip_decisions):
        if skip:
            skips+=1
            if r["gt_redundant"]==1: succ+=1   # genuinely already there -> fine
            # else: WRONG skip -> needed content absent -> fail
        else:
            succ+=1  # retrieved -> have content
    return succ/n, skips/n

def run_point(p_repeat, W, paraphrase_rate, mode, T=600, N_items=80, label=""):
    """One workload point. Returns aggregated rows."""
    per_seed = []
    for seed in SEEDS:
        rng = random.Random(seed)
        recs = gen_trace(rng, T, N_items, W, p_repeat, paraphrase_rate)
        labels = [r["gt_redundant"] for r in recs]
        scores = [check_score(r["query_toks"], r["resident_spans"], mode) for r in recs]
        red_frac = sum(labels)/len(labels)
        auc = roc_auc(scores, labels)
        per_seed.append({"seed":seed,"recs":recs,"labels":labels,"scores":scores,
                         "red_frac":red_frac,"auc":auc})
    return per_seed

def main():
    # ===== PART A + B: workload sweep =====
    print("== running workload sweep ==", flush=True)
    A_rows=[]   # redundancy fraction vs workload
    B_rows=[]   # AUC + best-F1 per workload/mode
    pareto_rows=[]  # full pareto for the FOCUS workload
    delta_rows=[]   # check-vs-random accuracy delta at matched skip rate

    p_repeats = [0.2, 0.4, 0.6, 0.8]
    Ws        = [5, 10, 20]
    paras     = [0.0, 0.3, 0.6, 0.9]
    modes     = ["jaccard","hashed"]

    # ---- A: redundancy fraction vs (p_repeat, W) [paraphrase doesn't affect GT redundancy] ----
    for pr in p_repeats:
        for W in Ws:
            ps = run_point(pr, W, 0.3, "jaccard")  # paraphrase irrelevant to red_frac
            rfs = [s["red_frac"] for s in ps]
            mean = sum(rfs)/len(rfs)
            lo,hi = bootstrap_ci(rfs, lambda v: sum(v)/len(v), B=2000, seed=1)
            A_rows.append({"p_repeat":pr,"W":W,"red_frac_mean":round(mean,4),
                           "ci_lo":round(lo,4),"ci_hi":round(hi,4)})
            print(f"  A p_repeat={pr} W={W} red_frac={mean:.3f}", flush=True)

    # ---- B: check quality (AUC, P/R/F1) vs paraphrase_rate and mode, at a fixed realistic workload ----
    FOCUS_pr, FOCUS_W = 0.5, 10
    for mode in modes:
        for para in paras:
            ps = run_point(FOCUS_pr, FOCUS_W, para, mode)
            aucs = [s["auc"] for s in ps]
            auc_mean = sum(aucs)/len(aucs)
            lo,hi = bootstrap_ci(aucs, lambda v: sum(v)/len(v), B=2000, seed=2)
            # pool all scores/labels for best-F1 tau
            allscores=[]; alllabels=[]
            for s in ps: allscores+=s["scores"]; alllabels+=s["labels"]
            best=None
            for tau in TAUS:
                p,r,f1,tp,fp,fn,tn = prf_at_tau(allscores,alllabels,tau)
                if best is None or (f1>best["f1"]):
                    best={"tau":tau,"prec":p,"rec":r,"f1":f1}
            B_rows.append({"mode":mode,"paraphrase":para,"red_frac":round(ps[0]["red_frac"],3),
                           "auc_mean":round(auc_mean,4),"auc_ci_lo":round(lo,4),"auc_ci_hi":round(hi,4),
                           "best_tau":best["tau"],"prec_at_bestF1":round(best["prec"],4) if not math.isnan(best["prec"]) else None,
                           "rec_at_bestF1":round(best["rec"],4) if not math.isnan(best["rec"]) else None,
                           "f1":round(best["f1"],4)})
            print(f"  B mode={mode} para={para} AUC={auc_mean:.3f} bestF1={best['f1']:.3f}@tau{best['tau']}", flush=True)

    # ---- C: accuracy-safety Pareto vs baselines at FOCUS workload, moderate paraphrase 0.4 ----
    # The KEY test: at each tau, check skip-rate -> match random-skip to same rate -> compare accuracy.
    FOCUS_para = 0.4
    for mode in modes:
        ps = run_point(FOCUS_pr, FOCUS_W, FOCUS_para, mode)
        # ALWAYS-RETRIEVE baseline
        # NEVER-RETRIEVE baseline
        # per-tau check policy + matched random-skip + oracle
        for tau in TAUS:
            check_accs=[]; rand_accs=[]; skiprates=[]; tok_saved=[]
            oracle_accs=[]; oracle_skiprates=[]
            for s in ps:
                recs=s["recs"]; scores=s["scores"]; labels=s["labels"]
                # check policy
                skip_dec = [sc>=tau for sc in scores]
                acc, sr = eval_skip_policy(recs, skip_dec)
                check_accs.append(acc); skiprates.append(sr); tok_saved.append(sr)
                # matched random-skip: skip the SAME NUMBER of turns at random
                k = sum(skip_dec)
                rrng = random.Random(s["seed"]*7+int(tau*100))
                idx = list(range(len(recs)))
                rrng.shuffle(idx)
                rand_skip=[False]*len(recs)
                for i in idx[:k]: rand_skip[i]=True
                racc,_ = eval_skip_policy(recs, rand_skip)
                rand_accs.append(racc)
                # oracle skip = skip exactly gt_redundant
                osk=[l==1 for l in labels]
                oacc,osr = eval_skip_policy(recs, osk)
                oracle_accs.append(oacc); oracle_skiprates.append(osr)
            cm=sum(check_accs)/len(check_accs)
            rm=sum(rand_accs)/len(rand_accs)
            srm=sum(skiprates)/len(skiprates)
            tsm=sum(tok_saved)/len(tok_saved)
            om=sum(oracle_accs)/len(oracle_accs); osrm=sum(oracle_skiprates)/len(oracle_skiprates)
            # delta CI (check - random) across seeds
            deltas=[c-r for c,r in zip(check_accs,rand_accs)]
            dlo,dhi=bootstrap_ci(deltas, lambda v:sum(v)/len(v), B=2000, seed=3)
            pareto_rows.append({"mode":mode,"tau":tau,"skip_rate":round(srm,4),
                                "tokens_saved_frac":round(tsm,4),
                                "acc_check":round(cm,4),"acc_random_matched":round(rm,4),
                                "acc_oracle":round(om,4),"oracle_skip_rate":round(osrm,4),
                                "delta_check_minus_random":round(cm-rm,4),
                                "delta_ci_lo":round(dlo,4),"delta_ci_hi":round(dhi,4)})
        print(f"  C mode={mode} pareto done", flush=True)

    # baselines summary
    base_rows=[]
    for mode in ["jaccard"]:  # baselines independent of mode
        ps = run_point(FOCUS_pr, FOCUS_W, FOCUS_para, mode)
        always=[1.0 for _ in ps]
        never=[]; 
        for s in ps:
            acc,_=eval_skip_policy(s["recs"],[True]*len(s["recs"]))
            never.append(acc)
        base_rows.append({"policy":"always_retrieve","acc":1.0,"tokens_saved":0.0})
        base_rows.append({"policy":"never_retrieve","acc":round(sum(never)/len(never),4),
                          "tokens_saved":1.0})

    # ---- write CSVs ----
    def wcsv(name, rows):
        if not rows: return
        with open(os.path.join(RES,name),"w",newline="") as f:
            w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        print("wrote", name, len(rows),"rows", flush=True)
    wcsv("A_redundancy_vs_workload.csv", A_rows)
    wcsv("B_check_quality.csv", B_rows)
    wcsv("C_pareto.csv", pareto_rows)
    wcsv("C_baselines.csv", base_rows)
    print("DONE", flush=True)

if __name__=="__main__":
    main()
