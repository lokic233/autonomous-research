#!/usr/bin/env python3
"""EXP-GREENPATH-r3 — CLAIM-0012 GREEN-path remaining gaps (VERDICT-0046 HIGH/MED items).
CPU/stdlib-only. Imports EXP-0041 burst_L3.py parsers (parse_cc/parse_codex/parse_gemini,
interfailure_gaps, burstiness_B). Adds the two analyses EXP-0042 did NOT cover:

  (A) (B,M)-PLANE PLACEMENT — Goh-Barabasi (2008) burstiness B and memory M, with
      finite-size correction (Kim & Jo 2016, B_n), computed on the AGENT failure
      inter-event (inter-failure call-gap) sequences, placed against published
      literature anchors for SRE/incident-clustering and human-activity baselines.
      (We cannot re-run external datasets on this node; we cite published B,M
      coordinates as the comparison anchors — flagged as literature-anchored, not
      re-measured, per the no-fabrication rule.)

  (B) LABEL AUDIT — sample the actual failure-labeled tool-results across harnesses,
      emit the raw evidence (tool, is_err flag basis, snippet) so a human can judge
      leakage/mislabeling. Quantify: fraction of CC is_error labels, Codex regex
      basis distribution, Gemini status basis. Flag any structural leakage risk.

Estimand: purely DESCRIPTIVE failure arrival-process. No prediction, no error-class conditioning.
"""
import sys, os, json, math, statistics, csv, glob, re
from collections import defaultdict, Counter

# import the validated parsers from EXP-0041
EXP41 = os.path.expanduser('~/autonomous-research/experiments/2026-05-31/EXP-0041/impl')
sys.path.insert(0, EXP41)
import burst_L3 as B3

OUT = os.path.expanduser('~/autonomous-research/experiments/2026-05-31/EXP-GREENPATH-r3/results')
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------------
# (B,M) Goh-Barabasi + finite-size corrected B_n (Kim & Jo 2016)
# ----------------------------------------------------------------------------
def memory_M(gaps):
    """lag-1 autocorrelation of consecutive inter-event times (Goh-Barabasi M)."""
    if len(gaps) < 3: return None
    a = gaps[:-1]; b = gaps[1:]
    n = len(a)
    ma = sum(a)/n; mb = sum(b)/n
    sa = math.sqrt(sum((x-ma)**2 for x in a)/n)
    sb = math.sqrt(sum((x-mb)**2 for x in b)/n)
    if sa == 0 or sb == 0: return None
    cov = sum((a[i]-ma)*(b[i]-mb) for i in range(n))/n
    return cov/(sa*sb)

def B_raw(gaps):
    if len(gaps) < 2: return None
    mu = statistics.mean(gaps); sd = statistics.pstdev(gaps)
    if mu+sd == 0: return None
    return (sd-mu)/(sd+mu)

def B_finite_corrected(gaps):
    """Kim & Jo 2016 finite-size-corrected burstiness A_n / B_n.
    B_n = (sqrt(n+1) r - sqrt(n-1)) / ((sqrt(n+1)-2) r + sqrt(n-1))
    where r = sd/mu (coeff of variation). Maps to [-1,1] removing finite-n bias."""
    if len(gaps) < 2: return None
    n = len(gaps)
    mu = statistics.mean(gaps); sd = statistics.pstdev(gaps)
    if mu == 0: return None
    r = sd/mu
    num = math.sqrt(n+1)*r - math.sqrt(n-1)
    den = (math.sqrt(n+1)-2)*r + math.sqrt(n-1)
    if den == 0: return None
    return num/den

def bootstrap_ci(values, statfn, nboot=2000, seed=12345):
    import random
    rng = random.Random(seed)
    if len(values) < 2: return (None, None)
    boots = []
    n = len(values)
    for _ in range(nboot):
        samp = [values[rng.randrange(n)] for _ in range(n)]
        s = statfn(samp)
        if s is not None: boots.append(s)
    if len(boots) < 10: return (None, None)
    boots.sort()
    lo = boots[int(0.025*len(boots))]
    hi = boots[int(0.975*len(boots))]
    return (round(lo,4), round(hi,4))

def pooled_gaps(parsed):
    g = []
    for key, events in parsed.items():
        seq = [e[0] for e in events]
        g.extend(B3.interfailure_gaps(seq))
    return g

# ----------------------------------------------------------------------------
# LABEL AUDIT: emit raw labeling evidence for human judgement
# ----------------------------------------------------------------------------
def audit_cc():
    """CC: is_error flag is the harness-native label. Sample failures + their basis."""
    fs = glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl'))
    samples = []; n_err = 0; n_ok = 0; toolfail = Counter()
    for f in fs:
        idmap = {}
        for line in open(f):
            line=line.strip()
            if not line: continue
            try: d=json.loads(line)
            except: continue
            msg=d.get('message')
            if isinstance(msg,dict) and isinstance(msg.get('content'),list):
                for b in msg['content']:
                    if isinstance(b,dict) and b.get('type')=='tool_use':
                        idmap[b.get('id')]=(b.get('name','?'), b.get('input',{}))
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
                        tid=b.get('tool_use_id'); tname,_=idmap.get(tid,('unknown',{}))
                        if is_err:
                            n_err+=1; toolfail[tname]+=1
                            content=b.get('content','')
                            txt = content if isinstance(content,str) else json.dumps(content)[:300]
                            if len(samples)<120:
                                samples.append({'harness':'cc','tool':tname,'basis':'is_error=true',
                                                'snippet':txt[:200].replace('\n',' ')})
                        else:
                            n_ok+=1
    return samples, n_err, n_ok, toolfail

def audit_codex():
    fs = glob.glob(os.path.expanduser('~/.codex/sessions/**/*.jsonl'), recursive=True)
    samples=[]; n_err=0; n_ok=0; basis=Counter(); toolfail=Counter()
    for f in fs:
        callmap={}
        for line in open(f):
            line=line.strip()
            if not line: continue
            try: d=json.loads(line)
            except: continue
            p=d.get('payload') or d
            if p.get('type')=='function_call':
                callmap[p.get('call_id')]=(p.get('name','?'), p.get('arguments',''))
        seen=set()
        for line in open(f):
            line=line.strip()
            if not line: continue
            try: d=json.loads(line)
            except: continue
            p=d.get('payload') or d
            if p.get('type')=='function_call_output':
                cid=p.get('call_id')
                if cid in seen: continue
                seen.add(cid)
                out_s=str(p.get('output',''))
                m=re.search(r'exited with code (\d+)', out_s)
                err=0; bkind='ok'
                if m and m.group(1)!='0':
                    err=1; bkind='exit_code_nonzero'
                elif 'error' in out_s[:120].lower() and 'code 0' not in out_s:
                    err=1; bkind='error_substr_in_first120'
                tname,_=callmap.get(cid,('unknown',''))
                if err:
                    n_err+=1; basis[bkind]+=1; toolfail[tname]+=1
                    if len(samples)<120:
                        samples.append({'harness':'codex','tool':tname,'basis':bkind,
                                        'snippet':out_s[:200].replace('\n',' ')})
                else:
                    n_ok+=1
    return samples, n_err, n_ok, basis, toolfail

def audit_gemini():
    fs = glob.glob(os.path.expanduser('~/.gemini/tmp/*/chats/session-*.json'))
    samples=[]; n_err=0; n_ok=0; toolfail=Counter()
    for f in fs:
        try: d=json.load(open(f))
        except: continue
        for m in d.get('messages',[]):
            for tc in (m.get('toolCalls') or []):
                st=tc.get('status')
                if st not in ('success','error'): continue
                if st=='error':
                    n_err+=1; tname=tc.get('name','?'); toolfail[tname]+=1
                    res=str(tc.get('result',''))[:200]
                    if len(samples)<60:
                        samples.append({'harness':'gemini','tool':tname,'basis':'status==error',
                                        'snippet':res.replace('\n',' ')})
                else: n_ok+=1
    return samples, n_err, n_ok, toolfail

# ----------------------------------------------------------------------------
def main():
    print("Parsing corpora via EXP-0041 parsers...")
    cc=B3.parse_cc(); cx=B3.parse_codex(); gm=B3.parse_gemini()
    print(f"  CC {len(cc)} / Codex {len(cx)} / Gemini {len(gm)} sessions (>={B3.MIN_TRIALS} calls)\n")

    # ---- (A) (B,M)-PLANE ----
    print("="*70); print("(A) (B,M)-PLANE — agent failure inter-event sequences"); print("="*70)
    bm_rows=[]
    for name,parsed in [('claude_code',cc),('codex',cx),('gemini',gm)]:
        gaps = pooled_gaps(parsed)
        Br = B_raw(gaps); Bn = B_finite_corrected(gaps); M = memory_M(gaps)
        ci_bn = bootstrap_ci(gaps, B_finite_corrected)
        ci_m  = bootstrap_ci(gaps, memory_M)
        row={'system':name,'kind':'AGENT (this work)','n_gaps':len(gaps),
             'B_raw':round(Br,4) if Br is not None else None,
             'B_finite_corr':round(Bn,4) if Bn is not None else None,
             'B_corr_CI':f"[{ci_bn[0]},{ci_bn[1]}]",
             'M_lag1':round(M,4) if M is not None else None,
             'M_CI':f"[{ci_m[0]},{ci_m[1]}]",
             'source':'measured on-node'}
        bm_rows.append(row)
        print(f"  {name:12} n_gaps={len(gaps):4}  B_raw={row['B_raw']}  B_corr={row['B_finite_corr']} {row['B_corr_CI']}  M={row['M_lag1']} {row['M_CI']}")

    # Literature anchors (PUBLISHED values, NOT re-measured here — cited for placement).
    # Goh & Barabasi 2008 PRL / Karsai-Jo 2025 review report these reference (B,M) regions.
    anchors=[
      {'system':'POISSON null','kind':'reference','n_gaps':'-','B_raw':0.0,'B_finite_corr':0.0,'B_corr_CI':'-','M_lag1':0.0,'M_CI':'-','source':'theory: random/IID -> B=0,M=0'},
      {'system':'human email (Barabasi 2005)','kind':'human baseline','n_gaps':'-','B_raw':0.62,'B_finite_corr':'~0.6','B_corr_CI':'-','M_lag1':0.0,'M_CI':'-','source':'Goh-Barabasi 2008 (B~0.6,M~0): heavy-tail, NO memory'},
      {'system':'human library loans','kind':'human baseline','n_gaps':'-','B_raw':0.30,'B_finite_corr':'~0.3','B_corr_CI':'-','M_lag1':0.07,'M_CI':'-','source':'Goh-Barabasi 2008'},
      {'system':'earthquakes','kind':'natural/SRE-like cascade','n_gaps':'-','B_raw':0.18,'B_finite_corr':'~0.18','B_corr_CI':'-','M_lag1':0.10,'M_CI':'-','source':'Goh-Barabasi 2008 (aftershock clustering: B>0 AND M>0)'},
      {'system':'SRE/datacenter outages','kind':'SRE incident-cluster','n_gaps':'-','B_raw':'>0 (Pareto/heavy-tail)','B_finite_corr':'-','B_corr_CI':'-','M_lag1':'>0 (Hawkes-fit)','M_CI':'-','source':'power-system outage Pareto inter-arrival (2303.12714, Maynooth 2018); cyber Hawkes self-excite (2311.15701)'},
      {'system':'heartbeats (anti-bursty)','kind':'reference','n_gaps':'-','B_raw':-0.70,'B_finite_corr':'~-0.7','B_corr_CI':'-','M_lag1':0.0,'M_CI':'-','source':'Goh-Barabasi 2008 (regular -> B<0)'},
    ]
    bm_rows.extend(anchors)
    with open(os.path.join(OUT,'bm_plane.csv'),'w',newline='') as fh:
        cols=['system','kind','n_gaps','B_raw','B_finite_corr','B_corr_CI','M_lag1','M_CI','source']
        w=csv.DictWriter(fh,fieldnames=cols); w.writeheader()
        for r in bm_rows: w.writerow(r)
    print(f"  -> {OUT}/bm_plane.csv")

    # ---- (B) LABEL AUDIT ----
    print("\n"+"="*70); print("(B) LABEL AUDIT"); print("="*70)
    cc_s,cc_e,cc_o,cc_tf = audit_cc()
    cx_s,cx_e,cx_o,cx_basis,cx_tf = audit_codex()
    gm_s,gm_e,gm_o,gm_tf = audit_gemini()
    print(f"  CC     : {cc_e} fails / {cc_e+cc_o} results ({cc_e/(cc_e+cc_o):.3f}); label=harness is_error flag (native)")
    print(f"           top failing tools: {cc_tf.most_common(6)}")
    print(f"  Codex  : {cx_e} fails / {cx_e+cx_o} ({cx_e/(cx_e+cx_o):.3f}); label basis dist: {dict(cx_basis)}")
    print(f"           top failing tools: {cx_tf.most_common(6)}")
    print(f"  Gemini : {gm_e} fails / {gm_e+gm_o} ({gm_e/(gm_e+gm_o):.3f}); label=harness status==error (native)")
    print(f"           top failing tools: {gm_tf.most_common(6)}")
    alls = cc_s+cx_s+gm_s
    with open(os.path.join(OUT,'label_audit_samples.csv'),'w',newline='') as fh:
        w=csv.DictWriter(fh,fieldnames=['harness','tool','basis','snippet']); w.writeheader()
        for s in alls: w.writerow(s)
    # codex regex-basis is the only HEURISTIC label -> quantify its fragility share
    cx_heur = cx_basis.get('error_substr_in_first120',0)
    cx_total = sum(cx_basis.values())
    print(f"\n  HEURISTIC-LABEL EXPOSURE (the committee's MED concern):")
    print(f"    CC  : 0% heuristic (is_error is harness-emitted, not regex)")
    print(f"    Gemini: 0% heuristic (status field is harness-emitted)")
    print(f"    Codex: {cx_heur}/{cx_total} = {100*cx_heur/cx_total if cx_total else 0:.1f}% of failure labels rest on the 'error' substring heuristic")
    print(f"           (the remaining {100*(cx_basis.get('exit_code_nonzero',0))/cx_total if cx_total else 0:.1f}% are non-zero exit codes = hard signal)")
    print(f"  -> {OUT}/label_audit_samples.csv ({len(alls)} samples for human review)")

    bundle={'bm_plane':bm_rows,
            'label_audit':{'cc':{'fails':cc_e,'total':cc_e+cc_o,'basis':'is_error native','top_tools':cc_tf.most_common(10)},
                           'codex':{'fails':cx_e,'total':cx_e+cx_o,'basis_dist':dict(cx_basis),'top_tools':cx_tf.most_common(10)},
                           'gemini':{'fails':gm_e,'total':gm_e+gm_o,'basis':'status native','top_tools':gm_tf.most_common(10)},
                           'codex_heuristic_share': (cx_heur/cx_total if cx_total else 0)}}
    with open(os.path.join(OUT,'greenpath_r3.json'),'w') as fh:
        json.dump(bundle,fh,indent=2,default=str)
    print(f"\n  -> {OUT}/greenpath_r3.json")

if __name__=='__main__':
    main()
