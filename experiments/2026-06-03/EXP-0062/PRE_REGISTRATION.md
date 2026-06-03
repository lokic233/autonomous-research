# PRE_REGISTRATION — EXP-0062 (CLAIM-0055)

**Researcher:** researcher-0060 (PERSISTENT-SEEDER, BUG-115) | **Project:** PROJ-0025 | **Task:** TASK-0052
**Level:** L0 (CPU-only, stdlib-only, SERIAL, <=15 min) | **Date:** 2026-06-03
**Committed BEFORE running.**

## THE CLAIM (CLAIM-0055) — EMPIRICAL-phenomenon
In agentic tool routing with HARD grammar-constrained decoding over an enum of K valid actions,
when a request's correct action is NOT in the enum (out-of-set intent), the decoder mechanically
forces the NEAREST in-enum member = a 100%-schema-valid, confidently-wrong action (silent misroute).
- Silent-misroute rate RISES as enum cardinality K FALLS AND as the semantic gap to the nearest
  in-enum neighbor SHRINKS (near-miss MORE dangerous than far).
- ZERO recall under schema-validate+retry (validity 100% by construction).
- NOT recoverable by the strongest distribution-faithful decoder (GAD, Park/Geng NeurIPS2024
  2405.21047) because it is SUPPORT-REMOVAL (true target has zero grammar support), not within-
  support distortion.
- Even an escape-hatch ('other'/ASK_USER) member has escape-recall that DECREASES as the nearest
  wrong member gets semantically CLOSER (it leaks at near-miss).

## INTENT-SPACE MODEL (harness OWNS ground truth)
- Intent space = a 2-D lattice, the unit square [0,1]^2 sampled on a G×G grid of candidate action
  cells (G=12 -> 144 candidate cells). Every cell is a possible action.
- A REQUEST = a point r in [0,1]^2 with a TRUE-target = its nearest grid cell t* (continuous->cell).
- The ENUM of valid actions = a chosen subset of K cells drawn from the 144.
- GT facts (harness-owned, NEVER read by the decoder):
  (a) in-set? = is t* in the enum;  (b) the correct action = t*.
- OUT-OF-SET requests are the test class: t* not in enum. Misroute is defined ONLY for these.

## DECODER MODEL (reads ONLY observables: similarity scores + emitted token + validity bit)
LM pre-mask next-action preference = softmax over a FIXED similarity kernel between request r and
EACH of the 144 candidate cells:  pref(c) ∝ exp(-||r - c|| / temp) * exp(noise_c),
noise_c ~ Normal(0, sigma) (calibrated Gumbel-like logit noise). The kernel is FIXED across K
(anti-tuned-knob): same temp + sigma used for every K in a given robustness cell.

ARMS:
- **A — greedy mask (baseline):** restrict pref to enum members; emit masked-argmax.
- **B — GAD-style distribution-faithful (STRONGEST):** renormalize the FULL pref distribution over
  ONLY the in-grammar (enum) support, then argmax/sample. For out-of-set targets the true cell has
  ZERO support -> B emits a wrong-but-valid in-enum action. Metric: GAD out-of-set GAP-RECOVERY =
  fraction of out-of-set requests for which B emits the true target (must be ~0 by construction,
  but measured honestly — if >0 the claim WEAKENS).
- **C — escape-hatch:** add an 'other'/ASK_USER cell. Route to escape iff pref(escape) > pref(nearest
  concrete in-enum member). The escape cell's preference modeled as a FIXED escape-prior p_esc
  (a flat affinity) competing against the nearest concrete distractor. Metric: escape-RECALL =
  fraction of out-of-set requests correctly routed to escape, AS A FUNCTION OF nearest-distractor
  proximity (gap bins).
- **MONITOR — schema-validate + retry (standard mitigation):** every emission of A/B is schema-valid
  by construction, so retry never triggers -> monitor-recall on the misroute class = 0. Stated
  explicitly; measured as a sanity check (must be exactly 0).

## ANTI-CIRCULARITY
GT = (true-target cell t*, in-enum-or-not) is harness-owned. Decoder/monitor see only similarity
scores (observable proxy for LM preference) + the emitted token + the validity bit. Misroute label
is computed AFTER the fact by the harness comparing emitted-cell vs t*. The decoder NEVER sees
"is this correct".

## SWEEPS + METRICS
- **K sweep:** K in {3, 5, 10, 20, 50}.
- **neighbor-gap sweep:** for out-of-set requests, bin by gap = ||t* - nearest-in-enum-cell||
  (low -> high), measure misroute severity / confidence.
- **out-of-set fraction:** report misroute-rate conditioned on out-of-set (the test class).
- Metrics: (1) misroute-rate (out-of-set requests emitting a confidently-wrong valid action),
  (2) validity-monitor recall (= 0), (3) GAD out-of-set gap-recovery (~0),
  (4) escape-recall vs distractor proximity (gap bins).
- **Seeds:** >=8 seeds per cell; report mean + 95% CI (normal approx).

## ★ ANTI-TUNED-KNOB ROBUSTNESS (GUARD 1)
Derive the K-effect from a FIXED kernel. Repeat the misroute-vs-K curve across >=3 temps
(temp in {0.05, 0.15, 0.40}) AND >=2 noise levels (sigma in {0.10, 0.30}) = >=6 robustness cells.
HELD requires the K-effect (misroute rises as K falls) to be PRESENT in ALL cells (monotone sign-
stable), not only at one tuned temp. If the K-effect appears at only one temp -> TUNED-KNOB ARTIFACT
-> WEAKEN.

## ★ ESCAPE-HATCH SCOPE (GUARD 2)
The escape claim is SCOPED to the PROXIMITY-DEPENDENCE CURVE: report escape-recall as a function of
distractor proximity. Claim = "escape-recall DECREASES as nearest distractor gets closer" (leaks at
near-miss), NOT "escape hatch never works". Do NOT overclaim uselessness.

## DECISION RULES
**HELD** requires ALL of:
1. misroute-rate rises as K falls (monotone, ROBUST across ALL >=6 temp×noise cells),
2. misroute-rate rises as neighbor-gap shrinks (near-miss > far),
3. validity-monitor recall == 0 (exact),
4. GAD-style B out-of-set gap-recovery ~0 (<= a few %),
5. escape-recall DECREASES with proximity (negative slope, sign-stable).

**FALSIFIED / WEAKEN** if ANY of:
- misroute flat (or non-monotone) in K, OR flat in gap,
- the K-effect appears only at one tuned temp (tuned-knob artifact),
- GAD-B recovers a meaningful fraction of the out-of-set gap,
- escape-recall is high AND proximity-INDEPENDENT (escape just works -> claim overstated).

Report which, with misroute(K, gap, temp) tables + GAD-recovery + escape-recall-vs-proximity
+ the robustness check.
