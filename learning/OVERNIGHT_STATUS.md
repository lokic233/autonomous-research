# OVERNIGHT STATUS — orchestrator-r2-001 (research-os round 2)
Generated 2026-05-31. Engine: research-os@473231e (BUG-22 fixed). Pushed to lokic233/autonomous-research main.
All CPU-doable work DISCHARGED; remaining work is GPU/human-gated. Clean park. `ros resume` picks up exactly here.

## WHAT ADVANCED (experiment-driven, every verdict cites experiments; Rule-3 map+prior-art merged)
### CLAIM-0006 (PROJ-0002, prefix-cache invalidation cost-map) — strongest claim, 1 gate from GREEN
- 3 real 6/6 committee YELLOW verdicts (VERDICT-0017/0022 + supporting evidence-updates 0014/0023).
- NOVELTY GATE-A FULLY CLOSED (10/10 neighbors body-verified distinct, ZERO inj/seq cost-map collision):
  "Don't Break the Cache" 2601.06007, Irminsul 2605.05696 (now 2-indexed twin), EPIC/CacheBlend/Cache-Craft/
  MEPIC/KVFlow/CacheClip, ContiguousKV 2601.13631, variable-block 2604.23994 — all body-read, "injection" 0x.
- EXP-0006: CDC's headline 8x-465x advantage = STRUCTURAL ARTIFACT of strawman contiguous baselines; vs a
  FAIR PIC baseline it collapses to median 1.77x [1.56,1.87], tie 1.29x [1.25,1.33] at inj/seq>=5%.
- EXP-0013 (stats pass): slope~1 is CDC-mechanism-specific (0.958 [0.937,0.980] R2=0.972, accounting identity)
  NOT a cross-engine law (vLLM-APC/Radix/FlashInfer R2=0.0007, position-driven). Engine-averaged slope~1 = artifact.
- SURVIVING CONTRIBUTION: the workload-conditioned WIN-REGION locating real agentic traffic on CDC's accounting
  line (win-region inj/seq<=1% = 100% Wilson[0.972,1.0]; median real inj/seq~2.8%, CDC-wins ~25%, ~46% at S>=50k).
  Honest characterization + negative result. Mechanism conceded non-novel.

### CLAIM-0009 (PROJ-0003, recovery MODALITY) — real 6/6, honestly narrowed to a config-fact
- Re-seeded from the refuted CLAIM-0008. Real 6/6 YELLOW (VERDICT-0020) + ablation (VERDICT-0021, EXP-0012).
- The committee caught (and EXP-0012 data-CONFIRMED) a predictor-misattribution: error-class & gate-type are
  COLINEAR; error-class adds <=0.2% over a single gate-type bit (lift -0.0043 out-of-sample); ablating the
  definitional web_disabled cell collapses LOO-Brier +40.1%->+2.2%; leave-one-CLASS-out -33%.
- SURVIVING: a gate-type+harness-routing CHARACTERIZATION (config fact: redirectable-hard-block vs
  grant-required vs transient). error-class-prediction framing RETIRED (observationally inseparable single-harness).

### CLOSED (clean negative results)
- CLAIM-0005 (PROJ-0001, super-quadratic injection): DONE. EXP-0010 — k is sub-quadratic AND drifts 1.0->2.0
  with context (regime-local crossover slope, Pope/Kwon-derivable), NOT a law. Sub-hypothesis buried DEAD-0009.
- CLAIM-0008 (PROJ-0003, error-class->recovery OCCURRENCE): DONE. EXP-0008 refuted it (signal washes out under
  workaround scoring). Surviving kernel re-seeded as CLAIM-0009.

## BLOCKED-ON-HUMAN (parked with resume recipes in ros resume next_action)
- CLAIM-0006 gate-B: GPU wall-clock TTFT on a REAL PIC artifact (CacheBlend/EPIC) across the inj/seq surface at
  the ~5% crossover. The ONLY remaining GREEN-blocker. Dispatch via `ros exp dispatch` on devgpu014 H100 (NOT
  fragile devgpu499; host-mem-floor watchdog). INVARIANT 3 — needs human go.
- CLAIM-0009: 4 non-CPU gates — (1) live >=2-source self-healing/error-recovery-trace prior-art sweep
  [web-search was permission-blocked on this node]; (2) a sampled cleanly-TERMINAL error class n>=10
  [corpus under-samples it]; (3) cross-harness replication [need a 2nd non-Claude-Code agent-trace corpus];
  (4) interventional routing-alteration [need harness control].

## OPEN-CPU (none remaining)
All CPU-doable required-evidence across all claims is discharged. No further CPU experiment advances any
in-flight claim without new data/harness or GPU.

## ENGINE BUGS (this round; full detail in ENGINE_BUGLOG_orchestrator-r2-001.md)
- FIXED+verified by driver: BUG-10 (atomic writes), BUG-16 (chair-last), BUG-18 (idempotent verdicts),
  BUG-19/20/20b (sandbox+concurrency), BUG-21 (completion gate), BUG-22 (gemini stdin-drain), BUG-23 (ros exp gc).
- Re-tested TODO carryover: BUG-2 CLOSED, BUG-3 holds, BUG-7 holds, BUG-4 data-fixed (engine-validator gap stands),
  BUG-6 mitigated (retry-backoff), BUG-1 partial.
- NEW still-open (low/medium): BUG-15 (claim map/baseline migration leak — engine validator gap), BUG-17
  (verdict ';' separator naive split), BUG-24 (ros exp gc races active researchers — needs age/owner guard;
  I un-retired EXP-0013 after gc reaped it mid-flight).

## TALLY
9 claims (5 promoted [pre-existing], 4 weakened: 0005/0008 done-negative, 0006/0009 parked-for-human),
25 experiments, 21 verdicts (3 real 6/6 committee this round: VERDICT-0017/0020/0022; rest evidence-updates/migrated),
9 cemetery. Never fabricated a vote. Every advancing claim has a real 6/6 committee verdict.
