# EXP-0055 (CLAIM-0050) — L1 cost-aware staged 4-gate — REPORT
**Researcher:** researcher-0053 | **Date:** 2026-06-03 | **Node:** devgpu014 (H100)
**Model:** Qwen3-VL-4B-Instruct (vLLM 0.22.0, ros-vllm07, bf16, temp=0)

## ONE-LINE DISPOSITION
GATE-1 (ecological premise) **PASSES on the letter** but with an important twist; GATE-2
(continuous-batching realism) shows the headline p99 regression **largely COLLAPSES at realistic
vLLM batch sizes**, surviving only in a small-batch / high-load corner. -> **keep-exploring,
leaning weaken**. The L0 M/G/1 magnitude (1.4-5.8x) is NOT robust to continuous batching at
realistic batch sizes; it is a small-batch + heavy-tail regime effect.

## GATE-1 — LOAD-BEARING real-VLM tau (Option A: real VLM forward pass)
Real Qwen3-VL-4B on a 220-example synthetic perception+reasoning IMAGE+TEXT mix spanning the two
claim-critical regimes (OCR/caption = big image/short answer; visual-reasoning = small image/long
CoT) + intermediate (small_short, large_long). Per-request: input_token_count (image+text, from
processed prompt) and REALIZED decode length (vLLM, natural EOS, max_tokens=4096 to uncensor tail).
Anti-circular preserved (decode realizes via EOS, not used in any ordering).

- **Measured Kendall-tau_b(input_tokens, decode_tokens) = +0.276, 95% bootstrap CI [+0.166, +0.385]**
  (p=1.4e-8; Spearman +0.397; n=220; B=5000 resamples). HICAP (uncensored, decisive).
- Base run (cap512): tau_b=+0.214 [+0.095,+0.326]. Drop-censored robustness: tau_b=+0.151 [+0.013,+0.279].
- Per-regime medians: ocr_short in=1118/out=9; reason_long in=190/out=763; large_long in=1208/out>=4096
  (34/40 right-censored, biases tau UP for that cell, so true tau slightly LOWER but still firmly >0);
  small_short in=125/out=2.

### GATE-1 DECISION = **PASS** (with honest caveat)
- L0 tau* band [+0.43 (rho=0.7) .. >+0.8 (high load)]. Measured tau CI-upper (+0.385) < +0.43 ->
  pre-registered rule satisfied. At the real tau (+0.276) the L0 M/G/1 model interpolates a p99
  ratio of 1.44 (rho=0.7), 1.68 (0.8), 2.92 (0.9), 5.12 (0.95) — i.e. real tau IS in the harmful
  region of the L0 model. So the ecological premise (real mixes below tau*) HOLDS.
- **HONEST CAVEAT (important):** the claim ASSUMED real VLM tau ~ 0.0 to -0.2. The measured real
  tau is clearly **POSITIVE (+0.28)** and statistically significant — input length is a MODERATELY
  INFORMATIVE proxy on this real mix, NOT the misleading/anti-correlated proxy the claim's framing
  implies. The premise survives only because L0's tau* crossover is high; the spirit ("input length
  is a bad proxy on real VLM mixes") is materially weakened.
- Ecological limitations STATED: single 4B VLM, synthetic images, greedy decode, large_long
  right-censored at 4096. Real production traces could differ.

## GATE-2 — continuous-batching realism (NOT M/G/1)
Stdlib iteration-level scheduler: up to B active reqs, each iteration advances every active req by
1 decode token (vLLM processor-sharing model), admission by policy (FCFS=arrival, SJF=input-token
proxy), preemption-free iteration-level. Workload coupled to the REAL measured tau via Gaussian
copula on the EMPIRICAL (input, decode) marginals. Load = utilization rho relative to capacity
(B/mean_decode). 10-12 reps/cell, bootstrap + batch-means CIs.

SJF_p99 / FCFS_p99 at real tau=+0.276 (>1 => SJF worse):
| rho\B | 4 | 8 | 16 | 24 | 32 | 48 | 64 | 128 |
|------|---|---|----|----|----|----|----|-----|
| 0.90 | 2.30 | 1.85 | 1.37 | 1.17 | 1.09 | 1.04 | 1.01 | 0.99 |
| 0.95 | 2.64 | 2.48 | 1.89 | 1.83 | 1.92 | 1.25 | 1.16 | 1.05 |
(CIs in raw/gate_refine.json; e.g. rho0.9/B16 ratio 1.37 CI[1.25,1.50]; rho0.9/B32 1.09 CI[1.04,1.13];
rho0.9/B128 0.995 CI[0.992,0.997]; rho0.95/B48 1.25 CI[1.12,1.40]; rho0.95/B128 1.05 CI[1.00,1.09].)

### GATE-2 DECISION = **AMBIGUOUS / regime-dependent (does NOT robustly survive)**
- Regression SURVIVES (>=1.2x, CI lower bound >1.0) ONLY at small batch (B<=16 at rho=0.9; B<=48
  at rho=0.95). At realistic vLLM batch sizes (B>=32-64) the effect COLLAPSES to ~1.0.
- This CONFIRMS committee concern (a): the M/G/1 sim OVERSTATED HOL blocking. Continuous batching
  with adequate batch width provides processor-sharing relief that erases the FCFS advantage SJF
  was sacrificing. The 1.4-5.8x L0 magnitude is a SMALL-BATCH artifact under realistic tau.
- Contrast (rho=0.9,B=32): ratio at tau=-0.2 (assumed) = 1.39; at tau=0.0 = 1.24; at real
  tau=+0.276 = 1.05; at +0.45 = 1.12. The POSITIVE real tau materially attenuates the harm.

## GATE-3 — CIs
All p99 ratios above carry bootstrap (B=3000) + batch-means CIs (raw JSONs)-… tau itself:
+0.276 [+0.166,+0.385] (B=5000). L0 tau* localized from EXP-0054 sweep: ~+0.485 at rho=0.7,
>+0.8 (off-grid) at rho>=0.9 (p99 stays >1 across the whole measured tau grid at high load).

## GATE-4 — sigma_d (decode tail) sensitivity (rho=0.9, B=32, real tau)
| sigma_d | 0.25 | 0.5 | 0.75 | 1.0 |
|---------|------|-----|------|-----|
| ratio   | 1.000| 1.000| 1.000| 1.192 |
The regression is **entirely conditional on the heavy decode tail (sigma_d=1.0)**; it vanishes
exactly at sigma_d<=0.75. The 1.4-5.8x magnitude is a heavy-tail phenomenon, not generic.

## VERDICT (honest)
CLAIM-0050 has a **marginal, regime-bounded** ecological foothold, not the strong one claimed:
1. Real VLM input-length IS positively correlated with decode (+0.28), contradicting the claimed
   ~0/negative — so input-length-SJF is a moderately reasonable proxy in reality.
2. The premise "below tau*" survives only because L0's M/G/1 tau* is high; but
3. under realistic continuous batching (large batch), the harm largely COLLAPSES (ratio ~1.0),
   surviving only at small batch + high load + heavy tail.
Consistent with Lykouris-Vassilvitskii / Purohit et al.: "bad predictor worse than baseline" is a
KNOWN robustness regime — here it manifests only in a narrow small-batch/heavy-tail corner, NOT at
realistic VLM serving params. The quantitative VLM-ecology contribution is a NEGATIVE/weakening
result: the dramatic L0 magnitude does not transfer to realistic continuous batching.

## PATHS (devgpu014)
~/exp0055/raw/gate1_vlm_hicap.csv (real VLM, decisive), gate1_vlm.csv (cap512), gate1_tau_summary.json,
gate234_results.json, gate_refine.json, run.log/run_hicap.log; scripts run_vlm*.py, gen_images.py,
calc_tau.py, gate234.py, gate_refine.py; manifest.json; images/ (220).
