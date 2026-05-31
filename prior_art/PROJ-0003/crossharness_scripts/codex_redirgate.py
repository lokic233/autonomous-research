import json, glob, os, re
from collections import Counter
files=glob.glob(os.path.expanduser('~/.codex/sessions/**/*.jsonl'),recursive=True)
K=6
def evstream(fp):
    """unified ordered stream of tool invocations across BOTH function_call(_output) and mcp_tool_call_end."""
    pend={}; ev=[]
    for l in open(fp):
        try: d=json.loads(l)
        except: continue
        p=d.get('payload',{})
        if not isinstance(p,dict): continue
        pt=p.get('type')
        if pt=='function_call':
            pend[p.get('call_id')]={'name':p.get('name')}
        elif pt=='function_call_output':
            fc=pend.get(p.get('call_id'))
            if not fc: continue
            out=p.get('output','')
            if isinstance(out,dict): out=json.dumps(out)
            m=re.search(r'exited with code (\d+)',out)
            web=fc['name'] and 'web_search' in fc['name']
            ie=('showing 0' in out.lower() and 'filtered' in out.lower()) if web else (bool(m) and m.group(1)!='0')
            ev.append({'tool':fc['name'],'web_block':False,'is_error':ie,'text':out[:120]})
        elif pt=='mcp_tool_call_end':
            inv=p.get('invocation',{}); tool=inv.get('tool')
            res=json.dumps(p.get('result',{})).lower()
            block = 'input filtering is enabled' in res or 'not permitted in this mode' in res
            iserr = block or '"err"' in res or 'error' in res[:200]
            ev.append({'tool':tool,'web_block':block,'is_error':iserr,'text':res[:120]})
    return ev
sessions=[evstream(f) for f in files]
sessions=[s for s in sessions if len(s)>=2]
# REDIRECTABLE gate test: knowledge_load blocked by input_filter -> does agent redirect to web_search?
blocks=0; redir=0; same=0; norecov=0; routes=Counter()
for s in sessions:
    for i,c in enumerate(s):
        if not c.get('web_block'): continue
        blocks+=1
        got=None
        for j in range(i+1,min(i+1+K,len(s))):
            n=s[j]
            if n['is_error']: continue
            tl=n['tool'] or ''
            if 'web_search' in tl or 'knowledge' in tl or (n['tool'] in ('exec_command','write_stdin')):
                got=tl; break
        if got is None: norecov+=1
        elif 'web_search' in (got or '') or (got not in ('knowledge_load',)): 
            redir+=1; routes[('knowledge_load',got)]+=1
        else: same+=1
print(f"REDIRECTABLE-gate replication (Codex input_filter block on knowledge_load):")
print(f"  total blocks: {blocks}")
print(f"  recovered-by-REDIRECT (switch to web_search/other tool): {redir}")
print(f"  recovered same-tool: {same}   no-recovery-in-window: {norecov}")
print(f"  redirect-share among recovered: {redir/max(redir+same,1):.3f}")
print("  top redirect routes:")
for k,v in routes.most_common(8): print('    ',k[0],'->',k[1],'x',v)
