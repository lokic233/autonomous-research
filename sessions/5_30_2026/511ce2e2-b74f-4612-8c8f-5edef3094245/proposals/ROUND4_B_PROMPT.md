You are ONE node in a 6-agent HOSTILE research committee. FINAL vote on Thesis B ONLY.
B was YELLOW because: only 2 engines, 2 context points, no fitted law, position dependence
unmeasured, and "superlinear is trivially predicted by quadratic attention." The full
experiment (E-B) has now RUN. Vote B RED/YELLOW/GREEN honestly. Do NOT force GREEN.

ANTI-COPING: superlinear/novel/significant FORBIDDEN unless followed by a cited number.

## THESIS B
"Tool-call mid-prompt injection is a superlinear, cross-engine prefix-cache recompute
pathology — a workload model for agentic serving." (recovery solution explicitly out of scope)

## E-B MEASURED RESULTS (real, H100, Qwen2.5-7B-Instruct, 3 engines × 5 context lengths × 3 positions × 5 reps)
PENALTY ratio = TTFT_contaminated / TTFT_cachehit:
- Magnitude: up to 16.75× (HF) / 12.67× (vLLM) at 32K. Reproduces prior live 8.21× (here 8.39× vLLM 16K/50%).
- penalty(L) power-law at P=50%, fitted across ALL 5 context points (4K/8K/16K/24K/32K):
  * vLLM-0.6.6:        penalty ∝ L^0.674, R²=0.974
  * SGLang-0.5.12:     penalty ∝ L^0.719, R²=0.998
  * HF-transformers:   penalty ∝ L^0.790, R²=0.973
  → cross-engine exponent agreement within 0.67–0.79 (±~8% of mean), 3 INDEPENDENT engines.
- POSITION dependence (now measured): strong, monotonic, stable. P25/P75 penalty ratio = 2.2–2.5×
  at every L. Penalty ≈ function of recomputed-token-count, as the mechanism predicts.
- THE KILL-TEST (absolute recompute exponent vs quadratic): absolute recompute TTFT ∝ N^1.29–1.31
  (95% CI upper ≈1.41, R²≥0.99) — FIRMLY SUB-QUADRATIC (k≈1.3 << naive attention k=2.0). On H100
  at 4K–32K, mid-prompt recompute is bandwidth/compute-bound, NOT attention-quadratic-bound, and
  NOT an emergent system amplifier. The harm is real and operationally large, but it is ORDINARY
  sub-quadratic prefill recompute — there is no hidden super-quadratic discovery.

## HONEST FRAMING
- What B IS: a measured, cross-engine (3 engines), position-resolved characterization of an
  operationally large (up to ~17×) agentic-serving pathology, with fitted scaling and a clean
  predictive structure (penalty ≈ f(recomputed tokens)).
- What B is NOT: a super-quadratic "emergent amplifier" discovery. The committee's "it's just
  algebra" critique is largely vindicated — the truth is even tamer than O(L²).

OUTPUT EXACTLY:
### B FINAL
- Vote: RED / YELLOW / GREEN
- Given it's measured/cross-engine/position-resolved but SUB-quadratic, is this GREEN-worthy as
  a WORKLOAD-MODEL/characterization paper, or does sub-quadratic cap it at YELLOW/workshop? (decide)
- Strongest remaining attack:
- Venue you'd bet on (MLSys / workshop / kill):
- One-line: the honest ceiling for this thesis.
