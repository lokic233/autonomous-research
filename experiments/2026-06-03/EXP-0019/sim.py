#!/usr/bin/env python3
# EXP-0019 L0: KV-offload tiered demote+prefetch vs evict-recompute. CPU-only, stdlib-only, SERIAL.
# Honest pipeline. Trust the CSVs this writes. NO multiprocessing.
import csv, math, random, os, time
random.seed(20260603)
HERE = os.path.dirname(os.path.abspath(__file__))
RES  = os.path.join(HERE, "results")
os.makedirs(RES, exist_ok=True)

# ---- KV size model (GQA, Qwen2.5-7B-like, fp16). See PRE_REG. ----
BYTES_PER_TOKEN = 2*28*4*128*2          # K,V * layers * kv_heads * head_dim * 2B = 57344 B
BLOCK_TOKENS    = 16
BYTES_PER_BLOCK = BYTES_PER_TOKEN*BLOCK_TOKENS   # 917504 B = 0.875 MiB
MiB = 1024*1024
GB  = 1e9                                # PCIe BW quoted in GB/s (decimal), bytes in binary; we keep BW as bytes/s decimal

# ---- sweeps ----
N_BLOCKS   = [32,64,128,256,512]                 # prefix length in 16-tok blocks
GAP_MED    = [0.2,0.5,1.0,2.0,5.0,10.0,30.0]     # s, median inter-turn gap (LogNormal)
GAP_SIGMA  = 0.8
PCIE_BW    = [8e9,16e9,32e9]                      # bytes/s effective (8/16/32 GB/s)
CONCURR    = [1,2,4,8,16,32]                      # sessions prefetching concurrently on shared link
P_RR       = [0.5,0.7,0.9,0.99]                   # re-reference prob on resume
PREFILL_TPS= [30000,60000,120000]                 # tokens/s prefill (recompute baseline)
MC = 2000

def lognormal_samples(median, sigma, n):
    mu = math.log(median)
    return [math.exp(random.gauss(mu, sigma)) for _ in range(n)]

# ============ PART A: gap-vs-fetch hide probability ============
# For each (N_blocks, PCIe_BW, C): contended per-session BW = BW/C. fetch_time = prefix_bytes/(BW/C).
# Hide prob = P(gap >= fetch_time) over the gap distribution (per gap_median).
with open(os.path.join(RES,"sweep_gap_vs_fetch.csv"),"w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["n_blocks","prefix_tokens","prefix_MiB","pcie_bw_GBs","concurrency",
                "per_sess_BW_GBs","fetch_time_s","gap_median_s","hide_prob","median_gap_ge_fetch"])
    for nb in N_BLOCKS:
        pbytes = nb*BYTES_PER_BLOCK
        ptok   = nb*BLOCK_TOKENS
        pMiB   = pbytes/MiB
        for bw in PCIE_BW:
            for C in CONCURR:
                per = bw/C
                ftime = pbytes/per
                for gm in GAP_MED:
                    gs = lognormal_samples(gm, GAP_SIGMA, MC)
                    hide = sum(1 for g in gs if g>=ftime)/MC
                    w.writerow([nb,ptok,round(pMiB,2),bw/1e9,C,round(per/1e9,3),
                                round(ftime,4),gm,round(hide,4),int(gm>=ftime)])

# ============ PART B: (B_eff, TTFT_resume) Pareto, both policies ============
# Matched GPU-KV capacity. Both policies free GPU KV by offloading/evicting cold prefixes, so the
# COLD-capacity gain is the SAME (both let GPU hold only HOT working set). The differentiator is the
# RESUME COST that lands on the critical path -> TTFT_resume. We report TTFT_resume as the Pareto axis
# at matched B_eff (i.e. for the same set of resumable sessions, which policy gives lower resume TTFT).
#
# evict-recompute TTFT = prefix_tokens / prefill_tps  (pure GPU compute, no PCIe, deterministic)
# prefetch TTFT (per cell, over gap dist):
#   fetch_contended = prefix_bytes/(BW/C). Useful traffic fraction = p_rr; wasted (1-p_rr) still
#   competes for BW within the window -> inflate effective C by 1/p_rr (wasted prefetches occupy link).
#   C_eff = C / p_rr. fetch_eff = prefix_bytes/(BW/C_eff).
#   residual_stall(sample) = max(0, fetch_eff - gap). TTFT_prefetch = E[residual_stall] (resumed sessions).
#   Also expected wasted bytes per resume-cycle = (1-p_rr)*prefix_bytes (reported as overhead).
with open(os.path.join(RES,"sweep_pareto.csv"),"w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["n_blocks","prefix_tokens","prefix_MiB","pcie_bw_GBs","concurrency","p_rr",
                "prefill_tps","gap_median_s",
                "ttft_evict_recompute_s","fetch_contended_s","fetch_eff_s",
                "ttft_prefetch_mean_s","ttft_prefetch_p90_s",
                "prefetch_wins","win_margin_s","wasted_MiB_per_cycle","bw_bound"])
    for nb in N_BLOCKS:
        pbytes=nb*BYTES_PER_BLOCK; ptok=nb*BLOCK_TOKENS; pMiB=pbytes/MiB
        for bw in PCIE_BW:
            for C in CONCURR:
                for prr in P_RR:
                    C_eff = C/prr
                    per       = bw/C
                    per_eff   = bw/C_eff
                    fetch_c   = pbytes/per
                    fetch_eff = pbytes/per_eff
                    wasted    = (1-prr)*pbytes/MiB
                    for gm in GAP_MED:
                        gs = lognormal_samples(gm,GAP_SIGMA,MC)
                        residual=[max(0.0,fetch_eff-g) for g in gs]
                        residual.sort()
                        tp_mean=sum(residual)/MC
                        tp_p90=residual[int(0.90*MC)]
                        # bw_bound flag: aggregate prefetch demand over the gap window exceeds link cap
                        # i.e. even at median gap the link can't move C_eff prefixes -> C_eff*pbytes > bw*gm
                        bw_bound = int(C_eff*pbytes > bw*gm)
                        for tps in PREFILL_TPS:
                            ttft_ev = ptok/tps
                            wins = int(tp_mean < ttft_ev)
                            margin = ttft_ev - tp_mean
                            w.writerow([nb,ptok,round(pMiB,2),bw/1e9,C,prr,tps,gm,
                                        round(ttft_ev,5),round(fetch_c,5),round(fetch_eff,5),
                                        round(tp_mean,5),round(tp_p90,5),
                                        wins,round(margin,5),round(wasted,2),bw_bound])
print("DONE_SIM")
