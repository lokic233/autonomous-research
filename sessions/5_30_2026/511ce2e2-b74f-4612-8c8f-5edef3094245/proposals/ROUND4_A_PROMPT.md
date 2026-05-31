You are ONE node in a 6-agent HOSTILE research committee (CC4.8, CC4.7, CC4.6, Agent-D,
Codex 5.5, Gemini 3.5). FINAL vote on Thesis A* ONLY. In round 3, A* got 5 GREEN / 1 YELLOW;
the lone holdout (CC4.8) raised TWO specific objections. BOTH have now been addressed with
NEW measurements. Vote A* RED/YELLOW/GREEN on the evidence. Do NOT vote GREEN to be agreeable;
do NOT vote RED by reflex. If you are CC4.8, judge honestly whether your objections are resolved.

ANTI-COPING: promising/novel/impactful/structural FORBIDDEN unless followed by a cited number.

## THESIS A* (final form)
"The NVIDIA CUDA-VMM per-context mapping-metadata ceiling (K≈520K access descriptors) is a
vendor-SPECIFIC portability cliff for branchable/CoW GPU memory — reproducible and forensically
located on NVIDIA, and ABSENT on AMD ROCm in all reachable VA. Any VMM-based KV/branch/CoW
design that scales on AMD can hit a hard wall on NVIDIA at ~520K mappings."
Contribution: cross-vendor characterization + the predictive model max_branches≈K/prefix_pages
(NVIDIA) + forensic root-cause. Venue target: ATC/EuroSys/OSDI.

## CC4.8's round-3 holdout objections AND how they were addressed:

OBJECTION 1 (mechanism): "520K is LOCATED at cuMemSetAccess but not EXPLAINED; single harness;
is it a fixed table, memory-bound, or tunable?"
→ ADDRESSED by E-A2 (independent cuda-python reimplementation, NOT the repo's bench code):
  - Distinct-handle branch regime (real CoW workload: P=512 distinct phys pages aliased across
    branches): ceiling = **523,404 total mappings** (1022 branches × 512) — INDEPENDENTLY
    REPRODUCES the repo's 516K–523K (data/metric4b_ceiling.csv) to within 0.6%. Not a harness
    artifact.
  - Single-shared-handle giant-reservation regime: walls at only **5,637** — a DIFFERENT, lower
    limit. So the ceiling is PATTERN-SENSITIVE: ~520K applies specifically to the distinct-
    prefix-page per-branch-reservation regime real CoW branching uses. This is the mechanism
    granularity asked for: it is a per-context access-descriptor-segment capacity, NOT data/HBM
    (live HBM was 1 GiB at the 523K wall) and NOT the Linux VMA sysctl (Lab 1: 392 VMAs).

OBJECTION 2 (AMD absence un-measured): "AMD 64M was your VA-reserve CAP, not AMD's ceiling —
'absent on AMD' is un-measured."
→ ADDRESSED by E-A1 (TWO independent AMD MI350X runs, chunked VA reservation to push toward a
  real wall):
  - Run 1: 4,000,000 mappings, zero failure.
  - Run 2: 50,000,000 mappings at 191 GiB VA, zero driver failure (96× NVIDIA's 520K) — then the
    unbounded probe thrashed the host and the node went offline (operational limit, not an AMD
    driver ceiling). HONEST CAVEAT: AMD was still not driven to a definitive hipMemSetAccess
    FAILURE; the claim is "no ceiling found in 191 GiB reachable VA across two runs at two scales
    (4M, 50M)", while NVIDIA fails reproducibly at the SAME ~520K across 4 prefix sizes (±1%).

## THE HONEST RESIDUAL (state it, then vote):
- NVIDIA side: SOLID — independently reproduced (523,404), forensically located, regime-
  characterized, predictive model holds (±1%).
- AMD side: divergence DIRECTIONALLY SOLID (two runs, two scales, no wall at 96× NVIDIA) but
  NOT a measured AMD K_ceiling (AMD may enforce none; we hit host limits first).

OUTPUT EXACTLY:
### A* FINAL
- Vote: RED / YELLOW / GREEN
- Are CC4.8's two objections resolved? (obj1 mechanism: yes/no; obj2 AMD absence: yes/no)
- Strongest remaining attack:
- Is the NVIDIA-specific portability-cliff claim GREEN-worthy EVEN IF AMD's exact ceiling stays
  unmeasured? (yes/no + why — this is the crux)
- Venue you'd bet on:
- One-line: what (if anything) is still needed for unconditional GREEN.
