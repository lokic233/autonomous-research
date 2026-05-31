#!/usr/bin/env python3
"""EXP-0038 (L2) — strengthening CLAIM-0012 (failure burstiness, PURELY DESCRIPTIVE).
CPU/stdlib-only. Extends EXP-0037 (burst_probe.py / burst_codex.py) + EXP-0031 gemini parser.

Deliverables:
 1. GEMINI 3rd harness (same per-session runs test + Stouffer aggregation).
 2. PER-SESSION PERMUTATION NULL (shuffle failure-indicator sequence within session, N>=1000,
    compare observed #runs to permuted distribution). Non-parametric, robust to small-n + heuristic labels.
 3. BURSTINESS COEFFICIENT B = (sigma-mu)/(sigma+mu) on inter-failure gaps PER HARNESS w/ bootstrap 95% CIs
    (resample sessions). B>0 => bursty. Also Fano/dispersion index (window=5).
 4. M4 web_disabled ablation re-check under permutation null + all 3 harnesses (CC has web_disabled;
    Codex web_disabled via output text; Gemini has no web tool -> trivially unaffected).

KEEP DESCRIPTIVE: arrival-process only. No error-class conditioning, no recovery prediction.
"""
import json, glob, os, math, random, statistics, re, csv
from collections import defaultdict

random.seed(20260531)
NPERM = 2000      # per-session permutations
NBOOT = 2000      # bootstrap resamples of sessions
MIN_TRIALS = 8    # min tool-results for a usable session (matches EXP-0037)

# ----------------------------------------------------------------------------
# RUNS TEST (Wald-Wolfowitz) analytic Z (for Stouffer); negative => clustered
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
# PER-SESSION PERMUTATION NULL: shuffle the 0/1 failure-indicator sequence,
# recompute #runs. Fewer-runs-than-null => clustered. one-sided exact p =
# P(R_perm <= R_obs). We also yield a per-session permutation Z (standardized
# vs the permuted null moments) to allow a permutation-based Stouffer combine.
# ----------------------------------------------------------------------------
def perm_runs_test(seq, nperm=NPERM):
    n1 = sum(seq); n0 = len(seq) - n1
    if n1 == 0 or n0 == 0: return None
    R_obs = count_runs(seq)
    perm_runs = []
    base = list(seq)
    for _ in range(nperm):
        random.shuffle(base)
        perm_runs.append(count_runs(base))
    le = sum(1 for r in perm_runs if r <= R_obs)   # clustered = fewer runs
    p_clustered = (le + 1) / (nperm + 1)           # add-one (exact, conservative)
    mu = statistics.mean(perm_runs)
    sd = statistics.pstdev(perm_runs)
    z_perm = (R_obs - mu) / sd if sd > 0 else 0.0  # negative => clustered
    return {'R_obs': R_obs, 'p_clustered': p_clustered, 'z_perm': z_perm,
            'mu_perm': mu, 'sd_perm': sd, 'n': len(seq), 'n1': n1}

# ----------------------------------------------------------------------------
# BURSTINESS COEFFICIENT (Goh-Barabasi) on inter-FAILURE gaps within a session.
# gap = #trials between consecutive failures (index difference). Need >=2 failures
# per session to form >=1 gap; combine gaps across sessions for a harness-level B.
# B = (sigma - mu)/(sigma + mu) in [-1,1]; B>0 bursty, B=0 Poisson, B<0 regular.
# ----------------------------------------------------------------------------
def interfailure_gaps(seq):
    idx = [i for i, v in enumerate(seq) if v == 1]
    return [idx[k+1] - idx[k] for k in range(len(idx)-1)]

def burstiness_B(gaps):
    if len(gaps) < 2: return None
    mu = statistics.mean(gaps)
    sd = statistics.pstdev(gaps)
    if mu + sd == 0: return None
    return (sd - mu) / (sd + mu)

def burstiness_B_corrected(gaps):
    """Kim & Jo (2016) finite-size-corrected burstiness. Raw B is biased toward -1
    for short sequences; this corrects for n. n = #inter-event intervals."""
    if len(gaps) < 2: return None
    mu = statistics.mean(gaps); sd = statistics.pstdev(gaps)
    if mu == 0: return None
    r = sd/mu; n = len(gaps)
    num = math.sqrt(n+1)*r - math.sqrt(n-1)
    den = (math.sqrt(n+1)-2)*r + math.sqrt(n-1)
    if den == 0: return None
    return num/den

# Fano / dispersion index on fixed window (window=5), pooled per harness
def dispersion_index(seqs, w=5):
    cnts = []
    for seq in seqs:
        for i in range(0, len(seq)-w+1, w):
            cnts.append(sum(seq[i:i+w]))
    if len(cnts) < 2: return None
    m = statistics.mean(cnts)
    if m == 0: return None
    var = statistics.variance(cnts)
    return var / m  # >1 overdispersed

# ----------------------------------------------------------------------------
# HARNESS PARSERS -> dict[session_key] = list of (is_err:int, label:str)
#   label used only for M4 web_disabled reclassification (NOT for conditioning).
# ----------------------------------------------------------------------------
def parse_cc():
    fs = glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl'))
    out = {}
    for f in fs:
        seq = []
        for line in open(f):
            line = line.strip()
            if not line: continue
            try: d = json.loads(line)
            except: continue
            msg = d.get('message')
            if isinstance(msg, dict) and isinstance(msg.get('content'), list):
                for b in msg['content']:
                    if not isinstance(b, dict): continue
                    if b.get('type') == 'tool_result':
                        is_err = 1 if b.get('is_error') else 0
                        txt = ''
                        c = b.get('content')
                        if isinstance(c, str): txt = c
                        elif isinstance(c, list):
                            txt = ' '.join(str(x.get('text','')) for x in c if isinstance(x, dict))
                        label = classify_web(txt) if is_err else 'ok'
                        seq.append((is_err, label))
        if len(seq) >= MIN_TRIALS:
            out[f] = seq
    return out

def classify_web(txt):
    t = txt.lower()
    if ('web' in t and ('disabl' in t or 'not enabled' in t or 'blocked' in t)) \
       or 'web search is not' in t or 'websearch' in t and 'disabl' in t:
        return 'web_disabled'
    return 'other_fail'

def parse_codex():
    fs = glob.glob(os.path.expanduser('~/.codex/sessions/**/*.jsonl'), recursive=True)
    out = {}
    for f in fs:
        seen = set(); seq = []
        for line in open(f):
            line = line.strip()
            if not line: continue
            try: d = json.loads(line)
            except: continue
            p = d.get('payload') or d
            if p.get('type') == 'function_call_output':
                cid = p.get('call_id')
                if cid in seen: continue   # dedup (EXP-0033 double-log neutralizer)
                seen.add(cid)
                out_s = str(p.get('output', ''))
                m = re.search(r'exited with code (\d+)', out_s)
                err = 0
                if m and m.group(1) != '0': err = 1
                elif 'error' in out_s[:120].lower() and 'code 0' not in out_s: err = 1
                label = classify_web(out_s) if err else 'ok'
                seq.append((err, label))
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
                # Gemini has no web tool in this corpus; label web_disabled never fires.
                seq.append((is_err, 'web_disabled' if False else ('ok' if not is_err else 'other_fail')))
        if len(seq) >= MIN_TRIALS:
            out[f] = seq
    return out

# ----------------------------------------------------------------------------
# ANALYSIS over a parsed harness (dict[key]=list[(err,label)])
# reclassify_web=True => treat web_disabled failures as non-failures (M4)
# ----------------------------------------------------------------------------
def to_seq(events, reclassify_web=False):
    if reclassify_web:
        return [0 if (e and lab == 'web_disabled') else e for (e, lab) in events]
    return [e for (e, lab) in events]

def analyze(name, parsed, reclassify_web=False):
    seqs = []
    analytic_zs = []
    perm_zs = []
    perm_ps = []
    sess_rows = []
    tot = errs = 0
    n_web = 0
    for key, events in parsed.items():
        n_web += sum(1 for (e, lab) in events if e and lab == 'web_disabled')
        seq = to_seq(events, reclassify_web)
        tot += len(seq); errs += sum(seq)
        if 0 < sum(seq) < len(seq):
            seqs.append(seq)
            az = runs_z(seq)
            pr = perm_runs_test(seq)
            if az is not None and pr is not None:
                analytic_zs.append(az)
                perm_zs.append(pr['z_perm'])
                perm_ps.append(pr['p_clustered'])
                sess_rows.append({'session': os.path.basename(key), 'n': len(seq),
                                  'fails': sum(seq), 'analytic_z': round(az, 3),
                                  'perm_z': round(pr['z_perm'], 3),
                                  'p_clustered': round(pr['p_clustered'], 4)})
    usable = len(analytic_zs)
    res = {'harness': name, 'reclassify_web': reclassify_web,
           'n_sessions': usable, 'total_trials': tot, 'total_fails': errs,
           'fail_rate': errs/tot if tot else 0, 'n_web_disabled': n_web}
    if usable == 0:
        res.update({'stouffer_analytic': None, 'stouffer_perm': None,
                    'frac_z_neg': None, 'B': None, 'B_ci': None,
                    'dispersion_index': None, 'frac_perm_sig': None,
                    'fisher_perm_chi2_p': None})
        return res, sess_rows, seqs

    res['stouffer_analytic'] = round(sum(analytic_zs)/math.sqrt(usable), 3)
    res['stouffer_perm'] = round(sum(perm_zs)/math.sqrt(usable), 3)
    res['frac_z_neg'] = round(sum(1 for z in analytic_zs if z < 0)/usable, 3)
    res['frac_perm_z_neg'] = round(sum(1 for z in perm_zs if z < 0)/usable, 3)
    # fraction of sessions whose permutation p_clustered < 0.05
    res['frac_perm_sig'] = round(sum(1 for p in perm_ps if p < 0.05)/usable, 3)
    res['median_analytic_z'] = round(statistics.median(analytic_zs), 3)
    res['median_perm_z'] = round(statistics.median(perm_zs), 3)
    # Fisher combine of per-session permutation p-values (one-sided clustered)
    chi2 = -2 * sum(math.log(max(p, 1e-12)) for p in perm_ps)
    res['fisher_chi2'] = round(chi2, 2)
    res['fisher_df'] = 2*usable
    # survival p via normal approx to chi2 (Wilson-Hilferty) for reporting
    df = 2*usable
    z_wh = ((chi2/df)**(1/3) - (1 - 2/(9*df))) / math.sqrt(2/(9*df))
    res['fisher_z'] = round(z_wh, 3)   # large positive => strong combined clustering

    # ---- burstiness coefficient B on pooled inter-failure gaps + bootstrap over sessions ----
    def B_from_seqlist(slist):
        gaps = []
        for s in slist:
            gaps.extend(interfailure_gaps(s))
        return burstiness_B(gaps)
    B_point = B_from_seqlist(seqs)
    def Bc_from_seqlist(slist):
        gaps = []
        for s in slist:
            gaps.extend(interfailure_gaps(s))
        return burstiness_B_corrected(gaps)
    Bc_point = Bc_from_seqlist(seqs)
    boot = []
    bootc = []
    nS = len(seqs)
    for _ in range(NBOOT):
        samp = [seqs[random.randrange(nS)] for _ in range(nS)]
        b = B_from_seqlist(samp)
        bc = Bc_from_seqlist(samp)
        if b is not None: boot.append(b)
        if bc is not None: bootc.append(bc)
    if boot:
        boot.sort()
        lo = boot[int(0.025*len(boot))]
        hi = boot[int(0.975*len(boot))-1] if int(0.975*len(boot)) > 0 else boot[-1]
        res['B'] = round(B_point, 4) if B_point is not None else None
        res['B_ci'] = [round(lo, 4), round(hi, 4)]
    else:
        res['B'] = round(B_point, 4) if B_point is not None else None
        res['B_ci'] = None
    if bootc:
        bootc.sort()
        loc = bootc[int(0.025*len(bootc))]
        hic = bootc[int(0.975*len(bootc))-1] if int(0.975*len(bootc)) > 0 else bootc[-1]
        res['B_corrected'] = round(Bc_point, 4) if Bc_point is not None else None
        res['Bc_ci'] = [round(loc, 4), round(hic, 4)]
    else:
        res['B_corrected'] = round(Bc_point, 4) if Bc_point is not None else None
        res['Bc_ci'] = None
    res['n_interfailure_gaps'] = sum(len(interfailure_gaps(s)) for s in seqs)
    di = dispersion_index(seqs)
    res['dispersion_index'] = round(di, 3) if di is not None else None
    return res, sess_rows, seqs

# ----------------------------------------------------------------------------
def main():
    print("Parsing corpora ...")
    cc = parse_cc()
    cx = parse_codex()
    gm = parse_gemini()
    print(f"  CC sessions>= {MIN_TRIALS}: {len(cc)}")
    print(f"  Codex sessions>= {MIN_TRIALS}: {len(cx)}")
    print(f"  Gemini sessions>= {MIN_TRIALS}: {len(gm)}")
    print()

    all_results = []
    all_sess_rows = []
    for name, parsed in [('claude_code', cc), ('codex', cx), ('gemini', gm)]:
        res, rows, _ = analyze(name, parsed, reclassify_web=False)
        all_results.append(res)
        for r in rows:
            r['harness'] = name; r['variant'] = 'base'
        all_sess_rows.extend(rows)
        print(f"=== {name} (base) ===")
        for k in ('n_sessions','total_trials','total_fails','fail_rate','n_web_disabled',
                  'stouffer_analytic','stouffer_perm','median_analytic_z','median_perm_z',
                  'frac_z_neg','frac_perm_z_neg','frac_perm_sig','fisher_chi2','fisher_z',
                  'B','B_ci','B_corrected','Bc_ci','n_interfailure_gaps','dispersion_index'):
            print(f"   {k:20}: {res.get(k)}")
        print()

    # ---- M4 web_disabled ablation: reclassify web_disabled as non-failure, all 3 harnesses ----
    print("="*70)
    print("M4 ABLATION: reclassify web_disabled failures as NON-failures")
    for name, parsed in [('claude_code', cc), ('codex', cx), ('gemini', gm)]:
        res, rows, _ = analyze(name, parsed, reclassify_web=True)
        res['harness'] = name + '_M4'
        all_results.append(res)
        print(f"=== {name} (M4 web_disabled->ok) ===")
        for k in ('n_sessions','n_web_disabled','stouffer_analytic','stouffer_perm',
                  'frac_perm_sig','B','B_ci','B_corrected','Bc_ci','dispersion_index'):
            print(f"   {k:20}: {res.get(k)}")
        print()

    # ---- write CSVs ----
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir = os.path.join(base, 'results')
    os.makedirs(rdir, exist_ok=True)
    with open(os.path.join(rdir, 'harness_summary.csv'), 'w', newline='') as fh:
        cols = ['harness','reclassify_web','n_sessions','total_trials','total_fails','fail_rate',
                'n_web_disabled','stouffer_analytic','stouffer_perm','median_analytic_z',
                'median_perm_z','frac_z_neg','frac_perm_z_neg','frac_perm_sig','fisher_chi2',
                'fisher_z','B','B_ci','B_corrected','Bc_ci','n_interfailure_gaps','dispersion_index']
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in all_results: w.writerow(r)
    with open(os.path.join(rdir, 'per_session.csv'), 'w', newline='') as fh:
        cols = ['harness','variant','session','n','fails','analytic_z','perm_z','p_clustered']
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in all_sess_rows: w.writerow(r)
    print(f"CSVs -> {rdir}/harness_summary.csv , per_session.csv")

if __name__ == '__main__':
    main()
