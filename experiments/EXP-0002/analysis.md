# EXP-0002 — CDC repair cost-surface (Lane B, robustness)  [prompt_version v001]

**Claim:** CLAIM-0006 — "CDC repair achieves ~2% recompute vs full."
**Agent:** researcher-cdc-robustness-B  •  **Level:** 0  •  **Hardware:** CPU-only (Mac, /usr/bin/python3). NO GPU/torch/CUDA touched (postmortem honored).
**Method:** token-proxy recompute-fraction = (# content-defined chunks in contaminated seq whose blake2b hash is NOT in the base-seq chunk-hash set) / (# chunks). Identical CDC reuse model to the original `nt2_cdc` microbench (rolling-hash boundary, mask=0xF, target ~16 tok, cap 2x, set-membership reuse). 3 reps/cell, 100 cells.
**Caveat:** this is a token-count proxy, NOT GPU wall-clock. The original "~2%" was also a chunk-count fraction from a single microbench (CTX=4000, inj=40 tok). GPU wall-clock anchor would need orchestrator dispatch.

## Reproduction of the original anchor
Original `nt2_cdc` (CTX=4000, inj=40, 5 inject_fracs) reproduced exactly: CDC recompute = **2.0–2.4%** across position. ✔ The ~2% is real — but ONLY at that operating point.

## Cost surface (100 cells: seq_len × inject_tokens × edit_pos)
Global recompute%: **min 0.02% / median 1.34% / max 53.05%**. The surface is NOT flat at 2%.

### Finding 1 — Recompute% is governed by **injection_tokens / sequence_length**, NOT by edit position.
| inj/seq ratio | mean recompute% |
|---|---|
| 0.0001 (1/16k) | 0.11% |
| 0.01  (40/4k)  | 2.20%  ← the anchor regime |
| 0.05  (200/4k) | 5.34% |
| 0.25  (1000/4k)| 20.47% |
| 1.00  (1000/1k)| 50.72% |

Recompute% ≈ inj/seq ratio (slope ~1.0 in the 1–6% band). The 2% bar is a thin contour at **inj/seq ≈ 1%**, not a property of the method.

### Finding 2 — Edit position barely matters (contradicts the intuitive "earlier edit = worse" worry).
At fixed (seq, inj), median spread across edit_pos ∈ {prepend 0.0 … terminal 1.0} = **0.39 pp** (max 5.07 pp). CDC's content-defined boundaries re-sync downstream regardless of where the edit lands — prepend ≈ terminal ≈ interior-position in *cost* terms. (NB: interior is still NOT bit-safe per DEAD-0008 — this is cost only, not a correctness revival.)

### Finding 3 — Where ~2% HOLDS vs BREAKS.
- **HOLDS (≤2%):** 66/100 cells — small injections (≤40 tok) into ≥4k contexts; large contexts (≥16k) tolerate bigger injections.
- **BREAKS (≫2%):** large tool injections relative to context. inj=1000 → 5.9% at 16k, 20% at 4k, **49–53% at 1k**. A 1000-token tool result (e.g. a big search/code-exec dump) into a 1–4k prompt collapses CDC to ~full-recompute.

## Verdict
~2% is **conditionally true**: it holds iff injection ≪ context (inj/seq ≲ 1%). It is NOT a universal property of CDC repair; it is a point on a surface where recompute% tracks inj/seq with slope ≈1. Edit position (prepend/terminal/depth) is NOT the cost driver — injection size is. This **weakens** the unconditional "~2%" framing and **supports** CLAIM-0006's reframing as a *conditional cost-map*: the claim should state the operating regime (inj/seq) under which 2% holds.
