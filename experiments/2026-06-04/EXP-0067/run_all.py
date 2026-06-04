#!/usr/bin/env python3
import sys, time, csv, json, statistics, math
sys.path.insert(0, "/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0067/")
exec(open("/Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0067/harness.py").read())

t0=time.time()
SEEDS=[0,1,2,3,4]; N=30000; CHUNKS=[1,2,4,8,16,32]
DS={s:synth_dataset(N,seed=s) for s in SEEDS}

ARMS={"stateless":arm_stateless,
      "sliding_W16":(lambda t,C,W:arm_sliding(t,C,16)),
      "unbounded":arm_unbounded}

# SWEEP 1: recall vs C per arm
rows1=[]
for an,fn in ARMS.items():
    for C in CHUNKS:
        for s in SEEDS:
            rmt,_=recall_for(DS[s],fn,C,None,only_multitoken=True)
            rall,_=recall_for(DS[s],fn,C,None,only_multitoken=False)
            rows1.append({"arm":an,"C":C,"seed":s,"recall_multitoken":rmt,"recall_all":rall})
with open(ART+"recall_by_chunk_arm.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["arm","C","seed","recall_multitoken","recall_all"]);w.writeheader();w.writerows(rows1)
print("sweep1",round(time.time()-t0,1),"s",flush=True)

# SWEEP 2: recall vs overlap-W for sliding arm at C in {8,16}
rows2=[]
WS=[0,2,4,8,16,32,64]
for C in (8,16):
    for W in WS:
        fn=(lambda t,Cc,Ww: arm_stateless(t,Cc,None)) if W==0 else (lambda t,Cc,Ww,Wfix=W: arm_sliding(t,Cc,Wfix))
        for s in SEEDS:
            rmt,_=recall_for(DS[s],fn,C,None,only_multitoken=True)
            rows2.append({"C":C,"W":W,"seed":s,"recall_multitoken":rmt})
with open(ART+"recall_by_overlap.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["C","W","seed","recall_multitoken"]);w.writeheader();w.writerows(rows2)
print("sweep2",round(time.time()-t0,1),"s",flush=True)

# SWEEP 3: phrase-length control at fixed C=8, stateless arm
rows3=[]
for plen in (1,2,3,4):
    for s in SEEDS:
        r,tot=recall_for(DS[s],arm_stateless,8,None,plen_filter=plen)
        rows3.append({"C_fixed":8,"phrase_len":plen,"seed":s,"recall":r,"n":tot})
with open(ART+"recall_by_phraselen.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["C_fixed","phrase_len","seed","recall","n"]);w.writeheader();w.writerows(rows3)
print("sweep3",round(time.time()-t0,1),"s",flush=True)

# AGGREGATE
def agg(rows,keyf,valf):
    from collections import defaultdict
    d=defaultdict(list)
    for r in rows: d[keyf(r)].append(valf(r))
    return {k:ci95(v) for k,v in d.items()}

a1mt=agg(rows1,lambda r:(r["arm"],r["C"]),lambda r:r["recall_multitoken"])
a2=agg(rows2,lambda r:(r["C"],r["W"]),lambda r:r["recall_multitoken"])
a3=agg(rows3,lambda r:r["phrase_len"],lambda r:r["recall"])

summary={"max_phrase_len":MAX_PHRASE_LEN,
         "sweep1_recall_mt":{f"{k[0]}|C={k[1]}":[round(v[0],4),round(v[1],4)] for k,v in a1mt.items()},
         "sweep2_recall_mt":{f"C={k[0]}|W={k[1]}":[round(v[0],4),round(v[1],4)] for k,v in a2.items()},
         "sweep3_phraselen":{f"plen={k}":[round(v[0],4),round(v[1],4)] for k,v in a3.items()}}
with open(ART+"summary.json","w") as f: json.dump(summary,f,indent=2)
print("TOTAL",round(time.time()-t0,1),"s",flush=True)
print(json.dumps(summary,indent=2))
