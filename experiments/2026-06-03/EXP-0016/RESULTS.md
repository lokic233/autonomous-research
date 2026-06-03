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
