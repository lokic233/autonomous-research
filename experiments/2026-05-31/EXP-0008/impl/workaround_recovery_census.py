#!/usr/bin/env python3
"""
EXP-0008 — Real agent-trace failure-class -> recovery census with a SHARPENED recovery
definition that COUNTS CROSS-TOOL WORKAROUNDS.  Domain MAP-0002 (CLAIM-0008). CPU/stdlib-only.

WHY: EXP-0007 defined recovery = "a later SAME-INTENT call (same tool / same Bash head-cmd /
same file_path) succeeds in-session." That is an explicit LOWER BOUND (VERDICT-0015 caveat):
it does NOT count the agent achieving the goal a DIFFERENT way (a WebFetch block resolved by an
external_web_search; a Bash failure resolved by an Edit). This experiment re-runs the SAME corpus
with a broader, bounded, honestly-operationalized recovery label and asks:
  Q1 How much does per-class recovery RISE when workarounds count vs same-intent-only?
  Q2 Does error-class STILL predict recovery (Cramer's V, honest LOO-Brier vs class-agnostic NULL),
     or do workarounds wash out the signal?
  Q3 Does the permanent(harness/policy gate) vs transient split SURVIVE? (the crux: if policy gates
     stay ~unrecoverable while transient errors gain a lot, the provenance/permanence axis STRENGTHENS.)

parse_session() and classify_error() are COPIED from EXP-0007 (no cross-dir import) so the failure
census is identical; only the RECOVERY label changes.

=========================  OPERATIONALIZATION OF "RECOVERY" (read honestly)  =========================
After a failed call of class C at position i, we look forward in the SAME session within a BOUNDED
window of K=6 subsequent tool calls. recovered_broad = 1 iff ANY of:
  (A) SAME-INTENT retry success  -- identical to EXP-0007 (same tool; Bash=same head-cmd; file=same path).
  (B) CROSS-TOOL WORKAROUND       -- a DIFFERENT tool whose INTENT-CLASS matches the failed call's
      intent-class succeeds within the window.  Intent-classes (tool -> class) are a fixed, pre-declared
      map (WEB_INFO / FILE_READ / FILE_WRITE / EXEC / SEARCH_DISCOVER / DELEGATE). A WebFetch (WEB_INFO)
      block resolved by external_web_search (WEB_INFO) counts; a Bash-read failure (FILE_READ) resolved
      by Read (FILE_READ) counts. We DELIBERATELY do NOT count a cross-CLASS success (e.g. a web block
      followed by an unrelated successful Edit) -- that is not evidence the same goal was met.
  (C) (reported separately, NOT in the headline label) explicit TEXTUAL goal-progression: the assistant's
      next text/thinking block within the window contains an explicit success/achieved-goal phrase.
      We compute this channel but report the primary label as A-or-B only, because (C) is noisier
      (the model can narrate optimism without the goal being met). We show how much (C) would add.

WINDOW K=6 calls. Rationale: a real workaround is near-term; an unrelated later success in a long
session is not "recovery of this failure." We also report K=3 and K=12 sensitivity.

HONEST FAILURE MODES of this definition (stated, not hidden):
  - FALSE POSITIVE risk: a same-intent-class success within K need not be the SAME concrete goal
    (two unrelated WebFetches to different URLs). This INFLATES recovery -> biases toward washing out
    the signal -> if the signal SURVIVES this generous definition it is robust. (Conservative for the claim.)
  - FALSE NEGATIVE risk: a genuine workaround using a tool we mapped to a different intent-class, or
    beyond window K, is missed. Mitigated by the K-sensitivity sweep + the broad intent map.
  - The (B) channel cannot count a workaround that needs NO further tool call (agent reasons around it
    in text only) -- that is exactly channel (C), reported separately.
  - INTENT-CLASS is tool-granularity, not semantic-goal granularity: it is an UPPER BOUND on true
    same-goal recovery, just as same-intent was a LOWER BOUND. The truth is bracketed [EXP-0007, this].
======================================================================================================
"""
import json, glob, os, re, random, math
from collections import defaultdict

ROOT = os.path.expanduser("~/.claude/projects")
random.seed(1234)
K_WINDOW = 6  # bounded look-ahead in tool calls

# ----------------- COPIED VERBATIM FROM EXP-0007 -----------------
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
# ----------------- END COPIED -----------------

# ---- intent-class map for cross-tool workaround detection (pre-declared, fixed) ----
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
        # heuristic: classify Bash by head command into read/write/exec
        if h in BASH_READ_HEADS: return "FILE_READ"
        if h in BASH_WRITE_HEADS: return "FILE_WRITE"
        # a Bash that echoes/redirects into a file -> write
        if cmd and re.search(r">\s*\S", cmd) and not re.search(r">/dev/null|2>&1", cmd): return "FILE_WRITE"
        if cmd and re.search(r"\bcurl\b|\bwget\b|\bfetch\b", cmd): return "WEB_INFO"
        return "EXEC"
    return "EXEC"

SUCCESS_TEXT = re.compile(r"\b(works?|working|succeed|succeeded|success|resolved|fixed|done|passes?|passed|"
                          r"now i (have|can|see)|that worked|confirmed|got it|completed)\b", re.I)

def parse_session(path):
    """COPIED structure from EXP-0007 parse_session, EXTENDED to also keep ordered text/thinking
    blocks interleaved (needed for the textual-progression channel C). Returns list of events where
    each is a dict with kind in {call, text}. 'call' events mirror EXP-0007 calls exactly."""
    uses={}; events=[]
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
                    events.append({"kind":"call","name":u["name"],"cmd":u["cmd"],"intent":u["intent"],
                                   "iclass":intent_class(u["name"],u["cmd"]),
                                   "is_error":bool(b.get("is_error")),"text":block_text(b)})
                elif tp in ("text","thinking"):
                    txt=b.get("text","") if tp=="text" else b.get("thinking","")
                    events.append({"kind":"text","text":txt or ""})
    return events

def calls_only(events):
    return [e for e in events if e["kind"]=="call"]

def label_same_intent(calls, idx):
    """EXP-0007 label: any LATER same-intent call succeeds (unbounded, whole session)."""
    intent=calls[idx]["intent"]
    for j in range(idx+1,len(calls)):
        if calls[j]["intent"]==intent and not calls[j]["is_error"]:
            return 1
    return 0

def label_broad(calls, idx, K):
    """Sharpened label within bounded window K (call positions).
    Returns dict of channel flags: same_intent (within K), workaround (cross-tool same intent-class within K),
    textual (channel C, computed on interleaved events separately), and recovered = same_intent OR workaround."""
    fail=calls[idx]; intent=fail["intent"]; ic=fail["iclass"]
    same=0; work=0
    hi=min(idx+1+K, len(calls))
    for j in range(idx+1, hi):
        cj=calls[j]
        if cj["is_error"]: continue
        if cj["intent"]==intent:
            same=1
        elif cj["iclass"]==ic:
            work=1
    return same, work

def main():
    files=sorted(glob.glob(os.path.join(ROOT,"**","*.jsonl"),recursive=True))
    # records: (error_class, same_intent_unbounded(EXP0007), same_within_K, workaround_within_K, textual_within_K, session_id)
    records=[]; n_sessions=0; n_calls_total=0; n_fail=0
    for path in files:
        try: events=parse_session(path)
        except Exception: continue
        calls=calls_only(events)
        if len(calls)<2: continue
        n_sessions+=1; n_calls_total+=len(calls)
        # build a map from call-position -> event index for the textual channel
        # walk events keeping call counter
        callpos_to_evt=[]; cp=0
        for ei,e in enumerate(events):
            if e["kind"]=="call":
                callpos_to_evt.append(ei); cp+=1
        sid=os.path.basename(path)
        for i,call in enumerate(calls):
            if not call["is_error"]: continue
            n_fail+=1
            si_unbounded = label_same_intent(calls,i)
            same_k, work_k = label_broad(calls,i,K_WINDOW)
            # textual channel C: scan events after this failed call's result, up to the (i+K)-th call's event
            ei_start=callpos_to_evt[i]
            ei_end = callpos_to_evt[min(i+K_WINDOW, len(calls)-1)] if i+K_WINDOW < len(calls) else len(events)
            textual=0
            for ev in events[ei_start+1:ei_end+1]:
                if ev["kind"]=="text" and SUCCESS_TEXT.search(ev["text"] or ""):
                    textual=1; break
            ec=classify_error(call["name"],call["cmd"],call["text"])
            records.append((ec, si_unbounded, same_k, work_k, textual, sid))
    return records, n_sessions, n_calls_total, n_fail

# ---------- stats helpers (copied from EXP-0007) ----------
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

if __name__=="__main__":
    records, n_sessions, n_calls_total, n_fail = main()
    N=len(records)
    ecs=[r[0] for r in records]
    si_unb=[r[1] for r in records]        # EXP-0007 same-intent (unbounded)
    same_k=[r[2] for r in records]        # same-intent within K
    work_k=[r[3] for r in records]        # workaround within K
    textual=[r[4] for r in records]
    broad=[1 if (r[2] or r[3]) else 0 for r in records]                 # PRIMARY sharpened label (A or B)
    broad_txt=[1 if (r[2] or r[3] or r[4]) else 0 for r in records]     # +channel C (reported, not headline)

    print(f"sessions={n_sessions} total_tool_calls={n_calls_total} failures={n_fail}  K_WINDOW={K_WINDOW}")
    print(f"\nGLOBAL recovery rates over N={N} failures:")
    print(f"  EXP-0007 same-intent (unbounded)      p0 = {sum(si_unb)/N:.4f}")
    print(f"  same-intent within K={K_WINDOW}                   = {sum(same_k)/N:.4f}")
    print(f"  BROAD (same-intent OR workaround), K={K_WINDOW}    = {sum(broad)/N:.4f}   <-- PRIMARY sharpened")
    print(f"  BROAD + textual channel C             = {sum(broad_txt)/N:.4f}   (reported, noisier)")
    print(f"  workaround-only flag rate             = {sum(work_k)/N:.4f}")

    # ---- per-class lift table: EXP-0007 (unbounded same-intent) vs BROAD ----
    classes=sorted(set(ecs))
    by_old=defaultdict(lambda:[0,0]); by_new=defaultdict(lambda:[0,0])
    for r in records:
        by_old[r[0]][1]+=1; by_old[r[0]][0]+=r[1]
        by_new[r[0]][1]+=1; by_new[r[0]][0]+= (1 if (r[2] or r[3]) else 0)
    print("\n=== per-class recovery: EXP-0007(same-intent unbounded) vs BROAD(workaround,K) ===")
    print(f"{'class':24s} {'n':>4} {'old_rate':>9} {'broad_rate':>11} {'LIFT':>7}")
    for ec in sorted(classes,key=lambda e:-by_old[e][1]):
        no=by_old[ec]; nn=by_new[ec]
        ro=no[0]/no[1]; rn=nn[0]/nn[1]
        print(f"{ec:24s} {no[1]:>4} {ro:>9.3f} {rn:>11.3f} {rn-ro:>+7.3f}")

    # ---- Q2: does error-class still predict under BROAD? ----
    p0b=sum(broad)/N
    chi,df,V,pp,_=cramers_and_perm(ecs, broad)
    p0_,bn,bl,bimp=loo_brier(ecs, broad)
    print("\n=== Q2: predictiveness under BROAD label (full taxonomy) ===")
    print(f"  null p0(broad)={p0b:.4f}  chi2={chi:.2f} df={df}  Cramers_V={V:.4f}  perm_p={pp:.4f}")
    print(f"  Brier null={bn:.4f}  LOO class-cond={bl:.4f}  improve={bimp:+.4f}  ({100*bimp/bn:.1f}% reduction)")
    # rare-collapse robustness
    by_n=defaultdict(int)
    for ec in ecs: by_n[ec]+=1
    ecs_c=[ec if by_n[ec]>=10 else "rare" for ec in ecs]
    chic,dfc,Vc,ppc,_=cramers_and_perm(ecs_c, broad)
    print(f"  [rare(n<10) collapsed] chi2={chic:.2f} df={dfc} Cramers_V={Vc:.4f} perm_p={ppc:.4f}")

    # ---- Q3: permanent vs transient under BROAD ----
    PERMANENT={"policy.web_disabled","policy.input_filter","policy.perm_denied","cancelled"}
    pc=["permanent" if ec in PERMANENT else "transient" for ec in ecs]
    chiP,dfP,phiP,ppP,byP=cramers_and_perm(pc, broad)
    print("\n=== Q3: PERMANENT vs TRANSIENT under BROAD label ===")
    for cl in sorted(byP.keys()):
        rec,tot=byP[cl]; print(f"  {cl:10s} n={tot:>4} recovered={rec:>4} rate={rec/tot:.3f}")
    print(f"  phi={phiP:.4f}  perm_p={ppP:.4f}")
    # also compare to EXP-0007 perm/transient under unbounded same-intent
    byP_old=defaultdict(lambda:[0,0])
    for r in records:
        cl="permanent" if r[0] in PERMANENT else "transient"
        byP_old[cl][1]+=1; byP_old[cl][0]+=r[1]
    print("  (EXP-0007 same-intent for comparison:)")
    for cl in sorted(byP_old.keys()):
        rec,tot=byP_old[cl]; print(f"    {cl:10s} rate={rec/tot:.3f}")

    # policy-gate specific: web_disabled / perm_denied / input_filter under broad
    print("\n=== Q3b: agent-UNCONTROLLABLE policy gates under BROAD (the crux cells) ===")
    for ec in ("policy.web_disabled","policy.perm_denied","policy.input_filter","cancelled"):
        no=by_old[ec]; nn=by_new[ec]
        if no[1]==0: continue
        print(f"  {ec:22s} n={no[1]:>3}  same-intent={no[0]/no[1]:.3f}  BROAD={nn[0]/nn[1]:.3f}  lift={nn[0]/nn[1]-no[0]/no[1]:+.3f}")

    # ---- K sensitivity ----
    print("\n=== K-window sensitivity (BROAD global rate, V, perm/transient phi) ===")
    files=sorted(glob.glob(os.path.join(ROOT,"**","*.jsonl"),recursive=True))
    for Kx in (3,6,12):
        recs2=[]
        for path in files:
            try: events=parse_session(path)
            except Exception: continue
            calls=calls_only(events)
            if len(calls)<2: continue
            for i,call in enumerate(calls):
                if not call["is_error"]: continue
                s,w=label_broad(calls,i,Kx)
                ec=classify_error(call["name"],call["cmd"],call["text"])
                recs2.append((ec,1 if (s or w) else 0))
        ec2=[r[0] for r in recs2]; lab2=[r[1] for r in recs2]
        gr=sum(lab2)/len(lab2)
        _,_,Vx,ppx,_=cramers_and_perm(ec2,lab2,B=2000)
        pc2=["permanent" if e in PERMANENT else "transient" for e in ec2]
        _,_,phix,_,byx=cramers_and_perm(pc2,lab2,B=2000)
        prate=byx["permanent"][0]/byx["permanent"][1]; trate=byx["transient"][0]/byx["transient"][1]
        print(f"  K={Kx:>2}: broad_rate={gr:.3f}  V={Vx:.3f} (perm_p={ppx:.4f})  perm={prate:.3f} trans={trate:.3f} phi={phix:.3f}")

    # ---- write CSV ----
    csv=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","experiment_result","per_class_workaround_recovery.csv"))
    os.makedirs(os.path.dirname(csv),exist_ok=True)
    with open(csv,"w") as f:
        f.write("class,n,old_same_intent_rate,broad_workaround_rate,lift,broad_recovered\n")
        for ec in sorted(classes,key=lambda e:-by_old[e][1]):
            no=by_old[ec]; nn=by_new[ec]
            f.write(f"{ec},{no[1]},{no[0]/no[1]:.4f},{nn[0]/nn[1]:.4f},{nn[0]/nn[1]-no[0]/no[1]:+.4f},{nn[0]}\n")
        f.write(f"# N={N},K_WINDOW={K_WINDOW}\n")
        f.write(f"# global_same_intent_unbounded={sum(si_unb)/N:.4f},global_broad={p0b:.4f},workaround_flag_rate={sum(work_k)/N:.4f}\n")
        f.write(f"# BROAD_full_taxonomy: chi2={chi:.4f},df={df},CramersV={V:.4f},perm_p={pp:.4f},brier_null={bn:.4f},brier_loo={bl:.4f},brier_improve={bimp:+.4f}\n")
        f.write(f"# BROAD_rare_collapsed: CramersV={Vc:.4f},perm_p={ppc:.4f}\n")
        f.write(f"# BROAD_perm_vs_transient: permanent_rate={byP['permanent'][0]/byP['permanent'][1]:.4f},transient_rate={byP['transient'][0]/byP['transient'][1]:.4f},phi={phiP:.4f},perm_p={ppP:.4f}\n")
    print("\nwrote",csv)
