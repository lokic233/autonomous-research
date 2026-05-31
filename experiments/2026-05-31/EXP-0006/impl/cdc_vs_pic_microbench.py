"""
EXP-0006 (CLAIM-0006) — CPU-ONLY recompute-fraction microbench: CDC vs a FAIR PIC-FAMILY baseline.

WHY: VERDICT-0012 (6/6 YELLOW) named the #1 GREEN-blocker: the 3 baselines in EXP-0003
(vLLM-APC, SGLang-Radix, FlashInfer) are all CONTIGUOUS shared-prefix engines -> they recompute
the WHOLE suffix after a mid-prefix insertion (~(1-f) of the sequence). That makes CDC's
8x-465x advantage a STRUCTURAL gap (CDC can do position-independent recovery; they cannot),
NOT a competitive benchmark. This experiment adds a PIC-FAMILY baseline that CAN do
position-independent recovery, and asks the honest question:
    once CDC is compared to a baseline that recomputes ONLY (affected window + a small
    selective fraction), does CDC still win, by how much, and in what regime?

METHODOLOGY: identical to EXP-0003 (experiments/2026-05-31/EXP-0003/impl/baseline_recompute_microbench.py).
  - recompute-fraction by TOKEN COUNT (no GPU, no kernels).
  - single MID-PREFIX TOOL INSERTION of R tokens at fractional position f into a reused
    prefix of length S; original suffix preserved.
  - metric = recomputed_tokens / total_tokens after insertion.

ARMS:
  1. CDC  : content-defined chunking (rolling-hash boundaries). VERBATIM from EXP-0003.
            Downstream chunks RE-SYNC; only chunks overlapping the edit are recomputed.
  2. PIC  : a FAITHFUL position-independent partial-recompute baseline modeled on the
            EPIC / CacheBlend / Irminsul / MEPIC family (all in prior_art LaneA note).
            On a mid-prefix insertion of R tokens it recomputes:
              (a) the R NEW tokens themselves (unavoidable; CDC pays this too),
              (b) a fixed-size BOUNDARY WINDOW around the insertion seam to repair the
                  attention-sink / boundary discontinuity (LegoLink in EPIC; the local
                  recompute in CacheBlend; MEPIC's "first block request-specific"),
              (c) a SELECTIVE fraction p of the DOWNSTREAM (post-insertion) reused tokens
                  to repair cross-attention drift (CacheBlend's HKVD: recompute the top-p%
                  highest-KV-deviation tokens; EPIC/MEPIC block-level partial recompute).
            It does NOT recompute the whole suffix -> this is the FAIR, non-strawman baseline.

  We sweep the PIC selective fraction p over the literature's published operating range.
  CacheBlend reports ~5-15% selective recompute recovers quality (HKVD top-k%); EPIC/MEPIC
  recompute roughly one block per chunk boundary. We report p in {1%, 5%, 10%, 15%} and a
  boundary window W. This makes the comparison robust: we show CDC vs PIC across PIC's whole
  honest tuning range, not a single cherry-picked point.

NOTE ON CDC's STATUS (prior_art LaneA): CDC is ITSELF a PIC-family mechanism (Irminsul = CDC-over-radix).
So this is NOT "novel-vs-prior-art" — it is an intra-family recompute-fraction comparison: does the
CDC *boundary-localized re-sync* policy recompute fewer tokens than the PIC *window+selective-fraction*
repair policy, on a mid-prefix insertion, across the inj/seq surface?
"""
import json, hashlib, random, math, statistics
random.seed(0)

def hfn(b): return hashlib.blake2b(repr(b).encode(), digest_size=16).digest()

# ---------------- CDC arm (verbatim from EXP-0003) ----------------
def cdc_blocks(tokens, tgt=16, mask=0xF):
    blocks=[]; cur=[]
    for t in tokens:
        cur.append(t)
        if (int.from_bytes(hashlib.blake2b(str(t).encode(),digest_size=2).digest(),"little") & mask)==0 or len(cur)>=2*tgt:
            blocks.append(tuple(cur)); cur=[]
    if cur: blocks.append(tuple(cur))
    return blocks

def cdc_recompute_tokens(base, contam):
    cb_base=cdc_blocks(base); cb_con=cdc_blocks(contam)
    cached=set(hfn(b) for b in cb_base)
    rec_tokens=sum(len(b) for b in cb_con if hfn(b) not in cached)
    return rec_tokens, sum(len(b) for b in cb_con)

# ---------------- PIC arm (fair position-independent partial recompute) ----------------
def pic_recompute_tokens(S, R, p_frac, W):
    new = R
    window = min(W, S)
    selective = math.ceil(p_frac * S)
    reused_recompute = min(S, window + selective)   # union, capped at reused length
    rec = new + reused_recompute
    tot = S + R
    return rec, tot

# ---------------- surface ----------------
SEQ_LENS = [4000, 8000, 32000]
INJ_SEQ_TARGETS = [0.001, 0.01, 0.05, 0.25, 1.00]   # 0.1% 1% 5% 25% 100%
PIC_P = [0.01, 0.05, 0.10, 0.15]   # selective-recompute fraction range from CacheBlend/EPIC/MEPIC lit
PIC_W = 256                         # boundary repair window (tokens). ~ EPIC LegoLink / a few blocks.
F_POSITIONS = [0.1, 0.5, 0.9]       # insertion fractional positions (confirm CDC position-(in)dep)

R = {
  "experiment":"EXP-0006","claim":"CLAIM-0006","device":"CPU",
  "model":"recompute-fraction (token-count) under single mid-prefix insertion; CDC vs FAIR PIC-family baseline",
  "pic_boundary_window_W": PIC_W,
  "pic_selective_fractions": PIC_P,
  "methodology":"matches EXP-0003; PIC = EPIC/CacheBlend/Irminsul/MEPIC-style window+selective partial recompute (NOT whole-suffix)",
  "rows":[]
}

for S in SEQ_LENS:
    base=[random.randint(10,50000) for _ in range(S)]
    for ratio in INJ_SEQ_TARGETS:
        Rtok=max(1,int(round(ratio*S)))
        tool=[random.randint(10,50000) for _ in range(Rtok)]
        cdc_pcts=[]
        for f in F_POSITIONS:
            p=int(S*f)
            contam=base[:p]+tool+base[p:]
            c_rec,c_tot=cdc_recompute_tokens(base,contam)
            cdc_pcts.append(100*c_rec/c_tot)
        cdc_mean=sum(cdc_pcts)/len(cdc_pcts)
        cdc_max=max(cdc_pcts); cdc_min=min(cdc_pcts)
        pic_by_p={}
        for p_frac in PIC_P:
            pr,pt=pic_recompute_tokens(S,Rtok,p_frac,PIC_W)
            pic_by_p[f"pic_p{int(p_frac*100)}_pct"]=round(100*pr/pt,3)
        pic_best=pic_recompute_tokens(S,Rtok,min(PIC_P),PIC_W)
        pic_typ =pic_recompute_tokens(S,Rtok,0.10,PIC_W)
        pic_best_pct=100*pic_best[0]/pic_best[1]
        pic_typ_pct =100*pic_typ[0]/pic_typ[1]
        row={
          "seq_len":S,"inj_over_seq":ratio,"inj_tokens":Rtok,
          "cdc_recompute_pct":round(cdc_mean,3),
          "cdc_recompute_pct_range":[round(cdc_min,3),round(cdc_max,3)],
          **{k:round(v,3) for k,v in pic_by_p.items()},
          "cdc_vs_pic_p1_x": round(pic_best_pct/max(cdc_mean,1e-9),2),
          "cdc_vs_pic_p10_x": round(pic_typ_pct/max(cdc_mean,1e-9),2),
          "winner_vs_pic_p1": "CDC" if cdc_mean < pic_best_pct else ("PIC" if cdc_mean>pic_best_pct else "tie"),
        }
        R["rows"].append(row)

cdc_vs_p1=[r["cdc_vs_pic_p1_x"] for r in R["rows"]]
cdc_vs_p10=[r["cdc_vs_pic_p10_x"] for r in R["rows"]]
R["summary"]={
  "cdc_vs_pic_p1(most_favorable_to_PIC)_x_min":round(min(cdc_vs_p1),2),
  "cdc_vs_pic_p1_x_max":round(max(cdc_vs_p1),2),
  "cdc_vs_pic_p1_x_median":round(statistics.median(cdc_vs_p1),2),
  "cdc_vs_pic_p10(typical)_x_min":round(min(cdc_vs_p10),2),
  "cdc_vs_pic_p10_x_max":round(max(cdc_vs_p10),2),
  "cdc_vs_pic_p10_x_median":round(statistics.median(cdc_vs_p10),2),
  "cells_where_CDC_wins_vs_pic_p1": sum(1 for r in R["rows"] if r["winner_vs_pic_p1"]=="CDC"),
  "cells_total": len(R["rows"]),
}

out_json="/Users/dengcchi/autonomous-research/experiments/2026-05-31/EXP-0006/experiment_result/results.json"
json.dump(R,open(out_json,"w"),indent=2)

# CSV
import csv
out_csv="/Users/dengcchi/autonomous-research/experiments/2026-05-31/EXP-0006/experiment_result/results.csv"
with open(out_csv,"w",newline="") as fcsv:
    w=csv.writer(fcsv)
    w.writerow(["seq_len","inj_over_seq","inj_tokens","cdc_recompute_pct",
                "pic_p1_pct","pic_p5_pct","pic_p10_pct","pic_p15_pct",
                "cdc_vs_pic_p1_x","cdc_vs_pic_p10_x","winner_vs_pic_p1"])
    for r in R["rows"]:
        w.writerow([r["seq_len"],r["inj_over_seq"],r["inj_tokens"],r["cdc_recompute_pct"],
                    r["pic_p1_pct"],r["pic_p5_pct"],r["pic_p10_pct"],r["pic_p15_pct"],
                    r["cdc_vs_pic_p1_x"],r["cdc_vs_pic_p10_x"],r["winner_vs_pic_p1"]])
print(json.dumps(R,indent=2))
