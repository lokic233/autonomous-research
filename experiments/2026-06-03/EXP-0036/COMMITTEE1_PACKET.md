# COMMITTEE#1 — CLAIM-0039 (PROJ-0010), evidence EXP-0036 (L0)
## SYSTEMS/throughput study, effect=kill / NEGATIVE. Designed to dodge all 3 anti-patterns (not tuned-knob, not KV-reuse, not predictor-vs-logprob) AS A STRUCTURAL-OCCUPANCY claim. It died on the pre-baked REAL-CONTINUOUS-BATCHING baseline. Vote honestly. Methodology integrity: the researcher CAUGHT+FIXED a policy-dependent-RNG bug (v1 gave spurious wins; v2 replays byte-identical arrival tapes across policies, verified CB==stepaware when M<B).

## L0 FINDINGS:
(A) residual_idle = (ready-work ceiling - CB decode-util) = 0.000000 across ALL 288 configs. Vanilla continuous batching (Orca/vLLM-style, work-conserving) hits the ready-work ceiling EXACTLY everywhere — nothing to reclaim. The idle that exists is STRUCTURAL (agents simultaneously off-GPU in tool-wait -> #ready-bursts < B); no scheduler can decode work that isn't ready. The claim's CENTRAL HYPOTHESIS is REFUTED: correlation does NOT create unfillable aligned bubbles CB misses — ceiling RISES with rho (0.472->0.483->0.489) because a correlated cohort returns ready work together. CB strictly dominates the serial strawman (median 1.50x, max 7.99x).
(B) step-aware vs REAL CB at matched p99 (paired bootstrap): median 0.00%, mean +0.32%, max +3.31%; TRUE wins (tput CI>0 AND p99 not worse) = 7/288 all trivial (<1%, NOT concentrated at high rho -> refutes the correlated-bubble win region); 66/288 'gain' only by SACRIFICING p99 (median 2.06x worse); 0/288 beat CB non-trivially at matched p99.
=> No win region. CB is already work-conserving; step-awareness can't manufacture work that doesn't exist, and reordering under contention only trades tail latency. Joins the dead scheduling claims CLAIM-0004/0006/0012 — continuous batching is the strong incumbent that captures the cross-request/cross-agent bubble.

## L0 LIMITATION (the researcher's honest L1 pointer): occupancy model = 1 token/slot/step, fixed B, NO KV pressure, NO prefill. Any residual that exists is likely KV-BOUND not slot-bound — a real L1 would test KV-cache admission under correlated bursts on real vLLM/SGLang. But the slot-occupancy claim as stated is dead.

## CLAIM
claim: "In multi-agent LLM serving where agents alternate short decode bursts with\
  \ long external tool-waits, the GPU 'step bubbles' (idle during an agent's tool-wait)\
  \ represent a MEASURABLE aggregate-throughput loss that vanilla continuous batching\
  \ does NOT fully recover (because tool-waits are long + bursty + correlated, leaving\
  \ residual idle), AND an agent-step-aware admission/interleaving policy reclaims\
  \ a non-trivial fraction of that residual idle at matched per-agent latency \u2014\
  \ beating REAL continuous batching (vLLM-style), not a serial strawman."
why_it_matters: "FRESH axis (cross-agent step-bubble throughput \u2014 untouched by\

## L0 RESULTS (EXP-0036)
# RESULTS — EXP-0036 / CLAIM-0039 (researcher-0036, L0, CPU-only, serial)

**VERDICT: NEGATIVE.** Vanilla continuous batching already captures it. The agent step-bubble does NOT
leave residual *fillable* GPU decode-idle beyond what continuous batching recovers, and an agent-step-aware
interleaving/admission policy does NOT beat continuous batching on throughput at matched per-agent p99.

This is the honest, pre-registered negative branch — and per the pipeline it is a WIN (it kills a claim
that was the obvious-thing-already-done).

## What was run
Discrete-time queueing/occupancy sim (stdlib-only, serial). M agents alternate short decode bursts
(~D tokens, exp-distributed) with long external tool-waits (~W steps; exponential OR heavy-tailed
lognormal; fraction rho of waits drawn from a SHARED cohort pool to make waits CORRELATED/aligned).
GPU = B decode slots, 1 token/slot/step. Three policies on the SAME pre-sampled arrival tape per seed
(fully PAIRED): (a) per-agent serial floor, (b) **real continuous batching** (Orca/vLLM-style: every step
greedily fill free slots with any ready burst, FCFS), (c) **agent-step-aware** (SJF on remaining burst to
maximize burst turnover under contention). Ready-work ceiling = E[min(#ready,B)]/B = max achievable util
given the arrivals (you cannot decode work that isn't ready).

Sweep: M∈{4,8,16,32}, B∈{2,4,8}, D∈{8,32}, W∈{50,200}, wait_dist∈{exp,lognormal-heavytail},
rho∈{0.0,0.5,0.9}, 5 seeds, horizon=4000 steps. **288 configs × 5 seeds × 3 policies = 4320 runs.**
Bootstrap 95% CI (2000 resamples) on the paired (c)−(b) throughput delta per config.

### Methodological fix (recorded for integrity)
v1 hashed the policy name into the RNG seed AND drew tool-waits mid-run, so each policy saw a *different*
arrival stream — producing spurious throughput "wins" (e.g. +0.46 tok/step at M=4,B=8 where no contention
can even exist). v2 PRE-SAMPLES each agent's full (burst, wait, cohort) tape from a policy-independent seed;
all three policies replay the identical tape. Verified: with M<B (no contention) CB and step-aware are now
**byte-identical** (tput 1.1205 == 1.1205), as they must be. All numbers below are from the corrected v2
on-disk CSVs (`results/policy_compare.csv`, `results/raw_runs.csv`).

## (A) Residual idle under continuous batching — vs serial floor + achievable ceiling
- **residual_idle = ready-work-ceiling − cb_util = 0.000000 across ALL 288 configs** (max 0.0, mean 0.0).
  Continuous batching is provably work-conserving: its decode-utilization **equals the ready-work ceiling
  everywhere**. There is **zero fillable idle** for any policy to reclaim.
- The idle that exists is **STRUCTURAL**: steps where #ready-bursts < B because agents are simultaneously
  off-GPU in tool-wait. Mean ceiling across configs = 0.481; 158/288 configs are work-*starved* (ceiling<0.50),
  43/288 are slot-saturated (ceiling≥0.98). No scheduler can decode work that isn't ready that step.
- **Correlation does NOT create unfillable aligned bubbles that CB misses** — the opposite of the claim's
  hypothesis. Mean ready-work ceiling *rises* slightly with rho: 0.472 (rho=0) → 0.483 (0.5) → 0.489 (0.9).
  Correlated cohort returns *bunch* ready work together (more slots filled when the cohort is active),
  rather than leaving a bubble CB can't fill.
- Sanity: CB strictly dominates the serial floor (cb_tput/serial_tput median 1.50×, max 7.99×) — confirming
  the serial strawman is indeed a floor and CB is the real bar.

## (B) Agent-step-aware (c) vs continuous batching (b) at matched p99 — PAIRED, bootstrap CI
- **(c)−(b) throughput delta across all 288 configs: median = 0.00%, mean +0.32%, max +3.31%.**
- **TRUE WINS (tput CI>0 AND p99 not worse): 7/288**, all trivial — largest +0.010 tok/step (~0.9% median,
  3.3% max), all within noise of CB. The 7 wins do NOT concentrate at high correlation (1/3/3 across
  rho=0.0/0.5/0.9), refuting the "correlated-bubble win region" hypothesis.
- **66/288 configs gain throughput ONLY by sacrificing latency** (SJF starves long bursts):
  stepaware p99 / CB p99 median **2.06×**, up to 3.5× worse. This is exactly the pre-registered
  latency-sacrifice failure → NEGATIVE.
- **215/288: no significant throughput difference** (CI spans 0). **0/288: stepaware never beats CB by a
  non-trivial margin at matched p99.** Step-aware never *loses* throughput, but it essentially equals CB
  and only ever "gains" by trading away tail latency.

## Why (the load-bearing mechanism)
Continuous batching is already greedy work-conserving — it never idles a slot when a ready burst exists.
The only residual idle is structural (not enough ready work), and step-awareness cannot manufacture work
that doesn't exist. Under contention (#ready>B), reordering (SJF) can shave a hair of throughput but only
by pushing long bursts to the tail → worse p99. There is no regime where the agent step-bubble structure
yields fillable idle that continuous batching leaves on the table.

## Verdict against the three pre-screened failure modes
- Not a Jensen-floor tuned-knob: no knob was tuned to match; (b)/(c) face identical arrivals. ✓
- Not a RoPE-wall KV-reuse play: pure occupancy/throughput, no KV. ✓
- Not a predictor-vs-own-logprob relabeling: systems throughput metric only. ✓
It is a clean systems/throughput-occupancy negative.

## What a real L1 should measure (if anyone revisits)
- Real **vLLM/SGLang continuous batching** (PagedAttention, chunked prefill, real iteration-level scheduling)
  under real multi-agent traces, not a slot model.
- **Real agent traces with real tool-wait distributions** (web/code/RAG tool latencies, actual correlation
  from shared backends) — measure whether real tool-wait correlation ever drops GPU SM utilization below the
  ready-work ceiling in a way iteration-level scheduling misses.
- **Real GPU decode utilization** (nsys/DCGM SM-occupancy), prefill/decode interference, and KV-cache
  pressure (admission may be KV-bound, not slot-bound — a different bottleneck this L0 abstracts away).
- The L0 abstraction (1 token/slot/step, no prefill, no KV pressure, B fixed) is exactly where a residual
  *could* hide; L1 should test if KV-cache admission under correlated bursts is the real (different) story.

## Prior-art caveat
Continuous batching (Orca, OSDI'22; vLLM/PagedAttention, SOSP'23) is the obvious incumbent and it provably
fills cross-request bubbles — this experiment confirms it captures essentially all of the agent step-bubble.
This instance has already killed scheduling claims CLAIM-0004/0006/0012; CLAIM-0039 joins them. The intended
novelty was "agent-step-bubble residual BEYOND continuous batching," and the honest finding is that there is
no such residual in the occupancy regime — the bubbles are either already filled or structurally unfillable
by any policy. Continuous batching is the obvious thing and it already captures it.

## Artifacts
- PRE_REGISTRATION.md (committed before any run)
- sim.py (v2, paired arrivals)
- results/policy_compare.csv (288 configs), results/raw_runs.csv (4320 runs)
- logs/sim_run_v2.log

## PRE-REG
# PRE_REGISTRATION — EXP-0036 / CLAIM-0039 (researcher-0036, L0)

Committed BEFORE running any sim. CPU-only, stdlib-only, SERIAL (multiprocessing BLOCKED on this Mac).
Trust on-disk CSVs not stdout. Honest pipeline: a NEGATIVE (continuous batching already captures it) is a WIN.

## THE CLAIM (CLAIM-0039)
In multi-agent LLM serving where agents alternate short decode bursts with long external tool-waits,
the GPU "step bubbles" (idle during an agent's tool-wait) are a MEASURABLE aggregate-throughput loss
that vanilla CONTINUOUS BATCHING does NOT fully recover (tool-waits long+bursty+correlated -> residual idle),
AND an agent-step-aware interleaving/admission policy reclaims a non-trivial fraction of that residual idle
at matched per-agent latency — beating REAL continuous batching (vLLM-style), NOT a serial strawman.

## THE LOAD-BEARING KILL (pre-baked as the control)
VANILLA CONTINUOUS BATCHING (Orca/vLLM): when one request is idle/waiting, the scheduler ALREADY runs
OTHER requests' decode on the GPU. So it already fills bubbles ACROSS requests. The real question:
is there ANY RESIDUAL idle specific to the agent step-bubble structure that continuous batching does NOT
already capture? If continuous batching captures it all -> NEGATIVE (the honest, likely outcome).

## TWO FALSIFIABLE PARTS
(A) Under realistic bursty/correlated multi-agent tool-wait arrivals, is there RESIDUAL GPU decode-idle
    that continuous batching leaves unfilled (vs an achievable ceiling)?
(B) Does an agent-step-aware interleaving/admission policy reclaim a NON-TRIVIAL fraction of that residual
    at MATCHED per-agent p99 latency, beating continuous batching?

## MODEL (queueing/occupancy sim, discrete-time steps; NO GPU/model)
- M concurrent agents. Each agent = infinite sequence of phases:
  * DECODE BURST: ~D tokens (D ~ geometric/lognormal, short, e.g. mean 8-32 tokens).
    Each token = 1 GPU decode step IF the agent holds a decode slot that step.
  * TOOL-WAIT: ~W steps external (agent off-GPU, frees its slot). W distribution:
      - exponential (light), OR
