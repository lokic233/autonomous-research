# PRE-REGISTRATION — EXP-0085 (CLAIM-0070, PROJ-0040) — L1 CHEAP-DECISIVE
Author: researcher-0070 | parent: orchestrator-r10-001 | 2026-06-05 | Node: cli:dengcchi-mac

## OBJECTIVE
Resolve the 4 required-evidence items from committee#1 (YELLOW, 6/6, no RED). RE-1 + RE-3 + RE-4
are cheap doc-reads that DETERMINE the claim's ALTITUDE (spec-violation vs documented-design-choice)
and GATE whether the expensive RE-2 prevalence scan is worth running.

## EXECUTION ORDER (cheap-first, gated)
1. RE-1 (DECISIVE): Read the ACTUAL WASI preview1 `random_get` spec text (witx/docs). Quote verbatim.
   - Q: Does the spec MANDATE cryptographic-quality entropy?
2. RE-3 (cheap): Compare Wasmtime + Wasmer DEFAULT WASI random_get + clock behavior. Is wazero anomalous?
3. RE-4 (cheap): Quote wazero v1.12.0 config.go doc strings for WithRandSource/WithSysWalltime/
   WithSysNanotime/WithSysNanosleep. Show no single doc/example warns the COMPOUND effect.
4. PRIOR-ART positioning: SWC-120, CWE-330/338, CrowdSec PR#4495, wetware/pkg #106.
5. RE-2 (EXPENSIVE) — RUN ONLY IF RE-1=CSPRNG-mandate AND RE-3=wazero-anomalous. Else SKIP.

## PRE-REGISTERED DECISION RULE (elevate-or-converge)
- RE-1 = CSPRNG-mandate AND RE-3 = wazero-anomalous  -> ELEVATE. (proceed to RE-2)
    - RE-2 >5% mature dependents bare-default -> SUPPORT -> committee#2 (green shot). Do NOT self-converge.
    - RE-2 ~0% -> YELLOW, scoped: real spec-violation but synthetic prevalence.
- RE-1 = no-mandate / spec-silent / permits-deterministic AND RE-3 = ecosystem-normal -> WEAKEN to
    documentation-quality (honest). SKIP RE-2. May converge.
- Mixed (one elevates, one doesn't) -> honest YELLOW with precise scope. SKIP RE-2.

## FALSIFIABILITY / HONEST-NEGATIVE BRANCH
A finding that WEAKENS the claim (spec silent / all runtimes deterministic) is a WIN if true.
RE-1 is one doc read that can break the claim. Report what the spec ACTUALLY says, verbatim.
