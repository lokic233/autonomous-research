# Quarantine — orphan / malformed registry artifacts (NOT live state)

Files here are NOT part of any claim's verdict_history and are excluded from live counts.
Quarantined by the monitor, never deleted, for audit.

## VERDICT-0010_orphan_9999-01-01.yaml (quarantined 2026-06-01 by monitor 6433b2c0)
- Was at registry/verdicts/PROJ-0002/9999-01-01/VERDICT-0010.yaml — a PHANTOM future date dir.
- A 6/6 GREEN verdict for CLAIM-0006 citing EXP-A006 (old EXP-A### scheme), created 2026-05-31T13:48
  by an early/test run that passed `--date 9999-01-01` (sentinel). It is NOT in CLAIM-0006's
  verdict_history (19 real entries: VERDICT-0007 green -> 18 yellows ending VERDICT-0043).
- CLAIM-0006's REAL current state is weakened/blocked at 4/6 (VERDICT-0043), parked on the vLLM>=0.7
  human decision. This orphan stale-green must NOT be counted as a real GREEN for CLAIM-0006.
- Root cause fixed in engine: ros.py _valid_date() now rejects malformed/sentinel/out-of-window
  --date values (BUG-27), so no phantom date dirs can be minted again.
