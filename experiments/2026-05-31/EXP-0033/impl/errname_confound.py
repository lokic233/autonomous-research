#!/usr/bin/env python3
"""EXP-0033 — discharge/confirm the ERROR-MESSAGE-NAMING confound for CLAIM-0011 (PROJ-0003).
CPU/stdlib only.

KEY OPERATIONALIZATION (corrected): an error "NAMES an in-inventory alternative" iff the error
text mentions, by name, a tool that EXISTS in that harness's own tool inventory. This excludes
Codex's "Have you tried Claude Code" (names a DIFFERENT HARNESS, not an in-inventory tool) and
generic suggestions. Only Gemini's run_shell_command block ("Did you mean grep_search/replace/
cli_help") names in-inventory tools.

Three tests:
  T1 WITHIN-HARNESS: within a single harness, split ALL erroring tool-calls by whether the error
     names an in-inventory tool; does naming predict cross-tool reactive redirect?
  T2 PREEMPT-vs-ISOLATE among UNNAMED canonical blocks: preempt fires BEFORE the error so cannot
     be error-driven. Is CC-preempt vs Codex-isolate present with no naming?
  T3 LARGER-N: fullest Codex+Gemini windows, block counts + Wilson CIs.
"""
import json,glob,os,re,math,csv
from collections import Counter
K=6

def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),float('nan'))
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0,c-h),min(1,c+h))

WEB_TWINS={'WebSearch','mcp__plugin_meta_mux__three_pai_external_web_search'}
GEM_TWINS={'grep_search','glob','replace','list_directory','read_file','write_file'}

# ---------- inventories ----------
def cc_inv():
    inv=Counter()
    for fp in glob.glob(os.path.expanduser('~/.claude/projects/**/*.jsonl'),recursive=True):
        for l in open(fp):
            try: d=json.loads(l)
            except: continue
            m=d.get('message',{})
            if isinstance(m,dict) and isinstance(m.get('content'),list):
                for b in m['content']:
                    if isinstance(b,dict) and b.get('type')=='tool_use': inv[b.get('name')]+=1
    return inv
def cx_inv():
    inv=Counter()
    for fp in glob.glob(os.path.expanduser('~/.codex/sessions/**/*.jsonl'),recursive=True):
        for l in open(fp):
            try: d=json.loads(l)
            except: continue
            p=d.get('payload',{})
            if isinstance(p,dict):
                if p.get('type')=='function_call': inv[p.get('name')]+=1
                elif p.get('type')=='mcp_tool_call_end': inv[p.get('invocation',{}).get('tool')]+=1
    return inv
def gm_inv():
    inv=Counter()
    for fp in glob.glob(os.path.expanduser('~/.gemini/tmp/*/chats/session-*.json')):
        try: d=json.load(open(fp))
        except: continue
        for m in d.get('messages',[]):
            for tc in (m.get('toolCalls') or []): inv[tc.get('name')]+=1
    return inv

# tokens that look like tool references in error text
def names_inv_tool(etxt, inv_names):
    """True iff error text mentions, by name, a tool that exists in this harness's inventory.
    Require a suggestion context ('did you mean'/'available'/'use'/'try'/quoted) AND the named
    token to be an in-inventory tool. Short canonical tool basenames also matched bare in
    'did you mean ... X' lists."""
    if not etxt: return False
    t=etxt.lower()
    # candidate quoted/listed tokens
    cands=set(re.findall(r'["\'`]([a-z_]{3,})["\'`]', t))
    # 'did you mean X, Y, Z' bare lists
    m=re.search(r'did you mean(?: one of)?:?\s*(.+)', t)
    if m:
        for tok in re.findall(r'[a-z_]{3,}', m.group(1)[:120]): cands.add(tok)
    inv_low={n.lower():n for n in inv_names if n}
    # match against inventory names by basename (strip mcp prefixes)
    inv_basenames=set()
    for n in inv_low:
        inv_basenames.add(n)
        inv_basenames.add(n.split('__')[-1])
    for c in cands:
        if c in inv_basenames: return True
    return False

# ---------- sequence builders carrying names-flag ----------
def cc_seqs(inv):
    out=[]
    for fp in glob.glob(os.path.expanduser('~/.claude/projects/**/*.jsonl'),recursive=True):
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
                        res[b.get('tool_use_id')]={'e':b.get('is_error'),'t':json.dumps(b.get('content'))}
        seq=[]
        for d in lines:
            m=d.get('message',{})
            if isinstance(m,dict) and isinstance(m.get('content'),list):
                for b in m['content']:
                    if isinstance(b,dict) and b.get('type')=='tool_use':
                        nm=b.get('name'); r=res.get(b.get('id'),{})
                        etxt=r.get('t','') if r.get('e') else ''
                        isb=(nm=='WebFetch' and r.get('e') and 'internet mode is not enabled' in etxt.lower())
                        seq.append({'n':nm,'b':isb,'err':bool(r.get('e')),'names':names_inv_tool(etxt,inv)})
        if seq: out.append(seq)
    return out

def codex_seqs(inv):
    """Codex logs each tool call TWICE: once as function_call(_output) and once as
    mcp_tool_call_end. We DEDUP by preferring the function_call stream (carries exit codes)
    and only adding mcp events whose tool did NOT appear in the function_call stream.
    Empirically every knowledge_load block & web_search call appears in BOTH streams, so we
    use function_call as the canonical ordered stream (matches EXP-0032 codex() = 152 blocks)."""
    out=[]
    for fp in glob.glob(os.path.expanduser('~/.codex/sessions/**/*.jsonl'),recursive=True):
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
                out_t=p.get('output','')
                if isinstance(out_t,dict): out_t=json.dumps(out_t)
                m=re.search(r'exited with code (\d+)',out_t)
                iserr=bool(m) and m.group(1)!='0'
                isb=(fc['n']=='knowledge_load' and 'input filtering is enabled' in out_t.lower())
                if isb: iserr=True
                etxt=out_t if iserr else ''
                seq.append({'n':fc['n'],'b':isb,'err':iserr,'names':names_inv_tool(etxt,inv),'src':'fc'})
            # mcp_tool_call_end intentionally NOT appended: it duplicates the function_call stream.
        if seq: out.append(seq)
    return out

def gemini_seqs(inv):
    out=[]
    for fp in glob.glob(os.path.expanduser('~/.gemini/tmp/*/chats/session-*.json')):
        try: d=json.load(open(fp))
        except: continue
        seq=[]
        for m in d.get('messages',[]):
            for tc in (m.get('toolCalls') or []):
                nm=tc.get('name'); st=tc.get('status')
                rd=str(tc.get('resultDisplay') or '')
                err=(st=='error')
                isb=(err and nm=='run_shell_command' and 'not found' in rd.lower() and 'did you mean' in rd.lower())
                etxt=rd if err else ''
                seq.append({'n':nm,'b':isb,'err':err,'names':names_inv_tool(etxt,inv)})
        if seq: out.append(seq)
    return out

# ---------- T1 within-harness generic cross-tool redirect ----------
def within_harness(seqs, label):
    res={'named':{'reactive':0,'preempt':0,'abandon':0,'n':0},
         'unnamed':{'reactive':0,'preempt':0,'abandon':0,'n':0}}
    for seq in seqs:
        for i,c in enumerate(seq):
            if not c['err']: continue
            tool=c['n']
            before=any((seq[j]['n']!=tool and not seq[j]['err']) for j in range(0,i))
            after=any((seq[j]['n']!=tool and not seq[j]['err']) for j in range(i+1,min(i+1+K,len(seq))))
            if after and not before: mode='reactive'
            elif before: mode='preempt'
            elif after and before: mode='reactive'
            else: mode='abandon'
            b='named' if c['names'] else 'unnamed'
            res[b][mode]+=1; res[b]['n']+=1
    print(f"\n[T1 within-harness GENERIC cross-tool redirect] {label}")
    for b in ('named','unnamed'):
        r=res[b]; n=r['n']
        rr=r['reactive']/n if n else float('nan')
        lo,hi=wilson(r['reactive'],n)
        print(f"  errors-{b:7}: n={n:4} reactive={r['reactive']:4} ({rr:.3f} W95[{lo:.3f},{hi:.3f}]) preempt={r['preempt']} abandon={r['abandon']}")
    return res

def canon_blocks(seqs,twin_set):
    o={'reactive':0,'preempt':0,'abandon':0,'blocks':0,'unnamed_blocks':0,'named_blocks':0,
       'u_reactive':0,'u_preempt':0,'u_abandon':0,'n_reactive':0,'n_preempt':0,'n_abandon':0}
    for seq in seqs:
        for i,c in enumerate(seq):
            if not c['b']: continue
            o['blocks']+=1
            def is_twin(cc): return cc['n'] in twin_set and not cc['err']
            before=any(is_twin(seq[j]) for j in range(0,i))
            after=any(is_twin(seq[j]) for j in range(i+1,min(i+1+K,len(seq))))
            if after and not before: mode='reactive'
            elif before: mode='preempt'
            elif after and before: mode='reactive'
            else: mode='abandon'
            o[mode]+=1
            if c['names']:
                o['named_blocks']+=1; o['n_'+mode]+=1
            else:
                o['unnamed_blocks']+=1; o['u_'+mode]+=1
    return o

if __name__=='__main__':
    print("="*70); print("EXP-0033 ERROR-NAMING CONFOUND — discharge/confirm"); print("="*70)
    ICC,ICX,IGM=cc_inv(),cx_inv(),gm_inv()
    ccs=cc_seqs(ICC); cxs=codex_seqs(ICX); gms=gemini_seqs(IGM)
    print(f"corpora: CC {len(ccs)} sess, Codex {len(cxs)} sess, Gemini {len(gms)} sess")

    r_cc=within_harness(ccs,'CC'); r_cx=within_harness(cxs,'CODEX'); r_gm=within_harness(gms,'GEMINI')

    print("\n"+"="*70)
    print("[T2 canonical blocks split by NAMES-IN-INVENTORY-TOOL]")
    cc_c=canon_blocks(ccs,WEB_TWINS)
    cx_c=canon_blocks(cxs,{'three_pai_external_web_search'})
    gm_c=canon_blocks(gms,GEM_TWINS)
    for lab,o in [('CC',cc_c),('CODEX',cx_c),('GEMINI',gm_c)]:
        print(f"  {lab}: blocks={o['blocks']} named={o['named_blocks']} unnamed={o['unnamed_blocks']}")
        print(f"      ALL    : reactive={o['reactive']} preempt={o['preempt']} abandon={o['abandon']}")
        ub=o['unnamed_blocks']
        if ub:
            print(f"      UNNAMED: n={ub} reactive={o['u_reactive']} preempt={o['u_preempt']} abandon={o['u_abandon']} "
                  f"| preempt-share={o['u_preempt']/ub:.3f} reactive-share={o['u_reactive']/ub:.3f}")
        nb=o['named_blocks']
        if nb:
            print(f"      NAMED  : n={nb} reactive={o['n_reactive']} preempt={o['n_preempt']} abandon={o['n_abandon']} "
                  f"| reactive-share={o['n_reactive']/nb:.3f}")

    print("\n"+"="*70); print("[T3 LARGER-N canonical-block reactive + preempt shares]")
    for lab,o in [('CC',cc_c),('CODEX',cx_c),('GEMINI',gm_c)]:
        b=o['blocks']; lo,hi=wilson(o['reactive'],b)
        plo,phi=wilson(o['preempt'],b)
        print(f"  {lab}: blocks={b} reactive={o['reactive']}({o['reactive']/max(b,1):.3f} W95[{lo:.3f},{hi:.3f}]) "
              f"preempt={o['preempt']}({o['preempt']/max(b,1):.3f} W95[{plo:.3f},{phi:.3f}]) abandon={o['abandon']}")

    csvp=os.path.join(os.path.dirname(__file__),'..','results','errname_metrics.csv')
    os.makedirs(os.path.dirname(csvp),exist_ok=True)
    with open(csvp,'w',newline='') as f:
        w=csv.writer(f)
        w.writerow(['test','harness','bucket','n','reactive','preempt','abandon','reactive_share','preempt_share'])
        for lab,r in [('CC',r_cc),('CODEX',r_cx),('GEMINI',r_gm)]:
            for bkt in ('named','unnamed'):
                rr=r[bkt]; n=rr['n']
                w.writerow(['T1_generic',lab,bkt,n,rr['reactive'],rr['preempt'],rr['abandon'],
                            f"{rr['reactive']/n:.4f}" if n else '', f"{rr['preempt']/n:.4f}" if n else ''])
        for lab,o in [('CC',cc_c),('CODEX',cx_c),('GEMINI',gm_c)]:
            b=o['blocks']
            w.writerow(['T2_canon_all',lab,'all',b,o['reactive'],o['preempt'],o['abandon'],
                        f"{o['reactive']/max(b,1):.4f}",f"{o['preempt']/max(b,1):.4f}"])
            if o['unnamed_blocks']:
                ub=o['unnamed_blocks']
                w.writerow(['T2_canon_unnamed',lab,'unnamed',ub,o['u_reactive'],o['u_preempt'],o['u_abandon'],
                            f"{o['u_reactive']/ub:.4f}",f"{o['u_preempt']/ub:.4f}"])
            if o['named_blocks']:
                nb=o['named_blocks']
                w.writerow(['T2_canon_named',lab,'named',nb,o['n_reactive'],o['n_preempt'],o['n_abandon'],
                            f"{o['n_reactive']/nb:.4f}",f"{o['n_preempt']/nb:.4f}"])
    print(f"\nCSV -> {os.path.abspath(csvp)}")
