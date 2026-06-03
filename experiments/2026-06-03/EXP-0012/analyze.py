#!/usr/bin/env python3
# Analysis — reads on-disk results.csv (TRUTH). Paired bootstrap CI on (CAUSAL - H2O) and
# (CAUSAL - RT) per AUC regime per budget. Decides held/partial/negative per PREREGISTRATION sec 7.
# X-AXIS = critical-handle AUC (decision-relevant: predictor's ability to ID the delayed-callback
# spans whose re-reference GATES task success). overall-ref AUC also reported.
import csv, os, random, statistics
ART = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(ART, "results", "results.csv"))))
for r in rows:
    r["sigma"]=float(r["sigma"]); r["seed"]=int(r["seed"]); r["auc"]=float(r["auc"])
    r["crit_auc"]=float(r["crit_auc"]); r["frac"]=float(r["frac"])
    r["m1_avail"]=float(r["m1_avail"]); r["m2_task"]=float(r["m2_task"])

sigmas = sorted(set(r["sigma"] for r in rows))
auc_by_sigma  = {sg: statistics.mean(r["auc"] for r in rows if r["sigma"]==sg) for sg in sigmas}
crit_by_sigma = {sg: statistics.mean(r["crit_auc"] for r in rows if r["sigma"]==sg) for sg in sigmas}

def paired_boot(deltas, B=5000, seed=0):
    rng = random.Random(seed); n=len(deltas); means=[]
    for _ in range(B):
        means.append(sum(deltas[rng.randrange(n)] for _ in range(n))/n)
    means.sort(); return means[int(0.025*B)], means[int(0.975*B)]

def get(sigma, frac, policy, metric):
    return {r["seed"]: r[metric] for r in rows if r["sigma"]==sigma and r["frac"]==frac and r["policy"]==policy}

fracs = sorted(set(r["frac"] for r in rows))
lines=["# EXP-0012 ANALYSIS (from on-disk results.csv)\n"]
lines.append("X-AXIS = critical-handle AUC (decision-relevant). overall-ref AUC reported alongside.\n")
lines.append("measured AUC by sigma:")
for sg in sigmas:
    lines.append(f"  sigma={sg}: critical-handle AUC={crit_by_sigma[sg]:.3f} | overall-ref AUC={auc_by_sigma[sg]:.3f}")

summary=[]
for metric in ["m2_task","m1_avail"]:
    lines.append(f"\n## METRIC = {metric}\n")
    lines.append("| crit_AUC | overall_AUC | budget_frac | CAUSAL | H2O | RT | ORACLE | (CAUSAL-H2O) 95%CI | (CAUSAL-RT) 95%CI | beats_H2O | beats_RT |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for sg in sigmas:
        cauc=crit_by_sigma[sg]; oauc=auc_by_sigma[sg]
        for fr in fracs:
            c=get(sg,fr,"CAUSAL",metric); h=get(sg,fr,"H2O",metric)
            rt=get(sg,fr,"RT",metric); o=get(sg,fr,"ORACLE",metric)
            seeds=sorted(c)
            cm=statistics.mean(c.values()); hm=statistics.mean(h.values())
            rtm=statistics.mean(rt.values()); om=statistics.mean(o.values())
            dh=[c[s]-h[s] for s in seeds]; dr=[c[s]-rt[s] for s in seeds]
            dhlo,dhhi=paired_boot(dh); drlo,drhi=paired_boot(dr)
            bh=dhlo>0; br=drlo>0
            lines.append(f"| {cauc:.3f} | {oauc:.3f} | {fr} | {cm:.3f} | {hm:.3f} | {rtm:.3f} | {om:.3f} | [{dhlo:+.3f},{dhhi:+.3f}] | [{drlo:+.3f},{drhi:+.3f}] | {'YES' if bh else 'no'} | {'YES' if br else 'no'} |")
            summary.append((metric,cauc,oauc,fr,cm,hm,rtm,om,dhlo,dhhi,drlo,drhi,bh,br))

lines.append("\n## DECISION (PREREGISTRATION sec 7) — realistic = critical-handle AUC < 0.85\n")
held=[]; needs_high=[]; partial=[]
for (metric,cauc,oauc,fr,cm,hm,rtm,om,dhlo,dhhi,drlo,drhi,bh,br) in summary:
    if metric!="m2_task": continue
    realistic = cauc < 0.85
    if bh and br and realistic: held.append((cauc,fr,dhlo,dhhi,om))
    elif bh and br and not realistic: needs_high.append((cauc,fr,dhlo,dhhi))
    elif (bh and not br) or (br and not bh): partial.append((cauc,fr,bh,br))

if held:
    verdict="HELD"
    lines.append(f"**HELD**: CAUSAL strictly beats BOTH H2O and RT (paired 95%CI_lo>0) at REALISTIC critical-handle AUC(<0.85) in {len(held)} (AUC,budget) cells on the sharp task metric m2_task:")
    for (cauc,fr,lo,hi,om) in held:
        lines.append(f"  - crit_AUC={cauc:.3f}, frac={fr}: (CAUSAL-H2O) 95%CI=[{lo:+.3f},{hi:+.3f}] | oracle headroom={om:.3f}")
elif needs_high and not held:
    verdict="PARTIAL"; lines.append("**PARTIAL**: beats H2O+RT only at AUC>=0.85 (unrealistic).")
elif partial and not held:
    verdict="PARTIAL"; lines.append("**PARTIAL**: beats only one baseline (RT-only strawman risk) at realistic AUC.")
else:
    verdict="NEGATIVE"; lines.append("**NEGATIVE (a WIN)**: CAUSAL does NOT strictly beat H2O at any realistic AUC/budget.")

# strawman guard: confirm there is at least one cell where it beats H2O specifically (not just RT)
beats_h2o_realistic = [(cauc,fr) for (metric,cauc,oauc,fr,cm,hm,rtm,om,dhlo,dhhi,drlo,drhi,bh,br) in summary
                       if metric=="m2_task" and bh and cauc<0.85]
lines.append(f"\nStrawman guard: cells where CAUSAL beats **H2O specifically** at realistic AUC: {len(beats_h2o_realistic)} -> {beats_h2o_realistic}")
lines.append(f"\n### VERDICT: {verdict}\n")
open(os.path.join(ART,"RESULTS_TABLE.md"),"w").write("\n".join(lines))
print("\n".join(lines)); print("\nVERDICT_TOKEN="+verdict)
