# PROJ-0001 — Orthogonal Seed Attempt: a METHODOLOGY/MEASUREMENT Contribution? — researcher-0001-seed2

**Date:** 2026-05-31 · **Agent:** researcher-0001-seed2 (orthogonal-direction seed lane, CPU/reading-only) ·
**Orchestrator session:** 22bd6bef-b84b-4827-a371-87443ea8602f
**Scope:** READ-ONLY. NO claims / verdicts / map edits / seeding / experiments. NO GPU / model CLIs / memory
probes (MI350X_CRASH_POSTMORTEM honored). NO binding to any promoted claim (BUG-25 honored). Wrote ONLY this
file, under prior_art/PROJ-0001/.

## Mandate (genuinely DIFFERENT direction)
6 prior lanes (laneB completeness, laneD adjacent-hunt, laneE synthesis, thesis, frontier 2-degree,
successor-scoping) all hunted in the **GPU-memory-systems SUBSTANCE** direction (VMM/CoW/ceiling/prefix-share/
KV-store scaling) and ALL early-killed every candidate via the **accounting-identity test + occupied-territory**.
This lane tries the ONE orthogonal direction not yet attempted: a **METHODOLOGY/MEASUREMENT** claim distilled
from *HOW* PROJ-0001 reached its negative result — analogous to PROJ-0003's M1-M11 measurement-methodology
paper (the durable survivor of a refuted-claims project). The candidate, as named in the brief:

> **"A reproducible protocol for falsifying HW-acceleration claims for agentic KV via the
> bytes-vs-bookkeeping + cross-vendor-ceiling + compound-collapse TRIAD"** — a measurement-methodology
> contribution analogous to PROJ-0003's M-catalog.

## TL;DR / VERDICT
**EARLY-KILL — OCCUPIED (canonical systems-benchmarking-methodology literature) + RESTATES the 5 claims +
fails the project's own accounting-identity bar.** This is the expected outcome (7th consecutive lane to kill).
The methodology angle is structurally weaker than PROJ-0003's because PROJ-0003's *primary thesis* was refuted
(forcing methodology to be the survivor), whereas PROJ-0001's *substance thesis is INTACT and strong* (5 GREEN
promoted claims, PUBLICATION_READINESS = GO) — so a methodology spin-out is not a forced survivor here, it is a
*second*, weaker paper that must clear a novelty bar it does not clear. **Do NOT seed. PROJ-0001 is complete on
its substance; the methodology is already (correctly) the implicit Methods section of the three-pillar paper,
not a separable contribution.**

## The proposed triad, stated precisely (so it can be honestly killed)
The "protocol" would package three measurement disciplines PROJ-0001 actually used:
- **T1 — bytes-vs-bookkeeping (the accounting-identity test):** before crediting a HW mechanism with a win,
  decompose the measured quantity into (i) the irreducible data bytes/FLOPs and (ii) the mechanism's
  bookkeeping; reject the claim if the "win" is an analytically-derivable restatement of the bytes (no
  non-derivable anomaly). This is literally the kill pattern laneB/D/frontier/successor applied 7×.
- **T2 — cross-vendor ceiling probe:** test the alleged HW capability on >=2 independent vendors; a wall on one
  and none on the other (NVIDIA ~520K vs AMD none, 153x) reframes a claimed "universal HW law" as a *vendor
  portability cliff* — falsifiable, not universal.
- **T3 — compound-collapse / end-to-end keystone:** never accept a per-op micro-benchmark in isolation; show the
  per-op deficit + the ceiling COMPOUND into an end-to-end throughput collapse under realistic load (the
  CLAIM-0003 keystone), because a mechanism can lose per-op and still be argued for until the compound is shown.

## Collision ledger (HEAVY early-kill)

### Gate 1 — does it RESTATE the 5 promoted claims? (the BUG-25 / DEAD-0003 mode)
**YES, largely.** T1 = the accounting-identity test that *is* the recurring kill heuristic already named in
laneD's cross-cutting observation and applied as CLAIM-0005/DEAD-0009/DEAD-0010. T2 = CLAIM-0002's own framing
("NVIDIA cliff, AMD none, 153x = a vendor portability cliff, not a GPU law") verbatim — it is the headline of a
GREEN claim, not a method abstracted above it. T3 = CLAIM-0003 (the compound throughput-collapse KEYSTONE)
restated as a "discipline." A protocol whose three steps are three of the five promoted claims with the nouns
swapped for verbs is the DEAD-0003 stapling failure ("A*+C* stapled, not a discovery"), one level up. **KILL.**

### Gate 2 — is the methodology OCCUPIED by the systems-benchmarking-methodology literature?
**YES, densely — by canonical and recent work, none in MAP-0001:**
| Method | Occupying prior art | Why it eats the triad |
|---|---|---|
| T1 bytes-vs-bookkeeping / analytical-model-as-baseline | **"Fair benchmarking considered difficult: Common pitfalls in DB performance testing"** (Raasveldt, Mühleisen et al., DBTest 2018) — canonical systems-benchmarking-pitfalls paper; **"Exploiting Simple Analytical Models for Modeling Hardware Accelerators"** (Altaf/Hill, UW-Madison PhD 2016 — analytical model AS the HW-accelerator baseline) | "Compare against an analytical/idealized model, not just a weaker system" and "decompose the measured number into its irreducible component" are textbook benchmarking discipline. The accounting-identity test is the well-known *roofline / analytical-bound* practice. NOT novel. |
| T2 cross-vendor ceiling / portability cliff | **Hoefler & Belli, "Scientific Benchmarking of Parallel Computing Systems" (SC15)** — the canonical 12-rule HPC benchmarking-methodology paper (report across systems, avoid single-platform universal claims); **"Benchmark scams" (EE Times/EDN)** — incl. the projected-vs-actual / cross-chip trap | "Test on >=2 independent platforms before claiming a universal HW law; a result on one vendor is platform-specific" is the FIRST principle of honest HW benchmarking. Cross-vendor falsification is decades-old standard practice, not a contribution. |
| T3 compound / end-to-end keystone | Hoefler-Belli (report end-to-end, not just kernel micro-benchmarks); the general "micro-benchmark ≠ application speedup / Amdahl" discipline | "Don't credit a micro-benchmark win without the end-to-end number" is Amdahl-101 + the oldest benchmarking caveat. NOT novel. |
| The overall "agentic / AI eval over-claims need a falsification protocol" framing | **"The Measurement Imbalance in Agentic AI Evaluation Undermines Industry Productivity Claims"** (arXiv:2506.02064, Stanford) — the agentic-eval-overclaiming methodology critique | The "industry HW/agentic claims are over-stated; here is the measurement discipline to falsify them" *meta-framing* is already a published 2025 thesis. A KV-specific instance does not clear it. |

### Gate 3 — collision vs PROJ-0003's M-catalog (the named analog)
**The analogy FAILS in the direction that matters.** PROJ-0003's M1-M11 survives because PROJ-0003's *primary
claims were REFUTED/deflated* (error-class does not predict recovery) — methodology is the **forced durable
survivor** of a negative project, and M1-M11 catch *non-obvious, agentic-recovery-SPECIFIC* lies (LOSO-vs-LOCO
leakage, double-log inflation, 3-way harness/model/error-text alias, one-cell-carried effects). Those are
**subtle, surprising, corpus-specific traps** — that is why they are publishable. PROJ-0001's triad, by
contrast, (a) is NOT a forced survivor (the substance thesis is INTACT + GREEN + GO), and (b) its three
"traps" are the *generic, well-known* HW-benchmarking caveats (analytical baseline, cross-platform, end-to-end),
NOT surprising domain-specific lies. So PROJ-0001 cannot reuse PROJ-0003's "methodology-is-the-survivor"
publishability argument — it has neither the necessity nor the non-obviousness. **KILL.**

### Gate 4 — the accounting-identity wall (the project's own 7×-applied test, applied to THIS candidate)
The triad's load-bearing content reduces to "apply known benchmarking discipline X to KV." There is no
non-derivable methodological anomaly: the protocol is a deterministic restatement of {analytical-baseline,
cross-platform, end-to-end} discipline specialized to one workload. By the project's own bar (a contribution
must produce a non-derivable anomaly, not a restatement of a known quantity/practice), the methodology angle
dies the *same* way the substance candidates did — one meta-level up. **KILL.**

## Cross-vendor characterization angle (the brief's alternative) — also killed
The brief offered "a cross-vendor characterization angle that isn't the (dead) AMD-ceiling re-probe." Any such
angle is (a) FORBIDDEN if it needs a mapping probe (MI350X_CRASH_POSTMORTEM — alloc AND teardown crashed the
node 3× incl a 4-5h HW repair), and (b) already OWNED by CLAIM-0002/0004 (the cross-vendor ceiling IS a promoted
claim) per laneD kills 1a/1b/1c. There is no cross-vendor characterization that is both non-forbidden and
not-already-a-claim. **KILL** (duplicate of laneD).

## Why even the orthogonal direction is closed (structural reason)
PROJ-0003's methodology paper is publishable *because its substance failed* — the discipline is the only
survivor and the traps are surprising. PROJ-0001's substance *succeeded* (5 GREEN, GO), so a methodology
spin-out is neither necessary nor non-obvious: the disciplines it would package are (i) three of the five
promoted claims restated, and (ii) otherwise canonical, decades-old systems-benchmarking practice (Raasveldt
DBTest'18, Hoefler-Belli SC15, "benchmark scams," analytical-model-as-baseline, the 2506.02064 agentic-eval
critique). The triad is correctly the *implicit Methods section* of the three-pillar indictment paper, NOT a
separable contribution. There is no fourth category beyond restatement / occupied-canonical / forbidden-probe.

## Conclusion
**EARLY-KILL the methodology/measurement seed. Do NOT seed.** The orthogonal METHODOLOGY direction — the one
genuinely-different lane not previously attempted — is ALSO closed: it restates 3 of the 5 promoted claims,
collides with canonical systems-benchmarking-methodology literature, fails the PROJ-0003-style "forced-survivor
+ non-obvious-trap" publishability test (PROJ-0001's substance is intact, so methodology is not a survivor), and
dies to the project's own accounting-identity bar one meta-level up. The cross-vendor alternative is forbidden
+ already a promoted claim (laneD duplicate). **PROJ-0001 is confirmed COMPLETE on its substance; the
methodology is the Methods section of the existing paper, not a second paper.** 7th consecutive lane to kill.

(No claims seeded. No verdicts. No map edits. No experiments registered. No binding to any promoted claim.
CPU/reading-only — no GPU/model CLIs/memory probes. Wrote ONLY prior_art/PROJ-0001/METHODOLOGY_ANGLE_seed2.md.)
