#!/usr/bin/env python3
"""
EXP-0060 — Agent KV Eviction Policy Benchmark vs Belady (PROJ-0014 / CLAIM-0025).
Pure stdlib, Mac CPU. Executes the FROZEN PRE_REGISTRATION.md (LOCKED-TS 2026-06-01T22:42:08Z).

POLICY-COMPARISON BENCHMARK (committee FIX-1 reframe), NOT a predictor. On the SAME agent KV touch-traces as EXP-0057,
how much of the LRU->Belady recompute-mass GAP do CLASSICAL frequency-aware eviction policies capture WITHOUT future
knowledge, AT MATCHED CACHE RESIDENCY?

REUSES EXP-0057 (experiments/2026-06-01/EXP-0057/impl/reuse_distance_census.py) VERBATIM: parse_cc_session,
parse_codex_session, load_corpus, extract_paths, file_class, build_units (reuse-unit + far-share), gini, det_hash, and
the cache-sim touch-stream + recompute-mass accounting (size(p)=(len(args_str)+len(result))/4). EXTENDS the RE-A3 cache
sim with policies: SGLang-LFU, SGLang-SLRU, ARC (Megiddo-Modha), LRU-K (K=2), static-pin+LRU(N in 2/3/5), keeping LRU
(baseline) and Belady-oracle (upper bound). Adds captured-fraction, matched-residency (pinned blocks charged against C),
session-clustered 2000x bootstrap CI, BH+Bonferroni over the 15 static-pin cells, HHI flag. CC primary; Codex reported
honestly (FIX-4) even when not bimodal.
"""
import json, glob, os, re, math, statistics, random, hashlib
from collections import defaultdict

# ---------------- FROZEN CONSTANTS (from pre-registration) ----------------
SEED            = 20260601
CHARS_PER_TOK   = 4.0
MIN_TRIALS      = 8
FAR_TOK         = 8192.0
NEAR_TOK        = 512.0
B0_FAR_FLOOR    = 0.15      # RE-B0 far-share floor
B0_BELADY_FLOOR = 0.05      # RE-B0 Belady-saves floor (max over caps)
CAP_FRACS       = [0.10, 0.20, 0.30, 0.50, 0.70]   # FROZEN 5 capacities (fracs of per-session distinct-path WS)
PIN_NS          = [2, 3, 5]
SLRU_PROTECTED  = 0.8       # protected segment = floor(0.8*C)
LRUK_K          = 2
NBOOT           = 2000
B1_CAPTURE_PASS = 0.50      # RE-B1 captured-fraction threshold
B1_NCAP_PASS    = 3         # >= 3 of 5 capacities
HHI_FLAG        = 0.20
ALPHA           = 0.05
LOCKED_TS       = "2026-06-01T22:42:08Z"

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

# ============ PARSERS / LOADERS / EXTRACTION (VERBATIM from EXP-0057) ============
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

def extract_paths(call):
    paths=[]
    inp=call["inp"]
    if isinstance(inp, dict):
        for k in ("file_path","path","notebook_path","filePath"):
            v=inp.get(k)
            if isinstance(v,str) and v.strip(): paths.append(v.strip())
        cmd=inp.get("command")
        if isinstance(cmd,str) and cmd:
            for m in PATH_RE.findall(cmd): paths.append(m)
    if call["name"] in SHELL_TOOLS or call["name"] in ("apply_patch",):
        for m in PATH_RE.findall(call["args_str"]): paths.append(m)
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

def gini(values):
    vs=sorted(v for v in values if v>0)
    n=len(vs)
    if n==0: return None
    cum=0.0; s=sum(vs)
    if s<=0: return None
    for i,v in enumerate(vs): cum+=(i+1)*v
    return (2*cum)/(n*s) - (n+1)/n

# ---- build_units (VERBATIM from EXP-0057): reuse units + gap_to_next for RE-B0 far-share ----
def build_units(sessions):
    recs=[]; all_reuse_gaps=[]
    for sname, calls in sessions.items():
        call_paths=[extract_paths(c) for c in calls]
        touches=[]
        for ci,c in enumerate(calls):
            for p in call_paths[ci]:
                touches.append((ci, p, c["start_pos"], c["end_pos"], c))
        by_path=defaultdict(list)
        for t in touches: by_path[t[1]].append(t)
        for p, tl in by_path.items():
            if len(tl)<2: continue
            for i in range(len(tl)-1):
                ci, path, sp, ep, c = tl[i]
                nci, npath, nsp, nep, nc = tl[i+1]
                gap_to_next = max(0.0,(nsp - ep)/CHARS_PER_TOK)
                recs.append(dict(sess=sname, path=path, gap_to_next=gap_to_next,
                                 y=1 if gap_to_next>FAR_TOK else 0))
                all_reuse_gaps.append(gap_to_next)
    return recs, all_reuse_gaps

# ============ CACHE-SIM TOUCH STREAM (EXP-0057 accounting, EXTENDED) ============
def session_touches(calls):
    """Ordered (path, size_tok) touch stream + next-touch index array (for Belady). size = EXP-0057 recompute mass."""
    touches=[]
    for ci,c in enumerate(calls):
        sz=(len(c["args_str"])+len(c["result"]))/CHARS_PER_TOK
        for p in extract_paths(c):
            touches.append((p, sz))
    n=len(touches)
    # next occurrence index per touch position (math.inf if never again) — VERBATIM logic from EXP-0057 re_a3
    future=defaultdict(list)
    for k,(p,sz) in enumerate(touches): future[p].append(k)
    nextpos=[math.inf]*n
    seen=defaultdict(int)
    for k,(p,sz) in enumerate(touches):
        occ=future[p]; idx=seen[p]
        nextpos[k]=occ[idx+1] if idx+1<len(occ) else math.inf
        seen[p]+=1
    return touches, nextpos

# ---------------- POLICY SIMULATORS (history-only unless 'belady'). Return recompute mass. ----------------
def sim_lru(touches, nextpos, C):
    cache={}; rc=0.0
    for k,(p,sz) in enumerate(touches):
        if p in cache: cache[p]=k
        else:
            rc+=sz
            if len(cache)>=C: del cache[min(cache, key=cache.get)]
            cache[p]=k
    return rc

def sim_belady(touches, nextpos, C):
    cache={}; rc=0.0   # path -> next-touch idx
    for k,(p,sz) in enumerate(touches):
        if p in cache: cache[p]=nextpos[k]
        else:
            rc+=sz
            if len(cache)>=C: del cache[max(cache, key=cache.get)]  # farthest next-touch (inf=never -> evict)
            cache[p]=nextpos[k]
    return rc

def sim_lfu(touches, nextpos, C):
    cache={}; rc=0.0   # path -> [freq, last_k]
    for k,(p,sz) in enumerate(touches):
        if p in cache:
            cache[p][0]+=1; cache[p][1]=k
        else:
            rc+=sz
            if len(cache)>=C:
                ev=min(cache, key=lambda q:(cache[q][0], cache[q][1]))  # min freq, tie-break LRU(oldest last)
                del cache[ev]
            cache[p]=[1,k]
    return rc

def sim_slru(touches, nextpos, C):
    protected_cap=int(math.floor(SLRU_PROTECTED*C))
    prot={}; prob={}; rc=0.0   # insertion-ordered dicts: first key = LRU
    def touch_mru(d,p):
        if p in d: del d[p]
        d[p]=True
    for k,(p,sz) in enumerate(touches):
        if p in prot:
            touch_mru(prot,p)
        elif p in prob:
            del prob[p]                          # promote on 2nd hit
            touch_mru(prot,p)
            if len(prot)>protected_cap and prot:
                old=next(iter(prot)); del prot[old]; touch_mru(prob,old)   # demote LRU of protected
        else:
            rc+=sz
            while len(prot)+len(prob)>=C and (prob or prot):
                if prob: old=next(iter(prob)); del prob[old]
                else: old=next(iter(prot)); del prot[old]
            touch_mru(prob,p)
    return rc

def sim_lruk(touches, nextpos, C, K=LRUK_K):
    cache=set(); rc=0.0
    hist=defaultdict(list)   # path -> last-K reference step indices (RETAINED across evictions)
    last=defaultdict(lambda:-1)
    for k,(p,sz) in enumerate(touches):
        h=hist[p]; h.append(k)
        if len(h)>K: del h[0]
        last[p]=k
        if p in cache:
            continue
        rc+=sz
        if len(cache)>=C:
            # victim = max backward-K-distance; under-K (len<K) => +inf, tie-break oldest last single ref
            best=None; best_key=None
            for q in cache:
                hq=hist[q]
                if len(hq)>=K: bk=k - hq[-K]; key=(0, bk)      # finite bk-dist
                else:          key=(1, k - last[q])            # +inf class, tie-break LRU among under-K
                if best_key is None or key>best_key:
                    best_key=key; best=q
            cache.discard(best)
        cache.add(p)
    return rc

def _arc_replace(T1,T2,B1,B2,p,x_in_b2):
    if T1 and ((x_in_b2 and len(T1)==p) or (len(T1) > p)):
        old=T1.pop(0); B1.append(old)
    elif T2:
        old=T2.pop(0); B2.append(old)
    elif T1:
        old=T1.pop(0); B1.append(old)

def sim_arc(touches, nextpos, C):
    T1=[];T2=[];B1=[];B2=[]; p=0; rc=0.0; c=C
    s1=set();s2=set();gb1=set();gb2=set()   # membership mirrors for O(1) lookups
    for k,(path,sz) in enumerate(touches):
        if path in s1:
            T1.remove(path); s1.discard(path); T2.append(path); s2.add(path)
        elif path in s2:
            T2.remove(path); T2.append(path)
        elif path in gb1:
            rc+=sz
            p=min(c, p + max(len(B2)//max(1,len(B1)),1))
            _arc_replace(T1,T2,B1,B2,p,False); _resync(s1,s2,gb1,gb2,T1,T2,B1,B2)
            B1.remove(path); gb1.discard(path); T2.append(path); s2.add(path)
        elif path in gb2:
            rc+=sz
            p=max(0, p - max(len(B1)//max(1,len(B2)),1))
            _arc_replace(T1,T2,B1,B2,p,True); _resync(s1,s2,gb1,gb2,T1,T2,B1,B2)
            B2.remove(path); gb2.discard(path); T2.append(path); s2.add(path)
        else:
            rc+=sz
            if len(T1)+len(B1)==c:
                if len(T1)<c:
                    B1.pop(0); _arc_replace(T1,T2,B1,B2,p,False)
                else:
                    T1.pop(0)
            else:
                total=len(T1)+len(T2)+len(B1)+len(B2)
                if total>=c:
                    if total==2*c and B2: B2.pop(0)
                    _arc_replace(T1,T2,B1,B2,p,False)
            T1.append(path)
        # resync membership sets (cheap; lists are small ~C)
        s1=set(T1); s2=set(T2); gb1=set(B1); gb2=set(B2)
    return rc

def _resync(s1,s2,gb1,gb2,T1,T2,B1,B2):
    s1.clear(); s1.update(T1); s2.clear(); s2.update(T2)
    gb1.clear(); gb1.update(B1); gb2.clear(); gb2.update(B2)

def sim_pin(touches, nextpos, C, N):
    """static-pin+LRU: pin = top-N by CAUSAL freq_so_far; pinned charged against C (FIX-5 matched residency)."""
    cache={}; rc=0.0           # path -> last_k (resident)
    freq=defaultdict(int)
    pin=set();
    for k,(p,sz) in enumerate(touches):
        freq[p]+=1
        # incremental top-N maintenance (monotonic increments, strict-> incumbent keeps ties)
        if p not in pin:
            if len(pin)<N: pin.add(p)
            else:
                m=min(pin, key=lambda q:freq[q])
                if freq[p]>freq[m]: pin.discard(m); pin.add(p)
        if p in cache:
            cache[p]=k; continue
        rc+=sz
        if len(cache)>=C:
            nonpin=[q for q in cache if q not in pin]
            if nonpin: ev=min(nonpin, key=lambda q:cache[q])      # LRU among non-pinned
            else:      ev=min(cache, key=cache.get)                # all pinned (N>=C degenerate) -> LRU among pinned
            del cache[ev]
        cache[p]=k
    return rc

POLICIES = ["lru","belady","lfu","slru","arc","lruk","pin2","pin3","pin5"]
CHEAP    = ["lfu","slru","arc","lruk","pin2","pin3","pin5"]   # candidates for RE-B1 "best cheap policy"
PIN_CELLS= ["pin2","pin3","pin5"]                              # FIX-3 free-parameter family (15 cells with caps)

def run_policy(name, touches, nextpos, C):
    if name=="lru":    return sim_lru(touches,nextpos,C)
    if name=="belady": return sim_belady(touches,nextpos,C)
    if name=="lfu":    return sim_lfu(touches,nextpos,C)
    if name=="slru":   return sim_slru(touches,nextpos,C)
    if name=="arc":    return sim_arc(touches,nextpos,C)
    if name=="lruk":   return sim_lruk(touches,nextpos,C)
    if name=="pin2":   return sim_pin(touches,nextpos,C,2)
    if name=="pin3":   return sim_pin(touches,nextpos,C,3)
    if name=="pin5":   return sim_pin(touches,nextpos,C,5)
    raise ValueError(name)

# ---------------- benchmark over a corpus ----------------
def benchmark(sessions):
    """Return per-session recompute mass: per_sess[sess][frac][policy] = mass; + cap C used per (sess,frac)."""
    per_sess={}; cap_used={}
    skeys=sorted(sessions.keys())
    for sname in skeys:
        calls=sessions[sname]
        touches, nextpos = session_touches(calls)
        if not touches: continue
        ndist=len(set(p for p,_ in touches))
        per_sess[sname]={}; cap_used[sname]={}
        for frac in CAP_FRACS:
            C=max(1,int(math.ceil(frac*ndist)))
            cap_used[sname][frac]=C
            d={}
            for pol in POLICIES:
                d[pol]=run_policy(pol, touches, nextpos, C)
            per_sess[sname][frac]=d
    return per_sess, cap_used

def pooled_mass(per_sess, frac, pol, sess_subset=None):
    keys=sess_subset if sess_subset is not None else per_sess.keys()
    return sum(per_sess[s][frac][pol] for s in keys if frac in per_sess[s])

def captured_fraction(lru, pol, bel):
    gap=lru-bel
    if gap<=0: return None
    return (lru-pol)/gap

def corpus_results(per_sess):
    """Pooled recompute + captured-fraction matrix + bootstrap CIs + p-values + HHI."""
    skeys=sorted(per_sess.keys())
    out={"n_sessions":len(skeys),"per_capacity":{}}
    # point estimates
    for frac in CAP_FRACS:
        lru=pooled_mass(per_sess,frac,"lru"); bel=pooled_mass(per_sess,frac,"belady")
        gap=lru-bel
        belady_saved = (gap/lru) if lru>0 else None
        cell={"cap_frac":frac,"recompute":{}, "captured":{}}
        for pol in POLICIES:
            cell["recompute"][pol]=round(pooled_mass(per_sess,frac,pol),1)
        for pol in CHEAP:
            cell["captured"][pol]=captured_fraction(lru, pooled_mass(per_sess,frac,pol), bel)
        cell["LRU_minus_Belady"]=round(gap,1); cell["belady_saved_frac"]=belady_saved
        out["per_capacity"][frac]=cell
    # bootstrap captured-fraction (session-clustered)
    boot={frac:{pol:[] for pol in CHEAP} for frac in CAP_FRACS}
    n=len(skeys)
    for _ in range(NBOOT):
        pick=[skeys[random.randrange(n)] for _ in range(n)]
        for frac in CAP_FRACS:
            lru=pooled_mass(per_sess,frac,"lru",pick); bel=pooled_mass(per_sess,frac,"belady",pick)
            gap=lru-bel
            for pol in CHEAP:
                cf=None if gap<=0 else (lru-pooled_mass(per_sess,frac,pol,pick))/gap
                if cf is not None: boot[frac][pol].append(cf)
    for frac in CAP_FRACS:
        ci={}; pval={}
        for pol in CHEAP:
            vals=sorted(boot[frac][pol])
            if vals:
                lb=vals[int(0.025*len(vals))]; ub=vals[int(0.975*len(vals))]
                # one-sided p for H0: captured <= 0.50
                p=sum(1 for v in vals if v<=B1_CAPTURE_PASS)/len(vals)
                ci[pol]=[round(lb,4),round(ub,4)]; pval[pol]=round(p,5)
            else:
                ci[pol]=[None,None]; pval[pol]=None
        out["per_capacity"][frac]["captured_CI95"]=ci
        out["per_capacity"][frac]["pval_H0_le_0.50"]=pval
    # HHI over LRU recompute mass by session (use frac=0.30 mid-capacity as reference; report all)
    out["HHI_by_cap"]={}
    for frac in CAP_FRACS:
        tot=pooled_mass(per_sess,frac,"lru")
        if tot>0:
            hhi=sum((per_sess[s][frac]["lru"]/tot)**2 for s in skeys if frac in per_sess[s])
        else: hhi=None
        out["HHI_by_cap"][frac]={"HHI":hhi,"flag":(hhi is not None and hhi>HHI_FLAG)}
    return out

def bh_bonferroni(pvals):
    """pvals: dict cell->p. Return per-cell BH-adjusted significance + Bonferroni at ALPHA. cell sig = reject H0(captured<=0.50)."""
    items=[(k,v) for k,v in pvals.items() if v is not None]
    m=len(items)
    res={}
    if m==0: return res
    # Bonferroni
    for k,v in items: res[k]={"p":v,"bonferroni_sig":(v<=ALPHA/m)}
    # Benjamini-Hochberg
    order=sorted(items, key=lambda kv:kv[1])
    bh_thresh=0.0; passing=set()
    for i,(k,v) in enumerate(order, start=1):
        if v<= (i/m)*ALPHA:
            bh_thresh=(i/m)*ALPHA
    for k,v in items:
        res[k]["bh_sig"]=(v<=bh_thresh)
    return res

# ---------------- main ----------------
def main():
    base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir=os.path.join(base,"results"); os.makedirs(rdir, exist_ok=True)
    print(f"[EXP-0060] locked {LOCKED_TS}  seed {SEED}  caps {CAP_FRACS}  policies {POLICIES}")
    print("Loading corpora...")
    corpora={"cc":load_corpus("cc"), "codex":load_corpus("codex")}
    bundle={"locked_ts":LOCKED_TS,"seed":SEED,"frozen":{
        "CAP_FRACS":CAP_FRACS,"PIN_NS":PIN_NS,"SLRU_PROTECTED":SLRU_PROTECTED,"LRUK_K":LRUK_K,
        "FAR_TOK":FAR_TOK,"B0_FAR_FLOOR":B0_FAR_FLOOR,"B0_BELADY_FLOOR":B0_BELADY_FLOOR,
        "B1_CAPTURE_PASS":B1_CAPTURE_PASS,"B1_NCAP_PASS":B1_NCAP_PASS,"NBOOT":NBOOT,"HHI_FLAG":HHI_FLAG,
        "POLICIES":POLICIES,"CHEAP":CHEAP,"PIN_CELLS":PIN_CELLS},"corpora":{}}

    for cname, sess in corpora.items():
        print(f"\n===== {cname}: {len(sess)} sessions (>= {MIN_TRIALS} calls) =====")
        recs, allgaps = build_units(sess)
        nU=len(recs)
        far_share = (sum(1 for g in allgaps if g>FAR_TOK)/nU) if nU else None
        near_share= (sum(1 for g in allgaps if g<NEAR_TOK)/nU) if nU else None
        med = statistics.median(allgaps) if allgaps else None
        print(f"   reuse units={nU}  far_share={far_share}  near_share={near_share}")
        per_sess, cap_used = benchmark(sess)
        cres=corpus_results(per_sess)
        belady_saves=[cres["per_capacity"][f]["belady_saved_frac"] for f in CAP_FRACS]
        belady_max=max([b for b in belady_saves if b is not None], default=None)
        # RE-B0 (CC primary; computed for both, gates only CC)
        b0_pass=(far_share is not None and far_share>=B0_FAR_FLOOR and belady_max is not None and belady_max>=B0_BELADY_FLOOR)
        # RE-B1 best cheap policy captured >= 0.50 at >= 3 of 5 caps
        capt_by_pol={pol:[cres["per_capacity"][f]["captured"][pol] for f in CAP_FRACS] for pol in CHEAP}
        b1_pol={}
        for pol in CHEAP:
            ncap=sum(1 for v in capt_by_pol[pol] if v is not None and v>=B1_CAPTURE_PASS)
            b1_pol[pol]={"captured_by_cap":[None if v is None else round(v,4) for v in capt_by_pol[pol]],
                         "n_caps_ge_0.50":ncap,"pass":ncap>=B1_NCAP_PASS}
        best_pol=max(CHEAP, key=lambda p:b1_pol[p]["n_caps_ge_0.50"])
        b1_pass=any(b1_pol[p]["pass"] for p in CHEAP)
        # FIX-3 BH/Bonferroni over the 15 static-pin cells
        pin_pvals={}
        for f in CAP_FRACS:
            for pol in PIN_CELLS:
                pv=cres["per_capacity"][f]["pval_H0_le_0.50"].get(pol)
                pin_pvals[f"{pol}@{f}"]=pv
        pin_correction=bh_bonferroni(pin_pvals)
        # broader all-cheap x cap correction for context
        all_pvals={f"{pol}@{f}":cres["per_capacity"][f]["pval_H0_le_0.50"].get(pol)
                   for f in CAP_FRACS for pol in CHEAP}
        all_correction=bh_bonferroni(all_pvals)
        # FIX-2 ARC-vs-custom verdict
        arc_caps=b1_pol["arc"]["n_caps_ge_0.50"]; lruk_caps=b1_pol["lruk"]["n_caps_ge_0.50"]
        bestpin=max(PIN_CELLS, key=lambda p:b1_pol[p]["n_caps_ge_0.50"])
        pin_caps=b1_pol[bestpin]["n_caps_ge_0.50"]
        fix2={"arc_n_caps":arc_caps,"lruk_n_caps":lruk_caps,"best_pin":bestpin,"best_pin_n_caps":pin_caps,
              "custom_obsolete":(max(arc_caps,lruk_caps)>=pin_caps)}
        hhi_flag=any(cres["HHI_by_cap"][f]["flag"] for f in CAP_FRACS)
        cres.update({"reuse_units":nU,"far_share":far_share,"near_share":near_share,"median_gap_tok":med,
                     "belady_saved_by_cap":belady_saves,"belady_saved_max":belady_max,
                     "RE_B0_PASS":b0_pass,"RE_B1":{"by_policy":b1_pol,"best_policy":best_pol,"PASS":b1_pass},
                     "FIX2_arc_vs_custom":fix2,"FIX3_pin_correction":pin_correction,
                     "FIX3_all_correction":all_correction,"HHI_flag_any":hhi_flag,
                     "cap_used_example":{f:cap_used[next(iter(cap_used))][f] for f in CAP_FRACS} if cap_used else {}})
        bundle["corpora"][cname]=cres
        print(f"   RE-B0 far_share={far_share} belady_max={belady_max} -> PASS={b0_pass}")
        print(f"   captured-fraction by cap (best cheap policy '{best_pol}'): {b1_pol[best_pol]['captured_by_cap']}")
        for pol in CHEAP:
            print(f"      {pol:6s} captured={b1_pol[pol]['captured_by_cap']} ncaps>=0.5={b1_pol[pol]['n_caps_ge_0.50']} pass={b1_pol[pol]['pass']}")
        print(f"   RE-B1 PASS={b1_pass} | FIX2 custom_obsolete={fix2['custom_obsolete']} (arc {arc_caps} / lruk {lruk_caps} / bestpin {bestpin} {pin_caps}) | HHI_flag={hhi_flag}")

    # OVERALL DISPOSITION (CC primary)
    cc=bundle["corpora"]["cc"]
    if not cc["RE_B0_PASS"]:
        disp={"verdict":"CLEAN-KILL (RE-B0)","rationale":
              f"premise gap vanished on CC: far_share={cc['far_share']} (need>={B0_FAR_FLOOR}), "
              f"belady_saved_max={cc['belady_saved_max']} (need>={B0_BELADY_FLOOR}). No project."}
    elif cc["RE_B1"]["PASS"]:
        bp=cc["RE_B1"]["best_policy"]
        disp={"verdict":"PASS","rationale":
              f"best cheap policy '{bp}' captures >=50% of (LRU-Belady) gap at "
              f"{cc['RE_B1']['by_policy'][bp]['n_caps_ge_0.50']}/5 caps at matched residency. "
              f"FIX2 custom_obsolete={cc['FIX2_arc_vs_custom']['custom_obsolete']}. HHI_flag={cc['HHI_flag_any']}."}
    else:
        bp=cc["RE_B1"]["best_policy"]; bn=cc["RE_B1"]["by_policy"][bp]["n_caps_ge_0.50"]
        disp={"verdict":"CLEAN-NEGATIVE-KILL (RE-B1)","rationale":
              f"NO cheap policy captures >=50% of (LRU-Belady) gap at >=3/5 caps. Best='{bp}' reaches threshold at "
              f"{bn}/5 caps only. Belady gap is ORACLE-ONLY -> ship classical eviction (LRU/LFU); reinforces DEAD-0019 "
              f"from the policy side. HHI_flag={cc['HHI_flag_any']}."}
    bundle["DISPOSITION"]=disp
    print(f"\nDISPOSITION: {disp['verdict']}\n  {disp['rationale']}")
    with open(os.path.join(rdir,"summary.json"),"w") as f:
        json.dump(bundle,f,indent=2,default=str)
    print(f"wrote {rdir}/summary.json")
    return bundle

if __name__=="__main__":
    main()
