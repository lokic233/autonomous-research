#!/usr/bin/env python3
"""
EXP-0055 — Within-Tool Pre-Execution Prediction of Result-Prefill Whales (PROJ-0009 / CLAIM-0020).
Pure stdlib, Mac CPU. Executes the FROZEN PRE_REGISTRATION.md (locked 2026-06-01T19:11:52Z).

QUESTION: WITHIN a high-volume tool class, can a cheap PRE-EXECUTION feature of the ARGUMENTS predict which call
is a result-prefill WHALE (top-decile result token length) OVER AND ABOVE a JOINT baseline that already includes
tool identity + an arg-TEMPLATE feature (sub-tool identity)? If arg-STRUCTURE adds nothing over arg-template B0,
the thesis is FALSIFIED as sub-tool identity recovery -> CLEAN NEGATIVE.

Reuses the EXP-0054 parse/JOIN/auc/logistic/standardize/session-clustered-CV/2000x-bootstrap machinery verbatim;
CHANGES the label (top-decile result length, per tool), the feature sets (B0 arg-template / B1 +arg-structure),
the unit (per CALL not per repeat), and the gate suite (RE-A0..A5 + stat discipline).

NO numpy/torch. RE-A2 (no-leakage) BY CONSTRUCTION: X is derived from args_str ONLY; result text NEVER enters X.
"""
import json, glob, os, re, math, random, statistics
from collections import defaultdict

# ---------------- FROZEN CONSTANTS (from pre-registration) ----------------
SEED            = 20260601
CHARS_PER_TOK   = 4.0
MIN_TRIALS      = 8
TOP_DECILE      = 0.90
POWER_N         = 150
POWER_POS_FLOOR = 0.02
TEMPLATE_TOPK   = 24
NFOLD           = 5
NBOOT           = 2000
L2              = 1.0
GD_ITERS        = 400
GD_LR           = 0.3
A1_POINT_FLOOR  = 0.03
A0_SHARE_FLOOR  = 0.50
HHI_FLAG        = 0.2
LOCKED_TS       = "2026-06-01T19:11:52Z"

random.seed(SEED)

def det_hash(s):
    import hashlib
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

# ---------------- PARSERS (EXP-0054 JOIN layer; per-call w/ stream offsets) ----------------
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

# ---------------- per-call record assembly (gap, freq, label inputs) ----------------
def build_call_records(sessions):
    """All calls across sessions -> list of dicts with name, args_str, inp, result_tok, gap_tok, tool_freq, sess."""
    recs=[]
    for sname, calls in sessions.items():
        freq=defaultdict(int)
        for c in calls: freq[c["name"]]+=1
        prev_end=None
        for c in calls:
            gap_tok = 0.0 if prev_end is None else max(0.0,(c["start_pos"]-prev_end)/CHARS_PER_TOK)
            prev_end=c["end_pos"]
            recs.append(dict(name=c["name"], args_str=c["args_str"], inp=c["inp"],
                             result_tok=len(c["result"])/CHARS_PER_TOK, gap_tok=gap_tok,
                             tool_freq=freq[c["name"]], sess=sname))
    return recs

# ---------------- arg-template (B0 sub-tool identity) + arg-structure (B1) from args_str ONLY ----------------
def arg_template(name, inp, args_str):
    if isinstance(inp, dict):
        cmd=inp.get("command")
        if isinstance(cmd,str) and cmd.strip():
            return "cmd:"+os.path.basename(cmd.strip().split()[0])[:24]
        for k in ("file_path","path","notebook_path","filePath"):
            v=inp.get(k)
            if isinstance(v,str) and v:
                ext=os.path.splitext(v)[1].lower()
                return "ext:"+(ext if ext else "noext")
        u=inp.get("url") or inp.get("query")
        if isinstance(u,str) and u:
            m=re.search(r"https?://([^/\s]+)", u)
            return "host:"+(m.group(1)[:24] if m else "q")
        keys=sorted(k for k in inp.keys())
        return "keys:"+(",".join(keys)[:32] if keys else "empty")
    s=args_str.strip()
    return "tok:"+(s.split()[0][:24] if s else "empty")

def arg_struct_feats(name, inp, args_str):
    s=args_str
    nums=re.findall(r"\d+", s)
    numeric_max=max((int(x) for x in nums[:60]), default=0)
    n_flags=len(re.findall(r"(?:^|\s)-{1,2}[A-Za-z]", s))
    has_pipe=1.0 if ("|" in s or ">" in s) else 0.0
    return [
        math.log1p(len(s)),                                   # 0 log_arg_len
        float(s.count("/")),                                  # 1 path_depth   (permuted in RE-A5)
        float(s.count("*")+s.count("?")+s.count("{")+s.count("[")),  # 2 glob_breadth (permuted in RE-A5)
        math.log1p(numeric_max),                              # 3 log_numeric_max
        float(n_flags),                                       # 4 n_flags
        has_pipe,                                             # 5 has_pipe
    ]
STRUCT_NAMES=["log_arg_len","path_depth","glob_breadth","log_numeric_max","n_flags","has_pipe"]
PERMUTE_STRUCT_IDX=[1,2]   # path_depth, glob_breadth  (RE-A5 within-session permutation)

# ---------------- AUC + logistic (EXP-0054 verbatim) ----------------
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

# ---------------- feature matrix builder ----------------
def build_X(recs, mode, pooled, template_vocab, tool_vocab, struct_override=None):
    """mode in {B0,B1}. pooled adds TOOL one-hot. Returns (X, cont_idx).
    struct_override: optional list aligned to recs giving precomputed 6-dim struct vectors (for RE-A5 permutation)."""
    X=[]
    for i,r in enumerate(recs):
        row=[math.log1p(r["gap_tok"]), math.log1p(r["tool_freq"])]   # cont 0,1
        if pooled:
            oh=[0.0]*len(tool_vocab);
            if r["name"] in tool_vocab: oh[tool_vocab[r["name"]]]=1.0
            row+=oh
        # arg-template one-hot (top-K + OTHER)
        tv=[0.0]*len(template_vocab)
        t=r["_tmpl"]
        tv[template_vocab.get(t, template_vocab["OTHER"])]=1.0
        row+=tv
        if mode=="B1":
            sv = struct_override[i] if struct_override is not None else r["_struct"]
            row+=list(sv)
        X.append(row)
    cont_idx=[0,1]
    if mode=="B1":
        base=2+(len(tool_vocab) if pooled else 0)+len(template_vocab)
        cont_idx=[0,1]+[base+k for k in range(len(STRUCT_NAMES))]
    return X, cont_idx

def cv_scores(recs, mode, pooled, template_vocab, tool_vocab, struct_override=None):
    """session-clustered 5-fold held-out scores + per-fold ids."""
    sess=[r["sess"] for r in recs]; uniq=sorted(set(sess))
    fold_of={s:(det_hash(s)%NFOLD) for s in uniq}
    foldid=[fold_of[s] for s in sess]
    X,cont=build_X(recs, mode, pooled, template_vocab, tool_vocab, struct_override)
    standardize(X, cont)
    y=[r["_y"] for r in recs]
    scores=[0.5]*len(recs)
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

def spearman(a, b):
    n=len(a)
    if n<3: return None
    def ranks(v):
        order=sorted(range(n), key=lambda i:v[i]); rk=[0.0]*n; i=0
        while i<n:
            j=i
            while j+1<n and v[order[j+1]]==v[order[i]]: j+=1
            r=(i+j)/2.0+1.0
            for k in range(i,j+1): rk[order[k]]=r
            i=j+1
        return rk
    ra=ranks(a); rb=ranks(b)
    ma=statistics.mean(ra); mb=statistics.mean(rb)
    num=sum((ra[i]-ma)*(rb[i]-mb) for i in range(n))
    da=math.sqrt(sum((ra[i]-ma)**2 for i in range(n))); db=math.sqrt(sum((rb[i]-mb)**2 for i in range(n)))
    if da==0 or db==0: return None
    return num/(da*db)

def mass_capture(scores, result_toks, frac=0.10):
    """fraction of TOTAL result-prefill mass captured by the top-frac scored calls."""
    n=len(scores); k=max(1,int(round(frac*n))); total=sum(result_toks)
    if total<=0: return None
    order=sorted(range(n), key=lambda i:scores[i], reverse=True)[:k]
    return sum(result_toks[i] for i in order)/total

def per_fold_dauc(s0,s1,y,foldid):
    folds=sorted(set(foldid)); ds=[]
    for f in folds:
        idx=[i for i in range(len(y)) if foldid[i]==f]
        a0=auc([s0[i] for i in idx],[y[i] for i in idx]); a1=auc([s1[i] for i in idx],[y[i] for i in idx])
        if a0 is not None and a1 is not None: ds.append(a1-a0)
    return ds

# ---------------- the within-tool analysis (RE-A0..A5 + stat discipline) ----------------
def label_top_decile(recs):
    """y=1 if result_tok strictly above 90th-percentile rank within this record set."""
    vals=sorted(r["result_tok"] for r in recs); n=len(vals)
    thr=vals[int(math.ceil(TOP_DECILE*n))-1]
    for r in recs: r["_y"]=1 if r["result_tok"]>thr else 0
    return thr

def attach_features(recs, template_vocab):
    for r in recs:
        r["_struct"]=arg_struct_feats(r["name"], r["inp"], r["args_str"])

def make_template_vocab(recs):
    cnt=defaultdict(int)
    for r in recs:
        t=arg_template(r["name"], r["inp"], r["args_str"]); r["_tmpl"]=t; cnt[t]+=1
    top=sorted(cnt.items(), key=lambda kv:(-kv[1],kv[0]))[:TEMPLATE_TOPK]
    vocab={t:i for i,(t,_) in enumerate(top)}
    if "OTHER" not in vocab: vocab["OTHER"]=len(vocab)
    return vocab

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

def bootstrap_spearman(scores, result_toks, recs):
    by_sess=defaultdict(list)
    for i,r in enumerate(recs): by_sess[r["sess"]].append(i)
    uniq=list(by_sess.keys()); vals=[]
    for _ in range(NBOOT//2):  # spearman bootstrap cheaper count
        pick=[uniq[random.randrange(len(uniq))] for _ in range(len(uniq))]
        idx=[]
        for sn in pick: idx.extend(by_sess[sn])
        sp=spearman([scores[i] for i in idx],[result_toks[i] for i in idx])
        if sp is not None: vals.append(sp)
    if not vals: return None,None
    vals.sort(); return vals[int(0.025*len(vals))], vals[int(0.975*len(vals))]

def hhi_whale_mass(recs):
    mass=defaultdict(float); tot=0.0
    for r in recs:
        if r["_y"]==1: mass[r["sess"]]+=r["result_tok"]; tot+=r["result_tok"]
    if tot<=0: return None
    return sum((m/tot)**2 for m in mass.values())

def permute_struct_within_session(recs, cols):
    """Return struct_override: copy of _struct with `cols` shuffled WITHIN each session."""
    override=[list(r["_struct"]) for r in recs]
    by_sess=defaultdict(list)
    for i,r in enumerate(recs): by_sess[r["sess"]].append(i)
    for sn, idxs in by_sess.items():
        for col in cols:
            vals=[recs[i]["_struct"][col] for i in idxs]
            perm=vals[:]; random.shuffle(perm)
            for k,i in enumerate(idxs): override[i][col]=perm[k]
    return override

# semantic tool-class map for RE-A3 cross-instrument (names differ across instruments)
SEMANTIC_CLASS={
    "Bash":"SHELL","exec_command":"SHELL","write_stdin":"SHELL","shell":"SHELL",
    "Read":"READ","read_file":"READ","cat":"READ","knowledge_load":"FETCH",
    "Grep":"SEARCH","grep":"SEARCH","Glob":"SEARCH",
    "WebFetch":"WEB","WebSearch":"WEB","three_pai_external_web_search":"WEB",
    "Write":"WRITE","Edit":"WRITE","apply_patch":"WRITE","Task":"TASK",
}
def semantic_class(tool):
    return SEMANTIC_CLASS.get(tool, "OTHER:"+tool)

def analyze_tool(tool, recs, pooled=False, tool_vocab=None):
    """recs already filtered to this tool (or pooled set). Returns gate dict."""
    out={"unit":tool, "n":len(recs)}
    template_vocab=make_template_vocab(recs)
    attach_features(recs, template_vocab)
    thr=label_top_decile(recs)
    y=[r["_y"] for r in recs]; pos=sum(y)
    out["pos_rate"]=pos/len(recs); out["whale_thr_tok"]=thr; out["n_pos"]=pos
    out["n_templates"]=len(template_vocab)
    if tool_vocab is None: tool_vocab={}
    # power floor
    out["powered"]= (len(recs)>=POWER_N and pos>0 and (len(recs)-pos)>0 and out["pos_rate"]>=POWER_POS_FLOOR)
    if not out["powered"]:
        out["status"]="underpowered"; return out
    # RE-A0 share (within this unit): top-decile-LENGTH calls' mass share
    rt=[r["result_tok"] for r in recs]; total=sum(rt)
    whale_mass=sum(r["result_tok"] for r in recs if r["_y"]==1)
    out["RE_A0_share"]= (whale_mass/total) if total>0 else None
    out["RE_A0_PASS"]= (out["RE_A0_share"] is not None and out["RE_A0_share"]>=A0_SHARE_FLOOR)
    # B0 / B1 CV
    s0,y0,fid=cv_scores(recs,"B0",pooled,template_vocab,tool_vocab)
    s1,y1,_  =cv_scores(recs,"B1",pooled,template_vocab,tool_vocab)
    a0=auc(s0,y0); a1=auc(s1,y1)
    out["auc_B0"]=a0; out["auc_B1"]=a1; out["dAUC_point"]=(a1-a0) if (a0 is not None and a1 is not None) else None
    lb,ub=bootstrap_dauc(s0,s1,y0,recs); out["dAUC_LB95"]=lb; out["dAUC_UB95"]=ub
    folds=per_fold_dauc(s0,s1,y0,fid)
    out["fold_dAUC"]=[round(x,4) for x in folds]
    out["fold_dAUC_std"]=statistics.pstdev(folds) if len(folds)>1 else None
    out["all_folds_positive"]= bool(folds) and all(x>0 for x in folds)
    # RE-A1
    out["RE_A1_PASS"]= (lb is not None and lb>0 and out["dAUC_point"] is not None and out["dAUC_point"]>=A1_POINT_FLOOR)
    # RE-A4 mass gate
    out["RE_A4_spearman_B1"]=spearman(s1, rt)
    sp_lb,sp_ub=bootstrap_spearman(s1, rt, recs); out["RE_A4_spearman_CI95"]=(sp_lb,sp_ub)
    out["RE_A4_masscap_B0"]=mass_capture(s0, rt); out["RE_A4_masscap_B1"]=mass_capture(s1, rt)
    if out["RE_A4_masscap_B0"] is not None and out["RE_A4_masscap_B1"] is not None:
        out["RE_A4_masscap_lift"]=out["RE_A4_masscap_B1"]-out["RE_A4_masscap_B0"]
    # RE-A5 (FROZEN) within-session permutation of path_depth/glob_breadth only
    ov=permute_struct_within_session(recs, PERMUTE_STRUCT_IDX)
    s1p,_,_=cv_scores(recs,"B1",pooled,template_vocab,tool_vocab,struct_override=ov)
    a1p=auc(s1p,y0); out["RE_A5_permuted_dAUC_point"]=(a1p-a0) if (a1p is not None and a0 is not None) else None
    out["RE_A5_survives"]= (out["RE_A5_permuted_dAUC_point"] is not None and out["RE_A5_permuted_dAUC_point"]>=A1_POINT_FLOOR)
    # RE-A5b (post-hoc diagnostic, NOT a frozen gate): permute ALL struct features within session.
    # If dAUC survives THIS, the signal is a genuine session-level confound; if it collapses, the within-call
    # arg-structure signal is real (just not carried by path/glob). Disambiguates the frozen RE-A5.
    ovall=permute_struct_within_session(recs, list(range(len(STRUCT_NAMES))))
    s1pa,_,_=cv_scores(recs,"B1",pooled,template_vocab,tool_vocab,struct_override=ovall)
    a1pa=auc(s1pa,y0); out["RE_A5b_permall_dAUC_point"]=(a1pa-a0) if (a1pa is not None and a0 is not None) else None
    out["RE_A5b_session_confound"]= (out["RE_A5b_permall_dAUC_point"] is not None and out["RE_A5b_permall_dAUC_point"]>=A1_POINT_FLOOR)
    out["semantic_class"]=semantic_class(tool)
    # HHI
    out["HHI_whale_mass"]=hhi_whale_mass(recs)
    out["HHI_flag"]= (out["HHI_whale_mass"] is not None and out["HHI_whale_mass"]>HHI_FLAG)
    out["status"]="ok"
    return out

def corpus_a0_global(recs):
    rt=sorted((r["result_tok"] for r in recs), reverse=True)
    n=len(rt); k=max(1,int(round((1-TOP_DECILE)*n))); total=sum(rt)
    return (sum(rt[:k])/total) if total>0 else None

def main():
    base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir=os.path.join(base,"results"); os.makedirs(rdir, exist_ok=True)
    print(f"[EXP-0055] locked {LOCKED_TS}  seed {SEED}")
    print("Loading corpora...")
    corpora={"cc":load_corpus("cc"), "codex":load_corpus("codex")}
    bundle={"locked_ts":LOCKED_TS,"seed":SEED,"corpora":{}}
    for cname, sess in corpora.items():
        print(f"\n===== {cname}: {len(sess)} sessions (>= {MIN_TRIALS} calls) =====")
        recs=build_call_records(sess)
        print(f"   total calls: {len(recs)}")
        tool_counts=defaultdict(int)
        for r in recs: tool_counts[r["name"]]+=1
        a0_global=corpus_a0_global(recs)
        # candidate powered tools
        cand=[t for t,c in sorted(tool_counts.items(), key=lambda kv:-kv[1]) if c>=POWER_N]
        cres={"n_sessions":len(sess),"total_calls":len(recs),
              "RE_A0_global_share":a0_global,"tool_counts":dict(sorted(tool_counts.items(),key=lambda kv:-kv[1])[:20]),
              "tools":{}}
        # within-tool
        tool_vocab_pool={t:i for i,t in enumerate(cand)}
        for t in cand:
            trecs=[dict(r) for r in recs if r["name"]==t]
            res=analyze_tool(t, trecs, pooled=False)
            cres["tools"][t]=res
            print(f"   [{t}] n={res['n']} pos_rate={res.get('pos_rate'):.3f} "
                  f"powered={res.get('powered')} dAUC={res.get('dAUC_point')} "
                  f"LB95={res.get('dAUC_LB95')} A1={res.get('RE_A1_PASS')} "
                  f"allfolds+={res.get('all_folds_positive')} A5surv={res.get('RE_A5_survives')}")
        # pooled across powered tools
        powered_tools=[t for t in cand if cres["tools"][t].get("powered")]
        if len(powered_tools)>=2:
            precs=[dict(r) for r in recs if r["name"] in powered_tools]
            # pooled label: top-decile WITHIN each tool, then pool
            for t in powered_tools:
                sub=[r for r in precs if r["name"]==t]
                vals=sorted(rr["result_tok"] for rr in sub); n=len(vals); thr=vals[int(math.ceil(TOP_DECILE*n))-1]
                for rr in sub: rr["_pool_y"]=1 if rr["result_tok"]>thr else 0
            # reuse analyze_tool but with pre-set labels: emulate by temporary override
            res=analyze_pooled(powered_tools, precs, tool_vocab_pool)
            cres["tools"]["__POOLED__"]=res
            print(f"   [POOLED {len(powered_tools)} tools] n={res['n']} dAUC={res.get('dAUC_point')} "
                  f"LB95={res.get('dAUC_LB95')} A1={res.get('RE_A1_PASS')}")
        cres["powered_tools"]=powered_tools
        bundle["corpora"][cname]=cres
    # RE-A3 cross-instrument sign agreement (per shared powered tool)
    bundle["RE_A3"]=cross_instrument(bundle)
    # overall disposition
    bundle["DISPOSITION"]=decide(bundle)
    with open(os.path.join(rdir,"summary.json"),"w") as f:
        json.dump(bundle,f,indent=2,default=str)
    print(f"\nDISPOSITION: {bundle['DISPOSITION']['verdict']}  ({bundle['DISPOSITION']['gate_fired']})")
    print(f"wrote {rdir}/summary.json")
    return bundle

def analyze_pooled(powered_tools, precs, tool_vocab_pool):
    out={"unit":"POOLED","n":len(precs),"pooled_tools":powered_tools}
    template_vocab=make_template_vocab(precs)
    attach_features(precs, template_vocab)
    for r in precs: r["_y"]=r["_pool_y"]
    y=[r["_y"] for r in precs]; pos=sum(y)
    out["pos_rate"]=pos/len(precs); out["n_pos"]=pos; out["powered"]=True
    rt=[r["result_tok"] for r in precs]; total=sum(rt)
    out["RE_A0_share"]=sum(r["result_tok"] for r in precs if r["_y"]==1)/total if total>0 else None
    out["RE_A0_PASS"]= out["RE_A0_share"] is not None and out["RE_A0_share"]>=A0_SHARE_FLOOR
    s0,y0,fid=cv_scores(precs,"B0",True,template_vocab,tool_vocab_pool)
    s1,y1,_  =cv_scores(precs,"B1",True,template_vocab,tool_vocab_pool)
    a0=auc(s0,y0); a1=auc(s1,y1)
    out["auc_B0"]=a0; out["auc_B1"]=a1; out["dAUC_point"]=(a1-a0) if (a0 and a1) else None
    lb,ub=bootstrap_dauc(s0,s1,y0,precs); out["dAUC_LB95"]=lb; out["dAUC_UB95"]=ub
    folds=per_fold_dauc(s0,s1,y0,fid); out["fold_dAUC"]=[round(x,4) for x in folds]
    out["fold_dAUC_std"]=statistics.pstdev(folds) if len(folds)>1 else None
    out["all_folds_positive"]=bool(folds) and all(x>0 for x in folds)
    out["RE_A1_PASS"]= (lb is not None and lb>0 and out["dAUC_point"] is not None and out["dAUC_point"]>=A1_POINT_FLOOR)
    out["RE_A4_spearman_B1"]=spearman(s1, rt)
    out["RE_A4_masscap_B0"]=mass_capture(s0, rt); out["RE_A4_masscap_B1"]=mass_capture(s1, rt)
    if out["RE_A4_masscap_B0"] is not None and out["RE_A4_masscap_B1"] is not None:
        out["RE_A4_masscap_lift"]=out["RE_A4_masscap_B1"]-out["RE_A4_masscap_B0"]
    ov=permute_struct_within_session(precs, PERMUTE_STRUCT_IDX)
    s1p,_,_=cv_scores(precs,"B1",True,template_vocab,tool_vocab_pool,struct_override=ov)
    a1p=auc(s1p,y0); out["RE_A5_permuted_dAUC_point"]=(a1p-a0) if (a1p and a0) else None
    out["RE_A5_survives"]= out["RE_A5_permuted_dAUC_point"] is not None and out["RE_A5_permuted_dAUC_point"]>=A1_POINT_FLOOR
    ovall=permute_struct_within_session(precs, list(range(len(STRUCT_NAMES))))
    s1pa,_,_=cv_scores(precs,"B1",True,template_vocab,tool_vocab_pool,struct_override=ovall)
    a1pa=auc(s1pa,y0); out["RE_A5b_permall_dAUC_point"]=(a1pa-a0) if (a1pa and a0) else None
    out["RE_A5b_session_confound"]= out["RE_A5b_permall_dAUC_point"] is not None and out["RE_A5b_permall_dAUC_point"]>=A1_POINT_FLOOR
    out["HHI_whale_mass"]=hhi_whale_mass(precs); out["HHI_flag"]= out["HHI_whale_mass"] is not None and out["HHI_whale_mass"]>HHI_FLAG
    out["status"]="ok"
    return out

def cross_instrument(bundle):
    """RE-A3 HARD GATE by SEMANTIC class (tool names differ across instruments).
    For each semantic class, take the highest-n powered tool's dAUC per corpus; report sign agreement."""
    per={}
    for cname in ("cc","codex"):
        tools=bundle["corpora"].get(cname,{}).get("tools",{})
        best={}
        for t,res in tools.items():
            if t=="__POOLED__" or res.get("status")!="ok" or not res.get("powered"): continue
            sc=res.get("semantic_class") or semantic_class(t)
            if sc not in best or res["n"]>best[sc]["n"]:
                best[sc]={"tool":t,"n":res["n"],"dAUC":res.get("dAUC_point")}
        per[cname]=best
    classes=set(per["cc"])|set(per["codex"]); out={}
    for sc in sorted(classes):
        cc=per["cc"].get(sc); cx=per["codex"].get(sc)
        rec={"cc":cc,"codex":cx}
        if cc and cx and cc["dAUC"] is not None and cx["dAUC"] is not None:
            rec["sign_agree"]=((cc["dAUC"]>0)==(cx["dAUC"]>0))
            rec["both_present"]=True
        else:
            rec["sign_agree"]=None; rec["both_present"]=False
        out[sc]=rec
    return out

def decide(bundle):
    """PASS iff >=1 powered tool clears ALL of:
       RE-A1 (dAUC_LB95>0 & point>=0.03) + all-folds-positive + RE-A5 not-survive (frozen)
       + RE-A3 HARD GATE: its SEMANTIC class is powered in BOTH corpora with SAME-SIGN dAUC."""
    a3=bundle["RE_A3"]
    winners=[]; near=[]
    for cname,cres in bundle["corpora"].items():
        for t,res in cres.get("tools",{}).items():
            if t=="__POOLED__" or res.get("status")!="ok": continue
            if not (res.get("RE_A1_PASS") and res.get("all_folds_positive") and not res.get("RE_A5_survives")):
                continue
            near.append(f"{cname}:{t}")
            sc=res.get("semantic_class") or semantic_class(t)
            rec=a3.get(sc,{})
            if rec.get("both_present") and rec.get("sign_agree"):
                winners.append(f"{cname}:{t} ({sc})")
    if winners:
        return {"verdict":"PASS",
                "gate_fired":"RE-A1 + all-folds-positive + RE-A5 not-survive + RE-A3 cross-instrument sign-agree",
                "winners":winners}
    # Build the honest kill narrative naming exactly which gate stopped each A1-passing tool.
    reasons=[]
    a1_pass=[]
    for cname,cres in bundle["corpora"].items():
        for t,res in cres.get("tools",{}).items():
            if t=="__POOLED__" or res.get("status")!="ok": continue
            if res.get("RE_A1_PASS"):
                a1_pass.append(f"{cname}:{t}")
                sc=res.get("semantic_class") or semantic_class(t)
                rec=a3.get(sc,{})
                if res.get("RE_A5_survives"):
                    reasons.append(f"{cname}:{t}({sc}) A1-pass(dAUC={round(res['dAUC_point'],3)}) but RE-A5 path/glob permutation survives (perm={round(res.get('RE_A5_permuted_dAUC_point') or 0,3)}); A5b-permall={round(res.get('RE_A5b_permall_dAUC_point') or 0,3)} session_confound={res.get('RE_A5b_session_confound')}")
                elif not (rec.get("both_present") and rec.get("sign_agree")):
                    if not rec.get("both_present"):
                        reasons.append(f"{cname}:{t}({sc}) A1-pass(dAUC={round(res['dAUC_point'],3)}) but RE-A3 HARD GATE fails: semantic class not powered in the other instrument -> no cross-instrument replication")
                    else:
                        reasons.append(f"{cname}:{t}({sc}) A1-pass(dAUC={round(res['dAUC_point'],3)}) but RE-A3 sign DISAGREES across instruments: cc={rec['cc']['dAUC'] if rec.get('cc') else None} codex={rec['codex']['dAUC'] if rec.get('codex') else None}")
                elif not res.get("all_folds_positive"):
                    reasons.append(f"{cname}:{t}({sc}) A1-pass but folds not all positive")
            else:
                reasons.append(f"{cname}:{t} RE-A1 fail (dAUC_point={round(res['dAUC_point'],3) if res.get('dAUC_point') is not None else None}, LB95={round(res['dAUC_LB95'],3) if res.get('dAUC_LB95') is not None else None}) -> arg-structure adds nothing over arg-template B0")
    # name the primary gate: if any A1-passing tool exists, the kill is RE-A3/RE-A5; else it's RE-A1.
    if a1_pass:
        gate="RE-A3 cross-instrument HARD GATE (sign flip / non-replication) + RE-A5 (within-session confound) — within-instrument signal does NOT generalize"
    else:
        gate="RE-A1 (arg-structure adds nothing over arg-template B0 -> sub-tool identity recovery)"
    return {"verdict":"KILL-NEGATIVE","gate_fired":gate,"a1_passing_tools":a1_pass,"reasons":reasons}

if __name__=="__main__":
    main()
