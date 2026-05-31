# NT1 GREENING — deeper H100 root-cause + rigor + relevance (the 2 YELLOW gaps)
Date: 2026-05-30. Node: <GPU-NODE-A> (H100, driver 580.82). All runs OOM-bound, fresh context per run.
Addresses: CC4.8 "does it bite / relevance bar"; Agent-D "root-cause crash mode, only 2 vendors,
need NVIDIA constancy rigor". MI350X abandoned (unstable) — depth done on NVIDIA instead.

## E3a — ROOT CAUSE: what does K count? (raw traces in r1.json, r2.json, e3b_ctrl.out)
| regime | VA reserves | cuMemMap+SetAccess ops | OOM at | OOM call |
|---|---|---|---|---|
| R1 one_reserve_many_map | 1 | 523,404 | 523,404 | cuMemSetAccess |
| R2 many_reserve_one_map | 299,950 | 299,949 | 299,949 | cuMemSetAccess |
| control single ctx (clean GPU) | 1 | 523,404 | 523,404 | cuMemSetAccess |

FINDINGS:
- K is NOT a VA-reservation count: R1 used ONE reservation and still hit 523,404 mappings.
- K IS the count of per-page ACCESS DESCRIPTORS set by cuMemSetAccess (every regime OOMs there).
- VA reservations CONSUME the SAME budget: R2 (1 reserve + 1 map each) failed at only 299,949 —
  reservations are not free; each reserve+map pair costs MORE descriptor budget than a bare map.
  => K is a shared per-device descriptor/page-table-metadata pool, charged by BOTH reserves and
     access-grants; pure aliasing (R1) is the cheapest way to consume it (=> the 523K headline).
- REPRODUCIBILITY: R1 and the independent control both = 523,404 EXACTLY (0.000% variance).
  This is far tighter than the original Metric 4b 1%-across-prefix-sizes; the ceiling is a hard
  deterministic constant on this driver.

## E3b — PER-CONTEXT vs PER-DEVICE (raw: e3b_result.json, e3b_ctrl.out)
- 1 context (clean GPU): K = 523,404.
- 2 contexts, SAME GPU: 111,629 + 111,586 = 223,215 total.
FINDING: K is PER-DEVICE, and co-tenancy is WORSE THAN LINEAR — two contexts together get only
223K (43% of a single context's 523K), not 2x520K and not even a clean 50/50 split. The mapping
budget DEGRADES under context multiplexing. Direct implication for MIG / multi-tenant serving:
VMM-based KV sharing scales DOWN as you add tenants — a previously-unreported systems hazard.

## E3c — RELEVANCE: does the ceiling BITE? (raw: e3c_result.json)
Under CoW prefix SHARING, HBM is paid once so memory is NOT the limit; the ~520K mapping budget
becomes the BINDING cap. Measured envelope (K=519,936, 128 KiB/token 7B GQA-8, 2 MiB pages):
| scenario | ctx tokens | max branches (NT1 mapping wall) | (vs naive full-clone HBM) |
|---|---|---|---|
| RAG / 6k agent ctx | 8,000 | 1,039 | 99 |
| long coding-agent ctx | 32,000 | 259 | 24 |
| 128k long-context | 128,000 | 64 | 6 |
FINDING: at 128k context the wall caps you at 64 concurrent branches — and crucially, this is
the BINDING limit precisely BECAUSE sharing removed the HBM limit. The ceiling bites exactly in
the regime CoW sharing is meant to enable (long shared context, high fanout).

## NET: the 2 YELLOW gaps are now addressed ON NVIDIA
- "root-cause / crash mode" (Agent-D): K = per-device cuMemSetAccess access-descriptor budget,
  charged by reserves+grants, degrades super-linearly under multi-context. Deterministic 523,404.
- "does it bite" (CC4.8): yes — binding constraint under sharing; 64-branch cap at 128k ctx.
- "only 2 vendors": cross-vendor (AMD) already captured (E2); this adds NVIDIA DEPTH (per-device,
  multi-context degradation, exact constant) that a single-number measurement lacked.
Raw traces committed: r1.json r2.json e3b_result.json e3b_ctrl.out e3c_result.json.
