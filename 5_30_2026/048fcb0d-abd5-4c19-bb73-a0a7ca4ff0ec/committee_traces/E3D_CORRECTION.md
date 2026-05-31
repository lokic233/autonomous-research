# E3d — CORRECTION of E3b's "super-linear degradation" overclaim (honest, H100)
CC4.8 was right to flag n=2. A clean 3-context sweep (each context maps to OOM on one GPU,
no huge pre-reservation) gives:
| contexts | per-context mappings | TOTAL |
|---|---|---|
| 1 | 523,404 | 523,404 |
| 2 | 260,281 / 263,003 | 523,284 |
| 3 | 171,633 / 174,206 / 177,325 | 523,164 |

TOTAL is CONSERVED at ~523,300 (+/-0.05%) and splits EVENLY (~K/n per context).

## What changed and why (full honesty, looped to committee)
- E3b earlier reported 2 contexts = 223,215 total (43% of one), which I framed as "super-linear
  degradation." That was an ARTIFACT: E3b had EACH worker pre-reserve a 1.5M-page VA range
  upfront; those reservations themselves consume the same descriptor budget (the R2 effect),
  starving the maps. When workers reserve only what they map (E3d), the budget is CONSERVED.
- CORRECTED FINDING (stronger + cleaner): K ~= 523,300 is a PER-DEVICE access-descriptor budget,
  CONSERVED and shared EVENLY across CUDA contexts (each context gets ~K/n_contexts). Reserves
  and maps both draw from it (R2). This is a hard, deterministic, conserved per-device resource.
- The MIG/multi-tenant implication SURVIVES and is actually cleaner: N co-tenants each get K/N
  mapping budget — a predictable per-tenant cap, not a chaotic degradation.

## Reconciliation of the two K numbers (CC4.8 point 1)
- 523,404 = pure single-reservation alias ceiling (R1/control/E3d n=1) — the descriptor budget.
- 519,936 = MEDIAN of B*P across prefix sizes in old Metric 4b (522,752 -> 516,096 as prefix
  grows). It is slightly BELOW 523,404 because multi-branch runs also spend reservations (R2),
  which draw from the same budget. Both numbers are consistent: 523,404 is the ceiling; B*P
  realizes slightly less when reservation overhead is included. Standardize headline on 523,404.

## R2 weight caveat (CC4.8 point 4) — stated
R2: 299,949 maps + 299,950 reserves before OOM. A reserve+map pair is ~1.745 "budget units" vs
1.0 for a bare map (523,404/299,949). So the budget is a SINGLE per-device pool charged at
DIFFERENT weights by reserves vs access-grants. Stated explicitly, not hidden.
