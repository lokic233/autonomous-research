#!/usr/bin/env python3
"""EXP-0042 (L4 ROBUSTNESS) — CLAIM-0012 stats-robustness blockers from VERDICT-0046.
CPU/stdlib-only. REUSES EXP-0041 burst_L3.py parsers + runs-test + tool-stratified permutation
machinery (imported as a module). PURELY DESCRIPTIVE.

THREE BLOCKING ITEMS:
 (1) CC-LEG ROBUSTNESS [load-bearing]: full per-session tool-stratified-Z DISTRIBUTION for CC
     (quantiles/histogram), SIZE-WEIGHTED vs UNWEIGHTED Stouffer, and LEAVE-ONE-SESSION-OUT (LOSO)
     sensitivity. Honest question: is CC's tool-strat signal real or Stouffer-aggregation-carried
     (the EXP-0040 killed failure mode, per-session median strat-Z=0)?
 (2) COX-vs-HAWKES BIC: per harness, fit on inter-failure event sequences:
     - Cox-only (rate-heterogeneity, i.e. inhomogeneous-rate / piecewise-constant baseline; here a
       per-tool-rate Poisson over call positions = rate heterogeneity, NO self-excitation)
     - Cox+Hawkes (baseline rate + self-excitation alpha*exp(-beta*dt) temporal-memory term)
     Report logL, k, BIC each; deltaBIC = BIC(Cox) - BIC(Cox+Hawkes). >0 (and >~6) => Hawkes term
     earns its parameters => genuine temporal memory beyond rate-heterogeneity.
 (3) MULTIPLE-COMPARISON: Bonferroni + Holm across the full discriminating-ablation family
     (~12 tests: per-harness whole-perm, tool-strat, retry-collapse). Does CC tool-strat p~0.009
     survive correction?

KEEP DESCRIPTIVE. No error-class conditioning, no recovery prediction.
"""
import json, glob, os, math, random, statistics, csv, sys
from collections import defaultdict

# import the L3 machinery (parsers, runs test, permutation nulls)
L3DIR = os.path.expanduser('~/autonomous-research/experiments/2026-05-31/EXP-0041/impl')
sys.path.insert(0, L3DIR)
import burst_L3 as L3   # parse_cc/parse_codex/parse_gemini, runs_z, count_runs,
                        # perm_runs_whole, perm_runs_tool_stratified, interfailure_gaps,
                        # collapse_retries, MIN_TRIALS

random.seed(20260531)
NPERM = 2500

# ----------------------------------------------------------------------------
# Normal CDF (stdlib) for converting per-session permutation Z back to a p-value
# and for Stouffer aggregate p.
# ----------------------------------------------------------------------------
def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

# ============================================================================
# (1) CC-LEG ROBUSTNESS
# ============================================================================
def quantiles(xs, qs=(0,5,10,25,50,75,90,95,100)):
    if not xs: return {}
    s = sorted(xs); n = len(s)
    out = {}
    for q in qs:
        if n == 1: out[q] = s[0]; continue
        pos = (q/100.0)*(n-1); lo = int(math.floor(pos)); hi = int(math.ceil(pos))
        frac = pos - lo
        out[q] = s[lo]*(1-frac) + s[hi]*frac
    return out

def histogram(xs, edges):
    h = [0]*(len(edges)-1)
    for x in xs:
        for i in range(len(edges)-1):
            if (edges[i] <= x < edges[i+1]) or (i==len(edges)-2 and x==edges[-1]):
                h[i]+=1; break
    return h

def stouffer_unweighted(zs):
    return sum(zs)/math.sqrt(len(zs)) if zs else None

def stouffer_weighted(zs, ws):
    """size-weighted Stouffer: Z = sum(w_i z_i)/sqrt(sum(w_i^2)). Weight = sqrt(n_calls) per session
    (info-content weighting; matches the standard weighted-Stouffer where w ~ sqrt(sample size))."""
    if not zs: return None
    num = sum(w*z for w,z in zip(ws,zs))
    den = math.sqrt(sum(w*w for w in ws))
    return num/den if den>0 else None

def cc_robustness(parsed):
    """Compute per-session tool-stratified Z for every CC session that is shufflable, plus
    whole-session perm Z. Return distribution + weighted/unweighted Stouffer + LOSO."""
    rows = []
    z_strat = []; z_whole = []; weights = []; sess_ids = []
    for key, events in parsed.items():
        seq   = [e[0] for e in events]
        tools = [e[1] for e in events]
        if not (0 < sum(seq) < len(seq)):
            continue
        rw = L3.perm_runs_whole(seq, nperm=NPERM)
        rs = L3.perm_runs_tool_stratified(seq, tools, nperm=NPERM)
        if rs is None:
            continue
        zs = rs['z_strat']; zw = rw['z_perm'] if rw else None
        z_strat.append(zs); z_whole.append(zw); weights.append(math.sqrt(len(seq)))
        sess_ids.append(os.path.basename(key))
        rows.append({'session': os.path.basename(key), 'n': len(seq), 'fails': sum(seq),
                     'n_tools': rs['n_tools'], 'strat_shufflable': rs['shufflable'],
                     'z_whole_perm': round(zw,3) if zw is not None else None,
                     'z_tool_strat': round(zs,3),
                     'p_tool_strat': round(rs['p_clustered'],4)})
    n = len(z_strat)
    qs = quantiles(z_strat)
    edges = [-6,-4,-3,-2,-1,-0.5,0,0.5,1,2,4,6]
    hist = histogram(z_strat, edges)
    su = stouffer_unweighted(z_strat)
    sw = stouffer_weighted(z_strat, weights)
    # LOSO: drop each session, recompute UNWEIGHTED stouffer; report worst (closest-to-0) and
    # which session removal most weakens. Also LOSO on weighted.
    loso = []
    for i in range(n):
        zs_i = z_strat[:i]+z_strat[i+1:]
        ws_i = weights[:i]+weights[i+1:]
        loso.append({'dropped': sess_ids[i], 'n_left': n-1,
                     'stouffer_unw': round(stouffer_unweighted(zs_i),3),
                     'stouffer_wt': round(stouffer_weighted(zs_i, ws_i),3),
                     'dropped_z': round(z_strat[i],3), 'dropped_w': round(weights[i],3)})
    # sort LOSO by weakest (largest, i.e. closest to 0 / most positive) unweighted stouffer
    loso_sorted = sorted(loso, key=lambda r: r['stouffer_unw'], reverse=True)
    frac_neg = sum(1 for z in z_strat if z < 0)/n if n else None
    frac_sig = sum(1 for r in rows if r['p_tool_strat'] < 0.05)/n if n else None
    # aggregate Stouffer p (one-sided clustered = lower tail)
    return {
        'n_sessions_shufflable': n,
        'median_z_strat': round(statistics.median(z_strat),3) if z_strat else None,
        'mean_z_strat': round(statistics.mean(z_strat),3) if z_strat else None,
        'quantiles': {k: round(v,3) for k,v in qs.items()},
        'hist_edges': edges, 'hist_counts': hist,
        'frac_sessions_z_neg': round(frac_neg,3) if frac_neg is not None else None,
        'frac_sessions_p_sig': round(frac_sig,3) if frac_sig is not None else None,
        'stouffer_unweighted': round(su,3) if su is not None else None,
        'stouffer_weighted_sqrtn': round(sw,3) if sw is not None else None,
        'stouffer_unw_p': norm_cdf(su) if su is not None else None,
        'stouffer_wt_p': norm_cdf(sw) if sw is not None else None,
        'loso_full': loso_sorted,
        'loso_worst_unw': loso_sorted[0] if loso_sorted else None,
        'loso_worst_wt': max(loso, key=lambda r: r['stouffer_wt']) if loso else None,
    }, rows

# ============================================================================
# (2) COX-only vs COX+HAWKES BIC on inter-failure / failure-arrival sequences
# ----------------------------------------------------------------------------
# We model failure ARRIVALS over the discrete CALL INDEX axis (each tool call = one unit of
# "time"; failures are events). Pooled across a harness's sessions (each session independent,
# its own time origin). This is the descriptive arrival process — same estimand as the claim.
#
# COX-only (rate-heterogeneity, NO self-excitation): conditional intensity at call position t in
#   a session is lambda0(tool_t) = per-tool baseline failure rate (a piecewise-constant Cox
#   baseline indexed by the covariate tool_name). This is EXACTLY the rate-heterogeneity /
#   Cox-mixture alternative the committee flagged. Likelihood = Bernoulli over calls with
#   p_t = lambda0(tool_t) (clamped to (eps,1-eps)). Params k = number of distinct tools (the
#   per-tool rates) — we count only tools that actually appear.
#
# COX+HAWKES: add a self-excitation term. Intensity (hazard) at call t:
#   p_t = sigma( logit(lambda0(tool_t)) + alpha * S_t ),  S_t = sum_{prior fails j<t in same session}
#         exp(-beta * (t - j))   (exponential Hawkes kernel over call-index gaps).
#   Params k = (#tools) + 2 (alpha, beta). alpha>0 => self-excitation/temporal memory.
#   We fit lambda0 as the Cox baseline (fixed from the Cox-only MLE = per-tool empirical rate)
#   then MLE (alpha,beta) by grid + local refine (stdlib, no optimizer). This is conservative:
#   it only asks whether ADDING memory on top of the rate-heterogeneity baseline improves fit
#   enough to pay for 2 params (BIC).
# ============================================================================
EPS = 1e-6
def sig(x):
    if x < -40: return EPS
    if x >  40: return 1-EPS
    return 1.0/(1.0+math.exp(-x))
def logit(p):
    p = min(max(p, EPS), 1-EPS)
    return math.log(p/(1-p))

def build_sessions(parsed):
    """Return list of sessions, each = list of (is_err, tool_name)."""
    out = []
    for key, events in parsed.items():
        seq = [(e[0], e[1]) for e in events]
        if 0 < sum(e[0] for e in seq) < len(seq):
            out.append(seq)
    return out

def cox_baseline_rates(sessions):
    """Per-tool empirical failure rate (pooled across sessions) = Cox rate-heterogeneity baseline."""
    fail = defaultdict(int); tot = defaultdict(int)
    for sess in sessions:
        for err, tool in sess:
            tot[tool]+=1; fail[tool]+=err
    rates = {}
    for t in tot:
        rates[t] = min(max(fail[t]/tot[t], EPS), 1-EPS)
    return rates

def cox_only_loglik(sessions, rates):
    ll = 0.0
    for sess in sessions:
        for err, tool in sess:
            p = rates.get(tool, EPS)
            ll += math.log(p) if err else math.log(1-p)
    return ll

def hawkes_loglik(sessions, rates, alpha, beta):
    """Cox baseline (per-tool logit) + alpha*S_t self-excitation, S_t exp-kernel over call index."""
    ll = 0.0
    for sess in sessions:
        prior_fail_idx = []
        for t,(err,tool) in enumerate(sess):
            S = 0.0
            for j in prior_fail_idx:
                S += math.exp(-beta*(t-j))
            eta = logit(rates.get(tool, EPS)) + alpha*S
            p = sig(eta)
            ll += math.log(p) if err else math.log(1-p)
            if err: prior_fail_idx.append(t)
    return ll

def fit_hawkes(sessions, rates):
    """Grid over (alpha,beta) then local refine. alpha in [0, 4], beta in [0.05, 3]."""
    best = (-1e18, 0.0, 1.0)
    alphas = [0.0,0.1,0.2,0.4,0.7,1.0,1.5,2.0,3.0,4.0]
    betas  = [0.1,0.25,0.5,0.75,1.0,1.5,2.0,3.0]
    for a in alphas:
        for b in betas:
            ll = hawkes_loglik(sessions, rates, a, b)
            if ll > best[0]: best = (ll, a, b)
    # local refine around best
    _, a0, b0 = best
    for _ in range(3):
        improved = False
        for da in (-0.15,-0.05,0.05,0.15):
            for db in (-0.2,-0.05,0.05,0.2):
                a = max(0.0, a0+da); b = max(0.02, b0+db)
                ll = hawkes_loglik(sessions, rates, a, b)
                if ll > best[0]:
                    best = (ll, a, b); a0, b0 = a, b; improved = True
        if not improved: break
    return best  # (ll, alpha, beta)

def cox_vs_hawkes(name, parsed):
    sessions = build_sessions(parsed)
    N = sum(len(s) for s in sessions)   # total Bernoulli observations (calls)
    rates = cox_baseline_rates(sessions)
    k_cox = len(rates)                  # per-tool baseline rates
    ll_cox = cox_only_loglik(sessions, rates)
    ll_haw, alpha, beta = fit_hawkes(sessions, rates)
    k_haw = k_cox + 2
    bic_cox = -2*ll_cox + k_cox*math.log(N)
    bic_haw = -2*ll_haw + k_haw*math.log(N)
    # LRT (nested: Hawkes adds alpha,beta; under H0 alpha=0)
    lr = 2*(ll_haw - ll_cox)
    return {
        'harness': name, 'n_sessions': len(sessions), 'n_calls': N, 'n_tools': k_cox,
        'cox_logL': round(ll_cox,2), 'cox_k': k_cox, 'cox_BIC': round(bic_cox,2),
        'hawkes_logL': round(ll_haw,2), 'hawkes_k': k_haw, 'hawkes_BIC': round(bic_haw,2),
        'hawkes_alpha': round(alpha,3), 'hawkes_beta': round(beta,3),
        'delta_BIC_cox_minus_hawkes': round(bic_cox - bic_haw,2),
        'LR_2dll': round(lr,3),
        'hawkes_earns_params': (bic_haw < bic_cox),
    }

# ============================================================================
# (3) MULTIPLE-COMPARISON correction across the discriminating-ablation family
# ============================================================================
def stouffer_to_p(z):
    """one-sided (clustered = lower tail) p from a Stouffer Z."""
    return norm_cdf(z)

def bonferroni_holm(named_ps):
    """named_ps = list of (name, p). Return per-test Bonferroni + Holm adjusted p and survival."""
    m = len(named_ps)
    # Bonferroni
    bonf = {nm: min(1.0, p*m) for nm,p in named_ps}
    # Holm: sort ascending, adjusted_i = max so far of (m-i)*p_(i)
    order = sorted(named_ps, key=lambda x: x[1])
    holm = {}; running = 0.0
    for i,(nm,p) in enumerate(order):
        adj = min(1.0, (m-i)*p)
        running = max(running, adj)
        holm[nm] = running
    rows = []
    for nm,p in named_ps:
        rows.append({'test': nm, 'p_raw': p, 'p_bonferroni': bonf[nm], 'p_holm': holm[nm],
                     'survives_bonf_0.05': bonf[nm] < 0.05, 'survives_holm_0.05': holm[nm] < 0.05})
    return rows

# ============================================================================
def main():
    print("Parsing corpora via L3 machinery...")
    cc = L3.parse_cc(); cx = L3.parse_codex(); gm = L3.parse_gemini()
    print(f"  CC sessions: {len(cc)}  Codex: {len(cx)}  Gemini: {len(gm)}\n")

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir = os.path.join(base, 'results'); os.makedirs(rdir, exist_ok=True)

    # ---- (1) CC robustness ----
    print("="*70); print("(1) CC-LEG ROBUSTNESS"); print("="*70)
    cc_res, cc_rows = cc_robustness(cc)
    for k in ('n_sessions_shufflable','median_z_strat','mean_z_strat','frac_sessions_z_neg',
              'frac_sessions_p_sig','stouffer_unweighted','stouffer_weighted_sqrtn',
              'stouffer_unw_p','stouffer_wt_p'):
        print(f"   {k:26}: {cc_res[k]}")
    print(f"   quantiles(z_strat)        : {cc_res['quantiles']}")
    print(f"   hist edges                : {cc_res['hist_edges']}")
    print(f"   hist counts               : {cc_res['hist_counts']}")
    print(f"   LOSO worst (unw, drop->Z) : {cc_res['loso_worst_unw']}")
    print(f"   LOSO worst (wt,  drop->Z) : {cc_res['loso_worst_wt']}")

    # ---- (2) Cox vs Hawkes ----
    print("\n"+"="*70); print("(2) COX-only vs COX+HAWKES BIC"); print("="*70)
    cvh = []
    for name, parsed in [('claude_code', cc), ('codex', cx), ('gemini', gm)]:
        r = cox_vs_hawkes(name, parsed); cvh.append(r)
        print(f"  --- {name} ---")
        for k in ('n_sessions','n_calls','n_tools','cox_logL','cox_BIC',
                  'hawkes_logL','hawkes_BIC','hawkes_alpha','hawkes_beta',
                  'delta_BIC_cox_minus_hawkes','LR_2dll','hawkes_earns_params'):
            print(f"     {k:30}: {r[k]}")

    # ---- (3) Multiple comparison ----
    # Build the discriminating-ablation family from EXP-0041 + this exp's strat tests.
    # We recompute the per-harness aggregate Stouffer Z for: whole-perm, tool-strat,
    # retry-collapse @0.6 — the family the committee referenced (~12 tests).
    print("\n"+"="*70); print("(3) MULTIPLE-COMPARISON CORRECTION"); print("="*70)
    family = []  # (name, p_one_sided)
    for name, parsed in [('claude_code', cc), ('codex', cx), ('gemini', gm)]:
        z_whole=[]; z_strat=[]; z_coll=[]
        for key, events in parsed.items():
            seq=[e[0] for e in events]; tools=[e[1] for e in events]
            if not (0<sum(seq)<len(seq)): continue
            rw=L3.perm_runs_whole(seq,nperm=NPERM)
            rs=L3.perm_runs_tool_stratified(seq,tools,nperm=NPERM)
            if rw: z_whole.append(rw['z_perm'])
            if rs: z_strat.append(rs['z_strat'])
            cseq,_=L3.collapse_retries(events,thresh=0.6)
            if 0<sum(cseq)<len(cseq):
                rc=L3.perm_runs_whole(cseq,nperm=NPERM)
                if rc: z_coll.append(rc['z_perm'])
        Zw=stouffer_unweighted(z_whole); Zs=stouffer_unweighted(z_strat); Zc=stouffer_unweighted(z_coll)
        if Zw is not None: family.append((f'{name}:whole_perm', stouffer_to_p(Zw)))
        if Zs is not None: family.append((f'{name}:tool_strat', stouffer_to_p(Zs)))
        if Zc is not None: family.append((f'{name}:retry_collapse_06', stouffer_to_p(Zc)))
    mc_rows = bonferroni_holm(family)
    print(f"  Family size m = {len(family)}")
    for r in mc_rows:
        print(f"   {r['test']:34} p={r['p_raw']:.3e}  bonf={r['p_bonferroni']:.3e}({r['survives_bonf_0.05']})  holm={r['p_holm']:.3e}({r['survives_holm_0.05']})")

    # ---- write CSVs + JSON ----
    with open(os.path.join(rdir,'cc_per_session_strat.csv'),'w',newline='') as fh:
        cols=['session','n','fails','n_tools','strat_shufflable','z_whole_perm','z_tool_strat','p_tool_strat']
        w=csv.DictWriter(fh,fieldnames=cols,extrasaction='ignore'); w.writeheader()
        for r in cc_rows: w.writerow(r)
    with open(os.path.join(rdir,'cc_loso.csv'),'w',newline='') as fh:
        cols=['dropped','n_left','stouffer_unw','stouffer_wt','dropped_z','dropped_w']
        w=csv.DictWriter(fh,fieldnames=cols); w.writeheader()
        for r in cc_res['loso_full']: w.writerow(r)
    with open(os.path.join(rdir,'cox_vs_hawkes.csv'),'w',newline='') as fh:
        cols=list(cvh[0].keys()); w=csv.DictWriter(fh,fieldnames=cols); w.writeheader()
        for r in cvh: w.writerow(r)
    with open(os.path.join(rdir,'multiple_comparison.csv'),'w',newline='') as fh:
        cols=['test','p_raw','p_bonferroni','p_holm','survives_bonf_0.05','survives_holm_0.05']
        w=csv.DictWriter(fh,fieldnames=cols); w.writeheader()
        for r in mc_rows: w.writerow(r)
    # JSON bundle for the report
    bundle={'cc_robustness':cc_res,'cox_vs_hawkes':cvh,'multiple_comparison':mc_rows}
    with open(os.path.join(rdir,'robust_L4.json'),'w') as fh:
        json.dump(bundle,fh,indent=2,default=str)
    print(f"\nCSVs+JSON -> {rdir}/")
    return bundle

if __name__=='__main__':
    main()
