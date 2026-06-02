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
