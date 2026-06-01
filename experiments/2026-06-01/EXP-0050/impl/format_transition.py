#!/usr/bin/env python3
"""
EXP-0050 (L0, CPU, stdlib-only) — CLAIM-0015 / PROJ-0004.
Format-Transition Speculation Cost in Speculative Decoding for Agent Trajectories.

Builds ON the EXP-0046 surviving finding (replicated single-token d=1 acceptance collapse) and tests the
CLAIM-0015 reframe: is the d=1 cost PREDICTABLE model-free from the injected payload's FORMAT CLASS, and
does format-class ADD predictive value OVER a length+entropy JOINT baseline?

Proxy (carried from EXP-0046, honest limits in impl/preregistration.md sec 1):
  draft  = trigram-backoff top-1 next-token predictor (HELD-OUT split; out-of-sample labels via cross-fit).
  target = realized assistant token.  accept := (draft top-1 == realized token).

Reuses EXP-0046 corpus parsing (CC tool_result join, Codex call_id dedup), trigram predictor + entropy,
and bootstrap idioms. ADDS: event-based extraction (keeps raw payload), regex format classifier,
per-transition AUC (format vs length+entropy joint vs draft-entropy), paired-bootstrap dAUC, RE-3..RE-8.

Pre-registration: impl/preregistration.md (LOCKED 2026-06-01T12:57:14Z, BEFORE this run).
"""
import json, glob, os, re, math, random, time
from collections import defaultdict, Counter

random.seed(20260601)
K = 8
B = 2000
HOME = os.path.expanduser('~')
TOKRE = re.compile(r"\w+|[^\w\s]")

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

# ---------------- EVENT extraction: per session -> list of (origin, raw_text) in file order ----------
def cc_events():
    fs = sorted(glob.glob(os.path.join(HOME,'.claude','projects','*','*.jsonl')))
    sessions={}
    for f in fs:
        evs=[]
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
                    if txt: evs.append(('asst',txt))
                elif bt=='tool_result':
                    evs.append(('tool',block_text(b)))
                elif role=='user' and bt=='text':
                    txt=b.get('text','')
                    if txt: evs.append(('user',txt))
        # usable filter: >=50 asst tokens & >=1 tool result
        n_asst=sum(len(tokenize(t)) for o,t in evs if o=='asst')
        if n_asst>=50 and any(o=='tool' for o,_ in evs):
            sessions[f]=evs
    return sessions

def codex_events():
    fs = sorted(glob.glob(os.path.join(HOME,'.codex','sessions','**','*.jsonl'), recursive=True))
    sessions={}
    for f in fs:
        evs=[]; seen=set(); prev_asst=None
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
                if txt and txt!=prev_asst: evs.append(('asst',txt)); prev_asst=txt
            elif t=='message' and p.get('role')=='assistant':
                c=p.get('content'); txt=''
                if isinstance(c,list): txt=' '.join(x.get('text','') for x in c if isinstance(x,dict))
                if txt and txt!=prev_asst: evs.append(('asst',txt)); prev_asst=txt
            elif t=='user_message' or (t=='message' and p.get('role')=='user'):
                txt=p.get('message','')
                if not txt:
                    c=p.get('content')
                    if isinstance(c,list): txt=' '.join(x.get('text','') for x in c if isinstance(x,dict))
                if txt: evs.append(('user',txt))
            elif t=='function_call_output':
                cid=p.get('call_id')
                if cid in seen: continue
                seen.add(cid)
                evs.append(('tool',str(p.get('output',''))))
        n_asst=sum(len(tokenize(t)) for o,t in evs if o=='asst')
        if n_asst>=50 and any(o=='tool' for o,_ in evs):
            sessions[f]=evs
    return sessions

# ---------------- token stream from events (for trigram + interior baseline) ----------------
def events_to_stream(evs):
    stream=[]
    for o,t in evs:
        for tk in tokenize(t): stream.append((o,tk))
    return stream

# ---------------- regex FORMAT classifier (locked rules; pre-reg sec 6) -------------------------
_SCALAR = re.compile(r'^[\s]*(-?\d+(\.\d+)?|true|false|null|none|yes|no|nan|[\w./:-]{1,24})[\s]*$', re.I)
_JSONK  = re.compile(r'("[^"]+"\s*:)|(\'[^\']+\'\s*:)')
_PIPE   = re.compile(r'^\s*\|.*\|\s*$')
_ALIGN  = re.compile(r'\S {2,}\S')
_FENCE  = re.compile(r'```')
_CODEKW = re.compile(r'\b(def|function|class|import|return|const|let|var|public|private|void|#include|func|package)\b')
_BRACKETS = set('{};()=<>[]')

def classify_format(payload):
    s = (payload or '')
    st = s.strip()
    if not st: return 'scalar'
    lines = [ln for ln in s.splitlines() if ln.strip()!='']
    # 1. scalar: single short line
    if len(lines) <= 1 and _SCALAR.match(st):
        return 'scalar'
    # 2. json
    if (st[0] in '{[' ) and _JSONK.search(st):
        return 'json'
    if _JSONK.search(st) and st.count('"')>=4 and (st[0] in '{['):
        return 'json'
    # 3. table
    pipe_rows = sum(1 for ln in lines if _PIPE.match(ln))
    align_rows = sum(1 for ln in lines if _ALIGN.search(ln))
    if len(lines) >= 2 and (pipe_rows >= 2 or align_rows >= 2):
        return 'table'
    # 4. code
    if _FENCE.search(s):
        return 'code'
    nchar = max(1, len(s))
    bdens = sum(1 for ch in s if ch in _BRACKETS) / nchar
    if bdens >= 0.06 or len(_CODEKW.findall(s)) >= 2:
        return 'code'
    # 5. stdout: multiline non-structured
    if len(lines) >= 2:
        return 'stdout'
    # 6. prose default
    return 'prose'

def shannon_entropy(toks):
    if not toks: return 0.0
    c=Counter(toks); n=len(toks); H=0.0
    for v in c.values():
        p=v/n; H-=p*math.log2(p)
    return H

# ---------------- trigram predictor (carried from EXP-0046) ----------------
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

# ---------------- extract per-session transitions (tool->asst and user->asst) ----------------
def extract_transitions(evs, predict, sess_id):
    """Return list of transition dicts using `predict` for accept labels (out-of-sample)."""
    trans=[]
    n=len(evs)
    for i in range(1,n):
        o,txt = evs[i]
        po,ptxt = evs[i-1]
        if o!='asst': continue
        if po not in ('tool','user'): continue
        asst_toks = tokenize(txt)[:K]
        if not asst_toks: continue
        ptoks = tokenize(ptxt)
        pc2 = ptoks[-2] if len(ptoks)>=2 else None
        pc1 = ptoks[-1] if len(ptoks)>=1 else None
        # depth-wise accept with rolling context (matches EXP-0046 splice rolling)
        acc=[None]*(K+1); 
        d1_H=None
        for d in range(1,len(asst_toks)+1):
            if d==1: cc2,cc1=pc2,pc1
            elif d==2: cc2,cc1=pc1,asst_toks[0]
            else: cc2,cc1=asst_toks[d-3],asst_toks[d-2]
            top1,H=predict(cc2,cc1)
            acc[d]=1 if top1==asst_toks[d-1] else 0
            if d==1: d1_H=H
        rec={'sess':sess_id,'origin':po,'acc':acc,'accept_d1':acc[1],'d1_H':d1_H}
        if po=='tool':
            fmt=classify_format(ptxt)
            rec['fmt']=fmt
            rec['plen']=len(ptoks)
            rec['pent']=shannon_entropy(ptoks)
        else:
            rec['fmt']='user_prose'; rec['plen']=len(ptoks); rec['pent']=shannon_entropy(ptoks)
        trans.append(rec)
    return trans

# ---------------- interior baseline accept (carried EXP-0046, stride-capped) ----------------
INTERIOR_CAP=1500
def interior_accept(evs, predict):
    stream=events_to_stream(evs)
    toks=[t for _,t in stream]; ori=[o for o,_ in stream]
    n=len(toks); last=None; dist=0; idxs=[]
    for i in range(n):
        o=ori[i]
        if o in ('tool','user'): last=o; dist=0
        elif o=='asst':
            dist+=1
            if dist>K: idxs.append(i)
    if not idxs: return (0,0)
    if len(idxs)>INTERIOR_CAP:
        stride=len(idxs)/INTERIOR_CAP
        sel=[idxs[int(k*stride)] for k in range(INTERIOR_CAP)]
    else: sel=idxs
    na=0; nn=0
    for i in sel:
        t=toks[i]; c2=toks[i-2] if i>=2 else None; c1=toks[i-1] if i>=1 else None
        top1,_=predict(c2,c1); na+=(1 if top1==t else 0); nn+=1
    return (nn,na)

# ---------------- AUC (rank-based Mann-Whitney, tie-aware) ----------------
def auc(score_label):
    pos=[s for s,l in score_label if l==1]; neg=[s for s,l in score_label if l==0]
    npos=len(pos); nneg=len(neg)
    if npos==0 or nneg==0: return None
    data=sorted(score_label, key=lambda x:x[0])
    # average ranks
    ranks=[0.0]*len(data); i=0
    while i<len(data):
        j=i
        while j+1<len(data) and data[j+1][0]==data[i][0]: j+=1
        avg=(i+j)/2.0+1.0
        for k in range(i,j+1): ranks[k]=avg
        i=j+1
    rpos=sum(ranks[k] for k in range(len(data)) if data[k][1]==1)
    return (rpos - npos*(npos+1)/2.0)/(npos*nneg)

# ---------------- logistic regression (stdlib gradient descent) ----------------
def fit_logistic(X, y, l2=1e-3, iters=2000, lr=0.5):
    nfeat=len(X[0]) if X else 0
    # standardize
    means=[0.0]*nfeat; stds=[1.0]*nfeat
    n=len(X)
    for j in range(nfeat):
        col=[row[j] for row in X]
        m=sum(col)/n; means[j]=m
        var=sum((v-m)**2 for v in col)/n; stds[j]=math.sqrt(var) if var>1e-12 else 1.0
    Xs=[[(row[j]-means[j])/stds[j] for j in range(nfeat)] for row in X]
    w=[0.0]*nfeat; b=0.0
    for _ in range(iters):
        gw=[0.0]*nfeat; gb=0.0
        for idx in range(n):
            z=b+sum(w[j]*Xs[idx][j] for j in range(nfeat))
            p=1.0/(1.0+math.exp(-z)) if z>-50 else 0.0
            if z>50: p=1.0
            err=p-y[idx]
            for j in range(nfeat): gw[j]+=err*Xs[idx][j]
            gb+=err
        for j in range(nfeat): w[j]=w[j]-lr*(gw[j]/n + l2*w[j])
        b=b-lr*(gb/n)
    def score(row):
        z=b+sum(w[j]*((row[j]-means[j])/stds[j]) for j in range(nfeat))
        return z  # monotone in prob; fine for AUC/threshold
    return score, (w,b,means,stds)

def pctl(vals,p):
    s=sorted(v for v in vals if v is not None)
    if not s: return None
    pos=p*(len(s)-1); lo=int(math.floor(pos)); hi=int(math.ceil(pos)); fr=pos-lo
    return s[lo]*(1-fr)+s[hi]*fr

# ---------------- build models on FIT transitions, score EVAL transitions ----------------
def build_models(fit_trans):
    tool=[t for t in fit_trans if t['origin']=='tool']
    # format rate table (Laplace)
    by={}
    for t in tool:
        by.setdefault(t['fmt'],[0,0])
        by[t['fmt']][0]+=1; by[t['fmt']][1]+=t['accept_d1']
    fmt_rate={k:(a+1)/(nn+2) for k,(nn,a) in by.items()}
    glob_rate=(sum(t['accept_d1'] for t in tool)+1)/(len(tool)+2) if tool else 0.5
    # len+ent joint logistic
    X=[[math.log1p(t['plen']), t['pent']] for t in tool]; y=[t['accept_d1'] for t in tool]
    lenent_score,_=fit_logistic(X,y) if len(set(y))>1 and len(y)>=10 else (None,None)
    # draft-entropy logistic
    Xd=[[t['d1_H']] for t in tool]; yd=y
    drafte_score,_=fit_logistic(Xd,yd) if len(set(yd))>1 and len(yd)>=10 else (None,None)
    return fmt_rate,glob_rate,lenent_score,drafte_score

def score_eval(eval_tool, fmt_rate, glob_rate, lenent_score, drafte_score):
    rows=[]
    for t in eval_tool:
        sf=fmt_rate.get(t['fmt'],glob_rate)
        sl=lenent_score([math.log1p(t['plen']),t['pent']]) if lenent_score else 0.0
        sd=drafte_score([t['d1_H']]) if drafte_score else 0.0
        rows.append({'sess':t['sess'],'label':t['accept_d1'],'sf':sf,'sl':sl,'sd':sd})
    return rows

def paired_dauc(rows, key_a, key_b):
    """point dAUC = AUC(a)-AUC(b); paired cluster-bootstrap over sessions."""
    a0=auc([(r[key_a],r['label']) for r in rows]); b0=auc([(r[key_b],r['label']) for r in rows])
    point=(a0-b0) if (a0 is not None and b0 is not None) else None
    by_sess=defaultdict(list)
    for r in rows: by_sess[r['sess']].append(r)
    sess=list(by_sess.keys()); nS=len(sess); diffs=[]; aa=[]; bb=[]
    for _ in range(B):
        samp=[]
        for _ in range(nS): samp.extend(by_sess[sess[random.randrange(nS)]])
        av=auc([(r[key_a],r['label']) for r in samp]); bv=auc([(r[key_b],r['label']) for r in samp])
        if av is not None: aa.append(av)
        if bv is not None: bb.append(bv)
        if av is not None and bv is not None: diffs.append(av-bv)
    return {'point':point,'auc_a':a0,'auc_b':b0,
            'dauc_ci':[pctl(diffs,0.025),pctl(diffs,0.975)],
            'auc_a_ci':[pctl(aa,0.025),pctl(aa,0.975)],
            'auc_b_ci':[pctl(bb,0.025),pctl(bb,0.975)]}

# ---------------- RE-6 concentration + RE-3 dip + RE-5 + cost_d ----------------
def concentration_and_dips(eval_tool, eval_user, interior_pairs):
    # interior_acc pooled over eval sessions
    inn=sum(p[0] for p in interior_pairs); ina=sum(p[1] for p in interior_pairs)
    interior_acc=(ina/inn) if inn>0 else None
    # accept(d) pooled over tool transitions
    def acc_at(d, trs):
        nn=0; aa=0
        for t in trs:
            if t['acc'][d] is not None: nn+=1; aa+=t['acc'][d]
        return (nn, aa)
    cost_point={}
    for d in range(1,K+1):
        nn,aa=acc_at(d,eval_tool); r=(aa/nn) if nn>0 else None
        cost_point[d]=(interior_acc-r) if (r is not None and interior_acc is not None) else None
    # RE-6 share with bootstrap over sessions
    by_sess=defaultdict(list)
    for t in eval_tool: by_sess[t['sess']].append(t)
    sess=list(by_sess.keys()); nS=len(sess)
    def share_from(trs):
        costs={}
        for d in range(1,K+1):
            nn,aa=acc_at(d,trs); r=(aa/nn) if nn>0 else None
            costs[d]=(interior_acc-r) if (r is not None and interior_acc is not None) else 0.0
        denom=sum(abs(costs[d]) for d in range(1,K+1))
        return (abs(costs[1])/denom) if denom>1e-12 else None
    share_point=share_from(eval_tool)
    shares=[]
    for _ in range(B):
        samp=[]
        for _ in range(nS): samp.extend(by_sess[sess[random.randrange(nS)]])
        s=share_from(samp)
        if s is not None: shares.append(s)
    share_ci=[pctl(shares,0.025),pctl(shares,0.975)]
    # RE-3 gap = mean(accept_d1|prose-control) - mean(accept_d1|nonprose)
    nonprose=[t for t in eval_tool if t['fmt'] in ('json','code','stdout','table','scalar')]
    prosectl=[t for t in eval_tool if t['fmt']=='prose']+list(eval_user)
    def mean_d1(trs):
        v=[t['accept_d1'] for t in trs if t['accept_d1'] is not None]
        return sum(v)/len(v) if v else None
    mp=mean_d1(prosectl); mn=mean_d1(nonprose)
    gap_point=(mp-mn) if (mp is not None and mn is not None) else None
    # bootstrap gap over sessions (pool tool+user by session)
    by_sess2=defaultdict(lambda:{'np':[],'pc':[]})
    for t in nonprose: by_sess2[t['sess']]['np'].append(t['accept_d1'])
    for t in prosectl: by_sess2[t['sess']]['pc'].append(t['accept_d1'])
    sess2=list(by_sess2.keys()); nS2=len(sess2); gaps=[]
    for _ in range(B):
        npv=[]; pcv=[]
        for _ in range(nS2):
            s=sess2[random.randrange(nS2)]; npv.extend(by_sess2[s]['np']); pcv.extend(by_sess2[s]['pc'])
        if npv and pcv: gaps.append(sum(pcv)/len(pcv)-sum(npv)/len(npv))
    gap_ci=[pctl(gaps,0.025),pctl(gaps,0.975)]
    # RE-5 recovered fraction of wasted draft FLOPs + bootstrap
    def reject(d,trs):
        nn,aa=acc_at(d,trs); return (1-aa/nn) if nn>0 else 0.0
    def recov_from(trs):
        rj=[reject(d,trs) for d in range(1,K+1)]; den=sum(rj)
        return (rj[0]/den) if den>1e-12 else None
    recov_point=recov_from(eval_tool)
    recs=[]
    for _ in range(B):
        samp=[]
        for _ in range(nS): samp.extend(by_sess[sess[random.randrange(nS)]])
        r=recov_from(samp)
        if r is not None: recs.append(r)
    recov_ci=[pctl(recs,0.025),pctl(recs,0.975)]
    p_reject_d1=reject(1,eval_tool)
    return {'interior_acc':interior_acc,'interior_n':inn,
            'cost_by_d':cost_point,'accept_d1_overall':1-p_reject_d1,
            'share_point':share_point,'share_ci':share_ci,
            'gap_point':gap_point,'gap_ci':gap_ci,'mean_prose_d1':mp,'mean_nonprose_d1':mn,
            'p_reject_d1':p_reject_d1,'recov_point':recov_point,'recov_ci':recov_ci}

# ---------------- per-corpus within analysis ----------------
def split_sessions(keys):
    s0=[]; s1=[]
    for kpath in keys:
        h=sum(ord(ch) for ch in os.path.basename(kpath))
        (s0 if h%2==0 else s1).append(kpath)
    if len(s0)<5 or len(s1)<5:
        s0=keys[::2]; s1=keys[1::2]
    return s0,s1

def n_table(trans):
    by={}
    for t in trans:
        if t['origin']!='tool': continue
        by.setdefault(t['fmt'],[0,0]); by[t['fmt']][0]+=1; by[t['fmt']][1]+=t['accept_d1']
    return {k:{'n':nn,'n_accept':a,'accept_rate':a/nn if nn else None} for k,(nn,a) in by.items()}

def within_corpus(name, sessions):
    keys=sorted(sessions.keys()); s0,s1=split_sessions(keys)
    predA=make_predictor(*build_ngram([events_to_stream(sessions[k]) for k in s0]))  # train S0
    predB=make_predictor(*build_ngram([events_to_stream(sessions[k]) for k in s1]))  # train S1
    # cross-fit labels: S1 transitions <- predA ; S0 transitions <- predB
    fit_trans=[]   # S0 transitions (labels via predB)
    for k in s0: fit_trans+=extract_transitions(sessions[k],predB,k)
    eval_trans=[]  # S1 transitions (labels via predA)
    for k in s1: eval_trans+=extract_transitions(sessions[k],predA,k)
    eval_tool=[t for t in eval_trans if t['origin']=='tool']
    eval_user=[t for t in eval_trans if t['origin']=='user']
    interior_pairs=[interior_accept(sessions[k],predA) for k in s1]
    # models on S0, score S1
    fmt_rate,glob_rate,lenent_score,drafte_score=build_models(fit_trans)
    rows=score_eval(eval_tool,fmt_rate,glob_rate,lenent_score,drafte_score)
    re1=paired_dauc(rows,'sf','sl')   # format vs len+ent joint
    re7=paired_dauc(rows,'sf','sd')   # format vs draft-entropy
    conc=concentration_and_dips(eval_tool,eval_user,interior_pairs)
    # RE-7 FDR/FNR at train-Youden threshold of M_format on eval
    fdr,fnr,thr=fdr_fnr(fit_trans,eval_tool,fmt_rate,glob_rate)
    out={'corpus':name,'n_sessions':len(keys),'n_fit_sessions':len(s0),'n_eval_sessions':len(s1),
         'n_eval_tool_trans':len(eval_tool),'n_eval_user_trans':len(eval_user),
         'fmt_rate_train':fmt_rate,'n_table_eval':n_table(eval_trans),
         'RE1_format_vs_lenent':re1,'RE7_format_vs_draftent':re7,
         'RE7_FDR':fdr,'RE7_FNR':fnr,'RE7_threshold':thr,
         'concentration_RE6':{'share_point':conc['share_point'],'share_ci':conc['share_ci']},
         'RE3_prose_gap':{'gap_point':conc['gap_point'],'gap_ci':conc['gap_ci'],
                          'mean_prose_d1':conc['mean_prose_d1'],'mean_nonprose_d1':conc['mean_nonprose_d1']},
         'RE5_flops':{'p_reject_d1':conc['p_reject_d1'],'recov_frac_point':conc['recov_point'],
                      'recov_frac_ci':conc['recov_ci']},
         'interior_acc':conc['interior_acc'],'interior_n':conc['interior_n'],
         'cost_by_d':conc['cost_by_d'],'accept_d1_overall':conc['accept_d1_overall']}
    return out

def fdr_fnr(fit_trans, eval_tool, fmt_rate, glob_rate):
    # decision: SUPPRESS d=1 (positive = token REJECTED). predict suppress if (1 - fmt_rate) high.
    # choose threshold on FIT via Youden J over suppression score = 1 - fmt_rate
    def sup_score(t): return 1.0 - fmt_rate.get(t['fmt'],glob_rate)
    fit_tool=[t for t in fit_trans if t['origin']=='tool']
    cand=sorted(set(sup_score(t) for t in fit_tool))
    bestJ=-1; bestT=0.5
    for thr in cand:
        tp=fp=tn=fn=0
        for t in fit_tool:
            pred=1 if sup_score(t)>=thr else 0
            actual=1 if t['accept_d1']==0 else 0   # reject = positive
            if pred and actual: tp+=1
            elif pred and not actual: fp+=1
            elif not pred and actual: fn+=1
            else: tn+=1
        tpr=tp/(tp+fn) if (tp+fn) else 0; fpr=fp/(fp+tn) if (fp+tn) else 0
        J=tpr-fpr
        if J>bestJ: bestJ=J; bestT=thr
    tp=fp=tn=fn=0
    for t in eval_tool:
        pred=1 if sup_score(t)>=bestT else 0
        actual=1 if t['accept_d1']==0 else 0
        if pred and actual: tp+=1
        elif pred and not actual: fp+=1
        elif not pred and actual: fn+=1
        else: tn+=1
    fdr=fp/(tp+fp) if (tp+fp) else None   # 1-precision
    fnr=fn/(tp+fn) if (tp+fn) else None   # 1-recall
    return fdr,fnr,bestT

# ---------------- RE-4 cross-corpus ----------------
def cross_corpus(name_tr, sess_tr, name_te, sess_te):
    predTr=make_predictor(*build_ngram([events_to_stream(v) for v in sess_tr.values()]))
    fit_trans=[]
    for k,v in sess_tr.items(): fit_trans+=extract_transitions(v,predTr,k)
    eval_trans=[]
    for k,v in sess_te.items(): eval_trans+=extract_transitions(v,predTr,k)  # out-of-sample (foreign corpus)
    eval_tool=[t for t in eval_trans if t['origin']=='tool']
    fmt_rate,glob_rate,lenent_score,drafte_score=build_models(fit_trans)
    rows=score_eval(eval_tool,fmt_rate,glob_rate,lenent_score,drafte_score)
    re1=paired_dauc(rows,'sf','sl')
    return {'train':name_tr,'test':name_te,'n_eval_tool':len(eval_tool),'RE1_format_vs_lenent':re1}

# ---------------- RE-8 classifier latency ----------------
def classifier_latency(all_sessions):
    payloads=[]
    for sess in all_sessions:
        for o,t in sess:
            if o=='tool': payloads.append(t)
    if not payloads: return None
    # warm
    for p in payloads[:200]: classify_format(p)
    reps=[]
    for _ in range(3):
        t0=time.perf_counter()
        for p in payloads: classify_format(p)
        reps.append((time.perf_counter()-t0)/len(payloads))
    reps.sort()
    return {'n_payloads':len(payloads),'median_sec_per_payload':reps[1],
            'us_per_payload':reps[1]*1e6}

def main():
    print("parsing corpora (event-based)...")
    cc=cc_events(); print("  CC usable sessions:",len(cc))
    cx=codex_events(); print("  Codex usable sessions:",len(cx))
    results={'within':[], 'cross':[], 'meta':{}}
    corp={'claude_code':cc,'codex':cx}
    for name in ('claude_code','codex'):
        if len(corp[name])<10:
            print("  SKIP within %s (sessions=%d)"%(name,len(corp[name]))); continue
        print("within-corpus:",name); results['within'].append(within_corpus(name,corp[name]))
    if len(cc)>=10 and len(cx)>=10:
        print("cross-corpus CC->Codex"); results['cross'].append(cross_corpus('claude_code',cc,'codex',cx))
        print("cross-corpus Codex->CC"); results['cross'].append(cross_corpus('codex',cx,'claude_code',cc))
    print("RE-8 classifier latency"); results['meta']['RE8_latency']=classifier_latency(list(cc.values())+list(cx.values()))
    base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir=os.path.join(base,'results'); os.makedirs(rdir,exist_ok=True)
    with open(os.path.join(rdir,'format_transition.json'),'w') as fh:
        json.dump(results,fh,indent=2,default=str)
    # console summary
    for r in results['within']:
        print("\n"+"="*78); print("WITHIN CORPUS:",r['corpus'],
              "(fit_sess=%d eval_sess=%d eval_tool_trans=%d)"%(r['n_fit_sessions'],r['n_eval_sessions'],r['n_eval_tool_trans']))
        print("  interior_acc=%.4f  accept_d1_overall=%.4f"%(r['interior_acc'] or 0, r['accept_d1_overall'] or 0))
        print("  n per format-class (eval):")
        for k,v in sorted(r['n_table_eval'].items()):
            print("    %-10s n=%-5d accept=%-4d rate=%.4f"%(k,v['n'],v['n_accept'],v['accept_rate'] or 0))
        re1=r['RE1_format_vs_lenent']; re7=r['RE7_format_vs_draftent']
        print("  [RE-1 LOAD-BEARING] AUC(format)=%.4f AUC(len+ent)=%.4f dAUC=%.4f CI=[%.4f,%.4f]  PASS=%s"%(
            re1['auc_a'] or 0, re1['auc_b'] or 0, re1['point'] or 0,
            re1['dauc_ci'][0] or 0, re1['dauc_ci'][1] or 0,
            (re1['dauc_ci'][0] is not None and re1['dauc_ci'][0]>0)))
        print("  [RE-7] AUC(format)=%.4f AUC(draft-ent)=%.4f dAUC=%.4f CI=[%.4f,%.4f]  FDR=%s FNR=%s"%(
            re7['auc_a'] or 0, re7['auc_b'] or 0, re7['point'] or 0,
            re7['dauc_ci'][0] or 0, re7['dauc_ci'][1] or 0, r['RE7_FDR'], r['RE7_FNR']))
        c=r['concentration_RE6']; print("  [RE-6] d=1 share=%.4f CI=[%.4f,%.4f]  PASS(>0.80)=%s"%(
            c['share_point'] or 0, c['share_ci'][0] or 0, c['share_ci'][1] or 0,
            (c['share_ci'][0] is not None and c['share_ci'][0]>0.80)))
        g=r['RE3_prose_gap']; print("  [RE-3] prose_d1=%.4f nonprose_d1=%.4f gap=%.4f CI=[%.4f,%.4f]  PASS(>0)=%s"%(
            g['mean_prose_d1'] or 0, g['mean_nonprose_d1'] or 0, g['gap_point'] or 0,
            g['gap_ci'][0] or 0, g['gap_ci'][1] or 0,
            (g['gap_ci'][0] is not None and g['gap_ci'][0]>0)))
        f=r['RE5_flops']; print("  [RE-5] P(reject@d1)=%.4f recov_frac_wasted_draft=%.4f CI=[%.4f,%.4f]"%(
            f['p_reject_d1'] or 0, f['recov_frac_point'] or 0, f['recov_frac_ci'][0] or 0, f['recov_frac_ci'][1] or 0))
    for r in results['cross']:
        re1=r['RE1_format_vs_lenent']
        print("\n[RE-4 cross] train=%s test=%s n=%d  dAUC(format-lenent)=%.4f CI=[%.4f,%.4f]"%(
            r['train'],r['test'],r['n_eval_tool'], re1['point'] or 0,
            re1['dauc_ci'][0] or 0, re1['dauc_ci'][1] or 0))
    lat=results['meta']['RE8_latency']
    if lat: print("\n[RE-8] classifier: %.2f us/payload over %d payloads (draft-fwd band 50-1000us)"%(
        lat['us_per_payload'],lat['n_payloads']))
    print("\nwrote",os.path.join(rdir,'format_transition.json'))
    return results

if __name__=='__main__':
    main()
