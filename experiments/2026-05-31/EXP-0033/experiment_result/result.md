# EXP-0033 — ERROR-MESSAGE-NAMING confound discharge/confirm for CLAIM-0011

**Claim under test:** CLAIM-0011 (RESTATED) — "PREEMPT-vs-ISOLATE is a harness regime independent of error TEXT."
**Gate:** the ONE confound GATE-2 (EXP-0032) left LIVE — recovery modality co-varies with whether the block
error NAMES an in-inventory alternative (only Gemini's error does).
**CPU/stdlib-only.** Agent: researcher-0011-errname. Corpora on-node: ~/.claude/projects (84 sess w/ calls),
~/.codex/sessions (67), ~/.gemini/tmp (18).
**Impl:** `impl/errname_confound.py` (T1/T2/T3), `impl/twin_distance.py` (preempt-distance),
`impl/codex_dedup_reconcile.py` (Codex double-log reconciliation). **CSV:** `results/errname_metrics.csv`.

## Corrected operationalization of "names an in-inventory alternative"
EXP-0032's loose reading mislabels things. The confound is specifically: *does the error name, by name,
a tool that EXISTS in THIS harness's own inventory?* Built per-harness inventories from the corpora and
matched error-text tokens (quoted tokens + "did you mean X,Y,Z" lists) against them:
- **CC** WebFetch block = `Internet mode is not enabled` → names NO in-inventory tool.
- **Codex** knowledge_load block = `Input filtering... Have you tried Claude Code with Internet?` → names a
  DIFFERENT HARNESS, NOT an in-inventory tool → counts as NO.
- **Gemini** run_shell_command block = `not found. Did you mean "grep_search","replace","cli_help"?` → names
  in-inventory tools → YES.
So at the canonical-block level, naming is **perfectly confounded with harness** (CC 0/43 named, Codex
0/152 named, Gemini 9/9 named). That is exactly why the confound was flagged LIVE.

## CRITICAL DATA CORRECTION (reconciliation with EXP-0032)
Codex logs every tool call TWICE (`function_call` + `mcp_tool_call_end`). EXP-0032's headline merged both →
double-counted (304). Using the canonical `function_call` stream (= EXP-0032's own `codex()` = **152 blocks**):
the web twin (`three_pai_external_web_search`) fires in the K=6 window **BEFORE** the knowledge_load block in
**152/152** cases. So Codex's modality is **PREEMPT (100%)**, NOT "abandon/isolate." EXP-0032's prose called
Codex "abandon+preempt/isolate"; the data (incl. EXP-0032's own function) shows **pure preempt**, with the
twin median 3 calls before the block (sample distances mostly 1).

## T1 — WITHIN-HARNESS naming test (generic cross-tool reactive redirect, split by names-in-inv-tool)
| harness | errors-NAMED (n) | reactive-share | errors-UNNAMED (n) | reactive-share |
|---|---|---|---|---|
| CC | 0 | — | 388 | 0.021 [0.010,0.040] |
| Codex | 0 | — | 248 | 0.081 [0.053,0.121] |
| Gemini | 9 | 0.222 [0.063,0.547] | 51 | 0.157 [0.082,0.280] |

**Result:** CC and Codex have ZERO within-harness naming variance (no error names an in-inventory tool), so a
clean within-harness naming-vs-not contrast is **not estimable** there. The ONLY harness with both buckets is
Gemini: named 0.222 vs unnamed 0.157 — **CIs overlap heavily; naming does NOT significantly predict redirect
within Gemini**. This is weak evidence AGAINST naming being the driver, but n=9 named is tiny.

## T2 — PREEMPT-vs-ISOLATE among UNNAMED canonical blocks (K=6, deduped)
| harness | blocks | named | unnamed | reactive | preempt | abandon | preempt-share | reactive-share |
|---|---|---|---|---|---|---|---|---|
| CC | 43 | 0 | 43 | 5 | 34 | 4 | 0.791 [0.648,0.886] | 0.116 [0.051,0.245] |
| Codex | 152 | 0 | 152 | 0 | 152 | 0 | **1.000 [0.975,1.000]** | 0.000 [0.000,0.025] |
| Gemini | 9 | 9 | 0 | 2 | 7 | 0 | 0.778 | 0.222 |

Both CC and Codex blocks are 100% UNNAMED, so naming is held constant. **The preempt-vs-isolate framing FAILS:
Codex does not ISOLATE — it PREEMPTS at 100%, more reliably than CC (79%).** Twin-distance confirms (CC 41/43
have a preceding twin, median dist 2; Codex 152/152, median dist 3). The supposed "CC-preempt vs Codex-isolate"
harness contrast is an artifact of EXP-0031/0032's recovery-definition + Codex double-log; under a uniform
deduped definition **both harnesses preempt** and Codex shows essentially no reactive redirect (0/152) — the
same near-zero reactive rate as CC (5/43=0.116, CIs touch).

## T3 — LARGER-N (fullest windows, deduped)
- CC: 43 blocks, reactive 0.116 [0.051,0.245], preempt 0.791 [0.648,0.886]
- Codex: 152 blocks, reactive 0.000 [0.000,0.025], preempt 1.000 [0.975,1.000]
- Gemini: 9 blocks (unchanged small-n), reactive 0.222 [0.063,0.547], preempt 0.778
- Gemini stays at n=9 named blocks — the corpus has no more run_shell_command blocks; the small-n caveat persists.

## VERDICT ON THE ERROR-NAMING CONFOUND
1. **Within-harness naming test: cannot discharge, weak refute.** Naming has ZERO variance within CC and Codex
   (no in-inventory tool is ever named), so the cleanest test is impossible there. Where both buckets exist
   (Gemini) naming does NOT significantly predict redirect (0.222 vs 0.157, overlapping). → The confound is
   neither confirmed nor cleanly discharged; the *only* within-harness signal weakly argues AGAINST it.
2. **Preempt-vs-isolate among UNNAMED blocks: the SURVIVING claim does NOT survive.** Holding naming constant
   (CC and Codex both 100% unnamed), the predicted CC-preempt-vs-Codex-isolate contrast disappears — **both
   preempt** (Codex 100% > CC 79%). The deduped reactive-redirect rates are both near zero and overlapping
   (CC 0.116, Codex 0.000). So even the preempt-vs-isolate regime — the form CLAIM-0011 was restated to — is
   NOT supported by the on-node data once the Codex double-log is fixed.
3. **What IS real and harness-linked:** Gemini alone shows a nonzero in-thread reactive redirect (2/9=0.222),
   and Gemini is the only harness whose error names in-inventory tools. With n=9 this is exactly the
   modality∼naming co-variation that GATE-2 flagged, and it remains **fully confounded** (Gemini = both
   "names a tool" AND "different harness routing"). On-node observation cannot separate them.

## HONEST CRUX (the binding question)
**The harness regime does NOT cleanly survive controlling for error-naming — and worse, the deduped data
removes the preempt-vs-isolate contrast entirely.** Once Codex's double-logging is corrected, CC and Codex
behave the SAME on their (both-unnamed) blocks: heavy preempt, ~0 reactive redirect. The only harness that
genuinely redirects in-thread is Gemini, and that is perfectly confounded with being the only harness whose
error names an in-inventory tool. So on CPU-dischargeable evidence the modality signal is consistent with being
**naming/prompt-driven (Gemini's enumerated alternatives) rather than a routing regime** — which further
WEAKENS CLAIM-0011. The clean separation needs the off-node GATE-1 interventional (same model, two harnesses,
identical error w/ and w/o named alternative).

## EFFECT: WEAKEN
- Error-naming confound: NOT discharged (unestimable within CC/Codex; non-significant within Gemini; perfectly
  confounded at the canonical-block level).
- Preempt-vs-isolate surviving claim: **REFUTED under deduped uniform definition** — Codex preempts 100%, does
  not isolate; CC and Codex reactive rates overlap near zero.
- Net: WEAKEN. The on-node data is consistent with modality being naming/prompt-driven, and the harness
  preempt-vs-isolate regime does not reproduce once Codex's double-log is fixed.

## CAVEATS
- Gemini n=9 named blocks — corpus has no more; small-n unresolved (larger-n attempted, none available).
- "names an in-inventory tool" uses corpus-derived inventories + token matching, not the live tool manifest.
- reactive/preempt is a K=6 call-ordering heuristic, not a parse of model intent.
- Codex double-log correction changes EXP-0031/0032 Codex characterization; flagged for committee.
