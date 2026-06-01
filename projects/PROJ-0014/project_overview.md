# PROJ-0014 — Agent KV Eviction Benchmark: Does a Cheap Frequency-Aware Policy Capture the PROJ-0011 Belady Gap?

Seeded: 2026-06-01 by orchestrator-r7-001 (design committee proj0013_design, 6/6 ALL_COMMITTEE_DONE).
Verdict: YELLOW / seed-with-mandatory-fixes (FINAL_VERDICT B=yellow; systems_reviewer RED rebutted+reframed, 4 yellow).
First claim: CLAIM-0025. POLICY-COMPARISON BENCHMARK (not a novel-mechanism claim, not a dAUC-predictability claim).

## THESIS (REFRAMED per committee FIX-1 — this is a BENCHMARK, not a mechanism proposal)
PROJ-0011 ESTABLISHED (surviving characterization, EXP-0057): agent file-path KV reuse distance is bimodal (18.9%
far >8192 tok, p99 ~86k) and LRU is suboptimal vs a Belady oracle (<=13% recompute-mass gap), but a cheap CAUSAL
PREDICTOR of far-reuse fails (DEAD-0019). OPEN QUESTION: on real agent KV traces, how much of the LRU->Belady
recompute-mass gap is captured by EXISTING / CLASSICAL frequency-aware eviction policies (SGLang's shipped
LFU/SLRU, ARC, LRU-K, GDSF, static pin+LRU) WITHOUT future knowledge? This is a BENCHMARK of deployed/classical
policies against the Belady oracle on agent traces — the EMPIRICAL gap-capture measurement is NOT shipped and is the
deliverable. NOT a claim to a novel eviction mechanism (SGLang ships LFU/SLRU/priority eviction in evict_policy.py;
TensorRT-LLM ships KvCacheRetentionConfig).

## FIRST CLAIM (CLAIM-0025)
On real agent KV working-set traces, a cheap frequency-aware eviction policy (best of {SGLang-LFU/SLRU, ARC, LRU-K,
static pin+LRU}) captures >= 50% of the LRU->Belady recompute-mass gap with no future knowledge, at matched cache
residency. Clean negative if FALSE: the Belady gap is realizable ONLY with future knowledge (best classical policy
captures < 50%) -> LRU/LFU is the right cheap policy, the gap is oracle-only -> "the <=13% agent-KV Belady gap is
not cheaply capturable; ship classical eviction, invest elsewhere" (reinforces DEAD-0019 from the policy side).

## PRE-REGISTERED RE GATES (committee MANDATORY FIXES baked in)
- RE-B0 (premise re-confirm): reproduce PROJ-0011 bimodality + LRU<Belady gap on current corpus (far-share >= 0.15,
  Belady saves >= 5% recompute over LRU). Floor; if gap vanished -> no project.
- RE-B1 (LOAD-BEARING benchmark): at a PRE-DECLARED N x capacity grid (>=5 capacities spanning working-set size),
  measure recompute-mass for {LRU, SGLang-LFU, SLRU, ARC, LRU-K, static pin+LRU(N in 2/3/5), Belady-oracle}. PASS =
  the BEST cheap policy captures >= 50% of the (LRU - Belady) gap at >= 3 of 5 capacities.
- [FIX-2 KILLER BASELINE] ARC + LRU-K are MANDATORY named baselines (not just LRU vs custom two-tier = strawman).
  If ARC captures the same Belady gap, the custom two-tier is OBSOLETE -> that is the killer experiment; report it.
- [FIX-5 anti-tautology MATCHED-RESIDENCY] charge pinned blocks honestly (pinned blocks occupy cache); the win must
  persist at MATCHED resident mass, else capacity illusion -> kill.
- [FIX-3 multiple-testing] pre-declare the N x capacity grid; apply BH/Bonferroni across the 15-cell
  best-of-{N=2,3,5} x 5-capacity free-parameter search.
- [FIX-4 honest cross-instrument] report Codex EVEN WHEN not bimodal (selective CC-only reporting = kill flag; Codex
  non-bimodality must appear with honest framing). CC-primary declared.
- RE-B3 (robustness): session-clustered 2000x bootstrap CI on captured-fraction; HHI flag.
- PRIOR ART: KVFlow 2507.07400, CDN-Belady LRU-BaSE/PFOO 2212.13671, Cold-RL 2508.12485, classical SLRU/ARC/GDSF/
  LFU-pinning, Marconi (reuse forecast), ScaleSim (invocation-distance), SGLang 2312.07104 evict_policy.py,
  TensorRT-LLM KvCacheRetentionConfig.

## NOVELTY / NON-COLLISION (committee-checked)
B is a STATIC-POLICY BENCHMARK, NOT a predictor (vs DEAD-0019/PROJ-0011 which killed a cheap CAUSAL PREDICTOR of
far-reuse; DEAD-0019's OWN revival gate explicitly invited "a policy that beats LRU"). The eviction MECHANISMS are
deployed (SGLang LFU/SLRU, TensorRT retention) — the contribution is the agent-trace gap-capture MEASUREMENT, not a
mechanism. Not DEAD-0016 (byte-identical), not PROJ-0002 (edit-invalidation). No decode-time SD.

## L0 GATING EXPERIMENT
Reuse the EXP-0057 capacity-sim harness VERBATIM; add SGLang-LFU/SLRU/ARC/LRU-K/static-pin policies; sweep the
pre-declared capacity grid; compute captured-fraction-of-Belady-gap + matched-residency control + BH-corrected CIs;
report CC + Codex. CPU stdlib, <30s. Produces a POSITIVE (a cheap classical policy captures the gap -> ship it) OR a
clean negative (gap is oracle-only -> reinforces DEAD-0019 from the policy side).
