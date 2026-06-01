#!/usr/bin/env python3
"""
EXP-0053 - Realized Cross-Session Prefix-Reuse Ceiling from Tool-Schema/System-Prompt Drift.
CLAIM-0017, PROJ-0007, Level-0, CPU-only. researcher-0017-L0-r6, prompt_version v001.
Satisfies VERDICT-0060 required_evidence. Thresholds FROZEN in impl/PRE_REGISTRATION.md
(LOCKED 2026-06-01T16:09:03Z, committed b83fb0c BEFORE this run).

Cross-SESSION + STRUCTURAL HEAD (distinct from PROJ-0005 intra-session BPE-tail seam; inverse of DEAD-0006).
Reuses EXP-0051 corpus-message parsing patterns; adds head reconstruction, block-LCP, caching-best-practice
canonicalizer (RE-B1 killer), drift-free control, drift-class predictor + sham, bootstrap CIs.
Analysis layer pure stdlib; only the production tokenizer needs the EXP-0049 venv.
"""
import json, glob, os, sys, re, math, random, hashlib
from collections import defaultdict, Counter

# ---- re-exec into EXP-0049 venv for the production tokenizer ----
EXP49 = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'EXP-0049')
VENV_PYTHON = os.path.join(EXP49, '.venv', 'bin', 'python3')
if sys.executable != VENV_PYTHON and os.path.exists(VENV_PYTHON):
    os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)
import warnings; warnings.filterwarnings("ignore")
from transformers import AutoTokenizer

def pp(*a, **k): print(*a, **k, flush=True)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
BLOCK = 16
BLOCK_SWEEP = [8, 16, 32]
TOKENIZERS = [('gpt2', 'gpt2'), ('qwen2-0.5b', 'Qwen/Qwen2-0.5B')]   # gpt2 primary; qwen2 = RE-B5 robustness
boot_rng = random.Random(42)

# ================= VOLATILE-FIELD REGEXES (drift classes) =================
DRIFT_PATTERNS = [
    ('timestamp', re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?')),
    ('date',      re.compile(r'(?<!\d)\d{4}-\d{2}-\d{2}(?!T)')),
    ('uuid',      re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')),
    ('abspath',   re.compile(r'/(?:Users|home)/[^\s"\',:;]+')),
    ('version',   re.compile(r'(?<!\d)\d+\.\d+\.\d+(?:\.\d+)?')),
    ('epoch',     re.compile(r'(?<!\d)1[0-9]{9}(?![0-9])')),
]
SENTINEL = ' VOL '

def find_volatile_spans(text):
    """list of (start,end,cls) char spans of volatile fields, non-overlapping, earliest-wins."""
    spans = []
    for cls, pat in DRIFT_PATTERNS:
        for m in pat.finditer(text):
            spans.append((m.start(), m.end(), cls))
    spans.sort()
    out = []; last = -1
    for s, e, c in spans:
        if s >= last:
            out.append((s, e, c)); last = e
    return out

# ================= LIST-BLOCK CANONICALIZATION (dynamically-ordered tool/skill lists) =================
LIST_BLOCK_RE = re.compile(r'(<available_skills>)(.*?)(</available_skills>)', re.DOTALL)

def sort_list_blocks(text):
    """canonicalize dynamically-ordered list blocks by sorting their bullet entries lexicographically."""
    def _sort(m):
        head, body, tail = m.group(1), m.group(2), m.group(3)
        parts = re.split(r'(?m)^(?=\s*-\s)', body)
        preamble = parts[0] if parts and not re.match(r'\s*-\s', parts[0]) else ''
        bullets = [p for p in parts if re.match(r'\s*-\s', p)]
        bullets_sorted = sorted(bullets, key=lambda x: x.strip().lower())
        return head + preamble + ''.join(bullets_sorted) + tail
    return LIST_BLOCK_RE.sub(_sort, text)

def canonicalize(text):
    """RE-B1 caching-best-practice: sort list blocks, strip volatile fields, relocate them to SUFFIX."""
    t = sort_list_blocks(text)
    spans = find_volatile_spans(t)
    collected = []; out = []; prev = 0
    for s, e, c in spans:
        out.append(t[prev:s]); out.append(SENTINEL); collected.append(t[s:e]); prev = e
    out.append(t[prev:])
    body = ''.join(out)
    suffix = '\n<<VOLATILE_SUFFIX>>\n' + '\n'.join(collected)
    return body + suffix

def drift_free(text):
    """control: neutralize volatile fields to a constant IN PLACE + sort list blocks (no-drift skeleton)."""
    t = sort_list_blocks(text)
    spans = find_volatile_spans(t)
    out = []; prev = 0
    for s, e, c in spans:
        out.append(t[prev:s]); out.append(SENTINEL); prev = e
    out.append(t[prev:])
    return ''.join(out)

# ================= HEAD RECONSTRUCTION PER FAMILY =================
def codex_heads():
    files = sorted(glob.glob(os.path.expanduser("~/.codex/sessions/**/*.jsonl"), recursive=True))
    heads = []
    for fp in files:
        try:
            with open(fp) as f:
                lines = [json.loads(l) for l in f if l.strip()]
        except Exception:
            continue
        base = None; devs = []
        for d in lines[:10]:
            typ = d.get("type"); p = d.get("payload", {}) if isinstance(d.get("payload"), dict) else {}
            if typ == "session_meta":
                bi = p.get("base_instructions")
                base = bi.get("text") if isinstance(bi, dict) else (bi if isinstance(bi, str) else None)
            if typ == "response_item" and p.get("role") == "developer":
                for c in p.get("content", []):
                    if isinstance(c, dict) and c.get("text"):
                        devs.append(c["text"])
        if base and devs:
            heads.append({'family': 'codex', 'file': os.path.basename(fp),
                          'text': base + "\n" + "\n".join(devs)})
    return heads

def cc_heads():
    """CC documented env block (real per-session values from trace) ++ first user-message template."""
    files = sorted(glob.glob(os.path.expanduser("~/.claude/projects/**/*.jsonl"), recursive=True))
    raw = []
    for fp in files:
        meta = None; first_user = None
        try:
            with open(fp) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    d = json.loads(line)
                    m = d.get("message")
                    if isinstance(m, dict) and meta is None:
                        meta = d
                    if isinstance(m, dict) and m.get("role") == "user" and first_user is None:
                        c = m.get("content")
                        if isinstance(c, str):
                            first_user = c
                        elif isinstance(c, list):
                            for b in c:
                                if isinstance(b, dict) and b.get("type") == "text":
                                    first_user = b.get("text"); break
                    if meta is not None and first_user is not None:
                        break
        except Exception:
            continue
        if meta is None or not first_user:
            continue
        ts = meta.get("timestamp", "2026-01-01T00:00:00Z"); date = ts[:10]
        env = ("<env>\n"
               f"Working directory: {meta.get('cwd', '')}\n"
               "Is directory a git repo: Yes\n"
               f"Current branch: {meta.get('gitBranch', '')}\n"
               "Platform: darwin\n"
               f"Today's date: {date}\n"
               f"Claude Code version: {meta.get('version', '')}\n"
               f"Session ID: {meta.get('sessionId', '')}\n"
               "</env>\n")
        raw.append({'family': 'claude_code', 'file': os.path.basename(fp),
                    'env': env, 'tmpl': first_user, 'text': env + first_user})
    by = defaultdict(list)
    for r in raw:
        by[hashlib.md5(r['tmpl'].encode()).hexdigest()].append(r)
    if not by:
        return []
    return max(by.values(), key=len)

def gemini_heads():
    files = sorted(glob.glob(os.path.expanduser("~/.gemini/tmp/**/chats/*.json"), recursive=True))
    raw = []
    for fp in files:
        try:
            d = json.load(open(fp))
        except Exception:
            continue
        msgs = d.get("messages")
        if not isinstance(msgs, list) or not msgs:
            continue
        first = msgs[0]; txt = ""
        c = first.get("content")
        if isinstance(c, list):
            txt = "".join(x.get("text", "") for x in c if isinstance(x, dict))
        elif isinstance(c, str):
            txt = c
        if not txt:
            continue
        env = (f"<session>\nsessionId: {d.get('sessionId', '')}\n"
               f"projectHash: {d.get('projectHash', '')}\n"
               f"startTime: {d.get('startTime', '')}\n</session>\n")
        raw.append({'family': 'gemini', 'file': os.path.basename(fp), 'env': env, 'tmpl': txt, 'text': env + txt})
    by = defaultdict(list)
    for r in raw:
        by[hashlib.md5(r['tmpl'].encode()).hexdigest()].append(r)
    if not by:
        return []
    return max(by.values(), key=len)

# ================= METRICS =================
def block_lcp_tokens(a, b, bs=BLOCK):
    """# leading bs-token blocks identical between token-id lists a,b, x bs => tokens of shared prefix."""
    n = min(len(a), len(b)) // bs
    k = 0
    for blk in range(n):
        s = blk * bs
        if a[s:s + bs] == b[s:s + bs]:
            k += 1
        else:
            break
    return k * bs

def first_div_block(a, b, bs=BLOCK):
    n = min(len(a), len(b)) // bs
    for blk in range(n):
        s = blk * bs
        if a[s:s + bs] != b[s:s + bs]:
            return blk
    if len(a) != len(b):
        return n
    return -1

def first_div_token(a, b):
    m = min(len(a), len(b))
    for i in range(m):
        if a[i] != b[i]:
            return i
    return -1 if len(a) == len(b) else m

def multiset_shared_tokens(a, b):
    """position-agnostic shared content (naive upper bound): sum(min counts)."""
    ca = Counter(a); cb = Counter(b)
    return sum((ca & cb).values())

# ================= AUC + BOOTSTRAP (EXP-0049/0051 conventions) =================
def fast_auc(preds, acts):
    paired = sorted(zip(preds, acts), key=lambda x: x[0])
    n_p = sum(1 for _, a in paired if a == 1); n_n = len(paired) - n_p
    if n_p == 0 or n_n == 0:
        return 0.5, n_p, n_n
    rs = 0.0; i = 0
    while i < len(paired):
        j = i
        while j < len(paired) and paired[j][0] == paired[i][0]:
            j += 1
        avg = (i + j + 1) / 2.0
        for k in range(i, j):
            if paired[k][1] == 1:
                rs += avg
        i = j
    u = rs - n_p * (n_p + 1) / 2
    return u / (n_p * n_n), n_p, n_n

def boot_ci(vals, B=10000, rng=boot_rng):
    n = len(vals)
    if n == 0:
        return 0.0, 0.0, 0.0
    means = []
    for _ in range(B):
        s = 0.0
        for _ in range(n):
            s += vals[rng.randrange(n)]
        means.append(s / n)
    means.sort()
    return sum(vals) / n, means[int(0.025 * B)], means[int(0.975 * B)]

def boot_auc_ci(preds, acts, B=2000, rng=boot_rng):
    n = len(preds); idx = list(range(n)); aucs = []
    for _ in range(B):
        si = [idx[rng.randrange(n)] for _ in range(n)]
        a, _, _ = fast_auc([preds[i] for i in si], [acts[i] for i in si]); aucs.append(a)
    aucs.sort()
    base, _, _ = fast_auc(preds, acts)
    return base, aucs[int(0.025 * B)], aucs[int(0.975 * B)]

# ================= PER-FAMILY ANALYSIS =================
def analyze_family(heads, tname, tok, bs=BLOCK):
    """heads: list of {'text':...}. Returns metrics dict for one (family,tokenizer,block)."""
    enc = []
    for h in heads:
        o = tok(h['text'], add_special_tokens=False, return_offsets_mapping=True)
        enc.append({'ids': o['input_ids'], 'off': o['offset_mapping'], 'text': h['text'], 'file': h.get('file', '')})
    order = sorted(range(len(enc)), key=lambda i: len(enc[i]['ids']))
    R = order[len(order) // 2]
    ref = enc[R]

    def tk(s):
        return tok(s, add_special_tokens=False)['input_ids']
    ref_canon = tk(canonicalize(ref['text'])); ref_df = tk(drift_free(ref['text']))

    rows = []
    pred_scores = []; sham_scores = []; pred_labels = []
    seam_count = 0; struct_count = 0
    for i, e in enumerate(enc):
        if i == R:
            continue
        a = e['ids']; b = ref['ids']
        realized_raw = block_lcp_tokens(a, b, bs)
        naive = multiset_shared_tokens(a, b)
        a_c = tk(canonicalize(e['text'])); a_d = tk(drift_free(e['text']))
        realized_canon = block_lcp_tokens(a_c, ref_canon, bs)
        naive_canon = multiset_shared_tokens(a_c, ref_canon)
        realized_df = block_lcp_tokens(a_d, ref_df, bs)
        shortfall_raw = naive - realized_raw
        shortfall_canon = naive_canon - realized_canon
        drift_cost = realized_df - realized_raw
        rows.append({'file': e['file'], 'len': len(a), 'naive': naive, 'realized_raw': realized_raw,
                     'realized_canon': realized_canon, 'realized_df': realized_df,
                     'shortfall_raw': shortfall_raw, 'shortfall_canon': shortfall_canon, 'drift_cost': drift_cost})
        # ---- RE-B4: first-divergence BPE-seam vs structural (char streams) ----
        fdt = first_div_token(a, b)
        if 0 <= fdt < len(e['off']) and fdt < len(ref['off']):
            ca = e['off'][fdt][0] if e['off'][fdt] else 0
            cr = ref['off'][fdt][0] if ref['off'][fdt] else 0
            wa = e['text'][max(0, ca - 32):ca + 32]; wr = ref['text'][max(0, cr - 32):cr + 32]
            if wa == wr:
                seam_count += 1
            else:
                struct_count += 1
        # ---- RE-B3: drift-class predictor vs sham, pooled blocks ----
        fdb = first_div_block(a, b, bs)
        vol_spans = find_volatile_spans(e['text'])
        vol_block = set()
        for (s, en, c) in vol_spans:
            for ti, off in enumerate(e['off']):
                ts, te = off
                if ts <= s < te or (ts <= s and te >= en):
                    vol_block.add(ti // bs); break
        sham_block = first_div_block(a, a_d, bs)
        nblocks = len(a) // bs
        for blk in range(nblocks):
            lab = 1 if blk == fdb else 0
            pscore = (1.0 / (blk + 1)) if blk in vol_block else 0.0
            sscore = (1.0 / (blk + 1)) if (sham_block >= 0 and blk >= sham_block) else 0.0
            pred_scores.append(pscore); sham_scores.append(sscore); pred_labels.append(lab)

    def col(k):
        return [r[k] for r in rows]
    out = {'family': heads[0]['family'], 'tokenizer': tname, 'n_sessions': len(heads), 'n_compared': len(rows),
           'ref_file': ref['file'], 'block': bs}
    for k in ['naive', 'realized_raw', 'realized_canon', 'realized_df', 'shortfall_raw', 'shortfall_canon', 'drift_cost']:
        m, lo, hi = boot_ci(col(k), B=10000)
        out[k] = {'mean': m, 'ci': [lo, hi]}
    sa = out['shortfall_canon']
    out['RE_B1'] = {'shortfall_after_mean': sa['mean'], 'ci': sa['ci'],
                    'PASS': bool(sa['mean'] >= 16 and sa['ci'][0] >= 16),
                    'KILL': bool(sa['mean'] < 16 or sa['ci'][0] <= 0)}
    dc = out['drift_cost']
    out['RE_B2'] = {'drift_cost_mean': dc['mean'], 'ci': dc['ci'],
                    'PASS': bool(dc['mean'] >= 16 and dc['ci'][0] >= 16),
                    'KILL': bool(dc['mean'] < 16 or dc['ci'][0] < 16)}
    if sum(pred_labels) > 0 and any(x == 0 for x in pred_labels):
        ra, rlo, rhi = boot_auc_ci(pred_scores, pred_labels, B=2000)
        sha, slo, shi = boot_auc_ci(sham_scores, pred_labels, B=2000)
    else:
        ra, rlo, rhi = 0.5, 0.5, 0.5; sha, slo, shi = 0.5, 0.5, 0.5
    out['RE_B3'] = {'real_auc': ra, 'real_ci': [rlo, rhi], 'sham_auc': sha, 'sham_ci': [slo, shi],
                    'n_pos': sum(pred_labels), 'n_blocks': len(pred_labels),
                    'PASS': bool(ra >= 0.70 and ra > sha)}
    tot = seam_count + struct_count
    seam_frac = (seam_count / tot) if tot else 0.0
    out['RE_B4'] = {'n_firstdiv': tot, 'bpe_seam': seam_count, 'structural': struct_count,
                    'seam_fraction': seam_frac, 'X_threshold': 0.50,
                    'FOLD': bool(seam_frac >= 0.50), 'STAY_DISTINCT': bool(seam_frac < 0.50)}
    out['rows'] = rows
    return out

def main():
    pp("=" * 72); pp("EXP-0053: Cross-Session Prefix-Reuse Ceiling (PROJ-0007/CLAIM-0017)"); pp("=" * 72)
    pp("Loading production tokenizers (Rust fast)...")
    toks = {}
    for name, hf in TOKENIZERS:
        t = AutoTokenizer.from_pretrained(hf, use_fast=True)
        assert t.is_fast, f"{name} must be fast"
        toks[name] = t; pp(f"  {name}: vocab={t.vocab_size} fast={t.is_fast}")

    pp("\nReconstructing heads...")
    fams = {'codex': codex_heads(), 'claude_code': cc_heads(), 'gemini': gemini_heads()}
    for k, v in fams.items():
        pp(f"  {k}: {len(v)} sessions (shared-skeleton group)")
    COUNTED = ['codex', 'claude_code']   # RE-B6 counted families (real in-prompt drift, >=8 sessions)

    results = {'experiment': 'EXP-0053', 'claim': 'CLAIM-0017', 'project': 'PROJ-0007', 'level': 0,
               'prompt_version': 'v001', 'lock_ts': '2026-06-01T16:09:03Z', 'block_primary': BLOCK,
               'tokenizers': [n for n, _ in TOKENIZERS], 'counted_families': COUNTED,
               'family_sizes': {k: len(v) for k, v in fams.items()},
               'cells': {}, 'block_sweep': {}}

    for fam, heads in fams.items():
        if len(heads) < 3:
            pp(f"  [skip {fam}: <3 sessions]"); continue
        for tname, tok in toks.items():
            pp(f"\n--- analyze {fam} x {tname} (n={len(heads)}) ---")
            r = analyze_family(heads, tname, tok, BLOCK)
            key = f"{fam}|{tname}"
            rows = r.pop('rows')
            results['cells'][key] = r
            pp(f"    naive={r['naive']['mean']:.1f}  realized_raw={r['realized_raw']['mean']:.1f}  "
               f"realized_canon={r['realized_canon']['mean']:.1f}  realized_df={r['realized_df']['mean']:.1f}")
            pp(f"    shortfall_raw={r['shortfall_raw']['mean']:.1f}  shortfall_canon={r['shortfall_canon']['mean']:.1f}"
               f"  drift_cost={r['drift_cost']['mean']:.1f}")
            pp(f"    RE-B1 {'PASS' if r['RE_B1']['PASS'] else ('KILL' if r['RE_B1']['KILL'] else 'INCONCLUSIVE')}"
               f" (shortfall_after={r['RE_B1']['shortfall_after_mean']:.1f} CI{r['RE_B1']['ci']})")
            pp(f"    RE-B2 {'PASS' if r['RE_B2']['PASS'] else 'KILL'} (drift_cost={r['RE_B2']['drift_cost_mean']:.1f} CI{r['RE_B2']['ci']})")
            pp(f"    RE-B3 real_auc={r['RE_B3']['real_auc']:.3f} sham_auc={r['RE_B3']['sham_auc']:.3f} "
               f"{'PASS' if r['RE_B3']['PASS'] else 'fail'}")
            pp(f"    RE-B4 seam_frac={r['RE_B4']['seam_fraction']:.3f} ({r['RE_B4']['bpe_seam']}/{r['RE_B4']['n_firstdiv']}) "
               f"{'FOLD' if r['RE_B4']['FOLD'] else 'STAY-DISTINCT'}")
            if tname == 'gpt2':
                csvp = os.path.join(RESULTS_DIR, f"per_row_{fam}.csv")
                with open(csvp, 'w') as f:
                    f.write("file,len,naive,realized_raw,realized_canon,realized_df,shortfall_raw,shortfall_canon,drift_cost\n")
                    for rr in rows:
                        f.write(f"{rr['file']},{rr['len']},{rr['naive']},{rr['realized_raw']},{rr['realized_canon']},"
                                f"{rr['realized_df']},{rr['shortfall_raw']},{rr['shortfall_canon']},{rr['drift_cost']}\n")

    # ---- RE-B6 cross-family consistency (primary tokenizer) ----
    pri = 'gpt2'
    fam_b1 = {f: results['cells'].get(f"{f}|{pri}", {}).get('RE_B1', {}) for f in COUNTED if f"{f}|{pri}" in results['cells']}
    b1_dirs = set('PASS' if v.get('PASS') else 'KILL' for v in fam_b1.values())
    results['RE_B6'] = {'counted_families': list(fam_b1.keys()),
                        'B1_consistent': len(b1_dirs) == 1,
                        'B1_directions': {f: ('PASS' if v.get('PASS') else 'KILL') for f, v in fam_b1.items()},
                        'n_counted': len(fam_b1)}

    # ---- RE-B5 tokenizer-invariance of first-divergence ----
    invar = {}
    for fam in COUNTED:
        g = results['cells'].get(f"{fam}|gpt2", {}).get('RE_B4', {})
        q = results['cells'].get(f"{fam}|qwen2-0.5b", {}).get('RE_B4', {})
        if g and q:
            invar[fam] = {'gpt2_struct_frac': 1 - g['seam_fraction'], 'qwen2_struct_frac': 1 - q['seam_fraction'],
                          'both_majority_structural': bool((1 - g['seam_fraction']) >= 0.5 and (1 - q['seam_fraction']) >= 0.5)}
    results['RE_B5'] = {'tokenizer_invariance': invar}

    # ---- block-size sweep (codex+cc, gpt2) ----
    for bs in BLOCK_SWEEP:
        sweep = {}
        for fam in COUNTED:
            if len(fams[fam]) < 3:
                continue
            r = analyze_family(fams[fam], 'gpt2', toks['gpt2'], bs); r.pop('rows', None)
            sweep[fam] = {'realized_raw': r['realized_raw']['mean'], 'shortfall_raw': r['shortfall_raw']['mean'],
                          'shortfall_canon': r['shortfall_canon']['mean'], 'drift_cost': r['drift_cost']['mean']}
        results['block_sweep'][bs] = sweep

    # ---- OVERALL pre-registered decision (gpt2 primary, per-family) ----
    overall = {}
    for fam in COUNTED:
        c = results['cells'].get(f"{fam}|gpt2")
        if not c:
            continue
        kill_reasons = []
        if c['RE_B1']['KILL']:
            kill_reasons.append('RE-B1 shortfall vanishes under canonicalization (prompt-eng anti-pattern)')
        if c['RE_B2']['KILL']:
            kill_reasons.append('RE-B2 drift-attributable effect < 1 block (quantization)')
        if c['RE_B4']['FOLD']:
            kill_reasons.append('RE-B4 fold-trigger fired (>=50% BPE-seam => fold into PROJ-0005)')
        overall[fam] = {'kill_reasons': kill_reasons,
                        'verdict': 'KILL/NEGATIVE' if kill_reasons else 'PASS',
                        'RE_B1_PASS': c['RE_B1']['PASS'], 'RE_B2_PASS': c['RE_B2']['PASS'],
                        'RE_B3_PASS': c['RE_B3']['PASS'], 'RE_B4_FOLD': c['RE_B4']['FOLD']}
    results['overall_per_family'] = overall

    with open(os.path.join(RESULTS_DIR, 'summary.json'), 'w') as f:
        json.dump(results, f, indent=2)
    pp("\nWROTE summary.json")
    pp("\nOVERALL per-family (gpt2):")
    for fam, o in overall.items():
        pp(f"  {fam}: {o['verdict']}  {('; '.join(o['kill_reasons']) if o['kill_reasons'] else 'all kill-gates clear')}")
    return results

if __name__ == '__main__':
    main()
