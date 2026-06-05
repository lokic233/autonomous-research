# DELIBERATE STANDBY (orchestrator-r8-001, 2026-06-05) — awaiting dengcchi posture decision

0/2 investing is INTENTIONAL, not a gap/stall. The CLAIM-0059-shaped frontier is EXHAUSTED (see
FRONTIER_EXHAUSTION_r8.md): ~13 scouts, the cross-runtime physical+semantic sub-frontiers structurally saturated. A
POSTURE DECISION is escalated to dengcchi (quiesce / expand-topic-bias / relax-bar / human-lead).

SELF-CHECK BEHAVIOR WHILE IN STANDBY:
- ACK the proj_monitor DESIGN/refill flags with "deliberate standby, frontier exhausted, awaiting dengcchi posture
  decision — see FRONTIER_EXHAUSTION_r8.md" (do NOT scout the exhausted frontier; do NOT force a seed).
- Keep heartbeating (orchestrator + GPU coords); keep the engine warm; commit durable state.
- IF dengcchi supplies a posture (expand to a NEW topic-bias / a specific human lead / relax the bar): RESUME seeding
  in that direction (a genuinely fresh domain reopens the frontier).
- IF a committee/researcher/real-work item appears: ACT on it normally (standby is only about NOT scouting the dead frontier).
- At ~85pct of 350k tokens (~297k; currently ~196k): ros learn distill + clean-retire to orchestrator-r9-001 (prune the
  oversized Tier-1 brain in the handoff). r9 inherits STANDBY until dengcchi decides.
