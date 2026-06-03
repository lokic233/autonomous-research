# PRE-REGISTRATION — EXP-0011 (CLAIM-0009)
researcher-0010 | L0 (CPU-only, stdlib-only, SERIAL, modeling/analytic) | <=15 min compute
Committed BEFORE running. Honest pipeline — negatives are WINS.

## THE CLAIM (CLAIM-0009)
On agentic/tool-calling generation, token-level early-exit (computing fewer transformer
layers when the intermediate LM head is confident) saves strictly MORE FLOPs at matched
output quality than on free-form reasoning text, because agentic boilerplate tokens
(JSON delimiters, tool-call scaffolding, schema keys) are low-entropy and saturate
confidence at shallow layers — so a STRUCTURE-AWARE early-exit threshold (looser inside
scaffolding, stricter in argument values/reasoning) beats a single GLOBAL threshold at
matched quality.

## HYPOTHESIS (falsifiable)
H1: At matched token-error-rate, a STRUCTURE-AWARE per-class tau policy achieves lower
    mean FLOPs/token (more layers skipped) than the BEST-TUNED GLOBAL single-tau policy.
H2 (the magnitude question — the real test): the FLOP-savings GAP (structure-aware minus
    best-tuned-global) at realistic boilerplate fraction f and realistic per-class depth
    gap is MEANINGFUL (we set a pre-registered meaningfulness bar: >= 5 percentage points
    of additional FLOPs saved at matched quality). If the gap is < 5pp at realistic f
    once global is properly tuned, we REPORT NEGATIVE/PARTIAL.

## EXP-0006 LESSON (explicitly honored)
The baseline MUST be the BEST-TUNED global threshold, swept to the per-workload optimum —
NOT an arbitrary one. Jensen's inequality guarantees per-class optimum >= global optimum
TRIVIALLY (optimizing per-partition can't be worse than a shared constraint). So the
existence of a gain is DEFINITIONAL, not a discovery. The ONLY honest question is the
MAGNITUDE of the gain at realistic operating points and whether it justifies complexity.
The EXP-0006 grammar-region claim DIED exactly here. We pre-commit to reporting magnitude.

## PRIOR ART (caveat owed)
Early-exit / depth-adaptive transformers are PUBLISHED: CALM (Schuster et al. 2022),
Depth-Adaptive Transformer (Elbayad 2020), SkipDecode (2023), LayerSkip (2024). Novelty
we must isolate: the AGENTIC-STRUCTURE-CONDITIONED threshold (tau by token class) and
whether it beats a tuned global on agentic traces. We do NOT re-derive early-exit; we
test the conditioning. This is a MODEL, not a real LM — flag the real-model sweep as owed.

## MODEL (analytic, deterministic+stochastic)
- L_total layers (default 32). A token exits at the shallowest layer L where intermediate
  LM-head confidence c(L) >= tau. FLOPs_token ~ L / L_total (linear in layers computed).
- An exit is CORRECT if early prediction == full-model prediction; else a QUALITY ERROR.
  We model error as: a token of class k that exits at layer L < L_total has error
  probability = P(early-pred != full-pred | exit at L), which DECREASES as L grows toward
  the class's confidence-saturation depth.
- CONFIDENCE-VS-LAYER is CLASS-DEPENDENT. We model confidence rising sigmoidally with
  layer, saturating at a class-specific depth d_k (in [0,1] of L_total):
    c_k(L) = sigmoid( a * (L/L_total - d_k) )   (a = slope)
  Boilerplate/delimiter/schema-key tokens: SHALLOW saturation (small d_k, e.g. 0.25).
  Argument-value / reasoning tokens: DEEP saturation (large d_k, e.g. 0.70).
- Quality error of an early exit at layer L for class k: the full-model prediction is
  "locked in" once c_k(L) crosses a correctness threshold; we model
    err_k(L) = max(0, base_err * (1 - c_k(L)))   — confident exits are usually correct.
  (So exiting early in a saturated region is nearly free of error; exiting before
  saturation costs quality.)

## TOKEN CLASSES & WORKLOADS
- AGENTIC workload: fraction f of tokens are BOILERPLATE (shallow d_k), (1-f) are
  VALUE/REASONING (deep d_k). f swept over {0.1, 0.2, 0.3, 0.4, 0.5}. Realistic-f anchor:
  we treat f in [0.2, 0.35] as realistic for tool-calling traces (JSON scaffolding,
  keys, delimiters) per published agent-trace token analyses — flagged as an ASSUMPTION
  owed to real measurement.
- FREE-FORM REASONING workload: f_boiler ~ 0 (almost all deep-saturating). Used to test
  the comparative claim "agentic saves MORE than reasoning".

## POLICIES
(a) GLOBAL (HONEST BASELINE): single tau applied to ALL tokens. We SWEEP tau over a fine
    grid and pick the tau that MINIMIZES FLOPs subject to error-rate <= budget. This is
    the best-tuned global — the key control.
(b) STRUCTURE-AWARE: per-class tau (tau_boiler, tau_value). Each swept; we pick the
    per-class pair minimizing FLOPs subject to the SAME matched error budget. Looser tau
    for boilerplate (exit shallow), stricter for value/reasoning.

## PRIMARY METRIC
FLOPs saved at MATCHED output quality. We fix an error budget E (token-error-rate), tune
BOTH policies to operate at error <= E, and compare mean FLOPs/token. Report
  delta_FLOP = FLOP_global_best - FLOP_structure_aware  (>=0 by Jensen; magnitude is the test).

## SWEEPS
- f in {0.1,0.2,0.3,0.4,0.5}
- depth gap (d_value - d_boiler) in {0.2, 0.35, 0.5}  (boiler d=0.25 fixed; value d varies)
- error budget E in {0.01, 0.02, 0.05}
- L_total = 32; tau grids fine (>=50 points each); slope a sweep light {6,10}
- STOCHASTIC component: per-token class assignment + confidence noise; >= 5 seeds; report
  mean +/- std.

## HONEST-NEGATIVE BRANCH (pre-committed)
Report NEGATIVE or PARTIAL if ANY of:
  (N1) structure-aware beats best-tuned-global by < 5pp FLOPs at realistic f (0.2-0.35);
  (N2) realistic agentic boilerplate fraction f is too low for the gap to matter;
  (N3) the matched-quality constraint erases the savings (tight E forces both policies
       to compute most layers anyway);
  (N4) the agentic-vs-reasoning comparative advantage is negligible.
We will NOT spin a definitional Jensen gain as a discovery.

## VERDICT RULE
- HELD: structure-aware beats best-tuned-global by >= 5pp FLOPs at realistic f AND the
  agentic>reasoning comparative gap holds, robust across seeds.
- PARTIAL: gain exists but is small / only at extreme f / sensitive to E.
- NEGATIVE: N1-N4 trip.

## REPRO
Single stdlib Python script run_l0.py, SERIAL (no multiprocessing). Trust on-disk CSVs.
