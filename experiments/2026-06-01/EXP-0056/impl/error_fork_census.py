#!/usr/bin/env python3
"""
EXP-0056 — Error-Fork KV Fragmentation census (PROJ-0010 / CLAIM-0021).
Pure stdlib, Mac CPU. Executes the FROZEN PRE_REGISTRATION.md (locked + committed first).

REUSES the EXP-0054 parse/JOIN/stat layer VERBATIM (imported, not re-implemented):
  parse_cc_session / parse_codex_session (tool_use->tool_result by id; function_call->
  function_call_output by call_id w/ dedup; carries result, is_error, char offsets, footprint),
  load_corpus, base_class, auc, logistic_fit/pred, standardize.

Adjudicates RE-B0 (magnitude floor), RE-B1 (re-convergence reality check, LOAD-BEARING NOVEL),
RE-B2 (predictive killer over JOINT baseline), RE-B2b (matched-success-divergence UPGRADE gate),
RE-B3 (cross-instrument sign agreement HARD GATE). NO numpy/torch. Target < 15 s.
"""
import json, os, re, math, random, statistics, csv, importlib.util
from collections import defaultdict, Counter

# ---------------- reuse EXP-0054 layer verbatim ----------------
E54 = os.path.expanduser(
    "~/autonomous-research/experiments/2026-06-01/EXP-0054/impl/redundant_prefill_census.py")
_spec = importlib.util.spec_from_file_location("e54", E54)
e54 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(e54)
parse_cc_session   = e54.parse_cc_session
parse_codex_session= e54.parse_codex_session
load_corpus        = e54.load_corpus
base_class         = e54.base_class
auc                = e54.auc
logistic_fit       = e54.logistic_fit
logistic_pred      = e54.logistic_pred
standardize        = e54.standardize
det_hash           = e54.det_hash

random.seed(20260601)

# ---------------- FROZEN CONSTANTS (from PRE_REGISTRATION) ----------------
MIN_TRIALS    = 8
CHARS_PER_TOK = 4.0
NBOOT         = 2000
NFOLD         = 5
B2B_K         = 8       # window of next-K calls after index call
B0_FLOOR      = 0.20    # RE-B0 magnitude floor
B2_DAUC_FLOOR = 0.03    # RE-B2 point floor
HHI_FLAG      = 0.20    # Herfindahl domination flag
RECONV_KILL_LB= 0.95    # RE-B1 ~100% re-convergence kill (LB95)
ERRRES_KILL_PT= 0.50    # RE-B1 error-result recurrence kill (point)

# ---------------- helpers ----------------
def first_error_idx(calls):
    for i, c in enumerate(calls):
        if c["is_error"]:
            return i
    return None

def shannon_bpc(s):
    if not s:
        return 0.0
    n = len(s); cnt = Counter(s)
    return -sum((c/n)*math.log2(c/n) for c in cnt.values())

def ols_residuals(xs, ys):
    """residual of OLS ys ~ xs."""
    n = len(xs)
    if n < 2:
        return [0.0]*n
    mx = statistics.mean(xs); my = statistics.mean(ys)
    sxx = sum((x-mx)**2 for x in xs)
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    b = sxy/sxx if sxx else 0.0
    a = my - b*mx
    return [y-(a+b*x) for x, y in zip(xs, ys)]

def boot_ci(vals_by_sess, stat_fn, sessions):
    """session-clustered bootstrap CI of stat_fn over resampled per-session value lists."""
    uniq = list(sessions)
    if not uniq:
        return (None, None)
    out = []
    for _ in range(NBOOT):
        pick = [uniq[random.randrange(len(uniq))] for _ in range(len(uniq))]
        pooled = []
        for s in pick:
            pooled.extend(vals_by_sess.get(s, []))
        v = stat_fn(pooled)
        if v is not None:
            out.append(v)
    if not out:
        return (None, None)
    out.sort()
    return (out[int(0.025*len(out))], out[int(0.975*len(out))])

# ---------------- cross-session pools ----------------
def build_pools(sessions):
    pool_all    = defaultdict(set)   # sig -> sessions (anywhere)
    pool_preerr = defaultdict(set)   # sig -> sessions (pre-first-error region)
    errres      = defaultdict(set)   # sig\0result -> sessions (error calls only)
    for sname, calls in sessions.items():
        fe = first_error_idx(calls)
        for i, c in enumerate(calls):
            pool_all[c["sig"]].add(sname)
            if fe is None or i < fe:
                pool_preerr[c["sig"]].add(sname)
            if c["is_error"]:
                errres[c["sig"] + "\x00" + c["result"]].add(sname)
    return pool_all, pool_preerr, errres

def is_nonshareable(sig, sname, pool_all):
    others = pool_all.get(sig, set()) - {sname}
    return len(others) == 0

# ---------------- session feature build ----------------
def session_features(sname, calls, pool_all):
    n = len(calls)
    # cadence (B0)
    gaps = []
    for i in range(1, n):
        g = max(0.0, (calls[i]["start_pos"] - calls[i-1]["end_pos"]) / CHARS_PER_TOK)
        gaps.append(math.log1p(g))
    mean_lg_gap = statistics.mean(gaps) if gaps else 0.0
    freq = defaultdict(int)
    for c in calls:
        freq[c["name"]] += 1
    mean_lg_freq = statistics.mean([math.log1p(freq[c["name"]]) for c in calls])
    cls = [base_class(c["name"]) for c in calls]
    read_f = cls.count("READ")/n; mut_f = cls.count("MUT")/n; vol_f = cls.count("VOL")/n
    # error features (B1)
    fe = first_error_idx(calls)
    n_err = sum(1 for c in calls if c["is_error"])
    err_pos_frac = (fe / n) if fe is not None else 1.0
    lg_nerr = math.log1p(n_err)
    fe_cls = base_class(calls[fe]["name"]) if fe is not None else None
    fe_read = 1.0 if fe_cls == "READ" else 0.0
    fe_mut  = 1.0 if fe_cls == "MUT"  else 0.0
    fe_vol  = 1.0 if fe_cls == "VOL"  else 0.0
    # label support: non-shareable footprint fraction
    tot_foot = sum(c["footprint"] for c in calls) or 1
    ns_foot = sum(c["footprint"] for c in calls if is_nonshareable(c["sig"], sname, pool_all))
    ns_frac = ns_foot / tot_foot
    return dict(sess=sname, n=n, tot_foot=tot_foot, ns_foot=ns_foot, ns_frac=ns_frac,
                fe=fe, n_err=n_err,
                b0=[mean_lg_gap, mean_lg_freq, read_f, mut_f, vol_f],
                b1_err=[err_pos_frac, lg_nerr, fe_read, fe_mut, fe_vol],  # entropy resid appended later
                fe_result=(calls[fe]["result"] if fe is not None else ""))

# ---------------- logistic CV held-out AUC (session-level) ----------------
def cv_auc(X, y, sess, with_keep):
    """5-fold session-clustered held-out scores -> overall AUC + per-fold AUC list."""
    uniq = sorted(set(sess))
    fold_of = {s: det_hash(s) % NFOLD for s in uniq}
    Xc = [list(row) for row in X]
    cont_idx = list(range(len(Xc[0]))) if Xc else []
    standardize(Xc, cont_idx)
    scores = [None]*len(Xc)
    for f in range(NFOLD):
        tr = [i for i in range(len(Xc)) if fold_of[sess[i]] != f]
        te = [i for i in range(len(Xc)) if fold_of[sess[i]] == f]
        if not tr or not te:
            continue
        ytr = [y[i] for i in tr]
        if len(set(ytr)) < 2:
            m = statistics.mean(ytr) if ytr else 0.5
            for i in te: scores[i] = m
            continue
        w, b = logistic_fit([Xc[i] for i in tr], ytr)
        for i in te: scores[i] = logistic_pred(w, b, Xc[i])
    a_all = auc(scores, y)
    perfold = []
    for f in range(NFOLD):
        te = [i for i in range(len(Xc)) if fold_of[sess[i]] == f]
        if len(te) < 2:
            perfold.append(None); continue
        perfold.append(auc([scores[i] for i in te], [y[i] for i in te]))
    return a_all, scores, perfold, fold_of

def re_b2(feats):
    out = {"n_sessions": len(feats)}
    if len(feats) < 30:
        out["status"] = "underpowered"; out["reason"] = f"n_sessions={len(feats)}<30"
        return out
    med = statistics.median([f["ns_frac"] for f in feats])
    y = [1 if f["ns_frac"] > med else 0 for f in feats]
    if len(set(y)) < 2:
        out["status"] = "degenerate"; out["reason"] = "no label variance"; return out
    sess = [f["sess"] for f in feats]
    X0 = [f["b0"] for f in feats]
    X1 = [f["b0"] + f["b1_err"] for f in feats]
    a0, s0, pf0, fold_of = cv_auc(X0, y, sess, False)
    a1, s1, pf1, _       = cv_auc(X1, y, sess, True)
    if a0 is None or a1 is None:
        out["status"] = "degenerate"; out["reason"] = "AUC undefined"; return out
    dauc = a1 - a0
    # per-fold dAUC
    fold_dauc = [(pf1[f]-pf0[f]) for f in range(NFOLD) if pf0[f] is not None and pf1[f] is not None]
    # session-clustered bootstrap of dAUC
    by_sess = defaultdict(list)
    for i in range(len(feats)):
        by_sess[sess[i]].append(i)
    uniq = list(by_sess.keys())
    dvals = []
    for _ in range(NBOOT):
        pick = [uniq[random.randrange(len(uniq))] for _ in range(len(uniq))]
        idx = []
        for sn in pick: idx.extend(by_sess[sn])
        bs0 = [s0[i] for i in idx]; bs1 = [s1[i] for i in idx]; by = [y[i] for i in idx]
        ba0 = auc(bs0, by); ba1 = auc(bs1, by)
        if ba0 is not None and ba1 is not None:
            dvals.append(ba1 - ba0)
    lb = ub = None
    if dvals:
        dvals.sort()
        lb = dvals[int(0.025*len(dvals))]; ub = dvals[int(0.975*len(dvals))]
    # Herfindahl of positive-class footprint mass
    pos_foot = [feats[i]["ns_foot"] for i in range(len(feats)) if y[i] == 1]
    tot = sum(pos_foot) or 1
    hhi = sum((p/tot)**2 for p in pos_foot)
    all_folds_pos = len(fold_dauc) == NFOLD and all(d > 0 for d in fold_dauc) if fold_dauc else False
    out.update(status="ok", label_median=med, pos_rate=sum(y)/len(y),
               auc_B0=a0, auc_B1=a1, dAUC_point=dauc, dAUC_LB95=lb, dAUC_UB95=ub,
               fold_dAUC=fold_dauc, fold_dAUC_std=(statistics.pstdev(fold_dauc) if len(fold_dauc) > 1 else None),
               all_folds_positive=all_folds_pos, herfindahl=hhi, hhi_flag=(hhi > HHI_FLAG))
    out["PASS"] = bool(lb is not None and lb > 0 and dauc >= B2_DAUC_FLOOR and all_folds_pos)
    return out

# ---------------- RE-B0 ----------------
def re_b0(sessions):
    fracs = []
    for sname, calls in sessions.items():
        fe = first_error_idx(calls)
        if fe is None:
            continue
        tot = sum(c["footprint"] for c in calls) or 1
        down = sum(calls[i]["footprint"] for i in range(fe+1, len(calls)))
        fracs.append(down/tot)
    if not fracs:
        return {"status": "no_error_sessions", "n_error_sessions": 0, "PASS": False}
    mean = statistics.mean(fracs); med = statistics.median(fracs)
    return {"status": "ok", "n_error_sessions": len(fracs), "mean_downstream_frac": mean,
            "median_downstream_frac": med, "PASS": mean >= B0_FLOOR}

# ---------------- RE-B1 ----------------
def re_b1(sessions, pool_preerr, errres):
    # post-error calls
    sig_reconv_by_sess = defaultdict(list)   # count-weighted bernoulli
    foot_reconv_num = defaultdict(float); foot_reconv_den = defaultdict(float)
    errres_by_sess = defaultdict(list)
    n_post = 0; n_post_err = 0
    for sname, calls in sessions.items():
        fe = first_error_idx(calls)
        if fe is None:
            continue
        for i in range(fe+1, len(calls)):
            c = calls[i]; n_post += 1
            reconv = 1 if (pool_preerr.get(c["sig"], set()) - {sname}) else 0
            sig_reconv_by_sess[sname].append(reconv)
            foot_reconv_den[sname] += c["footprint"]
            if reconv: foot_reconv_num[sname] += c["footprint"]
            if c["is_error"]:
                n_post_err += 1
                key = c["sig"] + "\x00" + c["result"]
                rec = 1 if (errres.get(key, set()) - {sname}) else 0
                errres_by_sess[sname].append(rec)
    sess = list(sessions.keys())
    def mean_or_none(lst): return statistics.mean(lst) if lst else None
    sig_pt = mean_or_none([v for l in sig_reconv_by_sess.values() for v in l])
    err_pt = mean_or_none([v for l in errres_by_sess.values() for v in l])
    sig_lb, sig_ub = boot_ci(sig_reconv_by_sess, mean_or_none, sess)
    err_lb, err_ub = boot_ci(errres_by_sess, mean_or_none, sess)
    # footprint-weighted sig reconvergence
    fnum = sum(foot_reconv_num.values()); fden = sum(foot_reconv_den.values())
    foot_pt = (fnum/fden) if fden else None
    out = {"n_post_error_calls": n_post, "n_post_error_errcalls": n_post_err,
           "sig_reconv_rate_count": sig_pt, "sig_reconv_CI95": (sig_lb, sig_ub),
           "sig_reconv_rate_footprint": foot_pt,
           "errresult_recur_rate": err_pt, "errresult_recur_CI95": (err_lb, err_ub)}
    # frozen interpretation flags
    out["flag_full_reconvergence_kill"] = bool(sig_lb is not None and sig_lb >= RECONV_KILL_LB)
    out["flag_errresult_recurs_kill"]   = bool(err_pt is not None and err_pt >= ERRRES_KILL_PT)
    out["novel_claim_supported"] = bool(
        sig_pt is not None and sig_pt < 0.80 and (err_pt is None or err_pt < ERRRES_KILL_PT))
    return out

# ---------------- RE-B2b matched-success-divergence ----------------
def _window_nonshare_frac(calls, i, pool_all, sname):
    den = 0.0; num = 0.0
    for j in range(i+1, min(i+1+B2B_K, len(calls))):
        c = calls[j]; den += c["footprint"]
        if is_nonshareable(c["sig"], sname, pool_all):
            num += c["footprint"]
    if den == 0:
        return None
    return num/den

def re_b2b(sessions, pool_all):
    # collect error + success index calls with (len bucket, entropy bucket) and window frac
    err_recs = []   # (sess, frac, lenb, entb)
    succ_pool = defaultdict(list)  # (lenb,entb) -> [(sess,frac)]
    for sname, calls in sessions.items():
        for i in range(len(calls)-1):
            c = calls[i]
            frac = _window_nonshare_frac(calls, i, pool_all, sname)
            if frac is None:
                continue
            ln = len(c["result"]); ent = shannon_bpc(c["result"])
            lenb = int(math.log10(ln+1)*2)      # ~half-decade buckets
            entb = round(ent*2)/2.0              # 0.5-bit buckets
            if c["is_error"]:
                err_recs.append((sname, frac, lenb, entb))
            else:
                succ_pool[(lenb, entb)].append((sname, frac))
    # match each error call to a random same-bucket success
    matched_err = []; matched_succ = []
    for (sname, frac, lenb, entb) in err_recs:
        cands = succ_pool.get((lenb, entb), [])
        if not cands:
            continue
        ms, mf = cands[random.randrange(len(cands))]
        matched_err.append((sname, frac)); matched_succ.append((ms, mf))
    out = {"n_error_calls_with_window": len(err_recs), "n_matched": len(matched_err)}
    if len(matched_err) < 3:
        out["status"] = "underpowered"; out["reason"] = f"matched n={len(matched_err)}<3"; out["PASS"] = False
        return out
    e_mean = statistics.mean([f for _, f in matched_err])
    s_mean = statistics.mean([f for _, f in matched_succ])
    delta = e_mean - s_mean
    # session-clustered bootstrap of delta
    err_by = defaultdict(list); succ_by = defaultdict(list)
    for s, f in matched_err: err_by[s].append(f)
    for s, f in matched_succ: succ_by[s].append(f)
    sess = sorted(set(list(err_by.keys()) + list(succ_by.keys())))
    dvals = []
    for _ in range(NBOOT):
        pick = [sess[random.randrange(len(sess))] for _ in range(len(sess))]
        ev = [v for s in pick for v in err_by.get(s, [])]
        sv = [v for s in pick for v in succ_by.get(s, [])]
        if ev and sv:
            dvals.append(statistics.mean(ev) - statistics.mean(sv))
    lb = ub = None
    if dvals:
        dvals.sort(); lb = dvals[int(0.025*len(dvals))]; ub = dvals[int(0.975*len(dvals))]
    out.update(status="ok", error_nonshare_mean=e_mean, success_nonshare_mean=s_mean,
               delta_b2b=delta, delta_CI95=(lb, ub))
    out["PASS"] = bool(lb is not None and lb > 0)
    return out

# ---------------- per-corpus driver ----------------
def analyze(corpus, sessions):
    R = {"corpus": corpus, "n_sessions": len(sessions)}
    pool_all, pool_preerr, errres = build_pools(sessions)
    # entropy residual of first-error results (length-residualized), global
    feats = [session_features(s, c, pool_all) for s, c in sessions.items()]
    fe_feats = [f for f in feats if f["fe"] is not None]
    if len(fe_feats) >= 2:
        lens = [math.log1p(len(f["fe_result"])) for f in fe_feats]
        ents = [shannon_bpc(f["fe_result"]) for f in fe_feats]
        resids = ols_residuals(lens, ents)
        rmap = {id(f): r for f, r in zip(fe_feats, resids)}
    else:
        rmap = {}
    for f in feats:
        r = rmap.get(id(f), 0.0)
        f["b1_err"] = f["b1_err"] + [r]
    R["RE_B0"]  = re_b0(sessions)
    R["RE_B1"]  = re_b1(sessions, pool_preerr, errres)
    R["RE_B2"]  = re_b2(feats)
    R["RE_B2b"] = re_b2b(sessions, pool_all)
    return R, feats

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir = os.path.join(base, "results"); os.makedirs(rdir, exist_ok=True)
    import time
    t0 = time.time()
    print("Loading corpora (reusing EXP-0054 loader)...")
    cc = load_corpus("cc"); cx = load_corpus("codex")
    print(f"  CC sessions(>= {MIN_TRIALS}): {len(cc)}   Codex sessions: {len(cx)}")
    results = {}; allfeats = {}
    for corpus, sess in [("cc", cc), ("codex", cx)]:
        print(f"\n===== analyzing {corpus} =====")
        R, feats = analyze(corpus, sess)
        results[corpus] = R; allfeats[corpus] = feats
        print(f"  RE-B0 : {R['RE_B0']}")
        print(f"  RE-B1 : {R['RE_B1']}")
        print(f"  RE-B2 : {R['RE_B2']}")
        print(f"  RE-B2b: {R['RE_B2b']}")
    # RE-B3 cross-instrument sign agreement on dAUC_point and delta_b2b
    def sgn(x): return (x > 0) - (x < 0) if x is not None else None
    cc2 = results["cc"]["RE_B2"]; cx2 = results["codex"]["RE_B2"]
    cc2b = results["cc"]["RE_B2b"]; cx2b = results["codex"]["RE_B2b"]
    d_cc = cc2.get("dAUC_point"); d_cx = cx2.get("dAUC_point")
    b_cc = cc2b.get("delta_b2b"); b_cx = cx2b.get("delta_b2b")
    dauc_agree = (sgn(d_cc) is not None and sgn(d_cc) == sgn(d_cx) and sgn(d_cc) != 0)
    b2b_agree  = (sgn(b_cc) is not None and sgn(b_cc) == sgn(b_cx) and sgn(b_cc) != 0)
    both_powered = (cc2.get("status") == "ok" and cx2.get("status") == "ok")
    re_b3 = {"dAUC_cc": d_cc, "dAUC_codex": d_cx, "dAUC_sign_agree": dauc_agree,
             "delta_b2b_cc": b_cc, "delta_b2b_codex": b_cx, "delta_b2b_sign_agree": b2b_agree,
             "both_corpora_powered": both_powered,
             "PASS": bool(both_powered and dauc_agree and b2b_agree)}
    print(f"\nRE-B3 cross-instrument: {re_b3}")

    # ---------- overall disposition (frozen rule) ----------
    def gate(corpus):
        R = results[corpus]
        return dict(B0=R["RE_B0"].get("PASS"), B2=R["RE_B2"].get("PASS"),
                    B2b=R["RE_B2b"].get("PASS"))
    primary = "cc"
    Rp = results[primary]
    b0p = Rp["RE_B0"].get("PASS"); b2p = Rp["RE_B2"].get("PASS"); b2bp = Rp["RE_B2b"].get("PASS")
    b1 = Rp["RE_B1"]
    b1_kill = b1.get("flag_full_reconvergence_kill") or b1.get("flag_errresult_recurs_kill")
    hhi_flag = Rp["RE_B2"].get("hhi_flag")
    if (b0p and b2p and b2bp and re_b3["PASS"] and not b1_kill and not hhi_flag):
        disposition = "GREEN"
    elif (b0p and b2p and re_b3["dAUC_sign_agree"] and not b1_kill):
        disposition = "YELLOW"
    else:
        disposition = "KILL"
    summary = {"exp": "EXP-0056", "project": "PROJ-0010", "claim": "CLAIM-0021",
               "primary_corpus": primary, "per_corpus_gates": {c: gate(c) for c in ("cc", "codex")},
               "RE_B3": re_b3, "RE_B1_primary": b1, "disposition": disposition,
               "wall_s": round(time.time()-t0, 2)}

    # ---------- write artifacts ----------
    bundle = {"results": results, "RE_B3": re_b3, "summary": summary,
              "frozen": {"MIN_TRIALS": MIN_TRIALS, "NBOOT": NBOOT, "NFOLD": NFOLD,
                         "B2B_K": B2B_K, "B0_FLOOR": B0_FLOOR, "B2_DAUC_FLOOR": B2_DAUC_FLOOR,
                         "HHI_FLAG": HHI_FLAG, "seed": 20260601}}
    with open(os.path.join(rdir, "census.json"), "w") as f:
        json.dump(bundle, f, indent=2, default=str)
    with open(os.path.join(rdir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    # per-session CSV per corpus
    for corpus in ("cc", "codex"):
        feats = allfeats[corpus]
        rows = []
        for f in feats:
            rows.append(dict(session=os.path.basename(f["sess"]), n_calls=f["n"],
                             n_err=f["n_err"], first_err_idx=f["fe"],
                             ns_frac=round(f["ns_frac"], 4),
                             tot_foot_tok=round(f["tot_foot"]/CHARS_PER_TOK, 1)))
        with open(os.path.join(rdir, f"sessions_{corpus}.csv"), "w", newline="") as fh:
            if rows:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader()
                for r in rows: w.writerow(r)
    print(f"\nDISPOSITION: {disposition}   wall={summary['wall_s']}s")
    print(f"wrote {rdir}/census.json, summary.json, sessions_*.csv")
    return bundle

if __name__ == "__main__":
    main()
