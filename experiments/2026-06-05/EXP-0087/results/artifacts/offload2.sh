#!/bin/bash
cd ~/zenoh_exp0087
BIN=./target/release/zenoh_exp0087
EP=tcp/127.0.0.1:7447; N=50000
LOG=~/exp0087_logs/offload2_out.txt
: > $LOG
run2() {
  local SLOW=$1 OFFLOAD=$2
  pkill -9 -f "zenoh_exp0087 (sub|pub)" 2>/dev/null; sleep 1
  local SF=""; [ "$OFFLOAD" = "1" ] && SF="--offload"
  $BIN sub --listen $EP --n $N --slow-us $SLOW $SF >/tmp/sub_out.txt 2>/dev/null &
  local SPID=$!; sleep 1.5
  $BIN pub --connect $EP --n $N >/tmp/pub_out.txt 2>/dev/null &
  local PP=$!; wait $PP
  for i in $(seq 1 130); do grep -q SUB_RESULT /tmp/sub_out.txt && break; sleep 1; done
  kill -9 $SPID 2>/dev/null
  echo "slow=$SLOW offload=$OFFLOAD | $(grep SUB_RESULT /tmp/sub_out.txt)" >> $LOG
}
echo "===== CONTROL (b): offload sub callback to unbounded channel =====" >> $LOG
run2 200 0
run2 200 1
echo "OFF_DONE" >> $LOG
