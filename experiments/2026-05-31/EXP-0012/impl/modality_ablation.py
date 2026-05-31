#!/usr/bin/env python3
"""
EXP-0012 — CLAIM-0009 ABLATION + INFORMED BASELINES (addresses VERDICT-0020). CPU/stdlib-only.

VERDICT-0020 (real 6/6 YELLOW) fatal objections this experiment ADDRESSES, honestly, CPU-only:
  (1) DEFINITIONAL INFLATION: V=0.717 headline carried by web_disabled (n~109, redirect-share=1.0
      BY CONSTRUCTION -- a hard tool-block CANNOT be same-tool-retried). Required: re-report
      V + LOO-Brier with web_disabled REMOVED, + leave-one-CLASS-out CV. If V collapses, the
      "error-class predicts modality" claim is really "web_disabled->redirect", a config fact.
  (2) PREDICTOR MISATTRIBUTION: error-class & GATE-TYPE are colinear here; the signal may be the
      harness ROUTING RULE (gate-type = REDIRECTABLE/TERMINAL flag), NOT error-class proper.
      Required: lift over (a) static deterministic error-class->Mode(modality) mapping, and
      (b) a GATE-TYPE-ONLY predictor. Report lift over BOTH, not just over the NULL p0=0.504.
      If error-class adds ~nothing over gate-type-only -> CONFIRMS misattribution -> WEAKENS claim.

parse_session/classify_error/intent_class/head_cmd/block_text/recovery_modality COPIED VERBATIM
from EXP-0009 (which copied them from EXP-0007/0008). No cross-dir import. Same corpus, same K=6,
same BROAD recovery def, same modality assignment -> the headline V here MUST reproduce EXP-0009's
0.717 as a sanity gate before we ablate.

GATE-TYPE definition (the harness-routing variable we test against error-class):
  A failure's error-class maps to a GATE-TYPE flag via the routing structure the harness exposes:
    REDIRECTABLE  : a hard tool-block that has a sanctioned ALTERNATIVE tool the agent is routed to
                    (the blocked tool cannot itself succeed) -> {policy.web_disabled, policy.input_filter}
    TERMINAL_GRANT: a permission gate that must be GRANTED (no alternative tool; same tool re-approved)
                    -> {policy.perm_denied}
    TRANSIENT     : everything else -- fixable in place / re-runnable, no routing rule
  This is the MINIMAL routing variable (3 levels, or 2 if we binarize REDIRECTABLE vs not). It is
  what a harness designer knows WITHOUT a fine-grained error taxonomy. If error-class beats this,
  error-class carries info beyond routing; if not, the signal IS routing (gate-type), not class.

HONESTY CONTRACT: error-class and gate-type may be PERFECTLY colinear in this single-harness corpus
(every error-class maps to exactly one gate-type, and the within-gate-type error-classes carry no
extra modality signal). If so we CANNOT separate them observationally -- only an interventional /
cross-harness test could. We report that plainly: "observationally inseparable; claim must be stated
as gate-type+routing characterization, not error-class prediction."
"""
import json, glob, os, re, random, math
from collections import defaultdict

ROOT = os.path.expanduser("~/.claude/projects")
random.seed(1234)
K_WINDOW = 6

# ============== COPIED VERBATIM FROM EXP-0009 (==EXP-0007/0008) ==============
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

def recovery_modality(calls, idx, K):
    fail=calls[idx]; intent=fail["intent"]; ic=fail["iclass"]
    same_tool=None; redirect_tool=None
    hi=min(idx+1+K, len(calls))
    for j in range(idx+1, hi):
        cj=calls[j]
        if cj["is_error"]: continue
        if cj["intent"]==intent:
            if same_tool is None: same_tool=cj["name"]
        elif cj["iclass"]==ic:
            if redirect_tool is None: redirect_tool=cj["name"]
    if same_tool is not None:
        return 1, "SAME_TOOL_RETRY", same_tool
    if redirect_tool is not None:
        return 1, "CROSS_TOOL_REDIRECT", redirect_tool
    return 0, None, None
# ============== END COPIED ==============

# ---- GATE-TYPE: the harness-routing variable (3-level + binary) ----
REDIRECTABLE_CLASSES = {"policy.web_disabled","policy.input_filter"}
TERMINAL_GRANT_CLASSES = {"policy.perm_denied"}
def gate_type(ec):
    if ec in REDIRECTABLE_CLASSES: return "REDIRECTABLE"
    if ec in TERMINAL_GRANT_CLASSES: return "TERMINAL_GRANT"
    return "TRANSIENT"
def gate_binary(ec):
    # the absolute minimal routing flag: is the gate a hard-block-with-alternative (redirect-only) or not?
    return "REDIRECTABLE" if ec in REDIRECTABLE_CLASSES else "OTHER"

# ---------- stats helpers (copied from EXP-0009) ----------
def chi2_table(table):
    rows=len(table); cols=2
    rt=[sum(r) for r in table]; ct=[sum(table[i][j] for i in range(rows)) for j in range(cols)]
    tot=sum(rt)
    if tot==0: return 0.0
    chi=0.0
    for i in range(rows):
        for j in range(cols):
            e=rt[i]*ct[j]/tot
            if e>0: chi+=(table[i][j]-e)**2/e
    return chi

def cramers_and_perm(keys, labels, B=5000):
    classes=sorted(set(keys)); N=len(labels)
    by=defaultdict(lambda:[0,0])
    for k,l in zip(keys,labels): by[k][1]+=1; by[k][0]+=l
    obs=[[by[k][0],by[k][1]-by[k][0]] for k in classes]
    chi=chi2_table(obs); V=math.sqrt(chi/N) if N else 0.0
    lab=list(labels); ge=0
    for _ in range(B):
        random.shuffle(lab)
        tab=defaultdict(lambda:[0,0])
        for k,l in zip(keys,lab): tab[k][1]+=1; tab[k][0]+=l
        if chi2_table([[tab[k][0],tab[k][1]-tab[k][0]] for k in classes])>=chi-1e-9: ge+=1
    return chi, len(classes)-1, V, (ge+1)/(B+1), by

def loo_brier(keys, labels):
    """Leave-one-SAMPLE-out Brier of class-conditional redirect-prob vs constant null p0."""
    by=defaultdict(lambda:[0,0])
    for k,l in zip(keys,labels): by[k][1]+=1; by[k][0]+=l
    N=len(labels); R=sum(labels); p0=R/N if N else 0.0
    bn=sum((p0-l)**2 for l in labels)/N
    bl=0.0
    for k,l in zip(keys,labels):
        rec,tot=by[k]
        p=(rec-l)/(tot-1) if tot>1 else p0
        bl+=(p-l)**2
    bl/=N
    return p0,bn,bl,bn-bl

def brier_of_predictor(pred_probs, labels):
    return sum((p-l)**2 for p,l in zip(pred_probs,labels))/len(labels) if labels else 0.0

def wilson(k,n,z=1.96):
    if n==0: return (0.0,0.0,0.0)
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return (p, max(0,c-h), min(1,c+h))

def build_records(K):
    files=sorted(glob.glob(os.path.join(ROOT,"**","*.jsonl"),recursive=True))
    recs=[]; n_sessions=0; n_calls=0; n_fail=0
    for path in files:
        try: calls=parse_session(path)
        except Exception: continue
        if len(calls)<2: continue
        n_sessions+=1; n_calls+=len(calls)
        sid=os.path.basename(path)
        for i,c in enumerate(calls):
            if not c["is_error"]: continue
            n_fail+=1
            ec=classify_error(c["name"],c["cmd"],c["text"])
            rec,mod,wtool=recovery_modality(calls,i,K)
            recs.append({"ec":ec,"sid":sid,"failtool":c["name"],"iclass":c["iclass"],
                         "recovered":rec,"modality":mod,"wtool":wtool})
    return recs, n_sessions, n_calls, n_fail

def loco_cv_brier(keys, labels):
    """Leave-one-CLASS-out CV: for each held-out class, predict its samples' redirect-prob using
    the GLOBAL redirect rate of the REMAINING classes' samples (the model literally never saw this
    class). This is the harsh test VERDICT-0020 asked for: can the predictor generalize to a class
    it was not trained on? If the per-class redirect rates are idiosyncratic (each class its own
    rate), LOCO Brier will be WORSE than the null -> the 'signal' does not transfer across classes,
    it is just memorized per-class rates. Returns (null_brier, loco_brier, improvement)."""
    N=len(labels); R=sum(labels); p0=R/N if N else 0.0
    by=defaultdict(lambda:[0,0])
    for k,l in zip(keys,labels): by[k][1]+=1; by[k][0]+=l
    bn=sum((p0-l)**2 for l in labels)/N
    bl=0.0
    for k,l in zip(keys,labels):
        # train rate = redirect rate over all samples NOT in class k
        rec_k,tot_k=by[k]
        rec_rest=R-rec_k; tot_rest=N-tot_k
        p=rec_rest/tot_rest if tot_rest>0 else p0
        bl+=(p-l)**2
    bl/=N
    return p0,bn,bl,bn-bl

def main():
    recs, ns, nc, nf = build_records(K_WINDOW)
    print(f"sessions={ns} total_tool_calls={nc} failures={nf}  K_WINDOW={K_WINDOW}")
    rec_only=[r for r in recs if r["recovered"]==1]
    Nr=len(rec_only)
    redir=[1 if r["modality"]=="CROSS_TOOL_REDIRECT" else 0 for r in rec_only]
    n_redirect=sum(redir); n_same=Nr-n_redirect
    p0=n_redirect/Nr
    print(f"\nRECOVERED N={Nr}  SAME={n_same}  REDIRECT={n_redirect}  NULL p0={p0:.4f}")

    ecs=[r["ec"] for r in rec_only]
    gts=[gate_type(r["ec"]) for r in rec_only]
    gtb=[gate_binary(r["ec"]) for r in rec_only]

    # ========== SANITY GATE: reproduce EXP-0009 headline V ==========
    chi,df,V,pp,by=cramers_and_perm(ecs, redir)
    _,bn,bl,bimp=loo_brier(ecs, redir)
    print("\n=== SANITY: full-taxonomy headline (must reproduce EXP-0009 V=0.717) ===")
    print(f"  error-class -> modality: V={V:.4f} perm_p={pp:.4f}  LOO-Brier null={bn:.4f} cc={bl:.4f} improve={bimp:+.4f} ({100*bimp/bn:.1f}%)")

    # ========== REQUIRED EVIDENCE 1a: web_disabled-ABLATED headline ==========
    idx_keep=[i for i,r in enumerate(rec_only) if r["ec"]!="policy.web_disabled"]
    ecs_ab=[ecs[i] for i in idx_keep]; redir_ab=[redir[i] for i in idx_keep]
    n_wd=Nr-len(idx_keep)
    chiA,dfA,VA,ppA,_=cramers_and_perm(ecs_ab, redir_ab)
    p0A,bnA,blA,bimpA=loo_brier(ecs_ab, redir_ab)
    print("\n=== REQUIRED 1a: web_disabled REMOVED (the definitionally-determined redirect=1.0 cell) ===")
    print(f"  removed {n_wd} web_disabled recovered failures; remaining N={len(idx_keep)}")
    print(f"  ABLATED error-class -> modality: V={VA:.4f} perm_p={ppA:.4f}")
    print(f"  ABLATED LOO-Brier: null={bnA:.4f} cc={blA:.4f} improve={bimpA:+.4f} ({100*bimpA/bnA if bnA else 0:.1f}%)")
    print(f"  ==> headline V {V:.3f} -> {VA:.3f} after ablation ({'COLLAPSES' if VA<0.3 else 'SURVIVES (weakened)' if VA<V*0.7 else 'SURVIVES'})")

    # also ablate BOTH definitional poles (web_disabled AND perm_denied)
    idx_keep2=[i for i,r in enumerate(rec_only) if r["ec"] not in ("policy.web_disabled","policy.perm_denied")]
    ecs_ab2=[ecs[i] for i in idx_keep2]; redir_ab2=[redir[i] for i in idx_keep2]
    chiA2,dfA2,VA2,ppA2,_=cramers_and_perm(ecs_ab2, redir_ab2)
    p0A2,bnA2,blA2,bimpA2=loo_brier(ecs_ab2, redir_ab2)
    print(f"\n  [also remove perm_denied -> only TRANSIENT classes remain, N={len(idx_keep2)}]")
    print(f"  TRANSIENT-only error-class -> modality: V={VA2:.4f} perm_p={ppA2:.4f} LOO-Brier improve={bimpA2:+.4f} ({100*bimpA2/bnA2 if bnA2 else 0:.1f}%)")

    # ========== REQUIRED EVIDENCE 1b: leave-one-CLASS-out CV ==========
    print("\n=== REQUIRED 1b: leave-one-CLASS-out CV (predict held-out class from REMAINING classes) ===")
    _,bnL,blL,bimpL=loco_cv_brier(ecs, redir)
    print(f"  FULL taxonomy LOCO: null={bnL:.4f} loco={blL:.4f} improve={bimpL:+.4f} ({100*bimpL/bnL:.1f}%)")
    _,bnLa,blLa,bimpLa=loco_cv_brier(ecs_ab, redir_ab)
    print(f"  ABLATED (no web_disabled) LOCO: null={bnLa:.4f} loco={blLa:.4f} improve={bimpLa:+.4f} ({100*bimpLa/bnLa if bnLa else 0:.1f}%)")
    print("  (LOCO improve <=0 => per-class rates do NOT transfer to unseen classes => 'signal' is memorized")
    print("   per-class rates, not a generalizable error-class->modality regularity.)")
    # per-class LOCO contribution
    print("  per-class held-out detail (class | n | actual_redir_rate | predicted_from_rest | brier_vs_null_delta):")
    N=len(redir); R=sum(redir); pg=R/N
    byc=defaultdict(lambda:[0,0])
    for e,l in zip(ecs,redir): byc[e][1]+=1; byc[e][0]+=l
    for e in sorted(byc,key=lambda x:-byc[x][1]):
        rec_e,tot_e=byc[e]
        if tot_e<5: continue
        actual=rec_e/tot_e
        pred=(R-rec_e)/(N-tot_e) if N-tot_e>0 else pg
        # brier improvement on this class's samples (null vs loco-pred)
        bnull=sum((pg-l)**2 for l in [1]*rec_e+[0]*(tot_e-rec_e))/tot_e
        bpred=sum((pred-l)**2 for l in [1]*rec_e+[0]*(tot_e-rec_e))/tot_e
        print(f"    {e:22s} n={tot_e:>3} actual={actual:.3f} pred_from_rest={pred:.3f} brier_delta={bnull-bpred:+.4f}")

    # ========== REQUIRED EVIDENCE 2: INFORMED BASELINES ==========
    print("\n=== REQUIRED 2: INFORMED BASELINES (lift over static-mapping AND gate-type-only) ===")
    # Baseline A: static deterministic error-class -> Mode(modality) mapping (in-sample MAP rule).
    #   For each class, predict its majority modality (Mode). Accuracy + Brier (0/1 pred).
    mode_map={}
    for e in sorted(byc):
        rec_e,tot_e=byc[e]
        mode_map[e]=1 if rec_e*2>=tot_e else 0   # 1=redirect if redirect is the mode
    pred_static=[mode_map[e] for e in ecs]
    acc_static=sum(1 for p,l in zip(pred_static,redir) if p==l)/Nr
    bri_static=brier_of_predictor([float(p) for p in pred_static], redir)
    # Baseline B: gate-type-only (3-level) -> class-conditional redirect-prob from gate-type
    def cc_probs(keys, labels):
        by=defaultdict(lambda:[0,0])
        for k,l in zip(keys,labels): by[k][1]+=1; by[k][0]+=l
        return [by[k][0]/by[k][1] for k in keys]
    pred_gate=cc_probs(gts, redir)
    bri_gate=brier_of_predictor(pred_gate, redir)
    # gate-type-only LOO-Brier (honest out-of-sample)
    _,bnG,blG,bimpG=loo_brier(gts, redir)
    chiG,dfG,VG,ppG,_=cramers_and_perm(gts, redir)
    # Baseline B2: gate-BINARY-only (just the REDIRECTABLE flag)
    pred_gateb=cc_probs(gtb, redir)
    bri_gateb=brier_of_predictor(pred_gateb, redir)
    _,bnGb,blGb,bimpGb=loo_brier(gtb, redir)
    chiGb,dfGb,VGb,ppGb,_=cramers_and_perm(gtb, redir)
    # Full error-class in-sample Brier (cc probs) for apples-to-apples accuracy
    pred_ec=cc_probs(ecs, redir)
    bri_ec=brier_of_predictor(pred_ec, redir)

    print(f"  NULL (constant p0={p0:.3f}) in-sample Brier            = {p0*(1-p0):.4f}  [variance floor]")
    print(f"  static error-class->Mode(modality) [0/1] : acc={acc_static:.3f}  Brier={bri_static:.4f}")
    print(f"  gate-type-ONLY (3-level) cc-prob          : in-sample Brier={bri_gate:.4f}  V={VG:.4f}  LOO-Brier improve={bimpG:+.4f} ({100*bimpG/bnG:.1f}%)")
    print(f"  gate-BINARY-ONLY (REDIRECTABLE flag)      : in-sample Brier={bri_gateb:.4f}  V={VGb:.4f}  LOO-Brier improve={bimpGb:+.4f} ({100*bimpGb/bnGb:.1f}%)")
    print(f"  full error-class cc-prob                  : in-sample Brier={bri_ec:.4f}  V={V:.4f}  LOO-Brier improve={bimp:+.4f} ({100*bimp/bn:.1f}%)")
    print(f"\n  LIFT of error-class OVER gate-type-only (LOO-Brier): {bimp-bimpG:+.4f}  ({(blG-bl):+.4f} abs Brier reduction)")
    print(f"  LIFT of error-class OVER gate-binary-only (LOO-Brier): {bimp-bimpGb:+.4f}  ({(blGb-bl):+.4f} abs Brier reduction)")
    print(f"  LIFT of error-class OVER static-mapping (Brier):       {bri_static-bri_ec:+.4f}")

    # ========== COLINEARITY DIAGNOSTIC: can the data even separate ec from gate-type? ==========
    print("\n=== COLINEARITY DIAGNOSTIC: is error-class -> gate-type a function (perfect colinearity)? ===")
    ec_to_gt=defaultdict(set)
    for e in ecs: ec_to_gt[e].add(gate_type(e))
    fn = all(len(v)==1 for v in ec_to_gt.values())
    print(f"  every error-class maps to exactly ONE gate-type? {fn}  (=> ec determines gate-type deterministically)")
    # Within-gate-type: does error-class add modality signal BEYOND gate-type?
    # Test: among samples sharing a gate-type, does the finer error-class still predict modality?
    print("  within-gate-type, does finer error-class add modality signal? (the ONLY observational way")
    print("  to credit error-class over gate-type):")
    any_within=False
    for gt in ("REDIRECTABLE","TERMINAL_GRANT","TRANSIENT"):
        sub=[(e,l) for e,l in zip(ecs,redir) if gate_type(e)==gt]
        if len(sub)<10: 
            print(f"    {gt:14s}: n={len(sub)} (too small to test)")
            continue
        nclass=len(set(e for e,_ in sub))
        if nclass<2:
            print(f"    {gt:14s}: n={len(sub)} but only {nclass} error-class -> error-class==gate-type here (no finer signal possible)")
            continue
        e2=[e for e,_ in sub]; l2=[l for _,l in sub]
        _,_,Vw,ppw,_=cramers_and_perm(e2,l2,B=2000)
        _,bnw,blw,bimpw=loo_brier(e2,l2)
        any_within=True
        print(f"    {gt:14s}: n={len(sub)} classes={nclass} within-V={Vw:.4f} perm_p={ppw:.4f} LOO-Brier_improve={bimpw:+.4f} ({100*bimpw/bnw if bnw else 0:.1f}%)")
    if not any_within:
        print("    ==> NO gate-type bucket has >=2 sizable error-classes with finer modality signal.")
        print("    ==> error-class and gate-type are OBSERVATIONALLY INSEPARABLE in this corpus.")

    # class composition per gate-type (for the writeup)
    print("\n  gate-type composition (which error-classes fall in each, among recovered):")
    comp=defaultdict(lambda:defaultdict(int))
    for e in ecs: comp[gate_type(e)][e]+=1
    for gt in ("REDIRECTABLE","TERMINAL_GRANT","TRANSIENT"):
        items=sorted(comp[gt].items(),key=lambda x:-x[1])
        print(f"    {gt:14s}: "+", ".join(f"{e}={n}" for e,n in items))

    # ---- write CSV summary ----
    csv=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","experiment_result","ablation_baselines.csv"))
    os.makedirs(os.path.dirname(csv),exist_ok=True)
    with open(csv,"w") as f:
        f.write("metric,value\n")
        f.write(f"N_recovered,{Nr}\n")
        f.write(f"NULL_p0,{p0:.4f}\n")
        f.write(f"full_V,{V:.4f}\n")
        f.write(f"full_LOObrier_improve,{bimp:.4f}\n")
        f.write(f"full_LOObrier_pct,{100*bimp/bn:.1f}\n")
        f.write(f"ablated_noWebDisabled_V,{VA:.4f}\n")
        f.write(f"ablated_noWebDisabled_LOObrier_improve,{bimpA:.4f}\n")
        f.write(f"ablated_noWebDisabled_LOObrier_pct,{100*bimpA/bnA if bnA else 0:.1f}\n")
        f.write(f"transientOnly_V,{VA2:.4f}\n")
        f.write(f"transientOnly_LOObrier_improve,{bimpA2:.4f}\n")
        f.write(f"LOCO_full_improve,{bimpL:.4f}\n")
        f.write(f"LOCO_full_pct,{100*bimpL/bnL:.1f}\n")
        f.write(f"LOCO_ablated_improve,{bimpLa:.4f}\n")
        f.write(f"static_mapping_accuracy,{acc_static:.4f}\n")
        f.write(f"static_mapping_brier,{bri_static:.4f}\n")
        f.write(f"gatetype3_V,{VG:.4f}\n")
        f.write(f"gatetype3_LOObrier_improve,{bimpG:.4f}\n")
        f.write(f"gatebinary_V,{VGb:.4f}\n")
        f.write(f"gatebinary_LOObrier_improve,{bimpGb:.4f}\n")
        f.write(f"errorclass_LIFT_over_gatetype3_LOObrier,{bimp-bimpG:.4f}\n")
        f.write(f"errorclass_LIFT_over_gatebinary_LOObrier,{bimp-bimpGb:.4f}\n")
        f.write(f"errorclass_LIFT_over_static_brier,{bri_static-bri_ec:.4f}\n")
        f.write(f"ec_determines_gatetype,{fn}\n")
    print("\nwrote",csv)

if __name__=="__main__":
    main()
