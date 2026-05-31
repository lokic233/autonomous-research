# EXP (CLAIM-0006 option-b): measured GPU kernel-THROUGHPUT table at inj/seq>=5% (the PIC-favorable regime)
Target: devgpu014 H100 (devgpu499 MI350X unreachable — do NOT queue there). Bounded microbench, host-mem-floor 300, os._exit.
Addresses VERDICT-0029 required-evidence option (b): convert the throughput-axis CONCESSION into a MEASURED table.
The committee's concern: at inj/seq>=5% (OUTSIDE the win-region) CDC recomputes the whole CONTIGUOUS chunk vs
PIC's smaller SELECTIVE set, so PIC could win aggregate THROUGHPUT even where CDC wins single-request TTFT.
METHOD: batched throughput (tokens/sec) of CDC contiguous-recompute vs PIC scattered-selective at inj/seq in
{5,10,25,50%} x seq {8k,32k}, batch sizes {1,8,32}, SDPA fp16. Report CDC/PIC throughput ratio per cell — and
HONESTLY surface where PIC wins (ratio<1). A measured negative table (PIC wins throughput at high inj/seq) is
publishable + closes the committee's rescope path. NOT vLLM serving (still owed) but a real measured throughput axis.
SAFETY: bounded attention workspaces freed per cell; host-mem-floor watchdog; os._exit teardown; H100 only.
