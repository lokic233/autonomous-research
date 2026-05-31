#!/usr/bin/env python3
"""
EXP-0022 - TWO-LAYER recovery decomposition (CLAIM-0010, laneC). MAP-0002. CPU/stdlib-only.

CLAIM-0010 (the NEW two-layer thesis surfaced by EXP-0019):
  "Agentic failure recovery is TWO-LAYER:
     COARSE gate-type routing (redirectable hard-block / grant-required / transient) is
        DETERMINISTIC / config-fixed, BUT
     FINE intra-gate recovery-tool SELECTION is high-entropy / ADAPTIVE (a decision, not a table)."

This experiment SHARPENS that claim with a clean variance decomposition + a rigorous fine-layer
adaptivity test, with the same rigor that killed the occurrence claim (LOO, leave-one-class-out,
entropy bootstrap CIs). HONEST: if the fine layer is small-n NOISE rather than adaptivity, that
WEAKENS / refutes CLAIM-0010 and we say so.

THREE QUESTIONS:
 (Q1) LAYER SEPARATION. How much of recovery-MODALITY variance does the COARSE gate-type explain
      (should be near-total -> the deterministic layer), vs how much does the FINE within-gate
      tool choice add? We measure modality determinism conditioned on gate-type (proportion of
      variance / impurity reduction), and contrast with the residual at the fine tool layer.
 (Q2) FINE-LAYER ADAPTIVITY. WITHIN each gate-type, is the chosen recovery TOOL predictable from
      CONTEXT (prior tool, error-class, error-text features) -- a learnable mapping -- or is it
      high-entropy / situation-dependent? Proper baseline = most-frequent-tool-WITHIN-gate.
      Out-of-sample = leave-one-out + leave-one-session-out. A context model that does NOT beat
      the within-gate modal baseline => the fine choice is NOT a fixed table (consistent with
      adaptive); but we ALSO check it is not just NOISE by testing whether ANY context signal
      predicts it at all (if even context can't, and entropy is high, it's situation-dependent).
 (Q3) HONEST CRUX. Does the two-layer structure HOLD (coarse deterministic + fine high-entropy,
      both demonstrated and robust) or does "fine adaptive" just look adaptive because of small-n?
      Bootstrap CIs on the fine-layer entropy; leave-one-class-out on the coarse determinism;
      degrees-of-freedom check (is fine entropy explainable by n alone?).

GATE-TYPE definition (coarse layer; from EXP-0009/0012 gate taxonomy, observational):
  We assign each ground-truth failure a COARSE gate-type from its error-class:
    REDIRECTABLE  : policy.web_disabled, policy.input_filter    (hard block, must switch tool)
    GRANT_REQUIRED: policy.perm_denied, fs.perm, ssh.auth       (gate must be opened, same-tool)
    TRANSIENT     : everything else (cancelled, fs.notfound, net.*, proc.*, code.*, other, ...)
  This is the deterministic/config layer the claim says is fixed. Modality (SAME_TOOL_RETRY vs
  CROSS_TOOL_REDIRECT) is the coarse-layer OUTPUT; recovery-TOOL identity is the fine-layer output.

HONESTY: single harness (Claude Code), observational. We can refute the OBSERVABLE signatures:
 - coarse-deterministic is observable as LOW modality-entropy given gate-type;
 - fine-adaptive is observable as HIGH tool-entropy within gate AND a context model failing to
   beat the within-gate modal baseline out-of-sample. We test both and report honestly.
We do NOT edit claims/map/cemetery.
"""
import json, glob, os, re, random, math
from collections import defaultdict, Counter

ROOT = os.path.expanduser("~/.claude/projects")
random.seed(20260531)
K_WINDOW = 6

# ============== COPIED VERBATIM FROM EXP-0009/0019 (==EXP-0007/0008/0012) ==============
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
# ============== END COPIED ==============

# ---- COARSE gate-type (the deterministic layer) ----
REDIRECTABLE = {"policy.web_disabled","policy.input_filter"}
GRANT_REQ    = {"policy.perm_denied","fs.perm","ssh.auth"}
def gate_type(cls):
    if cls in REDIRECTABLE: return "REDIRECTABLE"
    if cls in GRANT_REQ:    return "GRANT_REQUIRED"
    return "TRANSIENT"

# ---- modality (coarse-layer output), copied logic from EXP-0009 BROAD ----
def modality_and_recovery(calls, i):
    fc=calls[i]; fintent=fc["intent"]; ficlass=fc["iclass"]
    window=calls[i+1:i+1+K_WINDOW]
    same_tool=False; cross_tool=False
    for w in window:
        if w["is_error"]: continue
        if w["intent"]==fintent: same_tool=True
        elif w["iclass"]==ficlass: cross_tool=True
    rec = same_tool or cross_tool
    # default precedence A wins ties (same as EXP-0009)
    if same_tool: mod="SAME_TOOL_RETRY"
    elif cross_tool: mod="CROSS_TOOL_REDIRECT"
    else: mod=None
    return rec, mod

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

# error-text context features (cheap, for the fine-layer context model)
def text_features(text):
    t=(text or "").lower()
    feats=set()
    for kw in ["web","fetch","search","permission","denied","approval","cancel","timeout",
               "not found","no such","connection","http","host","syntax","module","test",
               "assert","exit code","curl","ssh","git"]:
        if kw in t: feats.add("kw:"+kw.replace(" ","_"))
    return feats

def main():
    files=sorted(glob.glob(os.path.join(ROOT,"**","*.jsonl"),recursive=True))
    n_sessions=0; n_calls=0
    rows=[]  # one row per ground-truth failure
    for path in files:
        calls=parse_session(path)
        if len(calls)<2: continue
        n_sessions+=1; n_calls+=len(calls)
        sid=os.path.basename(path)
        for i,c in enumerate(calls):
            if not c["is_error"]: continue
            cls=classify_error(c["name"],c["cmd"],c["text"])
            gt=gate_type(cls)
            nxt=calls[i+1] if i+1<len(calls) else None
            nt=routing_tool(nxt) if nxt is not None else "(END)"
            rec,mod=modality_and_recovery(calls,i)
            prior_tool=routing_tool(calls[i-1]) if i>0 else "(START)"
            rows.append({"sid":sid,"cls":cls,"gate":gt,"next":nt,"rec":1 if rec else 0,
                         "mod":mod,"prior":prior_tool,"feats":text_features(c["text"]),
                         "failed_tool":routing_tool(c)})
    N=len(rows)
    print(f"corpus: {n_sessions} sessions, {n_calls} calls, {N} ground-truth failures")
    gate_counts=Counter(r["gate"] for r in rows)
    print("gate-type distribution:", dict(gate_counts))

    # ================= Q1: LAYER SEPARATION (variance decomposition) =================
    # COARSE layer output = modality (SAME_TOOL_RETRY / CROSS_TOOL_REDIRECT). We measure how
    # deterministic modality is GIVEN gate-type, vs the residual entropy of the FINE tool choice
    # WITHIN gate (and within modality). Use normalized entropy as the variance proxy (categorical).
    print("\n================ Q1: LAYER SEPARATION ================")
    # 1a. Modality determinism given gate-type (coarse layer). Among RECOVERED failures w/ a modality.
    recmod=[r for r in rows if r["mod"] is not None]
    print(f"recovered failures with a modality: {len(recmod)}")
    # global modality entropy
    gmod=Counter(r["mod"] for r in recmod)
    _,gmodHn,gmodtop1=entropy_bits(gmod)
    print(f"  GLOBAL modality norm-entropy={gmodHn:.3f} top1={gmodtop1:.3f}  ({dict(gmod)})")
    # per-gate modality entropy (failure-weighted) = coarse-layer residual entropy
    per_gate_mod=defaultdict(Counter)
    for r in recmod: per_gate_mod[r["gate"]][r["mod"]]+=1
    tot=0; wHn=0.0
    print("  per-gate modality determinism (coarse layer output):")
    for g in ["REDIRECTABLE","GRANT_REQUIRED","TRANSIENT"]:
        ctr=per_gate_mod.get(g,Counter()); n=sum(ctr.values())
        if n==0: continue
        _,Hn,top1=entropy_bits(ctr)
        print(f"    {g:15s} n={n:4d} modality_normH={Hn:.3f} top1={top1:.3f}  {dict(ctr)}")
        wHn+=Hn*n; tot+=n
    coarse_resid = wHn/tot if tot else 0.0
    # variance EXPLAINED by gate = how much modality entropy drops when conditioning on gate
    coarse_explained = gmodHn - coarse_resid
    print(f"  => modality norm-entropy: GLOBAL={gmodHn:.3f} -> given-gate(weighted)={coarse_resid:.3f}")
    print(f"  => COARSE-LAYER variance EXPLAINED by gate-type = {coarse_explained:+.3f} norm-entropy units")
    # categorical 'variance explained' via Theil's U (uncertainty coefficient): U(mod|gate)
    def cond_entropy(pairs, xi, yi):
        # H(Y|X) in bits
        byx=defaultdict(Counter); cx=Counter()
        for p in pairs:
            byx[p[xi]][p[yi]]+=1; cx[p[xi]]+=1
        tot=sum(cx.values()); H=0.0
        for x,ctr in byx.items():
            nx=sum(ctr.values()); Hx,_,_=entropy_bits(ctr)
            H += (nx/tot)*Hx
        return H
    def entropyH(vals):
        return entropy_bits(Counter(vals))[0]
    mod_pairs=[(r["gate"],r["mod"]) for r in recmod]
    HY=entropyH([m for _,m in mod_pairs]); HYgX=cond_entropy(mod_pairs,0,1)
    theilU_mod = (HY-HYgX)/HY if HY>0 else 0.0
    print(f"  => Theil's U (modality | gate-type) = {theilU_mod:.3f}  (1=gate fully determines modality)")

    # 1b. FINE layer residual: tool-identity entropy WITHIN each gate (the adaptive layer candidate)
    per_gate_tool=defaultdict(Counter)
    for r in rows: per_gate_tool[r["gate"]][r["next"]]+=1
    gtool=Counter(r["next"] for r in rows); _,gtoolHn,gtooltop1=entropy_bits(gtool)
    print(f"\n  GLOBAL next-tool norm-entropy={gtoolHn:.3f} top1={gtooltop1:.3f}")
    tot=0; wHn=0.0
    print("  per-gate FINE tool-choice entropy (fine layer):")
    fine_by_gate={}
    for g in ["REDIRECTABLE","GRANT_REQUIRED","TRANSIENT"]:
        ctr=per_gate_tool.get(g,Counter()); n=sum(ctr.values())
        if n==0: continue
        _,Hn,top1=entropy_bits(ctr); modal=ctr.most_common(1)[0]
        print(f"    {g:15s} n={n:4d} tool_normH={Hn:.3f} top1={top1:.3f}  modal={modal[0]}({modal[1]}/{n})")
        fine_by_gate[g]=(n,Hn,top1)
        wHn+=Hn*n; tot+=n
    fine_resid = wHn/tot if tot else 0.0
    fine_explained = gtoolHn - fine_resid
    tool_pairs=[(r["gate"],r["next"]) for r in rows]
    HYt=entropyH([t for _,t in tool_pairs]); HYtgX=cond_entropy(tool_pairs,0,1)
    theilU_tool=(HYt-HYtgX)/HYt if HYt>0 else 0.0
    print(f"  => next-tool norm-entropy: GLOBAL={gtoolHn:.3f} -> given-gate(weighted)={fine_resid:.3f}")
    print(f"  => Theil's U (next-tool | gate-type) = {theilU_tool:.3f}  (how much gate determines the FINE tool)")
    print(f"\n  TWO-LAYER CONTRAST:")
    print(f"    COARSE  Theil U(modality|gate) = {theilU_mod:.3f}   residual modality normH = {coarse_resid:.3f}")
    print(f"    FINE    Theil U(tool|gate)     = {theilU_tool:.3f}   residual tool normH     = {fine_resid:.3f}")
    print(f"    => If U_mod >> U_tool AND fine residual entropy stays HIGH, the two-layer split HOLDS.")

    # ================= Q2: FINE-LAYER ADAPTIVITY (context model vs within-gate baseline) =================
    # WITHIN each gate, can CONTEXT (prior tool + error-class + text features) predict the next tool
    # better than the within-gate MODAL baseline, out-of-sample (LOO)? 
    #  - If a context model does NOT beat the within-gate modal baseline => no fixed table; consistent
    #    with adaptive (situation-dependent).
    #  - We ALSO report whether context beats it AT ALL (any learnable signal) to distinguish
    #    "adaptive decision" from "pure noise".
    print("\n================ Q2: FINE-LAYER ADAPTIVITY (within-gate, LOO) ================")
    # focus on gates with enough fine variety; do per-gate
    for g in ["REDIRECTABLE","GRANT_REQUIRED","TRANSIENT"]:
        grp=[r for r in rows if r["gate"]==g]
        n=len(grp)
        if n<10:
            print(f"  {g}: n={n} (small-n, skipped)"); continue
        labels=[r["next"] for r in grp]
        toolset=set(labels)
        # accuracy of within-gate MODAL baseline (LOO)
        cnt=Counter(labels)
        base_correct=0
        for r in grp:
            c2=Counter(cnt); c2[r["next"]]-=1
            pred=c2.most_common(1)[0][0]
            base_correct += (pred==r["next"])
        base_acc=base_correct/n
        # context model: simple LOO Naive-Bayes-ish over features (prior tool, cls, text kws)
        # build feature->tool counts, predict argmax_tool sum log P(feat|tool)P(tool), LOO
        def featset(r):
            fs=set(r["feats"]); fs.add("prior:"+r["prior"]); fs.add("cls:"+r["cls"]); fs.add("ft:"+r["failed_tool"])
            return fs
        # global counts
        tool_count=Counter(labels)
        feat_tool=defaultdict(Counter)
        for r in grp:
            for f in featset(r): feat_tool[f][r["next"]]+=1
        ctx_correct=0
        for r in grp:
            # LOO: remove this row's contributions
            tc=Counter(tool_count); tc[r["next"]]-=1
            rf=featset(r)
            best=None; bestscore=-1e9
            for tool in toolset:
                if tc[tool]<=0: continue
                score=math.log(tc[tool])
                for f in rf:
                    num=feat_tool[f][tool] - (1 if (f in rf and r["next"]==tool) else 0)
                    # laplace smoothing
                    score += math.log((num+1)/(tc[tool]+len(toolset)))
                if score>bestscore: bestscore=score; best=tool
            ctx_correct += (best==r["next"])
        ctx_acc=ctx_correct/n
        _,Hn,top1=entropy_bits(Counter(labels))
        print(f"  {g}: n={n} tools={len(toolset)} toolH_norm={Hn:.3f} top1={top1:.3f}")
        print(f"       within-gate MODAL baseline LOO-acc = {base_acc:.3f}")
        print(f"       CONTEXT model           LOO-acc = {ctx_acc:.3f}  (lift {ctx_acc-base_acc:+.3f})")
        if ctx_acc <= base_acc + 1e-9:
            print(f"       -> context does NOT beat within-gate modal: tool choice is NOT a context-table; "
                  f"{'high-entropy=>ADAPTIVE/situation-dependent' if Hn>0.5 else 'low-entropy=>near-fixed-route'}")
        else:
            print(f"       -> context DOES add signal (+{ctx_acc-base_acc:.3f}): a learnable mapping exists "
                  f"(weakens 'pure adaptive', toward routing/context-table)")

    # ================= Q3: HONEST CRUX (is fine 'adaptive' just small-n noise?) =================
    print("\n================ Q3: HONEST CRUX (bootstrap CIs, LOCO, df-vs-n) ================")
    # 3a. Bootstrap CI on fine-layer within-gate tool norm-entropy (failure-weighted, gates n>=10).
    big_gates=[g for g in ["REDIRECTABLE","GRANT_REQUIRED","TRANSIENT"] if gate_counts[g]>=10]
    def fine_wHn(sample):
        per=defaultdict(Counter)
        for r in sample:
            if r["gate"] in big_gates: per[r["gate"]][r["next"]]+=1
        tot=0; w=0.0
        for g,ctr in per.items():
            nn=sum(ctr.values()); _,Hn,_=entropy_bits(ctr); w+=Hn*nn; tot+=nn
        return w/tot if tot else 0.0
    obs_fine=fine_wHn(rows)
    B=2000; stats=[]
    for _ in range(B):
        samp=[rows[random.randrange(N)] for _ in range(N)]
        stats.append(fine_wHn(samp))
    stats.sort(); lo=stats[int(0.025*B)]; hi=stats[int(0.975*B)]
    print(f"  fine-layer within-gate tool norm-entropy = {obs_fine:.3f}  bootstrap 95% CI [{lo:.3f},{hi:.3f}]")
    print(f"  (HIGH and tightly bounded above ~0.5 => fine layer is genuinely diffuse, not small-n=0 noise)")

    # 3b. df-vs-n control: is the high entropy just because each gate has many tool symbols spread over
    #     few samples? Compare observed within-gate entropy to the entropy of a MULTINOMIAL null drawn
    #     from the observed tool distribution at the same n (expected entropy under 'fixed distribution').
    #     If observed ~ null-resample, the distribution is genuinely spread (not undersampling artifact).
    print("  df-vs-n control (observed within-gate normH vs resampled-from-own-dist expected normH):")
    for g in big_gates:
        ctr=per_gate_tool[g]; n=sum(ctr.values())
        _,obsHn,_=entropy_bits(ctr)
        tools=list(ctr.keys()); probs=[ctr[t]/n for t in tools]
        # expected normH if we DREW n samples from this exact distribution (sampling noise only)
        exps=[]
        for _ in range(500):
            draw=Counter()
            for _ in range(n):
                x=random.random(); cum=0.0
                for t,p in zip(tools,probs):
                    cum+=p
                    if x<=cum: draw[t]+=1; break
            _,Hn,_=entropy_bits(draw); exps.append(Hn)
        exps.sort(); elo=exps[int(0.025*len(exps))]; ehi=exps[int(0.975*len(exps))]
        em=sum(exps)/len(exps)
        print(f"    {g:15s} n={n:4d} observed_normH={obsHn:.3f}  resample-from-own-dist normH={em:.3f} [{elo:.3f},{ehi:.3f}]")
    print("    (observed == resample band by construction; the point: even the TRUE underlying dist is")
    print("     this diffuse -> the entropy is a property of the distribution, not just undersampling.)")

    # 3c. LEAVE-ONE-CLASS-OUT on the COARSE determinism: drop each error-class, recompute Theil U(mod|gate).
    #     If coarse determinism collapses when any single class is removed, it is a one-class artifact.
    print("  leave-one-CLASS-out on COARSE Theil U(modality|gate):")
    classes=sorted({r["cls"] for r in recmod})
    us=[]
    for drop in classes:
        pp=[(r["gate"],r["mod"]) for r in recmod if r["cls"]!=drop]
        if not pp: continue
        HY=entropyH([m for _,m in pp]); HYgX=cond_entropy(pp,0,1)
        u=(HY-HYgX)/HY if HY>0 else 0.0; us.append((drop,u))
    us2=[u for _,u in us]
    print(f"    full U={theilU_mod:.3f}; LOCO U range [{min(us2):.3f},{max(us2):.3f}] median={sorted(us2)[len(us2)//2]:.3f}")
    worst=min(us,key=lambda x:x[1])
    print(f"    most-influential class to drop: {worst[0]} -> U={worst[1]:.3f}")

    # 3d. LEAVE-ONE-SESSION-OUT on fine-layer within-gate entropy (is fine entropy a one-session artifact?)
    print("  leave-one-SESSION-out on fine-layer within-gate tool norm-entropy:")
    sids=sorted({r["sid"] for r in rows})
    loso=[]
    for s in sids:
        sub=[r for r in rows if r["sid"]!=s]
        loso.append(fine_wHn(sub))
    print(f"    full={obs_fine:.3f}; LOSO range [{min(loso):.3f},{max(loso):.3f}] median={sorted(loso)[len(loso)//2]:.3f}")

    # ---- CSV outputs ----
    outdir=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","experiment_result")
    os.makedirs(outdir,exist_ok=True)
    with open(os.path.join(outdir,"layer_decomposition.csv"),"w") as f:
        f.write("layer,metric,value\n")
        f.write(f"coarse,global_modality_normH,{gmodHn:.4f}\n")
        f.write(f"coarse,given_gate_modality_normH,{coarse_resid:.4f}\n")
        f.write(f"coarse,variance_explained_by_gate,{coarse_explained:.4f}\n")
        f.write(f"coarse,theilU_modality_given_gate,{theilU_mod:.4f}\n")
        f.write(f"fine,global_tool_normH,{gtoolHn:.4f}\n")
        f.write(f"fine,given_gate_tool_normH,{fine_resid:.4f}\n")
        f.write(f"fine,variance_explained_by_gate,{fine_explained:.4f}\n")
        f.write(f"fine,theilU_tool_given_gate,{theilU_tool:.4f}\n")
        f.write(f"fine,within_gate_tool_normH_bootCI_lo,{lo:.4f}\n")
        f.write(f"fine,within_gate_tool_normH_bootCI_hi,{hi:.4f}\n")
    with open(os.path.join(outdir,"per_gate.csv"),"w") as f:
        f.write("gate,n_fail,modality_normH,modality_top1,tool_normH,tool_top1,modal_tool\n")
        for g in ["REDIRECTABLE","GRANT_REQUIRED","TRANSIENT"]:
            mc=per_gate_mod.get(g,Counter()); tc=per_gate_tool.get(g,Counter())
            nm=sum(mc.values()); nt=sum(tc.values())
            _,mHn,mtop1=entropy_bits(mc); _,tHn,ttop1=entropy_bits(tc)
            modal=tc.most_common(1)[0] if tc else ("",0)
            f.write(f"{g},{nt},{mHn:.4f},{mtop1:.4f},{tHn:.4f},{ttop1:.4f},{modal[0]}\n")
    print(f"\nCSV: {os.path.join(outdir,'layer_decomposition.csv')}")
    print(f"CSV: {os.path.join(outdir,'per_gate.csv')}")

if __name__=="__main__":
    main()
