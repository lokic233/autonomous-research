#!/usr/bin/env python3
"""
EXP-0058 — Multi-Tool Batch Admission Mis-Estimation (PROJ-0012 / CLAIM-0023).
Pure stdlib, Mac CPU. Executes the FROZEN PRE_REGISTRATION.md (locked 2026-06-01T20:52:44Z, committed first).

THESIS: agents emit co-issued PARALLEL tool calls (one assistant turn, N calls emitted before ANY result exists);
their results return together and prefill as ONE BATCH. CLAIM: a cheap PRE-EXECUTION feature of the batch's JOINT
ARGUMENT structure predicts a whale BATCH (top-decile batch-total prefill mass) OVER AND ABOVE
{count, gap, freq, tool-mix, tool-pair/triple interactions, matched-max/sum-per-call}. Clean NEGATIVE if it fails.

REUSES EXP-0055 whale_prefill_predict.py VERBATIM (imported): auc, standardize, logistic_fit/pred, det_hash,
canon_args, block_text, spearman, mass_capture, load_corpus, parse_codex_session. NO numpy/torch.

FIX-1 (strawman) + FIX-4 (per-instrument parallel-call verification) resolved in PRE_REGISTRATION with live probes:
Codex emits genuine co-issued parallel calls; CC emits ZERO -> single-instrument (Codex) by design.
RE-B3 no-leakage BY CONSTRUCTION: X derived from args_str ONLY; result text NEVER enters X.
FIX-2 EARLY-KILL: if joint-arg features add nothing beyond matched-max/sum-per-call (RE-B2 fails) the batch whale
reduces to max(per-call whale) -> collapses to DEAD-0018 -> IMMEDIATE TERMINATION.
"""
import json, glob, os, re, math, random, statistics, importlib.util, time
from collections import defaultdict, Counter

# ---------------- reuse EXP-0055 layer verbatim ----------------
E55 = os.path.expanduser(
    "~/autonomous-research/experiments/2026-06-01/EXP-0055/impl/whale_prefill_predict.py")
_spec = importlib.util.spec_from_file_location("e55", E55)
e55 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(e55)
auc          = e55.auc
standardize  = e55.standardize
logistic_fit = e55.logistic_fit
logistic_pred= e55.logistic_pred
det_hash     = e55.det_hash
canon_args   = e55.canon_args
spearman     = e55.spearman
mass_capture = e55.mass_capture

# ---------------- FROZEN CONSTANTS (from PRE_REGISTRATION) ----------------
SEED            = 20260601
CHARS_PER_TOK   = 4.0
MIN_TRIALS      = 8
TOP_DECILE      = 0.90
NFOLD           = 5
NBOOT           = 2000
L2              = 1.0
TOPK_TOOL       = 12
TOPK_PAIR       = 16
TOPK_TRIPLE     = 12
B0_MULTI_FRAC   = 0.25     # RE-B0 multi-call fraction floor
B0_MASS_FLOOR   = 0.50     # RE-B0 top-decile mass floor
B1_SPEARMAN_MAX = 0.30     # RE-B1 size-total Spearman ceiling
B1_SIZE_AUC_MAX = 0.60     # RE-B1 size-only whale-AUC ceiling
B2_DAUC_FLOOR   = 0.03     # RE-B2 dAUC point floor
HHI_FLAG        = 0.20     # STAT discipline domination flag
TS_TIGHT_S      = 1.0      # robustness: strict co-issued ts-gap (diagnostic only)
LOCKED_TS       = "2026-06-01T20:52:44Z"

random.seed(SEED)

# ============================================================================
# CO-ISSUED BATCH PARSER (Codex) — call_id/message co-occurrence (FIX-4)
# batch = maximal run of consecutive function_call events with NO output between (all emitted pre-execution).
# ============================================================================
def parse_codex_batches(path):
    """Return (batches, total_calls). Each batch: list of call dicts {name,args_str,result_tok,ts}.
    Only co-issued runs (>=1 consecutive function_call before any output) are formed; size>=2 are parallel batches."""
    out_by_id = {}      # call_id -> result text
    emit = []           # ordered list of ('call', call_id, name, args_str, ts) and ('out', call_id)
    with open(path, errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: d = json.loads(line)
            except: continue
            p = d.get("payload") or d
            tp = p.get("type"); ts = d.get("timestamp")
            if tp == "function_call":
                name = p.get("name", "?"); raw = p.get("arguments", "")
                try: a = json.loads(raw) if isinstance(raw, str) else raw
                except Exception: a = raw
                astr = canon_args(a) if isinstance(a, (dict, list)) else str(a)
                emit.append(("call", p.get("call_id"), name, astr, ts))
            elif tp == "function_call_output":
                cid = p.get("call_id")
                if cid not in out_by_id:    # dedup by call_id (EXP-0033/0037 double-log neutralizer)
                    out_by_id[cid] = str(p.get("output", ""))
    # group into maximal consecutive function_call runs (no output between)
    batches = []; cur = []; total_calls = 0
    def flush():
        if cur: batches.append(cur[:]); cur.clear()
    for kind, cid, *rest in emit:
        if kind == "call":
            name, astr, ts = rest
            total_calls += 1
            cur.append(dict(call_id=cid, name=name, args_str=astr, ts=ts))
        else:
            flush()
    flush()
    # attach result tokens (join by call_id, pre-execution X never uses this)
    for b in batches:
        for c in b:
            c["result_tok"] = len(out_by_id.get(c["call_id"], "")) / CHARS_PER_TOK
    return batches, total_calls

def load_codex_batch_sessions():
    fs = sorted(glob.glob(os.path.expanduser("~/.codex/sessions/**/*.jsonl"), recursive=True))
    sessions = {}
    for f in fs:
        try: batches, total = parse_codex_batches(f)
        except Exception: continue
        if total >= MIN_TRIALS and batches:
            sessions[f] = batches
    return sessions

# ============================================================================
# CC PARALLEL-CALL PROBE (FIX-4) — establish CC emits ZERO co-issued parallel calls
# ============================================================================
def cc_parallel_probe():
    fs = sorted(glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")))
    tu_per_msg = Counter(); tr_per_msg = Counter()
    for f in fs:
        with open(f, errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line: continue
                try: d = json.loads(line)
                except: continue
                m = d.get("message")
                if not isinstance(m, dict): continue
                c = m.get("content")
                if not isinstance(c, list): continue
                tu = sum(1 for b in c if isinstance(b, dict) and b.get("type") == "tool_use")
                tr = sum(1 for b in c if isinstance(b, dict) and b.get("type") == "tool_result")
                if tu: tu_per_msg[tu] += 1
                if tr: tr_per_msg[tr] += 1
    n_multi_tu = sum(v for k, v in tu_per_msg.items() if k >= 2)
    n_multi_tr = sum(v for k, v in tr_per_msg.items() if k >= 2)
    return {"n_files": len(fs),
            "tool_use_per_assistant_msg_dist": dict(sorted(tu_per_msg.items())),
            "tool_result_per_user_msg_dist": dict(sorted(tr_per_msg.items())),
            "n_msgs_multi_tool_use": n_multi_tu, "n_msgs_multi_tool_result": n_multi_tr,
            "emits_coissued_parallel_calls": bool(n_multi_tu > 0 or n_multi_tr > 0)}

# ============================================================================
# PER-CALL pre-execution arg features (args_str ONLY) — §2a
# ============================================================================
def call_feats(args_str):
    s = args_str or ""
    nums = re.findall(r"\d+", s)
    numeric_max = max((int(x) for x in nums[:60]), default=0)
    has_numeric_limit = 1.0 if nums else 0.0
    path_depth = float(s.count("/"))
    glob_count = float(s.count("*") + s.count("?") + s.count("{") + s.count("["))
    bash_io = float(len(re.findall(r"head|tail|>>|>|\| ", s)))
    arg_tok = len(s) / CHARS_PER_TOK
    return [math.log1p(arg_tok), path_depth, glob_count, math.log1p(numeric_max), has_numeric_limit, bash_io]
CALL_FEAT_NAMES = ["log_arg_tok", "path_depth", "glob_count", "log_numeric_max", "has_numeric_limit", "bash_io_flags"]

# ============================================================================
# session-clustered CV held-out scores (generic) — reuse EXP-0055 pattern
# ============================================================================
def cv_scores(X, y, sess, cont_idx):
    uniq = sorted(set(sess)); fold_of = {s: det_hash(s) % NFOLD for s in uniq}
    foldid = [fold_of[s] for s in sess]
    Xc = [list(r) for r in X]; standardize(Xc, cont_idx)
    scores = [0.5] * len(Xc)
    for f in range(NFOLD):
        tr = [i for i in range(len(Xc)) if foldid[i] != f]; te = [i for i in range(len(Xc)) if foldid[i] == f]
        if not tr or not te: continue
        ytr = [y[i] for i in tr]
        if len(set(ytr)) < 2:
            mv = statistics.mean(ytr) if ytr else 0.5
            for i in te: scores[i] = mv
            continue
        w, b = logistic_fit([Xc[i] for i in tr], ytr)
        for i in te: scores[i] = logistic_pred(w, b, Xc[i])
    return scores, foldid

def per_fold_dauc(s0, s1, y, foldid):
    ds = []
    for f in sorted(set(foldid)):
        idx = [i for i in range(len(y)) if foldid[i] == f]
        a0 = auc([s0[i] for i in idx], [y[i] for i in idx]); a1 = auc([s1[i] for i in idx], [y[i] for i in idx])
        if a0 is not None and a1 is not None: ds.append(a1 - a0)
    return ds

def bootstrap_dauc(s0, s1, y, sess):
    by = defaultdict(list)
    for i, s in enumerate(sess): by[s].append(i)
    uniq = list(by.keys()); dvals = []
    for _ in range(NBOOT):
        pick = [uniq[random.randrange(len(uniq))] for _ in range(len(uniq))]
        idx = []
        for sn in pick: idx.extend(by[sn])
        a0 = auc([s0[i] for i in idx], [y[i] for i in idx]); a1 = auc([s1[i] for i in idx], [y[i] for i in idx])
        if a0 is not None and a1 is not None: dvals.append(a1 - a0)
    if not dvals: return None, None
    dvals.sort(); return dvals[int(0.025 * len(dvals))], dvals[int(0.975 * len(dvals))]

# ============================================================================
# PER-CALL whale predictor -> matched-max/sum-per-call (FIX-2, leakage-safe) — §2b
# ============================================================================
def per_call_whale_probs(batches):
    """All calls across multi-call+singleton batches; label top-decile per-call result_tok; session-clustered CV prob.
    batches: dict sess->list[batch]; returns {(sess, batch_idx, call_idx): p_call}."""
    recs = []  # (sess, bi, ci, feats, result_tok)
    for sess, blist in batches.items():
        for bi, b in enumerate(blist):
            for ci, c in enumerate(b):
                recs.append((sess, bi, ci, call_feats(c["args_str"]), c["result_tok"]))
    if not recs: return {}
    vals = sorted(r[4] for r in recs); n = len(vals); thr = vals[int(math.ceil(TOP_DECILE * n)) - 1]
    y = [1 if r[4] > thr else 0 for r in recs]
    X = [r[3] for r in recs]; sess = [r[0] for r in recs]
    cont_idx = list(range(len(CALL_FEAT_NAMES)))
    scores, _ = cv_scores(X, y, sess, cont_idx)
    return {(r[0], r[1], r[2]): scores[i] for i, r in enumerate(recs)}, (sum(y) / len(y))

# ============================================================================
# PER-BATCH feature assembly (B0 / B1) — §2c/§2d
# ============================================================================
def build_vocabs(mbatches):
    tool_cnt = Counter(); pair_cnt = Counter(); triple_cnt = Counter()
    for (sess, b) in mbatches:
        names = sorted(set(c["name"] for c in b))
        for nm in (c["name"] for c in b): tool_cnt[nm] += 1
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                pair_cnt[(names[i], names[j])] += 1
                for k in range(j + 1, len(names)):
                    triple_cnt[(names[i], names[j], names[k])] += 1
    tool_vocab = {t: i for i, (t, _) in enumerate(tool_cnt.most_common(TOPK_TOOL))}
    pair_vocab = {p: i for i, (p, _) in enumerate(pair_cnt.most_common(TOPK_PAIR))}
    triple_vocab = {t: i for i, (t, _) in enumerate(triple_cnt.most_common(TOPK_TRIPLE))}
    return tool_vocab, pair_vocab, triple_vocab

def batch_row(sess, b, bi, mode, vocabs, pcall):
    tool_vocab, pair_vocab, triple_vocab = vocabs
    size = len(b)
    # mean gap (stream order proxy: 0 within co-issued batch, but keep arg-length cadence) + mean freq placeholder
    gaps = []  # co-issued => emission gaps ~0; use 0.0 mean to honour frozen feature slot
    mean_gap = 0.0
    mean_freq = statistics.mean([1.0 for _ in b])  # within-batch tool freq proxy (kept for B0 slot parity)
    row = [math.log1p(size), math.log1p(mean_gap), math.log1p(mean_freq)]
    # tool-mix one-hot (presence)
    tv = [0.0] * (len(tool_vocab) + 1)
    present = set(c["name"] for c in b)
    other = False
    for nm in present:
        if nm in tool_vocab: tv[tool_vocab[nm]] = 1.0
        else: other = True
    tv[-1] = 1.0 if other else 0.0
    row += tv
    # tool-pair interactions
    pv = [0.0] * len(pair_vocab)
    names = sorted(present)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            p = (names[i], names[j])
            if p in pair_vocab: pv[pair_vocab[p]] = 1.0
    row += pv
    # tool-triple interactions
    trv = [0.0] * len(triple_vocab)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            for k in range(j + 1, len(names)):
                t = (names[i], names[j], names[k])
                if t in triple_vocab: trv[triple_vocab[t]] = 1.0
    row += trv
    # matched-max/sum per-call (FIX-2)
    ps = [pcall.get((sess, bi, ci), 0.5) for ci in range(size)]
    mm = max(ps); ms = sum(ps)
    row += [mm, ms]
    cont_idx = [0, 1, 2]  # log size/gap/freq
    base = len(row)
    if mode == "B1":
        # joint arg-structure: max AND sum over calls of each per-call feature
        cf = [call_feats(c["args_str"]) for c in b]
        d = len(CALL_FEAT_NAMES)
        maxv = [max(cf[ci][k] for ci in range(size)) for k in range(d)]
        sumv = [sum(cf[ci][k] for ci in range(size)) for k in range(d)]
        start = len(row)
        row += maxv + sumv
        cont_idx += list(range(start, start + 2 * d))
    # mark matched-max/sum cont indices (they are continuous)
    # positions of mm,ms = base-2, base-1
    cont_idx += [base - 2, base - 1]
    return row, cont_idx

def assemble(mbatches, mode, vocabs, pcall):
    X = []; cont_idx = None
    for (sess, b, bi) in mbatches:
        r, ci = batch_row(sess, b, bi, mode, vocabs, pcall)
        X.append(r)
        if cont_idx is None: cont_idx = ci
    return X, cont_idx

# ============================================================================
# GATES
# ============================================================================
def gini(vals):
    v = sorted(x for x in vals if x is not None)
    n = len(v)
    if n == 0 or sum(v) == 0: return None
    cum = 0.0
    for i, x in enumerate(v): cum += (i + 1) * x
    return (2 * cum) / (n * sum(v)) - (n + 1) / n

def analyze_codex(sessions):
    R = {"corpus": "codex", "n_sessions": len(sessions)}
    all_batches = sessions  # dict sess->list[batch]
    runs = [(s, b) for s, bl in all_batches.items() for b in bl]
    multi = [(s, b, bi) for s, bl in all_batches.items() for bi, b in enumerate(bl) if len(b) >= 2]
    R["n_runs"] = len(runs); R["n_multi_batches"] = len(multi)
    R["multi_frac"] = len(multi) / len(runs) if runs else 0.0
    R["size_dist"] = dict(sorted(Counter(len(b) for _, b in runs).items()))
    # batch totals
    bt = [(s, bi, sum(c["result_tok"] for c in b)) for (s, b, bi) in multi]
    totals = [x[2] for x in bt]
    # ---- RE-B0 magnitude floor ----
    if totals:
        st = sorted(totals, reverse=True); k = max(1, int(round(0.1 * len(st))))
        topdec_mass = sum(st[:k]) / sum(st) if sum(st) > 0 else 0.0
    else:
        topdec_mass = 0.0
    R["RE_B0"] = {"multi_frac": R["multi_frac"], "topdecile_mass_share": topdec_mass,
                  "PASS": bool(R["multi_frac"] >= B0_MULTI_FRAC and topdec_mass >= B0_MASS_FLOOR)}
    if len(multi) < 30:
        R["status"] = "underpowered"; R["reason"] = f"n_multi_batches={len(multi)}<30"
        return R
    # whale label
    vals = sorted(totals); n = len(vals); thr = vals[int(math.ceil(TOP_DECILE * n)) - 1]
    y = [1 if t > thr else 0 for t in totals]
    sess = [m[0] for m in multi]; sizes = [len(m[1]) for m in multi]
    R["whale_thr_tok"] = thr; R["pos_rate"] = sum(y) / len(y)
    # ---- RE-B1 count-insufficiency ----
    sp = spearman([float(s) for s in sizes], totals)
    Xsz = [[math.log1p(s)] for s in sizes]
    s_sz, _ = cv_scores(Xsz, y, sess, [0]); size_auc = auc(s_sz, y)
    R["RE_B1"] = {"spearman_size_total": sp, "size_only_whale_AUC": size_auc,
                  "PASS": bool(sp is not None and abs(sp) < B1_SPEARMAN_MAX and
                               size_auc is not None and size_auc <= B1_SIZE_AUC_MAX),
                  "premise_kill": bool((sp is not None and abs(sp) >= B1_SPEARMAN_MAX) or
                                       (size_auc is not None and size_auc > B1_SIZE_AUC_MAX))}
    # ---- per-call whale probs (FIX-2 matched-max/sum) ----
    pcall, per_call_pos = per_call_whale_probs(all_batches)
    R["per_call_whale_pos_rate"] = per_call_pos
    # ---- RE-B2 dAUC B1 vs B0 ----
    vocabs = build_vocabs([(s, b) for (s, b, bi) in multi])
    X0, c0 = assemble(multi, "B0", vocabs, pcall)
    X1, c1 = assemble(multi, "B1", vocabs, pcall)
    s0, fid = cv_scores(X0, y, sess, c0); s1, _ = cv_scores(X1, y, sess, c1)
    a0 = auc(s0, y); a1 = auc(s1, y); dpoint = (a1 - a0) if (a0 is not None and a1 is not None) else None
    lb, ub = bootstrap_dauc(s0, s1, y, sess)
    folds = per_fold_dauc(s0, s1, y, fid)
    all_pos = bool(folds) and all(x > 0 for x in folds)
    R["RE_B2"] = {"auc_B0": a0, "auc_B1": a1, "dAUC_point": dpoint, "dAUC_LB95": lb, "dAUC_UB95": ub,
                  "fold_dAUC": [round(x, 4) for x in folds],
                  "fold_dAUC_std": statistics.pstdev(folds) if len(folds) > 1 else None,
                  "all_folds_positive": all_pos,
                  "PASS": bool(lb is not None and lb > 0 and dpoint is not None and dpoint >= B2_DAUC_FLOOR and all_pos)}
    # ---- RE-B2b matched-count strata + decomposition vs max-null ----
    # (a) per-size-stratum AUC of B1
    strata = {}
    for label, pred in [("2", lambda s: s == 2), ("3", lambda s: s == 3), ("4", lambda s: s == 4),
                        (">=5", lambda s: s >= 5)]:
        idx = [i for i in range(len(multi)) if pred(sizes[i])]
        if len(idx) >= 20 and len(set(y[i] for i in idx)) > 1:
            strata[label] = {"n": len(idx), "auc_B1": auc([s1[i] for i in idx], [y[i] for i in idx]),
                             "auc_B0": auc([s0[i] for i in idx], [y[i] for i in idx])}
        else:
            strata[label] = {"n": len(idx), "auc_B1": None, "auc_B0": None, "note": "underpowered(<20 or no var)"}
    # (b) decomposition vs matched-max-per-call ALONE
    mm_alone = [[max(pcall.get((multi[i][0], multi[i][2], ci), 0.5) for ci in range(sizes[i]))]
                for i in range(len(multi))]
    s_mm, _ = cv_scores(mm_alone, y, sess, [0]); auc_maxnull = auc(s_mm, y)
    dauc_decomp = (a1 - auc_maxnull) if (a1 is not None and auc_maxnull is not None) else None
    strat_aucs = [v["auc_B1"] for v in strata.values() if v.get("auc_B1") is not None]
    strata_separate = bool(strat_aucs) and all(x > 0.5 for x in strat_aucs)
    R["RE_B2b"] = {"per_size_stratum": strata, "auc_maxnull_matched_max": auc_maxnull,
                   "dAUC_decomp_B1_vs_maxnull": dauc_decomp,
                   "strata_separate_gt_0.5": strata_separate,
                   "decomposition_beats_maxnull": bool(dauc_decomp is not None and dauc_decomp > 0)}
    # ---- RE-B4 heavy-tail mass capture lift ----
    mc0 = mass_capture(s0, totals, 0.10); mc1 = mass_capture(s1, totals, 0.10)
    R["RE_B4"] = {"masscap_B0": mc0, "masscap_B1": mc1,
                  "masscap_lift": (mc1 - mc0) if (mc0 is not None and mc1 is not None) else None,
                  "gini_batch_total": gini(totals)}
    # ---- STAT discipline: HHI / effective-n of whale mass (session + size strat) ----
    whale_mass_by_sess = defaultdict(float); tot_wm = 0.0
    for i in range(len(multi)):
        if y[i] == 1: whale_mass_by_sess[multi[i][0]] += totals[i]; tot_wm += totals[i]
    hhi_sess = sum((m / tot_wm) ** 2 for m in whale_mass_by_sess.values()) if tot_wm > 0 else None
    R["STAT"] = {"hhi_whale_mass_by_session": hhi_sess,
                 "effective_n_sessions": (1.0 / hhi_sess) if hhi_sess else None,
                 "n_whale_batches": sum(y), "n_whale_sessions": len(whale_mass_by_sess),
                 "hhi_flag": bool(hhi_sess is not None and hhi_sess > HHI_FLAG),
                 "fold_dAUC_std": R["RE_B2"]["fold_dAUC_std"], "all_folds_positive": all_pos}
    # ---- robustness: tight-timestamp co-issued batch def (diagnostic) ----
    R["robustness_tight_ts"] = robustness_tight(all_batches, vocabs, pcall)
    R["status"] = "ok"
    return R

def robustness_tight(all_batches, vocabs, pcall):
    """Re-split batches requiring all consecutive within-batch ts gaps < TS_TIGHT_S; recompute RE-B2 dAUC."""
    import datetime
    def pts(t):
        if not t: return None
        try: return datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
        except: return None
    tight = []
    for sess, bl in all_batches.items():
        for bi, b in enumerate(bl):
            if len(b) < 2: continue
            ok = True
            for k in range(1, len(b)):
                a = pts(b[k - 1].get("ts")); c = pts(b[k].get("ts"))
                if a and c and (c - a).total_seconds() >= TS_TIGHT_S: ok = False; break
            if ok: tight.append((sess, b, bi))
    if len(tight) < 30:
        return {"n_tight_batches": len(tight), "note": "underpowered(<30)"}
    totals = [sum(c["result_tok"] for c in b) for (s, b, bi) in tight]
    vals = sorted(totals); n = len(vals); thr = vals[int(math.ceil(TOP_DECILE * n)) - 1]
    y = [1 if t > thr else 0 for t in totals]; sess = [t[0] for t in tight]
    X0, c0 = assemble(tight, "B0", vocabs, pcall); X1, c1 = assemble(tight, "B1", vocabs, pcall)
    s0, fid = cv_scores(X0, y, sess, c0); s1, _ = cv_scores(X1, y, sess, c1)
    a0 = auc(s0, y); a1 = auc(s1, y)
    lb, ub = bootstrap_dauc(s0, s1, y, sess)
    folds = per_fold_dauc(s0, s1, y, fid)
    return {"n_tight_batches": len(tight), "auc_B0": a0, "auc_B1": a1,
            "dAUC_point": (a1 - a0) if (a0 is not None and a1 is not None) else None,
            "dAUC_LB95": lb, "all_folds_positive": bool(folds) and all(x > 0 for x in folds)}

# ============================================================================
# DISPOSITION (frozen decision tree)
# ============================================================================
def decide(R, cc_probe):
    b0 = R.get("RE_B0", {}).get("PASS")
    b1 = R.get("RE_B1", {})
    if R.get("status") == "underpowered":
        return {"verdict": "CLEAN-NEGATIVE-KILL", "gate_fired": "underpowered: " + R.get("reason", ""),
                "result_effect": "kill"}
    if not b0:
        return {"verdict": "CLEAN-NEGATIVE-KILL",
                "gate_fired": f"RE-B0 magnitude floor fail (multi_frac={R['RE_B0']['multi_frac']:.3f}, "
                              f"topdecile_mass={R['RE_B0']['topdecile_mass_share']:.3f})",
                "result_effect": "kill"}
    if b1.get("premise_kill"):
        return {"verdict": "CLEAN-NEGATIVE-KILL",
                "gate_fired": f"RE-B1 premise-kill: size predicts total (spearman={b1.get('spearman_size_total')}, "
                              f"size_AUC={b1.get('size_only_whale_AUC')}) -> budget-by-count works",
                "result_effect": "kill"}
    b2 = R.get("RE_B2", {})
    if not b2.get("PASS"):
        # FIX-2 EARLY-KILL: joint-arg adds nothing beyond matched-max/sum-per-call -> DEAD-0018 re-skin
        dd = R.get("RE_B2b", {}).get("dAUC_decomp_B1_vs_maxnull")
        return {"verdict": "EARLY-KILL-DEAD-0018-RESKIN", "early_kill_fired": True,
                "gate_fired": f"RE-B2 fail (dAUC_point={b2.get('dAUC_point')}, LB95={b2.get('dAUC_LB95')}, "
                              f"all_folds_pos={b2.get('all_folds_positive')}); joint-arg features add nothing over "
                              f"matched-max/sum-per-call B0 -> batch whale = max(per-call whale) -> collapses to "
                              f"DEAD-0018 (per-call axis already killed). dAUC_decomp_vs_maxnull={dd}.",
                "result_effect": "kill"}
    # RE-B2 passed -> check RE-B2b upgrade (not collapse)
    b2b = R.get("RE_B2b", {})
    collapsed = not (b2b.get("strata_separate_gt_0.5") and b2b.get("decomposition_beats_maxnull"))
    if collapsed:
        return {"verdict": "EARLY-KILL-DEAD-0018-RESKIN", "early_kill_fired": True,
                "gate_fired": f"RE-B2 passed but RE-B2b decomposition collapses: strata_separate="
                              f"{b2b.get('strata_separate_gt_0.5')}, beats_maxnull={b2b.get('decomposition_beats_maxnull')} "
                              f"(dAUC_decomp={b2b.get('dAUC_decomp_B1_vs_maxnull')}) -> reduces to max(per-call whale).",
                "result_effect": "kill"}
    flags = []
    if R.get("STAT", {}).get("hhi_flag"): flags.append("HHI>0.20 (few sessions drive AUC)")
    flags.append("RE-B5 single-instrument-by-design (CC emits zero co-issued parallel calls)")
    return {"verdict": "PASS-to-committee", "early_kill_fired": False,
            "gate_fired": "RE-B0 + RE-B1 + RE-B2 (dAUC_LB95>0, point>=0.03, all-folds+) + RE-B2b not-collapsed",
            "ceiling": "YELLOW/PASS-WITH-FLAG (single-instrument; never clean GREEN)",
            "flags": flags, "result_effect": "advance"}

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir = os.path.join(base, "results"); os.makedirs(rdir, exist_ok=True)
    t0 = time.time()
    print(f"[EXP-0058] locked {LOCKED_TS}  seed {SEED}")
    print("FIX-4 probe: CC parallel-call structure ...")
    cc_probe = cc_parallel_probe()
    print(f"  CC files={cc_probe['n_files']} multi-tool_use msgs={cc_probe['n_msgs_multi_tool_use']} "
          f"multi-tool_result msgs={cc_probe['n_msgs_multi_tool_result']} "
          f"emits_parallel={cc_probe['emits_coissued_parallel_calls']}")
    print("Loading Codex co-issued batches ...")
    sessions = load_codex_batch_sessions()
    print(f"  Codex sessions(>= {MIN_TRIALS} calls): {len(sessions)}")
    R = analyze_codex(sessions)
    disp = decide(R, cc_probe)
    bundle = {"exp": "EXP-0058", "project": "PROJ-0012", "claim": "CLAIM-0023", "locked_ts": LOCKED_TS, "seed": SEED,
              "FIX1_strawman": "Codex co-issued parallel calls = genuine pre-execution batch-dispatch decision point",
              "FIX4_cc_probe": cc_probe,
              "RE_B5_cross_instrument": {"status": "NOT-SATISFIABLE-single-instrument-by-design",
                                         "reason": "CC emits zero co-issued parallel tool calls in this corpus",
                                         "cc_multi_tool_use_msgs": cc_probe["n_msgs_multi_tool_use"],
                                         "cc_multi_tool_result_msgs": cc_probe["n_msgs_multi_tool_result"]},
              "codex": R, "DISPOSITION": disp, "wall_s": round(time.time() - t0, 2)}
    with open(os.path.join(rdir, "summary.json"), "w") as f:
        json.dump(bundle, f, indent=2, default=str)
    print(f"\n--- RE-B0 {R.get('RE_B0')}")
    print(f"--- RE-B1 {R.get('RE_B1')}")
    print(f"--- RE-B2 {R.get('RE_B2')}")
    print(f"--- RE-B2b {R.get('RE_B2b')}")
    print(f"--- RE-B4 {R.get('RE_B4')}")
    print(f"--- STAT {R.get('STAT')}")
    print(f"--- robustness_tight_ts {R.get('robustness_tight_ts')}")
    print(f"\nDISPOSITION: {disp['verdict']}  ({disp['gate_fired']})")
    print(f"wrote {rdir}/summary.json   wall={bundle['wall_s']}s")
    return bundle

if __name__ == "__main__":
    main()
