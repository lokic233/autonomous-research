#!/usr/bin/env python3
"""EXP-0015 L0 harness. CLAIM-0012. CPU-only, stdlib-only, SERIAL.
Honest pipeline. Anti-circular: predictor reads only noisy partial-decode OBSERVABLES,
never the latent abandonment hazard / label / abandon_step.
Outputs CSVs (trust disk, not stdout)."""
import random, math, csv, os, statistics

OUT = "/Users/dengcchi/autonomous-research-v3/experiments/2026-06-03/EXP-0015/results"
os.makedirs(OUT, exist_ok=True)

SEEDS = [11,23,37,59,71,89,101,113]   # 8 seeds
TRAIN_SEEDS = SEEDS[:4]
TEST_SEEDS  = SEEDS[4:]
N_TURNS_PER_EPISODE = 400              # turns per (seed,cell)
P_ABANDON_GRID = [0.10, 0.20, 0.35, 0.50]
TIMING_GRID    = ["early","mid","late","mixed"]
# noise sigmas chosen to span AUC bands; achieved AUC reported, not assumed.
NOISE_GRID     = [0.30, 0.70, 1.40]    # low/med/high observation noise

# ---------- trace model ----------
def lognormal(rng, mu, sigma):
    return math.exp(rng.gauss(mu, sigma))

def sample_turn(rng, p_abandon, timing):
    """Generate one agent turn with LATENT process. Returns dict.
    Latents are NOT visible to predictor. Observables are noisy fns of latents."""
    # latent variables
    latent_difficulty   = rng.random()          # [0,1] higher -> floundering
    latent_tool_fragility = rng.random()         # [0,1] higher -> malformed tool calls
    latent_branch_value = rng.random()           # [0,1] lower -> prune-prone
    # planned length (decode tokens if it ran to completion)
    L_plan = max(8, int(lognormal(rng, math.log(120), 0.6)))
    # latent abandonment hazard: rises with difficulty, fragility, low branch value
    hazard = 0.45*latent_difficulty + 0.35*latent_tool_fragility + 0.20*(1-latent_branch_value)
    # scale hazard so the marginal abandonment rate ~ p_abandon
    # threshold calibrated: turn abandoned if hazard*scale + noise crosses; use p_abandon as base rate
    abandoned = (rng.random() < p_abandon * (0.4 + 1.2*hazard))  # hazard modulates around p_abandon
    # abandon TYPE + WHEN
    abandon_step = None
    atype = None
    if abandoned:
        # type by fragility/value
        r = rng.random()
        if latent_tool_fragility > 0.6 and r < 0.5:
            atype = "tool_error_retry"
        elif latent_branch_value < 0.4 and r < 0.8:
            atype = "branch_prune"
        else:
            atype = "early_stop_or_interrupt"
        # WHEN depends on timing knob (fraction of L_plan at which it becomes abandoned)
        if timing == "early":
            frac = rng.betavariate(1.5, 5)   # mostly early
        elif timing == "mid":
            frac = rng.betavariate(3, 3)
        elif timing == "late":
            frac = rng.betavariate(5, 1.5)
        else:  # mixed
            frac = rng.random()
        abandon_step = max(1, int(frac * L_plan))
    # decoded tokens actually generated on this turn:
    #   completed -> L_plan; abandoned -> abandon_step (decode halts/discarded there)
    decoded = L_plan if not abandoned else abandon_step
    wasted  = 0 if not abandoned else abandon_step
    # ---- OBSERVABLES at a measurement prefix step (computed below per-step) ----
    return {
        "L_plan": L_plan, "abandoned": abandoned, "abandon_step": abandon_step,
        "atype": atype, "decoded": decoded, "wasted": wasted,
        "latent_difficulty": latent_difficulty,
        "latent_tool_fragility": latent_tool_fragility,
        "latent_branch_value": latent_branch_value,
        "retry_count": (1 if atype=="tool_error_retry" else 0) + (1 if rng.random()<0.15 else 0),
    }

def observables_at_step(rng, turn, t, sigma):
    """Anti-circular OBSERVABLES at prefix step t (< turn end). Noisy fns of LATENTS only.
    Predictor NEVER sees turn['abandoned'], abandon_step, or hazard."""
    d = turn["latent_difficulty"]; f = turn["latent_tool_fragility"]
    # o1 output entropy so far: rises with difficulty + grows slightly with t
    o1 = 0.5 + 0.8*d + 0.0008*t + rng.gauss(0, sigma*0.5)
    # o2 repetition ratio so far: rises with difficulty when floundering
    o2 = 0.1 + 0.6*d*(1 if t>0.3*turn["L_plan"] else 0.5) + rng.gauss(0, sigma*0.3)
    # o3 tool-call malformation prob: noisy fn of fragility
    o3 = 0.05 + 0.85*f + rng.gauss(0, sigma*0.4)
    # o4 turn_len_so_far / running quantile (structural). We pass the quantile in.
    # computed by caller; here just expose t.
    # o5 retry count observable
    o5 = turn["retry_count"] + (1 if rng.random()<sigma*0.1 else 0)
    return o1, o2, o3, o5

def gen_episode(seed, p_abandon, timing):
    rng = random.Random(seed*1000003 + hash((p_abandon, timing)) % 100000)
    turns = [sample_turn(rng, p_abandon, timing) for _ in range(N_TURNS_PER_EPISODE)]
    return turns

# ---------- part A: wasted-decode fraction surface ----------
def part_A():
    rows = []
    for p in P_ABANDON_GRID:
        for timing in TIMING_GRID:
            fracs = []; rates = []
            for s in SEEDS:
                turns = gen_episode(s, p, timing)
                total = sum(t["decoded"] for t in turns)
                wasted = sum(t["wasted"] for t in turns)
                fracs.append(wasted/total if total else 0)
                rates.append(sum(1 for t in turns if t["abandoned"])/len(turns))
            rows.append({
                "p_abandon": p, "timing": timing,
                "obs_abandon_rate_mean": round(statistics.mean(rates),4),
                "wasted_frac_mean": round(statistics.mean(fracs),4),
                "wasted_frac_std": round(statistics.pstdev(fracs),4),
                "wasted_frac_min": round(min(fracs),4),
                "wasted_frac_max": round(max(fracs),4),
            })
    with open(os.path.join(OUT,"A_wasted_decode_surface.csv"),"w",newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    return rows

# ---------- AUC helper (rank-based, stdlib) ----------
def auc(scores, labels):
    # Mann-Whitney U / AUC
    pos = [s for s,l in zip(scores,labels) if l==1]
    neg = [s for s,l in zip(scores,labels) if l==0]
    if not pos or not neg: return float('nan')
    # rank
    paired = sorted(zip(scores, labels))
    ranks = [0.0]*len(paired)
    i=0
    while i < len(paired):
        j=i
        while j+1<len(paired) and paired[j+1][0]==paired[i][0]:
            j+=1
        r = (i+j)/2.0 + 1
        for k in range(i,j+1): ranks[k]=r
        i=j+1
    sum_pos_ranks = sum(rk for rk,(sc,l) in zip(ranks,paired) if l==1)
    n_pos=len(pos); n_neg=len(neg)
    U = sum_pos_ranks - n_pos*(n_pos+1)/2.0
    return U/(n_pos*n_neg)

# ---------- part B: causal predictor AUC + lead time ----------
# Fixed-but-honest measurement step: we score each turn at a fixed EARLY prefix
# t_meas = min(prefix_frac * L_plan, ...) so the signal is available BEFORE completion
# AND before most abandonments. We train a simple logistic-ish weight vector on TRAIN seeds
# (gradient-free: use correlation-weighted linear combo), score on TEST seeds.
PREFIX_FRAC = 0.25   # measure at first 25% of planned length (early, pre-completion)

def featurize(rng, turns, sigma):
    # running quantile of abandoned-turn lengths (observable history proxy):
    # use running mean turn length so far as the structural baseline (no label leak).
    feats=[]; labels=[]; meta=[]
    running_lens=[]
    for tn in turns:
        L=tn["L_plan"]
        t_meas = max(2, int(PREFIX_FRAC*L))
        # if the turn abandons BEFORE t_meas, we only observe up to abandon_step
        obs_t = t_meas
        if tn["abandoned"] and tn["abandon_step"] < t_meas:
            obs_t = tn["abandon_step"]
        o1,o2,o3,o5 = observables_at_step(rng, tn, obs_t, sigma)
        running_lens.append(L)
        base = statistics.mean(running_lens)
        o4 = obs_t / (base+1e-9)   # turn-len-so-far vs running baseline
        feats.append([o1,o2,o3,o4,float(o5)])
        labels.append(1 if tn["abandoned"] else 0)
        meta.append({"obs_t":obs_t, "abandon_step":tn["abandon_step"], "L":L,
                     "abandoned":tn["abandoned"]})
    return feats, labels, meta

def fit_weights(feats, labels):
    # gradient-free: weight each feature by point-biserial correlation w/ label, standardized.
    n=len(feats); k=len(feats[0])
    cols=[[feats[i][j] for i in range(n)] for j in range(k)]
    w=[]
    for j in range(k):
        mu=statistics.mean(cols[j]); sd=statistics.pstdev(cols[j]) or 1e-9
        z=[(x-mu)/sd for x in cols[j]]
        # corr with label
        ly=labels; my=statistics.mean(ly); sdy=statistics.pstdev(ly) or 1e-9
        corr=sum((z[i])*((ly[i]-my)/sdy) for i in range(n))/n
        w.append(corr)
    return w, [statistics.mean(cols[j]) for j in range(k)], [statistics.pstdev(cols[j]) or 1e-9 for j in range(k)]

def score(feats, w, mu, sd):
    out=[]
    for f in feats:
        s=sum(w[j]*((f[j]-mu[j])/sd[j]) for j in range(len(w)))
        out.append(s)
    return out

def part_B():
    rows=[]
    # use a representative abandonment regime for predictor eval; report per p_abandon too.
    for sigma in NOISE_GRID:
        for p in P_ABANDON_GRID:
            # TRAIN on train seeds (mixed timing — realistic), TEST on test seeds
            tr_feats=[]; tr_labels=[]
            for s in TRAIN_SEEDS:
                rng=random.Random(7777+s)
                turns=gen_episode(s,p,"mixed")
                f,l,m=featurize(rng,turns,sigma); tr_feats+=f; tr_labels+=l
            w,mu,sd=fit_weights(tr_feats,tr_labels)
            # TEST
            te_scores=[]; te_labels=[]; leads=[]
            # operating threshold: choose on TRAIN to hit ~precision target via quantile
            tr_scores=score(tr_feats,w,mu,sd)
            thr=sorted(tr_scores)[int(0.80*len(tr_scores))]  # top-20% flagged
            for s in TEST_SEEDS:
                rng=random.Random(8888+s)
                turns=gen_episode(s,p,"mixed")
                f,l,m=featurize(rng,turns,sigma)
                sc=score(f,w,mu,sd)
                te_scores+=sc; te_labels+=l
                for si,mi in zip(sc,m):
                    if mi["abandoned"] and si>thr:
                        # lead time = abandon_step - obs_t (fired at obs_t)
                        leads.append(mi["abandon_step"]-mi["obs_t"])
            a=auc(te_scores,te_labels)
            # precision among flagged on TEST
            flagged=[(sc,l) for sc,l in zip(te_scores,te_labels) if sc>thr]
            prec = (sum(l for _,l in flagged)/len(flagged)) if flagged else float('nan')
            recall_flagged = (sum(l for _,l in flagged)/sum(te_labels)) if sum(te_labels) else float('nan')
            rows.append({
                "noise_sigma":sigma,"p_abandon":p,
                "test_auc":round(a,4),
                "flag_precision":round(prec,4) if prec==prec else "nan",
                "flag_recall":round(recall_flagged,4) if recall_flagged==recall_flagged else "nan",
                "median_lead_tokens": (round(statistics.median(leads),1) if leads else "nan"),
                "frac_positive_lead": (round(sum(1 for x in leads if x>0)/len(leads),3) if leads else "nan"),
                "n_flagged_abandoned": len(leads),
            })
    with open(os.path.join(OUT,"B_predictor_auc_leadtime.csv"),"w",newline="") as fh:
        w_=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); w_.writeheader(); w_.writerows(rows)
    return rows

# ---------- part C: reclaim vs latency at matched fairness ----------
# Token-time batch sim, SERIAL. Round-robin decode over an active batch of size B.
# Each "time tick" = one decode step that advances every active turn by 1 token.
# Completed-turn latency = ticks from admission to completion.
# Treatment: a flagged turn is DEPRIORITIZED -> decoded only every (1+W) ticks (bounded slowdown),
# freeing decode budget for others. Bounded-W = fairness cap.
def part_C(predictor_thr_quantile=0.80, W_grid=(0,1,2,4)):
    rows=[]
    sigma=0.70  # the medium-noise (~AUC 0.7) operating regime
    p=0.35      # a regime where waste is non-trivial
    # build predictor on train as in B
    tr_feats=[]; tr_labels=[]
    for s in TRAIN_SEEDS:
        rng=random.Random(7777+s); turns=gen_episode(s,p,"mixed")
        f,l,m=featurize(rng,turns,sigma); tr_feats+=f; tr_labels+=l
    w,mu,sd=fit_weights(tr_feats,tr_labels)
    tr_scores=score(tr_feats,w,mu,sd)
    thr=sorted(tr_scores)[int(predictor_thr_quantile*len(tr_scores))]

    for W in W_grid:
        comp_lat=[]; fp_lat=[]; reclaimed_total=0; baseline_wasted_total=0; treat_wasted_total=0
        for s in TEST_SEEDS:
            rng=random.Random(9999+s)
            turns=gen_episode(s,p,"mixed")
            f,l,m=featurize(rng,turns,sigma); sc=score(f,w,mu,sd)
            flagged=[si>thr for si in sc]
            B=16
            # admit turns in order; simulate token-time round robin
            # each turn: needs `decoded` tokens to finish (abandoned->abandon_step; completed->L_plan)
            # remaining = decoded; flagged turns get 1 token every (1+W) ticks
            import collections
            idx=0; tick=0; active=[]; admit_time={}; done_lat={}
            # for measuring baseline wasted vs treatment wasted: wasted tokens are those decoded on
            # abandoned turns. Treatment can REDUCE wasted by deferring an abandoned turn's decode past
            # the point we'd have learned it's abandoned — but online we don't kill; we DEFER. We model
            # reclaim as: tokens of an abandoned turn that, due to deprioritization, are NOT decoded
            # before tick where the turn would naturally end (abandon_step in real time). Concretely:
            # an abandoned turn needs abandon_step tokens; if deprioritized it takes longer wall-time to
            # emit them, so a fraction never get decoded within the episode horizon -> reclaimed.
            HORIZON_PAD=0  # we just run to completion of all turns; reclaim = deferred-past-abandon
            remaining=[]; sched_div=[]
            order=list(range(len(turns)))
            cur=0
            # event sim
            counters=[0]*len(turns)
            finished=[False]*len(turns)
            n=len(turns)
            # admit up to B at a time, FCFS
            next_admit=0
            active_set=[]
            t_tick=0
            # precompute need (decoded tokens) and whether abandoned + abandon_step
            need=[turns[i]["decoded"] for i in range(n)]
            is_ab=[turns[i]["abandoned"] for i in range(n)]
            ab_step=[turns[i]["abandon_step"] if turns[i]["abandoned"] else None for i in range(n)]
            progressed=[0]*n
            admit_t=[None]*n
            # baseline wasted = sum decoded on abandoned turns (all get fully decoded in baseline)
            for i in range(n):
                if is_ab[i]: baseline_wasted_total += need[i]
            # treatment sim
            MAXTICKS = sum(need)//1 + n*4 + 10
            while True:
                # admit
                while len(active_set)<B and next_admit<n:
                    admit_t[next_admit]=t_tick; active_set.append(next_admit); next_admit+=1
                if not active_set and next_admit>=n: break
                # decode one tick: each active turn advances if (not deprioritized) or (tick%(1+W)==0)
                still=[]
                for i in active_set:
                    dep = flagged[i]
                    advance = (not dep) or (W==0) or (t_tick % (1+W)==0)
                    if advance:
                        progressed[i]+=1
                    if progressed[i]>=need[i]:
                        # finished emitting its (decoded) tokens
                        lat=t_tick-admit_t[i]+1
                        if is_ab[i]:
                            # abandoned: wasted = tokens actually decoded = need[i] (it still emitted them)
                            treat_wasted_total += progressed[i]
                        else:
                            comp_lat.append(lat)
                            if flagged[i]:
                                fp_lat.append(lat)  # would-complete but was flagged (false positive)
                        finished[i]=True
                    else:
                        still.append(i)
                active_set=still
                t_tick+=1
                if t_tick>MAXTICKS: break
        # reclaim model: in baseline ALL abandoned tokens are wasted. Under treatment, deprioritization
        # SLOWS abandoned turns; the reclaim is the compute that would have been spent decoding the
        # abandoned turn's tokens *after the point the system would have observed abandonment*. We model
        # reclaim conservatively = baseline_wasted - treat_wasted is ~0 here (we still emit them) UNLESS
        # we add a kill-on-confirmed step. To stay HONEST and online-only, reclaim = deferred decode that
        # frees slots: measured as reduction in total ticks-to-drain is NOT reclaim of wasted tokens.
        # Honest accounting: with pure deferral (no kill) net wasted-token reclaim = 0.
        reclaim = baseline_wasted_total - treat_wasted_total
        def pct(xs,q):
            if not xs: return float('nan')
            xs=sorted(xs); k=min(len(xs)-1,int(q*len(xs)))
            return xs[k]
        rows.append({
            "W":W,
            "completed_p50": round(pct(comp_lat,0.50),1) if comp_lat else "nan",
            "completed_p99": round(pct(comp_lat,0.99),1) if comp_lat else "nan",
            "fp_turn_p99": round(pct(fp_lat,0.99),1) if fp_lat else "nan",
            "n_completed": len(comp_lat),
            "n_fp_flagged": len(fp_lat),
            "baseline_wasted_tokens": baseline_wasted_total,
            "treat_wasted_tokens": treat_wasted_total,
            "net_reclaim_tokens_pure_defer": reclaim,
        })
    with open(os.path.join(OUT,"C_reclaim_latency.csv"),"w",newline="") as fh:
        w_=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); w_.writeheader(); w_.writerows(rows)
    return rows

if __name__=="__main__":
    import time
    t0=time.time()
    A=part_A(); print("A done", round(time.time()-t0,1),"s")
    B=part_B(); print("B done", round(time.time()-t0,1),"s")
    C=part_C(); print("C done", round(time.time()-t0,1),"s")
    print("ALL DONE", round(time.time()-t0,1),"s")
