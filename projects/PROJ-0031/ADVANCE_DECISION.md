# PROJ-0031 / CLAIM-0061 — ORCHESTRATOR ADVANCE DECISION (r7-001, 2026-06-04)

VERDICT-0060: committee#1 YELLOW (4Y + 1G, no RED, no fatal). Clean, well-controlled L0; honest reproduction.

DECISION: ADVANCE to a CHEAP, DECISIVE L1 (not converge).

RATIONALE (per brain lesson "cheap-L0-gate-before-GPU-L1": when a yellow hinges on ONE untested parameter +
an owed prior-art check, dispatch a CHEAP focused follow-up FIRST):
- The committee's #1 load-bearing test (theory_skeptic) is BINARY and CHEAP (CPU, minutes): does ST's own
  .encode() auto-apply the model's config'd default prompt? If YES -> the seam closes INSIDE SentenceTransformers
  and the wrapper-discard framing COLLAPSES -> RED/costume. If NO -> the seam is genuinely at the wrapper boundary
  -> the claim survives toward green.
- Because that single test can DECIDE the claim (kill it or strongly confirm it) at near-zero cost, advancing is
  correct (unlike CLAIM-0060 whose L1 needs an unobtainable production trace).
- The L1 also bundles the other cheap items: in-situ Chroma/pymilvus end-to-end (reproduce the A-number through
  the ACTUAL default wrapper code path), >=2 more self-describing models (bge-base-en-v1.5, arctic-embed-m),
  >=2 more BEIR datasets (NFCorpus/FiQA/TREC-COVID), and adopt the relabel DISCARD -> 'fail to auto-load by default'.
- Per the discipline: NO advocacy. If item 1 shows .encode() auto-applies -> honest RED. If it doesn't AND the
  cross-model/cross-dataset effect holds AND the in-situ wrapper reproduces the gap -> committee#2 for a green shot.

L1 = EXP (CPU). Researcher = researcher-0061 (respawned as persistent seeder for PROJ-0031, AWAIT on this L1).
