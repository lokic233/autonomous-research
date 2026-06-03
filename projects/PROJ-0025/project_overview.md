# PROJ-0025 — Eval-and-safety ∩ agentic: constrained-decoding SUPPORT-REMOVAL MISROUTE — schema-valid silent errors no validity-check AND no faithful decoder can recover (EMPIRICAL PHENOMENON)
Fresh area: eval-and-safety ∩ agentic-systems (hard grammar-constrained decoding for tool routing; silent-error
monitorability). BEST-POSITIONED claim of the run for a green — first to CLEANLY clear the killer-#9 mechanism-novelty
bar. THESIS: in agentic tool routing with HARD grammar-constrained decoding over an enum of valid actions, when a
request's correct action is NOT in the enum (out-of-set intent, routine in open-world deployment), the decoder does
NOT error/abstain — it mechanically forces the NEAREST in-enum member = 100pct-schema-valid, confidently-wrong action.
Silent-misroute rate RISES as enum cardinality K falls AND as the semantic gap to the nearest in-enum neighbor shrinks
(a near-miss distractor is MORE dangerous than a far one). This failure class has ZERO recall under the standard
mitigation (schema-validate+retry — validity is 100pct by construction) AND is NOT recoverable by the strongest
distribution-faithful decoder (Grammar-Aligned Decoding, GAD), because it's SUPPORT-REMOVAL (true target has zero
grammar support) not within-support distortion (all GAD repairs). Even the strongest mitigation (an explicit
'other'/ASK_USER escape-hatch enum member) has escape-recall that DECREASES as the nearest wrong member gets
semantically closer -> leaks at the dangerous near-miss params. Passes all 9 killers incl #9: the core mechanism
(support-removal monitorability collapse + the (K, neighbor-gap) law) is NOT a named classical result, and the seminal
incumbent GAD (Park/Geng NeurIPS2024 2405.21047) EXPLICITLY assumes desired output is in-language -> silent on
zero-support -> does NOT acknowledge it. Tests the STRONGEST decoder (GAD-style faithful resampling) as Baseline B
(not a lexical strawman) + both standard mitigations. Anti-circular: GT = true target action + in-enum-or-not (harness-
owned); monitor sees only the emitted token + schema-validity bit, NEVER the GT label. Anchored structurally (K,
neighbor-gap), not on assumed traffic. ORCHESTRATOR GUARDS: (1) anti-tuned-knob — derive K-dependence from a FIXED
similarity kernel + report robustness across kernel temps/noise (don't manufacture the cardinality effect); (2) keep
the escape-hatch claim SCOPED to the proximity-dependence curve (escape-recall DECREASES with proximity), NOT 'escape
hatch useless'. Honest-negative (informative): if misroute-rate flat in K/neighbor-gap, OR GAD recovers the gap, OR
escape-recall is high+proximity-INDEPENDENT -> falsified. PRIOR-ART: GAD (2405.21047, seminal distribution-distortion,
within-support only); 'Wait that's not an option' (2409.00113, UNconstrained MCQ, model CAN say none); abstention lit
(Know-Your-Limits TACL2024, model CHOOSES to abstain — constrained decoding REMOVES the choice); structured-output-
impact (2509.21791, avg reasoning deltas not zero-support coercion). Delta = isolate support-removal coercion as a
distinct GAD-irrecoverable failure class + its (K x neighbor-gap) law + the monitorability collapse (validity-recall=0,
escape-recall decreasing in proximity). L1: real LMs (Llama-3.1-8B/Qwen2.5-7B) + real constrained backend (Outlines/
XGrammar/vLLM guided JSON) on a BFCL/ToolBench slice augmented w/ held-out out-of-set requests -> misroute-rate vs K
+ vs embedding-distance, validity-monitor recall (~0), GAD/ASAp gap-recovery (~0 for out-of-set), escape-hatch recall
vs distractor proximity.
