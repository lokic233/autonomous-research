# PROJ-0017 — Agentic-systems: cost-optimal recovery ROLLBACK DEPTH under rising post-deviation hazard (EMPIRICAL PHENOMENON / policy-cost)
Fresh area: agentic-systems (recovery policy). EMPIRICAL-phenomenon archetype (NO closed form in the
non-memoryless regime — optimal rollback depth depends jointly on the realized deviation-onset distribution,
hazard-rise shape, checkpoint spacing; policy must INFER an unobserved latent onset). Screened vs 3 anti-patterns
+ NOT metric-validity (headline = a POLICY-COST result, not 'metric over/under-counts'). Thesis: in long-horizon
agentic rollouts whose per-step failure hazard is path-dependent and RISING after a deviation, the token-cost-
optimal recovery is to roll back PAST the last checkpoint to before the inferred deviation onset; a Young/Daly-
style 'restart from most recent checkpoint' (optimal under MEMORYLESS failures) incurs >=25% more expected wasted
tokens (restarting inside a still-elevated-hazard region re-fails at high rate); the penalty grows monotonically
with hazard-rise steepness alpha and is ZERO when memoryless (alpha=0 = calibration control). Anti-circular: GT =
true latent deviation-onset + hazard process (simulator-known, policy-hidden); tested signal = policy observable
(only step failure events + checkpoint positions, via a noisy detector w/ calibrated FPR/FNR or fixed overshoot).
Honest-negative (informative): if alpha=0 penalty~0 (must hold) BUT realistic alpha>0 penalty stays <25% or not
monotone in alpha, FALSIFIED -> 'HPC restart already near-optimal for agents' (useful for framework designers).
PRIOR-ART: HPC ckpt theory (Young1974/Daly2006/Benoit2024) assumes MEMORYLESS, optimizes INTERVAL not recovery
DEPTH; agent-drift (2602.19008/2502.05227/2509.02360) establishes rising hazard but never -> rollback-depth cost;
agent rollback (2503.11951 SagaLLM transactional, 2604.09718 rerun cost) never derives cost-optimal DEPTH under
rising hazard. Delta = first to show memoryless-optimal restart is wasteful precisely in the path-dependent-rising
regime + optimal depth must OVERSHOOT the last checkpoint.
