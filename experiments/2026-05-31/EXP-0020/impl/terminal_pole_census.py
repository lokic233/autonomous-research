#!/usr/bin/env python3
"""
EXP-0020 -- TERMINAL-POLE census for the redirectable-vs-terminal taxonomy (CLAIM-0009). MAP-0002.
CPU-only, stdlib-only. Researcher: researcher-0003-laneA.

CONTEXT (honest): CLAIM-0009 is WEAKENED (VERDICT-0020 6/6 yellow, VERDICT-0021). EXP-0012 showed
error-class & gate-type are observationally INSEPARABLE single-harness; the surviving claim is a
gate-type+harness-routing CHARACTERIZATION with THREE poles:
   REDIRECTABLE  (hard tool-block -> cross-tool redirect; e.g. policy.web_disabled)
   SAME-TOOL/GRANT-REQUIRED (recovers by retrying same tool; e.g. policy.perm_denied, transient)
   TERMINAL  (genuinely unrecovered: NEITHER same-tool-retried NOR cross-tool-redirected to success)
EXP-0009 DEMONSTRATED the first two poles at n>=10. The TERMINAL pole was NOT demonstrated
(no class with n>=10 had ~0 recovery & ~0 redirect). This experiment asks the narrow, falsifiable
question: on THIS corpus, is there a cleanly-TERMINAL error class at n>=10 (recovery~0, redirect~0)?

If YES -> completes the trichotomy (3 demonstrated poles) = a real strengthening of the
characterization. If NO -> the corpus under-samples the terminal pole = a real, honestly-reported
LIMITATION (the terminal pole cannot be DEMONSTRATED on this corpus), not a result we fudge.

parse_session / classify_error / intent_class / head_cmd / block_text are COPIED VERBATIM from
EXP-0007/EXP-0008/EXP-0009 (no cross-dir import). recovery uses EXP-0008's BROAD definition (channel A
same-tool-retry OR channel B cross-tool-redirect within window K). A failure is TERMINAL iff broad
recovery did NOT fire (recovered==0) -- genuinely unrecovered within the bounded window.

We additionally tag SESSION-ENDING failures (failure is the LAST tool call, or no successful tool call
follows anywhere in the rest of the session) -- a stricter terminal signal independent of the window K,
and report repeated-identical-hard-error runs (same error-class fired >=3x consecutively for the same
intent without an intervening success).
"""
import json, glob, os, re, math
from collections import defaultdict

ROOT = os.path.expanduser("~/.claude/projects")
K_WINDOW = 6

# ============== COPIED VERBATIM FROM EXP-0007/0008/0009 ==============
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
# ============== END COPIED ==============

def recovery_broad(calls, idx, K):
    """EXP-0008 broad recovery: channel A (same-intent success) OR channel B (cross-tool same-iclass
    success) within K. Returns (recovered, modality)."""
    fail=calls[idx]; intent=fail["intent"]; ic=fail["iclass"]
    same=False; redirect=False
    hi=min(idx+1+K, len(calls))
    for j in range(idx+1, hi):
        cj=calls[j]
        if cj["is_error"]: continue
        if cj["intent"]==intent: same=True
        elif cj["iclass"]==ic: redirect=True
    if same: return 1, "SAME_TOOL_RETRY"
    if redirect: return 1, "CROSS_TOOL_REDIRECT"
    return 0, None

def is_session_ending(calls, idx):
    """Stricter, K-independent terminal signal: no SUCCESSFUL tool call occurs anywhere after idx in the
    session (the agent never lands another success -> the session effectively ended on unresolved error).
    Also flag 'last_call' = the failure is literally the final tool call."""
    last_call = (idx == len(calls)-1)
    any_success_after = any((not calls[j]["is_error"]) for j in range(idx+1, len(calls)))
    return last_call, (not any_success_after)

def wilson(k,n,z=1.96):
    if n==0: return (0.0,0.0,0.0)
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return (p, max(0,c-h), min(1,c+h))

def build(K):
    files=sorted(glob.glob(os.path.join(ROOT,"**","*.jsonl"),recursive=True))
    recs=[]; ns=0; nc=0; nf=0
    for path in files:
        try: calls=parse_session(path)
        except Exception: continue
        if len(calls)<2: continue
        ns+=1; nc+=len(calls)
        sid=os.path.basename(path)
        # consecutive-identical-hard-error run length per intent
        for i,c in enumerate(calls):
            if not c["is_error"]: continue
            nf+=1
            ec=classify_error(c["name"],c["cmd"],c["text"])
            rec,mod=recovery_broad(calls,i,K)
            last_call, no_success_after = is_session_ending(calls,i)
            # repeated-identical: how many times did the SAME (intent) fail with SAME ec before any success,
            # counting forward from i within the rest of the session contiguously for that intent?
            rep=1
            for j in range(i+1,len(calls)):
                cj=calls[j]
                if cj["intent"]==c["intent"]:
                    if cj["is_error"] and classify_error(cj["name"],cj["cmd"],cj["text"])==ec: rep+=1
                    else: break
            recs.append({"ec":ec,"sid":sid,"failtool":c["name"],"iclass":c["iclass"],
                         "recovered":rec,"modality":mod,
                         "terminal":(1-rec),"last_call":last_call,
                         "no_success_after":no_success_after,"rep_run":rep,
                         "text_head":(c["text"] or "")[:80].replace("\n"," ")})
    return recs, ns, nc, nf

def main():
    recs, ns, nc, nf = build(K_WINDOW)
    n_term = sum(r["terminal"] for r in recs)
    n_lastcall = sum(r["last_call"] for r in recs)
    n_nosucc = sum(r["no_success_after"] for r in recs)
    print(f"sessions={ns} total_tool_calls={nc} failures={nf}  K_WINDOW={K_WINDOW}")
    print(f"\nGLOBAL terminal (broad-recovery did NOT fire, K={K_WINDOW}): {n_term}/{nf} = {n_term/nf:.3f}")
    print(f"  (=> broad recovery rate {1-n_term/nf:.3f}, matches EXP-0008/0009 ~0.64)")
    print(f"session-ending signals (K-independent):")
    print(f"  failure is the LITERAL last tool call:        {n_lastcall}/{nf} = {n_lastcall/nf:.3f}")
    print(f"  NO successful tool call anywhere after fail:  {n_nosucc}/{nf} = {n_nosucc/nf:.3f}")

    # ===== Per-class TERMINAL census =====
    by=defaultdict(lambda:{"nf":0,"term":0,"rec":0,"redir":0,"same":0,"lastcall":0,"nosucc":0,"rep3":0})
    for r in recs:
        d=by[r["ec"]]; d["nf"]+=1
        d["term"]+=r["terminal"]; d["rec"]+=r["recovered"]
        if r["modality"]=="CROSS_TOOL_REDIRECT": d["redir"]+=1
        elif r["modality"]=="SAME_TOOL_RETRY": d["same"]+=1
        d["lastcall"]+=r["last_call"]; d["nosucc"]+=r["no_success_after"]
        if r["rep_run"]>=3: d["rep3"]+=1

    print("\n=== Per-class TERMINAL census (Wilson 95% CI on terminal-share). n_fail desc ===")
    print(f"{'class':22s}{'n':>5}{'term':>6}{'t_rate':>8}{'redir':>6}{'rec':>5}{'lastc':>6}{'nosuc':>6}{'rep>=3':>7}  term_rate_CI")
    for ec in sorted(by, key=lambda e:-by[e]["nf"]):
        d=by[ec]
        tr,lo,hi=wilson(d["term"], d["nf"])
        print(f"{ec:22s}{d['nf']:>5}{d['term']:>6}{tr:>8.3f}{d['redir']:>6}{d['rec']:>5}{d['lastcall']:>6}{d['nosucc']:>6}{d['rep3']:>7}  [{lo:.3f},{hi:.3f}]")

    # ===== TERMINAL POLE declaration: which class(es) at n>=10 are cleanly TERMINAL? =====
    # Criterion (mirrors EXP-0009's TERMINAL label, made explicit & quantified):
    #   cleanly-TERMINAL iff n_fail>=10 AND terminal-share high (recovery low) AND redirect~0.
    # We grade strictness: STRICT (rec_rate<=0.10 & redir==0), MODERATE (rec_rate<=0.25 & redir<=1).
    print("\n=== TERMINAL-POLE candidates (n_fail>=10) ===")
    print("  cleanly-TERMINAL  := rec_rate<=0.10 AND redirect==0  (no modality available)")
    print("  near-TERMINAL     := rec_rate<=0.25 AND redirect<=1")
    strict=[]; near=[]
    for ec in sorted(by, key=lambda e:-by[e]["nf"]):
        d=by[ec]
        if d["nf"]<10: continue
        rr=d["rec"]/d["nf"]
        tr,lo,hi=wilson(d["term"], d["nf"])
        tag=[]
        if rr<=0.10 and d["redir"]==0: tag.append("CLEANLY-TERMINAL"); strict.append(ec)
        elif rr<=0.25 and d["redir"]<=1: tag.append("NEAR-TERMINAL"); near.append(ec)
        else: tag.append("not-terminal (recovers)")
        print(f"  {ec:22s} n={d['nf']:>3} rec_rate={rr:.3f} term_rate={tr:.3f} CI[{lo:.3f},{hi:.3f}] redir={d['redir']} -> {' '.join(tag)}")

    # ===== SESSION-ENDING terminal sub-census (K-independent), per class, n>=10 on the no-success-after signal
    print("\n=== Session-ending terminal sub-census: classes where 'no success after' is common (n>=10) ===")
    for ec in sorted(by, key=lambda e:-by[e]["nosucc"]):
        d=by[ec]
        if d["nf"]<10: continue
        ns_rate,lo,hi=wilson(d["nosucc"], d["nf"])
        print(f"  {ec:22s} n={d['nf']:>3} no_success_after={d['nosucc']:>3} ({ns_rate:.3f}) CI[{lo:.3f},{hi:.3f}] last_call={d['lastcall']}")

    # ===== Repeated-identical-hard-error runs (>=3) -- a behavioral terminal signal independent of recovery
    print("\n=== Repeated-identical-hard-error runs (same intent & error-class failed >=3x consecutively) ===")
    rep_by=defaultdict(int); rep_tot=0
    for r in recs:
        if r["rep_run"]>=3: rep_by[r["ec"]]+=1; rep_tot+=1
    print(f"  total fail-points that begin a >=3-run: {rep_tot}")
    for ec,c in sorted(rep_by.items(), key=lambda x:-x[1]):
        print(f"    {c:>3}x  {ec}")

    # ===== Honest verdict on the terminal pole =====
    print("\n=== TERMINAL-POLE DEMONSTRABILITY (honest) ===")
    if strict:
        print(f"  DEMONSTRATED: cleanly-TERMINAL class(es) at n>=10: {strict}")
        print("  -> completes the trichotomy (REDIRECTABLE / SAME-TOOL / TERMINAL all demonstrated at n>=10).")
    elif near:
        print(f"  PARTIAL: near-TERMINAL class(es) at n>=10 (rec_rate<=0.25, redir<=1): {near}")
        print("  -> a terminal-LEANING pole exists but is not cleanly 0-recovery/0-redirect at n>=10.")
    else:
        print("  UNDER-SAMPLED: NO class at n>=10 is cleanly- or near-TERMINAL.")
        print("  -> the terminal pole CANNOT be demonstrated on this corpus (honest limitation).")
    # sample examples of the most-terminal class for the result writeup
    if by:
        top_term = max((ec for ec in by if by[ec]["nf"]>=10),
                       key=lambda e: by[e]["term"]/by[e]["nf"], default=None)
        if top_term:
            print(f"\n  Most terminal-leaning n>=10 class: {top_term} (term_rate={by[top_term]['term']/by[top_term]['nf']:.3f})")
            exs=[r for r in recs if r["ec"]==top_term and r["terminal"]][:5]
            for e in exs:
                print(f"    e.g. [{e['failtool']}] {e['text_head']}")

    # ---- write CSV ----
    csv=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","experiment_result","terminal_pole_per_class.csv"))
    os.makedirs(os.path.dirname(csv),exist_ok=True)
    with open(csv,"w") as f:
        f.write("class,n_fail,terminal,terminal_rate,term_lo,term_hi,recovered,recovery_rate,redirect,same_tool,last_call,no_success_after,rep_ge3,pole_label\n")
        for ec in sorted(by, key=lambda e:-by[e]["nf"]):
            d=by[ec]
            tr,lo,hi=wilson(d["term"], d["nf"]); rr=d["rec"]/d["nf"] if d["nf"] else 0
            if d["nf"]>=10:
                if rr<=0.10 and d["redir"]==0: lab="CLEANLY-TERMINAL"
                elif rr<=0.25 and d["redir"]<=1: lab="NEAR-TERMINAL"
                elif d["rec"]>0 and (d["redir"]/d["rec"] if d["rec"] else 0)>=0.40: lab="REDIRECTABLE"
                elif d["rec"]>0: lab="SAME-TOOL"
                else: lab="MIXED"
            else: lab="small-n"
            f.write(f"{ec},{d['nf']},{d['term']},{tr:.4f},{lo:.4f},{hi:.4f},{d['rec']},{rr:.4f},{d['redir']},{d['same']},{d['lastcall']},{d['nosucc']},{d['rep3']},{lab}\n")
        f.write(f"# sessions={ns},total_tool_calls={nc},failures={nf},K_WINDOW={K_WINDOW}\n")
        f.write(f"# global_terminal={n_term}({n_term/nf:.4f}),last_call={n_lastcall},no_success_after={n_nosucc}\n")
        f.write(f"# cleanly_terminal_n>=10={strict},near_terminal_n>=10={near}\n")
    print("\nwrote", csv)

if __name__=="__main__":
    main()

# ---- appended: K-sensitivity + is terminality even a CLASS property? (run via __main__ guard re-exec) ----
def supplementary():
    import random
    random.seed(7)
    def chi2_table(table):
        rows=len(table); rt=[sum(r) for r in table]
        ct=[sum(table[i][j] for i in range(rows)) for j in range(2)]; tot=sum(rt)
        if tot==0: return 0.0
        chi=0.0
        for i in range(rows):
            for j in range(2):
                e=rt[i]*ct[j]/tot
                if e>0: chi+=(table[i][j]-e)**2/e
        return chi
    print("\n=== SUPPLEMENTARY: is TERMINALITY a class property, or class-independent abandonment? ===")
    for Kx in (3,6,12,24):
        recs,ns,nc,nf=build(Kx)
        term=[r["terminal"] for r in recs]; ecs=[r["ec"] for r in recs]
        N=len(term); T=sum(term)
        by=defaultdict(lambda:[0,0])
        for e,t in zip(ecs,term): by[e][1]+=1; by[e][0]+=t
        classes=sorted(by)
        obs=[[by[e][0],by[e][1]-by[e][0]] for e in classes]
        chi=chi2_table(obs); V=math.sqrt(chi/N) if N else 0
        # permutation p
        lab=list(term); ge=0; B=2000
        for _ in range(B):
            random.shuffle(lab); t2=defaultdict(lambda:[0,0])
            for e,l in zip(ecs,lab): t2[e][1]+=1; t2[e][0]+=l
            if chi2_table([[t2[e][0],t2[e][1]-t2[e][0]] for e in classes])>=chi-1e-9: ge+=1
        pp=(ge+1)/(B+1)
        anyclean=any((by[e][1]>=10 and by[e][0]/by[e][1]>=0.90) for e in classes)
        print(f"  K={Kx:>2}: global_term_rate={T/N:.3f}  class-vs-terminal CramersV={V:.3f} perm_p={pp:.4f}  "
              f"any n>=10 class >=0.90 terminal? {anyclean}")
    print("  INTERPRETATION: if V is small / perm_p n.s., terminality is NOT predicted by error-class")
    print("  -> the 'terminal' failures are diffuse goal-abandonment, not a cleanly-terminal error class.")

if __name__=="__main__" and os.environ.get("SUPP")=="1":
    supplementary()
