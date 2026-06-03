# COMMITTEE#2 (FINAL) — CLAIM-0048 (PROJ-0018, eval-and-safety) — two-pass complete, L0+REAL-DATA-L1 in hand
## FINAL verdict (green/yellow/red). The L1 ecological result is the load-bearing new evidence. Vote HONESTLY by role. This is the strongest candidate of the v3 expansion — but do NOT green it if the in-the-wild inversion being undemonstrated is disqualifying; do NOT red a genuinely real+novel ecological finding just because the live demo needs an L2.

## TWO-PASS TRAIL: L0(EXP-0050) HELD both parts in SIM -> committee#1 VERDICT-0046 YELLOW (5/5, NO fatal/RED: mechanism real but = spoiler-effect/Duverger vote-splitting applied to eval-canonicalization; gated on a REAL-DATA L1) -> L1(EXP-0051, cost-aware staged) -> THIS committee#2.

## L0 (EXP-0050, simulation): canonicalizer RECALL has a SIGN-FLIPPING effect on maj@k self-consistency accuracy, governed by correct-vs-incorrect FRAGMENTATION ASYMMETRY phi. Sign-flip at FIXED precision z=-19.8 (phi<<0, recall HURTS) / +41.6 (phi>>0, recall helps) = PURE RECALL (precision-control passed z=-28.2). Ranking inversion CONSTRUCTED (two fixed models, |z|=48/53) — FLAGGED EXPLORATORY (post-hoc retune 0.42/0.46->0.50/0.28).

## L1 (EXP-0051, REAL DATA — the load-bearing new evidence):
STAGE-A GATE PASSED (the cost-aware ecological gate):
  - (b) THE MAKE-OR-BREAK NUMBER: real numeric/sympy (Minerva-style) grader PRECISION q = 1.0000 on BOTH GSM8K + MATH-500 (239881+4983 merged pairs all TRUE; ZERO adversarial false-merges: 18 != 18.5, 1/3 != 0.33, frac14/3 != frac15/3). Real numeric normalizers map to EXACT Rational/sympy values => genuinely high-precision. This RETIRES committee#1's biggest worry — the L0 q<=0.6 wash-out death-zone does NOT apply to real graders.
  - (a) real phi-asymmetry: MATH-500 strong phi<<0 (median ~-1.0 to -1.2, 86-90pct problems |phi|>0.2, almost all negative = correct CONCENTRATED H_C~1.15 / errors FRAGMENTED H_W~2.0) = EXACTLY the recall-HURTS regime. GSM8K phi~0 (symmetric, integer answers). So the foothold is REGIME-SPECIFIC to rich-symbolic-answer evals.
STAGE-B (real-model maj@k, Qwen2.5-0.5B vs 7B, 150 real GSM8K, k=16, temp0.8, H100): RANKING-INVERSION = HONEST NULL (no flip; 7B wins under both graders; numeric grader barely moves acc 0.480->0.487 / 0.780->0.780, collapses ~6-8pct buckets). This null is PREDICTED by Stage A (GSM8K phi~0 => no asymmetry => recall swap CANNOT flip rankings) and CONFIRMS the phi-governs-the-sign mechanism rather than refuting it. BUT: the in-the-wild ranking-inversion DEMONSTRATION remains UNACHIEVED — GSM8K was the wrong regime; a real inversion needs an L2 (MATH oxed{} extractor + symbolic benchmark + 2 models of differing answer-surface concentration + larger k).

## RESIDUAL GAPS (weigh honestly): (1) Stage-A phi uses REAL gold strings but MODELED answer-FREQUENCIES (real-model-sample phi on MATH is the open item; Stage-B gave real frequencies only on GSM8K=wrong-regime). (2) the headline leaderboard-INVERSION is shown only in SIM (L0, exploratory) + predicted-but-not-demonstrated on real data. (3) mechanism = spoiler-effect/Duverger applied to eval (novel DOMAIN-APPLICATION, committee#1 already established not-a-new-mechanism).

## THE VERDICT QUESTION (decide by role):
(a) GREEN: a validated novel domain-application — canonicalizer-recall is a REAL, high-precision-grader-relevant, phi-governed sign-flipping lever on symbolic-answer self-consistency evals; q=1.0 + MATH phi<<0 are real and decisive; the GSM8K null is confirmatory. (Risk: the in-the-wild INVERSION is undemonstrated + phi-frequencies proxy.)
(b) YELLOW: real + ecologically-founded but the headline leaderboard-inversion is undemonstrated in-the-wild AND phi-frequencies are still proxy -> needs an L2 (real MATH inversion) before validation.
(c) RED: too incremental over spoiler-effect/Wang2022/Bulian2022 given the live inversion isn't shown.
MANDATORY BASELINES (committee#1): spoiler-effect/Duverger, Bulian2022-BEM, Kuhn2023/Farquhar2024-semantic-entropy, Biderman2024.

## CLAIM YAML
claim: "Increasing an answer-equivalence canonicalizer's RECALL (how aggressively\
  \ it merges truly-equivalent free-form answers before a self-consistency majority\
  \ vote) does NOT monotonically improve maj@k accuracy: its sign is governed by the\
  \ correct-vs-incorrect FRAGMENTATION ASYMMETRY of the model's answer distribution.\
  \ When incorrect mass is concentrated on one dominant wrong attractor while correct\
  \ mass is fragmented across equivalent surface forms, raising canonicalizer recall\
  \ RAISES accuracy; but when the asymmetry is reversed (correct near-canonical, errors\
  \ fragmented), raising recall LOWERS maj@k accuracy and can INVERT the maj@k ranking\
  \ of two models that a lower-recall canonicalizer ranked the other way \u2014 a\
  \ harness-induced ranking hazard with the model and samples held fixed."
why_it_matters: "FRESH AREA (eval-and-safety: self-consistency x answer-extraction\

## L1 RESULTS (EXP-0051)
# RESULTS — EXP-0051 (L1, REAL DATA) / CLAIM-0048
**Researcher:** researcher-0049. **Node:** cli:dengcchi-mac (Stage A, CPU). Stage B (if run) cli:devgpu014 (H100).
**Mandate:** establish ECOLOGICAL plausibility of the L0 sign-flip (EXP-0050) on REAL benchmark data.
**Convention (matches L0):** phi = H_C − H_W. phi≪0 = correct CONCENTRATED / errors FRAGMENTED ⇒ raising recall HURTS. phi≫0 ⇒ recall HELPS.
**GT:** gold-anchored — two answer strings are truly-equivalent iff both parse to the same gold value. Canonicalizers read ONLY strings; q measured vs this GT.

## DATA SOURCE (REAL)
- **GSM8K test** — 1319 real problems (openai/grade-school-math test.jsonl). Gold = integer final answers parsed from `#### N`.
- **MATH-500** — 500 real problems (HuggingFaceH4/MATH-500 test.jsonl). Gold = `\boxed{}` answers: integers, fractions (`\frac{14}{3}`), radicals (`3\sqrt{13}`), `\pi`, etc. (404 of 500 parse to a numeric value; the rest are symbolic/text and excluded from phi).
- **FLAGGED proxy element:** Stage A has no real model-sample *frequencies*, so per-problem answer *distributions* are generated from REAL surface-form formats (the documented $/comma/decimal/`\frac`/`/`-fraction variety) over the REAL gold values plus realistic distinct wrong values. Stage B replaces these with real model samples. The two LOAD-BEARING quantities (q, and the H_C vs H_W structure) are anchored in real gold strings.

## REAL CANONICALIZER PAIR (canon.py)
- **EXACT-MATCH** (low recall): byte-equal after strip.
- **LEXICAL** (intermediate): lowercase, strip `$`,`,`, units, whitespace, trailing `.0`.
- **NUMERIC / Minerva-style** (HIGH recall): strip `$`/commas/units/`^\circ`/`\text{}`; parse ints, decimals→exact `Rational`, `a/b`, `\frac{a}{b}`, `\sqrt{n}`, `k\sqrt{n}`, `\pi` multiples via **sympy**; merge iff identical canonical value. Verified: `$18`=`18 dollars`=`18.0`=`18`; `\frac{14}{3}`=`14/3`; `\frac{1}{2}`=`0.5`=`0.50`=`1/2`; `90^\circ`=`90`; `3\sqrt{13}`→`3*sqrt(13)`.

---

## STAGE A — THE DECISIVE ECOLOGICAL GATE

### (b) EMPIRICAL PRECISION q of the high-recall normalizer — THE MAKE-OR-BREAK NUMBER (results/precision_recall.csv)
| dataset | empirical q | merged pairs | over-merges | recall: exact / lexical / numeric |
|---|---|---|---|---|
| GSM8K   | **1.0000** | 239,881 | **0** | 0.000 / 1.000 / 1.000 |
| MATH-500| **1.0000** | 4,983   | **0** | 0.000 / 0.485 / 1.000 |

- **q = 1.0000 on BOTH real datasets** — the numeric normalizer NEVER collapses two *distinct real gold values* into one bucket. Far above the L0 wash-out threshold (effect dies at q≤0.6).
- **Adversarial precision** (gold vs surface-CLOSE wrong values: `18` vs `18.5`/`19`, `1/3` vs `0.33`, `\frac{14}{3}` vs `\frac{15}{3}`): **ZERO false merges** on both datasets. Real numeric normalizers are genuinely high-precision because they map to exact `Rational`/sympy values, not lossy decimals.
- **Recall genuinely differs:** exact-match merges 0.000 of true-equivalent surface pairs (misses ALL of `$18`/`18 dollars`/`18.0`); numeric merges 1.000. On MATH the lexical normalizer only reaches 0.485 — so we have a REAL low→high recall pair, both high-precision. ⇒ **q-side of the gate PASSES decisively.**

### (a) EMPIRICAL PHI — is the fragmentation asymmetry real? (results/phi.csv; symmetric surface treatment: correct & wrong values use the SAME surface generator, so phi is NOT baked in)
| dataset | error regime | mean phi | median phi | H_C | H_W | frac \|phi\|>.2 | dir |
|---|---|---|---|---|---|---|---|
| GSM8K    | errors-fragmented (3–8 wrong vals) | +0.257 | +0.209 | 2.30 | 2.04 | 0.51 | mild + |
| GSM8K    | errors-concentrated (1–2)          | +0.031 | +0.021 | 2.29 | 2.26 | 0.07 | ~0 (symmetric) |
| GSM8K    | mixed (1–6)                        | +0.152 | +0.088 | 2.29 | 2.14 | 0.30 | mild + |
| MATH-500 | errors-fragmented (3–8)            | **−0.843** | **−0.986** | 1.16 | 2.00 | **0.93** | **strong −** |
| MATH-500 | errors-concentrated (1–2)          | **−1.033** | **−1.227** | 1.15 | 2.19 | **0.96** | **strong −** |
| MATH-500 | mixed (1–6)                        | **−0.925** | **−1.128** | 1.15 | 2.07 | **0.94** | **strong −** |

**Finding — the asymmetry is REAL but DATASET-STRUCTURED (not universal):**
- **MATH-500: strong, robust phi ≪ 0** (median ≈ −1.0 to −1.2; 86–90% of problems phi<−0.2). Correct answers are CONCENTRATED (a simple value with few surface forms, H_C≈1.15) while the wrong-answer mass FRAGMENTS across many distinct fractional/symbolic values (H_W≈2.0). Per the L0 prediction, **this is exactly the phi≪0 regime where raising canonicalizer recall HURTS maj@k** (z=−19.8/−28.2 in L0). The foothold EXISTS in real symbolic-answer math.
- **GSM8K: phi ≈ 0 (symmetric).** Integer answers carry uniform rich surface variety, so H_C≈H_W and the sign-flip has little foothold; raising recall is near-neutral/mildly helpful. No HURTS regime.

**Honest caveat:** the *magnitude/sign* of phi is sensitive to surface-form modeling (GSM8K mean phi moved +0.86→+0.26 when correct & wrong got symmetric surface treatment). phi here is **structural/proxy** — it reflects how the canonicalizer clusters real gold values into surface forms, NOT measured model-sample frequencies. That is precisely the residual risk Stage B is designed to retire.

### DOM_FRAC SENSITIVITY
Across error-spread regimes (1–2, 1–6, 3–8 distinct wrong values per problem) the MATH-500 phi≪0 conclusion is STABLE (median −0.99 → −1.23). GSM8K stays ≈0→mildly-positive. The direction is set by dataset answer-space structure, not by the error-spread hyperparameter.

## STAGE-A GATE DECISION: **PASS**
Pre-committed gate = (phi-asymmetry real) AND (high-recall q > 0.6, with margin q≥0.80).
- q = **1.0000** on both real datasets, 0 adversarial false merges ⇒ q-condition met with maximal margin.
- phi-asymmetry is **real and substantial on MATH-500** (median phi≈−1.0, 86–90% asymmetric, in the recall-HURTS direction) ⇒ phi-condition met on real symbolic-math QA.
**The L0 sign-flip HAS an ecological foothold:** real numeric graders are high-precision (so the effect is NOT washed out by over-merge), AND real symbolic-answer benchmarks (MATH) exhibit the correct-concentrated/errors-fragmented asymmetry the negative-slope regime requires. On integer-only QA (GSM8K) the asymmetry is weak (symmetric), so the hazard is dataset-specific — concentrated in rich-symbolic-answer-space evals.

---

## STAGE B — REAL model-pair maj@k ranking inversion (GATED THROUGH; run on devgpu014 H100)
Stage A passed the gate, so we ran the expensive stage. **REAL models, REAL samples, FIXED.**
- **Models:** Qwen2.5-0.5B-Instruct vs Qwen2.5-7B-Instruct (both genuine vLLM 0.22 inference on H100, bf16, gpu_mem 0.55, sequential, os._exit). 0.5B weights fetched via fwdproxy; 7B from cache.
- **Benchmark:** 150 random REAL GSM8K test problems, k=16 samples/problem at temp=0.8, top_p=0.95, seed=0. Final answers extracted from `#### N`. (2 of 2400 / 4 of 2400 empty extractions — negligible.)
- **Graders:** EXACT-MATCH vs the same high-recall NUMERIC/Minerva normalizer (canon.py). maj@k = does the plurality-voted *value bucket* equal the gold value.

| model | maj@k EXACT | maj@k NUMERIC | distinct buckets (exact→numeric collapse) |
|---|---|---|---|
| Qwen2.5-0.5B | 0.480 | 0.487 | 1427 → 1338 (89) |
| Qwen2.5-7B   | 0.780 | 0.780 | 522 → 479 (43) |

- **EXACT grader:** 7B beats 0.5B by +0.300. **NUMERIC grader:** 7B beats 0.5B by +0.293.
- **RANKING INVERSION: NO — HONEST NULL.** The grader swap does NOT flip the model ranking; 7B wins decisively under both.

### Why the null (and why it's consistent with Stage A, NOT a refutation):
The numeric grader barely moves accuracy (0.480→0.487 for 0.5B; 0.780→0.780 for 7B) and collapses only ~6%/8% of surface buckets. **GSM8K's integer-answer regime produces almost no fragmentation asymmetry** — exactly Stage A's finding (GSM8K **phi ≈ 0**). With no asymmetry to exploit, raising canonicalizer recall is near-neutral and CANNOT flip rankings. The L0 sign-flip's foothold is the **phi≪0 symbolic-answer regime (MATH, where Stage A found median phi ≈ −1.0)** — which integer GSM8K does not provide. The null is therefore the PREDICTED outcome on this benchmark, and it CONFIRMS rather than contradicts the phi-governs-the-sign mechanism. A positive Stage-B inversion would require a symbolic-answer benchmark (MATH/competition) with a robust answer-extractor + larger k — specified below for L2.

### WHAT AN L2 / STAGE-B+ NEEDS for a real inversion demonstration:
1. A **symbolic-answer benchmark** (MATH, MATH-500, or competition math) where the high-recall numeric grader genuinely recovers many true equivalences exact-match misses (`\frac{14}{3}`=`14/3`, `0.5`=`1/2`, `3\sqrt{13}`) — i.e. the phi≪0 regime Stage A measured on real MATH answers.
2. A robust **`\boxed{}` answer extractor** + the numeric/sympy grader applied to free-form model output.
3. **Two models with different answer-surface concentration** (e.g. one verbose/varied-format, one terse/canonical) so the grader swap differentially helps one — the in-the-wild spoiler analogue.
4. Larger k (32–64) and ≥300 problems for tight maj@k CIs.

## ARTIFACTS
- PRE_REGISTRATION.md (committed BEFORE running)
- canon.py — real EXACT / LEXICAL / NUMERIC(Minerva,sympy) canonicalizers
- stage_a.py, stage_a_phi.py — Stage-A precision/recall + phi measurement
- stage_b.py — real model-pair maj@k inversion runner (vLLM, H100)
- results/precision_recall.csv, results/phi.csv, results/stage_b_summary.json

## DISPOSITION
**KEEP-EXPLORING (lean SUPPORT on ecology, NULL on the in-the-wild inversion demonstration).**
- The L0 sign-flip HAS a real ecological foothold: real numeric graders are **high-precision (q=1.0, 0 adversarial over-merges)** — they do NOT wash out the effect (the L0 q≤0.6 death-zone does not apply to real numeric normalizers); AND real **symbolic-answer math (MATH-500) exhibits the phi≪0 correct-concentrated/errors-fragmented asymmetry** (median ≈ −1.0, 86–90% of problems) that the recall-HURTS regime requires.
- BUT the hazard is **dataset-specific**: integer-answer QA (GSM8K) is phi≈0 (symmetric), so the effect has little foothold there — confirmed by the Stage-B real-model NULL (no ranking inversion on GSM8K).
- The in-the-wild ranking-inversion DEMONSTRATION was NOT achieved (GSM8K is the wrong regime); it requires a symbolic-answer benchmark with a real extractor (L2 spec above). The phi-measurement uses real gold strings but proxy answer-*frequencies*; real model-sample phi on MATH is the remaining gap.
- **FLAGS:** L0 inversion construction = EXPLORATORY (post-hoc retune). Stage-A wrong-answer *surface multiplicity* is a flagged proxy; q and the H_C-vs-H_W dataset structure are anchored in real gold strings; Stage-B uses fully real model samples.

## CITATIONS
- Spoiler effect / Duverger's Law (vote-splitting) — mechanism analogue.
- Bulian et al. 2022, "Tomayto Tomahto..." (BEM / answer-equivalence beyond exact match).
- Kuhn et al. 2023; Farquhar et al. 2024 — semantic entropy (answer-meaning clustering).
- Biderman et al. 2024 (arXiv:2405.14782) — evaluation reproducibility / scoring sensitivity.

## ORCHESTRATOR POSTURE: NOT pushing for green. The L1 is honest: the ecological FOOTHOLD is real (q=1.0 + MATH phi<<0) but the in-the-wild INVERSION is undemonstrated (Stage-B null on the wrong regime). My read = this is most defensibly a YELLOW gated on an L2 (real MATH inversion) — but if the committee judges q=1.0 + real-MATH-phi<<0 + the confirmatory-null is ALREADY a validated domain-application contribution, GREEN is defensible; if it judges the undemonstrated live inversion + proxy-frequencies make it too incremental over spoiler-effect, RED. Real 6/6 by role. Lightweight: whatever the verdict, PROJ-0018 then converges (this is the single claim).
