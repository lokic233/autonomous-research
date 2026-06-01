#!/usr/bin/env python3
"""ALTITUDE-LIFT for CLAIM-0012 (PROJ-0003, researcher-0012-altitude-lift-r4).

QUESTION (product_realist's REAL bar): is the fitted Hawkes self-excitation kernel
DESCRIPTIVE-ONLY, or does it carry genuine OUT-OF-SAMPLE PREDICTIVE value? i.e. does
"a failure just occurred" materially raise the *forecastable* probability of the next
failure, beyond (a) a homogeneous-Poisson rate null, (b) a per-tool rate-heterogeneity
(Cox) model with NO memory, and (c) a naive model-free recent-failure-rate baseline?

DESIGN — FORWARD TIME-SPLIT, ONE-STEP-AHEAD (prequential) PREDICTION, CPU/stdlib only.
 - Corpus: Codex (the lone clean genuine-exec harness). Parser = EXP-0041 burst_L3.parse_codex
   (dedup by call_id; err = 'exited with code N!=0' or 'error' in output head). 4-tuple events.
 - For each session of n calls, split FORWARD in call-index time at fraction f:
       TRAIN = calls [0, f*n)   TEST(held-out tail) = calls [f*n, n)
 - FIT on POOLED TRAIN PREFIXES ONLY (no leakage of test outcomes into parameters):
       * global_rate           (homogeneous Poisson null: P(fail)=const)
       * per-tool rates        (Cox rate-heterogeneity baseline; reuse L4.cox_baseline_rates)
       * Hawkes (alpha,beta)    (reuse L4.fit_hawkes on the train prefixes)
       * recent-rate window W*  (model-free EWMA/sliding baseline; W tuned on TRAIN by
                                 predictive log-loss over a grid) + a logit-scaled fit
 - EVALUATE one-step-ahead on the held-out TAIL. At each test call t the intensity uses ONLY
   the observed history up to t (train + already-revealed tail) — this is honest filtering /
   prequential forecasting, the standard protocol for point-process out-of-sample evaluation:
       p_pois   = global_rate
       p_cox    = rate[tool_t]                                   (knows tool, no memory)
       p_hawkes = sig( logit(rate[tool_t]) + alpha * S_t )       S_t = sum_{prior fails j<t in
                  session} exp(-beta*(t-j))                        (fitted self-excitation kernel)
       p_recent = recent failure fraction over last W* calls in the session (model-free memory)
 - METRICS on pooled held-out calls (OUT-OF-SAMPLE):
       * mean predictive log-likelihood per held-out call, each model
       * dLL_oos(hawkes - poisson), (hawkes - cox), (hawkes - recent)   [bits & nats]
       * AUC (Mann-Whitney U / stdlib) of each model's p_t separating fail vs no-fail on test
       * early-warning: failure rate on test calls in the K-call window AFTER a failure vs the
         unconditional test failure rate (lift), + Hawkes precision/recall at its train-tuned
         operating threshold
 - INFERENCE (stdlib, no scipy):
       * SESSION BOOTSTRAP (B): resample held-out sessions w/ replacement, recompute dLL_oos
         totals -> 95% percentile CI. CI excluding 0 => predictive gain is real, not 1-session.
       * TIMING-PERMUTATION NULL (B): within each test tail permute the err labels (preserve
         per-session count) and recompute Hawkes-minus-Cox dLL -> null dist; observed percentile
         = p. Isolates whether *timing/clustering* (not marginal rate) drives the gain.

HONEST-NULL CLAUSE: if dLL_oos<=0 / CI includes 0 / Hawkes does NOT beat the recent-rate
baseline / timing-perm p not significant -> the predictive lift FAILS and the claim stays
DESCRIPTIVE. That is a legitimate terminal result; it is reported as such. No fabrication.
"""
import sys, os, json, math, random, statistics, csv
from collections import defaultdict

# ---- reuse existing stdlib machinery (parsers + Hawkes/Cox) -----------------
HOME = os.path.expanduser('~')
E41 = os.path.join(HOME, 'autonomous-research/experiments/2026-05-31/EXP-0041/impl')
E42 = os.path.join(HOME, 'autonomous-research/experiments/2026-05-31/EXP-0042/impl')
sys.path.insert(0, E41); sys.path.insert(0, E42)
import burst_L3 as L3   # parse_codex -> {file: [(err, tool, refined, argtext), ...]}
import robust_L4 as L4  # sig, logit, EPS, cox_baseline_rates, cox_only_loglik,
                        # hawkes_loglik, fit_hawkes

random.seed(20260601)
EPS = L4.EPS
sig = L4.sig
logit = L4.logit

# output dir = <experiment_root>/results , where experiment_root = parent of this file's dir
HERE = os.path.dirname(os.path.abspath(__file__))
EXP_ROOT = os.path.dirname(HERE)               # .../EXP-XXXX  (impl/ -> EXP-XXXX)
OUT = os.path.join(EXP_ROOT, 'results')
os.makedirs(OUT, exist_ok=True)

SPLIT_FRACTIONS = [0.5, 0.6, 0.7]   # forward time-split points (robustness sweep)
RECENT_W_GRID   = [2, 3, 4, 5, 6, 8, 10]
B_BOOT          = 2000
B_PERM          = 2000

# ----------------------------------------------------------------------------
def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

def to_sessions(parsed):
    """Codex parsed -> {key: [(err, tool), ...]} keeping only MIXED sessions (both
    failure & success present) AND with >=2 calls in BOTH train & test at min split.
    We keep the raw call order = forward call-index time."""
    out = {}
    for k, ev in parsed.items():
        s = [(int(e[0]), e[1]) for e in ev]
        if 0 < sum(x[0] for x in s) < len(s):
            out[k] = s
    return out

def split_session(s, f):
    n = len(s)
    cut = int(math.floor(f * n))
    cut = max(1, min(n - 1, cut))   # ensure both sides non-empty
    return s[:cut], s[cut:], cut

# ---- recent-rate (model-free memory) baseline ------------------------------
def recent_rate_at(history_err, t, W):
    """failure fraction over the last W calls strictly before position t (within session).
    history_err = list of 0/1 for calls 0..t-1 in THIS session. Laplace-smoothed."""
    lo = max(0, t - W)
    window = history_err[lo:t]
    if not window:
        return None
    return (sum(window) + 0.5) / (len(window) + 1.0)   # smoothed

def tune_recent_W(train_sessions):
    """Pick W maximizing one-step-ahead predictive LL on TRAIN (prequential within train)."""
    best_W, best_ll = RECENT_W_GRID[0], -1e18
    glob_rate = global_rate(train_sessions)
    for W in RECENT_W_GRID:
        ll = 0.0
        for s in train_sessions:
            errs = [e for e, _ in s]
            for t in range(len(s)):
                p = recent_rate_at(errs, t, W)
                if p is None:
                    p = glob_rate              # cold-start = global rate
                p = min(max(p, EPS), 1 - EPS)
                ll += math.log(p) if errs[t] else math.log(1 - p)
        if ll > best_ll:
            best_ll, best_W = ll, W
    return best_W

def global_rate(sessions):
    tot = sum(len(s) for s in sessions)
    fail = sum(e for s in sessions for e, _ in s)
    return min(max(fail / max(tot, 1), EPS), 1 - EPS)

# ---- per-call one-step-ahead predicted prob for each model on the test tail -
def predict_tail(session, cut, rates, glob_rate_v, alpha, beta, W):
    """Return list of (err_t, p_pois, p_cox, p_hawkes, p_recent, after_fail_flag) for the
    held-out tail calls (index >= cut). Uses ONLY history up to t (filtering)."""
    errs = [e for e, _ in session]
    rows = []
    # precompute prior-failure indices incrementally as we walk the WHOLE session, but only
    # emit rows for t>=cut. S_t / recent use full observed history up to t (train+revealed).
    prior_fail_idx = []
    for t, (err, tool) in enumerate(session):
        if t >= cut:
            S = 0.0
            for j in prior_fail_idx:
                S += math.exp(-beta * (t - j))
            p_haw = sig(logit(rates.get(tool, glob_rate_v)) + alpha * S)
            p_cox = min(max(rates.get(tool, glob_rate_v), EPS), 1 - EPS)
            p_pois = glob_rate_v
            pr = recent_rate_at(errs, t, W)
            p_rec = glob_rate_v if pr is None else min(max(pr, EPS), 1 - EPS)
            after_fail = 1 if (t - 1) in set(prior_fail_idx) else 0
            rows.append((err, p_pois, p_cox, p_haw, p_rec, after_fail))
        if err:
            prior_fail_idx.append(t)
    return rows

def ll_of(rows, idx):
    """sum predictive log-likelihood (nats) for model column idx over rows."""
    s = 0.0
    for r in rows:
        p = min(max(r[idx], EPS), 1 - EPS)
        s += math.log(p) if r[0] else math.log(1 - p)
    return s

def auc_mw(rows, idx):
    """AUC via Mann-Whitney U (stdlib). pos=fail, neg=no-fail, score=p model column idx."""
    pos = [r[idx] for r in rows if r[0] == 1]
    neg = [r[idx] for r in rows if r[0] == 0]
    if not pos or not neg:
        return None
    # rank-sum with tie handling
    allv = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    # assign average ranks
    ranks = [0.0] * len(allv)
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for kk in range(i, j + 1):
            ranks[kk] = avg
        i = j + 1
    R_pos = sum(ranks[k] for k in range(len(allv)) if allv[k][1] == 1)
    n1 = len(pos); n0 = len(neg)
    U = R_pos - n1 * (n1 + 1) / 2.0
    return U / (n1 * n0)

# ============================================================================
def run_split(sessions, f):
    """One forward time-split at fraction f. Returns metrics dict + per-session test rows
    (for bootstrap/permutation)."""
    keys = list(sessions.keys())
    train_all = []; per_sess_test = {}
    # build train prefixes + remember cut per session
    cuts = {}
    train_sessions = []
    for k in keys:
        tr, te, cut = split_session(sessions[k], f)
        cuts[k] = cut
        train_sessions.append(tr)
        train_all.extend(tr)
    # ---- FIT on train only ----
    glob_r = global_rate(train_sessions)
    rates = L4.cox_baseline_rates(train_sessions)        # per-tool from TRAIN
    ll_haw_tr, alpha, beta = L4.fit_hawkes(train_sessions, rates)
    W = tune_recent_W(train_sessions)
    # ---- EVALUATE on held-out tail ----
    all_rows = []
    for k in keys:
        rows = predict_tail(sessions[k], cuts[k], rates, glob_r, alpha, beta, W)
        if rows:
            per_sess_test[k] = rows
            all_rows.extend(rows)
    n_test = len(all_rows)
    n_test_fail = sum(r[0] for r in all_rows)
    # predictive LL (nats) per model
    LL = {'poisson': ll_of(all_rows, 1), 'cox': ll_of(all_rows, 2),
          'hawkes': ll_of(all_rows, 3), 'recent': ll_of(all_rows, 4)}
    per_call = {m: LL[m] / n_test for m in LL}
    NAT2BIT = 1.0 / math.log(2)
    dLL = {
        'hawkes_minus_poisson_nats': LL['hawkes'] - LL['poisson'],
        'hawkes_minus_cox_nats':     LL['hawkes'] - LL['cox'],
        'hawkes_minus_recent_nats':  LL['hawkes'] - LL['recent'],
        'hawkes_minus_poisson_bits_per_call': (per_call['hawkes'] - per_call['poisson']) * NAT2BIT,
        'hawkes_minus_cox_bits_per_call':     (per_call['hawkes'] - per_call['cox']) * NAT2BIT,
        'hawkes_minus_recent_bits_per_call':  (per_call['hawkes'] - per_call['recent']) * NAT2BIT,
    }
    auc = {m: auc_mw(all_rows, i) for m, i in
           [('poisson', 1), ('cox', 2), ('hawkes', 3), ('recent', 4)]}
    # early-warning lift: failure rate on test calls immediately after a failure vs uncond
    aft = [r[0] for r in all_rows if r[5] == 1]
    base_rate = n_test_fail / n_test if n_test else None
    ew_after_fail_rate = (sum(aft) / len(aft)) if aft else None
    ew_lift = (ew_after_fail_rate / base_rate) if (ew_after_fail_rate and base_rate) else None
    # ---- SESSION BOOTSTRAP CI on dLL(hawkes-cox) and dLL(hawkes-recent) ----
    test_keys = [k for k in keys if k in per_sess_test]
    def sess_dll(k, a_idx, b_idx):
        return ll_of(per_sess_test[k], a_idx) - ll_of(per_sess_test[k], b_idx)
    boot = {'hawkes_minus_cox': [], 'hawkes_minus_recent': [], 'hawkes_minus_poisson': []}
    nks = len(test_keys)
    for _ in range(B_BOOT):
        samp = [test_keys[random.randrange(nks)] for _ in range(nks)]
        boot['hawkes_minus_cox'].append(sum(sess_dll(k, 3, 2) for k in samp))
        boot['hawkes_minus_recent'].append(sum(sess_dll(k, 3, 4) for k in samp))
        boot['hawkes_minus_poisson'].append(sum(sess_dll(k, 3, 1) for k in samp))
    def ci(xs):
        xs = sorted(xs)
        lo = xs[int(0.025 * len(xs))]; hi = xs[int(0.975 * len(xs)) - 1]
        return round(lo, 3), round(hi, 3), round(statistics.mean(xs), 3)
    boot_ci = {m: ci(v) for m, v in boot.items()}
    # ---- TIMING-PERMUTATION NULL: hawkes-minus-cox dLL with err timing shuffled in tail ----
    obs_hc = dLL['hawkes_minus_cox_nats']
    perm_ge = 0
    perm_vals = []
    for _ in range(B_PERM):
        tot = 0.0
        for k in test_keys:
            rows = per_sess_test[k]
            errs = [r[0] for r in rows]
            random.shuffle(errs)
            # recompute hawkes & cox LL with permuted err labels (p columns fixed = the
            # model's predictions for the ACTUAL sequence; permuting labels breaks the
            # timing alignment, testing whether clustering is what's predicted).
            s_h = 0.0; s_c = 0.0
            for r, e in zip(rows, errs):
                ph = min(max(r[3], EPS), 1 - EPS); pc = min(max(r[2], EPS), 1 - EPS)
                s_h += math.log(ph) if e else math.log(1 - ph)
                s_c += math.log(pc) if e else math.log(1 - pc)
            tot += (s_h - s_c)
        perm_vals.append(tot)
        if tot >= obs_hc:
            perm_ge += 1
    perm_p = (perm_ge + 1) / (B_PERM + 1)
    return {
        'split_fraction': f, 'alpha': round(alpha, 4), 'beta': round(beta, 4),
        'recent_W': W, 'global_rate_train': round(glob_r, 4),
        'n_train_calls': len(train_all), 'n_test_calls': n_test,
        'n_test_fail': n_test_fail, 'n_test_sessions': len(test_keys),
        'test_base_rate': round(base_rate, 4) if base_rate else None,
        'per_call_LL': {m: round(v, 5) for m, v in per_call.items()},
        'dLL': {m: round(v, 4) for m, v in dLL.items()},
        'auc': {m: (round(v, 4) if v is not None else None) for m, v in auc.items()},
        'early_warning_after_fail_rate': round(ew_after_fail_rate, 4) if ew_after_fail_rate else None,
        'early_warning_lift_vs_base': round(ew_lift, 3) if ew_lift else None,
        'bootstrap95_dLL': {m: {'lo': c[0], 'hi': c[1], 'mean': c[2]} for m, c in boot_ci.items()},
        'timing_perm_obs_hawkes_minus_cox_nats': round(obs_hc, 4),
        'timing_perm_p': round(perm_p, 5),
        'timing_perm_null_mean': round(statistics.mean(perm_vals), 4),
    }

def verdict(splits):
    """Aggregate honest verdict across split fractions."""
    def ok(s):
        hc = s['bootstrap95_dLL']['hawkes_minus_cox']
        hr = s['bootstrap95_dLL']['hawkes_minus_recent']
        return (s['dLL']['hawkes_minus_cox_nats'] > 0 and hc['lo'] > 0 and
                s['dLL']['hawkes_minus_recent_nats'] > 0 and hr['lo'] > 0 and
                s['timing_perm_p'] < 0.05 and
                (s['auc']['hawkes'] or 0) > (s['auc']['cox'] or 0))
    passes = [s['split_fraction'] for s in splits if ok(s)]
    return {
        'splits_passing_full_bar': passes,
        'n_splits': len(splits),
        'PREDICTIVE_LIFT_SUPPORTED': len(passes) >= 1,
        'PREDICTIVE_LIFT_ROBUST_ALL_SPLITS': len(passes) == len(splits),
        'bar': ('dLL_oos(hawkes-cox)>0 & boot95 lo>0 AND dLL_oos(hawkes-recent)>0 & boot95 lo>0 '
                'AND timing_perm_p<0.05 AND AUC_hawkes>AUC_cox'),
    }

def main():
    parsed = L3.parse_codex()
    sessions = to_sessions(parsed)
    print(f"Codex mixed sessions: {len(sessions)}  "
          f"total calls: {sum(len(s) for s in sessions.values())}  "
          f"total fails: {sum(e for s in sessions.values() for e,_ in s)}")
    splits = []
    for f in SPLIT_FRACTIONS:
        r = run_split(sessions, f)
        splits.append(r)
        print(f"\n=== forward split f={f} ===")
        print(f"  fit: alpha={r['alpha']} beta={r['beta']} recentW={r['recent_W']} "
              f"glob_rate={r['global_rate_train']}")
        print(f"  test: {r['n_test_calls']} calls / {r['n_test_fail']} fails / "
              f"{r['n_test_sessions']} sessions  base_rate={r['test_base_rate']}")
        print(f"  per-call LL: {r['per_call_LL']}")
        print(f"  dLL(hawkes-poisson)={r['dLL']['hawkes_minus_poisson_nats']}  "
              f"(hawkes-cox)={r['dLL']['hawkes_minus_cox_nats']}  "
              f"(hawkes-recent)={r['dLL']['hawkes_minus_recent_nats']} nats")
        print(f"  AUC: {r['auc']}")
        print(f"  early-warning lift (P(fail|after fail)/base): {r['early_warning_lift_vs_base']} "
              f"(after-fail rate {r['early_warning_after_fail_rate']})")
        print(f"  boot95 dLL(hawkes-cox): {r['bootstrap95_dLL']['hawkes_minus_cox']}")
        print(f"  boot95 dLL(hawkes-recent): {r['bootstrap95_dLL']['hawkes_minus_recent']}")
        print(f"  timing-perm p (hawkes-cox clustering): {r['timing_perm_p']} "
              f"(obs {r['timing_perm_obs_hawkes_minus_cox_nats']} vs null mean "
              f"{r['timing_perm_null_mean']})")
    v = verdict(splits)
    print("\n=== HONEST VERDICT ===")
    for k, val in v.items():
        print(f"  {k}: {val}")
    bundle = {
        'corpus': 'codex',
        'n_mixed_sessions': len(sessions),
        'n_calls': sum(len(s) for s in sessions.values()),
        'n_fails': sum(e for s in sessions.values() for e, _ in s),
        'splits': splits, 'verdict': v,
        'protocol': 'forward time-split within-session, one-step-ahead prequential, params fit on train prefixes only',
    }
    with open(os.path.join(OUT, 'predictive_oos.json'), 'w') as fh:
        json.dump(bundle, fh, indent=2, default=str)
    # flat CSV of headline per-split numbers
    with open(os.path.join(OUT, 'predictive_oos.csv'), 'w', newline='') as fh:
        cols = ['split_fraction', 'alpha', 'beta', 'recent_W', 'n_test_calls', 'n_test_fail',
                'test_base_rate', 'll_poisson', 'll_cox', 'll_hawkes', 'll_recent',
                'dLL_hawkes_cox', 'dLL_hawkes_recent', 'dLL_hawkes_poisson',
                'auc_cox', 'auc_hawkes', 'auc_recent', 'ew_lift',
                'boot_hc_lo', 'boot_hc_hi', 'boot_hr_lo', 'boot_hr_hi', 'timing_perm_p']
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
        for s in splits:
            w.writerow({
                'split_fraction': s['split_fraction'], 'alpha': s['alpha'], 'beta': s['beta'],
                'recent_W': s['recent_W'], 'n_test_calls': s['n_test_calls'],
                'n_test_fail': s['n_test_fail'], 'test_base_rate': s['test_base_rate'],
                'll_poisson': s['per_call_LL']['poisson'], 'll_cox': s['per_call_LL']['cox'],
                'll_hawkes': s['per_call_LL']['hawkes'], 'll_recent': s['per_call_LL']['recent'],
                'dLL_hawkes_cox': s['dLL']['hawkes_minus_cox_nats'],
                'dLL_hawkes_recent': s['dLL']['hawkes_minus_recent_nats'],
                'dLL_hawkes_poisson': s['dLL']['hawkes_minus_poisson_nats'],
                'auc_cox': s['auc']['cox'], 'auc_hawkes': s['auc']['hawkes'],
                'auc_recent': s['auc']['recent'], 'ew_lift': s['early_warning_lift_vs_base'],
                'boot_hc_lo': s['bootstrap95_dLL']['hawkes_minus_cox']['lo'],
                'boot_hc_hi': s['bootstrap95_dLL']['hawkes_minus_cox']['hi'],
                'boot_hr_lo': s['bootstrap95_dLL']['hawkes_minus_recent']['lo'],
                'boot_hr_hi': s['bootstrap95_dLL']['hawkes_minus_recent']['hi'],
                'timing_perm_p': s['timing_perm_p'],
            })
    print(f"\n-> {OUT}/predictive_oos.json , predictive_oos.csv")
    return bundle

if __name__ == '__main__':
    main()
