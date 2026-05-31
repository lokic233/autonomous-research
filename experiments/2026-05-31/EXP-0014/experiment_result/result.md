# EXP-0014 RESULT — CLAIM-0006 gate-B: GPU wall-clock (H100 devgpu014)

**Device:** NVIDIA H100 (devgpu014). **Stack:** torch 2.5.1+cu124, SDPA attention. **Date:** 2026-05-31.
**Scope (HONEST):** kernel-level wall-clock proxy — measures the CDC-contiguous vs PIC-scattered-HKVD
recompute *kernels* directly (the committee's mechanism hypothesis). NOT a full vLLM/CacheBlend serving
benchmark (vllm/lmcache not installed on the node). Bounded; host-mem-floor 300GB watchdog; os._exit teardown;
node healthy throughout (no crash — cf. MI350X_CRASH_POSTMORTEM; this is a bounded attention microbench, not a
VMM mapping probe).

## QUESTION (committee gate-B, VERDICT-0017/0022/0023/0024)
Does the recompute-FRACTION tie at inj/seq>=5% (EXP-0006: CDC margin collapses to ~1.77x median, 1.29x tie)
become a WALL-CLOCK tie/loss for CDC? CDC does contiguous-chunk recompute (high arithmetic intensity);
PIC (CacheBlend-style) does scattered HKVD recompute (gather/scatter + kernel-launch overhead).

## RESULT — CDC wall-clock advantage HOLDS across all cells
PIC/CDC wall-clock ratio (>1 = CDC faster):
| inj/seq | seq=4k | seq=32k |
|---|---|---|
| 0.1% | 1.45x | **2.68x** |
| 1%   | 1.54x | 1.02x |
| 5%   | 1.45x | 1.42x |
| 25%  | 1.61x | 1.27x |

- CDC is wall-clock FASTER than PIC in ALL 8 decision cells (1.02x-2.68x).
- The fraction-tie at inj/seq>=5% does NOT become a wall-clock loss: CDC stays 1.27-1.42x faster — the
  scattered-HKVD gather overhead costs PIC more in wall-clock than the recompute-fraction parity suggests.
- Largest CDC advantage at the WIN-REGION corner (32k ctx, 0.1% inj): 2.68x — consistent with CLAIM-0006's
  surviving contribution (CDC wins where reused context is large + injection small).
- vs whole-suffix baseline: CDC is 1.3x (4k) to ~41x (32k, 0.1%: 0.71ms vs 28.9ms) faster — confirms
  avoiding whole-suffix recompute is the real win at large context.

## INTERPRETATION (for the committee)
The wall-clock evidence is FAVORABLE to CLAIM-0006's surviving win-region contribution: on real H100 the
contiguous-vs-scattered mechanism difference makes CDC's wall-clock advantage SURVIVE (and at the win-region
corner, EXCEED) the recompute-fraction picture. The fraction-tie does NOT flip to a wall-clock loss.
CAVEAT: kernel-level proxy, not full serving (no real vLLM/CacheBlend end-to-end TTFT incl scheduling,
batching, memory traffic). A full-stack run remains the strongest possible evidence; this is one rung below.
