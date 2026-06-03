# RESULTS — EXP-0015 (L0, CLAIM-0012, PROJ-0003)
researcher-0015 | node dengcchi-mac (CPU-only, stdlib-only, SERIAL) | 8 seeds | <1 min compute
HONEST PIPELINE. Negatives are wins. All numbers from on-disk CSVs in results/ (trusted over stdout).
Pre-registration committed BEFORE run (commit c620e6f). This is a CONSTRUCTED-TRACE characterization;
all conclusions are stated as WORKLOAD-CONDITIONAL, not universal.

## VERDICT: PARTIAL→NEGATIVE (the claim does NOT hold as a usable system mechanism)
- Part A (waste exists): HELD CONDITIONALLY — waste >15% only at moderate+ abandonment rate AND mid/late timing.
- Part B (cheap early predictor): PARTIAL — a non-oracle, anti-circular predictor reaches AUC ~0.71 with
  positive lead time, BUT ONLY when abandonment is genuinely latent-driven; predictability is a WORKLOAD
  property and is at chance when abandonment is near-coin-flip.
- Part C (reclaim without harm at matched fairness): NEGATIVE — the deprioritization mechanism reclaims
  ~0 compute (pure slowdown can't free a doomed turn's slots), and the only mechanism that DOES reclaim
  (kill-on-flag) destroys MORE completed turns than it reclaims wasted tokens at the achievable precision.

The CORE claim ("deprioritize to reclaim compute WITHOUT harming completed-turn latency at matched
fairness") FAILS. The waste exists and is partly predictable, but you cannot cheaply convert that
prediction into reclaimed compute without harm at realistic AUC.

---

## PART A — Wasted-decode fraction surface  (results/A_wasted_decode_surface.csv)
Wasted-decode fraction = decode tokens spent on abandoned turns / all decode tokens. 8 seeds, 400 turns/cell.

| p_abandon | early | mid | late | mixed |
|-----------|-------|-----|------|-------|
| 0.10      | 2.7%  | 5.3% | 7.7% | 4.9% |
| 0.20      | 5.7%  | 11.4%| 16.6%| 10.8%|
| 0.35      | 10.7% | 21.1%| 28.7%| 21.6%|
| 0.50      | 18.3% | 31.7%| 43.0%| 33.8%|

ANSWER: The >15% threshold is crossed only at p_abandon≥0.20 with LATE-timing abandonment, and broadly
at p_abandon≥0.35. At low abandonment (10%) or EARLY abandonment (turns die before decoding much), waste
is small (3–11%). So part 1 is TRUE only in higher-abandonment / late-abandonment regimes — explicitly
CONDITIONAL, not a universal >15%. (Honest-negative branch N-A: not universal; small in the low/early regime.)

## PART B — Anti-circular predictor: AUC + lead time
Two CSVs. The predictor reads ONLY noisy partial-decode observables (entropy/repetition≈difficulty,
malformation≈tool-fragility, prune-risk≈low branch value, len-so-far, retry-count) at the first 25% of
planned length. It NEVER reads the latent hazard, the label, or abandon_step. Trained on 4 seeds, scored
on 4 held-out seeds (Mann-Whitney AUC).

### B2_predictability_frontier.csv — predictability is a WORKLOAD property (sharpen abandonment→latent link)
| hazard_sharpness | oracle_auc | observable_auc | flag_prec | median_lead_tokens | %positive_lead |
|------------------|-----------|----------------|-----------|--------------------|----------------|
| 0  (coin flip)   | 0.50      | 0.55–0.60      | ~0.40     | 0–7                | ~50%           |
| 3                | 0.60      | 0.58           | 0.39      | 13–19              | 63–71%         |
| 6                | 0.66–0.69 | 0.63           | 0.46      | 19–24              | 68–72%         |
| 10               | 0.74      | 0.66–0.68      | 0.50      | 16–25              | 67–72%         |
| 16 (sharp)       | 0.80      | 0.71–0.73      | 0.53–0.56 | 22–29              | 69–80%         |

ANSWER: The non-oracle predictor reaches AUC ~0.71 with median lead 22–28 tokens and 69–80% of fires
BEFORE abandonment — USABLE lead time. BUT the observable predictor tracks the ORACLE with a ~0.05–0.09
gap, and the ORACLE itself only exceeds 0.7 when abandonment is strongly latent-determined. When
abandonment is closer to a coin flip (hazard_sharpness≤3), even the oracle is ≤0.60 → no signal can
predict it (honest-negative branch N-B fires for unpredictable workloads). KEY HONEST FINDING:
predictability is a property of HOW DETERMINISTIC the real abandonment is, not of predictor cleverness.

CIRCULARITY CHECK: oracle AUC = predictor-from-latent-hazard ≤ 0.80 even when the predictor never sees
it; the observable predictor sits BELOW the oracle. No leakage — the predictor cannot beat the oracle.

## PART C — Reclaim vs completed-turn latency at MATCHED FAIRNESS
Token-time round-robin batch sim, contended batch (B=8, admit_rate=3), predictor in its BEST regime
(observable AUC ~0.71). 4 held-out seeds.

### C_reclaim_latency.csv — DEPRIORITIZE-ONLY (bounded-W slowdown, no kill)
| W | completed_p50 | completed_p99 | fp_turn_p99 | reclaimed_slots | p99 Δ% | within +5%? |
|---|---------------|---------------|-------------|-----------------|--------|-------------|
| baseline | 119 | 454 | — | 0 | 0% | yes |
| 1 | 133 | 537 | 636 | 0 | +18.3% | NO |
| 2 | 140 | 714 | 953 | 0 | +57.3% | NO |
| 4 | 144 | 1055 | 1588 | 0 | +132% | NO |
| 8 | 144 | 1893 | 2859 | 0 | +317% | NO |

DEPRIORITIZE-ONLY reclaims ZERO slots (slowing a doomed turn doesn't free its slots — it just spreads
them over more wall-clock, DELAYING self-termination and STEALING cycles from completed turns). Even the
smallest bound (W=1) blows the +5% fairness budget (+18%). NEGATIVE (honest-negative branch N-C).

### C2_kill_reclaim_vs_harm.csv — KILL-ON-FLAG (the only mechanism that CAN reclaim)
| thr_quantile | kill_precision | reclaimed_tokens | reclaim_%_total | lost_completed_turns | lost_completed_% |
|--------------|----------------|------------------|-----------------|----------------------|------------------|
| 0.70 | 0.50 | 6674 | 3.4% | 210 | 18.6% |
| 0.80 | 0.50 | 3600 | 1.9% | 140 | 12.4% |
| 0.90 | 0.51 | 1340 | 0.7% | 62  | 5.5%  |
| 0.95 | 0.57 | 786  | 0.4% | 25  | 2.2%  |

ANSWER: To reclaim compute you must KILL the flagged turn — but at the achievable kill-precision (~0.50
at AUC 0.71), every doomed turn killed comes with ~1 GOOD turn killed. Reclaim is small (0.4–3.4% of
total decode) while lost completed turns are 2.2–18.6%. At EVERY operating point the harm (destroyed
user-facing completions) dominates the reclaim. The reclaim-WITHOUT-harm condition FAILS decisively.

---

## HONEST JOINT VERDICT
- Waste EXISTS and is non-trivial in high/late-abandonment regimes (conditional, not universal).
- A cheap, anti-circular early predictor CAN reach AUC ~0.71 with usable lead time — but only when the
  workload's abandonment is genuinely latent-determined, and never above the oracle ceiling.
- The claim's payoff step FAILS: deprioritization reclaims nothing (pure slowdown), and kill-on-flag at
  realistic precision destroys more good work than it reclaims. CLAIM-0012 does NOT hold as stated.

VERDICT: PARTIAL on measurement (A,B), NEGATIVE on the load-bearing system mechanism (C).

## PRIOR-ART CAVEAT (novelty)
Generic LLM-serving preemption/SLO scheduling already exists: Llumnix (migration/rescheduling), FastServe,
TokenFlow & FlowPrefill (preemptive scheduling / HOL-blocking), SLO-aware schedulers (SLICE, Nitsum),
speculative-decode scheduling (AdaSpec, semi-clairvoyant). The NOVEL angle of CLAIM-0012 is
AGENT-ABANDONMENT-SPECIFIC waste characterization + an early abandonment predictor exploiting agent-loop
structure (retries, tool malformation, branch pruning). This L0 shows the *mechanism* nonetheless reduces
to generic preemption/kill once you try to reclaim — with the agent-specific signal too weak/imprecise to
reclaim without harm. Distinguishing from generic preemption requires a real agent-specific signal
advantage that this constructed model does NOT demonstrate (novelty at risk).

## WHAT A REAL L1 SHOULD MEASURE (not provable at L0)
1. REAL abandonment in REAL agent traces (tau-bench / SWE-agent / production agent logs): the actual
   abandonment rate, timing distribution, AND how deterministically abandonment is tied to observable
   partial-decode signal — i.e. measure the real ORACLE AUC ceiling, which is the binding constraint.
2. REAL partial-decode signals as the predictor (true output entropy, repetition, tool-call parse-fail
   probability mid-generation, branch retry count) run on a real LLM — measure real AUC + real lead time.
3. REAL reclaimed GPU compute + p99 TTFT/TPOT at MATCHED FAIRNESS, with a REAL preemption/kill mechanism
   and the cost of re-running false-positive-killed turns counted honestly.

## REPRODUCIBILITY
Files in experiments/2026-06-03/EXP-0015/: harness.py (trace model + part A + AUC), predictability_sweep.py,
sharpen.py (latent-determinism sweep + final B2), part_c_final.py (deprioritize-only), part_c_kill.py
(kill variant), part_c_v2.py (earlier honest-zero-reclaim cross-check). Seeds [11,23,37,59,71,89,101,113],
train=first4 / test=last4. CPU-only, Python 3.9 stdlib, SERIAL. CSVs in results/.
