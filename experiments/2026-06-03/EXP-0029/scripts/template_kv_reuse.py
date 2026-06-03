#!/usr/bin/env python3
"""EXP-0029 L0: tool-result-schema template KV reuse vs exact-prefix (APC).
CPU-only, stdlib-only, SERIAL. Trust the CSV it writes, not stdout.

Three-way reuse measure per (new call) vs (cached prior call of SAME tool):
  (a) exact-prefix/APC  : tokens shared pos0 .. first differing token
  (b) template TOKEN-level (ceiling): all fixed-schema token positions regardless of value diffs
  (c) POSITION-AWARE (honest): schema tokens at IDENTICAL absolute position across the two requests
RoPE tax = (b) - (c).  schema-missed-by-APC = (b) - (a).
"""
import csv, os, random, statistics

BLOCK = 16
SEEDS = list(range(8))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

def make_tool_schema(rng, complexity):
    segs = [("S", ['{'])]
    n_fields = complexity
    keynames = ["status","code","rows","items","id","ts","msg","data","next","total","ok","url"]
    rng.shuffle(keynames)
    for i in range(n_fields):
        k = keynames[i % len(keynames)]
        if i > 0:
            segs.append(("S", [',']))
        segs.append(("S", ['"', k, '"', ':']))
        roll = rng.random()
        if roll < 0.25:
            segs.append(("S", ['"'])); segs.append(("V", (1, 3))); segs.append(("S", ['"']))
        elif roll < 0.55:
            segs.append(("V", (1, 2)))
        else:
            segs.append(("S", ['['])); segs.append(("V", (3, 30))); segs.append(("S", [']']))
    segs.append(("S", ['}']))
    return segs

def instantiate(schema, rng, value_len_mode):
    toks, is_schema = [], []
    for kind, payload in schema:
        if kind == "S":
            for t in payload:
                toks.append(("S", t)); is_schema.append(True)
        else:
            lo, hi = payload
            n = lo if value_len_mode == "fixed" else rng.randint(lo, hi)
            for _ in range(n):
                toks.append(("V", "v%d" % rng.randint(0, 10**9))); is_schema.append(False)
    return toks, is_schema

def measure_pair(cached_toks, cached_isS, new_toks, new_isS):
    Ln = len(new_toks)
    a = 0; m = min(len(cached_toks), Ln)
    while a < m and cached_toks[a] == new_toks[a]:
        a += 1
    b = sum(1 for s in new_isS if s)
    c = 0
    for p in range(Ln):
        if not new_isS[p]:
            continue
        if p < len(cached_toks) and cached_isS[p] and cached_toks[p] == new_toks[p]:
            c += 1
    return a, b, c, Ln

def run_condition(n_tools, complexity, value_len_mode, seed, calls_per_tool=12):
    rng = random.Random(1000 * seed + 7 * n_tools + complexity + (hash(value_len_mode) % 97))
    tools = [make_tool_schema(rng, complexity) for _ in range(n_tools)]
    tot_tok=tot_a=tot_b=tot_c=n_pairs=0
    for sch in tools:
        cached = None
        for ci in range(calls_per_tool):
            toks, isS = instantiate(sch, rng, value_len_mode)
            if cached is None:
                cached = (toks, isS); continue
            a,b,c,Ln = measure_pair(cached[0], cached[1], toks, isS)
            tot_tok+=Ln; tot_a+=a; tot_b+=b; tot_c+=c; n_pairs+=1
    return dict(n_tools=n_tools, complexity=complexity, mode=value_len_mode, seed=seed,
                pairs=n_pairs, tokens=tot_tok, a_prefix=tot_a, b_token_ceiling=tot_b, c_posaware=tot_c)

def main():
    rows=[]
    for mode in ("var","fixed"):
        for n_tools in (4,8,16):
            for complexity in (3,6):
                for seed in SEEDS:
                    rows.append(run_condition(n_tools, complexity, mode, seed))
    raw=os.path.join(OUT,"template_kv_reuse_raw.csv")
    with open(raw,"w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader()
        for r in rows: w.writerow(r)
    agg=os.path.join(OUT,"template_kv_reuse_agg.csv")
    keys=sorted(set((r["mode"],r["n_tools"],r["complexity"]) for r in rows))
    with open(agg,"w",newline="") as f:
        w=csv.writer(f)
        w.writerow(["mode","n_tools","complexity","prefix_frac_mean","prefix_frac_std",
                    "token_ceiling_frac_mean","token_ceiling_frac_std","posaware_frac_mean","posaware_frac_std",
                    "schema_missed_by_apc_mean","rope_tax_mean","posaware_beyond_prefix_mean","posaware_over_ceiling_mean"])
        for (mode,nt,cx) in keys:
            grp=[r for r in rows if r["mode"]==mode and r["n_tools"]==nt and r["complexity"]==cx]
            pf=[r["a_prefix"]/r["tokens"] for r in grp]
            tf=[r["b_token_ceiling"]/r["tokens"] for r in grp]
            cf=[r["c_posaware"]/r["tokens"] for r in grp]
            miss=[(r["b_token_ceiling"]-r["a_prefix"])/r["tokens"] for r in grp]
            tax=[(r["b_token_ceiling"]-r["c_posaware"])/r["tokens"] for r in grp]
            beyond=[(r["c_posaware"]-r["a_prefix"])/r["tokens"] for r in grp]
            ratio=[(r["c_posaware"]/r["b_token_ceiling"]) if r["b_token_ceiling"]>0 else 0 for r in grp]
            def ms(x): return (round(statistics.mean(x),4), round(statistics.pstdev(x),4))
            pm,ps=ms(pf); tm,ts=ms(tf); cm,cs=ms(cf)
            w.writerow([mode,nt,cx,pm,ps,tm,ts,cm,cs,
                        round(statistics.mean(miss),4),round(statistics.mean(tax),4),
                        round(statistics.mean(beyond),4),round(statistics.mean(ratio),4)])
    print("WROTE",raw,"and",agg,"rows=",len(rows))

if __name__=="__main__":
    main()
