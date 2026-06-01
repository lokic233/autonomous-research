# PROJ-0011 — Agent KV Reuse-Distance Bimodality: A Characterization for Eviction-Policy Selection

Seeded: 2026-06-01 by orchestrator-r7-001 (design committee proj0011_design, 6/6 ALL_COMMITTEE_DONE).
Verdict: YELLOW / seed-with-mandatory-fixes (FINAL_VERDICT A=yellow; 2 green + 3 yellow + 0 red). First claim: CLAIM-0022.
REFRAMED from a mechanism-discovery charter to a CHARACTERIZATION contribution (PROJ-0002 precedent) — see MANDATORY FIX 1.

## THESIS (characterization framing)
Cross-request prefix caches (SGLang RadixAttention 2312.07104, evicts the radix tree by LRU; vLLM PagedAttention/APC
2309.06180, LRU block eviction) assume the hottest blocks are the most-recently-used. But an agent's KV working set
(the files it re-touches) has BIMODAL reuse distance — on the live CC corpus, of 2512 file-path reuses across 34/65
sessions, 15% recur within <512 tok (near) while 25% recur only after >8192 tok (far), p99=514k tok. Under realistic
cache pressure a recency-LRU policy evicts the FAR-reuse file's KV before it is needed (full recompute) while a
reuse-distance-aware policy would retain it. The structural cause: agent file access is task-locality-driven, not
recency-driven (a config touched at step 2 is re-read at step 40 after an exploration detour). NON-MECHANISM-NOVEL
(the "non-LRU is better" mechanism is independently proposed by >=5 sources — FIX 2); the CONTRIBUTION is (a) the
first measured bimodal reuse-distance distribution of real agent KV working sets and (b) a dAUC-over-{LRU+LFU+reuse-
forecast} falsification with matched-recency stratification showing whether a CHEAP CAUSAL feature predicts the
far-reuse blocks LRU wrongly evicts, beyond what recency+frequency+a Marconi-style forecast already capture.

## FIRST CLAIM (CLAIM-0022)
A cheap CAUSAL (history-only) feature predicts which cached agent file-prefix will be re-touched at a FAR reuse
distance (the blocks recency-LRU wrongly evicts) OVER AND ABOVE a joint baseline that already contains the LRU+LFU
statistics AND a reuse-forecast baseline. Clean publishable negative if it fails: agent file reuse is recency/
frequency/forecast-dominated -> existing reuse-aware policies are sufficient -> no further cheap causal feature
warranted. The LOAD-BEARING contribution is the CHARACTERIZATION (bimodality + matched-recency falsification), not a
mechanism discovery.

## PRE-REGISTERED RE GATES (committee MANDATORY FIXES baked in)
- RE-A0 (bimodality floor, NOT load-bearing): >=15% of file-path reuses FAR (>8192 tok) AND >=10% NEAR (<512 tok)
  (live near=0.15, far=0.25). If unimodal -> clean kill.
- RE-A1 (LOAD-BEARING KILLER, over JOINT baseline): unit = each file-path touch followed by >=1 later touch in the
  same session. Label = the NEXT reuse of this path is FAR (>8192 tok). B0 = {log1p(gap-since-last-touch),
  log1p(path-touch-freq-so-far), tool one-hot, **file-class one-hot** [FIX-6]}. B1 = B0 + causal working-set features
  (path-depth, path-extension class, #distinct-paths-touched-since-this-path-last-seen [exploration breadth], MUT-vs-
  READ tool arg, intervening-tool-call count). PASS iff dAUC_LB95>0 AND dAUC_point>=0.03 AND all-5-folds-positive.
  If <=0 -> far-reuse not predictable beyond recency+freq+file-class -> clean negative.
- RE-A2 (matched-recency control + REUSE-FORECAST baseline, UPGRADE GATE) [FIX-3]: (a) within recency deciles, the
  working-set features must still separate far-reuse (per-stratum Mann-Whitney AUC, session-clustered bootstrap) —
  else recency-in-disguise; AND (b) the discriminator must BEAT a **Marconi-style reuse-forecast baseline** (2411.19379)
  added to B0, not merely {LRU+LFU} — else it only beats the weaker of two known incumbents. THE yellow->green gate.
- RE-A3 (eviction-cost translation, CAPACITY CURVE) [FIX-5]: convert predicted far-reuse hits into recompute-token
  mass SAVED under a fixed-capacity sim (LRU vs oracle vs B1) — Lorenz/Gini lift of recompute mass, reported ACROSS A
  RANGE of capacity settings (not a single point). AUC alone discards the heavy-tail recompute structure.
- RE-A4 (cross-instrument, HARD GATE): Codex replication — dAUC sign agreement REQUIRED for PASS.
- STAT DISCIPLINE [FIX-4]: fold-to-fold dAUC std; ALL 5 folds positive (sign stability); **Herfindahl by session** on
  the 2512 reuses / 34 sessions (effective-n) — if >0.2, flag AUC dominated by 2-3 sessions and down-weight.

## NOVELTY / NON-COLLISION (committee-checked; CHARACTERIZATION not mechanism)
MANDATORY FIX 2 — the "non-LRU reuse-aware eviction beats LRU" MECHANISM is independently proposed by: ScaleSim
2601.21473 (invocation-distance memory mgmt), Marconi 2411.19379 (admission+eviction by reuse-likelihood forecast —
this is RE-A2's forecast baseline), KVFlow 2507.07400 (agent-step-graph steps-to-execution eviction), CacheSage
2605.27744 (learned per-workload agent transition matrix survival eviction), SAECache 2605.18825 (semantic-aware
eviction, LRU "treats blocks uniformly"). This project does NOT claim the mechanism as a discovery; it CHARACTERIZES
the live bimodal reuse-distance distribution and runs the dAUC-over-{LRU+LFU+forecast} falsification with matched-
recency discipline against named incumbents RadixAttention 2312.07104 / vLLM APC 2309.06180. Within-sequence
attention-score eviction (H2O / SnapKV / HashEvict 2412.16187 / AhaKV 2506.03762 / RAC 2602.21547) is a different
axis (intra-sequence token importance, not inter-request file-reuse distance). Cemetery non-collision: lever is
eviction-DISTANCE — not byte-identical content (DEAD-0016/PROJ-0008), not drift (DEAD-0015/PROJ-0007), not error-fork
(DEAD-0017/PROJ-0010), not within-tool whale (DEAD-0018/PROJ-0009), not edit-invalidation (PROJ-0002). No decode-SD.

## L0 GATING EXPERIMENT (EXP-0057)
CPU, Mac stdlib, reuse EXP-0054 parse+JOIN + auc/logistic_fit/session-clustered-CV/2000x bootstrap. Extract file
paths from inp (file_path/path/notebook_path + Bash command path tokens); for each path-touch followed by a later
touch emit (gap_since_last, touch_freq_so_far, tool, file_class, working_set_features, next_reuse_is_far_label);
fit B0 vs B1 session-clustered CV; bootstrap dAUC; matched-recency stratified control + reuse-forecast baseline +
capacity-sim recompute Lorenz curve. ~2500 path-reuse rows, <10s. YELLOW->GREEN contingent on ALL fixes incorporated
into pre-registration BEFORE L0 entry (fixes change B0 composition + RE-A2 gate).
