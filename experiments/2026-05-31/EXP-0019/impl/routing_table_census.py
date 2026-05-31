#!/usr/bin/env python3
"""
EXP-0019 - HARNESS ROUTING-TABLE CHARACTERIZATION (laneB; under CLAIM-0009). MAP-0002. CPU/stdlib-only.

POSITIVE-CHARACTERIZATION LANE (distinct from the refuted error-class claims & from laneA terminal-pole work):
EXP-0012 established the CONFOUND -- harness routing (gate-type) determines recovery modality, NOT error-class
(observationally inseparable). This experiment turns the confound into a POSITIVE measurement of the harness's
de-facto ROUTING TABLE itself.

THESIS UNDER TEST (honest, falsifiable):
  "Agentic recovery competence is largely a property of the harness's FALLBACK ROUTING TABLE
   (low-entropy / near-deterministic next-tool-per-error-class), not adaptive LLM reasoning."
  - SUPPORT  if the per-class next-tool distribution is LOW-entropy / near-deterministic
             (the harness has a fixed fallback path per failure class).
  - REFUTE   if it is HIGH-entropy / diffuse (the next tool is chosen adaptively, not routed).

WHAT WE MEASURE (one rigorous census, same corpus ~/.claude/projects):
  For every ground-truth failure of class C at call position i, we look at WHAT TOOL THE AGENT INVOKES NEXT
  in the same session (the empirical fallback). We build, per class:
    1. the next-tool distribution P(next_tool | class C)              -> the de-facto routing table
    2. Shannon entropy H (bits) and normalized entropy H/Hmax          -> how deterministic the routing is
    3. top-1 routing share (mode mass)                                  -> determinism in one number
  Then we ask HOW MUCH RECOVERY IS ROUTING-EXPLAINED:
    4. of recovered failures (EXP-0008 BROAD def, copied verbatim), what fraction took the class's MODAL
       next-tool path?  -> routing-explained recovery fraction
    5. a "routing-only" predictor of recovery: predict recover=1 iff the class's modal-next-tool route has
       recovery-rate > 0.5; honest leave-one-out Brier vs NULL  -> can a fixed routing table predict
       recovery as well as anything?
  Baseline contrast: global next-tool entropy (class-agnostic) vs per-class entropy. If per-class entropy is
  MUCH lower than global, the class label collapses the agent's next move to a near-fixed route (routing-table
  story). If per-class ~ global, the next move is class-independent / adaptive.

HONESTY: this is OBSERVATIONAL on a SINGLE harness (Claude Code). Low entropy is consistent with a hard-wired
routing table AND with a strongly-learned-but-adaptive habit; we cannot interventionally separate them here.
But low per-class entropy + a single dominant route is the OBSERVABLE SIGNATURE a routing-table predicts, and
the entropy magnitude is itself the headline characterization regardless of mechanism. Small-n classes are
flagged; we refuse to over-read n<10. We do NOT edit claims/map/cemetery.
"""
import json, glob, os, re, random, math
from collections import defaultdict, Counter

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
# ============== END COPIED ==============

# ---- routing-tool label: the canonical name of a tool for the routing table ----
def routing_tool(call):
    """The fallback target identity: tool name; Bash collapsed to Bash:<head> so a tool-switch
    (WebFetch->external_web_search) is distinct from in-place Bash reinvocation, but generic Bash
    is one bucket per head-command so we do not explode entropy on argument noise."""
    n = call["name"] or "?"
    if n == "Bash":
        h = head_cmd(call["cmd"]) or "(bash)"
        return "Bash:" + h
    return n

def entropy_bits(counter):
    tot = sum(counter.values())
    if tot == 0: return 0.0, 0.0, 0.0
    H = 0.0
    for c in counter.values():
        p = c/tot
        if p > 0: H -= p*math.log2(p)
    k = len(counter)
    Hmax = math.log2(k) if k > 1 else 0.0
    top1 = max(counter.values())/tot
    Hnorm = (H/Hmax) if Hmax > 0 else 0.0
    return H, Hnorm, top1

# ---- BROAD recovery (copied logic from EXP-0008/0009) ----
def broad_recovered(calls, i):
    fc = calls[i]
    fintent = fc["intent"]; ficlass = fc["iclass"]
    window = calls[i+1:i+1+K_WINDOW]
    same_tool = False; cross_tool = False
    for w in window:
        if w["is_error"]: continue
        if w["intent"] == fintent:
            same_tool = True
        elif w["iclass"] == ficlass:
            cross_tool = True
    return same_tool or cross_tool, same_tool, cross_tool

def main():
    # recursive glob to include subagent traces (legitimate agent tool-use logs); maximizes n
    files = sorted(glob.glob(os.path.join(ROOT, "**", "*.jsonl"), recursive=True))
    n_sessions=0; n_calls=0
    # failures: list of dicts {class, next_tool(or None), recovered, modal_route_taken-later}
    failures=[]
    global_next = Counter()
    per_class_next = defaultdict(Counter)         # routing table P(next_tool|class)
    per_class_failrows = defaultdict(list)        # rows for recovery analysis
    for path in files:
        calls = parse_session(path)
        if len(calls) < 2: continue
        n_sessions += 1; n_calls += len(calls)
        for i,c in enumerate(calls):
            if not c["is_error"]: continue
            cls = classify_error(c["name"], c["cmd"], c["text"])
            # the immediate next tool invoked in the session (the empirical fallback)
            nxt = calls[i+1] if i+1 < len(calls) else None
            nt = routing_tool(nxt) if nxt is not None else "(END)"
            global_next[nt]+=1
            per_class_next[cls][nt]+=1
            rec, st, ct = broad_recovered(calls, i)
            per_class_failrows[cls].append({"next":nt,"rec":1 if rec else 0})
            failures.append({"cls":cls,"next":nt,"rec":1 if rec else 0})

    Nfail=len(failures)
    print(f"corpus: {n_sessions} sessions, {n_calls} calls, {Nfail} ground-truth failures")

    # ---- global next-tool entropy (class-agnostic baseline) ----
    gH, gHn, gtop1 = entropy_bits(global_next)
    print(f"\nGLOBAL next-tool dist: entropy={gH:.3f} bits, norm={gHn:.3f}, top1-share={gtop1:.3f}, "
          f"support={len(global_next)} | mode={global_next.most_common(1)[0]}")

    # ---- per-class routing table + entropy ----
    print("\n=== PER-CLASS DE-FACTO ROUTING TABLE (next-tool distribution) ===")
    print(f"{'class':22s} {'n':>4s} {'H_bits':>7s} {'Hnorm':>6s} {'top1':>6s} {'rec_rate':>8s}  modal_route -> recovery_of_that_route")
    rows_csv=[]
    classes_sorted = sorted(per_class_next.keys(), key=lambda k:-sum(per_class_next[k].values()))
    weighted_Hn=0.0; weighted_top1=0.0; tot_n=0
    for cls in classes_sorted:
        ctr = per_class_next[cls]
        n = sum(ctr.values())
        H,Hn,top1 = entropy_bits(ctr)
        modal_route, modal_n = ctr.most_common(1)[0]
        rows = per_class_failrows[cls]
        rec_rate = sum(r["rec"] for r in rows)/len(rows) if rows else 0.0
        # recovery rate among failures that took the MODAL route
        modal_rows=[r for r in rows if r["next"]==modal_route]
        modal_rec = (sum(r["rec"] for r in modal_rows)/len(modal_rows)) if modal_rows else 0.0
        flag = "" if n>=10 else "  (small-n)"
        print(f"{cls:22s} {n:4d} {H:7.3f} {Hn:6.3f} {top1:6.3f} {rec_rate:8.3f}  {modal_route} ({modal_n}/{n}, rec={modal_rec:.2f}){flag}")
        rows_csv.append((cls,n,H,Hn,top1,rec_rate,modal_route,modal_n,modal_rec))
        if n>=10:
            weighted_Hn += Hn*n; weighted_top1 += top1*n; tot_n += n
    wHn = weighted_Hn/tot_n if tot_n else 0.0
    wtop1 = weighted_top1/tot_n if tot_n else 0.0
    print(f"\nn>=10 classes: failure-weighted norm-entropy={wHn:.3f}, failure-weighted top1-route-share={wtop1:.3f}")
    print(f"GLOBAL norm-entropy={gHn:.3f}.  Entropy COLLAPSE from knowing class = {gHn-wHn:+.3f} (norm units)")

    # ---- how much recovery is ROUTING-EXPLAINED ----
    # routing-only predictor: leave-one-out. For each failure, look up its class's modal route
    # (computed WITHOUT this sample) and that route's recovery rate (computed WITHOUT this sample);
    # predict p=that rate. Compare honest LOO-Brier to NULL (global recovery rate, LOO).
    print("\n=== ROUTING-EXPLAINED RECOVERY (honest leave-one-out) ===")
    # precompute per (class) -> per (route) recovery sums for LOO
    # structures: cls -> route -> [n, sum_rec]; cls -> modal counts already in per_class_next
    cls_route_stats=defaultdict(lambda: defaultdict(lambda:[0,0]))
    for f in failures:
        s=cls_route_stats[f["cls"]][f["next"]]; s[0]+=1; s[1]+=f["rec"]
    tot_rec=sum(f["rec"] for f in failures)
    brier_null=0.0; brier_route=0.0
    for f in failures:
        # NULL LOO: global recovery rate excluding this sample
        p_null=(tot_rec - f["rec"])/(Nfail-1) if Nfail>1 else 0.5
        brier_null += (p_null - f["rec"])**2
        # routing LOO: this class's modal route excluding this sample, then that route's recovery rate excluding this sample
        ctr = Counter(per_class_next[f["cls"]]); ctr[f["next"]] -= 1
        if ctr[f["next"]]<=0: del ctr[f["next"]]
        if ctr:
            modal_route=ctr.most_common(1)[0][0]
        else:
            modal_route=f["next"]
        rs=cls_route_stats[f["cls"]][modal_route]
        if modal_route==f["next"]:
            n_loo=rs[0]-1; rec_loo=rs[1]-f["rec"]
        else:
            n_loo=rs[0]; rec_loo=rs[1]
        p_route=(rec_loo/n_loo) if n_loo>0 else p_null
        brier_route += (p_route - f["rec"])**2
    brier_null/=Nfail; brier_route/=Nfail
    improve=brier_null-brier_route
    print(f"NULL LOO-Brier (global recovery rate)        = {brier_null:.4f}")
    print(f"ROUTING-table LOO-Brier (class modal route)  = {brier_route:.4f}")
    print(f"Routing-table improvement over NULL          = {improve:+.4f} ({100*improve/brier_null:+.1f}%)")

    # fraction of recovered failures that went via their class's modal route
    rec_via_modal=0; rec_total=0
    for cls in per_class_next:
        modal=per_class_next[cls].most_common(1)[0][0]
        for r in per_class_failrows[cls]:
            if r["rec"]:
                rec_total+=1
                if r["next"]==modal: rec_via_modal+=1
    print(f"\nRecovered failures routed via their class's MODAL next-tool: {rec_via_modal}/{rec_total} = "
          f"{rec_via_modal/rec_total:.3f}")

    # ---- write CSV ----
    outdir=os.path.join(os.path.dirname(__file__),"..","experiment_result")
    os.makedirs(outdir,exist_ok=True)
    csvp=os.path.join(outdir,"routing_table.csv")
    with open(csvp,"w") as f:
        f.write("class,n_fail,entropy_bits,norm_entropy,top1_route_share,recovery_rate,modal_route,modal_n,modal_route_recovery\n")
        for r in rows_csv:
            f.write(f"{r[0]},{r[1]},{r[2]:.4f},{r[3]:.4f},{r[4]:.4f},{r[5]:.4f},{r[6]},{r[7]},{r[8]:.4f}\n")
    # also dump full per-class routing distributions
    distp=os.path.join(outdir,"routing_distributions.csv")
    with open(distp,"w") as f:
        f.write("class,next_tool,count,share\n")
        for cls in classes_sorted:
            tot=sum(per_class_next[cls].values())
            for tool,c in per_class_next[cls].most_common():
                f.write(f"{cls},{tool},{c},{c/tot:.4f}\n")
    print(f"\nCSV: {csvp}\nCSV: {distp}")

    # ---- verdict logic (printed; NOT written to claims/map) ----
    print("\n=== ROUTING-TABLE THESIS VERDICT (printed only) ===")
    print(f"failure-weighted per-class norm-entropy = {wHn:.3f} (0=deterministic route, 1=uniform/adaptive)")
    print(f"failure-weighted top1 route share       = {wtop1:.3f}")
    if wHn < 0.5 and wtop1 > 0.5:
        print("-> LOW per-class entropy + dominant single route = SUPPORTS routing-table characterization")
    elif wHn > 0.75:
        print("-> HIGH per-class entropy = REFUTES routing-table framing (next move looks adaptive)")
    else:
        print("-> MIXED")

if __name__=="__main__":
    main()


def robustness():
    """Bootstrap CI on the entropy-collapse statistic + a STRICT tool-name-only routing variant.
    Decisive Q: is per-class next-tool entropy RELIABLY below global (routing-table) or not (adaptive)?"""
    files = sorted(glob.glob(os.path.join(ROOT, "**", "*.jsonl"), recursive=True))
    failrows=[]  # (cls, next_tool)
    for path in files:
        calls=parse_session(path)
        if len(calls)<2: continue
        for i,c in enumerate(calls):
            if not c["is_error"]: continue
            cls=classify_error(c["name"],c["cmd"],c["text"])
            nxt=calls[i+1] if i+1<len(calls) else None
            nt=routing_tool(nxt) if nxt is not None else "(END)"
            failrows.append((cls,nt))
    big={cls for cls in Counter(c for c,_ in failrows) if Counter(c for c,_ in failrows)[cls]>=10}

    def collapse_stat(rows):
        g=Counter(nt for _,nt in rows)
        _,gHn,_=entropy_bits(g)
        per=defaultdict(Counter)
        for cls,nt in rows:
            if cls in big: per[cls][nt]+=1
        tot=0; wHn=0.0
        for cls,ctr in per.items():
            n=sum(ctr.values()); _,Hn,_=entropy_bits(ctr); wHn+=Hn*n; tot+=n
        wHn=wHn/tot if tot else 0.0
        return gHn - wHn   # positive => class collapses entropy (routing); <=0 => no collapse (adaptive)

    obs=collapse_stat(failrows)
    # bootstrap over failures
    B=2000; stats=[]
    n=len(failrows)
    for _ in range(B):
        samp=[failrows[random.randrange(n)] for _ in range(n)]
        stats.append(collapse_stat(samp))
    stats.sort()
    lo=stats[int(0.025*B)]; hi=stats[int(0.975*B)]
    frac_pos=sum(1 for s in stats if s>0)/B
    print("\n=== ROBUSTNESS: entropy-collapse (global_normH - per_class_normH), n>=10 classes ===")
    print(f"observed collapse = {obs:+.4f} bits-normalized (POSITIVE => routing collapses entropy)")
    print(f"bootstrap 95% CI  = [{lo:+.4f}, {hi:+.4f}]   P(collapse>0) = {frac_pos:.3f}")
    if hi < 0.05 and obs < 0.05:
        print("-> per-class entropy is NOT meaningfully below global: ADAPTIVE next-move, REFUTES routing-table thesis")
    elif lo > 0.10:
        print("-> per-class entropy reliably below global: SUPPORTS routing-table thesis")
    else:
        print("-> inconclusive collapse")

if __name__=="__main__":
    robustness()
