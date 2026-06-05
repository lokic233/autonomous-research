#!/bin/bash
cd ~/zenoh_exp0087
BIN=./target/release/zenoh_exp0087
N=50000; EP=tcp/127.0.0.1:7447
LOG=~/exp0087_logs/blockverify_out.txt
: > $LOG
run2() {
  local SLOW=$1 BLOCK=$2
  pkill -9 -f "zenoh_exp0087 (sub|pub)" 2>/dev/null; sleep 1
  local FLAG=""; [ "$BLOCK" = "1" ] && FLAG="--block"
  $BIN sub --listen $EP --n $N --slow-us $SLOW >/tmp/sub_out.txt 2>/dev/null &
  local SPID=$!; sleep 1.5
  local T0=$(date +%s.%N)
  $BIN pub --connect $EP --n $N $FLAG >/tmp/pub_out.txt 2>/dev/null &
  local PP=$!; wait $PP
  local T1=$(date +%s.%N)
  for i in $(seq 1 130); do grep -q SUB_RESULT /tmp/sub_out.txt && break; sleep 1; done
  kill -9 $SPID 2>/dev/null
  echo "slow=$SLOW block=$BLOCK pub_wall=$(echo "$T1-$T0"|bc)s | $(grep PUB_RESULT /tmp/pub_out.txt) | $(grep SUB_RESULT /tmp/sub_out.txt)" >> $LOG
}
echo "===== BLOCK VERIFY: does Block backpressure (slow pub_wall, full delivery) or drop? =====" >> $LOG
run2 200 0
run2 200 1
echo "BV_DONE" >> $LOG
