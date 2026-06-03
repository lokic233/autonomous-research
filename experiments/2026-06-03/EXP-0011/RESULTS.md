# RESULTS — EXP-0011 (CLAIM-0009)
researcher-0010 | L0 analytic model | CPU-only, stdlib-only, SERIAL, 5 seeds
Pre-registration committed FIRST (commit 0f55794). Honest pipeline; negatives are wins.
Numbers below are read from on-disk CSVs (results/sweep.csv, results/agentic_vs_reasoning.csv).

## VERDICT: PARTIAL (split) — comparative claim HELD; structure-aware-conditioning claim NEGATIVE

The claim has two separable parts. The model splits them cleanly:

### PART A (comparative) — HELD in model
"Agentic generation saves MORE FLOPs from early-exit than free-form reasoning."
- Agentic best-tuned-global early-exit saves **3.6pp (f=0.2) / 5.5pp (f=0.3)** MORE FLOPs
  than reasoning best-tuned-global at matched quality (realistic-f mean = **+4.56pp**,
  max +14.8pp). Monotonic in f: +1.8pp (f=0.1) -> +9.2pp (f=0.5).
- Mechanism confirmed in-model: shallow-saturating boilerplate tokens exit early, so a
  workload with more boilerplate gives the SAME global threshold more cheap exits.

### PART B (the actual novelty under test) — NEGATIVE
"A STRUCTURE-AWARE per-class threshold beats a single GLOBAL threshold at matched quality."
- Structure-aware per-class tau saves only **+0.46pp** FLOPs over the BEST-TUNED global at
  realistic f (0.2-0.3); median +0.42pp, max +1.17pp.
- **0 / 90** swept configurations clear the pre-registered 5pp meaningfulness bar — INCLUDING
  the most favorable extreme (f=0.5, max depth-gap, max delta_pp overall = **1.52pp**).
- This trips honest-negative branch **N1** (gap < 5pp at realistic f once global is tuned).
- Seed std is tiny (struct_flop_sd <= 0.0043, global <= 0.0073); the tiny negative min
  (-0.24pp) is Monte-Carlo noise around the Jensen floor, not a real reversal.

## WHY (the mechanism, and why EXP-0006 is vindicated)
Per-class >= global is DEFINITIONAL (Jensen): optimizing tau per partition cannot beat a
shared tau by definition. The pre-registered question was the MAGNITUDE. The model shows
the magnitude is ~0.5pp because **a single well-tuned global threshold already captures
almost all the structural benefit**: once tau is tuned to the workload's error budget,
shallow-saturating boilerplate tokens already exit early under that same global tau (their
confidence crosses any reasonable tau at a shallow layer regardless). The per-class knob
only buys the thin sliver where boilerplate could exit slightly shallower without blowing
the shared error budget — and that sliver is ~0.5pp at realistic f. This is EXACTLY the
EXP-0006 failure mode (grammar-region claim died against best-tuned-global), reproduced.

## SWEEP SUMMARY (struct extra savings over best-tuned-global, delta_pp)
- by f:      0.1->0.31 | 0.2->0.44 | 0.3->0.48 | 0.4->0.68 | 0.5->0.64  (mean over grid)
- by gap:    0.20->0.42 | 0.35->0.55 | 0.50->0.42  (realistic f)
- by E:      0.01->0.51 | 0.02->0.58 | 0.05->0.29  (realistic f)
- best-tuned-global already saves ~10.8% FLOPs at realistic f; struct gets ~11.3%.

## MAGNITUDE-AT-REALISTIC-f ANSWER (the headline)
At realistic agentic boilerplate fraction (f = 0.2-0.35), structure-aware per-class
early-exit beats a best-tuned global threshold by **< 0.5 percentage points of FLOPs at
matched quality** — NOT meaningful, and not worth the policy complexity. The comparative
"agentic > reasoning" effect (Part A) is real (~4.6pp) but it is delivered by the GLOBAL
policy already; conditioning the threshold on token class adds almost nothing.

## LIMITATIONS / WHAT A GPU PASS SHOULD MEASURE
This is an ANALYTIC MODEL, not a real LM. It assumes a parametric sigmoidal class-conditioned
confidence curve and a confidence-tied error model. A real-model L1/L2 pass should measure:
1. REAL layer-wise intermediate-LM-head confidence by token class on actual agent traces
   (tool-call JSON delimiters / schema keys / arg values / reasoning) with a real model
   (e.g. via early-exit LM heads a la CALM/LayerSkip) — to get the TRUE per-class
   saturation-depth gap and whether classes separate as assumed.
2. REAL boilerplate fraction f on production tool-calling traces (we ASSUMED 0.2-0.35;
   owed to measurement). If real f is higher and classes separate more crisply than the
   model, Part B could move — but the Jensen-vs-global ceiling argument suggests not by much.
3. REAL wall-clock with early-exit OVERHEAD (intermediate-head compute, batched-exit
   raggedness, KV-cache implications) — FLOPs-saved overstates wall-clock wins.
4. The matched-quality constraint at the SEQUENCE level (error propagation across a tool
   call), not the per-token level modeled here.

## PRIOR-ART CAVEAT (owed)
Early-exit / depth-adaptive decoding is PUBLISHED: CALM (Schuster 2022), Depth-Adaptive
Transformer (Elbayad 2020), SkipDecode (2023), LayerSkip (2024). This experiment does NOT
re-derive early-exit; it isolates the AGENTIC-STRUCTURE-CONDITIONED threshold and tests it
against a TUNED global baseline. The owed-and-flagged sweep is the real-model confidence-by-
token-class measurement on agent traces (item 1 above). The comparative agentic>reasoning
result (Part A) is, to our knowledge, the part most worth a real-model follow-up.

## FILES
- PREREGISTRATION.md (committed before run, commit 0f55794)
- run_l0.py (analytic model, vectorized over noise samples; SERIAL)
- results/sweep.csv (90 rows: slope x f x depth_gap x E, 5 seeds)
- results/agentic_vs_reasoning.csv (90 rows: agentic vs reasoning best-tuned-global savings)
