"""Part C KILL variant: the ONLY way deprioritization reclaims compute is to actually STOP decoding a
flagged turn (preempt/kill), not merely slow it. We model KILL-ON-FLAG with a bounded budget: a flagged
turn is preempted at its flag step (obs_t). Reclaim = tokens that would have been decoded after obs_t.
HARM = false positives: turns that WOULD have completed but were killed -> they NEVER complete (lost
work + the user must retry). We report reclaimed tokens, FP-kill count, and the lost completed-turns.
This makes the precision/recall tradeoff at AUC~0.71 fully explicit and honest. CPU/stdlib/serial."""
import sys,os,random,statistics,csv
sys.path.insert(0,".")
import harness as H, sharpen as S
OUT=H.OUT
SHARP=16; SIGMA=0.10; P=0.30

def run(thr_quantiles=(0.70,0.80,0.90,0.95)):
    trf=[];trl=[]
    for s in H.TRAIN_SEEDS:
        rng=random.Random(7777+s); F,L,M=S.P.feats_labels(rng,S.gen_ep(s,P,"mixed",SHARP),SIGMA); trf+=F;trl+=L
    w,mu,sd=H.fit_weights(trf,trl); trs=H.score(trf,w,mu,sd)
    rows=[]
    # gather test turns + scores + flag steps once
    test=[]
    for s in H.TEST_SEEDS:
        rng=random.Random(9999+s); turns=S.gen_ep(s,P,"mixed",SHARP)
        F,L,M=S.P.feats_labels(rng,turns,SIGMA); sc=H.score(F,w,mu,sd)
        test.append((turns,sc,M))
    for q in thr_quantiles:
        thr=sorted(trs)[int(q*len(trs))]
        reclaimed=0; fp_kills=0; tp_kills=0; lost_completed=0; total_completed=0
        total_decoded=0; total_abandoned=0
        for turns,sc,M in test:
            for t,si,mi in zip(turns,sc,M):
                total_decoded+=t["decoded"]
                if t["abandoned"]: total_abandoned+=1
                else: total_completed+=1
                if si>thr:  # KILL at obs_t
                    ot=mi["ot"]
                    if t["abandoned"]:
                        tp_kills+=1
                        # reclaim = tokens it WOULD have decoded after obs_t before self-terminating
                        reclaimed += max(0, t["abandon_step"]-ot)
                    else:
                        fp_kills+=1
                        lost_completed+=1
                        # NEGATIVE reclaim risk: we killed useful work = ot tokens already spent wasted,
                        # plus the turn must be re-run. We count lost completed turns as the HARM.
        rows.append({"thr_quantile":q,"obs_auc_regime":0.708,
            "tp_kills":tp_kills,"fp_kills":fp_kills,
            "kill_precision":round(tp_kills/(tp_kills+fp_kills),4) if (tp_kills+fp_kills) else "nan",
            "reclaimed_decode_tokens":reclaimed,
            "reclaim_pct_of_total":round(100*reclaimed/total_decoded,3) if total_decoded else 0,
            "lost_completed_turns":lost_completed,
            "lost_completed_pct":round(100*lost_completed/total_completed,3) if total_completed else 0,
            "total_completed":total_completed,"total_abandoned":total_abandoned})
    with open(os.path.join(OUT,"C2_kill_reclaim_vs_harm.csv"),"w",newline="") as fh:
        wr=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
    return rows
for r in run(): print(r)
