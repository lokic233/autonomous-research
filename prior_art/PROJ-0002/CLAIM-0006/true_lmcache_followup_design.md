# TRUE-LMCACHE / CacheBlend FOLLOW-UP — RIGOROUS EXPERIMENT DESIGN
**Claim:** CLAIM-0006 (Prefix-Cache Invalidation Law + CDC win-region; serving leg)
**Status feeding this design:** YELLOW (VERDICT-0029, VERDICT-0033, VERDICT-0034)
**Author:** researcher-0002-laneD (DESIGN-only, CPU). **Date:** 2026-05-31
**Runs once env `ros-vllm` (operator-owned, lmcache source-built against torch 2.5.1 on devgpu014) is GREEN.**
**SCOPE NOTE:** This is a *design document only*. No experiment is registered here; no claim/verdict/map edits.
The orchestrator owns GPU dispatch into `ros-vllm`. DO NOT pip-install lmcache into the working env (it BROKE
vLLM last time — lesson logged). DO NOT touch py312conda or run model CLIs from this lane.

---

## 0. WHY THIS EXPERIMENT EXISTS (the binding residual)

The committee has held YELLOW across VERDICT-0029/0033/0034 on a single, specific, *load-bearing* confound:

- **EXP-0026** (real vLLM 0.6.6 PagedAttention, Qwen2.5-7B, H100) showed **CDC wins ALL 12 serving cells**
  on BOTH TTFT (PIC/CDC 1.05–1.79×) and batched throughput (CDC/PIC 1.00–1.13×). **BUT** the PIC arm was a
  **faithful RE-IMPL** (scattered paged-gather over the vLLM page table), **NOT** the published **lmcache
  CacheBlend FUSED kernel** that *defines* PIC in the literature (arXiv:2405.16444, EuroSys'25 Best Paper).
- **EXP-0027** (oracle/fused-PIC roofline bound, SDPA-optimal, zero gather/launch overhead) showed CDC's
  serving advantage is **CONDITIONAL**: CDC wins ONLY at **high inj/seq (25%)** (oraclePIC/CDC 1.05–1.18×)
  and **LOSES at low inj/seq (1–5%)** (oraclePIC/CDC **0.61–0.99×**, i.e. the fused PIC is faster).

The committee's VERDICT-0033 fatal objection, restated precisely:
> "SIGN SURVIVES" overreaches when the comparator is suboptimal: EXP-0026's win was *partly* an artifact of
> the re-impl PIC's gather overhead; the throughput floor touches **1.00–1.01×** in some cells — within the
> margin a fused kernel could erase — and **inj/seq≥5% is exactly where CacheBlend's fused kernel was designed
> to excel.**

EXP-0027 (the oracle bound) already *vindicated* that skepticism analytically. **This experiment is the
empirical resolution**: measure the REAL lmcache CacheBlend fused KV-blending path on the same surface, with a
deliberate, dense sweep through the **low inj/seq (1–5%) regime where the oracle bound says CDC should lose.**

**The decisive question:** Does CDC beat the *real published fused* CacheBlend kernel, *especially at low
inj/seq* where EXP-0027's oracle bound predicts it should NOT?

---

## 1. HONEST EXPECTED OUTCOME (state up front — this is not a fishing trip)

Given EXP-0027's oracle bound, the **honest prior is that CDC LOSES to real lmcache CacheBlend at low inj/seq
(1–5%)** and wins at high inj/seq (≥25%). The most probable result is a **measured crossover**, not a clean
sweep. Specifically:

- **Likely:** real-CacheBlend/CDC < 1.0 (CacheBlend faster) at inj/seq ∈ {1%, 5%}, especially at 8k seq;
  CDC ≥ 1.0 at inj/seq = 25%. A real fused kernel *may* land **between** the EXP-0026 re-impl (which CDC beat
  everywhere) and the EXP-0027 zero-overhead oracle (which beat CDC at low inj/seq) — because real lmcache
  carries *some* real gather/launch/HBM overhead the oracle assumed away. The crossover inj/seq is the
  experimental unknown this run pins down.
- **Consequence for CLAIM-0006:** a low-inj/seq CDC loss **WEAKENS the unconditional "CDC wins serving"
  framing** and **forces the CONDITIONAL reframe**: *CDC's serving advantage vs a fused PIC is itself
  conditional on inj/seq (wins at high inj/seq, loses at low)* — note this is the **OPPOSITE direction** to the
  recompute-FRACTION win-region (which favors CDC at LOW inj/seq). That double-conditional is a real,
  publishable nuance, but it is NOT the headline the candidate claim currently asserts.
- **This is the correct scientific posture per VERDICT-0029:** "a measured negative result is publishable; an
  unmeasured concession is not." We design to *measure the negative if it exists*, not to dodge it.

---

## 2. CELLS (the surface) — dense LOW-inj/seq, because THAT is the decisive regime

Two seq lengths bracket the win-region transition (matches EXP-0026/0027 so results are directly comparable):

| seq (S) | rationale |
|---|---|
| 8 192 (8k)  | EXP-0027's *worst* cell for CDC (oraclePIC/CDC 0.61 @1%). Decisive low-S regime. |
| 28 672 (28k) | matches EXP-0026's large-ctx cell (CDC's strongest re-impl win, TTFT 1.79×). 32k OK if KV fits. |

**inj/seq sweep — DENSE in the decisive 1–5% band, anchored to CLAIM-0006's stated win-region (inj/seq ≤ ~1%):**

| inj/seq | R @8k | R @28k | why this cell is in the design |
|---|---|---|---|
| **0.5%** | 41  | 143 | *Below* the stated win-region corner — the most CDC-favorable-by-fraction, oracle-worst extreme. NEW vs EXP-0027. |
| **1%**   | 82  | 287 | CLAIM-0006 win-region corner. EXP-0027 oracle beat CDC here (0.61 @8k, 0.97 @28k). **THE decisive cell.** |
| **2%**   | 164 | 573 | mid-low; brackets the median agentic inj/seq (~2.8%, EXP-0005). NEW. |
| **5%**   | 410 | 1434 | EXP-0027 oracle still beat CDC (0.64 @8k, 0.99 @28k). The CacheBlend "designed-to-excel" floor. |
| **10%**  | 819 | 2867 | NEW intermediate — locate the crossover between 5% (oracle wins) and 25% (CDC wins). |
| **25%**  | 2048| 7168 | EXP-0027 oracle LOST to CDC (1.05–1.18×). CDC's expected-win anchor; confirms re-impl→fused didn't flip it. |

**= 2 seq × 6 inj/seq = 12 cells.** Identical seq/{1,5,25%} subset to EXP-0026/0027 for apples-to-apples; the
**0.5 / 2 / 10%** rows are NEW and exist specifically to *localize the crossover inj/seq* where real CacheBlend
overtakes CDC. The crossover location is the headline quantitative deliverable.

**Edit position:** mid-prefix insertion at f=0.5 (center), consistent with the position-independence law
(EXP-0002/0003: cost spread vs position median 0.39pp). Hold position fixed; the law already shows position is
not the cost driver, so spending the rep budget on inj/seq × batch resolution is the right trade.

---

## 3. THE TWO ARMS — CDC vs the REAL lmcache CacheBlend KV-blending path

### Arm A — CDC (contiguous recompute) [unchanged from EXP-0026]
Recompute the contiguous affected block as ONE prefill over a contiguous token range, re-using the vLLM KV
cache for the untouched prefix. End-to-end through the vLLM engine. (CDC pays a boundary window Wb=256 — see §6;
this asymmetry is the modeling choice EXP-0027 flagged and is held identical here so the comparison is fair.)

### Arm B — REAL lmcache CacheBlend (the fused KV-blending path) [THE NEW THING]
This is the arm EXP-0026 could NOT run (lmcache absent) and EXP-0027 could only *bound*. Now measured through
the operator's source-built lmcache in `ros-vllm`.

**lmcache / CacheBlend API & config to drive (cite arXiv:2405.16444; lmcache `LMCacheEngine` + CacheBlend
"blend" path):**
- **Mechanism:** CacheBlend reuses precomputed KV for ALL reused tokens *regardless of prefix position*, then
  **selectively recomputes a small fraction `r%` of tokens per layer** (the HKVD — High-KV-Deviation — tokens,
  selected by KV-deviation magnitude) and **fuses** the recomputed KV back into the cached KV via the fused
  blending kernel. This is the FUSED path that defines PIC; the re-impl in EXP-0026 emulated only the
  scattered-gather, not the fused blend.
- **The load-bearing knob — `r%` (CacheBlend recompute ratio):** CacheBlend §4 states the accounting identity
  "recompute r% of tokens ⇒ ~r% of full-prefill compute overhead." In lmcache this surfaces as the CacheBlend
  **recompute-ratio / blend special-tokens config** (config keys to confirm against the source-built version,
  e.g. `LMCACHE_CONFIG`/`CacheBlendConfig`: the recompute fraction and the gather/blend layer scope). **Two
  settings of `r%` are mandatory:**
  1. **`r%` = CacheBlend's own quality-preserving default** (the published recommended setting, ~15% per
     EPIC's `O(15%·N²)` note on CacheBlend) — *the literature-faithful operating point.*
  2. **`r%` tuned DOWN to the minimal fraction that still passes the §5 quality gate** (lowest-overhead honest
     CacheBlend) — *the most CacheBlend-favorable speed point that the committee cannot call a strawman.*
  Reporting BOTH brackets real CacheBlend's *actual* speed envelope and kills the "you ran an unoptimized r%"
  rebuttal symmetrically to how EXP-0026's re-impl invited the "unoptimized gather" rebuttal.
- **KV layout:** real vLLM PagedAttention non-contiguous paged KV (same engine version family as EXP-0026,
  pinned to whatever `ros-vllm` provides against torch 2.5.1 — record exact vLLM+lmcache versions in result.md).
- **Quality guard (REQUIRED, new vs EXP-0026/0027):** CacheBlend trades a *little* quality for speed via `r%`.
  Any speed comparison is only fair if both arms produce equivalent outputs. Record an output-fidelity metric
  per cell (greedy-decoded token-match rate, or F1/ROUGE vs a full-recompute reference on a fixed 20-prompt
  probe set) for BOTH arms. A CacheBlend `r%` setting that "wins" on speed but FAILS the quality gate is NOT a
  valid win — flag and exclude. CDC (exact recompute of the block) is the quality reference.

---

## 4. METRICS

Per cell, both arms, report median + p95 + 95% CI:
1. **E2E TTFT (ms)** — time to first token, end-to-end through the vLLM engine (the user-facing latency the
   serving claim is about). Primary.
2. **Batched throughput (tok/s)** — at batch sizes below. The axis VERDICT-0029 specifically demanded measured
   (not conceded) because CDC's larger contiguous recompute *could* favor PIC aggregate throughput.
3. **Output fidelity** (token-match / F1 vs full-recompute reference) — the CacheBlend quality guard (§3 Arm B).
4. **Derived:** `realCacheBlend/CDC` TTFT ratio and `CDC/realCacheBlend` throughput ratio per cell (so >1.0
   always = "CDC better," matching EXP-0026/0027 sign convention for direct overlay).

**Batch sizes:** **B ∈ {1, 8, 32}** — matches EXP-0025/0026. B=1 isolates per-request latency; B=8 is the
EXP-0026 cell where CDC's re-impl win was strongest (28k/B8); B=32 stresses aggregate throughput where a fused
kernel's better memory-hierarchy behavior could most plausibly overtake CDC. (Drop B=32 only if KV cache at 28k
× 32 does not fit under gpu_mem_util ≤ 0.6 — record the constraint; do NOT raise the mem cap.)

---

## 5. REPS, CI METHOD, STATISTICAL DECISION

- **Reps:** **30 per (cell × arm × batch)** — matches EXP-0021's CI-grade rep count (EXP-0026 used only 5;
  30 is required here because the decision hinges on cells where the ratio is expected NEAR 1.0, so the CI must
  be tight enough to *exclude* 1.0 to claim a sign).
- **Warmup:** discard first 3 reps per cell (CUDA-graph capture / lmcache cache-fill transients).
- **CI method:** **non-parametric bootstrap** (10 000 resamples) of the per-rep ratio distribution → 95% CI on
  the median ratio, identical to EXP-0021. Report `[lo, hi]` per cell. Paired by (prompt, seq, inj, batch) so
  the ratio CI is paired-bootstrap (resample matched rep pairs), not two independent CIs.
- **Sign decision per cell:** a cell is a **CDC WIN** iff the 95% CI of the relevant ratio is **strictly > 1.0**;
  a **CDC LOSS** iff strictly < 1.0; **TIE/ambiguous** iff the CI straddles 1.0. (Mirrors EXP-0021's "CI95
  excludes 1.0" rule that resolved the area_chair objection.)

---

## 6. CONTROLS & FAIRNESS (pre-empt the obvious rebuttals)

- **Boundary window Wb=256 (CDC) held identical to EXP-0027.** EXP-0027 noted CDC pays a boundary window
  (R+Wb) that the oracle PIC skipped — this asymmetry is *why* CDC lost at low inj/seq in the bound. Keep Wb=256
  for the headline (conservative, PIC-favorable). **Sensitivity sub-sweep:** also run CDC at Wb ∈ {64, 128} on
  the 4 low-inj/seq decisive cells (8k & 28k × 0.5% & 1%) — if a smaller honest Wb flips CDC back to a win
  there, that is a *legitimate CDC design lever* worth reporting (and weakens EXP-0027's bound), not a cheat.
  Document whichever Wb is used and why.
- **Same model, same vLLM engine, same KV layout, same prompts** across arms. Only the recompute path differs.
- **lmcache/vLLM/torch versions pinned and recorded** in result.md (the whole point is the *published fused
  kernel* — version provenance is load-bearing for the committee).
- **Quality gate symmetric:** CDC = exact (reference); CacheBlend must pass the fidelity gate at its `r%`.

---

## 7. PASS / FAIL CRITERION (what lets the committee resolve GREEN vs YELLOW)

The committee's open question (VERDICT-0033 path 1): *does CDC beat the REAL fused kernel, especially at low
inj/seq where the oracle bound says it shouldn't?* The criterion is stated so EITHER outcome is decision-grade:

- **GREEN-supporting (unconditional serving claim survives):** real-CacheBlend/CDC **95% CI > 1.0 (CDC wins)
  in ALL low-inj/seq cells** {0.5%, 1%, 2%, 5%} on BOTH TTFT and throughput, at a CacheBlend `r%` that PASSES
  the quality gate. This would mean the EXP-0027 oracle bound was *too* pessimistic (real fused overhead
  exceeds the oracle's zero-overhead assumption enough to keep CDC ahead) → committee can promote CLAIM-0006's
  serving leg toward GREEN with the *unconditional* framing intact.
- **FAIL / CONDITIONAL-REFRAME (the honest expected outcome):** real-CacheBlend/CDC **95% CI < 1.0
  (CacheBlend wins) in ANY low-inj/seq cell** (esp. 1%, the win-region corner) → the unconditional "CDC wins
  serving" framing is **falsified at low inj/seq**. CLAIM-0006 MUST adopt the **conditional serving reframe**:
  *"CDC's serving advantage vs a published fused CacheBlend kernel holds at high inj/seq (≥~X%) but inverts at
  low inj/seq; the crossover is at inj/seq ≈ [measured]."* This RESOLVES the YELLOW honestly (a measured
  negative is publishable; VERDICT-0033 path 3 = "narrow the claim text") — it does not kill the claim, it
  scopes the serving leg. The recompute-FRACTION law and win-region (the actual novelty) are untouched.
- **TIE (CI straddles 1.0) in the decisive cells:** insufficient to claim a sign → recommend more reps or
  treat as effectively "no CDC serving advantage at low inj/seq," which still forces the conditional reframe
  (cannot assert unconditional CDC serving win).

**Net:** GREEN requires CDC to win the LOW-inj/seq cells vs real CacheBlend. EXP-0027 predicts it won't. So the
most likely committee-resolving outcome is the **conditional reframe (YELLOW→GREEN-conditional)**, where the
claim's serving leg is honestly scoped to high inj/seq and the crossover is reported as a measured contour.

---

## 8. SAFETY / OPERATIONAL CONSTRAINTS (carry forward all logged lessons)

- **H100 devgpu014 ONLY** (non-fragile). NOT a mapping probe. Bounded: single vLLM engine, gpu_mem_util ≤ 0.6,
  tensor_parallel=1, host-mem-floor 300 watchdog, `os._exit(0)` teardown (vLLM holds CUDA graphs/NCCL).
- **`ros-vllm` env is the OPERATOR'S** (source-built lmcache vs torch 2.5.1). This lane does NOT build it, does
  NOT modify it, does NOT pip-install lmcache anywhere (pip-installing lmcache into the working env BROKE vLLM
  — logged). Orchestrator owns GPU dispatch into `ros-vllm`.
- Cap reps (30); do not chase large numbers. Record exact vLLM+lmcache+torch versions.

---

## 9. DELIVERABLE ON RUN COMPLETION (for the runner, not this lane)
A `result.md` reporting the 12-cell (× batch) table with `realCacheBlend/CDC` TTFT + throughput ratios + 95%
bootstrap CIs + quality-gate pass/fail per cell + the **measured crossover inj/seq**, mapped against EXP-0026
(re-impl) and EXP-0027 (oracle) so the committee sees the real fused kernel land between (or outside) the two
bounds. Then a fresh committee verdict on GREEN-vs-conditional per §7.
