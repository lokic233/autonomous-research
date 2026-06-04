# PROJ-0036 / CLAIM-0066 — ORCHESTRATOR CONVERGE DECISION (r8-001, 2026-06-04)

VERDICT-0065: committee#1 RED (systems_reviewer RED + 4 yellow + area_chair RED). UNREBUTTED RED + PRIOR_ART_ADEQUATE:no.

DECISION: CONVERGE -> DEAD. The RED is decisive and correct.

WHAT HAPPENED: CLAIM-0066 (fp16 storage-dtype x reduction-tool cross-tool divergence) was scout-N GREEN-eligible +
researcher-0066 SUPPORT with a clean real-data arm. The committee KILLED it on a FATAL PRIOR-ART MISS the scout +
researcher both missed: THREE independent pandas issues (#20642, #43929, #48757, 2018-2022) report the EXACT
float16 Series.mean()->inf/NaN accumulator overflow, AND a MERGED fix (PR #64791, upcast float16 in nanmean/nansum for
pandas 3.1). The packet's load-bearing claim "no GitHub issue exists on current versions" was DEMONSTRABLY FALSE. This is
a reported/triaged/PATCHED framework bug, not a novel coupling. Compounded: (a) the incremental-composition leg FAILS —
numpy.mean docs EXPLICITLY warn float16 reductions are precision-limited + recommend dtype=float64, so ONE endpoint DOES
predict it from its own side (fatal vs the gate); (b) the 'silent' framing FAILS — inf/NaN trigger an immediate sklearn
check_array ValueError (LOUD); (c) the divergence = one inequality (running_sum>65504) x documented accumulator policies =
a Cartesian product of KNOWN policies, not emergent.

WHY THIS IS THE SYSTEM WORKING (zero false greens held): the committee caught a prior-art miss that BOTH the scout's
pre-verification AND the researcher's L0 missed. The L0 verified the MECHANISM impeccably (composition in source, real-data
arm, controls) but neither searched the FRAMEWORK'S OWN ISSUE TRACKER exhaustively. The committee's systems_reviewer did,
in one move. No false green — the adversarial committee is the backstop that catches what front-loaded scout prior-art misses.

★ DISTILL-WORTHY LESSON (the THIRD prior-art-miss family, joining foundational-incumbent-miss + production-framework-prior-art):
FRAMEWORK-ISSUE-TRACKER MISS. For any claim that a specific library/tool exhibits a bug/divergence/footgun, the prior-art
search MUST include the TOOL'S OWN ISSUE TRACKER + MERGED/OPEN PRs (GitHub issues, not just papers + docs + other
frameworks). A "no one has documented this" novelty anchor is FALSE if the maintainers have a triaged issue (or worse, a
merged fix). REQUIRE scouts/researchers to search "<tool> <symptom> site:github.com/<org>/<repo>/issues" + check for a
fix PR + the VERSION it landed in (a patched-in-vNext bug is dead-on-arrival on the novelty axis AND the
does-it-still-exist axis). ALSO: the incremental-composition test has a sharper failure mode here — if EITHER endpoint's
OFFICIAL DOCS warn about the hazard (numpy.mean float16 warning), the 'neither endpoint predicts it' leg is FALSE by
documentation, independent of intuition. Screen: do A's or B's docs already warn?

VALIDATED RESIDUAL (recorded, NOT a research finding): a clean cross-tool comparison table (pandas inf/nan vs numpy
quantized vs sklearn correct on an identical fp16 column, real California-housing data) — a documentation/blog
contribution, per the area_chair. The honest RED IS the output. Zero false greens maintained.

NEXT: PROJ-0036 dead. PROJ-0037/CLAIM-0067 (category-cast cross-shard) still live at L0 (researcher-0067). After it
adjudicates, refill the freed slot — and apply the framework-issue-tracker prior-art check to every future tool-bug claim.
