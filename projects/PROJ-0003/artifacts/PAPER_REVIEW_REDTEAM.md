# PROJ-0003 — ADVERSARIAL RED-TEAM of PAPER_SYNTHESIS.md (hostile NeurIPS D&B reviewer pass)

**Reviewer:** researcher-0003-redteam · **Date:** 2026-05-31 · **CPU-only, document-only**
**Orchestrator:** session 22bd6bef-b84b-4827-a371-87443ea8602f
**Target:** `prior_art/PROJ-0003/PAPER_SYNTHESIS.md` (the negative-result + M1-M11 methodology synthesis)
**Posture:** I am the meanest reviewer in the batch. My job is to find the reason to reject. I read every
load-bearing number back to its experiment result.md, attacked the methodology as "standard caveats," hunted
for an over-claim, and checked whether the single weakest link is hidden. This document **recommends only** —
no claim/verdict/map/experiment edits, no touch to CLAIM-0012.

> **VERDICT: GO with a short punch-list (minor revisions).** The negative-result framing is defensible, the
> refutation chain traces cleanly to its experiments, the M1-M11 catalog mostly survives the "standard caveats"
> attack, the off-node gap is stated honestly, and I found **no positive prediction that the paper refuted and
> then re-asserts** (no over-claim). The punch-list is presentational + a handful of numbers that need an
> explicit cross-reference so a reviewer doesn't think they were invented. This is submission-ready after the
> punch-list; it is NOT a reject and NOT a major-revisions.

---

## Q1 — Is the negative-result framing defensible? Is the refuted-vs-survives boundary precise + honest?

**Defensible: YES.** Negative results + a transferable measurement methodology are explicitly in scope for
NeurIPS D&B (the synthesis cites this in §4.1, and the nearest neighbor MAST/Cemri is itself a 2025 D&B paper,
so the venue and the positioning neighbor coincide — a genuine strength, not a hedge). A hostile reviewer
cannot reject on "negative results aren't publishable here" — that attack is foreclosed by the track CFP.

**The boundary is stated precisely.** §3.1 (SURVIVES) vs §3.2 (REFUTED) is the strongest part of the paper:
- SURVIVES is narrowed to two things and *only* two: (i) the redirectable/grant-required/transient **gate
  taxonomy** (harness-agnostic, EXP-0031, Wilson-separated per-gate redirect shares), and (ii) "modality is a
  1-bit routing fact *within a harness*" (EXP-0012). Both are stated *against* what was refuted.
- REFUTED enumerates six casualties explicitly: occurrence prediction, error-class modality beyond the bit,
  flat routing table, adaptive fine layer, terminal pole, and routing-DETERMINES-modality (on-node). Each is
  paired to its experiment. This is exactly the honesty a hostile reviewer looks for and rarely finds.

**Where a hostile reviewer still pushes (punch-list, not reject):**
- **P1 — the survivor's own novelty is self-undercut, and the paper should say so *louder*.** Both final-
  determination docs (CLAIM-0010 §3, CLAIM-0011 §2-3) concede the gate taxonomy is "essentially the
  pre-existing EXP-0008/MAP-0002 occupied_territory insight" and "pre-empted in generic form by LangGraph."
  PAPER_SYNTHESIS §3.1/§4.2 acknowledges the LangGraph pre-emption but does **not** state plainly that the
  surviving *positive* taxonomy is largely non-novel on its own. A mean reviewer will write: "the only thing
  that survives is admitted by the authors' own appendix to be prior art." **Pre-empt this in the body:** the
  contribution is NOT the taxonomy-as-discovery; it is (a) the *negative* result that error-class/​routing do
  NOT predict modality, and (b) the methodology. The taxonomy is the *conditioning variable the methodology
  vindicates*, not a standalone claim. The synthesis knows this — make it explicit in §3.1 so the reviewer
  can't "discover" it as a gotcha.
- **P2 — "harness-agnostic" leans on n=9 (Gemini) and n=2 (Codex REDIRECTABLE class).** §3.1 asserts the gate
  taxonomy "recurs across all three on-node harnesses," but EXP-0031's Gemini REDIRECTABLE cell is 9 blocks
  (6 redirects, Wilson [0.610,1.000]) and EXP-0012's REDIRECTABLE is web_disabled=66 + input_filter=**2**. The
  "three-harness" structural claim is real but thin on two of three legs. The Limitations bullet already flags
  "Gemini blocks n=9" — good — but the word "harness-agnostic" in the headline survivor should be softened to
  "structurally recurrent across the three harnesses sampled (REDIRECTABLE leg thin on Codex n=2 / Gemini n=9)."

**Q1 result: framing defensible, boundary honest. Punch-list P1 (state survivor's limited standalone novelty
in-body) + P2 (qualify "harness-agnostic" given small-n legs).**

---

## Q2 — The M1-M11 trap catalog: real / non-obvious / NOT generic stats hygiene? Is the "standard caveats" attack rebutted?

This is the load-bearing question for a *methodology* paper, and it is where a hostile reviewer spends their
energy. The strongest possible attack is: **"M1-M11 are textbook caveats — null baselines, cross-validation,
sensitivity sweeps. Repackaging stats hygiene as a contribution is not a NeurIPS-level methodology."**

I went through each trap on three axes: **(a) paired to a specific false-positive it actually caught**,
**(b) non-obvious / contribution-worthy**, **(c) not generic.** Result: **the catalog largely survives**, but
its survival depends on a *framing move the synthesis makes implicitly and must make explicitly*: the
contribution is not the individual techniques (some ARE generic) — it is **which specific lie each one caught
in the agentic-recovery-attribution setting**, and the claim that this construct is *unusually* prone to four
specific failure modes (lower-bound outcome defs, one-cell-carried effects, duplicate-log inflation,
harness/model/error-text collinearity). That is the defensible methodological thesis, and §2's closing
paragraph states it — but it is buried under the table.

### Per-trap audit (does each rebut "standard caveat"?)

| # | Paired to a real false-positive? | Non-obvious / domain-specific? | "Standard caveat" rebuttal status |
|---|---|---|---|
| M1 null + *informed* baseline | YES — error-class beat the null but added ≤0.2% over a 1-bit gate flag (EXP-0008/0012, traced) | PARTLY — "compare to chance" is generic; "compare to the *informed* 1-bit baseline" is the non-obvious move | **HOLDS** *only* if framed as informed-baseline (beating chance ≠ useful). Generic if framed as "use a null." |
| M2 LOSO-vs-LOCO CV | YES — LOSO leaked per-class rates (+40%); LOCO revealed -33%, no generalization to unseen classes (EXP-0012, traced exactly) | **YES, strongly** — leave-one-CLASS-out (not sample-out) is the right unit when the question is "does the *taxonomy* generalize." This is the single most contribution-worthy trap. | **HOLDS — flagship.** A reviewer who calls this "just CV" is wrong: the LOSO/LOCO *unit choice* is the whole point and is routinely gotten wrong. |
| M3 lower-bound vs upper-bound recovery defs | YES — the headline V 0.64→0.24 was a *definitional* artifact of the lower-bound label (EXP-0007/0008, traced) | **YES** — that "recovery" has no canonical operationalization, and the choice flips the headline, is the domain-specific lesson | **HOLDS.** Domain-specific (agentic recovery has no settled outcome def). Not generic. |
| M4 ablate the decisive cell | YES — coarse "determinism" was web_disabled-carried: U 0.381→0.034 (EXP-0029, traced exactly) | PARTLY — "leave-one-group-out" is generic; "find the *one cell* carrying the effect and LOCO *it*" with bootstrap CIs is sharper | **HOLDS** if framed as decisive-cell (not generic ablation). The CI-bounded "residual < 0.15" makes it rigorous. |
| M5 double-log de-dup | YES — Codex logs every call twice (`function_call` + `mcp_tool_call_end`); 304→152; the entire CC-vs-Codex contrast dissolved (EXP-0033, traced exactly) | **YES, strongly** — this is THE most defensible trap. It is *specific to agentic trace logs*, not stats at all, and it silently 2×'d a headline. | **HOLDS — flagship.** No reviewer can call "harness logs duplicate tool-call events, canonicalize before counting" a textbook caveat. This is a real, novel, agent-trace-specific gotcha. |
| M6 naming-confound control | YES — only residual signal (Gemini 2/9) perfectly confounded with error-text naming an in-inventory twin (EXP-0032/0033, traced) | **YES** — "does the error TEXT name the alternative?" is a recovery-attribution-specific confound | **HOLDS.** Domain-specific; not generic. |
| M7 3-way-alias diagnosis | YES — established harness×model×error-naming collinearity is unbreakable on-node (perfect diagonal) | **YES** — enumerating the corpus-inventory collinearity *before* claiming causality is the move that prevents the whole paper from over-claiming | **HOLDS.** This is what makes the negative result honest rather than a positive over-claim. |
| M8 strict reactive/preempt/abandon | YES — lenient "any twin after window" inflated CC 66/66; strict → 5/43 (EXP-0033, traced exactly) | **YES** — the PREEMPT-vs-REACTIVE distinction (twin *before* block ≠ a recovery decision) is subtle and was the actual error in EXP-0031/0032 | **HOLDS — strong.** Mislabeling a preemptive parallel batch as a reactive routing decision is a real, non-obvious trap. |
| M9 anti-tautology delta | YES — frames ≤0.2% as the *content* vs the trivially-true "frameworks route errors" (LangGraph) | YES — this is the move that survives the LangGraph pre-emption | **HOLDS** but is more a *positioning* discipline than a measurement control; fine to keep, label it as such. |
| M10 window/terminality sensitivity | YES — terminal pole window-dependent (0.53→0.16 as K 3→24) AND class-independent (V=0.238 n.s.) (EXP-0020, traced exactly) | PARTLY — "sweep your window param" is generic sensitivity analysis; the *finding* (terminality is window-determined, not class-determined) is the domain content | **WEAKEST OF THE 11.** The technique (sweep K) IS generic. It HOLDS only because the *conclusion* it produced (no demonstrable terminal class) is a real negative result. Frame M10 as "the sensitivity sweep that *killed a pole of the taxonomy*," not as a generic robustness check. |
| M11 the off-node v2 factorial | YES — specifies the only design breaking the alias, pre-registered KILL conditions | **YES** — pre-registering the kill conditions so the result can't be "talked into a YELLOW" is a genuine methodological commitment, fully operationalized in the PROTOCOL doc | **HOLDS — strong.** This is the constructive half of the negative result. |

### "Standard caveats" rebuttal status: **REBUTTED, but the rebuttal must be made explicit in-body.**

- **Two flagship traps (M5 double-log dedup, M2 LOSO-vs-LOCO) and three strong domain-specific ones (M8 strict
  preempt/reactive, M6 naming, M7 alias) cannot be dismissed as stats hygiene.** M5 in particular is the single
  best defense: it is not statistics at all, it is an agent-trace-logging artifact that silently 2×'d a headline
  contrast, and it generalizes to anyone counting tool calls from harness logs. Lead the methodology section
  with M5 and M2.
- **Three traps (M1, M4, M10) ARE generic in their *technique* and survive only by their *framing* / the
  finding they produced.** A hostile reviewer WILL single these out. **Punch-list P3:** for M1/M4/M10, the
  paper must explicitly state the non-generic version (informed baseline / decisive-*cell* / the-sweep-that-
  killed-a-pole) and must not present them as "we used a null baseline / we did an ablation / we swept K."
- **The synthesis already contains the correct meta-rebuttal** (§2 closing: "agentic-recovery measurement is
  *unusually* prone to four specific lies"). **Punch-list P4: promote that sentence to the top of §2 / the
  abstract.** The contribution is "here are the four lies this construct invites and the controls that catch
  each," NOT "here are eleven good-practice tips." Stated that way, the catalog is contribution-worthy. Stated
  as a table of techniques, a mean reviewer reads it as a checklist and dings it.

**Q2 result: catalog is real and mostly non-obvious; the "standard caveats" attack is REBUTTABLE but the
rebuttal is currently implicit. Punch-list P3 (reframe M1/M4/M10 to their non-generic versions) + P4 (lead with
the four-lies thesis, lead the table with M5/M2).**

---

## Q3 — Does every refutation trace to its experiment? Any number that doesn't trace?

I read every load-bearing number in PAPER_SYNTHESIS back to the corresponding `experiment_result/result.md`.
**All cited experiments exist** (EXP-0007/0008/0009/0012/0019/0020/0022/0029/0031/0032/0033, plus EXP-0035 as
the CLAIM-0010 rigor re-check). **Traceability is excellent.** Specifics verified:

| Synthesis claim | Number | Traces to | Status |
|---|---|---|---|
| §1.1 occurrence washout | V 0.644→0.239, perm-p=0.164, φ 0.454→0.138 | EXP-0008 result.md | ✅ exact |
| §1.1 LOO-Brier | +0.087 (EXP-0007) → ≈0 | EXP-0008 (null improvement −0.0006; EXP-0007 +0.087) | ✅ exact |
| §1.2 error-class adds ≤0.2% | single-bit +0.0017, 3-level gate −0.0043; FULL +0.1002/40.1% | EXP-0012 result.md | ✅ exact |
| §1.2 LOCO −33%, within-REDIRECTABLE V=0.000 | −0.0826 (−33.0%); within-V 0.000 | EXP-0012 | ✅ exact |
| §1.3 routing-table refuted | per-class normH 0.738 vs global 0.714; collapse −0.024 | EXP-0019 | ✅ exact |
| §1.3 fine lift +0.09..+0.19 | +0.09 to +0.19 | EXP-0022 | ✅ exact |
| §1.3 coarse U 0.381→0.034 | 0.381 [0.310,0.472] → 0.034 [0.003,0.091] | EXP-0029 | ✅ exact |
| §1.4 Codex double-log → 152, 152/152 preempt | 304→152; 152/152 preempt | EXP-0033 | ✅ exact |
| §1.4 CC 66/66 → strict | CC reactive 5/43=0.116, preempt 34/43=0.791 | EXP-0033 (and CLAIM-0010/0011 final det.) | ✅ exact |
| §1.4 Gemini 2/9 | reactive 2/9, only named harness | EXP-0033 / EXP-0032 | ✅ exact |
| §3.1 per-gate shares ~1.0/0.27/0.25 | REDIRECTABLE 1.000 [0.610,1.000], GRANT 0.267, TRANSIENT 0.250 | EXP-0031 (Gemini per-gate) | ✅ exact |
| terminal pole window/class | term 0.53→0.16 (K 3→24), V=0.238 n.s. at K=6 | EXP-0020 | ✅ exact |
| EXP-0032 inventory discharge | Codex twin 442 calls, 41/41 available, 0 reactive | EXP-0032 | ✅ exact |

**Numbers that need a cross-reference but are NOT wrong (punch-list, traceability nits):**
- **N1 — "CC 66/66" vs the strict "2/43" vs "5/43".** The synthesis §1.4 says "CC's own 66/66 drops to 2/43
  under a uniform strict definition," while the abstract-level discussion and CLAIM-0010/0011 final dets use
  **5/43** (deduped strict) and **2/43** (EXP-0032 pre-dedup strict). Both are correct and both trace to
  EXP-0033's table, but the synthesis uses **2/43** in one place and the determination docs use **5/43** as the
  headline deduped figure. **A hostile reviewer will call this an inconsistency.** Pick ONE strict number for
  the headline (the deduped **5/43 = 0.116** is the right one — it's the post-M5 figure) and footnote the 2/43
  as the pre-dedup EXP-0032 value. This is the single most likely "gotcha" a reviewer will raise. **Fix it.**
- **N2 — the "66/68" vs "66/66" vs "68/68" REDIRECTABLE counts.** EXP-0031 reports CC 66/66; EXP-0029/CLAIM-0010
  reports the REDIRECTABLE cell as 68/68 (web_disabled=66 + input_filter=2, or 111 with the broader gate
  population). The synthesis uses 66/66 and 0/109 and 68/68 in different cells. These are different
  slices (66 = CC web blocks; 68 = REDIRECTABLE deterministic-modality cell; 109 = web_disabled failures;
  111 = REDIRECTABLE gate population in EXP-0029's larger parse). All trace, but the paper must **define each
  denominator once** in the corpus/methods section so a reviewer doesn't read drift. Currently the reader has
  to reconcile 66/68/109/111/142/152 across sections.
- **N3 — corpus size drifts across experiments** (EXP-0009 74 sess / EXP-0019 ~ / EXP-0022 79 sess,375 fails /
  EXP-0029 81 sess,384 fails). This is honestly the live corpus rotating up; each result.md notes it. But the
  paper presents one "corpus" — state the corpus-version drift explicitly (it's a rolling live `~/.claude`
  parse) so a reviewer doesn't think numbers were cherry-picked from different runs.

**Q3 result: every number traces; ZERO invented numbers. Punch-list N1 (unify the strict CC reactive figure on
5/43 = 0.116), N2 (define each denominator once), N3 (state the rolling-corpus version drift). These are
presentation/traceability nits, not integrity problems.**

---

## Q4 — Is the off-node interventional gap stated honestly as future work with a turnkey protocol, not hidden?

**YES — exemplary.** This is the strongest honesty signal in the package and a hostile reviewer cannot attack it:
- §1.5 and §4.3 state the single weakest link **in the body, not buried in limitations**: every causal-sounding
  claim is observational and confounded by a perfect on-node harness×model×error-naming alias.
- The synthesis names the exact blocker (OpenCode is the only model-agnostic harness on-node and it logs
  neither model nor tool outcomes — satisfies 0 of 6 required fields, per the PROTOCOL §7.3) and does NOT
  pretend the on-node work resolved causality.
- The turnkey resolver exists and is real: `CLAIM-0009_interventional_PROTOCOL.md` is a genuinely runnable,
  pre-registered spec — fixed cells C1-C6, byte-exact injection strings, locked N tiers (30/50/80) with a
  proper power analysis distinguishing the *easy* difference test (n≈15) from the *binding* equivalence test
  (n≥45-50 for a <0.3 margin), a confirmatory GLM with drop-one LRTs, and **pre-registered PASS/KILL thresholds
  with "no YELLOW."** This is exactly what a D&B reviewer wants to see attached to a negative result.

**The one thing a hostile reviewer WILL note (punch-list, not reject):** the paper claims the v2 factorial is
the *only* design that breaks the alias. **P5 — soften "only."** The PROTOCOL §7.1 itself lists SWE-agent and
OpenHands/OpenDevin as valid model-agnostic, fully-logged substitutes for the OpenCode pivot — so "only" is
slightly over-stated at the *design* level (the OpenCode-pivot factorial is one instantiation; the general
design is "any single model-agnostic harness hosting two models on an identical controlled block"). Say "the
factorial design (OpenCode/SWE-agent/OpenHands pivot)" rather than implying OpenCode is load-bearing.

**Q4 result: gap is honestly stated in-body with a real turnkey protocol. Punch-list P5 (soften "only the
OpenCode pivot" → the general model-agnostic-pivot design, naming the SWE-agent/OpenHands fallbacks already in
the protocol).**

---

## Q5 — Over-claims: does it anywhere assert a POSITIVE prediction it refuted?

**NO. I specifically hunted for this and found none.** This is the test a negative-result paper most often fails,
and the synthesis passes it:
- It never re-asserts "error-class predicts occurrence" (refuted §1.1) as if true elsewhere.
- It never re-asserts "error-class predicts modality" beyond the explicitly-bounded 1-bit gate fact (§1.2/§3.1
  are careful: "modality is a 1-bit routing fact *within a harness*" — the within-harness scope is preserved
  every time).
- It never re-asserts "harness routing determines modality" — §3.2 and §1.4 explicitly list it as
  largely-refuted/unresolved, and §4.3 ties the causal version to the off-node gap. The headline survivor
  one-sentence (§3.2) even *negates* it inline: "NOT shown to be harness-routing-determined."
- The "two-layer" architecture is consistently presented as **deflated** (§1.3), never re-promoted.
- M7/M9 (alias diagnosis, anti-tautology delta) are structurally present *precisely to prevent* the over-claim,
  and they do their job.

**The closest thing to an over-claim** is the word **"harness-agnostic"** applied to the surviving gate taxonomy
(§3.1, §6) — but this is a *generalization-breadth* claim about a descriptive taxonomy, not a re-assertion of a
refuted *predictive* claim. It is covered by punch-list P2 (qualify given n=2/n=9 legs). It does not rise to an
over-claim of a refuted prediction.

**Q5 result: NO over-claim of any refuted positive prediction. The negative-result discipline is intact
throughout. Only the descriptive "harness-agnostic" breadth needs the P2 qualifier.**

---

## GO / NO-GO VERDICT

**GO — submission-ready after a minor-revisions punch-list.** As a hostile reviewer I cannot find a reject-level
defect: the framing is in-scope, the refuted/survives boundary is honest and precise, every number traces to a
real experiment with zero fabrication, the methodology rebuts the "standard caveats" attack (decisively on M5/M2/
M8/M6/M7, framing-dependently on M1/M4/M10), the off-node gap is stated in-body with a genuinely turnkey
pre-registered protocol, and there is no over-claim of a refuted prediction. The defects are presentational and
cross-referential, not integrity defects.

### PUNCH-LIST (ordered by reviewer-attack severity)

1. **N1 (must-fix, highest gotcha-risk):** unify the strict CC reactive-redirect headline number. Use the
   **deduped 5/43 = 0.116** everywhere; footnote 2/43 as the pre-dedup EXP-0032 value. The current 2/43-vs-5/43
   split between the synthesis and the determination docs is the single most likely "inconsistent numbers"
   reviewer ding.
2. **P4 (must-fix for the methodology to land):** lead §2 and the abstract with the **"four specific lies"
   thesis** (lower-bound outcome defs / one-cell-carried effects / duplicate-log inflation / harness-model-
   error-text collinearity), and lead the M-table with **M5 (double-log) and M2 (LOSO-vs-LOCO)** — the two
   traps no reviewer can call generic. Currently the contribution-defining sentence is buried under the table.
3. **P3 (should-fix):** reframe **M1, M4, M10** to their non-generic versions in the text (informed baseline /
   decisive-*cell* ablation / "the sweep that killed the terminal pole"). As written, a mean reviewer singles
   these three out as textbook caveats. The findings they produced are domain-specific; the framing must say so.
4. **N2 (should-fix):** define each denominator (66 / 68 / 109 / 111 / 142 / 152) **once** in the corpus/methods
   section so the reader never reconciles drifting counts across sections.
5. **P1 (should-fix):** state plainly in §3.1 that the surviving *positive* gate taxonomy is largely non-novel
   on its own (EXP-0008/MAP-0002 + LangGraph generic pre-emption) — pre-empt the "your only survivor is prior
   art" attack by clarifying the contribution is the *negative result + methodology*, with the taxonomy as the
   conditioning variable the methodology vindicates.
6. **P2 (should-fix):** soften "harness-agnostic" → "structurally recurrent across the three harnesses sampled
   (REDIRECTABLE leg thin on Codex n=2 / Gemini n=9)."
7. **N3 (nice-to-have):** state the rolling live-corpus version drift (74→81 sessions across experiments) once,
   so cross-experiment count differences aren't read as cherry-picking.
8. **P5 (nice-to-have):** soften "the v2 factorial is the *only* resolver" → "the model-agnostic-pivot factorial
   design (OpenCode / SWE-agent / OpenHands)," consistent with PROTOCOL §7.1's own fallbacks.

**None of the eight blocks a submission on its own.** N1 + P4 are the two that most affect a reviewer score;
the rest harden it against a determined hostile reviewer. With N1 and P4 done, this is a defensible D&B
negative-result + methodology submission.
