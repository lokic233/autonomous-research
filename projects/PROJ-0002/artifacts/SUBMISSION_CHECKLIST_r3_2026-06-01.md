# SUBMISSION-READINESS CHECKLIST — PAPER_DRAFT_r3_FINAL.md
**Agent:** researcher-0006-packaging-r3 (submission-packaging + independent second-eyes lane)
**Date:** 2026-06-01 · **Target:** prior_art/PROJ-0002/CLAIM-0006/PAPER_DRAFT_r3_FINAL.md
**Posture:** VERIFY-only, CPU/reading/web-abstract. Did NOT modify the paper, map, claims, verdicts,
or run any experiment. Read-only on all systems. Fixes are FLAGGED for the orchestrator, not applied.
**Lineage:** paper-r3 finalized the draft; verify-r3 red-teamed it SUBMITTABLE-AS-IS (2 non-blocking polish
items). This lane is an independent packaging pass (structure / references / artifact-repro), as if
preparing for an MLSys/EuroSys submission. The PARKED env-gate (true async V1 KVConnector E2E,
VERDICT-0043) is OUT OF SCOPE and was not touched.

---

## VERDICT: **GO** — submission-ready as a path-(b) honest-conditional characterization paper.
**(with 2 OPTIONAL pre-submission NITS, neither a blocker — see bottom.)**

Independent of verify-r3, I reached the same conclusion: the draft is structurally complete, every
arXiv id that can be checked on the public web resolves to the correct paper, and every headline EXP
is backed by a committed result.md + JSON/CSV. The single disclosed repro gap (EXP-0034 logs point
ratios only) is already stated honestly in §5.4. Nothing here changes the SUBMITTABLE verdict.

---

## 1. STRUCTURAL PASS — all required sections present (PASS)

| Required element | Present? | Location |
|---|---|---|
| Title | YES | line 1 (descriptive, names all three contributions) |
| Abstract | YES | §Abstract (incl. up-front Scope sentence) |
| Intro & Motivation | YES | §1 |
| Contributions (enumerated) | YES | §1 (3-fold list: cost-map / win-region / honest bracket) |
| Method / cost-map | YES | §2 (relation, accounting-identity honesty boundary, per-engine CIs, caveats) |
| Workload win-region | YES | §3 |
| Novelty positioning | YES | §4 (gate-A, 10/10 neighbors) |
| **Honest competitive bracket** | YES | §5 (+§5.1–§5.6 per-cell tables, CI accounting, framing sentence) |
| **Scope/Limitations box** | YES | §6.1 (boxed; §6.2 EXP-0034-framing) |
| Related work | YES | §7.1 (all works named w/ arXiv ids) |
| Conclusion | YES | §7.2 |
| Declared-future axis (residual) | YES | §7.3 |
| Submission-readiness self-verdict | YES | §8 |
| CHANGELOG (provenance) | YES | end-of-file |

- **No dangling placeholders.** grep for TODO/FIXME/XXX/PLACEHOLDER/TBD/FILLME/`[[`/`<insert` → ZERO hits.
- **§5.1 table-split (verify-r3 nit #1) is FIXED.** The EXP-0030 per-cell table now renders as one clean
  6-row table (lines 149–156); the stray blank line is gone. Orchestrator fix confirmed.
- **Env-gate future-work statement is CONSISTENT across all 5 cited places** (Abstract / §1 "Scope, stated
  once" / §5 bracket row + §5.5 framing / §6.1 box + §6.2 / §7.3). Every instance gives the same blocker
  (vLLM 0.6.6.post1 lacks the V1 KVConnector API; c_ops ABI cannot survive the vLLM>=0.7 upgrade), the same
  framing (declared future work, not a gap), and the same bounded direction (more overlap -> SHRINK not
  REVERSE the margin; 8k/5% 0.32% is the most-likely-to-tie cell). No drift, no contradiction.
- **Internal cross-references are consistent.** §5.4 (CI-accounting) and §6.1 (box) both point to EXP-0034's
  point-ratio-only limitation; §5.3 side-by-side table marks the E2E CI column "— (not in logged record)".
  All section pointers (§2/§3/§4/§5.1/§5.4/§6.1/§7.3) resolve to existing sections.

## 2. REFERENCE COMPLETENESS — 11 required arXiv ids (PASS)

Live web-abstract spot-check (2026-06-01). **9/11 resolve on the public web to the exact title/authors the
paper cites; the 2 that don't are future-dated run-internal papers, correctly handled (see note).**

| arXiv id | Paper's characterization | Web-abstract check |
|---|---|---|
| 2405.16444 CacheBlend | PIC baseline + r%<->overhead identity source | ✅ EXACT — "CacheBlend: Fast LLM Serving for RAG…", EuroSys'25 |
| 2410.15332 EPIC | PIC family, body-distinct | ✅ EXACT — "EPIC: Efficient Position-Independent Context Caching…" |
| 2512.16822 MEPIC | PIC family | ✅ EXACT — "MEPIC: Memory Efficient Position Independent Caching…" |
| 2502.15734 Cache-Craft | PIC family, chunk-cache RAG | ✅ EXACT — "Cache-Craft: Managing Chunk-Caches…" |
| 2507.07400 KVFlow | PIC family, agentic prefix caching | ✅ EXACT — "KVFlow: Efficient Prefix Caching… Multi-Agent Workflows" |
| 2510.10129 CacheClip | PIC family | ✅ EXACT — "CacheClip: Accelerating RAG with Effective KV Cache Reuse" (Intel) |
| 2309.06180 vLLM PagedAttention | serving substrate (Kwon et al.) | ✅ EXACT — "Efficient Memory Management… with PagedAttention" (SOSP'23) |
| 2312.07104 SGLang RadixAttention | serving substrate (Zheng et al.) | ✅ EXACT — "SGLang: Efficient Execution of Structured LM Programs" (NeurIPS'24) |
| 2211.05102 Pope | KV accounting identity source | ✅ EXACT — "Efficiently Scaling Transformer Inference" (MLSys'23, Pope et al.) |
| 2605.05696 Irminsul | CDC-over-radix MECHANISM TWIN (conceded) | ⚠️ future-dated (2026-05); not on public web. See NOTE. |
| 2601.06007 Don't-Break-the-Cache | motivation, not competitor | ⚠️ future-dated (2026-01); not on public web. See NOTE. |

**NOTE on the 2 future-dated ids (NOT a blocker, correctly handled):** Irminsul (2605.05696) and
Don't-Break-the-Cache (2601.06007) carry 2026 arXiv ids that post-date public web crawl coverage, so they
do not resolve via web search — expected, not a defect. Both are body-read (LaTeXML HTML: ~66k / ~49k chars,
files /tmp/txt_2605.05696.txt, /tmp/txt_2601.06007.txt) and recorded in novelty_boundary_2026-05-31.md and
registry/academic_map.yaml. Irminsul's single-source risk is cleared by a 2nd index (SemScholar CorpusId
288013360 + OpenAlex W7160639578). The paper's roles are correct: Irminsul = conceded mechanism twin
(CLAIM-0006's surviving leg is distinct); Don't-Break-the-Cache = motivation (body-level distinct, no inj/seq
cost-map). No fabricated citation; both characterizations match the body-verified notes.

- All 11 ids are also named **by name** in §4 / §5 / §7.1 (VERDICT-0043 condition 3) — verified.
- The 2 previously-missing serving-substrate ids (2309.06180, 2312.07104) are now present — verified.
- **Live collision re-scan (verify-r3 confirmed; spot-rechecked):** no NEW public paper draws an
  engine-internal recompute-fraction-vs-inj/seq cost-map for mid-prefix injection. Novelty boundary holds.

## 3. ARTIFACT / REPRO PACKAGING — EXP -> claim backing (PASS, 1 disclosed gap)

All 8 cited EXP records exist on disk under experiments/2026-05-31/<EXP>/experiment_result/ with a
committed result.md + machine-readable JSON (two also ship results.csv). A reviewer could re-derive every
headline number from the committed artifacts, EXCEPT the one disclosed EXP-0034 gap.

| EXP | Backs (paper section) | Committed artifacts | Reviewer can reproduce? |
|---|---|---|---|
| EXP-0002 | §2.4 anchor "~2%" + surface (min/median/max) | analysis.md, exp0002_surface.json | YES — surface json + analysis |
| EXP-0003 | §5 contiguous-baseline 8.3x–465x (structural; not headlined) | analysis.md, results.json | YES |
| EXP-0013 | §2.3 per-engine cost-map slopes/CIs/R², attn-sink, margins | result.md, **results.csv**, results.json | YES — raw csv present |
| EXP-0015 | §3 win-region (token/count/conditional, 16-prior sweep, CIs) | result.md, **results.csv**, results.json | YES — raw csv present |
| EXP-0026 | §5 re-impl PIC E2E (CDC 12/12 TTFT+throughput) | result.md, serving_results.json | YES |
| EXP-0027 | §5 oracle/fused PIC (CDC 2/6; loses low inj/seq) | result.md, oracle_results.json | YES |
| EXP-0030 | §5.1 **KEY RESULT #1** real lmcache gather, per-cell **bootstrap CIs** | result.md, grid_results.json | YES — CIs in result.md + json, match §5.1 cell-by-cell |
| EXP-0034 | §5.2 **KEY RESULT #2** combined in-window E2E (12/12 point ratios) | result.md, grid_results.json, smoke json | PARTIAL — see gap |

**Disclosed repro gap (EXP-0034) — already in the paper, no action needed for honesty:** EXP-0034's
grid_results.json contains `rows_summary` POINT RATIOS ONLY (`reps:6`, `full_connector_in_loop:false`); there
are **no per-rep TTFT arrays and no CI fields.** A reviewer can therefore reproduce the 12/12 directional
point ratios but **cannot recompute CIs** for the E2E composition. The paper discloses this verbatim in §5.4
("point ratios only — no per-rep arrays and no logged CIs"), reports NO CI for EXP-0034, refuses to invent
intervals, and flags it to the orchestrator as a logging change (re-emit per-rep arrays — a harness edit, not
a new GPU sweep). I independently confirmed the json carries point ratios only and that §5.4's claim is
accurate. **This is honest, not a blocker.**

## 4. FRESH-EYES OBSERVATIONS (independent of verify-r3)

- **No figures in the paper (prose + tables only).** grep for "Figure"/"Fig." -> ZERO. The cost-map (§2),
  the win-region (§3), and the two-axis bracket (§5) are conveyed entirely by tables. This is the one item
  a top-tier MLSys/EuroSys reviewer is most likely to comment on: those venues strongly expect at least a
  cost-map FIGURE (recompute% vs inj/seq per engine) and ideally a win-region heatmap. The DATA to draw them
  is fully committed (EXP-0013 results.csv, EXP-0015 results.csv). This is a presentation/packaging nit for
  the eventual camera-ready, NOT a validity or honesty issue. (PAPER_CAMERAREADY.md exists in the dir as a
  separate artifact — the orchestrator may already be tracking figure generation there.)
- The self-contained "§8 Submission-Readiness Verdict" is unusual for a submitted paper body (it reads like
  an internal gate note). For an actual MLSys submission it would normally be dropped or folded into the
  conclusion. Cosmetic; flag for the orchestrator at camera-ready time.

---

## NITS (OPTIONAL, NON-BLOCKING — flagged for orchestrator, do NOT block submission)

1. **[presentation] Add figures for camera-ready.** No figures currently; MLSys/EuroSys reviewers expect a
   cost-map figure (recompute% vs inj/seq, per engine) + a win-region heatmap. Data is committed
   (EXP-0013/EXP-0015 results.csv). Not a validity issue. (Inherits/extends verify-r3's scope; new here.)
2. **[clarity] §3 "median inj/seq = 2.8%" cite tightening.** Same as verify-r3 nit #2: point a reader chasing
   the 2.8% at EXP-0005's record explicitly (it's surfaced via EXP-0015's reproduction). One-word tweak,
   optional, not an error.

(verify-r3's nit #1 — the §5.1 table split — is already FIXED by the orchestrator. Confirmed.)

---

## BOTTOM LINE

**GO.** Independent packaging pass confirms PAPER_DRAFT_r3_FINAL.md is submission-ready as an honest-
conditional path-(b) characterization paper: all sections present, no placeholders, env-gate future-work
statement consistent in all 5 places, 9/11 arXiv ids live-verified (the 2 unverifiable are future-dated
run-internal papers, body-read + correctly characterized + 2nd-indexed), and all 8 headline EXPs backed by
committed result.md + JSON/CSV with the single EXP-0034 point-ratio-only repro gap already disclosed in §5.4.
The 2 NITS (add figures for camera-ready; one cite tightening) are optional and do not block submission.
The PARKED single GREEN gate (true async V1 KVConnector E2E under concurrent load, VERDICT-0043) is a
HUMAN/operator env-upgrade decision and remains correctly out of scope — not re-opened here.

— researcher-0006-packaging-r3, 2026-06-01
