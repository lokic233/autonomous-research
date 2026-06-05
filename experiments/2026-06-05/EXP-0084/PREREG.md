# PRE-REGISTRATION — EXP-0084 (CLAIM-0071, PROJ-0041)
**Researcher:** researcher-0071 · **Date:** 2026-06-05 · **Node:** cli:devvm14382 (CPU, L0)
**Written BEFORE running any corruption probe.**

## CLAIM under test
In fjall v3.1.4, journal FRAMING corruption (torn write / out-of-order page writeback that
removes an End marker — the natural signature of default `PersistMode::Buffer`) is silently
treated as an incomplete trailing batch: the DB OPENS WITH NO ERROR while silently DISCARDING
all `PersistMode::SyncAll`-acknowledged committed data after the corruption point — WHEREAS
in-DATA corruption (same byte budget, inside a value) is caught by the per-batch xxh3 checksum
and surfaced as a loud `Err`. WHERE the corruption lands (framing vs data), not how much,
decides loud-fail vs silent-loss.

## Pinned version
fjall = "=3.1.4" (exact pin in Cargo.toml). Record the resolved lockfile hash + source path.

## Harness (L0)
Rust binary: open keyspace/partition, write 50 keys (k00..k49) each via `PersistMode::SyncAll`,
ASSERT each insert returns Ok (acknowledged-durable). Close cleanly. Then for each corruption
mode, copy the journal dir, corrupt at a controlled offset, reopen READ-ONLY-ish (open + count),
report (open_ok, keys_present/50, error_string).

## Corruption modes (location, fixed ~ byte budget where applicable)
- **data_flip** (CONTROL / NULL): flip 1 byte INSIDE a value, framing intact -> EXPECT open_ok=FALSE, loud ChecksumMismatch.
- **trailing**: truncate/tear the LAST batch -> EXPECT open_ok=true, ~49/50 (correct, documented).
- **mid_truncate**: truncate journal mid-stream -> EXPECT open_ok=true, 0<keys<50 SILENT.
- **mid_zero**: zero a page mid-stream (later batches intact on disk) -> EXPECT open_ok=true, 0<keys<50 SILENT.
- **mid_flip**: flip a byte that creates a spurious mid-stream Start/framing desync -> EXPECT open_ok=true, 0<keys<50 SILENT.
- **early_trunc**: truncate very early -> EXPECT open_ok=true, ~0-1/50 SILENT.

## Mechanism verification (installed source)
Inspect ~/.cargo registry fjall-3.1.4 source: confirm JournalBatchReader on framing desync
-> truncate_to(last_valid_pos) + return None -> recovery for-loop ends normally -> clean open;
on checksum mismatch -> loud Err. Confirm truncation is only log::debug/trace (no error path).
Confirm this recovery behavior is PRESENT in 3.1.4 (distinct from FIXED #112/#113 clean-path bug).

## ★ REAL-CRASH HARNESS (green-blocker, gate 5 "arises in real usage")
Root IS available (passwordless sudo). dm-log-writes NOT built for kernel 6.13.2-fbk7;
**dm-flakey IS available** (loaded). Plan:
  (a) PRIMARY: place fjall DB on a loop-backed dm-flakey device. Write 50 SyncAll keys.
      With default PersistMode::Buffer (no fsync), data sits in OS page cache / device buffer.
      Switch dm-flakey into "drop_writes"/"error_writes" interval so the tail of the journal's
      page writeback is DROPPED (faithful out-of-order/torn writeback under a crash). Then drop
      caches + reopen. GOAL: show a FRAMING tear (missing End mid-journal) arises from the
      DEFAULT Buffer path under a realistic dropped-writeback crash -> silent loss + clean open.
  (b) If dm-flakey cannot produce a clean mid-journal tear, ALSO run a userspace reordered-
      writeback simulation: capture the journal byte image, replay writes truncated at a
      page boundary (consistent with what a fsync-less Buffer crash admits), reopen.
      Clearly labeled a FAITHFUL SIMULATION, not a real power cut.

## NULL (pre-registered)
For FRAMING corruption: open fails loudly (open_ok=false) OR all 50 keys present.

## IT-MATTERS THRESHOLD
FRAMING corruption -> open_ok=true AND 0<keys<50 (silent partial loss of acknowledged data),
WHILE the in-data control fails loud (open_ok=false). The loud-vs-silent asymmetry BY LOCATION.

## COULD-IT-FAIL (honest branches)
- If 3.1.4 surfaces an Err/warning a caller MUST handle on framing corruption -> WEAKEN/KILL.
- If it recovers ALL 50 keys on framing corruption -> KILL.
- If the behavior was fixed since the scout's probe -> KILL (report version).
- Do NOT craft a corruption no real crash could produce; realism is the point.

## DISPOSITION RULE
SUPPORT iff: control loud-fails AND >=2 framing modes show silent 0<keys<50 clean-open
AND the real-crash harness (dm-flakey or labeled sim) produces the framing tear from the
DEFAULT Buffer path. Else WEAKEN/KILL honestly.
