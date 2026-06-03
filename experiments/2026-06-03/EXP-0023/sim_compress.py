#!/usr/bin/env python3
"""EXP-0023 L0 sim: receiver-role-conditioned inter-agent message compressor vs
generic LLMLingua-style salience compressor vs recency/length truncation, at MATCHED
compression ratio. stdlib only, SERIAL. Anti-circular: extractor reads realizable
role-match feature (noisy view of latent need), NEVER the latent act_on label.
"""
import csv, math, os, random, statistics

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)

ROLES = ["planner", "worker", "critic", "tool_broker"]
TOPIC_DIM = 6

def sigmoid(x):
    if x < -40: return 0.0
    if x > 40: return 1.0
    return 1.0 / (1.0 + math.exp(-x))

def gen_role_needs(rng):
    # latent receiver-need vector per role (NOT observed by any compressor)
    needs = {}
    for r in ROLES:
        v = [rng.gauss(0, 1) for _ in range(TOPIC_DIM)]
        # normalize
        n = math.sqrt(sum(x*x for x in v)) or 1.0
        needs[r] = [x/n for x in v]
    return needs

def gen_message(rng, receiver_role, needs, verb_frac, latent_noise, feature_noise):
    """Return list of spans; each span dict: tokens, act_on, salience, role_match, pos."""
    nspans = rng.randint(8, 20)
    spans = []
    nvec = needs[receiver_role]
    for pos in range(nspans):
        tokens = max(1, int(round(rng.lognormvariate(2.3, 0.6))))  # ~10 tokens median
        is_verbose = rng.random() < verb_frac
        # hidden span-topic vector
        t = [rng.gauss(0, 1) for _ in range(TOPIC_DIM)]
        nt = math.sqrt(sum(x*x for x in t)) or 1.0
        t = [x/nt for x in t]
        dot = sum(a*b for a, b in zip(nvec, t))  # latent alignment with receiver need
        if is_verbose:
            # role-irrelevant verbosity: NOT act-on regardless of topic alignment.
            # but it can still be "contentful" (high generic salience) -> the trap.
            act_on = 0
            contentful = rng.random() < 0.55  # half the chatter looks contentful
        else:
            # role-relevant span: act_on decided by latent need dotted topic + noise
            score = 3.0 * dot + rng.gauss(0, latent_noise)
            act_on = 1 if sigmoid(score) > 0.5 else 0
            contentful = True
        # REALIZABLE features (what compressors see):
        # generic salience proxy s: high if contentful (role-AGNOSTIC). noisy.
        salience = (1.6 if contentful else -0.4) + rng.gauss(0, 0.7)
        # role-match feature m_r: noisy observation of latent dot (receiver role+task signal)
        # ONLY signal the role-conditioned extractor reads. degraded view, never the label.
        role_match = 3.0 * dot + rng.gauss(0, feature_noise)
        spans.append(dict(tokens=tokens, act_on=act_on, salience=salience,
                          role_match=role_match, pos=pos))
    return spans

def keep_by_budget(spans, key, budget_tokens, reverse=True, recent=False):
    """Greedily keep spans ranked by key (desc) until token budget reached.
    recent=True: truncation keeps most-recent positions (highest pos)."""
    if recent:
        order = sorted(spans, key=lambda s: -s["pos"])
    else:
        order = sorted(spans, key=lambda s: s[key], reverse=reverse)
    kept = set()
    used = 0
    for s in order:
        if used + s["tokens"] <= budget_tokens:
            kept.add(s["pos"]); used += s["tokens"]
        # continue: try to pack smaller spans (matched-budget fairness)
    return kept, used

def actmass(spans):
    return sum(s["tokens"] for s in spans if s["act_on"] == 1)

def kept_actmass(spans, kept):
    return sum(s["tokens"] for s in spans if s["act_on"] == 1 and s["pos"] in kept)

def auc(scores, labels):
    # rank-based AUC (Mann-Whitney). scores higher -> more likely label 1.
    pairs = sorted(zip(scores, labels))
    pos = sum(labels); neg = len(labels) - pos
    if pos == 0 or neg == 0: return float("nan")
    # assign ranks (avg for ties)
    ranks = [0.0]*len(pairs); i = 0
    while i < len(pairs):
        j = i
        while j < len(pairs) and pairs[j][0] == pairs[i][0]: j += 1
        r = (i + j - 1)/2.0 + 1.0
        for k in range(i, j): ranks[k] = r
        i = j
    sum_pos = sum(rk for rk,(sc,lb) in zip(ranks, pairs) if lb == 1)
    return (sum_pos - pos*(pos+1)/2.0) / (pos*neg)

def bootstrap_ci(deltas, B=2000, seed=0):
    rng = random.Random(seed)
    n = len(deltas)
    if n == 0: return (float("nan"), float("nan"), float("nan"))
    means = []
    for _ in range(B):
        s = sum(deltas[rng.randrange(n)] for _ in range(n))
        means.append(s/n)
    means.sort()
    lo = means[int(0.025*B)]; hi = means[int(0.975*B)]
    return (statistics.mean(deltas), lo, hi)

VERB_FRACS = [0.2, 0.4, 0.6, 0.8]
NOISE_LEVELS = {"low": 0.6, "med": 1.4, "high": 3.0}   # feature_noise -> AUC low when high
LATENT_NOISE = 0.8
RATIOS = [0.3, 0.5, 0.7]
SEEDS = [11, 22, 33, 44, 55, 66, 77, 88]
N_MSG = 400

def run():
    cell_rows = []        # per (verb,noise,ratio,seed): success per compressor + auc
    raw_msg_delta = {}    # (verb,noise,ratio) -> list of per-message rc-minus-generic success deltas (pooled seeds)
    for verb in VERB_FRACS:
        for nlab, fnoise in NOISE_LEVELS.items():
            # AUC measured once per (verb,noise) over a pooled sample
            auc_rm_all, auc_sal_all, lbls_all = [], [], []
            for seed in SEEDS:
                rng = random.Random(hash((verb, nlab, seed)) & 0xffffffff)
                needs = gen_role_needs(rng)
                msgs = []
                for _ in range(N_MSG):
                    rr = rng.choice(ROLES)
                    spans = gen_message(rng, rr, needs, verb, LATENT_NOISE, fnoise)
                    msgs.append(spans)
                    for s in spans:
                        auc_rm_all.append(s["role_match"]); auc_sal_all.append(s["salience"])
                        lbls_all.append(s["act_on"])
                # per ratio
                for ratio in RATIOS:
                    succ = {"trunc": [], "generic": [], "rolecond": [], "oracle": []}
                    binsucc = {"trunc": 0, "generic": 0, "rolecond": 0, "oracle": 0}
                    kept_tok = {"trunc": 0, "generic": 0, "rolecond": 0, "oracle": 0}
                    tot_tok = 0
                    rc_minus_gen = []
                    nz = 0
                    for spans in msgs:
                        total = sum(s["tokens"] for s in spans)
                        budget = int(round(ratio*total))
                        tot_tok += total
                        am = actmass(spans)
                        # compressors
                        kt,_ = keep_by_budget(spans, "pos", budget, recent=True)
                        kg,ug = keep_by_budget(spans, "salience", budget)
                        kr,ur = keep_by_budget(spans, "role_match", budget)
                        ko,uo = keep_by_budget(spans, "act_on", budget)  # oracle: act_on as key (1>0)
                        kept_tok["trunc"]+= sum(s["tokens"] for s in spans if s["pos"] in kt)
                        kept_tok["generic"]+= ug; kept_tok["rolecond"]+= ur; kept_tok["oracle"]+= uo
                        if am > 0:
                            st = kept_actmass(spans, kt)/am
                            sg = kept_actmass(spans, kg)/am
                            sr = kept_actmass(spans, kr)/am
                            so = kept_actmass(spans, ko)/am
                            succ["trunc"].append(st); succ["generic"].append(sg)
                            succ["rolecond"].append(sr); succ["oracle"].append(so)
                            for k,v in (("trunc",st),("generic",sg),("rolecond",sr),("oracle",so)):
                                if v >= 0.9: binsucc[k]+=1
                            rc_minus_gen.append(sr - sg)
                            nz += 1
                    cell_rows.append(dict(
                        verb_frac=verb, noise=nlab, ratio=ratio, seed=seed,
                        n_msg_nonzero=nz,
                        succ_trunc=statistics.mean(succ["trunc"]),
                        succ_generic=statistics.mean(succ["generic"]),
                        succ_rolecond=statistics.mean(succ["rolecond"]),
                        succ_oracle=statistics.mean(succ["oracle"]),
                        bin_trunc=binsucc["trunc"]/nz, bin_generic=binsucc["generic"]/nz,
                        bin_rolecond=binsucc["rolecond"]/nz, bin_oracle=binsucc["oracle"]/nz,
                        actual_ratio_generic=kept_tok["generic"]/tot_tok,
                        actual_ratio_rolecond=kept_tok["rolecond"]/tot_tok,
                        actual_ratio_trunc=kept_tok["trunc"]/tot_tok,
                        rc_minus_gen_mean=statistics.mean(rc_minus_gen),
                    ))
                    raw_msg_delta.setdefault((verb,nlab,ratio), []).extend(rc_minus_gen)
            # store AUC for this (verb,noise)
            a_rm = auc(auc_rm_all, lbls_all)
            a_sal = auc(auc_sal_all, lbls_all)
            for row in cell_rows:
                if row["verb_frac"]==verb and row["noise"]==nlab and "auc_rolematch" not in row:
                    row["auc_rolematch"]=a_rm; row["auc_salience"]=a_sal
    # fill any missing auc (defensive)
    # write per-cell raw
    cols = list(cell_rows[0].keys())
    with open(os.path.join(OUT,"cells.csv"),"w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in cell_rows: w.writerow(r)
    # bootstrap CI on rc-minus-generic delta per (verb,noise,ratio), pooled across seeds (per-message)
    ci_rows=[]
    for (verb,nlab,ratio), deltas in sorted(raw_msg_delta.items()):
        m,lo,hi = bootstrap_ci(deltas, B=2000, seed=12345)
        # aggregate success means across seeds for this cell
        sub=[r for r in cell_rows if r["verb_frac"]==verb and r["noise"]==nlab and r["ratio"]==ratio]
        ci_rows.append(dict(
            verb_frac=verb, noise=nlab, ratio=ratio,
            auc_rolematch=sub[0]["auc_rolematch"], auc_salience=sub[0]["auc_salience"],
            succ_trunc=statistics.mean(r["succ_trunc"] for r in sub),
            succ_generic=statistics.mean(r["succ_generic"] for r in sub),
            succ_rolecond=statistics.mean(r["succ_rolecond"] for r in sub),
            succ_oracle=statistics.mean(r["succ_oracle"] for r in sub),
            rc_minus_gen_mean=m, ci_lo=lo, ci_hi=hi,
            sig=("YES" if (lo>0 or hi<0) else "no"),
            rc_beats_gen=("YES" if lo>0 else "no"),
            actual_ratio_generic=statistics.mean(r["actual_ratio_generic"] for r in sub),
            actual_ratio_rolecond=statistics.mean(r["actual_ratio_rolecond"] for r in sub),
        ))
    with open(os.path.join(OUT,"matched_ratio_ci.csv"),"w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(ci_rows[0].keys())); w.writeheader()
        for r in ci_rows: w.writerow(r)
    print("WROTE", os.path.join(OUT,"cells.csv"), len(cell_rows),"rows")
    print("WROTE", os.path.join(OUT,"matched_ratio_ci.csv"), len(ci_rows),"rows")
    return ci_rows

if __name__=="__main__":
    import time; t=time.time()
    run()
    print("elapsed_sec", round(time.time()-t,1))
