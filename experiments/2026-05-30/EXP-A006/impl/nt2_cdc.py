"""
NT2 v2 — the REAL repair. The cascade under mid-prompt injection is NOT just hash-chaining;
inserting tokens SHIFTS all downstream block boundaries so every later block's CONTENT changes
(fixed-size 16-tok blocks re-align). NT2 v1 (de-chained segmented hash) FAILED (1.0x) — honest
null. The correct repair is CONTENT-DEFINED CHUNKING (CDC): block boundaries set by content
(rolling hash), not fixed positions, so an insertion only creates/changes boundaries LOCALLY
and downstream chunks re-sync to their original content => reusable.
"""
import json, hashlib, random
random.seed(0)
def hfn(b): return hashlib.blake2b(repr(b).encode(),digest_size=16).digest()

def fixed_blocks(tokens, B=16):
    return [tuple(tokens[i:i+B]) for i in range(0,len(tokens)-B+1,B)]

def cdc_blocks(tokens, tgt=16, mask=0xF):
    """Content-defined chunking: cut after a token whose rolling hash hits a boundary
    condition; target avg chunk ~tgt tokens. Insertion only perturbs local chunks."""
    blocks=[]; cur=[]
    for t in tokens:
        cur.append(t)
        # boundary if hash(token) low bits == 0, OR chunk too big (cap 2*tgt)
        if (int.from_bytes(hashlib.blake2b(str(t).encode(),digest_size=2).digest(),"little") & mask)==0 or len(cur)>=2*tgt:
            blocks.append(tuple(cur)); cur=[]
    if cur: blocks.append(tuple(cur))
    return blocks

def reuse(base_blocks, contam_blocks):
    cached=set(hfn(b) for b in base_blocks)
    rec=sum(1 for b in contam_blocks if hfn(b) not in cached)
    return rec, len(contam_blocks), round(100*rec/len(contam_blocks),1)

R={"experiment":"NT2v2_content_defined_chunking_repair"}
CTX=4000
base=[random.randint(10,50000) for _ in range(CTX)]
tool=[random.randint(10,50000) for _ in range(40)]
rows=[]
for frac in [0.1,0.25,0.5,0.75,0.9]:
    pos=int(CTX*frac)
    contam=base[:pos]+tool+base[pos:]
    # fixed (vLLM) — recompute everything after first shifted block
    fb_base=fixed_blocks(base); fb_con=fixed_blocks(contam)
    fb_cached=set(hfn(b) for b in fb_base)
    # contiguous prefix-cache: reuse up to first miss, recompute rest
    first=next((i for i in range(min(len(fb_base),len(fb_con))) if hfn(fb_con[i]) not in fb_cached), len(fb_con))
    fixed_rec=len(fb_con)-first
    # CDC repair
    cb_base=cdc_blocks(base); cb_con=cdc_blocks(contam)
    cdc_rec, cdc_tot, cdc_pct = reuse(cb_base, cb_con)
    rows.append({"inject_frac":frac,
                 "fixed_recompute_blocks":fixed_rec,"fixed_total":len(fb_con),
                 "fixed_recompute_pct":round(100*fixed_rec/len(fb_con),1),
                 "cdc_recompute_blocks":cdc_rec,"cdc_total":cdc_tot,"cdc_recompute_pct":cdc_pct,
                 "reduction_x":round(fixed_rec/max(cdc_rec,1),1)})
R["rows"]=rows
R["claim_supported"]=all(r["fixed_recompute_blocks"] > r["cdc_recompute_blocks"]*2 for r in rows)
print(json.dumps(R,indent=2)); json.dump(R,open("nt2v2_result.json","w"),indent=2)
