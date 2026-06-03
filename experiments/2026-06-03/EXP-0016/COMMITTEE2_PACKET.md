# COMMITTEE#2 — CLAIM-0011 (PROJ-0001), WITH real-benchmark L1 (EXP-0014 L0 + EXP-0016 L1)
## SECOND pass (post-L1). committee#1 (VERDICT-0013) voted unanimous YELLOW, relabeled the L0 to a 'model-based sensitivity analysis', and approved an L1 to measure the REAL dependency-detector FNR e + real correctness on a real benchmark (tau-bench/AppWorld/BFCL). The L1 is now in. Cast FINAL votes WITH this evidence. The engine enforces real 6/6; GREEN/promote only if truly unanimous green by role — NEVER fabricate. This L1 RESOLVED the load-bearing unknown with REAL data and refutes the 'free win' — vote honestly (a well-evidenced negative that resolves the open question is the correct outcome; the contribution is now non-empty).

## L1 KEY FINDINGS (real BFCL v4, live-fetched; 257 real within-turn DAGs + 440 parallel instances; 3 detectors incl a real Qwen2.5-1.5B LLM run on H100):
1. REAL dependency-detector FNR e = 0.582 (heuristic value-dataflow) / 0.164 (state-aware heuristic) / 0.615 (LLM). ALL >> the 0.025 safety threshold AND >= L0's assumed 0.05. -> naive detect-then-parallelize is UNSAFE on real stateful agentic traces.
2. Real-data refinement L0 could not see: FNR is DOMINATED by STATEFUL/order dependencies (FNR 0.27-0.97) — deps with NO visible argument link; value data-flow is ~solvable (FNR 0.00-0.30). The danger is invisible state deps.
3. Empirical f_wrong (real missed edges dispatched parallel) = 2.4-8.5%/call, 3-17%/sequence — VALIDATES L0's binomial 1-(1-e)^k (modeled 0.074 vs empirical 0.024-0.085). Missed edges are stateful -> wrong CWD/missing file -> hard fail, not soft degradation.
4. f_indep on BFCL parallel categories = 1.000 (curated ceiling, NOT a population mix — honest caveat); L0's 0.44-0.71 mixed is more representative.
5. LLMCompiler (arXiv 2312.04511) comparison: it PLANS an explicit DAG with variable refs, never does post-hoc independence DETECTION — which is exactly why it gains accuracy where detect-then-parallelize loses it. The measured-e wall EXPLAINS LLMCompiler's design choice: the free win needs plan-time DAG construction, not after-the-fact detection.

## HONEST CAVEATS the researcher disclosed (weigh them): parallel-cat f_indep=1.0 is a curated ceiling; heuristic data-class recall is partly circular (use LLM's 0.70); GT state-edge rule is conservative; LLM judge is a small 1.5B (frontier untested, would likely lower e but unlikely to reach <=0.025 given 0.18-0.30 state recall); full agent-loop re-execution not done (f_wrong computed from real detector errors on real DAGs — the prereg-specified honest substitute).

## CLAIM
claim: "In real multi-tool LLM agent traces, the empirically-measured fraction of\
  \ independent (parallelizable) tool calls within a single agent step is HIGH ENOUGH\
  \ (>30%) that latency-bound agentic serving leaves substantial wall-clock on the\
  \ table by dispatching tool calls serially \u2014 AND parallel dispatch does NOT\
  \ change task correctness (the parallel calls are genuinely order-independent),\
  \ making it a free latency win that current serial agent loops forgo."
why_it_matters: 'Distinct from the dead efficiency-knob claims: this is an EMPIRICAL

## FULL L1 RESULTS (EXP-0016)
# RESULTS — EXP-0016 (L1, CLAIM-0011, PROJ-0001)
researcher-0016 | node cli:devgpu014 (H100, real egress via fwdproxy) + cli:dengcchi-mac (engine)
Pre-registered & committed BEFORE running (commit 25452d6). Honest pipeline. Negatives/insufficient = WINS.

## TL;DR VERDICT: **STRENGTHEN the L0 weaken** — real data CONFIRMS the L0's load-bearing pessimism, and
## refines it: the danger is STATEFUL/ORDER dependencies, not value data-flow.

The L0 (EXP-0014, YELLOW 6/6) ASSUMED a dependency-detector false-negative rate e=0.05 and was empty
until measured on real data. **We measured the real e on a real benchmark.** It is NOT <=0.025 (safe).
It is 0.16-0.61 depending on the detector — **at or well above the L0's assumed 0.05**. Parallel-dispatch
as a "free latency win" is refuted on real agentic tool-call traces, exactly as the L0 feared, and worse.

---

## 1. DID WE GET A REAL BENCHMARK? YES.
**Berkeley Function-Calling Leaderboard (BFCL) v4** — the canonical real multi-tool-call benchmark with
ground-truth. Pulled live from the official Gorilla repo (raw.githubusercontent.com/ShishirPatil/gorilla,
branch main, berkeley-function-call-leaderboard/bfcl_eval/data/ + possible_answer/) on 2026-06-03.
Categories used (REAL, with ground-truth call sets / DAGs):
  - BFCL_v4_parallel (200 instances, 540 calls), BFCL_v4_parallel_multiple (200, 607),
    BFCL_v4_live_parallel (16, 39), BFCL_v4_live_parallel_multiple (24, 55) — real parallel-intent calls.
  - BFCL_v4_multi_turn_base (200 instances -> 257 within-turn multi-call sequences, 668 calls) —
    real ordered tool-call DAGs over a stateful GorillaFileSystem/Twitter/etc. API. THIS is where real
    dependencies live (cd->relative-path ops; mkdir/touch/cp/mv->ops that consume the created entity).
Egress (PyPI/HF/GitHub = 200) confirmed working on devgpu014, reusing ros-EXP-0003 venv + fwdproxy env.

## 2. REAL INDEPENDENT-CALL FRACTION (M1) vs L0
| BFCL category | multicall inst | calls | instances w/ cross-call data dep | f_indep (call-wt) |
|---|---|---|---|---|
| parallel | 200 | 540 | 0 | **1.000** |
| parallel_multiple | 200 | 607 | 0 | **1.000** |
| live_parallel | 16 | 39 | 0 | 1.000 |
| live_parallel_multiple | 24 | 55 | 0 | 1.000 |

REAL finding: BFCL's parallel categories are **definitionally 100% independent** — every ground-truth call
takes only literal args, none consumes another call's output. **This is HIGHER than the L0's constructed
0.44-0.71**, because BFCL curates these instances to be parallelizable. HONEST CAVEAT: this is a CEILING /
selection artifact of the parallel category, not a population statistic for "all agent tool calls." The L0's
mixed-corpus 0.44-0.71 is arguably the more representative number for a heterogeneous workload; BFCL's
parallel split is the optimistic end. Either way: when calls ARE meant to be parallel, real independence is
genuinely high. The risk was never the genuinely-independent calls — it is detecting the dependent ones.
(CSV: results/metricA_findep_real.csv)

## 3. *** THE ANSWER — REAL DEPENDENCY-DETECTOR FALSE-NEGATIVE RATE e (M2) ***
Ground-truth DAGs = 257 real within-turn call sequences from BFCL multi_turn_base (668 calls, mean 2.6
calls/seq). True dependency edge i->j defined by BFCL execution semantics (NON-circular for the state class):
  - DATA/NAME dep: j's arg value = an entity i created/touched/moved/renamed.
  - STATE/ORDER dep: i mutates CWD (cd / mkdir) and j is a relative-path consumer (must run after i).
We evaluated THREE realistic detectors against these GT edges:

| detector | true edges | FN | **e = FNR** | recall | data-class FNR | state-class FNR |
|---|---|---|---|---|---|---|
| heuristic value-data-flow (shared-literal) | 110 | 64 | **0.582** | 0.418 | 0.000* | 0.970 |
| heuristic data-flow + CWD-state-aware       | 110 | 18 | **0.164** | 0.836 | 0.000* | 0.273 |
| LLM (Qwen2.5-1.5B-Instruct, pairwise judge)  | 109 | 67 | **0.615** | 0.385 | 0.302 | 0.818 |

\* the heuristic's perfect data-class recall is partly CIRCULAR (GT data-edges defined by the same
literal-match) — so the LLM's INDEPENDENT data-class recall of 0.70 (FNR 0.30) is the trustworthy
data-flow number. The state-class numbers are non-circular for all detectors.

**DECISION (pre-registered): is real e <=0.025 (parallel safe) or >0.05 (L0 pessimism holds)?**
-> **e is 0.16-0.61 across all detectors — NOT <=0.025, and >=/>> 0.05. L0 PESSIMISM HOLDS.**

KEY REFINEMENT THE L0 COULD NOT SEE (real-data contribution): the FNR is **dominated by STATEFUL/ORDER
dependencies** (FNR 0.27-0.97), NOT value data-flow (FNR 0.00-0.30). A detector that only follows explicit
argument data-flow (the textbook design) misses ~97% of real state dependencies. Even a CWD-state-aware
heuristic still has e=0.16. A small LLM judge is worst (e=0.61) — it under-flags ordering deps. The real
risk is precisely the dependencies that have NO visible argument link. (CSV: results/metricB_detector_e_real.csv)

## 4. REAL / EMPIRICAL f_wrong + correctness (M3)
Empirical f_wrong = fraction of real sequences/calls corrupted when the detector's MISSED true edges get
dispatched in parallel (the dependent call consumes stale/absent state):

| detector | f_wrong (seq w/ >=1 corruption) | f_wrong (per-call) | e | L0 modeled 1-(1-e)^k |
|---|---|---|---|---|
| heuristic data-flow | 0.167 | 0.085 | 0.582 | — |
| heuristic data-flow+state | 0.031 | 0.024 | 0.164 | 0.074 (k~0.43 edges/seq) |
| LLM Qwen-1.5B | 0.148 | 0.076 | 0.615 | — |

EMPIRICAL f_wrong (2.4-8.5% per-call; 3-17% per-sequence) is in the SAME RANGE the L0 modeled at e=0.05
(10-12%), and the L0's binomial 1-(1-e)^k bookkeeping is VALIDATED as a reasonable approximation (modeled
0.074 vs empirical 0.024-0.085). The L0 was not just hand-waving — its mechanism is real. End-to-end:
because true edges in multi_turn are stateful, a missed edge -> wrong CWD / missing file -> the dependent
call hard-fails or returns wrong output -> wrong final answer (not a soft degradation). (CSV: metricC_fwrong_real.csv)

## 5. LLMCompiler (arXiv 2312.04511, ICML 2024) NUMERIC COMPARISON (M4)
Published headline (fetched live from arxiv abstract + repo): vs ReAct, LLMCompiler reports up to **3.7x
latency speedup, 6.7x cost saving, and accuracy improvement of up to ~9%** (largest gain on ParallelQA,
the intertwined-multi-call benchmark; HotpotQA ~ parity). CRUCIAL CONTRAST: LLMCompiler does NOT do
post-hoc dependency DETECTION on a flat call set (the failure mode we measured). Its **Planner emits an
explicit DAG with variable references ($1,$2,...)** — dependencies are CONSTRUCTED at plan time, so the
parallelizer never has to "detect" a missed edge. That is exactly why it gains accuracy where our
detect-then-parallelize pipeline loses it. Our real-e result EXPLAINS LLMCompiler's design choice: explicit
LLM-planned DAGs sidestep the e~0.16-0.61 detection wall. The "free latency win" is achievable ONLY with
planned dependency structure, NOT with after-the-fact independence detection on arbitrary tool-call sets.

## 6. COMMITTEE#2-READY VERDICT: **HELD (strengthened, weaken-direction) — real e measured, L0 confirmed**
- Real benchmark obtained (BFCL v4). Real f_indep, real e, empirical f_wrong all measured on real data.
- The load-bearing unknown is RESOLVED: real e = 0.16-0.61 >> 0.025 safety threshold -> naive
  detect-then-parallelize is NOT a free win on real stateful agentic traces. L0's weaken HOLDS and is
  STRENGTHENED (real e >= L0's assumed 0.05).
- New real contribution beyond L0: the FNR is concentrated in STATEFUL/ORDER deps (data-flow is ~solvable);
  and the LLMCompiler comparison shows the escape hatch is plan-time DAG construction, not detection.
- Honest caveats: (a) BFCL parallel-category f_indep=1.0 is a curated ceiling, not population mix; (b) the
  heuristic's data-class recall is circular (use the LLM's 0.70 for data-flow); (c) GT state-edges use a
  conservative "any cd/mkdir gates later relative ops" rule — defensible from GorillaFileSystem semantics
  but could slightly over-count; (d) the LLM detector is a small 1.5B model — a frontier LLM judge would
  likely lower e but is untested here (egress allows weights, not API). None of these flip the headline:
  no detector tested reaches e<=0.025.

## PATHS
- devgpu014: /home/dengcchi/ros-EXP-0016/{analyze.py, llm_detector.py, RESULTS.md, results/*.csv, results_llm.json, data/, possible_answer/}
- Mac (engine instance): /Users/dengcchi/autonomous-research-v3/experiments/2026-06-03/EXP-0016/ (PREREG.md + this RESULTS.md + CSVs)

## REPRODUCE
  cd /home/dengcchi/ros-EXP-0016 && python3 analyze.py        # M1, M2(heuristic), M3
  ./run_llm.sh                                                # M2(LLM), independent non-circular e

## L1 PRE-REG
# PRE-REGISTRATION — EXP-0016 (L1, CLAIM-0011, PROJ-0001)
researcher-0016 | committed BEFORE running | honest pipeline (negative/insufficient = WIN)

## Context
L1 real-benchmark validation of YELLOW L0 (EXP-0014, VERDICT-0013 unanimous 6/6).
L0 was a model-based sensitivity analysis on a CONSTRUCTED ReAct-archetype corpus. It found:
 - Part A: f_indep|multicall 0.44-0.71 across mixes (>30%) — but readout of generating oracle.
 - Part B: at ASSUMED detector FNR e=0.05, f_wrong=1-(1-e)^k ~ 10-12% — but e=0.05 unestablished.
Committee: contribution EMPTY until measured on REAL data. THE load-bearing unknown is the REAL e.

## Benchmark I will attempt (in order)
1. BFCL (Berkeley Function-Calling Leaderboard) — parallel + parallel_multiple categories.
   HF dataset gorilla-llm/Berkeley-Function-Calling-Leaderboard. Has real multi-tool-call data
   with ground-truth answers (the ground-truth function calls + their arguments).
2. Fallback: tau-bench, AppWorld.
Egress confirmed working on cli:devgpu014 (PyPI/HF/GitHub 200). Will use REAL data there.

## What I'll measure
M1 (REAL workload mix): on real multi-call steps (parallel categories), the REAL independent-call
   fraction. A call B depends on A iff B's arg value references A's output/return (data-flow), OR
   ordering constraint. For BFCL parallel categories the ground truth is a SET of independent calls
   (definitionally parallel) — so I measure the empirical fraction of cross-call arg data-dependencies
   among the ground-truth call sets, and the fraction of multi-call instances that have ANY dependency.
   Compare to L0 constructed 0.44-0.71.

M2 (REAL detector FNR e — THE ANSWER): implement a realistic dependency detector (heuristic
   arg-reference/data-flow extractor: does call_j's argument values/placeholders reference call_i's
   expected output or entities produced by call_i?). Build ground-truth dependency edges from the
   benchmark (which calls' args are produced by / reference another call's output). Evaluate detector
   FNR e = missed-true-edges / true-edges. DECISION: is real e <= 0.025 (parallel dispatch safe) or
   > 0.05 (L0 pessimism holds)?

M3 (REAL/empirical f_wrong): from the detector's actual errors on real DAGs, compute the empirical
   fraction of parallelized steps corrupted (a missed dep edge dispatched in parallel) — NOT modeled
   1-(1-e)^k. End-to-end correctness under parallel-vs-serial where feasible.

## committee#1 reference: VERDICT-0013 yellow (required this exact real-e measurement).
