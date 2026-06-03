#!/usr/bin/env python3
"""EXP-0037 / CLAIM-0040 — early-commit on streaming tool-result prefix.
L0: CPU-only, stdlib-only, SERIAL. Analytic + Monte-Carlo trace sim.
Honest pipeline: negatives are wins. Trust on-disk CSVs."""
import random, math, csv, os, itertools, statistics

ART = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ART, "results")
os.makedirs(RES, exist_ok=True)

# ---- content position samplers ----
def sample_q(regime, rng):
    if regime == "front":  # Beta(1.5,6) mean~0.20
        return rng.betavariate(1.5, 6.0)
    if regime == "uniform":
        return rng.random()
    if regime == "tail":   # Beta(6,1.5) mean~0.80
        return rng.betavariate(6.0, 1.5)
    raise ValueError(regime)

def draw_regime(f_fl, remainder_mix, rng):
    # remainder_mix: fraction of the (1-f_fl) that is uniform vs tail
    u = rng.random()
    if u < f_fl:
        return "front"
    # split remainder
    r = (u - f_fl) / max(1e-9, (1 - f_fl))
    if remainder_mix == "uniform_heavy":
        return "uniform" if r < 0.7 else "tail"
    else:  # tail_heavy
        return "tail" if r < 0.7 else "uniform"

# ---- detector ----
# Smart detector: tries to fire just after the answer arrives. Parameterized by acc.
# On each result, with prob = base_fire it ATTEMPTS to fire (only attempts when its prefix-estimate
# thinks answer present). Accuracy `acc` governs whether its fire position is correct (d>=q) or
# premature (d<q). We model: detector observes q with noise; fires at d = q + eps if it BELIEVES
# answer arrived. Classification correctness = acc.
EPS = 0.02

def simulate_cell(f_fl, remainder_mix, acc, rho, W, n, seed, fire_mode="smart", d_fixed=0.3):
    """Return dict of aggregate metrics. T_step=1.0 (unit). T_stream = rho."""
    rng = random.Random(seed * 100003 + hash((f_fl, remainder_mix, round(acc,3), rho, W, fire_mode, d_fixed)) % 100003)
    T_step = 1.0
    T_stream = rho * T_step
    L_base = T_stream + T_step

    sum_early = 0.0
    n_fire = n_win = n_wrong = n_hold = 0
    n_front = 0
    for _ in range(n):
        regime = draw_regime(f_fl, remainder_mix, rng)
        q = sample_q(regime, rng)
        if regime == "front":
            n_front += 1
        # detector decision
        if fire_mode == "blind":
            # fires at fixed d regardless of content (no detectability)
            d = d_fixed
            fires = True
            # correctness purely by luck: d>=q ?
            correct = (d >= q)
        else:
            # smart: detector classifies whether answer is in prefix.
            # It only fires if it believes so. acc = P(correct classification).
            # Correct classification on a result whose answer IS reachably-early -> fire at d=q+eps (WIN).
            # Misclassification -> either fire too early (d<q, WRONG) or hold when it should fire (miss, no loss).
            # We collapse: with prob acc detector is "right" about this result.
            right = (rng.random() < acc)
            # ground truth: is answer early enough to be worth committing? treat q<=0.5 as 'commit-worthy'
            worth = (q <= 0.5)
            if right:
                if worth:
                    d = min(q + EPS, 1.0); fires = True; correct = True
                else:
                    fires = False; d = None; correct = None  # correctly holds on tail-heavy
            else:  # detector is wrong about this result
                if worth:
                    fires = False; d = None; correct = None  # missed a winnable one (no loss, no gain)
                else:
                    # thinks tail-heavy answer is early -> fires prematurely
                    d = min(q * 0.5 + EPS, 1.0); fires = True; correct = (d >= q)  # almost surely d<q -> WRONG
        if fires:
            n_fire += 1
            if correct:
                n_win += 1
                L = d * T_stream + T_step
            else:
                n_wrong += 1
                L = L_base + W * T_step
        else:
            n_hold += 1
            L = L_base
        sum_early += L

    E_early = sum_early / n
    dL = L_base - E_early
    pct = 100.0 * dL / L_base
    p_correct_given_fire = (n_win / n_fire) if n_fire else float('nan')
    # break-even: per-fire, average d among wins; use mean d ~ for front answer pos.
    # analytic p* using representative d (mean fire pos among wins)
    return {
        "f_fl": f_fl, "remainder_mix": remainder_mix, "acc": acc, "rho": rho, "W": W,
        "fire_mode": fire_mode, "d_fixed": d_fixed, "seed": seed, "n": n,
        "L_base": round(L_base,4), "E_early": round(E_early,4),
        "dL": round(dL,4), "pct_reduction": round(pct,3),
        "n_fire": n_fire, "n_win": n_win, "n_wrong": n_wrong, "n_hold": n_hold,
        "frac_front_actual": round(n_front/n,4),
        "p_correct_given_fire": round(p_correct_given_fire,4) if n_fire else "",
        "win": 1 if dL > 0 else 0,
    }

def breakeven_pstar(d, rho, W):
    """p* = W*T_step / ((1-d)*T_stream + W*T_step), T_step=1, T_stream=rho."""
    G = (1 - d) * rho
    P = W * 1.0
    return P / (G + P)

if __name__ == "__main__":
    seeds = [0,1,2,3,4,5,6]
    f_fls = [0.1,0.3,0.5,0.7,0.9]
    mixes = ["uniform_heavy","tail_heavy"]
    accs  = [0.5,0.6,0.7,0.8,0.9,0.95,1.0]
    rhos  = [0.25,0.5,1,2,4,8]
    Ws    = [0.5,1.0,2.0]
    N = 4000

    rows = []
    # MAIN smart sweep
    for f_fl, mix, acc, rho, W, seed in itertools.product(f_fls, mixes, accs, rhos, Ws, seeds):
        rows.append(simulate_cell(f_fl, mix, acc, rho, W, N, seed, fire_mode="smart"))
    main_csv = os.path.join(RES, "sweep_smart.csv")
    with open(main_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("WROTE", main_csv, len(rows), "rows")

    # BLIND detectability ablation (no signal: fixed d, acc irrelevant)
    brows = []
    for f_fl, mix, rho, W, d_fixed, seed in itertools.product(f_fls, mixes, rhos, Ws, [0.2,0.3,0.5], seeds):
        brows.append(simulate_cell(f_fl, mix, 0.5, rho, W, N, seed, fire_mode="blind", d_fixed=d_fixed))
    blind_csv = os.path.join(RES, "sweep_blind.csv")
    with open(blind_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(brows[0].keys())); w.writeheader(); w.writerows(brows)
    print("WROTE", blind_csv, len(brows), "rows")

    # ANALYTIC break-even table
    erows = []
    for d, rho, W in itertools.product([0.1,0.2,0.3,0.5,0.7], rhos, Ws):
        erows.append({"d_fire": d, "rho": rho, "W": W,
                      "gain_G": round((1-d)*rho,4), "penalty_P": round(W,4),
                      "pstar": round(breakeven_pstar(d, rho, W),4)})
    be_csv = os.path.join(RES, "breakeven.csv")
    with open(be_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(erows[0].keys())); w.writeheader(); w.writerows(erows)
    print("WROTE", be_csv, len(erows), "rows")
    print("DONE")
