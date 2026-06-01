#!/usr/bin/env python3
"""EXP-0044 WALL-CLOCK SENSITIVITY (researcher-0012-hold4-r3, 2026-06-01) — DEFENSIVE HARDENING ONLY.

PURPOSE (does NOT change VERDICT-0049): recompute the Codex H2 Cox-vs-Hawkes deltaBIC using REAL
inter-failure WALL-CLOCK seconds (from per-event ISO-8601 ms timestamps in ~/.codex/sessions/*.jsonl)
instead of the call-INDEX clock used in EXP-0042 robust_L4. This addresses systems_reviewer's
EXTERNAL-VALIDITY caveat (is the self-excitation an artifact of the call-index discretization?).
It is NOT the product_realist altitude fix and does NOT by itself earn a 6th GREEN.

REUSE: the EXP-0042 robust_L4 Hawkes machinery (cox_baseline_rates, cox_only_loglik, BIC, grid+refine
fitter) is reimplemented identically EXCEPT the self-excitation kernel: S_t = sum_j exp(-beta*dt_real)
where dt_real = (wall-clock seconds elapsed since failure j). Call-index version used (t-j) call gaps.

HONEST CAVEAT: wall-clock on a ~109-failure-event signal with ~45% sub-second and 388 exact-0s gaps
risks the Filimonov-Sornette small-N / coarse-timestamp regime. Read results as a robustness CHECK,
not a new estimate. CPU/stdlib only.
"""
import json, glob, os, math, re, csv, statistics
from datetime import datetime
from collections import defaultdict

EPS = 1e-6
MIN_TRIALS = 8

def pts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()

def sig(x):
    if x < -40: return EPS
    if x >  40: return 1-EPS
    return 1.0/(1.0+math.exp(-x))
def logit(p):
    p = min(max(p, EPS), 1-EPS)
    return math.log(p/(1-p))

# ---- parser: identical err/dedup logic to L3 parse_codex, PLUS per-event wall-clock time ----
def parse_codex_ts():
    fs = glob.glob(os.path.expanduser('~/.codex/sessions/**/*.jsonl'), recursive=True)
    out = {}
    for f in fs:
        callmap = {}
        for line in open(f):
            line = line.strip()
            if not line: continue
            try: d = json.loads(line)
            except: continue
            p = d.get('payload') or d
            if p.get('type') == 'function_call':
                callmap[p.get('call_id')] = (p.get('name','?'), p.get('arguments',''))
        seen = set(); seq = []
        for line in open(f):
            line = line.strip()
            if not line: continue
            try: d = json.loads(line)
            except: continue
            p = d.get('payload') or d
            if p.get('type') == 'function_call_output':
                cid = p.get('call_id')
                if cid in seen: continue
                seen.add(cid)
                out_s = str(p.get('output',''))
                m = re.search(r'exited with code (\d+)', out_s)
                err = 0
                if m and m.group(1) != '0': err = 1
                elif 'error' in out_s[:120].lower() and 'code 0' not in out_s: err = 1
                ts = d.get('timestamp')
                t = pts(ts) if ts else None
                tname = callmap.get(cid, ('unknown',''))[0]
                seq.append((err, tname, t))
        if len(seq) >= MIN_TRIALS:
            out[f] = seq
    return out

def build_sessions(parsed):
    """Each session = list of (err, tool, t0_relative_seconds). Drop events missing ts.
    t0 anchored at first event in session (relative seconds)."""
    out = []
    for key, events in parsed.items():
        ev = [e for e in events if e[2] is not None]
        if len(ev) < MIN_TRIALS: continue
        if not (0 < sum(e[0] for e in ev) < len(ev)): continue
        base = ev[0][2]
        out.append([(e[0], e[1], e[2]-base) for e in ev])
    return out

def cox_baseline_rates(sessions):
    fail = defaultdict(int); tot = defaultdict(int)
    for sess in sessions:
        for err, tool, _ in sess:
            tot[tool]+=1; fail[tool]+=err
    return {t: min(max(fail[t]/tot[t], EPS), 1-EPS) for t in tot}

def cox_only_loglik(sessions, rates):
    ll = 0.0
    for sess in sessions:
        for err, tool, _ in sess:
            p = rates.get(tool, EPS)
            ll += math.log(p) if err else math.log(1-p)
    return ll

def hawkes_loglik_wallclock(sessions, rates, alpha, beta):
    """Cox baseline (per-tool logit) + alpha*S_t, S_t = sum exp(-beta*dt_REAL_seconds)."""
    ll = 0.0
    for sess in sessions:
        prior_fail_t = []
        for (err, tool, tt) in sess:
            S = 0.0
            for tj in prior_fail_t:
                dt = tt - tj
                if dt < 0: dt = 0.0
                S += math.exp(-beta*dt)
            eta = logit(rates.get(tool, EPS)) + alpha*S
            p = sig(eta)
            ll += math.log(p) if err else math.log(1-p)
            if err: prior_fail_t.append(tt)
    return ll

def fit_hawkes_wallclock(sessions, rates, betas):
    """Grid over (alpha,beta) then local refine. alpha in [0,4]; beta(1/sec) supplied by caller."""
    best = (-1e18, 0.0, betas[len(betas)//2])
    alphas = [0.0,0.1,0.2,0.4,0.7,1.0,1.5,2.0,3.0,4.0]
    for a in alphas:
        for b in betas:
            ll = hawkes_loglik_wallclock(sessions, rates, a, b)
            if ll > best[0]: best = (ll, a, b)
    _, a0, b0 = best
    # local refine on alpha + multiplicative beta steps (beta spans orders of magnitude in 1/sec)
    for _ in range(4):
        improved = False
        for da in (-0.15,-0.05,0.05,0.15):
            for bm in (0.5,0.8,1.25,2.0):
                a = max(0.0, a0+da); b = max(1e-4, b0*bm)
                ll = hawkes_loglik_wallclock(sessions, rates, a, b)
                if ll > best[0]:
                    best = (ll, a, b); a0, b0 = a, b; improved = True
        if not improved: break
    return best

def cox_vs_hawkes_wallclock(name, sessions, betas, clock_label):
    N = sum(len(s) for s in sessions)
    rates = cox_baseline_rates(sessions)
    k_cox = len(rates)
    ll_cox = cox_only_loglik(sessions, rates)
    ll_haw, alpha, beta = fit_hawkes_wallclock(sessions, rates, betas)
    k_haw = k_cox + 2
    bic_cox = -2*ll_cox + k_cox*math.log(N)
    bic_haw = -2*ll_haw + k_haw*math.log(N)
    lr = 2*(ll_haw - ll_cox)
    return {
        'harness': name, 'clock': clock_label, 'n_sessions': len(sessions), 'n_calls': N,
        'n_tools': k_cox, 'n_failures': sum(sum(e[0] for e in s) for s in sessions),
        'cox_logL': round(ll_cox,2), 'cox_k': k_cox, 'cox_BIC': round(bic_cox,2),
        'hawkes_logL': round(ll_haw,2), 'hawkes_k': k_haw, 'hawkes_BIC': round(bic_haw,2),
        'hawkes_alpha': round(alpha,4), 'hawkes_beta_per_sec': round(beta,6),
        'hawkes_halflife_sec': round(math.log(2)/beta,3) if beta>0 else None,
        'delta_BIC_cox_minus_hawkes': round(bic_cox - bic_haw,2),
        'LR_2dll': round(lr,3),
        'hawkes_earns_params': (bic_haw < bic_cox),
        'survives_dBIC_gt6': (bic_cox - bic_haw) > 6.0 and alpha > 0,
    }

def main():
    parsed = parse_codex_ts()
    sessions = build_sessions(parsed)
    # diagnostics on wall-clock gaps (coarseness / Filimonov-Sornette regime)
    gaps=[]; zero=0; sub1=0
    for s in sessions:
        ts=[e[2] for e in s]
        for i in range(1,len(ts)):
            g=ts[i]-ts[i-1]; gaps.append(g)
            if g==0: zero+=1
            if g<1: sub1+=1
    diag = {
        'n_sessions': len(sessions),
        'n_calls': sum(len(s) for s in sessions),
        'n_failures': sum(sum(e[0] for e in s) for s in sessions),
        'gap_median_s': round(statistics.median(gaps),3) if gaps else None,
        'gap_mean_s': round(statistics.mean(gaps),3) if gaps else None,
        'gap_max_s': round(max(gaps),1) if gaps else None,
        'frac_zero_gap': round(zero/len(gaps),3) if gaps else None,
        'frac_sub1s_gap': round(sub1/len(gaps),3) if gaps else None,
    }
    # beta grid in 1/sec: half-lives from ~0.35s up to ~minutes
    betas = [0.001, 0.005, 0.01, 0.03, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
    wc = cox_vs_hawkes_wallclock('codex', sessions, betas, 'wallclock_seconds')

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir = os.path.join(base, 'results'); os.makedirs(rdir, exist_ok=True)

    # JSON
    payload = {'diagnostics': diag, 'wallclock_result': wc,
               'callindex_reference_note': 'compare to EXP-0042 results/latent_cox_vs_hawkes.csv (codex row)'}
    with open(os.path.join(rdir,'wallclock_codex.json'),'w') as fh:
        json.dump(payload, fh, indent=2)
    # CSV
    with open(os.path.join(rdir,'wallclock_codex.csv'),'w',newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(wc.keys()))
        w.writeheader(); w.writerow(wc)

    print("=== WALL-CLOCK DIAGNOSTICS ==="); 
    for k,v in diag.items(): print(f"  {k}: {v}")
    print("\n=== CODEX H2 COX-vs-HAWKES (WALL-CLOCK CLOCK) ===")
    for k,v in wc.items(): print(f"  {k}: {v}")

if __name__ == '__main__':
    main()
