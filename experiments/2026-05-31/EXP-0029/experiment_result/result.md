# EXP-0029 RESULT — RE-TEST of the REFRAMED CLAIM-0010 (researcher-0003-laneE)

**Claim under test (orchestrator/committee REFRAME of CLAIM-0010, post EXP-0022/VERDICT-0030):**
"Agentic failure recovery has (A) a PARTIAL coarse gate-table layer + (B) a CONTEXT-CONDITIONED
(NOT free-adaptive) fine layer with a QUANTIFIABLE residual-entropy floor."

**Corpus:** `~/.claude/projects` recursive `**/*.jsonl`. THIS run: **81 sessions / 3,567 calls /
384 ground-truth failures** (live corpus rotated up slightly from EXP-0022's 79/3,547/375; same
population, same parse/classify/gate/modality/context-feature code copied VERBATIM from EXP-0022 ==
EXP-0019/0009/0007). CPU-only, stdlib-only, ~2s + ~6s paired-CI addendum. Single harness (Claude Code).
Gate dist: TRANSIENT 236 / REDIRECTABLE 111 / GRANT_REQUIRED 37.

## What this experiment adds over EXP-0022
EXP-0022 weakened the strong "fine = adaptive" claim. THIS re-test asks the reframe's three sharp
questions with **proper out-of-sample CIs**: (Q1) is coarse determinism robust or a web_disabled
artifact (bootstrap CIs, not point LOCO); (Q2) what is the *irreducible residual-entropy floor* after
the BEST leak-free context model under **leave-one-SESSION-out** (kills within-session leakage that
LOO can't); (Q3) is the reframe DEFENSIBLE or does it COLLAPSE — decision rule stated before reading.

---

## Q1 — COARSE LAYER: web_disabled-carried, with CIs
| measure | Theil U(modality\|gate) | boot 95% CI |
|---|---|---|
| FULL | **0.381** | [0.310, 0.472] |
| drop `policy.web_disabled` (LOCO) | **0.034** | [0.003, 0.091] (n=167) |
| drop ALL REDIRECTABLE | 0.012 | [0.000, 0.064] (n=165) |

The full U CI **excludes 0** (a real coarse signal exists) but **collapses to ~0.03** when the single
`web_disabled` cell is removed — and the residual-U CI upper is **0.091 < 0.15**. **CONFIRMED with CIs:
the coarse determinism is web_disabled-CARRIED.** Per-gate modality determinism:
- **REDIRECTABLE**: modal share **1.000** [1.000,1.000], normH=0.000 — fully deterministic (68/68 CROSS_TOOL_REDIRECT). This is the carrying cell (definitional hard-block).
- **GRANT_REQUIRED**: modal share 0.842 [0.684,1.000], normH=0.629 — leans same-tool but n=19, wide CI.
- **TRANSIENT**: modal share 0.678 [0.603,0.753], normH=0.906 — barely above the 50/50 two-category floor; essentially NOT deterministic.

=> The coarse layer is a **PARTIAL gate-table whose determinism lives almost entirely in the one
REDIRECTABLE/web_disabled cell**. Defensible ONLY if labelled that way; "the coarse layer is
deterministic" (unqualified) is false outside that cell.

## Q2 — FINE LAYER: irreducible residual-entropy floor (leave-one-SESSION-out, leak-free)
Best **leak-free** context model = NB over {error-class, error-text keywords, prior tool}; `failed_tool`
DROPPED (the same-tool-retry leak). OOS scheme = **leave-one-session-out**. Baseline = within-gate
modal tool (also LOSO).

| gate | n | tools | modal LOSO-acc [CI] | context LOSO-acc [CI] | lift | residual-entropy FLOOR (H tool\|pred) [CI] |
|---|---|---|---|---|---|---|
| REDIRECTABLE | 111 | 10 | 0.396 [0.306,0.486] | **0.523 [0.432,0.613]** | **+0.126** | **0.608 [0.543,0.717]** (1.64 bits) |
| GRANT_REQUIRED | 37 | 15 | 0.432 [0.270,0.595] | 0.514 [0.351,0.676] | +0.081 | 0.676 [0.490,0.798] (1.94 bits) |
| TRANSIENT | 236 | 40 | 0.356 [0.297,0.419] | 0.386 [0.322,0.449] | +0.030 | **0.740 [0.684,0.789]** (3.33 bits) |

**PAIRED bootstrap CI on the lift** (resample correctness pairs, B=4000) — the rigorous significance test:
| gate | lift | paired 95% CI | P(lift≤0) | verdict |
|---|---|---|---|---|
| REDIRECTABLE | +0.126 | **[+0.063, +0.189]** | 0.000 | **SIGNIFICANT** |
| GRANT_REQUIRED | +0.081 | [+0.000, +0.189] | 0.046 | borderline n.s. |
| TRANSIENT | +0.030 | **[+0.008, +0.055]** | 0.000 | significant but TINY |

**Findings:**
1. The leak-free context signal is **real and out-of-sample** — strongest in REDIRECTABLE (+12.6 pts,
   skill +0.21, paired CI cleanly excludes 0), present-but-tiny in TRANSIENT (+3 pts), borderline in
   GRANT_REQUIRED (small-n). It is NOT a within-session or same-tool-retry artifact (LOSO + failed_tool dropped).
2. The **irreducible residual-entropy floor** — the genuinely situation-dependent remainder AFTER the
   best context model — is **high and tightly CI-bounded**: REDIRECTABLE 0.608 [0.543,0.717] (~1.6 bits),
   TRANSIENT 0.740 [0.684,0.789] (~3.3 bits). Even where context predicts best (REDIRECTABLE), the model
   tops out at ~52% accuracy; **~48% of the fine tool-choice is genuinely situation-dependent residual.**

=> The fine layer is exactly "context-conditioned, NOT free-adaptive, with a quantified residual floor":
a real but modest learnable lift sitting on top of a large (CI lower ≥ 0.54) irreducible-entropy floor.

## Q3 — HONEST CRUX: DEFENSIBLE vs COLLAPSE
Decision rule (pre-registered in code): COARSE-PARTIAL defensible if full-U CI excludes 0 AND honestly
labelled web_disabled-carried (residual-after-web_disabled CI upper < 0.15); FINE defensible if ≥1 large
gate shows a leak-free LOSO lift with CI excluding 0 AND a non-trivial residual floor (CI lower > 0.30);
COLLAPSE if coarse residual-U ≈ 0 AND no gate shows a significant leak-free lift.

- COARSE: full U CI [0.310,0.472] excludes 0; residual-after-web_disabled CI [0.003,0.091] ≈ 0 and < 0.15. **Partial gate-table, honestly web_disabled-carried — DEFENSIBLE only with that label.**
- FINE: REDIRECTABLE leak-free paired lift CI [+0.063,+0.189] excludes 0; residual floor CI lowers 0.543/0.684/0.490 all > 0.30. **Context-conditioned with a real quantified residual floor — DEFENSIBLE.**

### ===> REFRAME VERDICT: **DEFENSIBLE — but only in its honest, deflated form.**
The reframed two-layer claim survives rigorous OOS re-test as: **coarse = a PARTIAL gate-table whose
determinism is carried by the single REDIRECTABLE/web_disabled hard-block cell; fine = a context-conditioned
(error-text + prior-tool, leak-free, OOS) tool selection with a real but modest predictive lift (+12.6 pts
in REDIRECTABLE) over a large, CI-bounded irreducible residual-entropy floor (~0.54–0.74 norm-H, ~48%+
genuinely situation-dependent).** It does NOT collapse to "just web_disabled + noise" — the fine context
signal is genuinely out-of-sample and leak-free. But it is also NOT the original CLAIM-0010 ("coarse
deterministic / fine adaptive decision"): both layers are softer and the headline must carry the
web_disabled-carried and residual-floor qualifiers.

## EFFECT ON CLAIM-0010: **weaken** (confirms VERDICT-0030; converts the reframe into a defensible-but-deflated characterization)
This is a *constructive weaken*: it does not refute, but it locks the claim to its honest deflated form
and quantifies the residual that the original "adaptive" framing hand-waved. It is the GREEN-PATH version
of the claim ONLY IF the headline adopts the deflation: **"partial (web_disabled-carried) coarse gate-table
+ context-conditioned fine selection with a ~0.6–0.74 norm-entropy irreducible floor."** The remaining
GREEN blocker is unchanged: **single harness (Claude Code)** — cross-harness replication is required, and
the coarse layer's web_disabled-carried nature makes it especially harness-specific (the carrying cell is
a Claude-Code policy hook).

## PROJ-0003 LINEAGE / WIND-DOWN ASSESSMENT
- CLAIM-0008 (error-class → recovery OCCURRENCE): **REFUTED/weakened** (outcome-definition-dependent; V 0.64→0.24 n.s.).
- CLAIM-0009 (harness-routing confound): **CONFIRMED as a confound** (config-fact, not a research thesis on its own).
- CLAIM-0010 (two-layer): **WEAKENED → now a DEFENSIBLE-but-DEFLATED characterization** (this experiment).

**Assessment: PROJ-0003 should NOT be fully wound down — but it has exactly ONE surviving defensible
thesis, and it is narrow.** The honest surviving finding is the deflated two-layer characterization:
> Agentic recovery, on the Claude-Code corpus, decomposes into (1) a partial coarse gate-table whose
> only deterministic cell is the REDIRECTABLE web_disabled hard-block (cross-tool redirect, 68/68), and
> (2) a context-conditioned fine tool-selection with a small leak-free OOS predictive lift over a large,
> quantified irreducible residual-entropy floor (~48%+ situation-dependent).

This is publishable ONLY as a *negative/deflationary* characterization ("recovery is mostly NOT a routing
table and NOT free adaptivity — it is one config cell + a weakly-predictable context layer with a hard
entropy floor") AND only after **cross-harness** replication. If cross-harness fails (the web_disabled
cell is Claude-Code-specific and the +12pt fine lift does not reproduce), PROJ-0003 should wind down to
its honest surviving findings as a methods/negative-result note: every strong positive claim in the
lineage (0008 occurrence, 0010 adaptive) deflated under adversarial re-test; the durable contribution is
the *measurement methodology* (gate-type confound + LOO/LOSO/paired-bootstrap discipline) and the negative
result that single-harness recovery competence is dominated by one policy cell.

## Files
- impl: `experiments/2026-05-31/EXP-0029/impl/reframe_retest.py`, `paired_lift_ci.py`
- result: `experiments/2026-05-31/EXP-0029/experiment_result/` — `result.md`, `run_stdout.txt`,
  `paired_lift_stdout.txt`, `reframe_metrics.csv`, `paired_lift_ci.csv`
