#!/bin/bash
cd ~/zenoh_exp0087
BIN=./target/release/zenoh_exp0087
N=50000; RTR=tcp/127.0.0.1:7500
LOG=~/exp0087_logs/arm3c_out.txt
: > $LOG
run3() {
  local SLOW=$1 BLOCK=$2
  pkill -9 -f "zenoh_exp0087 (router|sub|pub)" 2>/dev/null; sleep 1
  local PFLAGS="--client"; [ "$BLOCK" = "1" ] && PFLAGS="$PFLAGS --block"
  $BIN router --listen $RTR >/dev/null 2>&1 &
  local RPID=$!; sleep 2
  $BIN sub --connect $RTR --client --n $N --slow-us $SLOW >/tmp/sub_out.txt 2>/dev/null &
  local SPID=$!; sleep 1.5
  $BIN pub --connect $RTR $PFLAGS --n $N >/tmp/pub_out.txt 2>/dev/null &
  local PP=$!; wait $PP
  for i in $(seq 1 130); do grep -q SUB_RESULT /tmp/sub_out.txt && break; sleep 1; done
  kill -9 $RPID $SPID 2>/dev/null
  echo "slow=$SLOW block=$BLOCK | $(grep PUB_RESULT /tmp/pub_out.txt) | $(grep SUB_RESULT /tmp/sub_out.txt)" >> $LOG
}
echo "===== ARM3c: patient 3-node drain =====" >> $LOG
run3 1000 0
run3 1000 1
echo "ARM3C_DONE" >> $LOG
