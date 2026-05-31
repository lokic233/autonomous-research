#!/usr/bin/env python3
"""Cross-harness replication check (Codex CLI corpus) for CLAIM-0009 gate-taxonomy + modality.
CPU/stdlib-only. Mirrors EXP-0009 logic adapted to Codex rollout JSONL schema."""
import json, glob, os, re
from collections import Counter, defaultdict

ROOT=os.path.expanduser("~/.codex/sessions")
K=6

def err_class_codex(name, args, out):
    t=(out or "").lower()
    # Codex web tool is an MCP tool: three_pai_external_web_search -> 'showing 0' = empty result
    if name and 'web_search' in name:
        if 'showing 0' in t and 'filtered' in t: return 'websearch.empty'
        return 'websearch.other'
    if 'command not found' in t or re.search(r'not found: \S', t): return 'cmd.notfound'
    if 'no such file' in t or 'does not exist' in t: return 'fs.notfound'
    if 'file not found' in t or 'paper not found' in t: return 'fs.notfound'
    if 'permission denied' in t: return 'fs.perm'
    if 'file exists' in t: return 'fs.exists'
    if 'timed out' in t or 'timeout' in t or 'deadline' in t: return 'proc.timeout'
    if 'traceback' in t or 'syntaxerror' in t or 'modulenotfound' in t: return 'code.build'
    return 'proc.exit_nodetail'

def intent_codex(name, args):
    n=name or ''
    if 'web_search' in n or 'knowledge' in n: return 'WEB_INFO'
    if n in ('exec_command','write_stdin','exec'):
        cmd=''
        try: cmd=(json.loads(args) if isinstance(args,str) else args).get('cmd','')
        except: pass
        c=cmd or ''
        h=''
        for p in c.strip().split():
            if '=' in p and not p.startswith('/'): continue
            if p in ('cd','sudo','time','env'): continue
            h=os.path.basename(p); break
        READ={'cat','ls','head','tail','grep','find','rg','wc','stat','sed','awk','less','more','sort','uniq','tree','du','diff'}
        WRITE={'tee','cp','mv','mkdir','touch','chmod','rm','ln'}
        if re.search(r'\bcurl\b|\bwget\b|\bfetch\b', c): return 'WEB_INFO'
        if h in READ: return 'FILE_READ'
        if h in WRITE: return 'FILE_WRITE'
        if re.search(r'>\s*\S', c) and not re.search(r'>/dev/null|2>&1', c): return 'FILE_WRITE'
        return 'EXEC'
    return 'EXEC'

def routing_tool(name, args):
    """canonical tool id: exec_command collapsed to exec:<headcmd> so a true tool switch
    (exec->web_search) differs from in-place exec reinvocation."""
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
    """ordered tool calls: name,args,intent,routing,is_error,err_text"""
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
            web = fc['name'] and 'web_search' in fc['name']
            if web:
                is_err = ('showing 0' in out.lower() and 'filtered' in out.lower())
            else:
                is_err = bool(m) and m.group(1)!='0'
            calls.append({'name':fc['name'],'args':fc['args'],
                          'intent':intent_codex(fc['name'],fc['args']),
                          'rt':routing_tool(fc['name'],fc['args']),
                          'is_error':is_err,'text':out})
    return calls

# GATE-TYPE map for Codex (analogous to EXP-0012 3-level)
def gate_type(cls):
    # In Codex there is NO web_disabled hard-block (web tool is granted) and NO perm-grant gate.
    # All observed failures are TRANSIENT (fixable in place / re-runnable). Documented explicitly.
    return 'TRANSIENT'

files=glob.glob(os.path.join(ROOT,'**','*.jsonl'),recursive=True)
sessions=[parse(f) for f in files]
sessions=[s for s in sessions if len(s)>=2]
nf=0; ncall=0
fails=[]  # (sess_idx, pos, cls, intent, rt)
for si,s in enumerate(sessions):
    ncall+=len(s)
    for i,c in enumerate(s):
        if c['is_error']:
            nf+=1
            cls=err_class_codex(c['name'],c['args'],c['text'])
            fails.append((si,i,cls,c['intent'],c['rt']))

# recovery + modality (BROAD: same-intent retry success within K = SAME_TOOL; diff-tool same-intent success = REDIRECT)
def recovered_modality(si,i,cls,intent,rt):
    s=sessions[si]
    same=False; redir=False
    for j in range(i+1, min(i+1+K, len(s))):
        c=s[j]
        if c['is_error']: continue
        if c['intent']!=intent: continue
        if c['rt']==rt: same=True
        else: redir=True
    if same: return 'SAME_TOOL_RETRY'
    if redir: return 'CROSS_TOOL_REDIRECT'
    return None

cls_counts=Counter(); cls_recov=Counter(); cls_redir=Counter(); cls_same=Counter()
glob_recov=0
for (si,i,cls,intent,rt) in fails:
    cls_counts[cls]+=1
    m=recovered_modality(si,i,cls,intent,rt)
    if m: 
        glob_recov+=1
        cls_recov[cls]+=1
        if m=='CROSS_TOOL_REDIRECT': cls_redir[cls]+=1
        else: cls_same[cls]+=1

print(f"Codex corpus: {len(sessions)} sessions, {ncall} tool calls, {nf} ground-truth failures")
print(f"global broad-recovery rate: {glob_recov}/{nf} = {glob_recov/max(nf,1):.3f}")
print()
print(f"{'class':22} {'n':>4} {'recov':>5} {'rec_rate':>8} {'redir':>5} {'same':>5} {'redir_share':>11} gate")
for cls,n in cls_counts.most_common():
    rc=cls_recov[cls]; rd=cls_redir[cls]; sm=cls_same[cls]
    rr=rc/n if n else 0
    rs=rd/rc if rc else float('nan')
    print(f"{cls:22} {n:>4} {rc:>5} {rr:>8.3f} {rd:>5} {sm:>5} {rs:>11.3f} {gate_type(cls)}")
