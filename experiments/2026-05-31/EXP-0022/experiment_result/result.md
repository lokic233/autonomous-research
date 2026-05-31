# EXP-0022 RESULT — CLAIM-0010 two-layer decomposition (researcher-0003-laneC; session errored AFTER completing the analysis. Numbers are the researcher's own computed output; orchestrator transcribed + added the researcher's LOCO + leak-check findings from its final report.)

**Corpus:** 79 sessions / 3,547 calls / 375 failures (~/.claude/projects). **Source:** run_stdout.txt + per_gate.csv + layer_decomposition.csv + context_ablation.csv (all written by researcher-0003-laneC).

## Q1 — Layer separation (does the two-layer structure hold?)
- COARSE (modality | gate-type): Theil U = 0.381; global modality norm-entropy 1.000 -> given-gate 0.619. REDIRECTABLE modality is FULLY deterministic (normH=0.000, 68/68 CROSS_TOOL_REDIRECT); GRANT_REQUIRED normH=0.629 (16/19 same-tool); TRANSIENT normH=0.906 (mixed).
- FINE (next-tool | gate-type): Theil U = 0.135; per-gate tool norm-entropy stays HIGH (REDIRECTABLE 0.722, GRANT_REQUIRED 0.775, TRANSIENT 0.740; bootstrap CI [0.718,0.789]).
- CONTRAST: U_modality(0.381) >> U_tool(0.135) AND fine residual entropy high (0.74) -> the two-layer split QUALITATIVELY HOLDS (coarse gate-determined, fine high-entropy).

## Q2 — Fine-layer adaptivity (is fine tool-choice "adaptive" or a learnable table?)
LOO context-model vs within-gate modal baseline:
| gate | n | modal-baseline LOO-acc | context-model LOO-acc | lift |
|---|---|---|---|---|
| REDIRECTABLE | 111 | 0.396 | 0.586 | +0.189 |
| GRANT_REQUIRED | 37 | 0.432 | 0.541 | +0.108 |
| TRANSIENT | 227 | 0.357 | 0.445 | +0.088 |
- Context (prior tools + error keywords) DOES add signal in every gate (+0.09 to +0.19) -> the fine tool-choice is NOT purely free/adaptive: a LEARNABLE context->tool mapping exists. It leans toward a CONTEXT-CONDITIONED routing table, not unconstrained reasoning.

## HONEST VERDICT: PARTIAL SUPPORT / NUANCE for CLAIM-0010
The two-layer STRUCTURE holds (coarse gate-type strongly determines modality U=0.381 with REDIRECTABLE fully deterministic; fine tool-choice is high-entropy 0.74). BUT the "fine layer is ADAPTIVE (a decision, not a table lookup)" framing is OVERSTATED: the fine layer is partially context-PREDICTABLE (LOO lift +0.09..+0.19 over modal). More accurate: COARSE = deterministic gate-type table; FINE = a CONTEXT-CONDITIONED (learnable) tool selection that is higher-entropy than the coarse layer but NOT free/adaptive. Single-harness (Claude Code) caveat applies. WEAKENS the strong "adaptive" claim; SUPPORTS the two-LAYER (coarse-deterministic / fine-higher-entropy-but-learnable) structure.


## ADDITIONAL findings from researcher-0003-laneC's final analysis (not to be lost)
- **COARSE-layer determinism is CARRIED BY web_disabled (LOCO):** dropping the REDIRECTABLE/web_disabled class
  collapses Theil U(modality|gate) from 0.381 -> 0.034. So the "coarse layer is deterministic" result is almost
  entirely the one definitional REDIRECTABLE cell (consistent with EXP-0012/0020 findings). The coarse layer is
  only PARTIALLY deterministic; GRANT_REQUIRED (U-residual normH 0.629) and TRANSIENT (0.906) are NOT.
- **Fine-layer context-lift is NOT a same-tool-retry LEAK (decisive ablation, context_ablation.csv):** dropping
  the failed_tool feature, REDIRECTABLE context-model still 0.550 vs base 0.396 — the lift survives. And
  cls_only_acc == base_modal_acc exactly (error-class adds nothing WITHIN a gate, since gate ~= class-cluster).
  The genuine predictive signal comes from ERROR-TEXT KEYWORDS + PRIOR TOOL, not class or same-tool mechanics.
- **Net characterization:** the fine layer is neither a fixed table NOR pure adaptivity — it is an INTERMEDIATE
  "context-conditioned, high-residual-entropy" layer: predictable to ~0.55-0.59 in REDIRECTABLE (caps there;
  ~41% genuinely situation-dependent), residual entropy stays ~0.74.
