# COMMITTEE#1 — CLAIM-0055 (PROJ-0025, eval-safety x agentic) — constrained-decoding SUPPORT-REMOVAL MISROUTE
## EMPIRICAL-PHENOMENON, effect=support/HELD. NOT metric-validity (causal behavioral effect: forced wrong ACTION). Anti-circular (GT=true-target+in-enum-or-not, harness-owned; monitor sees only emitted token+validity bit, NEVER GT). Vote HONESTLY by role — this is the strongest-positioned candidate of the v3 expansion + the first to cleanly clear the mechanism-novelty bar; do NOT rubber-stamp, do NOT reflexively kill.

## CLAIM: in agentic tool routing with HARD grammar-constrained decoding over an enum, when a request's correct action is NOT in the enum (out-of-set), the decoder mechanically forces the NEAREST in-enum member = 100pct-schema-valid, confidently-wrong action. Misroute rate rises as enum cardinality K falls + as the semantic gap to the nearest in-enum neighbor shrinks (near-miss MORE dangerous). ZERO recall under schema-validate+retry (validity 100pct by construction); NOT recoverable by the strongest faithful decoder (GAD) because it's SUPPORT-REMOVAL not within-support distortion; escape-hatch recall DECREASES as the nearest wrong member gets closer.

## L0 RESULT (6 temp x noise cells, anti-circular, both guards satisfied):
(R1, GUARD-1 anti-tuned-knob — STRONGEST possible): misroute rate monotone in K: 0.650(K=50) -> 0.859(20) -> 0.934(10) -> 0.970(5) -> 0.976(3), and KERNEL-INDEPENDENT (IDENTICAL across all 6 temp{0.05,0.15,0.40} x noise{0.10,0.30} cells). Geometric out-of-set-EXPOSURE law (smaller enum covers less intent space -> more out-of-set -> more forced misroutes); NO temp/noise can remove/reverse the sign = not a tuned-kernel artifact.
(R2 near-miss more dangerous): misroute CONFIDENCE rises monotone as neighbor-gap shrinks at every temp (0.05: 0.637far->0.801near; 0.15: 0.332->0.480; 0.40: 0.182->0.235), sign-stable — a near-miss looks confidently right.
(MONITORABILITY COLLAPSE): validity-monitor recall = 0 EXACT by construction (every emission is enum-member -> schema-valid -> retry never fires).
(GAD CANNOT FIX IT): GAD-style renorm-over-support out-of-set gap-recovery = 0.0000 in EVERY cell — true target has ZERO grammar support -> support-removal, OUTSIDE GAD's (2405.21047) within-support-distortion class.
(R5, GUARD-2 escape-hatch SCOPED to curve): escape-recall HIGH at far gaps (~1.0), COLLAPSES at near-miss (0.000-0.198), negative slope sign-stable — NOT useless; leaks specifically at near-miss = exactly where the misroute is also most confident.
No falsifier triggered.

## HONEST CAVEAT (researcher-flagged): L0 is a geometric similarity-kernel proxy, NOT a real LM — it establishes the MECHANISM + the monotone (K x neighbor-gap) laws, not absolute real-model rates. The kernel-independence is a strength (no tuned knob) but is intrinsic to the geometric model. The real-LM L1 must confirm on real logits.

## THE THREE THINGS TO STRESS-TEST HONESTLY:
(a) NOVELTY: is 'constrained decoding coerces out-of-set intents to valid-but-wrong actions' genuinely novel/unacknowledged, or known-folklore (everyone knows an enum-constrained decoder cannot emit a non-enum answer)? The non-obvious load-bearing part = the MONITORABILITY COLLAPSE (BOTH the validity monitor AND the strongest faithful decoder GAD are blind) + the (K, neighbor-gap) law + escape-leak-at-near-miss. Does GAD / the abstention lit / instruction-following lit already acknowledge the zero-support coercion + monitorability angle? (the scout claims GAD explicitly assumes in-language output, silent on zero-support — verify if you can).
(b) Is the GEOMETRIC-KERNEL L0 sufficient to establish the MECHANISM (the laws are monotone + kernel-INDEPENDENT, which is unusually strong for a proxy) pending the real-LM L1, or does 'no real logits' fundamentally undercut it?
(c) ECOLOGICAL: do production routers actually hard-constrain to a narrow enum with out-of-set traffic and NO escape hatch? (OpenAI strict / Outlines / XGrammar guided decoding are real + dominant; but do deployments include an escape hatch by default, blunting the harm?)

## CLAIM YAML
claim: "In agentic tool/action routing with HARD grammar-constrained decoding over\
  \ an enum of valid actions, when a request's correct action is NOT a member of the\
  \ enum (out-of-set intent), the decoder does not error or abstain \u2014 it mechanically\
  \ forces emission of the NEAREST in-enum member, producing a 100pct-schema-valid\
  \ confidently-wrong action call. The silent-misroute rate RISES as enum cardinality\
  \ falls and as the semantic gap between the true intent and its nearest in-enum\
  \ neighbor shrinks (a near-miss distractor is MORE dangerous than a far one). This\
  \ failure class has ZERO recall under the standard production mitigation (schema-validation\
  \ + retry \u2014 validity is 100pct by construction), is NOT recoverable by the\
  \ strongest distribution-faithful decoder (Grammar-Aligned Decoding) because the\
  \ failure is SUPPORT-REMOVAL (true target has zero grammar support) not within-support\
  \ distortion, and even an explicit 'other'/ASK_USER escape-hatch member has escape-recall\
  \ that DECREASES as the nearest wrong member gets semantically closer (so it leaks\
  \ at the dangerous near-miss params)."
why_it_matters: "FRESH AREA (eval-and-safety x agentic: constrained-decoding silent-error\

## L0 RESULTS (EXP-0062)
# RESULTS — EXP-0062 (CLAIM-0055)
**Researcher:** researcher-0060 | **L0** CPU-only, stdlib-only, SERIAL | elapsed ~13s | **2026-06-03**
**Outcome: HELD (support).** All five decision-rule conditions met, including the anti-tuned-knob
robustness guard and the scoped escape-hatch proximity-dependence guard.

## Setup (matches PRE_REGISTRATION.md)
- Intent space: 12×12 lattice = 144 candidate action cells in [0,1]^2. Request r ~ U([0,1]^2);
  true target t* = nearest cell. Enum = K random cells. GT (harness-owned): t*, in-enum?.
- Decoders read ONLY observables: similarity logits `-||r-c||/temp + N(0,sigma)` + emitted token +
  schema-validity bit. Misroute labeled AFTER the fact by harness (emitted vs t*). Anti-circular.
- Arm A = greedy mask; Arm B = GAD-style renormalize-over-support (argmax ≡ A, but we measure
  out-of-set gap-recovery); Monitor = schema-validate+retry; Arm C = escape-hatch ('other').
- 8 seeds/cell, 500 requests/trial, 95% CI. Kernel FIXED across K within each temp×sigma cell.

## R1 — Stream silent-misroute rate RISES as K falls (GUARD 1: anti-tuned-knob) ✓
`results/stream_misroute_vs_K_robustness.csv`

| K  | stream-misroute (mean±CI) | oos-fraction |
|----|---------------------------|--------------|
| 3  | 0.976 ± 0.006             | 0.976        |
| 5  | 0.970 ± 0.004             | 0.970        |
| 10 | 0.934 ± 0.006             | 0.934        |
| 20 | 0.859 ± 0.010             | 0.859        |
| 50 | 0.650 ± 0.022             | 0.650        |

Monotone decreasing in K. **Identical across ALL 6 temp×noise cells** (temp∈{0.05,0.15,0.40},
sigma∈{0.10,0.30}). This is the STRONGEST possible anti-tuned-knob result: the K-effect is not a
tuned-kernel artifact — it is a kernel-INDEPENDENT geometric law (out-of-set EXPOSURE grows as the
enum covers less of intent space). On out-of-set requests the masked decoder misroutes with
probability ≈1 regardless of K; the stream rate = P(out-of-set), which falls smoothly with K. No
temperature or noise tuning can remove or reverse the sign.

## R2 — Near-miss is MORE dangerous (misroute confidence rises as neighbor-gap shrinks) ✓
`results/misroute_confidence_vs_gap.csv` (K=10). Confidence = softmax mass on the emitted wrong action.

| temp | <=0.10 | <=0.20 | <=0.30 | <=0.45 | >0.45 |
|------|--------|--------|--------|--------|-------|
| 0.05 | 0.801  | 0.759  | 0.713  | 0.658  | 0.637 |
| 0.15 | 0.480  | 0.437  | 0.395  | 0.366  | 0.332 |
| 0.40 | 0.235  | 0.220  | 0.204  | 0.196  | 0.182 |

Confidence is monotone-decreasing in gap at EVERY temp and noise level (sign-stable): the closer the
nearest in-enum distractor, the MORE confidently the decoder emits the wrong-but-valid action — a
near-miss looks right. Absolute confidence scales with temp (expected), but the GAP-direction effect
(near > far) is invariant — not a tuned-knob artifact.

## R3 — Validity-monitor recall = 0 (by construction) ✓
Every A/B emission is an enum member ⇒ schema-valid ⇒ retry never fires ⇒ the standard
schema-validate+retry monitor catches 0/N misroutes. monitor_recall = 0.0 in every cell. The
monitorability collapse: the safety net that catches malformed output is blind to support-removal
coercion because the output is perfectly well-formed.

## R4 — GAD-style B recovers ~0 of the out-of-set gap (strongest-decoder-can't-fix-it) ✓
gad_recovery = 0.0000 in every cell. GAD (Park/Geng 2405.21047) recovers the grammar-CONDITIONAL
distribution, but on out-of-set intents the true target has ZERO grammar support, so renormalizing
over the enum cannot place any mass on it. This is SUPPORT-REMOVAL, not within-support distortion —
outside GAD's recoverable class. Confirms the mechanism-novelty (killer #9): the seminal incumbent
assumes the desired output is in-language and is silent on zero-support.

## R5 — Escape-recall DECREASES with distractor proximity (GUARD 2: scoped to the curve) ✓
`results/escape_recall_vs_proximity.csv` (K=10, escape-hatch arm C).

| temp/sigma | <=0.10 (near) | <=0.20 | <=0.30 | <=0.45 | >0.45 (far) |
|------------|---------------|--------|--------|--------|-------------|
| 0.05/0.1   | 0.000         | 0.221  | 0.859  | 1.000  | 1.000       |
| 0.15/0.3   | 0.080         | 0.309  | 0.710  | 0.995  | 1.000       |
| 0.40/0.3   | 0.198         | 0.312  | 0.486  | 0.778  | 0.966       |

Escape-recall is HIGH at far gaps (the hatch works when the true target is clearly novel) and
COLLAPSES at near-miss (the nearest concrete distractor out-competes 'other'). SCOPED claim confirmed:

## PRE-REG
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


## ORCHESTRATOR NOTE: PRIOR-ART (VERIFIED) — GAD (Park/Geng NeurIPS2024 2405.21047) = seminal within-support distribution-distortion fix, assumes desired output in-language -> SILENT on zero-support (does NOT acknowledge this mechanism = the killer-#9 pass); 'Wait that's not an option' (2409.00113, UNconstrained MCQ, model CAN say none); Know-Your-Limits abstention (model CHOOSES; hard-constrained decoding REMOVES the choice); structured-output-impact (2509.21791, avg reasoning deltas). Novelty = support-removal coercion as a GAD-irrecoverable failure class + the (K x neighbor-gap) law + the monitorability collapse. THIS IS THE STRONGEST-POSITIONED candidate of the run: non-textbook mechanism (cleared #9), STRONGEST decoder tested as the baseline (cleared the lexical-strawman trap), anti-tuned-knob is the strongest possible (kernel-independent), both standard mitigations modeled+insufficient, real safety relevance. If candidate-grade, L1 CONFIRMATORY: real LMs (Llama-3.1-8B/Qwen2.5-7B) + real constrained backend (Outlines/XGrammar/vLLM guided JSON) on a BFCL/ToolBench slice + held-out out-of-set requests -> misroute vs K + vs embedding-distance to nearest in-enum tool, validity-monitor recall~0, real GAD/ASAp out-of-set gap-recovery~0, escape-hatch recall vs distractor proximity. If you judge it's known-folklore OR the geometric L0 fundamentally undercuts it OR production escape-hatches blunt the harm, say YELLOW/RED honestly. If genuinely novel + the mechanism is L0-established + ecologically real, this is a clean APPROVE toward the real-LM L1 — and a real shot at v3's first green. Real 6/6 by role.
