#!/usr/bin/env python3
"""
EXP-0009 — Real agent-trace RECOVERY-MODALITY census (CLAIM-0009). Domain MAP-0002. CPU/stdlib-only.

CLAIM-0009 (surviving kernel from EXP-0008, which REFUTED occurrence-prediction CLAIM-0008):
  "Error-class predicts agent recovery MODALITY (same-tool-retry vs cross-tool-redirect), NOT recovery
   OCCURRENCE; failure provenance determines HOW an agent recovers, conditioned on whether a
   policy/permission gate is REDIRECTABLE (blocked tool -> sanctioned alternative) vs TERMINAL."

WHAT THIS PROBE DOES (one rigorous test, CPU-only, same corpus ~/.claude/projects):
  parse_session / classify_error / intent_class / head_cmd / block_text are COPIED VERBATIM from
  EXP-0007 + EXP-0008 (no cross-dir import). We reuse EXP-0008's BROAD recovery definition to decide
  WHICH failures recovered, then for each recovered failure we assign the recovery MODALITY:

    MODALITY = SAME_TOOL_RETRY  iff channel (A) fired (a later SAME-INTENT call -- same tool;
                                   Bash=same head-cmd; file=same path -- succeeded within window K).
    MODALITY = CROSS_TOOL_REDIRECT iff channel (A) did NOT fire but channel (B) did (a DIFFERENT tool
                                   of the SAME intent-class succeeded within K). i.e. the agent reached
                                   the goal by switching tools, not by retrying the same one.

  Precedence: if BOTH A and B fire we label SAME_TOOL_RETRY (the agent did get the same tool to work;
  a redirect is only the operative modality when same-tool retry did NOT succeed). This is the
  conservative reading of "how did it recover" -- it UNDER-counts redirect, biasing AGAINST the
  redirectable-gate story, so a surviving redirect signal is robust. We also report a B-priority
  variant (redirect wins ties) as a sensitivity check.

TESTS:
  T1. Among RECOVERED failures, does error-class PREDICT modality (binary: redirect vs same-tool-retry)?
      Cramer's V + permutation test vs a modality-AGNOSTIC NULL (global redirect rate among recovered).
      Honest leave-one-out Brier of class-conditional redirect-prob vs the constant-null.
  T2. Leave-ONE-SESSION-OUT: is the modality signal session-robust or one-session artifact (if N permits)?
  T3. REDIRECTABLE vs TERMINAL gate taxonomy: per error-class, what fraction of recovered failures used
      redirect? Declare a class REDIRECTABLE if it has a sanctioned alternate path (redirect-heavy) vs
      TERMINAL if no recovery modality is available (recovery rate ~0 AND no redirects). Does the
      dichotomy hold? Report per-class evidence + confidence (Wilson interval) given small N.

HONESTY: small-N cells dominate (web_disabled n~109 is the only large one; others n<30). We report
Wilson 95% CIs on every modality rate and refuse to over-read cells with n<10. If error-class does NOT
predict modality above the null, that WEAKENS CLAIM-0009 and we say so plainly.
"""
import json, glob, os, re, random, math
from collections import defaultdict

ROOT = os.path.expanduser("~/.claude/projects")
random.seed(1234)
K_WINDOW = 6

# ============== COPIED VERBATIM FROM EXP-0007 / EXP-0008 ==============
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
    """Returns ordered list of 'call' events (mirrors EXP-0008 calls_only); each has name/cmd/intent/
    iclass/is_error/text plus the WINNING-TOOL name when used as a recovery."""
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
# ============== END COPIED ==============

def recovery_modality(calls, idx, K):
    """For a failed call at idx, look forward within K successful calls.
    Returns (recovered, modality, winning_tool):
      modality in {None, 'SAME_TOOL_RETRY', 'CROSS_TOOL_REDIRECT'}.
    Channel A = same-intent success (same tool, same head/path). Channel B = different tool, same iclass.
    Precedence (conservative, default): A wins ties -> redirect only when same-tool retry did NOT succeed
    within K. We record the FIRST qualifying success of each channel and its tool name."""
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

def recovery_modality_Bpriority(calls, idx, K):
    """Sensitivity: redirect wins ties (if BOTH A and B fire, call it redirect)."""
    fail=calls[idx]; intent=fail["intent"]; ic=fail["iclass"]
    same=False; redirect=False
    hi=min(idx+1+K, len(calls))
    for j in range(idx+1, hi):
        cj=calls[j]
        if cj["is_error"]: continue
        if cj["intent"]==intent: same=True
        elif cj["iclass"]==ic: redirect=True
    if redirect: return 1, "CROSS_TOOL_REDIRECT"
    if same: return 1, "SAME_TOOL_RETRY"
    return 0, None

# ---------- stats helpers (copied from EXP-0007/0008) ----------
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

def cramers_and_perm(ecs, labels, B=5000):
    classes=sorted(set(ecs)); N=len(labels)
    by=defaultdict(lambda:[0,0])
    for ec,l in zip(ecs,labels): by[ec][1]+=1; by[ec][0]+=l
    obs=[[by[ec][0],by[ec][1]-by[ec][0]] for ec in classes]
    chi=chi2_table(obs); V=math.sqrt(chi/N) if N else 0.0
    lab=list(labels); ge=0
    for _ in range(B):
        random.shuffle(lab)
        tab=defaultdict(lambda:[0,0])
        for ec,l in zip(ecs,lab): tab[ec][1]+=1; tab[ec][0]+=l
        if chi2_table([[tab[ec][0],tab[ec][1]-tab[ec][0]] for ec in classes])>=chi-1e-9: ge+=1
    return chi, len(classes)-1, V, (ge+1)/(B+1), by

def loo_brier(ecs, labels):
    by=defaultdict(lambda:[0,0])
    for ec,l in zip(ecs,labels): by[ec][1]+=1; by[ec][0]+=l
    N=len(labels); R=sum(labels); p0=R/N if N else 0.0
    bn=sum((p0-l)**2 for l in labels)/N
    bl=0.0
    for ec,l in zip(ecs,labels):
        rec,tot=by[ec]
        p=(rec-l)/(tot-1) if tot>1 else p0
        bl+=(p-l)**2
    bl/=N
    return p0,bn,bl,bn-bl

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
            recB,modB=recovery_modality_Bpriority(calls,i,K)
            recs.append({"ec":ec,"sid":sid,"failtool":c["name"],"iclass":c["iclass"],
                         "recovered":rec,"modality":mod,"wtool":wtool,
                         "modalityB":modB})
    return recs, n_sessions, n_calls, n_fail

def main():
    recs, ns, nc, nf = build_records(K_WINDOW)
    print(f"sessions={ns} total_tool_calls={nc} failures={nf}  K_WINDOW={K_WINDOW}")

    rec_only=[r for r in recs if r["recovered"]==1]
    Nr=len(rec_only)
    n_redirect=sum(1 for r in rec_only if r["modality"]=="CROSS_TOOL_REDIRECT")
    n_same=Nr-n_redirect
    print(f"\nRECOVERED failures (broad def, K={K_WINDOW}): N={Nr}  "
          f"(of {nf} failures = {Nr/nf:.3f})")
    print(f"  SAME_TOOL_RETRY    = {n_same}  ({n_same/Nr:.3f})")
    print(f"  CROSS_TOOL_REDIRECT= {n_redirect}  ({n_redirect/Nr:.3f})   <-- modality-agnostic NULL redirect rate")

    # ===== T1: does error-class predict MODALITY among recovered? =====
    ecs=[r["ec"] for r in rec_only]
    redir=[1 if r["modality"]=="CROSS_TOOL_REDIRECT" else 0 for r in rec_only]
    chi,df,V,pp,by=cramers_and_perm(ecs, redir)
    p0,bn,bl,bimp=loo_brier(ecs, redir)
    print("\n=== T1: error-class -> recovery MODALITY (redirect vs same-tool-retry), among recovered ===")
    print(f"  modality-agnostic NULL redirect rate p0={n_redirect/Nr:.4f}")
    print(f"  full taxonomy: chi2={chi:.2f} df={df}  Cramers_V={V:.4f}  perm_p={pp:.4f}")
    print(f"  LOO-Brier: null={bn:.4f} class-cond={bl:.4f} improve={bimp:+.4f} ({100*bimp/bn if bn else 0:.1f}% reduction)")
    # rare collapse
    cnt=defaultdict(int)
    for e in ecs: cnt[e]+=1
    ecs_c=[e if cnt[e]>=10 else "rare" for e in ecs]
    chic,dfc,Vc,ppc,_=cramers_and_perm(ecs_c, redir)
    p0c,bnc,blc,bimpc=loo_brier(ecs_c, redir)
    print(f"  [rare(n<10)->'rare' collapsed] chi2={chic:.2f} df={dfc} Cramers_V={Vc:.4f} perm_p={ppc:.4f}  "
          f"LOO-Brier improve={bimpc:+.4f} ({100*bimpc/bnc if bnc else 0:.1f}%)")

    # ===== T3: per-class modality breakdown + REDIRECTABLE/TERMINAL taxonomy =====
    print("\n=== Per-class modality + recovery (Wilson 95% CI). 'redir_share' = redirect / recovered ===")
    print(f"{'class':22s}{'n_fail':>7}{'recov':>7}{'rec_rate':>9}{'same':>6}{'redir':>6}{'redir_share':>13}  redir_share_CI")
    by_ec=defaultdict(lambda:{"nf":0,"rec":0,"same":0,"redir":0})
    for r in recs:
        d=by_ec[r["ec"]]; d["nf"]+=1
        if r["recovered"]:
            d["rec"]+=1
            if r["modality"]=="CROSS_TOOL_REDIRECT": d["redir"]+=1
            else: d["same"]+=1
    rows=[]
    for ec in sorted(by_ec,key=lambda e:-by_ec[e]["nf"]):
        d=by_ec[ec]
        rr=d["rec"]/d["nf"] if d["nf"] else 0
        rs,lo,hi=wilson(d["redir"], d["rec"]) if d["rec"] else (0,0,0)
        rows.append((ec,d["nf"],d["rec"],rr,d["same"],d["redir"],rs,lo,hi))
        print(f"{ec:22s}{d['nf']:>7}{d['rec']:>7}{rr:>9.3f}{d['same']:>6}{d['redir']:>6}{rs:>13.3f}  [{lo:.3f},{hi:.3f}]")

    # Explicit REDIRECTABLE vs TERMINAL declaration with criteria
    print("\n=== REDIRECTABLE vs TERMINAL gate taxonomy (criteria: classes with n_fail>=10) ===")
    print("  REDIRECTABLE = recovered & redirect-share materially >0 (sanctioned alternative path exists)")
    print("  SAME-TOOL    = recovered mostly by retrying the same tool (transient/fixable in place)")
    print("  TERMINAL     = recovery rate ~0 AND ~no redirects (no modality available)")
    for ec in sorted(by_ec,key=lambda e:-by_ec[e]["nf"]):
        d=by_ec[ec]
        if d["nf"]<10: continue
        rr=d["rec"]/d["nf"]
        rs=d["redir"]/d["rec"] if d["rec"] else 0
        if rr<0.10 and d["redir"]==0: label="TERMINAL"
        elif d["rec"]>0 and rs>=0.40: label="REDIRECTABLE"
        elif d["rec"]>0 and rs<0.40: label="SAME-TOOL"
        else: label="MIXED/UNCLEAR"
        print(f"  {ec:22s} n={d['nf']:>3} rec_rate={rr:.3f} redir_share={rs:.3f}  -> {label}")

    # Winning-tool audit for redirects (what tool did the agent switch TO?)
    print("\n=== Redirect winning-tool audit (failtool -> winning tool), top pairs ===")
    pairs=defaultdict(int)
    for r in rec_only:
        if r["modality"]=="CROSS_TOOL_REDIRECT":
            pairs[(r["ec"], r["failtool"], r["wtool"])]+=1
    for (ec,ft,wt),c in sorted(pairs.items(),key=lambda x:-x[1])[:15]:
        print(f"  {c:>3}x  {ec:20s} {ft} -> {wt}")

    # ===== T2: leave-one-session-out robustness of the modality signal =====
    print("\n=== T2: leave-one-session-out (LOSO) robustness of modality-V and web_disabled redir-share ===")
    def cramers_V_only(ecs2, labels2):
        classes=sorted(set(ecs2)); N=len(labels2)
        by2=defaultdict(lambda:[0,0])
        for ec,l in zip(ecs2,labels2): by2[ec][1]+=1; by2[ec][0]+=l
        obs=[[by2[ec][0],by2[ec][1]-by2[ec][0]] for ec in classes]
        return math.sqrt(chi2_table(obs)/N) if N else 0.0
    sessions=sorted(set(r["sid"] for r in rec_only))
    Vs=[]; wd_shares=[]
    for drop in sessions:
        sub=[r for r in rec_only if r["sid"]!=drop]
        if len(sub)<20: continue
        e2=[r["ec"] for r in sub]; l2=[1 if r["modality"]=="CROSS_TOOL_REDIRECT" else 0 for r in sub]
        Vd=cramers_V_only(e2,l2)
        Vs.append(Vd)
        wd=[r for r in sub if r["ec"]=="policy.web_disabled"]
        if wd: wd_shares.append(sum(1 for r in wd if r["modality"]=="CROSS_TOOL_REDIRECT")/len(wd))
    if Vs:
        print(f"  LOSO Cramers_V over {len(Vs)} drops: min={min(Vs):.3f} median={sorted(Vs)[len(Vs)//2]:.3f} max={max(Vs):.3f}")
    if wd_shares:
        print(f"  LOSO web_disabled redirect-share: min={min(wd_shares):.3f} median={sorted(wd_shares)[len(wd_shares)//2]:.3f} max={max(wd_shares):.3f}")

    # ===== Sensitivity: B-priority (redirect wins ties) =====
    n_redirB=sum(1 for r in rec_only if r["modalityB"]=="CROSS_TOOL_REDIRECT")
    redirB=[1 if r["modalityB"]=="CROSS_TOOL_REDIRECT" else 0 for r in rec_only]
    chiB,dfB,VB,ppB,_=cramers_and_perm(ecs, redirB)
    _,bnB,blB,bimpB=loo_brier(ecs, redirB)
    print("\n=== Sensitivity: B-priority modality (redirect wins A/B ties) ===")
    print(f"  redirect rate p0={n_redirB/Nr:.4f}  Cramers_V={VB:.4f} perm_p={ppB:.4f}  LOO-Brier improve={bimpB:+.4f} ({100*bimpB/bnB if bnB else 0:.1f}%)")

    # ===== Sensitivity: STRICT redirect = cross-tool AND different tool NAME =====
    # 31/117 "redirects" are same tool NAME (e.g. Bash w/ different head-cmd) = arguably same-tool,
    # different-invocation. Strict variant counts only TRUE cross-tool-name redirects.
    strict=[1 if (r["modality"]=="CROSS_TOOL_REDIRECT" and r["failtool"]!=r["wtool"]) else 0 for r in rec_only]
    chiS,dfS,VS,ppS,_=cramers_and_perm(ecs, strict)
    _,bnS,blS,bimpS=loo_brier(ecs, strict)
    print("\n=== Sensitivity: STRICT redirect (cross-tool-NAME only; Bash->Bash counts as same-tool) ===")
    print(f"  strict redirect rate p0={sum(strict)/Nr:.4f}  Cramers_V={VS:.4f} perm_p={ppS:.4f}  "
          f"LOO-Brier improve={bimpS:+.4f} ({100*bimpS/bnS if bnS else 0:.1f}%)")

    # ===== K sensitivity for modality =====
    print("\n=== K-window sensitivity of modality signal ===")
    for Kx in (3,6,12):
        r2,_,_,_=build_records(Kx)
        ro=[r for r in r2 if r["recovered"]==1]
        if not ro: continue
        e3=[r["ec"] for r in ro]; l3=[1 if r["modality"]=="CROSS_TOOL_REDIRECT" else 0 for r in ro]
        _,_,Vx,ppx,_=cramers_and_perm(e3,l3,B=2000)
        _,bnx,blx,bimpx=loo_brier(e3,l3)
        rr=sum(l3)/len(l3)
        print(f"  K={Kx:>2}: recovered={len(ro)} redirect_rate={rr:.3f} V={Vx:.3f} (perm_p={ppx:.4f}) LOO-Brier_improve={bimpx:+.4f}")

    # ---- write CSV ----
    csv=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","experiment_result","per_class_modality.csv"))
    os.makedirs(os.path.dirname(csv),exist_ok=True)
    with open(csv,"w") as f:
        f.write("class,n_fail,recovered,recovery_rate,same_tool_retry,cross_tool_redirect,redirect_share,redir_share_lo,redir_share_hi,gate_label\n")
        for ec in sorted(by_ec,key=lambda e:-by_ec[e]["nf"]):
            d=by_ec[ec]
            rr=d["rec"]/d["nf"] if d["nf"] else 0
            rs,lo,hi=wilson(d["redir"], d["rec"]) if d["rec"] else (0,0,0)
            if d["nf"]>=10:
                if rr<0.10 and d["redir"]==0: lab="TERMINAL"
                elif d["rec"]>0 and (d["redir"]/d["rec"])>=0.40: lab="REDIRECTABLE"
                elif d["rec"]>0: lab="SAME-TOOL"
                else: lab="MIXED"
            else: lab="small-n"
            f.write(f"{ec},{d['nf']},{d['rec']},{rr:.4f},{d['same']},{d['redir']},{rs:.4f},{lo:.4f},{hi:.4f},{lab}\n")
        f.write(f"# N_recovered={Nr},redirect={n_redirect},same_tool={n_same},NULL_redirect_rate={n_redirect/Nr:.4f}\n")
        f.write(f"# T1_full_taxonomy: CramersV={V:.4f},perm_p={pp:.4f},LOO_Brier_improve={bimp:+.4f}\n")
        f.write(f"# T1_rare_collapsed: CramersV={Vc:.4f},perm_p={ppc:.4f},LOO_Brier_improve={bimpc:+.4f}\n")
    print("\nwrote",csv)

if __name__=="__main__":
    main()
