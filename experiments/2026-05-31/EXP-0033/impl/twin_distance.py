import json,glob,os,re
TWIN='three_pai_external_web_search'
WEB_TWINS={'WebSearch','mcp__plugin_meta_mux__three_pai_external_web_search'}

def cc_seq(fp):
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
                    res[b.get('tool_use_id')]={'e':b.get('is_error'),'t':json.dumps(b.get('content')).lower()}
    seq=[]
    for d in lines:
        m=d.get('message',{})
        if isinstance(m,dict) and isinstance(m.get('content'),list):
            for b in m['content']:
                if isinstance(b,dict) and b.get('type')=='tool_use':
                    nm=b.get('name'); r=res.get(b.get('id'),{})
                    isb=(nm=='WebFetch' and r.get('e') and 'internet mode is not enabled' in r.get('t',''))
                    seq.append((nm,isb))
    return seq

# distance to nearest PRECEDING twin (preempt distance) for CC and Codex blocks
import statistics
def dists(seqs, twinset, isblockfn):
    pre=[]
    for seq in seqs:
        names=[s[0] for s in seq]
        for i,(nm,isb) in enumerate(seq):
            if not isblockfn(nm,isb): continue
            # nearest preceding twin
            d=None
            for j in range(i-1,-1,-1):
                if names[j] in twinset: d=i-j; break
            pre.append(d)
    return pre

cc_seqs=[cc_seq(fp) for fp in glob.glob(os.path.expanduser('~/.claude/projects/**/*.jsonl'),recursive=True)]
cc_pre=dists(cc_seqs, WEB_TWINS, lambda nm,isb: isb)
cc_d=[d for d in cc_pre if d is not None]
print(f"CC blocks={len(cc_pre)} with-preceding-twin={len(cc_d)} median-dist={statistics.median(cc_d) if cc_d else 'NA'} dists(sample)={sorted(cc_d)[:15]}")

def cx_seq(fp):
    pend={}; seq=[]
    for l in open(fp):
        try: d=json.loads(l)
        except: continue
        p=d.get('payload',{})
        if not isinstance(p,dict): continue
        if p.get('type')=='function_call': pend[p.get('call_id')]={'n':p.get('name')}
        elif p.get('type')=='function_call_output':
            fc=pend.get(p.get('call_id'))
            if not fc: continue
            out=p.get('output','')
            if isinstance(out,dict): out=json.dumps(out)
            isb=(fc['n']=='knowledge_load' and 'input filtering is enabled' in out.lower())
            seq.append((fc['n'],isb))
    return seq
cx_seqs=[cx_seq(fp) for fp in glob.glob(os.path.expanduser('~/.codex/sessions/**/*.jsonl'),recursive=True)]
cx_pre=dists(cx_seqs, {TWIN}, lambda nm,isb: isb)
cx_d=[d for d in cx_pre if d is not None]
print(f"CODEX blocks={len(cx_pre)} with-preceding-twin={len(cx_d)} median-dist={statistics.median(cx_d) if cx_d else 'NA'} dists(sample)={sorted(cx_d)[:15]}")
