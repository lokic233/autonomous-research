#!/usr/bin/env python3
"""EXP-0056 harness: bounded-buffer sliding-window shuffle vs run-length L.
Pure stdlib, SERIAL, CPU-only. Measures per-mini-batch gradient-estimate variance
inflation = V_buffer / V_full across a B x L sweep + the scaling-axis test.
ANTI-CIRCULAR: measurement path (V_buffer, V_full) reads ONLY gradient vectors,
never source labels. Labels used only to build stream + diagnostic rho."""
import random, math, time, json, sys

D = 32                 # gradient dim
SIGMA_SIG = 1.0        # source signature scale
SIGMA_NOISE = 0.5      # per-item noise scale  -> within-source per-comp corr = 1/(1+0.25)=0.80
B_BATCH = 32           # mini-batch size b
SEEDS = [0,1,2,3,4]

# To keep wall-clock bounded and #batches >= hundreds across the grid, choose N per cell so that
# emitted batches ~ several hundred. We need N >= a few * L for many runs, and N/b batches.
# Use N adaptive: enough for >= 400 batches and >= ~8 runs of length L.
def choose_N(L):
    base = 400 * B_BATCH          # >=400 batches
    return max(base, 10 * L + 4 * 1600)  # ensure many full runs even at large L/B

def gen_stream_grads(seed, L, N):
    """Harness-owned GT. Returns (grads, labels). grads: list of list[float] length D.
    labels: source id per item (DIAGNOSTIC ONLY, never enters V metric)."""
    rng = random.Random(seed * 1_000_003 + 17)
    nsrc = N // L + 2
    # draw signatures g_s once
    sigs = [[rng.gauss(0.0, SIGMA_SIG) for _ in range(D)] for _ in range(nsrc)]
    grads = []
    labels = []
    i = 0
    s = 0
    while i < N:
        # contiguous run of length L for source s; ensure consecutive runs differ (s increments)
        g = sigs[s % nsrc]
        for _ in range(L):
            if i >= N: break
            xi = [g[j] + rng.gauss(0.0, SIGMA_NOISE) for j in range(D)]
            grads.append(xi)
            labels.append(s % nsrc)
            i += 1
        s += 1
    return grads, labels

def buffer_shuffle_order(n, B, rng):
    """Production sliding-window shuffle: yields a permutation index order of [0,n).
    Fill buffer to B, then emit uniform-random slot + refill; drain at end. Returns list of indices."""
    order = []
    buf = []
    nxt = 0
    # fill
    while nxt < n and len(buf) < B:
        buf.append(nxt); nxt += 1
    while buf:
        slot = rng.randrange(len(buf))
        order.append(buf[slot])
        if nxt < n:
            buf[slot] = nxt; nxt += 1
        else:
            # remove slot (swap-pop keeps uniformity over remaining)
            buf[slot] = buf[-1]; buf.pop()
    return order

def batch_mean_var(grads, order, b):
    """MEASUREMENT PATH (label-free). Given emitted index order, form consecutive batches of size b,
    compute total per-component variance of batch-mean vectors summed over D. Returns (V, nbatches)."""
    nb = len(order) // b
    # running mean/M2 per component (Welford), summed at end
    means = [0.0]*D
    M2 = [0.0]*D
    cnt = 0
    for k in range(nb):
        # batch mean vector
        bm = [0.0]*D
        base = k*b
        for t in range(b):
            x = grads[order[base+t]]
            for j in range(D):
                bm[j] += x[j]
        inv = 1.0/b
        cnt += 1
        for j in range(D):
            bm[j] *= inv
            delta = bm[j] - means[j]
            means[j] += delta / cnt
            M2[j] += delta * (bm[j] - means[j])
    if cnt < 2:
        return 0.0, cnt
    V = sum(M2[j] / (cnt - 1) for j in range(D))
    return V, cnt

def rho_same_source(labels, order, b):
    """DIAGNOSTIC (harness-side). Fraction of within-batch unordered pairs that are same-source."""
    nb = len(order) // b
    same = 0
    tot = 0
    for k in range(nb):
        base = k*b
        labs = [labels[order[base+t]] for t in range(b)]
        for ii in range(b):
            for jj in range(ii+1, b):
                tot += 1
                if labs[ii] == labs[jj]:
                    same += 1
    return same / tot if tot else 0.0

def run_cell(B, L, seed):
    """Returns dict with inflation, rho_buf, rho_full, nbatches for one (B,L,seed)."""
    N = choose_N(L)
    grads, labels = gen_stream_grads(seed, L, N)
    n = len(grads)
    # buffer shuffle
    rng_buf = random.Random(seed*7919 + B*31 + L*131 + 1)
    bo = buffer_shuffle_order(n, B, rng_buf)
    V_buf, nb = batch_mean_var(grads, bo, B_BATCH)
    rho_buf = rho_same_source(labels, bo, B_BATCH)
    # full shuffle baseline (oracle): full permutation
    rng_full = random.Random(seed*104729 + 3)
    fo = list(range(n))
    rng_full.shuffle(fo)
    V_full, _ = batch_mean_var(grads, fo, B_BATCH)
    rho_full = rho_same_source(labels, fo, B_BATCH)
    infl = V_buf / V_full if V_full > 0 else float('nan')
    return dict(B=B, L=L, seed=seed, N=n, nbatches=nb, V_buf=V_buf, V_full=V_full,
                inflation=infl, rho_buf=rho_buf, rho_full=rho_full)

def agg(cells):
    """cells: list of per-seed dicts for same (B,L). Returns mean inflation + 95% CI, mean rho."""
    infl = [c['inflation'] for c in cells]
    m = sum(infl)/len(infl)
    if len(infl) > 1:
        sd = math.sqrt(sum((x-m)**2 for x in infl)/(len(infl)-1))
        ci = 1.96 * sd / math.sqrt(len(infl))
    else:
        ci = 0.0
    rb = sum(c['rho_buf'] for c in cells)/len(cells)
    rf = sum(c['rho_full'] for c in cells)/len(cells)
    nb = cells[0]['nbatches']
    return dict(mean=m, ci=ci, sd=(sd if len(infl)>1 else 0.0), rho_buf=rb, rho_full=rf,
                nbatches=nb, n_seeds=len(cells))

print("harness loaded")
