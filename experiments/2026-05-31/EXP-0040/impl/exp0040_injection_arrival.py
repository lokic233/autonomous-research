#!/usr/bin/env python3
"""
EXP-0040 — DESCRIPTIVE arrival-process probe for PROJ-0002 (prefix-cache INVALIDATION events).
The CLAIM-0012 pivot applied to the INJECTION stream rather than the failure stream.
Prior PROJ-0002 lanes asked PREDICTIVE/cost questions + the workload MAGNITUDE distribution
(EXP-0005, order-blind marginal). NONE measured the TEMPORAL ARRIVAL PROCESS of invalidations.

Estimand (purely descriptive): within a real agent session, are LARGE prefix-cache invalidation
events (large tool RESULTS) temporally OVER-DISPERSED (bursty) vs a within-session permutation
null that holds the result-size multiset fixed but shuffles ORDER?
  V1 = inj/seq>5%   (COLLISION RISK: front-loaded by S-growth = EXP-0005 accumulation axis)
  V2 = RAW top-1/3 size (S-growth REMOVED; the survivor EXP-0005's i.i.d. size model can't address)
CPU-only, deterministic (seed 20260531), no GPU/torch/model CLIs/memory probes.
"""
import json, glob, math, statistics, random, os
SEED=20260531; random.seed(SEED)

def claude_stream(f):
    S=0; out=[]
    for line in open(f):
        line=line.strip()
        if not line: continue
        try: d=json.loads(line)
        except: continue
        msg=d.get('message')
        if not (isinstance(msg,dict) and isinstance(msg.get('content'),list)): continue
        for b in msg['content']:
            if not isinstance(b,dict): continue
            t=b.get('type')
            if t=='text': S+=max(1,len(b.get('text','')))//4
            elif t=='tool_use': S+=max(1,len(json.dumps(b.get('input',{}))))//4
            elif t=='tool_result':
                cont=b.get('content','')
                if isinstance(cont,list):
                    cont=' '.join(str(x.get('text','')) if isinstance(x,dict) else str(x) for x in cont)
                R=max(1,len(str(cont)))//4
                out.append((R, R/max(1,max(R,S)))); S+=R
    return out

def codex_stream(f):
    S=0; out=[]
    for line in open(f):
        line=line.strip()
        if not line: continue
        try: d=json.loads(line)
        except: continue
        if d.get('type')!='response_item': continue
        p=d.get('payload',{}); pt=p.get('type')
        if pt=='message':
            c=p.get('content',[])
            txt=''.join(x.get('text','') for x in c if isinstance(x,dict)) if isinstance(c,list) else str(c)
            S+=max(1,len(txt))//4
        elif pt=='reasoning': S+=max(1,len(json.dumps(p.get('summary',''))))//4
        elif pt=='function_call': S+=max(1,len(json.dumps(p.get('arguments',''))))//4
        elif pt=='function_call_output':
            o=p.get('output','')
            if isinstance(o,dict): o=o.get('content',json.dumps(o))
            R=max(1,len(str(o)))//4
            out.append((R, R/max(1,max(R,S)))); S+=R
    return out

def runs_count(seq):
    R=1
    for i in range(1,len(seq)):
        if seq[i]!=seq[i-1]: R+=1
    return R

def runs_z(seq):
    n1=sum(seq); n0=len(seq)-n1
    if n1==0 or n0==0: return None
    R=runs_count(seq); n=n0+n1
    mu=2*n0*n1/n+1
    var=(2*n0*n1*(2*n0*n1-n))/(n*n*(n-1))
    if var<=0: return None
    return (R-mu)/math.sqrt(var)

def perm_p(binseq, nperm=1500):
    obs=runs_count(binseq); le=0; s=list(binseq)
    for _ in range(nperm):
        random.shuffle(s)
        if runs_count(s)<=obs: le+=1
    return (le+1)/(nperm+1)

def analyze(name, files, reader):
    streams=[reader(f) for f in files]
    streams=[s for s in streams if len(s)>=8]
    res={}
    for tag in ('V1_injseq_gt5pct','V2_rawtop1_3'):
        zs=[]; pps=[]; posf=[]; usable=0; n1=0; ntot=0
        for st in streams:
            if tag.startswith('V2'):
                Rs=sorted(R for R,_ in st); cut=Rs[int(len(Rs)*2/3)]
                b=[1 if R>cut else 0 for (R,_) in st]
            else:
                b=[1 if ios>0.05 else 0 for (_,ios) in st]
            z=runs_z(b)
            if z is None: continue
            usable+=1; zs.append(z); n1+=sum(b); ntot+=len(b)
            idx=[i/(len(b)-1) for i,v in enumerate(b) if v]
            if idx: posf.append(statistics.mean(idx))
            pps.append(perm_p(b))
        res[tag]={
            'usable_sessions':usable,'big_rate':round(n1/max(1,ntot),4),
            'runs_Z_mean':round(statistics.mean(zs),3) if zs else None,
            'runs_Z_median':round(statistics.median(zs),3) if zs else None,
            'stouffer_Z':round(sum(zs)/math.sqrt(len(zs)),3) if zs else None,
            'sessions_Z_lt_neg1':sum(1 for z in zs if z<-1),
            'mean_norm_position_of_big':round(statistics.mean(posf),3) if posf else None,
            'sessions_frontloaded_pos_lt_0.4':sum(1 for p in posf if p<0.4),
            'n_sessions_pos':len(posf),
            'perm_p_median':round(statistics.median(pps),4) if pps else None,
            'perm_p_lt_0.05':sum(1 for p in pps if p<0.05),
        }
    return {'harness':name,'n_usable':len(streams),'results':res}

cl=glob.glob('/Users/dengcchi/.claude/projects/*/*.jsonl')
cx=glob.glob('/Users/dengcchi/.codex/sessions/*/*/*/*.jsonl')
out={'seed':SEED,'harnesses':[]}
for nm,fs,rd in (('claude_code',cl,claude_stream),('codex',cx,codex_stream)):
    out['harnesses'].append(analyze(nm,fs,rd))
print(json.dumps(out,indent=2))
od=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
json.dump(out, open(os.path.join(od,'results','results.json'),'w'), indent=2)
