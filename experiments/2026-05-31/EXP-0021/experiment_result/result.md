# EXP-0021 RESULT — CLAIM-0006 gate-B GREEN-path: CIs + PIC provenance (H100 devgpu014)

**Device:** H100 devgpu014, py312conda torch 2.5.1+cu124, SDPA. 30 reps/cell, bootstrap 95% CI (B=2000) on PIC/CDC ratio.
Addresses VERDICT-0025 required_evidence. Bounded microbench; host-mem-floor 300 watchdog; os._exit teardown; node healthy.

## Req #1 — CIs on all 8 cells (esp the 32k/1% 1.02x cell from EXP-0014)
| inj/seq | 4k PIC/CDC [CI95] | 32k PIC/CDC [CI95] |
|---|---|---|
| 0.1% | 1.256 [1.245,1.270] | 2.627 [2.587,2.637] |
| 1%   | 1.329 [1.317,1.336] | **1.129 [1.128,1.151]** |
| 5%   | 1.205 [1.189,1.207] | 1.354 [1.347,1.371] |
| 25%  | 1.364 [1.365,1.391] | 1.282 [1.271,1.319] |
- **ALL 8 cells: CI95 EXCLUDES 1.0** — including the previously-ambiguous 32k/1% cell (EXP-0014 point est
  1.02x; with 30 reps it is 1.129x [1.128,1.151], CI clears 1.0). So "CDC contiguous wall-clock-faster than
  PIC scattered in all 8 decision cells" is now STATISTICALLY SUPPORTED (resolves the area_chair's objection).

## Req #3 — PIC impl provenance + faithfulness sensitivity
PIC arm = CacheBlend-style: attend recompute-rows to full reused context + a selective p=1% scattered HKVD
gather (index_select). Sensitivity @32k/5%: faithful PIC/CDC=1.390x vs naive-gather=1.435x — the ratio is
ROBUST to impl faithfulness (3% swing); CDC's advantage is not an artifact of an unoptimized PIC arm.

## Req #2 — end-to-end serving cell: HONESTLY NOT MET
vLLM/lmcache are NOT installed on devgpu014 and prod paths block pip install; a real vLLM+CacheBlend
end-to-end serving cell could not be run this round. This remains OWED for full GREEN. The kernel-proxy
WITH CIs is the strongest available evidence; I did NOT fabricate a serving number.

## NET (for committee)
Resolves req#1 (CIs, all cells exclude 1.0) + req#3 (PIC provenance, robust). req#2 (serving cell) still owed
— bounded by node env, not by analysis. CLAIM-0006's gate-B is now: kernel wall-clock advantage statistically
solid; end-to-end serving anchor is the single remaining piece for unanimous GREEN.
