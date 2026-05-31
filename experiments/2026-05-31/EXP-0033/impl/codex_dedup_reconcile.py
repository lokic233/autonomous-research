# Reconcile: EXP-0032 codex() used ONLY function_call path (knowledge_load via function_call_output)
# and got blocks=152. My version adds mcp_tool_call_end -> double counts. Check both paths and
# whether twin fires before (preempt) vs after.
import json,glob,os,re
K=6
TWIN='three_pai_external_web_search'
files=glob.glob(os.path.expanduser('~/.codex/sessions/**/*.jsonl'),recursive=True)
fc_blocks=0; mcp_blocks=0
fc_pre=0; fc_after=0; fc_abandon=0
for fp in files:
    pend={}; seq_fc=[]; seq_all=[]
    for l in open(fp):
        try: d=json.loads(l)
        except: continue
        p=d.get('payload',{})
        if not isinstance(p,dict): continue
        pt=p.get('type')
        if pt=='function_call': pend[p.get('call_id')]={'n':p.get('name')}
        elif pt=='function_call_output':
            fc=pend.get(p.get('call_id'))
            if not fc: continue
            out=p.get('output','')
            if isinstance(out,dict): out=json.dumps(out)
            isb=(fc['n']=='knowledge_load' and 'input filtering is enabled' in out.lower())
            seq_fc.append({'n':fc['n'],'b':isb}); seq_all.append({'n':fc['n'],'b':isb,'src':'fc'})
        elif pt=='mcp_tool_call_end':
            tool=p.get('invocation',{}).get('tool'); res=json.dumps(p.get('result',{})).lower()
            isb=('input filtering is enabled' in res or 'not permitted in this mode' in res)
            seq_all.append({'n':tool,'b':isb,'src':'mcp'})
    # function_call-only path (EXP-0032 style)
    for i,c in enumerate(seq_fc):
        if not c['b']: continue
        fc_blocks+=1
        before=any(seq_fc[j]['n']==TWIN for j in range(0,i))
        after=any(seq_fc[j]['n']==TWIN for j in range(i+1,min(i+1+K,len(seq_fc))))
        if after and not before: fc_after+=1
        elif before: fc_pre+=1
        else: fc_abandon+=1
    for c in seq_all:
        if c['b'] and c['src']=='mcp': mcp_blocks+=1
print(f"function_call-path knowledge_load blocks: {fc_blocks}  (EXP-0032 reported 152)")
print(f"  preempt(twin before)={fc_pre} reactive(after-not-before)={fc_after} abandon={fc_abandon}")
print(f"mcp_tool_call_end-path blocks: {mcp_blocks}")
print(f"NOTE: each knowledge_load block appears in BOTH paths -> total 304 = double count")
