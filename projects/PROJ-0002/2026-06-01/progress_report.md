# PROJ-0002 — Beginning-of-Day Progress Report (2026-06-01 UTC)

**Project:** Prefix-cache invalidation + KV reusability under agentic edits
**Orchestrator:** orchestrator-r3-001 · **Rescan:** full claims+verdicts+cemetery, project_id-filtered (no cross-project leak)
**Headline:** CLAIM-0007 promoted. CLAIM-0006 PARKED at honest 4/6 (env-gated on vLLM>=0.7 — human decision). Adjacent territory EXHAUSTED (6 lanes). No new claim to seed.

## Proved / Promoted (6/6 GREEN committee)
| Claim | Verdict | One-liner |
|---|---|---|
| CLAIM-0007 | VERDICT-0008 green | Attention-Visible GPU-MMU Write-After-Share (also rostered under PROJ-0001 lineage); promoted. |

## In-progress / PARKED
| Claim | Latest verdict | State |
|---|---|---|
| CLAIM-0006 | VERDICT-0043 (4 GREEN / 2 yellow; long yellow history V0011–V0041) | **PARKED — honest 4/6 conditional.** "Prefix-Cache Invalidation Law": mid-prompt tool injection of size R breaks the hash chain → inj/seq recompute cost-map + cheap CDC repair. Novelty+theory+systems+area_chair GREEN; eval_prosecutor+product_realist YELLOW. Both serving axes (EXP-0030 gather, EXP-0034 E2E composition) measured FAVOR CDC. |

**CLAIM-0006 single binding GREEN gate:** a TRUE async-connector E2E on vLLM>=0.7 V1 KVConnector under CONCURRENT load. This is an OPERATOR ENV UPGRADE (vLLM 0.6.6 lacks the V1 KVConnector API; upgrading would break the source-built lmcache c_ops ABI in ros-vllm). **HUMAN DECISION (dengcchi) — do NOT auto-upgrade.** PAPER_DRAFT.md is SUBMITTABLE NOW as honest-conditional characterization, with the async-connector E2E declared as future work.

## r3 lanes
- **paper-r3** (in flight): finalize CLAIM-0006 PAPER_DRAFT.md per area_chair conditions — scope-statement placement; 8k-context/5%-level CIs from logged CSVs; named baselines incl Irminsul (arXiv 2605.05696, CDC-over-radix mechanism twin), EPIC/MEPIC/CacheBlend/Cache-Craft (body-verified distinct), "Don't Break the Cache" 2601.06007 (motivation). CPU-only, no GPU, no env upgrade.
- **adjacent-r3** (DONE): vetted best next-adjacent claim → KILL / DO-NOT-SEED. injection_arrival_EXP-0040 candidate: V1 collides with EXP-0005; V2 replicates 1/2-harness with no CPU-reachable revive data. No next-best alternative. Adjacent territory EXHAUSTED (confirmed by 6 lanes: laneB/E/D/adjacent2/descseed/r3). Deliverable: prior_art/PROJ-0002/ADJACENT_CLAIM_r3_2026-06-01.md.

## Cemetery (project-filtered): none under registry/cemetery/PROJ-0002 (kills tracked in prior_art lane notes + EXP-0040 do-not-seed).

## Status: CLAIM-0007 done; CLAIM-0006 parked at env-gate (submittable conditional paper); no adjacent claim to seed. Effort → finalize the paper + PROJ-0003.
