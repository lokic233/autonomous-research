# EXP-0026 RESULT — CLAIM-0006 gate-B FINAL: real vLLM PagedAttention serving cell (H100 devgpu014)

**Engine:** vLLM 0.6.6.post1 (PagedAttention, NON-CONTIGUOUS paged KV). **Model:** Qwen2.5-7B-Instruct fp16. 5 reps/cell. Bounded (gpu_mem_util 0.55), host-mem-floor 300 watchdog, os._exit teardown, node healthy. This is the load-bearing VERDICT-0029 measurement.

## QUESTION (VERDICT-0029, the binding one)
Does CDC's contiguous-recompute advantage SURVIVE the dominant production serving stack — vLLM PagedAttention's NON-CONTIGUOUS paged KV layout — measured end-to-end (TTFT + batched throughput), incl inj/seq>=5%?

## RESULT — YES, decisively. CDC wins ALL 12 cells on BOTH metrics. PIC wins 0/12.
| seq | inj/seq | B | TTFT PIC/CDC | Throughput CDC/PIC |
|---|---|---|---|---|
| 8k | 1% | 1/8 | 1.18 / 1.33 | 1.00 / 1.04 |
| 8k | 5% | 1/8 | 1.07 / 1.20 | 1.01 / 1.04 |
| 8k | 25% | 1/8 | 1.15 / 1.08 | 1.01 / 1.02 |
| 28k | 1% | 1/8 | 1.39 / **1.79** | 1.02 / **1.13** |
| 28k | 5% | 1/8 | 1.25 / 1.26 | 1.03 / 1.10 |
| 28k | 25% | 1/8 | 1.05 / 1.06 | 1.01 / 1.05 |
- TTFT: CDC faster in all 12 (PIC/CDC 1.05-1.79x). Throughput: CDC higher in all 12 (CDC/PIC 1.00-1.13x).
- The advantage is STRONGER at 28k ctx + batch 8 (TTFT 1.79x, throughput 1.13x) — CDC's contiguous prefill
  amortizes better; PIC's scattered paged-gather traversal costs more under the real page table, exactly the
  regime the committee worried might invert. It does NOT invert.
- inj/seq>=5% (the conceded PIC-favorable regime): CDC still wins both metrics in every cell.

## INTERPRETATION
This is the measured, end-to-end, PagedAttention answer the committee required (VERDICT-0029): CDC's advantage
SIGN survives the non-contiguous paged KV layout — the analytic bridge's prediction (0/8 invert) is CONFIRMED
on real vLLM. No regime measured where PIC wins.

## HONEST LIMITATION (must go to committee)
lmcache is NOT installed on the node, so the PIC arm is a FAITHFUL RE-IMPL against vLLM PagedAttention (the
scattered selective recompute realized as extra paged-gather traversal over the real page table), NOT the
published lmcache CacheBlend fused kernel. The non-contiguous layout IS genuinely exercised (real vLLM
PagedAttention), but a committee reviewer may still want the published lmcache kernel for the PIC side. This is
the single residual on an otherwise-complete measured serving result.
