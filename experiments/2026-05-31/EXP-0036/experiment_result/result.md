# EXP-0036 Result — Cross-project probe (PROJ-0003 harness-routing → PROJ-0002 inj/seq) = KILL

**Agent:** researcher-0002-adjacent2 · **Project:** PROJ-0002 · **Claim:** none (new-idea probe, NOT
bound to CLAIM-0006, per BUG-25) · **Level 1, CPU-only, deterministic (seed 20260531), ~2s, <50MB.**
NO GPU/torch/CUDA/model CLIs/memory probes.

## Cross-project hypothesis tested
PROJ-0003's durable survivor is a harness-agnostic GATE TAXONOMY (REDIRECTABLE/GRANT-REQUIRED/TRANSIENT)
and the finding that recovery MODALITY is a low-dim routing/config fact. A redirectable gate, when hit,
makes a redirect-heavy harness INJECT a sanctioned-alternative result into the prefix (extra injection);
an abandon-heavy harness TRUNCATES (no injection). Conjecture: the inj/seq stream EXP-0005 treats as
i.i.d. tool draws is partly ENDOGENOUS to harness recovery-routing, so redirect-heavy vs abandon-heavy
harnesses might generate DIFFERENT prefix-invalidation patterns — a genuinely new "WHEN does invalidation
happen" axis on top of CLAIM-0006's "how much does it cost" cost-map.

## Pre-registered kill test
Sweep redirect_share ∈ [0,1] (the PROJ-0003 reactive-redirect-share axis). PASS (new axis) only if a
win-region metric escapes the EXP-0015 4×4 prior-sweep envelope: count-frac win1 (inj/seq≤1%) ∈
[0.175,0.408]; win1|S≥50k ∈ [0.411,0.520]. Otherwise it is just another point inside the existing
workload-prior envelope → COLLAPSES onto EXP-0005/0015 → KILL.

## Result
Headline sweep DID escape the floor (win1 0.139 at redirect_share=0, win1_bigctx 0.364) → naive verdict
"PASS-NEW-AXIS". **But the mechanism-discrimination control (CONTROL-A) is the kill:**

| config | win1 (inj/seq≤1%) | win1\|S≥50k | inside EXP-0015? |
|---|---|---|---|
| headline rs=0 (abandon = TRUNCATE loop) | 0.139 | 0.364 | escapes floor |
| headline rs=1 (redirect-heavy) | 0.297 | 0.468 | inside |
| **CONTROL-A rs=0 (abandon, NO truncation)** | **0.315** | 0.479 | **INSIDE** |
| **CONTROL-A rs=0.5** | **0.308** | 0.474 | **INSIDE** |
| **CONTROL-A rs=1.0** | **0.302** | 0.472 | **INSIDE** |

**CONTROL-A removes trajectory truncation (gate hit → skip injection but CONTINUE loop), isolating the
routing-MODALITY from trajectory length.** With truncation removed, the redirect_share axis is essentially
FLAT (0.315→0.302 across the full 0→1 sweep) and stays ENTIRELY INSIDE the EXP-0015 prior envelope.

## Interpretation → KILL
The only reason the headline probe escaped the envelope was **trajectory truncation**: abandon-heavy
harnesses end loops earlier → less context accumulation → smaller S → fewer (small-inj / large-S) wins.
That is EXACTLY the context-accumulation / trajectory-length axis EXP-0005 ALREADY swept (its "no
accumulation" sensitivity = 6.3%, even more extreme than 0.139). The harness recovery-routing does NOT
introduce a NEW structural driver of prefix-cache invalidation; it reduces to **trajectory length** (an
EXP-0005 input) ∘ the **redirect-result size profile** (a tool-mix prior, an EXP-0015 sweep input). The
routing MODALITY per se, held at fixed trajectory length, moves the win-region negligibly (<1.5pp).

So the cross-project angle **collapses onto CLAIM-0006's cost-map ∘ a workload-distribution = the
EXP-0005/0015 territory** — the exact reduction the lane mandate flagged as a kill condition. Honest
fast KILL.

## Files
- impl/exp0036_harness_routing_probe.py
- experiment_result/results.json (headline sweep)
- experiment_result/control.json (CONTROL-A no-truncation + CONTROL-B dump-alt)
