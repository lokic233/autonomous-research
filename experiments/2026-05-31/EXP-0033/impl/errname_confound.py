#!/usr/bin/env python3
"""EXP-0033 — discharge/confirm the ERROR-MESSAGE-NAMING confound for CLAIM-0011 (PROJ-0003).
CPU/stdlib only. Three tests:
  T1 WITHIN-HARNESS: within a single harness, do blocks whose error NAMES an in-inventory
     alternative redirect more than blocks whose error does NOT? (supports prompt-confound)
  T2 PREEMPT-vs-ISOLATE without naming: is the CC-preempt vs Codex-isolate difference present
     among blocks whose error does NOT name an alt? Preempt fires BEFORE the error so cannot be
     error-driven. (tests whether surviving claim holds with confound live)
  T3 LARGER-N: pull fullest Gemini+Codex windows.
"""
import json,glob,os,re,math,csv
K=6

def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),float('nan'))
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0,c-h),min(1,c+h))

# An error NAMES an in-inventory ALTERNATIVE TOOL if it suggests another tool by name.
# Strict: "did you mean <tool>", or lists quoted tool alternatives, or "use <tool>".
NAME_TOOL = re.compile(r'did you mean|available (?:tools|commands)|valid (?:tools|options)|"[a-z_]{3,}"(?:,? ?(?:or )?"[a-z_]{3,}")+|use (?:the )?["\'`][a-z_]{3,}', re.I)
def names_tool_alt(t):
    return bool(NAME_TOOL.search(t or ''))

WEB_TWINS={'WebSearch','mcp__plugin_meta_mux__three_pai_external_web_search'}

# ============ CC ============
def cc_seqs():
    """Return list of sessions; each session = ordered list of {n, b(internet block), err, etxt, names}."""
    files=glob.glob(os.path.expanduser('~/.claude/projects/**/*.jsonl'),recursive=True)
    out=[]
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
                        res[b.get('tool_use_id')]={'e':b.get('is_error'),'t':json.dumps(b.get('content'))}
        seq=[]
        for d in lines:
            m=d.get('message',{})
            if isinstance(m,dict) and isinstance(m.get('content'),list):
                for b in m['content']:
                    if isinstance(b,dict) and b.get('type')=='tool_use':
                        nm=b.get('name'); r=res.get(b.get('id'),{})
                        etxt=r.get('t','') if r.get('e') else ''
                        isb=(nm=='WebFetch' and r.get('e') and 'internet mode is not enabled' in (etxt.lower()))
                        seq.append({'n':nm,'b':isb,'err':bool(r.get('e')),'etxt':etxt,'names':names_tool_alt(etxt)})
        if seq: out.append(seq)
    return out

# ============ CODEX ============
def codex_seqs():
    files=glob.glob(os.path.expanduser('~/.codex/sessions/**/*.jsonl'),recursive=True)
    TWIN='three_pai_external_web_search'
    out=[]
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
                out_t=p.get('output','')
                if isinstance(out_t,dict): out_t=json.dumps(out_t)
                m=re.search(r'exited with code (\d+)',out_t)
                iserr=bool(m) and m.group(1)!='0'
                isb=(fc['n']=='knowledge_load' and 'input filtering is enabled' in out_t.lower())
                if isb: iserr=True
                etxt=out_t if iserr else ''
                seq.append({'n':fc['n'],'b':isb,'err':iserr,'etxt':etxt[:400],'names':names_tool_alt(out_t)})
            elif pt=='mcp_tool_call_end':
                inv=p.get('invocation',{}); tool=inv.get('tool')
                res=json.dumps(p.get('result',{}))
                rl=res.lower()
                isb=('input filtering is enabled' in rl or 'not permitted in this mode' in rl)
                iserr=isb or '"err"' in rl or 'error' in rl[:200]
                etxt=res if iserr else ''
                seq.append({'n':tool,'b':isb,'err':iserr,'etxt':etxt[:400],'names':names_tool_alt(res)})
        if seq: out.append(seq)
    return out

# ============ GEMINI ============
def gemini_seqs():
    files=glob.glob(os.path.expanduser('~/.gemini/tmp/*/chats/session-*.json'))
    out=[]
    for fp in files:
        try: d=json.load(open(fp))
        except: continue
        seq=[]
        for m in d.get('messages',[]):
            for tc in (m.get('toolCalls') or []):
                nm=tc.get('name'); st=tc.get('status')
                rd=str(tc.get('resultDisplay') or '')
                rdl=rd.lower()
                err=(st=='error')
                isb=(err and nm=='run_shell_command' and 'not found' in rdl and 'did you mean' in rdl)
                etxt=rd if err else ''
                seq.append({'n':nm,'b':isb,'err':err,'etxt':etxt[:400],'names':names_tool_alt(rd)})
        if seq: out.append(seq)
    return out

GEM_TWINS={'grep_search','glob','replace','list_directory','read_file','write_file'}

def classify_block(seq,i,twins,twin_pred=None):
    """Return (mode, names) for block at i. mode in reactive/preempt/abandon."""
    def is_twin(c):
        if twin_pred: return twin_pred(c)
        return c['n'] in twins and not c['err']
    before=any(is_twin(seq[j]) for j in range(0,i))
    after=any(is_twin(seq[j]) for j in range(i+1,min(i+1+K,len(seq))))
    if after and not before: return 'reactive'
    if before: return 'preempt'
    if after and before: return 'reactive'
    return 'abandon'

# ---- T1 within-harness naming test ----
# We need blocks within a harness with naming variation. Use ALL erroring tool-calls as "blocks"
# where a redirect-twin family is defined, and split by whether the error names a tool alt.
# CC: redirect target = WEB_TWINS for WebFetch internet blocks (no naming) PLUS any other error
#     whose text names an alt -> does it redirect to a *different* successful tool?
# General within-harness: for every ERROR, classify names-alt yes/no, and whether a DIFFERENT
# successful tool (cross-tool redirect) appears in K-after-not-before.

def within_harness(seqs, label):
    # rows: bucket -> [reactive,preempt,abandon] for the canonical block twins
    # plus a GENERAL cross-tool redirect test over all errors split by naming.
    res={'named':{'reactive':0,'preempt':0,'abandon':0,'n':0},
         'unnamed':{'reactive':0,'preempt':0,'abandon':0,'n':0}}
    for seq in seqs:
        for i,c in enumerate(seq):
            if not c['err']: continue
            # generic cross-tool redirect: a DIFFERENT tool succeeds after (not same tool)
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

if __name__=='__main__':
    print("="*70)
    print("EXP-0033 ERROR-NAMING CONFOUND — discharge/confirm")
    print("="*70)
    ccs=cc_seqs(); cxs=codex_seqs(); gms=gemini_seqs()
    print(f"corpora: CC {len(ccs)} sessions, Codex {len(cxs)} sessions, Gemini {len(gms)} sessions")

    # T1
    r_cc=within_harness(ccs,'CC')
    r_cx=within_harness(cxs,'CODEX')
    r_gm=within_harness(gms,'GEMINI')

    # ---- T2 PREEMPT-vs-ISOLATE among UNNAMED canonical blocks ----
    # canonical block twins per harness; restrict to blocks whose error does NOT name a tool alt.
    def canon_blocks(seqs,twins,twin_name_set,gemini=False):
        out={'reactive':0,'preempt':0,'abandon':0,'blocks':0,'unnamed_blocks':0,
             'u_reactive':0,'u_preempt':0,'u_abandon':0}
        for seq in seqs:
            for i,c in enumerate(seq):
                if not c['b']: continue
                out['blocks']+=1
                def is_twin(cc): return cc['n'] in twin_name_set and not cc['err']
                before=any(is_twin(seq[j]) for j in range(0,i))
                after=any(is_twin(seq[j]) for j in range(i+1,min(i+1+K,len(seq))))
                if after and not before: mode='reactive'
                elif before: mode='preempt'
                elif after and before: mode='reactive'
                else: mode='abandon'
                out[mode]+=1
                if not c['names']:
                    out['unnamed_blocks']+=1
                    out['u_'+mode]+=1
        return out
    print("\n"+"="*70)
    print("[T2 PREEMPT-vs-ISOLATE on canonical blocks, split by error-naming]")
    cc_c=canon_blocks(ccs,WEB_TWINS,WEB_TWINS)
    cx_c=canon_blocks(cxs,{'three_pai_external_web_search'},{'three_pai_external_web_search'})
    gm_c=canon_blocks(gms,GEM_TWINS,GEM_TWINS,gemini=True)
    for lab,o in [('CC',cc_c),('CODEX',cx_c),('GEMINI',gm_c)]:
        b=o['blocks']
        print(f"  {lab}: blocks={b} | ALL: reactive={o['reactive']} preempt={o['preempt']} abandon={o['abandon']}")
        ub=o['unnamed_blocks']
        print(f"        UNNAMED-error blocks={ub} | reactive={o['u_reactive']} preempt={o['u_preempt']} abandon={o['u_abandon']}")
        if ub:
            pre_iso = o['u_preempt']+o['u_reactive']  # twin appears at all (preempt or reactive)
            print(f"        among UNNAMED: preempt-share={o['u_preempt']/ub:.3f} reactive-share={o['u_reactive']/ub:.3f} abandon-share={o['u_abandon']/ub:.3f}")

    # ---- T3 larger-n: report block counts and reactive shares ----
    print("\n"+"="*70)
    print("[T3 LARGER-N canonical-block reactive-redirect]")
    for lab,o in [('CC',cc_c),('CODEX',cx_c),('GEMINI',gm_c)]:
        b=o['blocks']
        lo,hi=wilson(o['reactive'],b)
        print(f"  {lab}: blocks={b} reactive={o['reactive']} share={o['reactive']/max(b,1):.3f} W95[{lo:.3f},{hi:.3f}]")

    # CSV
    csvp=os.path.join(os.path.dirname(__file__),'..','results','errname_metrics.csv')
    os.makedirs(os.path.dirname(csvp),exist_ok=True)
    with open(csvp,'w',newline='') as f:
        w=csv.writer(f)
        w.writerow(['test','harness','bucket','n','reactive','preempt','abandon','reactive_share'])
        for lab,r in [('CC',r_cc),('CODEX',r_cx),('GEMINI',r_gm)]:
            for bkt in ('named','unnamed'):
                rr=r[bkt]; n=rr['n']
                w.writerow(['T1_generic',lab,bkt,n,rr['reactive'],rr['preempt'],rr['abandon'],
                            f"{rr['reactive']/n:.4f}" if n else ''])
        for lab,o in [('CC',cc_c),('CODEX',cx_c),('GEMINI',gm_c)]:
            w.writerow(['T2_canon_all',lab,'all',o['blocks'],o['reactive'],o['preempt'],o['abandon'],
                        f"{o['reactive']/max(o['blocks'],1):.4f}"])
            w.writerow(['T2_canon_unnamed',lab,'unnamed',o['unnamed_blocks'],o['u_reactive'],o['u_preempt'],o['u_abandon'],
                        f"{o['u_reactive']/max(o['unnamed_blocks'],1):.4f}" if o['unnamed_blocks'] else ''])
    print(f"\nCSV -> {os.path.abspath(csvp)}")
