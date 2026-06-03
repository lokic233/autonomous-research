# RESULTS — EXP-0017 (L0, CLAIM-0013, PROJ-0001)
researcher-0017 | node cli:dengcchi-mac | CPU-only, stdlib-only (Python 3.9.6, no numpy), SERIAL.
Pre-registered & committed BEFORE running (commit 8dedca1). Honest pipeline. Negatives = WINS.
Run wall-clock: 5.1s (<< 15 min budget). 8 seeds, bootstrap 95% CI (2000 resamples). Trust on-disk CSVs in results/.

## TL;DR VERDICT: **HELD (conditional on workload + detectability)** — a model-based characterization.
Both falsifiable parts pass on the constructed trace generator, with explicit conditionality and a clean
anti-circularity guard. THIS IS NOT A REAL-DATA RESULT — it is a sensitivity/characterization study whose
contribution is the *framework + the conditional map*, not a universal number. A real L1 must measure the
real redundancy fraction, the real cheap-check AUC, and real task accuracy on real agent+RAG traces.

- (A) Redundant-retrieval fraction is >20% across essentially the whole realistic workload band, rising
      monotonically with re-query rate p_repeat and context-window size W (0.235 -> 0.816). The 20% floor
      is only approached at the LOW end (p_repeat=0.2, small W).
- (B) The cheap in-context-overlap check (lexical Jaccard, NO LLM call, NO ground-truth access) achieves
      AUC 0.84-1.00 (degrading cleanly with paraphrase), **beats random-skip at matched skip-rate by
      +9 to +19 accuracy points (CI strictly > 0 everywhere skip-rate>0)**, and yields a SAFE Pareto point:
      at tau=0.3 it skips 39% of retrievals at task-accuracy 1.000 (== always-retrieve) — i.e. 39% token/
      latency savings at ZERO accuracy loss, vs random-skip's 0.816 at the same skip-rate.
- Honest-negative branch NOT triggered: red_frac >= 20% in realistic band (N1 no), check beats random-skip
      with CI>0 (N2 no), and a savings>0 / acc-loss<=2pt point exists (N3 no). So under THIS workload model,
      the gate is real and non-empty. Verdict downgraded from "strong HELD" to "HELD-conditional" only
      because it is a constructed-trace study (see Limitations).

---

## 1. ANTI-CIRCULARITY (the load-bearing design choice — CLAIM-0008 was RED'd for exactly this)
Ground-truth redundancy and the cheap check share NO information channel:
  - GT-REDUNDANT(turn t) := the target need's LATENT item-id is already resident in the live context window
    (item-id bookkeeping). The check NEVER sees the item-id.
  - The cheap check sees ONLY realizable text: max lexical/hashed-embedding overlap between the query tokens
    and the resident span tokens. Whether a redundant span is *detectable* is governed by a SEPARATE knob
    (paraphrase_rate) that rewords the stored span away from the canonical query — so the check's recall is
    honestly bounded below 1 and degrades with paraphrasing. The predictor sits strictly BELOW the oracle
    (AUC < 1 for any paraphrase>0; oracle AUC = 1 by construction). This is the headroom gap, measured.

## 2. PART A — REDUNDANCY FRACTION vs WORKLOAD (results/A_redundancy_vs_workload.csv)
Redundancy is a function of how often the agent re-queries a recently-seen item (p_repeat) and how long
items stay resident (window size W). NOT a universal constant.

| p_repeat \ W | W=5 | W=10 | W=20 |
|---|---|---|---|
| 0.2 (low reuse)  | 0.235 | 0.283 | 0.355 |
| 0.4 (moderate)   | 0.431 | 0.459 | 0.505 |
| 0.6 (high)       | 0.616 | 0.630 | 0.657 |
| 0.8 (very high)  | 0.803 | 0.809 | 0.816 |

(95% CI widths ~ +/-0.01, see CSV.) FINDING: >20% redundancy holds across the entire realistic band; the
20% threshold is only *approached* at the lowest-reuse/smallest-window corner (0.235). For any long-horizon
agent that revisits topics (p_repeat>=0.4) the redundant fraction is 43-82%. CONDITIONALITY IS THE RESULT:
redundancy is driven by reuse-locality x window-residency, both of which are real, measurable trace properties.

## 3. PART B — CHEAP-CHECK QUALITY + ORACLE GAP (results/B_check_quality.csv)
At a fixed realistic workload (p_repeat=0.5, W=10), sweeping paraphrase_rate (= detectability difficulty):

| mode    | paraphrase | AUC (CI)             | best-F1 | prec | recall |
|---------|-----------|----------------------|---------|------|--------|
| jaccard | 0.0       | 1.000 [1.000,1.000]  | 1.000   | 0.999| 1.000  |
| jaccard | 0.3       | 0.954 [0.949,0.961]  | 0.922   | 0.993| 0.860  |
| jaccard | 0.6       | 0.901 [0.896,0.906]  | 0.835   | 0.900| 0.779  |
| jaccard | 0.9       | 0.835 [0.819,0.849]  | 0.764   | 0.664| 0.899  |
| hashed  | 0.0       | 0.933 [0.926,0.942]  | 0.869   | 0.865| 0.873  |
| hashed  | 0.3       | 0.862 [0.850,0.875]  | 0.801   | 0.844| 0.763  |
| hashed  | 0.6       | 0.782 [0.767,0.795]  | 0.735   | 0.664| 0.824  |
| hashed  | 0.9       | 0.686 [0.668,0.703]  | 0.716   | 0.575| 0.949  |

ORACLE GAP: oracle AUC = 1.0 (reads GT item-id). The cheap lexical check loses 0 to 0.165 AUC depending on
paraphrasing; the cruder hashed-embedding surrogate loses 0.07 to 0.31. The gap IS the cost of using a
realizable signal — and it grows exactly where redundant recalls are reworded rather than near-duplicate.
Lexical Jaccard dominates the stdlib hashed-embedding surrogate at every paraphrase level (the surrogate is
a deliberately cheap "hashing trick", not a learned embedding — a real embedding would likely close much of
the paraphrase gap; that is an explicit L1 question).

## 4. PART C — *** THE REAL BAR: BEAT RANDOM-SKIP @ MATCHED SKIP-RATE, DON'T TANK ACCURACY *** (results/C_pareto.csv)
FOCUS workload p_repeat=0.5, W=10, paraphrase=0.4 (a deliberately MIXED/moderate detectability point).
Baselines (results/C_baselines.csv): always-retrieve acc=1.000 savings=0; never-retrieve acc=0.541 savings=1.0.

Lexical-Jaccard check, by threshold tau (acc_check vs matched random-skip; delta CI):
| tau  | skip/savings | acc_check | acc_random@matched | delta (CI)            | acc_oracle |
|------|-------------|-----------|--------------------|-----------------------|------------|
| 0.10 | 0.781       | 0.741     | 0.642              | +0.099 [0.096,0.102]  | 1.000      |
| 0.15 | 0.520       | 0.950     | 0.761              | +0.190 [0.185,0.195]  | 1.000      |
| 0.20 | 0.439       | 0.995     | 0.804              | +0.192 [0.187,0.197]  | 1.000      |
| 0.25 | 0.420       | 0.999     | 0.807              | +0.193 [0.185,0.200]  | 1.000      |
| **0.30** | **0.393**   | **1.000** | **0.816**          | **+0.184 [0.178,0.190]** | 1.000  |
| 0.35 | 0.332       | 1.000     | 0.848              | +0.152 [0.147,0.158]  | 1.000      |
| 0.40 | 0.196       | 1.000     | 0.913              | +0.088 [0.080,0.095]  | 1.000      |

KEY RESULT (the bar the prompt set): the cheap check **beats random-skip at matched skip-rate at EVERY
operating point, with the bootstrap CI on the accuracy-delta strictly above 0** (+9 to +19 pts). At tau=0.3
it recovers the ORACLE outcome — 39% of retrievals skipped at task-accuracy 1.000, identical to always-
retrieve — so there is a genuine safe (savings=39%, acc-loss=0) Pareto point. The hashed-embedding surrogate
also beats random-skip everywhere (delta CI>0), but its safe point is smaller (~11% savings at acc 0.998).
So the gate is NON-EMPTY: it is not just "skipping things", it skips the RIGHT things.

ACCURACY-SAFETY of WRONG skips is explicitly modeled: a false-positive redundancy (check fires but item NOT
resident) removes needed content -> task fails. That is why aggressive low-tau skipping (tau<=0.1) DOES drop
accuracy (0.741 at 78% skip) — the safe region is tau in [0.25,0.4], where high precision keeps wrong-skips rare.

## 5. HONEST VERDICT
**HELD, conditional.** Under a constructed long-horizon agent+RAG trace model with reuse-locality and a
bounded context window: (A) redundant retrievals are a non-trivial >20% fraction across the realistic
workload band, and (B) a cheap, realizable, NO-LLM in-context-overlap check identifies them well enough to
beat random-skip at matched skip-rate by a CI-significant margin and to skip ~39% of retrievals at zero
task-accuracy loss. The honest-negative branch was not triggered. BUT this is a model-based characterization;
the numbers are conditional on the workload knobs and on lexical detectability, both of which are stated, not
hidden. The contribution is the anti-circular framework + the conditional map, not a universal constant.

## 6. LIMITATIONS / WHAT A REAL L1 MUST MEASURE
- REAL TRACES: real long-horizon agent+RAG logs (e.g. LangChain/AutoGPT-style agents, or memory-augmented
  assistants) with annotated "was the answer already in the live context window" labels. Our redundancy is
  generated, not observed.
- REAL EMBEDDING CHECK: replace the stdlib hashing-trick surrogate with a real sentence embedding; this most
  likely closes much of the paraphrase-driven AUC gap (our lexical check already does well; the question is
  how much a real embedding helps on genuine paraphrase).
- REAL TASK ACCURACY: our task-success model (success iff needed item available) is a clean abstraction; a
  real LLM may partially recover from a wrong skip (re-ask) or fail in subtler ways. Measure end-to-end task
  success with a real model in the loop.
- REAL COST MODEL: we count skipped retrievals as token/latency savings 1:1; real injected-token and
  retrieval-latency costs vary by system.

## 7. PRIOR-ART CAVEAT (be honest: adaptive retrieval IS published)
Self-RAG, FLARE, SKR ("when to retrieve"), Adaptive-RAG, and RAG cache/dedup all decide *whether/when* to
retrieve, and context-aware retrieval gating exists. **We do NOT claim novelty for adaptive retrieval.** The
narrow, honest novelty here is the *in-context-redundancy-specific* gate — skip a retrieval specifically
because the answer is ALREADY resident in the live context window — characterized ANTI-CIRCULARLY against an
independent (item-id) redundancy ground-truth, and benchmarked against the correct hard baseline (random-skip
at matched skip-rate), with the wrong-skip accuracy cost explicitly modeled. The prior adaptive-retrieval work
generally gates on "do I need external knowledge at all", not on "is this specific content already in my window";
and rarely reports the matched-skip-rate-vs-random control or an independent redundancy GT. That control + GT
definition is the methodological contribution. Whether it survives on real traces is the L1 question.

## FILES
- PRE_REGISTRATION.md (committed pre-run, 8dedca1)
- run_exp0017.py (stdlib-only, serial)
- results/A_redundancy_vs_workload.csv, B_check_quality.csv, C_pareto.csv, C_baselines.csv
- logs/run.log
