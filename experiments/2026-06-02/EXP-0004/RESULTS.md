# RESULTS — EXP-0004 (L0, CPU-only): Speculative Tool-Call Prefetch

- **Claim:** CLAIM-0003 | **Exp:** EXP-0004 | **Task:** TASK-0004 | **Project:** PROJ-0002
- **Method:** Analytic latency model + Monte-Carlo (5 seeds × 4000 trials/config, lognormal
  multiplicative jitter σ=0.15). Stdlib-only Python, CPU, ~7 s wall. See `PRE_REGISTRATION.md`
  (committed BEFORE running, commit b8427a1) for the full model.
- **Verdict: PARTIAL / CONDITIONAL** — leaning negative for the regime the claim emphasizes.

## Headline numbers
- **252 swept configs; 64.7% net-win overall**, but only **51.8% win in the realistic regime**
  (tool latency ≥ arg decode, r ≥ 1).
- MC validates analytic: max |analytic − MC| = **0.049** (well within σ=0.15 noise). Model sound.
- **Break-even correctness p\*** ranges 0.43→0.97 across the realistic regime and climbs monotonically
  with both tool/decode ratio `r` and leading-arg fraction `lead`.

## The core finding: break-even p\* rises toward 1 exactly where the claim wants to win
The upside when correct, `S = min((1−lead)·t_args, t_tool) − c_commit`, **saturates** at the
smaller of (remaining decode, tool latency). The penalty when wrong, `P = w·t_tool`, **grows
linearly** in tool latency. Break-even is `p* = P/(S+P)`. So as `t_tool` grows past `t_args`
(the "comparable-or-bigger tool latency" regime the claim names), the gain caps but the
misspeculation penalty keeps rising → p\* → 1.

### Break-even p\* (min correctness to net-win), w=1.0 (full wasted tool work)
```
 r=t_tool/t_args | lead=0.3   lead=0.5   lead=0.7
            0.25 |   0.556     0.556     0.556
             0.5 |   0.526     0.526     0.667
             1.0 |   0.606     0.690     0.800
             2.0 |   0.755     0.816     0.889
             4.0 |   0.860     0.899     0.941
             8.0 |   0.925     0.947     0.970
```
### Break-even p\* , w=0.5 (optimistic: only half the tool work wasted before cancel)
```
 r=t_tool/t_args | lead=0.3   lead=0.5   lead=0.7
            0.25 |   0.385     0.385     0.385
             0.5 |   0.357     0.357     0.500
             1.0 |   0.435     0.526     0.667
             2.0 |   0.606     0.690     0.800
             4.0 |   0.755     0.816     0.889
             8.0 |   0.860     0.899     0.941
```

### Expected latency, lead=0.5, w=1.0 (t_args normalized to 1; * = speculative beats baseline)
```
  r    T_base   p=0.7    p=0.8    p=0.9    p=0.95   p=0.99
 0.5    1.60   1.44*   1.34*   1.25*   1.20*  1.16*
 1.0    2.10   2.08*   1.94*   1.79*   1.72*  1.66*
 2.0    3.10   3.38    3.14    2.90*   2.77*  2.67*
 4.0    5.10   5.99    5.54    5.09*   4.87*  4.69*
 8.0    9.10  11.19   10.34    9.49    9.07*  8.73*
```

## Win region (map)
- **r < 1 (fast tools, slow-relative decode):** speculation wins at modest correctness (p\* ≈ 0.40–0.67).
  BUT this is the regime with the *least* tool latency to overlap — the absolute time saved is small
  (e.g. r=0.5: ~10–25% step speedup). The claim is technically supported here but the payoff is minor.
- **r ≈ 1 (tool ≈ arg-decode):** need p\* ≈ 0.61–0.80 (w=1). Plausible for high-confidence first args
  but not guaranteed; speedup ~5–20% at p≥0.8.
- **r ≥ 2 (tool latency dominates — the headline regime in the claim):** need p\* ≈ 0.76–0.97.
  At r=8 you need **>0.92 correctness just to break even**, and full wins (>10%) need p≈0.99.
  This is the regime the claim says is the win case, and it is precisely where it is HARDEST to win.
- **lead matters adversely:** higher leading-arg fraction (more decoded before firing) *raises*
  p\* because it shrinks the remaining-decode you can overlap (`(1-lead)·t_args`) while the penalty is
  unchanged. Speculating earlier (small lead) helps, but earlier = lower-confidence args = lower p.

## Honest verdict
**PARTIAL / CONDITIONAL, trending NEGATIVE for the emphasized regime.** The claim's win-condition
("speculation-correctness × overlapped-tool-latency > wasted-work cost") is mechanically correct as
stated, but the experiment shows the **break-even correctness is implausibly high exactly in the
high-tool-latency regime** the claim foregrounds: the overlap gain saturates at min(remaining-decode,
tool-latency) while wasted-work penalty scales with tool-latency, so p\* → 1 as r grows. Speculative
tool-call prefetch is only a robust, low-risk win when **tool latency is comparable to or smaller than
the remaining arg-decode (r ≲ 1)** — but that is the regime with the least latency to overlap, so the
absolute benefit is modest. For the lucrative high-tool-latency regime the net win requires
correctness rates (≥0.9–0.97) that are optimistic for real agent argument prediction. The honest-negative
branch in pre-registration fires: **wasted-work dominates in the interesting regime.**

## What a GPU / real-trace pass should measure
1. **Real per-token decode timings** (t_name, t_args) from an actual served model on GPU — to fix the
   true `t_tool/t_args` ratio per tool. (We swept it; we do not know where real agents sit.)
2. **Real speculation-correctness p_correct on agent traces:** decode the tool name + leading args,
   fire speculatively, and measure how often the leading-args (and full args) match the committed call,
   bucketed by tool and by leading-arg fraction. This is THE unknown that decides everything.
3. **Real wasted-work cost w and cancel latency:** can a fired tool actually be cancelled, and how much
   of t_tool is burned (idempotency, side-effects) — w is assumed; side-effecting tools may have w>1
   (rollback cost) which would make the negative even stronger.
4. **Commit cost c_commit:** real validation/merge overhead when speculated args are confirmed.

## Prior-art caveat (OWED at committee)
This experiment ran with **no network egress** — no literature/prior-art sweep was performed.
Speculative execution / prefetch under misprediction penalty is a classic CS pattern (branch
prediction, speculative I/O, LLM speculative *decoding*); the analytic break-even here is structurally
the same `p* = penalty/(gain+penalty)` form. **Flag at committee: a prior-art sweep is owed** to check
whether this specific agent-step framing (and any measured agent argument-prediction rates) already
exists.

## Artifacts
- `PRE_REGISTRATION.md` — model + win-condition + honest-negative branch (committed pre-run)
- `sim.py` — analytic + Monte-Carlo simulation (stdlib only)
- `results/sweep.csv` — 252-config expected-latency table (baseline vs speculative, analytic + MC mean±std)
- `results/breakeven.csv` — break-even p\* curve over (r, lead, w)
- `results/summary.json` — aggregate win fractions and p\* range
- `logs/run.log` — run log + MC-vs-analytic validation
