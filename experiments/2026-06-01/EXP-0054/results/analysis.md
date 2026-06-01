# EXP-0054 — Redundant Tool-Call Prefill Tax: ANALYSIS (PROJ-0008 / CLAIM-0018)

**Agent:** researcher-0018-L0-r6 | **Pre-registration locked:** `2026-06-01T17:40:50Z` (committed HEAD 65df6f8 BEFORE run)
**Corpora:** CC `~/.claude/projects` (60 sessions ≥8 calls, 2,278 tool calls) + Codex `~/.codex/sessions` (80 sessions, 2,659 calls).
**Method:** pure-stdlib census per frozen PRE_REGISTRATION.md. All thresholds unchanged from lock.

## HEADLINE VERDICT: **CLAIM-0018 KILLED — clean, first-class negative (triple-negative).**
The *structural premise is TRUE* (within-session byte-identical re-invocations are genuinely interior + long-gap +
100% unrecoverable by production exact-prefix caches — RE-A2 PASS). But the claim that this is a **recoverable prefill
tax is FALSE on real traces**: byte-identical ARGS overwhelmingly do NOT yield byte-identical RESULTS, so the recoverable
tax collapses to f=0.19% ≪ 2% floor, and the determinism-class discriminator is non-predictive (and inverted). The
9.8%/8.2% "repeat" live signal **conflated arg-repetition with recoverable-output repetition** — exactly the committee's
RE-A3 concern (VERDICT-0062), now empirically confirmed *against* the claim.

---

## PER-GATE DISPOSITION

### RE-A2 — EXACT-PREFIX-SURVIVAL KILLER — **PASS (but necessary-not-sufficient)**
- CC: **100%** of 175 surviving repeats exact-prefix-non-recoverable (≥95% threshold). Median intervening gap = 3,593 tok.
- Codex: 100% of 36 surviving repeats non-recoverable.
- The repeats ARE true interior repeats that production exact-prefix caches (vLLM APC / SGLang RadixAttention /
  TensorRT-LLM) cannot reach. The mechanism the project posits is real. It just doesn't matter, because (RE-A3/A4) the
  repeats carry almost no recoverable output.
- **Tier-2 scope boundary (RE-A2 fix #4):** 100% of byte-identical repeats are *content-addressable* by non-prefix KV
  reuse (CacheBlend 2405.16444 / PromptCache 2311.04934 / LMCache) — the args are literally identical. We did NOT
  implement/evaluate non-prefix fusion; it is our **named scope boundary**, not claimed structurally impossible. NOTE:
  even non-prefix reuse would only be *correct* on the ~15% (CC) / 0% (Codex) of repeats whose OUTPUT is also identical.

### RE-A3 — RESULT-EQUIVALENCE CO-PRIMARY — **DECISIVE NEGATIVE**
result_equiv_rate (byte-identical result | byte-identical args), among surviving repeats:
- **CC: 15.4%** (27/175).   **Codex: 0.0%** (0/36).
- By determinism class (CC) — **HYPOTHESIS INVERTED**:

  | class | n | result_equiv_rate |
  |---|---|---|
  | MUTATING (Write/Edit) | 9 | **0.778** |
  | INVALIDATED (read w/ intervening write) | 13 | 0.308 |
  | DETERMINISTIC (read, no intervening write) | 9 | **0.111** |
  | VOLATILE (Bash/web) | 144 | 0.104 |

  The naive theory ("READ is cacheable, WRITE/Bash is not") is **backwards**: DETERMINISTIC reads have the *lowest*
  output-equivalence, MUTATING the *highest*. Mechanism: the bulk of byte-identical repeats are re-run Bash/exec
  (VOLATILE, 144/175) whose stdout differs on re-execution; the rare identical-output repeats are idempotent Write
  confirmations ("File updated"). Re-reads return differing bytes (changed files, dynamic line-number/truncation framing).
- Per the project_overview honest-kill pathway ("RE-A3 result-equivalence ~0 → no recoverable output → tax illusory"),
  this resolves against the claim.

### RE-A4 — EFFECT-SIZE FLOOR + COST — **KILL (f ≪ 2%)**
- **f (recoverable tax tokens / total tool-call prefill tokens) = CC 0.19%, Codex 0.0%.**
- CC f 95% CI (session-clustered bootstrap, B=2000) = **(0.0%, 0.30%)** — *includes 0* and is an order of magnitude
  below the 2% floor. (CI corrected mid-run: see PROCESS INTEGRITY below.)
- Cost translation (CC, the only nonzero corpus), under chunked-prefill batching — *kept for completeness, but the
  effect is below floor so the dollar figure is negligible*: wasted prefill ≈ f × total-tool-call-prefill-tokens. For
  70B (2·N FLOPs/tok, ~2k tok/s effective, $2/GPU-hr) this is a fraction of a GPU-second per 1k sessions. Not material.
- **KILL.**

### RE-A1 — DETERMINISM-CLASS dAUC OVER JOINT BASELINE — **FAIL → DEMOTE**
- Predicting result_equiv over surviving repeats, session-clustered 5-fold CV (deterministic md5 folds, reproducible):
  - CC: AUC(B0 = gap+tool-freq+**tool-identity** one-hot) = 0.614; AUC(B1 = B0 + determinism-class) = 0.614.
  - **dAUC = +0.00025, 95% LB = −0.4 (< 0).**  Determinism class adds **nothing** over the joint baseline.
  - Codex: label degenerate (all surviving = MUTATING, result_equiv all-0) → AUC undefined → determinism prediction
    vacuous → DEMOTE for Codex.
- Determinism class is dominated by / collinear with tool identity (which B0 already contains), and the state-conditioning
  surplus (RE-A7) is non-predictive. **DEMOTE** to "agents repeat popular (mostly volatile) tools" workload restatement.

### RE-A5 — CROSS-CORPUS SIGN REPLICATION — **FAIL (both agree the claim is dead)**
- f: CC 0.19% vs Codex 0.0% — no positive replication. Class-effect direction: Codex degenerate, uncomparable.
- The corpora agree in *direction of refutation*: neither shows a material recoverable tax.

### RE-A6 — ANTI-TAUTOLOGY (structural retry + K=200 adjacency) — **PASS (filters applied, pop non-empty)**
- CC: 187 raw repeats → −11 structural retries (prior errored) → −1 adjacent (<200 tok) → **175 surviving** long-gap
  repeats. Codex: 44 → −0 retry → −8 adjacent → **36 surviving**. Surviving population is non-empty and not a retry
  artifact; the negative is genuine, not a tautology of the exclusion rule.

### RE-A7 — DETERMINISM CLASS CONDITIONED ON INTERVENING-WRITE STATE — **conditioned; inverted**
- CC: DETERMINISTIC (no intervening write) result_equiv 0.111 vs INVALIDATED (intervening same-target write) 0.308.
  The state-conditioning runs *opposite* to the hypothesis (invalidated reads are MORE output-stable here, small n).
  The predictor DID condition on session state (target extraction succeeded for file tools); the ceiling is that
  state-conditioning does not rescue predictivity. Codex: no DETERMINISTIC/INVALIDATED reads survived (all MUTATING).

---

## OVERALL (frozen decision tree → KILL)
- RE-A2 PASS (≥95%) — mechanism real, but necessary-not-sufficient.
- **RE-A4 f=0.19% ≪ 2%, CI∋0 → KILL.**
- **RE-A3 result_equiv ≈ 0–15% → recoverable output illusory → KILL.**
- **RE-A1 dAUC LB<0 → DEMOTE** (determinism class = repackaged tool identity).
- RE-A5 no positive replication. RE-A6 pop non-empty (negative is genuine). RE-A7 conditioned, inverted.
- **DISPOSITION: CLAIM-0018 KILLED. Useful published negative: "production exact-prefix KV caching is *sufficient* for
  agent within-session self-repetition — the residual interior-repeat tax is recoverable on <0.2% of tool-call prefill
  tokens, because byte-identical tool ARGS almost never reproduce byte-identical OUTPUTS on real long-horizon traces."**

## COMMITTEE required_evidence (VERDICT-0062) — addressed
- RE-A1 tool-identity one-hot folded into joint baseline B0 ✓ (dAUC over it = ~0, LB<0 → demote).
- RE-A2 rescoped to exact-prefix + non-prefix (CacheBlend/LMCache) reported as named scope boundary ✓.
- RE-A3 result-equivalence reported CO-PRIMARY with f (not conflated) ✓ — and it is the decisive negative.
- RE-A4 FLOPs/TTFT/$ cost translation under chunked-prefill batching ✓ (negligible, below floor).
- RE-A6 structural retry detection (prior-error heuristic, no gap cutoff) ✓.
- RE-A7 determinism class conditioned on intervening-WRITE state ✓.
- PROMOTION prior-art citations OWED only on promotion; claim is KILLED so promotion not sought. Related work named:
  CacheBlend 2405.16444, PromptCache 2311.04934, LMCache, ToolCacheAgent (OpenReview tX3YcbNa5w), LLM-dCache 2406.06799.

## PROCESS INTEGRITY (mid-run corrections; thresholds UNCHANGED)
1. **f bootstrap CI artifact:** first run produced LB(0.0036) > point(0.0019) — impossible. Cause: `boot_ci_ratio`
   resampled only tax-bearing sessions, excluding zero-tax sessions from the denominator universe, inflating the ratio.
   Corrected to resample over ALL sessions (num=0 for non-tax). Verdict unchanged (point f=0.19% < 2% floor regardless).
2. **CV reproducibility:** fold assignment used Python `hash()` (per-process salted) → non-reproducible AUC. Replaced
   with deterministic md5 folds; two consecutive runs now bit-identical. dAUC LB<0 in all cases → RE-A1 FAIL stable.
Neither correction moved a threshold or manufactured a PASS; both are length/intent-consistent fixes to the frozen intent.

## ARTIFACTS
- impl/redundant_prefill_census.py, impl/PRE_REGISTRATION.md
- results/census.json, results/surviving_cc.csv, results/surviving_codex.csv
