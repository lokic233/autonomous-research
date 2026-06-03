# PRE-REGISTRATION — EXP-0014 (L0, CLAIM-0011, PROJ-0001)
researcher-0014 | node cli:dengcchi-mac | CPU-only, stdlib-only, SERIAL (multiprocessing BLOCKED on this Mac)
TASK-0013 | Pre-registered & committed BEFORE running. Honest pipeline — a NEGATIVE result is a WIN.

## THE CLAIM (CLAIM-0011)
"In real multi-tool LLM agent traces, the empirically-measured fraction of INDEPENDENT (parallelizable)
tool calls within a single agent step is HIGH ENOUGH (>30%) that latency-bound serving leaves substantial
wall-clock on the table by dispatching serially — AND parallel dispatch does NOT change task correctness
(the parallel calls are genuinely order-independent)."

This is a MEASUREMENT / CHARACTERIZATION study. Two FALSIFIABLE parts:
  (A) independent-call fraction (>30% threshold)
  (B) order-independence / correctness-safety of parallel dispatch.

## SCOPE HONESTY (load-bearing — read first)
No real agent benchmark (tau-bench / AppWorld / BFCL) is installable offline on this CPU-only Mac with
no network. We therefore CONSTRUCT a corpus of realistic multi-tool agent STEPS from known ReAct /
tool-calling archetypes. CONSEQUENCE, pre-committed:
  - We DO NOT claim a universal population statistic for "real agents."
  - We PARAMETERIZE the workload mix and report the independent-call fraction AS A FUNCTION of mix:
    "IF the workload is composed of X% fan-out / Y% sequential / Z% mixed steps, THEN parallelism is P."
  - The headline number is CONDITIONAL on the assumed mix and is labeled as such everywhere.
  - L1 (real-trace) is required to turn this into a population claim. Stated explicitly in RESULTS.

## PRIOR ART (must distinguish — pre-committed)
Parallel function calling IS published and shipped. We MUST NOT claim the IDEA as novel:
  - LLMCompiler (Kim et al. 2023/24): plans a tool-call DAG, dispatches independent calls in parallel.
  - OpenAI/Anthropic "parallel tool calls" (native multi-tool-call in one assistant turn).
  - ReWOO (Xu et al. 2023): decouples reasoning from observation, plans tool calls upfront.
  - AsyncLM / async function calling: overlaps generation with tool execution.
Our contribution is NOT "you can parallelize tool calls." It is the EMPIRICAL CHARACTERIZATION:
  (1) how MUCH independent parallelism actually exists as a function of workload composition, and
  (2) the CORRECTNESS-SAFETY bound — what fraction of steps a realistic (imperfect) dependency
      detector would PARALLELIZE WRONGLY, producing a wrong result.
If a committee judges this fully subsumed by LLMCompiler's empirical eval, that is a novelty caveat we
report honestly (LLMCompiler reports latency speedups but, to our knowledge, does not report a
detection-error correctness-safety bound as a function of an imperfect dependency classifier).

## PRE-REGISTERED METRICS
### Metric A — independent-call fraction f_indep(mix)
For a corpus of agent STEPS (each step = a set of tool calls the agent would issue), define for each
step the call-level dependency graph (DAG). A call B DEPENDS on a prior same-step call A iff:
  (D1 data dependency)  B's arguments reference A's result (a value produced by A), OR
  (D2 ordering/side-effect dependency) B must observe A's side effect (A writes, B reads/writes same
      resource; A must commit before B is meaningful).
A call with NO dependency on ANY prior same-step call is PARALLELIZABLE (independent).
  f_indep = (# independent calls) / (# total calls), reported per-step and corpus-aggregate, per mix.
We ALSO report the step-level "parallel width" k = number of independent calls dispatchable together.

### Metric B — correctness-safety under detection error
Genuinely independent calls (by construction) cannot change the answer when reordered/parallelized.
The REAL risk is a dependency DETECTOR that MIS-CLASSIFIES a dependent call as independent (a false
negative on a true edge), then dispatches it in parallel and consumes a stale/absent result → wrong
final answer. We model a detector with per-edge false-negative rate e (it misses a true dependency
edge with prob e) and per-non-edge false-positive rate p (it hallucinates a dependency — harmless to
correctness, only costs latency). For each step we compute:
  P(step corrupted) = P(detector misses >=1 true dependency edge that is load-bearing for the answer).
  f_wrong(e) = fraction of parallelized steps that would produce a wrong result at detection-error e.
Report f_wrong as a function of e over a realistic range (e in {0, 0.01, 0.05, 0.10, 0.20}).

### Metric C — latency headroom
If a step has total n calls of which a chain of depth d_crit are on the critical path and each tool
takes ~t_tool, then serial wall-clock = n * t_tool; ideal-parallel wall-clock = d_crit * t_tool
(critical-path length). Speedup S = n / d_crit. Report S and wall-clock saved as a function of
f_indep and parallel width k. Model t_tool variability (5 seeds, lognormal jitter) since real tools
have heterogeneous latency — report S under equal-latency AND heterogeneous-latency assumptions
(heterogeneous reduces ideal speedup because the slowest independent call gates the batch).

## CORPUS (constructed, archetype-based — HONESTLY parameterized)
Step archetypes (each a template that emits a realistic tool-call set with an explicit ground-truth DAG):
  AR1 FAN-OUT  : parallel multi-source retrieval/search (e.g. search 3 docs / query 4 APIs), then
                 (optionally) one aggregator call that DEPENDS on all of them. High independence.
  AR2 SEQUENTIAL: read-then-transform-then-write chain (each call consumes prior result). Low independence.
  AR3 MIXED    : a fan-out of k independent lookups feeding a dependent synthesis, plus 1-2 independent
                 side calls. Medium independence.
  AR4 SINGLE   : one tool call (trivially no intra-step parallelism). Independence undefined/100% of 1.
Each archetype's DAG is GROUND TRUTH (we know the true edges by construction), enabling Metric B
(detector error) to be measured honestly against truth. Mix is a free parameter; we sweep it.

## PRE-REGISTERED DECISION RULE
- HELD: at a DEFENSIBLE/realistic mix (we will state a "balanced realistic" mix AND report the full
  curve), corpus f_indep > 0.30 AND f_wrong at a plausible detector error (e<=0.05) is LOW
  (pre-registered "low" = f_wrong <= 0.05, i.e. <=5% of parallelized steps corrupted) → the claim's
  two parts both hold at that mix.
- PARTIAL: f_indep > 0.30 holds for SOME mixes but the result is strongly mix-dependent (flips below
  0.30 for plausible mixes), OR correctness-safety holds only at unrealistically low detector error.
- NEGATIVE (claim dies): f_indep <= ~0.30 across the plausible mix range (parallelism is rare in
  realistic compositions), OR parallel calls are NOT reliably order-independent / a realistic detector
  corrupts a non-trivial fraction of steps (f_wrong high at plausible e). EITHER part failing kills it.

## HONEST-NEGATIVE BRANCH (pre-committed, report whichever is true)
(N1) If independent-call fraction is <~30% across realistic mixes → NEGATIVE (premise A fails).
(N2) If a realistic dependency detector (e~0.05–0.10) corrupts a meaningful fraction of steps
     (f_wrong well above 5%) → NEGATIVE on the correctness-safety part (premise B fails): the "free
     latency win" is NOT free, it trades latency for wrong answers.
(N3) If the result is ENTIRELY an artifact of the assumed mix (no defensible mix gives >30%) →
     report it as mix-conditional, not a population claim (PARTIAL at best).
(N4) If LLMCompiler / parallel-function-calling fully subsumes BOTH the parallelism measurement AND a
     correctness-safety bound → novelty caveat / PARTIAL.

## METHOD
1. Build archetype templates with ground-truth DAGs (stdlib only).
2. Implement an independence analyzer: given a step's calls + their arg/result references + resource
   read/write sets, build the dependency graph via D1 (data) + D2 (side-effect) and compute f_indep,
   per-step k, critical-path depth d_crit.
3. Sweep workload mix over a grid; for each mix, sample N steps (>=5 seeds), aggregate f_indep curve.
4. Correctness-safety: for each step apply a stochastic detector at error e in {0,.01,.05,.10,.20},
   over 5+ seeds; a step is "corrupted" iff the detector parallelizes two calls with a true
   load-bearing dependency edge between them. Report f_wrong(e).
5. Latency headroom: compute S = n/d_crit per step; aggregate by mix; equal-latency AND
   heterogeneous-latency (lognormal, 5 seeds) variants.
6. RESULTS.md: f_indep vs mix; f_wrong vs detector error; latency headroom; honest held/partial/negative.
7. <=15 min compute, SERIAL. Then ros exp complete. Commit.

## SEEDS
>=5 seeds wherever stochastic (mix sampling, detector error, latency jitter). Seeds 0..N fixed & logged.
