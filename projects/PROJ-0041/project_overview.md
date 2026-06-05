# PROJ-0041 — IMMATURE-WEDGE (databases-and-storage-engines): fjall LSM treats journal FRAMING corruption as a benign trailing-batch truncation -> silently discards SyncAll-acknowledged committed data with a CLEAN OPEN, while in-DATA corruption fails LOUD (checksum) (NEW NON-OBVIOUS COUPLING)

FRESH-DOMAIN resume, IMMATURE-WEDGE seam (validated path per FRONTIER_EXHAUSTION_r10_freshdomains.md). CLAIM-0059 winning
shape. scout-AA GO 4/5, pre-verified end-to-end on real fjall 3.1.4 with a clean A/B control.

## THE SEAM (two independently-owned subsystems)
- A = WRITE/DURABILITY path: default PersistMode::Buffer (write() to OS buffer, no fsync, "matches RocksDB"); SyncAll
  documented "data + metadata flushed... definitely durable".
- B = JOURNAL RECOVERY (JournalBatchReader): per-batch xxh3 checksum + Start/End framing. On checksum mismatch ->
  Err(ChecksumMismatch) (LOUD). On a FRAMING desync (Start-inside-batch / item-or-end-outside-batch / missing terminator)
  -> truncate_to(last_valid_pos) + return None -> iterator ends -> recovery for-loop ends NORMALLY -> CLEAN OPEN,
  post-corruption batches gone, truncation only log::debug/trace (no error path).
- DIVERGENCE: A's realistic crash signature under the default (torn append / out-of-order page writeback = FRAMING
  corruption) routes into B's SILENT branch, NOT B's loud-checksum branch.

## PRIMARY THESIS (verified, fjall 3.1.4, devvm14382; clean A/B)
WHERE the corruption lands decides loud-fail vs silent-loss. 50 SyncAll-acknowledged keys, corrupt journal, reopen:
data_flip (inside a value, framing intact) -> open_ok=FALSE loud ChecksumMismatch (NULL outcome, the discriminator);
trailing -> 49/50 (correct); mid_truncate -> 25/50 SILENT; mid_zero (out-of-order writeback) -> 16/50 SILENT; mid_flip
(spurious mid-stream Start) -> 12/50 SILENT; early_trunc -> 1/50 SILENT. All silent cases open_ok=true, no error.

## NOVELTY (MUST headline; gate-4 defense)
NOT generic "single-file WALs lose data after a hole" (folklore). The fjall-specific, un-owned claim: the LOUD-vs-SILENT
recovery ASYMMETRY by corruption LOCATION (in-data->loud checksum vs framing->silent truncate) under the DEFAULT durability
mode, + a CLEAN OPEN WITH NO ERROR while discarding committed-acknowledged data.

## 6-GATE SCREEN (cleared — see CLAIM-0071)
#1 incremental-composition PASS (durability-default x recovery-framing; neither predicts silent loss; README "let it crash"
but silent path produces no error). #2 verify PASS (installed+probed 3.1.4, measured). #3 issue/CVE/paper PASS UN-OWNED
(#53 = cosmetic warning-suppression on a TRAILING batch, never the silent committed-loss consequence; #112/#113 = a
different FIXED clean-path bug; recovery behavior STILL present in 3.1.4 + measured; no CVE/Jepsen/paper). #4 not-folklore =
live gate (scope to the loud-vs-silent-by-LOCATION asymmetry, fjall-specific). #5 prevalence PASS (Buffer is the DEFAULT;
torn/partial writes are THE realistic crash signature; fjall real+shipping). #6 not-tautology PASS (data_flip control nulled
with a loud Err -> discriminator real).

## L0 / NULL EXIT
Null = open fails loudly OR all 50 keys present. GO = open_ok=true AND 0<keys<50 (silent partial loss). Observed exactly
that on framing corruption; control (data_flip) loud-failed.
★ L1 HARDENING (scout-AA named it, the green-blocker): replace hand-corruption with a REAL reordered-writeback crash harness
(dm-log-writes / dm-flakey / CrashMonkey block-reorder replay) to prove the framing tear ARISES from the documented default
under real power-loss -> raises gate-5 from plausible-prevalent to demonstrably-arises. (devvm has root? verify; else
simulate ordered writeback faithfully.)

## HONEST RISK
Gate 4 (folklore): frame as the ASYMMETRY not "data loss". #53: distinct+stronger (committed-acknowledged loss on
non-trailing corruption w/ clean open). L0 hand-corruption -> L1 needs the real-crash harness. scout-AA 4/5.

## POSTURE
EXPAND-LIGHTWEIGHT: ONE sharp claim (CLAIM-0071), normal pipeline. L0 reproduce the loud-vs-silent asymmetry + the
dm-log-writes real-crash harness for L1. Owner: orchestrator-r10-001.
