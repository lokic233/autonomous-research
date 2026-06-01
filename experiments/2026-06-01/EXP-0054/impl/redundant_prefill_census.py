#!/usr/bin/env python3
"""
EXP-0054 — Redundant Tool-Call Prefill Tax census (PROJ-0008 / CLAIM-0018).
Pure stdlib, Mac CPU. Executes the FROZEN PRE_REGISTRATION.md (locked 2026-06-01T17:40:50Z).

Measures within-session BYTE-IDENTICAL interior tool re-invocations on real CC + Codex traces and
adjudicates RE-A1..A7 (committee fixes baked in). Reuses the EXP-0041 parse_cc/parse_codex JOIN layer
(tool_use->tool_result by id for CC; function_call->function_call_output by call_id w/ dedup for Codex),
extended to carry result text, is_error, and stream char-offsets for token-gap measurement.

NO numpy/torch. Everything (logistic regression, AUC, bootstrap) is hand-rolled stdlib.
"""
import json, glob, os, re, math, random, statistics, csv, hashlib
from collections import defaultdict

def det_hash(s):
    """deterministic int hash (Python's hash() is per-process salted -> non-reproducible folds)."""
    return int(hashlib.md5(s.encode("utf-8","ignore")).hexdigest()[:8], 16)

random.seed(20260601)

# ---------------- FROZEN CONSTANTS (from pre-registration) ----------------
MIN_TRIALS   = 8        # min tool calls per session
CHARS_PER_TOK= 4.0      # token proxy
K_ADJ_TOK    = 200      # RE-A6 adjacency cutoff (tokens)
BLOCK_TOK    = 16       # RE-A2 exact-prefix block size (tokens)
A4_FLOOR     = 0.02     # RE-A4 f floor (2%)
NBOOT        = 2000     # bootstrap resamples
NFOLD        = 5        # session-clustered CV folds
L2           = 1.0      # logistic ridge
GD_ITERS     = 400
GD_LR        = 0.3

READ_TOOLS   = {"Read","Glob","Grep","LS","NotebookRead"}
MUT_TOOLS    = {"Write","Edit","MultiEdit","NotebookEdit"}
VOL_TOOLS    = {"Bash","WebFetch","WebSearch","Task"}

def canon_args(inp):
    try:
        return json.dumps(inp, sort_keys=True, default=str)
    except Exception:
        return str(inp)

def sig_of(name, inp):
    return name + "\x00" + canon_args(name and inp or inp)

def block_text(b):
    cont=b.get("content","")
    if isinstance(cont,list):
        out=[]
        for x in cont:
            if isinstance(x,dict): out.append(x.get("text", json.dumps(x, default=str)))
            else: out.append(str(x))
        return "\n".join(out)
    return str(cont)

# ---------------- PARSERS: ordered calls w/ stream offsets ----------------
# Each call: dict(name, inp, args_str, sig, result, is_error, start_pos, end_pos, footprint_chars)
def parse_cc_session(path):
    uses={}   # id -> (name, inp, start_pos)
    events=[] # ordered (kind, payload) with running pos
    pos=0
    with open(path, errors="ignore") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try: d=json.loads(line)
            except: continue
            m=d.get("message")
            if not isinstance(m,dict): continue
            c=m.get("content")
            if isinstance(c,str):
                pos+=len(c); continue
            if not isinstance(c,list): continue
            for b in c:
                if not isinstance(b,dict):
                    pos+=len(str(b)); continue
                tp=b.get("type")
                if tp=="text":
                    pos+=len(b.get("text","") or "")
                elif tp=="tool_use":
                    name=b.get("name",""); inp=b.get("input",{}) or {}
                    astr=canon_args(inp)
                    uses[b.get("id","")]=(name, inp, astr, pos)
                    pos+=len(astr)
                elif tp=="tool_result":
                    uid=b.get("tool_use_id","")
                    rtext=block_text(b); is_err=bool(b.get("is_error"))
                    events.append(("result", uid, rtext, is_err, pos))
                    pos+=len(rtext)
                else:
                    pos+=len(json.dumps(b, default=str))
    calls=[]
    for kind, uid, rtext, is_err, rpos in events:
        u=uses.get(uid)
        if u is None:
            name, inp, astr, spos = "unknown", {}, "", rpos
        else:
            name, inp, astr, spos = u
        calls.append(dict(name=name, inp=inp, args_str=astr, sig=name+"\x00"+astr,
                          result=rtext, is_error=is_err, start_pos=spos,
                          end_pos=rpos+len(rtext), footprint=len(astr)+len(rtext)))
    return calls

def parse_codex_session(path):
    callmap={}  # call_id -> (name, args_str, start_pos)
    events=[]
    pos=0
    with open(path, errors="ignore") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try: d=json.loads(line)
            except: continue
            p=d.get("payload") or d
            tp=p.get("type")
            if tp=="function_call":
                name=p.get("name","?"); raw=p.get("arguments","")
                try:
                    a=json.loads(raw) if isinstance(raw,str) else raw
                except Exception:
                    a=raw
                astr=canon_args(a) if isinstance(a,(dict,list)) else str(a)
                callmap[p.get("call_id")]=(name, a, astr, pos)
                pos+=len(astr)
            elif tp=="function_call_output":
                cid=p.get("call_id")
                out=str(p.get("output",""))
                events.append(("result", cid, out, pos))
                pos+=len(out)
            elif tp in ("message","reasoning") or "text" in p:
                pos+=len(json.dumps(p, default=str)[:4000])
    seen=set(); calls=[]
    for kind, cid, out, rpos in events:
        if cid in seen: continue   # dedup double-log
        seen.add(cid)
        cm=callmap.get(cid)
        if cm is None:
            name, a, astr, spos = "unknown", {}, "", rpos
        else:
            name, a, astr, spos = cm
        # error heuristic from output
        m=re.search(r"exited with code (\d+)", out)
        is_err=False
        if m and m.group(1)!="0": is_err=True
        elif "error" in out[:120].lower() and "code 0" not in out: is_err=True
        calls.append(dict(name=name, inp=a, args_str=astr, sig=name+"\x00"+astr,
                          result=out, is_error=is_err, start_pos=spos,
                          end_pos=rpos+len(out), footprint=len(astr)+len(out)))
    return calls

def load_corpus(kind):
    if kind=="cc":
        fs=sorted(glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")))
        parse=parse_cc_session
    else:
        fs=sorted(glob.glob(os.path.expanduser("~/.codex/sessions/**/*.jsonl"), recursive=True))
        parse=parse_codex_session
    sessions={}
    for f in fs:
        try: calls=parse(f)
        except Exception: continue
        if len(calls)>=MIN_TRIALS:
            sessions[f]=calls
    return sessions

# ---------------- determinism class (state-aware, RE-A7) ----------------
def base_class(name):
    if name in READ_TOOLS: return "READ"
    if name in MUT_TOOLS:  return "MUT"
    if name in VOL_TOOLS:  return "VOL"
    n=name.lower()
    if any(k in n for k in ("read","list","grep","glob","cat","view")): return "READ"
    if any(k in n for k in ("write","edit","patch","apply","create")):  return "MUT"
    return "VOL"   # exec_command/shell/unknown default volatile

def target_of(call):
    inp=call["inp"]
    if isinstance(inp,dict):
        for k in ("file_path","path","notebook_path","filePath"):
            v=inp.get(k)
            if isinstance(v,str) and v: return v
    return None

def determinism_class(calls, orig_idx, rep_idx):
    """State-aware class for a READ-like repeat; conditions on intervening same-target mutation."""
    rep=calls[rep_idx]; bc=base_class(rep["name"])
    if bc=="MUT": return "MUTATING"
    if bc=="VOL": return "VOLATILE"
    # READ-like: check intervening MUTATING/VOLATILE to same target
    tgt=target_of(rep)
    if tgt is None:
        return "DETERMINISTIC"   # cannot resolve target -> ceiling acknowledged
    base=os.path.basename(tgt)
    for j in range(orig_idx+1, rep_idx):
        cj=calls[j]; bcj=base_class(cj["name"])
        if bcj=="MUT" and target_of(cj)==tgt:
            return "INVALIDATED"
        if bcj=="VOL":
            # shell/exec that names the target file -> potential mutation
            txt=cj["args_str"]
            if base and base in txt:
                return "INVALIDATED"
    return "DETERMINISTIC"

# ---------------- repeat extraction + filtering ----------------
def extract_repeats(calls):
    """Return list of repeat-records with prior linkage, gap, filters, class, result_equiv."""
    first_seen={}; last_occ={}; tool_freq=defaultdict(int)
    for c in calls: tool_freq[c["name"]]+=1
    sig_indices=defaultdict(list)
    recs=[]
    for i,c in enumerate(calls):
        s=c["sig"]
        if s in last_occ:
            pidx=last_occ[s]; prior=calls[pidx]
            gap_tok=max(0.0,(c["start_pos"]-prior["end_pos"])/CHARS_PER_TOK)
            recs.append(dict(
                idx=i, prior_idx=pidx, name=c["name"], sig=s,
                gap_tok=gap_tok,
                prior_is_error=prior["is_error"],
                tool_freq=tool_freq[c["name"]],
                footprint=c["footprint"],
                det_class=determinism_class(calls, pidx, i),
                result_equiv=(c["result"]==prior["result"]),
                non_recoverable=(gap_tok>=BLOCK_TOK),
            ))
        last_occ[s]=i
    return recs

# ---------------- AUC + logistic regression (stdlib) ----------------
def auc(scores, labels):
    pos=[s for s,y in zip(scores,labels) if y==1]
    neg=[s for s,y in zip(scores,labels) if y==0]
    if not pos or not neg: return None
    # rank-based Mann-Whitney
    order=sorted(range(len(scores)), key=lambda i:scores[i])
    ranks=[0.0]*len(scores); i=0
    while i<len(order):
        j=i
        while j+1<len(order) and scores[order[j+1]]==scores[order[i]]: j+=1
        r=(i+j)/2.0+1.0
        for k in range(i,j+1): ranks[order[k]]=r
        i=j+1
    sum_pos=sum(ranks[i] for i in range(len(scores)) if labels[i]==1)
    npos=len(pos); nneg=len(neg)
    return (sum_pos - npos*(npos+1)/2.0)/(npos*nneg)

def standardize(X, cont_idx):
    means={}; sds={}
    for j in cont_idx:
        col=[row[j] for row in X]
        m=statistics.mean(col); sd=statistics.pstdev(col) or 1.0
        means[j]=m; sds[j]=sd
    for row in X:
        for j in cont_idx:
            row[j]=(row[j]-means[j])/sds[j]
    return means, sds

def logistic_fit(X, y):
    n=len(X); d=len(X[0]) if n else 0
    w=[0.0]*d; b=0.0
    for _ in range(GD_ITERS):
        gw=[0.0]*d; gb=0.0
        for xi,yi in zip(X,y):
            z=b+sum(w[j]*xi[j] for j in range(d))
            p=1.0/(1.0+math.exp(-max(-40,min(40,z))))
            e=p-yi
            for j in range(d): gw[j]+=e*xi[j]
            gb+=e
        for j in range(d): w[j]=w[j]-GD_LR*(gw[j]/n + L2*w[j]/n)
        b=b-GD_LR*(gb/n)
    return w,b

def logistic_pred(w,b,xi):
    z=b+sum(w[j]*xi[j] for j in range(len(xi)))
    return 1.0/(1.0+math.exp(-max(-40,min(40,z))))

def build_features(recs, with_class):
    """Return (X, y, cont_idx, sessions). Features: log1p(gap), log1p(freq), tool one-hot[, class one-hot]."""
    tools=sorted({r["name"] for r in recs})
    classes=sorted({r["det_class"] for r in recs})
    tidx={t:k for k,t in enumerate(tools)}
    cidx={c:k for k,c in enumerate(classes)}
    X=[]; y=[]
    for r in recs:
        row=[math.log1p(r["gap_tok"]), math.log1p(r["tool_freq"])]
        oh=[0.0]*len(tools); oh[tidx[r["name"]]]=1.0; row+=oh
        if with_class:
            ohc=[0.0]*len(classes); ohc[cidx[r["det_class"]]]=1.0; row+=ohc
        X.append(row); y.append(1 if r["result_equiv"] else 0)
    return X, y, [0,1]

def cv_scores(recs, with_class):
    """session-clustered 5-fold CV held-out predicted scores aligned to recs order."""
    sess=[r["sess"] for r in recs]
    uniq=sorted(set(sess))
    fold_of={s:(det_hash(s)%NFOLD) for s in uniq}
    X,y,cont=build_features(recs, with_class)
    # standardize on full (continuous only); acceptable, no leakage of label
    standardize(X, cont)
    scores=[None]*len(recs)
    for f in range(NFOLD):
        tr=[i for i in range(len(recs)) if fold_of[sess[i]]!=f]
        te=[i for i in range(len(recs)) if fold_of[sess[i]]==f]
        if not tr or not te: continue
        Xtr=[X[i] for i in tr]; ytr=[y[i] for i in tr]
        if len(set(ytr))<2:
            for i in te: scores[i]=statistics.mean(ytr) if ytr else 0.5
            continue
        w,b=logistic_fit(Xtr,ytr)
        for i in te: scores[i]=logistic_pred(w,b,X[i])
    return scores, y

def re_a1(recs, corpus):
    """dAUC = AUC(B1=base+class) - AUC(B0=base) on result_equiv, session-clustered CV + bootstrap LB."""
    out={"corpus":corpus,"n":len(recs)}
    ys=[1 if r["result_equiv"] else 0 for r in recs]
    if len(recs)<30 or len(set(ys))<2 or statistics.pvariance(ys)<0.01:
        out["status"]="degenerate"; out["pos_rate"]=sum(ys)/len(ys) if ys else None
        return out
    s0,y0=cv_scores(recs, with_class=False)
    s1,y1=cv_scores(recs, with_class=True)
    a0=auc(s0,y0); a1=auc(s1,y1)
    out["auc_B0"]=a0; out["auc_B1"]=a1; out["dAUC"]=(a1-a0) if (a0 and a1) else None
    # session-clustered bootstrap of dAUC
    by_sess=defaultdict(list)
    for i,r in enumerate(recs): by_sess[r["sess"]].append(i)
    uniq=list(by_sess.keys())
    dvals=[]
    for _ in range(NBOOT):
        pick=[uniq[random.randrange(len(uniq))] for _ in range(len(uniq))]
        idx=[]
        for sname in pick: idx.extend(by_sess[sname])
        bs0=[s0[i] for i in idx]; bs1=[s1[i] for i in idx]; by=[y0[i] for i in idx]
        ba0=auc(bs0,by); ba1=auc(bs1,by)
        if ba0 is not None and ba1 is not None: dvals.append(ba1-ba0)
    if dvals:
        dvals.sort()
        out["dAUC_LB95"]=dvals[int(0.025*len(dvals))]
        out["dAUC_UB95"]=dvals[int(0.975*len(dvals))]
    out["status"]="ok"
    out["PASS"]= (out.get("dAUC_LB95") is not None and out["dAUC_LB95"]>0)
    return out

# ---------------- bootstrap CI for a session-clustered ratio ----------------
def boot_ci_ratio(by_sess_num, by_sess_den):
    # UNIVERSE = ALL sessions (denominator keys); numerator=0 for sessions w/o tax.
    # (Resampling only tax-bearing sessions would inflate the ratio -> fixed per process-integrity.)
    uniq=list(by_sess_den.keys())
    if not uniq: return (None,None)
    vals=[]
    for _ in range(NBOOT):
        pick=[uniq[random.randrange(len(uniq))] for _ in range(len(uniq))]
        num=sum(by_sess_num.get(s,0.0) for s in pick); den=sum(by_sess_den[s] for s in pick)
        if den>0: vals.append(num/den)
    if not vals: return (None,None)
    vals.sort()
    return (vals[int(0.025*len(vals))], vals[int(0.975*len(vals))])

# ---------------- main per-corpus analysis ----------------
def analyze(corpus, sessions):
    R={"corpus":corpus, "n_sessions":len(sessions)}
    all_calls=0; all_footprint=0
    all_repeats=[]
    # denominators per session for f
    den_foot=defaultdict(float)
    for sname, calls in sessions.items():
        all_calls+=len(calls)
        for c in calls:
            all_footprint+=c["footprint"]; den_foot[sname]+=c["footprint"]
        recs=extract_repeats(calls)
        for r in recs: r["sess"]=sname
        all_repeats.extend(recs)
    R["total_tool_calls"]=all_calls
    R["total_footprint_tok"]=all_footprint/CHARS_PER_TOK
    R["n_repeats_all"]=len(all_repeats)
    R["repeat_rate_calls"]=len(all_repeats)/all_calls if all_calls else None

    # RE-A6 structural filters
    n_retry=sum(1 for r in all_repeats if r["prior_is_error"])
    after_retry=[r for r in all_repeats if not r["prior_is_error"]]
    n_adjacent=sum(1 for r in after_retry if r["gap_tok"]<K_ADJ_TOK)
    surviving=[r for r in after_retry if r["gap_tok"]>=K_ADJ_TOK]
    R["n_excluded_retry"]=n_retry
    R["n_excluded_adjacent"]=n_adjacent
    R["n_surviving"]=len(surviving)
    R["gap_median_tok"]=statistics.median([r["gap_tok"] for r in surviving]) if surviving else None
    R["RE_A6_PASS"]= len(surviving)>=30

    # RE-A2 exact-prefix non-recoverable
    if surviving:
        nrec=sum(1 for r in surviving if r["non_recoverable"])
        R["RE_A2_nonrecoverable_frac"]=nrec/len(surviving)
        R["RE_A2_PASS"]= R["RE_A2_nonrecoverable_frac"]>=0.95
        # tier-2: every byte-identical repeat is content-addressable by non-prefix KV reuse
        R["tier2_nonprefix_addressable_frac"]=1.0
    else:
        R["RE_A2_nonrecoverable_frac"]=None; R["RE_A2_PASS"]=False; R["tier2_nonprefix_addressable_frac"]=None

    # RE-A3 result-equivalence
    if surviving:
        re_rate=sum(1 for r in surviving if r["result_equiv"])/len(surviving)
        R["RE_A3_result_equiv_rate"]=re_rate
        by_class=defaultdict(lambda:[0,0])
        for r in surviving:
            by_class[r["det_class"]][1]+=1
            if r["result_equiv"]: by_class[r["det_class"]][0]+=1
        R["result_equiv_by_class"]={c:{"n":v[1],"equiv":v[0],"rate":(v[0]/v[1] if v[1] else None)}
                                    for c,v in by_class.items()}
    else:
        R["RE_A3_result_equiv_rate"]=None; R["result_equiv_by_class"]={}

    # RE-A4 f token fraction + CI (recoverable tax = surviving & non_recoverable & result_equiv)
    rec_tax=[r for r in surviving if r["non_recoverable"] and r["result_equiv"]]
    R["n_recoverable_tax"]=len(rec_tax)
    num_foot=defaultdict(float)
    for r in rec_tax: num_foot[r["sess"]]+=r["footprint"]
    num_total=sum(r["footprint"] for r in rec_tax)
    R["f_token_frac"]=num_total/all_footprint if all_footprint else None
    lb,ub=boot_ci_ratio(num_foot if num_foot else {s:0.0 for s in sessions}, den_foot)
    R["f_CI95"]=(lb,ub)
    R["RE_A4_PASS"]= (R["f_token_frac"] is not None and R["f_token_frac"]>=A4_FLOOR and lb is not None and lb>0)

    # RE-A7 read-like split deterministic vs invalidated
    det=[r for r in surviving if r["det_class"]=="DETERMINISTIC"]
    inv=[r for r in surviving if r["det_class"]=="INVALIDATED"]
    R["RE_A7_deterministic_n"]=len(det); R["RE_A7_invalidated_n"]=len(inv)
    R["RE_A7_det_equiv_rate"]=(sum(1 for r in det if r["result_equiv"])/len(det)) if det else None
    R["RE_A7_inv_equiv_rate"]=(sum(1 for r in inv if r["result_equiv"])/len(inv)) if inv else None

    # RE-A1 dAUC
    R["RE_A1"]=re_a1(surviving, corpus)
    R["_surviving"]=surviving   # keep for cross-corpus
    return R

def cost_translation(f, total_footprint_tok, n_sessions):
    """RE-A4 FLOPs/TTFT/$ grounding under chunked-prefill batching."""
    wasted_tok = f*total_footprint_tok
    wasted_per_sess = wasted_tok/n_sessions if n_sessions else 0
    out={}
    for npar,thru,label in [(8e9,1e4,"8B"),(70e9,2e3,"70B")]:
        flops=wasted_tok*2*npar
        # per-session added prefill latency (s) at chunked-prefill throughput
        ttft_s=wasted_per_sess/thru
        gpu_s=wasted_tok/thru
        usd=gpu_s/3600.0*2.0   # ~$2/GPU-hr
        out[label]={"wasted_prefill_FLOPs":flops,
                    "added_TTFT_s_per_session":ttft_s,
                    "wasted_GPU_seconds_total":gpu_s,
                    "usd_at_2perGPUhr":usd,
                    "usd_per_1k_sessions":usd/max(n_sessions,1)*1000}
    out["wasted_tokens_total"]=wasted_tok
    out["wasted_tokens_per_session"]=wasted_per_sess
    return out

def main():
    base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir=os.path.join(base,"results"); os.makedirs(rdir, exist_ok=True)
    print("Loading corpora...")
    cc=load_corpus("cc"); cx=load_corpus("codex")
    print(f"  CC sessions(>= {MIN_TRIALS}): {len(cc)}   Codex sessions: {len(cx)}")

    results={}
    for corpus, sess in [("cc",cc),("codex",cx)]:
        print(f"\n===== analyzing {corpus} =====")
        R=analyze(corpus, sess)
        R["cost"]=cost_translation(R["f_token_frac"] or 0.0, R["total_footprint_tok"], R["n_sessions"])
        results[corpus]=R
        for k in ("n_sessions","total_tool_calls","n_repeats_all","repeat_rate_calls",
                  "n_excluded_retry","n_excluded_adjacent","n_surviving","gap_median_tok",
                  "RE_A2_nonrecoverable_frac","RE_A3_result_equiv_rate","n_recoverable_tax",
                  "f_token_frac","f_CI95","RE_A7_det_equiv_rate","RE_A7_inv_equiv_rate"):
            print(f"   {k:28}: {R.get(k)}")
        print(f"   result_equiv_by_class      : {R.get('result_equiv_by_class')}")
        print(f"   RE_A1                       : {R.get('RE_A1')}")
        print(f"   PASS A2={R['RE_A2_PASS']} A4={R['RE_A4_PASS']} A6={R['RE_A6_PASS']} "
              f"A1={R['RE_A1'].get('PASS')}")

    # RE-A5 cross-corpus sign replication
    def det_minus_vol(R):
        bc=R["result_equiv_by_class"]
        d=bc.get("DETERMINISTIC",{}).get("rate"); v=bc.get("VOLATILE",{}).get("rate")
        if d is None or v is None: return None
        return d-v
    cc_f=results["cc"]["f_token_frac"]; cx_f=results["codex"]["f_token_frac"]
    cc_e=det_minus_vol(results["cc"]); cx_e=det_minus_vol(results["codex"])
    a5_f = (cc_f is not None and cx_f is not None and cc_f>0 and cx_f>0)
    a5_e = (cc_e is not None and cx_e is not None and (cc_e>0)==(cx_e>0))
    re_a5={"cc_f":cc_f,"codex_f":cx_f,"cc_det_minus_vol":cc_e,"codex_det_minus_vol":cx_e,
           "f_sign_agree":a5_f,"class_effect_sign_agree":a5_e,"PASS":(a5_f and a5_e)}
    print(f"\nRE-A5 cross-corpus: {re_a5}")

    # strip non-serializable, dump
    for R in results.values(): R.pop("_surviving",None)
    bundle={"results":results,"RE_A5":re_a5,
            "frozen":{"K_ADJ_TOK":K_ADJ_TOK,"BLOCK_TOK":BLOCK_TOK,"A4_FLOOR":A4_FLOOR,
                      "CHARS_PER_TOK":CHARS_PER_TOK,"locked":"2026-06-01T17:40:50Z"}}
    with open(os.path.join(rdir,"census.json"),"w") as f:
        json.dump(bundle,f,indent=2,default=str)
    # per-corpus surviving repeat CSV
    for corpus, sess in [("cc",cc),("codex",cx)]:
        rows=[]
        for sname, calls in sess.items():
            recs=extract_repeats(calls)
            for r in recs:
                if not r["prior_is_error"] and r["gap_tok"]>=K_ADJ_TOK:
                    rows.append(dict(session=os.path.basename(sname), tool=r["name"],
                                     gap_tok=round(r["gap_tok"],1), det_class=r["det_class"],
                                     result_equiv=r["result_equiv"], non_recoverable=r["non_recoverable"],
                                     footprint_tok=round(r["footprint"]/CHARS_PER_TOK,1)))
        with open(os.path.join(rdir,f"surviving_{corpus}.csv"),"w",newline="") as fh:
            if rows:
                w=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); w.writeheader()
                for r in rows: w.writerow(r)
    print(f"\nwrote {rdir}/census.json + surviving_*.csv")
    return bundle

if __name__=="__main__":
    main()
