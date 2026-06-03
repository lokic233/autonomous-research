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
the escape hatch is NOT useless — it leaks specifically at near-miss, exactly where the misroute is
also most confident (R2). Higher noise (sigma=0.3) softens the collapse slightly but the negative
slope is sign-stable across all 6 cells.

## DECISION
All HELD conditions satisfied:
1. ✓ stream-misroute rises as K falls — ROBUST (kernel-independent, all 6 temp×noise cells)
2. ✓ near-miss more dangerous (misroute confidence rises as gap shrinks) — sign-stable all temps
3. ✓ validity-monitor recall = 0
4. ✓ GAD-style B out-of-set gap-recovery ~0 (0.0000)
5. ✓ escape-recall decreases with proximity (leaks at near-miss) — sign-stable, scoped to curve

No falsifier triggered: misroute is NOT flat in K, NOT a tuned artifact, GAD-B does NOT recover the
gap, escape-recall is NOT proximity-independent.

**VERDICT: HELD / support** (L0). Leave at evidence_ready for the orchestrator (no self-converge).

## Honest caveats / scope
- L0 is a geometric similarity-kernel proxy for LM preference, not a real LM. The K-effect being
  kernel-INDEPENDENT is a strength (no tuned knob) but also means L0 establishes the MECHANISM and
  its monotone laws, not the absolute rates a real model would show.
- "misroute on out-of-set ≈ 1 for any K" is structural (the true target is never emittable). The
  substantive, K-sensitive quantity is the STREAM rate via out-of-set exposure (R1) and the
  near-miss CONFIDENCE/severity (R2). Reported as such, not as raw conditional misroute.

## What L1 should measure
Real LMs (Llama-3.1-8B / Qwen2.5-7B) + a real constrained backend (Outlines / XGrammar / vLLM guided
JSON) on a BFCL/ToolBench slice with HELD-OUT out-of-set requests (intents whose correct tool is
removed from the enum): (1) stream silent-misroute rate vs K and vs embedding-distance to nearest
in-enum tool; (2) near-miss confidence/severity vs embedding gap; (3) validity-monitor recall ≈ 0;
(4) real GAD / ASAp out-of-set gap-recovery ≈ 0; (5) escape-hatch (ASK_USER / 'none of these') recall
vs distractor proximity. Confirm the K-effect is kernel/embedding-temperature robust on real logits.

## Prior art (verified)
GAD (2405.21047, seminal within-support distribution-faithful fix; assumes desired output in-language
→ silent on zero-support). 'Wait, that's not an option' (2409.00113, UNconstrained MCQ — model CAN say
none). Know-Your-Limits abstention (model CHOOSES; constrained decoding REMOVES the choice).
structured-output-impact (2509.21791, avg reasoning deltas). NOVELTY = support-removal coercion as a
GAD-irrecoverable failure class + its (K × neighbor-gap) law + the monitorability collapse.

## Artifacts
- PRE_REGISTRATION.md, RESULTS.md, harness.py, harness2.py, run.py, run2.py
- results/stream_misroute_vs_K_robustness.csv, results/misroute_confidence_vs_gap.csv,
  results/escape_recall_vs_proximity.csv, results/run2.log
