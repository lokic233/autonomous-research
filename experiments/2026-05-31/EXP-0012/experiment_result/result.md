# EXP-0012 — CLAIM-0009 ABLATION + INFORMED BASELINES (addresses VERDICT-0020)

**Domain:** MAP-0002. **CPU-only, stdlib-only, ~12s.** **Claim under test:** CLAIM-0009 (narrowed).
**Mandate (VERDICT-0020 required-evidence, the 3 CPU-doable items):**
1. ABLATED HEADLINE — recompute modality effect (Cramér's V + out-of-sample LOO-Brier) with `web_disabled`
   REMOVED, plus leave-one-**CLASS**-out CV. Decisive Q: does the signal SURVIVE removing the
   definitionally-determined cell, or does it collapse (claim is really "web_disabled→redirect", a config fact)?
2. INFORMED BASELINES — lift over (a) static deterministic error-class→Mode(modality) mapping and
   (b) a GATE-TYPE-ONLY predictor. Report lift over BOTH, not just over NULL p0=0.504.
3. BRUTAL HONESTY — if error-class and gate-type are observationally inseparable in this single-harness
   corpus, say so plainly.

`parse_session/classify_error/intent_class/head_cmd/block_text/recovery_modality` are **copied verbatim**
from EXP-0009 (==EXP-0007/0008), no cross-dir import. Same corpus `~/.claude/projects`, same K=6, same BROAD
recovery def, same modality assignment. **Sanity gate passed**: full-taxonomy V=0.7135, LOO-Brier +40.1% —
reproduces EXP-0009's headline (V=0.717) on the refreshed corpus (76 sessions / 3,530 calls / 369 failures /
233 recovered; was 74/3,508/364/232).

## GATE-TYPE — the harness-routing variable we test error-class against
A failure's error-class maps deterministically to a routing flag the harness exposes WITHOUT a fine taxonomy:
- **REDIRECTABLE** = hard tool-block with a sanctioned ALTERNATIVE tool (`policy.web_disabled`, `policy.input_filter`)
- **TERMINAL_GRANT** = permission gate that must be GRANTED, no alternative (`policy.perm_denied`)
- **TRANSIENT** = everything else (fixable in place / re-runnable; no routing rule)

This is the minimal "what does the harness route" variable. If error-class beats it, error-class carries
modality info beyond routing. If not, the headline signal IS routing (gate-type), not error-class.

## RESULTS

### 1a — web_disabled ABLATED (remove the redirect=1.0-by-construction cell, n=66)
| variant | N | Cramér's V | perm-p | LOO-Brier improve (out-of-sample) |
|---|---|---|---|---|
| FULL taxonomy (sanity) | 233 | **0.7135** | 0.0002 | **+0.1002 (40.1%)** |
| **web_disabled REMOVED** | 167 | **0.4490** | 0.0006 | **+0.0047 (2.2%)** |
| web_disabled + perm_denied removed (TRANSIENT-only) | 153 | 0.4088 | 0.0058 | **−0.0043 (−1.9%)** |

**The out-of-sample predictive value evaporates on ablation.** V drops 0.714→0.449 (a chi-square artifact —
χ²/N still flags *association* among the small transient cells), but the honest **out-of-sample LOO-Brier
gain collapses from +0.100 (40%) to +0.0047 (2.2%)**, and goes **negative** once both definitional poles are
removed. The 40% Brier reduction in the headline was **almost entirely the web_disabled cell** (and secondarily
perm_denied). Among genuinely transient errors, error-class does NOT predict modality out-of-sample.

### 1b — leave-one-CLASS-out CV (predict a held-out class from the REMAINING classes)
| variant | null Brier | LOCO Brier | improve |
|---|---|---|---|
| FULL taxonomy | 0.2500 | 0.3326 | **−0.0826 (−33.0%)** |
| web_disabled removed | 0.2144 | 0.2219 | **−0.0075 (−3.5%)** |

**LOCO improvement is NEGATIVE — the predictor is WORSE than the constant null when forced to generalize to
an unseen class.** Per-class detail: every class's actual redirect-rate is mispredicted by the pooled rate of
the others (web_disabled actual=1.000 vs pred-from-rest=0.311, Δ−0.231; perm_denied actual=0.000 vs 0.539,
Δ−0.034; cancelled 0.147 vs 0.568, Δ−0.048). The per-class rates are **idiosyncratic and do not transfer.**
This is the decisive falsification of "error-class → modality" as a *regularity*: the headline LOO-Brier
(−40%) was leave-one-SAMPLE-out, which leaks the class's own rate; under leave-one-CLASS-out it is *memorized
per-class rates*, not a learnable error-class→modality law.

### 2 — INFORMED BASELINES (the predictor-misattribution test)
| predictor | in-sample Brier | Cramér's V | out-of-sample LOO-Brier improve |
|---|---|---|---|
| NULL (constant p0=0.506) | 0.2500 | — | 0 (floor) |
| static error-class→Mode(modality) [0/1] | 0.1803 (acc 0.820) | — | — |
| **gate-type-ONLY (3-level)** | 0.1435 | 0.6525 | **+0.1045 (41.8%)** |
| **gate-BINARY-ONLY (REDIRECTABLE flag)** | 0.1496 | 0.6338 | **+0.0986 (39.4%)** |
| full error-class | 0.1227 | 0.7135 | +0.1002 (40.1%) |

**Lift of error-class over the informed baselines (out-of-sample LOO-Brier):**
- over **gate-type-only (3-level): −0.0043** — error-class is *worse* out-of-sample than the 3-level gate flag.
- over **gate-binary-only (just REDIRECTABLE): +0.0017** — a rounding-error gain over a *single bit*.
- over static-mapping (Brier): +0.058 in-sample only (vanishes out-of-sample per 1a/1b).

**A single bit — "is this a redirectable hard-block?" — recovers 39.4% of the Brier; the entire 17-class
error taxonomy recovers 40.1%. Error-class adds essentially nothing (≤0.2%) over the gate-type flag.**
This is exactly the signature VERDICT-0020 predicted for PREDICTOR MISATTRIBUTION.

### 3 — COLINEARITY DIAGNOSTIC (can the data even separate error-class from gate-type?)
- **error-class → gate-type is a perfect function** (every class maps to exactly one gate-type). So error-class
  and gate-type are **deterministically colinear** in this corpus by construction.
- The only observational way to credit error-class over gate-type is a *within-gate-type* modality signal from
  the finer class. Results:
  - **REDIRECTABLE** (n=68; classes: web_disabled=66, input_filter=2): within-V = **0.000**, LOO-Brier +0.000 —
    the finer class adds *nothing*; redirect-share is 1.0 regardless of which redirectable class.
  - **TERMINAL_GRANT** (n=14): only 1 error-class — error-class *is* gate-type here; no finer signal possible.
  - **TRANSIENT** (n=151; 13 classes): within-V=0.381 (perm-p=0.017 in-sample) but **LOO-Brier −0.0103 (−4.7%)** —
    no out-of-sample signal; the in-sample association is overfitting to tiny cells (10 of 13 classes have n≤4).

**Conclusion: error-class and gate-type are OBSERVATIONALLY INSEPARABLE in this single-harness corpus.**
No gate-type bucket contains ≥2 sizable error-classes that carry finer out-of-sample modality signal. We
CANNOT attribute the modality signal to error-class proper rather than gate-type+routing on this data —
only an interventional / cross-harness test (out of scope, CPU-only) could.

## VERDICT for CLAIM-0009: **WEAKEN** (verging on REFUTE of the error-class framing)
The committee's two objections are CONFIRMED by the data:
1. **DEFINITIONAL INFLATION — confirmed.** Removing the single by-construction cell (web_disabled, redirect=1.0)
   collapses the out-of-sample LOO-Brier gain from +40.1% to +2.2%, and removing both definitional poles drives
   it negative. The headline was carried by definitionally-determined cells. leave-one-CLASS-out CV is
   **negative (−33%)** — the "predictor" does not generalize to unseen classes; it memorizes per-class rates.
2. **PREDICTOR MISATTRIBUTION — confirmed.** A single bit (REDIRECTABLE flag) matches the full 17-class taxonomy
   out-of-sample (39.4% vs 40.1%); error-class lift over gate-type-only is **−0.0043** (negative). error-class
   adds nothing over gate-type. The colinearity diagnostic shows error-class→gate-type is a perfect function and
   the within-gate-type finer-class signal is zero (REDIRECTABLE) or out-of-sample-null (TRANSIENT).

**Honest statement of what survives.** What is real and robust is a **gate-type + harness-routing
characterization**, NOT an error-class predictor: *the harness's routing rule — whether a failure's gate is a
redirectable hard-block, a grant-required permission, or a transient error — determines recovery modality.*
That is a config/routing fact of the Claude Code harness, true but unsurprising and not the "error-class
predicts modality" headline. The error-class framing **must be retired** in favor of gate-type until an
interventional or cross-harness test can break the colinearity. On this single-harness observational corpus,
error-class and gate-type are **inseparable**, so no claim that privileges error-class over gate-type is
defensible.

## Files
- impl: `experiments/2026-05-31/EXP-0012/impl/modality_ablation.py`
- csv:  `experiments/2026-05-31/EXP-0012/experiment_result/ablation_baselines.csv`
- log:  `experiments/2026-05-31/EXP-0012/experiment_result/run_stdout.txt`
