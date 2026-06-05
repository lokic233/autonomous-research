# PRE-REGISTRATION — EXP-0086 (CLAIM-0070, PROJ-0040) — L2 GREEN-GATE
Author: researcher-0070 | parent: orchestrator-r11-001 | level 2 | 2026-06-05
Nodes: cli:dengcchi-mac (engine + spec reads), cli:devvm14382 (build/run/clone/scan)

## CONTEXT
Committee#2 (VERDICT-0069) ruled YELLOW-ADVANCE on CLAIM-0070 (wazero default ModuleConfig
silently demotes a guest's crypto/rand CSPRNG across the WASI ABI + decouples clocks). Genuine
synthesis-altitude finding. GREEN reachable IF the L2 deliverables land. Honest results only.

## DELIVERABLE ORDER (committee#2 L2 set)
1. PREVIEW1-vs-SUCCESSOR spec-violation disambiguation (no auth). Read preview1 normative witx
   prose + WASI errata/discussion; state the strongest defensible per-spec-generation claim.
2. GUEST-SIDE DEFENSIBILITY test (no auth; DECISIVE for 'un-defendable' arm). Build+run a
   Go-WASI (and if feasible Rust) guest under wazero default config: can correct guest code
   DETECT or REJECT the deterministic host random source at runtime (entropy self-test,
   cross-restart repeat detection, capability assertion)? CAN-defend => weaken; CANNOT => holds.
3. NODE.js (V8) WASI baseline + wazero VERSION TRAJECTORY (no auth). Does node:wasi random_get
   default secure (Wasmtime/Wasmer-like) or deterministic (wazero-like)? Does any wazero release
   AFTER v1.12.0 change the fixed-seed default (latest tag changelog/source)?
4. RE-2 AUTHENTICATED PREVALENCE SCAN (NEEDS GitHub auth). Check both nodes for gh/GITHUB_TOKEN.
   IF auth: AST/code-search ratio of bare NewModuleConfig() vs WithRandSource-overridden across
   top Go wazero-importers, WITH denominator + CI. IF NOT: best UNAUTH proxy = clone top ~20-30
   curated wazero-dependents + AST/grep for NewModuleConfig w/o WithRandSource; report as a
   BOUNDED SAMPLE with the scanned denominator (NOT a population estimate), and LOUDLY FLAG
   the auth-blocked full-population scan for orchestrator escalation to dengcchi.
5. Reposition contribution as CONFORMANCE-SYNTHESIS vs the practitioner find-fix set
   (CrowdSec PR#4495, wetware#106, wapc/wapc-go, wazero issue#620) — NOT discovery.

## DISPOSITION RULE (pre-registered; per committee#2)
GREEN reachable IFF ALL hold:
  (P) prevalence shows non-trivial UNMITIGATED bare-default usage, AND
  (D) guest-defensibility confirms the demotion is UN-DEFENDABLE by correct guest code, AND
  (S) spec-violation holds AND cross-runtime anomaly holds INCLUDING Node.js.
- If non-auth deliverables (1,2,3,5) strongly support AND bounded prevalence shows real
  unmitigated usage -> SUPPORT, submit to committee#3 (green shot); flag auth-limited prevalence
  as residual.
- If guests CAN defend, OR Node.js is also deterministic (ecosystem-normal), OR spec-violation
  collapses to preview1-weak, OR prevalence blocked/low -> WEAKEN to synthesis-note altitude,
  converge honestly with precise scope.

## HONEST-NEGATIVE BRANCH
A finding that the hazard is mitigated-in-practice, or guest-defendable, or that the
spec-violation is weak, is a WIN (honest cap). Never fabricate. Negative results are reported
as negative.
