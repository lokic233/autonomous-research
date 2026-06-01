# EXP-0059 — Analysis: Cross-Session KV-Sharing Ceiling / Volatile-Token Normalization Budget

**Claim:** CLAIM-0024  **Project:** PROJ-0013  **Agent:** researcher-0024-L0-r7  **Level:** L0, Mac CPU.
**Pre-registration:** `impl/PRE_REGISTRATION.md` LOCKED-TS `2026-06-01T22:43:20Z`, committed **`0d14531`** BEFORE the
run. No threshold moved after the lock. Tokenizer gpt2 (Rust fast, EXP-0049 venv, token-counting only). Block 16.
Seed 20260601. Bootstrap B=2000 (session + class clustered).

This is a **CHARACTERIZATION + POLICY-COMPARISON**, NOT a dAUC-predictability claim. No predictor was built. The
unlocked mass is reported as an **UPPER BOUND** on recoverable KV mass (FIX-2), not a shippable gain.

CORPORA REPORTED SEPARATELY (honest discordance). Heads: Claude Code = largest drift-free template fleet group of
267 sessions -> **n=50** (49 compared vs median-length reference); reconstructed `<env>` block (real in-trace
cwd/gitBranch/version/sessionId/date) ++ first user template. Codex = **n=122** (121 compared); `base_instructions`
++ developer envelope, fully in-trace.

---
## HEADLINE NUMBERS

| metric | Claude Code | Codex |
|---|---|---|
| mean realized_raw prefix (tok) | 47.3 | 6628.8 |
| mean canonicalized-max prefix (tok) | 577.6 | 6678.0 |
| **realized_frac (RE-A0)** | **0.082** | **0.993** |
| RE-A0 disposition | **PASS — 92% gap to explain** | **CLEAN KILL — no ceiling** |
| top-3 unlocked-mass share (RE-A1) | 1.000 | 1.000 (degenerate) |
| top-3 share CI95 (RE-A3, incl. class-selection var) | [0.736, 1.000] | [1.000, 1.000] |
| Gini across classes | 0.605 | 0.000 |
| HHI unlocked mass across sessions | 0.020 (no domination) | 0.009 |
| collision alias rate — overall / **semantic** | 0.657 / **0.000** | 1.000 / **0.000** |
| RE-A2 recompute saved @cap=0.30 | **+32,040 tok (+28.1%)**, hit Δ +0.283 | −549 tok (−2.7%), hit Δ −0.000 |

---
## PER-GATE DISPOSITION

### RE-A0 (magnitude floor) — realized_frac <= 0.6 ?
- **Claude Code: PASS (gap exists).** realized_frac = **0.082**. The fleet shares only ~47 raw tokens (~3 blocks)
  cross-session but ~578 after masking volatile classes — a **>90% relative gap**, far past the 40% floor.
- **Codex: CLEAN KILL (first-class negative).** realized_frac = **0.993**. Codex sessions already share ~6,629
  tokens of *exact* prefix (`base_instructions` is byte-identical across sessions; the developer envelope shares a
  long head). Masking every volatile class adds only ~49 tokens (6,629 → 6,678). **Volatile tokens are NOT the
  Codex bottleneck** — the residual non-shared mass is genuine content, not drift. Honest negative, reported, no
  positive forced.

### RE-A1 (load-bearing concentration) — top-3 unlock >= 50% of recoverable mass ?
- **Claude Code: PASS, but DEGENERATE (FIX-4 single-class domination flag FIRES).** Three classes carry all
  attributed unlocked mass — `session_uuid` 93.8%, `date` 3.1%, `gitbranch` 3.1% — so top-3 share = 1.000, but
  **top-1 (`session_uuid`) alone is 93.8% of the top-3**. This is honestly a **top-1 lever (the per-session Session
  ID)**, not a diverse three-class budget. Gini=0.605 reflects that 9 of 12 classes contribute exactly zero
  (`cwd`, `abspath`, `version`, etc. are constant within the same-repo fleet, so they never bind).
  - **Marginal vs total:** sum of add-one-in marginals = 12,384 tok captures only **48%** of the true gap (canon−raw
    = 25,984 tok). The other ~52% is **interaction** (the all-classes canonicalizer relocates *every* volatile
    field to the suffix and extends the shared prefix jointly; no single field unlocks it alone). Reported honestly:
    the single-field decomposition explains roughly half of the realized ceiling; the full ceiling needs joint
    masking.
- **Codex: moot (A0 already killed).** Only `uuid` shows any (tiny, ~10 tok/session) mass; the "share=1.0, Gini=0"
  is the degenerate one-nonzero-class artifact on a near-zero total. No concentration claim is made.

### RE-A2 (policy comparison) — recompute saved WITH vs WITHOUT canonicalizer at fixed capacity
- **Claude Code: PASS (decisive policy gap).** Across the capacity sweep, canonicalizing the head before cross-
  session radix sharing saves **22.7%–31.7%** of recompute token-mass (e.g. +32,040 tok / +28.1% at cap=0.30),
  with hit-rate delta **+0.23 to +0.32**. The gap is robust to cache capacity (positive even at cap=0.05).
- **Codex: FAIL/negative.** Canonicalization yields **−2.7%** recompute (slightly worse) and ~0 hit-rate delta —
  consistent with RE-A0: there is no volatile-driven ceiling to recover, and suffix relocation marginally perturbs
  the already-shared prefix.

### RE-A3 (robustness) — session-clustered + class-selection bootstrap; HHI across sessions
- **Claude Code:** top-3 share CI95 = **[0.736, 1.000]** (bootstrap resamples both sessions *and* the 12 classes
  per FIX-1, so the lower bound reflects taxonomy-selection uncertainty). HHI of unlocked mass across sessions =
  **0.020** (well below the 0.2 domination flag) — the budget is **not** driven by a few outlier sessions; it is a
  fleet-wide property. Even at the CI lower bound (0.736) the concentration clears the 0.50 RE-A1 threshold.
- **Codex:** CI [1.000, 1.000] degenerate, HHI 0.009 — irrelevant given the A0 kill.

---
## COMMITTEE FIXES — DISPOSITION

- **[FIX-2 UPPER BOUND]** All unlocked-mass and recompute-saved figures are an **UPPER BOUND** on recoverable KV
  mass. Prompt-output-equivalence under masking was **not** demonstrated at L0; we default to upper bound. The bound
  is **tight for Claude Code** because the binding class is `session_uuid` (an INERT identifier whose value cannot
  plausibly change model semantics) — see FIX-3. It would be loose only if a POTENTIALLY-SEMANTIC class
  (`cwd/abspath/version/gitbranch/sandbox/approval`) were the lever, which it is not here.
- **[FIX-3 COLLISION / false-positive aliasing]** Of the prefix blocks unlocked *only* by canonicalization,
  **alias_rate_overall = 0.657** for CC (the rest are no-op unlocks where the raw value was already identical), but
  the **semantic-class alias rate = 0.000** — *every* genuine cross-session alias is on an INERT class
  (`session_uuid`/`date`: diff_inert=46, diff_semantic=0). **The collision COST of the CC budget is therefore ~0**:
  masking never aliases two semantically-distinct prefixes; it only collapses sessions that differ in an
  output-irrelevant identifier. This is the best case for the budget. (Codex: alias rate 1.0 but on ~zero mass —
  moot.)
- **[FIX-4 PER-CLASS LORENZ]** Per-class marginals reported above and in `results/summary.json`
  (`RE_A1.per_class_marginal_share`, `class_mass_ranked`, `lorenz_points`). The **single-class-domination flag
  fired for CC** (`session_uuid` = 93.8% of top-3) — the headline is honestly a one-field lever, not a three-field
  budget. Gini on the full 12-class vector = 0.605.
- **[FIX-1 class-selection variance]** RE-A3 bootstrap resamples the class taxonomy as well as sessions; the
  reported CI95 already incorporates this variance source.

---
## HONEST CC-vs-CODEX DISCORDANCE
The two instruments **disagree by design of their head construction, and we report them separately rather than
averaging**:
- **Codex bakes a byte-identical `base_instructions` block** (~6.6k shared tokens) ahead of any volatile field, so
  cross-session radix sharing is *already near its ceiling* — volatile tokens are not the bottleneck (CLEAN KILL).
- **Claude Code's reconstructed `<env>` head places a per-session-unique `Session ID` early** (token ~47), which
  forces a cross-session branch before the long shared remainder — a real, concentrated, low-cost ceiling (POSITIVE,
  upper bound).

**Reconstruction caveat (CC):** the CC head is a reconstructed envelope (real in-trace values, CC's documented
`<env>` format + first user template). The *qualitative* finding — a per-session unique identifier early in the
shared head forces an early cross-session branch, and masking it (or relocating it to the suffix, per Anthropic/
OpenAI cache guidance) unlocks the long shared remainder — is robust and matches published prompt-caching guidance.
The *exact magnitude* (session_uuid ≈ 94% of the marginal budget; +28% recompute saved) depends on the reconstructed
field ordering and is therefore an **upper-bound, instrument-specific** measurement, not a fleet-universal constant.

---
## VERDICT
**DISCORDANT, both first-class:** **Claude Code = POSITIVE** quantified volatile-token normalization budget (realized
8.2% of canonicalized-max; a ~10× cross-session prefix ceiling concentrated in essentially ONE inert field —
`session_uuid` (94% of marginal mass) — with ~0 semantic-collision cost and +22–32% recompute-mass saved at fixed
radix capacity; reported as an UPPER BOUND on a reconstructed-envelope head). **Codex = CLEAN NEGATIVE** (realized
99.3% of canonicalized-max — its byte-identical base-instructions head already shares ~6.6k tokens; volatile tokens
are not the bottleneck). The CLAIM-0024 "top-3 classes unlock a majority" form holds for CC only as a *top-1* lever
(FIX-4 domination flag), and does not generalize cross-instrument.
