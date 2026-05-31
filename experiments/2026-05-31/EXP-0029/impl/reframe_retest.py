#!/usr/bin/env python3
"""
EXP-0029 - RE-TEST the REFRAMED CLAIM-0010 (researcher-0003-laneE). MAP-0002. CPU/stdlib-only.

REFRAMED CLAIM (post EXP-0022/VERDICT-0030):
  "Agentic failure recovery has (A) a PARTIAL coarse gate-table layer + (B) a CONTEXT-CONDITIONED
   (NOT free-adaptive) fine layer with a QUANTIFIABLE residual-entropy floor."

This re-tests the reframe RIGOROUSLY with proper out-of-sample CIs:
 (Q1) COARSE ROBUSTNESS: is the web_disabled-CARRIED determinism an artifact? Bootstrap CI on
      Theil U(modality|gate) FULL vs web_disabled-DROPPED (LOCO). If FULL U CI excludes 0 only via
      the one cell, the coarse layer is "partial" = honest. Also report per-gate modality determinism
      with bootstrap CIs (is GRANT_REQUIRED / TRANSIENT determinism distinguishable from chance?).
 (Q2) FINE IRREDUCIBLE RESIDUAL: with the BEST context model we can build out-of-sample (LOSO, not
      just LOO, to kill session-leak), what is the genuine residual-entropy floor = the
      situation-dependent remainder the context model CANNOT predict? We report:
        - context-model OUT-OF-SAMPLE accuracy with bootstrap CI,
        - the conditional residual norm-entropy H(tool | context-prediction-bucket) as the floor,
        - and an explicit "irreducible fraction" = 1 - (oos_acc - chance)/(1 - chance) style skill,
          plus the residual entropy in bits, with CIs.
 (Q3) HONEST CRUX: is the reframe DEFENSIBLE (coarse-partial w/ a real gate signal beyond web_disabled
      OR honestly labelled web_disabled-carried; fine context-conditioned w/ a real, OOS, leak-free
      lift AND a quantified non-trivial residual floor) -- OR does it COLLAPSE to "it's all web_disabled
      + a weak context signal"? Decision rule stated up front and applied to the numbers.

HONESTY: single harness (Claude Code), observational. We test OBSERVABLE signatures with OOS CIs.
Collapse is a valid finding. We do NOT edit claims/map/cemetery.

Reuses parse_session/classify_error/intent_class/head_cmd/block_text/routing_tool/gate_type/
modality_and_recovery/text_features VERBATIM from EXP-0022 (==EXP-0019/0009/0007).
"""
import json, glob, os, re, random, math
from collections import defaultdict, Counter

ROOT = os.path.expanduser("~/.claude/projects")
random.seed(20260531)
K_WINDOW = 6
B = 2000  # bootstrap resamples

# ============== COPIED VERBATIM FROM EXP-0022 ==============
def classify_error(tool_name, cmd, text):
    t=(text or "").lower()
    if re.search(r"internet mode is not enabled|enable_web_tools|pretooluse:web(search|fetch) hook error", t): return "policy.web_disabled"
    if re.search(r"input filtering is enabled|external webpage access is not permitted", t): return "policy.input_filter"
    if re.search(r"permission to use .* has been denied|permission denied for tool|requires approval", t): return "policy.perm_denied"
    if re.search(r"cancelled:|<tool_use_error>cancelled|operation was cancelled|user (rejected|cancel)", t): return "cancelled"
    if re.search(r"exceeds maximum allowed size|file content \(.*kb\) exceeds|too large.*offset", t): return "read.too_large"
    if re.search(r"file does not exist|does not exist\. note: your current working directory", t): return "fs.notfound"
    if re.search(r"cannot resolve|unknown host|name or service not known|could not resolve|temporary failure in name resolution", t): return "net.dns"
    if re.search(r"connection refused|connection timed out|connection reset|no route to host|network is unreachable|http 000|curl: \(\d", t): return "net.conn"
    if re.search(r"http (4\d\d|5\d\d)|forbidden|unauthorized", t): return "net.http"
    if re.search(r"permission denied \(publickey|host key verification failed|could not read from remote", t): return "ssh.auth"
    if re.search(r"no such file or directory|file not found|local file not found|cannot stat|not a directory", t): return "fs.notfound"
    if re.search(r"permission denied", t): return "fs.perm"
    if re.search(r"command not found|: not found|unknown command", t): return "cmd.notfound"
    if re.search(r"timed out|timeout|deadline exceeded|killed", t): return "proc.timeout"
    if re.search(r"syntaxerror|parse error|unexpected token|compilation failed|cannot find module|importerror|modulenotfounderror|traceback \(most recent", t): return "code.build"
    if re.search(r"test.*fail|assertion|assert |\d+ failed|fail\b", t): return "code.test"
    if tool_name in ("Edit","Write","MultiEdit","str_replace_editor"):
        if re.search(r"string to replace|not found in file|no match|does not match|found \d+ matches", t): return "edit.mismatch"
        return "edit.other"
    if re.search(r"^exit code \d+\s*$", t.strip()) or t.strip() in ("","exit code 1"): return "proc.exit_nodetail"
    return "other"

def head_cmd(cmd):
    if not cmd: return ""
    parts=cmd.strip().split()
    for p in parts:
        if "=" in p and not p.startswith("/"): continue
        if p in ("cd","sudo","time","env"): continue
        return os.path.basename(p)
    return parts[0] if parts else ""

def block_text(b):
    cont=b.get("content","")
    if isinstance(cont,list):
        out=[]
        for x in cont:
            if isinstance(x,dict): out.append(x.get("text", json.dumps(x)))
            else: out.append(str(x))
        return "\n".join(out)
    return str(cont)

BASH_READ_HEADS = {"cat","ls","head","tail","grep","find","rg","wc","stat","file","less","more","awk","sed","cut","sort","uniq","diff","tree","du"}
BASH_WRITE_HEADS = {"tee","cp","mv","mkdir","touch","chmod","rm","ln"}
def intent_class(tool_name, cmd):
    n=tool_name or ""
    if n in ("WebFetch","WebSearch") or "external_web_search" in n or "knowledge" in n:
        return "WEB_INFO"
    if n in ("Read","Glob","Grep"): return "FILE_READ"
    if n in ("Edit","Write","MultiEdit","str_replace_editor"): return "FILE_WRITE"
    if n in ("ToolSearch",): return "SEARCH_DISCOVER"
    if n in ("Agent","Workflow","Skill","Task"): return "DELEGATE"
    if n=="Bash":
        h=head_cmd(cmd)
        if h in BASH_READ_HEADS: return "FILE_READ"
        if h in BASH_WRITE_HEADS: return "FILE_WRITE"
        if cmd and re.search(r">\s*\S", cmd) and not re.search(r">/dev/null|2>&1", cmd): return "FILE_WRITE"
        if cmd and re.search(r"\bcurl\b|\bwget\b|\bfetch\b", cmd): return "WEB_INFO"
        return "EXEC"
    return "EXEC"

def parse_session(path):
    uses={}; calls=[]
    with open(path) as f:
        for line in f:
            try: d=json.loads(line)
            except: continue
            m=d.get("message")
            if not isinstance(m,dict): continue
            c=m.get("content")
            if not isinstance(c,list): continue
            for b in c:
                if not isinstance(b,dict): continue
                tp=b.get("type")
                if tp=="tool_use":
                    name=b.get("name",""); inp=b.get("input",{}) or {}
                    cmd=inp.get("command","") if isinstance(inp,dict) else ""
                    fp=inp.get("file_path","") if isinstance(inp,dict) else ""
                    intent=name+":"+(head_cmd(cmd) if name=="Bash" else fp)
                    uses[b.get("id","")]={"name":name,"cmd":cmd,"intent":intent}
                elif tp=="tool_result":
                    uid=b.get("tool_use_id","")
                    u=uses.get(uid,{"name":"?","cmd":"","intent":"?:"})
                    calls.append({"name":u["name"],"cmd":u["cmd"],"intent":u["intent"],
                                  "iclass":intent_class(u["name"],u["cmd"]),
                                  "is_error":bool(b.get("is_error")),"text":block_text(b)})
    return calls

def routing_tool(call):
    n = call["name"] or "?"
    if n == "Bash":
        h = head_cmd(call["cmd"]) or "(bash)"
        return "Bash:" + h
    return n

REDIRECTABLE = {"policy.web_disabled","policy.input_filter"}
GRANT_REQ    = {"policy.perm_denied","fs.perm","ssh.auth"}
def gate_type(cls):
    if cls in REDIRECTABLE: return "REDIRECTABLE"
    if cls in GRANT_REQ:    return "GRANT_REQUIRED"
    return "TRANSIENT"

def modality_and_recovery(calls, i):
    fc=calls[i]; fintent=fc["intent"]; ficlass=fc["iclass"]
    window=calls[i+1:i+1+K_WINDOW]
    same_tool=False; cross_tool=False
    for w in window:
        if w["is_error"]: continue
        if w["intent"]==fintent: same_tool=True
        elif w["iclass"]==ficlass: cross_tool=True
    rec = same_tool or cross_tool
    if same_tool: mod="SAME_TOOL_RETRY"
    elif cross_tool: mod="CROSS_TOOL_REDIRECT"
    else: mod=None
    return rec, mod

def text_features(text):
    t=(text or "").lower()
    feats=set()
    for kw in ["web","fetch","search","permission","denied","approval","cancel","timeout",
               "not found","no such","connection","http","host","syntax","module","test",
               "assert","exit code","curl","ssh","git"]:
        if kw in t: feats.add("kw:"+kw.replace(" ","_"))
    return feats
# ============== END COPIED ==============

def entropy_bits(counter):
    tot=sum(counter.values())
    if tot==0: return 0.0,0.0,0.0
    H=0.0
    for c in counter.values():
        p=c/tot
        if p>0: H-=p*math.log2(p)
    k=len(counter); Hmax=math.log2(k) if k>1 else 0.0
    top1=max(counter.values())/tot
    return H,(H/Hmax if Hmax>0 else 0.0),top1

def entropyH(vals): return entropy_bits(Counter(vals))[0]

def cond_entropy(pairs):  # H(Y|X), pairs=(x,y)
    byx=defaultdict(Counter); 
    for x,y in pairs: byx[x][y]+=1
    tot=sum(sum(c.values()) for c in byx.values()); H=0.0
    for x,ctr in byx.items():
        nx=sum(ctr.values()); Hx,_,_=entropy_bits(ctr); H += (nx/tot)*Hx
    return H

def theilU(pairs):  # U(Y|X), pairs=(x,y)
    HY=entropyH([y for _,y in pairs]); HYgX=cond_entropy(pairs)
    return (HY-HYgX)/HY if HY>0 else 0.0

# ---------------- LOAD ----------------
def load_rows():
    files=sorted(glob.glob(os.path.join(ROOT,"**","*.jsonl"),recursive=True))
    rows=[]; n_sessions=0; n_calls=0
    for path in files:
        calls=parse_session(path)
        if len(calls)<2: continue
        n_sessions+=1; n_calls+=len(calls)
        sid=os.path.basename(path)
        for i,c in enumerate(calls):
            if not c["is_error"]: continue
            cls=classify_error(c["name"],c["cmd"],c["text"]); gt=gate_type(cls)
            nxt=calls[i+1] if i+1<len(calls) else None
            nt=routing_tool(nxt) if nxt is not None else "(END)"
            rec,mod=modality_and_recovery(calls,i)
            prior=routing_tool(calls[i-1]) if i>0 else "(START)"
            rows.append({"sid":sid,"cls":cls,"gate":gt,"next":nt,"rec":1 if rec else 0,
                         "mod":mod,"prior":prior,"feats":text_features(c["text"]),
                         "failed_tool":routing_tool(c)})
    return rows,n_sessions,n_calls

# ---------------- CONTEXT MODEL (NB) with selectable features & OOS scheme ----------------
def featset(r, keys):
    fs=set()
    if "kw" in keys: fs |= set(r["feats"])
    if "prior" in keys: fs.add("prior:"+r["prior"])
    if "cls" in keys: fs.add("cls:"+r["cls"])
    if "ft" in keys: fs.add("ft:"+r["failed_tool"])
    return fs

def predict_oos(train, test_row, keys):
    """NB trained on `train` rows, predict next-tool for test_row. Returns predicted tool."""
    labels=[r["next"] for r in train]
    if not labels: return None
    toolset=set(labels); tool_count=Counter(labels)
    feat_tool=defaultdict(Counter)
    for r in train:
        for f in featset(r,keys): feat_tool[f][r["next"]]+=1
    rf=featset(test_row,keys); n=len(train)
    best=None; bs=-1e18
    for tool in toolset:
        score=math.log(tool_count[tool])
        for f in rf:
            score += math.log((feat_tool[f][tool]+1)/(tool_count[tool]+len(toolset)))
        if score>bs: bs=score; best=tool
    return best

def loso_eval(grp, keys):
    """Leave-one-SESSION-out: for each row, train on rows NOT in its session. Returns (preds, labels)."""
    by_sid=defaultdict(list)
    for r in grp: by_sid[r["sid"]].append(r)
    preds=[]; labels=[]
    for r in grp:
        train=[x for x in grp if x["sid"]!=r["sid"]]
        p=predict_oos(train, r, keys)
        preds.append(p); labels.append(r["next"])
    return preds, labels

def loo_eval(grp, keys):
    preds=[]; labels=[]
    for idx,r in enumerate(grp):
        train=grp[:idx]+grp[idx+1:]
        p=predict_oos(train, r, keys)
        preds.append(p); labels.append(r["next"])
    return preds, labels

def acc(preds, labels):
    n=len(labels); 
    return sum(1 for p,l in zip(preds,labels) if p==l)/n if n else 0.0

def boot_ci_acc(preds, labels, B=B):
    n=len(labels); idx=list(range(n)); stats=[]
    pl=list(zip(preds,labels))
    for _ in range(B):
        s=[pl[random.randrange(n)] for _ in range(n)]
        stats.append(sum(1 for p,l in s if p==l)/n)
    stats.sort(); return stats[int(0.025*B)], stats[int(0.975*B)]

def main():
    rows,nses,ncalls=load_rows()
    N=len(rows)
    print(f"corpus: {nses} sessions, {ncalls} calls, {N} ground-truth failures")
    gate_counts=Counter(r["gate"] for r in rows)
    print("gate-type distribution:", dict(gate_counts))
    cls_counts=Counter(r["cls"] for r in rows)
    print("error-class distribution:", dict(cls_counts.most_common()))

    recmod=[r for r in rows if r["mod"] is not None]

    out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","experiment_result")
    os.makedirs(out,exist_ok=True)
    csv_rows=[]  # (section,key,value)

    # ============== Q1: COARSE ROBUSTNESS (web_disabled-carried? bootstrap CIs) ==============
    print("\n================ Q1: COARSE LAYER ROBUSTNESS (bootstrap CIs on Theil U) ================")
    mod_pairs=[(r["gate"],r["mod"]) for r in recmod]
    U_full=theilU(mod_pairs)
    # web_disabled-dropped (LOCO)
    nowd=[r for r in recmod if r["cls"]!="policy.web_disabled"]
    U_nowd=theilU([(r["gate"],r["mod"]) for r in nowd])
    # also drop ALL REDIRECTABLE (web_disabled + input_filter)
    noredir=[r for r in recmod if r["gate"]!="REDIRECTABLE"]
    U_noredir=theilU([(r["gate"],r["mod"]) for r in noredir])
    # bootstrap CIs
    def bootU(sample_pool):
        m=len(sample_pool); stats=[]
        for _ in range(B):
            s=[sample_pool[random.randrange(m)] for _ in range(m)]
            stats.append(theilU([(r["gate"],r["mod"]) for r in s]))
        stats.sort(); return stats[int(0.025*B)],stats[int(0.5*B)],stats[int(0.975*B)]
    flo,fmed,fhi=bootU(recmod)
    nlo,nmed,nhi=bootU(nowd) if nowd else (0,0,0)
    rlo,rmed,rhi=bootU(noredir) if noredir else (0,0,0)
    print(f"  Theil U(modality|gate) FULL          = {U_full:.3f}  boot95% [{flo:.3f},{fhi:.3f}]")
    print(f"  Theil U  drop policy.web_disabled    = {U_nowd:.3f}  boot95% [{nlo:.3f},{nhi:.3f}]  (n={len(nowd)})")
    print(f"  Theil U  drop ALL REDIRECTABLE       = {U_noredir:.3f}  boot95% [{rlo:.3f},{rhi:.3f}]  (n={len(noredir)})")
    carried = (U_nowd < 0.5*U_full)
    print(f"  => web_disabled-CARRIED determinism? {'YES (drops >50%)' if carried else 'NO'}; "
          f"residual U after dropping web_disabled CI upper={nhi:.3f}")
    csv_rows += [("Q1coarse","theilU_full",f"{U_full:.4f}"),("Q1coarse","theilU_full_lo",f"{flo:.4f}"),
                 ("Q1coarse","theilU_full_hi",f"{fhi:.4f}"),("Q1coarse","theilU_drop_webdisabled",f"{U_nowd:.4f}"),
                 ("Q1coarse","theilU_drop_wd_lo",f"{nlo:.4f}"),("Q1coarse","theilU_drop_wd_hi",f"{nhi:.4f}"),
                 ("Q1coarse","theilU_drop_redir",f"{U_noredir:.4f}"),("Q1coarse","theilU_drop_redir_hi",f"{rhi:.4f}")]

    # per-gate modality determinism with bootstrap CI on top1 share, vs chance (majority of 2-cat = >=0.5)
    print("\n  per-gate modality determinism (is GRANT_REQUIRED/TRANSIENT > chance?):")
    for g in ["REDIRECTABLE","GRANT_REQUIRED","TRANSIENT"]:
        gg=[r for r in recmod if r["gate"]==g]; n=len(gg)
        if n==0: print(f"    {g}: n=0"); continue
        ctr=Counter(r["mod"] for r in gg); _,Hn,top1=entropy_bits(ctr)
        # bootstrap top1
        stats=[]
        for _ in range(B):
            s=[gg[random.randrange(n)] for _ in range(n)]
            c=Counter(r["mod"] for r in s); stats.append(max(c.values())/n)
        stats.sort(); tlo,thi=stats[int(0.025*B)],stats[int(0.975*B)]
        print(f"    {g:15s} n={n:4d} modal_share={top1:.3f} boot95%[{tlo:.3f},{thi:.3f}] normH={Hn:.3f}  {dict(ctr)}")
        csv_rows += [(f"Q1gate_{g}","n",str(n)),(f"Q1gate_{g}","modal_share",f"{top1:.4f}"),
                     (f"Q1gate_{g}","modal_share_lo",f"{tlo:.4f}"),(f"Q1gate_{g}","modal_share_hi",f"{thi:.4f}"),
                     (f"Q1gate_{g}","modality_normH",f"{Hn:.4f}")]

    # ============== Q2: FINE IRREDUCIBLE RESIDUAL (best OOS context model, LOSO, leak-free) ==============
    print("\n================ Q2: FINE LAYER IRREDUCIBLE RESIDUAL (LOSO out-of-sample) ================")
    # Use LEAVE-ONE-SESSION-OUT to kill within-session leakage. Best LEAK-FREE feature set = kw+prior+cls
    # (DROP failed_tool to avoid same-tool-retry leak, per EXP-0022's decisive ablation).
    LEAKFREE_KEYS={"kw","prior","cls"}
    print(f"  context features (LEAK-FREE): {sorted(LEAKFREE_KEYS)}  | OOS scheme = leave-one-session-out")
    fine_floor={}
    for g in ["REDIRECTABLE","GRANT_REQUIRED","TRANSIENT"]:
        grp=[r for r in rows if r["gate"]==g]; n=len(grp)
        if n<10: print(f"  {g}: n={n} skipped"); continue
        labels_all=[r["next"] for r in grp]; toolset=set(labels_all)
        _,Hn_uncond,top1=entropy_bits(Counter(labels_all))
        # within-gate modal baseline (= chance), LOSO so comparable
        by_sid=defaultdict(list)
        for r in grp: by_sid[r["sid"]].append(r)
        base_preds=[]; 
        for r in grp:
            train=[x for x in grp if x["sid"]!=r["sid"]]
            c=Counter(x["next"] for x in train)
            base_preds.append(c.most_common(1)[0][0] if c else None)
        base_acc=acc(base_preds, labels_all)
        # context model LOSO (leak-free)
        ctx_preds, ctx_labels = loso_eval(grp, LEAKFREE_KEYS)
        ctx_acc=acc(ctx_preds, ctx_labels)
        clo,chi=boot_ci_acc(ctx_preds, ctx_labels)
        blo,bhi=boot_ci_acc(base_preds, labels_all)
        lift=ctx_acc-base_acc
        # skill (how much of the gap to perfect did context close beyond chance)
        skill = (ctx_acc - base_acc)/(1.0 - base_acc) if base_acc<1 else 0.0
        # RESIDUAL ENTROPY FLOOR: H(tool | model-prediction-bucket). Group rows by predicted tool,
        # measure residual norm-entropy of TRUE tool within each predicted bucket, failure-weight.
        buck=defaultdict(Counter)
        for p,l in zip(ctx_preds, ctx_labels): buck[p][l]+=1
        tot=0; wH=0.0; wHbits=0.0
        for p,ctr in buck.items():
            nn=sum(ctr.values()); Hbits,Hn2,_=entropy_bits(ctr); wH+=Hn2*nn; wHbits+=Hbits*nn; tot+=nn
        resid_normH = wH/tot if tot else 0.0
        resid_bits = wHbits/tot if tot else 0.0
        # bootstrap CI on residual_normH
        pl=list(zip(ctx_preds,ctx_labels)); stats=[]
        for _ in range(B):
            s=[pl[random.randrange(len(pl))] for _ in range(len(pl))]
            bk=defaultdict(Counter)
            for p,l in s: bk[p][l]+=1
            t2=0; w2=0.0
            for p,ctr in bk.items():
                nn=sum(ctr.values()); _,Hn2,_=entropy_bits(ctr); w2+=Hn2*nn; t2+=nn
            stats.append(w2/t2 if t2 else 0.0)
        stats.sort(); rlo2,rhi2=stats[int(0.025*B)],stats[int(0.975*B)]
        print(f"  {g}: n={n} tools={len(toolset)} uncond_normH={Hn_uncond:.3f} top1={top1:.3f}")
        print(f"       modal baseline LOSO-acc = {base_acc:.3f} boot95%[{blo:.3f},{bhi:.3f}]")
        print(f"       context  model LOSO-acc = {ctx_acc:.3f} boot95%[{clo:.3f},{chi:.3f}]  lift={lift:+.3f} skill={skill:+.3f}")
        print(f"       IRREDUCIBLE residual norm-entropy floor (H tool|pred) = {resid_normH:.3f} boot95%[{rlo2:.3f},{rhi2:.3f}]  ({resid_bits:.2f} bits)")
        fine_floor[g]=(n,base_acc,ctx_acc,lift,(clo,chi),resid_normH,(rlo2,rhi2))
        csv_rows += [(f"Q2fine_{g}","n",str(n)),(f"Q2fine_{g}","modal_base_loso_acc",f"{base_acc:.4f}"),
                     (f"Q2fine_{g}","ctx_loso_acc",f"{ctx_acc:.4f}"),(f"Q2fine_{g}","ctx_acc_lo",f"{clo:.4f}"),
                     (f"Q2fine_{g}","ctx_acc_hi",f"{chi:.4f}"),(f"Q2fine_{g}","lift",f"{lift:.4f}"),
                     (f"Q2fine_{g}","residual_normH_floor",f"{resid_normH:.4f}"),
                     (f"Q2fine_{g}","residual_floor_lo",f"{rlo2:.4f}"),(f"Q2fine_{g}","residual_floor_hi",f"{rhi2:.4f}"),
                     (f"Q2fine_{g}","residual_bits",f"{resid_bits:.4f}")]

    # ============== Q3: HONEST CRUX (decision rule) ==============
    print("\n================ Q3: HONEST CRUX (defensible vs collapses) ================")
    print("  DECISION RULE (stated before reading numbers):")
    print("   COARSE-PARTIAL is DEFENSIBLE if: FULL U CI excludes 0 AND we HONESTLY label it web_disabled-carried")
    print("     (residual-after-web_disabled CI upper < ~0.15 => 'partial gate-table, carried by one cell').")
    print("   FINE-CONTEXT-CONDITIONED is DEFENSIBLE if: in >=1 large gate the LOSO context lift CI excludes 0")
    print("     (leak-free) AND the residual-entropy floor is non-trivial (CI lower > ~0.3 => real remainder).")
    print("   COLLAPSE if: coarse U after dropping web_disabled is indistinguishable from 0 (CI incl 0)")
    print("     AND NO gate shows a leak-free LOSO lift whose CI excludes 0.")
    # evaluate
    coarse_defensible = (flo>0) and (nhi < 0.15)
    coarse_collapse_part = (nlo <= 0.02) or (nhi < 0.05)  # residual U ~ 0
    # fine: any gate with leak-free LOSO lift CI excluding 0? approximate via lift vs base CI overlap:
    fine_lift_sig=False; fine_floor_real=False
    for g,(n,ba,ca,lift,(clo2,chi2),rH,(rlo3,rhi3)) in fine_floor.items():
        # lift CI: ctx acc CI lower must exceed base acc point (conservative)
        if clo2 > ba: fine_lift_sig=True
        if rlo3 > 0.30: fine_floor_real=True
    print(f"\n  COARSE: FULL U CI=[{flo:.3f},{fhi:.3f}] (excludes 0: {flo>0}); "
          f"residual-after-web_disabled U CI=[{nlo:.3f},{nhi:.3f}] (~0: {coarse_collapse_part})")
    print(f"    -> coarse layer = {'PARTIAL gate-table, HONESTLY web_disabled-carried (DEFENSIBLE if labelled so)' if (flo>0 and coarse_collapse_part) else ('coarse signal beyond web_disabled SURVIVES' if nhi>=0.15 else 'ambiguous')}")
    print(f"  FINE: leak-free LOSO lift CI-excludes-0 in some gate: {fine_lift_sig}; residual floor non-trivial (CI low>0.30): {fine_floor_real}")
    print(f"    -> fine layer = {'CONTEXT-CONDITIONED w/ real residual floor (DEFENSIBLE)' if (fine_lift_sig and fine_floor_real) else 'weak/collapses'}")
    if (fine_lift_sig and fine_floor_real) and (flo>0):
        verdict="DEFENSIBLE-REFRAME (coarse-partial[honestly web_disabled-carried] + fine-context-conditioned w/ quantified residual floor)"
    elif fine_lift_sig and (flo>0):
        verdict="PARTIALLY-DEFENSIBLE (signals real but residual-floor framing weak)"
    else:
        verdict="COLLAPSES (reduces to web_disabled + a weak context signal)"
    print(f"\n  ===> REFRAME VERDICT: {verdict}")
    csv_rows += [("Q3","coarse_full_U_lo",f"{flo:.4f}"),("Q3","coarse_full_U_hi",f"{fhi:.4f}"),
                 ("Q3","coarse_resid_U_after_wd_lo",f"{nlo:.4f}"),("Q3","coarse_resid_U_after_wd_hi",f"{nhi:.4f}"),
                 ("Q3","fine_lift_significant",str(fine_lift_sig)),("Q3","fine_floor_nontrivial",str(fine_floor_real)),
                 ("Q3","reframe_verdict",verdict)]

    # write CSVs
    with open(os.path.join(out,"reframe_metrics.csv"),"w") as f:
        f.write("section,key,value\n")
        for s,k,v in csv_rows: f.write(f"{s},{k},{v}\n")
    print(f"\nCSV: {os.path.join(out,'reframe_metrics.csv')}")

if __name__=="__main__":
    main()
