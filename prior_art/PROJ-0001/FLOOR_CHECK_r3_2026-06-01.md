# FLOOR_CHECK_r3 — PROJ-0001 final-consistency (2026-06-01)

**Agent:** researcher-0001-floor-r3 (floor-maintenance, VERIFY-only)
**Scope:** Task 1 — internal consistency of the AMD-transfer map-delta between
`registry/academic_map.yaml` (MAP-0001 `amd_transfer_status`) and the updated
`DEAD-0003.yaml` `revival_conditions`. Read-only; no re-probe, no edits.

## VERDICT: CONSISTENT

The two texts agree on every load-bearing assertion. No drift found.

| Assertion | academic_map MAP-0001 | DEAD-0003 revival_conditions |
|---|---|---|
| Scope = per-op fork-cost axis ONLY | yes | yes |
| Transfers WITHOUT a probe | yes | yes |
| Capacity ceiling relaxed (never-binding in grid → can't flip a cell) | yes | yes |
| Per-op map-count ~512x higher (AMD 4KB granule) | yes | yes |
| Both deltas push SAME direction → widen SW's O(1) win | yes | yes |
| DEAD-0003 AMD revival door = PREDICTED-NO-ANOMALY | yes | yes |
| No GPU re-probe (MI350X_CRASH_POSTMORTEM honored) | yes | yes |

## Anchor check
- Both texts cite CLAIM-0001's "0/12 SW-win region" as the transferred evidence.
  `registry/claims/PROJ-0001/2026-05-31/CLAIM-0001.yaml` → `status: promoted`,
  claim text begins "HW VMM CoW is dominated for agent KV (0/12 win-region; ...)".
  The anchor is real, promoted/GREEN, and matches both references.
- Provenance line matches in both: gapmine-r3 proposed + verify-r3 verified +
  orchestrator-r3-001 applied (2026-06-01).
- Scoping caveat present on both sides: this is the per-op-fork-cost axis ONLY,
  NOT "AMD VMM dominated in general". (map-delta states it explicitly; revival_conditions
  states the dual "AMD VMM-CoW win-region is analytically excluded on the per-op axis".)

## Conclusion
Project is closed/DONE. The AMD-transfer map-delta is internally consistent across
the academic map and the DEAD-0003 cemetery record; the retirement of the AMD-side
revival door as predicted-no-anomaly is stated identically in both places. Floor held.
No action required; nothing flagged for orchestrator.
