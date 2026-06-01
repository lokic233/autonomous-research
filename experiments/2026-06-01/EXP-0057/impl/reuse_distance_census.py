#!/usr/bin/env python3
"""
EXP-0057 — Agent KV Reuse-Distance Bimodality & Far-Reuse Predictability (PROJ-0011 / CLAIM-0022).
Pure stdlib, Mac CPU. Executes the FROZEN PRE_REGISTRATION.md (LOCKED-TS 2026-06-01T20:46:46Z).

QUESTION: Does a cheap CAUSAL (history-only) WORKING-SET feature predict which cached agent file-prefix will be
re-touched at a FAR reuse distance (gap_to_next > 8192 tok — the blocks recency-LRU wrongly evicts) OVER AND ABOVE
a JOINT baseline that already contains LRU(recency)+LFU(freq)+tool+file-class (B0), AND over a Marconi-style
reuse-forecast baseline (B0+forecast)? If not -> CLEAN NEGATIVE: existing reuse-aware policies are sufficient.

UNIT  : each file-path touch followed by >=1 LATER touch of the same path in the same session.
LABEL : next reuse of this path is FAR (gap_to_next > 8192 tok). NEAR (<512 tok) used only for RE-A0.
PATHS : from inp file_path/path/notebook_path/filePath + Bash command path tokens (>=1 '/'). identity = normpath as-given.

Reuses the EXP-0054/0055 parse+JOIN+stream-offset / auc / logistic_fit / standardize / session-clustered 5-fold CV
(det_hash%5) / 2000x session-clustered bootstrap / det_hash machinery VERBATIM. CHANGES: the unit (path-touch w/ later
reuse), the label (next-reuse-FAR), the feature sets (B0 / B1 / B0+forecast), and the gate suite (RE-A0..A4 + stat
discipline). NO numpy/torch. Features are CAUSAL (past+current call only); label is the FUTURE gap -> no leakage.
"""
import json, glob, os, re, math, random, statistics, hashlib
from collections import defaultdict

# ---------------- FROZEN CONSTANTS (from pre-registration) ----------------
SEED            = 20260601
CHARS_PER_TOK   = 4.0
MIN_TRIALS      = 8
FAR_TOK         = 8192.0
NEAR_TOK        = 512.0
A0_FAR_FLOOR    = 0.15
A0_NEAR_FLOOR   = 0.10
A1_POINT_FLOOR  = 0.03
NFOLD           = 5
NBOOT           = 2000
L2              = 1.0
GD_ITERS        = 400
GD_LR           = 0.3
TOOL_TOPK       = 12
HHI_FLAG        = 0.20
A2_DECILES      = 10
A2_DECILE_PASS  = 6        # >=6/10 deciles LB95>0.5
CAP_FRACS       = [0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 0.90]
MIN_UNITS       = 100      # RE-A1 powering
MIN_FARPOS      = 20
LOCKED_TS       = "2026-06-01T20:46:46Z"

random.seed(SEED)

MUT_TOOLS = {"Write","Edit","MultiEdit","NotebookEdit","apply_patch","write","edit"}
SHELL_TOOLS = {"Bash","shell","exec_command","exec","bash"}
WRITE_OP_RE = re.compile(r"(^|\s|;|&&|\|\|)(mv|cp|rm|tee|touch|mkdir|dd|sed\s+-i)\b")
PATH_RE = re.compile(r"(?:\.{0,2}/)?(?:[\w.@+\-]+/)+[\w.@+\-]+")

def det_hash(s):
    return int(hashlib.md5(s.encode("utf-8","ignore")).hexdigest()[:8], 16)

def canon_args(inp):
    try: return json.dumps(inp, sort_keys=True, default=str)
    except Exception: return str(inp)

def block_text(b):
    cont=b.get("content","")
    if isinstance(cont,list):
        out=[]
        for x in cont:
            if isinstance(x,dict): out.append(x.get("text", json.dumps(x, default=str)))
            else: out.append(str(x))
        return "\n".join(out)
    return str(cont)

# ---------------- PARSERS (EXP-0055 JOIN layer w/ stream offsets) ----------------
def parse_cc_session(path):
    uses={}; events=[]; pos=0
    with open(path, errors="ignore") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try: d=json.loads(line)
            except: continue
            m=d.get("message")
            if not isinstance(m,dict): continue
            c=m.get("content")
            if isinstance(c,str): pos+=len(c); continue
            if not isinstance(c,list): continue
            for b in c:
                if not isinstance(b,dict): pos+=len(str(b)); continue
                tp=b.get("type")
                if tp=="text": pos+=len(b.get("text","") or "")
                elif tp=="tool_use":
                    name=b.get("name",""); inp=b.get("input",{}) or {}
                    astr=canon_args(inp); uses[b.get("id","")]=(name, inp, astr, pos); pos+=len(astr)
                elif tp=="tool_result":
                    uid=b.get("tool_use_id",""); rtext=block_text(b); is_err=bool(b.get("is_error"))
                    events.append(("result", uid, rtext, is_err, pos)); pos+=len(rtext)
                else: pos+=len(json.dumps(b, default=str))
    calls=[]
    for kind, uid, rtext, is_err, rpos in events:
        u=uses.get(uid)
        if u is None: name, inp, astr, spos = "unknown", {}, "", rpos
        else: name, inp, astr, spos = u
        calls.append(dict(name=name, inp=inp, args_str=astr, result=rtext, is_error=is_err,
                          start_pos=spos, end_pos=rpos+len(rtext)))
    return calls

def parse_codex_session(path):
    callmap={}; events=[]; pos=0
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
                try: a=json.loads(raw) if isinstance(raw,str) else raw
                except Exception: a=raw
                astr=canon_args(a) if isinstance(a,(dict,list)) else str(a)
                callmap[p.get("call_id")]=(name, a, astr, pos); pos+=len(astr)
            elif tp=="function_call_output":
                cid=p.get("call_id"); out=str(p.get("output","")); events.append(("result", cid, out, pos)); pos+=len(out)
            elif tp in ("message","reasoning") or "text" in p:
                pos+=len(json.dumps(p, default=str)[:4000])
    seen=set(); calls=[]
    for kind, cid, out, rpos in events:
        if cid in seen: continue
        seen.add(cid)
        cm=callmap.get(cid)
        if cm is None: name, a, astr, spos = "unknown", {}, "", rpos
        else: name, a, astr, spos = cm
        calls.append(dict(name=name, inp=a, args_str=astr, result=out, is_error=False,
                          start_pos=spos, end_pos=rpos+len(out)))
    return calls

def load_corpus(kind):
    if kind=="cc":
        fs=sorted(glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))); parse=parse_cc_session
    else:
        fs=sorted(glob.glob(os.path.expanduser("~/.codex/sessions/**/*.jsonl"), recursive=True)); parse=parse_codex_session
    sessions={}
    for f in fs:
        try: calls=parse(f)
        except Exception: continue
        if len(calls)>=MIN_TRIALS: sessions[f]=calls
    return sessions

# ---------------- FILE-PATH EXTRACTION (frozen §1) ----------------
def extract_paths(call):
    """Return list of normalized path identities this call touches (file-tool fields + Bash command tokens)."""
    paths=[]
    inp=call["inp"]
    if isinstance(inp, dict):
        for k in ("file_path","path","notebook_path","filePath"):
            v=inp.get(k)
            if isinstance(v,str) and v.strip(): paths.append(v.strip())
        cmd=inp.get("command")
        if isinstance(cmd,str) and cmd:
            for m in PATH_RE.findall(cmd): paths.append(m)
    # also scan args_str for shell-style calls whose command isn't a dict field (Codex apply_patch / exec arrays)
    if call["name"] in SHELL_TOOLS or call["name"] in ("apply_patch",):
        for m in PATH_RE.findall(call["args_str"]): paths.append(m)
    # normalize + dedup within the call
    seen=set(); out=[]
    for p in paths:
        np_=os.path.normpath(p)
        if np_ in (".","/","..","") : continue
        if np_ not in seen:
            seen.add(np_); out.append(np_)
    return out

FILE_CLASS = {
    **{e:"CODE" for e in (".py",".js",".ts",".tsx",".jsx",".java",".c",".cc",".cpp",".h",".hpp",".go",".rs",
                          ".rb",".php",".swift",".kt",".scala",".sh",".pl",".lua",".m",".r")},
    **{e:"CONFIG" for e in (".json",".yaml",".yml",".toml",".ini",".cfg",".conf",".env",".lock",".properties",".gradle")},
    **{e:"DOC" for e in (".md",".markdown",".txt",".rst",".adoc")},
    **{e:"DATA" for e in (".csv",".tsv",".parquet",".jsonl",".ndjson",".arrow",".pkl",".npy",".db")},
    ".ipynb":"NOTEBOOK",
    **{e:"WEB" for e in (".html",".css",".xml",".svg")},
}
def file_class(path):
    ext=os.path.splitext(os.path.basename(path))[1].lower()
    if not ext: return "NOEXT"
    return FILE_CLASS.get(ext, "OTHER")

def is_mut(call):
    if call["name"] in MUT_TOOLS: return 1.0
    if call["name"] in SHELL_TOOLS:
        cmd=""
        if isinstance(call["inp"], dict): cmd=call["inp"].get("command","") or ""
        if not cmd: cmd=call["args_str"]
        if ">" in cmd or WRITE_OP_RE.search(cmd): return 1.0
    return 0.0

# ---------------- UNIT / FEATURE BUILD (frozen §1-2) ----------------
def build_units(sessions):
    """Emit one record per path-touch that has a later same-path touch in the session (causal features + far label)."""
    recs=[]
    all_reuse_gaps=[]   # for RE-A0: gap_to_next over ALL units
    for sname, calls in sessions.items():
        # precompute paths per call ONCE (avoid O(n^2) regex re-extraction)
        call_paths=[extract_paths(c) for c in calls]
        # ordered touch events: (call_idx, path, start_pos, end_pos, call)
        touches=[]
        for ci,c in enumerate(calls):
            for p in call_paths[ci]:
                touches.append((ci, p, c["start_pos"], c["end_pos"], c))
        by_path=defaultdict(list)
        for t in touches: by_path[t[1]].append(t)
        for p, tl in by_path.items():
            if len(tl)<2: continue   # need a later touch
            prior_gaps=[]   # genuine observed inter-touch gaps of THIS path (causal forecast history)
            for i in range(len(tl)-1):     # units = all but last
                ci, path, sp, ep, c = tl[i]
                nci, npath, nsp, nep, nc = tl[i+1]
                gap_to_next = max(0.0,(nsp - ep)/CHARS_PER_TOK)
                # gap_since_last: from prev same-path touch end -> this start; first touch -> from session start
                if i==0:
                    gap_since_last = sp/CHARS_PER_TOK; prev_ci = 0
                else:
                    pci,ppath,psp,pep,pc = tl[i-1]
                    gap_since_last = max(0.0,(sp - pep)/CHARS_PER_TOK); prev_ci = pci
                    prior_gaps.append(gap_since_last)   # genuine interval ending at THIS touch (past obs)
                freq_so_far = i+1
                lo = prev_ci if i>0 else 0
                interv_calls = max(0, ci - lo)
                distinct=set()
                for cj in range(lo, ci):
                    for q in call_paths[cj]:
                        if q!=path: distinct.add(q)
                expl_breadth = len(distinct)
                # Marconi-style forecast: running estimate from this path's PRIOR genuine inter-touch gaps
                if prior_gaps:
                    fc_mean = sum(prior_gaps)/len(prior_gaps); fc_cnt = len(prior_gaps)
                else:
                    fc_mean = 0.0; fc_cnt = 0
                recs.append(dict(
                    sess=sname, name=c["name"], path=path, file_class=file_class(path),
                    gap_since_last=gap_since_last, freq_so_far=freq_so_far,
                    path_depth=float(path.count("/")), expl_breadth=float(expl_breadth),
                    mut_flag=is_mut(c), interv_calls=float(interv_calls),
                    fc_mean=fc_mean, fc_cnt=float(fc_cnt),
                    size_tok=(len(c["args_str"])+len(c["result"]))/CHARS_PER_TOK,
                    call_idx=ci, gap_to_next=gap_to_next,
                    y=1 if gap_to_next>FAR_TOK else 0,
                ))
                all_reuse_gaps.append(gap_to_next)
    return recs, all_reuse_gaps

# ---------------- AUC + logistic (EXP-0054/0055 verbatim) ----------------
def auc(scores, labels):
    pos=[s for s,y in zip(scores,labels) if y==1]; neg=[s for s,y in zip(scores,labels) if y==0]
    if not pos or not neg: return None
    order=sorted(range(len(scores)), key=lambda i:scores[i]); ranks=[0.0]*len(scores); i=0
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
    for j in cont_idx:
        col=[row[j] for row in X]
        m=statistics.mean(col); sd=statistics.pstdev(col) or 1.0
        for row in X: row[j]=(row[j]-m)/sd

def logistic_fit(X, y):
    n=len(X); d=len(X[0]) if n else 0; w=[0.0]*d; b=0.0
    for _ in range(GD_ITERS):
        gw=[0.0]*d; gb=0.0
        for xi,yi in zip(X,y):
            z=b+sum(w[j]*xi[j] for j in range(d)); p=1.0/(1.0+math.exp(-max(-40,min(40,z)))); e=p-yi
            for j in range(d): gw[j]+=e*xi[j]
            gb+=e
        for j in range(d): w[j]=w[j]-GD_LR*(gw[j]/n + L2*w[j]/n)
        b=b-GD_LR*(gb/n)
    return w,b

def logistic_pred(w,b,xi):
    z=b+sum(w[j]*xi[j] for j in range(len(xi))); return 1.0/(1.0+math.exp(-max(-40,min(40,z))))

# ---------------- feature matrix builders (B0 / B1 / B0+forecast / WS-only) ----------------
def make_vocabs(recs):
    tcnt=defaultdict(int)
    for r in recs: tcnt[r["name"]]+=1
    top=sorted(tcnt.items(), key=lambda kv:(-kv[1],kv[0]))[:TOOL_TOPK]
    tool_vocab={t:i for i,(t,_) in enumerate(top)}; tool_vocab["OTHER"]=len(tool_vocab)
    fclasses=sorted({r["file_class"] for r in recs})
    fc_vocab={c:i for i,c in enumerate(fclasses)}
    return tool_vocab, fc_vocab

def build_X(recs, mode, tool_vocab, fc_vocab):
    """mode in {B0,B1,FC,WS}. Returns (X, cont_idx)."""
    X=[]
    for r in recs:
        if mode=="WS":
            row=[r["path_depth"], math.log1p(r["expl_breadth"]), r["mut_flag"], math.log1p(r["interv_calls"])]
            X.append(row); continue
        row=[math.log1p(r["gap_since_last"]), math.log1p(r["freq_so_far"])]   # cont 0,1
        oh=[0.0]*len(tool_vocab); oh[tool_vocab.get(r["name"], tool_vocab["OTHER"])]=1.0; row+=oh
        fc=[0.0]*len(fc_vocab); fc[fc_vocab[r["file_class"]]]=1.0; row+=fc
        if mode=="B1":
            row+=[r["path_depth"], math.log1p(r["expl_breadth"]), r["mut_flag"], math.log1p(r["interv_calls"])]
        elif mode=="FC":
            row+=[math.log1p(r["fc_mean"]), math.log1p(r["fc_cnt"])]
        X.append(row)
    base=2+len(tool_vocab)+len(fc_vocab)
    if mode=="B0": cont_idx=[0,1]
    elif mode=="B1": cont_idx=[0,1,base,base+1,base+3]            # path_depth, log expl, log interv (mut_flag binary)
    elif mode=="FC": cont_idx=[0,1,base,base+1]
    elif mode=="WS": cont_idx=[0,1,3]                              # path_depth, log expl, log interv
    return X, cont_idx

def cv_scores(recs, mode, tool_vocab, fc_vocab):
    sess=[r["sess"] for r in recs]; uniq=sorted(set(sess))
    fold_of={s:(det_hash(s)%NFOLD) for s in uniq}; foldid=[fold_of[s] for s in sess]
    X,cont=build_X(recs, mode, tool_vocab, fc_vocab); standardize(X, cont)
    y=[r["y"] for r in recs]; scores=[0.5]*len(recs)
    for f in range(NFOLD):
        tr=[i for i in range(len(recs)) if foldid[i]!=f]; te=[i for i in range(len(recs)) if foldid[i]==f]
        if not tr or not te: continue
        Xtr=[X[i] for i in tr]; ytr=[y[i] for i in tr]
        if len(set(ytr))<2:
            mv=statistics.mean(ytr) if ytr else 0.5
            for i in te: scores[i]=mv
            continue
        w,b=logistic_fit(Xtr,ytr)
        for i in te: scores[i]=logistic_pred(w,b,X[i])
    return scores, y, foldid

def per_fold_dauc(s0,s1,y,foldid):
    ds=[]
    for f in sorted(set(foldid)):
        idx=[i for i in range(len(y)) if foldid[i]==f]
        a0=auc([s0[i] for i in idx],[y[i] for i in idx]); a1=auc([s1[i] for i in idx],[y[i] for i in idx])
        if a0 is not None and a1 is not None: ds.append(a1-a0)
    return ds

def bootstrap_dauc(s0,s1,y,recs):
    by_sess=defaultdict(list)
    for i,r in enumerate(recs): by_sess[r["sess"]].append(i)
    uniq=list(by_sess.keys()); dvals=[]
    for _ in range(NBOOT):
        pick=[uniq[random.randrange(len(uniq))] for _ in range(len(uniq))]
        idx=[]
        for sn in pick: idx.extend(by_sess[sn])
        ba0=auc([s0[i] for i in idx],[y[i] for i in idx]); ba1=auc([s1[i] for i in idx],[y[i] for i in idx])
        if ba0 is not None and ba1 is not None: dvals.append(ba1-ba0)
    if not dvals: return None,None
    dvals.sort(); return dvals[int(0.025*len(dvals))], dvals[int(0.975*len(dvals))]

def hhi_by_session(recs):
    cnt=defaultdict(int)
    for r in recs: cnt[r["sess"]]+=1
    tot=len(recs)
    if tot==0: return None
    return sum((c/tot)**2 for c in cnt.values())

# ---------------- RE-A1 (per corpus) ----------------
def re_a1(recs, corpus, tool_vocab, fc_vocab):
    out={"corpus":corpus,"n_units":len(recs),"n_sessions":len(set(r["sess"] for r in recs))}
    y=[r["y"] for r in recs]; pos=sum(y)
    out["far_pos"]=pos; out["pos_rate"]=pos/len(recs) if recs else None
    out["HHI_session"]=hhi_by_session(recs); out["HHI_flag"]=(out["HHI_session"] is not None and out["HHI_session"]>HHI_FLAG)
    if len(recs)<MIN_UNITS or pos<MIN_FARPOS or pos==0 or pos==len(recs) or out["n_sessions"]<2:
        out["status"]="underpowered"; return out
    s0,y0,fid=cv_scores(recs,"B0",tool_vocab,fc_vocab)
    s1,_,_  =cv_scores(recs,"B1",tool_vocab,fc_vocab)
    a0=auc(s0,y0); a1=auc(s1,y0)
    out["auc_B0"]=a0; out["auc_B1"]=a1; out["dAUC_point"]=(a1-a0) if (a0 is not None and a1 is not None) else None
    lb,ub=bootstrap_dauc(s0,s1,y0,recs); out["dAUC_LB95"]=lb; out["dAUC_UB95"]=ub
    folds=per_fold_dauc(s0,s1,y0,fid); out["fold_dAUC"]=[round(x,4) for x in folds]
    out["fold_dAUC_std"]=statistics.pstdev(folds) if len(folds)>1 else None
    out["all_folds_positive"]=bool(folds) and all(x>0 for x in folds)
    out["RE_A1_PASS"]=(lb is not None and lb>0 and out["dAUC_point"] is not None
                       and out["dAUC_point"]>=A1_POINT_FLOOR and out["all_folds_positive"])
    out["status"]="ok"; out["_s0"]=s0; out["_s1"]=s1; out["_y"]=y0; out["_fid"]=fid
    return out

# ---------------- RE-A2 (matched-recency + forecast baseline) ----------------
def re_a2(recs, tool_vocab, fc_vocab, a1):
    out={}
    # (b) beat B0+forecast
    sfc,yfc,_=cv_scores(recs,"FC",tool_vocab,fc_vocab)
    s1=a1["_s1"]; y=a1["_y"]
    afc=auc(sfc,yfc); a1auc=auc(s1,y)
    out["auc_B0_forecast"]=afc; out["auc_B1"]=a1auc
    out["dAUC_fc_point"]=(a1auc-afc) if (afc is not None and a1auc is not None) else None
    lb,ub=bootstrap_dauc(sfc,s1,y,recs); out["dAUC_fc_LB95"]=lb; out["dAUC_fc_UB95"]=ub
    out["PASS_b_beats_forecast"]=(lb is not None and lb>0)
    # (a) matched-recency: ws_score deciles by gap_since_last
    sw,yw,_=cv_scores(recs,"WS",tool_vocab,fc_vocab)
    order=sorted(range(len(recs)), key=lambda i:recs[i]["gap_since_last"])
    n=len(recs); per=max(1,n//A2_DECILES)
    by_sess_global=defaultdict(list)
    deciles=[]
    npass=0
    for d in range(A2_DECILES):
        lo=d*per; hi=(d+1)*per if d<A2_DECILES-1 else n
        idx=order[lo:hi]
        ys=[recs[i]["y"] for i in idx]; ws=[sw[i] for i in idx]
        a=auc(ws,ys)
        # session-clustered bootstrap LB95 within decile
        by_sess=defaultdict(list)
        for i in idx: by_sess[recs[i]["sess"]].append(i)
        uniq=list(by_sess.keys()); vals=[]
        if a is not None and len(uniq)>=2:
            for _ in range(NBOOT):
                pick=[uniq[random.randrange(len(uniq))] for _ in range(len(uniq))]
                bi=[]
                for sn in pick: bi.extend(by_sess[sn])
                av=auc([sw[i] for i in bi],[recs[i]["y"] for i in bi])
                if av is not None: vals.append(av)
        lb_d=None
        if vals: vals.sort(); lb_d=vals[int(0.025*len(vals))]
        gmin=min(recs[i]["gap_since_last"] for i in idx); gmax=max(recs[i]["gap_since_last"] for i in idx)
        rec={"decile":d,"n":len(idx),"far_pos":sum(ys),"auc":a,"auc_LB95":lb_d,
             "gap_since_last_range":[round(gmin,1),round(gmax,1)]}
        if lb_d is not None and lb_d>0.5: npass+=1
        deciles.append(rec)
    out["deciles"]=deciles; out["n_deciles_separating"]=npass
    out["PASS_a_matched_recency"]=(npass>=A2_DECILE_PASS)
    out["RE_A2_GREEN"]=(out["PASS_a_matched_recency"] and out["PASS_b_beats_forecast"])
    return out

# ---------------- RE-A3 capacity-curve cache sim ----------------
def gini(values):
    vs=sorted(v for v in values if v>0)
    n=len(vs)
    if n==0: return None
    cum=0.0; s=sum(vs)
    if s<=0: return None
    for i,v in enumerate(vs): cum+=(i+1)*v
    return (2*cum)/(n*s) - (n+1)/n

def re_a3(sessions, b1_score_by):
    """fixed-capacity per-path cache sim per session, pooled. b1_score_by: dict (sess,call_idx,path)->far_score."""
    curve=[]
    for frac in CAP_FRACS:
        tot_lru=0.0; tot_oracle=0.0; tot_b1=0.0
        per_path_lru=defaultdict(float); per_path_b1=defaultdict(float)
        for sname, calls in sessions.items():
            touches=[]
            for ci,c in enumerate(calls):
                for p in extract_paths(c):
                    touches.append((ci,p,(len(c["args_str"])+len(c["result"]))/CHARS_PER_TOK,c))
            if not touches: continue
            distinct=set(t[1] for t in touches)
            C=max(1,int(math.ceil(frac*len(distinct))))
            # precompute next-touch index per touch position for oracle
            future=defaultdict(list)
            for k,(ci,p,sz,c) in enumerate(touches): future[p].append(k)
            nextpos=[None]*len(touches)
            seen_count=defaultdict(int)
            for k,(ci,p,sz,c) in enumerate(touches):
                occ=future[p]; idx=seen_count[p]
                nextpos[k]=occ[idx+1] if idx+1<len(occ) else math.inf
                seen_count[p]+=1
            for policy in ("lru","oracle","b1"):
                cache={}   # path -> meta (last_touch_k, nextpos, b1score)
                seen_c2=defaultdict(int)
                for k,(ci,p,sz,c) in enumerate(touches):
                    if p in cache:
                        # HIT: update recency / nextpos
                        cache[p]["last"]=k; cache[p]["next"]=nextpos[k]
                        cache[p]["b1"]=b1_score_by.get((sname,ci,p), cache[p]["b1"])
                    else:
                        # MISS -> recompute
                        if policy=="lru": tot_lru+=sz; per_path_lru[(sname,p)]+=sz
                        elif policy=="oracle": tot_oracle+=sz
                        else: tot_b1+=sz; per_path_b1[(sname,p)]+=sz
                        if len(cache)>=C:
                            if policy=="lru":
                                ev=min(cache, key=lambda q:cache[q]["last"])
                            elif policy=="oracle":
                                ev=max(cache, key=lambda q:cache[q]["next"])
                            else:
                                ev=max(cache, key=lambda q:(cache[q]["b1"], -cache[q]["last"]))
                            del cache[ev]
                        cache[p]={"last":k,"next":nextpos[k],"b1":b1_score_by.get((sname,ci,p),0.0)}
        saved_b1=(tot_lru-tot_b1)/tot_lru if tot_lru>0 else None
        saved_oracle=(tot_lru-tot_oracle)/tot_lru if tot_lru>0 else None
        curve.append({"cap_frac":frac,"recompute_LRU":round(tot_lru,1),"recompute_Oracle":round(tot_oracle,1),
                      "recompute_B1":round(tot_b1,1),"saved_frac_B1":saved_b1,"saved_frac_Oracle":saved_oracle,
                      "gini_LRU":gini(list(per_path_lru.values())),"gini_B1":gini(list(per_path_b1.values()))})
    return curve

# ---------------- main ----------------
def main():
    base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir=os.path.join(base,"results"); os.makedirs(rdir, exist_ok=True)
    print(f"[EXP-0057] locked {LOCKED_TS}  seed {SEED}")
    print("Loading corpora...")
    corpora={"cc":load_corpus("cc"), "codex":load_corpus("codex")}
    bundle={"locked_ts":LOCKED_TS,"seed":SEED,"frozen":{
        "FAR_TOK":FAR_TOK,"NEAR_TOK":NEAR_TOK,"A0_FAR_FLOOR":A0_FAR_FLOOR,"A0_NEAR_FLOOR":A0_NEAR_FLOOR,
        "A1_POINT_FLOOR":A1_POINT_FLOOR,"CHARS_PER_TOK":CHARS_PER_TOK,"NBOOT":NBOOT,"NFOLD":NFOLD,
        "MIN_UNITS":MIN_UNITS,"MIN_FARPOS":MIN_FARPOS,"CAP_FRACS":CAP_FRACS,"A2_DECILE_PASS":A2_DECILE_PASS},
        "corpora":{}}
    a1_by={}
    for cname, sess in corpora.items():
        print(f"\n===== {cname}: {len(sess)} sessions (>= {MIN_TRIALS} calls) =====")
        recs, allgaps = build_units(sess)
        nU=len(recs); print(f"   reuse units (path-touch w/ later reuse): {nU}")
        cres={"n_sessions":len(sess),"n_units":nU}
        # RE-A0 bimodality over ALL units
        if nU>0:
            share_far=sum(1 for g in allgaps if g>FAR_TOK)/nU
            share_near=sum(1 for g in allgaps if g<NEAR_TOK)/nU
            sgaps=sorted(allgaps)
            cres["RE_A0"]={"share_FAR":share_far,"share_NEAR":share_near,
                           "PASS":(share_far>=A0_FAR_FLOOR and share_near>=A0_NEAR_FLOOR),
                           "median_gap_tok":statistics.median(sgaps),
                           "p99_gap_tok":sgaps[int(0.99*len(sgaps))-1] if len(sgaps)>=100 else sgaps[-1],
                           "max_gap_tok":sgaps[-1]}
            print(f"   RE-A0 share_FAR(>{int(FAR_TOK)})={share_far:.3f} share_NEAR(<{int(NEAR_TOK)})={share_near:.3f} "
                  f"PASS={cres['RE_A0']['PASS']} median={cres['RE_A0']['median_gap_tok']:.0f} p99={cres['RE_A0']['p99_gap_tok']:.0f}")
        else:
            cres["RE_A0"]={"PASS":False,"note":"no reuse units"}
        # per-tool / per-file-class breakdown
        tb=defaultdict(lambda:[0,0]); fb=defaultdict(lambda:[0,0])
        for r in recs:
            tb[r["name"]][0]+=1; tb[r["name"]][1]+=r["y"]; fb[r["file_class"]][0]+=1; fb[r["file_class"]][1]+=r["y"]
        cres["by_tool"]={t:{"n":v[0],"far":v[1],"far_rate":(v[1]/v[0] if v[0] else None)} for t,v in
                         sorted(tb.items(), key=lambda kv:-kv[1][0])[:15]}
        cres["by_file_class"]={c:{"n":v[0],"far":v[1],"far_rate":(v[1]/v[0] if v[0] else None)} for c,v in
                               sorted(fb.items(), key=lambda kv:-kv[1][0])}
        # RE-A1
        if nU>0:
            tool_vocab, fc_vocab = make_vocabs(recs)
            a1=re_a1(recs, cname, tool_vocab, fc_vocab)
            cres["RE_A1"]={k:v for k,v in a1.items() if not k.startswith("_")}
            print(f"   RE-A1 status={a1['status']} n={a1['n_units']} far_pos={a1['far_pos']} "
                  f"dAUC={a1.get('dAUC_point')} LB95={a1.get('dAUC_LB95')} folds+={a1.get('all_folds_positive')} "
                  f"PASS={a1.get('RE_A1_PASS')} HHI={a1.get('HHI_session'):.3f}" if a1.get('HHI_session') else
                  f"   RE-A1 status={a1['status']} n={a1['n_units']} far_pos={a1['far_pos']}")
            a1_by[cname]=a1
            # RE-A2 (only if A1 powered)
            if a1["status"]=="ok":
                a2=re_a2(recs, tool_vocab, fc_vocab, a1)
                cres["RE_A2"]=a2
                print(f"   RE-A2 (a)matched-recency {a2['n_deciles_separating']}/10 PASS_a={a2['PASS_a_matched_recency']} | "
                      f"(b) dAUC_vs_forecast={a2['dAUC_fc_point']} LB95={a2['dAUC_fc_LB95']} PASS_b={a2['PASS_b_beats_forecast']} "
                      f"-> GREEN={a2['RE_A2_GREEN']}")
                # RE-A3 capacity sim (CC primary; run for both, report)
                b1_score_by={}
                for i,r in enumerate(recs):
                    b1_score_by[(r["sess"],r["call_idx"],r["path"])]=a1["_s1"][i]
                cres["RE_A3_capacity_curve"]=re_a3(sess, b1_score_by)
                print(f"   RE-A3 capacity curve computed ({len(CAP_FRACS)} settings)")
        bundle["corpora"][cname]=cres
    # RE-A4 cross-instrument sign agreement
    cc_a1=a1_by.get("cc"); cx_a1=a1_by.get("codex")
    re_a4={"cc_status":cc_a1["status"] if cc_a1 else None,"codex_status":cx_a1["status"] if cx_a1 else None,
           "cc_dAUC":cc_a1.get("dAUC_point") if cc_a1 else None,"codex_dAUC":cx_a1.get("dAUC_point") if cx_a1 else None}
    if (cc_a1 and cx_a1 and cc_a1["status"]=="ok" and cx_a1["status"]=="ok"
            and cc_a1.get("dAUC_point") is not None and cx_a1.get("dAUC_point") is not None):
        re_a4["sign_agree"]=((cc_a1["dAUC_point"]>0)==(cx_a1["dAUC_point"]>0))
        re_a4["both_positive"]=(cc_a1["dAUC_point"]>0 and cx_a1["dAUC_point"]>0)
    else:
        re_a4["sign_agree"]=None; re_a4["both_positive"]=False
        re_a4["note"]="codex underpowered or A1 not ok -> sign agreement cannot be established"
    bundle["RE_A4"]=re_a4
    print(f"\nRE-A4 cross-instrument: cc_dAUC={re_a4['cc_dAUC']} codex_dAUC={re_a4['codex_dAUC']} "
          f"sign_agree={re_a4['sign_agree']} both_positive={re_a4['both_positive']}")
    # overall disposition (CC primary)
    bundle["DISPOSITION"]=decide(bundle)
    print(f"\nDISPOSITION: {bundle['DISPOSITION']['verdict']}\n  {bundle['DISPOSITION']['rationale']}")
    with open(os.path.join(rdir,"summary.json"),"w") as f:
        json.dump(bundle,f,indent=2,default=str)
    print(f"wrote {rdir}/summary.json")
    return bundle

def decide(bundle):
    cc=bundle["corpora"].get("cc",{})
    a0=cc.get("RE_A0",{}); a1=cc.get("RE_A1",{}); a2=cc.get("RE_A2",{}); a4=bundle.get("RE_A4",{})
    if not a0.get("PASS"):
        return {"verdict":"CLEAN-KILL (RE-A0)","rationale":
                f"distribution not bimodal: share_FAR={a0.get('share_FAR')} share_NEAR={a0.get('share_NEAR')} "
                f"(need >={A0_FAR_FLOOR}/{A0_NEAR_FLOOR}) -> no eviction-distance lever."}
    if a1.get("status")!="ok":
        return {"verdict":"INCONCLUSIVE (RE-A1 underpowered)","rationale":
                f"CC reuse units n={a1.get('n_units')} far_pos={a1.get('far_pos')} below powering floor "
                f"(>={MIN_UNITS} units, >={MIN_FARPOS} far)."}
    if not a1.get("RE_A1_PASS"):
        return {"verdict":"CLEAN-NEGATIVE-KILL (RE-A1)","rationale":
                f"far-reuse NOT predictable beyond recency+freq+file-class: dAUC_point={a1.get('dAUC_point')} "
                f"LB95={a1.get('dAUC_LB95')} all_folds_positive={a1.get('all_folds_positive')} "
                f"(need point>={A1_POINT_FLOOR} & LB95>0 & all-folds+). -> LRU+LFU(+forecast) sufficient; "
                f"do NOT build a new cheap causal reuse-aware feature. HHI={a1.get('HHI_session')} flag={a1.get('HHI_flag')}."}
    # A1 passed
    if a4.get("sign_agree") is not True or not a4.get("both_positive"):
        return {"verdict":"NOT-PASS (RE-A4 cross-instrument)","rationale":
                f"CC RE-A1 PASS (dAUC={a1.get('dAUC_point')}) but cross-instrument sign agreement fails/unestablished: "
                f"cc_dAUC={a4.get('cc_dAUC')} codex_dAUC={a4.get('codex_dAUC')} codex_status={a4.get('codex_status')}. "
                f"{a4.get('note','')}"}
    if a2.get("RE_A2_GREEN"):
        return {"verdict":"GREEN-PASS","rationale":
                f"RE-A0 bimodal, RE-A1 dAUC={a1.get('dAUC_point')} (LB95={a1.get('dAUC_LB95')}, all-folds+), "
                f"RE-A2 matched-recency {a2.get('n_deciles_separating')}/10 & beats Marconi-forecast "
                f"(dAUC_fc={a2.get('dAUC_fc_point')}, LB95={a2.get('dAUC_fc_LB95')}), RE-A4 sign-agree. "
                f"HHI={a1.get('HHI_session')} flag={a1.get('HHI_flag')}."}
    return {"verdict":"YELLOW","rationale":
            f"RE-A1 PASS (dAUC={a1.get('dAUC_point')}) & RE-A4 sign-agree, but RE-A2 upgrade fails: "
            f"matched-recency PASS_a={a2.get('PASS_a_matched_recency')} ({a2.get('n_deciles_separating')}/10), "
            f"beats-forecast PASS_b={a2.get('PASS_b_beats_forecast')} (dAUC_fc={a2.get('dAUC_fc_point')}, "
            f"LB95={a2.get('dAUC_fc_LB95')}). Beats LRU+LFU+class but not the Marconi-style forecast incumbent."}

if __name__=="__main__":
    main()
