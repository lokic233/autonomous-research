# EXP-0060 PRE-REGISTRATION — Agent KV Eviction Policy Benchmark vs Belady (PROJ-0014 / CLAIM-0025)

**LOCKED-TS (UTC):** `2026-06-01T22:42:08Z`  (committed via `ros commit` BEFORE the main measurement run)
**Agent:** researcher-0025-L0-r7  | **Sub-monitor:** sub-monitor-0014-r7 | **prompt_version:** v001
**Host:** cli:dengcchi-mac (macOS, CPU-only, pure Python stdlib — `json, glob, os, re, math, statistics, random, hashlib`. NO numpy/torch.)

This document FREEZES every capacity value, policy, hyperparameter, threshold, and PASS / KILL decision rule. No threshold
may change after this lock. **A clean honest NEGATIVE is a FIRST-CLASS publishable result.** NO gate threshold will be
moved to manufacture a PASS.

## WHAT THIS IS (committee FIX-1 reframe)
This is a **POLICY-COMPARISON BENCHMARK**, NOT a predictor and NOT a dAUC-predictability claim. PROJ-0011/EXP-0057
ESTABLISHED (surviving result, re-confirmed here as RE-B0): agent file-path KV reuse distance is BIMODAL (CC: 18.9% far
>8192 tok, p99 ≈86k) and a Belady oracle saves ≤13% recompute-mass over LRU. A cheap CAUSAL PREDICTOR of far-reuse
FAILED (DEAD-0019). **OPEN QUESTION answered here:** on the same agent KV traces, how much of the LRU→Belady
recompute-mass GAP do EXISTING / CLASSICAL frequency-aware eviction policies capture WITHOUT future knowledge, AT MATCHED
CACHE RESIDENCY?

**CLAIM-0025:** best of {SGLang-LFU, SGLang-SLRU, ARC, LRU-K, static-pin+LRU(N∈2/3/5)} captures ≥ 50% of the
(LRU − Belady) recompute-mass gap with no future knowledge, at matched residency, at ≥3 of 5 pre-declared capacities.
**CLEAN NEGATIVE (first-class):** best cheap policy captures < 50% ⇒ the Belady gap is ORACLE-ONLY ⇒ ship classical
eviction (LRU/LFU), reinforces DEAD-0019 from the policy side.

## ARXIV LIVE-VERIFICATION (checked 2026-06-01, WebFetch arxiv.org/abs/<id>)
- **2507.07400** = "KVFlow: Efficient Prefix Caching for Accelerating LLM-Based Multi-Agent Workflows" — workflow-aware
  KV management predicting future agent activity, beats LRU. ✓
- **2212.13671** = "Optimizing Replacement Policies for Content Delivery Network Caching: Beyond Belady…" — LRU-BaSE /
  PFOO, RL eviction vs Belady byte-miss-ratio. ✓ (CDN-Belady)
- **2508.12485** = "Cold-RL: Learning Cache Eviction with Offline Reinforcement Learning for NGINX" — DQN eviction vs LRU. ✓
- **2312.07104** = "SGLang: Efficient Execution of Structured Language Model Programs" — RadixAttention KV reuse; SGLang
  ships LFU/SLRU/priority eviction (`evict_policy.py`). ✓
- **ARC** = Megiddo & Modha, "ARC: A Self-Tuning, Low Overhead Replacement Cache", FAST'03 (killer baseline). [classic, not arXiv]
- **LRU-K** = O'Neil, O'Neil & Weikum, "The LRU-K Page Replacement Algorithm For Database Disk Buffering", SIGMOD'93
  (killer baseline). [classic, not arXiv]

---

## 0. CORPORA & PARSING (frozen — reused VERBATIM from EXP-0057 harness)
- **CC (primary):** `~/.claude/projects/*/*.jsonl`, `parse_cc_session`.
- **Codex (cross-instrument, FIX-4 honest report):** `~/.codex/sessions/**/*.jsonl`, `parse_codex_session` (dedup by call_id).
- A **session** = one jsonl file with `>= 8` tool calls (MIN_TRIALS=8).
- **Token proxy (frozen):** tokens = chars / 4.0 (CHARS_PER_TOK=4.0). Every gate is a ratio invariant to the proxy.
- `parse_cc_session` / `parse_codex_session` / `load_corpus` / `extract_paths` / `file_class` / `build_units` / `gini`
  / `det_hash` are reused **VERBATIM** from `EXP-0057/impl/reuse_distance_census.py`. The trace builder, the reuse-unit
  definition, the path-touch touch-stream, and the **recompute-mass accounting** are UNCHANGED.

## 1. UNIT, TOUCH-STREAM, RECOMPUTE-MASS (frozen — inherited from EXP-0057 §1, cited)
- **FILE-PATH EXTRACTION:** per call collect path-set from `inp` fields {file_path,path,notebook_path,filePath} and Bash/shell
  command path tokens (regex `(?:\.{0,2}/)?(?:[\w.@+\-]+/)+[\w.@+\-]+`). Path identity = `os.path.normpath` AS-GIVEN
  (conservative: splits one real file into ≥1 ids → only REDUCES measured reuse, cannot inflate any gate).
- **TOUCH:** each distinct path in a call = one touch event at that call, with `size(p) = (len(args_str)+len(result))/4.0`
  tokens (the recompute mass charged on a miss for that path at that touch).
- **REUSE UNIT** (for RE-B0 far-share, inherited from EXP-0057): a path-touch followed by ≥1 LATER same-path touch in the
  same session. `gap_to_next` in tokens. **FAR** = gap_to_next > 8192 tok; **NEAR** = < 512 tok.
- **CACHE SIM TOUCH STREAM (inherited from EXP-0057 RE-A3, EXTENDED):** per session, ordered touches over the full call
  stream. On each touch of path p: HIT if p∈cache (no recompute); else MISS → `recompute_mass += size(p)`, insert p, evict
  per policy if cache full. Recompute mass is pooled across sessions, per (policy, capacity).

## 2. CACHE CAPACITY (frozen — FIX-3 pre-declared grid)
- Capacity is **slot-count** (number of resident path-blocks), the EXP-0057 harness unit. We do NOT switch to a mass-cap
  (that would require rewriting the Belady oracle, forbidden by the harness-verbatim mandate). **Each resident path = one
  block occupying one slot.** This is the faithful slot-count operationalization of "resident mass"; FIX-5 matched-residency
  (below) is honored at this slot granularity.
- Per session, `C = ceil(frac · n_distinct_paths(session))`, the per-session working-set-relative capacity (EXP-0057 form).
- **FROZEN 5 capacities (fracs of per-session distinct-path working set):** `CAP_FRACS = [0.10, 0.20, 0.30, 0.50, 0.70]`.
  Justification: frac<1 induces eviction; 0.10 = well BELOW working set (heavy eviction, large gap), 0.70 = most of the
  working set (light eviction, small gap). This spans below-to-near the working-set size — the meaningful eviction regime.
  (frac≥0.90 ≈ no-eviction → gap→0 → captured-fraction = 0/0 undefined, intentionally excluded; frac=0.05 too small for
  short sessions to be stable. EXP-0057 used 7 fracs incl. 0.05/0.90; we freeze the 5-value interior grid here.)

## 3. POLICY SET (FROZEN, history-only, NO future knowledge). Each on the IDENTICAL touch stream, MATCHED capacity C.
- **LRU (baseline):** evict resident path with oldest last-touch. [from harness]
- **Belady-oracle (upper bound):** evict resident path with farthest next-touch (never-again first). [from harness]
- **SGLang-LFU:** evict least-frequently-used (min reference count), **tie-break LRU** (oldest last-touch). Mirrors SGLang
  `evict_policy.py` LFU semantics. Frequency = # references since (re)admission of the resident block.
- **SGLang-SLRU (segmented LRU):** two segments, **protected cap = floor(0.8·C)**, probationary = C − protected (FROZEN
  80/20 split). New block enters probationary (MRU). A HIT on a probationary block PROMOTES it to protected MRU ("promote
  on 2nd hit": load = 1st touch in probationary, first hit = 2nd touch → promote). HIT on protected → protected MRU. If
  protected overflows cap, demote its LRU to probationary MRU. Eviction: LRU of probationary if non-empty, else LRU of
  protected.
- **ARC (Adaptive Replacement Cache, Megiddo–Modha FAST'03):** standard T1/T2 resident lists, B1/B2 ghost lists,
  self-tuning target p. Ghost lists hold path identities only (no mass, occupy NO capacity slot). MANDATORY KILLER
  BASELINE. Standard algorithm with `REPLACE(x,p)`; miss = any access not resident in T1∪T2. (FIX-2)
- **LRU-K (K=2):** evict by Backward-K-distance = `now − (Kth-most-recent reference time)`; resident blocks with < K
  references have +∞ backward-K-distance and are evicted first, tie-broken by oldest single last-reference (LRU among
  under-K). **HIST RETAINED:** a global per-path last-K reference-time history persists across evictions (no retention-period
  decay; full retention — documented simplification of O'Neil et al.). MANDATORY KILLER BASELINE. (FIX-2)
- **static-pin+LRU, N∈{2,3,5} (the "custom two-tier" candidate):** at each step the pin set = the top-N paths by
  **causal global session-prefix frequency** (freq_so_far observed up to and including the current step; history-only).
  Resident pinned blocks are protected from eviction; the remaining slots are LRU. **FIX-5 MATCHED RESIDENCY:** pinned
  blocks COUNT against C (total resident ≤ C). On a miss with cache full: victim = LRU among resident NON-pinned; if all
  resident are pinned (degenerate N≥C), victim = LRU among pinned (so residency never exceeds C). A pin "win" that only
  appears because pinning let a policy hold more than C blocks is a capacity illusion and is structurally impossible here.

## 4. METRICS (frozen)
- **recompute_mass(policy, C)** = pooled Σ over sessions of miss masses (tokens), per capacity.
- **captured-fraction(policy, C)** = `(recompute_LRU − recompute_policy) / (recompute_LRU − recompute_Belady)`, per
  capacity, per policy. (=1.0 ⇒ matches Belady; =0 ⇒ no better than LRU; <0 ⇒ worse than LRU.) Undefined/skip a capacity
  if `(recompute_LRU − recompute_Belady) <= 0` (no gap to capture); reported as null and NOT counted toward "≥3 of 5".
- **per-session recompute** stored for each (policy, C) to enable the session-clustered bootstrap.

---

## GATES — exact metric, threshold, decision (ALL FROZEN)

### RE-B0 — PREMISE RE-CONFIRM (FLOOR; not the headline). On CC (primary):
- `far_share = #(reuse units with gap_to_next > 8192) / N_units` (inherited EXP-0057 metric).
- `belady_saves_max = max over the 5 CAP_FRACS of (recompute_LRU − recompute_Belady)/recompute_LRU`.
- **PASS iff** `far_share >= 0.15` AND `belady_saves_max >= 0.05`.
- **FAIL** → **CLEAN KILL, no project:** the LRU→Belady gap vanished on the current corpus; STOP and write it up honestly.

### RE-B1 — LOAD-BEARING BENCHMARK. On CC (primary), at MATCHED RESIDENT MASS (slot-count C):
- Report the full **policy × capacity matrix** of recompute_mass and captured-fraction.
- **PASS iff** the BEST cheap policy (max over {LFU, SLRU, ARC, LRU-K, static-pin N∈{2,3,5}}) has
  `captured-fraction >= 0.50` at **>= 3 of the 5 capacities**, AT MATCHED RESIDENT MASS.
- **FAIL** → **CLEAN-NEGATIVE-KILL:** the Belady gap is oracle-only; ship classical LRU/LFU; reinforces DEAD-0019.
- **FIX-2 explicit verdict:** report ARC and LRU-K captured-fractions vs the static-pin custom policy. If ARC (or LRU-K)
  captures ≥ what static-pin captures, the custom two-tier is OBSOLETE — report it explicitly ("ARC already captures X%;
  custom two-tier adds nothing").

### RE-B3 — ROBUSTNESS (frozen).
- **Bootstrap:** 2000× session-clustered bootstrap (resample sessions w/ replacement), recompute pooled captured-fraction
  per (policy, capacity); report 95% CI [2.5th, 97.5th pct].
- **Multiple-testing (FIX-3):** the free-parameter search is best-of-{N=2,3,5} × 5 capacities = **15 cells** (static-pin).
  One-sided bootstrap p-value per cell for H0: captured-fraction ≤ 0.50. Apply **Benjamini-Hochberg** AND report
  **Bonferroni** across the 15 cells at α=0.05. Report which cells survive each correction. (ARC/LRU-K/LFU/SLRU are
  parameter-free; reported per-capacity without the 15-cell penalty, plus a broader all-policy×cap correction for context.)
- **HHI flag:** per-session HHI over the cache-sim recompute mass = `Σ_s (recompute_LRU_s / Σ recompute_LRU)^2`. If
  `HHI > 0.20` → FLAG that the captured-fraction is dominated by a few sessions and DOWN-WEIGHT the conclusion.

### FIX-4 — HONEST CROSS-INSTRUMENT (Codex).
- CC is the declared PRIMARY corpus. Report Codex captured-fraction matrix EVEN WHEN Codex is NOT bimodal (it was NOT in
  EXP-0057: far_share=0.036). Selective CC-only reporting is a KILL FLAG. Frame honestly (e.g. "Codex near-reuse-dominated;
  Belady gap tiny; capture ratio noisy on few far positives"). Codex does NOT gate the CC disposition.

---

## OVERALL DISPOSITION (frozen decision tree)
- **CLEAN KILL (RE-B0)** iff far_share<0.15 OR belady_saves_max<0.05 on CC (gap vanished → no project).
- **PASS** iff RE-B0 PASS AND RE-B1 PASS (best cheap policy ≥0.50 captured at ≥3/5 caps, matched residency) AND that win
  survives BH correction (RE-B3) and is not HHI-dominated (or explicitly down-weighted). Name the winning policy and %;
  state explicitly whether ARC/LRU-K (parameter-free) or static-pin (free-N) is the winner and the ARC-vs-custom verdict.
- **CLEAN-NEGATIVE-KILL** iff RE-B0 PASS but RE-B1 FAIL (best cheap policy < 0.50 at < 3 of 5 caps) → Belady gap is
  oracle-only → ship classical eviction; reinforces DEAD-0019 from the policy side. First-class publishable negative.

## OUTPUTS
- `impl/PRE_REGISTRATION.md` (this file; committed BEFORE the run, frozen)
- `impl/eviction_benchmark.py` (extends EXP-0057 harness verbatim; stdout tee'd to `logs/run_main.log`)
- `results/summary.json` (CC + Codex: per-policy per-capacity recompute_mass, captured-fraction, bootstrap CIs,
  BH/Bonferroni p-values, HHI, RE-B0/B1/B3 dispositions)
- `impl/analysis.md` (headline one-liner; per-gate disposition table; which policy captured the most gap and how much;
  explicit ARC-vs-custom verdict (FIX-2); matched-residency control (FIX-5); Codex honest report (FIX-4); final
  DISPOSITION = PASS or CLEAN-NEGATIVE-KILL).
