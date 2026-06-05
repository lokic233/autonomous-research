# PROJ-0041 / CLAIM-0071 — ORCHESTRATOR CONVERGE DECISION (r11-001, 2026-06-05)
VERDICT-0070: committee#1 UNANIMOUS 6/6 YELLOW (no RED). Both orchestrator-flagged stress-tests resolved AGAINST the strong form.
DECISION: CONVERGE (accept the honest yellow; do NOT advance to the heavy L1).
RATIONALE: (1) MECHANISM-NOVELTY DEAD: the loud-vs-silent-by-location asymmetry is documented WAL-family behavior; RocksDB
WAL Recovery Modes PARAMETERIZES it (configurable API in a mature peer), LevelDB log_reader same shape (>=2-source
collision). (2) SEVERITY STRUCTURALLY CAPPED (the decisive POSIX-barrier argument): the silent-loss of SyncAll-acked data
is a POSIX-impossible injection artifact (fsync(N+1) Ok => N on disk on barrier-honoring hardware); the only REAL crash
(dm-flakey) drops un-fsync'd Buffer data = contractually-ALLOWED loss = contract working as specified. (3) The L1 to reach
GREEN requires a dm-log-writes barrier-reorder replay that the POSIX argument suggests likely CANNOT cross the durability
boundary on conforming hardware -- so the heavy L1's modal outcome is confirming the loss is contractually-allowed -> low EV;
plus a peer-LSM differential + reframe + mandatory prior-art (RocksDB/LevelDB/ALICE/FAST'17). (4) What survives is a NARROW
un-owned INSTANTIATION (fjall ships the silent-truncate default with no AbsoluteConsistency opt-out + no error surface) =
worth a FJALL ISSUE/ADVISORY, not a publishable novel finding. LIGHTWEIGHT posture: converge the honest yellow + move on.
VALIDATED CONTRIBUTION (recorded honestly): fjall 3.1.4 hardwires silent-truncate-on-framing-corruption as the only
recovery mode (no opt-out, no error surface), with a clean discriminating control (in-data->loud checksum). An honest,
source-verified, actionable-for-fjall instantiation of known WAL recovery behavior. Zero false greens maintained.
DISTILL-NOTE: the immature-wedge can still hit the mature-DOMAIN's documented behavior even in a YOUNG tool when the young
tool INHERITS a mature format family (LSM/WAL): fjall is young but its journal recovery is the LevelDB/RocksDB WAL family,
so the MECHANISM is owned by the family even though the fjall INSTANCE is un-owned. SCREEN immature-wedge claims: is the
mechanism genuinely new to the young tool, or INHERITED from a mature lineage the tool reimplements? (Also: a crash-durability
claim must clear the POSIX barrier — a manual-corruption/reorder-sim that creates a state unreachable on barrier-honoring
hardware proves nothing about acknowledged-durable loss; only dm-log-writes-class barrier-reorder replay does.)
NEXT: PROJ-0041 converged. CLAIM-0070 (wazero) L2 still live (the stronger green-track). Refill the freed slot with a fresh immature-wedge claim.
