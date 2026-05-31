# EXP-0019 — Harness ROUTING-TABLE characterization: is recovery a low-entropy fallback table or adaptive? (laneB, under CLAIM-0009)

**Domain:** MAP-0002 (Agent failure attribution & recovery). **CPU-only, stdlib-only, ~20s.**
**Lane:** laneB positive-characterization of the CONFOUND (distinct from laneA terminal-pole work and from the
retired error-class claims). **Claim registered against:** CLAIM-0009 (level 1).

## Why this experiment (the gap it fills)
EXP-0012/VERDICT-0021 confirmed the CONFOUND: recovery MODALITY is determined by the harness's gate-type
(REDIRECTABLE/TERMINAL/TRANSIENT routing flag), NOT by error-class — they are observationally inseparable in
this single Claude Code corpus, and a single REDIRECTABLE bit matches the full 17-class taxonomy out-of-sample.
The map records this as a red_zone ("harness-routing-as-confound, CONFIRMED").

This experiment turns that confound into a POSITIVE, falsifiable measurement of the harness's **de-facto
ROUTING TABLE itself**, testing an honest thesis nobody had measured:

> **THESIS:** "Agentic recovery competence is largely a property of the harness's fallback ROUTING TABLE
> (low-entropy / near-deterministic next-tool per error-class), not adaptive LLM reasoning."
> - **SUPPORT** if the per-class next-tool distribution is LOW-entropy / near-deterministic.
> - **REFUTE** if it is HIGH-entropy / diffuse (next tool chosen adaptively, not routed).

Either outcome is valuable: SUPPORT gives a new "recovery = fixed routing table" characterization; REFUTE
rehabilitates an adaptive-recovery story. This is NOT another attempt to separate error-class from gate-type
(that is settled/dead, EXP-0012) — it is a direct entropy census of the agent's empirical fallback move.

## Data (REAL, same corpus, recursive glob)
`~/.claude/projects` Claude Code session logs. `parse_session/classify_error/intent_class/head_cmd/block_text`
**copied verbatim** from EXP-0009 (==EXP-0007/0008/0012). Recursive glob `**/*.jsonl` (includes subagent traces
= legitimate agent tool-use logs) to maximize n. After `tool_result`→`tool_use` join + <2-call drop:
**78 sessions, 3,544 tool calls, 373 ground-truth failures** — matches EXP-0012's refreshed corpus (76/3,530/369),
confirming we are measuring the SAME population the confound was confirmed on.

> NOTE on corpus volatility: the non-recursive `*/*.jsonl` glob (what earlier runs used) now returns only
> 53 sessions/114 failures — the live corpus has rotated; the recursive glob recovers the full 373-failure
> population including subagent logs and is the correct, comparable basis. Headline uses the recursive corpus.

## Method (one rigorous census)
For every ground-truth failure of class C at call position *i*, record the **immediate next tool invoked** in
the session = the empirical fallback. `routing_tool()` canonicalizes: tool name, with `Bash` collapsed to
`Bash:<head-command>` (so a true tool-switch like WebFetch→external_web_search is distinct from in-place Bash
reinvocation, but argument noise does not explode the support). Per class we compute:
1. **Routing table** P(next_tool | class C) — the de-facto fallback distribution.
2. **Shannon entropy** H (bits) and **normalized entropy** H/Hmax (0=one fixed route, 1=uniform/adaptive).
3. **Top-1 route share** (modal-route mass) — determinism in one number.
4. **Routing-explained recovery:** of recovered failures (EXP-0008 BROAD def, copied verbatim, K=6), what
   fraction took the class's MODAL route; and a **routing-only recovery predictor** (predict p = the class's
   modal-route recovery rate) scored by **honest leave-one-out Brier** vs the global-rate NULL.
5. **Entropy collapse** = global-normalized-entropy − failure-weighted per-class-normalized-entropy (n≥10
   classes). POSITIVE ⇒ knowing the class makes the next move more deterministic (routing-table). ≤0 ⇒ the
   class does not constrain the next move (adaptive). **2000-sample bootstrap 95% CI** on this statistic.

## Results

### Per-class de-facto routing table (n≥10 classes)
| class | n | norm-entropy | top1-route-share | recovery | modal route (share) | modal-route recovery |
|---|---|---|---|---|---|---|
| other | 113 | 0.703 | 0.451 | 0.593 | external_web_search (51/113) | 0.628 |
| **policy.web_disabled** | 109 | **0.738** | **0.404** | 0.606 | WebSearch (44/109) | **0.455** |
| cancelled | 59 | 0.749 | 0.373 | 0.576 | external_web_search (22/59) | 0.864 |
| policy.perm_denied | 30 | 0.720 | 0.533 | 0.467 | external_web_search (16/30) | 0.563 |
| fs.notfound | 20 | 0.852 | 0.350 | 0.800 | Bash:ls (7/20) | 0.857 |
| proc.exit_nodetail | 14 | 0.858 | 0.429 | 0.857 | external_web_search (6/14) | 0.833 |

(rare classes n≤6 reported in CSV; degenerate norm-entropy=0 only because n=1.)

### Headline statistics
- **Global next-tool norm-entropy = 0.714**; failure-weighted **per-class norm-entropy = 0.738**.
- **Entropy collapse = −0.024** (per-class entropy is *not even lower* than global). **Bootstrap 95% CI
  [−0.052, +0.009], P(collapse>0) = 0.073.** Knowing the error-class does NOT make the agent's next move
  more deterministic than the class-agnostic baseline.
- **Top-1 route share = 0.423** — even the most-common fallback per class is taken **less than half the time**.
- **Routing-only recovery predictor: LOO-Brier 0.2557 vs NULL 0.2357 — WORSE than null by −8.5%.** A fixed
  "modal route per class" predictor does NOT beat the constant global recovery rate out-of-sample.
- **Only 103/233 = 44.2% of recovered failures** went via their class's modal route — the majority recovered
  via a *different* tool than the class's most-common fallback.

### The decisive cell: policy.web_disabled is NOT a deterministic route
This is the cell that produced the "redirect = 1.000" modality signal in EXP-0009/0012. At **tool granularity**
it is diffuse: norm-entropy **0.738**, modal route (WebSearch) taken only **40%** of the time, and that modal
route recovers only **45%**. The agent DOES redirect off the blocked tool — but it chooses the *target*
adaptively among {WebSearch, external_web_search, knowledge_load, Bash:curl, …}. The "near-deterministic
routing" appearance in EXP-0009/0012 was an artifact of the coarse 2-level REDIRECTABLE/TERMINAL collapse;
at the actual tool-choice level there is no fixed route.

## VERDICT for the routing-table thesis: **REFUTE**
The harness does NOT have a low-entropy fallback routing table per error-class. Per-class next-tool entropy is
high (norm 0.74), statistically indistinguishable from (and if anything slightly above) the global next-tool
entropy (collapse CI [−0.052, +0.009], P(collapse>0)=7.3%); the modal route is taken <43% of the time; and a
routing-only recovery predictor is WORSE than the null out-of-sample (−8.5% Brier). **Recovery competence is
NOT explained by a fixed routing table — the next tool-choice after a failure looks ADAPTIVE, not routed.**

This REFUTES laneB's routing-table framing and, symmetrically, **rehabilitates an adaptive-recovery story**:
the *gate-type* (redirectable-vs-terminal) is a config fact (EXP-0012), but *which* sanctioned alternative the
agent picks within a gate is high-entropy and behaves like a decision, not a table lookup.

## Honest caveats (anti-overclaim)
- **Single harness** (Claude Code), observational. High entropy is consistent with adaptive reasoning AND with
  a stochastic-but-fixed policy; we cannot interventionally distinguish them on CPU. But low entropy is the
  OBSERVABLE SIGNATURE a routing-table predicts, and it is absent — so the routing-table thesis is refuted on
  its own observable, regardless of the deeper mechanism.
- **Next-tool = immediate next call**, not "the tool that achieved recovery." A diffuse immediate-next
  distribution could still hide a fixed eventual-recovery route. Mitigation: the routing-explained-recovery
  predictor (modal-route → recovery) and the 44% "recovered-via-modal-route" stat both target recovery
  directly and both fail to support routing. (A bounded-window most-frequent-recovery-tool variant is the
  natural next probe; not run, CPU-budget.)
- **Bash collapsed to Bash:<head>** is a choice; collapsing all Bash to one token would LOWER entropy (fewer
  symbols) and bias TOWARD support — i.e. the refute is conservative under the alternative grouping.
- Rare classes (n≤6) are not interpreted; headline uses only n≥10 classes.

## NEW-THESIS NOTE for the ORCHESTRATOR (I do not seed claims/map)
This is a genuinely new, defensible angle worth a seed by the orchestrator, *opposite in sign* to laneB's prior
expectation and complementary to laneA: **"Within a harness gate-type, recovery-tool selection is high-entropy /
adaptive, not table-routed."** Concretely: gate-TYPE is a deterministic config fact (EXP-0012), but the
*tool chosen within a redirectable gate* is high-entropy (norm 0.74, modal share 0.40) and a fixed-route
predictor underperforms the null. This separates the genuinely-determined layer (gate routing) from the
genuinely-adaptive layer (intra-gate tool selection) — a cleaner two-layer characterization than either the
retired error-class claim or a flat routing-table claim. Cross-harness + interventional (force a route, see if
recovery degrades) would be the GREEN path. Map-relevant: the MAP-0002 red_zone "harness-routing-as-confound"
should be annotated that the confound is at the COARSE gate-type layer only; the fine tool-selection layer is
adaptive (this experiment), so an adaptive-recovery claim is NOT dead at tool granularity.

## Files
- impl: `experiments/2026-05-31/EXP-0019/impl/routing_table_census.py`
- csv:  `experiments/2026-05-31/EXP-0019/experiment_result/routing_table.csv` (per-class entropy + modal route)
- csv:  `experiments/2026-05-31/EXP-0019/experiment_result/routing_distributions.csv` (full per-class P(next_tool))
- log:  `experiments/2026-05-31/EXP-0019/experiment_result/run_stdout.txt`
