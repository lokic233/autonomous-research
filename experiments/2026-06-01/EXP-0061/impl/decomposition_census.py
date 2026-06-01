#!/usr/bin/env python3
"""
EXP-0061 - Agent serving PREFILL TOKEN-MASS decomposition (PROJ-0015 / CLAIM-0026).
Pure stdlib, Mac CPU, NO numpy/scipy. Executes the FROZEN impl/PRE_REGISTRATION.md
(LOCK-TS 2026-06-01T23:44:20Z, committed 8e60c29 BEFORE this run).

CHARACTERIZATION ONLY (no predictor, no dAUC). Headline = the granular token-mass decomposition
(tool-result vs arg vs decode-interstitial) + heavy-tail Gini + cross-instrument replication.

Reuses parse machinery (canon_args/block_text field semantics, char/4 proxy, 2000x session-clustered
bootstrap, gini, HHI-by-session) from EXP-0054/0057/0059 VERBATIM; EXTENDS to a full mutually-exclusive
content-class census (R/A/TX/TH/U/O) + static prefix S.
"""
import json, glob, os, math, random
from collections import defaultdict

# ---------------- FROZEN CONSTANTS (PRE_REGISTRATION sec 12) ----------------
SEED          = 20260601
NBOOT         = 2000
CHARS_PER_TOK = 4.0
MIN_TRIALS    = 8
TOPDECILE     = 0.10
A0_THRESH     = 0.50
A1_THRESH     = 0.50
CROSS_MARGIN  = 0.40
GINI_NEG      = 0.50
HHI_FLAG      = 0.20
LOCKED_TS     = "2026-06-01T23:44:20Z"
PREREG_COMMIT = "8e60c29"
COST_RATIOS   = [10.0, 100.0]   # decode $/tok : prefill $/tok (Splitwise 2311.18677 / DistServe 2401.09670) - SECONDARY

random.seed(SEED)
def tok(n): return n / CHARS_PER_TOK   # char/4 proxy; cancels in all ratios

# ---------------- field semantics reused VERBATIM (EXP-0057) ----------------
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

# ---------------- DECOMPOSITION PARSERS (PRE_REGISTRATION sec 5) ----------------
def decompose_cc_session(path):
    R=A=TX=TH=U=O=0.0
    result_sizes=[]            # char len per tool_result block (RE-A1 concentration unit)
    S=0.0; got_first_user=False
    with open(path, errors="ignore") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try: d=json.loads(line)
            except: continue
            m=d.get("message")
            if not isinstance(m,dict): continue
            role=m.get("role"); c=m.get("content")
            if isinstance(c,str):
                if role=="assistant": TX+=len(c)
                else:
                    U+=len(c)
                    if not got_first_user: S+=len(c); got_first_user=True   # static prefix LOWER BOUND
                continue
            if not isinstance(c,list):
                O+=len(str(c)); continue
            first_user_here=False
            for b in c:
                if not isinstance(b,dict): O+=len(str(b)); continue
                tp=b.get("type")
                if tp=="text":
                    t=b.get("text","") or ""
                    if role=="assistant": TX+=len(t)
                    else:
                        U+=len(t)
                        if not got_first_user: S+=len(t); first_user_here=True
                elif tp=="thinking":
                    TH+=len(b.get("thinking","") or "")
                elif tp=="tool_use":
                    A+=len(canon_args(b.get("input",{}) or {}))
                elif tp=="tool_result":
                    rt=block_text(b); R+=len(rt); result_sizes.append(len(rt))
                else:
                    O+=len(json.dumps(b, default=str))
            if first_user_here: got_first_user=True
    return dict(R=R,A=A,TX=TX,TH=TH,U=U,O=O,S=S,result_sizes=result_sizes,n=len(result_sizes))

MIRROR_CODEX = {"agent_message","user_message","mcp_tool_call_end","mcp_tool_call_begin",
                "exec_command_end","exec_command_begin","exec_command_output_delta",
                "token_count","task_started","task_complete","turn_aborted","turn_context","event_msg"}

def _codex_msg_text(p):
    c=p.get("content"); tot=0
    if isinstance(c,str): tot+=len(c)
    elif isinstance(c,list):
        for x in c:
            if isinstance(x,dict): tot+=len(x.get("text","") or "")
            else: tot+=len(str(x))
    return tot

def _codex_reasoning_text(p):
    tot=0
    summ=p.get("summary")
    if isinstance(summ,list):
        for x in summ:
            if isinstance(x,dict): tot+=len(x.get("text","") or "")
            else: tot+=len(str(x))
    cont=p.get("content")
    if isinstance(cont,str): tot+=len(cont)
    elif isinstance(cont,list):
        for x in cont:
            if isinstance(x,dict): tot+=len(x.get("text","") or "")
    enc=p.get("encrypted_content")
    if isinstance(enc,str): tot+=len(enc)   # encrypted reasoning IS re-served; counting it is CONSERVATIVE (enlarges decode)
    return tot

def decompose_codex_session(path):
    R=A=TX=TH=U=O=0.0
    result_sizes=[]; S=0.0; seen_out=set()
    with open(path, errors="ignore") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try: d=json.loads(line)
            except: continue
            p=d.get("payload") or d
            tp=p.get("type")
            # static prefix: header line carries base_instructions; session_meta likewise
            bi=p.get("base_instructions")
            if isinstance(bi,dict) and isinstance(bi.get("text"),str): S+=len(bi["text"])
            elif isinstance(bi,str): S+=len(bi)
            if tp in MIRROR_CODEX: continue
            if tp=="function_call":
                raw=p.get("arguments","")
                try: a=json.loads(raw) if isinstance(raw,str) else raw
                except Exception: a=raw
                astr=canon_args(a) if isinstance(a,(dict,list)) else str(a)
                A+=len(astr)
            elif tp=="function_call_output":
                cid=p.get("call_id")
                if cid in seen_out: continue       # dedup (matches parse_codex_session)
                seen_out.add(cid)
                out=str(p.get("output","")); R+=len(out); result_sizes.append(len(out))
            elif tp=="reasoning":
                TH+=_codex_reasoning_text(p)
            elif tp=="message":
                role=p.get("role"); tlen=_codex_msg_text(p)
                if role=="developer": S+=tlen            # static
                elif role=="user": U+=tlen
                else: TX+=tlen                            # assistant / other
            elif tp in ("session_meta", None):
                pass                                      # static header handled via base_instructions
            else:
                O+=len(json.dumps(p, default=str))
    return dict(R=R,A=A,TX=TX,TH=TH,U=U,O=O,S=S,result_sizes=result_sizes,n=len(result_sizes))

def load_corpus(kind):
    if kind=="cc":
        fs=sorted(glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))); dec=decompose_cc_session
    else:
        fs=sorted(glob.glob(os.path.expanduser("~/.codex/sessions/**/*.jsonl"), recursive=True)); dec=decompose_codex_session
    sessions={}
    for f in fs:
        try: s=dec(f)
        except Exception: continue
        if s["n"]>=MIN_TRIALS: sessions[os.path.basename(f)]=s
    return sessions

# ---------------- metrics (gini/hhi VERBATIM EXP-0057/0059) ----------------
def gini(values):
    vs=sorted(v for v in values if v>0); n=len(vs)
    if n==0: return None
    s=sum(vs)
    if s<=0: return None
    cum=0.0
    for i,v in enumerate(vs): cum+=(i+1)*v
    return (2*cum)/(n*s) - (n+1)/n

def hhi(values):
    s=sum(v for v in values if v>0)
    if s<=0: return 0.0
    return sum((v/s)**2 for v in values if v>0)

def median(xs):
    ys=sorted(xs); n=len(ys)
    if n==0: return None
    return ys[n//2] if n%2 else (ys[n//2-1]+ys[n//2])/2.0

def topdecile_share(sizes):
    """share of total result mass held by the top ceil(10%) of result-bearing calls."""
    vs=sorted((v for v in sizes if v>0), reverse=True); n=len(vs)
    if n==0: return None
    tot=sum(vs)
    if tot<=0: return None
    k=max(1, math.ceil(TOPDECILE*n))
    return sum(vs[:k])/tot

# ---------------- denominators (PRE_REGISTRATION sec 7) ----------------
def denoms(agg):
    R,A,TX,TH,U,O = agg["R"],agg["A"],agg["TX"],agg["TH"],agg["U"],agg["O"]
    D1 = R+A+TX+TH+U+O          # raw span (CONSERVATIVE HEADLINE)
    D2 = R+A+TX+TH+U            # drop structural O
    D3 = R+A+TX+TH              # result vs decode (drop user+overhead)
    D3p= R+TX                   # result vs assistant-text-only (literal committee reading)
    return {"D1_raw_span":D1,"D2_non_overhead":D2,"D3_decode_only":D3,"D3p_asst_text_only":D3p}

def pooled_agg(sessions, keys):
    out={k:0.0 for k in ("R","A","TX","TH","U","O","S")}
    for k in keys:
        s=sessions[k]
        for kk in out: out[kk]+=s[kk]
    return out

def pooled_f(sessions, keys, dkey):
    agg=pooled_agg(sessions, keys)
    D=denoms(agg)[dkey]
    return (agg["R"]/D) if D>0 else None

def boot_ci(draw_fn, n_draws=NBOOT):
    vals=[v for _ in range(n_draws) for v in [draw_fn()] if v is not None]
    if not vals: return (None,None,None)
    vals.sort()
    return (vals[int(0.025*len(vals))], vals[int(0.975*len(vals))], sum(vals)/len(vals))

# ---------------- per-corpus analysis ----------------
def analyze(sessions, corpus):
    keys=list(sessions.keys())
    agg=pooled_agg(sessions, keys)
    D=denoms(agg)
    # point result-shares
    shares={dk:(agg["R"]/dv if dv>0 else None) for dk,dv in D.items()}
    # static vs dynamic
    Smass=agg["S"]; dynamic=D["D1_raw_span"]
    static_share = Smass/(Smass+dynamic) if (Smass+dynamic)>0 else None
    # per-session result-share (D1) for median + HHI
    sess_R=[sessions[k]["R"] for k in keys]
    sess_D1=[denoms(sessions[k])["D1_raw_span"] for k in keys]
    sess_fr=[(r/d if d>0 else 0.0) for r,d in zip(sess_R,sess_D1)]
    hhi_result=hhi(sess_R)
    med_fr=median(sess_fr)
    # pooled result_sizes for concentration
    all_sizes=[v for k in keys for v in sessions[k]["result_sizes"]]
    td_point=topdecile_share(all_sizes)
    g_point=gini(all_sizes)
    # --- RE-A0 bootstrap: pooled f on D1 (conservative) ---
    def draw_f():
        pick=[keys[random.randrange(len(keys))] for _ in range(len(keys))]
        return pooled_f(sessions, pick, "D1_raw_span")
    a0_lb,a0_ub,a0_mean=boot_ci(draw_f)
    # --- RE-A1 bootstrap: top-decile share + gini (session-clustered) ---
    def draw_td():
        pick=[keys[random.randrange(len(keys))] for _ in range(len(keys))]
        sz=[v for k in pick for v in sessions[k]["result_sizes"]]
        return topdecile_share(sz)
    td_lb,td_ub,td_mean=boot_ci(draw_td)
    def draw_g():
        pick=[keys[random.randrange(len(keys))] for _ in range(len(keys))]
        sz=[v for k in pick for v in sessions[k]["result_sizes"]]
        return gini(sz)
    g_lb,g_ub,g_mean=boot_ci(draw_g)
    # cost-weighted SECONDARY (RE-A4): prefill=R+U+S, decode=A+TX+TH
    prefill=agg["R"]+agg["U"]+agg["S"]; decode=agg["A"]+agg["TX"]+agg["TH"]
    cost_shares={}
    for w in COST_RATIOS:
        denom=prefill*1.0 + decode*w
        cost_shares[f"decode_x{int(w)}"]= (agg["R"]*1.0/denom) if denom>0 else None
    # baseline (b): agent result/decode token ratio
    result_decode_ratio = (agg["R"]/decode) if decode>0 else None
    return {
        "corpus":corpus, "n_sessions":len(keys),
        "n_result_calls":len(all_sizes),
        "mass_tok":{k:tok(agg[k]) for k in ("R","A","TX","TH","U","O","S")},
        "mass_char":{k:agg[k] for k in ("R","A","TX","TH","U","O","S")},
        "denominators_tok":{k:tok(v) for k,v in D.items()},
        "result_share_point":shares,
        "HEADLINE_denominator":"D1_raw_span",
        "RE_A0": {"f_point":shares["D1_raw_span"], "LB95":a0_lb, "UB95":a0_ub, "boot_mean":a0_mean,
                  "threshold":A0_THRESH, "PASS":(a0_lb is not None and a0_lb>A0_THRESH),
                  "downgrade_to_largest_component":(a0_lb is not None and a0_lb<=A0_THRESH)},
        "RE_A1": {"topdecile_share_point":td_point, "topdecile_LB95":td_lb, "topdecile_UB95":td_ub,
                  "topdecile_PASS":(td_lb is not None and td_lb>A1_THRESH),
                  "gini_point":g_point, "gini_LB95":g_lb, "gini_UB95":g_ub,
                  "gini_negative_flag":(g_point is not None and g_point<GINI_NEG)},
        "RE_A2_denominator_robustness":shares,
        "static_dynamic":{"S_tok":tok(Smass),"dynamic_tok":tok(dynamic),"static_share":static_share,
                          "note_cc_lower_bound": (corpus=="cc")},
        "STAT":{"HHI_by_session_resulttok":hhi_result,"HHI_flag":(hhi_result>HHI_FLAG),
                "session_median_result_share_D1":med_fr},
        "SECONDARY_cost_weighted":{"prefill_tok":tok(prefill),"decode_tok":tok(decode),"cost_result_share":cost_shares},
        "baseline_b_result_decode_ratio":result_decode_ratio,
        "_keys":keys,
    }

# ---------------- main ----------------
def main():
    base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir=os.path.join(base,"results"); os.makedirs(rdir, exist_ok=True)
    print(f"[EXP-0061] LOCK {LOCKED_TS} prereg {PREREG_COMMIT} seed {SEED} NBOOT {NBOOT}")
    corpora={"cc":load_corpus("cc"), "codex":load_corpus("codex")}
    for c,s in corpora.items(): print(f"  {c}: {len(s)} sessions (>= {MIN_TRIALS} result-calls)")
    res={"experiment":"EXP-0061","claim":"CLAIM-0026","project":"PROJ-0015","level":0,
         "locked_ts":LOCKED_TS,"prereg_commit":PREREG_COMMIT,"seed":SEED,"nboot":NBOOT,
         "chars_per_tok":CHARS_PER_TOK,"frozen":{"A0":A0_THRESH,"A1":A1_THRESH,"cross_margin":CROSS_MARGIN,
         "gini_neg":GINI_NEG,"hhi_flag":HHI_FLAG,"min_trials":MIN_TRIALS,"topdecile":TOPDECILE},
         "corpora":{}}
    an={}
    for c,s in corpora.items():
        if len(s)<2:
            res["corpora"][c]={"status":"too_few_sessions","n":len(s)}; continue
        a=analyze(s,c); an[c]=a
        keys=a.pop("_keys")
        res["corpora"][c]=a
        r0=a["RE_A0"]; r1=a["RE_A1"]
        print(f"\n[{c}] n={a['n_sessions']} result-calls={a['n_result_calls']}")
        print(f"  result-share D1(raw-span,HEADLINE)={r0['f_point']:.4f}  LB95={r0['LB95']:.4f} UB95={r0['UB95']:.4f}  PASS={r0['PASS']}")
        print(f"  denom robustness: " + " ".join(f"{k}={v:.3f}" for k,v in a['result_share_point'].items() if v is not None))
        print(f"  top-decile result-mass={r1['topdecile_share_point']:.4f} LB95={r1['topdecile_LB95']:.4f} PASS={r1['topdecile_PASS']}")
        print(f"  Gini(result calls)={r1['gini_point']:.4f} CI95=[{r1['gini_LB95']:.4f},{r1['gini_UB95']:.4f}] neg_flag={r1['gini_negative_flag']}")
        print(f"  HHI-by-session={a['STAT']['HHI_by_session_resulttok']:.4f} flag={a['STAT']['HHI_flag']} session-median f={a['STAT']['session_median_result_share_D1']:.4f}")
        print(f"  static_share={a['static_dynamic']['static_share']:.4f} (cc lower-bound={a['static_dynamic']['note_cc_lower_bound']})")
        print(f"  SECONDARY cost-weighted result-$-share: {a['SECONDARY_cost_weighted']['cost_result_share']}")
        # per-session csv
        with open(os.path.join(rdir,f"per_session_{c}.csv"),"w") as f:
            f.write("session,n_calls,R_tok,A_tok,TX_tok,TH_tok,U_tok,O_tok,S_tok,D1_tok,result_share_D1\n")
            for k in keys:
                ss=s[k]; D1=denoms(ss)["D1_raw_span"]
                fr=(ss["R"]/D1 if D1>0 else 0.0)
                f.write(f"{k},{ss['n']},{tok(ss['R']):.1f},{tok(ss['A']):.1f},{tok(ss['TX']):.1f},"
                        f"{tok(ss['TH']):.1f},{tok(ss['U']):.1f},{tok(ss['O']):.1f},{tok(ss['S']):.1f},"
                        f"{tok(D1):.1f},{fr:.4f}\n")

    # ---- RE-A3 cross-instrument hard gate + Gini-delta CI ----
    cc=an.get("cc"); cx=an.get("codex")
    cross={}
    if cc and cx:
        fcc=cc["RE_A0"]["f_point"]; fcx=cx["RE_A0"]["f_point"]
        lbcc=cc["RE_A0"]["LB95"]; lbcx=cx["RE_A0"]["LB95"]
        cross={"f_cc_D1":fcc,"f_codex_D1":fcx,"abs_diff":abs(fcc-fcx),
               "both_LB95_gt_0.50":bool(lbcc>A0_THRESH and lbcx>A0_THRESH),
               "margin_ok_lt_0.40":bool(abs(fcc-fcx)<CROSS_MARGIN),
               "HARD_GATE_PASS":bool(lbcc>A0_THRESH and lbcx>A0_THRESH and abs(fcc-fcx)<CROSS_MARGIN)}
        # paired Gini-delta CI (independent session resample per corpus, paired by draw index)
        kcc=list(corpora["cc"].keys()); kcx=list(corpora["codex"].keys())
        deltas=[]
        for _ in range(NBOOT):
            pc=[kcc[random.randrange(len(kcc))] for _ in range(len(kcc))]
            px=[kcx[random.randrange(len(kcx))] for _ in range(len(kcx))]
            gc=gini([v for k in pc for v in corpora["cc"][k]["result_sizes"]])
            gx=gini([v for k in px for v in corpora["codex"][k]["result_sizes"]])
            if gc is not None and gx is not None: deltas.append(gc-gx)
        deltas.sort()
        if deltas:
            cross["gini_delta_cc_minus_codex"]={"point":cc["RE_A1"]["gini_point"]-cx["RE_A1"]["gini_point"],
                "LB95":deltas[int(0.025*len(deltas))],"UB95":deltas[int(0.975*len(deltas))]}
    res["RE_A3_cross_instrument"]=cross

    # ---- DISPOSITION ----
    disp=decide(an, cross)
    res["DISPOSITION"]=disp
    print(f"\nRE-A3 cross-instrument: {cross.get('HARD_GATE_PASS')} (|cc-codex|={cross.get('abs_diff')})")
    print(f"DISPOSITION: {disp['verdict']}\n  {disp['rationale']}")
    with open(os.path.join(rdir,"summary.json"),"w") as f:
        json.dump(res,f,indent=2,default=str)
    print(f"wrote {rdir}/summary.json")
    return res

def decide(an, cross):
    cc=an.get("cc"); cx=an.get("codex")
    if not (cc and cx):
        return {"verdict":"INCONCLUSIVE","rationale":"one corpus missing/underpowered"}
    # clean-negative (fix #8)
    neg=[]
    for c,a in (("CC",cc),("Codex",cx)):
        if a["RE_A0"]["LB95"] is not None and a["RE_A0"]["LB95"]<=A0_THRESH:
            neg.append(f"{c} RE-A0 LB95={a['RE_A0']['LB95']:.3f}<=0.50")
        if a["RE_A1"]["gini_negative_flag"]:
            neg.append(f"{c} Gini={a['RE_A1']['gini_point']:.3f}<0.50 (no heavy tail)")
    a0_both=cc["RE_A0"]["PASS"] and cx["RE_A0"]["PASS"]
    a1_both=cc["RE_A1"]["topdecile_PASS"] and cx["RE_A1"]["topdecile_PASS"]
    hard=cross.get("HARD_GATE_PASS")
    if neg and not a0_both:
        # if CC fails the majority bar but is still largest single component, report downgrade
        return {"verdict":"CLEAN-NEGATIVE / DOWNGRADE","rationale":
                "; ".join(neg)+f". Per pre-reg sec7 downgrade: tool-result reported as LARGEST SINGLE COMPONENT where LB95<=0.50 "
                f"(CC f={cc['RE_A0']['f_point']:.3f}, Codex f={cx['RE_A0']['f_point']:.3f}). Codex anchors cross-instrument."}
    if a0_both and a1_both and hard:
        return {"verdict":"GREEN-PASS","rationale":
                f"RE-A0 both LB95>0.50 (CC {cc['RE_A0']['LB95']:.3f}, Codex {cx['RE_A0']['LB95']:.3f}); "
                f"RE-A1 top-decile both>0.50 & Gini>0.50 both; RE-A3 hard-gate PASS (|cc-codex|={cross['abs_diff']:.3f}<0.40). "
                f"Tool-result is the MAJORITY of dynamic served token mass, heavy-tailed, replicated cross-instrument."}
    if a0_both and hard:
        return {"verdict":"PASS (A0+A3); A1 partial","rationale":
                f"RE-A0 majority both + cross-instrument hard-gate PASS, but top-decile concentration gate not met on both "
                f"(CC {cc['RE_A1']['topdecile_PASS']}, Codex {cx['RE_A1']['topdecile_PASS']})."}
    return {"verdict":"MIXED / instrument-dependent","rationale":
            f"a0_both={a0_both} a1_both={a1_both} hard_gate={hard}; "
            f"CC f={cc['RE_A0']['f_point']:.3f} (LB {cc['RE_A0']['LB95']}), Codex f={cx['RE_A0']['f_point']:.3f} (LB {cx['RE_A0']['LB95']}). "
            f"Per fix#5: if magnitudes diverge report 'instrument-dependent magnitude' not 'replicated dominance'."}

if __name__=="__main__":
    main()
