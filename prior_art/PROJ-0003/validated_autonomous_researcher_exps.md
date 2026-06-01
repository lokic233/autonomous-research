# PROJ-0003 — Validated Autonomous-Researcher Experiment Digest

**Project:** PROJ-0003 — "Agent failure attribution & recovery (workload models)" / MAP-0002.
**Status: DONE** — negative-result + measurement-methodology paper FINALIZED. The original
predictive lineage (CLAIM-0008/0009/0010/0011) is refuted or deflated-to-config-fact; the one live
descriptive claim **CLAIM-0012** (failure burstiness) sits at **VERDICT-0049 = 5/6 GREEN +
area_chair evidence-weighted override**, at the HUMAN green/promote gate awaiting dengcchi's A/B
decision (engine unanimous-rule blocks auto-promote).

This file unifies all internal autonomous-researcher / lane notes for PROJ-0003 into one place.
Each section is a concise digest preserving substantive findings, EXP/CLAIM/VERDICT ids, and key
numbers. Source notes were folded in and removed. The companion file (`needs_attention.md`) remains
a separate prior-art record; the publishable paper/determination artifacts now live under
`projects/PROJ-0003/artifacts/`. The `crossharness_scripts/` directory — executable cross-harness
analysis code, retained — stays here as-is (it is code, not a note).

---

## 1. CLAIM-0009 — Cross-harness + interventional design (error-class → recovery MODALITY)

**Disposition: DONE — MIXED, deflated-to-config-fact + gate taxonomy.** Controlling verdict
VERDICT-0027 (chain V0018→V0020→V0021→V0026→V0027). Revival = off-node interventional only.

- **The confound.** On Claude Code every error-class maps to exactly one gate-type
  (`error-class → gate-type` is a perfect function), so modality cannot be attributed to error-class
  vs gate-type. EXP-0012: full 17-class taxonomy adds ≤0.2% over a single gate-type bit; 1 REDIRECTABLE
  bit ≈ full taxonomy; error-class→gate-type a perfect function. Two ways to break it: cross-harness
  replication (does the gate→modality mapping replicate on a 2nd corpus?) and interventional
  route-alteration (hold error fixed, change only the harness route).
- **The cross-harness result (FRESHLY RUN, the headline number).** Apples-to-apples Cramér's V of
  error-class → recovery-modality on the already-collected **Codex** corpus:
  **Codex V = 0.586, perm-p = 0.0002, N = 78 recovered failures**, vs the Claude-Code anchor
  (EXP-0009) **V = 0.717**. So the *association* replicates on a 2nd independent harness — both strong,
  both perm-p = 0.0002. (Corpora found on-node: Codex `~/.codex/sessions` 89 sess; Gemini
  `~/.gemini/tmp/*/chats` 62 sess; OpenCode 80 sess.)
- **Why it is NOT GREEN (honest).** (a) **Mechanism does not transfer** — Codex has no `web_disabled`
  clean REDIRECTABLE policy-gate; its V is carried by transient-exec failures (`cmd.notfound` 0.944,
  `proc.exit_nodetail` 0.842) redirecting to other exec tools, a "try-another-command" mechanism, not
  the REDIRECTABLE-vs-TERMINAL policy dichotomy that is CLAIM-0009's actual claimed law.
  (b) Under a uniform strict + double-log-deduped definition (EXP-0033) the dramatic CC-vs-Codex
  modality *contrast* COLLAPSES: Codex logs every call twice (`function_call` + `mcp_tool_call_end`);
  deduped, Codex preempts 100% (web twin fires before the block 152/152). Both harnesses are
  PREEMPT-dominant with near-zero *reactive* redirect (CC reactive 0.116, Codex 0.000); CC's headline
  66/66 redirect drops to 2/43 (later 5/43) under the uniform strict definition.
- **The 3-way alias (why the interventional leg is required).** Recovery modality is perfectly aliased
  HARNESS × MODEL × ERROR-NAMING: on-node MODEL⊗HARNESS is a perfect diagonal (Claude×ClaudeCode,
  GPT-5.5×Codex, Gemini×Gemini); only Gemini's block error names an in-inventory twin (2/9 reactive);
  arXiv:2603.02277 gives a per-MODEL disengagement account (GPT-5.2 92% disengage vs Claude 0%) of the
  same abandon-vs-persist observable. The ONLY model-agnostic harness present (OpenCode) logs 0/6
  required fields (no model/tool/args/outcome/order), so the de-aliasing cell cannot be run on-node.
- **The interventional PROTOCOL (pre-registered, off-node future work).** Canonical runnable spec
  consolidates v1 (laneD) + v2 (design) — both SUBSUMED/archival. An OpenCode-pivot 6-cell factorial
  (C1–C6) crossing F_harness × F_model × F_error_naming on an identical deterministic tool-block shim
  (`url_fetch` returns a byte-identical content-free hard-block; functional twin `web_search` in every
  cell). Primary metric = strict reactive-redirect share R = REDIRECT/(REDIRECT+ABANDON), preempts
  excluded. UNNAMED vs NAMED error-text sub-factor kills the EXP-0033 naming confound. N = 50/cell
  TARGET (min 30, robust 80); GLM coefficient on F_harness after conditioning on F_model +
  F_error_naming is the causal estimand; pre-registered binary PASS/KILL (no YELLOW). C1 (CC×Claude)
  and C4 (Codex×GPT) are positive anchor controls. **Off-node-blocked solely by harness logging.**
- **What still blocks 6/6 GREEN:** the interventional de-aliasing leg (off-node-blocked) + a sampled
  TERMINAL class (absent in both corpora).

## 2. CLAIM-0010 — Two-layer recovery reframe

**Disposition: DONE — DEAD as a standalone thesis; deflated-to-config-fact + residual-floor negative
result.** Controlling verdict VERDICT-0044 (chain V0030→V0035→V0044). Folded into synthesis §1.3.

- Asserted TWO-LAYER recovery: a coarse gate-table deterministic layer + a fine adaptive layer. **Both
  pillars dissolve.** The coarse "layer" is **91% one cell** (`web_disabled`; Theil-U 0.381→0.034
  without it, EXP-0029), and that cell's "deterministic redirect" is the EXP-0033 measurement artifact
  (~79% PREEMPT mislabeled as reactive redirect). EXP-0012 reduces the coarse layer to the same 1-bit
  gate-type config-fact.
- The fine layer's only material lift (**+12.6 pts**) lives in that same artifact cell and is
  CC-policy-specific. The durable remainder is the **negative result**: a ~0.6–0.74 residual-entropy
  floor on recovery modality.

## 3. CLAIM-0011 — Prior-art positioning + harness-routing claim

**Disposition: DONE — DEAD / refuted on-node.** Controlling verdict VERDICT-0042
(chain V0036→V0038→V0039→V0040→V0042). Folded into synthesis §1.4.

- **The claim:** recovery modality is determined by HARNESS ROUTING (cross-harness), invariant to
  error-class within a gate-type yet flips across harnesses on identical errors.
- **Positioning (GATE-3 / VERDICT-0038):** three orthogonal axes — WHAT fails (MAST/AgentBench
  taxonomy), HOW the MODEL recovers (Reflexion/Self-Refine — the NULL CLAIM-0011 refutes), HOW recovery
  is ROUTED (the harness layer, where CLAIM-0011 lives). EXP-0012 is the anti-tautology anchor: full
  17-class taxonomy adds ≤0.2% out-of-sample LOO-Brier over a single gate-type bit (full taxonomy
  +40.1% vs null on 233 recovered failures, K=6).
- **Why refuted:** the headline cross-harness contrast (CC 66/66 redirect vs Codex 0/142 abandon) was a
  **Codex double-log artifact** — deduped, Codex preempts 152/152; both harnesses preempt-dominant. The
  only surviving significant difference (CC reactive 5/43 vs Codex 0/152, Fisher p=0.0004) is
  **direction-wrong** vs the claim and **perfectly aliased with MODEL disposition** (arXiv:2603.02277).
  What survives is the non-novel pre-existing (EXP-0008 / MAP-0002) gate taxonomy, not a routing law.

**Cross-cutting (CLAIM-0008/0009/0010/0011):** CLAIM-0008 (error-class predicts recovery OCCURRENCE)
is DEAD/refuted — apparent V=0.64 was a lower-bound recovery-definition artifact carried by the
`web_disabled` cell (0/109 "unrecoverable"); counting cross-tool workarounds washes it out
(V 0.64→0.24, perm-p=0.164 n.s.; LOO-Brier +0.087→~0; permanence φ 0.45→0.14) — VERDICT-0016. The three
modality claims (0009/0010/0011) all reduce to the same two components: (a) the harness-agnostic gate
taxonomy (redirectable / grant-required / transient) surviving as a *characterization*, and (b) the
negative results. The genuinely durable positive contribution is the **M1–M11 measurement methodology**
that caught the artifacts (PAPER_SYNTHESIS §2).

## 4. CLAIM-0012 — Failure burstiness / over-dispersion (Cox-vs-Hawkes) — the live GREEN-path

**Disposition: LIVE — VERDICT-0049 = 5/6 GREEN + area_chair evidence-weighted override**, at the
HUMAN green/promote gate awaiting dengcchi A/B. Verdict chain VERDICT-0046 → V0047 → V0048 → V0049.

- **The estimand (novel, web-checked):** tool-call failures within a real agent session are temporally
  CLUSTERED (over-dispersed/bursty) more than a within-session Bernoulli/Poisson null. Live prior-art
  sweep: no published work measures the burstiness coefficient of tool-call failures in real agent
  traces (closest neighbors are taxonomic/attribution — 2509.25370, 2512.07497, AgentProp-Bench
  2604.16706, ag2ai 2505.00212 — or multi-agent message cascades 2603.04474; SRE/cyber baselines are
  Hawkes self-exciting). Bar RAISED: the correct null is NOT Poisson (Barabási 2005; Goh-Barabási 2008;
  Karsai-Jo 2025), and arXiv 2604.15084 (static heterogeneity manufactures apparent burstiness) is the
  single most dangerous hostile cite — defended by tool-stratified permutation (EXP-0041) + Cox-vs-Hawkes
  BIC (EXP-0042).
- **H1 (3-harness descriptive over-dispersion): ROBUST.** EXP-0037 candidate (runs-test): CC Stouffer
  Z=−4.07 (p≈2e-5, 12/17 sess Z<0), Codex deduped Z=−15.07 (33/43 Z<0). Decisive-cell ablation
  reclassifying `web_disabled` as non-failure STRENGTHENS CC (−4.07→−4.63) — NOT a `web_disabled`
  artifact. (B,M)-plane (EXP-0043): CC B_corr=0.429, Codex 0.276, Gemini 0.214 (crosses 0); memory M
  crosses 0 everywhere (agent ≈ human-email heavy-tail with NO memory).
- **H2 (discriminating self-excitation BEYOND static rate-heterogeneity): GREEN on Codex only.** The
  progression EXP-0042 → EXP-0043 → EXP-0044 narrowed the claim from "3-harness" to **"1 clean harness
  (Codex)"**:
  - **EXP-0042** re-verified CC: per-session tool-stratified Z median 0.0 (12/19 sess ≈0); unweighted
    Stouffer −2.33 (p=0.0098); size-weighted −6.59 is a √n artifact (one 862-call session, w=29);
    **LOSO kill: drop that session → −0.89, p≈0.19 NON-sig.** CC's discriminating leg is
    aggregation-carried / fragile. Full-corpus Codex Hawkes ΔBIC=+28.32 (α=4.45, β=1.25).
  - **EXP-0044** cleared all 3 VERDICT-0047 BLOCKING ablations on Codex: **B1 Codex LOSO PASS** (not a
    single-session artifact); **B2 latent-state Cox PASS** (ΔBIC +15.0 vs steelman; CC marginal +8.9;
    **Gemini FAIL −0.45** — its "memory" is time-varying heterogeneity); **B3 gate-stripped Hawkes** —
    **Gemini FALSIFIED** (α→0, ΔBIC→−9.4; 98% schema/path gates = mechanical artifact), CC survives
    (α stable), Codex genuine-exec. Codex corpus: 64 sess ≥8 calls, 2001 calls, 106 fails, 60
    inter-failure gaps.
  - **Wall-clock refit** (defensive, no verdict change): refit Hawkes on real ISO-8601-ms timestamps
    (100% coverage, time-monotonic) instead of call-index — **ΔBIC=51.1 SURVIVES** (interior β-max
    ~0.8/s; de-coarsening converges to call-index ref 26.85). Addresses systems_reviewer external-
    validity caveat, not the altitude YELLOW.
  - **IC-selection small-N citation** (closed VERDICT-0048's lone required_evidence): N=60 gaps is
    small-sample regime for BIC Hawkes-vs-Cox; cite Vrieze 2012, Hurvich-Tsai 1989 (AICc), and the
    Filimonov-Sornette small-N Hawkes-estimation caveat; show the conclusion does not hinge on a single
    fragile IC comparison. VERDICT-0048 = YELLOW-CLEAN ("one citation from GREEN").
- **Altitude-lifter playbook (path-B prep, NOT executed).** The lone VERDICT-0049 YELLOW (product_realist)
  is a contribution-ALTITUDE objection (1 clean harness, modest N~60, descriptive-only, not a uniform
  3-harness law), not an evidential gap. **The altitude is essentially fixed by available data —
  path B cannot cheaply help:** (L1) 2nd clean genuine-exec harness OFF-NODE-BLOCKED (only `.codex`/
  `.claude`/`.gemini` are real corpora on-node; everything else empty/certs/config); (L2) Codex corpus
  EXHAUSTED (98 jsonl, <2% headroom from short sessions); (L3) wall-clock re-clock CPU-doable but
  altitude-orthogonal (done); (L4) phase-Cox regularization is a design refinement, altitude-orthogonal.
  Argues for **path A (accept the area_chair override + promote)**.
- **Honest disposition:** STILL YELLOW at the originally-claimed altitude; defensible 1-clean-harness
  (Codex) GREEN-able core. H1 = 3-harness-descriptive; H2 = Codex-clean only (Gemini killed, CC
  fragile-but-not-gate-driven side-result).

## 5. EXP-0037 — Burstiness fresh-claim candidate (seed origin of CLAIM-0012)

**Recommendation: SEED (cautiously).** The fresh angle that became CLAIM-0012: an arrival-process /
temporal-structure question (WHEN failures arrive), with NO prediction claim and NO error-class
conditioning — distinct from the refuted predictive lineage. Per-session Wald-Wolfowitz runs test on
the ordered failure-indicator sequence, Stouffer combined: CC Z=−4.07 (p≈2e-5), Codex deduped Z=−15.07.
Decisive-cell ablation (reclassify `web_disabled`) strengthens CC → burstiness is not a `web_disabled`
artifact. Replicates across 2 harnesses; survives the lineage's own decisive-cell ablation. Thin-n
caveats noted. Angles (a) failure-census and (b) recovery-cost were collision-killed; (c) temporal
structure was chosen.

## 6. Floor-hold lane notes (CLAIM-0012, holds 5–10) — collapsed

The CLAIM-0012 floor-hold notes (`FLOOR_HOLD`, `HOLD6`, `HOLD7`, `HOLD8`, `HOLD9`, `HOLD10`) are
maintenance heartbeats with no new findings: each records CLAIM-0012 at VERDICT-0049 (5/6 GREEN +
area_chair override) at the HUMAN green/promote gate, H2 fully hardened on every on-node axis (LOSO
ΔBIC≥17.6, steelman phase-Cox +15.0, gate-strip falsifies Gemini, IC-citation/small-N mitigation,
wall-clock ΔBIC=51.1 survives), sole open hold = product_realist altitude YELLOW with no cheap on-node
remedy (path B empty), and no new runnable on-node work can change the verdict — floor held pending
dengcchi's A/B decision.

## 7. Retained code

- **`crossharness_scripts/`** — executable cross-harness analysis code, retained. (`codex_redirgate.py`,
  `codex_xharness.py` — the apples-to-apples Codex cross-harness Cramér's-V / redirect-gate analyses.)

## 8. CLAIM-0012 — OOS predictive altitude-lift (EXP-0047) — HONEST MIXED/PARTIAL

**Goal (path B, no override):** answer product_realist's lone-YELLOW altitude objection
(CLAIM-0012 is "descriptive-only") by testing whether the fitted Hawkes self-excitation
kernel has genuine **out-of-sample predictive teeth** — earned on-node, CPU/stdlib only, no
2nd harness (off-node lever map-confirmed BLOCKED).

**Method:** forward time-split, one-step-ahead **prequential** OOS on Codex (49 mixed
sessions / 1716 calls / 111 fails). Params fit on TRAIN prefixes only (no leakage); test
intensities use observed history (filtering). Hawkes vs Poisson / Cox(per-tool rate, no
memory) / model-free recent-rate window. Session-bootstrap 95% CI + timing-permutation null.
Pre-registered pass-bar with explicit honest-null clause. Reuses `EXP-0041/burst_L3.parse_codex`
+ `EXP-0042/robust_L4.{cox_baseline_rates,fit_hawkes,...}`.

**Result — strict bar FAILS (0/3 splits); signal is real but heuristic-sized:**
- **Early-warning lift 7.8×–10.9×** (3/3 splits): a just-occurred failure raises forecastable
  next-call failure prob to ~0.19–0.37 vs ~0.024–0.038 base. Real, actionable recovery trigger.
- **Timing-permutation p=0.0005** (f=0.5,0.6): the Hawkes-over-Cox gain is genuine
  timing/clustering, not marginal rate. (Loses power at f=0.7: only 13 test fails.)
- **Memory > memorylessness OOS:** AUC_hawkes > AUC_cox > AUC_poisson in 3/3 splits; Hawkes
  beats Cox on dLL in 3/3 (boot95 lo>0 at f=0.5).
- **But** the **parametric Hawkes kernel does NOT robustly beat a trivial recent-failure-rate
  window** — at f=0.5 the recent-rate heuristic *beats* Hawkes (AUC 0.65 vs 0.60). No single
  split satisfies dLL(haw−cox)>0 & dLL(haw−recent)>0 & timing-p<0.05 & AUC_haw>AUC_cox together.

**Altitude implication (honest, for the committee — NOT a verdict):** the descriptive claim
**can** be lifted to an **operational early-warning** framing (self-excitation is predictive
OOS, ~8–11× early-warning lift, memory beats memoryless), but it **cannot** be lifted to
"parametric Hawkes has operational predictive superiority" — a one-line recent-rate window is a
sufficient/superior operationalization. CLAIM-0012's parametric content stays best supported as
**descriptive/in-sample** (BIC/LOSO per VERDICT-0049); the *operational* generalization is the
simpler heuristic, not the kernel. Legitimate honest mixed/partial terminal result; no
fabrication, no override sought. Engine effect=keep-exploring (claim weakened, not killed).

**Artifacts:** `experiments/2026-06-01/EXP-0047/{impl/predictive_oos.py, results/predictive_oos.{json,csv}, analysis.md}`;
write-up `projects/PROJ-0003/artifacts/CLAIM-0012_oos_predictive_altitude_lift_EXP-0047.md`.
