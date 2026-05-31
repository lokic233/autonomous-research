#!/usr/bin/env python3
"""
EXP-0018 — Idle-window speculative prefill: break-even surface (CPU token-count proxy)
Lane A, researcher-0001-laneA, CLAIM-0002-adjacent open_gap (MAP-0001).

CPU-ONLY. No GPU, no model CLIs, no memory probes. Pure stdlib analytic proxy.

MODEL (engine-side continuation prefill during idle windows):
  When a turn ends, the engine has an idle window of length W (seconds) before the
  next real continuation arrives. During W it can speculatively PREFILL a predicted
  continuation of P tokens (its best guess at what the user/agent will send next).

  Per-turn outcomes:
    - HIT  (prob h): the real continuation's prefix matches the speculated prefix for
            m tokens (m <= P). Those m tokens are already prefilled -> TTFT saved.
    - MISS (prob 1-h): speculated prefill is discarded -> pure wasted compute.

  Cost/benefit in *prefill-token* units (the only currency a CPU proxy can honestly
  carry; wall-clock TTFT is monotone in prefill tokens for a fixed engine/model, by
  Pope 2211.05102 prefill FLOP accounting — see KILL ANALYSIS).

  Let:
    P     = speculated prefill length (tokens), bounded by what fits in W:
            P <= floor(W * R_prefill), R_prefill = engine prefill throughput (tok/s).
    h     = hit rate (speculation correct enough to reuse)
    m|hit = expected matched-prefix length on a hit (tokens reused), m <= P
    Cw    = wasted compute on a turn = P tokens prefilled, of which only the reused
            part has value. On a MISS, all P wasted. On a HIT, (P - m) wasted (over-
            speculation tail) + m useful.
    Lsaved= latency saved on a hit = m tokens of prefill the real request didn't pay.

  NET VALUE per turn (token units):
    E[saved]  = h * m                         (prefill tokens the real request skips)
    E[wasted] = h*(P - m) + (1-h)*P  =  P - h*m
    NET       = E[saved] - alpha * E[wasted]
              = h*m - alpha*(P - h*m)
              = h*m*(1+alpha) - alpha*P

  alpha = wasted-compute weight (opportunity cost of a wasted prefill token relative
          to the value of a saved prefill token). alpha encodes whether idle compute
          is "free" (alpha->0, GPU otherwise idle) or contended (alpha->1, speculation
          steals from real work).

  BREAK-EVEN: NET >= 0  <=>  h*m*(1+alpha) >= alpha*P
              <=>  h * (m/P) >= alpha/(1+alpha)
  Define reuse-fraction f = m/P (expected fraction of speculated tokens actually reused).
  BREAK-EVEN CONDITION:   h * f >= alpha/(1+alpha)              ... (*)

  This is the whole surface. It is a SINGLE inequality in three dimensionless numbers
  (h, f, alpha). Everything else (W, R_prefill, P, model size) cancels into f and the
  token currency. THAT cancellation is the kill signal — see result.md.

We sweep the idle-window-length DISTRIBUTION because P is W-limited and f depends on P:
longer windows -> larger P -> typically smaller f (over-speculation tail grows), so the
distribution of W matters for the *achievable* operating point, not for the break-even
identity itself.
"""
import math, csv, statistics, os, json

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, ".."))

# ---- 1. Break-even identity surface: h*f >= alpha/(1+alpha) ----
def breakeven_h(f, alpha):
    """Minimum hit-rate to break even at reuse-fraction f, waste-weight alpha."""
    thr = alpha / (1.0 + alpha)
    if f <= 0: return float('inf')
    return thr / f

# ---- 2. Idle-window distribution -> achievable P, and f(P) decay model ----
# Realistic agentic idle windows are heavy-tailed (think-time / tool-latency gaps).
# Model W ~ lognormal-ish via discrete buckets (seconds). We DON'T sample randomly to
# keep it deterministic/reproducible; we enumerate a representative distribution.
IDLE_BUCKETS = [  # (window_seconds, probability_mass)
    (0.2, 0.30),   # micro-gap (token streaming pause)
    (1.0, 0.30),   # short think
    (3.0, 0.20),   # tool call
    (10.0, 0.12),  # long tool / retrieval
    (30.0, 0.08),  # human walked away
]
R_PREFILL = 6000.0  # tok/s prefill throughput, 7B-class on one datacenter GPU (order-of-mag; cancels)

# f(P): reuse fraction decays as we speculate further out — the deeper the speculation,
# the more likely the real continuation diverges. Geometric divergence with per-token
# survival s: expected matched prefix m = (1 - s^P)/(1-s)*... -> use m = s*(1-s^P)/(1-s)
# normalized; simpler honest proxy: f(P) = (1 - exp(-1/(beta)))... We use a token-level
# survival model: each speculated token is "still on the correct path" w.p. q; expected
# matched-prefix length given we speculate P tokens = sum_{i=1..P} q^i = q*(1-q^P)/(1-q).
def expected_match_len(P, q):
    if P <= 0: return 0.0
    if q >= 1.0: return float(P)
    return q * (1 - q**P) / (1 - q)

def reuse_fraction(P, q):
    if P <= 0: return 0.0
    return expected_match_len(P, q) / P

# ---- 3. Sweep the break-even surface ----
# DESIGN NOTE: P is a TUNED design parameter (how many tokens to speculate), bounded
# above by the W-budget but realistically set to a plausible next-continuation length.
# Filling the whole idle window (P=W*R) is strictly dominated (f->0). So we sweep P over
# realistic continuation lengths and CAP at the W-budget.
rows = []
alphas = [0.0, 0.1, 0.25, 0.5, 1.0]      # free-idle -> fully-contended
qs     = [0.80, 0.90, 0.95, 0.99]         # per-token path-survival (speculation quality)
hits   = [0.1, 0.3, 0.5, 0.7, 0.9]        # turn-level hit rate
P_DESIGN = [16, 64, 256, 1024]            # realistic speculated-continuation lengths

for (W, pmass) in IDLE_BUCKETS:
    P_budget = int(math.floor(W * R_PREFILL))
    for P in P_DESIGN:
      if P > P_budget:   # window too short to even prefill this much
          continue
      for q in qs:
        f = reuse_fraction(P, q)
        m = expected_match_len(P, q)
        for alpha in alphas:
            hmin = breakeven_h(f, alpha)
            for h in hits:
                net = h*m*(1+alpha) - alpha*P     # token units
                pays = net >= 0
                rows.append(dict(
                    W_s=W, idle_pmass=pmass, P_tokens=P, q_survival=q,
                    reuse_frac_f=round(f,5), match_len_m=round(m,3),
                    alpha_waste=alpha, hit_rate_h=h,
                    breakeven_hmin=round(hmin,5) if hmin!=float('inf') else None,
                    net_value_tok=round(net,3), pays_off=int(pays),
                ))

csv_path = os.path.join(ROOT, "breakeven_surface.csv")
with open(csv_path, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

# ---- 4. Distribution-weighted achievable operating point ----
# For a fixed speculation quality q and waste-weight alpha, what's the expected NET
# across the idle-window distribution, as a function of hit rate?
summary = {}
for q in qs:
    for alpha in alphas:
        for h in hits:
            exp_net = 0.0
            exp_P = 0.0
            for (W, pmass) in IDLE_BUCKETS:
                P = int(math.floor(W * R_PREFILL))
                m = expected_match_len(P, q)
                net = h*m*(1+alpha) - alpha*P
                exp_net += pmass * net
                exp_P   += pmass * P
            summary[(q,alpha,h)] = (exp_net, exp_P)

# ---- 5. The collapse check: does break-even depend on ANY system param? ----
# Re-derive hmin for a RANGE of (W, R_prefill, model-size) holding (q,alpha) fixed.
# If hmin is invariant to W/R/model, the "characterization" is a tautology.
collapse_rows = []
for q in [0.90, 0.95]:
    for alpha in [0.25, 0.5]:
        base = None
        for W in [0.2, 1.0, 3.0, 10.0, 30.0, 120.0]:
            for R in [2000.0, 6000.0, 20000.0]:
                P = int(math.floor(W*R))
                f = reuse_fraction(P, q)
                hmin = breakeven_h(f, alpha)
                collapse_rows.append(dict(q=q, alpha=alpha, W_s=W, R_prefill=R,
                                          P=P, reuse_f=round(f,5),
                                          breakeven_hmin=round(hmin,5)))

collapse_path = os.path.join(ROOT, "collapse_check.csv")
with open(collapse_path, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(collapse_rows[0].keys()))
    w.writeheader(); w.writerows(collapse_rows)

# Print key findings
print("=== BREAK-EVEN IDENTITY ===")
print("NET>=0  <=>  h*f >= alpha/(1+alpha)   [f=reuse-fraction, dimensionless]")
print()
print("=== break-even h_min for representative (f, alpha) ===")
for alpha in alphas:
    thr = alpha/(1+alpha)
    print(f"  alpha={alpha:>4}: waste-threshold alpha/(1+alpha)={thr:.3f}  "
          f"-> need h*f >= {thr:.3f}")
print()
print("=== reuse-fraction f vs speculation depth P (q=path-survival) ===")
for q in qs:
    line=[]
    for W in [0.2,1.0,3.0,10.0,30.0]:
        P=int(W*R_PREFILL); line.append(f"W={W}s(P={P}): f={reuse_fraction(P,q):.3f}")
    print(f"  q={q}: "+ " | ".join(line))
print()
print("=== COLLAPSE CHECK: does h_min depend on W or R_prefill? ===")
# group by (q,alpha,W) and see if R changes hmin
from collections import defaultdict
g = defaultdict(set)
for r in collapse_rows:
    g[(r['q'],r['alpha'],r['W_s'])].add(r['breakeven_hmin'])
maxspread=0.0
for k,v in g.items():
    spread=max(v)-min(v)
    maxspread=max(maxspread,spread)
print(f"  Max spread in h_min when varying R_prefill (fixed q,alpha,W): {maxspread:.6f}")
# group by (q,alpha,R) see if W changes hmin (via P->f)
gW = defaultdict(list)
for r in collapse_rows:
    gW[(r['q'],r['alpha'],r['R_prefill'])].append((r['W_s'],r['breakeven_hmin']))
print("  h_min DOES vary with W (through reuse-fraction f(P)) — example q=0.95,alpha=0.5,R=6000:")
for r in collapse_rows:
    if r['q']==0.95 and r['alpha']==0.5 and r['R_prefill']==6000.0:
        print(f"    W={r['W_s']:>5}s P={r['P']:>7} f={r['reuse_f']:.4f} h_min={r['breakeven_hmin']}")
print()
print(f"CSV: {csv_path}")
print(f"CSV: {collapse_path}")
print(f"rows: surface={len(rows)} collapse={len(collapse_rows)}")
