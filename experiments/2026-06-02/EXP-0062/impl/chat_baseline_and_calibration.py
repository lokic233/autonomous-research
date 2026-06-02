#!/usr/bin/env python3
"""
EXP-0062 - GREEN-LIFT of CLAIM-0026 (PROJ-0015). Executes the FROZEN
impl/PRE_REGISTRATION.md. Closes 3 gaps from VERDICT-0072:
  Gap 1: on-node CHAT baseline (zero-tool sessions, IDENTICAL instrument).
  Gap 2: char/4 vs real gpt2 tokenizer calibration (stratified 10% subsample) + recompute headline.
  Gap 3: prior-art cites (handled in analysis.md).
  + jackknife-by-session robustness.

REUSES experiments/2026-06-01/EXP-0061/impl/decomposition_census.py VERBATIM (import):
  parsers decompose_cc_session/decompose_codex_session, canon_args, block_text, gini,
  denoms, load_corpus, char/4 proxy (CHARS_PER_TOK=4.0), MIN_TRIALS, session-clustered bootstrap.

Gap 2 token-counting uses gpt2 (EXP-0049 .venv) ONLY for token counts; all shares/bootstrap stdlib.
Run under the venv python so transformers is importable; stdlib math used for everything else.
"""
import json, glob, os, math, random, importlib.util, warnings
warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))  # autonomous-research
DC_PATH = os.path.join(ROOT, "experiments/2026-06-01/EXP-0061/impl/decomposition_census.py")
spec = importlib.util.spec_from_file_location("dc", DC_PATH)
dc = importlib.util.module_from_spec(spec); spec.loader.exec_module(dc)

# ---- FROZEN constants (PRE_REGISTRATION sec FROZEN CONSTANTS) ----
SEED_CAL        = 20260602
NBOOT           = dc.NBOOT          # 2000
CHARS_PER_TOK   = dc.CHARS_PER_TOK  # 4.0
CHAT_MIN_CHARS  = 1000
CHAT_RESULT_MAX = 0.10
SUBSAMPLE_FRAC  = 0.10
A0_THRESH       = 0.50
CROSS_SEP       = 0.40
MIN_TRIALS      = dc.MIN_TRIALS     # 8
RESULTS = os.path.join(os.path.dirname(HERE), "results")
os.makedirs(RESULTS, exist_ok=True)

CC_GLOB = os.path.expanduser("~/.claude/projects/*/*.jsonl")
CX_GLOB = os.path.expanduser("~/.codex/sessions/**/*.jsonl")

# ============================================================ GAP 1: CHAT BASELINE
def is_chat(s):
    # chat = zero tool round-trips (no tool_result blocks, no arg mass) and substantive
    dyn = s["R"]+s["A"]+s["TX"]+s["TH"]+s["U"]+s["O"]
    return (s["n"]==0 and s["A"]==0.0 and dyn >= CHAT_MIN_CHARS)

def load_chat(kind):
    if kind=="cc":
        fs=sorted(glob.glob(CC_GLOB)); dec=dc.decompose_cc_session
    else:
        fs=sorted(glob.glob(CX_GLOB, recursive=True)); dec=dc.decompose_codex_session
    out={}
    for f in fs:
        try: s=dec(f)
        except Exception: continue
        if is_chat(s): out[os.path.basename(f)]=s
    return out

def share(agg, num="R"):
    D = agg["R"]+agg["A"]+agg["TX"]+agg["TH"]+agg["U"]+agg["O"]  # D1 raw span
    return (agg[num]/D) if D>0 else None

def pooled(sessions, keys):
    o={k:0.0 for k in ("R","A","TX","TH","U","O","S")}
    for k in keys:
        for kk in o: o[kk]+=sessions[k][kk]
    return o

def boot_share(sessions, num):
    keys=list(sessions.keys()); rnd=random.Random(SEED_CAL)
    vals=[]
    for _ in range(NBOOT):
        pick=[keys[rnd.randrange(len(keys))] for _ in range(len(keys))]
        v=share(pooled(sessions,pick), num)
        if v is not None: vals.append(v)
    vals.sort()
    if not vals: return (None,None,None)
    return (vals[int(0.025*len(vals))], vals[int(0.975*len(vals))], sum(vals)/len(vals))

def gap1_chat():
    res={}
    for kind in ("cc","codex"):
        ch=load_chat(kind); keys=list(ch.keys())
        agg=pooled(ch,keys)
        Rc=share(agg,"R"); Uc=share(agg,"U")
        decode=(agg["TX"]+agg["TH"]); D=agg["R"]+agg["A"]+agg["TX"]+agg["TH"]+agg["U"]+agg["O"]
        dec_share=decode/D if D>0 else None
        rlb,rub,rm=boot_share(ch,"R")
        ulb,uub,um=boot_share(ch,"U")
        res[kind]={
            "n_chat_sessions":len(keys),
            "chat_result_share_Rc_D1":Rc, "Rc_LB95":rlb,"Rc_UB95":rub,
            "chat_userprompt_share_Uc_D1":Uc, "Uc_LB95":ulb,"Uc_UB95":uub,
            "chat_decode_share_D1":dec_share,
            "mass_tok":{k:dc.tok(agg[k]) for k in ("R","A","TX","TH","U","O")},
        }
    return res

# ============================================================ GAP 2: TOKENIZER CALIBRATION
# segment extractors mirror decompose_* field semantics EXACTLY (reuse dc.canon_args/dc.block_text)
def segs_cc(path):
    seg={"R":[],"A":[],"TX":[],"TH":[],"U":[]}
    for line in open(path,errors="ignore"):
        line=line.strip()
        if not line: continue
        try: d=json.loads(line)
        except: continue
        m=d.get("message")
        if not isinstance(m,dict): continue
        role=m.get("role"); c=m.get("content")
        if isinstance(c,str):
            if role=="assistant": seg["TX"].append(c)
            else: seg["U"].append(c)
            continue
        if not isinstance(c,list): continue
        for b in c:
            if not isinstance(b,dict): continue
            tp=b.get("type")
            if tp=="text":
                t=b.get("text","") or ""
                (seg["TX"] if role=="assistant" else seg["U"]).append(t)
            elif tp=="thinking": seg["TH"].append(b.get("thinking","") or "")
            elif tp=="tool_use": seg["A"].append(dc.canon_args(b.get("input",{}) or {}))
            elif tp=="tool_result": seg["R"].append(dc.block_text(b))
    return seg

def segs_codex(path):
    seg={"R":[],"A":[],"TX":[],"TH":[],"U":[]}; seen=set()
    for line in open(path,errors="ignore"):
        line=line.strip()
        if not line: continue
        try: d=json.loads(line)
        except: continue
        p=d.get("payload") or d; tp=p.get("type")
        if tp in dc.MIRROR_CODEX: continue
        if tp=="function_call":
            raw=p.get("arguments","")
            try: a=json.loads(raw) if isinstance(raw,str) else raw
            except Exception: a=raw
            seg["A"].append(dc.canon_args(a) if isinstance(a,(dict,list)) else str(a))
        elif tp=="function_call_output":
            cid=p.get("call_id")
            if cid in seen: continue
            seen.add(cid); seg["R"].append(str(p.get("output","")))
        elif tp=="reasoning":
            # capture ACTUAL served reasoning text (summary + content + encrypted base64 blob), char-for-char
            parts=[]
            summ=p.get("summary")
            if isinstance(summ,list):
                for x in summ: parts.append(x.get("text","") if isinstance(x,dict) else str(x))
            cont=p.get("content")
            if isinstance(cont,str): parts.append(cont)
            elif isinstance(cont,list):
                for x in cont:
                    if isinstance(x,dict): parts.append(x.get("text","") or "")
            enc=p.get("encrypted_content")
            if isinstance(enc,str): parts.append(enc)
            t="".join(parts)
            if t: seg["TH"].append(t)
        elif tp=="message":
            role=p.get("role")
            txt=""
            c=p.get("content")
            if isinstance(c,str): txt=c
            elif isinstance(c,list):
                txt="\n".join(x.get("text","") if isinstance(x,dict) else str(x) for x in c)
            if role=="user": seg["U"].append(txt)
            elif role!="developer": seg["TX"].append(txt)
    return seg

def gap2_calibration(tk):
    rnd=random.Random(SEED_CAL)
    out={}
    for kind,gl,segfn,decfn in (("cc",CC_GLOB,segs_cc,dc.decompose_cc_session),
                                ("codex",CX_GLOB,segs_codex,dc.decompose_codex_session)):
        fs=sorted(glob.glob(gl, recursive=True))
        # agent inclusion = SAME as EXP-0061 (n>=MIN_TRIALS result-calls)
        pool={k:[] for k in ("R","A","TX","TH","U")}
        full_char={k:0.0 for k in ("R","A","TX","TH","U")}
        for f in fs:
            try: s=decfn(f)
            except Exception: continue
            if s["n"]<MIN_TRIALS: continue
            sg=segfn(f)
            for k in pool:
                for seg in sg[k]:
                    if seg:
                        pool[k].append(seg); full_char[k]+=len(seg)
        # stratified 10% subsample per class; gpt2 token count
        cpt={}; sub_detail={}
        for k in pool:
            segl=pool[k]
            if not segl: cpt[k]=None; continue
            n=len(segl); m=max(1,int(round(SUBSAMPLE_FRAC*n)))
            idx=sorted(rnd.sample(range(n), m))
            ch=tok=0
            for i in idx:
                s=segl[i]
                ch+=len(s); tok+=len(tk.encode(s, add_special_tokens=False))
            cpt[k]= (ch/tok) if tok>0 else None
            sub_detail[k]={"n_segments":n,"subsampled":m,"sub_chars":ch,"sub_tokens":tok}
        # recompute true-token result-share f_true = R_true / sum(true) using D1 classes present in calibration (R,A,TX,TH,U)
        true_mass={}
        for k in ("R","A","TX","TH","U"):
            c=full_char[k]; r=cpt.get(k)
            true_mass[k]= (c/r) if (r and r>0) else (c/CHARS_PER_TOK)
        D_true=sum(true_mass.values())
        f_true=(true_mass["R"]/D_true) if D_true>0 else None
        # char/4 comparator on the SAME classes (R..U, excl O to match calibration scope)
        D_char4=sum(full_char[k] for k in ("R","A","TX","TH","U"))/CHARS_PER_TOK
        f_char4=( (full_char["R"]/CHARS_PER_TOK)/D_char4 ) if D_char4>0 else None
        out[kind]={"cpt_by_class":cpt,"subsample_detail":sub_detail,
                   "full_char_mass":full_char,
                   "f_char4_RclassesAU":f_char4,"f_true_RclassesAU":f_true,
                   "true_token_mass":true_mass,
                   "verdict":("ARTIFACT_downgrade" if (f_true is not None and f_true<A0_THRESH)
                              else ("HARDENED" if (f_true is not None and f_char4 is not None and f_true>=f_char4)
                                    else "robust_confirmed"))}
    return out

# ============================================================ JACKKNIFE robustness
def jackknife():
    out={}
    for kind in ("cc","codex"):
        sess=dc.load_corpus(kind); keys=list(sess.keys())
        # rank sessions by total result mass R
        ranked=sorted(keys, key=lambda k: sess[k]["R"], reverse=True)
        def f_drop(drop):
            ks=[k for k in keys if k not in set(drop)]
            agg=pooled(sess,ks); return share(agg,"R")
        out[kind]={"full":share(pooled(sess,keys),"R"),
                   "drop_top1":f_drop(ranked[:1]),
                   "drop_top3":f_drop(ranked[:3]),
                   "n_sessions":len(keys)}
    return out

# ============================================================ MAIN
def main():
    print(f"[EXP-0062] SEED_CAL={SEED_CAL} NBOOT={NBOOT} CHAT_MIN_CHARS={CHAT_MIN_CHARS} SUBSAMPLE_FRAC={SUBSAMPLE_FRAC}")
    # GAP 1
    g1=gap1_chat()
    for k,v in g1.items():
        print(f"[chat:{k}] n={v['n_chat_sessions']} Rc/D1={v['chat_result_share_Rc_D1']:.4f} (UB95 {v['Rc_UB95']:.4f}) "
              f"Uc/D1={v['chat_userprompt_share_Uc_D1']:.4f} [{v['Uc_LB95']:.3f},{v['Uc_UB95']:.3f}] decode={v['chat_decode_share_D1']:.4f}")
    json.dump(g1, open(os.path.join(RESULTS,"chat_baseline.json"),"w"), indent=2, default=str)
    # GAP 2
    from transformers import AutoTokenizer
    tk=AutoTokenizer.from_pretrained("gpt2", use_fast=True)
    g2=gap2_calibration(tk)
    for k,v in g2.items():
        print(f"[calib:{k}] cpt={ {c:(round(x,3) if x else None) for c,x in v['cpt_by_class'].items()} } "
              f"f_char4={v['f_char4_RclassesAU']:.4f} f_true={v['f_true_RclassesAU']:.4f} -> {v['verdict']}")
    json.dump(g2, open(os.path.join(RESULTS,"calibration.json"),"w"), indent=2, default=str)
    # JACKKNIFE
    jk=jackknife()
    for k,v in jk.items():
        print(f"[jackknife:{k}] full={v['full']:.4f} drop_top1={v['drop_top1']:.4f} drop_top3={v['drop_top3']:.4f}")
    json.dump(jk, open(os.path.join(RESULTS,"jackknife.json"),"w"), indent=2, default=str)
    print("WROTE results/{chat_baseline,calibration,jackknife}.json")

if __name__=="__main__":
    main()
