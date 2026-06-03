#!/usr/bin/env python3
"""Diagnostic: WHERE does position-aware schema reuse survive?
Hypothesis: only the leading schema span BEFORE the first variable value is position-stable;
everything after the first variable-length value is shifted (RoPE-dead). Confirm by measuring
position-aware reuse as a fraction of (prefix-schema) vs (post-first-value schema)."""
import csv, os, random, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import template_kv_reuse as T

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"results")

def first_value_pos(isS):
    for p,s in enumerate(isS):
        if not s: return p
    return len(isS)

def run(n_tools=8, complexity=6, seed=0, calls_per_tool=12):
    rng=random.Random(99*seed+n_tools+complexity)
    tools=[T.make_tool_schema(rng,complexity) for _ in range(n_tools)]
    pre_total=pre_reuse=post_total=post_reuse=0
    for sch in tools:
        cached=None
        for ci in range(calls_per_tool):
            toks,isS=T.instantiate(sch,rng,"var")
            if cached is None: cached=(toks,isS); continue
            fv=first_value_pos(isS)  # first variable value position in NEW
            ct,ci2=cached
            for p in range(len(toks)):
                if not isS[p]: continue
                reusable = (p<len(ct) and ci2[p] and ct[p]==toks[p])
                if p < fv:
                    pre_total+=1; pre_reuse+=1 if reusable else 0
                else:
                    post_total+=1; post_reuse+=1 if reusable else 0
            cached=cached  # keep first as cache
    return pre_total,pre_reuse,post_total,post_reuse

rows=[]
for seed in range(8):
    pt,pr,qt,qr=run(seed=seed)
    rows.append((seed,pt,pr,qt,qr))
with open(os.path.join(OUT,"diag_where.csv"),"w",newline="") as f:
    w=csv.writer(f); w.writerow(["seed","preval_schema_tok","preval_reused","postval_schema_tok","postval_reused"])
    for r in rows: w.writerow(r)
PT=sum(r[1] for r in rows); PR=sum(r[2] for r in rows); QT=sum(r[3] for r in rows); QR=sum(r[4] for r in rows)
print("PRE-first-value schema tokens: reuse %.4f (%d/%d)"%(PR/PT,PR,PT))
print("POST-first-value schema tokens: reuse %.4f (%d/%d)"%(QR/QT if QT else 0,QR,QT))
print("=> of ALL schema tokens, fraction that are POST-first-value: %.4f"%(QT/(PT+QT)))
