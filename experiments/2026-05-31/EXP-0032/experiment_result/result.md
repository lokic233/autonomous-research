# EXP-0032 — GATE-2 confound ablation for CLAIM-0011 (tool-inventory-overlap + error-message-naming)

**Claim under test:** CLAIM-0011 — "recovery MODALITY is set by HARNESS ROUTING, not error-class/model-reasoning."
**Gate:** VERDICT-0038 GATE-2 (CPU-DOABLE). **CPU/stdlib-only.** Agent: researcher-0011-gate2.
**Corpora (REAL, on-node):** ~/.claude/projects (187 jsonl), ~/.codex/sessions (91 jsonl), ~/.gemini/tmp (64 json).

## The two confounds (from the committee, VERDICT-0038)
- **(a) PROMPT/ERROR-MESSAGE confound:** maybe modality is driven by whether the block ERROR names an
  in-inventory alternative ("did you mean X?"), not the routing table.
- **(b) TOOL-INVENTORY-OVERLAP confound:** maybe Codex "abandons" only because no in-inventory redirect
  TWIN exists, while CC/Gemini have one.

## Method
For each harness's REDIRECTABLE block I extracted (1) the exact block error text, (2) whether an in-inventory
sanctioned twin exists AND is used in the corpus, and (3) the in-thread redirect behaviour under two
definitions: a STRICT reactive-redirect (twin appears in K=6 AFTER the block and NOT before) and the LENIENT
any-after-window definition (twin anywhere in the K=6 window after the block — the EXP-0009/0031 definition).

## FINDING 1 — exact block error messages (error-message-naming check)
| harness | blocked tool | exact block error | names in-inventory alt? |
|---|---|---|---|
| Claude Code | WebFetch | `Internet mode is not enabled (https://fburl.com/claude.code.internet.mode)` | **NO** |
| Codex | knowledge_load (URL) | `Input filtering is enabled... External webpage access is not permitted... (Have you tried Claude Code with Internet? ...)` | **NO** (names a *different harness*, not a tool) |
| Gemini | run_shell_command | `Tool "run_shell_command" not found. Did you mean one of: "grep_search", "replace", "cli_help"?` | **YES** |

## FINDING 2 — tool-inventory-overlap metric (twin availability)
| harness | in-inventory twin | twin available in block-sessions | twin corpus usage |
|---|---|---|---|
| CC | WebSearch + three_pai_external_web_search | **20/20 (100%)** | heavily used |
| Codex | three_pai_external_web_search | **41/41 (100%)** | 442 calls in corpus |
| Gemini | grep_search/glob/replace | **7/7 (100%)** | used |

**An available sanctioned twin EXISTS in 100% of block-sessions for ALL THREE harnesses — including Codex
(442 web_search calls).** Twin-availability is therefore CONSTANT across harnesses and CANNOT explain the
modality difference.

## FINDING 3 — in-thread redirect behaviour (uniform definitions, this corpus snapshot)
| harness | blocks | STRICT reactive-redirect (after-not-before) | LENIENT any-after-window |
|---|---|---|---|
| CC | 43 | 2/43 = 0.047 [0.013,0.155] | **40/43 = 0.930** |
| Codex | 152 | 0/152 = 0.000 [0.000,0.025] | 14/152 = 0.092 |
| Gemini | 9 | 6/9 = 0.667 [0.354,0.879] | 6/9 = 0.667 |

(Codex: all 152 blocks have web_search used BEFORE the block — preemptive/parallel — and 0 as a genuine
reactive in-thread redirect, reproducing the prior 0/142 figure.)

## VERDICT ON THE CONFOUNDS

### Confound (b) TOOL-INVENTORY-OVERLAP: **REFUTED (supports routing).**
Codex has a fully-available in-inventory web twin (three_pai_external_web_search, 442 calls, present in 41/41
block-sessions) and STILL produces 0 reactive in-thread redirects from the knowledge_load block. Codex does
NOT abandon "because no twin exists" — the twin exists and is used heavily, just never as a reactive redirect
off the block. Twin-availability is constant (100%) across all three harnesses, so it cannot drive the modality
difference. This confound is DISCHARGED. (supports CLAIM-0011)

### Confound (a) ERROR-MESSAGE-NAMING: **PARTIALLY LIVE — honest caveat.**
The strict reactive-redirect rate tracks error-message-naming almost perfectly: Gemini's error NAMES an
in-inventory alternative and has the highest reactive redirect (0.667); CC and Codex errors do NOT name an
in-inventory tool and have near-zero strict reactive redirect (0.047, 0.000). So at the STRICT level the
prompt-confound is LIVE and CANNOT be excluded — modality may be partly prompt-driven.
HOWEVER: under the lenient any-after-window definition (the one CLAIM-0011's 66/66 used) the CC-vs-Codex gap
is large and ROBUST (0.930 vs 0.092) even though NEITHER error names a tool — so a harness difference exists
that is NOT explained by error-message-naming. The mechanism, on inspection, is PREEMPTIVE PARALLEL twin-firing:
CC fires WebFetch + the web twin together in the same batch (so the twin is always "near" the block), whereas
Codex isolates knowledge_load. That preempt-vs-isolate pattern is itself a routing/harness fact, not an
error-text fact — supporting CLAIM-0011 — but it is NOT the clean "in-thread reactive redirect" the claim
advertises.

## HONEST CRUX
- Inventory-overlap confound: DISCHARGED (Codex has+uses an available twin yet still 0 reactive redirect).
- Error-message-naming confound: NOT fully discharged. At strict definition, redirect rate co-varies with
  whether the error names an alternative (Gemini high, CC/Codex low). The CC-vs-Codex harness gap survives
  (lenient 0.93 vs 0.09) and is NOT prompt-explained, but it reflects preempt-vs-isolate routing, not
  reactive in-thread redirect.
- IMPORTANT correction to EXP-0031: under a UNIFORM strict definition applied to all 3 corpora on THIS
  snapshot, CC's redirect collapses to 2/43; the headline "66/66" appears to count preemptive/parallel twin
  usage (any-after-window). CC and Codex are more SIMILAR than EXP-0031 claimed when the recovery definition
  is held constant.

## EFFECT: **WEAKEN** (qualified)
One confound discharged (inventory), one not fully discharged (error-naming co-varies with redirect; and the
strict-definition reanalysis shrinks CC's redirect signal and narrows the CC-vs-Codex gap). The routing thesis
SURVIVES as "preempt-vs-isolate is a harness fact independent of error text," but the clean
"in-thread reactive redirect = routing" framing does NOT survive a uniform definition. Net: WEAKEN — the claim
needs to be RESTATED around preempt-vs-isolate routing and the strict reactive-redirect numbers, and GATE-2 is
only PARTIALLY passed.

## CAVEATS
- Single corpus snapshot; counts differ from EXP-0031 (corpus drift + recovery-definition difference).
- Gemini n=9 blocks (small). Codex/CC larger.
- Window K=6; "reactive vs preempt" is a heuristic on call ordering, not a parse of model intent.
