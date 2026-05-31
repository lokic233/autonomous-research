# EXP-0009 — Real-trace recovery-MODALITY census (CLAIM-0009)

**Domain:** MAP-0002 (Agent failure attribution & recovery). **CPU-only, stdlib-only, ~12s.**
**Claim under test:** CLAIM-0009 (seed) — "Error-class predicts agent recovery MODALITY (same-tool-retry
vs cross-tool-redirect), NOT recovery occurrence; failure provenance determines HOW an agent recovers,
conditioned on whether a policy/permission gate is REDIRECTABLE (blocked tool → sanctioned alternative)
vs TERMINAL." CLAIM-0009 is the surviving kernel from EXP-0008, which REFUTED occurrence-prediction
(CLAIM-0008): V 0.644→0.239 (n.s.), LOO-Brier +0.087→~0 once cross-tool workarounds were counted.

## The pivot this experiment tests
EXP-0008 showed error-class does NOT predict *whether* recovery happens once workarounds count. But it
left a sharper hypothesis on the table: error-class predicts *how* the agent recovers. This experiment
tests exactly that — among the failures that DID recover, is the recovery MODALITY (same-tool retry vs
cross-tool redirect) predicted by error-class?

## Data (REAL, same corpus, refreshed)
`~/.claude/projects` Claude Code session logs. After join + <2-call drop: **74 sessions, 3,508 tool calls,
364 ground-truth failures** (`is_error:true`). (EXP-0008 saw 71/3,416/357; the corpus grew slightly.)
`parse_session`/`classify_error`/`intent_class`/`head_cmd`/`block_text` are **copied verbatim** from
EXP-0007/EXP-0008 — identical 17-class taxonomy, identical failure census, identical broad-recovery
machinery. Only the new layer (modality assignment) is added.

## Method — modality label (stated honestly)
1. **Which failures recovered:** reuse EXP-0008's BROAD definition (same-intent retry OR cross-tool
   same-intent-class success within bounded window K=6). 232 / 364 = 0.637 recovered — matches EXP-0008.
2. **Modality of each recovered failure (default precedence: A wins ties):**
   - `SAME_TOOL_RETRY` iff a later SAME-INTENT call succeeded within K (same tool; Bash=same head-cmd;
     file=same path) — EXP-0007's channel A.
   - `CROSS_TOOL_REDIRECT` iff channel A did NOT fire but a DIFFERENT tool of the same intent-class
     succeeded within K (channel B). Redirect is the operative modality only when same-tool retry failed.
   - This **under-counts** redirect (if both fire we call it same-tool) → biases AGAINST the redirectable
     story → a surviving redirect signal is robust. A B-priority tie-break variant is reported as sensitivity.
3. **Tests:** (T1) does error-class predict modality (Cramér's V + 5000-shuffle permutation vs the
   modality-agnostic NULL = global redirect rate among recovered; honest leave-one-out Brier).
   (T2) leave-one-session-out robustness. (T3) explicit REDIRECTABLE-vs-TERMINAL gate taxonomy with
   per-class Wilson 95% CIs.

## Results

### Global modality split (N=232 recovered failures)
| modality | n | share |
|---|---|---|
| SAME_TOOL_RETRY | 115 | 0.496 |
| CROSS_TOOL_REDIRECT | 117 | 0.504 | ← modality-agnostic NULL redirect rate p0=0.504 |

A near-even global split — so the NULL is maximally uninformative (p0≈0.5), making any predictive lift meaningful.

### T1 — does error-class PREDICT modality? **YES, strongly and out-of-sample.**
- Full taxonomy: χ²=119.4 (df=15), **Cramér's V = 0.717 (large)**, permutation **p = 0.0002**.
- **Honest leave-one-out Brier: null=0.250 → class-conditional=0.149, improvement +0.1015 (≈40.6% reduction).**
  Knowing the error-class predicts recovery MODALITY OUT-OF-SAMPLE, strongly beating the null.
- Rare-class collapse (n<10→"rare"): V=0.682, perm-p=0.0002, LOO-Brier +0.107 (42.7%). Not a tail artifact.

This is the **inverse** of EXP-0008: the signal that *washed out* for recovery OCCURRENCE (V→0.24, Brier→0)
is *large and out-of-sample-predictive* for recovery MODALITY (V=0.72, Brier −40.6%).

### T1 robustness — survives every knob that killed the occurrence claim
| variant | redirect rate | Cramér's V | perm-p | LOO-Brier improve |
|---|---|---|---|---|
| default (A wins ties) | 0.504 | **0.717** | 0.0002 | **+0.102 (40.6%)** |
| B-priority (redirect wins ties) | 0.642 | 0.616 | 0.0002 | +0.065 (28.2%) |
| **STRICT (cross-tool-NAME only)**† | 0.371 | **0.869** | 0.0002 | **+0.163 (69.7%)** |
| K=3 | 0.506 | 0.644 | 0.0005 | +0.068 |
| K=6 | 0.504 | 0.717 | 0.0005 | +0.102 |
| K=12 | 0.552 | 0.655 | 0.0005 | +0.089 |

† STRICT: 31/117 default "redirects" are the SAME tool name with a different invocation (e.g. `Bash`
with a different head-cmd). Counting only TRUE cross-tool-*name* redirects (Bash→Bash = same-tool)
makes the signal even **stronger** (V=0.869) because it cleanly isolates the genuine tool-switch class
(web_disabled→external_web_search) from in-place Bash reinvocations. The signal is not a K-window or
tie-break artifact — unlike EXP-0008's occurrence signal, it holds or strengthens under every variant.

### T2 — leave-one-session-out: **session-robust.**
Over 36 droppable sessions: LOSO Cramér's V **min=0.698, median=0.716, max=0.776** — the modality signal
is essentially invariant to dropping any single session. web_disabled redirect-share = **1.000 across all
36 drops** (min=median=max=1.000). Not a one-session artifact.

### T3 — REDIRECTABLE vs TERMINAL gate taxonomy (classes with n_fail≥10; Wilson 95% CI on redirect-share)
| class | n_fail | recov | rec_rate | redir_share | 95% CI | gate label |
|---|---|---|---|---|---|---|
| **policy.web_disabled** | 109 | 66 | 0.606 | **1.000** | [0.945, 1.000] | **REDIRECTABLE** |
| proc.exit_nodetail | 14 | 12 | 0.857 | 0.667 | [0.391, 0.862] | REDIRECTABLE |
| other | 104 | 66 | 0.635 | 0.333 | [0.232, 0.453] | SAME-TOOL |
| fs.notfound | 20 | 16 | 0.800 | 0.312 | [0.142, 0.556] | SAME-TOOL |
| cancelled | 59 | 34 | 0.576 | 0.147 | [0.064, 0.301] | SAME-TOOL |
| **policy.perm_denied** | 30 | 14 | 0.467 | **0.000** | [0.000, 0.215] | SAME-TOOL |

**The dichotomy holds, and it is the KEY structural finding:**
- `policy.web_disabled` is a **clean REDIRECTABLE gate**: of 66 recoveries, **66/66 = 1.000 are cross-tool
  redirects** (CI [0.945,1.000]), 0 are same-tool retries. The agent NEVER recovers a web block by retrying
  the blocked tool — it ALWAYS switches to the sanctioned alternative. Audit: 34× WebSearch→external_web_search,
  26× WebFetch→external_web_search, 6× WebFetch→Bash(curl). This is the textbook redirectable gate.
- `policy.perm_denied` is the **structural contrast**: redirect-share **0.000** (CI [0,0.215]) — when this
  recovers (14/30), it is ALWAYS same-tool (the permission gets granted / the same tool is re-approved),
  NEVER a redirect. **Same provenance family (policy gate), opposite modality** — exactly what CLAIM-0009
  predicts: the redirectable-vs-terminal distinction is a property of the gate, not of "policy" as a label.
- Transient/environmental classes (`fs.notfound`, `cancelled`, `other`) are SAME-TOOL dominant (redirect
  0.15–0.33): the agent fixes the path / re-runs / edits in place rather than switching tools.

No class with n≥10 is strictly TERMINAL (rec_rate~0 & 0 redirects) in this corpus — every large class has
*some* recovery modality. `fs.perm` (n=1) is the only 0-recovery cell and is too small to call. So the
honest finding is a **REDIRECTABLE ↔ SAME-TOOL** axis is sharply present; a true TERMINAL pole is
under-sampled here (the corpus's policy gates all turned out to have an available modality).

## Headline (the defensible claim that survives)
**Error-class strongly predicts recovery MODALITY (V=0.72, LOO-Brier −40.6% out-of-sample, perm-p=0.0002),
and is session-robust (LOSO V 0.70–0.78) and knob-robust (holds/strengthens across K and tie-break
variants — the opposite of the occurrence signal in EXP-0008).** The mechanism is the redirectable-vs-
terminal gate structure: `policy.web_disabled` recovers 100% by cross-tool redirect (sanctioned alternative
exists), `policy.perm_denied` recovers 0% by redirect / 100% by same-tool (the gate must be opened, not
routed around), and transient errors recover mostly same-tool. **Provenance determines HOW, not WHETHER.**

## Honest caveats / confidence limits (anti-overclaim)
- **N is small for the decisive contrast.** The clean result rests on TWO large-ish policy cells:
  web_disabled (n=109, recov 66 — strong) and perm_denied (n=30, recov 14 — the redirect-share=0 CI is
  [0,0.215], so "near-0" is solid but "exactly 0" is not provable). All other policy cells are n≤2
  (input_filter n=2). **The redirectable-vs-terminal taxonomy is established on essentially two classes;**
  a third, cleanly-terminal policy class is NOT present in this corpus to complete the trichotomy.
- **Mechanical coupling, named honestly:** web_disabled's redirect-share=1.000 is partly definitional —
  a hard tool block CANNOT be recovered same-tool, so any recovery MUST be a redirect. That is the correct
  causal story (the gate is redirect-only), but it means the web_disabled cell is not an *independent* test
  of "error-class predicts modality" — it is the mechanism itself. The NON-trivial, non-circular evidence is
  the **CONTRAST with perm_denied** (also a policy gate, also a hard block, yet 0% redirect / 100% same-tool)
  and the within-transient spread — those are what the LOO-Brier gain and V are actually measuring.
- **Single-harness corpus** (Claude Code only). The web_disabled→external_web_search redirect and the
  perm_denied same-tool re-approval are both harness-specific behaviors. Cross-harness generality unmeasured.
- The modality label inherits EXP-0008's intent-class bracketing (upper-bound on same-goal). Mitigated by
  the STRICT cross-tool-NAME variant (which only strengthens the result) and the per-pair winning-tool audit.

## VERDICT for CLAIM-0009
**SUPPORTS.** On the same real-trace corpus where recovery-OCCURRENCE prediction was refuted (EXP-0008),
recovery-MODALITY prediction is strong, out-of-sample, session-robust, and knob-robust: error-class →
modality V=0.717 (LOO-Brier −40.6%; STRICT cross-tool V=0.869, −69.7%), LOSO V 0.70–0.78, perm-p=0.0002.
The redirectable-vs-terminal gate distinction is real and discriminating *within* the policy family
(web_disabled 100% redirect vs perm_denied 0% redirect). **Honest scope of the support:** the decisive
evidence is two policy cells + the transient/same-tool contrast; the result is a strong characterization on
a single harness with a small decisive N, NOT yet a cross-harness law. A true TERMINAL pole (0 recovery,
0 redirect) is under-sampled. CLAIM-0009 is supported as a *predictive characterization*; promotion to a
general law needs cross-harness + a sampled terminal class + interventional confirmation.

## Files
- impl: `experiments/2026-05-31/EXP-0009/impl/recovery_modality_census.py`
- csv:  `experiments/2026-05-31/EXP-0009/experiment_result/per_class_modality.csv`
- log:  `experiments/2026-05-31/EXP-0009/experiment_result/run_stdout.txt`
