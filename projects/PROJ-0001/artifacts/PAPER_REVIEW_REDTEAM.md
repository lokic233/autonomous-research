# PROJ-0001 — Adversarial Self-Review (Hostile MLSys/ATC Reviewer Pass)

**Date:** 2026-05-31 · **Agent:** researcher-0001-review (final red-team lane, CPU-only) ·
**Orchestrator session:** 22bd6bef-b84b-4827-a371-87443ea8602f
**Scope:** READ-ONLY. NO claim/verdict/map edits, NO experiments, NO GPU/model CLIs/mapping re-probes
(FORBIDDEN per MI350X postmortem). This is the last quality gate before the paper is submission-ready.
**Object reviewed:** `prior_art/PROJ-0001/PAPER_DRAFT.md` (30,002 bytes, 8 sections + abstract + 2 appendices).
**Cross-checked against:** the 5 promoted claims (CLAIM-0001/0002/0003/0004/0007 incl writeup_notes +
evidence_corrections), EXP result files (A001/A002/A003/A004/A007), PAPER_HARDENING_2026-05-31.md,
PAPER_SYNTHESIS_laneE.md, PUBLICATION_READINESS.md, PAPER_OUTLINE.md, CROSSVENDOR_RESULT.md.

---

## VERDICT: GO — SUBMISSION-READY. No blocking defect. Punch-list is empty (only 2 optional polish items).

I red-teamed the draft as a hostile MLSys/ATC PC member trying to find a rejection. **Every attack I
could mount is already pre-empted in the draft prose itself.** Every quantitative number traces to a
cited EXP result file and matches the source byte-for-byte. No over-claim, no slope law, no "CDC always
wins", no re-probe instruction. The negative result is framed as a contribution, not a non-result.

---

## 1. EVERY ATTACKABLE CLAIM + WHETHER THE DRAFT ALREADY DEFENDS IT

| # | Reviewer attack | Where in draft | Defended? | Defense |
|---|---|---|---|---|
| A1 | "Your ceiling is per-CONTEXT, so concurrent contexts each get 520K — your keystone collapse is wrong." | §3.2 | **YES (strongest defense)** | §3.2 gives the e3d conservation table (n=1:523,404; n=2:260,281+263,003=523,284; n=3 sums to 523,164), total conserved ±0.05%, splits ~K/n. Explicitly calls out the earlier per-context wording as "a wording defect that inverted this evidence" and aligns to CLAIM-0002/0004 evidence_corrections. This is THE per-device fix, fully landed. |
| A2 | "Two different ceilings (523,404 vs 519,936) — you don't even know your own number." | §3.3 | **YES** | §3.3 reconciles: 523,404 = pure single-reservation alias ceiling (measured, headlined); 519,936 = median realized B×P (model input to e3c only). Spread 522,752@1GiB→516,096@12GiB brackets the ceiling; ~0.66% gap predicted by reservation-overhead model. Matches HARDENING ITEM 1 verbatim. K-reconciliation landed. |
| A3 | "Your 41-152x FlashInfer gap is fake — you never ran FlashInfer." | §4.3 + Appendix B | **YES** | §4.3 labels it explicitly "analytic paged-step projection, not a measured FlashInfer run", presents it as a BONUS widening multiplier, and states the MEASURED 1.06-2.20x SW domination carries the thesis alone (self-healing: both arms measured). FlashInfer-analytic label landed. |
| A4 | "B=16 crashed too, so your 'B>=128 boundary' is fuzzy / cherry-picked." | §5.1 table | **YES** | §5.1 splits crash class: B=16 = `transient_cublas(1of3reps;NOT_ceiling)` (2/3 reps OK), B=64 clean, ceiling crash (`cuMemSetAccess`) at EVERY B>=128. Ceiling-crash vs transient split landed; matches CSV row-for-row. |
| A5 | "It's a single-driver quirk, not a real limit — unfalsifiable." | §3.4 | **YES** | Cross-vendor: NVIDIA hard wall ~520K vs AMD MI350X no wall to 80M (153x), 3 independent AMD scales (4M/50M/80M). Draft argues this is STRONGER/more falsifiable than a "universal GPU law" because it measured the divergence. Correct posture. |
| A6 | "Will this survive the next driver version?" | §3.4 threat-to-validity | **YES** | Scoped to CUDA 12.8 / driver 580.82.07 / 2 MiB granule, stated as an explicit threat-to-validity, NOT a permanence claim. Notes re-probing is hazardous (host-node destabilization) — fences it as a limitation, NOT a re-run instruction. |
| A7 | "0/12 (A001) and 0/8 (A003) are the same experiment double-counted." | §5.3 | **YES** | §5.3: different measurement grids (per-op rollback grid vs end-to-end fanout sweep), both reporting zero HW wins — "mutually reinforcing, not redundant." |
| A8 | "You're motivated — you only looked for HW losses." | §6 (Concession) | **YES** | The write-after-share concession (max_abs_diff=0.0, kernel-transparent) is the rhetorical load-bearer: "we searched for a hardware advantage, found exactly this one narrow capability, and report that it does not redeem the abstraction." Disarms the motivated-reasoning charge. |
| A9 | "vAttention already did CUDA-VMM-for-KV — what's new?" | §2.3 + §7 | **YES** | Fenced sharply: vAttention = read-only contiguous-VA KV, NO fork/CoW branching, never enters the per-device access-descriptor budget regime. Stated in abstract positioning, §2.3, AND §7 as "the single most important boundary." |
| A10 | "RadixAttention / PagedAttention already own prefix sharing." | §2.2 + §7 | **YES** | Software prefix-sharing is explicitly the BASELINE THAT WINS (0/12, 0/8), not a contribution. RadixAttention token-prefix=KV sharing fenced as DEAD-0006. |
| A11 | "2026 KV-sharing wave (ForkKV/TokenDance/etc.) scoops you." | §7 | **YES** | All 11 forward neighbors characterized as software-side / read-only / multi-agent — none is HW-VMM-CoW, so none is a must-cite collision; cited as forward-frontier occupancy. |
| A12 | "Your concession undermines your own negative result." | §6 Rhetorical role | **YES** | Explicitly orthogonal: a correctness/capability property, NOT performance; does not rescue VMM on capacity (I) or perf (II/III). Logically airtight — no contradiction with the domination claims. |

**Result: 12/12 attackable claims are pre-defended in the draft prose.** All four writeup_notes
hardening items (per-device fix, K-reconciliation, FlashInfer-analytic label, ceiling/transient split)
are folded into the prose, not just sitting in the claim YAMLs.

---

## 2. NUMBER TRACEABILITY — every quantitative claim verified against a cited EXP result file

I independently re-read the source files (not just Appendix B) and confirmed each headline number:

| Draft number | Source file (verified this pass) | Match |
|---|---|---|
| 523,404 ceiling, charged at `cuMemSetAccess` | `EXP-A007/.../r1.json` → `mappings_before_fail: 523404, va_reserves: 1, oom_call: cuMemSetAccess` | EXACT |
| n=1:523,404 / n=2:260,281+263,003=523,284 / n=3:171,633+174,206+177,325=523,164 | `EXP-A004/.../e3d_results.jsonl` (lines 1-3) — read directly, all six per-context values match | EXACT |
| K_CEILING = 523404 (throughput experiment input) | `EXP-A003/impl/bench_ET_tax_throughput.py:64` → `K_CEILING = 523404` | EXACT |
| 519,936 model input; spread 522,752@1GiB→516,096@12GiB | `EXP-A004/impl/e3c_relevance.py` + HARDENING ITEM 1 | EXACT |
| 0/12, 4 arms (hw_vmm_cow / hw_vmm_cow_fullfwd / sw_prefix / flashinfer) | `EXP-A001/.../ec_rollback_e2e.csv`: arm counts 24 hw_vmm_cow (2 hw arms × 12) + 12 sw_prefix + 12 flashinfer | EXACT |
| 1.06-2.20x (1.056-2.195) SW domination; 41-152x (41.3-151.5) FlashInfer ANALYTIC | `EXP-A001/.../ec_rollback_e2e.csv` notes column; recomputed in HARDENING ITEM 2 | EXACT |
| HW crash table B=4 clean / B=16 transient_cublas / B=64 clean / B=128,256,511,919,1124 cuMemSetAccess ceiling | `EXP-A003/.../et_tax_throughput.csv` hw rows — read directly, every B + crash_call matches the draft table | EXACT (incl. the odd `cuMemSetAccess_ceiling(illegal_access)@B~171` at B=919) |
| SW 280.5→799.79 tok/s, 0 crashes | `EXP-A003/.../et_tax_throughput.csv` sw rows: B=4→280.5 (min), B=919→799.79 (max), all crashed=False | EXACT |
| max_abs_diff = 0.0, kernel-transparent, bit-identical | `EXP-A007/.../e1b_result.json` → `max_abs_diff_vs_clone: 0.0, sdpa_output_bit_identical_to_full_clone: true` | EXACT |
| AMD 80M no wall = 153x; 4M/50M/80M runs; 4KiB vs 2MiB = 512x granule | `511ce2e2__CROSSVENDOR_RESULT.md` (scales 4M/50M/80M confirmed; granule 4096B "512× finer than 2 MiB") | EXACT |

**UNTRACED NUMBERS: NONE.** Every quantitative figure in the draft (abstract, §3-§6, both appendices)
maps to a cited EXP result file and matches the source. The prior-prose lane's traceability finding
holds for the draft AS WRITTEN. (Note: MEMORY.md's older "96x" AMD figure does NOT appear in the draft —
the draft correctly headlines the largest clean watchdog-safe run, 80M = 153x. No leak of the stale number.)

---

## 3. STRONGEST REVIEWER REJECTION ARGUMENT + REBUTTAL STATUS

**Strongest single attack (the one a hostile PC member leads with):**
> "The keystone (Pillar III, CLAIM-0003) is a throughput-collapse claim resting on a PER-DEVICE mapping
> ceiling. If that budget were actually per-context — i.e. each concurrent branching context got its own
> ~520K — then under realistic multi-context serving the wall would NOT bind at B>=128, the 0/8 collapse
> would be an artifact of a single-context micro-benchmark, and the keystone evaporates. The entire MLSys
> contribution hinges on the per-device quantifier being correct."

**Rebuttal status: FULLY PRESENT and load-bearing (§3.2).** The draft's §3.2 is built precisely to kill
this attack: the e3d conservation table shows the total budget is conserved at ~523,300 (±0.05%) and
splits ~K/n across concurrent contexts (n=2 → ~260K each, NOT ~520K each; n=3 → ~174K each). This is
direct measured evidence that the budget is one device-wide pool, not a per-context allotment — exactly
the regime under which the keystone collapse binds harder, not softer, as contexts multiply. The draft
also explicitly flags and retracts the earlier "per-context" wording as an evidence-inverting defect.
**The rebuttal is the strongest part of the paper, not a gap.** No fix needed.

(Secondary strongest attack — "FlashInfer 41-152x is fabricated" — is also fully rebutted: §4.3 labels
it analytic and demotes it to a bonus multiplier, with the measured 1.06-2.20x SW domination carrying
the thesis alone. Not load-bearing, so even a full concession of the FlashInfer arm leaves the thesis intact.)

---

## 4. VENUE-FIT CHECK

- **Keystone CLAIM-0003 → MLSys.** SOUND. The draft frames Pillar III as the end-to-end serving
  throughput-collapse headline (capacity × per-op cost multiplying into measured collapse, against a
  software baseline that SCALES 280→800 tok/s). A clean negative + systems-impact result with a scaling
  baseline is exactly MLSys's wheelhouse. The header and §5.3 both target MLSys explicitly; matches
  PAPER_OUTLINE.md:163.
- **CLAIM-0001/0002/0004/0007 → ATC/EuroSys/OSDI.** SOUND. Mechanism + measurement body (per-op
  domination, vendor ceiling, capability delta) is appropriate supporting-venue framing; matches
  PAPER_OUTLINE.md:164. The body can stand alone as an ATC/EuroSys systems paper if split from the keystone.
- **Negative-result framing as a CONTRIBUTION, not a non-result.** YES. The draft positions itself as a
  "measured negative result" / "characterization angle" and earns it three ways: (1) it BUILT both arms
  and measured head-to-head (not a paper-design argument); (2) the cross-vendor divergence makes the
  capacity pillar falsifiable (a portability cliff, not an unfalsifiable universal law) — which a systems
  PC rewards; (3) the §6 concession makes the negative read as rigorous rather than motivated. §1 and §7
  both explicitly stake out the negative/characterization angle as the contribution that the
  positive-result prior art structurally does not occupy. This is a publishable shape, not a "we tried X
  and it didn't work" non-result.

**Venue-fit: PASS.**

---

## 5. OVER-CLAIM SCAN

Searched the full draft for the canonical over-claim patterns. Findings:

- **"CDC always wins" / "always" / "guaranteed" / "universal law":** NONE. The draft deliberately frames
  the ceiling as a *vendor portability cliff*, NOT a universal GPU law (§3.4 explicitly: "a *stronger and
  more falsifiable* claim than 'structural GPU limit'").
- **A slope law / scaling law asserted as a finding:** NONE. The only forward-looking SW-scaling question
  (§8 "Forward direction") is explicitly fenced as future/separate work, NOT a PROJ-0001 claim, with its
  most-probable outcome flagged as "a derivable accounting identity" — i.e. the draft pre-emptively
  declines to claim a slope law. Correct.
- **A re-probe / re-run instruction:** NONE. The single regex hit ("re-run instruction") is at §3.4 line
  214, where the draft says the driver-version scoping is "a stated threat-to-validity, **not** a re-run
  instruction" — i.e. it explicitly REFUSES to instruct a re-probe (consistent with the MI350X postmortem
  / FORBIDDEN re-probe constraint). This is correct hygiene, not an over-claim.
- **"CoW always loses" absolutism:** NOT present. The draft says HW VMM CoW is "dominated" / "0/12 in any
  win-region" (bounded to the measured grid) and CONCEDES the one capability delta (§6). The honest
  concession is exactly what prevents the absolutism over-claim.
- **MEMORY.md stale "96x":** does NOT appear in the draft (draft headlines 153x). No leak.

**OVER-CLAIMS: NONE.** The draft is, if anything, conservatively scoped.

---

## PUNCH-LIST (optional polish only — NONE gate submission)

1. **(OPTIONAL, GPU-safe) One real FlashInfer cell.** A measured FlashInfer kernel-latency bench (NOT a
   mapping probe — no MI350X-postmortem risk) would convert the 41-152x from analytic→measured. It only
   WIDENS an already-proven gap and is NOT required (the measured 1.06-2.20x SW domination is self-healing).
   Per PUBLICATION_READINESS.md §2b. Deferrable.
2. **(OPTIONAL, doc hygiene, OUTSIDE the draft) `needs_attention.md` lines 7+9** still contain stale
   "re-probe before paper-track" wording. This is a notes-file artifact, NOT a draft defect — the DRAFT
   already scopes the ceiling correctly (§3.4) and refuses to re-probe. Reword to a driver-version-scoped
   statement; do NOT re-probe. Does not gate the paper.

Neither item touches a promoted claim or the draft's correctness. The draft is submission-ready as written.

---

## Constraints honored
Wrote ONLY this file under `prior_art/PROJ-0001/`. No claim/verdict/map edits. No experiments. No
GPU/model CLIs/mapping re-probes (FORBIDDEN per MI350X postmortem). CPU-only. All findings verified
against existing result files with exact paths above. Did NOT re-mine adjacent/frontier claims (mined out).
