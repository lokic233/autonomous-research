# PROJ-0001 Paper-Track Synthesis + Cross-Claim Consistency Audit — researcher-0001-laneE

**Date:** 2026-05-31 · **Agent:** researcher-0001-laneE (paper-track synthesis lane, CPU-only) ·
**Orchestrator session:** 22bd6bef-b84b-4827-a371-87443ea8602f
**Scope:** READ-ONLY. No claim/verdict/map edits. Findings + recommendations only.
Distinct from laneB (completeness audit) and laneD (new adjacent-claim hunt): this lane =
mutual-consistency audit of the 5 promoted claims + unified-thesis synthesis + weakest-link.

## TL;DR
The 5 promoted claims (CLAIM-0001/0002/0003/0004/0007) compose into a clean, well-fenced
architectural-indictment thesis. They are MUTUALLY CONSISTENT in spirit. BUT a hostile reviewer
has exactly ONE high-value attack and I found it precisely:

> **WEAKEST LINK / EVIDENCE-CHAIN GAP (HIGH): CLAIM-0002 and CLAIM-0004 say the mapping ceiling
> is "PER-CONTEXT", but the load-bearing evidence (EXP-A004 e3d) proves it is PER-DEVICE
> (device-wide, conserved, split evenly across contexts). The original committee CONSENSUS
> explicitly headlined it as "conserved per-DEVICE budget". The word "per-context" in the current
> CLAIM-0002/0004 YAML directly contradicts the evidence that earned their GREEN.**

This is NOT a reason to doubt the science — the phenomenon is real and GREEN. It is a wording
defect introduced during the 2026-05-31 claim migration that, if it ships to a paper verbatim, a
systems reviewer will catch in 30 seconds and use to question the whole resource model. Flagged
for orchestrator (out of my lane to edit promoted claims).

---

## Part 1 — Unified-thesis synthesis (how the 5 claims compose)

Top-level thesis (project_overview): **"GPU CUDA-VMM is the wrong abstraction for agentic KV
branching."** The 5 promoted claims compose as a 3-pillar indictment + 1 honest concession:

```diagram
                 THESIS: CUDA-VMM is the wrong abstraction for agentic KV branching
                                              |
        +----------------------+--------------+-----------------+------------------+
        |                      |                                |                  |
   [CAPACITY]             [PERFORMANCE]                    [COMPOUND]         [CONCESSION]
   CLAIM-0002/0004        CLAIM-0001                       CLAIM-0003         CLAIM-0007
   Mapping ceiling/wall   CoW dominated                    Throughput         Write-after-share
   ~520K device budget    0/12 win-region                  collapse           bit-identical,
   vendor cliff (NVIDIA   1.06-2.20x slower than SW         HW 0/8 fanout,     kernel-transparent
   wall; AMD none, 153x)  41-152x slower than FlashInfer    crashes B>=128     (the ONE real
        |                      |                                |              HW capability delta)
        +----------------------+----------------+---------------+
                                                |
                            CLAIM-0003 is the KEYSTONE: it multiplies the
                            capacity wall (0002/0004) x the per-op slowdown (0001)
                            into an end-to-end collapse. It is the paper's headline.
```

**Compositional logic (the argument a paper makes):**
1. CLAIM-0002/0004 (capacity): VMM CoW *cannot scale branch fanout* on NVIDIA — a hard device-wide
   ~520K access-descriptor budget binds whenever you share a prefix via CoW; AMD has no such wall,
   so this is a *vendor portability cliff*, not a universal GPU law. (Honest, falsifiable, stronger.)
2. CLAIM-0001 (per-op cost): even *below* the ceiling, HW VMM CoW is *dominated* — never wins
   (0/12), 1.06-2.20x slower than software prefix-sharing, 41-152x slower than FlashInfer.
3. CLAIM-0003 (keystone): capacity wall x per-op slowdown *compound* into end-to-end throughput
   collapse — HW wins 0/8 fanout regimes, crashes at B>=128 (the ceiling biting in vivo), while
   software scales 280->800 tok/s. This unifies 1+2 into the indictment.
4. CLAIM-0007 (the honest concession that makes the paper credible): there IS exactly one thing HW
   CoW does that software prefix-sharing structurally cannot — an attention-visible, bit-identical
   (max_abs_diff=0.0), kernel-transparent write-after-share. The paper concedes this so the
   negative result reads as rigorous, not motivated. This is the rhetorical load-bearer:
   "we looked hard for a win and found only this narrow capability, which doesn't rescue VMM."

**Synthesis verdict:** the composition is sound and the claims are non-redundant — each occupies a
distinct axis (capacity / per-op speed / end-to-end / capability). CLAIM-0003 is correctly the
headline (MLSys). CLAIM-0007 is correctly the disarming concession. This is a publishable shape.

---

## Part 2 — Cross-claim consistency audit (5 promoted claims)

### CONSISTENCY-1 (HIGH, the weakest link) — "per-context" vs "per-device" contradiction
- **CLAIM-0002 YAML:** "The NVIDIA ~520K CUDA-VMM **per-context** mapping ceiling..."
- **CLAIM-0004 YAML:** "a conserved **per-context** VMM mapping budget governs branch fanout..."
- **Evidence (EXP-A004 e3d_results.jsonl):**
    `n_contexts=1 -> total 523404`; `n_contexts=2 -> total 523284` (260281+263003);
    `n_contexts=3 -> total 523164` (171633+174206+177325).
  The TOTAL is conserved at ~523,300 (+/-0.05%) and splits ~EVENLY (~K/n) across contexts. This is
  the textbook signature of a **per-DEVICE** budget shared across contexts, NOT a per-context one.
- **Original committee CONSENSUS.md (sess 048fcb0d) said exactly this:**
    "E3d (clean) shows the budget is CONSERVED and shared evenly... headline the **conserved-per-device**
    budget, fully retract 'super-linear'." The per-device framing is what earned the 6/6 GREEN.
- **So the current claim wording inverts its own winning evidence.** A reviewer who reads e3d (or
  the consensus) will see CLAIM-0002/0004 assert the opposite of what the data shows. The
  CROSSVENDOR_RESULT.md prior-art doc ALSO repeats "per-context mapping-metadata ceiling" (5x) and
  laneD/laneB both inherited the "per-context" phrasing — so the defect has propagated across the
  whole prior-art set.
- **Impact:** the *phenomenon* is GREEN and unchanged; only the *quantifier word* is wrong. But for
  a resource-model claim ("a conserved budget governs fanout"), getting per-context vs per-device
  wrong is the single most exploitable inconsistency in the whole project, because it changes the
  predicted concurrent-branch math (e.g. 2 contexts each get ~260K, not ~520K each).
- **RECOMMEND (orchestrator, do NOT let me edit promoted claims):** change "per-context" ->
  "per-device (device-wide, conserved, split evenly across contexts)" in CLAIM-0002 + CLAIM-0004,
  and in CROSSVENDOR_RESULT.md. This is a pure wording fix that ALIGNS the claim with the evidence
  and the original consensus; it strengthens, not weakens, the claim. No re-experiment needed
  (forbidden anyway per MI350X postmortem).

### CONSISTENCY-2 (MEDIUM) — the K-number discrepancy (519,936 vs 523,404) is still unreconciled
- EXP-A004 e3c uses `K=519,936`; EXP-A002/A004-e3a/A007-r1 assert a deterministic **523,404** at
  ~0% variance. CLAIM-0002 headlines "523,404 +/-0.6%".
- The original area-chair (CC48) flagged this EXACT discrepancy as a named GREEN-blocker:
  "Number inconsistency: E3c uses K=519,936 while E3a/E3b assert a deterministic 523,404 at 0.000%
  variance — reconcile or the 'hard constant' claim is dented."
- It is reconcilable (519,936 = 254 x 2046 or a rounded design constant for the e3c envelope table;
  523,404 = the measured fail count) but I find **no doc that actually reconciles them**. For a
  paper that headlines a "deterministic +/-0.6% hard constant", an unreconciled 0.66% gap between
  the cited constant and the table input is a soft target.
- **RECOMMEND (orchestrator/paper-track):** add one sentence reconciling 519,936 (envelope-model
  rounding) vs 523,404 (measured ceiling) wherever the constant is headlined.

### CONSISTENCY-3 (MEDIUM) — CLAIM-0001's FlashInfer "41-152x" is partly ANALYTIC, not measured
- EXP-A001 ec_rollback_e2e.csv: every `flashinfer` row is tagged
  `ANALYTIC: 48 paged-steps@~0.034ms + measured sw bookkeeping`. The HW-vs-SW arm IS measured
  end-to-end; the FlashInfer arm is an analytic projection (paged-step latency x steps + measured
  bookkeeping), not a real FlashInfer run.
- The claim text presents "41-152x slower than FlashInfer" with the same weight as the measured
  "1.06-2.20x slower than software". A hostile reviewer will demand the FlashInfer number be
  labeled analytic/projected, or be backed by a real FlashInfer run.
- This does NOT threaten the thesis (the *measured* 1.06-2.20x SW domination already proves "HW CoW
  dominated"; FlashInfer just widens the gap). But the claim should mark the FlashInfer multiple as
  analytic to survive review.
- **RECOMMEND (paper-track):** annotate CLAIM-0001 "41-152x slower than FlashInfer (analytic
  paged-step projection)" OR run one real FlashInfer cell. Note: GPU re-run is allowed here (this
  is NOT a mapping probe — no MI350X-postmortem risk), if a node is available; otherwise just label.

### CONSISTENCY-4 (LOW) — CLAIM-0003 "crashes for all B>=128" vs the B=16 transient in the data
- A003 et_tax_throughput.csv: the ceiling crash (`cuMemSetAccess`) first appears at B=128 and at
  every B>=128 (128/256/511/919/1124) — CONSISTENT with the claim.
- BUT the B=16 row is also marked `crashed=True` with `transient_cublas(1of3reps; NOT_ceiling)`.
  The data and notes correctly distinguish this transient cuBLAS failure from the ceiling crash, so
  the claim ("crashes for all B>=128") is technically accurate. The risk is only that a reader
  skimming the CSV sees a crashed=True at B=16 and thinks the B>=128 boundary is fuzzy.
- **RECOMMEND (paper-track):** in any table, split the `crashed` column into `ceiling_crash` vs
  `transient` so the B>=128 boundary reads cleanly. Cosmetic.

### CONSISTENCY-5 (consistent, no action) — AMD multiplier drift (96x / 123x / 153x)
- CROSSVENDOR_RESULT cites 96x (50M run, crashed), 123x (64M), 153x (80M safe run). The MEMORY note
  says "50M maps (96x)"; the current CLAIM-0002 YAML says "80M = 153x"; project_overview says "153x"
  in one place / the roster line is truncated.
- These are NOT contradictory: each is a different run's cap (the headline rightly uses the largest
  CLEAN, watchdog-safe run = 80M = 153x). The MEMORY.md "96x" is just an older run's number. So the
  claims are internally consistent; only MEMORY.md is stale (out of my lane; cosmetic).
- **No action needed for the claims.** (Note for orchestrator: project_overview.md roster line for
  CLAIM-0002 is truncated mid-word "porta" — cosmetic display issue only.)

### CONSISTENCY-6 (consistent) — CLAIM-0001 (0/12) vs CLAIM-0003 (0/8) vs DEAD-0003
- 0/12 (per-op win-region, EXP-A001) and 0/8 (fanout-regime win, EXP-A003) are DIFFERENT
  measurement grids, both reporting zero HW wins — mutually reinforcing, not contradictory.
- DEAD-0003 (unified VMM decision-procedure) was correctly killed *because* 0/12 makes the
  "when-to-use-VMM" TRUE-branch measure-zero. This is a consistent, well-reasoned fence: the project
  does NOT claim a decision procedure, it claims domination. Good.
- CLAIM-0007's capability delta does NOT contradict CLAIM-0001/0003: a bit-identical write-after-
  share is a *correctness/capability* property, orthogonal to the *performance* domination. The
  needs_attention.md vAttention boundary note keeps this sharp. Consistent.

---

## Part 3 — Prior-art / MAP-0001 completeness for the 5 promoted claims (Rule-3)

I re-checked completeness specifically for the 5 PROMOTED claims (laneB covered the broader map):

| Check | Status |
|---|---|
| All 5 promoted claims appear in MAP-0001.associated_claims | OK (0001/0002/0003/0004/0007 all present; 0005 dangling per laneB-D1, but 0005 is weakened not promoted) |
| Each promoted claim has supporting_evidence with a real artifacts path | OK (A001/A002/A003/A004/A007 all exist with data files) |
| related_work.md covers the perf + capacity baselines | OK (vAttention/PagedAttention/RadixAttention/FlashInfer/Continuum) |
| vAttention boundary (read-only VMM-KV vs our fork/CoW) | OK and explicitly fenced (needs_attention #1) |
| Cross-vendor evidence intact + caveated | OK (CROSSVENDOR_RESULT.md; re-probe caveat in needs_attention #2; re-probe is FORBIDDEN per postmortem, so caveat should be reworded to "driver-version-scoped claim" not "re-probe before paper-track") |
| **NEW completeness GAP (this lane):** per-context/per-device wording defect propagated into prior-art (CROSSVENDOR_RESULT.md) AND both claims | **DEFECT — CONSISTENCY-1 above** |
| **NEW completeness GAP:** K=519,936 vs 523,404 never reconciled in any doc | **DEFECT — CONSISTENCY-2 above** |
| **Stale:** needs_attention #2 says "re-probe before paper-track" but re-probing AMD/NVIDIA mapping ceiling is FORBIDDEN (MI350X postmortem). The recheck path it prescribes is unsafe. | should be reworded to a driver-version-scoped claim, not a re-run instruction |

MAP-0001 red_zones DO correctly fence the dead-ends adjacent to the promoted claims (HW VMM CoW
DEAD via 0001/0003; isolation DEAD-0001; attestation DEAD-0002; super-linear DEAD-0004; etc.).
laneB's D3/D4 map-hygiene items appear already applied (DEAD-0004/0007 red_zones now present;
needs_attention D4 stale-item correction appended). No NEW missing red_zone for the 5 promoted.

---

## Part 4 — The single weakest link (answer to the brief)

**The single weakest link in the thesis chain is the capacity pillar's RESOURCE MODEL (CLAIM-0002 +
CLAIM-0004), specifically the "per-context" wording that contradicts the per-device evidence
(CONSISTENCY-1), compounded by the unreconciled K-constant (CONSISTENCY-2).**

Why this and not, say, CLAIM-0001's analytic FlashInfer number:
- CLAIM-0003 (the keystone/headline) DEPENDS on the capacity pillar being a correctly-characterized
  hard wall. If a reviewer destabilizes "what exactly is conserved, and is it per-context or
  per-device, and is K 519,936 or 523,404", they destabilize the *mechanism* behind the headline
  collapse — the most damaging place to land a hit.
- CLAIM-0001's analytic-FlashInfer issue (CONSISTENCY-3) is real but self-healing: the *measured*
  SW domination already carries the "dominated" claim; FlashInfer is a bonus multiplier.
- The capacity-model wording is the only place where a current claim asserts something its own
  load-bearing data contradicts. That is the textbook reviewer kill-shot. It is ALSO the cheapest to
  fix (one word, no experiment), which is why it is worth flagging precisely now, pre-paper.

---

## Files / paths referenced
- Claims: registry/claims/PROJ-0001/2026-05-31/CLAIM-{0001,0002,0003,0004,0007}.yaml
- Evidence: experiments/2026-05-30/EXP-A004/experiment_result/e3d_results.jsonl (per-device proof),
  e3c_result.json (K=519,936), EXP-A001/.../ec_rollback_e2e.csv (FlashInfer ANALYTIC tag),
  EXP-A003/.../et_tax_throughput.csv (B=128 ceiling boundary + B=16 transient)
- Original consensus: sessions/5_30_2026/048fcb0d-abd5-4c19-bb73-a0a7ca4ff0ec/committee_traces/CONSENSUS.md
  ("conserved-per-device budget"); votes/d_CC48.txt (K-number + per-device flags)
- Prior-art: prior_art/PROJ-0001/511ce2e2__CROSSVENDOR_RESULT.md, needs_attention.md
- Postmortem: learning/MI350X_CRASH_POSTMORTEM.md (mapping re-probes FORBIDDEN)

## Recommendations to orchestrator (I did NOT edit any claim/verdict/map — out of lane)
1. **[HIGH]** CLAIM-0002 + CLAIM-0004: replace "per-context" -> "per-device (conserved, split evenly
   across contexts)". Aligns claim with EXP-A004 e3d + original consensus. STRENGTHENS the claim.
   Also fix CROSSVENDOR_RESULT.md (5 occurrences).
2. **[MED]** Reconcile K=519,936 (envelope-model) vs 523,404 (measured) with one sentence wherever
   the constant is headlined.
3. **[MED]** Label CLAIM-0001's "41-152x slower than FlashInfer" as analytic/projected, or run one
   real FlashInfer cell (GPU-safe; NOT a mapping probe).
4. **[LOW]** needs_attention #2: reword "re-probe before paper-track" to a driver-version-scoped
   claim ("scoped to CUDA 12.8 / 580.82.07") — re-probing is FORBIDDEN per MI350X postmortem.
5. **[LOW/cosmetic]** CLAIM-0003 table: split crashed -> ceiling_crash vs transient. MEMORY.md "96x"
   stale vs claim's 153x (not project-scope).

(No claims seeded. No verdicts. No map edits. No GPU/model CLIs. CPU-only. Wrote ONLY
prior_art/PROJ-0001/PAPER_SYNTHESIS_laneE.md.)
