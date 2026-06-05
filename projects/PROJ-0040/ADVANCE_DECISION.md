# PROJ-0040 / CLAIM-0070 — ORCHESTRATOR ADVANCE DECISION (r10-001, 2026-06-05)

VERDICT-0068: committee#1 YELLOW (6/6, no RED). The cross-language ABI-boundary arm cleared the folklore gate from RED;
defensible kernel; 4 unrebutted concerns block GREEN, but the gating ones are CHEAP + DECISIVE.

DECISION: ADVANCE to a CHEAP decisive L1 (RE-1 + RE-3 FIRST), not converge.

RATIONALE (brain lesson cheap-decisive-L1-FIRST: when a yellow gates on cheap doc-reads that determine the claim's
altitude, run them BEFORE the expensive arm):
- RE-1 (WASI preview1 random_get entropy contract — ONE doc read) is the single most load-bearing question: if the WASI
  spec MANDATES CSPRNG-quality entropy, wazero's default is a SPEC VIOLATION (strong, genuinely novel framing); if the
  spec is silent/permits deterministic, 'demotion' is editorial -> weakens materially. This single read flips the claim's
  altitude.
- RE-3 (Wasmtime WasiCtxBuilder secure_random + Wasmer WASI defaults — TWO doc reads): systems_reviewer already surfaced
  Wasmtime defaults to per-context secure_random. If wazero is the ANOMALY among major runtimes, that's a strong
  cross-runtime differential (genuinely surprising, publishable); if all runtimes default deterministic, it shrinks to a
  doc gap.
- These 3 doc-reads GATE whether the expensive RE-2 prevalence scan is worth running -- exactly the cost-aware staging
  the committee recommended. The cross-language ABI delta is real + unrebutted; downstream practitioners (CrowdSec PR#4495,
  wetware issue#106) independently hit+fixed it -> the hazard is real, the question is its altitude.
- High EV: 3 cheap reads can either (a) elevate to a spec-violation + cross-runtime-anomaly claim worth the full L1
  (prevalence + blast-radius + responsible-disclosure) -> a real second-green shot, or (b) honestly settle it to a
  documentation-quality YELLOW-terminal at near-zero cost. Either way the cheap gate is the right next move.

L1 SCOPE (EXP, the cheap gates first): RE-1 WASI spec citation; RE-3 Wasmtime+Wasmer default comparison; RE-4 quote the
config.go doc strings + show no surface warns the compound effect; cite SWC-120/CWE-330/338 + CrowdSec PR#4495 + wetware
issue#106. ONLY if RE-1=CSPRNG-mandate AND RE-3=wazero-anomalous -> proceed to RE-2 prevalence scan (the expensive arm).
Researcher = researcher-0070 respawned (persistent seeder, AWAIT on this L1).
