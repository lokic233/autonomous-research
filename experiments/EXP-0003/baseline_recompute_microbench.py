"""
EXP-0003 (CLAIM-0006, Lane A) — CPU-ONLY recompute-fraction microbench.
Positions CDC (~2%) head-to-head vs the 3 mandatory baselines under a single MID-PREFIX
TOOL INSERTION (tokens spliced in at fractional position f; original suffix preserved).

Arms (all are reuse/recompute-COUNT models on token streams; NO GPU, NO kernels):
  1. vLLM APC  : fixed 16-tok blocks, hash(prefix+block), CONTIGUOUS longest-prefix match.
                 (uses the same fixed-block / contiguous-prefix logic vLLM's hash_block_tokens implies)
  2. RadixAttention (SGLang): token-granularity (page=1 tok) radix-tree SHARED-PREFIX match.
                 = recompute everything after the first divergent token. (DEAD-0006 falsification arm.)
  3. FlashInfer: kernel lib, no cache policy of its own -> recompute fraction == host engine
                 (we report it == best host engine = RadixAttention, its typical pairing).
  4. CDC       : content-defined chunking (rolling-hash boundaries) -> downstream chunks RE-SYNC.
                 (verbatim mechanism from sess 048fcb0d nt2_cdc.py)

Metric: recompute_fraction = recomputed_units / total_units after the insertion.
We report fraction in TOKENS (common denominator) so arms are comparable despite differing grain.
"""
import json, hashlib, random
random.seed(0)

def hfn(b): return hashlib.blake2b(repr(b).encode(), digest_size=16).digest()

def fixed_blocks(tokens, B=16):
    return [tuple(tokens[i:i+B]) for i in range(0, len(tokens)-B+1, B)]

def cdc_blocks(tokens, tgt=16, mask=0xF):
    blocks=[]; cur=[]
    for t in tokens:
        cur.append(t)
        if (int.from_bytes(hashlib.blake2b(str(t).encode(),digest_size=2).digest(),"little") & mask)==0 or len(cur)>=2*tgt:
            blocks.append(tuple(cur)); cur=[]
    if cur: blocks.append(tuple(cur))
    return blocks

def vllm_recompute_tokens(base, contam, B=16):
    fb_base=fixed_blocks(base); fb_con=fixed_blocks(contam)
    cached=set(hfn(b) for b in fb_base)
    first=next((i for i in range(min(len(fb_base),len(fb_con))) if hfn(fb_con[i]) not in cached), len(fb_con))
    rec_blocks=len(fb_con)-first
    return rec_blocks*B, len(fb_con)*B  # recomputed tokens (approx, full suffix from first diverged block)

def radix_recompute_tokens(base, contam):
    # token-granularity shared-prefix: reuse the longest common token prefix, recompute the rest.
    n=min(len(base),len(contam))
    lcp=0
    while lcp<n and base[lcp]==contam[lcp]: lcp+=1
    return len(contam)-lcp, len(contam)

def cdc_recompute_tokens(base, contam):
    cb_base=cdc_blocks(base); cb_con=cdc_blocks(contam)
    cached=set(hfn(b) for b in cb_base)
    rec_tokens=sum(len(b) for b in cb_con if hfn(b) not in cached)
    return rec_tokens, sum(len(b) for b in cb_con)

R={"experiment":"EXP-0003","claim":"CLAIM-0006","device":"CPU","model":"recompute-fraction (token-count) under single mid-prefix insertion","tool_insert_len":40,"rows":[]}
TOOL=40
for CTX in [4000, 8000, 32000]:
    base=[random.randint(10,50000) for _ in range(CTX)]
    tool=[random.randint(10,50000) for _ in range(TOOL)]
    for f in [0.1,0.25,0.5,0.75,0.9]:
        p=int(CTX*f)
        contam=base[:p]+tool+base[p:]
        v_rec,v_tot=vllm_recompute_tokens(base,contam)
        r_rec,r_tot=radix_recompute_tokens(base,contam)
        c_rec,c_tot=cdc_recompute_tokens(base,contam)
        row={
          "ctx":CTX,"inject_frac":f,
          "vllm_apc_recompute_pct":round(100*v_rec/v_tot,2),
          "radix_recompute_pct":round(100*r_rec/r_tot,2),
          "flashinfer_recompute_pct":round(100*r_rec/r_tot,2),  # == host engine (radix), no policy of its own
          "cdc_recompute_pct":round(100*c_rec/c_tot,2),
          "cdc_vs_radix_x":round((r_rec/max(c_rec,1)),1),
          "cdc_vs_vllm_x":round((v_rec/max(c_rec,1)),1),
        }
        R["rows"].append(row)
# falsification check: does RadixAttention also drop to ~CDC level? (DEAD-0006 test)
R["radix_min_recompute_pct"]=round(min(r["radix_recompute_pct"] for r in R["rows"]),2)
R["radix_max_recompute_pct"]=round(max(r["radix_recompute_pct"] for r in R["rows"]),2)
R["cdc_max_recompute_pct"]=round(max(r["cdc_recompute_pct"] for r in R["rows"]),2)
R["DEAD0006_collapse"]= R["radix_min_recompute_pct"] <= R["cdc_max_recompute_pct"]*1.5  # if radix ~ CDC -> claim dead
print(json.dumps(R,indent=2))
json.dump(R,open("/Users/dengcchi/autonomous-research/experiments/EXP-0003/results.json","w"),indent=2)
