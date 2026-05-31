#!/usr/bin/env python3
# EXP-0014 — CLAIM-0006 gate-B: GPU WALL-CLOCK of CDC contiguous-chunk vs PIC scattered-HKVD recompute.
# H100 devgpu014. BOUNDED kernel microbench (NOT a VMM mapping probe). host-mem-floor watchdog + os._exit teardown.
# (Full source archived; ran in py312conda torch 2.5.1+cu124. SDPA attention, 32 heads x 128 dim, fp16.)
# cells: seq {4096,32768} x inj/seq {0.1,1,5,25}% x modes {whole_suffix, cdc(contiguous), pic(scattered HKVD)}.
# metric: median + p95 TTFT ms over 5 reps; report PIC/CDC wall-clock ratio per cell. See DESIGN.md for method.
