# Honest amplification check: vary fact-universe size so restore_rate actually drives amplification
# (not universe exhaustion). amplification = fraction of writes whose fact_id already seen.
import random
def amp(seed,n_facts,T,restore_rate):
    rng=random.Random(seed); seen=set(); seen_list=[]; canon=0; td=0
    for t in range(T):
        if seen_list and rng.random()<restore_rate:
            fid=rng.choice(seen_list)
        else:
            if canon>=n_facts:
                fid=rng.choice(seen_list) if seen_list else 0
            else:
                fid=canon; canon+=1; seen_list.append(fid)
        if fid in seen: td+=1
        seen.add(fid)
    return td/T
print(f"{'n_facts':>8}{'restore':>8}{'T':>6} | {'amplification':>14}  >25%?")
for nf in [250, 1000, 5000]:   # 250=saturates, 5000=no saturation at T=1000
    for rr in [0.2,0.4,0.6]:
        vals=[amp(s,nf,1000,rr) for s in range(5)]
        a=sum(vals)/len(vals)
        print(f"{nf:>8}{rr:>8}{1000:>6} | {a:>14.3f}  {'YES' if a>0.25 else 'no'}")
print("DONE")
