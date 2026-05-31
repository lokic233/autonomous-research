# EXP-0008 — Recovery census with CROSS-TOOL WORKAROUNDS counted (CLAIM-0008)

**Domain:** MAP-0002 (Agent failure attribution & recovery). **CPU-only, stdlib-only, ~6s.**
**Claim under test:** CLAIM-0008 "Error-class predicts agent recovery competence" (YELLOW/weakened).
**Motivation:** VERDICT-0015 GREEN-path item — EXP-0007's recovery label was *same-intent retry success*,
an explicit LOWER BOUND. This experiment decouples the outcome definition by counting cross-tool workarounds.

## Data (REAL, same corpus as EXP-0007, refreshed)
`~/.claude/projects` Claude Code session logs. After joining `tool_result`→`tool_use` and dropping
<2-call sessions: **71 sessions, 3,416 tool calls, 357 ground-truth failures** (`is_error:true`).
(EXP-0007 saw 70/3,396/356 — three new sessions appeared since; effectively the same corpus.)

## Method — sharpened recovery definition (stated honestly)
`parse_session`/`classify_error` are **copied verbatim from EXP-0007** (identical 17-class failure
taxonomy, identical failure census). Only the **recovery label** changes. After a failure of class C at
call position *i*, look forward in a **bounded window of K=6 tool calls**. `recovered_broad = 1` iff EITHER:
- **(A) same-intent retry** succeeds within K (same tool; Bash=same head-cmd; file=same path) — EXP-0007's signal; OR
- **(B) cross-tool workaround**: a *different* tool of the **same pre-declared INTENT-CLASS** succeeds
  within K. Intent-classes: `WEB_INFO` (WebFetch/WebSearch/external_web_search/knowledge/curl|wget Bash),
  `FILE_READ` (Read/Glob/Grep/cat|ls|grep|find… Bash), `FILE_WRITE` (Edit/Write/tee|cp|mv|redirect Bash),
  `SEARCH_DISCOVER` (ToolSearch), `DELEGATE` (Agent/Workflow/Skill), `EXEC` (other Bash). A cross-CLASS
  success is **deliberately NOT** counted.
- **(C)** an explicit textual goal-progression channel (assistant "works/resolved/done…" within window) is
  computed but reported **separately**, NOT in the headline label, because narration ≠ verified success.

### Honest failure modes of this operationalization
- **Intent-class is an UPPER BOUND** on true same-goal recovery (tool-granularity, not goal-granularity): two
  unrelated WebFetches to different URLs both score WEB_INFO. This **inflates** recovery → biases *against*
  the claim → if the predictive signal survives this generous label, it is robust. The truth is now
  **bracketed**: EXP-0007 same-intent = lower bound, EXP-0008 broad = upper bound.
- Workarounds outside window K, or via a tool we mapped to another class, are missed (false negatives).
- Channel (B) cannot capture a pure-reasoning workaround needing no tool call (that is channel C).
- **Audit check (done):** all 66 web_disabled "broad recoveries" are `WebFetch/WebSearch → external_web_search`
  and the queries are **topically aligned** (blocked arxiv URL → same-paper search; same research question).
  These are genuine same-goal recoveries, not intent-class false positives.

## Results

### Global recovery rate (N=357)
| definition | rate |
|---|---|
| EXP-0007 same-intent (unbounded) | 0.451 |
| same-intent within K=6 | 0.319 |
| **BROAD (same-intent OR workaround), K=6** | **0.639** |
| BROAD + textual channel C | 0.700 |

Counting workarounds raises the global recovery rate from **0.451 → 0.639** (+0.19). The true in-session
recovery rate is substantially higher than EXP-0007's lower bound — the agent frequently achieves the goal
a different way. Workaround flag fires on **40.9%** of failures.

### Q1 — per-class lift (same-intent → broad)
| class | n | same-intent | broad | LIFT |
|---|---|---|---|---|
| **policy.web_disabled** | 109 | **0.000** | **0.606** | **+0.606** |
| other | 98 | 0.745 | 0.643 | −0.102* |
| cancelled | 59 | 0.559 | 0.576 | +0.017 |
| policy.perm_denied | 30 | 0.567 | 0.467 | −0.100* |
| fs.notfound | 19 | 0.632 | 0.789 | +0.158 |
| proc.exit_nodetail | 14 | 0.500 | 0.857 | +0.357 |
| ssh.auth | 6 | 0.667 | 0.833 | +0.167 |
| proc.timeout | 4 | 0.500 | 0.750 | +0.250 |

\* The negative "lifts" for `other`/`perm_denied` are an artifact of comparing **unbounded** same-intent
(EXP-0007 scans the whole session) against **windowed** broad (K=6). Some unbounded same-intent successes
fall outside K=6, so a broad-but-windowed label can be lower than an unbounded-but-same-intent label on a
class with distant retries. The honest within-K comparison (same-intent-within-K=0.319 → broad=0.639)
shows the workaround channel only ever ADDS recoveries; nothing is removed.

**Headline Q1 finding: the single biggest "permanent gate" cell collapses.** `policy.web_disabled` goes
from 0/109 (EXP-0007) to **66/109 = 0.606** once we count the agent switching from the blocked WebFetch/
WebSearch to the *sanctioned* `external_web_search` tool. EXP-0007's 0/109 was an **artifact of the
same-intent definition**, not a true property of the failure: the agent had an allowed alternate channel
and used it most of the time.

### Q2 — does error-class STILL predict recovery under the broad label?
**Largely NO — the signal substantially washes out.**
- Null p0(broad)=0.639. Full taxonomy: χ²=20.5 (df=16), **Cramér's V = 0.239** (down from **0.644**), permutation **p=0.164 (NOT significant)**.
- **Honest LOO-Brier: null=0.2308 → class-conditional=0.2314, improvement = −0.0006 (≈0%).** Under the
  broad definition, **knowing the error-class gives NO out-of-sample predictive gain over the
  class-agnostic null.** (EXP-0007 had +0.087 / −35%.)
- Rare-class collapse (n<10→rare) recovers some signal: V=0.211, perm-p=0.015 — significant but weak.

The EXP-0007 effect (V=0.64, LOO-Brier −35%) was **driven primarily by the web_disabled 0/109 cell**.
Once that cell is correctly scored as recoverable-by-workaround, the out-of-sample predictive power of
error-class essentially vanishes at the full-taxonomy level.

### Q3 — does the PERMANENT vs TRANSIENT (provenance/permanence) axis hold? **THE CRUX**
**It WEAKENS sharply.**
| split | EXP-0007 same-intent | EXP-0008 broad (K=6) |
|---|---|---|
| permanent (web_disabled/input_filter/perm_denied/cancelled) | 0.250 | **0.580** |
| transient | 0.707 | 0.713 |
| φ | **0.454** | **0.138** (perm-p=0.012) |

The permanent/transient gap shrinks from **0.46 → 0.13**. The "permanent harness gate" bucket was
dominated by `web_disabled`, which is **not actually a hard wall** — it is a *redirectable* gate (blocked
tool → allowed tool). Transient recovery barely moves (0.707→0.713) because transient errors were already
mostly same-intent-retryable; it is the *permanent* bucket that gains almost all the lift, **collapsing the
very contrast EXP-0007 leaned on.**

### Q3b — do agent-UNCONTROLLABLE policy gates stay near-unrecoverable? (the deciding question)
| gate | n | same-intent | broad | lift |
|---|---|---|---|---|
| policy.web_disabled | 109 | 0.000 | **0.606** | **+0.606** |
| policy.input_filter | 2 | 0.000 | 1.000 | +1.000 |
| policy.perm_denied | 30 | 0.567 | 0.467 | −0.100 (windowing artifact) |
| cancelled | 59 | 0.559 | 0.576 | +0.017 |

**No.** The largest policy-gate class (web_disabled) does NOT stay unrecoverable — it is the *biggest*
beneficiary of workarounds. The crux hypothesis ("policy gates stay near-unrecoverable while transient
errors gain from workarounds, STRENGTHENING the permanence axis") is **refuted by the data**: the opposite
happens. The gate that looked permanent had a sanctioned alternate channel; the agent routinely takes it.

### K-window sensitivity
| K | broad rate | V (perm-p) | perm | trans | φ |
|---|---|---|---|---|---|
| 3 | 0.476 | 0.320 (0.001) | 0.370 | 0.611 | 0.240 |
| 6 | 0.639 | 0.239 (0.160) | 0.580 | 0.713 | 0.138 |
| 12 | 0.796 | 0.216 (0.413) | 0.760 | 0.841 | 0.099 |

The wider the window, the weaker the signal — at every K≥6 the full-taxonomy effect is non-significant and
the permanence φ is ≤0.14. Only at a very tight K=3 (which under-counts genuine multi-step workarounds)
does a moderate signal (V=0.32) persist. The result is **not** a K=6 artifact; it strengthens against the claim as K grows.

## VERDICT for CLAIM-0008
**WEAKEN.** The EXP-0007 result was **outcome-definition-dependent**. Under the honest, broader recovery
definition that counts cross-tool workarounds:
1. The true recovery rate is much higher than EXP-0007's lower bound (0.45 → 0.64; web_disabled 0 → 0.61).
2. Error-class loses out-of-sample predictive power over the null (LOO-Brier −35% → ≈0%; V 0.64 → 0.24, perm-p=0.16, n.s.).
3. The provenance/permanence axis — EXP-0007's headline — **collapses** (φ 0.45 → 0.14): the dominant
   "permanent gate" (web_disabled) is in fact a *redirectable* gate the agent works around 61% of the time.

The honest reading: EXP-0007's strong signal was **largely manufactured by scoring a redirectable policy
gate as 0/109 unrecoverable**. When recovery is defined by *goal achievement by any sanctioned means* rather
than *same-tool retry*, the predictive law is weak and not out-of-sample significant. A residual, modest
signal survives only at very tight windows / after rare-class collapse (V≈0.21–0.32). **CLAIM-0008 as
stated ("error-class predicts recovery competence") is not robust to the outcome definition.** A defensible
*reformulated* claim might be: *error-class predicts the recovery MODALITY (same-tool retry vs cross-tool
redirect), not whether recovery happens* — but that is a different, narrower claim than CLAIM-0008.

## Honest caveats / limits
- **Single-harness corpus** (Claude Code only); the web_disabled→external_web_search redirect is harness-specific.
- **Small N** for several decisive cells: input_filter n=2, perm_denied n=30. The web_disabled cell (n=109)
  carries the result, so the conclusion rests on one large, audited class.
- Intent-class is an **upper bound** (false-positive-leaning); EXP-0007 same-intent is the lower bound.
  Truth is bracketed [0.45, 0.64] globally. Even at the *lower* (conservative-for-the-claim) edge of the
  workaround channel, the perm/transient φ already drops below 0.25 (K=3 row), so the weakening is not an artifact of generosity.
- This does **not** refute that error-class carries *some* information; it refutes that it is a *strong,
  out-of-sample, permanence-driven* predictor once workarounds count.

## Files
- impl: `experiments/2026-05-31/EXP-0008/impl/workaround_recovery_census.py`
- csv:  `experiments/2026-05-31/EXP-0008/experiment_result/per_class_workaround_recovery.csv`
- log:  `experiments/2026-05-31/EXP-0008/experiment_result/run_stdout.txt`
