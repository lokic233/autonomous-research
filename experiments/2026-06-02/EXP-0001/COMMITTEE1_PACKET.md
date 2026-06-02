# COMMITTEE#1 REVIEW PACKET — CLAIM-0001 (PROJ-0001), evidence EXP-0001 (L0)

## PASS: This is committee#1 (post-L0, pre-GPU). Two-pass model: L0 -> committee#1 -> (approve a GPU exp for required_evidence) -> GPU -> committee#2 -> verdict.
If you would approve advancing, state the SPECIFIC required_evidence a GPU validation pass must produce. An honest YELLOW with concrete required_evidence is a valid outcome. A negative/conditional result is a legitimate candidate — do NOT inflate to green to make progress, and do NOT rubber-stamp.

## THE CLAIM (as seeded)
claim: In multi-turn agentic LLM serving, a tool-boundary-aware KV/prefix-cache retention
  heuristic (pin system + tool-schema prefixes, evict per-turn scratch first) yields
  a strictly higher prefix-cache hit rate and fewer recomputed prompt tokens than
  structure-blind LRU on realistic agent traces, because agentic traffic has a bimodal,
  structurally-predictable reuse pattern that LRU cannot exploit.
why_it_matters: "Agentic workloads (tool-calling loops) dominate emerging LLM serving\

## CLAIM STATUS AFTER L0: weakened (researcher ran exp complete --effect weaken). The universal phrasing was falsified; a conditional (starvation-only) effect survives.

## L0 EVIDENCE — EXP-0001 RESULTS
# RESULTS — EXP-0001 (L0, CPU-only prefix-cache eviction simulation)

- **Claim tested:** CLAIM-0001 (tool-boundary-aware retention beats structure-blind LRU)
- **Level:** L0, CPU-only, stdlib-only, trace-driven block/prefix-cache simulation.
- **Seeds:** 11, 23, 47 (mean ± population std). **Block size:** 16 tokens.
- **Trace params (frozen):** 40 sessions × 8 turns, hot prefix 2048 tok, scratch 256 tok/turn,
  shared_prefix_frac=0.75. 320 requests/seed, 1376 distinct hot blocks/seed.
- **Pre-registration:** see `PRE_REGISTRATION.md` (committed before the run).

## Headline table (mean over 3 seeds; capacity = fraction × distinct-hot-block working set)

| cap_frac | capacity | LRU hit rate | TBA hit rate | Δhit (TBA−LRU) | LRU recomp toks | TBA recomp toks | Δrecomp | verdict |
|---------:|---------:|-------------:|-------------:|---------------:|----------------:|----------------:|--------:|:-------:|
| 0.25 | 344  | 0.5045 ±.0032 | 0.5116 ±.0018 | **+0.0071** | 507,392 | 500,139 | **−7,253**  | **TBA wins** |
| 0.50 | 688  | 0.5556 ±.0036 | 0.5570 ±.0031 | +0.0014 | 455,083 | 453,632 | −1,451  | TBA wins (marginal) |
| 0.75 | 1032 | 0.5958 ±.0094 | 0.5957 ±.0020 | −0.0001 | 413,952 | 414,037 | +85     | tie |
| 1.00 | 1376 | 0.6412 ±.0063 | 0.6271 ±.0022 | −0.0142 | 367,360 | 381,867 | +14,507 | **TBA loses** |
| 1.50 | 2064 | 0.7272 ±.0037 | 0.7099 ±.0078 | −0.0173 | 279,381 | 297,045 | +17,664 | **TBA loses** |

## Verdict: PARTIAL → mostly NEGATIVE for the claim as stated

The claim is **only true in the severely cache-starved regime** (capacity ≤ ~50% of the hot
working set), where TBA's prefix-pinning buys a small, real edge:
- At **cap_frac=0.25**: TBA +0.71 pp hit rate (0.5116 vs 0.5045; non-overlapping at 1σ) and
  −7,253 recomputed tokens (−1.4% recompute). A genuine, reproducible win.
- At **cap_frac=0.50**: marginal win (+0.14 pp), within noise.

But the claim's universal phrasing ("strictly higher hit rate and FEWER recomputed tokens than
LRU") is **FALSEFIED at matched budget for the ample-cache regime**:
- At **cap_frac ≥ 1.0** TBA is **strictly worse**: −1.4 pp to −1.7 pp hit rate and **+14.5k–17.7k
  MORE recomputed tokens** than plain LRU. The losses exceed 1σ and are stable across seeds.

## Why (mechanism — this is the honest, interesting part)
The claim assumes per-turn scratch is "cold / rarely reused." In a realistic **conversational**
agent trace it is **not**: each turn's scratch (USER + TOOL-RESULT + ASSISTANT) is appended to the
running context and is therefore **reused by all later turns of the same session**. So scratch has
real, recent temporal locality. LRU captures that locality automatically. TBA's rule "evict scratch
first" **throws away recently-used, soon-to-be-reused conversation blocks** to protect hot prefix
blocks that LRU would have kept anyway once capacity is adequate. Under cache pressure (cap ≤ 0.5)
protecting the cross-session shared prefix dominates and TBA wins; with headroom, the blind
2-class priority actively destroys recoverable cold-block locality and loses.

**Takeaway:** a *structure-aware* policy helps, but a naive "pin hot / evict scratch first" 2-class
heuristic is too blunt. The right policy must respect that intra-session scratch is reused — i.e.
TBA needs to distinguish *committed conversation scratch* (reused) from *truly transient* scratch,
or fall back to LRU within a protected hot floor. The claim's bimodal-reuse premise is too coarse.

## Artifacts
- Simulator: `sim.py`
- Raw per-(policy×capacity×seed) rows: `results/results.csv`
- Aggregates: `results/summary.json`
- Run log: `logs/run.log`, console: `logs/stdout.log`

## Reproduce
```
/usr/bin/python3 sim.py   # ~10s, CPU-only, stdlib-only, seeds {11,23,47}
```

## PRE-REGISTRATION (committed pre-run)
# PRE_REGISTRATION — EXP-0001 (L0, CPU-only, trace-driven cache simulation)

- **Claim:** CLAIM-0001
- **Experiment:** EXP-0001  | **Task:** TASK-0001 | **Project:** PROJ-0001
- **Level:** L0 (CPU-only, ≤15 min wall-clock, no GPU, no model inference, no network)
- **Pre-registered:** 2026-06-02, committed to git BEFORE any run.

## Hypothesis (CLAIM-0001)
In multi-turn agentic LLM serving, a tool-boundary-aware KV/prefix-cache retention heuristic
(pin SYSTEM + TOOL-SCHEMA prefix blocks, evict per-turn scratch first) yields a **strictly higher
prefix-cache hit rate** and **FEWER recomputed prompt tokens** than a structure-blind LRU policy on
realistic agent traces — because agentic traffic has a bimodal, structurally-predictable reuse
pattern (hot shared prefix + cold per-turn scratch) that LRU cannot exploit under cache pressure.

## What "prefix cache" means here (block/radix model)
We model a vLLM-style **block-level prefix cache**:
- Tokens are grouped into fixed-size **blocks** (default block_size = 16 tokens).
- A request's prompt is a sequence of blocks. A block is cacheable/sharable keyed by the **hash of
  its content chained with the hash of its prefix** (radix/prefix-hash chaining), so a block only
  hits if ALL preceding blocks in that request also matched (true prefix semantics).
- The cache holds at most `capacity_blocks` blocks. On insert past capacity, the eviction policy
  chooses victims.
- A prompt block is a **hit** if it is resident AND its full prefix chain is resident (prefix
  property). On a miss, the block (and everything after it in that prompt) must be **recomputed**.

## Metrics (frozen before running)
- **PRIMARY — prefix-cache hit rate** = (prompt tokens served from cache) / (total prompt tokens
  across all requests). Tokens in a block count as hits only when the block hits under prefix
  semantics.
- **SECONDARY — total recomputed prompt tokens** = total prompt tokens − cached prompt tokens
  (i.e. tokens that had to be recomputed). Lower is better.
- **TERTIARY — eviction count** = number of block evictions performed by the policy.

## Trace model (synthetic, stdlib-only, seeded)
Multi-turn tool-calling sessions interleaved to create real cache pressure:
- `n_sessions` concurrent sessions. Each session has `turns_per_session` turns.
- Each session owns a long shared **HOT prefix** = SYSTEM preamble + TOOL-SCHEMA. This prefix is
  reused across **all turns of that session** AND is **structurally similar across sessions**: a
  large common boilerplate sub-prefix (shared SYSTEM + shared tool-schema skeleton) is identical
  across sessions, followed by a small session-specific tail. This makes cross-session prefix reuse
  realistic (same agent app, same tools).
- Each turn appends a **COLD scratch** segment = USER message + TOOL-RESULT + ASSISTANT reply.
  Scratch is unique per turn (rarely reused). A turn's prompt = HOT prefix ⊕ (accumulated prior
  turns' scratch, conversational) ⊕ this turn's user — i.e. growing conversation. To keep the hot
  prefix the dominant *shared* structure while scratch grows, we model the cacheable reusable unit
  as: shared-prefix blocks (hot, cross-turn + cross-session) + per-turn scratch blocks (cold).
- Turns from different sessions are **interleaved** in arrival order (round-robin-ish with seeded
  jitter) so the cache sees mixed pressure, not one session at a time.
- **Parameters:** block_size=16, prefix_len (hot tokens), scratch_len (cold tokens/turn),
  shared_prefix_frac (fraction of hot prefix identical across sessions).
- **Seeds:** ≥3 fixed RNG seeds; report mean ± std.

## Two policies compared (identical cache CAPACITY)
- **(a) LRU baseline:** structure-blind. On eviction, evict least-recently-used block regardless of
  class.
- **(b) Tool-boundary-aware (TBA):** 2-class priority + LRU within class. Class HOT = blocks
  belonging to SYSTEM + TOOL-SCHEMA prefixes (pinned/prioritized for retention). Class COLD =
  per-turn scratch blocks. On eviction: **evict COLD (LRU within COLD) first**; only touch HOT
  blocks (LRU within HOT) when no COLD blocks remain. Capacity is matched EXACTLY to LRU.

## Cache budget sweep (frozen)
Capacity expressed as a fraction of the total HOT-prefix working-set (distinct hot blocks across all
sessions). Sweep points: **{0.25, 0.50, 0.75, 1.0, 1.5}** × distinct-hot-blocks (rounded). This
spans "can't hold the hot set" → "holds hot set + headroom for scratch."

## Decision rule + HONEST-NEGATIVE branch
- **WIN (claim holds):** TBA has strictly higher hit rate AND strictly fewer recomputed tokens than
  LRU (mean over seeds, non-overlapping at ≥1σ ideally) at one or more matched capacities.
- **PARTIAL:** TBA wins in some capacity regime(s) and ties/loses in others — report exactly which.
- **NEGATIVE (reported honestly, counts as a valid result):** if TBA does NOT strictly beat LRU on
  hit rate at matched capacity anywhere, we REPORT THE NEGATIVE. No metric redefinition, no
  cherry-picking seeds, no capacity p-hacking after the fact. The sweep grid above is frozen.

## Outputs
- `sim.py` (generator + both policies + sweep) in EXP dir.
- `results/results.csv` — one row per (policy × capacity × seed) with all three metrics.
- `RESULTS.md` — table (mean±std) + honest verdict.

## ORCHESTRATOR NOTES FOR THE COMMITTEE
- L0 ran with NO network egress -> NO live prior-art sweep was done. novelty_killer: a live >=2-source prior-art sweep vs vLLM/SGLang RadixAttention prefix-cache eviction, prompt-cache retention, and recent agent-KV-cache eviction work is OWED. If egress is blocked at your end, cast an honest YELLOW with a scoping fix (do NOT fabricate a green or a clean novelty claim).
- L0 is a trace-driven SIM with content-addressed proxy tokens, not real inference. A GPU pass (real vLLM enable_prefix_caching on devgpu014/H100 — NOT the fragile MI350X) is the natural committee#1 ask if the claim is candidate-grade.
- The interesting honest finding is the MECHANISM + CROSSOVER (TBA helps only when cache < shared-prefix working set; the naive 2-class rule backfires with headroom because conversational scratch has real temporal locality).
