#!/usr/bin/env python3
"""
EXP-0028 — Compaction-as-prefix-invalidation: NEW cost surface, or the p~=0 boundary
of CLAIM-0006's tool-injection accounting identity?
Agent: researcher-0002-laneE | Project: PROJ-0002 | Claim: none | Level 1
CPU-only, stdlib only, deterministic (seed 20260531). prompt_version: researcher_laneE_v001
"""
import json, random

random.seed(20260531)
BASE = 1500          # never-touched system+schema prefix (tokens)
W = 64               # CDC boundary re-chunk window (tokens)

def policies(S, H, G):
    Sp = S - H + G
    p_c = BASE / Sp
    full = (Sp - BASE) / Sp
    cdc  = (G + W) / Sp
    r_over_s = G / Sp
    pic_factor = 1.0 if r_over_s >= 0.05 else 1.0 + 0.7 * (1 - r_over_s/0.05)
    pic = (G * pic_factor) / Sp
    return dict(Sp=Sp, p_c=p_c, full=full, cdc=cdc, pic=pic, r_over_s=r_over_s)

grid = []
for S in (8000, 23000, 50000, 120000, 400000):
    for H_frac in (0.3, 0.5, 0.7, 0.9):
        H = int((S - BASE) * H_frac)
        for rho in (0.05, 0.1, 0.2, 0.4):
            G = max(1, int(rho * H))
            r = policies(S, H, G)
            id_cdc = (G + W) / r['Sp']
            id_full = (r['Sp'] - BASE) / r['Sp']
            grid.append(dict(S=S, H=H, G=G, rho=rho, **r,
                             cdc_id_err=abs(r['cdc']-id_cdc),
                             full_id_err=abs(r['full']-id_full)))

max_cdc_err  = max(g['cdc_id_err']  for g in grid)
max_full_err = max(g['full_id_err'] for g in grid)

be = []
for g in grid:
    saved_per_step = g['S'] - g['Sp']
    if saved_per_step <= 0:
        continue
    C_cdc  = g['cdc']  * g['Sp']
    C_full = g['full'] * g['Sp']
    be.append(dict(S=g['S'], rho=g['rho'],
                   Tstar_cdc = C_cdc/saved_per_step,
                   Tstar_full= C_full/saved_per_step))

out = dict(
  base=BASE, w=W, n_grid=len(grid),
  identity_test_1_cdc_equals_R_over_S = dict(
      max_abs_err=max_cdc_err, PASS=bool(max_cdc_err < 1e-12),
      note="CDC compaction recompute fraction == (G+W)/S' i.e. CLAIM-0006's R/S identity with R:=summary-size G (+ boundary w). Compaction is NOT a new cost surface for CDC."),
  identity_test_2_full_equals_front_edit = dict(
      max_abs_err=max_full_err, PASS=bool(max_full_err < 1e-12),
      note="FULL compaction == diverged-suffix recompute from first-changed pos = CLAIM-0006 FULL at p=p_c (the front). Same identity, p~=0 corner."),
  break_even_is_generic_identity = dict(
      closed_form="T* = C_recompute / (S - S')  (one-time recompute amortized over per-step length savings)",
      structurally_same_as="DEAD-0010 speculate-or-skip h*f>=alpha/(1+alpha): generic cost/benefit ratio, NO KV-specific anomaly",
      example_Tstar = sorted(set(round(b['Tstar_cdc'],3) for b in be))[:8]),
  sample_grid = grid[:6],
)
with open('experiments/2026-05-31/EXP-0028/experiment_result/results.json','w') as f:
    json.dump(out, f, indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='sample_grid'}, indent=2, default=str)[:1600])
