#!/usr/bin/env python3
"""
EXP-0051 — Re-Tokenization Boundary Churn: L1-prep extension of EXP-0049.
CLAIM-0014, PROJ-0005, Level-0, CPU-only. researcher-0014-L1prep-r5, prompt_version v001.

EXTENDS EXP-0049 to satisfy the CPU-doable VERDICT-0055 required_evidence:
  RE-01  quantitative BPE NULL MODEL (observed seam churn vs generic random-offset BPE churn)
  RE-02  3 tokenizers {gpt2, qwen2-0.5b, llama-3-128k} x 2 corpora {claude_code, codex} = 6 cells
  RE-05  per-cell gate evals + multiple-comparison correction (Holm-Bonferroni + Benjamini-Hochberg)
  RE-06  block-size sensitivity {8,16,32}
Reuses EXP-0049 corpus parsers + delimiter classifier + chained-block invalidation rule VERBATIM.
NULL model + MC-correction + block sweep are pure-stdlib. See impl/PRE_REGISTRATION.md (LOCKED).
NOT in scope: RE-03 (H100 vLLM APC counters/TTFT), RE-04 (deployed regime-(a) prevalence).
"""
import json, glob, os, sys, math, random
from collections import defaultdict, Counter

# Reuse EXP-0049 venv (transformers 4.57.6, Rust fast tokenizers). Re-exec into it.
EXP49 = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'EXP-0049')
VENV_PYTHON = os.path.join(EXP49, '.venv', 'bin', 'python3')
if sys.executable != VENV_PYTHON and os.path.exists(VENV_PYTHON):
    os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

import warnings; warnings.filterwarnings("ignore")
from transformers import AutoTokenizer

def pp(*a, **k): print(*a, **k, flush=True)

MAX_PREFIX_CHARS = 4096
BLOCK_SIZES = [8, 16, 32]
PRIMARY_BLOCK = 16
K_NULL = 5
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

null_rng = random.Random(42)      # null offsets
boot_rng = random.Random(42)      # bootstrap resampling

TOKENIZER_SPECS = [
    ('gpt2', 'gpt2'),
    ('qwen2-0.5b', 'Qwen/Qwen2-0.5B'),
    ('llama-3-128k', 'NousResearch/Meta-Llama-3-8B'),
]
CORPORA = ['claude_code', 'codex']

# ===== EXP-0049 parsers (VERBATIM) =====
def parse_cc_sessions():
    root = os.path.expanduser("~/.claude/projects")
    files = sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True))
    sessions = []
    for fp in files:
        turns = []
        try:
            with open(fp) as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    d = json.loads(line); m = d.get("message")
                    if not isinstance(m, dict): continue
                    role = m.get("role", ""); content = m.get("content")
                    if isinstance(content, str):
                        turns.append({"role": role, "type": "text", "text": content})
                    elif isinstance(content, list):
                        for b in content:
                            if not isinstance(b, dict): continue
                            tp = b.get("type", "")
                            if tp == "text":
                                turns.append({"role": role, "type": "text", "text": b.get("text", "")})
                            elif tp == "tool_use":
                                turns.append({"role": role, "type": "tool_use",
                                    "text": json.dumps({"name": b.get("name",""), "input": b.get("input",{})}),
                                    "tool_use_id": b.get("id","")})
                            elif tp == "tool_result":
                                rc = b.get("content","")
                                if isinstance(rc, list):
                                    parts=[]
                                    for x in rc:
                                        parts.append(x.get("text", json.dumps(x)) if isinstance(x,dict) else str(x))
                                    rc = "\n".join(parts)
                                turns.append({"role": role, "type": "tool_result", "text": str(rc),
                                    "tool_use_id": b.get("tool_use_id","")})
        except Exception:
            continue
        if turns: sessions.append({"source":"claude_code","file":fp,"turns":turns})
    return sessions

def parse_codex_sessions():
    root = os.path.expanduser("~/.codex/sessions")
    files = sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True))
    sessions = []
    for fp in files:
        turns = []
        try:
            with open(fp) as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    d = json.loads(line); p = d.get("payload") or d; tp = p.get("type","")
                    if tp == "message":
                        turns.append({"role":p.get("role","assistant"),"type":"text","text":str(p.get("content",""))})
                    elif tp == "function_call":
                        turns.append({"role":"assistant","type":"tool_use",
                            "text": json.dumps({"name":p.get("name",""),"arguments":p.get("arguments","")}),
                            "tool_use_id": p.get("call_id","")})
                    elif tp == "function_call_output":
                        turns.append({"role":"tool","type":"tool_result","text":str(p.get("output","")),
                            "tool_use_id": p.get("call_id","")})
        except Exception:
            continue
        if turns: sessions.append({"source":"codex","file":fp,"turns":turns})
    return sessions

# ===== EXP-0049 delimiter classifier (VERBATIM) =====
CHAT_TEMPLATE_MARKERS = ['<|im_start|>','<|im_end|>','<|tool_call|>','<|/tool_call|>','<tool_call>',
    '</tool_call>','<|eot_id|>','<|start_header_id|>','<|end_header_id|>','<|begin_of_text|>',
    '[TOOL_RESULTS]','[/TOOL_RESULTS]','<|assistant|>','<|user|>','<|system|>']

def classify_delimiter(prefix_tail, result_head):
    tail = prefix_tail[-50:] if len(prefix_tail)>50 else prefix_tail
    head = result_head[:50] if len(result_head)>50 else result_head
    seam = tail+head
    has_template = any(mk in seam for mk in CHAT_TEMPLATE_MARKERS)
    if tail.endswith('\n\n'): d='double_newline'
    elif tail.endswith('\n'): d='single_newline'
    elif tail.endswith(' '): d='space'
    elif tail.endswith('}'): d='json_close_brace'
    elif tail.endswith('"'): d='quote'
    elif tail.endswith(':'): d='colon'
    elif tail.endswith('>'): d='angle_bracket'
    elif tail.endswith('.'): d='period'
    elif tail.endswith(','): d='comma'
    elif tail.endswith(')'): d='paren_close'
    elif tail.endswith(']'): d='bracket_close'
    elif tail and tail[-1].isalnum(): d='alnum'
    else: d='other_punct'
    return d, has_template

def extract_injection_seams(sessions):
    for sess in sessions:
        parts=[]
        for turn in sess["turns"]:
            if turn["type"]=="tool_result":
                prefix_text="\n".join(parts); result_text=turn["text"]
                if len(prefix_text)<20 or len(result_text)<1:
                    parts.append(result_text); continue
                dclass,has_tmpl=classify_delimiter(prefix_text,result_text)
                yield (prefix_text,result_text,sess["source"],dclass,has_tmpl)
                parts.append(result_text)
            else:
                parts.append(turn["text"])

# ===== block invalidation: chained-suffix rule from first divergent token (EXP-0049 semantics) =====
def first_divergence(a, b):
    m = min(len(a), len(b))
    for i in range(m):
        if a[i] != b[i]:
            return i
    return -1 if len(a)==len(b) else m

def churn_from(first_div, len_a, len_b, bs):
    max_len = max(len_a, len_b)
    if max_len == 0: return 0.0
    total = (max_len + bs - 1)//bs
    if first_div < 0: return 0.0
    first_block = first_div // bs
    return (total - first_block)/total

# ===== AUC (rank-based, EXP-0049 fast_auc VERBATIM) =====
def fast_auc(preds, acts):
    paired = sorted(zip(preds, acts), key=lambda x:x[0])
    n_p = sum(1 for _,a in paired if a==1); n_n=len(paired)-n_p
    if n_p==0 or n_n==0: return 0.5, n_p, n_n
    rs=0.0; i=0
    while i<len(paired):
        j=i
        while j<len(paired) and paired[j][0]==paired[i][0]: j+=1
        avg=(i+j+1)/2.0
        for k in range(i,j):
            if paired[k][1]==1: rs+=avg
        i=j
    u=rs - n_p*(n_p+1)/2
    return u/(n_p*n_n), n_p, n_n

def boot_ci(vals, B=10000, rng=boot_rng):
    n=len(vals)
    if n==0: return 0.0,0.0,0.0
    means=[]
    for _ in range(B):
        s=0.0
        for _ in range(n): s+=vals[rng.randrange(n)]
        means.append(s/n)
    means.sort()
    return sum(vals)/n, means[int(0.025*B)], means[int(0.975*B)]

def boot_p_twosided(vals, B=10000, rng=boot_rng):
    """two-sided bootstrap p for H0: mean==0 (frac of boot means on the wrong side)."""
    n=len(vals)
    if n==0: return 1.0
    cnt_le=0; cnt_ge=0
    for _ in range(B):
        s=0.0
        for _ in range(n): s+=vals[rng.randrange(n)]
        m=s/n
        if m<=0: cnt_le+=1
        if m>=0: cnt_ge+=1
    return min(1.0, 2.0*min(cnt_le,cnt_ge)/B)

def boot_auc_ci_p(preds, acts, B=2000, rng=boot_rng):
    n=len(preds); idx=list(range(n))
    aucs=[]
    for _ in range(B):
        si=[idx[rng.randrange(n)] for _ in range(n)]
        a,_,_=fast_auc([preds[i] for i in si],[acts[i] for i in si])
        aucs.append(a)
    aucs.sort()
    lo=aucs[int(0.025*B)]; hi=aucs[int(0.975*B)]
    # two-sided p for H0: AUC==0.5
    cnt_le=sum(1 for a in aucs if a<=0.5); cnt_ge=sum(1 for a in aucs if a>=0.5)
    p=min(1.0, 2.0*min(cnt_le,cnt_ge)/B)
    base,_,_=fast_auc(preds,acts)
    return base, lo, hi, p

# ===== MC correction (stdlib) =====
def holm_bonferroni(pvals, alpha=0.05):
    m=len(pvals); order=sorted(range(m), key=lambda i:pvals[i]); reject=[False]*m
    for rank,i in enumerate(order):
        thresh=alpha/(m-rank)
        if pvals[i]<=thresh: reject[i]=True
        else: break
    return reject

def benjamini_hochberg(pvals, alpha=0.05):
    m=len(pvals); order=sorted(range(m), key=lambda i:pvals[i]); reject=[False]*m
    kmax=-1
    for rank,i in enumerate(order):
        if pvals[i] <= (rank+1)/m*alpha: kmax=rank
    for rank,i in enumerate(order):
        if rank<=kmax: reject[i]=True
    return reject

# ============================================================
def main():
    pp("="*70); pp("EXP-0051: Re-Tokenization Churn — RE-01/02/05/06"); pp("="*70)
    pp("\nLoading tokenizers (production Rust fast)...")
    toks={}
    for name,hf in TOKENIZER_SPECS:
        t=AutoTokenizer.from_pretrained(hf, use_fast=True)
        assert t.is_fast, f"{name} must be fast"
        toks[name]=t
        pp(f"  {name}: vocab={t.vocab_size} is_fast={t.is_fast}")

    pp("\nParsing corpora...")
    sessions = parse_cc_sessions()+parse_codex_sessions()
    seams = list(extract_injection_seams(sessions))
    pp(f"  sessions={len(sessions)} seams={len(seams)}")
    sc=Counter(s[2] for s in seams)
    for k,v in sc.items(): pp(f"    {k}: {v}")
    if len(seams)<10:
        pp("FATAL: <10 seams"); return

    # Pre-draw null offsets per seam (deterministic), independent of tokenizer
    seam_null_offsets=[]
    for (prefix_text,_,_,_,_) in seams:
        tp=prefix_text[-MAX_PREFIX_CHARS:]
        L=len(tp)
        offs=[]
        for _ in range(K_NULL):
            if L>20: offs.append(null_rng.randint(20, L))
            else: offs.append(L)
        seam_null_offsets.append(offs)

    records=[]  # per (seam,tok)
    for tname,tok in toks.items():
        pp(f"\n--- tokenizing cell group: {tname} ---")
        enc=lambda s: tok.encode(s, add_special_tokens=False)
        ctrl_ids = enc("\n")
        for si,(prefix_text,result_text,source,dclass,has_tmpl) in enumerate(seams):
            tp = prefix_text[-MAX_PREFIX_CHARS:]
            prefix_ids = enc(tp)
            result_ids = enc(result_text)
            # TREATMENT
            cached = prefix_ids + result_ids
            retok  = enc(tp + result_text)
            fd = first_divergence(cached, retok)
            # CONTROL clean-\n
            c_cached = prefix_ids + ctrl_ids
            c_retok  = enc(tp + "\n")
            c_fd = first_divergence(c_cached, c_retok)
            # TEMPLATE control (<|tool_result|>)
            tmpl_prefix = tp + "\n<|tool_result|>\n"
            t_cached = enc(tmpl_prefix) + result_ids
            t_retok  = enc(tmpl_prefix + result_text)
            t_fd = first_divergence(t_cached, t_retok)
            t_churn16 = churn_from(t_fd, len(t_cached), len(t_retok), PRIMARY_BLOCK)
            # NULL: same append op at random offsets
            null_fd=[]
            for off in seam_null_offsets[si]:
                npfx = tp[:off]
                n_pref_ids = enc(npfx)
                n_cached = n_pref_ids + result_ids
                n_retok  = enc(npfx + result_text)
                null_fd.append((first_divergence(n_cached,n_retok), len(n_cached), len(n_retok)))
            records.append({
                'source':source,'tokenizer':tname,'delimiter_class':dclass,'has_chat_template':has_tmpl,
                'fd':fd,'lc':len(cached),'lr':len(retok),
                'c_fd':c_fd,'c_lc':len(c_cached),'c_lr':len(c_retok),
                't_churn16':t_churn16,
                'null_fd':null_fd,
            })
        pp(f"    done {tname}: {len([r for r in records if r['tokenizer']==tname])} records")

    # ---- derive churn at each block size ----
    def rec_churn(r, bs): return churn_from(r['fd'], r['lc'], r['lr'], bs)
    def rec_ctrl(r, bs):  return churn_from(r['c_fd'], r['c_lc'], r['c_lr'], bs)
    def rec_null(r, bs):
        return sum(churn_from(fd,lc,lr,bs) for (fd,lc,lr) in r['null_fd'])/len(r['null_fd']) if r['null_fd'] else 0.0

    cells = [(t,c) for t in [s[0] for s in TOKENIZER_SPECS] for c in CORPORA]

    # ===== AGGREGATE (block=16) sanity vs EXP-0049 (2-tokenizer subset) =====
    agg16 = [rec_churn(r,16) for r in records]
    pp(f"\n[sanity] EXP-0051 3-tok aggregate mean churn (block16) = {sum(agg16)/len(agg16):.6f}")
    sub = [rec_churn(r,16) for r in records if r['tokenizer'] in ('gpt2','qwen2-0.5b')]
    pp(f"[sanity] gpt2+qwen2 subset mean churn (block16) = {sum(sub)/len(sub):.6f}  (EXP-0049 was 0.010953)")

    # ===== RE-01 NULL MODEL (primary block=16) =====
    pp("\n"+"="*70); pp("RE-01: BPE NULL MODEL (observed seam churn - random-offset null)"); pp("="*70)
    deltas16=[rec_churn(r,16)-rec_null(r,16) for r in records]
    d_mean,d_lo,d_hi = boot_ci(deltas16, B=10000)
    re01_pass = d_lo>0
    pp(f"  observed mean (block16) = {sum([rec_churn(r,16) for r in records])/len(records):.6f}")
    pp(f"  null     mean (block16) = {sum([rec_null(r,16) for r in records])/len(records):.6f}")
    pp(f"  delta (obs-null) mean   = {d_mean:.6f}  95% CI [{d_lo:.6f}, {d_hi:.6f}]")
    pp(f"  RE-01 {'PASS (novelty exceeds generic BPE)' if re01_pass else 'PARTIAL/KILL (indistinguishable from generic BPE)'}")
    # per-cell RE-01 delta
    re01_cells={}
    for (t,c) in cells:
        cr=[r for r in records if r['tokenizer']==t and r['source']==c]
        if not cr: continue
        dl=[rec_churn(r,16)-rec_null(r,16) for r in cr]
        m,lo,hi=boot_ci(dl,B=4000)
        re01_cells[f"{t}|{c}"]={'n':len(cr),'delta':m,'ci':[lo,hi],'pass':lo>0}
        pp(f"    {t:13s} x {c:11s} n={len(cr):5d} delta={m:+.6f} CI[{lo:+.6f},{hi:+.6f}] {'PASS' if lo>0 else 'no'}")

    # ===== RE-05 PER-CELL GATES + MC CORRECTION (block=16) =====
    pp("\n"+"="*70); pp("RE-05: PER-CELL GATES (block=16) + MULTIPLE-COMPARISON CORRECTION"); pp("="*70)
    cell_stats={}; tests=[]  # tests: (name, pval)
    for (t,c) in cells:
        cr=[r for r in records if r['tokenizer']==t and r['source']==c]
        if not cr: continue
        ch=[rec_churn(r,16) for r in cr]
        diff=[rec_churn(r,16)-rec_ctrl(r,16) for r in cr]
        # gate-a: mean churn > 0
        a_mean,a_lo,a_hi=boot_ci(ch,B=10000)
        a_p = sum(1 for _ in range(1))  # placeholder
        # one-sided p (H0 mean<=0): frac of bootstrap means <=0
        nn=len(ch); cnt=0; B=10000
        for _ in range(B):
            s=0.0
            for _ in range(nn): s+=ch[boot_rng.randrange(nn)]
            if s/nn<=0: cnt+=1
        a_p=cnt/B
        # gate-b: churn - control, two-sided p
        b_mean,b_lo,b_hi=boot_ci(diff,B=10000)
        b_p=boot_p_twosided(diff,B=10000)
        # gate-c: delimiter AUC (LOO class-mean predictor, label=has_churn@16)
        by=defaultdict(list)
        for r in cr: by[r['delimiter_class']].append(rec_churn(r,16))
        preds=[]; acts=[]
        gmean=sum(ch)/len(ch)
        for r in cr:
            vals=by[r['delimiter_class']]
            if len(vals)<=1: pr=gmean
            else: pr=(sum(vals)-rec_churn(r,16))/(len(vals)-1)
            preds.append(pr); acts.append(1 if rec_churn(r,16)>0 else 0)
        auc,c_lo,c_hi,c_p=boot_auc_ci_p(preds,acts,B=2000)
        cell_stats[f"{t}|{c}"]={'n':len(cr),
            'gate_a':{'mean':a_mean,'ci':[a_lo,a_hi],'p':a_p,'raw_pass':a_lo>0},
            'gate_b':{'mean':b_mean,'ci':[b_lo,b_hi],'p':b_p,'raw_pass':b_lo>0},
            'gate_c':{'auc':auc,'ci':[c_lo,c_hi],'p':c_p,'raw_pass':c_lo>0.5}}
        tests.append((f"{t}|{c}|gate_a", a_p, b_lo if False else None))
        tests.append((f"{t}|{c}|gate_b", b_p, None))
        tests.append((f"{t}|{c}|gate_c", c_p, None))
        # store directional pass for later (a gate "passes" post-correction only if raw_pass dir AND reject H0)
    # Build flat pval list for the 18 (or fewer) tests
    test_names=[]; test_p=[]
    for (t,c) in cells:
        key=f"{t}|{c}"
        if key not in cell_stats: continue
        for g in ['gate_a','gate_b','gate_c']:
            test_names.append(f"{key}|{g}"); test_p.append(cell_stats[key][g]['p'])
    holm = holm_bonferroni(test_p, 0.05)
    bh   = benjamini_hochberg(test_p, 0.05)
    mc={}
    for nm,p,h,b in zip(test_names,test_p,holm,bh):
        key,g = nm.rsplit('|',1)
        rawpass = cell_stats[key][g]['raw_pass']
        mc[nm]={'p':p,'holm_reject':h,'bh_reject':b,'raw_pass':rawpass,
                'holm_pass':bool(h and rawpass),'bh_pass':bool(b and rawpass)}
    pp(f"\n  {'cell|gate':40s} {'p':>9} {'rawdir':>7} {'holm':>6} {'bh':>6}")
    for nm in test_names:
        m=mc[nm]
        pp(f"  {nm:40s} {m['p']:9.4f} {str(m['raw_pass']):>7} {str(m['holm_pass']):>6} {str(m['bh_pass']):>6}")
    # survivor counts on gate-b (the committee's headline generalization gate)
    gb_keys=[nm for nm in test_names if nm.endswith('gate_b')]
    gb_holm=sum(1 for nm in gb_keys if mc[nm]['holm_pass'])
    gb_bh  =sum(1 for nm in gb_keys if mc[nm]['bh_pass'])
    pp(f"\n  gate-b cells surviving Holm: {gb_holm}/{len(gb_keys)} ; BH-FDR: {gb_bh}/{len(gb_keys)}")
    ga_keys=[nm for nm in test_names if nm.endswith('gate_a')]
    gc_keys=[nm for nm in test_names if nm.endswith('gate_c')]
    ga_holm=sum(1 for nm in ga_keys if mc[nm]['holm_pass']); ga_bh=sum(1 for nm in ga_keys if mc[nm]['bh_pass'])
    gc_holm=sum(1 for nm in gc_keys if mc[nm]['holm_pass']); gc_bh=sum(1 for nm in gc_keys if mc[nm]['bh_pass'])
    pp(f"  gate-a cells surviving Holm: {ga_holm}/{len(ga_keys)} ; BH: {ga_bh}/{len(ga_keys)}")
    pp(f"  gate-c cells surviving Holm: {gc_holm}/{len(gc_keys)} ; BH: {gc_bh}/{len(gc_keys)}")

    # ===== RE-06 BLOCK-SIZE SWEEP =====
    pp("\n"+"="*70); pp("RE-06: BLOCK-SIZE SENSITIVITY {8,16,32}"); pp("="*70)
    blocksweep={}
    for bs in BLOCK_SIZES:
        allch=[rec_churn(r,bs) for r in records]
        m,lo,hi=boot_ci(allch,B=4000)
        blocksweep[bs]={'aggregate':{'mean':m,'ci':[lo,hi]}, 'cells':{}}
        pp(f"  block={bs:2d}: aggregate mean churn={m:.6f} CI[{lo:.6f},{hi:.6f}]")
        for (t,c) in cells:
            cr=[r for r in records if r['tokenizer']==t and r['source']==c]
            if not cr: continue
            ch=[rec_churn(r,bs) for r in cr]
            diff=[rec_churn(r,bs)-rec_ctrl(r,bs) for r in cr]
            cm=sum(ch)/len(ch); dm=sum(diff)/len(diff)
            blocksweep[bs]['cells'][f"{t}|{c}"]={'mean':cm,'diff':dm,'n':len(cr)}

    # ===== CHAT-TEMPLATE CONTROL (headline mitigation) =====
    raw16=[rec_churn(r,16) for r in records]; tmpl16=[r['t_churn16'] for r in records]
    mean_raw=sum(raw16)/len(raw16); mean_tmpl=sum(tmpl16)/len(tmpl16)
    redux = 1.0-(mean_tmpl/mean_raw) if mean_raw>0 else 0.0
    pp("\n"+"="*70); pp("CHAT-TEMPLATE CONTROL (HEADLINE mitigation)"); pp("="*70)
    pp(f"  mean churn raw={mean_raw:.6f}  with <|tool_result|> template={mean_tmpl:.6f}  reduction={redux*100:.1f}%")

    # ===== WRITE OUTPUTS =====
    summary={
        'experiment':'EXP-0051','claim':'CLAIM-0014','project':'PROJ-0005','level':0,
        'extends':'EXP-0049','prompt_version':'v001',
        'n_seams':len(seams),'n_records':len(records),
        'corpora':dict(sc),'tokenizers':[s[0] for s in TOKENIZER_SPECS],
        'block_sizes':BLOCK_SIZES,'primary_block':PRIMARY_BLOCK,'K_null':K_NULL,
        'sanity':{'subset_gpt2_qwen2_mean_churn16':sum(sub)/len(sub),'exp0049_was':0.010953484511091663},
        'RE01_null_model':{
            'aggregate':{'obs_mean':sum([rec_churn(r,16) for r in records])/len(records),
                         'null_mean':sum([rec_null(r,16) for r in records])/len(records),
                         'delta_mean':d_mean,'delta_ci':[d_lo,d_hi],'pass':re01_pass},
            'per_cell':re01_cells},
        'RE05_per_cell_gates':cell_stats,
        'RE05_mc_correction':{'tests':mc,
            'gate_b_survivors':{'holm':gb_holm,'bh':gb_bh,'total':len(gb_keys)},
            'gate_a_survivors':{'holm':ga_holm,'bh':ga_bh,'total':len(ga_keys)},
            'gate_c_survivors':{'holm':gc_holm,'bh':gc_bh,'total':len(gc_keys)}},
        'RE06_block_sweep':blocksweep,
        'chat_template_control':{'mean_raw':mean_raw,'mean_with_template':mean_tmpl,'reduction_frac':redux},
    }
    with open(os.path.join(RESULTS_DIR,'summary.json'),'w') as f:
        json.dump(summary,f,indent=2)
    pp(f"\n  wrote {os.path.join(RESULTS_DIR,'summary.json')}")

    # per-cell CSV
    with open(os.path.join(RESULTS_DIR,'per_cell_results.csv'),'w') as f:
        hdr=['tokenizer','corpus','n','churn16','churn8','churn32','ctrl16','diff16',
             'null16','re01_delta16','re01_pass','auc16','auc_ci_lo','auc_ci_hi',
             'gate_a_raw','gate_b_raw','gate_c_raw','gate_b_p','gate_b_holm','gate_b_bh']
        f.write(','.join(hdr)+'\n')
        for (t,c) in cells:
            key=f"{t}|{c}"
            cr=[r for r in records if r['tokenizer']==t and r['source']==c]
            if not cr: continue
            ch16=sum(rec_churn(r,16) for r in cr)/len(cr)
            ch8 =sum(rec_churn(r,8)  for r in cr)/len(cr)
            ch32=sum(rec_churn(r,32) for r in cr)/len(cr)
            ct16=sum(rec_ctrl(r,16) for r in cr)/len(cr)
            nl16=sum(rec_null(r,16) for r in cr)/len(cr)
            cs=cell_stats[key]
            gb=f"{key}|gate_b"
            row=[t,c,len(cr),f"{ch16:.6f}",f"{ch8:.6f}",f"{ch32:.6f}",f"{ct16:.6f}",
                 f"{ch16-ct16:.6f}",f"{nl16:.6f}",f"{re01_cells[key]['delta']:.6f}",
                 re01_cells[key]['pass'],f"{cs['gate_c']['auc']:.4f}",
                 f"{cs['gate_c']['ci'][0]:.4f}",f"{cs['gate_c']['ci'][1]:.4f}",
                 cs['gate_a']['raw_pass'],cs['gate_b']['raw_pass'],cs['gate_c']['raw_pass'],
                 f"{cs['gate_b']['p']:.4f}",mc[gb]['holm_pass'],mc[gb]['bh_pass']]
            f.write(','.join(str(x) for x in row)+'\n')
    pp(f"  wrote {os.path.join(RESULTS_DIR,'per_cell_results.csv')}")
    return summary

if __name__=='__main__':
    main()
