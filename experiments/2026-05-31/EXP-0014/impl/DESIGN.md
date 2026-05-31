# EXP-0014 DESIGN — CLAIM-0006 gate-B: GPU wall-clock TTFT vs a REAL PIC artifact
Target node: devgpu014 (H100, NOT fragile). Bounded inference benchmark — NOT a VMM mapping probe.
Honors MI350X_CRASH_POSTMORTEM: no unbounded VA mapping; normal model+KV alloc (GB-scale, bounded);
os._exit(0) on teardown; host-MemAvailable watchdog aborts if < host_mem_floor (300 GiB); minimal cell set.

## QUESTION (the committee's gate-B, VERDICT-0017/0022/0023)
The CPU token-count proxy (EXP-0006) shows CDC's recompute-fraction advantage over a fair PIC baseline
collapses to ~1.77x median and a tie (1.29x) at inj/seq>=5%. BUT a recompute-FRACTION tie != a WALL-CLOCK
tie: CDC does CONTIGUOUS-chunk recompute (high arithmetic intensity, FlashAttention-friendly) while PIC
(CacheBlend-style) does SCATTERED HKVD recompute (gather/scatter, lower arithmetic intensity, kernel-launch
overhead). At the ~5% crossover the wall-clock could diverge 2-3x in EITHER direction. Measure it on real HW.

## METHOD (minimal, decision-relevant cell set — R0/R1)
- Engine: a REAL PIC artifact. Primary = LMCache CacheBlend (published OSS) on vLLM; if unavailable in the
  node env, fall back to an EPIC-style selective-recompute reference + document the substitution honestly.
- Model: a single mid-size model that fits one H100 (e.g. 7B-8B, fp16). Bounded KV; no multi-node.
- Surface: the DECISION cells only (not the full 405-cell sweep — that was the CPU proxy's job):
  inj/seq in {0.1%, 1%, 5%, 25%} x seq_len in {4k, 32k}. ~8 cells x 3 reps = 24 measured points per arm.
  Arms: CDC-contiguous-repair vs PIC-scattered-HKVD-repair (+ a recompute-whole-suffix control).
- Metric: end-to-end TTFT wall-clock (ms) per cell, median + p95 over reps; report the CDC/PIC wall-clock
  RATIO per cell and specifically AT the ~5% crossover where the fraction tie lives.
- Output: experiment_result/result.md + ttft_results.csv (cell, arm, ttft_ms_median, ttft_ms_p95, ratio).

## DECISION VALUE (R0 necessity gate)
This is the SINGLE remaining GREEN-blocker for CLAIM-0006 (novelty gate-A fully closed). It directly decides
whether the surviving win-region contribution holds in wall-clock (GREEN) or whether the fraction-tie becomes
a wall-clock LOSS for CDC (further weaken / honest negative). Either outcome is decision-relevant. NOT gold-plating.

## SAFETY (R2/R3/R4)
- Bounded: one model load + KV cache (tens of GB GPU, well under 80GB H100). No unbounded host mapping.
- Watchdog: poll /proc/meminfo MemAvailable each cell; abort (os._exit(0)) if < 300 GiB host free.
- Teardown: os._exit(0) after writing results — skip slow destructor paths (defensive; this workload doesn't
  create millions of kernel objects, but follow the rule).
- Node: H100 devgpu014 (non-fragile) PREFERRED. If ever routed to MI350X, host-mem-floor 300 is engine-enforced.
