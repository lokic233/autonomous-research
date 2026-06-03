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
      - heavy-tailed lognormal/pareto (bursty), parameter `wait_dist`.
  * CORRELATION: prob rho that a finishing burst triggers a SHARED tool-wait — i.e. a fraction of agents
    that finish near-simultaneously all call the SAME slow tool and return at the SAME step
    (correlated bubble that could align idle across agents). Implemented as a shared "tool-return cohort":
    with prob rho an agent joins the current cohort and its W is the cohort's shared (long) wait;
    else independent W. Sweep rho in {0.0, 0.5, 0.9}.
- GPU: B decode slots. Per step, up to B agents that are in DECODE phase AND admitted each emit 1 token
  (fixed per-slot decode throughput = 1 token/slot/step). GPU decode-utilization at a step = (#busy slots)/B.
- Aggregate throughput = total tokens decoded / total steps. (work is conserved across policies — same total
  tokens to emit per agent over the horizon — so throughput differences = makespan/idle differences.)
- Per-agent latency metric: per-burst COMPLETION latency = (#steps from burst becoming ready to its last token
  emitted). p99 over all bursts across all agents. This is the matched-latency constraint.

## THREE POLICIES
(a) PER-AGENT SERIAL (STRAWMAN / reference floor ONLY): at most 1 agent on GPU at a time; an agent holds the
    GPU through its entire burst, then yields; next ready agent runs. No cross-agent overlap. NOT the comparison.
(b) REAL CONTINUOUS BATCHING (Orca/vLLM-style, the HONEST strong baseline): every step, fill free slots
    immediately with ANY agent currently in DECODE phase and ready (FCFS by ready-time among waiting bursts).
    A slot is freed the step an agent enters tool-wait. Greedy work-conserving — never leaves a slot idle if a
    ready burst exists. THIS is the bar to beat.
(c) AGENT-STEP-AWARE interleaving/admission: same slot-filling, BUT uses knowledge of agent step structure /
    anticipated tool-wait to PACK bursts: (i) admission prioritizes agents whose burst is SHORT / will free the
    slot soon (SJF-ish on remaining burst) to increase burst turnover; (ii) anticipatory admission — when a
    correlated cohort is KNOWN to be about to return (tool-wait expiry predictable), the scheduler holds/reserves
    nothing extra (no slots to add — B fixed) but reorders ready queue to avoid head-of-line blocking by long
    bursts so that when the cohort returns, slots are maximally available. Crucially (c) has the SAME B and SAME
    total work as (b); it only differs in WHICH ready burst fills a free slot and ordering. If B>=#ready always,
    (c) === (b) (no decision to make) -> residual win only possible when #ready transiently EXCEEDS B (contention)
    AND idle exists elsewhere — the regime to find.

NOTE on the crux: continuous batching (b) is already work-conserving — it NEVER idles a slot if a ready burst
exists. Therefore the ONLY residual idle (b) can leave is STRUCTURAL: steps where #ready-bursts < B (not enough
ready work), which happens exactly under CORRELATED waits (all agents off-GPU together). (c) cannot create work
that doesn't exist, so (c) CANNOT fill structural idle either. The honest hypothesis: (c) can only beat (b) on
LATENCY-at-matched-throughput or THROUGHPUT-at-matched-latency via better ORDERING under contention (#ready>B),
NOT by filling correlated structural bubbles. We measure both and report honestly.

## METRICS (all from on-disk CSV)
- gpu_decode_utilization = mean busy-slots/B over horizon (per policy)
- aggregate_throughput = total_tokens / total_steps
- achievable_ceiling = utilization/throughput of a hypothetical CLAIRVOYANT work-conserving scheduler with the
  SAME arrival process (== (b) actually, since (b) is already greedy work-conserving; ceiling for util is
  min(1.0, mean_ready/B) — i.e. you cannot exceed available ready work). We compute the "ready-work ceiling"
  = E[min(#ready, B)]/B per step = the max achievable util given arrivals. residual_idle = ceiling - util(b).
- per_burst_p99_latency (per policy)
- For (c) vs (b): throughput delta AND latency delta. Bootstrap 95% CI over seeds.

## MATCHED-LATENCY PROTOCOL
We do NOT tune knobs to match (Jensen-floor failure-mode #1 avoided). Instead: (b) and (c) face the SAME arrival
stream per seed. We report (c)-vs-(b) throughput delta AND p99 delta jointly. The claim (B) holds ONLY if
(c) throughput > (b) throughput with CI excluding 0 AND (c) p99 <= (b) p99 (no latency sacrifice). If (c) gains
throughput only by RAISING p99, that's a latency sacrifice -> NEGATIVE.

## SWEEPS
- M (agents): {4, 8, 16, 32}
- B (slots): {2, 4, 8}
- D mean burst tokens: {8, 32}
- wait_dist: {exponential, lognormal-heavytail}
- W mean (steps): {50, 200}  (long tool-waits relative to bursts)
- rho (correlation): {0.0, 0.5, 0.9}
- seeds: 5 (>=5 required)
- horizon: enough steps for >= ~200 bursts/agent to converge p99; cap for <=15min serial.
  Use horizon = 4000 steps; subsample sweep grid to stay in budget.

## HONEST-NEGATIVE BRANCH (pre-committed)
Report the NEGATIVE ("continuous batching already captures it") if ANY of:
1. vanilla continuous batching (b) already drives GPU util near the ready-work ceiling (residual_idle small,
   e.g. < few %) across realistic M -> the bubbles are filled or are structural-unfillable.
2. (c) does NOT beat (b) on throughput at matched p99 (CI includes 0 or p99 worse).
3. the only (c) win requires sacrificing per-agent p99 latency.
Expectation per the theory note above: (b) is work-conserving so residual idle is STRUCTURAL (correlated
all-off-GPU steps) which NEITHER (b) NOR (c) can fill -> likely NEGATIVE. The win region, if any, is narrow:
high contention (#ready>B, i.e. low B / high M) where ORDERING under load lets (c) shave p99 at equal throughput.

## DELIVERABLES
- this PRE_REGISTRATION.md (committed first)
- sim.py (stdlib only, serial)
- results/*.csv (raw per-seed per-config)
- RESULTS.md (analysis + held/partial/negative verdict)
