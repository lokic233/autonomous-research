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

M4: numeric comparison vs LLMCompiler (arXiv 2312.04511) reported accuracy under DAG-parallel
   dispatch (HotpotQA/ParallelQA) vs measured correctness.

## Honest-fallback branch
If NO real benchmark reachable: (a) report unreachable, (b) hand-construct SMALL set of real-style
DAGs from published BFCL/tau-bench examples (LABELED illustrative, not population), (c) conclude
"sensitivity framework only — real detector FNR and real correctness remain unmeasured." That is a WIN.

## Decision rule (pre-registered)
- STRENGTHEN/SUPPORT the L0 weaken-direction if real e > 0.05 (pessimism holds; parallel-as-free refuted).
- WEAKEN the L0 weaken (i.e. parallel IS safe) if real e <= 0.025 AND empirical f_wrong <= 5%.
- KEEP-EXPLORING / sensitivity-framework-only if data insufficient or detector cannot be cleanly evaluated.
- Report f_indep on real data vs L0 either way.
