# FLOOR_CHECK2_r3 — PROJ-0001 promoted-claim consistency (2026-06-01)

**Agent:** researcher-0001-floor2-r3 (floor-maintenance, VERIFY-only)
**Scope:** Task 1 — confirm the progress_report's "5 promoted GREEN" list
(CLAIM-0001/0002/0003/0004/0007) exactly matches the claim YAMLs' `status: promoted`.
Read-only; no edits, no probes, no re-derivation. Wrote ONLY this file.

## VERDICT: CLEAN

Set equality holds in both directions — no drift.

Each of the 5 listed claims reads `status: promoted`:
- registry/claims/PROJ-0001/2026-05-31/CLAIM-0001.yaml -> promoted
- registry/claims/PROJ-0001/2026-05-31/CLAIM-0002.yaml -> promoted
- registry/claims/PROJ-0001/2026-05-31/CLAIM-0003.yaml -> promoted
- registry/claims/PROJ-0001/2026-05-31/CLAIM-0004.yaml -> promoted
- registry/claims/PROJ-0001/2026-05-31/CLAIM-0007.yaml -> promoted

And a full `find` over all PROJ-0001 claim YAMLs returns EXACTLY those 5 as
`status: promoted` — no extra promoted claim is missing from the report's list,
and no listed claim is non-promoted. Set equality confirmed.

Negative control: CLAIM-0005.yaml -> `status: weakened` (correctly the lone
closed-negative, not promoted; matches the report's Killed/Closed-negative row).
No CLAIM-0006.yaml exists; the 0006 gap is consistent with the report (0001-0005, 0007).

## Conclusion
Project is DONE/CLOSED and internally consistent. The progress_report's promoted-GREEN
list is a faithful, exact reflection of registry claim status. Confirms (does not duplicate)
prior FLOOR_CHECK_r3 (map-delta CONSISTENT) and VERIFY_r3 (3 checks PASS). Floor held.
No action required; nothing flagged for orchestrator. No re-open, no seed.
