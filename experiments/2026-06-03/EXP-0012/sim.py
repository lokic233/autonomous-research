#!/usr/bin/env python3
# EXP-0012 L0 — CLAIM-0010. CPU-only, stdlib-only, SERIAL. researcher-0011.
# Honest, NON-CIRCULAR trace simulation. See PREREGISTRATION.md.
#
# CIRCULARITY INVARIANT: variable `theta` (latent reference-propensity, the GENERATIVE CAUSE)
# is read ONLY inside generate_trace() and oracle/AUC measurement. The RT / H2O / CAUSAL policy
# decision functions read ONLY realizable past observables. (Auditable by grep.)
import random, math, csv, os, statistics

ART = os.path.dirname(os.path.abspath(__file__))

# ----------------------------- TRACE MODEL -----------------------------
# A trace is a sequence of committed SPANS, each with a role (PROSE | TOOL_RESULT),
# a token length, and a hidden latent theta (reference propensity). Decode proceeds for
# H future steps; at each step a reference event targets some committed span sampled from
# the latent callback structure. A subset of references are CRITICAL (gate task success).

PROSE, TOOL = "PROSE", "TOOL"

def generate_trace(rng, n_spans=60, horizon=240):
    spans = []
    # latent topic/callback graph: a handful of TOOL_RESULT spans carry "handles" that are
    # structurally destined to be dereferenced LATER (delayed callbacks). This is the latent
    # cause H2O cannot see (delayed -> low accumulated past attention by the time it's needed).
    for i in range(n_spans):
        is_tool = (rng.random() < 0.5)
        role = TOOL if is_tool else PROSE
        # tool results are VERBOSE (long); prose shorter
        toklen = int(rng.uniform(60, 200)) if is_tool else int(rng.uniform(8, 40))
        # latent reference propensity theta (the GENERATIVE CAUSE — predictor never sees it)
        if is_tool:
            # subset of tool spans are "callback handles": high theta, but DELAYED references
            is_handle = (rng.random() < 0.30)
            theta = rng.uniform(0.55, 0.95) if is_handle else rng.uniform(0.0, 0.15)
            # does this handle carry a recurring substring/ID? correlated-with-but-not-equal-theta
            # (n-gram signal). Handles usually do; some non-handles spuriously do too.
            has_handle_ngram = (rng.random() < (0.80 if is_handle else 0.12))
            delayed = is_handle  # handle references are delayed (cold then hot)
        else:
            theta = rng.uniform(0.0, 0.35)  # prose: low/medium, NOT delayed
            has_handle_ngram = (rng.random() < 0.05)
            delayed = False
        spans.append(dict(idx=i, role=role, toklen=toklen, theta=theta,
                          has_ngram=has_handle_ngram, delayed=delayed))

    # ---- generate PAST attention mass (realizable observable) ----
    # H2O-style accumulated past attention. Recent + generally-salient spans accrue mass.
    # CRITICAL design point: delayed-callback handles accrue LOW past attention before they go
    # hot (they were referenced once at commit, then cold), so past-attention is a WEAK signal
    # for exactly the spans that matter most. Past attention is correlated with recency and a
    # GENERIC saliency that is only weakly tied to theta for delayed spans.
    for s in spans:
        recency = (s["idx"] + 1) / n_spans
        generic_salience = rng.uniform(0.0, 0.4)
        if s["delayed"]:
            # delayed handles: low accumulated past attention (cold), regardless of high theta
            past_attn = 0.15 * recency + generic_salience * 0.5 + rng.uniform(0, 0.1)
        else:
            # non-delayed: past attention tracks theta + recency (H2O does fine here)
            past_attn = 0.5 * s["theta"] + 0.5 * recency + generic_salience * 0.3
        s["past_attn"] = past_attn

    # ---- generate FUTURE references from latent theta (decode horizon) ----
    # Each future step references a span sampled prop. to theta (delayed handles only become
    # eligible after a delay -> referenced in the LATER half of the horizon).
    future_refs = []   # list of (step, span_idx)
    critical_refs = [] # subset that gates task success: the delayed-handle dereferences
    for step in range(horizon):
        late = step > horizon * 0.5
        weights = []
        for s in spans:
            w = s["theta"]
            if s["delayed"] and not late:
                w = 0.0          # not yet eligible (still cold)
            if s["delayed"] and late:
                w = s["theta"] * 2.0  # now hot — must be retained
            weights.append(max(w, 1e-6))
        tot = sum(weights)
        r = rng.random() * tot
        acc = 0.0
        chosen = 0
        for j, w in enumerate(weights):
            acc += w
            if r <= acc:
                chosen = j; break
        future_refs.append((step, chosen))
        if spans[chosen]["delayed"] and late:
            critical_refs.append((step, chosen))
    return spans, future_refs, critical_refs

# ----------------------------- OBSERVABLES (predictor inputs) -----------------------------
# Realizable at inference from PAST only: decayed past-attention mass + repeat-substring/n-gram
# hits. NOISY function of theta. SWEEP sigma to move measured AUC.
def make_observables(rng, spans, sigma):
    obs = []
    for s in spans:
        # n-gram/handle hit signal (realizable: count of recurring substrings/IDs)
        ngram_sig = (1.0 if s["has_ngram"] else 0.0) + rng.uniform(-0.05, 0.05)
        # decayed past attention (realizable)
        pa = s["past_attn"]
        # combine; this is what CAUSAL sees. It does NOT see theta or delayed/.
        raw = 0.55 * ngram_sig + 0.45 * pa
        noisy = raw + rng.gauss(0, sigma)
        obs.append(noisy)
    return obs

# ----------------------------- AUC (measured, headroom only) -----------------------------
def measure_auc(scores, labels):
    # labels: 1 if span is referenced in the future at all, else 0. AUC of scores vs labels.
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    if not pos or not neg:
        return 0.5
    wins = 0.0
    for p in pos:
        for n in neg:
            if p > n: wins += 1
            elif p == n: wins += 0.5
    return wins / (len(pos) * len(neg))

# ----------------------------- POLICIES (NO theta) -----------------------------
# Each returns a SET of retained span indices given budget B (tokens). Span-boundary detection
# error: the CAUSAL policy operates on jittered boundaries (merge/split adjacent spans) to model
# realistic boundary detection error — applied as score-noise on merged groups.

def keep_by_score(spans, scores, B):
    order = sorted(range(len(spans)), key=lambda i: -scores[i])
    kept, used = set(), 0
    for i in order:
        if used + spans[i]["toklen"] <= B:
            kept.add(i); used += spans[i]["toklen"]
    return kept

def policy_RT(spans, B, **kw):
    # recency-truncation: keep most-recent spans (highest idx) until budget
    order = sorted(range(len(spans)), key=lambda i: -spans[i]["idx"])
    kept, used = set(), 0
    for i in order:
        if used + spans[i]["toklen"] <= B:
            kept.add(i); used += spans[i]["toklen"]
    return kept

def policy_H2O(spans, B, **kw):
    # attention-eviction: keep highest accumulated PAST attention (realizable observable)
    scores = [s["past_attn"] for s in spans]
    return keep_by_score(spans, scores, B)

def policy_CAUSAL(spans, B, obs=None, rng=None, boundary_err=0.10, **kw):
    # noisy causal reference predictor: score = predicted future-ref prob from NOISY observables.
    # realistic span-boundary detection error: jitter scores on adjacent-span confusion.
    scores = list(obs)
    if rng is not None and boundary_err > 0:
        for i in range(len(scores)):
            if rng.random() < boundary_err:
                # boundary confusion: blend with a neighbor's score
                j = i + (1 if rng.random() < 0.5 else -1)
                j = max(0, min(len(scores) - 1, j))
                scores[i] = 0.5 * scores[i] + 0.5 * scores[j]
    return keep_by_score(spans, scores, B)

def policy_ORACLE(spans, B, **kw):
    # UPPER BOUND ONLY — sees latent theta. NOT a competitor.
    scores = [s["theta"] for s in spans]
    return keep_by_score(spans, scores, B)

# ----------------------------- SCORING -----------------------------
def eval_policy(kept, future_refs, critical_refs):
    # M1: referenced-span availability (recall of future references)
    if future_refs:
        hits = sum(1 for (_, idx) in future_refs if idx in kept)
        m1 = hits / len(future_refs)
    else:
        m1 = 1.0
    # M2: task solved iff ALL critical references land on retained spans
    if critical_refs:
        m2 = 1.0 if all(idx in kept for (_, idx) in critical_refs) else 0.0
    else:
        m2 = 1.0
    return m1, m2

# ----------------------------- EXPERIMENT -----------------------------
def run():
    SEEDS = list(range(64))                      # >= 8 seeds
    # sigma sweep tuned so the CRITICAL-HANDLE AUC (the predictor's ability to identify the
    # delayed-callback spans that GATE task success — the relevant decision) spans ~{0.85..0.63},
    # i.e. across the realistic-vs-unrealistic 0.85 threshold. (overall-ref AUC stays ~0.5-0.6
    # because most generic refs go to non-delayed spans H2O catches; that's expected & honest.)
    SIGMAS = [0.05, 0.20, 0.40, 0.65, 0.90]
    BUDGET_FRACS = [0.2, 0.3, 0.4, 0.5, 0.6]
    POLICIES = [("RT", policy_RT), ("H2O", policy_H2O),
                ("CAUSAL", policy_CAUSAL), ("ORACLE", policy_ORACLE)]

    rows = []
    for sigma in SIGMAS:
        for seed in SEEDS:
            rng = random.Random((seed * 1000003) ^ int(sigma * 1e6))
            spans, future_refs, critical_refs = generate_trace(rng)
            total_tok = sum(s["toklen"] for s in spans)
            # measured future-ref AUC of the CAUSAL observables (headroom/x-axis only)
            obs = make_observables(rng, spans, sigma)
            referenced = set(idx for (_, idx) in future_refs)
            labels = [1 if s["idx"] in referenced else 0 for s in spans]
            auc = measure_auc(obs, labels)  # overall-ref AUC (generic; mostly H2O-catchable refs)
            # CRITICAL-HANDLE AUC: predictor's ability to identify the delayed-callback spans whose
            # re-reference GATES task success (M2). This is the decision-relevant AUC — the x-axis
            # the CLAIM is about ("which committed tool-result spans get re-referenced"). Measured,
            # not assumed. Still computed from NOISY obs only (no theta).
            crit_idx = set(idx for (_, idx) in critical_refs)
            crit_labels = [1 if s["idx"] in crit_idx else 0 for s in spans]
            crit_auc = measure_auc(obs, crit_labels)
            for frac in BUDGET_FRACS:
                B = int(total_tok * frac)
                for pname, pfn in POLICIES:
                    # fresh rng stream for policy-internal randomness (boundary err) — deterministic
                    prng = random.Random((seed * 7919) ^ int(sigma * 1e6) ^ int(frac * 1000))
                    kept = pfn(spans, B, obs=obs, rng=prng)
                    kept_tok = sum(spans[i]["toklen"] for i in kept)
                    m1, m2 = eval_policy(kept, future_refs, critical_refs)
                    rows.append(dict(sigma=sigma, seed=seed, auc=round(auc, 4),
                                     crit_auc=round(crit_auc, 4),
                                     frac=frac, budget=B, total_tok=total_tok,
                                     policy=pname, kept_tok=kept_tok,
                                     m1_avail=round(m1, 6), m2_task=m2))
    # write on-disk (truth)
    out = os.path.join(ART, "results", "results.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"WROTE {out} rows={len(rows)}")

if __name__ == "__main__":
    run()
