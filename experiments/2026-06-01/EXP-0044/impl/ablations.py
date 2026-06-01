#!/usr/bin/env python3
"""EXP-0044 — VERDICT-0047's 3 BLOCKING ablations for CLAIM-0012 (H2: discriminating
self-excitation beyond static rate-heterogeneity). CPU/stdlib-only. Reuses EXP-0041
burst_L3 parsers + EXP-0042 robust_L4 Hawkes/Cox machinery.

BLOCKING-1: CODEX LOSO. Drop EACH codex session in turn; recompute (a) Hawkes dBIC,
            (b) tool-stratified permutation Stouffer Z + p, (c) whole-perm Stouffer Z.
            PASS = dBIC stays >6 AND tool-strat stays significant for ALL single-session
            removals. FAIL = any single removal collapses -> single-session artifact.

BLOCKING-2: TIME-VARYING / LATENT-STATE COX on Codex. Current Cox = per-tool rate only.
            Steelman static-heterogeneity null (arXiv 2604.15084): a session-PHASE /
            session-DIFFICULTY-stratified per-tool baseline where a "hard subtask" phase
            elevates ALL tool failure rates. We build (i) a session-phase (early/mid/late
            tertile) x tool baseline, and (ii) an HMM-style 2-state (easy/hard) latent
            difficulty modulation fit by EM, each MULTIPLYING the per-tool rate. Then
            recompute dBIC vs the Hawkes self-excitation model. If the latent-state Cox
            ABSORBS the Hawkes gain (dBIC <= 6), apparent self-excitation = time-varying
            heterogeneity, NOT genuine memory -> weakens H2.

BLOCKING-3 lives in ablations_gate.py (gate-stripped Hawkes for CC + Gemini).

DESCRIPTIVE arrival-process only.
"""
import sys, os, json, math, random, statistics, csv
from collections import defaultdict

E41 = os.path.expanduser('~/autonomous-research/experiments/2026-05-31/EXP-0041/impl')
E42 = os.path.expanduser('~/autonomous-research/experiments/2026-05-31/EXP-0042/impl')
sys.path.insert(0, E41); sys.path.insert(0, E42)
import burst_L3 as L3
import robust_L4 as L4

random.seed(20260601)
NPERM = 2500
EPS = L4.EPS

OUT = os.path.expanduser('~/autonomous-research/experiments/2026-06-01/EXP-0044/results')
os.makedirs(OUT, exist_ok=True)

def norm_cdf(z):
    return 0.5*(1.0+math.erf(z/math.sqrt(2.0)))
def stouffer(zs):
    return sum(zs)/math.sqrt(len(zs)) if zs else None

# ============================================================================
# BLOCKING-1: CODEX LOSO
# ============================================================================
def codex_loso():
    cx = L3.parse_codex()
    keys = list(cx.keys())
    # per-session precompute: seq, tools, whole-perm Z, tool-strat Z (shufflable only)
    sess = {}
    for k in keys:
        ev = cx[k]
        seq=[e[0] for e in ev]; tools=[e[1] for e in ev]
        if not (0<sum(seq)<len(seq)):
            sess[k]={'mixed':False,'n':len(seq),'fails':sum(seq)}; continue
        rw=L3.perm_runs_whole(seq,nperm=NPERM)
        rs=L3.perm_runs_tool_stratified(seq,tools,nperm=NPERM)
        sess[k]={'mixed':True,'n':len(seq),'fails':sum(seq),
                 'zw':rw['z_perm'] if rw else None,
                 'zs':rs['z_strat'] if rs else None,
                 'ps':rs['p_clustered'] if rs else None,
                 'shufflable':rs['shufflable'] if rs else False}
    mixed_keys=[k for k in keys if sess[k]['mixed']]

    # FULL (no drop) baselines
    full_haw = L4.cox_vs_hawkes('codex', cx)
    zs_all=[sess[k]['zs'] for k in mixed_keys if sess[k]['zs'] is not None]
    zw_all=[sess[k]['zw'] for k in mixed_keys if sess[k]['zw'] is not None]
    full_stouffer_strat = stouffer(zs_all)
    full_stouffer_whole = stouffer(zw_all)

    rows=[]
    for k in mixed_keys:
        sub = {kk:vv for kk,vv in cx.items() if kk!=k}
        h = L4.cox_vs_hawkes('codex', sub)
        zs_i=[sess[kk]['zs'] for kk in mixed_keys if kk!=k and sess[kk]['zs'] is not None]
        zw_i=[sess[kk]['zw'] for kk in mixed_keys if kk!=k and sess[kk]['zw'] is not None]
        Zs=stouffer(zs_i); Zw=stouffer(zw_i)
        rows.append({
            'dropped': os.path.basename(k),
            'dropped_n': sess[k]['n'], 'dropped_fails': sess[k]['fails'],
            'dropped_zs': round(sess[k]['zs'],3) if sess[k]['zs'] is not None else None,
            'n_sessions_left': h['n_sessions'], 'n_calls_left': h['n_calls'],
            'dBIC': h['delta_BIC_cox_minus_hawkes'],
            'hawkes_alpha': h['hawkes_alpha'], 'hawkes_beta': h['hawkes_beta'],
            'stouffer_strat': round(Zs,3) if Zs is not None else None,
            'stouffer_strat_p': round(norm_cdf(Zs),4) if Zs is not None else None,
            'stouffer_whole': round(Zw,3) if Zw is not None else None,
            'stouffer_whole_p': round(norm_cdf(Zw),5) if Zw is not None else None,
        })
    # sort by weakest (highest dBIC->lowest = worst for survival): show worst-collapse first
    rows_by_dbic = sorted(rows, key=lambda r: r['dBIC'])
    rows_by_strat = sorted(rows, key=lambda r: (r['stouffer_strat'] if r['stouffer_strat'] is not None else 0), reverse=True)

    worst_dbic = rows_by_dbic[0]
    worst_strat = rows_by_strat[0]
    all_dbic = [r['dBIC'] for r in rows]
    all_strat_p = [r['stouffer_strat_p'] for r in rows if r['stouffer_strat_p'] is not None]

    pass_dbic = all(d > 6 for d in all_dbic)
    pass_strat = all(p < 0.05 for p in all_strat_p)

    summary={
        'n_mixed_sessions': len(mixed_keys),
        'full_dBIC': full_haw['delta_BIC_cox_minus_hawkes'],
        'full_alpha': full_haw['hawkes_alpha'], 'full_beta': full_haw['hawkes_beta'],
        'full_n_calls': full_haw['n_calls'],
        'full_stouffer_strat': round(full_stouffer_strat,3) if full_stouffer_strat is not None else None,
        'full_stouffer_strat_p': round(norm_cdf(full_stouffer_strat),5) if full_stouffer_strat is not None else None,
        'full_stouffer_whole': round(full_stouffer_whole,3) if full_stouffer_whole is not None else None,
        'dBIC_min': min(all_dbic), 'dBIC_max': max(all_dbic),
        'dBIC_median': round(statistics.median(all_dbic),2),
        'strat_p_max': max(all_strat_p), 'strat_p_min': min(all_strat_p),
        'worst_dBIC_drop': worst_dbic,
        'worst_strat_drop': worst_strat,
        'PASS_dBIC_all_gt6': pass_dbic,
        'PASS_strat_all_sig': pass_strat,
        'BLOCKING1_PASS': pass_dbic and pass_strat,
    }
    return summary, rows_by_dbic

# ============================================================================
# BLOCKING-2: TIME-VARYING / LATENT-STATE COX  (steelman static-heterogeneity null)
# ----------------------------------------------------------------------------
# We extend the per-tool Cox baseline with a TIME-VARYING (session-phase) and a LATENT
# (HMM-style 2-state difficulty) multiplier on the per-tool rate. The question: does a
# richer STATIC/SLOW-VARYING heterogeneity model (no per-event self-excitation memory)
# fit as well as the Hawkes self-excitation model? If so, the "memory" is just
# time-varying rate. We compare BIC of (a) plain Cox, (b) phase-Cox, (c) HMM-Cox,
# (d) Hawkes. dBIC = BIC(best static-heterogeneity) - BIC(Hawkes). If <=6, Hawkes does
# not earn its memory params over the steelman null -> WEAKENS H2.
# ============================================================================
def build_sessions(parsed):
    out=[]
    for k,ev in parsed.items():
        s=[(e[0],e[1]) for e in ev]
        if 0<sum(e[0] for e in s)<len(s): out.append(s)
    return out

def phase_of(t, n, nphase=3):
    # tertile index 0..nphase-1 by call position
    if n<=1: return 0
    return min(nphase-1, int(nphase*t/n))

# (b) PHASE-COX: rate = sig( logit(tool_rate) + phase_effect[phase] ). phase_effect fit by
#     MLE (1D each) given per-tool baseline. Time-varying baseline, NO self-excitation.
def fit_phase_cox(sessions, tool_rates, nphase=3):
    # phase additive logit offsets; fit by coordinate ascent on Bernoulli LL
    phase_off=[0.0]*nphase
    def ll(off):
        s=0.0
        for sess in sessions:
            n=len(sess)
            for t,(err,tool) in enumerate(sess):
                ph=phase_of(t,n,nphase)
                eta=L4.logit(tool_rates.get(tool,EPS))+off[ph]
                p=L4.sig(eta)
                s+=math.log(p) if err else math.log(1-p)
        return s
    best=ll(phase_off)
    for _ in range(40):
        improved=False
        for ph in range(nphase):
            for d in (-0.4,-0.1,0.1,0.4):
                cand=phase_off[:]; cand[ph]+=d
                v=ll(cand)
                if v>best+1e-9:
                    best=v; phase_off=cand; improved=True
        if not improved: break
    k = len(tool_rates) + nphase   # per-tool rates + phase offsets (one redundant but conservative count)
    return best, k, phase_off

# (c) HMM-COX: 2 latent difficulty states (easy/hard). In state s, ALL tool rates are
#     scaled by exp(gamma_s) in logit space (gamma_easy<0, gamma_hard>0). Sticky transition
#     matrix. Fit by EM (forward-backward) over the per-session call sequence. NO per-event
#     self-excitation (the state is a slow latent, not triggered by individual failures).
def hmm_cox_loglik_and_fit(sessions, tool_rates, iters=60):
    # params: gamma[2] (logit offsets per state), trans 2x2 (sticky), init pi[2]
    gamma=[-0.7, 0.9]
    A=[[0.85,0.15],[0.25,0.75]]   # sticky
    pi=[0.6,0.4]
    def emis(err,tool,st):
        p=L4.sig(L4.logit(tool_rates.get(tool,EPS))+gamma[st])
        return p if err else (1-p)
    total_ll=0.0
    for _ in range(iters):
        # accumulators
        g0=[0.0,0.0]; g1=[0.0,0.0]   # for gamma re-est (weighted err/total per state)
        gerr=[0.0,0.0]; gtot=[0.0,0.0]
        A_num=[[1e-6,1e-6],[1e-6,1e-6]]
        pi_num=[1e-6,1e-6]
        total_ll=0.0
        for sess in sessions:
            T=len(sess)
            # forward
            alpha=[[0.0,0.0] for _ in range(T)]
            sc=[0.0]*T
            for st in range(2):
                alpha[0][st]=pi[st]*emis(sess[0][0],sess[0][1],st)
            sc[0]=sum(alpha[0]) or 1e-300
            for st in range(2): alpha[0][st]/=sc[0]
            for t in range(1,T):
                for st in range(2):
                    alpha[t][st]=sum(alpha[t-1][p]*A[p][st] for p in range(2))*emis(sess[t][0],sess[t][1],st)
                sc[t]=sum(alpha[t]) or 1e-300
                for st in range(2): alpha[t][st]/=sc[t]
            total_ll+=sum(math.log(x) for x in sc)
            # backward
            beta=[[0.0,0.0] for _ in range(T)]
            beta[T-1]=[1.0,1.0]
            for t in range(T-2,-1,-1):
                for st in range(2):
                    beta[t][st]=sum(A[st][p]*emis(sess[t+1][0],sess[t+1][1],p)*beta[t+1][p] for p in range(2))/ (sc[t+1] or 1e-300)
            # gamma posteriors
            for t in range(T):
                den=sum(alpha[t][st]*beta[t][st] for st in range(2)) or 1e-300
                for st in range(2):
                    g=alpha[t][st]*beta[t][st]/den
                    gtot[st]+=g
                    if sess[t][0]: gerr[st]+=g
                    if t==0: pi_num[st]+=g
                # xi for transitions
                if t<T-1:
                    for st in range(2):
                        for p in range(2):
                            xi=alpha[t][st]*A[st][p]*emis(sess[t+1][0],sess[t+1][1],p)*beta[t+1][p]/(sc[t+1] or 1e-300)
                            A_num[st][p]+=xi
        # M-step: re-estimate gamma_st so that mean predicted prob matches observed err-rate in state.
        # Approximate: set gamma_st via logit(observed weighted err rate) minus mean tool logit.
        for st in range(2):
            if gtot[st]>1e-6:
                obs=min(max(gerr[st]/gtot[st],EPS),1-EPS)
                gamma[st]=L4.logit(obs)  # absorb baseline; tool_rates still add per-call variation
        # keep ordering easy<hard
        if gamma[0]>gamma[1]: gamma=[gamma[1],gamma[0]]
        for st in range(2):
            ssum=sum(A_num[st])
            A[st]=[A_num[st][p]/ssum for p in range(2)]
        psum=sum(pi_num); pi=[pi_num[st]/psum for st in range(2)]
    # k params: per-tool rates + 2 gamma + 2 free transition + 1 free init
    k=len(tool_rates)+2+2+1
    return total_ll, k, {'gamma':gamma,'A':A,'pi':pi}

def latent_cox_vs_hawkes(name, parsed):
    sessions=build_sessions(parsed)
    N=sum(len(s) for s in sessions)
    rates=L4.cox_baseline_rates(sessions)
    # plain cox
    ll_cox=L4.cox_only_loglik(sessions,rates); k_cox=len(rates)
    bic_cox=-2*ll_cox+k_cox*math.log(N)
    # phase cox
    ll_ph,k_ph,phoff=fit_phase_cox(sessions,rates,nphase=3)
    bic_ph=-2*ll_ph+k_ph*math.log(N)
    # hmm cox
    ll_hmm,k_hmm,hmmp=hmm_cox_loglik_and_fit(sessions,rates)
    bic_hmm=-2*ll_hmm+k_hmm*math.log(N)
    # hawkes
    ll_haw,alpha,beta=L4.fit_hawkes(sessions,rates); k_haw=k_cox+2
    bic_haw=-2*ll_haw+k_haw*math.log(N)
    best_static_bic=min(bic_cox,bic_ph,bic_hmm)
    best_static_name=['plain_cox','phase_cox','hmm_cox'][[bic_cox,bic_ph,bic_hmm].index(best_static_bic)]
    dbic_vs_best_static = best_static_bic - bic_haw
    return {
        'harness':name,'n_sessions':len(sessions),'n_calls':N,'n_tools':k_cox,
        'cox_logL':round(ll_cox,2),'cox_BIC':round(bic_cox,2),
        'phase_cox_logL':round(ll_ph,2),'phase_cox_k':k_ph,'phase_cox_BIC':round(bic_ph,2),'phase_offsets':[round(x,3) for x in phoff],
        'hmm_cox_logL':round(ll_hmm,2),'hmm_cox_k':k_hmm,'hmm_cox_BIC':round(bic_hmm,2),
        'hmm_gamma':[round(x,3) for x in hmmp['gamma']],'hmm_A':[[round(y,3) for y in r] for r in hmmp['A']],
        'hawkes_logL':round(ll_haw,2),'hawkes_BIC':round(bic_haw,2),'hawkes_alpha':round(alpha,3),'hawkes_beta':round(beta,3),
        'best_static_model':best_static_name,'best_static_BIC':round(best_static_bic,2),
        'dBIC_bestStatic_minus_hawkes':round(dbic_vs_best_static,2),
        'hawkes_survives_steelman': dbic_vs_best_static > 6,
    }

def main():
    print("="*70); print("BLOCKING-1: CODEX LOSO"); print("="*70)
    b1, b1rows = codex_loso()
    for k,v in b1.items():
        if k not in ('worst_dBIC_drop','worst_strat_drop'): print(f"   {k:28}: {v}")
    print("   worst_dBIC_drop:", b1['worst_dBIC_drop'])
    print("   worst_strat_drop:", b1['worst_strat_drop'])

    print("\n"+"="*70); print("BLOCKING-2: LATENT-STATE / TIME-VARYING COX vs HAWKES"); print("="*70)
    cc=L3.parse_cc(); cx=L3.parse_codex(); gm=L3.parse_gemini()
    b2=[]
    for nm,p in [('codex',cx),('claude_code',cc),('gemini',gm)]:
        r=latent_cox_vs_hawkes(nm,p); b2.append(r)
        print(f"  --- {nm} ---")
        for k in ('n_calls','cox_BIC','phase_cox_BIC','phase_offsets','hmm_cox_BIC','hmm_gamma',
                  'hawkes_BIC','hawkes_alpha','best_static_model','best_static_BIC',
                  'dBIC_bestStatic_minus_hawkes','hawkes_survives_steelman'):
            print(f"     {k:30}: {r[k]}")

    # write outputs
    with open(os.path.join(OUT,'codex_loso.csv'),'w',newline='') as fh:
        cols=list(b1rows[0].keys()); w=csv.DictWriter(fh,fieldnames=cols); w.writeheader()
        for r in b1rows: w.writerow(r)
    with open(os.path.join(OUT,'latent_cox_vs_hawkes.csv'),'w',newline='') as fh:
        cols=list(b2[0].keys()); w=csv.DictWriter(fh,fieldnames=cols,extrasaction='ignore'); w.writeheader()
        for r in b2: w.writerow(r)
    bundle={'blocking1_codex_loso':b1,'blocking2_latent_cox':b2}
    with open(os.path.join(OUT,'ablations_b1_b2.json'),'w') as fh:
        json.dump(bundle,fh,indent=2,default=str)
    print(f"\n-> {OUT}/codex_loso.csv , latent_cox_vs_hawkes.csv , ablations_b1_b2.json")
    return bundle

if __name__=='__main__':
    main()
