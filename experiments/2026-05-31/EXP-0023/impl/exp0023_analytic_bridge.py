#!/usr/bin/env python3
# EXP-0023 — CLAIM-0006 gate-B ANALYTIC BRIDGE (CPU, stdlib only, deterministic).
# Bridges the H100 KERNEL-PROXY (EXP-0014/0021) to a realistic END-TO-END TTFT estimate by
# adding the serving-stack overheads the kernel-proxy omits. Produces a best/worst-case
# end-to-end CDC/PIC sensitivity band, and answers: does CDC's kernel advantage SURVIVE serving,
# or is it FRAGILE (i.e. how load-bearing is the missing real vLLM+CacheBlend serving cell)?
#
# THIS IS A MODEL, NOT A MEASUREMENT. All overhead magnitudes are PLAUSIBLE RANGES from the
# cited literature (see SOURCES). The honest deliverable is the sensitivity BAND + which
# overheads it is sensitive to, NOT a point estimate.
#
# ===================== SOURCES (real, cited; not invented) =====================
# [K]  EXP-0021 (this project): H100 SDPA kernel-proxy, 30 reps/cell, bootstrap 95% CI on
#      PIC/CDC wall-clock ratio. ALL 8 cells exclude 1.0. Ratios used below.
# [W]  EXP-0014 (this project): whole-suffix anchor 32k/0.1%: CDC ~0.71 ms vs whole-suffix
#      ~28.9 ms (~41x). Used to scale ABSOLUTE kernel times. Model: 7-8B, 32 heads x128, fp16.
# [CB] CacheBlend, arXiv:2405.16444 (Yao et al.): PIC selective-recompute of a small HKVD
#      fraction (~15% of reused tokens); reports 2.2-3.3x TTFT reduction vs full prefill;
#      the scattered KV gather / HBM load is OVERLAPPED with compute (pipelined) -> in a
#      tuned serving stack the gather overhead is partially HIDDEN, which ERODES the
#      kernel-proxy's PIC penalty (the proxy measured gather NOT overlapped).
# [NV] NVIDIA "Getting Started with CUDA Graphs" + PyTorch CUDA-graph blog: per-kernel CPU
#      LAUNCH submission overhead is "microsecond scale" (commonly 5-10 us/launch); CUDA
#      graphs amortize it to near-zero. Scattered selective recompute issues MORE distinct
#      kernels (extra index_select/gather + per-chunk attn) than one contiguous block.
# [SCH] vLLM scheduler/continuous-batching: per-step Python scheduling + sampling + prepare-
#      inputs adds a fixed CPU cost per forward step (tens to low-hundreds of us, hidden under
#      CUDA graph in steady state; visible at prefill). Modeled as a fixed per-call overhead.
# ==============================================================================

import json, math, csv, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "experiment_result")
os.makedirs(OUT, exist_ok=True)

# ---- [K] kernel-proxy PIC/CDC ratios (EXP-0021, point) and CI half-info ----
# ratio_kernel = PIC_kernel / CDC_kernel  (>1 => CDC faster at kernel level)
KERNEL = {
    ("4k","0.1%"):1.256, ("4k","1%"):1.329, ("4k","5%"):1.205, ("4k","25%"):1.364,
    ("32k","0.1%"):2.627,("32k","1%"):1.129,("32k","5%"):1.354,("32k","25%"):1.282,
}
# CI95 lows (PIC/CDC) from EXP-0021 — used to stress the WORST realistic kernel ratio
KERNEL_CI_LO = {
    ("4k","0.1%"):1.245,("4k","1%"):1.317,("4k","5%"):1.189,("4k","25%"):1.365,
    ("32k","0.1%"):2.587,("32k","1%"):1.128,("32k","5%"):1.347,("32k","25%"):1.271,
}

# ---- [W] absolute kernel times (ms) reconstructed from anchors ----
# Anchor: 32k/0.1% CDC ~= 0.71 ms (EXP-0014). The CDC recompute touches the *new* rows
# attending to the full reused context; cost ~ R_new x S (rows x ctx). We reconstruct CDC_ms
# per cell from a simple, transparent attention-FLOP proxy normalized to the 0.71ms anchor,
# then PIC_ms = ratio_kernel * CDC_ms. This makes the ABSOLUTE scale explicit so we can add
# ABSOLUTE serving overheads (us) and see when they dominate.
SEQ = {"4k":4096, "32k":32768}
INJ = {"0.1%":0.001, "1%":0.01, "5%":0.05, "25%":0.25}
# CDC recompute rows = injected rows R = inj*S (it recomputes the injected/suffix chunk
# contiguously, attending to S reused). Work proxy ~ R * S. Anchor at 32k/0.1%: R=32.768 rows.
def cdc_work(seqk, injp):
    S = SEQ[seqk]; R = INJ[injp]*S
    return R * S
ANCHOR_WORK = cdc_work("32k","0.1%")
ANCHOR_MS   = 0.71  # [W]
def cdc_ms(seqk, injp):
    return ANCHOR_MS * cdc_work(seqk, injp)/ANCHOR_WORK

# ---- serving-overhead model (ABSOLUTE, added to BOTH arms, but asymmetrically) ----
# We model end-to-end prefill-TTFT of the *repair* path as:
#   TTFT_arm = kernel_ms(arm) + launch_overhead(arm) + sched_overhead + (1-overlap)*gather_penalty(PIC only)
# CDC contiguous => fewer kernel launches, no scattered gather.
# PIC scattered => extra gather kernels + non-coalesced HBM traffic, partially overlapped [CB].
#
# Plausible ranges (ms). Sources in header.
SERVING = {
    # per-call fixed scheduling+sampling+prepare-inputs CPU cost, applied EQUALLY to both arms
    # (so it SHRINKS the ratio toward 1.0 — this is the theory_skeptic's "wins flip under serving").
    "sched_ms":       {"best_for_cdc":0.05, "nominal":0.20, "worst_for_cdc":0.60},
    # extra kernel launches PIC issues over CDC (gather + per-chunk attn). count * per-launch us.
    "pic_extra_launches": {"best_for_cdc":40, "nominal":12, "worst_for_cdc":2},   # CUDA-graph amortizes -> worst_for_cdc=few
    "us_per_launch":  {"best_for_cdc":10.0, "nominal":6.0, "worst_for_cdc":0.3},  # [NV]; CUDA-graph -> ~0.3us
    # scattered-gather HBM penalty PIC pays at kernel level is ALREADY in KERNEL ratio; but a TUNED
    # serving stack OVERLAPS gather with compute [CB], REMOVING part of that penalty from PIC's
    # end-to-end. overlap_frac = fraction of PIC's kernel-level gather penalty hidden by pipelining.
    # This is the dominant EROSION of CDC's advantage. 0=no overlap(proxy), 1=fully hidden.
    "pic_gather_overlap_frac": {"best_for_cdc":0.0, "nominal":0.45, "worst_for_cdc":0.85},
}

def pic_gather_penalty_ms(seqk, injp, ratio):
    # The kernel-level PIC penalty over CDC = (ratio-1)*CDC_ms is mostly scattered-gather/low-AI.
    # We attribute a fraction g_attr of it to *overlappable* gather (rest is irreducible recompute).
    return (ratio-1.0)*cdc_ms(seqk,injp)

# fraction of the kernel PIC-penalty that is overlappable gather (vs irreducible compute).
# CacheBlend overlaps the KV LOAD/gather; the selective recompute itself is not free.
G_ATTR = {"best_for_cdc":0.30, "nominal":0.55, "worst_for_cdc":0.80}

def end_to_end(seqk, injp, scenario, kernel_ratio):
    c = cdc_ms(seqk, injp)
    # base PIC kernel time
    p_kernel = kernel_ratio * c
    sched = SERVING["sched_ms"][scenario]
    launches = SERVING["pic_extra_launches"][scenario]
    us = SERVING["us_per_launch"][scenario]
    pic_extra_launch_ms = launches*us/1000.0
    overlap = SERVING["pic_gather_overlap_frac"][scenario]
    gattr = G_ATTR[scenario]
    # overlappable part of PIC's kernel penalty that serving HIDES:
    penalty = pic_gather_penalty_ms(seqk,injp,kernel_ratio)
    hidden = overlap * gattr * penalty
    cdc_e2e = c + sched
    pic_e2e = p_kernel + sched + pic_extra_launch_ms - hidden
    return cdc_e2e, pic_e2e, pic_e2e/cdc_e2e

scenarios = ["best_for_cdc","nominal","worst_for_cdc"]
rows=[]
for seqk in ["4k","32k"]:
    for injp in ["0.1%","1%","5%","25%"]:
        kr = KERNEL[(seqk,injp)]
        kr_lo = KERNEL_CI_LO[(seqk,injp)]
        for sc in scenarios:
            # worst_for_cdc also uses the CI-low kernel ratio (most adverse but still measured)
            use_kr = kr_lo if sc=="worst_for_cdc" else kr
            c,p,r = end_to_end(seqk,injp,sc,use_kr)
            rows.append(dict(seq=seqk,inj=injp,scenario=sc,kernel_ratio=round(kr,3),
                             cdc_ms=round(c,4),pic_ms=round(p,4),e2e_ratio=round(r,4)))

# write CSV
csvp=os.path.join(OUT,"e2e_sensitivity.csv")
with open(csvp,"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["seq","inj","scenario","kernel_ratio","cdc_ms","pic_ms","e2e_ratio"])
    w.writeheader(); [w.writerow(x) for x in rows]

# summarize the BAND
def band(filterfn):
    rs=[x["e2e_ratio"] for x in rows if filterfn(x)]
    return min(rs),max(rs)
all_lo,all_hi = band(lambda x:True)
worst_lo,worst_hi = band(lambda x:x["scenario"]=="worst_for_cdc")
nom_lo,nom_hi = band(lambda x:x["scenario"]=="nominal")
best_lo,best_hi = band(lambda x:x["scenario"]=="best_for_cdc")
winregion = [x for x in rows if (x["seq"]=="32k" and x["inj"] in ("0.1%","1%"))]
wr_worst = [x["e2e_ratio"] for x in winregion if x["scenario"]=="worst_for_cdc"]
# does CDC survive (ratio>1) everywhere even worst-case?
n_invert = sum(1 for x in rows if x["e2e_ratio"]<1.0)
n_invert_worst = sum(1 for x in rows if x["scenario"]=="worst_for_cdc" and x["e2e_ratio"]<1.0)

summary=dict(
  all_band=[round(all_lo,3),round(all_hi,3)],
  best_for_cdc_band=[round(best_lo,3),round(best_hi,3)],
  nominal_band=[round(nom_lo,3),round(nom_hi,3)],
  worst_for_cdc_band=[round(worst_lo,3),round(worst_hi,3)],
  winregion_32k_lowinj_worstcase_ratios=[round(v,3) for v in wr_worst],
  n_cells_inverted_total=n_invert,
  n_cells_inverted_worstcase=n_invert_worst,
)
with open(os.path.join(OUT,"summary.json"),"w") as f:
    json.dump({"summary":summary,"rows":rows,
               "overhead_model":SERVING,"g_attr":G_ATTR,
               "anchor_ms_32k_0.1pct":ANCHOR_MS},f,indent=2)
print(json.dumps(summary,indent=2))
print("\n--- worst_for_cdc rows ---")
for x in rows:
    if x["scenario"]=="worst_for_cdc":
        flag = "  <-- INVERTS" if x["e2e_ratio"]<1.0 else ""
        print(f'{x["seq"]:>4} {x["inj"]:>5}  e2e PIC/CDC={x["e2e_ratio"]:.3f}  (cdc {x["cdc_ms"]:.3f}ms / pic {x["pic_ms"]:.3f}ms){flag}')

# ============ BREAK-EVEN PROBE: how much overlap+sched flips each cell to a tie? ============
# Hold extra-launches favorable to CDC fixed at the WORST-for-CDC setting (CUDA-graph amortized:
# 2 launches x 0.3us ~ negligible), then ask: at what (overlap_frac, g_attr) does PIC e2e == CDC e2e
# given a fixed sched? This isolates the SINGLE most load-bearing assumption (gather overlap).
def breakeven_overlap(seqk, injp, kernel_ratio, sched_ms, gattr):
    c = cdc_ms(seqk, injp)
    penalty = (kernel_ratio-1.0)*c
    # pic_e2e = kr*c + sched + ~0 - overlap*gattr*penalty ; cdc_e2e = c + sched
    # tie: kr*c - overlap*gattr*penalty = c  =>  overlap = (kr-1)*c / (gattr*penalty) = 1/gattr
    # (since penalty=(kr-1)*c). So break-even overlap = 1/gattr, INDEPENDENT of cell magnitude!
    # i.e. PIC ties CDC only if it hides MORE than 100% of the attributable gather penalty.
    if gattr<=0: return float('inf')
    return 1.0/gattr

print("\n=== BREAK-EVEN: overlap_frac needed to FLIP a cell to PIC-faster (sched ignored, launches~0) ===")
for gattr in (0.30,0.55,0.80,1.0):
    print(f"  g_attr={gattr:.2f}: break-even overlap_frac = {breakeven_overlap('32k','0.1%',2.627,0.2,gattr):.3f}  "
          f"({'IMPOSSIBLE (>1)' if 1.0/gattr>1 else 'POSSIBLE'})")
print("INTERPRETATION: break-even overlap = 1/g_attr. Since g_attr<=1 always, PIC needs to hide")
print(">=100% of the gather penalty to even TIE — i.e. ALSO claw back irreducible recompute, which")
print("overlap cannot do. So the kernel advantage CANNOT invert from gather-overlap alone; only a")
print("LARGE per-call sched/launch asymmetry FAVORING PIC (implausible) could flip it. The flip risk")
print("is therefore LOW; the missing serving cell is MODERATELY (not critically) load-bearing.")
