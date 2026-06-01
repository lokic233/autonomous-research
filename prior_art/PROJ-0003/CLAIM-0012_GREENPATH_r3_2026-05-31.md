# CLAIM-0012 GREEN-PATH SYNTHESIS — researcher-0012-green-r3

**Date:** 2026-05-31 (PDT node; 2026-06-01 UTC) · **Agent:** researcher-0012-green-r3 · **CPU/stdlib-only, READ + local-Python**
**Mandate:** execute the CPU statistical GREEN-path for CLAIM-0012 (burstiness / failure-clustering) against VERDICT-0046 (6/6 YELLOW).
**Scope discipline:** re-analyzed EXISTING logged trace data (`~/.claude/projects`, `~/.codex/sessions`, `~/.gemini`). No GPU, no new experiments, no map/claim/verdict edits, no fabricated data.
**Artifacts:** `experiments/2026-06-01/EXP-0043/{impl/bm_plane_and_label_audit.py, results/*.csv, results/greenpath_r3.json, logs/run.log}`; independent re-run of `EXP-0042/impl/robust_L4.py` (reproduced exactly).

---

## TL;DR HONEST VERDICT: **STILL YELLOW — but a defensible, narrowed 2-harness GREEN-able core.**

The over-dispersion phenomenon is **REAL and 3-harness robust**. The *interesting* version of the claim (self-exciting failure cascades beyond rate-heterogeneity) is **2-harness (Codex + Gemini-with-caveats)**, with **CC fragile** (EXP-0040 failure mode) and a **newly-surfaced label-composition problem on Gemini** that the committee had not quantified. The over-dispersion does **NOT fully resolve to committee-GREEN at the altitude originally claimed.** Recommend reframe + downgrade of the discriminating claim to 1.5–2 harnesses. Details below, test by test.

---

## 1. LIVE PRIOR-ART SWEEP (BLOCKING gap — web was unavailable to the committee). **Status: CLOSED. Novelty SURVIVES; altitude bar RAISED.**

Web is available on this node; I ran the live sweep the committee could not. Findings:

**The novelty is intact — no published work reports the burstiness coefficient of tool-call failures in real agent traces.** Closest neighbors, all distinct:
- **"Where LLM Agents Fail and How They Learn From Failures"** (2509.25370, ICLR'26 under review), **"How Do LLMs Fail in Agentic Scenarios"** (KAMI, 2512.07497), **AgentProp-Bench** (2604.16706, "propagation cascades"), **ag2ai Agents_Failure_Attribution** (ICML'25 spotlight, 2505.00212): all **taxonomic / qualitative / attribution** — none measure the **temporal arrival over-dispersion** of tool-call failures.
- **"From Spark to Fire: Modeling Error Cascades in LLM Multi-Agent"** (2603.04474): models error *cascades* but in **multi-agent message passing**, not the within-session tool-call arrival statistic on real single-agent traces.
- **"Time-To-Inconsistency: Survival Analysis of LLM Robustness"** (2510.02712): survival analysis of adversarial multi-turn dialogue, not tool-call failure arrival.

**The bar the sweep RAISES (the committee was right):**
- **Barabási 2005** (Nature 435:207) + **Goh & Barabási 2008** (burstiness B & memory M) + **Karsai & Jo 2025** (Handbook review, 2412.13617): burstiness is **near-universal** in human/natural dynamics → the correct null is **NOT Poisson**, it is "bursty like everything else." Pooled-Poisson rejection alone is low-altitude.
- **arXiv 2604.15084 "Static heterogeneity generates apparent universality in first-passage bursty dynamics"** — **the single most dangerous hostile-reviewer citation.** It shows that *static rate-heterogeneity alone* manufactures apparent power-law/bursty inter-event statistics **without any temporal memory.** This is *exactly* the Cox-mixture alternative. CLAIM-0012's defense against it is the **tool-stratified permutation** (EXP-0041) + **Cox-vs-Hawkes BIC** (EXP-0042) — which is why those tests are load-bearing, and why CC failing them matters.
- **SRE/incident baselines exist and are heavy-tailed/self-exciting:** power-system outage inter-arrivals fit Pareto (2303.12714; Maynooth thesis 2018); cyber-attack & cyber-risk arrivals fit **Hawkes self-excitation** (2311.15701, hal-05108348); Google SRE "cascading failures" (positive-feedback) is the qualitative analog. So the agent finding is **citing into a real, occupied comparative literature** — it must be *placed* against it, not announced as novel clustering.

**Net:** novelty (the *estimand* — agent tool-call failure burstiness) is genuinely open; but the **contribution altitude** is gated on showing the agent process is **more than universal-burstiness + static heterogeneity** — i.e. on the discriminating tests, which is where it gets fragile (§4).

---

## 2. CC-LEG ROBUSTNESS: per-session strat-Z distribution + size-weighted Stouffer + LOSO. **Status: RE-VERIFIED (EXP-0042). CC discriminating leg is FRAGILE.**

I independently re-ran `EXP-0042/impl/robust_L4.py` — **reproduces exactly.**
- Per-session tool-stratified Z (CC, 19 shufflable sessions): **median = 0.0**, 12/19 sessions sit at z_strat ≈ 0 (no within-tool clustering). Only 3 sessions meaningfully negative. **This is structurally the EXP-0040 failure mode the project already killed** (a per-session-null result resurrected by aggregation).
- Unweighted Stouffer = **−2.33 (p=0.0098)**; **size-weighted = −6.59** but this is an **artifact** — √n weighting up-weights the single 862-call session (w=29) ~4–9× over all others.
- **LOSO kill test:** dropping that one 862-call session → unweighted Stouffer **−0.89 (p≈0.19, NON-significant).** The CC rate-stratified signal does not survive removal of one session.

**Read:** CC's *whole-session* over-dispersion is robust (survives Bonferroni). CC's *rate-stratified* (discriminating) signal is **aggregation-carried / fragile** — fails the project's own evidentiary standard.

---

## 3. (B,M)-PLANE vs SRE + HUMAN BASELINES (HIGH gap — NOT previously done). **Status: NEW. Placement is SUGGESTIVE but UNDERPOWERED on the memory axis.**

Computed Goh-Barabási burstiness B (finite-size-corrected, Kim & Jo 2016) and lag-1 memory M on pooled inter-failure call-gaps, with 2000-sample bootstrap CIs (`results/bm_plane.csv`):

| system | B_corr [95% CI] | M_lag1 [95% CI] | placement |
|---|---|---|---|
| **Claude Code (agent)** | **0.429 [0.216, 0.533]** | 0.179 **[−0.128, 0.207]** | B>0 clean; M crosses 0 |
| **Codex (agent)** | **0.276 [0.126, 0.382]** | 0.228 **[−0.211, 0.275]** | B>0 clean; M crosses 0 |
| **Gemini (agent)** | 0.214 **[−0.367, 0.336]** | 0.071 [−0.192, 0.311] | B crosses 0; M crosses 0 |
| Poisson null (theory) | 0.0 | 0.0 | random |
| human email (Barabási 05) | ~0.6 | ~0.0 | heavy-tail, **NO memory** |
| human library loans | ~0.3 | ~0.07 | weak memory |
| earthquakes (aftershock) | ~0.18 | ~0.10 | **B>0 AND M>0 (cascade)** |
| SRE/datacenter outages | >0 (Pareto) | >0 (Hawkes-fit) | self-exciting cluster |
| heartbeats | ~−0.7 | ~0.0 | anti-bursty |

**The intended story (and where it holds):** the agents' *point estimates* land in the **earthquake/SRE cascade quadrant (B>0 AND M>0)** — distinct from the human-email region (B>0, M≈0, heavy-tail-without-memory). That positive-M placement is the qualitative discriminator that says "agent failures look like self-exciting cascades, not just heavy-tailed waiting times."

**The honest weakening:** the **bootstrap M-CI crosses 0 for ALL THREE harnesses** (CC [−0.13,0.21], Codex [−0.21,0.28], Gemini [−0.19,0.31]). On the lag-1-M axis alone, the agent placement is **NOT statistically separable from the memoryless human-email region.** B_corr is clean >0 only for CC and Codex; Gemini's B_corr crosses 0 (42 gaps, underpowered — consistent with EXP-0038). So the (B,M)-plane **point estimates** support the cascade-region story, but the **CIs do not let you defend the memory axis from the (B,M)-plane statistic alone.** The defensible memory evidence is the **Hawkes ΔBIC (§4), not the lag-1 M.** (Note: anchor coordinates for human/SRE systems are LITERATURE-CITED published values, not re-measured on-node — flagged, not fabricated; re-measuring an SRE incident dataset would require a datum not logged here.)

---

## 4. COX-vs-HAWKES BIC (HIGH gap). **Status: RE-VERIFIED (EXP-0042). Hawkes WINS on all 3 — the strongest positive result.**

Independently reproduced. Model: failure arrivals over call-index; Cox = per-tool baseline rate (pure rate-heterogeneity, the 2604.15084 alternative); Cox+Hawkes adds a 2-param self-excitation kernel α·Σexp(−β·Δ).

| harness | Cox BIC | Hawkes BIC | α | β | **ΔBIC (Cox−Hawkes)** |
|---|---|---|---|---|---|
| claude_code | 750.10 | 740.35 | 1.25 | 0.45 | **+9.74** |
| codex | 739.10 | 712.25 | 4.30 | 1.20 | **+26.85** |
| gemini | 199.02 | 185.26 | 3.55 | 1.15 | **+13.76** |

All ΔBIC > 6 ("strong") with α > 0 → **genuine self-excitation beyond rate-heterogeneity, quantified on all 3.** This is the cleanest answer to "is it really self-exciting clustering" and resolves the committee's "'both contribute' asserted not quantified." **Caveat (consistent with §2):** CC's α=1.25 is the weakest, and the CC win is a *pooled-corpus* fit — per §2 the CC clustering lives in a few long sessions, so CC's Hawkes win does not generalize per-session. **Honest:** Codex+Gemini Hawkes wins are corpus-broad; CC's is pooled-fit-only.

---

## 5. LABEL AUDIT + BONFERRONI (MED gap). **Status: NEW audit + RE-VERIFIED Bonferroni. Labels are CLEAN of leakage, but Gemini has a TRIVIALITY problem the committee did not catch.**

**Bonferroni/Holm (re-verified, m=9 family):** CC tool-strat is the **only** test failing Bonferroni (0.0086 → 0.078). It "passes" Holm only **artifactually** (rank 9/9, multiplier decayed to 1 because every other test is strong). Codex 3/3 and Gemini 3/3 survive both corrections decisively. → **The discriminating CC claim does not survive multiple-comparison correction.**

**Label audit (NEW — 285 samples emitted to `results/label_audit_samples.csv` for human review):**
- **No leakage / no mislabeling of the labeling MECHANISM:** CC uses harness-native `is_error` (0% regex), Gemini uses native `status==error` (0% regex), Codex is 99% non-zero-exit-code (hard signal), only **1/105** rests on the substring heuristic. The committee's "heuristic-label" MED concern is **largely defused** — labels are harness-emitted, not invented.
- **BUT a label-COMPOSITION problem surfaces that materially affects altitude:**
  - **CC failures:** 48/146 (33%) are `permission_gate` ("haven't granted permission"), 5 web-gate, 17 file-notfound, ~74 genuine exec. A third of CC "failures" are deterministic permission denials that cluster by construction.
  - **Gemini failures (the alarming one):** **30/60 (50%) are `schema_argerror`** (malformed args, e.g. missing `file_path`), **20/60 (33%) are `path_gate`** (path-not-in-workspace), 9 file-notfound, and **only 1/60 is a genuine exec error.** Gemini's "burstiness" is **~98% an artifact of the agent repeatedly emitting malformed / out-of-workspace tool calls** — these cluster trivially. This is a *lower-altitude* phenomenon than "self-exciting failure cascade."
- **Mitigant:** retry-collapse@Jaccard0.6 removes only 0.42% (CC) / 0.67% (Codex) of calls → back-to-back *identical* retries are rare, so the CC/Codex clustering is NOT a trivial verbatim-retry storm. Gemini removes 6.4% (more retries) yet strengthens — consistent with its clustering being malformed-call repetition with varying args.

**Honest read:** labels are sound (no leakage), but **Gemini's leg is carried by trivial malformed-call clustering**, and a third of CC's failures are policy gates. The *cleanest* leg on failure-semantics grounds is **Codex** (heterogeneous genuine exec failures: code 127 `command not found`, code 28 search, code 1).

---

## 6. WHAT STRENGTHENS vs WHAT WEAKENS THE CLAIM

| Evidence | Direction | Note |
|---|---|---|
| Live prior-art sweep: estimand genuinely open | **strengthens** (novelty) | but raises the altitude bar (universal-burstiness + 2604.15084 static-heterogeneity null) |
| Whole-session over-dispersion, 3 harnesses, survives Bonferroni | **strengthens** | the robust core |
| Cox-vs-Hawkes ΔBIC > 6, α>0, all 3 | **strengthens** (strongest) | genuine self-excitation; CC pooled-only |
| (B,M) point estimates in cascade quadrant | weakly strengthens | M-CI crosses 0 all 3 → can't defend memory axis from B,M alone |
| CC per-session strat-Z median=0, LOSO collapse, fails Bonferroni | **WEAKENS** | EXP-0040 failure mode; CC discriminating leg fragile |
| Gemini failures 98% malformed-call/path-gate artifacts | **WEAKENS** | Gemini discriminating leg is low-altitude triviality |
| Labels harness-native, ~0% heuristic | neutral/strengthens | defuses the leakage concern |

---

## 7. COMMITTEE-READINESS DETERMINATION

**Over-dispersion (whole-session, vs Bernoulli/Poisson null):** **3-harness robust, survives Bonferroni.** GREEN-able *as a descriptive statistic* — BUT against the universal-burstiness null (Barabási 2005) this alone is low-altitude ("agents are bursty like everything else").

**The DISCRIMINATING claim (self-excitation beyond static rate-heterogeneity — the only version that clears the 2604.15084 / universal-burstiness bar):**
- **Codex: GREEN-grade.** tool-strat survives Bonferroni at ~0; Hawkes ΔBIC +26.9; broad per-session signal; cleanest failure semantics.
- **Gemini: YELLOW.** Hawkes ΔBIC +13.8 and tool-strat survive Bonferroni — but the failure population is ~98% trivial malformed-call/path artifacts, so the *altitude* of what's clustering is low.
- **Claude Code: weakened toward RED on the discriminating leg.** Per-session strat median=0, LOSO-collapses to ns, fails Bonferroni — the EXP-0040 killed mode. CC's *whole-session* over-dispersion survives; its *rate-stratified self-excitation* does not generalize.

**OVERALL: STILL YELLOW.** The phenomenon is real; the honest, defensible contribution is **narrower than the headline 3-harness self-exciting-burstiness claim.** It does **not** cleanly resolve to committee-GREEN at the originally-claimed altitude. The over-dispersion **partially resolves** (3-harness descriptive over-dispersion is solid) but the **discriminating self-excitation does NOT resolve to 3-harness GREEN** — it is **1 clean harness (Codex) + 1 fragile (CC) + 1 trivial-population (Gemini).**

**Recommended reframe (defensible, NOT forced GREEN):**
> *"Tool-call failures in real agent traces are temporally over-dispersed (3-harness, survives Bonferroni & a within-session permutation null). On Codex — the harness with the cleanest genuine-exec failure semantics — the over-dispersion exceeds what static per-tool rate-heterogeneity explains (tool-stratified permutation + Cox-vs-Hawkes ΔBIC=+26.9, α>0), placing agent failures in the self-exciting / cascade region of the Goh-Barabási (B,M) plane alongside SRE incident and aftershock processes rather than the memoryless heavy-tailed human-email regime. The self-excitation component is fragile on Claude Code (aggregation-carried, LOSO-sensitive, fails Bonferroni) and carried by trivial malformed-call clustering on Gemini — so the discriminating result is reported as 1 strong + 2 caveated harnesses, not a uniform 3-harness law."*

This keeps the project's evidentiary honesty (does not paper over the CC EXP-0040 mode or the Gemini label-composition problem) while preserving the genuinely-strong Codex + Hawkes-BIC core.

---

## 8. FLAGGED DATA GAPS (not logged on-node; would be needed to fully close)
- **No on-node SRE/incident inter-arrival dataset** → (B,M) anchors for SRE/human systems are literature-cited published values, not re-measured. A re-measured comparison would need an external incident dataset (e.g. a public outage/incident log) imported — **flag for orchestrator**, not fabricatable here.
- **No human-operator baseline trace** (e.g. a human's own shell-command failure stream) logged → the "human baseline" leg of the (B,M) comparison is anchored to literature only.
- Gemini corpus is thin (10–11 sessions, 42 gaps) and 98% trivial-failure-population → a larger, genuine-exec-failure Gemini corpus would be needed to upgrade its leg.

## 9. FILES
- `prior_art/PROJ-0003/CLAIM-0012_GREENPATH_r3_2026-05-31.md` (this doc)
- `experiments/2026-06-01/EXP-0043/impl/bm_plane_and_label_audit.py`
- `experiments/2026-06-01/EXP-0043/results/{bm_plane.csv, label_audit_samples.csv, greenpath_r3.json}`
- `experiments/2026-06-01/EXP-0043/logs/run.log`
- Re-verified (reproduced exactly): `experiments/2026-05-31/EXP-0042/impl/robust_L4.py` + its `results/*.csv`
