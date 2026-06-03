#!/usr/bin/env python3
# EXP-0062 CLAIM-0055: support-removal coercion in grammar-constrained tool routing.
# CPU-only, stdlib-only, SERIAL. Harness owns GT; decoders read only observables.
import math, random, csv, os, statistics

# ---- Intent space: GxG lattice of candidate action cells in [0,1]^2 ----
G = 12
CELLS = [(i/(G-1), j/(G-1)) for i in range(G) for j in range(G)]  # 144 cells
NCELLS = len(CELLS)

def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def nearest_cell(r):
    best, bi = 1e9, -1
    for i, c in enumerate(CELLS):
        d = dist(r, c)
        if d < best: best, bi = d, i
    return bi  # true-target cell index t*

# ---- FIXED similarity kernel: pref(c) propto exp(-||r-c||/temp) * exp(noise) ----
def pref_logits(r, temp, sigma, rng):
    # log-pref(c) = -dist/temp + noise_c ; noise FIXED-form (Gumbel-ish gaussian logit noise)
    return [(-dist(r, c)/temp + rng.gauss(0, sigma)) for c in CELLS]

def argmax_over(logits, idxs):
    best, bi = -1e18, -1
    for i in idxs:
        if logits[i] > best: best, bi = logits[i], i
    return bi

# ---- enum sampling (FIXED kernel; enum is just a subset of cells) ----
def sample_enum(K, rng):
    return rng.sample(range(NCELLS), K)

# ---- one trial ----
def run_cell(K, temp, sigma, seed, n_requests=600, esc_prior=None):
    rng = random.Random(seed)
    # results accumulators
    oos_total = 0
    misroute = 0            # arm A: out-of-set -> valid wrong action (always true for A on oos)
    gad_recover = 0         # arm B recovers true target on oos
    monitor_recall_hits = 0 # validity-monitor catches a misroute (should be 0)
    # gap bins for misroute severity & escape recall
    gap_bins = [0.10, 0.20, 0.30, 0.45, 99]  # upper edges
    bin_oos = [0]*len(gap_bins)
    bin_esc_hit = [0]*len(gap_bins)
    # escape prior: a flat affinity for the 'other' cell, in logit terms
    # model: escape competes vs the nearest concrete in-enum member's logit
    for _ in range(n_requests):
        enum = sample_enum(K, rng)
        enum_set = set(enum)
        r = (rng.random(), rng.random())
        tstar = nearest_cell(r)
        in_set = tstar in enum_set
        logits = pref_logits(r, temp, sigma, rng)
        # ARM A: greedy mask over enum
        emitA = argmax_over(logits, enum)
        # ARM B: GAD-style — renormalize FULL pref over enum support, argmax (same as A for argmax,
        #   but we also measure gap-recovery: does B ever put mass on true target? true target not in
        #   support => recovery only if tstar happens to be in enum. For oos it's 0 by construction.)
        emitB = emitA  # argmax of renormalized-over-support == masked argmax
        if not in_set:
            oos_total += 1
            # gap = dist from true target to nearest in-enum cell
            gap = min(dist(CELLS[tstar], CELLS[e]) for e in enum)
            bi = next(k for k,ub in enumerate(gap_bins) if gap <= ub)
            bin_oos[bi] += 1
            # ARM A misroute: emitted a valid action != true target. ALWAYS valid (schema-ok),
            # ALWAYS wrong on oos. Count as misroute.
            if emitA != tstar:
                misroute += 1
            # ARM B gap-recovery: did B emit the true (oos) target? impossible -> 0
            if emitB == tstar:
                gad_recover += 1
            # MONITOR: schema-validate+retry. emitA is in enum => schema-valid => retry never fires.
            # monitor recall on misroute class = caught misroutes / misroutes = 0.
            # (we never increment monitor_recall_hits)
            # ARM C: escape-hatch. escape wins iff its logit > nearest concrete in-enum logit.
            if esc_prior is not None:
                nearest_in_enum_logit = logits[emitA]  # the best concrete distractor
                esc_logit = esc_prior + rng.gauss(0, sigma)
                if esc_logit > nearest_in_enum_logit:
                    bin_esc_hit[bi] += 1
    misroute_rate = misroute/oos_total if oos_total else 0.0
    gad_recovery = gad_recover/oos_total if oos_total else 0.0
    monitor_recall = monitor_recall_hits/misroute if misroute else 0.0
    esc_recall_by_bin = [ (bin_esc_hit[k]/bin_oos[k] if bin_oos[k] else None) for k in range(len(gap_bins)) ]
    return dict(K=K, temp=temp, sigma=sigma, seed=seed, oos_total=oos_total,
                misroute_rate=misroute_rate, gad_recovery=gad_recovery,
                monitor_recall=monitor_recall, bin_oos=bin_oos,
                esc_recall_by_bin=esc_recall_by_bin, gap_edges=gap_bins)

def ci95(vals):
    if len(vals) < 2: return (statistics.mean(vals), 0.0)
    m = statistics.mean(vals); s = statistics.stdev(vals)
    return (m, 1.96*s/math.sqrt(len(vals)))

print("harness loaded", NCELLS, "cells")
