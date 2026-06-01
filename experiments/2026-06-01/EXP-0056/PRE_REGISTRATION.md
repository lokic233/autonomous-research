# EXP-0056 PRE-REGISTRATION — Error-Fork KV Fragmentation (PROJ-0010 / CLAIM-0021)

**Status: LOCKED. Written and committed BEFORE the main analysis run.**
**Agent:** researcher-0021-L0-r7 · **Sub-monitor:** sub-monitor-0010-r7 · **Date:** 2026-06-01

## HONEST-NEGATIVE IS FIRST-CLASS
A clean negative (any load-bearing gate fails) is a fully successful, publishable outcome. This experiment
is **pass-or-kill on the gates as written below**. I will NOT tune thresholds, re-define labels post-hoc, or
force a positive. If the corpus is underpowered for a family (n<3 sessions, or degenerate label variance), I
will say so explicitly and SKIP — not invent. Decimal thresholds, the label definition, and the overall kill
rule are frozen by this commit.

## THESIS (CLAIM-0021)
In cross-session RadixAttention prefix sharing, a tool ERROR injects a high-entropy result + corrective
reasoning. The error subtree is rarely reproduced by a future session (errors nondeterministic), so prefill
DOWNSTREAM of an early error may be **permanently forked out of the shared tree** UNLESS the agent re-converges
to canonical state. The **LOAD-BEARING NOVEL** claim is **RE-B1 re-convergence** (a cross-session error-RESULT-
identity recurrence property absent from PROJ-0007). The load-bearing DISTINCTION from DEAD-0015/PROJ-0007:
error forks are **nondeterministic-IRREPRODUCIBLE**, vs PROJ-0007's canonicalization-RECOVERABLE drift.

## OPERATIONAL MODEL (frozen)
- Reuse EXP-0054 `parse_cc_session` / `parse_codex_session` JOIN layer verbatim: tool_use→tool_result by id
  (CC); function_call→function_call_output by call_id w/ dedup (Codex). Each call carries
  `name, inp, args_str, sig=name\0canon_args, result, is_error, start_pos, end_pos, footprint`.
- **Corpus filter:** sessions with ≥8 tool calls (MIN_TRIALS=8), same as EXP-0054.
- **First-error index** per session = index of first call with `is_error=True`. "Downstream of first error" =
  all calls with index > first-error index. Footprint = chars(args)+chars(result).
- **Shareability (cross-session, multiset-membership proxy for the radix tree — ceiling acknowledged in
  analysis):**
  - `pool_all[sig]` = set of sessions in which `sig` appears anywhere.
  - `pool_preerr[sig]` = set of sessions in which `sig` appears in that session's PRE-error region (before its
    first error). This is the "canonical / reproducible" shared-tree pool.
  - A call is **non-shareable** iff its `sig` appears in NO OTHER session's `pool_all` (cross-session-unique).
  - A post-error call **re-converges** iff its `sig` ∈ `pool_preerr` of ≥1 OTHER session (re-enters the
    canonical shared tree).
  - **error-RESULT identity** key = `sig \0 result_text` (exact). A post-error error-call's error-result
    "recurs" iff this exact key appears in ≥1 OTHER session.
- **Entropy proxy** = Shannon entropy (bits/char) over the char distribution of the result text.
  **Length-residualized** = residual of OLS regression of entropy on `log1p(len(result))` across all results.
- All statistics hand-rolled stdlib (logistic ridge, Mann-Whitney AUC, session-clustered bootstrap). NO
  numpy/torch. Target wall < 15 s. `random.seed(20260601)`. Deterministic md5 folds.

## PRE-REGISTERED GATES (thresholds LOCKED)

### RE-B0 — magnitude floor (FLOOR GATE)
Mean over error-bearing sessions of (downstream-of-first-error footprint / total session footprint).
**PASS iff mean ≥ 0.20** (live reference 0.63). If < 0.20, the downstream region is too small to matter →
kill. Report mean + median + n_error_sessions.

### RE-B1 — re-convergence reality check (LOAD-BEARING NOVEL)
Over all post-error calls (across error-bearing sessions):
- `sig_reconv_rate` = fraction whose `sig` ∈ another session's `pool_preerr` (count-weighted) + footprint-
  weighted variant, with session-clustered 2000× bootstrap 95% CI.
- `errresult_recur_rate` = over post-error **error-calls**, fraction whose exact `sig\0result` recurs in ≥1
  OTHER session, with CI.
Interpretation (frozen):
- If `errresult_recur_rate` is HIGH (point ≥ 0.50) → same errors recur across sessions → error subtrees ARE
  re-shared → "permanently forked" WEAKENED (push toward kill of the novel claim).
- If `sig_reconv_rate` ≈ 1.0 (LB95 ≥ 0.95) → post-error prefill benign / fully re-converges → **CLEAN KILL**.
- The novel claim is SUPPORTED only if post-error segments are substantially non-re-converging
  (`sig_reconv_rate` point < 0.80) AND error-results are largely irreproducible (`errresult_recur_rate`
  point < 0.50). This is a REPORTED reality check; the binding pass/kill is RE-B2 + RE-B2b + RE-B3.

### RE-B2 — predictive killer over JOINT baseline (LOAD-BEARING KILLER)
Session-level logistic. **Label** = 1 iff session's NON-SHAREABLE footprint FRACTION (non-shareable
footprint / total session footprint) is in the TOP HALF (strictly above the corpus median) — a pure
cross-session sharing property, computed independently of the error features.
- **B0** (joint cadence baseline) = {mean log1p(inter-call gap_tok), mean log1p(tool_freq), tool-class mix
  (READ/MUT/VOL fractions)}.
- **B1** = B0 + error features {first-error position fraction (=1.0 if no error), log1p(#errors), first-error
  tool-class one-hot, length-residualized error-result entropy proxy (=0 if no error)}.
- `dAUC = AUC(B1) − AUC(B0)` under session-clustered 5-fold CV held-out scores, 2000× session-clustered
  bootstrap.
- **PASS iff `dAUC_LB95 > 0` AND `dAUC_point ≥ 0.03`.** If ≤ 0 → non-shareability fully explained by ordinary
  cadence → clean negative.
- Reported alongside: fold-to-fold dAUC std, **sign-stability (ALL 5 folds dAUC > 0 required for PASS)**,
  Herfindahl of positive-class footprint mass (**> 0.2 ⇒ FLAG** 2–3-session domination, downgrades any PASS to
  a flagged/yellow result).
- **Underpower rule:** if n_sessions < 30 OR positive-class variance degenerate OR any fold lacks both classes
  → mark `degenerate/underpowered`, report descriptively, and the gate does NOT PASS.

### RE-B2b — matched-success-divergence baseline (THE yellow→green UPGRADE GATE)
Build a CONTROL group of SUCCESSFUL calls matched to error calls by (result length bucket, entropy bucket).
For each group, compute the **downstream non-shareable fraction** = (footprint of non-shareable calls in the
≤K-call window AFTER the index call) / (total footprint in that window), K=BLOCK window of the next 8 calls.
- `delta_b2b = mean(error-group non-shareable frac) − mean(matched-success non-shareable frac)`, with
  session-clustered 2000× bootstrap CI.
- **PASS (upgrade to green) iff `delta_b2b` LB95 > 0** (error group's downstream is significantly MORE
  non-shareable than matched successes). If the CI includes 0 → "error-fork" effect is statistically
  INDISTINGUISHABLE from ordinary trajectory divergence → thesis **FALSIFIED as ordinary divergence**
  (clean negative / yellow-not-green).
- Underpower rule: if matched n < 3 per group → SKIP with explicit note.

### RE-B3 — cross-instrument replication (HARD GATE)
Run the full pipeline on Codex traces. **SIGN AGREEMENT REQUIRED for PASS** on the two load-bearing effects:
(a) RE-B2 `dAUC_point` sign, and (b) RE-B2b `delta_b2b` sign. If either corpus is underpowered (n<3), report
and the HARD GATE cannot be satisfied (no PASS without cross-instrument sign agreement).

### OVERALL DISPOSITION RULE (frozen kill rule)
- **GREEN (claim supported, upgrade):** RE-B0 PASS **and** RE-B2 PASS **and** RE-B2b PASS **and** RE-B3 sign
  agreement **and** RE-B1 reality-check consistent (not ~100% re-convergence, not ≥0.50 error-result
  recurrence) **and** no Herfindahl flag.
- **YELLOW (partial):** RE-B0 PASS and RE-B2 PASS and RE-B3 agreement, but RE-B2b CI includes 0 OR Herfindahl
  flag OR RE-B1 partially weakens — mechanism present but not distinguished from ordinary divergence /
  domination-flagged.
- **KILL (clean negative):** RE-B0 fails, OR RE-B2 dAUC ≤ 0 / LB95 ≤ 0 / not all folds positive, OR RE-B2b
  falsified, OR RE-B3 sign disagreement, OR RE-B1 shows ~100% re-convergence or ≥0.50 error-result recurrence.
- Underpowered families are reported as underpowered and CANNOT contribute a PASS.

## PRIOR-ART / NON-OVERLAP (arXiv IDs re-verified live 2026-06-01)
- **SGLang RadixAttention / HiCache** — arXiv **2312.07104** ("SGLang: Efficient Execution of Structured
  Language Model Programs", Zheng et al.). Verified live via external search. RadixAttention shares KV across
  requests via a radix tree keyed on token prefixes; HiCache adds hierarchical (CPU/GPU) cache tiers. It
  assumes divergence is task-content-driven and does NOT model tool errors as a distinct non-shareable fork
  class nor measure a cross-session re-convergence rate.
- **vLLM PagedAttention / Automatic Prefix Caching (APC)** — arXiv **2309.06180** ("Efficient Memory
  Management for Large Language Model Serving with PagedAttention", Kwon et al.). Verified live. APC reuses
  identical prompt prefixes across requests; again error-agnostic, no re-convergence accounting.
- **Internal RE-B7/RE-B8** (if present in PROJ-0010 charter lineage): error-aware shareability variants —
  this EXP states non-overlap by measuring the cross-session error-RESULT-identity recurrence rate, which
  neither OSS system nor the byte-identical line (DEAD-0016) measures.
- **Non-collision with our own line:** NOT PROJ-0003 (failure attribution/recovery cause — we measure KV-cache
  SHAREABILITY cost, not cause/recovery). NOT DEAD-0015/PROJ-0007 (canonicalization-recoverable drift — our
  forks are error nondeterminism, NOT canonicalizable; that is the load-bearing distinction). NOT DEAD-0016
  (byte-identical interior repeats). NOT EXP-0054/CLAIM-0018 (within-session redundant prefill tax). No
  decode-time speculative decoding.

## FROZEN CONSTANTS
MIN_TRIALS=8 · CHARS_PER_TOK=4.0 · NBOOT=2000 · NFOLD=5 · L2=1.0 · GD_ITERS=400 · GD_LR=0.3 ·
B2b_WINDOW_K=8 calls · RE-B0 floor=0.20 · RE-B2 dAUC floor=0.03 & LB95>0 & all-5-folds>0 ·
Herfindahl flag>0.20 · RE-B1 reconv-kill LB95≥0.95, errresult-recur-kill point≥0.50 · seed=20260601.
