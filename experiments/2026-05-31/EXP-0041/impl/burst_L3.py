#!/usr/bin/env python3
"""EXP-0041 (L3) — the COMMITTEE'S 2 KILLER ABLATIONS for CLAIM-0012 (VERDICT-0045, 6/6 YELLOW).
CPU/stdlib-only. Reuses EXP-0037/0038 (burst_L2.py) parse + runs-test + permutation + dispersion
machinery, EXTENDED to carry tool_name + input-args per call (needed to discriminate true
temporal-memory burstiness from trivial alternatives).

THE TASK (purely DESCRIPTIVE; arrival-process only):
 (1) TOOL-STRATIFIED PERMUTATION NULL  [load-bearing killer]
     Instead of permuting failure labels across ALL calls in a session, permute them ONLY among
     calls to the SAME tool_name within each session (block permutation). N>=2000.
     - If Z COLLAPSES toward 0 -> the over-dispersion was RATE-HETEROGENEITY (some tools fail more
       = trivial Cox mixture-Poisson) -> unpublishable as 'burstiness'.
     - If Z SURVIVES (stays significantly negative) -> genuine WITHIN-tool temporal memory -> real.
 (2) RETRY-CASCADE ABLATION
     Collapse immediate fail->retry-same-intent->fail runs to a SINGLE root event. Same-intent =
     same tool_name AND (near-)identical normalized input args in immediate succession. Recompute
     dispersion + runs test (whole-session permutation, as in L2, on the collapsed sequence).
     - If significance DIES -> clustering is deterministic CONTROL-FLOW (retry loops), not stochastic.
     - If it SURVIVES -> not just retry mechanics.
 (3) (optional) mixture-of-Poissons vs single-Poisson likelihood comparison (LRT / BIC) per harness.

KEEP DESCRIPTIVE. No error-class conditioning for the claim, no recovery prediction.
"""
import json, glob, os, math, random, statistics, re, csv, hashlib
from collections import defaultdict

random.seed(20260531)
NPERM = 2500
MIN_TRIALS = 8

# ----------------------------------------------------------------------------
# RUNS TEST (Wald-Wolfowitz) analytic Z; negative => clustered (fewer runs)
# ----------------------------------------------------------------------------
def count_runs(seq):
    R = 1
    for i in range(1, len(seq)):
        if seq[i] != seq[i-1]: R += 1
    return R

def runs_z(seq):
    n1 = sum(seq); n0 = len(seq) - n1
    if n1 == 0 or n0 == 0: return None
    R = count_runs(seq)
    n = n0 + n1
    mu = 2*n0*n1/n + 1
    var = (2*n0*n1*(2*n0*n1 - n)) / (n*n*(n-1))
    if var <= 0: return None
    return (R - mu) / math.sqrt(var)

# ----------------------------------------------------------------------------
# WHOLE-SESSION permutation null (L2 baseline): shuffle the full 0/1 sequence.
# ----------------------------------------------------------------------------
def perm_runs_whole(seq, nperm=NPERM):
    n1 = sum(seq); n0 = len(seq) - n1
    if n1 == 0 or n0 == 0: return None
    R_obs = count_runs(seq)
    base = list(seq); pr = []
    for _ in range(nperm):
        random.shuffle(base); pr.append(count_runs(base))
    mu = statistics.mean(pr); sd = statistics.pstdev(pr)
    le = sum(1 for r in pr if r <= R_obs)
    return {'z_perm': (R_obs - mu)/sd if sd > 0 else 0.0,
            'p_clustered': (le+1)/(nperm+1), 'R_obs': R_obs, 'n': len(seq), 'n1': n1}

# ----------------------------------------------------------------------------
# TOOL-STRATIFIED permutation null (THE KILLER):
#  - The failure LABELS are shuffled, but only WITHIN each tool_name block, i.e.
#    each tool keeps its own marginal failure rate fixed. Positions stay; only the
#    assignment of which same-tool calls failed is randomized.
#  - This destroys WITHIN-tool temporal memory while PRESERVING between-tool rate
#    heterogeneity. If observed clustering survives this null -> not rate-mixing.
#  - We standardize R_obs vs the stratified-permuted distribution -> z_strat.
#    z_strat << 0 => clustering beyond what tool-rate-mixing explains.
# ----------------------------------------------------------------------------
def perm_runs_tool_stratified(seq, tools, nperm=NPERM):
    n1 = sum(seq); n0 = len(seq) - n1
    if n1 == 0 or n0 == 0: return None
    R_obs = count_runs(seq)
    # group call POSITIONS by tool_name
    groups = defaultdict(list)
    for i, t in enumerate(tools):
        groups[t].append(i)
    # the per-tool failure labels (to be permuted within each group)
    grp_labels = {t: [seq[i] for i in idxs] for t, idxs in groups.items()}
    # if every tool is homogeneous (all-fail or all-ok), stratified perm is degenerate:
    # no within-tool variation to shuffle -> the test cannot run meaningfully.
    shufflable = any(0 < sum(lab) < len(lab) for lab in grp_labels.values())
    pr = []
    work = list(seq)
    for _ in range(nperm):
        for t, idxs in groups.items():
            lab = grp_labels[t][:]
            random.shuffle(lab)
            for j, i in enumerate(idxs):
                work[i] = lab[j]
        pr.append(count_runs(work))
    mu = statistics.mean(pr); sd = statistics.pstdev(pr)
    le = sum(1 for r in pr if r <= R_obs)
    return {'z_strat': (R_obs - mu)/sd if sd > 0 else 0.0,
            'p_clustered': (le+1)/(nperm+1), 'R_obs': R_obs,
            'n_tools': len(groups), 'shufflable': shufflable,
            'mu': mu, 'sd': sd}

# ----------------------------------------------------------------------------
# DISPERSION index (Fano), window=5, pooled per harness
# ----------------------------------------------------------------------------
def dispersion_index(seqs, w=5):
    cnts = []
    for seq in seqs:
        for i in range(0, len(seq)-w+1, w):
            cnts.append(sum(seq[i:i+w]))
    if len(cnts) < 2: return None
    m = statistics.mean(cnts)
    if m == 0: return None
    return statistics.variance(cnts)/m

# ----------------------------------------------------------------------------
# Inter-failure gaps + burstiness B (Goh-Barabasi)
# ----------------------------------------------------------------------------
def interfailure_gaps(seq):
    idx = [i for i, v in enumerate(seq) if v == 1]
    return [idx[k+1]-idx[k] for k in range(len(idx)-1)]

def burstiness_B(gaps):
    if len(gaps) < 2: return None
    mu = statistics.mean(gaps); sd = statistics.pstdev(gaps)
    if mu+sd == 0: return None
    return (sd-mu)/(sd+mu)

# ----------------------------------------------------------------------------
# RETRY-CASCADE COLLAPSE:
#  A "same-intent retry" = a call whose (tool_name, normalized-args-signature) equals
#  the IMMEDIATELY PRECEDING call's signature, where the preceding call FAILED.
#  We collapse a maximal run of [fail, (same-intent)*] into ONE root event whose
#  failure label = 1 if ANY member of the run failed (the root attempt is what matters;
#  the retries are deterministic control-flow, not independent arrivals).
#  Rationale (committee): CC has no call_id-analog dedup like Codex EXP-0033; this is the
#  reasonable same-intent-retry collapse for ALL harnesses.
# ----------------------------------------------------------------------------
def arg_sig(tool, args):
    """normalized signature of a call's intent. args is a dict or str."""
    if isinstance(args, dict):
        # canonical json of sorted top-level items, trimmed
        try:
            s = json.dumps(args, sort_keys=True, default=str)[:400]
        except Exception:
            s = str(args)[:400]
    else:
        s = str(args)[:400]
    return tool + '|' + hashlib.md5(s.encode('utf-8','ignore')).hexdigest()[:12]

def collapse_retries(events):
    """events = list of (is_err, tool_name, arg_signature). Returns collapsed 0/1 seq
    + collapsed tool list. A same-intent retry = same signature as the immediately
    preceding call AND the preceding call failed. Collapse maximal such runs into one
    root event (label = OR of the run; tool = root's tool)."""
    if not events:
        return [], []
    out_seq = []; out_tools = []
    i = 0
    n = len(events)
    while i < n:
        err0, tool0, sig0 = events[i]
        j = i + 1
        run_err = err0
        # extend run while next call is a same-intent retry of a FAILED attempt
        while j < n:
            prev_err = events[j-1][0]
            same_intent = (events[j][2] == sig0)
            if prev_err == 1 and same_intent:
                run_err = run_err or events[j][0]
                j += 1
            else:
                break
        out_seq.append(1 if run_err else 0)
        out_tools.append(tool0)
        i = j
    return out_seq, out_tools

# ----------------------------------------------------------------------------
# Mixture-of-Poissons vs single-Poisson (optional strengthening). Window counts.
#  single: lambda = mean count. mixture: 2-comp EM. Compare via BIC.
#  A better mixture fit => rate-heterogeneity present (does NOT by itself refute
#  temporal memory, but documents the Cox-alternative the committee flagged).
# ----------------------------------------------------------------------------
def poisson_logpmf(k, lam):
    if lam <= 0: return -1e18 if k > 0 else 0.0
    return k*math.log(lam) - lam - math.lgamma(k+1)

def fit_single_poisson(counts):
    lam = sum(counts)/len(counts) if counts else 0.0
    ll = sum(poisson_logpmf(k, lam) for k in counts)
    return ll, 1

def fit_mixture_poisson(counts, iters=200):
    if len(counts) < 4: return None
    m = sum(counts)/len(counts)
    l1, l2 = max(m*0.5, 0.01), m*1.5 + 0.5
    w = 0.5
    for _ in range(iters):
        r = []
        for k in counts:
            a = w*math.exp(poisson_logpmf(k, l1))
            b = (1-w)*math.exp(poisson_logpmf(k, l2))
            tot = a+b
            r.append(a/tot if tot > 0 else 0.5)
        sr = sum(r); 
        if sr <= 0 or sr >= len(counts): break
        w = sr/len(counts)
        l1 = sum(ri*k for ri, k in zip(r, counts))/sr
        l2 = sum((1-ri)*k for ri, k in zip(r, counts))/(len(counts)-sr)
        if l1 <= 0: l1 = 0.01
        if l2 <= 0: l2 = 0.01
    ll = 0.0
    for k in counts:
        a = w*math.exp(poisson_logpmf(k, l1))
        b = (1-w)*math.exp(poisson_logpmf(k, l2))
        ll += math.log(a+b) if (a+b) > 0 else -1e18
    return ll, 3, (w, l1, l2)

def window_counts(seqs, w=5):
    c = []
    for seq in seqs:
        for i in range(0, len(seq)-w+1, w):
            c.append(sum(seq[i:i+w]))
    return c

# ----------------------------------------------------------------------------
# HARNESS PARSERS -> dict[session_key] = list of (is_err, tool_name, arg_sig)
# ----------------------------------------------------------------------------
def classify_web(txt):
    t = txt.lower()
    if ('web' in t and ('disabl' in t or 'not enabled' in t or 'blocked' in t)) \
       or 'web search is not' in t or ('websearch' in t and 'disabl' in t):
        return 'web_disabled'
    return 'other_fail'

def parse_cc():
    fs = glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl'))
    out = {}
    for f in fs:
        # first pass: map tool_use_id -> (tool_name, arg_sig)
        idmap = {}
        for line in open(f):
            line = line.strip()
            if not line: continue
            try: d = json.loads(line)
            except: continue
            msg = d.get('message')
            if isinstance(msg, dict) and isinstance(msg.get('content'), list):
                for b in msg['content']:
                    if isinstance(b, dict) and b.get('type') == 'tool_use':
                        idmap[b.get('id')] = (b.get('name','?'), b.get('input', {}))
        # second pass: results in order
        seq = []
        for line in open(f):
            line = line.strip()
            if not line: continue
            try: d = json.loads(line)
            except: continue
            msg = d.get('message')
            if isinstance(msg, dict) and isinstance(msg.get('content'), list):
                for b in msg['content']:
                    if isinstance(b, dict) and b.get('type') == 'tool_result':
                        is_err = 1 if b.get('is_error') else 0
                        tid = b.get('tool_use_id')
                        tname, targs = idmap.get(tid, ('unknown', {}))
                        sig = arg_sig(tname, targs)
                        seq.append((is_err, tname, sig))
        if len(seq) >= MIN_TRIALS:
            out[f] = seq
    return out

def parse_codex():
    fs = glob.glob(os.path.expanduser('~/.codex/sessions/**/*.jsonl'), recursive=True)
    out = {}
    for f in fs:
        # map call_id -> (name, arguments)
        callmap = {}
        for line in open(f):
            line = line.strip()
            if not line: continue
            try: d = json.loads(line)
            except: continue
            p = d.get('payload') or d
            if p.get('type') == 'function_call':
                callmap[p.get('call_id')] = (p.get('name','?'), p.get('arguments', ''))
        seen = set(); seq = []
        for line in open(f):
            line = line.strip()
            if not line: continue
            try: d = json.loads(line)
            except: continue
            p = d.get('payload') or d
            if p.get('type') == 'function_call_output':
                cid = p.get('call_id')
                if cid in seen: continue        # dedup (EXP-0033 double-log neutralizer)
                seen.add(cid)
                out_s = str(p.get('output', ''))
                m = re.search(r'exited with code (\d+)', out_s)
                err = 0
                if m and m.group(1) != '0': err = 1
                elif 'error' in out_s[:120].lower() and 'code 0' not in out_s: err = 1
                tname, targs = callmap.get(cid, ('unknown', ''))
                # for codex exec_command, refine intent by first cmd token (sub-tool)
                refined = tname
                if tname == 'exec_command':
                    try:
                        a = json.loads(targs) if isinstance(targs, str) else targs
                        cmd = (a or {}).get('cmd', '')
                        verb = str(cmd).strip().split()[0] if cmd else 'sh'
                        refined = 'exec:' + os.path.basename(verb)[:24]
                    except Exception:
                        refined = 'exec:sh'
                sig = arg_sig(refined, targs)
                seq.append((err, refined, sig))
        if len(seq) >= MIN_TRIALS:
            out[f] = seq
    return out

def parse_gemini():
    fs = glob.glob(os.path.expanduser('~/.gemini/tmp/*/chats/session-*.json'))
    out = {}
    for f in fs:
        try: d = json.load(open(f))
        except: continue
        seq = []
        for m in d.get('messages', []):
            for tc in (m.get('toolCalls') or []):
                st = tc.get('status')
                if st not in ('success', 'error'): continue
                is_err = 1 if st == 'error' else 0
                tname = tc.get('name', '?')
                sig = arg_sig(tname, tc.get('args', {}))
                seq.append((is_err, tname, sig))
        if len(seq) >= MIN_TRIALS:
            out[f] = seq
    return out

# ----------------------------------------------------------------------------
# Per-harness analysis: base (L2 whole-session) + tool-stratified + retry-collapsed
# ----------------------------------------------------------------------------
def analyze(name, parsed):
    base_seqs = []
    z_whole = []; z_strat = []
    p_whole = []; p_strat = []
    collapsed_seqs = []
    z_whole_coll = []; p_whole_coll = []
    n_tools_total = set()
    sess_rows = []
    tot = errs = 0
    n_collapsed_removed = 0
    strat_shufflable_sessions = 0
    for key, events in parsed.items():
        seq = [e[0] for e in events]
        tools = [e[1] for e in events]
        tot += len(seq); errs += sum(seq)
        for t in tools: n_tools_total.add(t)
        if not (0 < sum(seq) < len(seq)):
            continue
        base_seqs.append(seq)
        # BASE whole-session
        rw = perm_runs_whole(seq)
        az = runs_z(seq)
        # TOOL-STRATIFIED
        rs = perm_runs_tool_stratified(seq, tools)
        if rs and rs['shufflable']:
            strat_shufflable_sessions += 1
        # RETRY-COLLAPSED
        cseq, ctools = collapse_retries(events)
        n_collapsed_removed += (len(seq) - len(cseq))
        rc = None
        if 0 < sum(cseq) < len(cseq):
            rc = perm_runs_whole(cseq)
            collapsed_seqs.append(cseq)
        if rw:
            z_whole.append(rw['z_perm']); p_whole.append(rw['p_clustered'])
        if rs:
            z_strat.append(rs['z_strat']); p_strat.append(rs['p_clustered'])
        if rc:
            z_whole_coll.append(rc['z_perm']); p_whole_coll.append(rc['p_clustered'])
        sess_rows.append({
            'harness': name, 'session': os.path.basename(key), 'n': len(seq), 'fails': sum(seq),
            'analytic_z': round(az, 3) if az is not None else None,
            'z_whole_perm': round(rw['z_perm'], 3) if rw else None,
            'z_tool_strat': round(rs['z_strat'], 3) if rs else None,
            'strat_shufflable': rs['shufflable'] if rs else None,
            'n_collapsed': len(cseq), 'fails_collapsed': sum(cseq),
            'z_whole_coll': round(rc['z_perm'], 3) if rc else None,
        })
    def stouffer(zs):
        return round(sum(zs)/math.sqrt(len(zs)), 3) if zs else None
    res = {
        'harness': name,
        'n_sessions': len(base_seqs),
        'total_trials': tot, 'total_fails': errs,
        'fail_rate': round(errs/tot, 4) if tot else 0,
        'n_distinct_tools': len(n_tools_total),
        # BASE (replicates L2)
        'stouffer_whole_perm': stouffer(z_whole),
        'median_z_whole': round(statistics.median(z_whole), 3) if z_whole else None,
        'frac_whole_sig': round(sum(1 for p in p_whole if p < 0.05)/len(p_whole), 3) if p_whole else None,
        # KILLER 1: tool-stratified
        'stouffer_tool_strat': stouffer(z_strat),
        'median_z_strat': round(statistics.median(z_strat), 3) if z_strat else None,
        'frac_strat_sig': round(sum(1 for p in p_strat if p < 0.05)/len(p_strat), 3) if p_strat else None,
        'n_strat_shufflable_sessions': strat_shufflable_sessions,
        # KILLER 2: retry-collapsed
        'n_sessions_collapsed': len(collapsed_seqs),
        'n_calls_removed_by_collapse': n_collapsed_removed,
        'pct_calls_removed': round(100*n_collapsed_removed/tot, 2) if tot else None,
        'stouffer_whole_coll': stouffer(z_whole_coll),
        'median_z_coll': round(statistics.median(z_whole_coll), 3) if z_whole_coll else None,
        'frac_coll_sig': round(sum(1 for p in p_whole_coll if p < 0.05)/len(p_whole_coll), 3) if p_whole_coll else None,
        # dispersion under each
        'dispersion_base': round(dispersion_index(base_seqs), 3) if dispersion_index(base_seqs) else None,
        'dispersion_collapsed': round(dispersion_index(collapsed_seqs), 3) if collapsed_seqs and dispersion_index(collapsed_seqs) else None,
    }
    # burstiness B base vs collapsed
    gb = []; 
    for s in base_seqs: gb.extend(interfailure_gaps(s))
    res['B_base'] = round(burstiness_B(gb), 4) if burstiness_B(gb) is not None else None
    gc = []
    for s in collapsed_seqs: gc.extend(interfailure_gaps(s))
    res['B_collapsed'] = round(burstiness_B(gc), 4) if burstiness_B(gc) is not None else None
    # mixture vs single Poisson (window counts) base
    wc = window_counts(base_seqs)
    if len(wc) >= 8:
        ll1, k1 = fit_single_poisson(wc)
        mix = fit_mixture_poisson(wc)
        if mix:
            ll2, k2, params = mix
            bic1 = -2*ll1 + k1*math.log(len(wc))
            bic2 = -2*ll2 + k2*math.log(len(wc))
            res['poisson_single_ll'] = round(ll1, 2)
            res['poisson_mix_ll'] = round(ll2, 2)
            res['poisson_LR_2dll'] = round(2*(ll2-ll1), 3)
            res['poisson_BIC_single'] = round(bic1, 2)
            res['poisson_BIC_mix'] = round(bic2, 2)
            res['mixture_preferred'] = bic2 < bic1
            res['mix_params_w_l1_l2'] = [round(x, 3) for x in params]
    return res, sess_rows

def main():
    print("Parsing corpora (carrying tool_name + arg signatures)...")
    cc = parse_cc(); cx = parse_codex(); gm = parse_gemini()
    print(f"  CC sessions>= {MIN_TRIALS}: {len(cc)}")
    print(f"  Codex sessions>= {MIN_TRIALS}: {len(cx)}")
    print(f"  Gemini sessions>= {MIN_TRIALS}: {len(gm)}\n")

    results = []; all_rows = []
    for name, parsed in [('claude_code', cc), ('codex', cx), ('gemini', gm)]:
        res, rows = analyze(name, parsed)
        results.append(res); all_rows.extend(rows)
        print(f"=== {name} ===")
        for k in ('n_sessions','total_trials','total_fails','fail_rate','n_distinct_tools',
                  'stouffer_whole_perm','median_z_whole','frac_whole_sig',
                  'stouffer_tool_strat','median_z_strat','frac_strat_sig','n_strat_shufflable_sessions',
                  'n_sessions_collapsed','n_calls_removed_by_collapse','pct_calls_removed',
                  'stouffer_whole_coll','median_z_coll','frac_coll_sig',
                  'dispersion_base','dispersion_collapsed','B_base','B_collapsed',
                  'poisson_LR_2dll','poisson_BIC_single','poisson_BIC_mix','mixture_preferred','mix_params_w_l1_l2'):
            if k in res: print(f"   {k:28}: {res.get(k)}")
        print()

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir = os.path.join(base, 'results'); os.makedirs(rdir, exist_ok=True)
    with open(os.path.join(rdir, 'harness_summary_L3.csv'), 'w', newline='') as fh:
        cols = ['harness','n_sessions','total_trials','total_fails','fail_rate','n_distinct_tools',
                'stouffer_whole_perm','median_z_whole','frac_whole_sig',
                'stouffer_tool_strat','median_z_strat','frac_strat_sig','n_strat_shufflable_sessions',
                'n_sessions_collapsed','n_calls_removed_by_collapse','pct_calls_removed',
                'stouffer_whole_coll','median_z_coll','frac_coll_sig',
                'dispersion_base','dispersion_collapsed','B_base','B_collapsed',
                'poisson_single_ll','poisson_mix_ll','poisson_LR_2dll','poisson_BIC_single',
                'poisson_BIC_mix','mixture_preferred','mix_params_w_l1_l2']
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore'); w.writeheader()
        for r in results: w.writerow(r)
    with open(os.path.join(rdir, 'per_session_L3.csv'), 'w', newline='') as fh:
        cols = ['harness','session','n','fails','analytic_z','z_whole_perm','z_tool_strat',
                'strat_shufflable','n_collapsed','fails_collapsed','z_whole_coll']
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore'); w.writeheader()
        for r in all_rows: w.writerow(r)
    print(f"CSVs -> {rdir}/harness_summary_L3.csv , per_session_L3.csv")

if __name__ == '__main__':
    main()
