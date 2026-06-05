# RESULTS — EXP-0084 (CLAIM-0071, PROJ-0041)
**Researcher:** researcher-0071 · **Date:** 2026-06-05 · **Node:** cli:devvm14382 (CPU, L0)
**Disposition: SUPPORT** (with one honestly-scoped L1 gap — see §7).

---

## 1. Pinned version + environment
- **fjall = "=3.1.4"** (exact pin). Cargo.lock: `name = "fjall" version = "3.1.4"
  source = registry+https://github.com/rust-lang/crates.io-index`. Transitive: lsm-tree 3.1.4.
- Rust 1.96.0. Kernel 6.13.2-0_fbk7. Root/passwordless sudo available.
- Source inspected at `~/.cargo/registry/src/index.crates.io-*/fjall-3.1.4/src/journal/`.

## 2. Verified mechanism (READ FROM INSTALLED 3.1.4 SOURCE)
The journal is a single, sequentially-written file **pre-allocated to 64 MiB**
(`writer.rs: PRE_ALLOCATED_BYTES = 64*1024*1024`). Default durability is
`PersistMode::Buffer` whose doc literally says: *"data is **not** guaranteed to be
persisted in case of a power loss event or OS crash"* and whose impl is a no-op
(`writer.rs:232  PersistMode::Buffer => Ok(())` — no fsync).

Recovery routes corruption into TWO branches by LOCATION:

**SILENT branch (framing desync → `truncate_to(last_valid_pos)` + `return None`, NO Err):**
- `reader.rs::next()` — a torn/short item read yields `UnexpectedEof`/`Other` →
  `maybe_truncate_file_to_last_valid_pos()` → `None`. Truncation logged at **debug** only.
- `batch_reader.rs` — `Start` inside a batch; `Item`/`Clear` without an open batch (lost
  Start); `on_close()` with `is_in_batch` (torn trailing batch, missing End): each calls
  `truncate_to(..)` (logged **trace/debug**: *"missing terminator, but last batch, so
  probably incomplete, discarding to keep atomicity"*) then `return None`.
- The recovery for-loop in `db.rs` sees the iterator end → logs **TRACE "Recovery
  successful"** → DB opens. Post-desync batches are gone; **no error is returned to the
  caller.** Even data physically present on disk *after* the hole is discarded.

**LOUD branch (`return Some(Err(JournalRecovery(..)))`):**
- `batch_reader.rs::End` with `got_checksum != expected_checksum` → **ERROR log** +
  `Err(JournalRecovery(ChecksumMismatch))`. (Also `InsufficientLength`, `TooManyItems`.)

→ **The per-batch xxh3 checksum only guards the in-DATA case; a framing tear never
reaches the checksum and silently truncates.** This is distinct from the FIXED #112/#113
clean-path bug; it is the live recovery behavior in 3.1.4.

## 3. Hand-corruption asymmetry table (50 SyncAll-acknowledged keys, corrupt journal, reopen)
Each insert + `db.persist(PersistMode::SyncAll)` returned `Ok` (acknowledged-durable).

| MODE          | location  | OPEN_OK | KEYS   | ERR                              |
|---------------|-----------|---------|--------|----------------------------------|
| none (base)   | —         | true    | 50/50  | none                             |
| **data_flip** | **DATA**  | **false** | **0/50** | **JournalRecovery(ChecksumMismatch)** ← CONTROL/NULL, loud |
| trailing      | framing   | true    | 49/50  | none  (documented torn tail)     |
| mid_truncate  | framing   | true    | 25/50  | **none** (SILENT)                |
| mid_zero      | framing   | true    | 16/50  | **none** (SILENT)                |
| mid_flip      | framing   | true    | 25/50  | **none** (SILENT)                |
| early_trunc   | framing   | true    | 2/50   | **none** (SILENT)                |

**In-data control fails LOUD; every framing mode opens clean (OPEN_OK=true) with
0<keys<50 and NO error.** WHERE the corruption lands, not how much, decides the outcome.
Recovery-log proof (mid_truncate): `DEBUG truncating journal to 5350` → `Recovery
successful` → `KEYS=25/50 ERR=none`, vs data_flip: `ERROR Invalid batch: checksum check
failed` → `OPEN_OK=false`.

## 4. ★ Real-crash harness — reordered-writeback (the green-blocker, gate 5)

### (a) dm-flakey REAL DEVICE-LEVEL CRASH (root; gold-standard instrument)
Loop-backed ext4 on a `dm-flakey v1.5.0` device. Default `Buffer` appends sit in page
cache (no fsync); `dmsetup ... drop_writes` silently drops the writeback of the dirty
journal pages at the crash instant = a faithful lost/torn page writeback on power loss.
Then restore device, `echo 3 > drop_caches`, remount, reopen.

| Case | data state at crash | journal post-crash | OPEN_OK | KEYS  | ERR  |
|------|---------------------|--------------------|---------|-------|------|
| A    | 45 appends live ONLY in journal | 535 B (frontier dropped) | true | **5/50** | **none** |
| B    | appends flushed to SST before crash | 5350 B | true | 50/50 | none |

→ Case A is a **real dropped-writeback crash that silently loses 40 committed keys with a
clean open and NO error.** Case B shows that when the data already reached a durable SST,
nothing is lost (correct). Every dm-flakey run confirms **OPEN_OK=true, ERR=none**; the
journal frontier is genuinely dropped on the device (size shrinks). HONEST NOTE: the keys
lost in Case A were `PersistMode::Buffer` (un-fsync'd) — losing those on power loss is
*documented*. dm-flakey cannot drop data whose `SyncAll` fsync already completed (post-fsync
= on the platter), so the device instrument alone does not lose *acknowledged* data.

### (b) Reordered-writeback SIMULATION on the REAL fjall 3.1.4 journal (faithful, labeled)
Models the non-trivial case a fsync-less Buffer crash physically admits: the kernel writes
dirty pages back in ARBITRARY order, so a crash can persist a LATER page while dropping an
INTERIOR one. We write 50 SyncAll-acked keys (real fjall journal), then zero ONE interior
4 KiB page (a dropped page-writeback) leaving surrounding pages — incl. later acked batches —
intact. NOT a real power cut; clearly labeled a simulation operating on real fjall bytes.

| drop_page | OPEN_OK | KEYS  | ERR  | note |
|-----------|---------|-------|------|------|
| 0 (header)| true    | 0/50  | none | magic region gone → empty, clean open |
| **1 (interior)** | **true** | **38/50** | **none** | **mid-journal tear: 12 acked keys silently lost** |
| 2,3 (past data) | true | 50/50 | none | falls in the 64 MiB pre-alloc zero region (no data) |

Recovery log (drop_page=1): `DEBUG truncating journal to 4103` → `DEBUG Invalid batch:
missing terminator ... discarding to keep atomicity` → `KEYS=38/50 ERR=none`. The keys
AFTER the dropped interior page were physically on disk yet were discarded — **silent loss
of SyncAll-acknowledged data via a realistic interior page-drop, clean open, no error.**

## 5. Pre-registered NULL — did it happen?
NULL was: "for framing corruption, open fails loudly OR all 50 keys present." It did **NOT**
happen on any framing mode (all opened clean with 0<keys<50). It happened only on the
in-data control (data_flip → loud fail) — exactly the discriminator the claim predicts.

## 6. IT-MATTERS threshold — met?
YES. Framing corruption → OPEN_OK=true AND 0<keys<50 (silent partial loss of acknowledged
data) on ≥4 hand modes + the reorder-sim interior tear, WHILE the in-data control fails loud
(OPEN_OK=false). Disposition rule (control loud-fails AND ≥2 framing modes silent-clean AND
real-crash harness produces the tear from the default Buffer path): **satisfied.**

## 7. Honest scope / remaining L1 step
- The **clean-open-no-error + silent-truncate asymmetry by location** is verified in source
  and reproduced deterministically (hand-corruption + real-journal reorder sim).
- The **real device-level crash (dm-flakey)** demonstrates the silent-loss + clean-open from
  the DEFAULT Buffer path, but the bytes it can drop are un-fsync'd Buffer data (documented
  loss). The *strongest* form — a real power cut dropping data whose `SyncAll` already
  returned — is NOT achievable with dm-flakey (post-fsync data is on the platter) and is the
  remaining L1 step: e.g. dm-log-writes replay reordering *barrier-respecting* writes, or a
  hardware/QEMU power-cut harness that reorders across an fsync barrier the FS didn't honor.
  The interior-tear case (which discards acked data physically present after a hole) is shown
  faithfully via the labeled reorder sim on the real journal; lifting it to a real reordered
  device write is the L1 follow-up.

## 8. Novelty (gate-4 defense)
NOT generic "single-file WALs lose data after a hole" (folklore). The contribution is the
**LOUD-vs-SILENT recovery ASYMMETRY by corruption LOCATION** (in-data → loud xxh3 checksum
`Err`; framing → silent `truncate_to`+`None`) under the **DEFAULT** durability mode, plus a
**CLEAN OPEN WITH NO ERROR while discarding committed data even physically present after the
hole** — fjall-specific, verified in 3.1.4 source, and un-owned (issue #53 is a cosmetic
trailing-batch warning suppression; #112/#113 a different fixed clean-path bug; no
CVE/Jepsen/paper).

## 9. Disposition
**SUPPORT.** Mechanism verified in source; asymmetry reproduced; control loud-fails; real
dm-flakey crash + faithful real-journal reorder sim both produce silent loss + clean-open.
Submit to committee (do NOT self-converge). The acked-data-via-real-reordered-device-write
is flagged as the L1 hardening step, not a refutation.

## Artifacts
- `harness/src/main.rs` (probe + reorder_sim), `harness/Cargo.toml` (=3.1.4), `harness/Cargo.lock`
- `harness/dmflakey_crash.sh` (real device-level crash driver)
- `artifacts/run_main.txt` (hand asymmetry table), `artifacts/log_asymmetry_excerpt.txt`
- `artifacts/reorder_sim.txt` (real-journal reorder sim + recovery log)
- `artifacts/dmflakey_clean.txt` (real dm-flakey crash, Case A 5/50 + Case B 50/50)
- `artifacts/dmflakey_run1..4*.txt` (earlier dm-flakey runs incl. the IO-error edge case)
