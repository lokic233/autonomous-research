# EXP-0010 — Is the sub-quadratic injection-recompute exponent k≈1.3 a LAW or a LOCAL fit?

**Claim:** CLAIM-0005 (weakened) — originally "tool-call mid-prompt injection is a SUPER-quadratic recompute pathology."
**Agent:** researcher-subquad-0005 · **Level:** 1 · **Budget:** 30 min, CPU-only.
**Hardware:** CPU-only (Mac, `/usr/bin/python3` 3.9, stdlib only — NO GPU, NO torch/CUDA, NO model CLI, NO memory probes). Postmortem honored.
**Methodology family:** token-count / analytic FLOP-cost proxy on token streams — same family as PROJ-0002 `EXP-0002`/`EXP-0003` recompute-fraction microbenches. **NOT GPU wall-clock.**

## Background (what was already known)
- EXP-A005 (GPU, H100/MI350X, Qwen2.5-7B, 3 engines) **weakened** the super-quadratic framing: it fit `TTFT_cont(N) ~ N^k` (N = recomputed token count) and found **k = 1.29–1.31**, i.e. SUB-quadratic. The "super-quadratic discovery" is DEAD (red-zone; not revived here).
- The **surviving** question: is k≈1.3 a robust, characterizable regularity (a real corrected finding), or just a local fit / artifact?

## What this experiment did
Three parts, all CPU/stdlib:
- **(A) Proper re-fit of EXP-A005's own GPU TTFT data** — added what the original lacked: bootstrap 95% CI (4000 resamples), R², residual sign-run diagnostic, and a single-vs-piecewise model comparison, per engine × per inject position.
- **(B) Analytic FLOP-cost proxy across regimes** — reconstructed the recompute cost of the naive recompute-whole-suffix baseline at Qwen2.5-7B scale (d=3584, 28 layers) using the standard prefill decomposition (attention ~ `nl·d·(N·P + N²/2)`, MLP ~ `nl·c_mlp·d²·N`; Pope 2211.05102 / Kwon 2309.06180 accounting — used only as a proxy). Fit `cost(N) ~ N^k` per regime to test whether k is fixed or drifts.
- **(C) Naive baseline positioning** — recompute-token-count of naive-whole-suffix vs radix-LCP, the minimum baseline required by CLAIM-0005.

## Results

### (A) The GPU exponent IS robustly sub-quadratic — but is NOT a tight universal constant
Every engine × position fit has **CI upper bound < 1.85** → unambiguously SUB-quadratic. No fit is super-quadratic. But k is **not** a single tight number:

| engine | P25 | P50 | P75 | R² range |
|---|---|---|---|---|
| vLLM-0.6.6 | 1.293 | **1.313** | 1.285 | 0.993–0.998 |
| hf-transformers | 1.272 | 1.333 | 1.183 | 0.976–0.994 |
| sglang-0.5.12 | 1.180 | 1.174 | 1.090 | 0.992–0.998 |

- Range **1.09–1.33** across cells; bootstrap CIs are **wide** (e.g. hf P50: [1.10, 1.67]) because each fit has only n=5 points. vLLM is the tightest (~1.29–1.31, CI ⊂ [1.22, 1.53]).
- Pooled P50 across engines: **k = 1.27, CI95 [1.06, 1.52], R² 0.91**.
- Residual sign-runs = 3 everywhere (mild systematic curvature in log-log → a single power law is an approximation, not exact; piecewise SS is marginally lower but not a clean break).

### (B) k is NOT a law — it DRIFTS monotonically 1.0 → 2.0 with context length
The analytic proxy (R² ≥ 0.998 every cell) shows the exponent is **regime-dependent**, exactly as the attention/MLP-balance argument predicts:

| L regime (small inject, P50) | k_local |
|---|---|
| small-ctx 256–2k | **1.024** (MLP/linear-bound) |
| **A005-window 4k–32k** | **1.248** ← matches the GPU-measured 1.27–1.33 |
| large-ctx 64k–512k | **1.815** |
| asymptotic 1M–8M | **1.985** (attention/quadratic-bound) |

- Full surface (24 cells): **k_min 1.02, k_max 1.99, span 0.97**, monotone increasing toward 2.0.
- **The proxy independently predicts k=1.248 in the exact 4k–32k window where EXP-A005 measured 1.27–1.33 on real GPUs** — strong mechanistic corroboration that the GPU k≈1.3 is the *local* slope where attention FLOPs (∝N·P+N²/2) and MLP FLOPs (∝N) cross over for a 7B model at few-k–tens-of-k context.
- ⟹ **"k≈1.3" is a LOCAL OPERATING-POINT value, not a robust scaling law.** It is the few-k–32k context slice of a continuous 1→2 transition. At small ctx the penalty is ~linear; at large ctx it approaches the known quadratic-attention bound. There is no anomalous, conserved sub-quadratic exponent.

### (C) Naive vs radix baseline (token-count) — trivially position-governed
naive-whole-suffix / radix-LCP recompute ratio = 1.33× / 1.98× / 3.9× at inject f = 0.25 / 0.5 / 0.75, ctx-invariant. This is the Pope/Kwon accounting identity (recompute = tokens-after-divergence), flagged in academic_map as NOT a discovery.

## Honest verdict
**Effect on CLAIM-0005: weaken (confirms-and-explains-dead).**
- This does **NOT** support a re-framed "sub-quadratic characterization is a finding" claim. The sub-quadratic exponent is **not a robust law**: it is a regime-local slope that drifts continuously from 1 (MLP-bound, small ctx) to 2 (attention-bound, large ctx), and the specific value k≈1.3 is just where EXP-A005's 4k–32k Qwen-7B operating point lands on that continuum. The proxy *derives* 1.248 from textbook prefill FLOP accounting → the value is **explained, not anomalous**.
- The honest contribution is a **negative/corrective characterization**: (1) re-confirms EXP-A005's k<2 with proper CIs/R² (all CI-upper < 1.85); (2) shows the exponent is NOT universal (1.09–1.33 across engines, 1.0–2.0 across regimes); (3) explains it mechanistically as the attention/MLP crossover — i.e. an accounting consequence, the same red-zone territory CLAIM-0006's slope~1 was retired into (Pope/Kwon). There is no discovery here, sub- or super-quadratic.

## Map / prior-art deltas (orchestrator to record)
- **MAP-0001 red_zones:** add — "mid-prompt injection recompute exponent k (sub-quadratic ~1.3) = regime-local attention/MLP-crossover slope, NOT a law; drifts 1.0→2.0 with ctx; derivable from Pope 2211.05102 / Kwon 2309.06180 accounting — same accounting-identity retirement as CLAIM-0006 slope~1." Confirms the super-quadratic framing stays DEAD.
- **No new prior-art needed.** The mechanism is the standard prefill FLOP decomposition; no new citation surfaces.
- **Cemetery candidate:** the "k≈1.3 is a characterizable sub-quadratic regularity" sub-hypothesis should be buried alongside the super-quadratic one — both are facets of the same non-finding.

## Files
- impl: `experiments/2026-05-31/EXP-0010/impl/exp0010_recompute_exponent.py`
- results JSON: `experiments/2026-05-31/EXP-0010/experiment_result/exp0010_results.json`
- CSVs: `partA_gpu_refit.csv`, `partB_regime_drift.csv`
