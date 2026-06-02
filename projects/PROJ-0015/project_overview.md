# PROJ-0015 — Agent Serving KV Is Tool-Result-Dominated: Prefill Token-Mass Decomposition

**Type:** CHARACTERIZATION (decisive descriptive RESULT; publishable positive-or-negative; NO predictor, NO dAUC).
**Seeded:** 2026-06-01 by orchestrator-r8-001 via the proj0015_design committee (5/5 unanimous PICK of Charter A over Charter C; FINAL_VERDICT green-seed; Charter C KILLED at design for mechanism mischaracterization of APC). Refills portfolio 3/4 -> 4/4 after PROJ-0014 converged (DEAD-0021).
**First claim:** CLAIM-0026. **L0 gating experiment:** EXP-0061 (Mac CPU stdlib, reuse EXP-0054/0057/0059 parse+JOIN + 2000x session-clustered bootstrap; NO numpy).

## THESIS (REFRAMED per mandatory fix #1 — "TOKEN MASS", NOT "serving dollar")
The LLM-serving stack (DistServe 2401.09670 / SplitWise 2311.18677 prefill/decode disaggregation; chunked-prefill Sarathi-Serve 2403.02310; RadixAttention 2312.07104 / vLLM-APC 2309.06180 prefix caching) was architected for CHAT (prompt = human text; served stream dominated by model DECODE). Agentic workloads INVERT this: the served context is overwhelmingly EXTERNAL TOOL-RESULT TEXT fed back as PREFILL. This project delivers — TO OUR KNOWLEDGE, the first (novelty bounded by available prior art; the mandated live >=2-source web sweep was egress-blocked, see VERDICT-0073 GAP-3 scoping) — a granular TOKEN-MASS decomposition of real agent serving traces — tool-result vs arg vs decode-interstitial — with its heavy-tail (Gini) and cross-instrument structure, establishing WHERE the agent serving prefill TOKEN MASS lives (NOT $ cost; token mass != cost mass — prefill is ~10-100x cheaper per token than decode). The genuinely-novel delta beyond "prefill-heavy folklore" is the heavy-tail concentration (cacheable hot spots) + the granular decomposition + cross-instrument replication that the disaggregation/caching literature ASSUMES but never MEASURES on real agent tool-loops.

## PRE-MEASURED LIVE STATS (premeasure_r8 cross-check, this design pass; corpora CC ~69 sess/~2474 calls, Codex ~89 sess/~2968 calls)
- tool-RESULT/span: CC 0.626 (CI95 [0.498, 0.705]) / Codex 0.861; per-session result-frac median CC 0.688 / Codex 0.849.
- top-decile result-mass: CC 0.788 (CI95 [0.619, 0.872]) / Codex 0.576; Gini CC 0.864 / Codex 0.748.
- NOTE: CC result-dominance CI95 lower bound is BORDERLINE 0.498-0.502 vs the 0.50 gate; Codex (0.845 LB95) is the strong-instrument anchor. The conservative-denominator headline (fix #3) + cross-instrument margin (fix #5) handle this.

## BINDING MANDATORY FIXES (L0 PRE_REGISTRATION must honor ALL 9; from the design committee)
1. REFRAME: strike "serving dollar" -> "prefill TOKEN MASS". Optional SECONDARY RE-A4 cost-weighted variant using a published prefill-vs-decode $/token ratio (Splitwise 2311.18677 / DistServe 2401.09670), reported SECONDARY not headline.
2. CONTRIBUTION = the GRANULAR decomposition (result vs arg vs decode-interstitial) + heavy-tail Gini + cross-instrument replication. Explicitly concede "prefill-heavy" is already ASSUMED by DistServe/SplitWise; the bare direction is NOT the claim; reject any "rediscovers prefill-heaviness" reading.
3. RE-A2 DENOMINATOR: the MOST-CONSERVATIVE denominator (assistant-text-block-only) is the HEADLINE; raw-span + non-result-mass are robustness checks. Commit BEFORE seeing the conservative number. If conservative <50% -> downgrade to "largest single component" not "majority".
4. STATIC vs DYNAMIC: distinguish static system-prompt prefix (KV memory after turn 1, ~0 marginal compute) from dynamic per-turn tool-result prefill (both). Report both shares; "tool-result dominated" refers to DYNAMIC marginal prefill, not total KV memory.
5. RE-A3 CROSS-INSTRUMENT MARGIN: both LB95 > 0.50 AND |CC - Codex| < 0.40 on the chosen denominator. Direction-only-replication-with-divergent-magnitude -> "instrument-dependent magnitude" not "replicated dominance".
6. GINI WITH CIs: report Gini with 2000x session-clustered bootstrap CI + a CI on the CC-Codex Gini delta. No headline point estimates without CIs.
7. OPERATIONAL DEFINITIONS: pin "tool-result"/"arg"/"decode-interstitial" to parse_cc_session/parse_codex_session FIELD NAMES in the pre-reg; disclose + pre-register the tokenizer (or explicit char-proxy).
8. CLEAN-NEGATIVE CRITERION: NOT just "LB95 < 0.50". ALSO clean-negative if "Gini < 0.5 on either corpus" (no heavy tail = no cacheable hot spots = boring uniform).
9. MANDATORY RELATED WORK: cite + one-line differentiate DistServe, SplitWise, DuetServe, Sarathi-Serve, Parrot, Autellix, RadixAttention, vLLM-APC ("does not measure the prefill/decode token-mass split of real agent tool-loops").
MANDATORY BASELINES: (a) a standard CHAT trace (ShareGPT or equivalent multi-turn) showing the prefill/decode mass split is structurally different for agent tool-loops vs chat; (b) DistServe's ASSUMED prefill/decode mix — cite it and show the measured agent ratio diverges.

## RE GATES (pre-register, frozen)
- RE-A0 (LOAD-BEARING): pooled result/total-stream fraction, 2000x session-clustered bootstrap LB95 > 0.50 on CC AND Codex, on the CONSERVATIVE denominator (fix #3). Clean negative if CC LB95 crosses 0.50.
- RE-A1: top-decile result-mass LB95 > 0.50 both corpora; Gini w/ CI (fix #6, #8).
- RE-A2: three-denominator robustness, conservative = headline (fix #3).
- RE-A3: cross-instrument HARD GATE with equivalence margin (fix #5).
- Chat-baseline contrast (mandatory baseline a).
- STAT: HHI-by-session (premeasure HHI by result-tok 0.170 — near 0.20 flag, report session-median as robustness).

## NOVELTY / NON-COLLISION
Direct mass MEASUREMENT, no predictor (NOT DEAD-0017/18/19/20/21), no eviction mechanism (orthogonal PROJ-0011), no byte-identical-repeat (DEAD-0016), no edit-invalidation (PROJ-0002). DistServe/SplitWise/DuetServe/Sarathi/Parrot/Autellix/RadixAttention/vLLM-APC implement disaggregation/caching knobs but ASSUME the workload mix, never measure the prefill/decode token-mass split of real agent tool-loops. Charter C (cross-request staleness) was KILLED at design (APC is token-content-addressed -> changed content = miss not stale hit).
