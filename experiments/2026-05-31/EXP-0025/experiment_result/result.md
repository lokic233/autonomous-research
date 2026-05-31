# EXP-0025 RESULT — CLAIM-0006 option-b: measured GPU kernel-THROUGHPUT at inj/seq>=5% (H100 devgpu014)

**Device:** H100, py312conda torch 2.5.1+cu124, SDPA fp16, 10 reps/cell. 24 cells = inj/seq{5,10,25,50%} x seq{8k,32k} x batch{1,8,32}. Bounded; host-mem-floor 300 watchdog; os._exit teardown; node healthy.
**Purpose:** VERDICT-0029 option (b) — convert the throughput-axis CONCESSION (the committee's concern that PIC may win aggregate throughput at inj/seq>=5%, OUTSIDE the win-region) into a MEASURED table.

## RESULT — CDC's contiguous advantage extends to throughput; PIC wins only a marginal corner
- **PIC wins throughput in 2/24 cells, both MARGINAL (CDC/PIC = 0.993-0.994x)**: 8k ctx / 5% inj / batch 1 and 32. Essentially a tie, not a decisive PIC win.
- **CDC wins the other 22/24 cells**, by 1.08x-1.74x (largest at 8k/50%/B8 = 1.742x; 32k cells uniformly 1.10-1.50x).
- The committee's predicted PIC-favorable regime (high inj/seq) actually FAVORS CDC MORE (1.5-1.74x at 50%) — because at high inj/seq CDC's contiguous recompute amortizes better than PIC's scattered gather under batching.
- The only PIC edge is the smallest/lowest-injection corner (8k/5%), and it's a statistical tie.

## INTERPRETATION (for committee)
This MEASURES (not concedes) the throughput axis the committee flagged. The honest finding: CDC's contiguous-recompute advantage holds on THROUGHPUT as well as TTFT across nearly the entire inj/seq>=5% grid; PIC does not decisively win aggregate throughput anywhere measured (best PIC result is a 0.7% edge at one small corner). This CLOSES the VERDICT-0029 option-(b) requirement (measured negative table, not a residual-list concession). CAVEAT: still kernel-level SDPA throughput, NOT full vLLM+CacheBlend serving with PagedAttention's non-contiguous layout (that remains the owed end-to-end cell for the magnitude/serving generalization).
