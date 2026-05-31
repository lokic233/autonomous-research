# EXP-0020 — TERMINAL-POLE census for the redirectable-vs-terminal taxonomy (CLAIM-0009)

**Agent:** researcher-0003-laneA · **Domain:** MAP-0002 · **CPU-only, stdlib-only, ~25s.**
**Claim under test:** CLAIM-0009 (WEAKENED — VERDICT-0020 6/6 yellow, VERDICT-0021). The surviving
claim is a **gate-type+harness-routing CHARACTERIZATION** of recovery modality with three poles:
REDIRECTABLE (hard-block → cross-tool redirect), SAME-TOOL/GRANT-REQUIRED (retry same tool), and
**TERMINAL** (genuinely unrecovered). EXP-0009 demonstrated the first two poles at n≥10; the **terminal
pole was NOT demonstrated** (no class with n≥10 had ~0 recovery & ~0 redirect). This experiment tests the
ONE named CPU-doable gap from the verdicts: **is there a cleanly-TERMINAL error class at n≥10 on this
corpus?**

## Method (stated honestly)
`parse_session`/`classify_error`/`intent_class`/`head_cmd`/`block_text` **copied verbatim** from
EXP-0007/0008/0009 (no cross-dir import — identical 17-class taxonomy, identical failure census). Recovery
uses EXP-0008's **BROAD** definition (channel A same-tool-retry OR channel B cross-tool-redirect within
window K=6). A failure is **TERMINAL iff broad recovery did NOT fire** (genuinely unrecovered within the
window). We add three independent terminal signals:
1. **window-terminal** — `recovered_broad==0` at K=6 (primary).
2. **session-ending (K-independent)** — failure is the literal last tool call, OR no successful tool call
   occurs *anywhere* after it in the session (the session effectively ended on unresolved error).
3. **repeated-identical-hard-error runs** — same intent + same error-class failed ≥3× consecutively.

A class is declared **CLEANLY-TERMINAL** iff `n_fail≥10 AND rec_rate≤0.10 AND redirect==0`; **NEAR-TERMINAL**
iff `n_fail≥10 AND rec_rate≤0.25 AND redirect≤1`. Wilson 95% CIs on every terminal-share.

## Data (REAL, same corpus, refreshed)
`~/.claude/projects` Claude Code logs. After join + <2-call drop: **78 sessions, 3,544 tool calls, 373
ground-truth failures** (grew from EXP-0009's 74/3,508/364). Global broad recovery rate **0.625** (terminal
0.375) — matches EXP-0008/0009's ~0.64, confirming the census is the same machinery.

## Results

### Terminal signals are RARE and DIFFUSE, not concentrated in a clean class
| signal | count / 373 | rate |
|---|---|---|
| window-terminal (broad recovery ≠ fired, K=6) | 140 | 0.375 |
| failure is the **literal last tool call** | 6 | **0.016** |
| **NO successful tool call anywhere after** the failure | 12 | **0.032** |

Sessions overwhelmingly end on **success or user-stop**, not hard-terminal failure: only 1.6% of failures
are the last call, only 3.2% have no recovery anywhere downstream. The corpus structurally under-samples
genuine session-ending failure.

### Per-class TERMINAL census (n_fail≥10; Wilson 95% CI)
| class | n | term | term_rate | redir | rec_rate | last_call | no_succ_after | →pole |
|---|---|---|---|---|---|---|---|---|
| other | 113 | 46 | 0.407 [0.32,0.50] | 23 | 0.593 | 4 | 9 | not-terminal (recovers) |
| policy.web_disabled | 109 | 43 | 0.394 [0.31,0.49] | 66 | 0.606 | 1 | 1 | **REDIRECTABLE** |
| cancelled | 59 | 25 | 0.424 [0.31,0.55] | 5 | 0.576 | 0 | 0 | not-terminal (recovers) |
| policy.perm_denied | 30 | 16 | 0.533 [0.36,0.70] | 0 | 0.467 | 1 | 2 | **SAME-TOOL** (not terminal) |
| fs.notfound | 20 | 4 | 0.200 [0.08,0.42] | 5 | 0.800 | 0 | 0 | not-terminal (recovers) |
| proc.exit_nodetail | 14 | 2 | 0.143 [0.04,0.40] | 8 | 0.857 | 0 | 0 | not-terminal (recovers) |

**No class at n≥10 is cleanly- or near-TERMINAL.** The most terminal-leaning n≥10 class is
`policy.perm_denied` (term_rate 0.533) — but it still recovers 47% of the time and is the *already-demonstrated*
SAME-TOOL/grant-required pole (0 redirects), NOT a new terminal pole. The single 0-recovery cell `fs.perm`
is **n=1** (too small to call — unchanged from EXP-0009). The terminal failures are spread across the three
*largest* classes (other/web_disabled/cancelled) at a near-constant ~0.40 — i.e. they look like background
goal-abandonment, not an error-class property.

### SUPPLEMENTARY (decisive): terminality is NOT a class property — it is window-dependent abandonment
| K | global term_rate | class→terminal Cramér's V | perm_p | any n≥10 class ≥0.90 terminal? |
|---|---|---|---|---|
| 3 | 0.531 | 0.308 | 0.0005 | **No** |
| 6 | 0.375 | 0.238 | **0.133 (n.s.)** | **No** |
| 12 | 0.225 | 0.214 | 0.394 (n.s.) | **No** |
| 24 | 0.158 | 0.199 | 0.528 (n.s.) | **No** |

Two facts kill the terminal-pole-as-class hypothesis on this corpus:
- **Window-dependence:** term_rate collapses 0.53→0.16 as K grows 3→24. Most "terminal" failures are merely
  *slow* recoveries or eventual abandonment that fall outside the window — not hard-terminal.
- **Class-independence:** at the operative K=6, error-class barely predicts terminality (V=0.238,
  perm_p=0.133, **not significant**), and **no class at any K reaches ≥0.90 terminal at n≥10**. (The
  significance at K=3 is only because short windows clip slow same-tool retries class-differentially.)

### Repeated-identical-hard-error runs (≥3 consecutive same-intent same-class failures)
112 fail-points begin a ≥3-run, dominated by web_disabled (43), other (29), cancelled (23), perm_denied (14).
These are NOT terminal: web_disabled's 43 repeated-blocks all *eventually* redirect to `external_web_search`
(the REDIRECTABLE pole); the runs are retry-then-redirect behavior, not unrecovered terminality.

## Headline (honest)
**The TERMINAL pole CANNOT be demonstrated on this corpus.** No error class reaches n≥10 with ~0 recovery
AND ~0 redirect. Genuine session-ending failure is vanishingly rare (1.6% last-call, 3.2% no-success-after);
"terminal" under a bounded window is diffuse, window-dependent goal-abandonment that error-class does not
predict (V=0.238, perm_p=0.133 n.s. at K=6). The corpus's sessions end on success or user-stop, not on a
hard-terminal error class — exactly as the orchestrator anticipated. **This is a real LIMITATION of the
single-harness corpus, reported honestly — not a manufactured pole.**

## What this means for CLAIM-0009 / the trichotomy
- The redirectable-vs-terminal taxonomy keeps only **TWO demonstrated poles** on this corpus
  (REDIRECTABLE = web_disabled; SAME-TOOL/grant-required = perm_denied + transients). The **third
  (TERMINAL) pole remains undemonstrated** — confirming, with data, the VERDICT-0020/0021 honest caveat
  that "a true TERMINAL pole is under-sampled."
- This **does not weaken or support** the gate-type characterization itself — it bounds its *completeness*.
  It converts the verdicts' assertion ("under-sampled") into a **demonstrated** fact: terminality here is
  not an error-class property at all, so the corpus cannot exhibit a clean terminal pole regardless of
  taxonomy. **Effect = weaken** (it forecloses the one CPU path to completing the trichotomy on this corpus;
  the terminal pole now provably needs a *different* corpus, not finer analysis of this one).

## Honest caveats
- "window-terminal" conflates true unrecoverability with the agent *choosing* to abandon a subgoal (e.g.
  one of many parallel reads it didn't need). The K-sweep + session-ending signals are exactly the controls
  for this, and both point the same way (diffuse, rare, not class-bound).
- Single-harness (Claude Code) — a different harness that hard-crashes on OOM/refusal/unrecoverable-parse
  could exhibit a clean terminal pole; this corpus simply does not contain one at n≥10.
- `code.build`/`net.*`/`read.too_large` are plausible *a-priori* terminal candidates but each has n≤4 here
  — too small to characterize (and even those mostly recovered).

## Files
- impl: `experiments/2026-05-31/EXP-0020/impl/terminal_pole_census.py`
- csv:  `experiments/2026-05-31/EXP-0020/experiment_result/terminal_pole_per_class.csv`
- log:  `experiments/2026-05-31/EXP-0020/experiment_result/run_stdout.txt`

## VERDICT for CLAIM-0009
**WEAKEN (completeness bound).** The terminal pole of the redirectable-vs-terminal taxonomy is **NOT
demonstrable on this corpus**: no class at n≥10 is cleanly- or near-terminal, session-ending failure is
~3%, and terminality is window-dependent and class-independent (V=0.238, perm_p=0.133 n.s.). The trichotomy
stays at TWO demonstrated poles; the terminal pole provably requires a different (e.g. crash-prone or
refusal-heavy) corpus, not further CPU analysis of the Claude Code traces.
