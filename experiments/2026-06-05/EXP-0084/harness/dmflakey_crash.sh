#!/usr/bin/env bash
# REAL-CRASH HARNESS (dm-flakey, two-phase) for EXP-0084 / CLAIM-0071
# Phase A: create DB + write N_SYNC keys with SyncAll, CLEAN close -> LSM manifest/tables +
#          early journal fully durable on the device (the app's committed baseline).
# Phase B: reopen, APPEND N_BUF keys in DEFAULT PersistMode::Buffer (write to OS page cache,
#          no fsync) then N_TAIL keys in SyncAll (app believes definitely durable). NO clean
#          close. Only the journal FRONTIER pages are dirty; LSM files untouched.
# CRASH:   dm-flakey drop_writes silently DROPS the writeback of those dirty journal pages =
#          faithful model of lost/out-of-order page writeback on power loss with no fsync ->
#          torn journal frontier = FRAMING tear (missing End marker mid-journal).
set -u
BIN=/home/dengcchi/fjall_exp/EXP-0084/harness/target/release/fjall_probe
WORK=/home/dengcchi/fjall_exp/EXP-0084/dmflakey
IMG=$WORK/backing.img; MNT=$WORK/mnt; DM=flk$$; DEV=/dev/mapper/$DM; LOOP=""
N_SYNC=${1:-5}; N_BUF=${2:-40}; N_TAIL=${3:-5}
TOTAL=$((N_SYNC+N_BUF+N_TAIL))
cleanup(){ sudo umount -l $MNT 2>/dev/null; sudo dmsetup remove $DM 2>/dev/null; [ -n "$LOOP" ] && sudo losetup -d "$LOOP" 2>/dev/null; }
trap cleanup EXIT
rm -rf $WORK; mkdir -p $WORK $MNT
dd if=/dev/zero of=$IMG bs=1M count=256 status=none
LOOP=$(sudo losetup -f --show $IMG); SECTORS=$(sudo blockdev --getsz $LOOP)
echo "loop=$LOOP sectors=$SECTORS dm=$DM"
sudo dmsetup create $DM --table "0 $SECTORS flakey $LOOP 0 60 0" || { echo DMFAIL; exit 1; }
sudo mkfs.ext4 -q -F $DEV; sudo mount $DEV $MNT; sudo chmod 777 $MNT
DBP=$MNT/db

echo "=== Phase A: $N_SYNC SyncAll keys + clean close (durable baseline) ==="
$BIN crash_setup $DBP $N_SYNC 2>/dev/null
sync; sleep 0.5
echo "journal after baseline: $($BIN inspect_jnl $DBP 2>/dev/null)"

echo "=== Phase B: append $N_BUF Buffer + $N_TAIL SyncAll-tail keys, NO clean close ==="
$BIN crash_append $DBP $N_SYNC $N_BUF $N_TAIL 2>/dev/null

echo "=== CRASH (drop_writes): journal-frontier writeback silently dropped ==="
sudo dmsetup suspend --noflush $DM
sudo dmsetup load $DM --table "0 $SECTORS flakey $LOOP 0 0 60 1 drop_writes"
sudo dmsetup resume $DM
sync 2>/dev/null   # writeback of dirty journal pages -> DROPPED (power-loss instant)
sleep 1
sudo umount -l $MNT 2>/dev/null

echo "=== restore device, drop caches, remount (what survived) ==="
sudo dmsetup suspend --noflush $DM
sudo dmsetup load $DM --table "0 $SECTORS flakey $LOOP 0 60 0"
sudo dmsetup resume $DM
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
sudo mount $DEV $MNT
echo "journal post-crash: $($BIN inspect_jnl $DBP 2>/dev/null)"

echo "=== REOPEN fjall after crash ==="
ST=$(mktemp /tmp/crash_reopen.XXXXXX.stderr)
RUST_LOG=debug $BIN crash_open $DBP $TOTAL 2>"$ST"
echo "--- recovery log ---"
grep -iE "truncating|Recovery successful|Recovered active memtable|checksum|ERROR|Invalid batch|missing terminator|Unrecoverable" "$ST" | tail -12
