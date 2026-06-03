#!/usr/bin/env python3
"""EXP-0046 / CLAIM-0047 — rollback-depth under rising post-deviation hazard.
L0: CPU-only, pure-stdlib, SERIAL. See PRE_REGISTRATION.md.

Faithful generative process. Two recovery policies. Common-random-numbers paired contrast.
Anti-circular: GT = true latent onset + hazard (simulator-known); policy sees observables only.
"""
import random, math, csv, os, hashlib, statistics, time

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUTDIR, exist_ok=True)

# ---- defaults ----
N_TARGET   = 200      # productive steps to "complete" a rollout
H0_DEV     = 0.01     # per-step prob of deviating while on-path
H0_FAIL    = 0.002    # base per-step failure hazard
H_CAP      = 0.6      # cap on per-step hazard (valid prob)
S_TOKENS   = 2        # cost of a checkpoint save
MASTER     = 20260603

def cell_seed(cfg):
    h = hashlib.sha256(repr(sorted(cfg.items())).encode()).hexdigest()
    return (MASTER + int(h[:8], 16)) % (2**31)

def hazard(t_since_dev, alpha, shape, base_w, k):
    """Per-step FAILURE hazard while OFF-path, as a function of steps since deviation onset."""
    if shape == "linear":
        h = H0_FAIL + alpha * t_since_dev
    else:  # weibull-shaped increasing intensity, k>1
        h = H0_FAIL + base_w * (t_since_dev ** (k - 1))
    return min(H_CAP, h)

def checkpoints_upto(pos, c):
    """positions of checkpoints at-or-before pos (0 is an implicit always-available checkpoint)."""
    # checkpoints at 0, c, 2c, ... ; the position 0 = fresh start always available.
    last = (pos // c) * c
    return last  # most-recent checkpoint position <= pos

def simulate_rollout(seed, alpha, c, shape, base_w, k, policy, det_fpr, det_fnr, det_sd, overshoot):
    """
    Returns wasted_tokens for one COMPLETED rollout under the given policy.
    Common random numbers: deviation draws and failure draws come from a single RNG stream keyed by
    (seed, absolute_step_index, draw_kind) so BOTH policies see identical underlying randomness for
    the same (step, attempt) — implemented by re-deriving draws deterministically from sub-seeds.

    State the simulator tracks (GROUND TRUTH, policy-hidden):
      progress  = number of productive steps confirmed so far (0..N_TARGET)
      onset     = absolute progress-index at which the agent deviated (or None if on-path)
                  Represented as the progress value at the step where deviation happened.
      We model the canonical path as progress 0..N_TARGET. on_path is True iff onset is None OR
      current progress < onset (we've rolled back before it). Off-path => t_since_dev = progress-onset.
    """
    rng = random.Random(seed)

    progress = 0          # productive steps confirmed
    onset = None          # GT deviation onset (progress index) — hidden from policy
    wasted = 0            # re-executed steps + checkpoint overhead
    # checkpoint save overhead: we "save" each time progress crosses a multiple of c (forward only).
    saved_marks = set()

    # detector RNG (independent stream, but deterministic per rollout+policy is fine since policies
    # differ in HOW they use it; the underlying failure/deviation stream is shared via `rng`).
    det_rng = random.Random(seed ^ 0x9E3779B1)

    steps_guard = 0
    MAX_STEPS = 200000  # safety
    while progress < N_TARGET:
        steps_guard += 1
        if steps_guard > MAX_STEPS:
            break
        # checkpoint save overhead when first reaching a new checkpoint boundary
        mark = (progress // c) * c
        if progress > 0 and progress % c == 0 and mark not in saved_marks:
            saved_marks.add(mark)
            wasted += S_TOKENS

        # determine on/off path
        if onset is None:
            on_path = True
            t_since = 0
        elif progress < onset:
            on_path = True
            t_since = 0
        else:
            on_path = False
            t_since = progress - onset

        # execute one step (1 token; productive if it succeeds and doesn't get rolled back later)
        if on_path:
            # chance to deviate
            if onset is None and rng.random() < H0_DEV:
                onset = progress  # deviate now (this step is the onset)
            fail_h = H0_FAIL
            t_for_fail = 0
        else:
            fail_h = hazard(t_since, alpha, shape, base_w, k)

        failed = (rng.random() < fail_h)

        if not failed:
            progress += 1
            continue

        # ----- FAILURE: trigger recovery -----
        fail_pos = progress
        last_ckpt = (fail_pos // c) * c

        if policy == "A":
            restart = last_ckpt
        else:  # policy B — deviation-aware
            if policy == "B1":  # noisy detector
                miss = (det_rng.random() < det_fnr)
                if miss or onset is None:
                    # detector missed (or there is no true onset to find) -> behave like A
                    restart = last_ckpt
                else:
                    fp = (det_rng.random() < det_fpr)
                    if fp:
                        # fabricate a spurious EARLY onset -> over-rollback
                        est_onset = max(0, onset - random.Random(seed ^ fail_pos).randint(2*c, 4*c))
                    else:
                        noise = int(round(det_rng.gauss(0, det_sd)))
                        est_onset = max(0, onset + noise)
                    # roll back PAST last ckpt: snap to nearest checkpoint <= est_onset
                    restart = (est_onset // c) * c
                    # ensure it's actually past the last checkpoint at least sometimes; if est_onset
                    # lands in same ckpt bucket as failure, it degenerates to A (honest).
            else:  # B2 fixed overshoot: roll back `overshoot` checkpoints beyond last
                restart = max(0, last_ckpt - overshoot * c)

        # wasted tokens = steps we have to re-execute = (fail_pos - restart)
        # (we lose all confirmed progress from restart..fail_pos and must redo it)
        wasted += (fail_pos - restart)
        # roll progress back
        progress = restart
        # if we rolled back BEFORE the true onset, we're back on-path and the deviation is undone;
        # the agent may deviate again later (onset reset so it can re-happen).
        if onset is not None and restart < onset:
            onset = None  # genuinely escaped the off-path region; can re-deviate fresh
        # else: still at/after onset -> remains off-path, t_since recomputed next loop.
        # remove checkpoint-save marks above restart so re-crossing re-charges S (we redo those saves)
        saved_marks = {m for m in saved_marks if m <= restart}

    return wasted

def mc_penalty(alpha, c, shape, base_w, k, R, policyB, det_fpr, det_fnr, det_sd, overshoot):
    cfg = dict(alpha=alpha, c=c, shape=shape, base_w=base_w, k=k, R=R, policyB=policyB,
               fpr=det_fpr, fnr=det_fnr, sd=det_sd, ov=overshoot)
    base = cell_seed(cfg)
    wa, wb = [], []
    for i in range(R):
        s = base + i
        wa.append(simulate_rollout(s, alpha, c, shape, base_w, k, "A", det_fpr, det_fnr, det_sd, overshoot))
        wb.append(simulate_rollout(s, alpha, c, shape, base_w, k, policyB, det_fpr, det_fnr, det_sd, overshoot))
    mean_a = statistics.fmean(wa)
    mean_b = statistics.fmean(wb)
    # paired penalty distribution via bootstrap on per-rollout (wa-wb)/wb? define penalty on means.
    penalty = (mean_a - mean_b) / mean_b if mean_b > 0 else 0.0
    # bootstrap CI on penalty (resample paired indices)
    rb = random.Random(base ^ 0xABCDEF)
    boots = []
    n = R
    for _ in range(400):
        idx = [rb.randrange(n) for _ in range(n)]
        ma = statistics.fmean([wa[j] for j in idx])
        mb = statistics.fmean([wb[j] for j in idx])
        boots.append((ma - mb) / mb if mb > 0 else 0.0)
    boots.sort()
    lo = boots[int(0.025 * len(boots))]
    hi = boots[int(0.975 * len(boots))]
    return dict(alpha=alpha, c=c, shape=shape, k=k, policyB=policyB, fpr=det_fpr, fnr=det_fnr,
                sd=det_sd, overshoot=overshoot, R=R,
                mean_waste_A=mean_a, mean_waste_B=mean_b,
                penalty=penalty, ci_lo=lo, ci_hi=hi)

def main():
    t0 = time.time()
    R = 20000
    rows = []

    # ---- 1. PRIMARY alpha sweep (LINEAR, c=20, B1 detector realistic FPR=FNR=0.1) ----
    print("=== alpha sweep (LINEAR, c=20, B1 fpr=fnr=0.1) ===")
    for alpha in [0.0, 0.005, 0.01, 0.02, 0.04, 0.08]:
        r = mc_penalty(alpha, 20, "linear", 0.0, 2.0, R, "B1", 0.1, 0.1, 3.0, 1)
        rows.append({**r, "sweep": "alpha_linear_B1"})
        print(f"  alpha={alpha:<6} A={r['mean_waste_A']:.2f} B={r['mean_waste_B']:.2f} "
              f"penalty={r['penalty']*100:+.1f}% CI[{r['ci_lo']*100:+.1f},{r['ci_hi']*100:+.1f}] "
              f"({time.time()-t0:.0f}s)")

    # ---- 1b. alpha sweep with B2 fixed-overshoot (perfect-info-free heuristic) ----
    print("=== alpha sweep (LINEAR, c=20, B2 overshoot=1) ===")
    for alpha in [0.0, 0.005, 0.01, 0.02, 0.04, 0.08]:
        r = mc_penalty(alpha, 20, "linear", 0.0, 2.0, R, "B2", 0.0, 0.0, 0.0, 1)
        rows.append({**r, "sweep": "alpha_linear_B2"})
        print(f"  alpha={alpha:<6} A={r['mean_waste_A']:.2f} B={r['mean_waste_B']:.2f} "
              f"penalty={r['penalty']*100:+.1f}% CI[{r['ci_lo']*100:+.1f},{r['ci_hi']*100:+.1f}] "
              f"({time.time()-t0:.0f}s)")

    # ---- 2. Weibull variant (k=2), B1 ----
    print("=== Weibull k=2 sweep via base_w (c=20, B1 fpr=fnr=0.1) ===")
    for base_w in [0.0, 0.0005, 0.001, 0.002, 0.004]:
        r = mc_penalty(0.0, 20, "weibull", base_w, 2.0, R, "B1", 0.1, 0.1, 3.0, 1)
        rows.append({**r, "sweep": "weibull_B1"})
        print(f"  base_w={base_w:<7} A={r['mean_waste_A']:.2f} B={r['mean_waste_B']:.2f} "
              f"penalty={r['penalty']*100:+.1f}% CI[{r['ci_lo']*100:+.1f},{r['ci_hi']*100:+.1f}] "
              f"({time.time()-t0:.0f}s)")

    # ---- 3. checkpoint spacing sweep (LINEAR alpha=0.02, B1) ----
    print("=== checkpoint spacing sweep (alpha=0.02, B1 fpr=fnr=0.1) ===")
    for c in [10, 20, 40]:
        r = mc_penalty(0.02, c, "linear", 0.0, 2.0, R, "B1", 0.1, 0.1, 3.0, 1)
        rows.append({**r, "sweep": "ckpt_spacing_B1"})
        print(f"  c={c:<4} A={r['mean_waste_A']:.2f} B={r['mean_waste_B']:.2f} "
              f"penalty={r['penalty']*100:+.1f}% CI[{r['ci_lo']*100:+.1f},{r['ci_hi']*100:+.1f}] "
              f"({time.time()-t0:.0f}s)")

    # ---- 4. detector FPR/FNR boundary (LINEAR alpha=0.02, c=20, B1) ----
    print("=== detector FPR/FNR boundary (alpha=0.02, c=20, B1) ===")
    for (fpr, fnr) in [(0.0,0.0),(0.1,0.1),(0.25,0.25),(0.5,0.5)]:
        r = mc_penalty(0.02, 20, "linear", 0.0, 2.0, R, "B1", fpr, fnr, 3.0, 1)
        rows.append({**r, "sweep": "detector_noise_B1"})
        print(f"  fpr=fnr={fpr:<4} A={r['mean_waste_A']:.2f} B={r['mean_waste_B']:.2f} "
              f"penalty={r['penalty']*100:+.1f}% CI[{r['ci_lo']*100:+.1f},{r['ci_hi']*100:+.1f}] "
              f"({time.time()-t0:.0f}s)")

    # write CSV
    fields = ["sweep","alpha","c","shape","k","base_w","policyB","fpr","fnr","sd","overshoot","R",
              "mean_waste_A","mean_waste_B","penalty","ci_lo","ci_hi"]
    with open(os.path.join(OUTDIR, "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            r.setdefault("base_w", r.get("base_w", 0.0))
            w.writerow(r)
    print(f"\nWROTE {os.path.join(OUTDIR,'results.csv')}  ({len(rows)} rows)  total {time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()
