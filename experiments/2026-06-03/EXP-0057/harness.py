#!/usr/bin/env python3
"""EXP-0057 harness: committee#1 follow-up for CLAIM-0051.
REUSES EXP-0056 harness verbatim for buffer shuffle + label-free metric + signatures.
Adds: (1) interleaving stage (cycle_length C) -> L_eff=L/C test, (2) rho_within sweep,
(3) per-shard-shuffle baseline. Pure stdlib, SERIAL, CPU-only.
ANTI-CIRCULAR preserved: measurement reads ONLY gradient vectors; labels build stream + diag rho."""
import random, math
# load the EXP-0056 harness (gen_stream_grads, buffer_shuffle_order, batch_mean_var,
# rho_same_source, agg, D, B_BATCH, SIGMA_SIG, SIGMA_NOISE, SEEDS, choose_N)
exec(open('/tmp/exp0056_harness.py').read())

# ---------------------------------------------------------------------------
# Generalized stream generator: parametrized signal/noise scale (for rho_within sweep)
# and an INTERLEAVED variant (cycle_length C). C=1 reproduces the L0 sequential stream.
# ---------------------------------------------------------------------------
def gen_stream_param(seed, L, N, sig_scale=SIGMA_SIG, noise_scale=SIGMA_NOISE):
    """L0-identical sequential stream but with tunable sig/noise scales."""
    rng = random.Random(seed * 1_000_003 + 17)
    nsrc = N // L + 2
    sigs = [[rng.gauss(0.0, sig_scale) for _ in range(D)] for _ in range(nsrc)]
    grads, labels = [], []
    i = 0; s = 0
    while i < N:
        g = sigs[s % nsrc]
        for _ in range(L):
            if i >= N: break
            xi = [g[j] + rng.gauss(0.0, noise_scale) for j in range(D)]
            grads.append(xi); labels.append(s % nsrc); i += 1
        s += 1
    return grads, labels

def gen_stream_interleave(seed, L, N, C, sig_scale=SIGMA_SIG, noise_scale=SIGMA_NOISE):
    """INTERLEAVED stream (tf.data.interleave cycle_length=C / WebDataset multi-shard).
    C concurrent source-runs emitted in strict round-robin (one item per active slot per cycle).
    When a slot's run of length L is exhausted, a fresh source replaces that slot.
    Within a run, items are same-source contiguous. C=1 reproduces the L0 sequential stream.
    Returns (grads, labels) for the EMITTED (interleaved) order — fed into the buffer."""
    rng = random.Random(seed * 1_000_003 + 17 + C * 8675309)
    nsrc = (N // max(1, L // C if C else L)) + 2 * C + 4
    sigs = [[rng.gauss(0.0, sig_scale) for _ in range(D)] for _ in range(nsrc)]
    # each slot tracks (source_idx, remaining_in_run)
    next_src = 0
    slots = []
    for _ in range(C):
        slots.append([next_src, L]); next_src += 1
    grads, labels = [], []
    emitted = 0
    sp = 0  # round-robin pointer
    while emitted < N:
        slot = slots[sp % C]
        src, rem = slot
        if rem <= 0:
            slot[0] = next_src; next_src += 1
            slot[1] = L
            src = slot[0]; rem = L
            if next_src >= nsrc:  # grow signature pool if needed
                sigs.append([rng.gauss(0.0, sig_scale) for _ in range(D)])
                nsrc += 1
        g = sigs[src]
        xi = [g[j] + rng.gauss(0.0, noise_scale) for j in range(D)]
        grads.append(xi); labels.append(src)
        slot[1] -= 1
        emitted += 1
        sp += 1
    return grads, labels

# ---------------------------------------------------------------------------
# Per-shard-shuffle baseline: shuffle WITHIN each contiguous same-source run (shard),
# no cross-shard mixing. Operates on the EMITTED stream's contiguous same-label runs.
# Returns an index order. (For interleaved streams, "shards" = maximal same-source
# contiguous segments of the emitted stream — which for C>1 are length-1, so per-shard
# == identity; we therefore apply per-shard baseline to the SEQUENTIAL stream where it
# is the meaningful weaker baseline, matching the prereg.)
# ---------------------------------------------------------------------------
def per_shard_shuffle_order(labels, rng):
    """Shuffle within each maximal contiguous same-label run; preserve run order globally."""
    n = len(labels)
    order = []
    i = 0
    while i < n:
        j = i
        while j < n and labels[j] == labels[i]:
            j += 1
        run = list(range(i, j))
        rng.shuffle(run)
        order.extend(run)
        i = j
    return order

# ---------------------------------------------------------------------------
# Diagnostic: achieved within-source per-component correlation (verify rho_within).
# Correlation between two items of the SAME source on the same component =
# Var(signal)/(Var(signal)+Var(noise)). Estimate empirically from the generated grads+labels.
# ---------------------------------------------------------------------------
def measure_within_corr(grads, labels):
    """Empirical within-source per-component correlation, averaged over components & sources.
    For each source with >=2 items, corr_j ~ Cov over pairs / Var. Use the standard estimator:
    pooled within-source variance vs between-source variance is complex; instead estimate
    rho = 1 - E[within-source per-comp variance] / E[total per-comp variance about source-agnostic mean]."""
    from collections import defaultdict
    by = defaultdict(list)
    for idx, lab in enumerate(labels):
        by[lab].append(idx)
    # within-source variance per component (noise variance estimate)
    within_num = 0.0; within_den = 0
    grand = [0.0]*D; gc = 0
    for lab, idxs in by.items():
        if len(idxs) < 2: continue
        m = [0.0]*D
        for ix in idxs:
            x = grads[ix]
            for j in range(D): m[j] += x[j]
        inv = 1.0/len(idxs)
        for j in range(D): m[j] *= inv
        for ix in idxs:
            x = grads[ix]
            for j in range(D):
                within_num += (x[j]-m[j])**2
        within_den += (len(idxs)-1)*D
    # total variance about grand mean
    n = len(grads)
    for x in grads:
        for j in range(D): grand[j] += x[j]
    for j in range(D): grand[j] /= n
    tot_num = 0.0
    for x in grads:
        for j in range(D):
            tot_num += (x[j]-grand[j])**2
    var_noise = within_num/within_den
    var_total = tot_num/((n-1)*D)
    # within-source correlation rho = signal_var/(signal_var+noise_var); signal_var ~ var_total - var_noise
    var_signal = max(0.0, var_total - var_noise)
    return var_signal/(var_signal+var_noise) if (var_signal+var_noise)>0 else 0.0

print("EXP-0057 harness loaded (interleave + rho_within + per-shard baseline)")
