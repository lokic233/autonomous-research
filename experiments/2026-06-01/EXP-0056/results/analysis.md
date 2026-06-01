# EXP-0056 — Error-Fork KV Fragmentation: CLEAN NEGATIVE (CLAIM-0021 KILLED)

**PROJ-0010 / CLAIM-0021** · researcher-0021-L0-r7 · sub-monitor-0010-r7 · 2026-06-01
**Disposition: KILL (clean negative).** Wall 3.75 s. Pre-registration locked + committed (ros HEAD 384bcaf)
BEFORE this run; all thresholds frozen. Honest-negative is first-class — no gate was tuned.

## TL;DR
The thesis — that tool errors create a *predictable, error-specific* class of permanently-non-shareable
post-error prefill in cross-session RadixAttention — is **falsified as ordinary trajectory divergence**. The
load-bearing upgrade gate **RE-B2b** shows error-group downstream non-shareability is **statistically
indistinguishable** from length/entropy-matched successful calls (CC delta −0.071, codex +0.010; both CIs
include 0). The predictive gate **RE-B2** adds **no** signal over the joint cadence baseline (CC dAUC +0.007
LB95<0, not all folds positive, Herfindahl-flagged; codex dAUC −0.082 LB95<0). The cross-instrument **RE-B3**
hard gate fails on **sign disagreement** for both load-bearing effects. The premise floor RE-B0 passes and
RE-B1 re-convergence is near-zero — but that near-zero is the *universal base rate*, not an error effect (see
"The RE-B1 trap" below). Net: errors are **not** a distinct KV-fork class; cross-session divergence is
task-content-driven exactly as SGLang/vLLM already assume.

## Corpus
- CC: 64 sessions (≥8 tool calls), 39 error-bearing; 1,630 post-error calls (182 post-error error-calls).
- Codex: 83 sessions, 65 error-bearing; 2,081 post-error calls (74 post-error error-calls).
- Reused EXP-0054 `parse_cc_session`/`parse_codex_session` JOIN layer verbatim (tool_use→tool_result by id;
  function_call→function_call_output by call_id w/ dedup), plus its hand-rolled logistic / Mann-Whitney AUC /
  session-clustered bootstrap. No numpy/torch.

## Per-gate verdicts

| Gate | CC | Codex | Threshold | Verdict |
|---|---|---|---|---|
| **RE-B0** magnitude floor (mean downstream-of-1st-error footprint frac) | 0.633 | 0.921 | ≥0.20 | **PASS** both (premise holds: downstream region is large) |
| **RE-B1** sig re-convergence rate (count / footprint) | 0.025 / 0.015 | 0.000 / 0.000 | report+CI | near-zero (see trap) |
| **RE-B1** error-RESULT identity recurrence | 0.038 | 0.000 | report+CI | near-zero |
| **RE-B2** dAUC(B1−B0), session CV | +0.007 (LB −0.080) | −0.082 (LB −0.182) | LB95>0 ∧ ≥0.03 ∧ all-5-folds>0 | **FAIL** both |
| RE-B2 all-folds-positive | False [+,−,+,−,+] | False [all −] | required | FAIL |
| RE-B2 Herfindahl (pos-class mass) | 0.313 **FLAG** | 0.038 | >0.20 ⇒ flag | CC domination-flagged |
| **RE-B2b** Δ(error − matched-success non-shareable frac) | −0.071 (CI −0.178,+0.013) | +0.010 (CI −0.030,+0.061) | LB95>0 | **FAIL** both (indistinguishable) |
| **RE-B3** cross-instrument sign agreement (dAUC & Δb2b) | — | — | both signs agree | **FAIL** (both disagree) |

**Overall (frozen disposition rule): KILL.** RE-B2 fails, RE-B2b is falsified, RE-B3 (hard gate) fails on sign
disagreement. Multiple independent kills — not a single marginal miss.

## The RE-B1 trap (why the "novel claim" flag is a false positive in isolation)
The pre-registered code sets `novel_claim_supported=True` because post-error re-convergence is low
(2.5%/0%) and error-results rarely recur (3.8%/0%). Read alone, that looks like "errors permanently fork the
tree." **It does not** — and this is precisely the failure mode the committee anticipated with the RE-B2b
upgrade gate (FIX-1). The matched-success control shows the **non-shareable fraction is ~89–97% for
SUCCESSFUL calls too** (CC success mean 0.967, codex 0.925). The session-level label median for non-shareable
footprint fraction is **0.98 (CC) / 0.986 (codex)** — i.e. *almost every* tool call, error or not, is
cross-session-unique at the signature level. Near-zero re-convergence is the **universal base rate** of agent
tool streams, not an error-induced fork. Once contextualized by RE-B2b, RE-B1 in isolation is non-load-bearing
and the novel claim collapses. On CC the error group is even *slightly more* shareable than matched successes
(Δ = −0.071), the opposite of the thesis direction.

## Robustness of the negative to the membership proxy
Cross-session shareability is a multiset-membership proxy over `name\0canon_args` (a ceiling vs. literal
contiguous radix-prefix sharing; args carry full paths/commands/repos so absolute sharing is low ~3–5%).
**The kill does not depend on that absolute level**, because RE-B2 and RE-B2b are *relative* comparisons within
the same proxy: error vs. matched-success, and B1 vs. B0 cadence. Even if true token-prefix sharing were
higher, errors are not *differentially* less shareable than matched successes, and error features carry no
predictive power for the non-shareable fraction over ordinary cadence. The outcome variable is also nearly
saturated (non-shareable frac ≈0.98, tiny variance) → there is no meaningful error-driven variation to explain.

## Statistical discipline (pre-registered)
2000× session-clustered bootstrap; 5-fold session-clustered CV; deterministic md5 folds; seed 20260601.
Sign-stability checked (CC folds [+,−,+,−,+], codex all −) → not stable → fail. Herfindahl of positive-class
mass reported (CC 0.31 flagged 2–3-session domination; would have downgraded any PASS regardless). All
2000-resample CIs reported above.

## Prior-art & non-collision (arXiv IDs re-verified live 2026-06-01)
- **SGLang / RadixAttention / HiCache** — arXiv **2312.07104** (Zheng et al.). Radix-tree KV reuse keyed on
  token prefixes; HiCache adds CPU/GPU tiers. Assumes divergence is task-content-driven; does not model errors
  as a fork class nor measure re-convergence. **This result corroborates that assumption** (errors are not
  special) rather than extending it.
- **vLLM PagedAttention / Automatic Prefix Caching** — arXiv **2309.06180** (Kwon et al.). Identical-prefix
  reuse, error-agnostic. Same corroboration.
- **Non-collision with our own line:** NOT PROJ-0003 (failure cause/recovery — we measured KV shareability cost,
  not cause). NOT DEAD-0015/PROJ-0007 (canonicalization-recoverable drift — the load-bearing distinction we
  *tested* was nondeterministic-irreproducible error forks; we found errors are not a distinguishable fork
  class at all). NOT DEAD-0016 (byte-identical interior repeats). NOT EXP-0054/CLAIM-0018 (within-session
  redundant prefill tax — that was also killed). No decode-time speculative decoding.

## Useful knowledge produced (the value of the negative)
1. For agent tool-call streams, **cross-session prefix sharing at the tool-signature level is negligible
   (~3–5% re-occurrence) and error-agnostic** — successes and errors re-converge at the same near-zero rate.
   Errors do **not** constitute a distinct non-shareable fork class; existing RadixAttention/APC error-agnostic
   designs are adequate. No error-aware KV-cache accounting is warranted by this evidence.
2. Methodological: a low absolute re-convergence rate (RE-B1) is **uninformative without a matched-success
   control** (RE-B2b). The committee's FIX-1 upgrade gate was decisive — it converted an apparent positive into
   a clean falsification.
3. Premise RE-B0 *does* hold (most footprint is downstream of the first error: CC 63%, codex 92%) — so the
   negative is about *shareability differential*, not about the downstream region being trivially small.

## Reproduce
`/usr/bin/python3 experiments/2026-06-01/EXP-0056/impl/error_fork_census.py` (≈4 s, stdlib only).
Artifacts: `results/census.json`, `results/summary.json`, `results/sessions_{cc,codex}.csv`,
`logs/run_main.log`. Frozen gates in `PRE_REGISTRATION.md`.
