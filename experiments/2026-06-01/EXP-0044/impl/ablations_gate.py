#!/usr/bin/env python3
"""EXP-0044 BLOCKING-3: GATE-STRIPPED HAWKES REFIT for CC + Gemini.
CPU/stdlib-only. Reuses EXP-0041 parsers + EXP-0042 Hawkes/Cox machinery.

VERDICT-0047 theory_skeptic: deterministic gate-cascades inflate Hawkes alpha mechanically,
not stochastically. CC ~1/3 permission_gate; Gemini ~98% path_gate+schema_argerror (per the
EXP-0043 label audit). We re-classify each CC/Gemini FAILURE as gate vs genuine-exec using the
SAME classifiers EXP-0043 reported, DROP the gate failures (treat the call as the non-error
outcome it mechanically is, i.e. set is_err=0 and keep the call in the sequence so positions/
rate-baseline are preserved), and REFIT Hawkes on the genuine-exec residual.

If CC's alpha COLLAPSES after removing permission_gate -> self-excitation is mechanical.
If Gemini's residual is too thin to fit -> its leg was ~entirely gate/malformed artifact.

Two strip modes per harness, reported both:
  (i) STRIP_TO_OK : gate failure -> is_err=0 (call still happened, just not a genuine failure)
  (ii) DROP_CALL  : remove the gate call entirely from the sequence (stricter; changes positions)
DESCRIPTIVE arrival-process only.
"""
import sys, os, json, math, csv, re
from collections import Counter, defaultdict

E41=os.path.expanduser('~/autonomous-research/experiments/2026-05-31/EXP-0041/impl')
E42=os.path.expanduser('~/autonomous-research/experiments/2026-05-31/EXP-0042/impl')
sys.path.insert(0,E41); sys.path.insert(0,E42)
import burst_L3 as L3
import robust_L4 as L4

OUT=os.path.expanduser('~/autonomous-research/experiments/2026-06-01/EXP-0044/results')
os.makedirs(OUT,exist_ok=True)

# ---- gate classifiers (mirror EXP-0043 label-audit categories) -------------
def classify_cc_fail(tname, snippet):
    """Return gate-category for a CC failure, given tool name + result text.
    NOTE: this CC corpus snapshot is genuine-exec-heavy (Exit code N: ping/ssh/http/file).
    permission_gate must match the ACTUAL Claude permission-denial phrasing, NOT the generic
    word 'permission' (which false-positives on SSH 'connection is not ...' warnings)."""
    t=(snippet or '').lower()
    if "haven't granted" in t or 'has not granted' in t or 'permission to use' in t \
       or 'requested permissions' in t or 'permission denied to' in t \
       or ('permission' in t and ('grant' in t or 'approve' in t or 'allow' in t)) \
       or 'user has not approved' in t or 'requires approval' in t:
        return 'permission_gate'
    if 'web search is not' in t or ('web' in t and ('disabl' in t or 'not enabled' in t)):
        return 'web_gate'
    if 'no such file' in t or 'enoent' in t or 'does not exist' in t \
       or 'file not found' in t or 'local file not found' in t:
        return 'file_notfound'
    return 'genuine_exec'

def classify_gemini_fail(tname, snippet):
    # NOTE: real Gemini error strings observed on-node (EXP-0043 + EXP-0044 inspection):
    #   schema_argerror -> "params must have required property ..." / "must be ..." / "invalid params"
    #   path_gate       -> "Path not in workspace" / "outside the workspace" / "Tool ... not allowed"
    #   the substring match is on the RAW (case-preserved-then-lowered) result text.
    t=(snippet or '').lower()
    # schema / malformed-arg gate (deterministic JSON-schema validation failure, pre-execution)
    if ('params must have' in t) or ('required property' in t) or ('must have required' in t) \
       or (('invalid' in t) and ('param' in t)) or ('schema' in t) \
       or (('missing' in t) and ('param' in t or 'field' in t or 'required' in t or 'argument' in t)):
        return 'schema_argerror'
    # path / workspace gate (deterministic sandbox boundary denial, pre-execution)
    if ('path not in workspace' in t) or ('not in workspace' in t) or ('outside' in t and 'workspace' in t) \
       or ('not within' in t) or ('must be within' in t) or ('not allowed' in t) \
       or (('path' in t) and ('workspace' in t or 'allowed' in t)):
        return 'path_gate'
    if 'no such file' in t or 'not found' in t or 'does not exist' in t:
        return 'file_notfound'
    return 'genuine_exec'

# ---- re-parse CC carrying failure snippet so we can classify ----------------
import glob
def parse_cc_with_snippet():
    fs=glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl'))
    out={}
    for f in fs:
        idmap={}
        for line in open(f):
            line=line.strip()
            if not line: continue
            try: d=json.loads(line)
            except: continue
            msg=d.get('message')
            if isinstance(msg,dict) and isinstance(msg.get('content'),list):
                for b in msg['content']:
                    if isinstance(b,dict) and b.get('type')=='tool_use':
                        idmap[b.get('id')]=(b.get('name','?'),b.get('input',{}))
        seq=[]
        for line in open(f):
            line=line.strip()
            if not line: continue
            try: d=json.loads(line)
            except: continue
            msg=d.get('message')
            if isinstance(msg,dict) and isinstance(msg.get('content'),list):
                for b in msg['content']:
                    if isinstance(b,dict) and b.get('type')=='tool_result':
                        is_err=1 if b.get('is_error') else 0
                        tid=b.get('tool_use_id'); tname,targs=idmap.get(tid,('unknown',{}))
                        content=b.get('content','')
                        snip=content if isinstance(content,str) else json.dumps(content)[:400]
                        seq.append((is_err,tname,tname,L3.arg_text(tname,targs),snip))
        if len(seq)>=L3.MIN_TRIALS: out[f]=seq
    return out

def parse_gemini_with_snippet():
    fs=glob.glob(os.path.expanduser('~/.gemini/tmp/*/chats/session-*.json'))
    out={}
    for f in fs:
        try: d=json.load(open(f))
        except: continue
        seq=[]
        for m in d.get('messages',[]):
            for tc in (m.get('toolCalls') or []):
                st=tc.get('status')
                if st not in ('success','error'): continue
                is_err=1 if st=='error' else 0
                tname=tc.get('name','?')
                snip=str(tc.get('result',''))[:400]
                seq.append((is_err,tname,tname,L3.arg_text(tname,tc.get('args',{})),snip))
        if len(seq)>=L3.MIN_TRIALS: out[f]=seq
    return out

def strip_gates(parsed_snip, classify, gate_cats, mode='to_ok'):
    """Return parsed dict in burst_L3 4-tuple form with gate failures stripped.
    mode='to_ok': gate fail -> is_err=0 (keep call). mode='drop': remove call."""
    out={}; counts=Counter()
    for k,ev in parsed_snip.items():
        newev=[]
        for (is_err,ct,rt,atxt,snip) in ev:
            if is_err:
                cat=classify(ct,snip)
                counts[cat]+=1
                if cat in gate_cats:
                    if mode=='drop':
                        continue
                    else:
                        newev.append((0,ct,rt,atxt)); continue
            newev.append((is_err,ct,rt,atxt))
        if len(newev)>=L3.MIN_TRIALS:
            out[k]=newev
    return out, counts

def refit(name, parsed):
    return L4.cox_vs_hawkes(name, parsed)

def main():
    print("Parsing CC + Gemini with failure snippets...")
    cc=parse_cc_with_snippet(); gm=parse_gemini_with_snippet()
    print(f"  CC sessions {len(cc)} / Gemini {len(gm)}")

    # baseline (no strip) — use 4-tuple view
    def to4(parsed_snip):
        return {k:[(e[0],e[1],e[2],e[3]) for e in ev] for k,ev in parsed_snip.items()}
    cc4=to4(cc); gm4=to4(gm)

    results=[]
    # classify-only distribution first
    _,cc_counts=strip_gates(cc,classify_cc_fail,set(),mode='to_ok')
    _,gm_counts=strip_gates(gm,classify_gemini_fail,set(),mode='to_ok')
    print("  CC failure categories:", dict(cc_counts))
    print("  Gemini failure categories:", dict(gm_counts))

    configs=[
      ('claude_code','baseline', cc4, None),
      ('claude_code','strip_permission_gate_to_ok', cc, ({'permission_gate'},'to_ok')),
      ('claude_code','strip_all_gates_to_ok', cc, ({'permission_gate','web_gate','file_notfound'},'to_ok')),
      ('claude_code','strip_permission_gate_drop', cc, ({'permission_gate'},'drop')),
      ('gemini','baseline', gm4, None),
      ('gemini','strip_pathschema_to_ok', gm, ({'path_gate','schema_argerror'},'to_ok')),
      ('gemini','strip_all_gates_to_ok', gm, ({'path_gate','schema_argerror','file_notfound'},'to_ok')),
      ('gemini','strip_pathschema_drop', gm, ({'path_gate','schema_argerror'},'drop')),
    ]
    classify={'claude_code':classify_cc_fail,'gemini':classify_gemini_fail}
    for name,label,data,strip in configs:
        if strip is None:
            parsed=data; removed={}
        else:
            cats,mode=strip
            parsed,removed=strip_gates(cc if name=='claude_code' else gm, classify[name], cats, mode=mode)
        # count fails remaining
        nf=sum(e[0] for ev in parsed.values() for e in ev)
        nc=sum(len(ev) for ev in parsed.values())
        try:
            r=refit(name,parsed)
        except Exception as ex:
            r={'harness':name,'error':str(ex),'n_calls':nc}
        row={'harness':name,'config':label,'n_sessions':r.get('n_sessions'),
             'n_calls':r.get('n_calls',nc),'n_fails_remaining':nf,
             'cox_BIC':r.get('cox_BIC'),'hawkes_BIC':r.get('hawkes_BIC'),
             'hawkes_alpha':r.get('hawkes_alpha'),'hawkes_beta':r.get('hawkes_beta'),
             'dBIC':r.get('delta_BIC_cox_minus_hawkes'),
             'hawkes_earns':r.get('hawkes_earns_params')}
        results.append(row)
        print(f"  {name:12} {label:30} n_calls={row['n_calls']} fails={nf} alpha={row['hawkes_alpha']} dBIC={row['dBIC']}")

    with open(os.path.join(OUT,'gate_stripped_hawkes.csv'),'w',newline='') as fh:
        cols=['harness','config','n_sessions','n_calls','n_fails_remaining','cox_BIC','hawkes_BIC','hawkes_alpha','hawkes_beta','dBIC','hawkes_earns']
        w=csv.DictWriter(fh,fieldnames=cols,extrasaction='ignore'); w.writeheader()
        for r in results: w.writerow(r)
    bundle={'cc_failure_categories':dict(cc_counts),'gemini_failure_categories':dict(gm_counts),'refits':results}
    with open(os.path.join(OUT,'gate_stripped.json'),'w') as fh:
        json.dump(bundle,fh,indent=2,default=str)
    print(f"\n-> {OUT}/gate_stripped_hawkes.csv , gate_stripped.json")
    return bundle

if __name__=='__main__':
    main()
