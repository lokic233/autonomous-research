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
