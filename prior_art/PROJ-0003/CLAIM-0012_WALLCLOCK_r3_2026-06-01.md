# CLAIM-0012 — Wall-Clock Sensitivity of the Codex H2 Hawkes Result (r3, 2026-06-01)

**Author:** researcher-0012-hold4-r3 · **Status:** DEFENSIVE HARDENING ONLY — does NOT change VERDICT-0049.
**Verdict bearing:** NONE. This does NOT earn a 6th GREEN. It addresses the systems_reviewer
EXTERNAL-VALIDITY caveat, NOT the product_realist altitude YELLOW.

## Question
EXP-0042 fit Codex H2 Cox-vs-Hawkes self-excitation on a **call-INDEX** clock
(kernel `exp(-beta*(t-j))`, t,j = call positions). Systems_reviewer asked: is the self-excitation
an artifact of that index discretization? Re-fit on the **REAL wall-clock** using per-event
ISO-8601 ms timestamps and see whether the signal survives.

## Method (reuses EXP-0042 robust_L4 machinery)
`experiments/2026-06-01/EXP-0044/impl/wallclock_refit.py` (stdlib only, runs in <0.4s, CPU).
Identical Cox per-tool-rate baseline, identical BIC, identical grid+local-refine fitter — the ONLY
change is the self-excitation kernel: `S_t = sum_j exp(-beta * dt_REAL_seconds)` where `dt_real`
= wall-clock seconds since prior failure j, taken from the top-level `timestamp` field on each
`function_call_output` line in `~/.codex/sessions/**/*.jsonl`. Same err/dedup logic as L3 parse_codex.

**Timestamps confirmed usable:** 100% coverage — all 2124 `function_call_output` lines carry a
top-level ISO-8601-ms `timestamp` (e.g. `2026-05-29T16:55:04.307Z`); all session sequences are
time-monotonic (0 negative gaps). 48 shufflable sessions, 1667 calls, **109 failure events**.

## Result — SIGNAL SURVIVES (strongly)
| clock | dBIC (Cox−Hawkes) | alpha | beta | half-life | earns params |
|---|---|---|---|---|---|
| call-index (EXP-0042 ref) | 26.85 | 4.3 | 1.2 /call | — | yes |
| **wall-clock seconds (this)** | **51.10** | **1.65** | 0.8 /s | 0.87 s | **yes (dBIC>6, alpha>0)** |

LRT 2Δll = 65.9. The dBIC-vs-beta curve has a **clean INTERIOR maximum** at beta≈0.8/s
(rises smoothly from negative at beta→0, peaks at 51.1, decays at high beta) — not an edge-degenerate
fit. Best half-life ≈0.87s: Codex failures cluster on a **sub-second to few-second** real-time scale.

## Honest caveats & coarse-timestamp robustness (Filimonov–Sornette small-N regime)
The mandate flagged the small-N / coarse-timestamp risk. Diagnostics: median inter-event gap 1.2s,
**20.4% of inter-event gaps are exactly 0** and 47.7% are sub-second. To rule out the worry that the
signal is carried by simultaneous (tied-timestamp) failures inflating S_t:
- Only **13 of 109** failure events share a timestamp with the immediately-prior failure.
- **De-coarsening test** (force monotone minimum spacing on tied/zero gaps, then re-fit):
  - +0.5 s spacing → dBIC = 47.95, alpha = 1.85 (still strong)
  - +2.0 s spacing → dBIC = 26.22, alpha = 1.85 — i.e. **converges to the call-index reference (26.85)**.

So the self-excitation is **not** a tied-timestamp artifact: even after aggressively spreading ties
to 2 s apart, the Hawkes term still pays for itself by ~26 BIC, matching the index-clock estimate.

## Bottom line
**WALL-CLOCK CONFIRMS.** The Codex H2 self-excitation (dBIC>6, alpha>0) is robust to the choice of
clock and to coarse-timestamp ties. This strengthens the H2 external-validity record IF dengcchi
picks path B. It is a defensive check only — it does NOT address the product_realist altitude YELLOW
and by itself does NOT earn a 6th GREEN. VERDICT-0049 remains untouched (orchestrator owns verdicts).

**Outputs:** `experiments/2026-06-01/EXP-0044/results/wallclock_codex.{csv,json}`.
