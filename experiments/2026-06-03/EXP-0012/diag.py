import random, statistics
import sim
# Diagnose: why is AUC low/flat? Check (a) overall-ref AUC, (b) critical-handle AUC,
# (c) how separable handles are by obs at low sigma.
for sigma in [0.0,0.02,0.05,0.1,0.2,0.4,0.8]:
    overall=[]; crit=[]
    for seed in range(16):
        rng=random.Random((seed*1000003)^int(sigma*1e6) if sigma>0 else seed*1000003)
        spans,fr,cr=sim.generate_trace(rng)
        obs=sim.make_observables(rng,spans,sigma)
        refset=set(i for(_,i) in fr); critset=set(i for(_,i) in cr)
        # overall
        lab=[1 if s["idx"] in refset else 0 for s in spans]
        overall.append(sim.measure_auc(obs,lab))
        # critical-handle: label = is this span a delayed handle that gets critically referenced
        labc=[1 if s["idx"] in critset else 0 for s in spans]
        crit.append(sim.measure_auc(obs,labc))
    print(f"sigma={sigma:<5} overall_AUC={statistics.mean(overall):.3f}  critical_handle_AUC={statistics.mean(crit):.3f}")
