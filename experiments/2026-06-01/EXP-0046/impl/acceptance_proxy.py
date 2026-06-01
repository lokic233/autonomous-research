#!/usr/bin/env python3
"""
EXP-0046 (L0, CPU, stdlib-only) — CLAIM-0013 / PROJ-0004.
Tool-Boundary Acceptance Cliff in Speculative Decoding for Agent Trajectories.

Top-1-AGREEMENT PROXY (NOT a real SD draft/target pair — see preregistration.md sec 2):
 draft   = trigram-backoff next-token predictor trained on a HELD-OUT 50/50 session split.
 target  = realized assistant-generated token.
 accepted:= draft top-1 == target token.  Signal = P(accept) vs distance-from-tool-boundary.

Reuses corpus-parsing logic from EXP-0007 (CC tool_result join) + EXP-0037 (Codex call_id dedup);
reuses bootstrap/Holm idioms from EXP-0042. Pre-registered: K=8, margins, Holm, 4 controls.
"""
import json, glob, os, re, math, random
from collections import defaultdict, Counter

random.seed(20260601)
K = 8
B = 2000
HOME = os.path.expanduser('~')
TOKRE = re.compile(r"\w+|[^\w\s]")
INTERIOR_CAP = 1500   # deterministic stride cap on interior tokens per session (baseline stability)

def tokenize(s):
    if not s: return []
    return TOKRE.findall(str(s).lower())[:20000]

def block_text(b):
    cont = b.get('content','')
    if isinstance(cont, list):
        out=[]
        for x in cont:
            if isinstance(x, dict): out.append(x.get('text') or x.get('content') or '')
            else: out.append(str(x))
        return ' '.join(str(o) for o in out)
    return str(cont)

# ---------------- corpus stream extraction: list of (origin, token) in file order ----------------
def cc_streams():
    fs = sorted(glob.glob(os.path.join(HOME,'.claude','projects','*','*.jsonl')))
    sessions={}
    for f in fs:
        stream=[]
        try: lines=open(f, errors='ignore').read().splitlines()
        except: continue
        for line in lines:
            line=line.strip()
            if not line: continue
            try: d=json.loads(line)
            except: continue
            m=d.get('message')
            if not isinstance(m,dict): continue
            role=m.get('role') or d.get('type')
            c=m.get('content')
            if isinstance(c,str): c=[{'type':'text','text':c}]
            if not isinstance(c,list): continue
            for b in c:
                if not isinstance(b,dict): continue
                bt=b.get('type')
                if role=='assistant' and bt in ('text','thinking'):
                    txt=b.get('text','') or b.get('thinking','')
                    for t in tokenize(txt): stream.append(('asst',t))
                elif bt=='tool_result':
                    for t in tokenize(block_text(b)): stream.append(('tool',t))
                elif role=='user' and bt=='text':
                    for t in tokenize(b.get('text','')): stream.append(('user',t))
        n_asst=sum(1 for o,_ in stream if o=='asst')
        if n_asst>=50 and any(o=='tool' for o,_ in stream):
            sessions[f]=stream
    return sessions

def codex_streams():
    fs = sorted(glob.glob(os.path.join(HOME,'.codex','sessions','**','*.jsonl'), recursive=True))
    sessions={}
    for f in fs:
        stream=[]; seen=set(); prev_asst=None
        try: lines=open(f, errors='ignore').read().splitlines()
        except: continue
        for line in lines:
            line=line.strip()
            if not line: continue
            try: d=json.loads(line)
            except: continue
            p=d.get('payload') or d
            t=p.get('type')
            if t=='agent_message':
                txt=p.get('message','') or ''
                if txt and txt!=prev_asst:
                    for tk in tokenize(txt): stream.append(('asst',tk)); 
                    prev_asst=txt
            elif t=='message' and p.get('role')=='assistant':
                c=p.get('content'); txt=''
                if isinstance(c,list):
                    txt=' '.join(x.get('text','') for x in c if isinstance(x,dict))
                if txt and txt!=prev_asst:
                    for tk in tokenize(txt): stream.append(('asst',tk))
                    prev_asst=txt
            elif t=='user_message' or (t=='message' and p.get('role')=='user'):
                txt=p.get('message','')
                if not txt:
                    c=p.get('content')
                    if isinstance(c,list): txt=' '.join(x.get('text','') for x in c if isinstance(x,dict))
                for tk in tokenize(txt): stream.append(('user',tk))
            elif t=='function_call_output':
                cid=p.get('call_id')
                if cid in seen: continue
                seen.add(cid)
                for tk in tokenize(str(p.get('output',''))): stream.append(('tool',tk))
        n_asst=sum(1 for o,_ in stream if o=='asst')
        if n_asst>=50 and any(o=='tool' for o,_ in stream):
            sessions[f]=stream
    return sessions

# ---------------- n-gram predictor (trigram backoff) + entropy ----------------
def build_ngram(train_streams):
    uni=Counter(); bi=defaultdict(Counter); tri=defaultdict(Counter)
    for stream in train_streams:
        toks=[t for _,t in stream]
        for i,t in enumerate(toks):
            uni[t]+=1
            if i>=1: bi[toks[i-1]][t]+=1
            if i>=2: tri[(toks[i-2],toks[i-1])][t]+=1
    return uni,bi,tri

def make_predictor(uni,bi,tri):
    uni_top1 = uni.most_common(1)[0][0] if uni else None
    tot=sum(uni.values()) or 1
    uni_H=0.0
    for v in uni.values():
        pp=v/tot; uni_H-=pp*math.log2(pp)
    cache={}
    def predict(c2,c1):
        key=(c2,c1)
        r=cache.get(key)
        if r is not None: return r
        dist=None
        if c2 is not None and key in tri: dist=tri[key]
        elif c1 is not None and c1 in bi: dist=bi[c1]
        if dist is None:
            r=(uni_top1, uni_H)
        else:
            top1=dist.most_common(1)[0][0]
            tot2=sum(dist.values())
            H=0.0
            for v in dist.values():
                pp=v/tot2; H-=pp*math.log2(pp)
            r=(top1,H)
        cache[key]=r
        return r
    return predict

# ---------------- per-session evaluation ----------------
def eval_session(stream, predict):
    toks=[t for _,t in stream]; ori=[o for o,_ in stream]
    n=len(toks)
    S=defaultdict(lambda:[0,0])   # flat count dict: key -> [n, acc]
    meas=[]                       # (cls in {tool,interior}, acc, H) for entropy strata
    last_btype=None; dist=0
    interior_idx=[]
    int_seen=0
    for i in range(n):
        o=ori[i]; t=toks[i]
        if o=='tool': last_btype='tool'; dist=0
        elif o=='user': last_btype='user'; dist=0
        elif o=='asst':
            dist+=1
            c2=toks[i-2] if i>=2 else None
            c1=toks[i-1] if i>=1 else None
            top1,H=predict(c2,c1)
            acc=1 if top1==t else 0
            if last_btype=='tool' and dist<=K:
                S['tool:%d'%dist][0]+=1; S['tool:%d'%dist][1]+=acc
                meas.append(('tool',acc,H))
            elif last_btype=='user' and dist<=K:
                S['user:%d'%dist][0]+=1; S['user:%d'%dist][1]+=acc
            elif dist>K:
                # deterministic stride cap on interior
                if INTERIOR_CAP<=0 or (int_seen % 1)==0:
                    pass
                if len(interior_idx) < INTERIOR_CAP*3:
                    interior_idx.append(i)
                int_seen+=1
    # interior baseline with stride cap (deterministic): take evenly spaced up to CAP
    if interior_idx:
        if len(interior_idx)>INTERIOR_CAP:
            stride=len(interior_idx)/INTERIOR_CAP
            sel=[interior_idx[int(k*stride)] for k in range(INTERIOR_CAP)]
        else:
            sel=interior_idx
        for i in sel:
            t=toks[i]; c2=toks[i-2] if i>=2 else None; c1=toks[i-1] if i>=1 else None
            top1,H=predict(c2,c1); acc=1 if top1==t else 0
            S['interior'][0]+=1; S['interior'][1]+=acc
            meas.append(('interior',acc,H))
    # tool suffixes (last two tokens before each tool->asst transition = tool-result tail)
    tool_suffixes=[]
    for i in range(1,n):
        if ori[i]=='asst' and ori[i-1]=='tool':
            tool_suffixes.append((toks[i-2] if i>=2 else None, toks[i-1]))
    # SPLICE (content-type-matched null): graft tool-result tail as context before interior runs
    if tool_suffixes and interior_idx:
        runs=[]; cur=[interior_idx[0]]
        for x in interior_idx[1:]:
            if x==cur[-1]+1: cur.append(x)
            else:
                if len(cur)>=K: runs.append(cur)
                cur=[x]
        if len(cur)>=K: runs.append(cur)
        for ri,run in enumerate(runs):
            c2s,c1s=tool_suffixes[ri%len(tool_suffixes)]
            for d in range(1,K+1):
                idx=run[d-1]; t=toks[idx]
                if d==1: cc2,cc1=c2s,c1s
                elif d==2: cc2,cc1=c1s,toks[run[0]]
                else: cc2,cc1=toks[run[d-3]],toks[run[d-2]]
                top1,_=predict(cc2,cc1)
                S['splice:%d'%d][0]+=1; S['splice:%d'%d][1]+=(1 if top1==t else 0)
    return dict(S), meas

# ---------------- aggregation + statistics ----------------
def agg(dicts):
    out=defaultdict(lambda:[0,0])
    for D in dicts:
        for k,(nn,aa) in D.items():
            out[k][0]+=nn; out[k][1]+=aa
    return out

def rate(pair):
    n,a=pair; return (a/n) if n>0 else None

def stats_from_agg(A, strat_cuts, strat_dicts_sum):
    iacc=rate(A.get('interior',[0,0]))
    res={'interior_acc':iacc, 'interior_n':A.get('interior',[0,0])[0]}
    def pen(prefix):
        d_acc={}; d_pen={}
        for d in range(1,K+1):
            r=rate(A.get('%s:%d'%(prefix,d),[0,0])); d_acc[d]=r
            d_pen[d]=(iacc-r) if (r is not None and iacc is not None) else None
        return d_acc,d_pen
    res['tool_acc'],res['tool_pen']=pen('tool')
    res['user_acc'],res['user_pen']=pen('user')
    res['splice_acc'],res['splice_pen']=pen('splice')
    def meanv(d):
        vals=[v for v in d.values() if v is not None]
        return sum(vals)/len(vals) if vals else None
    res['mean_tool_pen']=meanv(res['tool_pen'])
    res['mean_user_pen']=meanv(res['user_pen'])
    res['mean_splice_pen']=meanv(res['splice_pen'])
    # diffs
    res['diff_content']={d:(res['tool_pen'][d]-res['splice_pen'][d]) if (res['tool_pen'][d] is not None and res['splice_pen'][d] is not None) else None for d in range(1,K+1)}
    res['diff_shift']  ={d:(res['tool_pen'][d]-res['user_pen'][d])   if (res['tool_pen'][d] is not None and res['user_pen'][d]   is not None) else None for d in range(1,K+1)}
    res['mean_diff_content']=meanv(res['diff_content'])
    res['mean_diff_shift']=meanv(res['diff_shift'])
    # within-entropy-stratum pooled penalty (tool d<=K vs interior)
    pooled=None
    if strat_dicts_sum is not None:
        num=0.0; wsum=0
        for q in range(4):
            tn,ta=strat_dicts_sum.get(('tool',q),[0,0])
            inn,ia=strat_dicts_sum.get(('int',q),[0,0])
            if tn>0 and inn>0:
                pen_q=(ia/inn)-(ta/tn); num+=tn*pen_q; wsum+=tn
        pooled=(num/wsum) if wsum>0 else None
    res['within_strat_tool_pen']=pooled
    return res

def quartile_cuts(vals):
    s=sorted(vals); n=len(s)
    if n<4: return [0,0,0]
    def q(p):
        pos=p*(n-1); lo=int(math.floor(pos)); hi=int(math.ceil(pos)); fr=pos-lo
        return s[lo]*(1-fr)+s[hi]*fr
    return [q(0.25),q(0.5),q(0.75)]

def strat_index(H,cuts):
    if H<=cuts[0]: return 0
    if H<=cuts[1]: return 1
    if H<=cuts[2]: return 2
    return 3

def per_session_strat(meas, cuts):
    D=defaultdict(lambda:[0,0])
    for cls,acc,H in meas:
        q=strat_index(H,cuts)
        key=('tool',q) if cls=='tool' else ('int',q)
        D[key][0]+=1; D[key][1]+=acc
    return dict(D)

def strat_agg(dicts):
    out=defaultdict(lambda:[0,0])
    for D in dicts:
        for k,(nn,aa) in D.items():
            out[k][0]+=nn; out[k][1]+=aa
    return out

def pctl(vals,p):
    s=sorted(v for v in vals if v is not None)
    if not s: return None
    pos=p*(len(s)-1); lo=int(math.floor(pos)); hi=int(math.ceil(pos)); fr=pos-lo
    return s[lo]*(1-fr)+s[hi]*fr

def holm(pvals):
    # pvals: dict d->p ; return dict d->(p_holm, survives@0.05)
    items=sorted(pvals.items(), key=lambda kv: kv[1])
    m=len(items); out={}; running=0.0
    for i,(d,p) in enumerate(items):
        adj=min(1.0,(m-i)*p); running=max(running,adj)
        out[d]=(running, running<0.05)
    return out

def analyze(name, sessions):
    keys=sorted(sessions.keys())
    # 50/50 split by deterministic hash
    train=[]; test=[]
    for kpath in keys:
        h=sum(ord(ch) for ch in os.path.basename(kpath))
        (train if h%2==0 else test).append(kpath)
    if len(test)<5 or len(train)<5:
        # fallback: alternate
        train=keys[::2]; test=keys[1::2]
    uni,bi,tri=build_ngram([sessions[k] for k in train])
    predict=make_predictor(uni,bi,tri)
    per_sess=[]; per_meas=[]; all_H=[]
    for k in test:
        S,meas=eval_session(sessions[k],predict)
        per_sess.append(S); per_meas.append(meas)
        for cls,acc,H in meas: all_H.append(H)
    cuts=quartile_cuts(all_H)
    per_strat=[per_session_strat(m,cuts) for m in per_meas]
    # point estimates
    A=agg(per_sess); SA=strat_agg(per_strat)
    point=stats_from_agg(A,cuts,SA)
    # cluster bootstrap by session
    nS=len(per_sess); idxs=list(range(nS))
    boot={k:[] for k in ['mean_tool_pen','mean_user_pen','mean_splice_pen',
                          'mean_diff_content','mean_diff_shift','within_strat_tool_pen']}
    boot_pos={d:[] for d in range(1,K+1)}
    for _ in range(B):
        samp=[idxs[random.randrange(nS)] for _ in range(nS)]
        Ab=agg([per_sess[i] for i in samp])
        SAb=strat_agg([per_strat[i] for i in samp])
        st=stats_from_agg(Ab,cuts,SAb)
        for k in boot: boot[k].append(st[k])
        for d in range(1,K+1): boot_pos[d].append(st['tool_pen'][d])
    def ci(vals):
        return [pctl(vals,0.025), pctl(vals,0.975)]
    out={'corpus':name,'n_train':len(train),'n_test':len(test),
         'interior_acc':point['interior_acc'],'interior_n':point['interior_n'],
         'entropy_cuts':cuts,
         'point':{k:point[k] for k in ['mean_tool_pen','mean_user_pen','mean_splice_pen',
                  'mean_diff_content','mean_diff_shift','within_strat_tool_pen']},
         'ci':{k:ci(boot[k]) for k in boot},
         'tool_pen_by_pos':{d:point['tool_pen'][d] for d in range(1,K+1)},
         'tool_acc_by_pos':{d:point['tool_acc'][d] for d in range(1,K+1)},
         'user_pen_by_pos':{d:point['user_pen'][d] for d in range(1,K+1)},
         'splice_pen_by_pos':{d:point['splice_pen'][d] for d in range(1,K+1)},
         'tool_pen_ci_by_pos':{d:ci(boot_pos[d]) for d in range(1,K+1)},
         }
    # per-position one-sided p (penalty<=0) + Holm
    pp={}
    for d in range(1,K+1):
        vals=[v for v in boot_pos[d] if v is not None]
        if vals:
            pp[d]=(sum(1 for v in vals if v<=0)+1)/(len(vals)+1)
        else: pp[d]=1.0
    hp=holm(pp)
    out['pos_pval_raw']={d:pp[d] for d in range(1,K+1)}
    out['pos_pval_holm']={d:hp[d][0] for d in range(1,K+1)}
    out['pos_holm_sig']={d:hp[d][1] for d in range(1,K+1)}
    out['n_pos_holm_sig']=sum(1 for d in range(1,K+1) if hp[d][1] and (point['tool_pen'][d] or 0)>0)
    return out

def main():
    print("parsing corpora...")
    cc=cc_streams(); print("  CC usable sessions:",len(cc))
    cx=codex_streams(); print("  Codex usable sessions:",len(cx))
    results=[]
    for name,sess in [('claude_code',cc),('codex',cx)]:
        if len(sess)<10:
            print("  SKIP %s (too few sessions=%d)"%(name,len(sess))); continue
        print("analyzing",name,"...")
        results.append(analyze(name,sess))
    base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir=os.path.join(base,'results'); os.makedirs(rdir,exist_ok=True)
    with open(os.path.join(rdir,'acceptance_proxy.json'),'w') as fh:
        json.dump(results,fh,indent=2,default=str)
    # console summary
    PR={'min_margin':0.02,'min_superiority':0.01}
    for r in results:
        print("\n"+"="*72); print("CORPUS:",r['corpus'],"(train=%d test=%d)"%(r['n_train'],r['n_test']))
        print("interior baseline acc = %.4f (n=%d)"%(r['interior_acc'],r['interior_n']))
        print("position |  tool_acc  tool_pen   [95%% CI]        holm_sig")
        for d in range(1,K+1):
            ta=r['tool_acc_by_pos'][d]; tp=r['tool_pen_by_pos'][d]; c=r['tool_pen_ci_by_pos'][d]
            print("   d=%d    | %s   %+.4f   [%+.4f,%+.4f]   %s"%(
                d, ("%.4f"%ta if ta is not None else " NA  "),
                tp if tp is not None else 0,
                c[0] if c[0] is not None else 0, c[1] if c[1] is not None else 0,
                r['pos_holm_sig'][d]))
        p=r['point']; ci=r['ci']
        def line(lbl,key):
            v=p[key]; c=ci[key]
            print("  %-22s = %+.4f  CI[%+.4f,%+.4f]"%(lbl, v if v is not None else 0,
                  c[0] if c[0] is not None else 0, c[1] if c[1] is not None else 0))
        line('mean_tool_pen',     'mean_tool_pen')
        line('mean_user_pen',     'mean_user_pen')
        line('mean_splice_pen',   'mean_splice_pen')
        line('diff_content(T-Spl)','mean_diff_content')
        line('diff_shift(T-User)', 'mean_diff_shift')
        line('within_strat_pen',  'within_strat_tool_pen')
        print("  Holm-sig positions (pen>0): %d / 8"%r['n_pos_holm_sig'])
        # gate
        A=(p['mean_tool_pen'] is not None and p['mean_tool_pen']>=PR['min_margin'] and ci['mean_tool_pen'][0] is not None and ci['mean_tool_pen'][0]>0 and r['n_pos_holm_sig']>=4)
        c1=(ci['mean_diff_content'][0] is not None and ci['mean_diff_content'][0]>0)
        c2=(ci['mean_diff_shift'][0] is not None and ci['mean_diff_shift'][0]>0)
        c3=(ci['within_strat_tool_pen'][0] is not None and ci['within_strat_tool_pen'][0]>0)
        print("  GATE: PASS-A(effect&margin&holm)=%s | C1 content-null superiority=%s | C2 context-shift superiority=%s | C3 entropy-survives=%s"%(A,c1,c2,c3))
        r['_gate']={'PASS_A':A,'C1_content':c1,'C2_shift':c2,'C3_entropy':c3,
                    'CANDIDATE_POSITIVE': bool(A and c1 and c2 and c3)}
    with open(os.path.join(rdir,'acceptance_proxy.json'),'w') as fh:
        json.dump(results,fh,indent=2,default=str)
    print("\nwrote",os.path.join(rdir,'acceptance_proxy.json'))
    return results

if __name__=='__main__':
    main()
