# Needs Attention — PROJ-0001

Open prior-art risks / things to recheck before promoting further:
1. **vAttention overlap (CLAIM-0001/0007):** read-only VMM-KV is theirs; our delta is fork/CoW + the
   negative result. Keep the boundary sharp; recheck if vAttention adds branching.
2. **Cross-vendor ceiling (CLAIM-0002/0004):** measured NVIDIA 520K vs AMD no-wall (see
   511ce2e2__CROSSVENDOR_RESULT.md). A driver update could change the number — re-probe before paper-track.
3. **CLAIM-0005 (injection penalty):** sub-quadratic; needs a 3rd independent engine (TensorRT-LLM) to settle.
4. Freshness: LLM-inference area moves fast — re-run prior-art search before any candidate→paper-track promotion.


## UPDATE 2026-05-31 (orchestrator-r2-001, via laneB audit D4)
- STALE ITEM CORRECTED: 'CLAIM-0005 needs a 3rd engine (TensorRT-LLM) to settle' is OBSOLETE. CLAIM-0005 is CLOSED (VERDICT-0019): k is sub-quadratic AND drifts 1.0->2.0 with context (regime-local crossover slope, accounting-derivable), NOT a law. Sub-hypothesis buried DEAD-0009. No 3rd engine needed.
- PROJ-0001 assessed SATURATED/mature (laneB completeness audit): 5 promoted GREEN claims + 9 dead ideas fully fence the area; residual = paper-track + cosmetic map-hygiene (now applied).
