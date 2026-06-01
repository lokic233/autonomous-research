#!/usr/bin/env python3
"""
EXP-0052 (L0, CPU, stdlib-only) — CLAIM-0016 / PROJ-0006.
Agent-Event-Phase Desynchronization Tax in BATCH Speculative Decoding.

CPU Monte-Carlo BATCH-ROUND min-bound model on the EXP-0046 top-1-agreement acceptance proxy.
REUSES EXP-0046 corpus parsers (cc_streams/codex_streams) + trigram predictor verbatim (imported).
Pre-registration: impl/preregistration.md (LOCKED 2026-06-01T16:07:18Z, BEFORE this run).

Scope guard: phase = batch-GROUPING key only (boundary_type + distance). NOT a standalone dAUC
discriminator (that died DEAD-0011/0012). Success = cross-sequence min-bound GOODPUT recovery only.
"""
import json, os, sys, math, random, time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
EXP46 = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'EXP-0046', 'impl')
sys.path.insert(0, EXP46)
import acceptance_proxy as ap   # reuse cc_streams, codex_streams, build_ngram, make_predictor

SEED = 20260601
B_BOOT = 2000
N_PERM = 1000
W = 32
K_TRANS = 2
K_RES = 8
GRID_B = [4, 8, 16, 32]
GRID_GAMMA = [4, 8]
PRIMARY_B = 8
PRIMARY_GAMMA = 8
PHASE_RANK = {'TRANSITION': 0, 'RESUMPTION': 1, 'FREE_FORM': 2}

def phase_of(boundary_type, d):
    if boundary_type == 'tool' and 1 <= d <= K_TRANS:
        return 'TRANSITION'
    if (boundary_type == 'tool' and K_TRANS < d <= K_RES) or (boundary_type == 'user' and 1 <= d <= K_RES):
        return 'RESUMPTION'
    return 'FREE_FORM'

def dbucket(d):
    if d <= 0: return 0
    if d <= 8: return d
    return 9

def session_acc_phase(stream, predict):
    toks = [t for _, t in stream]; ori = [o for o, _ in stream]
    n = len(toks); last_btype = None; d = 0
    acc = []; ph = []; db = []
    for i in range(n):
        o = ori[i]; t = toks[i]
        if o == 'tool': last_btype = 'tool'; d = 0
        elif o == 'user': last_btype = 'user'; d = 0
        elif o == 'asst':
            d += 1
            c2 = toks[i-2] if i >= 2 else None
            c1 = toks[i-1] if i >= 1 else None
            top1, _ = predict(c2, c1)
            acc.append(1 if top1 == t else 0)
            ph.append(phase_of(last_btype, d)); db.append(dbucket(d))
    return acc, ph, db

def build_rounds(acc, ph, db, gamma):
    M = len(acc)
    if M == 0: return []
    sess_diff = sum(acc) / M
    rounds = []; p = 0
    while p < M:
        run = 0
        while run < gamma and (p + run) < M and acc[p + run] == 1:
            run += 1
        accepted_len = run
        lo = max(0, p - W)
        rmean = (sum(acc[lo:p]) / (p - lo)) if p > lo else sess_diff
        rounds.append({'al': accepted_len, 'ph': ph[p], 'db': db[p], 'rmean': rmean, 'diff': sess_diff})
        p += accepted_len + 1
    return rounds

def chunk_min_mean(als, B):
    nfull = len(als) // B
    if nfull == 0: return None
    s = 0.0
    for c in range(nfull):
        s += min(als[c*B:(c+1)*B])
    return s / nfull

def orderings(rounds, rng):
    """Precompute al-arrays under each policy ordering ONCE (independent of B). Returns dict + mean_al."""
    n = len(rounds)
    al = [r['al'] for r in rounds]
    mean_al = sum(al) / n if n else 0.0
    idx = list(range(n))
    ridx = idx[:]; rng.shuffle(ridx)
    o_random = [al[i] for i in ridx]
    o_static = [al[i] for i in sorted(idx, key=lambda i: rounds[i]['diff'])]
    o_sham = [al[i] for i in sorted(idx, key=lambda i: rounds[i]['rmean'])]
    o_phase = [al[i] for i in sorted(idx, key=lambda i: PHASE_RANK[rounds[i]['ph']])]
    return {'mean_al': mean_al, 'random': o_random, 'static': o_static, 'sham': o_sham, 'phase': o_phase}

def pctl(vals, p):
    s = sorted(v for v in vals if v is not None)
    if not s: return None
    pos = p * (len(s) - 1); lo = int(math.floor(pos)); hi = int(math.ceil(pos)); fr = pos - lo
    return s[lo]*(1-fr) + s[hi]*fr

def holm(pmap):
    items = sorted(pmap.items(), key=lambda kv: kv[1])
    m = len(items); out = {}; running = 0.0
    for i, (k, p) in enumerate(items):
        adj = min(1.0, (m - i) * p); running = max(running, adj)
        out[k] = (running, running < 0.05)
    return out

def analyze_corpus(name, sessions):
    keys = sorted(sessions.keys())
    train = []; test = []
    for kp in keys:
        h = sum(ord(ch) for ch in os.path.basename(kp))
        (train if h % 2 == 0 else test).append(kp)
    if len(test) < 5 or len(train) < 5:
        train = keys[::2]; test = keys[1::2]
    uni, bi, tri = ap.build_ngram([sessions[k] for k in train])
    predict = ap.make_predictor(uni, bi, tri)
    sess_acc = {}
    for k in test:
        acc, ph, db = session_acc_phase(sessions[k], predict)
        if len(acc) >= 10: sess_acc[k] = (acc, ph, db)
    test = [k for k in test if k in sess_acc]
    rounds_by_gamma = {g: {k: build_rounds(*sess_acc[k], gamma=g) for k in test} for g in GRID_GAMMA}

    out = {'corpus': name, 'n_train': len(train), 'n_test': len(test), 'tokenizer': 'stdlib-regex',
           'total_rounds_by_gamma': {g: sum(len(v) for v in rounds_by_gamma[g].values()) for g in GRID_GAMMA},
           'cells': {}}

    for gamma in GRID_GAMMA:
        rbg = rounds_by_gamma[gamma]
        flat = [r for k in test for r in rbg[k]]
        rng = random.Random(SEED)
        O = orderings(flat, rng)
        # point estimates per B
        cellpt = {}
        for B in GRID_B:
            gr = chunk_min_mean(O['random'], B); gs = chunk_min_mean(O['static'], B)
            gh = chunk_min_mean(O['sham'], B); gp = chunk_min_mean(O['phase'], B)
            cellpt[B] = {'mean_al': O['mean_al'], 'g_random': gr, 'g_static': gs, 'g_sham': gh, 'g_phase': gp,
                         'delta1_phase_minus_static': gp - gs, 'delta2_phase_minus_sham': gp - gh,
                         'tax': (O['mean_al'] - gr)/O['mean_al'] if O['mean_al'] > 0 else None}
        # cluster bootstrap by session — orderings rebuilt once per resample, reused across B
        b_d1 = {B: [] for B in GRID_B}; b_d2 = {B: [] for B in GRID_B}; b_tax = {B: [] for B in GRID_B}
        tkeys = test; nS = len(tkeys); brng = random.Random(SEED + 1)
        for _ in range(B_BOOT):
            samp = [tkeys[brng.randrange(nS)] for _ in range(nS)]
            bflat = [r for k in samp for r in rbg[k]]
            if len(bflat) < max(GRID_B): continue
            BO = orderings(bflat, brng)
            for B in GRID_B:
                gr = chunk_min_mean(BO['random'], B); gs = chunk_min_mean(BO['static'], B)
                gh = chunk_min_mean(BO['sham'], B); gp = chunk_min_mean(BO['phase'], B)
                if None in (gr, gs, gh, gp): continue
                b_d1[B].append(gp - gs); b_d2[B].append(gp - gh)
                if BO['mean_al'] > 0: b_tax[B].append((BO['mean_al'] - gr)/BO['mean_al'])
        for B in GRID_B:
            c = cellpt[B]
            c.update({'B': B, 'gamma': gamma,
                      'delta1_ci': [pctl(b_d1[B], 0.025), pctl(b_d1[B], 0.975)],
                      'delta1_p': (sum(1 for v in b_d1[B] if v <= 0) + 1)/(len(b_d1[B]) + 1),
                      'delta2_ci': [pctl(b_d2[B], 0.025), pctl(b_d2[B], 0.975)],
                      'tax_ci': [pctl(b_tax[B], 0.025), pctl(b_tax[B], 0.975)]})
            out['cells']['B%d_g%d' % (B, gamma)] = c

    # RE-A4 permutation null at PRIMARY cell
    rbg = rounds_by_gamma[PRIMARY_GAMMA]
    flat2 = []
    for k in test:
        for r in rbg[k]:
            rr = dict(r); rr['sess'] = k; flat2.append(rr)
    prng = random.Random(SEED)
    Oprim = orderings(flat2, prng)
    g_static_fixed = chunk_min_mean(Oprim['static'], PRIMARY_B)
    g_phase_obs = chunk_min_mean(Oprim['phase'], PRIMARY_B)
    d1_obs = g_phase_obs - g_static_fixed
    strata = defaultdict(list)
    for i, r in enumerate(flat2): strata[(r['sess'], r['db'])].append(i)
    base_al = [r['al'] for r in flat2]
    perm_rng = random.Random(SEED + 2); d1_perm = []
    for _ in range(N_PERM):
        perm_ph = [None]*len(flat2)
        for stratum, idxs in strata.items():
            labels = [flat2[i]['ph'] for i in idxs]; perm_rng.shuffle(labels)
            for j, i in enumerate(idxs): perm_ph[i] = labels[j]
        pidx = sorted(range(len(flat2)), key=lambda i: PHASE_RANK[perm_ph[i]])
        gpp = chunk_min_mean([base_al[i] for i in pidx], PRIMARY_B)
        d1_perm.append(gpp - g_static_fixed)
    p_perm = (sum(1 for v in d1_perm if v >= d1_obs) + 1)/(N_PERM + 1)
    out['perm_null'] = {'cell': 'B%d_g%d' % (PRIMARY_B, PRIMARY_GAMMA), 'd1_obs': d1_obs,
                        'd1_perm_mean': sum(d1_perm)/len(d1_perm), 'd1_perm_p975': pctl(d1_perm, 0.975),
                        'p': p_perm, 'survives': p_perm < 0.05}

    # RE-A6 overhead timing
    flat = [r for k in test for r in rbg[k]]; nflat = len(flat); reps = 7
    t_class = []
    for _ in range(reps):
        t0 = time.perf_counter()
        for r in flat: _ = PHASE_RANK[r['ph']]
        t_class.append(time.perf_counter() - t0)
    t_group = []
    for _ in range(reps):
        t0 = time.perf_counter()
        _ = sorted(range(nflat), key=lambda i: PHASE_RANK[flat[i]['ph']])
        t_group.append(time.perf_counter() - t0)
    med = lambda x: sorted(x)[len(x)//2]
    overhead_per_round = (med(t_class) + med(t_group)) / max(1, nflat)
    out['overhead'] = {'n_rounds': nflat, 'median_class_s': med(t_class), 'median_group_s': med(t_group),
                       'overhead_s_per_round': overhead_per_round, 'delta1_primary': d1_obs,
                       'net_tokens_at_Ttok': {'%dms' % t: d1_obs - overhead_per_round/(t/1000.0) for t in (1,5,10)}}
    return out


# ====================== EXPLORATORY (NON-PREREGISTERED) REGIME SWEEP ======================
# Diagnostic ONLY: the pre-registered analysis uses the raw proxy bits (sec 5). At proxy
# acceptance ~0.28 the batch min-bound collapses to ~0 for B>=4 under EVERY policy, so the
# metric loses resolving power. This sweep lifts acceptance to alpha_base in a resolvable
# regime while PRESERVING the REAL between-session difficulty spread, the REAL per-phase
# deviations, and the REAL phase MIX (~97.5% FREE_FORM). It tests whether phase composition
# could EVER beat static-task-difficulty grouping. NOT used for the pre-registered verdict;
# clearly labeled exploratory per the locked prereg (no post-hoc edit to the prereg or to RE-A1..A7).
def regime_sweep(name, sessions, alpha_bases=(0.5, 0.6, 0.7, 0.8, 0.9), B=PRIMARY_B, gamma=PRIMARY_GAMMA):
    keys = sorted(sessions.keys()); train = []; test = []
    for kp in keys:
        h = sum(ord(c) for c in os.path.basename(kp)); (train if h % 2 == 0 else test).append(kp)
    if len(test) < 5 or len(train) < 5: train = keys[::2]; test = keys[1::2]
    uni, bi, tri = ap.build_ngram([sessions[k] for k in train]); predict = ap.make_predictor(uni, bi, tri)
    sa = {}
    for k in test:
        acc, ph, db = session_acc_phase(sessions[k], predict)
        if len(acc) >= 10: sa[k] = (acc, ph, db)
    test = list(sa.keys())
    alln = 0; alla = 0; phn = defaultdict(int); pha = defaultdict(int); sess_diff = {}
    for k in test:
        acc, ph, db = sa[k]; sd = sum(acc)/len(acc); sess_diff[k] = sd
        alln += len(acc); alla += sum(acc)
        for a, p in zip(acc, ph): phn[p] += 1; pha[p] += a
    glob = alla/alln
    phase_dev = {p: (pha[p]/phn[p] - glob) for p in phn}
    phase_mix = {p: phn[p]/alln for p in phn}
    # real round skeleton (session, phase) preserving phase mix + session structure
    skel = {k: [(r['ph']) for r in build_rounds(*sa[k], gamma=gamma)] for k in test}
    rng = random.Random(SEED + 7)
    cells = []
    for ab in alpha_bases:
        # synthesize accepted_len per round from alpha_eff = base + (sess_diff-glob) + phase_dev (BOTH confounds, real magnitudes)
        sess_rounds = {}
        for k in test:
            rr = []
            recent = []
            for ph in skel[k]:
                aeff = ab + (sess_diff[k] - glob) + phase_dev.get(ph, 0.0)
                aeff = 0.02 if aeff < 0.02 else (0.98 if aeff > 0.98 else aeff)
                run = 0
                while run < gamma:
                    if rng.random() < aeff: run += 1
                    else: break
                recent.append(run); 
                if len(recent) > W: recent.pop(0)
                rmean = sum(recent[:-1])/(len(recent)-1) if len(recent) > 1 else sess_diff[k]
                rr.append({'al': run, 'ph': ph, 'rmean': rmean, 'diff': sess_diff[k]})
            sess_rounds[k] = rr
        flat = [r for k in test for r in sess_rounds[k]]
        prng = random.Random(SEED)
        O = orderings(flat, prng)
        gr = chunk_min_mean(O['random'], B); gs = chunk_min_mean(O['static'], B)
        gh = chunk_min_mean(O['sham'], B); gp = chunk_min_mean(O['phase'], B)
        d1 = gp - gs; d2 = gp - gh
        # light cluster bootstrap by session (resample synthesized rounds; no re-synth)
        bd1 = []; bd2 = []; nS = len(test); brng = random.Random(SEED + 8)
        for _ in range(500):
            samp = [test[brng.randrange(nS)] for _ in range(nS)]
            bflat = [r for k in samp for r in sess_rounds[k]]
            if len(bflat) < B: continue
            BO = orderings(bflat, brng)
            bgs = chunk_min_mean(BO['static'], B); bgh = chunk_min_mean(BO['sham'], B); bgp = chunk_min_mean(BO['phase'], B)
            if None in (bgs, bgh, bgp): continue
            bd1.append(bgp - bgs); bd2.append(bgp - bgh)
        cells.append({'alpha_base': ab, 'mean_al': O['mean_al'],
                      'g_random': gr, 'g_static': gs, 'g_sham': gh, 'g_phase': gp,
                      'delta1_phase_minus_static': d1, 'delta1_ci': [pctl(bd1, 0.025), pctl(bd1, 0.975)],
                      'delta2_phase_minus_sham': d2, 'delta2_ci': [pctl(bd2, 0.025), pctl(bd2, 0.975)],
                      'tax': (O['mean_al']-gr)/O['mean_al'] if O['mean_al'] > 0 else None})
    return {'corpus': name, 'B': B, 'gamma': gamma, 'global_acc': glob,
            'phase_dev': phase_dev, 'phase_mix': phase_mix,
            'between_session_diff_std': (sum((sess_diff[k]-sum(sess_diff.values())/len(sess_diff))**2 for k in test)/len(test))**0.5,
            'cells': cells}


def main():
    t_start = time.perf_counter()
    print("parsing corpora (reusing EXP-0046 parsers)...")
    cc = ap.cc_streams(); print("  CC usable sessions:", len(cc))
    cx = ap.codex_streams(); print("  Codex usable sessions:", len(cx))
    results = []
    for name, sess in [('claude_code', cc), ('codex', cx)]:
        if len(sess) < 10:
            print("  SKIP %s (too few sessions=%d)" % (name, len(sess))); continue
        print("analyzing", name, "..."); sys.stdout.flush()
        results.append(analyze_corpus(name, sess))
        print("  done", name, "%.1fs" % (time.perf_counter()-t_start)); sys.stdout.flush()

    pmap = {}
    for r in results:
        for ck, cell in r['cells'].items():
            pmap['%s:%s' % (r['corpus'], ck)] = cell['delta1_p']
    hp = holm(pmap)
    holm_out = {k: {'p_raw': pmap[k], 'p_holm': hp[k][0], 'sig': hp[k][1]} for k in pmap}

    # EXPLORATORY regime sweep (diagnostic; not part of pre-registered verdict)
    print("\nEXPLORATORY regime sweep..."); sys.stdout.flush()
    sweeps = []
    for name, sess in [('claude_code', cc), ('codex', cx)]:
        if len(sess) >= 10:
            sweeps.append(regime_sweep(name, sess))
    rdir0 = os.path.join(os.path.dirname(HERE), 'results'); os.makedirs(rdir0, exist_ok=True)
    with open(os.path.join(rdir0, 'exp_regime_sweep.json'), 'w') as fh:
        json.dump(sweeps, fh, indent=2, default=str)

    rdir = os.path.join(os.path.dirname(HERE), 'results'); os.makedirs(rdir, exist_ok=True)
    payload = {'results': results, 'holm_grid': holm_out, 'family_size': len(pmap),
               'primary_cell': 'B%d_g%d' % (PRIMARY_B, PRIMARY_GAMMA),
               'seed': SEED, 'B_boot': B_BOOT, 'n_perm': N_PERM,
               'wall_s': time.perf_counter()-t_start, 'regime_sweep': sweeps}
    with open(os.path.join(rdir, 'batch_round_model.json'), 'w') as fh:
        json.dump(payload, fh, indent=2, default=str)

    print("\n" + "="*78)
    print("FAMILY SIZE (RE-A5):", len(pmap), " primary cell:", payload['primary_cell'])
    for r in results:
        c = r['cells'].get(payload['primary_cell'])
        print("\n" + "="*78)
        print("CORPUS:", r['corpus'], "(train=%d test=%d, rounds@g8=%s)" %
              (r['n_train'], r['n_test'], r['total_rounds_by_gamma'].get(8)))
        if c:
            print("  PRIMARY B=%d gamma=%d:" % (c['B'], c['gamma']))
            print("    mean_accepted_len = %.4f" % c['mean_al'])
            print("    goodput  random=%.4f static=%.4f sham=%.4f phase=%.4f" %
                  (c['g_random'], c['g_static'], c['g_sham'], c['g_phase']))
            print("    RE-A1 delta1(phase-static) = %+.4f  CI[%+.4f,%+.4f]  p=%.4f" %
                  (c['delta1_phase_minus_static'], c['delta1_ci'][0], c['delta1_ci'][1], c['delta1_p']))
            print("    RE-A2 delta2(phase-sham)   = %+.4f  CI[%+.4f,%+.4f]" %
                  (c['delta2_phase_minus_sham'], c['delta2_ci'][0], c['delta2_ci'][1]))
            print("    RE-A3 tax = %.4f (%.1f%%)  CI[%.4f,%.4f]" %
                  (c['tax'], 100*c['tax'], c['tax_ci'][0], c['tax_ci'][1]))
        pn = r['perm_null']; print("    RE-A4 perm: d1_obs=%+.4f perm_mean=%+.4f p975=%+.4f p=%.4f survives=%s" %
              (pn['d1_obs'], pn['d1_perm_mean'], pn['d1_perm_p975'], pn['p'], pn['survives']))
        ov = r['overhead']; print("    RE-A6 overhead/round=%.3e s  net @1ms=%+.4f @5ms=%+.4f @10ms=%+.4f" %
              (ov['overhead_s_per_round'], ov['net_tokens_at_Ttok']['1ms'],
               ov['net_tokens_at_Ttok']['5ms'], ov['net_tokens_at_Ttok']['10ms']))
    print("\n  RE-A5 Holm grid (RE-A1 delta1):")
    for k in sorted(holm_out):
        h = holm_out[k]; print("    %-22s p_raw=%.4f p_holm=%.4f sig=%s" % (k, h['p_raw'], h['p_holm'], h['sig']))
    print("\n  EXPLORATORY regime sweep (phase mix ~97.5%% FREE_FORM; preserves real difficulty spread + phase dev):")
    for sw in sweeps:
        print("   CORPUS %s  between-session diff std=%.4f  phase_dev=%s" % (sw['corpus'], sw['between_session_diff_std'],
              {k: round(v,4) for k,v in sw['phase_dev'].items()}))
        for c in sw['cells']:
            print("     alpha_base=%.1f mean_al=%.3f static=%.3f sham=%.3f phase=%.3f | d1(phase-static)=%+.4f CI[%+.4f,%+.4f] d2(phase-sham)=%+.4f CI[%+.4f,%+.4f]" % (
                c['alpha_base'], c['mean_al'], c['g_static'], c['g_sham'], c['g_phase'],
                c['delta1_phase_minus_static'], c['delta1_ci'][0], c['delta1_ci'][1],
                c['delta2_phase_minus_sham'], c['delta2_ci'][0], c['delta2_ci'][1]))
    print("\nwall=%.1fs  wrote %s" % (payload['wall_s'], os.path.join(rdir, 'batch_round_model.json')))
    return payload

if __name__ == '__main__':
    main()
