#!/usr/bin/env python3
"""
EXP-0007 — Real agent-trace FAILURE-CLASS -> RECOVERY-COMPETENCE census (CLAIM-0008).
Domain: MAP-0002 (Agent failure attribution & recovery). CPU-only, stdlib-only.

QUESTION (CLAIM-0008): Does the ERROR-CLASS of a failed tool call PREDICT whether the
agent RECOVERS (a same-intent retry later succeeds in the same session)?

DATA: real Claude Code agent sessions in ~/.claude/projects. Ground-truth failures = tool_result is_error.

METHOD:
  1. Parse each session jsonl in order; join tool_result -> tool_use by tool_use_id.
  2. TAXONOMY: classify each FAILED tool call into an error-class (regex on content + tool + command).
  3. RECOVERY LABEL: scan forward for next SAME-INTENT call (same tool; for Bash same head command,
     for file tools same file_path). RECOVERED=1 iff a later same-intent call succeeds; else 0.
  4. PREDICTIVENESS vs NULL: global recovery p0 = null baseline; per-class rate p_c;
     Cramer's V; permutation test (shuffle labels, chi2); honest leave-one-out Brier improvement.
HONESTY: if per-class indistinguishable from p0 (high perm-p, tiny V, ~0 Brier gain) -> class does
NOT predict recovery -> WEAKENS/refutes CLAIM-0008.
"""
import json, glob, os, re, random, math
from collections import defaultdict

ROOT = os.path.expanduser("~/.claude/projects")
random.seed(1234)

def classify_error(tool_name, cmd, text):
    t=(text or "").lower()
    # ---- policy / harness blocks (semantically PERMANENT failures) ----
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
                                  "is_error":bool(b.get("is_error")),"text":block_text(b)})
    return calls

def label_recovery(calls, idx):
    intent=calls[idx]["intent"]
    for j in range(idx+1,len(calls)):
        if calls[j]["intent"]==intent and not calls[j]["is_error"]:
            return 1
    return 0

files=sorted(glob.glob(os.path.join(ROOT,"**","*.jsonl"),recursive=True))
records=[]; n_sessions=0; n_calls_total=0; n_fail=0
for path in files:
    try: calls=parse_session(path)
    except Exception: continue
    if len(calls)<2: continue
    n_sessions+=1; n_calls_total+=len(calls)
    for i,call in enumerate(calls):
        if call["is_error"]:
            n_fail+=1
            records.append((classify_error(call["name"],call["cmd"],call["text"]), label_recovery(calls,i)))

print(f"sessions={n_sessions} total_tool_calls={n_calls_total} failures={n_fail}")

by_class=defaultdict(lambda:[0,0])
for ec,rec in records:
    by_class[ec][1]+=1; by_class[ec][0]+=rec
N=len(records); R=sum(r for _,r in records)
p0=R/N if N else 0.0
classes=sorted(by_class.keys())
obs=[[by_class[ec][0], by_class[ec][1]-by_class[ec][0]] for ec in classes]

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

chi2_obs=chi2_table(obs); k=len(classes)
cramers_v=math.sqrt(chi2_obs/N) if N else 0.0  # 2-col table -> V=sqrt(chi2/N)

labels=[r for _,r in records]; ecs=[e for e,_ in records]
B=5000; ge=0
for _ in range(B):
    random.shuffle(labels)
    tab=defaultdict(lambda:[0,0])
    for ec,lab in zip(ecs,labels):
        tab[ec][1]+=1; tab[ec][0]+=lab
    if chi2_table([[tab[ec][0],tab[ec][1]-tab[ec][0]] for ec in classes])>=chi2_obs-1e-9: ge+=1
perm_p=(ge+1)/(B+1)

brier_null=sum((p0-r)**2 for _,r in records)/N
pc={ec:(by_class[ec][0]/by_class[ec][1]) for ec in classes}
brier_class=sum((pc[ec]-r)**2 for ec,r in records)/N
brier_loo=0.0
for ec,r in records:
    rec,tot=by_class[ec]
    p_loo=(rec-r)/(tot-1) if tot>1 else p0
    brier_loo+=(p_loo-r)**2
brier_loo/=N

print("\n=== per-class recovery rate vs NULL p0={:.3f} ===".format(p0))
print("| class | n | recovered | rate | delta_vs_null |")
print("|---|---|---|---|---|")
for ec in sorted(classes,key=lambda e:-by_class[e][1]):
    rec,tot=by_class[ec]; print(f"| {ec} | {tot} | {rec} | {rec/tot:.3f} | {rec/tot-p0:+.3f} |")
print(f"\nN_failures={N}  global_recovery(p0)={p0:.4f}")
print(f"chi2={chi2_obs:.3f}  df={k-1}  CramersV={cramers_v:.4f}")
print(f"permutation_p = {perm_p:.4f}  (B={B})")
print(f"Brier(null const p0) = {brier_null:.4f}")
print(f"Brier(class in-sample) = {brier_class:.4f}  improve={brier_null-brier_class:+.4f}")
print(f"Brier(class LOO HONEST) = {brier_loo:.4f}  improve={brier_null-brier_loo:+.4f}")

# ---------- ROBUSTNESS 1: collapse rare classes (n<10) into 'rare', re-test ----------
MIN_N=10
def collapse(ec): 
    rec,tot=by_class[ec]
    return ec if tot>=MIN_N else "rare"
rec2=[(collapse(ec),r) for ec,r in records]
bc2=defaultdict(lambda:[0,0])
for ec,r in rec2: bc2[ec][1]+=1; bc2[ec][0]+=r
cl2=sorted(bc2.keys())
obs2=[[bc2[ec][0],bc2[ec][1]-bc2[ec][0]] for ec in cl2]
chi2_2=chi2_table(obs2); v2=math.sqrt(chi2_2/N) if N else 0.0
lab2=[r for _,r in rec2]; e2=[e for e,_ in rec2]; ge2=0
for _ in range(B):
    random.shuffle(lab2)
    tb=defaultdict(lambda:[0,0])
    for ec,l in zip(e2,lab2): tb[ec][1]+=1; tb[ec][0]+=l
    if chi2_table([[tb[ec][0],tb[ec][1]-tb[ec][0]] for ec in cl2])>=chi2_2-1e-9: ge2+=1
perm_p2=(ge2+1)/(B+1)

# ---------- ROBUSTNESS 2: theory-driven 2-class split PERMANENT vs TRANSIENT ----------
PERMANENT={"policy.web_disabled","policy.input_filter","policy.perm_denied","cancelled"}
def perm_class(ec): return "permanent" if ec in PERMANENT else "transient"
recP=[(perm_class(ec),r) for ec,r in records]
bcP=defaultdict(lambda:[0,0])
for ec,r in recP: bcP[ec][1]+=1; bcP[ec][0]+=r
clP=sorted(bcP.keys())
obsP=[[bcP[ec][0],bcP[ec][1]-bcP[ec][0]] for ec in clP]
chi2_P=chi2_table(obsP); vP=math.sqrt(chi2_P/N) if N else 0.0
labP=[r for _,r in recP]; eP=[e for e,_ in recP]; geP=0
for _ in range(B):
    random.shuffle(labP)
    tb=defaultdict(lambda:[0,0])
    for ec,l in zip(eP,labP): tb[ec][1]+=1; tb[ec][0]+=l
    if chi2_table([[tb[ec][0],tb[ec][1]-tb[ec][0]] for ec in clP])>=chi2_P-1e-9: geP+=1
perm_pP=(geP+1)/(B+1)

print("\n=== ROBUSTNESS 1: rare(n<{}) collapsed ===".format(MIN_N))
for ec in sorted(cl2,key=lambda e:-bc2[e][1]):
    rec,tot=bc2[ec]; print(f"  {ec:22s} n={tot:3d} rec={rec:3d} rate={rec/tot:.3f} ({rec/tot-p0:+.3f})")
print(f"  chi2={chi2_2:.3f} df={len(cl2)-1} CramersV={v2:.4f} perm_p={perm_p2:.4f}")
print("\n=== ROBUSTNESS 2: theory split PERMANENT vs TRANSIENT ===")
for ec in clP:
    rec,tot=bcP[ec]; print(f"  {ec:12s} n={tot:3d} rec={rec:3d} rate={rec/tot:.3f} ({rec/tot-p0:+.3f})")
print(f"  chi2={chi2_P:.3f} df={len(clP)-1} CramersV(phi)={vP:.4f} perm_p={perm_pP:.4f}")

csv_path=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","experiment_result","per_class_recovery.csv"))
os.makedirs(os.path.dirname(csv_path),exist_ok=True)
with open(csv_path,"w") as f:
    f.write("class,n,recovered,recovery_rate,delta_vs_null\n")
    for ec in sorted(classes,key=lambda e:-by_class[e][1]):
        rec,tot=by_class[ec]; f.write(f"{ec},{tot},{rec},{rec/tot:.4f},{rec/tot-p0:+.4f}\n")
    f.write(f"# N={N},p0={p0:.4f},chi2={chi2_obs:.4f},df={k-1},CramersV={cramers_v:.4f},perm_p={perm_p:.4f},brier_null={brier_null:.4f},brier_loo={brier_loo:.4f},brier_improve_loo={brier_null-brier_loo:+.4f}\n")
    f.write(f"# ROBUST1_rareCollapsed: chi2={chi2_2:.4f},df={len(cl2)-1},CramersV={v2:.4f},perm_p={perm_p2:.4f}\n")
    f.write(f"# ROBUST2_perm_vs_transient: chi2={chi2_P:.4f},df={len(clP)-1},phi={vP:.4f},perm_p={perm_pP:.4f}\n")
print("wrote",csv_path)
