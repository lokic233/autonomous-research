#!/usr/bin/env python3
"""EXP-XHARNESS-r3: Cross-harness Cramer's V for CLAIM-0009 on Codex corpus,
apples-to-apples with EXP-0009 Claude-Code V=0.717. CPU/stdlib-only."""
import json, glob, os, re, math, random
from collections import defaultdict
ROOT=os.path.expanduser("~/.codex/sessions"); K=6; random.seed(0)
def err_class_codex(name,args,out):
    t=(out or "").lower()
    if name and 'web_search' in name:
        if 'showing 0' in t and 'filtered' in t: return 'websearch.empty'
        return 'websearch.other'
    if 'command not found' in t or re.search(r'not found: \S',t): return 'cmd.notfound'
    if 'no such file' in t or 'does not exist' in t: return 'fs.notfound'
    if 'file not found' in t or 'paper not found' in t: return 'fs.notfound'
    if 'permission denied' in t: return 'fs.perm'
    if 'file exists' in t: return 'fs.exists'
    if 'timed out' in t or 'timeout' in t or 'deadline' in t: return 'proc.timeout'
    if 'traceback' in t or 'syntaxerror' in t or 'modulenotfound' in t: return 'code.build'
    return 'proc.exit_nodetail'
def intent_codex(name,args):
    n=name or ''
    if 'web_search' in n or 'knowledge' in n: return 'WEB_INFO'
    if n in ('exec_command','write_stdin','exec'):
        cmd=''
        try: cmd=(json.loads(args) if isinstance(args,str) else args).get('cmd','')
        except: pass
        c=cmd or ''; h=''
        for p in c.strip().split():
            if '=' in p and not p.startswith('/'): continue
            if p in ('cd','sudo','time','env'): continue
            h=os.path.basename(p); break
        READ={'cat','ls','head','tail','grep','find','rg','wc','stat','sed','awk','less','more','sort','uniq','tree','du','diff'}
        WRITE={'tee','cp','mv','mkdir','touch','chmod','rm','ln'}
        if re.search(r'\bcurl\b|\bwget\b|\bfetch\b',c): return 'WEB_INFO'
        if h in READ: return 'FILE_READ'
        if h in WRITE: return 'FILE_WRITE'
        if re.search(r'>\s*\S',c) and not re.search(r'>/dev/null|2>&1',c): return 'FILE_WRITE'
        return 'EXEC'
    return 'EXEC'
def routing_tool(name,args):
    n=name or ''
    if n in ('exec_command','write_stdin'):
        cmd=''
        try: cmd=(json.loads(args) if isinstance(args,str) else args).get('cmd','')
        except: pass
        h=''
        for p in (cmd or '').strip().split():
            if '=' in p and not p.startswith('/'): continue
            if p in ('cd','sudo','time','env'): continue
            h=os.path.basename(p); break
        return 'exec:'+h
    return n
def parse(fp):
    pend={}; calls=[]
    for l in open(fp):
        try: d=json.loads(l)
        except: continue
        p=d.get('payload',{})
        if not isinstance(p,dict): continue
        pt=p.get('type')
        if pt=='function_call':
            pend[p.get('call_id')]={'name':p.get('name'),'args':p.get('arguments')}
        elif pt=='function_call_output':
            cid=p.get('call_id'); fc=pend.get(cid)
            if not fc: continue
            out=p.get('output','')
            if isinstance(out,dict): out=json.dumps(out)
            m=re.search(r'exited with code (\d+)',out)
            web=fc['name'] and 'web_search' in fc['name']
            if web: is_err=('showing 0' in out.lower() and 'filtered' in out.lower())
            else: is_err=bool(m) and m.group(1)!='0'
            calls.append({'name':fc['name'],'args':fc['args'],'intent':intent_codex(fc['name'],fc['args']),
                          'rt':routing_tool(fc['name'],fc['args']),'is_error':is_err,'text':out})
    return calls
files=glob.glob(os.path.join(ROOT,'**','*.jsonl'),recursive=True)
sessions=[parse(f) for f in files]; sessions=[s for s in sessions if len(s)>=2]
def recovered_modality(si,i,cls,intent,rt):
    s=sessions[si]; same=False; redir=False
    for j in range(i+1,min(i+1+K,len(s))):
        c=s[j]
        if c['is_error']: continue
        if c['intent']!=intent: continue
        if c['rt']==rt: same=True
        else: redir=True
    if same: return 'SAME_TOOL_RETRY'
    if redir: return 'CROSS_TOOL_REDIRECT'
    return None
rows=[]
for si,s in enumerate(sessions):
    for i,c in enumerate(s):
        if not c['is_error']: continue
        cls=err_class_codex(c['name'],c['args'],c['text'])
        m=recovered_modality(si,i,cls,c['intent'],c['rt'])
        if m: rows.append((cls,1 if m=='CROSS_TOOL_REDIRECT' else 0))
N=len(rows)
def cramers_v(rws):
    tab=defaultdict(lambda:[0,0])
    for cls,red in rws: tab[cls][red]+=1
    rtot=[0,0]; ctot={}; tot=0
    for cls,(s,r) in tab.items():
        rtot[0]+=s; rtot[1]+=r; ctot[cls]=s+r; tot+=s+r
    if tot==0: return 0.0,0.0,0
    chi=0.0
    for cls,(s,r) in tab.items():
        for k,obs in ((0,s),(1,r)):
            exp=rtot[k]*ctot[cls]/tot
            if exp>0: chi+=(obs-exp)**2/exp
    k=min(2,len(tab))
    v=math.sqrt(chi/(tot*(k-1))) if tot>0 and k>1 else 0.0
    return v,chi,len(tab)
V,chi,C=cramers_v(rows); df=(2-1)*(C-1)
labels=[r[1] for r in rows]; cls_seq=[r[0] for r in rows]; obsV=V; ge=0; B=5000
for _ in range(B):
    random.shuffle(labels)
    pv,_,_=cramers_v(list(zip(cls_seq,labels)))
    if pv>=obsV-1e-12: ge+=1
perm_p=(ge+1)/(B+1)
redir=sum(l for _,l in rows); p0=redir/N if N else 0
print("CODEX cross-harness (apples-to-apples with EXP-0009 Claude-Code V=0.717)")
print(f"sessions={len(sessions)} recovered-failures(N)={N} classes={C}")
print(f"global redirect rate p0={p0:.3f} (NULL)")
print(f"Cramers_V={V:.4f}  chi2={chi:.2f} df={df}  perm_p={perm_p:.4f}")
print("\nper-class among-recovered:")
tab=defaultdict(lambda:[0,0])
for cls,red in rows: tab[cls][red]+=1
print(f"{'class':22}{'n_rec':>6}{'redir':>6}{'same':>6}{'redir_share':>12}")
for cls in sorted(tab,key=lambda c:-(tab[c][0]+tab[c][1])):
    s,r=tab[cls]; n=s+r
    print(f"{cls:22}{n:>6}{r:>6}{s:>6}{(r/n if n else 0):>12.3f}")
