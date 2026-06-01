# EXP-0057 PRE-REGISTRATION — Agent KV Reuse-Distance Bimodality & Far-Reuse Predictability (PROJ-0011 / CLAIM-0022)

**LOCKED-TS (UTC):** `2026-06-01T20:46:46Z`  (committed via `ros commit` BEFORE the main measurement run)
**Agent:** researcher-0022-L0-r7  | **Sub-monitor:** sub-monitor-0011-r7 | **prompt_version:** v001
**Host:** cli:dengcchi-mac (macOS, CPU-only, pure Python stdlib — `json, glob, os, re, math, statistics, random, hashlib`. NO numpy/torch.)

This document FREEZES every metric, threshold, feature set, and PASS / KILL / YELLOW decision rule. No threshold may
change after this lock. A clean honest NEGATIVE is a FIRST-CLASS publishable result. NO gate threshold will be moved to
manufacture a PASS. If a metric produces an artifact mid-run, it is re-operationalized to a length/intent-consistent
form of the FROZEN intent (thresholds unchanged) and the diagnosis is documented.

## ARXIV LIVE-VERIFICATION (checked 2026-06-01, WebFetch arxiv.org/abs/<id>)
- **2312.07104** = "SGLang: Efficient Execution of Structured Language Model Programs" — RadixAttention KV-cache reuse, LRU radix tree. ✓
- **2309.06180** = "Efficient Memory Management for LLM Serving with PagedAttention" — vLLM, LRU block eviction / APC. ✓
- **2411.19379** = "Marconi: Prefix Caching for the Era of Hybrid LLMs" — admission+eviction by reuse-likelihood FORECAST (RE-A2 baseline). ✓
- **2507.07400** = "KVFlow: Efficient Prefix Caching for Accelerating LLM-Based Multi-Agent Workflows" — Agent Step Graph, steps-to-execution eviction. ✓
- **2601.21473** = "ScaleSim: Serving Large-Scale Multi-Agent Simulation with Invocation Distance-Based Memory Management" — invocation distance. ✓
All five resolve to the cited titles. (CacheSage 2605.27744 / SAECache 2605.18825 / HashEvict 2412.16187 / AhaKV 2506.03762 / RAC 2602.21547 cited in charter as non-collision context only; not load-bearing here.)

---

## 0. CORPORA & PARSING (frozen — reuse EXP-0054/0055 layer verbatim)
- **CC (primary):** `~/.claude/projects/*/*.jsonl`. `parse_cc_session`: map `tool_use.id -> (name,input,args_str,start_pos)`;
  walk `tool_result` in file order, carry result text, is_error, stream char-offsets.
- **Codex (RE-A4 cross-instrument):** `~/.codex/sessions/**/*.jsonl`. `parse_codex_session`: map `function_call.call_id ->`
  `(name,args,args_str,start_pos)`; walk `function_call_output`, **dedup by call_id**, carry output, offsets.
- A **session** = one jsonl file with `>= 8` tool calls (MIN_TRIALS).
- **Token proxy (frozen):** tokens = chars / 4.0 (CHARS_PER_TOK=4.0). Every gate is a ratio or a threshold far from the
  constant (≥512 / ≥8192 tok), invariant to the proxy. Same accounting units as EXP-0054/0055.
- **Call stream position:** each call has `start_pos` (where its args appear) and `end_pos` (end of its result footprint),
  in chars; identical offset accounting to EXP-0055.

## 1. UNIT, LABEL, FILE-PATH EXTRACTION (frozen — verbatim from charter)
- **FILE-PATH EXTRACTION:** for each call, collect the set of file-paths it touches:
  (a) from `inp` fields `file_path` / `path` / `notebook_path` / `filePath` (EXP-0054 `target_of`);
  (b) from Bash/shell command path tokens: regex over `inp.command` (or args_str) for path-like tokens
      `(?:\.{0,2}/)?(?:[\w.@+\-]+/)+[\w.@+\-]+` (at least one `/`), i.e. multi-segment paths. Each distinct path in a
      call = one **touch event** located at that call's `start_pos` / `end_pos`, with that call's tool & inp.
  - **Path identity** = `os.path.normpath(raw_path_string)` AS-GIVEN (no cwd resolution). Documented CEILING: a relative
    Bash path and an absolute file-tool path to the SAME real file are counted as DISTINCT identities — this is
    CONSERVATIVE (splits a real file into two ids, REDUCES measured reuse), it cannot inflate any gate.
- **UNIT:** each file-path touch that is followed by `>= 1` LATER touch of the SAME path identity in the SAME session.
  (For a path with touches t1<...<tk, units = t1..t_{k-1}.)
- **gap_to_next(unit)** = `(start_pos(next same-path touch) − end_pos(this touch)) / 4.0` tokens.
- **LABEL (frozen):** `next_reuse_is_FAR = (gap_to_next > 8192 tok)`.  NEAR = `gap_to_next < 512 tok` (used ONLY for RE-A0).
- **gap_since_last(unit)** = `(start_pos(this touch) − end_pos(prev same-path touch)) / 4.0`. For the FIRST touch of a
  path (no prior touch) → `start_pos(this touch) / 4.0` (distance from session start; a never-seen path is maximally stale).

## 2. FEATURES (frozen). ALL features are CAUSAL / history-only (computed from the past + the current call); the LABEL is the FUTURE gap_to_next. No leakage by construction.
**B0 (JOINT baseline = LRU + LFU + tool + file-class):**
- `c0 = log1p(gap_since_last)`              (recency / LRU)               [continuous, standardized]
- `c1 = log1p(freq_so_far)`                 (count of touches of this path up to & incl. now; LFU) [continuous, std]
- `tool one-hot`                            (top-12 tool names by unit frequency + OTHER)
- `file-class one-hot`  [FIX-6]             (classes below). **NOTE:** this categorical IS the "path-extension class"
   listed in the charter's B1 set; per FIX-6 it lives in B0, so B1 does NOT re-add it (re-adding identical columns is
   degenerate collinearity contributing exactly zero discriminative power — B1 gets NO credit for the extension signal).

**file-class map (frozen, by lowercased extension of basename):**
  CODE = .py .js .ts .tsx .jsx .java .c .cc .cpp .h .hpp .go .rs .rb .php .swift .kt .scala .sh .pl .lua .m .r ;
  CONFIG = .json .yaml .yml .toml .ini .cfg .conf .env .lock .properties .gradle ;
  DOC = .md .markdown .txt .rst .adoc ; DATA = .csv .tsv .parquet .jsonl .ndjson .arrow .pkl .npy .db ;
  NOTEBOOK = .ipynb ; WEB = .html .css .xml .svg ; NOEXT = (no extension) ; OTHER = anything else.

**B1 = B0 + working-set features (the cheap CAUSAL surplus under test):**
- `path_depth`             = number of `/` in normalized path        [continuous, standardized]
- `log1p(exploration_breadth)` = # DISTINCT OTHER paths touched between the previous touch of this path and this touch
                              (since session start for first touch)   [continuous, standardized]
- `mut_flag`              = 1.0 if this touch MUTATES else 0.0 (READ). MUT iff tool ∈ {Write,Edit,MultiEdit,NotebookEdit,
                            apply_patch,write,edit} OR (tool is Bash/shell/exec AND command matches a write op near a
                            path: leading `mv|cp|rm|tee|touch|mkdir|dd|sed -i` OR contains `>`/`>>`). Else READ. [binary]
- `log1p(intervening_calls)` = # tool calls between previous touch of this path and this touch (call-index since start
                            for first touch)                          [continuous, standardized]

**B0+forecast (Marconi-style reuse-likelihood forecast added to B0; RE-A2(b) incumbent):**
- `fc1 = log1p(mean of this path's PRIOR observed inter-touch gaps)`  (running reuse-distance estimate)  [continuous]
- `fc2 = log1p(# of this path's PRIOR observed inter-touch gaps)`     (forecast confidence / intervals seen) [continuous]
  Faithful-but-simplified operationalization note: Marconi (2411.19379) forecasts reuse likelihood across a hit-scenario
  taxonomy; our cheap stdlib proxy is the per-path running reuse-distance estimate — the history-only CORE of such a
  forecast. This is the strong incumbent B1 must beat for the YELLOW→GREEN upgrade.

**Logistic regression (EXP-0054/0055 verbatim):** pure-stdlib batch GD, L2 λ=1.0, GD_ITERS=400, GD_LR=0.3, continuous
features standardized. AUC = Mann-Whitney rank statistic on pooled session-clustered 5-fold CV held-out scores
(folds = `det_hash(session)%5`, never leak a session across train/test). dAUC CI = session-clustered bootstrap (resample
SESSIONS w/ replacement, B=2000, bootstrap the held-out per-call scores by session; 95% LB = 2.5th pct). SEED=20260601.

---

## GATES — exact metric, threshold, decision (ALL FROZEN)

### RE-A0 — BIMODALITY FLOOR (NOT load-bearing). Over ALL reuse units (using gap_to_next):
- `share_FAR = #(gap_to_next > 8192) / N_units`,  `share_NEAR = #(gap_to_next < 512) / N_units`.
- **PASS iff** `share_FAR >= 0.15` AND `share_NEAR >= 0.10`.  (live design: near≈0.15, far≈0.25.)
- **FAIL (unimodal)** → **CLEAN KILL** (report honestly; the distribution is not bimodal → no eviction-distance lever).

### RE-A1 — LOAD-BEARING KILLER. dAUC = AUC(B1) − AUC(B0) on the far-reuse label, CC primary corpus.
- Session-clustered 5-fold CV; 2000× session-clustered bootstrap of dAUC; per-fold dAUC reported.
- **PASS iff** `dAUC_LB95 > 0` AND `dAUC_point >= 0.03` AND **all 5 folds positive**.
- **FAIL (any of the three)** → **CLEAN NEGATIVE-KILL:** far-reuse is NOT predictable beyond recency+freq+file-class →
  existing reuse-aware policies (RadixAttention/vLLM-APC LRU + LFU) are SUFFICIENT → do NOT build a new cheap causal
  feature. (Powering: require N_units ≥ 100, far-pos count ≥ 20, 0 < pos_rate < 1, ≥ 2 sessions; else `underpowered`.)

### RE-A2 — MATCHED-RECENCY CONTROL + REUSE-FORECAST BASELINE (the YELLOW→GREEN upgrade gate).
- **(a) matched-recency:** `ws_score` = session-clustered-CV held-out logistic prediction on WORKING-SET-ONLY features
  {path_depth, exploration_breadth, mut_flag, intervening_calls}. Decile the units by `gap_since_last` (10 equal-count
  bins). In each decile compute Mann-Whitney `AUC(ws_score, far_label)` + 2000× session-clustered bootstrap LB95.
  **PASS-(a) iff `>= 6` of 10 deciles have `AUC_LB95 > 0.5`** (working-set still separates far-reuse WITHIN matched
  recency → not recency-in-disguise). Report all 10 deciles.
- **(b) beat the forecast incumbent:** `dAUC_fc = AUC(B1) − AUC(B0+forecast)`, session-clustered bootstrap LB95.
  **PASS-(b) iff `dAUC_fc_LB95 > 0`.** Report BOTH `dAUC` (B1 vs B0, = beats LRU+LFU+class) and `dAUC_fc` (B1 vs
  B0+forecast). If B1 beats B0 but `dAUC_fc_LB95 <= 0` → **stays YELLOW** (beats the weaker incumbent only).
- **RE-A2 GREEN iff PASS-(a) AND PASS-(b).**

### RE-A3 — EVICTION-COST TRANSLATION, CAPACITY CURVE (descriptive translation; reported across a RANGE, not a gate).
- Fixed-capacity per-path cache sim over the touch stream, per session, capacity `C = ceil(frac · n_distinct_paths)` for
  `frac ∈ {0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 0.90}` (FROZEN list).
- On each touch of path p: HIT if p∈cache (no recompute); else MISS → `recompute_mass += size(p)`, insert p, evict if full.
  `size(p)` = token footprint of the (re)loading touch = `(len(args_str)+len(result))/4`.
- Policies: **LRU** (evict oldest last-touch), **Oracle/Belady** (evict farthest next-touch; never-again first),
  **B1-pred** (evict cached path with HIGHEST predicted far-reuse prob from B1 CV held-out score at its last touch;
  tie-break LRU). Belady = the ceiling; B1-pred approximates it from history only.
- Report per capacity: recompute_mass(LRU / Oracle / B1), `saved_frac_B1 = (LRU−B1)/LRU`, `saved_frac_oracle =
  (LRU−Oracle)/LRU`, and the **Gini** of per-path recompute mass under LRU vs B1 (Lorenz heavy-tail lift). Pooled over CC.

### RE-A4 — CROSS-INSTRUMENT (HARD GATE). Replicate RE-A1 on Codex.
- Compute `dAUC(B1 vs B0)` on Codex (same pipeline). **SIGN AGREEMENT with CC is REQUIRED for an overall PASS**
  (both dAUC_point > 0). Sign disagreement ⇒ **NOT PASS** (report honestly). If Codex is `underpowered` (fails the
  RE-A1 powering floor) → sign agreement cannot be established → **NOT PASS** (documented, not fabricated).

### STAT DISCIPLINE (frozen).
- Report fold-to-fold dAUC std; require ALL 5 folds positive for RE-A1 PASS (sign stability).
- **HHI by session** over the reuse units: `HHI = Σ_s (n_units_s / N_units)^2`. If `HHI > 0.20` → FLAG that AUC is
  dominated by 2–3 sessions and DOWN-WEIGHT the conclusion (reported on both corpora). Effective-n note alongside N.

---

## OVERALL DISPOSITION (frozen decision tree)
- **GREEN / committee-ready PASS** iff: RE-A0 PASS (bimodal) AND RE-A1 PASS (LB95>0 & point≥0.03 & all-5-folds+) AND
  RE-A4 sign-agreement AND RE-A2 GREEN (matched-recency PASS-(a) AND beats B0+forecast PASS-(b)). HHI not flagged (or
  conclusion explicitly down-weighted if flagged).
- **YELLOW** iff RE-A0 PASS AND RE-A1 PASS AND RE-A4 sign-agree BUT RE-A2(b) fails (beats LRU+LFU+class but not the
  Marconi-style forecast) — a cheap causal feature helps over the weakest incumbent only; not a green upgrade.
- **CLEAN NEGATIVE-KILL** iff RE-A1 fails → far-reuse not predictable beyond recency+freq+file-class → **LRU+LFU(+forecast)
  is sufficient; do NOT build a new reuse-aware eviction feature.** (First-class publishable negative.)
- **CLEAN KILL** iff RE-A0 fails (unimodal — no eviction-distance lever).
- **NOT PASS (cross-instrument)** iff RE-A4 sign disagrees or Codex underpowered.

## OUTPUTS
- `impl/reuse_distance_census.py` (this run; header docstring; stdout `tee`'d to `logs/run_main.log`)
- `results/summary.json` (all gate numbers: n, #sessions, per-tool/per-file-class breakdown, dAUC point+LB95+per-fold+std,
  RE-A0 shares, RE-A2 per-decile + forecast-baseline dAUC, RE-A3 capacity curve + Gini, RE-A4 Codex dAUC+sign, HHI)
- `impl/analysis.md` (honest per-gate DISPOSITION, headline one-liner, committee-facing recommendation)
