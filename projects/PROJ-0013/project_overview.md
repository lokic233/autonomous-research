# PROJ-0013 — Cross-Session KV-Sharing Ceiling: A Quantified Volatile-Token Normalization Budget

Seeded: 2026-06-01 by orchestrator-r7-001 (design committee proj0013_design, 6/6 ALL_COMMITTEE_DONE).
Verdict: YELLOW / seed-with-mandatory-fixes (FINAL_VERDICT A=yellow; novelty_killer GREEN + product_realist GREEN
+ 3 yellow). First claim: CLAIM-0024. CHARACTERIZATION + POLICY-COMPARISON (not a dAUC-predictability claim).

## THESIS
SGLang RadixAttention (arXiv 2312.07104) / vLLM APC (2309.06180) share KV across requests by exact token-prefix
match at the radix branch point. The REALIZED cross-session hit-rate on real agent traces is capped well below the
structural maximum because a small, identifiable set of VOLATILE tokens (timestamps, absolute paths, PIDs, session
UUIDs, cwd) inside otherwise-identical system/tool-schema prefixes forces an early branch. QUANTIFY, on the live
CC+Codex corpora: (i) realized exact-prefix cross-session sharable fraction (FLOOR), (ii) counterfactual sharable
fraction after a FROZEN cheap canonicalizer masking k volatile token classes (CEILING), (iii) Lorenz of KV mass
unlocked per volatile-class = a normalization BUDGET. Deliverable = the GAP + its concentration, NOT a predictor.

## FIRST CLAIM (CLAIM-0024)
On real agent traces the realized cross-session exact-prefix KV-sharable fraction is far below the canonicalized
maximum, and the gap is concentrated in <=5 volatile token classes such that masking the top-3 unlocks a measurable
majority of the recoverable cross-session KV mass. Clean negative if FALSE: realized sharing is already near the
canonicalized max (volatile tokens not the bottleneck) OR unlocked mass is diffuse across many idiosyncratic classes
(no cheap normalization budget).

## PRE-REGISTERED RE GATES (committee MANDATORY FIXES baked in)
- RE-A0 (magnitude floor): realized cross-session sharable prefix fraction <= 0.6 of canonicalized-max (real >=40%
  relative gap to explain). Floor; if realized ~ max -> clean kill (no ceiling).
- RE-A1 (LOAD-BEARING characterization, concentration): after the FROZEN canonicalizer, top-3 volatile classes unlock
  >= 50% of total recoverable KV mass (Lorenz/Gini on per-class unlocked mass). PASS = concentrated cheap budget;
  FAIL (diffuse) = no cheap lever -> clean negative. MEASUREMENT, not a dAUC.
- RE-A2 (policy comparison): simulate cross-session radix sharing WITH vs WITHOUT canonicalizer at fixed capacity;
  recompute-token-mass saved + hit-rate delta = the decisive GAP.
- [FIX-1] Pre-register the volatile-class taxonomy + regexes FROZEN before the run; bootstrap must include
  CLASS-SELECTION as a variance source, not just sessions.
- [FIX-2 CORRECTNESS BOUND] State the equivalence assumption explicitly: either prove a canonicalized prefix is
  SAFE to share (model output equivalent under masked PIDs/timestamps) OR report the measurement as an UPPER BOUND
  on recoverable mass, NOT a shippable gain. (Default: report as UPPER BOUND unless equivalence is demonstrated.)
- [FIX-3 false-positive collision] Measure the regex-masking cache-collision rate: how often does canonicalization
  ALIAS semantically-distinct prompts into shared KV? Report it as the cost side of the budget.
- [FIX-4 stratified] If top-3 HHI domination is driven by ONE class (e.g. timestamps), report per-class Lorenz
  separately; Gini on k=3 is near-degenerate -> give the full per-class marginal contribution.
- RE-A3 (robustness): session-clustered 2000x bootstrap CI on unlocked-mass fraction; HHI of unlocked mass across
  sessions (>0.2 => flag domination). CC AND Codex reported separately; honest discordance disclosure.
- MANDATORY BASELINES: realized exact-prefix hit-rate (no canon) = floor; canonicalized hit-rate = ceiling;
  per-volatile-class marginal contribution to gap closure.
- PRIOR ART (cite + disclaim canonicalizer novelty; contribution is the MEASUREMENT): EFIM 2505.21889, SAECache
  2605.18825, Prompt Cache 2311.04934, Preble 2407.00023, SGLang 2312.07104, vLLM APC 2309.06180.

## NOVELTY / NON-COLLISION (committee-checked)
novelty_killer GREEN (60+ abstracts, 5 queries, cs.DC/cs.LG): no shipping vLLM/SGLang/TensorRT/LMCache mechanism
canonicalizes volatile tokens before KV sharing; the contribution is the QUANTIFIED realized-ceiling MEASUREMENT +
normalization budget. ACCEPTS DEAD-0015/PROJ-0007 (cross-session schema/prompt drift is canonicalization-recoverable)
and delivers the quantified budget DEAD-0015 did NOT — a measurement, not a revived predictability claim. Not
DEAD-0016 (byte-identical interior repeats), not DEAD-0017 (error-fork), not PROJ-0002 (within-session edit-
invalidation). No decode-time SD.

## L0 GATING EXPERIMENT
Parse CC+Codex; per session extract system/tool-schema prefix + first divergent token vs other sessions; measure
realized shared-prefix length distribution; apply FROZEN canonicalizer; re-measure; compute per-volatile-class
unlocked mass + Lorenz/Gini + collision rate + capacity-sim recompute saved. CPU stdlib, reuse EXP-0054/0057
parse+JOIN + capacity-sim, <30s. Produces a POSITIVE (quantified normalization budget, reported as upper bound) OR a
clean negative (realized ~ max, or diffuse).
