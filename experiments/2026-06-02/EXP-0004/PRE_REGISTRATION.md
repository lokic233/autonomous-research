# PRE_REGISTRATION — EXP-0004 (L0, CPU-only)

- **Claim:** CLAIM-0003
- **Experiment:** EXP-0004 | Task TASK-0004 | Project PROJ-0002
- **Researcher:** researcher-0004
- **Level:** L0 (analytic + Monte-Carlo simulation, stdlib-only Python, ≤15 min, no GPU/network)
- **Date:** 2026-06-02

## The claim under test (CLAIM-0003)
"In tool-calling LLM agents, speculatively initiating the tool call as soon as the tool NAME +
high-confidence leading arguments are decoded (overlapping execution with the remaining
argument-JSON decode) reduces end-to-end agent-step latency vs serialize-then-call, with a net
win whenever speculation-correctness-rate × overlapped-tool-latency exceeds the wasted-work cost
of mispeculated calls."

## Latency model (one agent step)
Three primitive durations:
- `t_name` — time to decode the tool_name token(s) (small, fixed; same in both arms, cancels out).
- `t_args` — time to decode the remaining argument-JSON after the leading args.
- `t_tool` — tool execution (server-side) latency.
- `lead` — fraction of arg-JSON decoded BEFORE we can speculate (leading-arg fraction). The
  speculation trigger point is at `t_name + lead*t_args`; the remaining decode is `(1-lead)*t_args`.

**Baseline (serialize-then-call):**
  `T_base = t_name + t_args + t_tool`

**Speculative:** fire the tool at the trigger point `t_name + lead*t_args`. Two outcomes:
- **Correct (prob p):** the speculated args match the final args. Tool runs CONCURRENTLY with the
  remaining decode `(1-lead)*t_args`. We must still finish decoding before committing the result
  (commit cost `c_commit`, a fixed small overhead representing validation/merge).
  `T_spec_correct = t_name + lead*t_args + max((1-lead)*t_args, t_tool) + c_commit`
- **Wrong (prob 1-p):** the early-fired tool call was on wrong args. We pay wasted tool work
  `w * t_tool` (w = fraction of t_tool burned before we can cancel/discard; w in [0,1]), THEN we
  fall back to the serialize path for the correct call:
  `T_spec_wrong = t_name + t_args + t_tool + w*t_tool`  (= baseline + wasted work)
  (We assume the wasted work overlaps the tail decode where possible but in the worst-realistic
  case the corrected call cannot start until decode completes, so the redo is fully serial. We
  also report an optimistic variant where part of the redo overlaps.)

**Expected speculative latency:**
  `E[T_spec] = p*T_spec_correct + (1-p)*T_spec_wrong`

## Parameters swept
- `p_correct` ∈ {0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99}
- `r = t_tool / t_args` ∈ {0.25, 0.5, 1, 2, 4, 8}  (tool latency relative to arg decode)
- `lead` ∈ {0.3, 0.5, 0.7}  (leading-arg fraction decoded before speculation)
- `w` (wasted-work fraction of t_tool on misspeculation) ∈ {0.5, 1.0}
- `c_commit` = 0.05 * t_args (small fixed commit cost)
- Normalize `t_args = 1.0`, `t_name = 0.1` (cancels out anyway). t_tool = r.
- Monte-Carlo: ≥5 seeds, per-config jitter (lognormal multiplicative noise σ=0.15 on each
  primitive) to produce mean±std. Report analytic mean alongside MC mean.

## Win-condition tested
Speculative wins iff `E[T_spec] < T_base`. We solve for the **break-even p_correct** as a function
of (r, lead, w): the minimum correctness rate at which speculation breaks even. We map the win
region over (r, p) for each (lead, w).

## Analytic break-even
Speedup-when-correct: `S = T_base - T_spec_correct = (1-lead)*t_args + t_tool - max((1-lead)*t_args, t_tool) - c_commit`
  = `min((1-lead)*t_args, t_tool) - c_commit`.
Penalty-when-wrong: `P = T_spec_wrong - T_base = w*t_tool`.
Net E[T_spec]-T_base = `-p*S + (1-p)*P`. Break-even: `p* = P / (S + P)`.
So speculation needs `p_correct ≥ P/(S+P) = w*t_tool / (min((1-lead)*t_args, t_tool) - c_commit + w*t_tool)`.

## HONEST-NEGATIVE branch
If the break-even p* is implausibly high for realistic regimes (e.g. p* > ~0.9 whenever tool
latency ≥ arg decode, because the misspeculation penalty w*t_tool grows with t_tool exactly where
the upside saturates at min(.,.)), OR wasted-work dominates the overlap gain across the realistic
sweep → report **NEGATIVE**. If win region exists only in a narrow/unrealistic corner (e.g. tiny
t_tool, which is the regime where there's little to overlap anyway) → report **PARTIAL/conditional**.
We will state plainly which realistic regimes win and whether they matter.

## Predicted tension (stated up front, falsifiable)
The upside `S` saturates at `min((1-lead)*t_args, t_tool)` — it cannot exceed the smaller of the
two overlapped quantities — while the penalty `P = w*t_tool` grows LINEARLY in t_tool. So as the
"interesting" regime (big tool latency) is entered, upside caps but penalty keeps rising → we
PREDICT break-even p* rises toward 1 in exactly the regime the claim says should win. This is the
honest tension the experiment will quantify.
