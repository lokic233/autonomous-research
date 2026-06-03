#!/usr/bin/env python3
"""EXP-0010 L0 trace sim: tool-result extractive compression.
stdlib-only, SERIAL. 4 policies: NC, RT (recency-trunc), EC (extractive-causal),
EO (extractive-oracle). Metric: context-tokens vs task-success (referenced-span availability).
"""
import random, math

SPAN_LEN = 32
T_TURNS = 60
WARMUP = 5
REF_RATE = 3
SYS_TOKENS = 200  # fixed system preamble, always retained, never compressed

class Span:
    __slots__ = ("sid","turn","tokens","salience","ref_count")
    def __init__(self, sid, turn, tokens, salience):
        self.sid=sid; self.turn=turn; self.tokens=tokens
        self.salience=salience  # OBSERVABLE proxy for attention/citation signal
        self.ref_count=0        # times referenced so far (observable, causal)

def gen_trace(seed, verbosity, ref_density, predictability):
    rng = random.Random(seed)
    # predictability -> weights on (recency, salience, repeat) vs uniform noise
    pmap = {
        "low":  dict(w_rec=0.3, w_sal=0.1, w_rep=0.1, w_noise=0.5),
        "med":  dict(w_rec=0.4, w_sal=0.4, w_rep=0.3, w_noise=0.15),
        "high": dict(w_rec=0.4, w_sal=0.8, w_rep=0.8, w_noise=0.03),
    }
    w = pmap[predictability]
    spans_by_turn = {}   # turn -> list[Span]
    all_spans = []
    sid = 0
    # references[t] = list of span sids that turn t demands (must be present at turn t)
    references = {}
    for t in range(T_TURNS):
        # tool-result for turn t
        vtok = max(SPAN_LEN, int(rng.gammavariate(2.0, verbosity/2.0)))
        nspan = max(1, math.ceil(vtok/SPAN_LEN))
        tspans = []
        for _ in range(nspan):
            sal = rng.random()  # latent salience in [0,1)
            sp = Span(sid, t, SPAN_LEN, sal); sid+=1
            tspans.append(sp); all_spans.append(sp)
        spans_by_turn[t] = tspans
        # generate references from PRIOR turns (t demands earlier spans)
        references[t] = []
        if t > WARMUP:
            prior = [s for tt in range(t) for s in spans_by_turn[tt]]
            if prior:
                k = min(len(prior), rng.poisson if hasattr(rng,'poisson') else _pois(rng, REF_RATE))
                # build sampling weights
                # target sparsity: only a ref_density fraction of prior spans ever get referenced.
                # Implement by restricting the "eligible" pool to a stable sparse subset per trace.
                k = min(k, len(prior))
                weights = []
                for s in prior:
                    dist = t - s.turn
                    rec = math.exp(-dist/8.0)
                    rep = (s.ref_count+0.0)
                    score = (w["w_rec"]*rec + w["w_sal"]*s.salience + w["w_rep"]*rep
                             + w["w_noise"]*rng.random())
                    weights.append(score)
                # pick k distinct via weighted sampling
                chosen = _weighted_sample(rng, prior, weights, k)
                for s in chosen:
                    s.ref_count += 1
                    references[t].append(s.sid)
    # Enforce sparsity post-hoc: cap distinct referenced spans to ref_density * total spans.
    # If more distinct spans were referenced, that's fine — density controls REF_RATE-driven
    # spread; we additionally scale ref_rate via density already implicitly. Keep as-is but
    # record the realized distinct-referenced fraction.
    return spans_by_turn, references, all_spans, sid

def _pois(rng, lam):
    L = math.exp(-lam); k=0; p=1.0
    while True:
        k+=1; p*=rng.random()
        if p<=L: return k-1

def _weighted_sample(rng, items, weights, k):
    # sample k distinct items proportional to weights (no replacement)
    items = list(items); weights = list(weights)
    out = []
    for _ in range(min(k, len(items))):
        tot = sum(weights)
        if tot <= 0:
            idx = rng.randrange(len(items))
        else:
            r = rng.random()*tot; acc=0; idx=0
            for i,wt in enumerate(weights):
                acc+=wt
                if r<=acc: idx=i; break
        out.append(items[idx])
        items.pop(idx); weights.pop(idx)
    return out

# ---- density control: we want only ref_density of spans EVER referenced.
# Simplest faithful approach: pre-designate an eligible pool = ref_density fraction of spans
# (chosen by salience-biased lottery so eligibility correlates with observable signal at
# higher predictability). References can only land on eligible spans. Regenerate with this.

def gen_trace2(seed, verbosity, ref_density, predictability):
    rng = random.Random(seed*7919+13)
    pmap = {
        "low":  dict(w_rec=0.3, w_sal=0.05, w_rep=0.1, w_noise=0.6, elig_sal=0.0),
        "med":  dict(w_rec=0.4, w_sal=0.4,  w_rep=0.3, w_noise=0.15, elig_sal=0.5),
        "high": dict(w_rec=0.35,w_sal=0.8,  w_rep=0.8, w_noise=0.03, elig_sal=0.9),
    }
    w = pmap[predictability]
    spans_by_turn={}; all_spans=[]; sid=0
    for t in range(T_TURNS):
        vtok = max(SPAN_LEN, int(rng.gammavariate(2.0, verbosity/2.0)))
        nspan = max(1, math.ceil(vtok/SPAN_LEN))
        ts=[]
        for _ in range(nspan):
            sal=rng.random()
            sp=Span(sid,t,SPAN_LEN,sal); sid+=1; ts.append(sp); all_spans.append(sp)
        spans_by_turn[t]=ts
    # designate eligible pool: ref_density fraction of all spans.
    n_elig = max(1, int(round(ref_density*len(all_spans))))
    # eligibility lottery biased by salience by elig_sal (predictability ties eligibility to
    # the OBSERVABLE signal — claim-favorable when high).
    keyed = sorted(all_spans, key=lambda s: -(w["elig_sal"]*s.salience + (1-w["elig_sal"])*rng.random()))
    eligible = set(s.sid for s in keyed[:n_elig])
    references={}
    for t in range(T_TURNS):
        references[t]=[]
        if t>WARMUP:
            prior=[s for tt in range(t) for s in spans_by_turn[tt] if s.sid in eligible]
            if not prior: continue
            k=min(len(prior), _pois(rng, REF_RATE))
            if k<=0: continue
            weights=[]
            for s in prior:
                dist=t-s.turn
                rec=math.exp(-dist/8.0)
                score=(w["w_rec"]*rec + w["w_sal"]*s.salience + w["w_rep"]*s.ref_count
                       + w["w_noise"]*rng.random())
                weights.append(score)
            for s in _weighted_sample(rng, prior, weights, k):
                s.ref_count+=1; references[t].append(s.sid)
    return spans_by_turn, references, all_spans, sid

def simulate(spans_by_turn, references, all_spans, total_sid, policy, budget_tokens):
    """Replay the trace turn by turn. At each turn: add new tool-result spans, register the
    turn's demands (count hit/miss vs current retained set), then enforce budget by the policy.
    Returns (mean_context_tokens, peak_context_tokens, task_success)."""
    # precompute future reference turn per span (for oracle)
    future_ref = {}  # sid -> sorted list of turns that reference it
    for t,refs in references.items():
        for s in refs:
            future_ref.setdefault(s, []).append(t)
    retained = {}  # sid -> Span (currently in context)
    # observable causal state: ref_count_so_far per span
    seen_ref = {}  # sid -> count referenced so far
    ctx_samples=[]; peak=0
    demands=0; hits=0
    span_by_id = {s.sid:s for s in all_spans}
    for t in range(T_TURNS):
        # 1. append new tool-result spans
        for s in spans_by_turn[t]:
            retained[s.sid]=s
        # 2. evaluate this turn's demands against CURRENT retained set
        for sid in references[t]:
            demands+=1
            if sid in retained:
                hits+=1
            seen_ref[sid]=seen_ref.get(sid,0)+1  # observable AFTER this turn references it
        # 3. enforce budget
        cur_tokens = SYS_TOKENS + sum(s.tokens for s in retained.values())
        if cur_tokens > budget_tokens and policy!="NC":
            # need to drop spans until within budget
            drop_budget = cur_tokens - budget_tokens
            items = list(retained.values())
            if policy=="RT":
                # drop OLDEST first
                items.sort(key=lambda s:(s.turn, s.sid))  # oldest first -> drop from front
                order = items
            elif policy=="EC":
                # causal score: keep high (salience + seen_ref so far + recency). Drop LOW.
                def cscore(s):
                    rec = math.exp(-(t - s.turn)/8.0)
                    return 0.8*s.salience + 1.0*seen_ref.get(s.sid,0) + 0.4*rec
                items.sort(key=lambda s: cscore(s))  # lowest score first -> drop
                order = items
            elif policy=="EO":
                # oracle: keep spans with a FUTURE reference (turn > t). Drop those with no
                # future ref first; among future-ref spans, drop the latest-needed first.
                def oscore(s):
                    futs=[ft for ft in future_ref.get(s.sid,[]) if ft> t]
                    if not futs: return (0, 0)        # no future need -> drop first
                    return (1, -min(futs))            # needed soon -> keep (higher key)
                items.sort(key=lambda s: oscore(s))   # lowest first -> drop
                order = items
            dropped=0
            for s in order:
                if dropped >= drop_budget: break
                # never drop spans appended THIS turn? allow dropping; but keep current-turn new
                # result spans only if not over — simplest: allow dropping any non-current span.
                if s.turn==t: continue
                del retained[s.sid]; dropped+=s.tokens
            # if still over (all old dropped), allow dropping current-turn spans too
            if dropped < drop_budget:
                for s in order:
                    if dropped>=drop_budget: break
                    if s.sid in retained:
                        del retained[s.sid]; dropped+=s.tokens
        cur_tokens = SYS_TOKENS + sum(s.tokens for s in retained.values())
        ctx_samples.append(cur_tokens); peak=max(peak,cur_tokens)
    success = hits/demands if demands else 1.0
    mean_ctx = sum(ctx_samples)/len(ctx_samples)
    return mean_ctx, peak, success, demands
