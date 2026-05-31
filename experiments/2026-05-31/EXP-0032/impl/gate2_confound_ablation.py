import json,glob,os,math
K=6
def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),float('nan'))
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0,c-h),min(1,c+h))

WEB_TWINS={'WebSearch','mcp__plugin_meta_mux__three_pai_external_web_search'}

# ---------- CLAUDE CODE ----------
def cc():
    files=glob.glob(os.path.expanduser('~/.claude/projects/**/*.jsonl'),recursive=True)
    blocks=0; reactive=0; preempt=0; abandon=0; twin_avail_sessions=0; block_sessions=0; sess_with_twin=0
    for fp in files:
        lines=[]
        for l in open(fp):
            try: lines.append(json.loads(l))
            except: pass
        res={}
        for d in lines:
            m=d.get('message',{})
            if isinstance(m,dict) and isinstance(m.get('content'),list):
                for b in m['content']:
                    if isinstance(b,dict) and b.get('type')=='tool_result':
                        res[b.get('tool_use_id')]={'e':b.get('is_error'),'t':json.dumps(b.get('content'))[:300]}
        seq=[]
        for d in lines:
            m=d.get('message',{})
            if isinstance(m,dict) and isinstance(m.get('content'),list):
                for b in m['content']:
                    if isinstance(b,dict) and b.get('type')=='tool_use':
                        nm=b.get('name'); r=res.get(b.get('id'),{})
                        isb=(nm=='WebFetch' and r.get('e') and 'internet mode' in (r.get('t','').lower()))
                        seq.append({'n':nm,'b':isb})
        names=[c['n'] for c in seq]
        has_twin=any(n in WEB_TWINS for n in names)
        if has_twin: sess_with_twin+=1
        hb=any(c['b'] for c in seq)
        if hb:
            block_sessions+=1
            if has_twin: twin_avail_sessions+=1
        for i,c in enumerate(seq):
            if not c['b']: continue
            blocks+=1
            before=any(seq[j]['n'] in WEB_TWINS for j in range(0,i))
            after=any(seq[j]['n'] in WEB_TWINS for j in range(i+1,min(i+1+K,len(seq))))
            if after and not before: reactive+=1
            elif before: preempt+=1
            else: abandon+=1
    return dict(blocks=blocks,reactive=reactive,preempt=preempt,abandon=abandon,
                block_sessions=block_sessions,twin_avail_sessions=twin_avail_sessions)

# ---------- CODEX ----------
def codex():
    files=glob.glob(os.path.expanduser('~/.codex/sessions/**/*.jsonl'),recursive=True)
    blocks=0; reactive=0; preempt=0; abandon=0; block_sessions=0; twin_avail_sessions=0
    TWIN='three_pai_external_web_search'
    for fp in files:
        pend={}; seq=[]
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
                seq.append({'n':fc['n'],'b':isb})
        names=[c['n'] for c in seq]
        has_twin=TWIN in names
        hb=any(c['b'] for c in seq)
        if hb:
            block_sessions+=1
            if has_twin: twin_avail_sessions+=1
        for i,c in enumerate(seq):
            if not c['b']: continue
            blocks+=1
            before=any(seq[j]['n']==TWIN for j in range(0,i))
            after=any(seq[j]['n']==TWIN for j in range(i+1,min(i+1+K,len(seq))))
            if after and not before: reactive+=1
            elif before: preempt+=1
            else: abandon+=1
    return dict(blocks=blocks,reactive=reactive,preempt=preempt,abandon=abandon,
                block_sessions=block_sessions,twin_avail_sessions=twin_avail_sessions)

# ---------- GEMINI ----------
def gemini():
    files=glob.glob(os.path.expanduser('~/.gemini/tmp/*/chats/session-*.json'))
    blocks=0; reactive=0; preempt=0; abandon=0; block_sessions=0; twin_avail_sessions=0
    # Gemini redirectable block = run_shell_command 'not found. did you mean'
    # twin = the named alternatives grep_search/glob/replace (file-discovery family)
    TWINS={'grep_search','glob','replace','list_directory','read_file','write_file'}
    for fp in files:
        try: d=json.load(open(fp))
        except: continue
        seq=[]
        for m in d.get('messages',[]):
            for tc in (m.get('toolCalls') or []):
                nm=tc.get('name'); st=tc.get('status')
                rd=str(tc.get('resultDisplay') or '').lower()
                isb=(st=='error' and nm=='run_shell_command' and 'not found' in rd and 'did you mean' in rd)
                seq.append({'n':nm,'b':isb,'err':st=='error'})
        names=[c['n'] for c in seq]
        has_twin=any(n in TWINS for n in names)
        hb=any(c['b'] for c in seq)
        if hb:
            block_sessions+=1
            if has_twin: twin_avail_sessions+=1
        for i,c in enumerate(seq):
            if not c['b']: continue
            blocks+=1
            # twin must be a SUCCESSFUL call
            before=any((seq[j]['n'] in TWINS and not seq[j]['err']) for j in range(0,i))
            after=any((seq[j]['n'] in TWINS and not seq[j]['err']) for j in range(i+1,min(i+1+K,len(seq))))
            if after and not before: reactive+=1
            elif after and before: reactive+=1  # gemini blocked tool can't preempt itself; after=redirect
            elif before: preempt+=1
            else: abandon+=1
    return dict(blocks=blocks,reactive=reactive,preempt=preempt,abandon=abandon,
                block_sessions=block_sessions,twin_avail_sessions=twin_avail_sessions)

for nm,fn in [('CC',cc),('CODEX',codex),('GEMINI',gemini)]:
    r=fn()
    lo,hi=wilson(r['reactive'],r['blocks'])
    print(f"[{nm}] blocks={r['blocks']} reactive_redirect={r['reactive']} preempt={r['preempt']} abandon={r['abandon']} | reactive_share={r['reactive']/max(r['blocks'],1):.3f} W95[{lo:.3f},{hi:.3f}] | block_sessions={r['block_sessions']} twin_available_in_block_sessions={r['twin_avail_sessions']}")
