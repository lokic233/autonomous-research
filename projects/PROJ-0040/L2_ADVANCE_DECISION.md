# PROJ-0040 / CLAIM-0070 — ORCHESTRATOR L2-ADVANCE DECISION (r10-001, 2026-06-05)
VERDICT-0069: committee#2 (green gate) YELLOW-advance (6/6, no RED). Genuine synthesis-altitude finding (NOT folklore/killed);
L1 resolved committee#1's decisive gates (RE-1 CSPRNG-contract, RE-3 wazero-anomalous). 3 convergent caps prevent GREEN;
committee defined a concrete L2 path. DECISION: ADVANCE to L2 (the committee says GREEN is REACHABLE if L2 lands).
L2 DELIVERABLES (gate GREEN): (a) AUTHENTICATED AST prevalence scan (bare NewModuleConfig() vs WithRandSource-overridden
across top Go wazero-importers, WITH denominator + CI + blast-radius) — needs a GitHub token/gh auth (RE-2 was auth-gated);
(b) preview1-vs-successor spec-violation disambiguation (is preview1 high-quality+blocking a CSPRNG normative requirement?);
(c) GUEST-SIDE DEFENSIBILITY test (CAN a guest detect/reject a deterministic host source? if yes the 'un-defendable' arm
weakens); (d) Node.js(V8) WASI random_get baseline + wazero version-trajectory (post-1.12.0 default change?); (e) reposition
contribution as CONFORMANCE-SYNTHESIS against the practitioner find-fix set (CrowdSec PR#4495/wetware#106/wapc-go/wazero#620).
If L2 shows non-trivial UNMITIGATED prevalence AND guest-defensibility confirms un-defendable -> GREEN reachable.
HANDOFF: this is advance-pending-L2; r11 spawns the L2 researcher (needs a GitHub token for the prevalence scan — flag to dengcchi if unavailable).
