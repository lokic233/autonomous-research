"""
EXP-0002 Lane-B CDC cost-surface (CPU-ONLY, token-proxy recompute fraction; NO GPU/torch/CUDA).
Extends original nt2_cdc microbench across axes it held fixed: seq length, injection token count,
edit POSITION incl. prepend & terminal. Same CDC reuse model (content-defined chunking, set-membership).
"""
import json, hashlib, random, statistics

def cdc_blocks(tokens, tgt=16, mask=0xF):
    blocks=[]; cur=[]
    for t in tokens:
        cur.append(t)
        if (int.from_bytes(hashlib.blake2b(str(t).encode(),digest_size=2).digest(),"little") & mask)==0 or len(cur)>=2*tgt:
            blocks.append(tuple(cur)); cur=[]
    if cur: blocks.append(tuple(cur))
    return blocks

def hfn(b): return hashlib.blake2b(repr(b).encode(),digest_size=16).digest()

def cdc_recompute_pct(base, contam):
    cb_base=cdc_blocks(base); cb_con=cdc_blocks(contam)
    cached=set(hfn(b) for b in cb_base)
    rec=sum(1 for b in cb_con if hfn(b) not in cached)
    return rec, len(cb_con), 100.0*rec/len(cb_con)

def make_contam(base, edit_pos, inj):
    tool=[random.randint(10,50000) for _ in range(inj)]
    return base[:edit_pos]+tool+base[edit_pos:]

results={"experiment":"EXP-0002_cdc_cost_surface","method":"CPU token-proxy (set-membership CDC reuse), NO GPU","reps":3,"surface":[]}
seq_lens   = [1000, 4000, 16000, 64000]
inj_counts = [1, 10, 40, 200, 1000]
pos_fracs  = [0.0, 0.1, 0.5, 0.9, 1.0]
REPS=3
for CTX in seq_lens:
    for inj in inj_counts:
        for pf in pos_fracs:
            pcts=[]
            for r in range(REPS):
                random.seed(1000*CTX+inj+int(pf*100)+r)
                base=[random.randint(10,50000) for _ in range(CTX)]
                epos=int(CTX*pf)
                _,_,pct=cdc_recompute_pct(base, make_contam(base, epos, inj))
                pcts.append(pct)
            mean=sum(pcts)/len(pcts)
            results["surface"].append({"seq_len":CTX,"inject_tokens":inj,"edit_pos_frac":pf,
                "cdc_recompute_pct_mean":round(mean,2),"cdc_recompute_pct_min":round(min(pcts),2),"cdc_recompute_pct_max":round(max(pcts),2)})
json.dump(results, open("/tmp/exp0002_surface.json","w"), indent=2)
print("rows:", len(results["surface"]))
allp=[r["cdc_recompute_pct_mean"] for r in results["surface"]]
print("global min/median/max recompute%:", round(min(allp),2), round(statistics.median(allp),2), round(max(allp),2))
