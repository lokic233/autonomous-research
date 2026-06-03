# RESULTS — EXP-0049 (CLAIM-0047) — CORRECTED RE-RUN of EXP-0046

**Researcher:** researcher-0047 | **Outcome: HONEST-NEGATIVE** (claim's >=25% fair-token penalty NOT
established; the prior +4000% was a non-completion artifact, and under FAIR finite accounting the
wasted-token comparison is dominated by an irreconcilable completion-rate gap, not a clean token win).
Calibration gate **PASSED** (the two EXP-0046 bugs are fixed). All numbers from committed CSV
`results/results_corrected.csv` (25 rows, R=4000, 22s, SERIAL, pure-stdlib). NOT fabricated.

## CALIBRATION GATE (FIX #3) — PASS
Pre-reg locked: at alpha=0 require |penalty| < 5% with CI overlapping 0, else STILL-BUGGY.
  - **alpha=0, B1 (FPR=FNR=0.1): penalty = -2.6%**, CI[-3.7, -1.6], dnc_A=dnc_B=0.0
  - **alpha=0, B2 (overshoot=1):     penalty = -1.6%**, CI[-2.0, -1.1], dnc_A=dnc_B=0.0
Both |penalty| < 5%. **GATE PASSES.** The EXP-0046 alpha=0 bug (-46%/-28%, B unconditionally
over-rolled-back) is FIXED by the evidence-gated detector (FIX #2): at flat hazard, re-fails are rare,
so B's >=K_EVID=2-fails-since-advance gate rarely fires and B behaves ~like A. The tiny residual -2%
is B's occasional spurious-evidence overshoot — within tolerance, CI excludes a B-advantage. Honest
memoryless prediction confirmed: when failures are memoryless, restart-from-last-checkpoint is optimal
and deviation-aware rollback gives no benefit (small deadweight if it fires at all).

## penalty(alpha) — LINEAR, c=20, B1 (FPR=FNR=0.1), R=4000  [the headline sweep]
| alpha | pen_marginal | CI | dnc_A | dnc_B | pen_COMPLETION-CONDITIONAL |
|------:|-------------:|----|------:|------:|---------------------------:|
| 0.000 |  **-2.6%** | [-3.7,-1.6] | 0.000 | 0.000 |  -3% |
| 0.002 |  +27.2%    | [+23.4,+31.4] | **0.605** | 0.014 |  **-51%** |
| 0.005 |  +50.8%    | [+47.0,+54.9] | **0.700** | 0.014 |  **-61%** |
| 0.010 |  +68.7%    | [+64.7,+72.8] | **0.671** | 0.011 |  **-58%** |
| 0.020 |  +94.0%    | [+89.0,+99.0] | **0.579** | 0.009 |  **-52%** |
| 0.040 |  +55.3%    | [+52.0,+58.9] | **0.498** | 0.016 |  **-45%** |
(B2 sweep nearly identical: +4.4/+53/+72/+91/+46% with the same dnc_A~0.5-0.7 vs dnc_B~0.01.)

## WHY THIS IS A NEGATIVE, NOT A HELD — three load-bearing observations
**1. The dnc rates are NOT comparable (50-70% vs ~1%).** The pre-reg states verbatim that the penalty
is trustable only when "the dnc rates for both policies are reported and comparable." They are NOT.
Policy A (restart-from-last-checkpoint) fails to COMPLETE 50-70% of rollouts at every alpha>0; policy
B completes ~99%. A and B are effectively playing different games (A doesn't finish; B finishes), so a
single marginal wasted-token mean is not an apples-to-apples token comparison.

**2. The marginal "penalty" is an ARTIFACT of A's non-completion and is ARBITRARY (set by the give-up
bound).** Varying MAX_ATTEMPTS at alpha=0.02 (R=2000):
  - MAX_ATTEMPTS=50  -> pen=+91%,  A_mean=162,  dnc_A=0.578
  - MAX_ATTEMPTS=200 -> pen=+395%, A_mean=481,  dnc_A=0.570
  - MAX_ATTEMPTS=1000-> pen=+886%, A_mean=1624, dnc_A=0.558
A's dnc is genuine (~0.57: it truly cannot escape the rising-hazard region from the last checkpoint),
but its DNC rollouts have UNBOUNDED token cost, so the marginal penalty diverges with the give-up bound.
This reproduces EXP-0046's +4000% as the SAME artifact, merely re-scaled by the bound. There is no
bound-independent finite penalty here.

**3. The only apples-to-apples token comparison (completion-conditional) FAVORS A, not B.** Among
rollouts that COMPLETED, policy A wastes 45-61% FEWER tokens than B at every alpha>0. Reason: when A
does complete (it never deviated, or deviated late/mildly), it never paid B's overshoot/over-rollback
deadweight. So conditional on finishing, the memoryless restart is *cheaper*, not more expensive.

**4. Non-monotonicity:** the marginal penalty is NOT monotone in alpha (rises 0.002->0.02 then FALLS at
0.04: +94%->+55%). At very high alpha, A gives up earlier (cheaper DNC) and B's re-execution also rises,
shrinking the gap. The pre-reg requires monotone non-decreasing for HELD — FAILS.

## The TRUE, defensible finding (the real mechanism, honestly stated)
The claim's underlying MECHANISM is real and confirmed: under a rising post-deviation hazard,
restart-from-last-checkpoint frequently CANNOT escape the elevated-hazard region (it restarts inside it
and re-fails), so it fails to COMPLETE 50-70% of the time, while rolling back PAST the inferred onset
restores the on-path low hazard and completes ~99%. **The benefit of deviation-aware rollback is a
COMPLETION-RATE / reliability benefit, NOT a wasted-token benefit.** On the claim's stated currency
(>=25% more expected WASTED TOKENS, fair finite accounting, comparable dnc), the claim is NOT supported:
the token comparison is either arbitrary (marginal, bound-dependent) or favors A (completion-conditional).

## detector FPR/FNR boundary (alpha=0.02, c=20, B1) — marginal pen (uninterpretable per above, reported for completeness)
(0,0): +115% | (0.1,0.1): +94% | (0.25,0.25): +64% | (0.5,0.5): +34%. dnc_A~0.58 throughout, dnc_B~0.01-0.016.
B's marginal advantage degrades smoothly with detector noise but never inverts here — again driven by the
completion-rate gap, not tokens.

## checkpoint spacing (alpha=0.02, B1) — marginal pen
c=10: +7.7% (dnc_A=0.76) | c=20: +94% (dnc_A=0.58) | c=40: +32% (dnc_A=0.35). Spacing changes dnc_A and
thus the artifact magnitude; no stable token penalty.

## Weibull k=2 variant (c=20, B1), swept base_w
base_w=0: -3.3% | 0.0002: -67% | 0.0005: -53% | 0.001: -3% (dnc_A 0->0.34). At low base_w B's overshoot
is net-negative (deadweight) consistent with the gate; as hazard rises dnc_A climbs and the same artifact
re-appears. No clean monotone >=25% token win.

## SANITY (hand-checked)
- Hazards in [0,1]: h0_fail=0.002, alpha*t capped at H_CAP=0.6. OK.
- alpha=0 paired waste_A ~= waste_B (22 vs 23 tokens), CI excludes B-advantage. Common-RNG verified (A,B
  share seed -> identical onset/failure draws; gate -2.6% is a tight paired contrast, not RNG noise).
- Both policies face the SAME MAX_ATTEMPTS=50 give-up rule; DNC waste = actual finite tokens spent. OK.

## DECISION: HONEST-NEGATIVE
Gate PASSES; alpha=0 ~ -2.6% (~0). But: (a) alpha>0 marginal penalty is a non-completion artifact
(diverges with the give-up bound, dnc_A 0.5-0.7 vs dnc_B ~0.01, NOT comparable -> untrustable per
pre-reg), (b) the only fair apples-to-apples token metric (completion-conditional) FAVORS A by 45-61%,
(c) the marginal penalty is non-monotone. The >=25%-more-WASTED-TOKENS claim under FAIR finite,
comparable accounting is NOT supported. The real effect is a COMPLETION-RATE/reliability advantage for
deviation-aware rollback, not a token-cost advantage. => "HPC-inherited restart-from-last-checkpoint is
near-optimal for agent TOKEN economics; deviation-aware rollback buys RELIABILITY (completion), not
fewer tokens." This is a clean, useful negative on the claim as stated.

## WHAT L1 SHOULD MEASURE
1. REAL agent-trace hazard curves: instrument real long-horizon agent rollouts (tool-use/coding agents)
   to measure whether per-step failure hazard actually RISES with steps-since-deviation, and fit alpha /
   Weibull-k to real traces (the whole claim hinges on this being non-memoryless in practice).
2. Re-pose the claim in the RIGHT currency: if the real win is completion-rate, measure
   completion-rate(policy) and tokens-to-COMPLETION conditional on completing, with a realistic,
   agent-grounded give-up budget (real agents have a finite token budget -> DNC has a real, bounded cost).
3. Whether a real deviation detector (from observable failure clustering / repeated tool errors) can fire
   the evidence gate with the FPR/FNR assumed here, on real traces.
