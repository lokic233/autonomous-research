#!/usr/bin/env python3
"""
EXP-0059 — Cross-Session KV-Sharing Ceiling: Quantified Volatile-Token Normalization Budget.
CLAIM-0024 / PROJ-0013, Level-0, CPU. researcher-0024-L0-r7, prompt_version v001.
Executes the FROZEN impl/PRE_REGISTRATION.md (LOCKED-TS 2026-06-01T22:43:20Z, committed 0d14531 BEFORE this run).

CHARACTERIZATION + POLICY-COMPARISON (NOT a dAUC predictor). Deliverable = the GAP (realized vs canonicalized-max
cross-session sharable fraction), its CONCENTRATION (per-class Lorenz/Gini + marginals = the normalization budget),
a capacity-sim recompute-saved gap, and the collision/alias cost. Unlocked mass reported as an UPPER BOUND (FIX-2).

Reuses EXP-0053 head reconstruction (codex_heads/cc_heads), block_lcp, volatile-span machinery, and the
relocate-to-suffix canonicalizer VERBATIM; parameterizes masking by class subset. Pure stdlib analysis; the
EXP-0049 venv is used ONLY for the gpt2 production tokenizer (token counting).
"""
import json, glob, os, sys, re, random, hashlib
from collections import defaultdict, Counter

# ---- re-exec into EXP-0049 venv for the production tokenizer (token counting only) ----
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
SEED = 20260601
NBOOT = 2000
LOCKED_TS = "2026-06-01T22:43:20Z"
PREREG_COMMIT = "0d14531"
boot_rng = random.Random(SEED)

# ================= FROZEN VOLATILE-CLASS TAXONOMY (priority order; specific first) =================
# (priority, class_name, compiled_regex). Value-only spans (labels stay static/shared).
DRIFT_PATTERNS = [
    (1, 'session_uuid', re.compile(r'(?<=Session ID: )[0-9a-fA-F-]{8,}')),
    (1, 'session_uuid', re.compile(r'(?<=sessionId: )[0-9a-fA-F-]{8,}')),
    (1, 'session_uuid', re.compile(r'(?<="sessionId":")[0-9a-fA-F-]{8,}')),
    (2, 'cwd',          re.compile(r'(?<=Working directory: )/[^\s"\',:;\n]+')),
    (2, 'cwd',          re.compile(r'(?<=cwd: )/[^\s"\',:;\n]+')),
    (3, 'pid',          re.compile(r'(?i)\bpid[\s:=]+\d{2,7}\b')),
    (4, 'timestamp',    re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?')),
    (5, 'date',         re.compile(r'(?<!\d)\d{4}-\d{2}-\d{2}(?!T)')),
    (6, 'uuid',         re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')),
    (7, 'abspath',      re.compile(r'/(?:Users|home)/[^\s"\',:;\n]+')),
    (8, 'version',      re.compile(r'(?<!\d)\d+\.\d+\.\d+(?:\.\d+)?')),
    (9, 'epoch',        re.compile(r'(?<!\d)1[0-9]{9}(?![0-9])')),
    (10, 'gitbranch',   re.compile(r'(?<=Current branch: )[^\s\n]+')),
    (10, 'gitbranch',   re.compile(r'(?<=gitBranch": ")[^"\n]+')),
    (11, 'sandbox',     re.compile(r'`sandbox_mode` is `[\w-]+`')),
    (11, 'sandbox',     re.compile(r'`(?:read-only|danger-full-access|workspace-write)`')),
    (12, 'approval',    re.compile(r'`approval_policy` is `[\w-]+`')),
    (12, 'approval',    re.compile(r'Approval policy is currently [\w-]+')),
    (12, 'approval',    re.compile(r'Approvals are your mechanism[^.]*\.')),
]
ALL_CLASSES = ['session_uuid', 'cwd', 'pid', 'timestamp', 'date', 'uuid', 'abspath',
               'version', 'epoch', 'gitbranch', 'sandbox', 'approval']
INERT_CLASSES = {'session_uuid', 'pid', 'timestamp', 'date', 'uuid', 'epoch'}
SEMANTIC_CLASSES = {'cwd', 'abspath', 'version', 'gitbranch', 'sandbox', 'approval'}
SENTINEL = ' VOL '

def find_volatile_spans(text):
    """non-overlapping (start,end,cls) spans; earliest-start wins; identical span -> more specific (lower prio)."""
    spans = []
    for prio, cls, pat in DRIFT_PATTERNS:
        for m in pat.finditer(text):
            spans.append((m.start(), m.end(), prio, cls))
    spans.sort(key=lambda x: (x[0], x[1], x[2]))  # start, end, priority(specific first)
    out = []; last = -1
    for s, e, prio, c in spans:
        if s >= last:
            out.append((s, e, c)); last = e
    return out

def mask_subset(text, classes):
    """strip spans whose class in `classes`, replace in-place with sentinel, relocate stripped text to SUFFIX.
    classes=set()/None -> returns text unchanged (FLOOR)."""
    if not classes:
        return text
    spans = [sp for sp in find_volatile_spans(text) if sp[2] in classes]
    if not spans:
        return text
    collected = []; out = []; prev = 0
    for s, e, c in spans:
        out.append(text[prev:s]); out.append(SENTINEL); collected.append(text[s:e]); prev = e
    out.append(text[prev:])
    return ''.join(out) + '\n<<VOLATILE_SUFFIX>>\n' + '\n'.join(collected)

# ================= HEAD RECONSTRUCTION (EXP-0053 verbatim) =================
def drift_free_all(text):
    """neutralize ALL volatile fields in place (for CC family grouping key only)."""
    spans = find_volatile_spans(text)
    out = []; prev = 0
    for s, e, c in spans:
        out.append(text[prev:s]); out.append(SENTINEL); prev = e
    out.append(text[prev:])
    return ''.join(out)

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
        key = hashlib.md5(drift_free_all(r['tmpl'])[:400].encode()).hexdigest()
        by[key].append(r)
    if not by:
        return []
    return max(by.values(), key=len)

# ================= METRICS =================
def block_lcp_tokens(a, b, bs=BLOCK):
    n = min(len(a), len(b)) // bs
    k = 0
    for blk in range(n):
        s = blk * bs
        if a[s:s + bs] == b[s:s + bs]:
            k += 1
        else:
            break
    return k * bs

def gini(values):
    vs = sorted(v for v in values if v > 0)
    n = len(vs)
    if n == 0:
        return 0.0
    s = sum(vs)
    if s <= 0:
        return 0.0
    cum = 0.0
    for i, v in enumerate(vs):
        cum += (i + 1) * v
    return (2 * cum) / (n * s) - (n + 1) / n

def lorenz_points(values):
    """cumulative-share points (x=class-rank-share, y=mass-share) for the Lorenz curve."""
    vs = sorted(v for v in values if v >= 0)
    n = len(vs); s = sum(vs)
    if n == 0 or s <= 0:
        return []
    pts = [[0.0, 0.0]]; cum = 0.0
    for i, v in enumerate(vs):
        cum += v
        pts.append([(i + 1) / n, cum / s])
    return pts

def hhi(values):
    s = sum(v for v in values if v > 0)
    if s <= 0:
        return 0.0
    return sum((v / s) ** 2 for v in values if v > 0)

# ================= PER-CORPUS ANALYSIS =================
def analyze_corpus(heads, tok, corpus, bs=BLOCK):
    pp(f"\n--- analyze {corpus} (n={len(heads)}) ---")
    def tk(s):
        return tok(s, add_special_tokens=False)['input_ids']

    # encode raw + reference selection (median head length)
    raw_ids = [tk(h['text']) for h in heads]
    order = sorted(range(len(heads)), key=lambda i: len(raw_ids[i]))
    R = order[len(order) // 2]
    ref_text = heads[R]['text']

    # precompute reference variants
    ref_raw = raw_ids[R]
    ref_canon = tk(mask_subset(ref_text, set(ALL_CLASSES)))
    ref_by_class = {c: tk(mask_subset(ref_text, {c})) for c in ALL_CLASSES}

    per_session = []          # dict per non-ref session
    class_mass = {c: 0.0 for c in ALL_CLASSES}   # total unlocked mass per class (sum of marginals)
    # collision accounting (FIX-3): among unlocked prefix region, count masked spans w/ differing vs identical raw val
    coll = {'unlocked_blocks_total': 0, 'spans_in_unlocked_diff': 0, 'spans_in_unlocked_same': 0,
            'diff_inert': 0, 'diff_semantic': 0, 'same_inert': 0, 'same_semantic': 0}
    # build reference's masked-span value map keyed by approximate ordinal occurrence per class
    ref_spans_by_class = defaultdict(list)
    for s, e, c in find_volatile_spans(ref_text):
        ref_spans_by_class[c].append(ref_text[s:e])

    for i, h in enumerate(heads):
        if i == R:
            continue
        a_raw = raw_ids[i]
        realized_raw = block_lcp_tokens(a_raw, ref_raw, bs)
        a_canon = tk(mask_subset(h['text'], set(ALL_CLASSES)))
        canon_max = block_lcp_tokens(a_canon, ref_canon, bs)
        gap = max(0, canon_max - realized_raw)
        rec = {'file': h['file'], 'len': len(a_raw), 'realized_raw': realized_raw,
               'canon_max': canon_max, 'gap': gap, 'unlocked': {}}
        for c in ALL_CLASSES:
            a_c = tk(mask_subset(h['text'], {c}))
            lcp_c = block_lcp_tokens(a_c, ref_by_class[c], bs)
            u = max(0, lcp_c - realized_raw)
            rec['unlocked'][c] = u
            class_mass[c] += u
        per_session.append(rec)

        # ---- collision / alias accounting in the UNLOCKED region (FIX-3) ----
        # unlocked region = char span of this session's head between raw-divergence and canon-divergence.
        if gap > 0:
            spans_i = defaultdict(list)
            for s, e, c in find_volatile_spans(h['text']):
                spans_i[c].append((h['text'][s:e]))
            # for each class, compare the ordinal-matched raw values of session vs reference within unlocked range.
            # operationalize at class granularity: a class contributes an alias if it has unlocked mass and the
            # session's value(s) differ from the reference's value(s).
            for c in ALL_CLASSES:
                if rec['unlocked'][c] <= 0:
                    continue
                coll['unlocked_blocks_total'] += rec['unlocked'][c] // bs
                vi = spans_i.get(c, []); vr = ref_spans_by_class.get(c, [])
                differ = (vi != vr)
                if differ:
                    coll['spans_in_unlocked_diff'] += 1
                    coll['diff_semantic' if c in SEMANTIC_CLASSES else 'diff_inert'] += 1
                else:
                    coll['spans_in_unlocked_same'] += 1
                    coll['same_semantic' if c in SEMANTIC_CLASSES else 'same_inert'] += 1

    n = len(per_session)
    mean_raw = sum(r['realized_raw'] for r in per_session) / n if n else 0.0
    mean_canon = sum(r['canon_max'] for r in per_session) / n if n else 0.0
    mean_gap = sum(r['gap'] for r in per_session) / n if n else 0.0
    realized_frac = (mean_raw / mean_canon) if mean_canon > 0 else 1.0

    # ---- RE-A0 ----
    re_a0 = {'mean_realized_raw': mean_raw, 'mean_canon_max': mean_canon, 'mean_gap': mean_gap,
             'realized_frac': realized_frac, 'threshold': 0.6,
             'PASS_gap_exists': bool(realized_frac <= 0.6),
             'CLEAN_KILL_no_ceiling': bool(realized_frac > 0.6)}

    # ---- RE-A1 concentration ----
    total_unlocked = sum(class_mass.values())
    ranked = sorted(class_mass.items(), key=lambda kv: -kv[1])
    top3 = ranked[:3]
    top3_mass = sum(v for _, v in top3)
    top3_share = (top3_mass / total_unlocked) if total_unlocked > 0 else 0.0
    masses = [class_mass[c] for c in ALL_CLASSES]
    re_a1 = {'class_mass': dict(class_mass), 'class_mass_ranked': ranked,
             'total_unlocked_mass(sum_marginals)': total_unlocked,
             'total_gap_mass(canon-raw)': sum(r['gap'] for r in per_session),
             'top3_classes': [c for c, _ in top3], 'top3_share': top3_share, 'threshold': 0.50,
             'gini_across_classes': gini(masses), 'lorenz_points': lorenz_points(masses),
             'PASS_concentrated': bool(top3_share >= 0.50),
             'FAIL_diffuse': bool(top3_share < 0.50)}
    # FIX-4 per-class marginal share of gap-closure
    re_a1['per_class_marginal_share'] = {c: (class_mass[c] / total_unlocked if total_unlocked > 0 else 0.0)
                                         for c in ALL_CLASSES}
    # flag single-class domination of the top-3
    re_a1['top1_share_of_top3'] = (top3[0][1] / top3_mass) if top3_mass > 0 else 0.0
    re_a1['single_class_dominates_top3'] = bool(re_a1['top1_share_of_top3'] >= 0.80)

    # ---- RE-A3 bootstrap (session + class clustered) on top3 share; HHI across sessions ----
    sess_gap = [r['gap'] for r in per_session]
    hhi_sessions = hhi(sess_gap)
    # per-session per-class unlocked for resampling
    sess_unlocked = [[r['unlocked'][c] for c in ALL_CLASSES] for r in per_session]
    boot_top3 = []
    K = len(ALL_CLASSES)
    for _ in range(NBOOT):
        # resample sessions (clustered) and classes (with replacement) -> FIX-1 class-selection variance
        si = [boot_rng.randrange(n) for _ in range(n)] if n else []
        ci = [boot_rng.randrange(K) for _ in range(K)]
        cm = [0.0] * K
        for s_ix in si:
            row = sess_unlocked[s_ix]
            for slot, c_ix in enumerate(ci):
                cm[slot] += row[c_ix]
        tot = sum(cm)
        if tot <= 0:
            continue
        srt = sorted(cm, reverse=True)
        boot_top3.append(sum(srt[:3]) / tot)
    boot_top3.sort()
    if boot_top3:
        ci_lo = boot_top3[int(0.025 * len(boot_top3))]
        ci_hi = boot_top3[int(0.975 * len(boot_top3))]
    else:
        ci_lo = ci_hi = 0.0
    re_a3 = {'top3_share_point': top3_share, 'top3_share_CI95': [ci_lo, ci_hi],
             'bootstrap_B': NBOOT, 'includes_class_selection_variance': True,
             'HHI_unlocked_mass_across_sessions': hhi_sessions,
             'HHI_flag_domination': bool(hhi_sessions > 0.2)}

    # ---- FIX-3 collision rate ----
    denom = coll['spans_in_unlocked_diff'] + coll['spans_in_unlocked_same']
    sem_denom = coll['diff_semantic'] + coll['same_semantic']
    collision = {
        'unlocked_class_instances': denom,
        'alias_rate_overall': (coll['spans_in_unlocked_diff'] / denom) if denom else 0.0,
        'alias_rate_semantic_classes': (coll['diff_semantic'] / sem_denom) if sem_denom else 0.0,
        'noop_unlock_rate(identical_raw)': (coll['spans_in_unlocked_same'] / denom) if denom else 0.0,
        'diff_inert': coll['diff_inert'], 'diff_semantic': coll['diff_semantic'],
        'same_inert': coll['same_inert'], 'same_semantic': coll['same_semantic'],
        'note': 'alias = unlocked prefix relies on masking a class whose RAW value differs cross-session; '
                'semantic-class alias rate is the real cost side (cwd/abspath/version/gitbranch/sandbox/approval).'}

    return {'corpus': corpus, 'n_sessions': len(heads), 'n_compared': n, 'ref_file': heads[R]['file'],
            'block': bs, 'RE_A0': re_a0, 'RE_A1': re_a1, 'RE_A3': re_a3, 'collision': collision,
            '_per_session': per_session, '_raw_ids': raw_ids, '_R': R, '_heads': heads, '_tk': tk}

# ================= RE-A2 CAPACITY SIM (cross-session radix sharing WITH vs WITHOUT canonicalizer) =================
CAP_FRACS = [0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 1.00]

def capacity_sim(heads, tk, variant_classes, bs=BLOCK):
    """Process sessions in file order; cache up to C most-recently-used head anchors. Per session,
    hit_tokens = max over cached anchors of block_lcp; recompute = len - hit. Returns curve over CAP_FRACS."""
    # encode each head under the variant (raw if variant_classes is None/empty)
    ids = [tk(mask_subset(h['text'], variant_classes)) for h in heads]
    N = len(ids)
    distinct = len({tuple(x) for x in ids})
    curve = []
    for frac in CAP_FRACS:
        C = max(1, int(round(frac * distinct)))
        cache = []  # list of (token_ids), MRU at end
        tot_recompute = 0; tot_hit = 0; tot_len = 0; n_full_hits = 0
        for x in ids:
            best = 0
            for anchor in cache:
                h = block_lcp_tokens(x, anchor, bs)
                if h > best:
                    best = h
            recompute = len(x) - best
            tot_recompute += recompute; tot_hit += best; tot_len += len(x)
            if best >= (len(x) // bs) * bs and best > 0:
                n_full_hits += 1
            # insert into cache (MRU); evict LRU if over capacity
            cache.append(x)
            if len(cache) > C:
                cache.pop(0)
        curve.append({'cap_frac': frac, 'C': C, 'tot_recompute_tok': tot_recompute,
                      'tot_hit_tok': tot_hit, 'tot_len_tok': tot_len,
                      'hit_rate': (tot_hit / tot_len) if tot_len else 0.0})
    return curve

def re_a2(heads, tk, bs=BLOCK):
    raw_curve = capacity_sim(heads, tk, None, bs)
    canon_curve = capacity_sim(heads, tk, set(ALL_CLASSES), bs)
    rows = []
    any_pos = False
    for rc, cc in zip(raw_curve, canon_curve):
        saved = rc['tot_recompute_tok'] - cc['tot_recompute_tok']
        saved_frac = (saved / rc['tot_recompute_tok']) if rc['tot_recompute_tok'] else 0.0
        hit_delta = cc['hit_rate'] - rc['hit_rate']
        if saved > 0 and hit_delta > 0.01:
            any_pos = True
        rows.append({'cap_frac': rc['cap_frac'], 'C': rc['C'],
                     'recompute_raw': rc['tot_recompute_tok'], 'recompute_canon': cc['tot_recompute_tok'],
                     'recompute_saved_tok': saved, 'recompute_saved_frac': saved_frac,
                     'hit_rate_raw': rc['hit_rate'], 'hit_rate_canon': cc['hit_rate'],
                     'hit_rate_delta': hit_delta})
    return {'curve': rows, 'PASS_policy_gap': bool(any_pos),
            'note': 'WITH vs WITHOUT canonicalizer at fixed capacity; recompute_saved = the decisive policy GAP. '
                    'UPPER BOUND (FIX-2): assumes masked-prefix reuse is output-equivalent.'}

# ================= MAIN =================
def main():
    pp("=" * 78)
    pp("EXP-0059: Cross-Session KV-Sharing Ceiling / Volatile-Token Normalization Budget")
    pp(f"CLAIM-0024 PROJ-0013 | LOCKED-TS {LOCKED_TS} | prereg commit {PREREG_COMMIT}")
    pp("=" * 78)
    pp("Loading gpt2 tokenizer (Rust fast)...")
    tok = AutoTokenizer.from_pretrained('gpt2', use_fast=True)
    assert tok.is_fast

    pp("Reconstructing heads...")
    fams = {'claude_code': cc_heads(), 'codex': codex_heads()}
    for k, v in fams.items():
        pp(f"  {k}: {len(v)} sessions")

    results = {'experiment': 'EXP-0059', 'claim': 'CLAIM-0024', 'project': 'PROJ-0013', 'level': 0,
               'prompt_version': 'v001', 'locked_ts': LOCKED_TS, 'prereg_commit': PREREG_COMMIT,
               'block': BLOCK, 'seed': SEED, 'tokenizer': 'gpt2',
               'taxonomy': ALL_CLASSES, 'inert_classes': sorted(INERT_CLASSES),
               'semantic_classes': sorted(SEMANTIC_CLASSES),
               'family_sizes': {k: len(v) for k, v in fams.items()}, 'corpora': {}}

    for corpus, heads in fams.items():
        if len(heads) < 3:
            pp(f"  [skip {corpus}: <3 sessions]")
            results['corpora'][corpus] = {'status': 'skipped_too_few', 'n': len(heads)}
            continue
        r = analyze_corpus(heads, tok, corpus, BLOCK)
        tk = r.pop('_tk')
        a2 = re_a2(heads, tk, BLOCK)
        r['RE_A2'] = a2
        # strip internals before serialize, keep per-session csv
        per_session = r.pop('_per_session'); r.pop('_raw_ids'); r.pop('_R'); r.pop('_heads')
        results['corpora'][corpus] = r
        # disposition
        a0 = r['RE_A0']; a1 = r['RE_A1']
        if a0['CLEAN_KILL_no_ceiling']:
            disp = 'CLEAN-NEGATIVE (RE-A0): realized ~ canonicalized-max; volatile tokens NOT the bottleneck'
        elif a1['FAIL_diffuse']:
            disp = 'CLEAN-NEGATIVE (RE-A1): gap real but diffuse across classes; no cheap normalization lever'
        elif a2['PASS_policy_gap']:
            disp = 'POSITIVE (UPPER BOUND): concentrated volatile-token normalization budget + capacity-sim gap'
        else:
            disp = 'WEAK/NEGATIVE: concentration ok but no capacity-sim policy gap'
        r['DISPOSITION'] = disp
        # console
        pp(f"  [{corpus}] RE-A0 realized_frac={a0['realized_frac']:.3f} (raw={a0['mean_realized_raw']:.0f} "
           f"canon={a0['mean_canon_max']:.0f}) -> {'PASS-gap' if a0['PASS_gap_exists'] else 'CLEAN-KILL'}")
        pp(f"  [{corpus}] RE-A1 top3={a1['top3_classes']} share={a1['top3_share']:.3f} gini={a1['gini_across_classes']:.3f} "
           f"-> {'PASS-concentrated' if a1['PASS_concentrated'] else 'FAIL-diffuse'}")
        pp(f"  [{corpus}] RE-A3 top3_CI95={[round(x,3) for x in r['RE_A3']['top3_share_CI95']]} "
           f"HHI_sessions={r['RE_A3']['HHI_unlocked_mass_across_sessions']:.3f} flag={r['RE_A3']['HHI_flag_domination']}")
        pp(f"  [{corpus}] collision alias_rate_overall={r['collision']['alias_rate_overall']:.3f} "
           f"semantic={r['collision']['alias_rate_semantic_classes']:.3f}")
        mid = a2['curve'][len(a2['curve']) // 2]
        pp(f"  [{corpus}] RE-A2 @cap={mid['cap_frac']} saved={mid['recompute_saved_tok']} tok "
           f"({mid['recompute_saved_frac']:.3f}) hit_delta={mid['hit_rate_delta']:.3f} PASS={a2['PASS_policy_gap']}")
        pp(f"  [{corpus}] DISPOSITION: {disp}")
        # per-session csv
        csvp = os.path.join(RESULTS_DIR, f"per_session_{corpus}.csv")
        with open(csvp, 'w') as f:
            f.write("file,len,realized_raw,canon_max,gap," + ",".join(ALL_CLASSES) + "\n")
            for rr in per_session:
                f.write(f"{rr['file']},{rr['len']},{rr['realized_raw']},{rr['canon_max']},{rr['gap']},"
                        + ",".join(str(rr['unlocked'][c]) for c in ALL_CLASSES) + "\n")

    # cross-instrument discordance
    cc = results['corpora'].get('claude_code', {})
    cx = results['corpora'].get('codex', {})
    def disp_of(x): return x.get('DISPOSITION', x.get('status', 'n/a'))
    results['CROSS_INSTRUMENT'] = {
        'cc_disposition': disp_of(cc), 'codex_disposition': disp_of(cx),
        'cc_realized_frac': cc.get('RE_A0', {}).get('realized_frac'),
        'codex_realized_frac': cx.get('RE_A0', {}).get('realized_frac'),
        'cc_top3_share': cc.get('RE_A1', {}).get('top3_share'),
        'codex_top3_share': cx.get('RE_A1', {}).get('top3_share'),
        'concordant': bool(isinstance(cc.get('DISPOSITION'), str) and isinstance(cx.get('DISPOSITION'), str)
                           and cc.get('DISPOSITION', 'a')[:8] == cx.get('DISPOSITION', 'b')[:8])}

    with open(os.path.join(RESULTS_DIR, 'summary.json'), 'w') as f:
        json.dump(results, f, indent=2, default=str)
    pp(f"\nWROTE {RESULTS_DIR}/summary.json")
    pp(f"CROSS-INSTRUMENT concordant={results['CROSS_INSTRUMENT']['concordant']}")
    return results

if __name__ == '__main__':
    main()
